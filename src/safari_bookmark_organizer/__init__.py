"""
Safari Bookmark Organizer

AI-powered Safari bookmark organization system using OpenCode CLI
for intelligent categorization and management.
"""

from .bookmark_parser import BookmarkParser
from .ai_categorizer import AICategorizer
from .organizer import BookmarkOrganizer
from .opencode_client import OpenCodeClient

__version__ = "0.1.0"
__all__ = ["BookmarkParser", "AICategorizer", "BookmarkOrganizer", "OpenCodeClient"]
