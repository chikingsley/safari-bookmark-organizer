import json
import plistlib
from pathlib import Path
from typing import Any

import pytest

from safari_bookmark_organizer.bookmark_parser import BookmarkParser


def _make_plist(tmp_path: Path, data: dict[str, Any]) -> Path:
    """Write a plist file and return its path."""
    p = tmp_path / "bookmarks.plist"
    with p.open("wb") as f:
        plistlib.dump(data, f)
    return p


def _minimal_plist() -> dict[str, Any]:
    """Minimal valid Safari bookmarks structure."""
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


class TestBookmarkParser:
    def test_load_valid_plist(self, tmp_path: Path) -> None:
        path = _make_plist(tmp_path, _minimal_plist())
        parser = BookmarkParser(str(path))
        data = parser.load()
        assert isinstance(data, dict)
        assert "Children" in data

    def test_load_nonexistent_file(self) -> None:
        parser = BookmarkParser("/tmp/does_not_exist.plist")
        with pytest.raises(FileNotFoundError):
            parser.load()

    def test_load_invalid_plist(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.plist"
        bad.write_text("not a plist", encoding="utf-8")
        parser = BookmarkParser(str(bad))
        with pytest.raises(Exception):  # noqa: B017
            parser.load()

    def test_parse_extracts_bookmarks_and_folders(self, tmp_path: Path) -> None:
        path = _make_plist(tmp_path, _minimal_plist())
        parser = BookmarkParser(str(path))
        parser.load()
        parser.parse()

        assert len(parser.bookmarks) == 2
        # Root node is also parsed as a folder, so we get root + "Tech"
        assert len(parser.folders) == 2

        # Verify bookmark fields
        assert parser.bookmarks[0]["title"] == "Example"
        assert parser.bookmarks[0]["url"] == "https://example.com"
        assert parser.bookmarks[0]["uuid"] == "AAA-111"

        # Nested bookmark has parent
        assert parser.bookmarks[1]["title"] == "My Repo"
        assert parser.bookmarks[1]["parent"] == "Tech"

        # The second folder is "Tech" (first is root)
        tech_folder = next(f for f in parser.folders if f["title"] == "Tech")
        assert tech_folder["uuid"] == "BBB-222"

    def test_parse_empty_children(self, tmp_path: Path) -> None:
        data: dict[str, Any] = {
            "WebBookmarkType": "WebBookmarkTypeList",
            "Title": "",
            "Children": [],
        }
        path = _make_plist(tmp_path, data)
        parser = BookmarkParser(str(path))
        parser.load()
        parser.parse()

        assert parser.bookmarks == []
        # Root node itself is parsed as a folder
        assert len(parser.folders) == 1
        assert parser.folders[0]["title"] == ""

    def test_parse_missing_title_defaults(self, tmp_path: Path) -> None:
        data: dict[str, Any] = {
            "WebBookmarkType": "WebBookmarkTypeList",
            "Title": "",
            "Children": [
                {
                    "WebBookmarkType": "WebBookmarkTypeLeaf",
                    "URLString": "https://notitle.com",
                    # No URIDictionary at all
                },
            ],
        }
        path = _make_plist(tmp_path, data)
        parser = BookmarkParser(str(path))
        parser.load()
        parser.parse()

        assert parser.bookmarks[0]["title"] == "Untitled"

    def test_parse_auto_loads(self, tmp_path: Path) -> None:
        """Calling parse() without load() should auto-load."""
        path = _make_plist(tmp_path, _minimal_plist())
        parser = BookmarkParser(str(path))
        parser.parse()  # should not raise
        assert len(parser.bookmarks) == 2

    def test_to_json(self, tmp_path: Path) -> None:
        path = _make_plist(tmp_path, _minimal_plist())
        parser = BookmarkParser(str(path))
        parser.load()
        parser.parse()

        result = json.loads(parser.to_json())
        assert "bookmarks" in result
        assert "folders" in result
        assert len(result["bookmarks"]) == 2

    def test_get_bookmarks_by_category(self, tmp_path: Path) -> None:
        path = _make_plist(tmp_path, _minimal_plist())
        parser = BookmarkParser(str(path))
        parser.load()
        parser.parse()

        categories = parser.get_bookmarks_by_category()
        assert "example.com" in categories
        assert "github.com" in categories

    def test_save_to_file(self, tmp_path: Path) -> None:
        path = _make_plist(tmp_path, _minimal_plist())
        parser = BookmarkParser(str(path))
        parser.load()
        parser.parse()

        out = tmp_path / "output.json"
        parser.save_to_file(str(out))
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert len(data["bookmarks"]) == 2
