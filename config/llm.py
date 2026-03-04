"""LLM provider abstraction layer."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class LLMMessage:
    role: str
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """Generate a response from the LLM."""
        ...

    @abstractmethod
    def provider_name(self) -> str:
        ...


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
        return self._client

    async def generate(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        client = self._get_client()
        response = await client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            usage={"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens},
        )

    def provider_name(self) -> str:
        return "anthropic"


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            import openai
            self._client = openai.AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def generate(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content,
            model=response.model,
            usage={"prompt_tokens": response.usage.prompt_tokens, "completion_tokens": response.usage.completion_tokens},
        )

    def provider_name(self) -> str:
        return "openai"


def create_llm_provider(provider: str, api_key: str, model: str | None = None) -> LLMProvider:
    """Factory function to create LLM provider instances."""
    if provider == "anthropic":
        return AnthropicProvider(api_key=api_key, model=model or "claude-sonnet-4-20250514")
    elif provider == "openai":
        return OpenAIProvider(api_key=api_key, model=model or "gpt-4o")
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
