from app.agent import run_agent


def test_agent_yields_observable_steps_and_result():
    steps = list(run_agent("late night driving music with hopeful tilt", persona="warm", k=5))
    titles = [s.get("title") for s in steps if "title" in s]
    assert "Parse intent" in titles
    assert "Retrieve candidates" in titles
    assert "Self-critique" in titles
    assert "DJ commentary" in titles

    result = next((s for s in steps if s.get("step") == "result"), None)
    assert result is not None
    assert len(result["picks"]) == 5
    assert isinstance(result["commentary"], str)
    assert len(result["commentary"]) > 0
    assert result["total_ms"] > 0


def test_focus_playlist_results_are_low_distraction():
    result = next(
        s
        for s in run_agent(
            "deep focus music with no sharp edges and steady momentum",
            persona="warm",
            k=8,
        )
        if s.get("step") == "result"
    )
    picks = result["picks"]
    assert len(picks) == 8
    assert sum(1 for p in picks if p["mood"] == "chill") >= 6
    assert max(float(p["energy"]) for p in picks[:5]) <= 0.58
    assert all(p.get("_rag_score", 0) > 0 for p in picks[:5])
