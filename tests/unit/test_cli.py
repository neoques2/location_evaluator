import subprocess
import sys
from pathlib import Path


def test_cli_dry_run():
    repo_root = Path(__file__).resolve().parents[2]
    main_path = repo_root / 'main.py'
    result = subprocess.run([sys.executable, str(main_path), '--dry-run'], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'Grid Configuration:' in result.stdout
