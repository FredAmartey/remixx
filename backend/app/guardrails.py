"""Input/output guardrails + confidence scoring.

Input guardrail: blocks obvious prompt-injection patterns (regex match on the
incoming user text). Pydantic already enforces the length limits.

Output confidence: a cheap proxy combining the top-3 RAG cosine score and the
top-3 reranker score, both normalized to [0, 1] and averaged. This is exposed
on every recommendation response so callers can show low-confidence states.
"""
from __future__ import annotations

import re

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?previous\s+(?:instructions?|prompts?)",
    r"<\|im_start\|>",
    r"system\s*:\s*you\s+are",
    r"forget\s+(?:everything|all|prior)",
    r"new\s+instructions?:",
    r"<\|endoftext\|>",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in PROMPT_INJECTION_PATTERNS]


def is_prompt_injection(text: str) -> bool:
    """Return True if `text` matches any known prompt-injection pattern."""
    return any(p.search(text) for p in _COMPILED)


def compute_confidence(picks: list[dict]) -> float:
    """Average of top-3 _rag_score and normalized top-3 _score, in [0, 1].

    _rag_score is a cosine similarity (typically 0.2–0.7 for relevant matches);
    _score is the reranker output (roughly 0–5.6). Normalising both to [0, 1]
    and averaging keeps the proxy robust to either signal alone being weak.
    """
    top = picks[:3]
    if not top:
        return 0.0
    rag = [float(p.get("_rag_score", 0.0)) for p in top]
    rerank = [float(p.get("_score", 0.0)) for p in top]
    norm_rag = max(0.0, min(1.0, sum(rag) / len(rag)))
    norm_rerank = max(0.0, min(1.0, sum(rerank) / (len(rerank) * 5.6)))
    return round((norm_rag + norm_rerank) / 2, 3)
