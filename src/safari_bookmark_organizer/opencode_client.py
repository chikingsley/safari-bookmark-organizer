from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Iterable, List

from loguru import logger


@dataclass
class OpenCodeConfig:
    model: str = "zai-coding-plan/glm-4.7-flash"
    attach: str | None = None


class OpenCodeClient:
    """Minimal OpenCode CLI wrapper for categorization."""

    def __init__(self, config: OpenCodeConfig | None = None):
        self.config = config or self._load_config()

    @staticmethod
    def _load_config() -> OpenCodeConfig:
        model = os.getenv("OPENCODE_MODEL", "zai-coding-plan/glm-4.7-flash")
        attach = os.getenv("OPENCODE_ATTACH")
        return OpenCodeConfig(model=model, attach=attach)

    def categorize(self, title: str, url: str, categories: Iterable[str]) -> List[str]:
        """Return a list of categories from OpenCode CLI JSON output."""
        prompt = {
            "title": title,
            "url": url,
            "categories": list(categories),
            "instruction": "Return a JSON array of category names only.",
        }
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
        except Exception as exc:
            logger.warning("OpenCode CLI failed, falling back to rules: {}", exc)
            return []

        # OpenCode JSON format is line-delimited events; capture latest text part.
        last_text = ""
        for line in result.stdout.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "text":
                part = event.get("part", {})
                text = part.get("text")
                if isinstance(text, str):
                    last_text = text

        if not last_text:
            return []
        try:
            parsed = json.loads(last_text)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            logger.warning("OpenCode response was not JSON: {}", last_text)
        return []
