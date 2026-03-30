from langchain_openai import ChatOpenAI

from jarvis.config import settings


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.7,
    )
