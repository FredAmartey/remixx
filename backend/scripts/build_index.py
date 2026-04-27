"""Build the FAISS index over the catalog with multi-source fusion.

Each track gets two text representations — metadata (title/artist/genre/mood)
and a Claude-generated vibe blurb. We encode both with sentence-transformers,
normalize, and average the two embeddings to produce a single 384-dim fused vector.

When a vibe is missing for a track (rare), the fused vector falls back to the
metadata embedding alone.
"""
from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

from app.rag import CATALOG, INDEX, META, MODEL_NAME, VIBES, metadata_text, vibe_text


def main() -> None:
    df = pd.read_csv(CATALOG)
    vibes: dict[str, str] = {}
    if VIBES.exists():
        vibes = json.loads(VIBES.read_text())
        print(f"Loaded {len(vibes)} cached vibe descriptions.")
    else:
        print("WARNING: vibes.json not found; falling back to metadata-only.")

    print(f"Loading model {MODEL_NAME}…")
    model = SentenceTransformer(MODEL_NAME)

    meta_texts = [metadata_text(row) for _, row in df.iterrows()]
    vibe_texts = [vibe_text(row, vibes) for _, row in df.iterrows()]

    print(f"Encoding metadata texts ({len(meta_texts)})…")
    meta_embs = model.encode(meta_texts, normalize_embeddings=True, show_progress_bar=True).astype("float32")

    # Vibes: encode in one batch but only for rows that have a vibe; missing → use metadata embedding
    has_vibe_mask = np.array([v is not None for v in vibe_texts])
    fused = meta_embs.copy()
    if has_vibe_mask.any():
        non_null_vibes = [v for v in vibe_texts if v is not None]
        print(f"Encoding {len(non_null_vibes)} vibe blurbs…")
        vibe_embs = model.encode(non_null_vibes, normalize_embeddings=True, show_progress_bar=True).astype("float32")
        # Late fusion: average + renormalize
        idxs = np.where(has_vibe_mask)[0]
        combined = (meta_embs[idxs] + vibe_embs) / 2.0
        # Renormalize so cosine via inner product still works
        norms = np.linalg.norm(combined, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        combined = combined / norms
        fused[idxs] = combined.astype("float32")

    index = faiss.IndexFlatIP(fused.shape[1])
    index.add(fused)

    INDEX.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX))
    META.write_text(json.dumps(
        {"ids": df["id"].tolist(), "model": MODEL_NAME, "fusion": "metadata+vibe (late, averaged)"},
        indent=2,
    ))
    coverage = int(has_vibe_mask.sum()) / len(df)
    print(f"Built index: {index.ntotal} vectors, dim {fused.shape[1]}, vibe coverage {coverage:.0%}")


if __name__ == "__main__":
    main()
