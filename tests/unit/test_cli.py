import subprocess
import sys


def test_cli_dry_run():
    result = subprocess.run(
        [sys.executable, "main.py", "--dry-run"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "Grid Configuration:" in result.stdout
