#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gemini_sync_bridge.services.replay import FaultInjectionError, replay_artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay run artifacts to validate determinism")
    parser.add_argument("--upserts", required=True)
    parser.add_argument("--deletes", required=True)
    parser.add_argument("--expected-digest", default=None)
    parser.add_argument("--write-digest", default=None)
    parser.add_argument("--fault-step", default=None)
    args = parser.parse_args()

    try:
        digest = replay_artifacts(
            upserts_path=args.upserts,
            deletes_path=args.deletes,
            fault_step=args.fault_step,
        )
    except FaultInjectionError as exc:
        print(json.dumps({"passed": False, "error": str(exc)}, indent=2))
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    passed = True
    if args.expected_digest and digest != args.expected_digest:
        passed = False

    if args.write_digest:
        Path(args.write_digest).write_text(digest, encoding="utf-8")

    output = {
        "passed": passed,
        "digest": digest,
        "expected_digest": args.expected_digest,
    }
    print(json.dumps(output, indent=2, sort_keys=True))

    if not passed:
        print("ERROR: replay digest did not match expected value", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
