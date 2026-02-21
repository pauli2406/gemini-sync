#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time

from ingest_relay.schemas import MappingConfig
from ingest_relay.services.normalizer import normalize_records


def main() -> int:
    parser = argparse.ArgumentParser(description="Performance smoke benchmark for normalization")
    parser.add_argument("--records", type=int, default=1000)
    parser.add_argument("--max-seconds", type=float, default=2.0)
    args = parser.parse_args()

    mapping = MappingConfig(
        idField="employee_id",
        titleField="full_name",
        contentTemplate="{{ department }} {{ role }} {{ bio }}",
        uriTemplate="https://example.local/{{ employee_id }}",
        metadataFields=["department"],
    )

    rows = [
        {
            "employee_id": idx,
            "full_name": f"Employee {idx}",
            "department": "Engineering",
            "role": "Developer",
            "bio": "Writes code",
            "updated_at": "2026-02-16T08:30:00Z",
        }
        for idx in range(args.records)
    ]

    start = time.perf_counter()
    docs = normalize_records(
        connector_id="perf-smoke",
        mapping=mapping,
        source_watermark_field="updated_at",
        rows=rows,
    )
    elapsed = time.perf_counter() - start

    payload = {
        "records": args.records,
        "documents_produced": len(docs),
        "elapsed_seconds": elapsed,
        "max_seconds": args.max_seconds,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))

    return 0 if elapsed <= args.max_seconds else 1


if __name__ == "__main__":
    raise SystemExit(main())
