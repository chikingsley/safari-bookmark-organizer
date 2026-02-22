from __future__ import annotations

from conftest import make_bookmark

from safari_bookmark_organizer.ai_categorizer import (
    DEFAULT_CATEGORIES,
    OPINIONATED_CATEGORIES,
    AICategorizer,
)
from safari_bookmark_organizer.types import FolderNode


class TestCategorizeWithoutLLM:
    """Without LLM, everything goes to uncategorized."""

    def test_single_bookmark(self) -> None:
        categorizer = AICategorizer(use_llm=False)
        result = categorizer.categorize_bookmark(make_bookmark("GitHub Home", "https://github.com"))
        assert result == "uncategorized"

    def test_all_bookmarks(self) -> None:
        categorizer = AICategorizer(use_llm=False)
        bookmarks = [
            make_bookmark("GitHub", "https://github.com"),
            make_bookmark("Stack Overflow", "https://stackoverflow.com"),
            make_bookmark("Guitar Tab", "https://sixstringfingerpicking.com/tab"),
        ]
        result = categorizer.categorize_all(bookmarks)
        assert list(result.keys()) == ["uncategorized"]
        assert len(result["uncategorized"]) == 3


class TestCategories:
    def test_default_categories(self) -> None:
        categorizer = AICategorizer(use_llm=False)
        assert categorizer.opencode_categories == DEFAULT_CATEGORIES
        assert "uncategorized" in categorizer.opencode_categories

    def test_opinionated_categories(self) -> None:
        categorizer = AICategorizer(use_llm=False, taxonomy="opinionated")
        assert categorizer.opencode_categories == OPINIONATED_CATEGORIES

    def test_set_custom_categories(self) -> None:
        categorizer = AICategorizer(use_llm=False)
        custom = ["a", "b", "uncategorized"]
        categorizer.set_opencode_categories(custom)
        assert categorizer.opencode_categories == custom


class TestFolderStructure:
    def test_suggest_folder_structure(self) -> None:
        categorizer = AICategorizer(use_llm=False)
        categories = {
            "development": [
                make_bookmark("GitHub", "https://github.com"),
                make_bookmark("SO", "https://stackoverflow.com"),
            ],
            "solo": [make_bookmark("One", "https://one.com")],
        }
        structure = categorizer.suggest_folder_structure(categories)
        assert structure.name == "Bookmarks"
        children = structure.children
        assert len(children) == 1
        child = children[0]
        assert child.name == "Development"
        assert child.type == "folder"
        assert isinstance(child, FolderNode)
        assert len(child.children) == 2
