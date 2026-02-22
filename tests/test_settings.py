from __future__ import annotations

import pytest
from pydantic import ValidationError

from safari_bookmark_organizer.settings import LLMSettings


class TestLLMSettings:
    def test_defaults(self) -> None:
        settings = LLMSettings(_env_file=None)
        assert settings.api_key is None
        assert settings.base_url == "https://openrouter.ai/api/v1"
        assert settings.model == "openai/gpt-4o-mini"
        assert settings.enabled is False
        assert settings.batch_size == 25

    def test_env_var_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LLM_API_KEY", "sk-test-key-123")
        monkeypatch.setenv("LLM_BASE_URL", "https://ollama.peacockery.studio/v1")
        monkeypatch.setenv("LLM_MODEL", "llama3:8b")
        monkeypatch.setenv("LLM_ENABLED", "true")
        monkeypatch.setenv("LLM_BATCH_SIZE", "50")
        settings = LLMSettings(_env_file=None)
        assert settings.api_key == "sk-test-key-123"
        assert settings.base_url == "https://ollama.peacockery.studio/v1"
        assert settings.model == "llama3:8b"
        assert settings.enabled is True
        assert settings.batch_size == 50

    def test_enabled_accepts_truthy_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for value in ("1", "true", "True", "yes", "YES"):
            monkeypatch.setenv("LLM_ENABLED", value)
            settings = LLMSettings(_env_file=None)
            assert settings.enabled is True, f"Expected True for '{value}'"

    def test_batch_size_validation_min(self) -> None:
        with pytest.raises(ValidationError):
            LLMSettings(batch_size=0, _env_file=None)

    def test_batch_size_validation_max(self) -> None:
        with pytest.raises(ValidationError):
            LLMSettings(batch_size=101, _env_file=None)

    def test_batch_size_boundary_values(self) -> None:
        s1 = LLMSettings(batch_size=1, _env_file=None)
        assert s1.batch_size == 1
        s100 = LLMSettings(batch_size=100, _env_file=None)
        assert s100.batch_size == 100

    def test_constructor_override(self) -> None:
        settings = LLMSettings(
            api_key="sk-my-key",
            base_url="https://api.openai.com/v1",
            model="gpt-4o",
            enabled=True,
            _env_file=None,
        )
        assert settings.api_key == "sk-my-key"
        assert settings.base_url == "https://api.openai.com/v1"
        assert settings.model == "gpt-4o"
        assert settings.enabled is True

    def test_api_key_none_by_default(self) -> None:
        settings = LLMSettings(_env_file=None)
        assert settings.api_key is None
