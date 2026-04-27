"""Build the FAISS index over the catalog. Run after sample_catalog.py."""
from __future__ import annotations

import json
from pathlib import Path

import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer

from app.rag import CATALOG, INDEX, META, MODEL_NAME, track_text


def main() -> None:
    df = pd.read_csv(CATALOG)
    texts = [track_text(row) for _, row in df.iterrows()]

    print(f"Loading model {MODEL_NAME}…")
    model = SentenceTransformer(MODEL_NAME)
    embs = model.encode(texts, normalize_embeddings=True, show_progress_bar=True).astype("float32")

    index = faiss.IndexFlatIP(embs.shape[1])  # inner product = cosine on normalized vectors
    index.add(embs)

    INDEX.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX))
    META.write_text(json.dumps({"ids": df["id"].tolist(), "model": MODEL_NAME}, indent=2))
    print(f"Built index: {index.ntotal} vectors, dim {embs.shape[1]}")


if __name__ == "__main__":
    main()
