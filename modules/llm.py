from __future__ import annotations

from typing import Iterable

import os
import backoff
import openai
from langchain_core.messages import BaseMessage, MessageLikeRepresentation
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from modules.config import get_settings

def get_api_key() -> str:
    """
    Fetches the OpenAI API key, preferring the OPENAI_API_KEY environment variable,
    then falling back to config.toml ([app].openai_api_key).
    """
    env_key = os.getenv("OPENAI_API_KEY")
    if env_key:
        return env_key
    else:
        settings = get_settings()
        if settings.openai_api_key:
            return settings.openai_api_key
        
    raise RuntimeError(
        "OPENAI_API_KEY is required. Set it as an environment variable or in config.toml under [app]."
    )

def get_chat_model() -> ChatOpenAI:
    """ Initialize the chat model """
    settings = get_settings()
    api_key = get_api_key()
    return ChatOpenAI(
        model = settings.openai_model,
        api_key = api_key,
        temperature = 0.2,
        max_retries = 0,
    )

def get_embedding_model() -> OpenAIEmbeddings:
    """ Initializes the embedding model """
    settings = get_settings()
    api_key = get_api_key()
    return OpenAIEmbeddings(
        model = settings.openai_embedding_model,
        api_key= api_key
    )

@backoff.on_exception(backoff.expo,(openai.RateLimitError, openai.APIError),max_time =120,)
def invoke_with_retry(model: ChatOpenAI, messages: Iterable[BaseMessage],) -> BaseMessage:
    """ Invoke LLM with exponential backoff for 429 / arte - limit style errors """
    return model.invoke(list[MessageLikeRepresentation](messages))

def embed_documents_with_retry(embedder: OpenAIEmbeddings, texts: list[str]) -> list[list[float]]:
    @backoff.on_exception(backoff.expo, (openai.RateLimitError, openai.APIError), max_time=120,)
    def _inner(batch: list[str]) -> list[list[float]]:
        return embedder.embed_documents(batch)
    return _inner(texts)

