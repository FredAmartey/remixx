"""Generate Claude-cached vibe descriptions for each catalog track.

For each row in catalog.csv, calls Haiku to produce a 1-2 sentence vibe blurb
that captures what the song *feels* like beyond its raw audio features.

Output: backend/data/vibes.json keyed by track id. Skips tracks already cached.
Parallelized via a ThreadPoolExecutor — each Agent SDK / API call is independent.
"""
from __future__ import annotations

import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

from app.llm import LLMClient

CATALOG = Path(__file__).resolve().parents[1] / "data" / "catalog.csv"
OUT = Path(__file__).resolve().parents[1] / "data" / "vibes.json"
WORKERS = 8

PROMPT_TMPL = """Write 1-2 sentences describing the vibe of this song. Be specific and evocative — like a music critic. Don't restate the title or genre. Focus on: what listening experience it evokes, the emotional register, the kind of moment it fits.

Track: {title}
Artist: {artist}
Genre: {genre}
Energy: {energy:.2f} (0=quiet, 1=intense)
Valence: {valence:.2f} (0=sad, 1=happy)
Danceability: {danceability:.2f}

Vibe description:"""

_lock = threading.Lock()


def _generate_one(row: dict, client: LLMClient) -> tuple[str, str | None, str | None]:
    """Returns (track_id, vibe_or_none, error_or_none)."""
    tid = str(row["id"])
    try:
        prompt = PROMPT_TMPL.format(
            title=row["title"],
            artist=row["artist"],
            genre=row["genre"],
            energy=float(row["energy"]),
            valence=float(row["valence"]),
            danceability=float(row["danceability"]),
        )
        vibe = client.complete("haiku", prompt, max_tokens=200).strip()
        return tid, vibe, None
    except Exception as exc:
        return tid, None, str(exc)


def main() -> int:
    df = pd.read_csv(CATALOG)
    cache: dict[str, str] = {}
    if OUT.exists():
        cache = json.loads(OUT.read_text())
        print(f"Loaded {len(cache)} cached vibes; will skip those.")

    todo = [row.to_dict() for _, row in df.iterrows() if str(row["id"]) not in cache]
    print(f"Queueing {len(todo)} tracks across {WORKERS} workers.")

    client = LLMClient()
    written = 0
    failed = 0
    t_start = time.time()

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(_generate_one, row, client): row for row in todo}
        for fut in as_completed(futures):
            tid, vibe, err = fut.result()
            row = futures[fut]
            if vibe:
                with _lock:
                    cache[tid] = vibe
                    written += 1
                    if written % 25 == 0:
                        OUT.write_text(json.dumps(cache, indent=2))
                rate = written / max(time.time() - t_start, 1)
                eta = (len(todo) - written) / max(rate, 0.01)
                print(f"[{written:3d}/{len(todo)}] {row['title'][:36]:<36} — {vibe[:50]}  | {rate:.1f}/s  eta {eta:.0f}s")
            else:
                failed += 1
                print(f"  FAIL  {row['title'][:36]}: {err}", file=sys.stderr)

    OUT.write_text(json.dumps(cache, indent=2))
    elapsed = time.time() - t_start
    print(f"\nDone in {elapsed:.0f}s. Wrote {written} new, {failed} failed. Total cached: {len(cache)}/{len(df)}.")
    return 0 if failed < len(df) * 0.1 else 1


if __name__ == "__main__":
    sys.exit(main())
