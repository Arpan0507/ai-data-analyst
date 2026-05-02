"""
memory.py — FAISS Vector Memory Layer

Stores dataset profiles, past insights, and cleaning decisions
in a FAISS vector index for context-aware future analyses.
Uses sentence-transformers for text embedding.
"""

from __future__ import annotations

import os
import json
import pickle
import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

# Lazy imports for FAISS and sentence-transformers
_index = None
_metadata_store: list[dict[str, Any]] = []
_embedder = None
_MEMORY_DIR = "data/memory"
_INDEX_FILE = os.path.join(_MEMORY_DIR, "faiss_index.bin")
_META_FILE = os.path.join(_MEMORY_DIR, "metadata.pkl")
_EMBED_DIM = 384  # MiniLM default


def _get_embedder():
    """Lazy-load the sentence embedding model."""
    global _embedder
    if _embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedder = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Loaded sentence-transformers model: all-MiniLM-L6-v2")
        except ImportError:
            logger.warning(
                "sentence-transformers not available. "
                "Memory layer will use simple TF-IDF fallback."
            )
            _embedder = "fallback"
    return _embedder


def _embed_text(text: str) -> np.ndarray:
    """Embed text into a vector."""
    embedder = _get_embedder()
    if embedder == "fallback":
        return _simple_hash_embed(text)
    return embedder.encode([text], normalize_embeddings=True)[0]


def _simple_hash_embed(text: str) -> np.ndarray:
    """Fallback: create a simple hash-based embedding."""
    np.random.seed(hash(text) % (2**31))
    vec = np.random.randn(_EMBED_DIM).astype(np.float32)
    vec /= np.linalg.norm(vec) + 1e-8
    return vec


def initialize_memory():
    """Load or create the FAISS index and metadata store."""
    global _index, _metadata_store

    os.makedirs(_MEMORY_DIR, exist_ok=True)

    try:
        import faiss

        if os.path.exists(_INDEX_FILE) and os.path.exists(_META_FILE):
            _index = faiss.read_index(_INDEX_FILE)
            with open(_META_FILE, "rb") as f:
                _metadata_store = pickle.load(f)
            logger.info(
                f"Loaded memory: {_index.ntotal} entries from disk."
            )
        else:
            _index = faiss.IndexFlatIP(_EMBED_DIM)  # Inner product (cosine for normalized vectors)
            _metadata_store = []
            logger.info("Created new FAISS memory index.")

    except ImportError:
        logger.warning("faiss-cpu not installed. Memory layer disabled.")
        _index = None
        _metadata_store = []


def store_memory(text: str, metadata: dict[str, Any]) -> bool:
    """
    Store a text entry in the vector memory.

    Parameters
    ----------
    text : str
        The text to embed and store.
    metadata : dict
        Associated metadata (type, session_id, timestamp, etc.)

    Returns
    -------
    bool
        True if stored successfully.
    """
    global _index, _metadata_store

    if _index is None:
        return False

    try:
        import faiss
        embedding = _embed_text(text).astype(np.float32).reshape(1, -1)
        _index.add(embedding)
        _metadata_store.append({
            "text": text[:2000],  # Limit stored text size
            **metadata,
        })
        _save_to_disk()
        return True
    except Exception as exc:
        logger.error(f"Failed to store memory: {exc}")
        return False


def search_memory(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """
    Search the memory for relevant past context.

    Parameters
    ----------
    query : str
        The search query text.
    top_k : int
        Number of results to return.

    Returns
    -------
    list[dict]
        List of matching entries with text, metadata, and score.
    """
    global _index, _metadata_store

    if _index is None or _index.ntotal == 0:
        return []

    try:
        embedding = _embed_text(query).astype(np.float32).reshape(1, -1)
        scores, indices = _index.search(embedding, min(top_k, _index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(_metadata_store):
                continue
            entry = _metadata_store[idx].copy()
            entry["similarity_score"] = float(score)
            results.append(entry)

        return results
    except Exception as exc:
        logger.error(f"Memory search failed: {exc}")
        return []


def get_memory_context(query: str, top_k: int = 3) -> str:
    """
    Get formatted memory context for agent consumption.

    Returns a text string summarizing relevant past analyses.
    """
    results = search_memory(query, top_k)
    if not results:
        return ""

    lines = ["Relevant past analyses:"]
    for i, r in enumerate(results, 1):
        lines.append(f"\n[{i}] (similarity: {r.get('similarity_score', 0):.2f})")
        lines.append(f"  Type: {r.get('type', 'unknown')}")
        lines.append(f"  {r.get('text', '')[:500]}")

    return "\n".join(lines)


def _save_to_disk():
    """Persist the FAISS index and metadata to disk."""
    global _index, _metadata_store

    if _index is None:
        return

    try:
        import faiss
        os.makedirs(_MEMORY_DIR, exist_ok=True)
        faiss.write_index(_index, _INDEX_FILE)
        with open(_META_FILE, "wb") as f:
            pickle.dump(_metadata_store, f)
    except Exception as exc:
        logger.error(f"Failed to save memory to disk: {exc}")


def get_memory_stats() -> dict[str, Any]:
    """Return memory index statistics."""
    return {
        "total_entries": _index.ntotal if _index else 0,
        "index_file": _INDEX_FILE,
        "metadata_file": _META_FILE,
    }
