"""
AI Categorizer

AI-powered categorization of bookmarks using OpenCode CLI.
This module handles the intelligent organization logic.
"""

from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING

from loguru import logger

from .opencode_client import OpenCodeClient
from .utils import extract_domain

if TYPE_CHECKING:
    from .types import BookmarkAnalysis, BookmarkItem, BookmarkNode, FolderNode, FolderStructure


class AICategorizer:
    """AI-powered bookmark categorization."""

    def __init__(self, use_opencode: bool | None = None, taxonomy: str = "default"):
        # Predefined categories and patterns
        self.categories: dict[str, dict[str, list[str]]] = {
            "work": {
                "patterns": [r"work", r"company", r"business", r"enterprise", r"corporate"],
                "domains": ["buildingconnected", "autodesk", "postman", "monday", "construction"],
            },
            "education": {
                "patterns": [r"course", r"learn", r"tutorial", r"university", r"school"],
                "domains": ["youtube.com/playlist", "docs.n8n", "maricopa.edu"],
            },
            "development": {
                "patterns": [r"api", r"developer", r"code", r"programming", r"docs"],
                "domains": ["github", "stackoverflow", "developer.apple", "docs.python"],
            },
            "personal": {
                "patterns": [r"personal", r"hobby", r"fun", r"guitar"],
                "domains": ["sixstringfingerpicking", "netflix", "spotify"],
            },
            "tools": {
                "patterns": [r"tool", r"service", r"utility", r"software"],
                "domains": ["postman", "figma", "canva", "notion"],
            },
        }
        self.taxonomy = taxonomy
        self.opencode_categories: list[str] = self._default_opencode_categories()
        self._opencode_client: OpenCodeClient | None = None
        opencode_enabled = (
            use_opencode
            if use_opencode is not None
            else os.getenv("OPENCODE_ENABLED", "").lower() in {"1", "true", "yes"}
        )
        if taxonomy == "opinionated":
            self.opencode_categories = [
                "work",
                "build",
                "learn",
                "tools",
                "reference",
                "personal",
                "uncategorized",
            ]
        if opencode_enabled:
            try:
                self._opencode_client = OpenCodeClient()
                logger.info("OpenCode client initialized")
            except Exception as exc:
                logger.warning("OpenCode client disabled: {}", exc)

    def set_opencode_categories(self, categories: list[str]) -> None:
        self.opencode_categories = categories

    def _default_opencode_categories(self) -> list[str]:
        return [*self.categories.keys(), "uncategorized"]

    def categorize_bookmark(self, bookmark: BookmarkItem) -> list[str]:
        """Categorize a single bookmark based on URL, title, and content."""
        url = bookmark["url"]
        title = bookmark["title"]

        # Combine text for analysis
        text = f"{title} {url}".lower()

        if self._opencode_client:
            oc_categories = self._opencode_client.categorize(title, url, self.opencode_categories)
            if oc_categories:
                category = oc_categories[0]
                if category in self.opencode_categories:
                    return [category]

        best_category = "uncategorized"
        best_score = 0

        # Rules-based scoring fallback
        for category, rules in self.categories.items():
            score = 0
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in rules["patterns"]):
                score += 2
            if any(domain in url.lower() for domain in rules["domains"]):
                score += 1
            if score > best_score:
                best_score = score
                best_category = category

        return [best_category] if best_score else ["uncategorized"]

    def categorize_all(self, bookmarks: list[BookmarkItem]) -> dict[str, list[BookmarkItem]]:
        """Categorize all bookmarks and return organized structure."""
        if self._opencode_client:
            return self._categorize_all_opencode(bookmarks)

        organized: dict[str, list[BookmarkItem]] = {}

        for bookmark in bookmarks:
            category = self.categorize_bookmark(bookmark)[0]
            organized.setdefault(category, []).append(bookmark)

        return organized

    def _categorize_all_opencode(
        self, bookmarks: list[BookmarkItem]
    ) -> dict[str, list[BookmarkItem]]:
        assert self._opencode_client is not None

        organized: dict[str, list[BookmarkItem]] = {}
        batch_size = int(os.getenv("OPENCODE_BATCH_SIZE", "50"))
        batch_size = max(1, min(batch_size, 200))

        for i in range(0, len(bookmarks), batch_size):
            chunk = bookmarks[i : i + batch_size]
            payload = [{"title": b["title"], "url": b["url"]} for b in chunk]

            categories = self._opencode_client.categorize_many(payload, self.opencode_categories)
            if len(categories) != len(chunk):
                logger.warning(
                    "OpenCode batch categorization failed (got {} for {}), falling back to rules",
                    len(categories),
                    len(chunk),
                )
                for bookmark in chunk:
                    category = self.categorize_bookmark(bookmark)[0]
                    organized.setdefault(category, []).append(bookmark)
                continue

            for bookmark, category in zip(chunk, categories, strict=True):
                if category not in self.opencode_categories:
                    category = "uncategorized"
                organized.setdefault(category, []).append(bookmark)

        return organized

    def suggest_folder_structure(
        self, categories: dict[str, list[BookmarkItem]]
    ) -> FolderStructure:
        """Suggest an optimal folder structure based on categorized bookmarks."""
        structure: FolderStructure = {"name": "Bookmarks", "children": []}

        # Create folders for each category
        for category, bookmarks in categories.items():
            if len(bookmarks) > 1:  # Only create folder if multiple bookmarks
                folder: FolderNode = {
                    "name": category.capitalize(),
                    "type": "folder",
                    "children": [],
                }

                # Add bookmarks to folder
                for bookmark in bookmarks:
                    node: BookmarkNode = {
                        "name": bookmark["title"],
                        "url": bookmark["url"],
                        "type": "bookmark",
                    }
                    folder["children"].append(node)

                structure["children"].append(folder)

        return structure

    def analyze_bookmark_content(self, bookmark: BookmarkItem) -> BookmarkAnalysis:
        """Analyze bookmark content and suggest tags/keywords."""
        # This would be enhanced with actual AI/ML analysis
        analysis: BookmarkAnalysis = {"keywords": [], "tags": [], "confidence": 0.0}

        url = bookmark["url"]
        title = bookmark["title"]

        # Simple keyword extraction
        text = f"{title} {url}"

        # Extract potential keywords
        potential_keywords = [
            "api",
            "documentation",
            "tutorial",
            "course",
            "tool",
            "service",
            "platform",
            "software",
            "development",
            "learning",
        ]

        for keyword in potential_keywords:
            if keyword.lower() in text.lower():
                analysis["keywords"].append(keyword)

        # Simple tagging based on domain
        domain = extract_domain(url)
        if domain:
            analysis["tags"].append(domain)

        analysis["confidence"] = min(0.9, len(analysis["keywords"]) * 0.1)

        return analysis
