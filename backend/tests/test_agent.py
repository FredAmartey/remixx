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
