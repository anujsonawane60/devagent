"""Tests for config/llm.py"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from config.llm import (
    AnthropicProvider,
    LLMMessage,
    LLMResponse,
    OpenAIProvider,
    create_llm_provider,
)


class TestFactory:
    def test_create_anthropic(self):
        p = create_llm_provider("anthropic", "key123")
        assert isinstance(p, AnthropicProvider)
        assert p.api_key == "key123"

    def test_create_openai(self):
        p = create_llm_provider("openai", "key456", model="gpt-4o-mini")
        assert isinstance(p, OpenAIProvider)
        assert p.model == "gpt-4o-mini"

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            create_llm_provider("gemini", "key")


class TestAnthropicProvider:
    @pytest.mark.asyncio
    async def test_generate(self):
        provider = AnthropicProvider(api_key="test-key")
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Hello!")]
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=5)
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        provider._client = mock_client

        result = await provider.generate([LLMMessage(role="user", content="Hi")])
        assert isinstance(result, LLMResponse)
        assert result.content == "Hello!"

    def test_provider_name(self):
        assert AnthropicProvider("k").provider_name() == "anthropic"


class TestOpenAIProvider:
    @pytest.mark.asyncio
    async def test_generate(self):
        provider = OpenAIProvider(api_key="test-key")
        mock_client = AsyncMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "World!"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-4o"
        mock_response.usage = MagicMock(prompt_tokens=8, completion_tokens=3)
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        provider._client = mock_client

        result = await provider.generate([LLMMessage(role="user", content="Hi")])
        assert isinstance(result, LLMResponse)
        assert result.content == "World!"

    def test_provider_name(self):
        assert OpenAIProvider("k").provider_name() == "openai"
