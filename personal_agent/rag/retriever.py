"""Query the ChromaDB knowledge base and return relevant chunks."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import CHROMA_DIR

try:
    import chromadb
    from chromadb.utils import embedding_functions
    _CHROMA_AVAILABLE = True
except ImportError:
    _CHROMA_AVAILABLE = False


def _get_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    ef = embedding_functions.DefaultEmbeddingFunction()
    return client.get_or_create_collection("knowledge", embedding_function=ef)


def query_knowledge(question: str, n_results: int = 4) -> str:
    """
    Search indexed files for chunks relevant to `question`.
    Returns a formatted string ready to inject into a prompt.
    """
    if not _CHROMA_AVAILABLE:
        return "[RAG unavailable — install chromadb: pip install chromadb]"

    try:
        collection = _get_collection()
        count = collection.count()
        if count == 0:
            return "[Knowledge base is empty. Run: python rag/ingest.py]"

        results = collection.query(
            query_texts=[question],
            n_results=min(n_results, count),
        )

        docs      = results["documents"][0]
        metadatas = results["metadatas"][0]

        if not docs:
            return "No relevant content found in knowledge base."

        formatted = []
        for doc, meta in zip(docs, metadatas):
            src = meta.get("source", "unknown")
            formatted.append(f"[File: {src}]\n{doc}")

        return "\n\n---\n\n".join(formatted)

    except Exception as e:
        return f"[RAG ERROR] {e}"
