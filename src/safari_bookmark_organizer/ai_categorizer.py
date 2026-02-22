"""
AI Categorizer

AI-powered categorization of bookmarks using LLM APIs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from .llm_client import LLMClient
from .settings import LLMSettings
from .types import BookmarkNode, FolderNode, FolderStructure

if TYPE_CHECKING:
    from .safari_io import SafariBookmarkItem

DEFAULT_CATEGORIES = [
    "work",
    "education",
    "development",
    "personal",
    "tools",
    "uncategorized",
]

OPINIONATED_CATEGORIES = [
    "work",
    "build",
    "learn",
    "tools",
    "reference",
    "personal",
    "uncategorized",
]


class AICategorizer:
    """AI-powered bookmark categorization via LLM API."""

    def __init__(
        self,
        *,
        use_llm: bool | None = None,
        taxonomy: str = "default",
        settings: LLMSettings | None = None,
    ):
        self._settings = settings or LLMSettings()
        self.taxonomy = taxonomy
        self.opencode_categories: list[str] = list(DEFAULT_CATEGORIES)
        self._llm_client: LLMClient | None = None

        if taxonomy == "opinionated":
            self.opencode_categories = list(OPINIONATED_CATEGORIES)

        llm_enabled = use_llm if use_llm is not None else self._settings.enabled
        if llm_enabled:
            try:
                self._llm_client = LLMClient(settings=self._settings)
                logger.info("LLM client initialized")
            except Exception as exc:
                logger.warning("LLM client disabled: {}", exc)

    def set_opencode_categories(self, categories: list[str]) -> None:
        self.opencode_categories = categories

    def categorize_bookmark(self, bookmark: SafariBookmarkItem) -> str:
        """Categorize a single bookmark. Returns 'uncategorized' if LLM is unavailable."""
        if self._llm_client:
            category = self._llm_client.categorize(
                bookmark.title, bookmark.url, self.opencode_categories
            )
            if category in self.opencode_categories:
                return category

        return "uncategorized"

    def categorize_all(
        self, bookmarks: list[SafariBookmarkItem]
    ) -> dict[str, list[SafariBookmarkItem]]:
        """Categorize all bookmarks and return organized structure."""
        if self._llm_client:
            return self._categorize_all_llm(bookmarks)

        return {"uncategorized": list(bookmarks)}

    def _categorize_all_llm(
        self, bookmarks: list[SafariBookmarkItem]
    ) -> dict[str, list[SafariBookmarkItem]]:
        if self._llm_client is None:
            raise RuntimeError("LLM client is not initialized")

        organized: dict[str, list[SafariBookmarkItem]] = {}
        batch_size = self._settings.batch_size

        for i in range(0, len(bookmarks), batch_size):
            chunk = bookmarks[i : i + batch_size]
            payload = [{"title": b.title, "url": b.url} for b in chunk]

            categories = self._llm_client.categorize_many(payload, self.opencode_categories)
            if len(categories) != len(chunk):
                logger.warning(
                    "LLM batch failed (got {} for {}), marking chunk as uncategorized",
                    len(categories),
                    len(chunk),
                )
                organized.setdefault("uncategorized", []).extend(chunk)
                continue

            for bookmark, category in zip(chunk, categories, strict=True):
                resolved = category if category in self.opencode_categories else "uncategorized"
                organized.setdefault(resolved, []).append(bookmark)

        return organized

    def suggest_folder_structure(
        self, categories: dict[str, list[SafariBookmarkItem]]
    ) -> FolderStructure:
        """Suggest an optimal folder structure based on categorized bookmarks."""
        children: list[BookmarkNode | FolderNode] = []

        for category, bookmarks in categories.items():
            if len(bookmarks) > 1:
                folder_children: list[BookmarkNode | FolderNode] = [
                    BookmarkNode(name=bookmark.title, url=bookmark.url) for bookmark in bookmarks
                ]
                children.append(FolderNode(name=category.capitalize(), children=folder_children))

        return FolderStructure(name="Bookmarks", children=children)
