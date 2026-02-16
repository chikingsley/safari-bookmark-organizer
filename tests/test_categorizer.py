from safari_bookmark_organizer.ai_categorizer import AICategorizer
from safari_bookmark_organizer.types import BookmarkItem


def _bookmark(title: str, url: str) -> BookmarkItem:
    return {"title": title, "url": url}


class TestRuleBasedCategorization:
    """Test the rule-based fallback (no OpenCode)."""

    def setup_method(self) -> None:
        self.categorizer = AICategorizer(use_opencode=False)

    def test_work_pattern(self) -> None:
        result = self.categorizer.categorize_bookmark(
            _bookmark("Company Portal", "https://company.com/work")
        )
        assert result == ["work"]

    def test_education_domain(self) -> None:
        result = self.categorizer.categorize_bookmark(
            _bookmark("n8n Course", "https://docs.n8n.io/courses/beginner")
        )
        assert result == ["education"]

    def test_development_domain(self) -> None:
        result = self.categorizer.categorize_bookmark(
            _bookmark("My Repo", "https://github.com/user/repo")
        )
        assert result == ["development"]

    def test_personal_pattern(self) -> None:
        result = self.categorizer.categorize_bookmark(
            _bookmark("Guitar Lessons", "https://sixstringfingerpicking.com")
        )
        assert result == ["personal"]

    def test_uncategorized_fallback(self) -> None:
        result = self.categorizer.categorize_bookmark(
            _bookmark("Random Page", "https://randomxyz123.com/page")
        )
        assert result == ["uncategorized"]


class TestCategorizeAll:
    def test_groups_bookmarks(self) -> None:
        categorizer = AICategorizer(use_opencode=False)
        bookmarks = [
            _bookmark("GitHub Home", "https://github.com"),
            _bookmark("Stack Overflow", "https://stackoverflow.com/questions"),
            _bookmark("Guitar Tab", "https://sixstringfingerpicking.com/tab"),
        ]
        result = categorizer.categorize_all(bookmarks)
        assert "development" in result
        assert len(result["development"]) == 2
        assert "personal" in result


class TestFolderStructure:
    def test_suggest_folder_structure(self) -> None:
        categorizer = AICategorizer(use_opencode=False)
        categories = {
            "development": [
                _bookmark("GitHub", "https://github.com"),
                _bookmark("SO", "https://stackoverflow.com"),
            ],
            "solo": [_bookmark("One", "https://one.com")],
        }
        structure = categorizer.suggest_folder_structure(categories)
        assert structure["name"] == "Bookmarks"
        # Only "development" should become a folder (solo has <2 items)
        children = structure["children"]
        assert len(children) == 1
        assert children[0]["name"] == "Development"
        assert len(children[0]["children"]) == 2


class TestOpinionatedTaxonomy:
    def test_opinionated_categories(self) -> None:
        categorizer = AICategorizer(use_opencode=False, taxonomy="opinionated")
        expected = ["work", "build", "learn", "tools", "reference", "personal", "uncategorized"]
        assert categorizer.opencode_categories == expected


class TestAnalyzeBookmark:
    def test_keyword_extraction(self) -> None:
        categorizer = AICategorizer(use_opencode=False)
        result = categorizer.analyze_bookmark_content(
            _bookmark("API Documentation Tutorial", "https://docs.example.com/api")
        )
        assert "api" in result["keywords"]
        assert "documentation" in result["keywords"]
        assert "tutorial" in result["keywords"]
        assert result["confidence"] > 0

    def test_tags_include_domain(self) -> None:
        categorizer = AICategorizer(use_opencode=False)
        result = categorizer.analyze_bookmark_content(
            _bookmark("Page", "https://example.com/page")
        )
        assert "example.com" in result["tags"]
