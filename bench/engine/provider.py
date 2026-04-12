"""LLM provider abstraction for the benchmark engine."""

from __future__ import annotations


class MockProvider:
    """Deterministic mock provider for testing without API calls."""

    async def complete(self, prompt: str, system: str = "", model: str = "mock") -> str:
        """Return deterministic mock response based on prompt content."""
        keywords = [w for w in prompt.split() if len(w) > 4][:5]
        body = ", ".join(keywords) if keywords else "sample output"
        return f"Mock response for: {body}"


class OpenAIProvider:
    """Provider that calls the OpenAI-compatible API."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key
        self.base_url = base_url

    async def complete(self, prompt: str, system: str = "", model: str = "gpt-4o") -> str:
        """Call the OpenAI API and return the completion text."""
        try:
            import openai
        except ImportError as exc:
            raise RuntimeError("openai package is required for OpenAIProvider") from exc

        client = openai.AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(model=model, messages=messages)
        return response.choices[0].message.content or ""


def create_provider(provider_type: str = "mock", **kwargs: str | None) -> MockProvider | OpenAIProvider:
    """Factory function to create an LLM provider."""
    if provider_type == "openai":
        return OpenAIProvider(**kwargs)
    return MockProvider()
