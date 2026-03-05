"""LLM provider abstraction layer.

Supported providers:
  - anthropic  (Claude)
  - openai     (GPT-4o, Codex, o1, etc.)
  - gemini     (Google Gemini)
  - deepseek   (DeepSeek — uses OpenAI-compatible API)
"""

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
    """Supports OpenAI and any OpenAI-compatible API (DeepSeek, etc.)."""

    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str | None = None, provider_label: str = "openai"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self._provider_label = provider_label
        self._client = None

    def _get_client(self):
        if self._client is None:
            import openai
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = openai.AsyncOpenAI(**kwargs)
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
        return self._provider_label


class GeminiProvider(LLMProvider):
    """Google Gemini via the google-generativeai SDK."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    async def generate(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        client = self._get_client()
        # Convert messages to Gemini format: combine into a single prompt
        # Gemini uses "user" and "model" roles
        contents = []
        for m in messages:
            role = "model" if m.role == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": m.content}]})

        response = await client.aio.models.generate_content(
            model=self.model,
            contents=contents,
            config={"max_output_tokens": kwargs.get("max_tokens", 4096)},
        )
        usage = {}
        if response.usage_metadata:
            usage = {
                "prompt_tokens": response.usage_metadata.prompt_token_count,
                "completion_tokens": response.usage_metadata.candidates_token_count,
            }
        return LLMResponse(
            content=response.text,
            model=self.model,
            usage=usage,
        )

    def provider_name(self) -> str:
        return "gemini"


def create_llm_provider(provider: str, api_key: str, model: str | None = None, base_url: str | None = None) -> LLMProvider:
    """Factory function to create LLM provider instances."""
    if provider == "anthropic":
        return AnthropicProvider(api_key=api_key, model=model or "claude-sonnet-4-20250514")
    elif provider == "openai":
        return OpenAIProvider(api_key=api_key, model=model or "gpt-4o")
    elif provider == "gemini":
        return GeminiProvider(api_key=api_key, model=model or "gemini-2.0-flash")
    elif provider == "deepseek":
        return OpenAIProvider(
            api_key=api_key,
            model=model or "deepseek-chat",
            base_url="https://api.deepseek.com",
            provider_label="deepseek",
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Supported: anthropic, openai, gemini, deepseek")
