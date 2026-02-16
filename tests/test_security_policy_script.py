from __future__ import annotations

import subprocess
import sys


def test_security_policy_script_passes_for_repo_defaults() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/check_security_policy.py",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
