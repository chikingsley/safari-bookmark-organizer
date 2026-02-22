# Safari Bookmark Organizer

## Quick Reference

```bash
uv run pytest                          # Run tests
uv run ruff check src/ tests/         # Lint
uv run ruff format --check src/ tests/ # Format check
uv run ty check                        # Type check
uv run safari-organizer --help         # CLI entry point
```

## Architecture

- **models.py** — Pydantic v2 models for Safari plist nodes (Leaf, List, Proxy) with discriminated unions and `extra="allow"` for lossless round-trip I/O
- **safari_io.py** — `SafariBookmarkItem` (tree wrapper) and `SafariBookmarks` (file I/O: open/save/load/dump)
- **ai_categorizer.py** — LLM-powered categorization via OpenAI-compatible APIs
- **llm_client.py** — OpenAI SDK client with structured output (`response_format` + Pydantic models)
- **organizer.py** — Main orchestrator: load, categorize, build organized tree, save
- **types.py** — Pydantic BaseModel types for plans, moves, folder structures
- **cli.py** — Typer CLI (parse, organize, analyze, backup, preview)
- **preview.py** — Local HTTP server with single-page web UI for dry-run preview
- **settings.py** — Pydantic BaseSettings for LLM config (`LLM_*` env vars)

## Type Checker Suppression Tracking

These inline suppression comments exist due to known ty/Pydantic compatibility gaps.
**Check on ty updates** — when ty adds Pydantic plugin support, these may become removable.

### `ty: ignore` comments (4 total)

| Location | Rule | Reason | Removable when... |
|---|---|---|---|
| `safari_io.py:175` | `missing-argument` | ty doesn't understand `populate_by_name=True` in Pydantic's `model_config`. We construct `WebBookmarkTypeLeaf(url_string=...)` using the snake_case field name, but ty only sees the PascalCase alias `URLString` as valid. | ty supports Pydantic `populate_by_name=True` |
| `safari_io.py:183` | `missing-argument` | Same as above for `WebBookmarkTypeList(title=...)` vs alias `Title`. | ty supports Pydantic `populate_by_name=True` |
| `conftest.py:89` | `missing-argument` | Same `populate_by_name` false positive in test helper. | ty supports Pydantic `populate_by_name=True` |
| `organizer.py:147` | `invalid-argument-type` | `SafariBookmarkItem._node` is typed as base `WebBookmarkType` but is always a concrete subclass (Leaf/List/Proxy) at runtime. ty can't verify `WebBookmarkType` matches `ChildrenType` (the union of concrete subclasses). Changing `_node`'s type to the union would cascade narrowing requirements across the entire wrapper class. | ty gains flow-sensitive narrowing through list comprehensions, or `_node` type is refactored |

### `ty` rule in `pyproject.toml`

| Rule | Setting | Reason |
|---|---|---|
| `unknown-argument` | `"ignore"` | Pydantic `BaseSettings` generates `__init__` params from fields + accepts `_env_file` at runtime. ty sees these as unknown arguments. | ty supports Pydantic BaseSettings |

### `noqa` comments (2 total, all intentional)

| Location | Rule | Reason |
|---|---|---|
| `preview.py:164` | `S104` | Binding to `0.0.0.0` is intentional — local preview server checks for wildcard bind to compute browser URL |
| `test_safari_io.py:643` | `S324` | SHA1 used for plist content verification in tests, not for security |

### `test_safari_io.py:630` — `ty: ignore[invalid-argument-type]`

This is an intentional type mismatch in a test: it passes a text-mode file handle to a function expecting `IO[bytes]` to verify the function raises `IOError`. The wrong type IS the test.

## Maintenance Checklist

When ty releases a new version:

1. Run `uv run ty check` without any ignores (temporarily remove them)
2. If Pydantic `populate_by_name` issues are gone, delete the 3 `missing-argument` ignores
3. If `_node` type narrowing works, delete the `invalid-argument-type` ignore in organizer.py
4. Check if `unknown-argument = "ignore"` in pyproject.toml is still needed
5. Re-add only the ignores that are still required
