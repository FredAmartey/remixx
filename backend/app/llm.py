"""Unified LLM client. Uses Claude Agent SDK (subscription) by default,
falls back to the anthropic SDK when ANTHROPIC_API_KEY is set."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

# Load backend/.env if present so users can configure ANTHROPIC_API_KEY
# without exporting it in their shell.
_env_path = Path(__file__).resolve().parents[1] / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

MODELS = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-6",
}

Transport = Literal["agent_sdk", "anthropic_sdk"]


class LLMClient:
    """Single entrypoint for all LLM calls in Remixx."""

    transport: Transport

    def __init__(self) -> None:
        if os.getenv("ANTHROPIC_API_KEY"):
            self.transport = "anthropic_sdk"
            from anthropic import Anthropic
            self._anthropic = Anthropic()
        else:
            self.transport = "agent_sdk"
            self._anthropic = None

    def complete(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 1024,
        system: str | None = None,
    ) -> str:
        """Synchronous completion. Returns the assistant's text response."""
        model_id = MODELS[model]
        if self.transport == "anthropic_sdk":
            msg = self._anthropic.messages.create(
                model=model_id,
                max_tokens=max_tokens,
                system=system or "",
                messages=[{"role": "user", "content": prompt}],
            )
            # message.content is a list of content blocks; take text from the first text block
            for block in msg.content:
                if getattr(block, "type", None) == "text":
                    return block.text
            return ""
        else:
            return asyncio.run(
                _agent_sdk_complete(model_id, prompt, max_tokens, system)
            )


async def _agent_sdk_complete(
    model_id: str, prompt: str, max_tokens: int, system: str | None
) -> str:
    """Run Agent SDK query and concatenate assistant text from streamed messages."""
    from claude_agent_sdk import ClaudeAgentOptions, query

    options = ClaudeAgentOptions(
        model=model_id,
        system_prompt=system or None,
        max_turns=1,
    )

    parts: list[str] = []
    async for message in query(prompt=prompt, options=options):
        # The SDK yields different message types. We want assistant text content.
        # AssistantMessage has a `content` list of TextBlock/ToolUseBlock/etc.
        content = getattr(message, "content", None)
        if not content:
            continue
        for block in content:
            text = getattr(block, "text", None)
            if isinstance(text, str):
                parts.append(text)
    return "".join(parts).strip()
