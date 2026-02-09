"""
AI Categorizer

AI-powered categorization of bookmarks using OpenCode CLI.
This module handles the intelligent organization logic.
"""

from typing import Any, Dict, List, Optional
from loguru import logger
import re
import json
import os

from .opencode_client import OpenCodeClient


class AICategorizer:
    """AI-powered bookmark categorization."""

    def __init__(self, use_opencode: Optional[bool] = None):
        # Predefined categories and patterns
        self.categories = {
            'work': {
                'patterns': [r'work', r'company', r'business', r'enterprise', r'corporate'],
                'domains': ['buildingconnected', 'autodesk', 'postman', 'monday', 'construction']
            },
            'education': {
                'patterns': [r'course', r'learn', r'tutorial', r'university', r'school'],
                'domains': ['youtube.com/playlist', 'docs.n8n', 'maricopa.edu']
            },
            'development': {
                'patterns': [r'api', r'developer', r'code', r'programming', r'docs'],
                'domains': ['github', 'stackoverflow', 'developer.apple', 'docs.python']
            },
            'personal': {
                'patterns': [r'personal', r'hobby', r'fun', r'guitar'],
                'domains': ['sixstringfingerpicking', 'netflix', 'spotify']
            },
            'tools': {
                'patterns': [r'tool', r'service', r'utility', r'software'],
                'domains': ['postman', 'figma', 'canva', 'notion']
            }
        }
        self._opencode_client: Optional[OpenCodeClient] = None
        opencode_enabled = (
            use_opencode
            if use_opencode is not None
            else os.getenv("OPENCODE_ENABLED", "").lower() in {"1", "true", "yes"}
        )
        if opencode_enabled:
            try:
                self._opencode_client = OpenCodeClient()
                logger.info("OpenCode client initialized")
            except Exception as exc:
                logger.warning("OpenCode client disabled: {}", exc)

    def categorize_bookmark(self, bookmark: Dict) -> List[str]:
        """Categorize a single bookmark based on URL, title, and content."""
        categories = []
        
        url = bookmark.get('url', '')
        title = bookmark.get('title', '')
        
        # Combine text for analysis
        text = f"{title} {url}".lower()

        if self._opencode_client:
            oc_categories = self._opencode_client.categorize(title, url, self.categories.keys())
            if oc_categories:
                return oc_categories

        # Check each category
        for category, rules in self.categories.items():
            # Check URL patterns
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in rules['patterns']):
                categories.append(category)
                continue
            
            # Check domains
            if any(domain in url.lower() for domain in rules['domains']):
                categories.append(category)
        
        # Always add a default category if none found
        if not categories:
            categories.append('uncategorized')
        
        return categories

    def categorize_all(self, bookmarks: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize all bookmarks and return organized structure."""
        organized = {}
        
        for bookmark in bookmarks:
            categories = self.categorize_bookmark(bookmark)
            
            for category in categories:
                if category not in organized:
                    organized[category] = []
                organized[category].append(bookmark)
        
        return organized

    def suggest_folder_structure(self, categories: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Suggest an optimal folder structure based on categorized bookmarks."""
        structure = {
            'name': 'Bookmarks',
            'children': []
        }
        
        # Create folders for each category
        for category, bookmarks in categories.items():
            if len(bookmarks) > 1:  # Only create folder if multiple bookmarks
                folder = {
                    'name': category.capitalize(),
                    'type': 'folder',
                    'children': []
                }
                
                # Add bookmarks to folder
                for bookmark in bookmarks:
                    folder['children'].append({
                        'name': bookmark['title'],
                        'url': bookmark['url'],
                        'type': 'bookmark'
                    })
                
                structure['children'].append(folder)
        
        return structure

    def analyze_bookmark_content(self, bookmark: Dict) -> Dict:
        """Analyze bookmark content and suggest tags/keywords."""
        # This would be enhanced with actual AI/ML analysis
        analysis = {
            'keywords': [],
            'tags': [],
            'confidence': 0.0
        }
        
        url = bookmark.get('url', '')
        title = bookmark.get('title', '')
        
        # Simple keyword extraction
        text = f"{title} {url}"
        
        # Extract potential keywords
        potential_keywords = [
            'api', 'documentation', 'tutorial', 'course', 'tool',
            'service', 'platform', 'software', 'development', 'learning'
        ]
        
        for keyword in potential_keywords:
            if keyword.lower() in text.lower():
                analysis['keywords'].append(keyword)
        
        # Simple tagging based on domain
        domain = self._extract_domain(url)
        if domain:
            analysis['tags'].append(domain)
        
        analysis['confidence'] = min(0.9, len(analysis['keywords']) * 0.1)
        
        return analysis

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        if not url:
            return ""
        
        domain = url.replace('https://', '').replace('http://', '').split('/')[0]
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain


if __name__ == "__main__":
    # Test the categorizer
    categorizer = AICategorizer()
    
    # Sample bookmarks
    test_bookmarks = [
        {'title': 'BuildingConnected API Docs', 'url': 'https://buildingconnected.com/developers'},
        {'title': 'n8n Beginner Course', 'url': 'https://docs.n8n.io/courses/beginner'},
        {'title': 'Fingerpicking Guitar Lessons', 'url': 'https://sixstringfingerpicking.com'},
        {'title': 'Postman API Tool', 'url': 'https://postman.com'},
    ]
    
    # Categorize
    categories = categorizer.categorize_all(test_bookmarks)
    print("Categorization Results:")
    for category, bookmarks in categories.items():
        print(f"  {category}: {len(bookmarks)} bookmarks")
    
    # Suggest structure
    structure = categorizer.suggest_folder_structure(categories)
    print(f"\nSuggested Structure:")
    print(json.dumps(structure, indent=2))
