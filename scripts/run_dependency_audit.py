#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile

EXCLUDED_PACKAGES = {
    "pip",
    "setuptools",
    "wheel",
    "gemini-sync-bridge",
}


def main() -> int:
    list_result = subprocess.run(
        ["pip", "list", "--format=json"],
        capture_output=True,
        text=True,
        check=True,
    )
    packages = json.loads(list_result.stdout)

    pinned = [
        f"{pkg['name']}=={pkg['version']}"
        for pkg in packages
        if pkg["name"].lower() not in EXCLUDED_PACKAGES
    ]

    if not pinned:
        print("No packages to audit.")
        return 0

    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
        handle.write("\n".join(sorted(pinned)))
        requirements_path = handle.name

    result = subprocess.run(
        ["pip-audit", "--requirement", requirements_path, "--progress-spinner", "off"],
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
