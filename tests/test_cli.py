from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from safari_bookmark_organizer.cli import app

runner = CliRunner()


class TestVersionAndHelp:
    def test_version(self) -> None:
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_help(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "parse" in result.output
        assert "organize" in result.output
        assert "analyze" in result.output
        assert "backup" in result.output
        assert "preview" in result.output


class TestParseCommand:
    def test_parse_valid_file(self, make_plist, minimal_plist_data) -> None:
        path = make_plist(minimal_plist_data)
        result = runner.invoke(app, ["parse", str(path)])
        assert result.exit_code == 0
        assert "Parsed" in result.output
        assert "2 bookmarks" in result.output

    def test_parse_with_output(self, make_plist, minimal_plist_data, tmp_path: Path) -> None:
        path = make_plist(minimal_plist_data)
        out = tmp_path / "output.json"
        result = runner.invoke(app, ["parse", str(path), "--output", str(out)])
        assert result.exit_code == 0
        assert out.exists()
        assert "Saved to" in result.output

    def test_parse_nonexistent_file(self) -> None:
        result = runner.invoke(app, ["parse", "/tmp/nonexistent_xyz.plist"])
        assert result.exit_code != 0


class TestBackupCommand:
    def test_backup_creates_file(self, make_plist, sample_plist_data, tmp_path: Path) -> None:
        path = make_plist(sample_plist_data)
        backup_path = tmp_path / "backup.plist"
        result = runner.invoke(app, ["backup", str(path), "--backup-path", str(backup_path)])
        assert result.exit_code == 0
        assert backup_path.exists()
        assert "Backup created" in result.output


class TestAnalyzeCommand:
    def test_analyze_valid_file(self, make_plist, sample_plist_data) -> None:
        path = make_plist(sample_plist_data)
        result = runner.invoke(app, ["analyze", str(path), "--no-llm"])
        assert result.exit_code == 0
        assert "Bookmark Analysis" in result.output
        assert "Total bookmarks" in result.output

    def test_analyze_with_taxonomy(self, make_plist, sample_plist_data) -> None:
        path = make_plist(sample_plist_data)
        result = runner.invoke(
            app, ["analyze", str(path), "--no-llm", "--taxonomy", "opinionated"]
        )
        assert result.exit_code == 0

    def test_analyze_nonexistent_file(self) -> None:
        result = runner.invoke(app, ["analyze", "/tmp/nonexistent_xyz.plist", "--no-llm"])
        assert result.exit_code != 0


class TestOrganizeCommand:
    def test_organize_dry_run_default(self, make_plist, sample_plist_data) -> None:
        path = make_plist(sample_plist_data)
        result = runner.invoke(app, ["organize", str(path), "--no-llm"])
        assert result.exit_code == 0
        assert "Dry run" in result.output or "dry run" in result.output.lower()

    def test_organize_with_output(self, make_plist, sample_plist_data, tmp_path: Path) -> None:
        path = make_plist(sample_plist_data)
        out = tmp_path / "organized.plist"
        result = runner.invoke(app, ["organize", str(path), "--no-llm", "--output", str(out)])
        assert result.exit_code == 0
        assert out.exists()

    def test_organize_with_backup(self, make_plist, sample_plist_data, tmp_path: Path) -> None:
        path = make_plist(sample_plist_data)
        result = runner.invoke(app, ["organize", str(path), "--no-llm", "--backup"])
        assert result.exit_code == 0
        assert "backup" in result.output.lower()


class TestIntegrationWithRealFile:
    """Integration tests using a real bookmarks file if available."""

    def test_cli_analyze_and_organize(self, tmp_path: Path) -> None:
        backup = Path("bookmarks_backup.plist")
        if not backup.exists():
            pytest.skip("bookmarks_backup.plist not present in repo")

        result = runner.invoke(app, ["analyze", str(backup), "--no-llm"])
        assert result.exit_code == 0

        output_path = tmp_path / "organized.plist"
        result = runner.invoke(
            app,
            ["organize", str(backup), "--output", str(output_path), "--no-llm"],
        )
        assert result.exit_code == 0
        assert output_path.exists()
