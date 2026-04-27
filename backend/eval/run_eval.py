"""Eval harness: run the agent on 25 predefined queries and score against a golden set.

Pass criterion (per query): at least one of the picks has a genre matching
expected_genres OR a mood matching expected_mood_keywords.

Reports overall pass rate, average latency, and a per-query summary. Saves the
full run to ``last_run.json`` so the README can embed the numbers.

Usage:
    uv run python -m eval.run_eval                # full 25-query run
    uv run python -m eval.run_eval --limit 3      # smoke test (first 3 only)
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

from app.agent import run_agent
from app.guardrails import compute_confidence

GOLDEN = Path(__file__).resolve().parent / "golden_set.json"


def matches(picks: list[dict], expected_genres: list[str], expected_mood_keywords: list[str]) -> bool:
    """A pick passes if its genre OR mood matches anything in the expected sets."""
    eg = {g.lower() for g in expected_genres}
    em = {m.lower() for m in expected_mood_keywords}
    for p in picks:
        genre = str(p.get("genre", "")).lower()
        mood = str(p.get("mood", "")).lower()
        if any(e in genre or genre in e for e in eg if e):
            return True
        if any(e in mood or mood in e for e in em if e):
            return True
    return False


def run() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="run only the first N cases")
    args = parser.parse_args()

    cases = json.loads(GOLDEN.read_text())
    if args.limit:
        cases = cases[: args.limit]

    results = []
    print(f"Remixx eval — {len(cases)} queries\n{'─' * 50}")
    t_overall = time.time()

    for i, case in enumerate(cases, 1):
        t0 = time.time()
        try:
            final = None
            for step in run_agent(case["query"], persona="warm", k=5):
                if step.get("step") == "result":
                    final = step
                    break
            elapsed = round(time.time() - t0, 1)
            if final is None:
                results.append({"i": i, "query": case["query"], "ok": False, "ms": int(elapsed * 1000), "conf": 0.0, "reason": "no result"})
                print(f"[{i:>2}/{len(cases)}] FAIL  {elapsed:>5.1f}s  no result   query={case['query'][:60]!r}")
                continue
            ok = matches(final["picks"], case.get("expected_genres", []), case.get("expected_mood_keywords", []))
            conf = compute_confidence(final["picks"])
            results.append({"i": i, "query": case["query"], "ok": ok, "ms": int(elapsed * 1000), "conf": conf})
            status = "PASS" if ok else "FAIL"
            print(f"[{i:>2}/{len(cases)}] {status}  {elapsed:>5.1f}s  conf={conf:>4.2f}   query={case['query'][:60]!r}")
        except Exception as exc:  # pragma: no cover
            elapsed = round(time.time() - t0, 1)
            results.append({"i": i, "query": case["query"], "ok": False, "ms": int(elapsed * 1000), "conf": 0.0, "reason": str(exc)})
            print(f"[{i:>2}/{len(cases)}] ERROR {elapsed:>5.1f}s  {exc!s}")

    total_elapsed = round(time.time() - t_overall, 1)
    passes = sum(1 for r in results if r["ok"])
    avg_ms = round(statistics.mean([r["ms"] for r in results]) / 1000, 1) if results else 0.0
    avg_conf = round(statistics.mean([r["conf"] for r in results]), 2) if results else 0.0

    print(f"\n{'─' * 50}")
    print(f"PASS: {passes}/{len(results)} ({100 * passes // max(len(results), 1)}%)")
    print(f"Avg latency: {avg_ms}s")
    print(f"Avg confidence: {avg_conf}")
    print(f"Total time: {total_elapsed}s")

    out = Path(__file__).resolve().parent / "last_run.json"
    out.write_text(json.dumps({
        "results": results,
        "summary": {"pass": passes, "total": len(results),
                    "avg_latency_s": avg_ms, "avg_confidence": avg_conf,
                    "total_time_s": total_elapsed},
    }, indent=2))
    print(f"\nSaved full results to {out}")

    return 0 if passes >= len(results) * 0.6 else 1


if __name__ == "__main__":
    sys.exit(run())
