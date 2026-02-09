from pathlib import Path

import pytest
from click.testing import CliRunner

from safari_bookmark_organizer.cli import main


def test_cli_analyze_and_organize(tmp_path: Path):
    backup = Path("bookmarks_backup.plist")
    if not backup.exists():
        pytest.skip("bookmarks_backup.plist not present in repo")

    runner = CliRunner()
    result = runner.invoke(main, ["analyze", str(backup)])
    assert result.exit_code == 0

    output_path = tmp_path / "organized.plist"
    result = runner.invoke(
        main,
        ["organize", str(backup), "--dry-run", "--output", str(output_path)],
    )
    assert result.exit_code == 0
    assert output_path.exists()
