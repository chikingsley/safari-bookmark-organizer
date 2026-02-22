"""
Settings

Centralized configuration using Pydantic Settings.
Reads from environment variables (prefixed with LLM_) and .env files.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """Configuration for LLM API integration (OpenRouter, Ollama, vLLM, etc.)."""

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: str | None = Field(default=None)
    base_url: str = Field(default="https://openrouter.ai/api/v1")
    model: str = Field(default="openai/gpt-4o-mini")
    enabled: bool = Field(default=False)
    batch_size: int = Field(default=25, ge=1, le=100)
