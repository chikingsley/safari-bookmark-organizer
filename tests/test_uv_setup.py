from pathlib import Path


def test_project_structure() -> None:
    """Test that project structure matches expected layout."""
    required_files = [
        "pyproject.toml",
        ".python-version",
        ".gitignore",
        "README.md",
        "src/safari_bookmark_organizer/__init__.py",
        "src/safari_bookmark_organizer/models.py",
        "src/safari_bookmark_organizer/safari_io.py",
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
    from safari_bookmark_organizer.safari_io import SafariBookmarks

    # Test basic functionality with real file if available
    backup_path = Path("bookmarks_backup.plist")
    if not backup_path.exists():
        return
    bookmarks = SafariBookmarks.open(backup_path)
    assert len(bookmarks.children) >= 1
