# Local Getting Started Guide

This guide takes you from a fresh clone to a successful local connector run.
It uses Docker Postgres and local `file://` artifacts, so you can start without
Google Cloud credentials.

## What You Will Run

- A local Postgres container for runtime state and sample source data
- The Gemini Sync Bridge CLI (`init-db`, `run`, `serve`)
- A local SQL pull connector writing artifacts to `./local-bucket`
- Ops and Studio UIs at `http://localhost:8080`

## 1) Prerequisites

- Python `3.11+`
- Docker + Docker Compose
- `git`
- `curl`

## 2) Install Dependencies

From the repository root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## 3) Start Postgres (Docker)

```bash
docker compose up -d postgres
docker compose ps postgres
docker compose logs --tail=30 postgres
```

Continue when logs show `database system is ready to accept connections`.

## 4) Configure Local Environment

```bash
cp .env.example .env
```

The default `.env.example` already enables local dry-run ingestion:

- `GEMINI_INGESTION_DRY_RUN=true`
- Runtime DB: `DATABASE_URL=.../gemini_sync_bridge`
- Source secret: `SECRET_HR_DB_CREDENTIALS=.../hr`

## 5) Initialize Runtime Tables

```bash
.venv/bin/gemini-sync-bridge init-db
```

Optional check:

```bash
docker compose exec -T postgres psql -U postgres -d gemini_sync_bridge -c "\\dt"
```

## 6) Seed Sample Source Data

Create the `hr` source database (safe to rerun):

```bash
docker compose exec -T postgres psql -U postgres -d postgres <<'SQL'
SELECT 'CREATE DATABASE hr'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'hr')\gexec
SQL
```

Create source table and seed records:

```bash
docker compose exec -T postgres psql -U postgres -d hr <<'SQL'
CREATE TABLE IF NOT EXISTS employees (
  employee_id BIGINT PRIMARY KEY,
  full_name TEXT NOT NULL,
  department TEXT NOT NULL,
  role TEXT NOT NULL,
  bio TEXT NOT NULL,
  allowed_users TEXT[] NOT NULL DEFAULT '{}',
  allowed_groups TEXT[] NOT NULL DEFAULT '{}',
  updated_at TIMESTAMPTZ NOT NULL
);

INSERT INTO employees (
  employee_id,
  full_name,
  department,
  role,
  bio,
  allowed_users,
  allowed_groups,
  updated_at
) VALUES
  (
    1001,
    'Ada Lovelace',
    'Engineering',
    'Staff Engineer',
    'Builds sync and ingestion workflows.',
    ARRAY['ada@company.test'],
    ARRAY['engineering'],
    NOW() - INTERVAL '1 hour'
  ),
  (
    1002,
    'Grace Hopper',
    'Platform',
    'Principal Engineer',
    'Owns reliability and release quality.',
    ARRAY['grace@company.test'],
    ARRAY['platform'],
    NOW()
  )
ON CONFLICT (employee_id) DO UPDATE
SET
  full_name = EXCLUDED.full_name,
  department = EXCLUDED.department,
  role = EXCLUDED.role,
  bio = EXCLUDED.bio,
  allowed_users = EXCLUDED.allowed_users,
  allowed_groups = EXCLUDED.allowed_groups,
  updated_at = EXCLUDED.updated_at;
SQL
```

## 7) Create a Local Connector Config

Create a local connector file so you do not modify tracked samples:

```bash
cat > connectors/hr-employees-local.yaml <<'YAML'
apiVersion: sync.gemini.io/v1alpha1
kind: Connector
metadata:
  name: hr-employees-local
spec:
  mode: sql_pull
  schedule: "0 */3 * * *"
  source:
    type: postgres
    secretRef: hr-db-credentials
    query: >
      SELECT employee_id, full_name, department, role, bio, allowed_users, allowed_groups, updated_at
      FROM employees
    watermarkField: updated_at
  mapping:
    idField: employee_id
    titleField: full_name
    contentTemplate: "{{ department }} {{ role }} {{ bio }}"
    uriTemplate: "https://hr.internal/employees/{{ employee_id }}"
    aclUsersField: allowed_users
    aclGroupsField: allowed_groups
    metadataFields:
      - department
      - role
  output:
    bucket: file://./local-bucket
    prefix: hr-employees-local
    format: ndjson
  gemini:
    projectId: local-dev
    location: global
    dataStoreId: hr-local
  reconciliation:
    deletePolicy: auto_delete_missing
YAML
```

## 8) Validate and Run

```bash
mkdir -p local-bucket
python scripts/validate_connectors.py
.venv/bin/gemini-sync-bridge run --connector connectors/hr-employees-local.yaml
```

Expected first run:

- `upserts` should be `2`
- `deletes` should be `0`

## 9) Verify Local Artifacts

```bash
find local-bucket/connectors/hr-employees-local -maxdepth 4 -type f | sort
cat local-bucket/connectors/hr-employees-local/state/latest_success.json
```

Read latest run files:

```bash
RUN_ID="$(python3 - <<'PY'
import json
from pathlib import Path

state = Path("local-bucket/connectors/hr-employees-local/state/latest_success.json")
print(json.loads(state.read_text(encoding="utf-8"))["run_id"])
PY
)"

cat "local-bucket/connectors/hr-employees-local/runs/${RUN_ID}/manifest.json"
head -n 2 "local-bucket/connectors/hr-employees-local/runs/${RUN_ID}/upserts.ndjson"
```

## 10) Start API + UIs

Run the API server:

```bash
.venv/bin/gemini-sync-bridge serve --host 0.0.0.0 --port 8080
```

In another terminal:

```bash
curl -s http://localhost:8080/healthz
curl -s "http://localhost:8080/v1/ops/snapshot?window_hours=168&limit_runs=5" | python3 -m json.tool | head -n 40
```

Open:

- Ops dashboard: `http://localhost:8080/ops`
- Studio: `http://localhost:8080/studio/connectors`
- Connector detail: `http://localhost:8080/ops/connectors/hr-employees-local`

## 11) Optional: REST Push Smoke Test

Create a local push connector:

```bash
cat > connectors/support-push-local.yaml <<'YAML'
apiVersion: sync.gemini.io/v1alpha1
kind: Connector
metadata:
  name: support-push-local
spec:
  mode: rest_push
  source:
    type: http
    secretRef: support-push-token
  mapping:
    idField: ticket_id
    titleField: title
    contentTemplate: "{{ subject }} {{ body }}"
    uriTemplate: "https://support.internal/tickets/{{ ticket_id }}"
    aclUsersField: allowed_users
    aclGroupsField: allowed_groups
  output:
    bucket: file://./local-bucket
    prefix: support-push-local
    format: ndjson
  gemini:
    projectId: local-dev
    location: global
    dataStoreId: support-local
  reconciliation:
    deletePolicy: auto_delete_missing
YAML
```

Send events:

```bash
curl -X POST "http://localhost:8080/v1/connectors/support-push-local/events" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: local-run-001" \
  -d '[
    {
      "doc_id":"support-push-local:123",
      "title":"VPN issue",
      "content":"Cannot connect from home",
      "uri":"https://support.internal/tickets/123",
      "mime_type":"text/plain",
      "updated_at":"2026-02-16T08:30:00Z",
      "acl_users":[],
      "acl_groups":["it-support"],
      "metadata":{"connector_id":"support-push-local"},
      "checksum":"sha256:test",
      "op":"UPSERT"
    }
  ]'
```

Process queued push batch:

```bash
.venv/bin/gemini-sync-bridge run --connector connectors/support-push-local.yaml
```

## 12) Local Quality Gates (Optional)

```bash
python scripts/check_tdd_guardrails.py
python scripts/check_docs_drift.py
python scripts/check_openapi_drift.py
python scripts/check_connector_reference_drift.py
python scripts/check_security_policy.py
python scripts/run_dependency_audit.py
```

## 13) Stop and Reset

Stop local services:

```bash
docker compose down
```

Remove local artifacts and runtime DB state:

```bash
rm -rf local-bucket
docker compose down -v
```
