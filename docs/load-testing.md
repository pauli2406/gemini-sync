# Load Testing Guide (100 Connectors)

## Goal

Validate sustained operation for 100 connectors with mixed schedules over 24 hours.

## Suggested Test Mix

- 40 x `sql_pull` connectors (3-hour schedule)
- 40 x `rest_pull` connectors (30-minute schedule)
- 20 x `rest_push` connectors (5-minute processor schedule)

## Metrics to Track

- run success rate (`run_state.status`)
- freshness lag by connector (`connector_checkpoints.updated_at`)
- mean/95th runtime per connector
- queue depth for push events (`push_batches.status = PENDING`)

## Pass Criteria

- no sustained backlog growth for push batches
- 99%+ success rate over 24h
- freshness `<= 3h` for scheduled connectors
- no checkpoint advancement on failed runs

## Execution Pattern

1. Deploy with Helm and seed 100 connector definitions.
2. Enable Splunk dashboards for run metrics.
3. Run a 24h synthetic source workload.
4. Export `run_state` and compare to SLO thresholds.
