"""
Ingest files from the knowledge/ directory into ChromaDB.
Run this whenever you add new files:  python rag/ingest.py
"""

import os
import sys
import hashlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import KNOWLEDGE_DIR, CHROMA_DIR, SUPPORTED_EXTENSIONS, CHUNK_SIZE, CHUNK_OVERLAP

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    print("Install chromadb: pip install chromadb")
    sys.exit(1)


def _get_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    ef = embedding_functions.DefaultEmbeddingFunction()
    return client.get_or_create_collection("knowledge", embedding_function=ef)


def _chunk_text(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunks.append(text[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def _extract_text(filepath: str) -> str:
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".pdf":
        try:
            import fitz  # pymupdf
            doc = fitz.open(filepath)
            return "\n".join(page.get_text() for page in doc)
        except ImportError:
            return "[PDF skipped — install pymupdf: pip install pymupdf]"

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"[ERROR reading {filepath}: {e}]"


def ingest(directory: str = KNOWLEDGE_DIR):
    collection = _get_collection()
    total_chunks = 0
    total_files = 0

    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        print(f"Created knowledge directory: {directory}")
        print("Drop your files there and run this script again.")
        return

    for root, _, files in os.walk(directory):
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            fpath = os.path.join(root, fname)
            rel_path = os.path.relpath(fpath, directory)
            text = _extract_text(fpath)

            if not text.strip():
                continue

            chunks = _chunk_text(text)
            ids, docs, metas = [], [], []

            for i, chunk in enumerate(chunks):
                chunk_id = hashlib.md5(f"{rel_path}:{i}:{chunk[:50]}".encode()).hexdigest()
                ids.append(chunk_id)
                docs.append(chunk)
                metas.append({"source": rel_path, "chunk": i})

            # Upsert so re-running is idempotent
            collection.upsert(ids=ids, documents=docs, metadatas=metas)
            total_chunks += len(chunks)
            total_files += 1
            print(f"  ✓ {rel_path} ({len(chunks)} chunks)")

    print(f"\nDone. Indexed {total_files} files → {total_chunks} chunks.")


if __name__ == "__main__":
    print(f"Indexing files from: {KNOWLEDGE_DIR}\n")
    ingest()
