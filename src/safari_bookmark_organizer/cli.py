"""
Command Line Interface

CLI for the Safari Bookmark Organizer.
"""

from __future__ import annotations

import sys
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from .organizer import BookmarkOrganizer
from .preview import run_preview
from .safari_io import SafariBookmarkItem, SafariBookmarks
from .settings import LLMSettings

app = typer.Typer(help="Safari Bookmark Organizer CLI.")


class Taxonomy(StrEnum):
    default = "default"
    existing = "existing"
    opinionated = "opinionated"


def _build_settings(*, llm: bool = False) -> LLMSettings:
    """Build LLMSettings, optionally enabling LLM categorization."""
    if llm:
        return LLMSettings(enabled=True)
    return LLMSettings()


def _version_callback(value: bool) -> None:
    if value:
        typer.echo("safari-bookmark-organizer 0.1.0")
        raise typer.Exit()


def _count_items(root: SafariBookmarkItem) -> tuple[int, int]:
    """Count bookmarks and folders in the tree."""
    num_bookmarks = 0
    num_folders = 0
    if root.is_bookmark:
        num_bookmarks = 1
    elif root.is_folder:
        num_folders = 1
    for child in root.children:
        bm, fd = _count_items(child)
        num_bookmarks += bm
        num_folders += fd
    return num_bookmarks, num_folders


@app.callback()
def _callback(
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version."),
    ] = None,
) -> None:
    """Safari Bookmark Organizer CLI."""


@app.command()
def parse(
    file_path: Annotated[
        str, typer.Argument(help="Path to Safari bookmarks plist")
    ] = "~/Library/Safari/Bookmarks.plist",
    output: Annotated[str | None, typer.Option("--output", "-o", help="Output file path")] = None,
) -> None:
    """Parse Safari bookmarks file."""
    try:
        path = Path(file_path).expanduser()
        bookmarks = SafariBookmarks.open(path)
        num_bookmarks, num_folders = _count_items(bookmarks)

        typer.echo(f"Parsed {num_bookmarks} bookmarks and {num_folders} folders")

        if output:
            out_path = Path(output).expanduser()
            out_path.write_text(bookmarks.json(), encoding="utf-8")
            typer.echo(f"Saved to {output}")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        sys.exit(1)


@app.command()
def organize(
    file_path: Annotated[
        str, typer.Argument(help="Path to Safari bookmarks plist")
    ] = "~/Library/Safari/Bookmarks.plist",
    apply: Annotated[
        bool, typer.Option("--apply", help="Apply changes to the bookmarks file")
    ] = False,
    llm: Annotated[
        bool, typer.Option("--llm/--no-llm", help="Enable LLM categorization")
    ] = False,
    taxonomy: Annotated[
        Taxonomy, typer.Option(help="Category taxonomy", case_sensitive=False)
    ] = Taxonomy.default,
    output: Annotated[
        str | None, typer.Option("--output", "-o", help="Output file for organized bookmarks")
    ] = None,
    backup: Annotated[
        bool, typer.Option("--backup", "-b", help="Create backup before organizing")
    ] = False,
) -> None:
    """Organize Safari bookmarks using AI categorization."""
    try:
        settings = _build_settings(llm=llm)
        organizer = BookmarkOrganizer(
            file_path, use_llm=llm, taxonomy=taxonomy.value, settings=settings
        )

        if backup:
            organizer.backup_current()
            typer.echo("Created backup of current bookmarks")

        organizer.load_and_parse()
        organizer.preview_changes()

        if apply:
            typer.confirm("Apply these changes?", abort=True)
            organizer.organize(dry_run=False)
            save_path = output or file_path
            organizer.save_organized(save_path)
            typer.echo(f"Organization completed and saved to {save_path}")
        else:
            typer.echo("Dry run completed - no changes made")
            if output:
                organizer.save_organized(output)
                typer.echo(f"Saved organized version to {output}")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        sys.exit(1)


@app.command()
def analyze(
    file_path: Annotated[
        str, typer.Argument(help="Path to Safari bookmarks plist")
    ] = "~/Library/Safari/Bookmarks.plist",
    llm: Annotated[
        bool, typer.Option("--llm/--no-llm", help="Enable LLM categorization")
    ] = False,
    taxonomy: Annotated[
        Taxonomy, typer.Option(help="Category taxonomy", case_sensitive=False)
    ] = Taxonomy.default,
) -> None:
    """Analyze bookmark structure and suggest organization."""
    try:
        settings = _build_settings(llm=llm)
        organizer = BookmarkOrganizer(
            file_path, use_llm=llm, taxonomy=taxonomy.value, settings=settings
        )
        organizer.load_and_parse()

        plan = organizer.get_organization_plan()

        typer.echo("Bookmark Analysis:")
        typer.echo(f"Total bookmarks: {plan.total_bookmarks}")
        typer.echo(f"Categories found: {len(plan.categories)}")
        typer.echo(f"Suggested folders: {len(plan.folders_to_create)}")

        typer.echo("\nCategory Distribution:")
        for category, count in sorted(plan.categories.items(), key=lambda x: x[1], reverse=True):
            typer.echo(f"  {category}: {count} bookmarks")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        sys.exit(1)


@app.command()
def backup(
    file_path: Annotated[
        str, typer.Argument(help="Path to Safari bookmarks plist")
    ] = "~/Library/Safari/Bookmarks.plist",
    backup_path: Annotated[
        str | None, typer.Option("--backup-path", "-b", help="Custom backup file path")
    ] = None,
) -> None:
    """Create a backup of Safari bookmarks."""
    try:
        organizer = BookmarkOrganizer(file_path)
        organizer.backup_current(backup_path)
        save_path = backup_path or "bookmarks_backup.plist"
        typer.echo(f"Backup created at {save_path}")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        sys.exit(1)


@app.command()
def preview(
    file_path: Annotated[
        str, typer.Argument(help="Path to Safari bookmarks plist")
    ] = "~/Library/Safari/Bookmarks.plist",
    llm: Annotated[
        bool, typer.Option("--llm/--no-llm", help="Enable LLM categorization")
    ] = False,
    taxonomy: Annotated[
        Taxonomy, typer.Option(help="Category taxonomy", case_sensitive=False)
    ] = Taxonomy.default,
    host: Annotated[str, typer.Option(help="Preview server host")] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="Preview server port")] = 8000,
    open_browser: Annotated[
        bool, typer.Option("--open/--no-open", help="Open browser automatically")
    ] = True,
) -> None:
    """Launch a local preview UI for the proposed organization."""
    try:
        settings = _build_settings(llm=llm)
        run_preview(
            file_path,
            use_llm=llm,
            taxonomy=taxonomy.value,
            host=host,
            port=port,
            open_browser=open_browser,
            settings=settings,
        )
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        sys.exit(1)


def main() -> None:
    """Entry point for the CLI."""
    app()
