"""Smoke tests for LLMClient transport selection. The actual completion call
is exercised manually below; we don't want unit tests hitting the LLM."""
from app.llm import LLMClient


def test_picks_agent_sdk_when_no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client = LLMClient()
    assert client.transport == "agent_sdk"


def test_picks_anthropic_sdk_when_api_key_present(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-key-for-test")
    client = LLMClient()
    assert client.transport == "anthropic_sdk"


def test_haiku_model_id_resolves():
    from app.llm import MODELS
    assert MODELS["haiku"] == "claude-haiku-4-5-20251001"
    assert MODELS["sonnet"] == "claude-sonnet-4-6"
