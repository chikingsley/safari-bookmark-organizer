# Safari Bookmark Organizer

A project to programmatically organize Safari bookmarks using AI categorization.

## Project Structure

- `src/safari_bookmark_organizer/organizer.py` - Main organization logic
- `src/safari_bookmark_organizer/ai_categorizer.py` - Categorization logic (rule-based, OpenCode-ready)
- `tests/` - Pytest discovery location (contains moved root test scripts)

## Approach

1. **Backup**: Always work with copies, never modify original directly
2. **Parse**: Read the binary PLIST format
3. **Analyze**: Use AI to understand bookmark content and categorize
4. **Organize**: Create logical folder structures
5. **Test**: Dry-run testing before any real changes
6. **Deploy**: Background service for continuous organization

## AI Model

OpenCode CLI integration is supported and enabled by default in the CLI.
Disable it with `--no-opencode` or set `OPENCODE_ENABLED=0`.

## Usage

```bash
# Set up environment (using UV)
uv sync

# Run organizer (dry-run mode)
uv run safari-organizer analyze

# Preview organization
uv run safari-organizer organize --dry-run

# Apply organization
uv run safari-organizer organize --apply

# Override OpenCode model (optional)
OPENCODE_MODEL=zai-coding-plan/glm-4.7-flash uv run safari-organizer organize --dry-run --opencode

# Launch preview UI
uv run safari-organizer preview --port 8000

# Run tests
uv run pytest

# Run with linting
uv run ruff check .
```

## Docker

Build and run the preview UI:

```bash
docker compose up --build
```

Set your Cloudflare tunnel token in a local `.env` file:

```bash
CLOUDFLARE_TUNNEL_TOKEN=...
BOOKMARKS_PATH=/Users/youruser/Library/Safari/Bookmarks.plist
```
