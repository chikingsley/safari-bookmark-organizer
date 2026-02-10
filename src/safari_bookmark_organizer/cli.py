"""
Command Line Interface

CLI for the Safari Bookmark Organizer.
"""

import os
import sys
from pathlib import Path

import click
from loguru import logger

from .bookmark_parser import BookmarkParser
from .organizer import BookmarkOrganizer
from .preview import run_preview


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Safari Bookmark Organizer CLI."""
    pass


@main.command()
@click.argument('file_path', type=click.Path(), default="~/Library/Safari/Bookmarks.plist")
@click.option('--output', '-o', type=click.Path(), help='Output file path')
def parse(file_path, output):
    """Parse Safari bookmarks file."""
    try:
        parser = BookmarkParser(file_path)
        parser.load()
        parser.parse()
        
        click.echo(f"✅ Parsed {len(parser.bookmarks)} bookmarks and {len(parser.folders)} folders")
        
        if output:
            parser.save_to_file(output)
            click.echo(f"📁 Saved to {output}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument('file_path', type=click.Path(), default="~/Library/Safari/Bookmarks.plist")
@click.option('--apply', 'dry_run', flag_value=False, default=True, help='Apply changes to the bookmarks file')
@click.option('--dry-run', 'dry_run', flag_value=True, help='Preview changes without applying (default)')
@click.option('--opencode/--no-opencode', default=True, help='Enable OpenCode categorization')
@click.option('--model', type=str, help='Override OpenCode model (OPENCODE_MODEL)')
@click.option('--output', '-o', type=click.Path(), help='Output file for organized bookmarks')
@click.option('--backup', '-b', is_flag=True, help='Create backup before organizing')
def organize(file_path, dry_run, opencode, model, output, backup):
    """Organize Safari bookmarks using AI categorization."""
    try:
        if model:
            os.environ["OPENCODE_MODEL"] = model
        organizer = BookmarkOrganizer(file_path, use_opencode=opencode)
        
        # Create backup if requested
        if backup:
            organizer.backup_current()
            click.echo("💾 Created backup of current bookmarks")
        
        # Load and parse
        organizer.load_and_parse()
        
        # Preview changes
        organizer.preview_changes()
        
        if not dry_run:
            click.confirm('⚠️  Apply these changes?', abort=True)
            
            # Organize
            organizer.organize(dry_run=False)
            
            # Save
            save_path = output or file_path
            organizer.save_organized(save_path)
            
            click.echo(f"✅ Organization completed and saved to {save_path}")
        else:
            click.echo("📝 Dry run completed - no changes made")
            
            if output:
                organizer.save_organized(output)
                click.echo(f"📁 Saved organized version to {output}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument('file_path', type=click.Path(), default="~/Library/Safari/Bookmarks.plist")
@click.option('--opencode/--no-opencode', default=True, help='Enable OpenCode categorization')
@click.option('--model', type=str, help='Override OpenCode model (OPENCODE_MODEL)')
def analyze(file_path, opencode, model):
    """Analyze bookmark structure and suggest organization."""
    try:
        if model:
            os.environ["OPENCODE_MODEL"] = model
        organizer = BookmarkOrganizer(file_path, use_opencode=opencode)
        organizer.load_and_parse()
        
        plan = organizer.get_organization_plan()
        
        click.echo("📊 Bookmark Analysis:")
        click.echo(f"Total bookmarks: {plan['total_bookmarks']}")
        click.echo(f"Categories found: {len(plan['categories'])}")
        click.echo(f"Suggested folders: {len(plan['folders_to_create'])}")
        
        click.echo("\n📁 Category Distribution:")
        for category, count in sorted(plan['categories'].items(), key=lambda x: x[1], reverse=True):
            click.echo(f"  {category}: {count} bookmarks")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument('file_path', type=click.Path(), default="~/Library/Safari/Bookmarks.plist")
@click.option('--backup-path', '-b', type=click.Path(), help='Custom backup file path')
def backup(file_path, backup_path):
    """Create a backup of Safari bookmarks."""
    try:
        organizer = BookmarkOrganizer(file_path)
        organizer.backup_current(backup_path)
        
        save_path = backup_path or "bookmarks_backup.plist"
        click.echo(f"💾 Backup created at {save_path}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument('file_path', type=click.Path(), default="~/Library/Safari/Bookmarks.plist")
@click.option('--opencode/--no-opencode', default=True, help='Enable OpenCode categorization')
@click.option('--model', type=str, help='Override OpenCode model (OPENCODE_MODEL)')
@click.option('--host', type=str, default="127.0.0.1", show_default=True, help='Preview server host')
@click.option('--port', type=int, default=8000, show_default=True, help='Preview server port')
@click.option('--open/--no-open', "open_browser", default=True, help='Open browser automatically')
def preview(file_path, opencode, model, host, port, open_browser):
    """Launch a local preview UI for the proposed organization."""
    try:
        run_preview(file_path, use_opencode=opencode, model=model, host=host, port=port, open_browser=open_browser)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
