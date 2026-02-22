"""
Bookmark Organizer

Main organization logic that combines parsing and AI categorization
to create an organized bookmark structure.
"""

from __future__ import annotations

import plistlib
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from .ai_categorizer import AICategorizer
from .models import WebBookmarkTypeList
from .safari_io import SafariBookmarkItem, SafariBookmarks
from .types import BookmarkMove, OrganizationPlan

if TYPE_CHECKING:
    from .settings import LLMSettings


class BookmarkOrganizer:
    """Main bookmark organization class."""

    def __init__(
        self,
        file_path: str | None = None,
        *,
        use_llm: bool | None = None,
        taxonomy: str = "default",
        settings: LLMSettings | None = None,
    ):
        self.file_path = file_path or "~/Library/Safari/Bookmarks.plist"
        self.taxonomy = taxonomy
        self.categorizer = AICategorizer(
            use_llm=use_llm, taxonomy=taxonomy, settings=settings
        )
        self._bookmarks: SafariBookmarks | None = None
        self._organized: SafariBookmarks | None = None

    @property
    def bookmarks(self) -> SafariBookmarks:
        if self._bookmarks is None:
            raise RuntimeError("Not loaded; call load_and_parse() first")
        return self._bookmarks

    @property
    def organized(self) -> SafariBookmarks | None:
        return self._organized

    def _collect_bookmarks(self) -> list[SafariBookmarkItem]:
        """Walk tree and collect all leaf bookmarks."""
        result: list[SafariBookmarkItem] = []

        def _walk(item: SafariBookmarkItem) -> None:
            if item.is_bookmark:
                result.append(item)
            for child in item.children:
                _walk(child)

        _walk(self.bookmarks)
        return result

    def _copy_bookmarks_tree(self) -> SafariBookmarks:
        """Create a deep copy of the bookmarks tree by serializing/deserializing."""
        data = self.bookmarks._node.model_dump(by_alias=True)
        return SafariBookmarks(WebBookmarkTypeList.model_validate(data))

    def _existing_taxonomy(self) -> list[str]:
        deny = {
            "BookmarksBar",
            "BookmarksMenu",
            "ReadingList",
            "Favorites",
        }
        titles: set[str] = set()

        def _walk(item: SafariBookmarkItem) -> None:
            if item.is_folder and item.title.strip() and item.title.strip() not in deny:
                titles.add(item.title.strip())
            for child in item.children:
                _walk(child)

        _walk(self.bookmarks)
        categories = sorted(titles)
        if "uncategorized" not in categories:
            categories.append("uncategorized")
        return categories

    def load_and_parse(self) -> None:
        """Load and parse the bookmarks file."""
        path = Path(self.file_path).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"Bookmarks file not found: {path}")

        with path.open("rb") as f:
            data = plistlib.load(f)
        self._bookmarks = SafariBookmarks(WebBookmarkTypeList.model_validate(data))
        self._bookmarks._path = path

        if self.taxonomy == "existing":
            self.categorizer.set_opencode_categories(self._existing_taxonomy())
        logger.info("Loaded and parsed bookmarks")

    def organize(self, *, dry_run: bool = True) -> None:
        """Organize bookmarks using AI categorization."""
        if self._bookmarks is None:
            self.load_and_parse()

        all_bookmarks = self._collect_bookmarks()
        categorized = self.categorizer.categorize_all(all_bookmarks)
        logger.info(f"Categorized bookmarks into {len(categorized)} categories")

        self._organized = self._create_organized_structure(categorized)

        if dry_run:
            logger.info("Dry run completed - no changes made")
        else:
            logger.info("Organization completed")

    def _create_organized_structure(
        self, categories: dict[str, list[SafariBookmarkItem]]
    ) -> SafariBookmarks:
        """Create the organized bookmark structure by moving items into category folders."""
        organized = self._copy_bookmarks_tree()

        # Only move bookmarks that belong to categories with 2+ items
        movable_categories = {
            category: bookmarks for category, bookmarks in categories.items() if len(bookmarks) >= 2
        }

        move_uuids = {bm.id for bucket in movable_categories.values() for bm in bucket}

        # Remove matching bookmarks from root level
        to_remove = [
            child._node
            for child in organized.children
            if child.is_bookmark and child.id in move_uuids
        ]
        root = organized._node
        if not isinstance(root, WebBookmarkTypeList):
            raise TypeError("Expected WebBookmarkTypeList root node")
        for node in to_remove:
            # ty: _node is typed as base WebBookmarkType but is always a concrete
            # subclass (Leaf/List/Proxy) matching ChildrenType at runtime.
            root.children.remove(node)  # ty: ignore[invalid-argument-type]

        # Create category folders with relocated bookmarks
        for category, bookmarks in movable_categories.items():
            folder = organized.add_folder(category.capitalize())
            for bm in bookmarks:
                folder.add_bookmark(bm.url, title=bm.title)

        return organized

    def save_organized(self, output_path: str | None = None) -> None:
        """Save the organized bookmarks to a file."""
        if self._organized is None:
            self.organize(dry_run=False)
        if self._organized is None:
            raise RuntimeError("Organization produced no data")

        output_path = output_path or "organized_bookmarks.plist"
        expanded_path = Path(output_path).expanduser()
        self._organized.save(expanded_path)
        logger.info(f"Saved organized bookmarks to {expanded_path}")

    def get_organization_plan(self) -> OrganizationPlan:
        """Get a plan of how bookmarks will be organized."""
        if self._bookmarks is None:
            self.load_and_parse()

        all_bookmarks = self._collect_bookmarks()
        categorized = self.categorizer.categorize_all(all_bookmarks)

        plan = OrganizationPlan(total_bookmarks=len(all_bookmarks))

        for category, bookmarks in categorized.items():
            plan.categories[category] = len(bookmarks)

            if len(bookmarks) >= 2:
                plan.folders_to_create.append(category)

                for bookmark in bookmarks:
                    parent = bookmark.parent
                    from_folder = parent.title if parent and parent.title else "Root"
                    plan.bookmarks_to_move.append(
                        BookmarkMove(
                            title=bookmark.title,
                            from_folder=from_folder,
                            to_folder=category,
                        )
                    )

        return plan

    def preview_changes(self) -> None:
        """Preview what changes will be made."""
        plan = self.get_organization_plan()

        print("Organization Plan Preview:")
        print(f"Total bookmarks: {plan.total_bookmarks}")
        print(f"Categories found: {len(plan.categories)}")
        print(f"Folders to create: {len(plan.folders_to_create)}")
        print(f"Bookmarks to move: {len(plan.bookmarks_to_move)}")

        print("\nCategories:")
        for category, count in plan.categories.items():
            print(f"  {category}: {count} bookmarks")

        print("\nFolders to create:")
        for folder in plan.folders_to_create:
            print(f"  - {folder.capitalize()}")

        print("\nSample moves (first 5):")
        for move in plan.bookmarks_to_move[:5]:
            print(f"  '{move.title}' from {move.from_folder} -> {move.to_folder}")

    def backup_current(self, backup_path: str | None = None) -> None:
        """Create a backup of current bookmarks."""
        if self._bookmarks is None:
            self.load_and_parse()

        backup_path = backup_path or "bookmarks_backup_before_organization.plist"
        expanded_path = Path(backup_path).expanduser()
        self.bookmarks.save(expanded_path)
        logger.info(f"Created backup at {expanded_path}")
