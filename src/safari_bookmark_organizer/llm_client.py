"""
LLM Client

Bookmark categorization via OpenAI-compatible APIs (OpenRouter, Ollama, vLLM).
Uses structured output (response_format) for reliable JSON responses.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger
from openai import APIError, OpenAI
from pydantic import BaseModel

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from .settings import LLMSettings


class CategoryResult(BaseModel):
    """Structured output for single bookmark categorization."""

    category: str


class BatchCategoryResult(BaseModel):
    """Structured output for batch bookmark categorization."""

    categories: list[str]


class LLMClient:
    """LLM-powered bookmark categorization via OpenAI-compatible API."""

    def __init__(self, settings: LLMSettings) -> None:
        self.settings = settings
        self._client = OpenAI(
            base_url=settings.base_url,
            api_key=settings.api_key or "unused",
        )

    def categorize(self, title: str, url: str, categories: Iterable[str]) -> str:
        """Categorize a single bookmark. Returns category string or 'uncategorized'."""
        cats = list(categories)
        try:
            response = self._client.beta.chat.completions.parse(
                model=self.settings.model,
                messages=[
                    {"role": "system", "content": self._system_prompt(cats)},
                    {"role": "user", "content": f"Title: {title}\nURL: {url}"},
                ],
                response_format=CategoryResult,
            )
        except APIError as exc:
            logger.warning("LLM API call failed: {}", exc)
            return "uncategorized"

        parsed = response.choices[0].message.parsed
        if parsed and parsed.category in cats:
            return parsed.category
        return "uncategorized"

    def categorize_many(
        self, bookmarks: Sequence[dict[str, str]], categories: Iterable[str]
    ) -> list[str]:
        """Categorize a batch of bookmarks. Returns list of category strings."""
        cats = list(categories)
        bookmark_text = "\n".join(
            f"{i + 1}. Title: {b['title']} | URL: {b['url']}" for i, b in enumerate(bookmarks)
        )
        try:
            response = self._client.beta.chat.completions.parse(
                model=self.settings.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._batch_system_prompt(cats, len(bookmarks)),
                    },
                    {"role": "user", "content": bookmark_text},
                ],
                response_format=BatchCategoryResult,
            )
        except APIError as exc:
            logger.warning("LLM API batch call failed: {}", exc)
            return []

        parsed = response.choices[0].message.parsed
        if parsed and len(parsed.categories) == len(bookmarks):
            return [c if c in cats else "uncategorized" for c in parsed.categories]
        return []

    def _system_prompt(self, categories: list[str]) -> str:
        cats = ", ".join(categories)
        return (
            f"You categorize bookmarks into exactly one of these categories: {cats}. "
            "Choose the single best-fitting category based on the title and URL."
        )

    def _batch_system_prompt(self, categories: list[str], count: int) -> str:
        cats = ", ".join(categories)
        return (
            f"You categorize bookmarks into exactly one of these categories: {cats}. "
            f"You will receive {count} bookmarks. Return exactly {count} categories, "
            "one per bookmark, in the same order."
        )
