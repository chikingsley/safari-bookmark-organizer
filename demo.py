#!/usr/bin/env python3

"""
Demo script for Safari Bookmark Organizer.

Run with:
  uv run demo.py
"""

import os
from pathlib import Path

from safari_bookmark_organizer.ai_categorizer import AICategorizer
from safari_bookmark_organizer.organizer import BookmarkOrganizer


def get_bookmarks_path() -> Path:
    env_path = os.getenv("BOOKMARKS_PATH")
    if env_path:
        return Path(env_path).expanduser()
    return Path("~/Library/Safari/Bookmarks.plist").expanduser()


def demo_analysis():
    """Demo the analysis functionality."""
    print("🔍 Analyzing your Safari bookmarks...")
    print("=" * 50)

    path = get_bookmarks_path()
    if not path.exists():
        raise FileNotFoundError(f"Bookmarks file not found: {path}")

    # Use a copy for safety if you plan to apply changes.
    organizer = BookmarkOrganizer(str(path))
    organizer.load_and_parse()

    # Get organization plan
    plan = organizer.get_organization_plan()

    print(f"📊 Found {plan['total_bookmarks']} total bookmarks")
    print(f"📁 Identified {len(plan['categories'])} categories")
    print(f"📂 Would create {len(plan['folders_to_create'])} folders")
    print(f"🔄 Would move {len(plan['bookmarks_to_move'])} bookmarks")

    print("\n📋 Category Breakdown:")
    for category, count in sorted(plan["categories"].items(), key=lambda x: x[1], reverse=True):
        bar = "█" * (count // 5)
        print(f"  {category:15} {count:3} {bar}")

    print("\n🎯 Sample Organization:")
    for move in plan["bookmarks_to_move"][:10]:
        print(f"  • '{move['title']}' → {move['to']}")

    if len(plan["bookmarks_to_move"]) > 10:
        print(f"  ... and {len(plan['bookmarks_to_move']) - 10} more")


def demo_categorization():
    """Demo the AI categorization."""
    print("\n🤖 AI Categorization Demo")
    print("=" * 50)

    categorizer = AICategorizer(use_opencode=False)

    # Test bookmarks
    test_bookmarks = [
        {"title": "GitHub - Project Repo", "url": "https://github.com/yourusername/yourproject"},
        {
            "title": "BuildingConnected API Documentation",
            "url": "https://buildingconnected.com/developers/api",
        },
        {"title": "n8n Automation Course", "url": "https://docs.n8n.io/courses/automation"},
        {
            "title": "Fingerstyle Guitar Lessons",
            "url": "https://sixstringfingerpicking.com/lessons",
        },
        {"title": "Postman API Testing", "url": "https://postman.com/api-testing"},
    ]

    print("Testing categorization on sample bookmarks:\n")

    for bookmark in test_bookmarks:
        categories = categorizer.categorize_bookmark(bookmark)
        analysis = categorizer.analyze_bookmark_content(bookmark)

        print(f"📌 {bookmark['title']}")
        print(f"   URL: {bookmark['url']}")
        print(f"   Categories: {', '.join(categories)}")
        print(f"   Keywords: {', '.join(analysis['keywords'])}")
        print(f"   Confidence: {analysis['confidence']:.1%}")
        print()


def demo_usage():
    """Show how to use the organizer."""
    print("\n🚀 Usage Examples")
    print("=" * 50)

    print("1. Analyze your bookmarks:")
    print("   uv run safari-organizer analyze")

    print("\n2. Preview organization (dry run):")
    print("   uv run safari-organizer organize --dry-run")

    print("\n3. Apply organization:")
    print("   uv run safari-organizer organize --apply")

    print("\n4. Create backup:")
    print("   uv run safari-organizer backup")

    print("\n⚠️  Always backup before applying changes!")
    print("   The organizer creates automatic backups, but manual backups are recommended.")


if __name__ == "__main__":
    print("🌟 Safari Bookmark Organizer Demo")
    print("=" * 50)
    print("AI-powered organization for your Safari bookmarks")
    print()

    demo_analysis()
    demo_categorization()
    demo_usage()

    print("\n🎉 Demo completed!")
    print("\n📁 Files created during demo:")
    print("  • parsed_bookmarks.json - Full parsed bookmark data")

    print("\n💡 Next steps:")
    print("  1. Review the sample files to understand your bookmark structure")
    print("  2. Customize categories in ai_categorizer.py")
    print("  3. Run with --dry-run to preview changes")
    print("  4. Apply organization when ready")
