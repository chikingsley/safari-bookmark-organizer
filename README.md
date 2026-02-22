# Safari Bookmark Organizer

AI-powered Safari bookmark organization using LLM APIs (OpenRouter, Ollama, vLLM) for smart categorization.

## What It Does

1. Reads Safari's `~/Library/Safari/Bookmarks.plist` (binary or XML)
2. Categorizes bookmarks using LLM APIs with structured output
3. Proposes an organized folder structure with a dry-run preview
4. Writes the reorganized bookmarks to a new plist file
5. Preview UI — local web server to browse the proposed structure with search/filter

## Setup

```bash
uv sync
```

## CLI Commands

```bash
# Parse and inspect a bookmarks file
uv run safari-organizer parse

# Analyze bookmark structure and show organization plan
uv run safari-organizer analyze

# Organize bookmarks (dry-run by default)
uv run safari-organizer organize

# Organize with LLM categorization and write output
uv run safari-organizer organize --llm --apply --output organized.plist

# Create a backup
uv run safari-organizer backup

# Launch web preview UI
uv run safari-organizer preview --port 8000
```

All commands accept a file path argument to use a specific plist instead of the default Safari path:

```bash
uv run safari-organizer analyze ~/Desktop/Bookmarks.plist
```

## LLM Configuration

Enable AI-powered categorization via `--llm` flag or environment variables:

```bash
# OpenRouter (default)
LLM_API_KEY=sk-or-v1-... LLM_ENABLED=1 uv run safari-organizer organize

# Or use CLI flag
uv run safari-organizer organize --llm

# Disable with --no-llm (default)
uv run safari-organizer organize --no-llm
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_API_KEY` | (none) | API key for the LLM provider |
| `LLM_BASE_URL` | `https://openrouter.ai/api/v1` | OpenAI-compatible API endpoint |
| `LLM_MODEL` | `openai/gpt-4o-mini` | Model to use for categorization |
| `LLM_ENABLED` | `false` | Enable LLM categorization by default |
| `LLM_BATCH_SIZE` | `25` | Bookmarks per batch API call (1-100) |

### Example `.env` configurations

```bash
# OpenRouter
LLM_API_KEY=sk-or-v1-your-key-here
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=openai/gpt-4o-mini

# Local Ollama
LLM_BASE_URL=https://ollama.peacockery.studio/v1
LLM_MODEL=llama3:8b

# Local vLLM
LLM_BASE_URL=https://vllm.peacockery.studio/v1
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
```

## Project Structure

```text
src/safari_bookmark_organizer/
    models.py           # Pydantic v2 models for Safari plist nodes
    safari_io.py        # SafariBookmarkItem tree API + SafariBookmarks file I/O
    ai_categorizer.py   # LLM-powered categorization
    llm_client.py       # OpenAI SDK client with structured output
    organizer.py        # Main orchestrator (load, categorize, organize, save)
    types.py            # Pydantic models for plans, moves, folder structures
    cli.py              # Typer CLI
    preview.py          # Local web preview server
    settings.py         # LLM config (pydantic-settings, env vars)

tests/
    test_categorizer.py     # AI categorizer tests
    test_cli.py             # CLI integration tests
    test_llm_client.py      # LLM client tests (mocked)
    test_models_pydantic.py # Pydantic model unit tests
    test_organizer.py       # Organizer logic tests
    test_safari_io.py       # SafariBookmarkItem + file I/O tests
    test_settings.py        # Settings/env var tests
    support/fixtures/       # Real Safari plist fixtures (binary + XML)
```

## Development

```bash
uv run pytest                      # Run tests
uv run ruff check src/ tests/     # Lint
uv run ruff format src/ tests/    # Format
uv run ty check                    # Type check
```
