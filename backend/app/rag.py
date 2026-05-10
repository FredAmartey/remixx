"""Retrieval over the Remixx catalog.

The default path builds a tiny local TF-IDF index from catalog metadata and cached
vibe blurbs. That keeps the app responsive in demos and avoids a 60s
sentence-transformer startup/download cost.

Set REMIXX_USE_SEMANTIC_RAG=1 to use the heavier sentence-transformers + FAISS
index when you want deeper semantic retrieval and can afford the startup time.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CATALOG = DATA_DIR / "catalog.csv"
INDEX = DATA_DIR / "index.faiss"
META = DATA_DIR / "index_meta.json"
VIBES = DATA_DIR / "vibes.json"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def metadata_text(row: dict) -> str:
    """Metadata-only text representation: title + artist + genre + mood."""
    return f"{row['title']} by {row['artist']}. Genre: {row['genre']}, mood: {row['mood']}."


def vibe_text(row: dict, vibes: dict[str, str]) -> str | None:
    """Vibe blurb if cached, else None."""
    return vibes.get(str(row["id"]))


class RAGRetriever:
    """Loads a local retrieval index and runs catalog search."""

    def __init__(self, model, index, ids: list[str], mode: str = "tfidf") -> None:
        self.model = model
        self.index = index
        self.ids = ids
        self.mode = mode

    @classmethod
    def load(cls) -> "RAGRetriever":
        if os.getenv("REMIXX_USE_SEMANTIC_RAG") == "1":
            return cls._load_semantic()

        df = pd.read_csv(CATALOG)
        vibes = json.loads(VIBES.read_text()) if VIBES.exists() else {}
        ids = [str(row["id"]) for _, row in df.iterrows()]
        texts = [
            " ".join(
                part for part in (metadata_text(row), vibe_text(row, vibes)) if part
            )
            for _, row in df.iterrows()
        ]
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            max_features=5000,
        )
        matrix = vectorizer.fit_transform(texts)
        return cls(vectorizer, matrix, ids)

    @classmethod
    def _load_semantic(cls) -> "RAGRetriever":
        if not INDEX.exists() or not META.exists():
            raise FileNotFoundError(
                f"Index not built. Run: uv run python -m scripts.build_index"
            )
        import faiss
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(MODEL_NAME)
        index = faiss.read_index(str(INDEX))
        meta = json.loads(META.read_text())
        return cls(model, index, meta["ids"], mode="semantic")

    def search(self, query: str, k: int = 30) -> list[dict]:
        """Return top-k {id, score} entries, score is cosine similarity in [-1, 1]."""
        if self.mode == "tfidf":
            qv = self.model.transform([query])
            scores = (self.index @ qv.T).toarray().ravel()
            ranked = scores.argsort()[::-1][:k]
            return [
                {"id": self.ids[i], "score": float(scores[i])}
                for i in ranked
                if scores[i] > 0
            ]

        qv = self.model.encode([query], normalize_embeddings=True).astype("float32")
        scores, indices = self.index.search(qv, k)
        results = []
        for s, i in zip(scores[0], indices[0]):
            if i == -1:
                continue
            results.append({"id": self.ids[i], "score": float(s)})
        return results
