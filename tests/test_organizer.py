import plistlib
from pathlib import Path
from typing import Any

import pytest

from safari_bookmark_organizer.organizer import BookmarkOrganizer


def _make_plist(tmp_path: Path, data: dict[str, Any]) -> Path:
    p = tmp_path / "bookmarks.plist"
    with p.open("wb") as f:
        plistlib.dump(data, f)
    return p


def _sample_plist() -> dict[str, Any]:
    """Plist with enough bookmarks to trigger folder creation (>=2 per category)."""
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


class TestBookmarkOrganizer:
    def test_load_and_parse(self, tmp_path: Path) -> None:
        path = _make_plist(tmp_path, _sample_plist())
        organizer = BookmarkOrganizer(str(path), use_opencode=False)
        organizer.load_and_parse()

        assert organizer.original_data is not None
        assert len(organizer.parser.bookmarks) == 4

    def test_organize_dry_run(self, tmp_path: Path) -> None:
        path = _make_plist(tmp_path, _sample_plist())
        organizer = BookmarkOrganizer(str(path), use_opencode=False)
        result = organizer.organize(dry_run=True)

        assert isinstance(result, dict)
        assert "Children" in result

    def test_organize_creates_category_folders(self, tmp_path: Path) -> None:
        path = _make_plist(tmp_path, _sample_plist())
        organizer = BookmarkOrganizer(str(path), use_opencode=False)
        result = organizer.organize(dry_run=True)

        children = result["Children"]
        folder_titles = [
            c.get("Title")
            for c in children
            if c.get("WebBookmarkType") == "WebBookmarkTypeList"
        ]
        # "development" category has 3 bookmarks -> should create a "Development" folder
        assert "Development" in folder_titles

    def test_organize_preserves_original(self, tmp_path: Path) -> None:
        path = _make_plist(tmp_path, _sample_plist())
        organizer = BookmarkOrganizer(str(path), use_opencode=False)
        organizer.load_and_parse()
        original_copy = organizer.original_data.copy()  # type: ignore[union-attr]
        organizer.organize(dry_run=True)

        # original_data should not be mutated
        assert organizer.original_data == original_copy

    def test_save_organized(self, tmp_path: Path) -> None:
        path = _make_plist(tmp_path, _sample_plist())
        organizer = BookmarkOrganizer(str(path), use_opencode=False)
        organizer.organize(dry_run=False)

        out = tmp_path / "organized.plist"
        organizer.save_organized(str(out))
        assert out.exists()

        with out.open("rb") as f:
            saved = plistlib.load(f)
        assert isinstance(saved, dict)
        assert "Children" in saved

    def test_get_organization_plan(self, tmp_path: Path) -> None:
        path = _make_plist(tmp_path, _sample_plist())
        organizer = BookmarkOrganizer(str(path), use_opencode=False)
        plan = organizer.get_organization_plan()

        assert plan["total_bookmarks"] == 4
        assert isinstance(plan["categories"], dict)
        assert isinstance(plan["folders_to_create"], list)
        assert isinstance(plan["bookmarks_to_move"], list)

    def test_backup_current(self, tmp_path: Path) -> None:
        path = _make_plist(tmp_path, _sample_plist())
        organizer = BookmarkOrganizer(str(path), use_opencode=False)

        backup = tmp_path / "backup.plist"
        organizer.backup_current(str(backup))
        assert backup.exists()

        with backup.open("rb") as f:
            data = plistlib.load(f)
        assert "Children" in data

    def test_load_nonexistent_file(self) -> None:
        organizer = BookmarkOrganizer("/tmp/nope.plist", use_opencode=False)
        with pytest.raises(FileNotFoundError):
            organizer.load_and_parse()

    def test_existing_taxonomy(self, tmp_path: Path) -> None:
        data: dict[str, Any] = {
            "WebBookmarkType": "WebBookmarkTypeList",
            "Title": "",
            "Children": [
                {
                    "WebBookmarkType": "WebBookmarkTypeList",
                    "Title": "BookmarksBar",
                    "Children": [],
                },
                {
                    "WebBookmarkType": "WebBookmarkTypeList",
                    "Title": "My Custom Folder",
                    "Children": [],
                },
            ],
        }
        path = _make_plist(tmp_path, data)
        organizer = BookmarkOrganizer(str(path), use_opencode=False, taxonomy="existing")
        organizer.load_and_parse()

        # BookmarksBar should be excluded, My Custom Folder should be included
        cats = organizer.categorizer.opencode_categories
        assert "My Custom Folder" in cats
        assert "BookmarksBar" not in cats
        assert "uncategorized" in cats
