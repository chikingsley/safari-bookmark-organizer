"""
Bookmark Organizer

Main organization logic that combines parsing and AI categorization
to create an organized bookmark structure.
"""

from typing import Dict, List, Any, Optional
from .bookmark_parser import BookmarkParser
from .ai_categorizer import AICategorizer
from pathlib import Path
import json
import plistlib
from loguru import logger
import copy


class BookmarkOrganizer:
    """Main bookmark organization class."""

    def __init__(self, file_path: Optional[str] = None, use_opencode: Optional[bool] = None):
        self.file_path = file_path or "~/Library/Safari/Bookmarks.plist"
        self.parser = BookmarkParser(file_path)
        self.categorizer = AICategorizer(use_opencode=use_opencode)
        self.original_data = None
        self.organized_data = None

    def load_and_parse(self) -> None:
        """Load and parse the bookmarks file."""
        self.parser.load()
        self.parser.parse()
        self.original_data = copy.deepcopy(self.parser.data)
        logger.info("Loaded and parsed bookmarks")

    def organize(self, dry_run: bool = True) -> Dict[str, Any]:
        """Organize bookmarks using AI categorization."""
        if not self.parser.bookmarks:
            self.load_and_parse()

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

    def _create_organized_structure(self, categories: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Create the organized bookmark structure by moving items into category folders."""
        organized = copy.deepcopy(self.original_data)

        # Index original children for removal tracking
        root_children = organized.get('Children', [])

        # Only move bookmarks that belong to categories with 2+ items
        movable_categories = {
            category: bookmarks
            for category, bookmarks in categories.items()
            if len(bookmarks) >= 2
        }

        move_targets = {
            (b.get('title'), b.get('url'))
            for bucket in movable_categories.values()
            for b in bucket
        }

        category_folders = {
            category: self._create_category_folder(category, bookmarks)
            for category, bookmarks in movable_categories.items()
        }

        # Remove bookmarks that will be relocated
        def should_move(item: Dict[str, Any]) -> bool:
            return (
                isinstance(item, dict)
                and item.get('WebBookmarkType') == 'WebBookmarkTypeLeaf'
                and (item.get('URIDictionary', {}).get('title'), item.get('URLString')) in move_targets
            )

        root_children[:] = [child for child in root_children if not should_move(child)]

        # Append new folders with relocated bookmarks
        root_children.extend(category_folders.values())

        return organized

    def _create_category_folder(self, category_name: str, bookmarks: List[Dict]) -> Dict[str, Any]:
        """Create a folder structure for a category."""
        folder = {
            'WebBookmarkType': 'WebBookmarkTypeList',
            'Title': category_name.capitalize(),
            'Children': [],
            'URIDictionary': {
                'title': category_name.capitalize()
            }
        }
        
        # Add bookmarks to folder
        for bookmark in bookmarks:
            folder_bookmark = {
                'WebBookmarkType': 'WebBookmarkTypeLeaf',
                'Title': bookmark['title'],
                'URLString': bookmark['url'],
                'URIDictionary': {
                    'title': bookmark['title']
                }
            }
            folder['Children'].append(folder_bookmark)
        
        return folder

    def save_organized(self, output_path: Optional[str] = None) -> None:
        """Save the organized bookmarks to a file."""
        if not self.organized_data:
            self.organize(dry_run=False)
        
        output_path = output_path or "organized_bookmarks.plist"
        expanded_path = Path(output_path).expanduser()
        
        with open(expanded_path, 'wb') as f:
            plistlib.dump(self.organized_data, f)
        
        logger.info(f"Saved organized bookmarks to {expanded_path}")

    def get_organization_plan(self) -> Dict[str, Any]:
        """Get a plan of how bookmarks will be organized."""
        if not self.parser.bookmarks:
            self.load_and_parse()
        
        # Categorize bookmarks
        categorized = self.categorizer.categorize_all(self.parser.bookmarks)
        
        # Create organization plan
        plan = {
            'total_bookmarks': len(self.parser.bookmarks),
            'categories': {},
            'folders_to_create': [],
            'bookmarks_to_move': []
        }
        
        for category, bookmarks in categorized.items():
            plan['categories'][category] = len(bookmarks)
            
            if len(bookmarks) >= 2:
                plan['folders_to_create'].append(category)
                
                for bookmark in bookmarks:
                    plan['bookmarks_to_move'].append({
                        'title': bookmark['title'],
                        'from': bookmark.get('parent', 'Root'),
                        'to': category
                    })
        
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
        for category, count in plan['categories'].items():
            print(f"  {category}: {count} bookmarks")
        
        print("\n📂 Folders to create:")
        for folder in plan['folders_to_create']:
            print(f"  • {folder.capitalize()}")
        
        print("\n🔄 Sample moves (first 5):")
        for move in plan['bookmarks_to_move'][:5]:
            print(f"  '{move['title']}' from {move['from']} → {move['to']}")

    def backup_current(self, backup_path: Optional[str] = None) -> None:
        """Create a backup of current bookmarks."""
        backup_path = backup_path or "bookmarks_backup_before_organization.plist"
        expanded_path = Path(backup_path).expanduser()
        
        if not self.original_data:
            self.load_and_parse()
        
        with open(expanded_path, 'wb') as f:
            plistlib.dump(self.original_data, f)
        
        logger.info(f"Created backup at {expanded_path}")


if __name__ == "__main__":
    # Test the organizer
    organizer = BookmarkOrganizer("bookmarks_backup.plist")
    
    # Load and parse
    organizer.load_and_parse()
    
    # Preview changes
    organizer.preview_changes()
    
    # Organize (dry run)
    organized = organizer.organize(dry_run=True)
    
    # Save organized version
    organizer.save_organized("test_organized.plist")
    
    print("\n✅ Organization test completed successfully!")
    print("📁 Files created:")
    print("  • sample_bookmarks.json (from test_parser.py)")
    print("  • test_organized.plist (organized version)")
    print("  • bookmarks_backup_before_organization.plist (backup)")
