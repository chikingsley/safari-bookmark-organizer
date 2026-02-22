# Safari Bookmark Organizer - Project Status

## Current State

All core functionality complete. LLM integration via OpenAI-compatible APIs (OpenRouter, Ollama, vLLM). All linting, formatting, and type checking clean.

### Stack

- **Models**: Pydantic v2 with discriminated unions, `extra="allow"` for lossless plist round-trip
- **LLM**: OpenAI SDK with structured output (`response_format` + Pydantic models)
- **CLI**: Typer (parse, organize, analyze, backup, preview)
- **Settings**: pydantic-settings with `LLM_*` env vars
- **Linting**: ruff (extensive rule set)
- **Type checking**: ty
- **Testing**: pytest with real Safari plist fixtures

### Core Modules

- **models.py** — Pydantic models for Safari plist nodes (WebBookmarkTypeLeaf, WebBookmarkTypeList, WebBookmarkTypeProxy)
- **safari_io.py** — `SafariBookmarkItem` tree wrapper + `SafariBookmarks` file I/O (open, save, load, dump, context manager)
- **ai_categorizer.py** — LLM-powered bookmark categorization
- **llm_client.py** — OpenAI SDK client with structured output for reliable categorization
- **organizer.py** — Orchestrator: load plist, categorize bookmarks, build organized tree, save output
- **types.py** — Pydantic BaseModel types for OrganizationPlan, BookmarkMove, FolderStructure
- **preview.py** — Local HTTP server serving a single-page web UI for dry-run preview with search/filter
- **cli.py** — Typer CLI with 5 commands
- **settings.py** — LLM config via pydantic-settings (LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, etc.)

### Test Coverage

- Real Safari plist fixtures (binary + XML) in `tests/support/fixtures/`
- Tests cover: models, safari I/O, categorizer, organizer, CLI, settings, LLM client

## History

### OpenCode → OpenRouter migration (completed)

Replaced OpenCode CLI subprocess wrapper with direct LLM API calls:

1. Deleted `opencode_client.py` (subprocess wrapper for `opencode run`)
2. Created `llm_client.py` using `openai` SDK with `beta.chat.completions.parse()` for structured output
3. Replaced `OpenCodeSettings` with `LLMSettings` (`LLM_*` env vars instead of `OPENCODE_*`)
4. CLI flags: `--opencode/--no-opencode` → `--llm/--no-llm`
5. Supports OpenRouter (default), Ollama, vLLM, or any OpenAI-compatible endpoint

### Rule-based categorizer removal (completed)

Deleted hardcoded URL pattern/domain matching rules. Without LLM enabled, all bookmarks return "uncategorized". With LLM, the API handles categorization with grammar-constrained structured output.

### Modernization (completed)

1. Pydantic Settings — `BaseSettings` with env var support
2. Click to Typer — CLI migration
3. Ruff rules — extensive lint rule set
4. Test improvements — proper fixtures, parametrized tests
5. ty type checker — added to CI checks

### Pydantic Migration (completed)

Ported Pydantic v2 models and real plist fixtures from `safari-bookmarks-cli`:

1. Added Pydantic models (`models.py`) and Safari I/O wrapper (`safari_io.py`)
2. Converted TypedDict types to Pydantic BaseModel (`types.py`)
3. Migrated `ai_categorizer.py` from dict access to `SafariBookmarkItem` attributes
4. Migrated `organizer.py` from `BookmarkParser` to `SafariBookmarks` I/O
5. Deleted deprecated `bookmark_parser.py`
