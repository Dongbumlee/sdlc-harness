"""Thin wrapper that adapts the provider interface for the orchestrator."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bench.engine.provider import MockProvider, OpenAIProvider


class LLMClient:
    """Adapts a bench-engine provider for orchestrator use."""

    def __init__(self, provider: MockProvider | OpenAIProvider) -> None:
        self.provider = provider

    async def complete(self, system: str, prompt: str, model: str = "gpt-4o") -> str:
        """Forward to the underlying provider."""
        return await self.provider.complete(prompt=prompt, system=system, model=model)
