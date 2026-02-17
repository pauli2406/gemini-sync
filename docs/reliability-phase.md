# Reliability Phase

This phase focuses on three outcomes:

1. Expanded source adapter test matrix.
2. Deterministic replay and fault-injection harness.
3. Operational SLO dashboards tied to release gates.

## Expanded Adapter Test Matrix

Current coverage includes:

- SQL pull extraction and watermark progression.
- REST pull pagination and cursor handling.
- Retry behavior under transient 429 conditions.

Key tests:

- `tests/test_extractors_sql.py`
- `tests/test_extractors_rest_pull.py`
- `tests/test_extractors_retry.py`

## Deterministic Replay and Fault Injection

Replay digest command:

```bash
python scripts/replay_run_artifacts.py \
  --upserts file://./local-bucket/connectors/hr-employees/runs/<run_id>/upserts.ndjson \
  --deletes file://./local-bucket/connectors/hr-employees/runs/<run_id>/deletes.ndjson
```

Fault injection example:

```bash
python scripts/replay_run_artifacts.py \
  --upserts file://./local-bucket/connectors/hr-employees/runs/<run_id>/upserts.ndjson \
  --deletes file://./local-bucket/connectors/hr-employees/runs/<run_id>/deletes.ndjson \
  --fault-step load_upserts
```

## SLO Metrics and Gate

Generate report:

```bash
python scripts/generate_slo_report.py --database-url "$DATABASE_URL" --output slo-metrics.json
```

Evaluate thresholds:

```bash
python scripts/check_slo_gate.py --metrics slo-metrics.json
```

Default thresholds:

- success rate >= 99%
- max freshness lag `<= 10800` seconds
- MTTR `<= 1800` seconds

## Workflow Integration

- `.github/workflows/nightly-evals.yaml` optionally runs SLO report + gate when `DATABASE_URL` is set.
- `.github/workflows/release-canary.yaml` requires both canary and SLO metric payloads for release gating.
