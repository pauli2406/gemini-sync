# Splunk Dashboard Queries

## Run Success Rate

```spl
source="gemini-sync-bridge" event.status=* 
| timechart span=1h count by event.status
```

## Top Failing Connectors

```spl
source="gemini-sync-bridge" event.status="FAILED"
| stats count by event.connector_id, event.error_class
| sort - count
```

## Freshness (Checkpoint Lag Proxy)

Use DB-exported checkpoint events or enrich run success events with checkpoint timestamp:

```spl
source="gemini-sync-bridge" event.status="SUCCESS"
| eval lag_seconds=now()-strptime(event.finished_at, "%Y-%m-%dT%H:%M:%S%z")
| stats avg(lag_seconds), p95(lag_seconds) by event.connector_id
```
