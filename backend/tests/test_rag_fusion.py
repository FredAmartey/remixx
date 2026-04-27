"""Confirm the fused index loads and returns plausible results.

We don't have a baseline to compare against in this test; that's what
eval/run_eval.py is for. This just confirms the index has the expected shape
and behavior after rebuilding with vibes.
"""
import json
from app.rag import META, RAGRetriever


def test_index_meta_records_fusion():
    meta = json.loads(META.read_text())
    assert "fusion" in meta
    assert "vibe" in meta["fusion"].lower()
    assert len(meta["ids"]) == 500


def test_retriever_returns_results_after_fusion_rebuild():
    r = RAGRetriever.load()
    results = r.search("late night driving with hopeful tilt", k=5)
    assert len(results) == 5
    for hit in results:
        assert hit["score"] > 0
        assert isinstance(hit["id"], str)
