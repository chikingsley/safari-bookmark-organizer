from __future__ import annotations

from unittest.mock import MagicMock, patch

from openai import APIError

from safari_bookmark_organizer.llm_client import (
    BatchCategoryResult,
    CategoryResult,
    LLMClient,
)
from safari_bookmark_organizer.settings import LLMSettings


def _make_client() -> LLMClient:
    return LLMClient(settings=LLMSettings(api_key="test-key", _env_file=None))


def _mock_parse_response(parsed: CategoryResult | BatchCategoryResult | None) -> MagicMock:
    """Build a mock response matching openai's beta.chat.completions.parse() shape."""
    message = MagicMock()
    message.parsed = parsed
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


class TestCategorize:
    @patch("safari_bookmark_organizer.llm_client.OpenAI")
    def test_categorize_success(self, mock_openai_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.beta.chat.completions.parse.return_value = _mock_parse_response(
            CategoryResult(category="development")
        )

        client = _make_client()
        result = client.categorize("My Repo", "https://github.com/user/repo", ["development", "personal"])
        assert result == "development"

    @patch("safari_bookmark_organizer.llm_client.OpenAI")
    def test_categorize_unknown_category_returns_uncategorized(self, mock_openai_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.beta.chat.completions.parse.return_value = _mock_parse_response(
            CategoryResult(category="unknown_cat")
        )

        client = _make_client()
        result = client.categorize("Test", "https://test.com", ["work", "personal"])
        assert result == "uncategorized"

    @patch("safari_bookmark_organizer.llm_client.OpenAI")
    def test_categorize_none_parsed_returns_uncategorized(self, mock_openai_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.beta.chat.completions.parse.return_value = _mock_parse_response(None)

        client = _make_client()
        result = client.categorize("Test", "https://test.com", ["work"])
        assert result == "uncategorized"

    @patch("safari_bookmark_organizer.llm_client.OpenAI")
    def test_categorize_api_error_returns_uncategorized(self, mock_openai_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.beta.chat.completions.parse.side_effect = APIError(
            message="Server error", request=MagicMock(), body=None
        )

        client = _make_client()
        result = client.categorize("Test", "https://test.com", ["work"])
        assert result == "uncategorized"


class TestCategorizeMany:
    @patch("safari_bookmark_organizer.llm_client.OpenAI")
    def test_categorize_many_success(self, mock_openai_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.beta.chat.completions.parse.return_value = _mock_parse_response(
            BatchCategoryResult(categories=["development", "personal"])
        )

        client = _make_client()
        bookmarks = [
            {"title": "Repo", "url": "https://github.com"},
            {"title": "Guitar", "url": "https://guitar.com"},
        ]
        result = client.categorize_many(bookmarks, ["development", "personal"])
        assert result == ["development", "personal"]

    @patch("safari_bookmark_organizer.llm_client.OpenAI")
    def test_categorize_many_length_mismatch_returns_empty(self, mock_openai_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.beta.chat.completions.parse.return_value = _mock_parse_response(
            BatchCategoryResult(categories=["development"])
        )

        client = _make_client()
        bookmarks = [
            {"title": "A", "url": "https://a.com"},
            {"title": "B", "url": "https://b.com"},
        ]
        result = client.categorize_many(bookmarks, ["development", "personal"])
        assert result == []

    @patch("safari_bookmark_organizer.llm_client.OpenAI")
    def test_categorize_many_none_parsed_returns_empty(self, mock_openai_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.beta.chat.completions.parse.return_value = _mock_parse_response(None)

        client = _make_client()
        result = client.categorize_many([{"title": "X", "url": "https://x.com"}], ["a"])
        assert result == []

    @patch("safari_bookmark_organizer.llm_client.OpenAI")
    def test_categorize_many_api_error_returns_empty(self, mock_openai_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.beta.chat.completions.parse.side_effect = APIError(
            message="Server error", request=MagicMock(), body=None
        )

        client = _make_client()
        result = client.categorize_many([{"title": "X", "url": "https://x.com"}], ["a"])
        assert result == []

    @patch("safari_bookmark_organizer.llm_client.OpenAI")
    def test_categorize_many_unknown_categories_resolve_to_uncategorized(
        self, mock_openai_cls: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.beta.chat.completions.parse.return_value = _mock_parse_response(
            BatchCategoryResult(categories=["development", "bogus"])
        )

        client = _make_client()
        bookmarks = [
            {"title": "A", "url": "https://a.com"},
            {"title": "B", "url": "https://b.com"},
        ]
        result = client.categorize_many(bookmarks, ["development", "personal"])
        assert result == ["development", "uncategorized"]
