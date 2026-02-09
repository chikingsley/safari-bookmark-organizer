from pathlib import Path

def test_project_structure():
    """Test that project structure matches expected layout."""
    required_files = [
        "pyproject.toml",
        ".python-version",
        ".gitignore",
        "README.md",
        "src/safari_bookmark_organizer/__init__.py",
        "src/safari_bookmark_organizer/bookmark_parser.py",
        "src/safari_bookmark_organizer/ai_categorizer.py",
        "src/safari_bookmark_organizer/organizer.py",
        "src/safari_bookmark_organizer/cli.py",
    ]
    
    missing_files = [path for path in required_files if not Path(path).exists()]
    assert not missing_files, f"Missing files: {missing_files}"
    
    # Check pyproject.toml structure
    pyproject = Path("pyproject.toml")
    content = pyproject.read_text()
    required_sections = [
        "[project]",
        "[build-system]",
        "[tool.hatch.build.targets.wheel]",
        "[dependency-groups]",
        "[tool.pytest.ini_options]",
        "[tool.ruff]",
    ]
    missing_sections = [section for section in required_sections if section not in content]
    assert not missing_sections, f"Missing pyproject.toml sections: {missing_sections}"
    
    # Check .python-version
    python_version_file = Path(".python-version")
    version = python_version_file.read_text().strip()
    assert version.startswith("3.1"), f"Unexpected python version: {version}"
    
    # Check imports work
    import sys
    sys.path.insert(0, str(Path("src")))
    from safari_bookmark_organizer.bookmark_parser import BookmarkParser
    from safari_bookmark_organizer.ai_categorizer import AICategorizer
    from safari_bookmark_organizer.organizer import BookmarkOrganizer
    from safari_bookmark_organizer.cli import main
    
    # Test basic functionality
    backup_path = Path("bookmarks_backup.plist")
    if not backup_path.exists():
        return
    parser = BookmarkParser(str(backup_path))
    parser.load()
    parser.parse()
    assert len(parser.bookmarks) >= 1
