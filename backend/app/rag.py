"""Semantic retrieval over the Remixx catalog using sentence-transformers + FAISS.

Builds a single text representation per track from metadata
("{title} by {artist}. Genre: {genre}, mood: {mood}.") and embeds it with
all-MiniLM-L6-v2. Inner-product search on normalized vectors = cosine similarity.

Vibes (Claude-generated descriptions) are NOT included yet — that's a planned
RAG enhancement.
"""
from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CATALOG = DATA_DIR / "catalog.csv"
INDEX = DATA_DIR / "index.faiss"
META = DATA_DIR / "index_meta.json"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def track_text(row: dict) -> str:
    """Single text representation for embedding."""
    return f"{row['title']} by {row['artist']}. Genre: {row['genre']}, mood: {row['mood']}."


class RAGRetriever:
    """Loads a pre-built FAISS index and runs semantic search."""

    def __init__(self, model: SentenceTransformer, index, ids: list[str]) -> None:
        self.model = model
        self.index = index
        self.ids = ids

    @classmethod
    def load(cls) -> "RAGRetriever":
        if not INDEX.exists() or not META.exists():
            raise FileNotFoundError(
                f"Index not built. Run: uv run python -m scripts.build_index"
            )
        model = SentenceTransformer(MODEL_NAME)
        index = faiss.read_index(str(INDEX))
        meta = json.loads(META.read_text())
        return cls(model, index, meta["ids"])

    def search(self, query: str, k: int = 30) -> list[dict]:
        """Return top-k {id, score} entries, score is cosine similarity in [-1, 1]."""
        qv = self.model.encode([query], normalize_embeddings=True).astype("float32")
        scores, indices = self.index.search(qv, k)
        results = []
        for s, i in zip(scores[0], indices[0]):
            if i == -1:
                continue
            results.append({"id": self.ids[i], "score": float(s)})
        return results
