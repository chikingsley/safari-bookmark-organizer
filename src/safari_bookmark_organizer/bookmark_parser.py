"""
Bookmark Parser

Parse Safari's binary PLIST bookmark format and extract structured data.
"""

from __future__ import annotations

import json
import plistlib
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from typing import Dict, List, Optional


class BookmarkParser:
    """Parse and extract data from Safari bookmarks.plist file."""

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or "~/Library/Safari/Bookmarks.plist"
        self.data = None
        self.bookmarks = []
        self.folders = []

    def load(self) -> dict[str, Any]:
        """Load and parse the bookmarks.plist file."""
        try:
            expanded_path = Path(self.file_path).expanduser()
            with open(expanded_path, 'rb') as f:
                self.data = plistlib.load(f)
            logger.info(f"Loaded bookmarks from {expanded_path}")
            return self.data
        except Exception as e:
            logger.error(f"Failed to load bookmarks: {e}")
            raise

    def parse(self) -> None:
        """Parse the loaded bookmark data into structured format."""
        if not self.data:
            self.load()

        # Extract bookmarks and folders
        self._extract_items(self.data)
        logger.info(f"Found {len(self.bookmarks)} bookmarks and {len(self.folders)} folders")

    def _extract_items(self, data: Dict[str, Any], parent: Optional[str] = None) -> None:
        """Recursively extract bookmarks and folders."""
        if not isinstance(data, dict):
            return

        # Handle different bookmark types
        if 'WebBookmarkType' in data:
            bookmark_type = data['WebBookmarkType']
            
            if bookmark_type == 'WebBookmarkTypeLeaf':
                # Individual bookmark
                bookmark = {
                    'title': data.get('URIDictionary', {}).get('title', 'Untitled'),
                    'url': data.get('URLString', ''),
                    'type': 'bookmark',
                    'parent': parent,
                    'uuid': data.get('WebBookmarkUUID')
                }
                self.bookmarks.append(bookmark)
                
            elif bookmark_type == 'WebBookmarkTypeList':
                # Folder
                folder = {
                    'title': data.get('Title', 'Untitled Folder'),
                    'type': 'folder',
                    'parent': parent,
                    'uuid': data.get('WebBookmarkUUID'),
                    'children': []
                }
                self.folders.append(folder)
                
                # Recursively process children
                if 'Children' in data:
                    for child in data['Children']:
                        self._extract_items(child, folder['title'])

    def to_json(self) -> str:
        """Convert parsed data to JSON format."""
        return json.dumps({
            'bookmarks': self.bookmarks,
            'folders': self.folders
        }, indent=2)

    def get_bookmarks_by_category(self) -> Dict[str, List[Dict]]:
        """Categorize bookmarks by domain/type."""
        categories = {}
        
        for bookmark in self.bookmarks:
            if not bookmark['url']:
                continue
                
            # Simple domain-based categorization
            domain = self._extract_domain(bookmark['url'])
            if domain not in categories:
                categories[domain] = []
            categories[domain].append(bookmark)
        
        return categories

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        if not url:
            return "unknown"
        
        # Remove protocol and path
        domain = url.replace('https://', '').replace('http://', '').split('/')[0]
        
        # Handle common domains
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return domain

    def save_to_file(self, output_path: str) -> None:
        """Save parsed data to JSON file."""
        with open(output_path, 'w') as f:
            f.write(self.to_json())
        logger.info(f"Saved parsed bookmarks to {output_path}")


if __name__ == "__main__":
    # Test the parser
    parser = BookmarkParser("bookmarks_backup.plist")
    parser.load()
    parser.parse()
    
    # Save to JSON for inspection
    parser.save_to_file("parsed_bookmarks.json")
    
    # Print some stats
    print(f"Total bookmarks: {len(parser.bookmarks)}")
    print(f"Total folders: {len(parser.folders)}")
    
    # Show categories
    categories = parser.get_bookmarks_by_category()
    print(f"Categories found: {len(categories)}")
    for category, bookmarks in list(categories.items())[:5]:
        print(f"  {category}: {len(bookmarks)} bookmarks")