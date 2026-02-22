from __future__ import annotations

import plistlib
from pathlib import Path
from typing import Any

import pytest

from safari_bookmark_organizer.models import WebBookmarkTypeLeaf
from safari_bookmark_organizer.safari_io import SafariBookmarkItem


@pytest.fixture()
def make_plist(tmp_path: Path):
    """Factory fixture that writes plist data to a temp file and returns its path."""

    def _make(data: dict[str, Any], filename: str = "bookmarks.plist") -> Path:
        p = tmp_path / filename
        with p.open("wb") as f:
            plistlib.dump(data, f, fmt=plistlib.FMT_BINARY)
        return p

    return _make


@pytest.fixture()
def minimal_plist_data() -> dict[str, Any]:
    """Minimal valid Safari bookmarks structure (1 root bookmark + 1 folder with 1 child)."""
    return {
        "WebBookmarkType": "WebBookmarkTypeList",
        "Title": "",
        "Children": [
            {
                "WebBookmarkType": "WebBookmarkTypeLeaf",
                "URLString": "https://example.com",
                "URIDictionary": {"title": "Example"},
                "WebBookmarkUUID": "AAA-111",
            },
            {
                "WebBookmarkType": "WebBookmarkTypeList",
                "Title": "Tech",
                "WebBookmarkUUID": "BBB-222",
                "Children": [
                    {
                        "WebBookmarkType": "WebBookmarkTypeLeaf",
                        "URLString": "https://github.com/user/repo",
                        "URIDictionary": {"title": "My Repo"},
                        "WebBookmarkUUID": "CCC-333",
                    },
                ],
            },
        ],
    }


@pytest.fixture()
def sample_plist_data() -> dict[str, Any]:
    """Plist with 4 bookmarks across domains — enough to trigger folder creation (>=2 per category)."""
    return {
        "WebBookmarkType": "WebBookmarkTypeList",
        "Title": "",
        "Children": [
            {
                "WebBookmarkType": "WebBookmarkTypeLeaf",
                "URLString": "https://github.com/user/repo1",
                "URIDictionary": {"title": "Repo 1"},
            },
            {
                "WebBookmarkType": "WebBookmarkTypeLeaf",
                "URLString": "https://github.com/user/repo2",
                "URIDictionary": {"title": "Repo 2"},
            },
            {
                "WebBookmarkType": "WebBookmarkTypeLeaf",
                "URLString": "https://stackoverflow.com/q/123",
                "URIDictionary": {"title": "SO Question"},
            },
            {
                "WebBookmarkType": "WebBookmarkTypeLeaf",
                "URLString": "https://randomsite.com",
                "URIDictionary": {"title": "Random"},
            },
        ],
    }


def make_bookmark(title: str, url: str) -> SafariBookmarkItem:
    """Create a minimal SafariBookmarkItem for testing."""
    # ty: populate_by_name=True lets Pydantic accept snake_case names,
    # but ty only sees the PascalCase aliases as valid parameters.
    return SafariBookmarkItem(WebBookmarkTypeLeaf(url_string=url, uri_dictionary={"title": title}))  # ty: ignore[missing-argument]
