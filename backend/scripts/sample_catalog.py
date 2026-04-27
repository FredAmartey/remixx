"""Download and sample 500 tracks for the Remixx catalog.

Pulls from the maharshipandya/spotify-tracks-dataset HuggingFace mirror of
Kaggle's Spotify Tracks Dataset (114K rows), samples with genre diversity,
derives a mood label from valence + energy, and writes backend/data/catalog.csv.
"""
from pathlib import Path

import pandas as pd
from huggingface_hub import hf_hub_download

OUT = Path(__file__).resolve().parents[1] / "data" / "catalog.csv"

def derive_mood(row) -> str:
    e, v = row["energy"], row["valence"]
    if e > 0.7 and v > 0.6: return "happy"
    if e > 0.7 and v < 0.4: return "intense"
    if e < 0.4 and v > 0.6: return "relaxed"
    if e < 0.4 and v < 0.4: return "sad"
    return "chill"

def main() -> None:
    path = hf_hub_download(
        repo_id="maharshipandya/spotify-tracks-dataset",
        filename="dataset.csv",
        repo_type="dataset",
    )
    df = pd.read_csv(path)

    # Genre-diversified pool first (≤30 per genre), then sample 500 from that pool.
    # Use groupby().sample() directly — it preserves the grouping column, unlike
    # apply() which drops it in newer pandas versions.
    diversified = (
        df.groupby("track_genre", group_keys=False)
          .sample(n=30, random_state=42)
          .reset_index(drop=True)
    )
    sampled = diversified.sample(500, random_state=42).reset_index(drop=True)

    keep = ["track_id", "track_name", "artists", "album_name", "track_genre",
            "danceability", "energy", "valence", "acousticness", "tempo"]
    sampled = sampled[keep].rename(columns={
        "track_id": "id",
        "track_name": "title",
        "artists": "artist",
        "album_name": "album",
        "track_genre": "genre",
        "tempo": "tempo_bpm",
    })
    sampled["mood"] = sampled.apply(derive_mood, axis=1)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    sampled.to_csv(OUT, index=False)
    print(f"Wrote {len(sampled)} tracks to {OUT}")
    print(f"Genres: {sampled['genre'].nunique()} | Moods: {sampled['mood'].value_counts().to_dict()}")

if __name__ == "__main__":
    main()
