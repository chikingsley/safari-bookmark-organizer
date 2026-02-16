from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from loguru import logger

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


@dataclass
class OpenCodeConfig:
    model: str = "openai/gpt-4o-mini"
    attach: str | None = None


class OpenCodeClient:
    """Minimal OpenCode CLI wrapper for categorization."""

    def __init__(self, config: OpenCodeConfig | None = None):
        self.config = config or self._load_config()

    @staticmethod
    def _load_config() -> OpenCodeConfig:
        model = os.getenv("OPENCODE_MODEL", "openai/gpt-4o-mini")
        attach = os.getenv("OPENCODE_ATTACH")
        return OpenCodeConfig(model=model, attach=attach)

    def _run(self, prompt: dict[str, Any]) -> str:
        cmd = ["opencode", "run", "--format", "json", "--model", self.config.model]
        if self.config.attach:
            cmd.extend(["--attach", self.config.attach])
        cmd.append(json.dumps(prompt))

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
            logger.warning("OpenCode CLI failed: {}", exc)
            return ""

        # OpenCode JSON format is line-delimited events; capture latest text part.
        last_text = ""
        raw_non_json: list[str] = []
        for line in result.stdout.splitlines():
            if not line.lstrip().startswith("{"):
                stripped = line.strip()
                if stripped and len(raw_non_json) < 3:
                    raw_non_json.append(stripped)
                continue
            try:
                event: Any = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "text":
                part = event.get("part", {})
                text = part.get("text")
                if isinstance(text, str):
                    last_text = text
        if not last_text:
            if raw_non_json:
                logger.warning("OpenCode output was not JSON events: {}", raw_non_json[0])
            if result.stderr.strip():
                logger.warning("OpenCode stderr: {}", result.stderr.strip().splitlines()[-1])
        return last_text

    def categorize(self, title: str, url: str, categories: Iterable[str]) -> list[str]:
        """Return a list of categories from OpenCode CLI JSON output."""
        prompt = {
            "title": title,
            "url": url,
            "categories": list(categories),
            "instruction": (
                "Choose exactly one category from categories for this bookmark. "
                'Return ONLY a JSON array with one string, e.g. ["work"].'
            ),
        }
        last_text = self._run(prompt)
        if not last_text:
            return []
        try:
            parsed: Any = json.loads(last_text)
        except json.JSONDecodeError:
            logger.warning("OpenCode response was not JSON: {}", last_text)
            return []

        if isinstance(parsed, str):
            return [parsed]
        if isinstance(parsed, list) and parsed:
            return [str(cast("object", parsed[0]))]
        return []

    def categorize_many(
        self, bookmarks: Sequence[dict[str, str]], categories: Iterable[str]
    ) -> list[str]:
        """Return one category per bookmark in order."""
        prompt = {
            "categories": list(categories),
            "bookmarks": list(bookmarks),
            "instruction": (
                "For each bookmark, choose exactly one category from categories. "
                "Return ONLY a JSON array of category strings with the same length as bookmarks."
            ),
        }
        last_text = self._run(prompt)
        if not last_text:
            return []
        try:
            parsed: Any = json.loads(last_text)
        except json.JSONDecodeError:
            logger.warning("OpenCode response was not JSON: {}", last_text)
            return []
        if not isinstance(parsed, list):
            return []
        return [str(cast("object", item)) for item in cast("list[Any]", parsed)]
