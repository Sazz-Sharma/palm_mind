from __future__ import annotations

import os
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings
from loguru import logger


class Settings(BaseSettings):
    app_env: str = Field("dev", alias="APP_ENV")
    app_name: str = Field("palm_mind_rag", alias="APP_NAME")
    api_prefix: str = Field("/api", alias="API_PREFIX")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    host: str = Field("0.0.0.0", alias="HOST")
    port: int = Field(8000, alias="PORT")

    groq_api_key: str = Field("", alias="GROQ_API_KEY")
    groq_model: str = Field("llama-3.3-70b-versatile", alias="GROQ_MODEL")

    pinecone_api_key: str = Field("", alias="PINECONE_API_KEY")
    pinecone_index_name: str = Field("", alias="PINECONE_INDEX_NAME")
    pinecone_host: str | None = Field(None, alias="PINECONE_HOST")
    pinecone_embedding_model: str | None = Field(None, alias="PINECONE_EMBEDDING_MODEL")

    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")

    database_url: str = Field("sqlite:///./app.db", alias="DATABASE_URL")

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    logger.remove()
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=settings.log_level.upper(),
        colorize=True,
        backtrace=False,
        diagnose=False,
    )
    logger.debug(f"Loaded settings for env={settings.app_env}")
    return settings