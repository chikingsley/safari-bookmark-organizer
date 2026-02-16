"""
Bookmark Organizer

Main organization logic that combines parsing and AI categorization
to create an organized bookmark structure.
"""

from __future__ import annotations

import copy
import plistlib
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from loguru import logger

from .ai_categorizer import AICategorizer
from .bookmark_parser import BookmarkParser

if TYPE_CHECKING:
    from .types import BookmarkItem, OrganizationPlan


class BookmarkOrganizer:
    """Main bookmark organization class."""

    def __init__(
        self,
        file_path: str | None = None,
        use_opencode: bool | None = None,
        taxonomy: str = "default",
    ):
        self.file_path = file_path or "~/Library/Safari/Bookmarks.plist"
        self.parser = BookmarkParser(file_path)
        self.taxonomy = taxonomy
        self.categorizer = AICategorizer(use_opencode=use_opencode, taxonomy=taxonomy)
        self.original_data: dict[str, Any] | None = None
        self.organized_data: dict[str, Any] | None = None

    def _existing_taxonomy(self) -> list[str]:
        deny = {
            "BookmarksBar",
            "BookmarksMenu",
            "ReadingList",
            "Favorites",
        }
        titles = {
            folder["title"].strip()
            for folder in self.parser.folders
            if folder.get("title") and folder["title"].strip() not in deny
        }
        categories = sorted(titles)
        if "uncategorized" not in categories:
            categories.append("uncategorized")
        return categories

    def load_and_parse(self) -> None:
        """Load and parse the bookmarks file."""
        self.parser.load()
        self.parser.parse()
        if self.taxonomy == "existing":
            self.categorizer.set_opencode_categories(self._existing_taxonomy())
        if self.parser.data is None:
            raise RuntimeError("Bookmark parser did not load any data")
        self.original_data = copy.deepcopy(self.parser.data)
        logger.info("Loaded and parsed bookmarks")

    def organize(self, dry_run: bool = True) -> dict[str, Any]:
        """Organize bookmarks using AI categorization."""
        if not self.parser.bookmarks:
            self.load_and_parse()
        if self.original_data is None:
            raise RuntimeError("Original bookmark data not loaded")

        # Categorize bookmarks
        categorized = self.categorizer.categorize_all(self.parser.bookmarks)
        logger.info(f"Categorized bookmarks into {len(categorized)} categories")

        # Create organized structure
        self.organized_data = self._create_organized_structure(categorized)

        if dry_run:
            logger.info("Dry run completed - no changes made")
        else:
            logger.info("Organization completed")

        return self.organized_data

    def _create_organized_structure(
        self, categories: dict[str, list[BookmarkItem]]
    ) -> dict[str, Any]:
        """Create the organized bookmark structure by moving items into category folders."""
        if self.original_data is None:
            raise RuntimeError("Original bookmark data not loaded")
        organized: dict[str, Any] = copy.deepcopy(self.original_data)

        # Index original children for removal tracking
        children_any = organized.get("Children")
        if isinstance(children_any, list):
            root_children: list[dict[str, Any]] = [
                cast("dict[str, Any]", child)
                for child in cast("list[Any]", children_any)
                if isinstance(child, dict)
            ]
        else:
            root_children = []
        organized["Children"] = root_children

        # Only move bookmarks that belong to categories with 2+ items
        movable_categories = {
            category: bookmarks for category, bookmarks in categories.items() if len(bookmarks) >= 2
        }

        move_targets = {
            (b["title"], b["url"]) for bucket in movable_categories.values() for b in bucket
        }

        category_folders = {
            category: self._create_category_folder(category, bookmarks)
            for category, bookmarks in movable_categories.items()
        }

        # Remove bookmarks that will be relocated
        def should_move(item: dict[str, Any]) -> bool:
            return (
                item.get("WebBookmarkType") == "WebBookmarkTypeLeaf"
                and (item.get("URIDictionary", {}).get("title"), item.get("URLString"))
                in move_targets
            )

        root_children[:] = [child for child in root_children if not should_move(child)]

        # Append new folders with relocated bookmarks
        root_children.extend(category_folders.values())

        return organized

    def _create_category_folder(
        self, category_name: str, bookmarks: list[BookmarkItem]
    ) -> dict[str, Any]:
        """Create a folder structure for a category."""
        children: list[dict[str, Any]] = []
        folder = {
            "WebBookmarkType": "WebBookmarkTypeList",
            "Title": category_name.capitalize(),
            "Children": children,
            "URIDictionary": {"title": category_name.capitalize()},
        }

        # Add bookmarks to folder
        for bookmark in bookmarks:
            folder_bookmark = {
                "WebBookmarkType": "WebBookmarkTypeLeaf",
                "Title": bookmark["title"],
                "URLString": bookmark["url"],
                "URIDictionary": {"title": bookmark["title"]},
            }
            children.append(folder_bookmark)

        return folder

    def save_organized(self, output_path: str | None = None) -> None:
        """Save the organized bookmarks to a file."""
        if self.organized_data is None:
            self.organize(dry_run=False)
        assert self.organized_data is not None

        output_path = output_path or "organized_bookmarks.plist"
        expanded_path = Path(output_path).expanduser()

        with expanded_path.open("wb") as f:
            plistlib.dump(self.organized_data, f)

        logger.info(f"Saved organized bookmarks to {expanded_path}")

    def get_organization_plan(self) -> OrganizationPlan:
        """Get a plan of how bookmarks will be organized."""
        if not self.parser.bookmarks:
            self.load_and_parse()

        # Categorize bookmarks
        categorized = self.categorizer.categorize_all(self.parser.bookmarks)

        # Create organization plan
        plan: OrganizationPlan = {
            "total_bookmarks": len(self.parser.bookmarks),
            "categories": {},
            "folders_to_create": [],
            "bookmarks_to_move": [],
        }

        for category, bookmarks in categorized.items():
            plan["categories"][category] = len(bookmarks)

            if len(bookmarks) >= 2:
                plan["folders_to_create"].append(category)

                for bookmark in bookmarks:
                    parent = bookmark.get("parent")
                    from_folder = parent if isinstance(parent, str) and parent else "Root"
                    plan["bookmarks_to_move"].append(
                        {
                            "title": bookmark["title"],
                            "from": from_folder,
                            "to": category,
                        }
                    )

        return plan

    def preview_changes(self) -> None:
        """Preview what changes will be made."""
        plan = self.get_organization_plan()

        print("📊 Organization Plan Preview:")
        print(f"Total bookmarks: {plan['total_bookmarks']}")
        print(f"Categories found: {len(plan['categories'])}")
        print(f"Folders to create: {len(plan['folders_to_create'])}")
        print(f"Bookmarks to move: {len(plan['bookmarks_to_move'])}")

        print("\n📁 Categories:")
        for category, count in plan["categories"].items():
            print(f"  {category}: {count} bookmarks")

        print("\n📂 Folders to create:")
        for folder in plan["folders_to_create"]:
            print(f"  • {folder.capitalize()}")

        print("\n🔄 Sample moves (first 5):")
        for move in plan["bookmarks_to_move"][:5]:
            print(f"  '{move['title']}' from {move['from']} → {move['to']}")

    def backup_current(self, backup_path: str | None = None) -> None:
        """Create a backup of current bookmarks."""
        backup_path = backup_path or "bookmarks_backup_before_organization.plist"
        expanded_path = Path(backup_path).expanduser()

        if self.original_data is None:
            self.load_and_parse()
        assert self.original_data is not None

        with expanded_path.open("wb") as f:
            plistlib.dump(self.original_data, f)

        logger.info(f"Created backup at {expanded_path}")
