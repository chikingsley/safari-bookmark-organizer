"""
Bookmark Parser

Parse Safari's binary PLIST bookmark format and extract structured data.
"""

from __future__ import annotations

import json
import plistlib
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from loguru import logger

from .utils import extract_domain

if TYPE_CHECKING:
    from .types import BookmarkItem, FolderItem


class BookmarkParser:
    """Parse and extract data from Safari bookmarks.plist file."""

    def __init__(self, file_path: str | None = None):
        self.file_path = file_path or "~/Library/Safari/Bookmarks.plist"
        self.data: dict[str, Any] | None = None
        self.bookmarks: list[BookmarkItem] = []
        self.folders: list[FolderItem] = []

    def load(self) -> dict[str, Any]:
        """Load and parse the bookmarks.plist file."""
        try:
            expanded_path = Path(self.file_path).expanduser()
            with expanded_path.open("rb") as f:
                data = plistlib.load(f)
            if not isinstance(data, dict):
                raise ValueError("Expected Safari bookmarks plist root to be a dict")
            self.data = data
            logger.info(f"Loaded bookmarks from {expanded_path}")
            return self.data
        except Exception as e:
            logger.error(f"Failed to load bookmarks: {e}")
            raise

    def parse(self) -> None:
        """Parse the loaded bookmark data into structured format."""
        if self.data is None:
            self.load()

        # Extract bookmarks and folders
        assert self.data is not None
        self._extract_items(self.data)
        logger.info(f"Found {len(self.bookmarks)} bookmarks and {len(self.folders)} folders")

    def _extract_items(self, data: Any, parent: str | None = None) -> None:
        """Recursively extract bookmarks and folders."""
        if not isinstance(data, dict):
            return
        data = cast("dict[str, Any]", data)

        # Handle different bookmark types
        bookmark_type = data.get("WebBookmarkType")
        if not isinstance(bookmark_type, str):
            return

        if bookmark_type == "WebBookmarkTypeLeaf":
            uri_dict = data.get("URIDictionary")
            title = "Untitled"
            if isinstance(uri_dict, dict):
                title_value = cast("dict[str, Any]", uri_dict).get("title")
                if isinstance(title_value, str):
                    title = title_value
            url_value = data.get("URLString")
            url = url_value if isinstance(url_value, str) else ""
            uuid_value = data.get("WebBookmarkUUID")
            uuid = uuid_value if isinstance(uuid_value, str) else None
            bookmark: BookmarkItem = {
                "title": title,
                "url": url,
                "type": "bookmark",
                "parent": parent,
                "uuid": uuid,
            }
            self.bookmarks.append(bookmark)

        elif bookmark_type == "WebBookmarkTypeList":
            title_value = data.get("Title")
            title = title_value if isinstance(title_value, str) else "Untitled Folder"
            uuid_value = data.get("WebBookmarkUUID")
            uuid = uuid_value if isinstance(uuid_value, str) else None
            folder: FolderItem = {
                "title": title,
                "type": "folder",
                "parent": parent,
                "uuid": uuid,
                "children": [],
            }
            self.folders.append(folder)

            children = data.get("Children")
            if isinstance(children, list):
                for child in cast("list[Any]", children):
                    self._extract_items(child, title)

    def to_json(self) -> str:
        """Convert parsed data to JSON format."""
        return json.dumps({"bookmarks": self.bookmarks, "folders": self.folders}, indent=2)

    def get_bookmarks_by_category(self) -> dict[str, list[BookmarkItem]]:
        """Categorize bookmarks by domain/type."""
        categories: dict[str, list[BookmarkItem]] = {}

        for bookmark in self.bookmarks:
            if not bookmark["url"]:
                continue

            # Simple domain-based categorization
            domain = extract_domain(bookmark["url"])
            if domain not in categories:
                categories[domain] = []
            categories[domain].append(bookmark)

        return categories

    def save_to_file(self, output_path: str) -> None:
        """Save parsed data to JSON file."""
        path = Path(output_path).expanduser()
        path.write_text(self.to_json(), encoding="utf-8")
        logger.info(f"Saved parsed bookmarks to {path}")
