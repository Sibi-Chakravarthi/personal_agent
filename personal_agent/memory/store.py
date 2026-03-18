"""
Persistent long-term memory using ChromaDB.
Stores conversation summaries, facts, and preferences across sessions.
Supports categorized memory types and targeted search.
"""

import os
import sys
import time
import hashlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import CHROMA_DIR, MEMORY_RECALL_COUNT

try:
    import chromadb
    from chromadb.utils import embedding_functions
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False

# Memory categories
MEMORY_TYPES = {"exchange", "fact", "preference", "task", "note", "general"}


def _get_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    ef = embedding_functions.DefaultEmbeddingFunction()
    return client.get_or_create_collection("agent_memory", embedding_function=ef)


def save_memory(text: str, tags: list[str] = None, category: str = "general"):
    """Save a memory/fact for future recall."""
    if not _AVAILABLE:
        return

    if category not in MEMORY_TYPES:
        category = "general"

    try:
        collection = _get_collection()
        uid = hashlib.md5(f"{time.time()}:{text[:40]}".encode()).hexdigest()
        collection.add(
            ids=[uid],
            documents=[text],
            metadatas=[{
                "timestamp": time.strftime("%Y-%m-%d %H:%M"),
                "tags": ",".join(tags or []),
                "category": category,
            }]
        )
    except Exception:
        pass


def recall_memories(query: str, count: int = None) -> str:
    """Retrieve memories relevant to the current query."""
    if not _AVAILABLE:
        return ""

    count = count or MEMORY_RECALL_COUNT

    try:
        collection = _get_collection()
        if collection.count() == 0:
            return ""

        results = collection.query(
            query_texts=[query],
            n_results=min(count, collection.count()),
        )

        docs  = results["documents"][0]
        metas = results["metadatas"][0]

        if not docs:
            return ""

        lines = ["[Relevant memories from past sessions:]"]
        for doc, meta in zip(docs, metas):
            ts = meta.get("timestamp", "")
            cat = meta.get("category", "")
            cat_label = f" [{cat}]" if cat and cat != "general" else ""
            lines.append(f"• [{ts}]{cat_label} {doc}")

        return "\n".join(lines)

    except Exception:
        return ""


def search_memories(query: str, category: str = None, count: int = 10) -> str:
    """Search memories with optional category filter."""
    if not _AVAILABLE:
        return "ChromaDB not installed."

    try:
        collection = _get_collection()
        if collection.count() == 0:
            return "No memories stored yet."

        where_filter = None
        if category and category in MEMORY_TYPES:
            where_filter = {"category": category}

        results = collection.query(
            query_texts=[query],
            n_results=min(count, collection.count()),
            where=where_filter,
        )

        docs = results["documents"][0]
        metas = results["metadatas"][0]

        if not docs:
            return "No matching memories found."

        lines = [f"🔍 Found {len(docs)} memories:"]
        for doc, meta in zip(docs, metas):
            ts = meta.get("timestamp", "")
            cat = meta.get("category", "")
            lines.append(f"  [{ts}] ({cat}) {doc}")
        return "\n".join(lines)

    except Exception as e:
        return f"[ERROR] {e}"


def forget_memory(query: str) -> str:
    """Delete memories matching a query (closest match)."""
    if not _AVAILABLE:
        return "ChromaDB not installed."

    try:
        collection = _get_collection()
        if collection.count() == 0:
            return "No memories to delete."

        results = collection.query(query_texts=[query], n_results=1)
        if results["ids"][0]:
            doc = results["documents"][0][0]
            collection.delete(ids=results["ids"][0])
            return f"🗑️ Deleted memory: {doc[:100]}"
        return "No matching memory found."

    except Exception as e:
        return f"[ERROR] {e}"


def list_memories(limit: int = 20) -> str:
    """List all stored memories (for the /memories command)."""
    if not _AVAILABLE:
        return "ChromaDB not installed."

    try:
        collection = _get_collection()
        count = collection.count()
        if count == 0:
            return "No memories stored yet."

        result = collection.get(limit=min(limit, count), include=["documents", "metadatas"])
        lines = [f"🧠 Stored memories ({count} total):\n"]
        for doc, meta in zip(result["documents"], result["metadatas"]):
            ts = meta.get("timestamp", "")
            cat = meta.get("category", "")
            cat_label = f" ({cat})" if cat else ""
            lines.append(f"[{ts}]{cat_label} {doc}")
        return "\n".join(lines)

    except Exception as e:
        return f"[ERROR] {e}"
