#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from ingest_relay.services.slo import compute_slo_metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate SLO report from run state")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--window-hours", type=int, default=24 * 7)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    engine = create_engine(args.database_url, future=True)
    with Session(engine) as session:
        metrics = compute_slo_metrics(session=session, window_hours=args.window_hours)

    payload = metrics.to_dict()
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    print(rendered)

    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
