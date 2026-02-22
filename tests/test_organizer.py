from __future__ import annotations

import plistlib
from typing import Any

import pytest

from safari_bookmark_organizer.organizer import BookmarkOrganizer


class TestBookmarkOrganizer:
    def test_load_and_parse(self, make_plist, sample_plist_data) -> None:
        path = make_plist(sample_plist_data)
        organizer = BookmarkOrganizer(str(path), use_llm=False)
        organizer.load_and_parse()

        assert organizer._bookmarks is not None
        all_bookmarks = organizer._collect_bookmarks()
        assert len(all_bookmarks) == 4

    def test_organize_dry_run(self, make_plist, sample_plist_data) -> None:
        path = make_plist(sample_plist_data)
        organizer = BookmarkOrganizer(str(path), use_llm=False)
        organizer.organize(dry_run=True)

        assert organizer.organized is not None

    def test_organize_creates_uncategorized_folder(self, make_plist, sample_plist_data) -> None:
        """Without LLM, all bookmarks land in Uncategorized."""
        path = make_plist(sample_plist_data)
        organizer = BookmarkOrganizer(str(path), use_llm=False)
        organizer.organize(dry_run=True)

        organized = organizer.organized
        assert organized is not None
        folder_titles = [c.title for c in organized.children if c.is_folder]
        assert "Uncategorized" in folder_titles

    def test_organize_preserves_original(self, make_plist, sample_plist_data) -> None:
        path = make_plist(sample_plist_data)
        organizer = BookmarkOrganizer(str(path), use_llm=False)
        organizer.load_and_parse()
        original_json = organizer.bookmarks.json()
        organizer.organize(dry_run=True)

        assert organizer.bookmarks.json() == original_json

    def test_save_organized(self, make_plist, sample_plist_data, tmp_path) -> None:
        path = make_plist(sample_plist_data)
        organizer = BookmarkOrganizer(str(path), use_llm=False)
        organizer.organize(dry_run=False)

        out = tmp_path / "organized.plist"
        organizer.save_organized(str(out))
        assert out.exists()

        with out.open("rb") as f:
            saved = plistlib.load(f)
        assert isinstance(saved, dict)
        assert "Children" in saved

    def test_get_organization_plan(self, make_plist, sample_plist_data) -> None:
        path = make_plist(sample_plist_data)
        organizer = BookmarkOrganizer(str(path), use_llm=False)
        plan = organizer.get_organization_plan()

        assert plan.total_bookmarks == 4
        assert isinstance(plan.categories, dict)
        assert isinstance(plan.folders_to_create, list)
        assert isinstance(plan.bookmarks_to_move, list)

    def test_backup_current(self, make_plist, sample_plist_data, tmp_path) -> None:
        path = make_plist(sample_plist_data)
        organizer = BookmarkOrganizer(str(path), use_llm=False)

        backup = tmp_path / "backup.plist"
        organizer.backup_current(str(backup))
        assert backup.exists()

        with backup.open("rb") as f:
            data = plistlib.load(f)
        assert "Children" in data

    def test_load_nonexistent_file(self) -> None:
        organizer = BookmarkOrganizer("/tmp/nope.plist", use_llm=False)
        with pytest.raises(FileNotFoundError):
            organizer.load_and_parse()

    def test_existing_taxonomy(self, make_plist) -> None:
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
        path = make_plist(data)
        organizer = BookmarkOrganizer(str(path), use_llm=False, taxonomy="existing")
        organizer.load_and_parse()

        cats = organizer.categorizer.opencode_categories
        assert "My Custom Folder" in cats
        assert "BookmarksBar" not in cats
        assert "uncategorized" in cats
