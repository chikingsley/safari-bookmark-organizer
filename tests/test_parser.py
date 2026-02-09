import json
import plistlib
from pathlib import Path

import pytest

def is_serializable(obj):
    """Check if an object is JSON serializable."""
    try:
        json.dumps(obj)
        return True
    except (TypeError, OverflowError):
        return False

def safe_extract(data, max_items=5):
    """Safely extract serializable data for inspection."""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if len(result) >= max_items:
                break
            if is_serializable(value):
                result[key] = value
            else:
                result[key] = f"<binary data: {type(value).__name__}>"
        return result
    if isinstance(data, list):
        return [safe_extract(item) for item in data[:max_items]]
    return data if is_serializable(data) else f"<binary: {type(data).__name__}>"

def test_basic_parsing(tmp_path: Path):
    """Parse the backup plist and validate basic structure."""
    file_path = Path("bookmarks_backup.plist")
    if not file_path.exists():
        pytest.skip("bookmarks_backup.plist not present in repo")

    with open(file_path, "rb") as f:
        data = plistlib.load(f)

    assert isinstance(data, dict)
    assert "Children" in data

    # Extract safe sample data to a temp file, not the repo
    sample_data = safe_extract(data)
    sample_path = tmp_path / "sample_bookmarks.json"
    sample_path.write_text(json.dumps(sample_data, indent=2))

    children = data["Children"]
    assert isinstance(children, list)
    assert len(children) >= 1

    bookmark_count = 0
    folder_count = 0
    for item in children:
        if isinstance(item, dict) and item.get("WebBookmarkType"):
            if item["WebBookmarkType"] == "WebBookmarkTypeLeaf":
                bookmark_count += 1
            elif item["WebBookmarkType"] == "WebBookmarkTypeList":
                folder_count += 1

    assert bookmark_count + folder_count <= len(children)
