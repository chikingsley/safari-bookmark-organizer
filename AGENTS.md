## Project Operating Rules

### Dependency Management
- Use uv only. Do not use pip directly.
- Install/sync dependencies with `uv sync`.
- Add dev dependencies with `uv add --dev <package>`.
- Commit `uv.lock` for reproducible installs.

### Running Tools
- Run tests with `uv run pytest`.
- Run the CLI with `uv run safari-organizer ...`.

### Notes
- Keep `pyproject.toml` as the single source of truth for dependencies.
