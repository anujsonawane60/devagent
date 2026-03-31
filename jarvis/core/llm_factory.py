from langchain_core.language_models import BaseChatModel

from jarvis.config import settings


def create_llm(
    provider: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
    **kwargs,
) -> BaseChatModel:
    """Create an LLM instance for the given provider.

    Falls back to settings defaults if args are not provided.
    """
    provider = provider or settings.DEFAULT_LLM_PROVIDER
    model = model or settings.DEFAULT_LLM_MODEL
    temperature = temperature if temperature is not None else settings.DEFAULT_LLM_TEMPERATURE

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            api_key=settings.OPENAI_API_KEY,
            temperature=temperature,
            **kwargs,
        )
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model,
            api_key=settings.ANTHROPIC_API_KEY,
            temperature=temperature,
            **kwargs,
        )
    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=temperature,
            **kwargs,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def create_llm_for_agent(agent_name: str) -> BaseChatModel:
    """Create an LLM using per-agent overrides from config, or defaults."""
    overrides = settings.AGENT_LLM_OVERRIDES.get(agent_name, {})
    return create_llm(
        provider=overrides.get("provider"),
        model=overrides.get("model"),
        temperature=overrides.get("temperature"),
    )
