#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any


def run_once(selector: str | None) -> dict[str, Any]:
    cmd = ["pytest", "-q"]
    if selector:
        cmd.append(selector)

    result = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Simple flaky test detector")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--selector", default=None)
    args = parser.parse_args()

    runs = [run_once(args.selector) for _ in range(args.runs)]
    return_codes = [entry["returncode"] for entry in runs]
    flaky = len(set(return_codes)) > 1

    output = {
        "runs": args.runs,
        "selector": args.selector,
        "return_codes": return_codes,
        "flaky_detected": flaky,
    }
    print(json.dumps(output, indent=2, sort_keys=True))

    if flaky:
        print("ERROR: flaky behavior detected across repeated pytest runs", file=sys.stderr)
        return 1

    if any(code != 0 for code in return_codes):
        print("ERROR: tests failed consistently", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
