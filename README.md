# Safari Bookmark Organizer

A project to programmatically organize Safari bookmarks using AI categorization.

## Project Structure

- `bookmarks_backup.plist` - Backup of original Safari bookmarks
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

OpenCode CLI integration is supported and disabled by default.
Enable it by setting `OPENCODE_ENABLED=1` and optionally `OPENCODE_MODEL`.

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

# Enable OpenCode categorization
OPENCODE_ENABLED=1 OPENCODE_MODEL=zai-coding-plan/glm-4.7-flash uv run safari-organizer organize --dry-run --opencode

# Run tests
uv run pytest

# Run with linting
uv run ruff check .
```
