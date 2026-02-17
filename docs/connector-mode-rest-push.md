# REST Push Connector Mode

## When to use this mode

Use `rest_push` when upstream systems push canonical documents into Gemini Sync Bridge instead of being polled.

Best fit:

- Source systems can send events/webhooks.
- You want idempotent push ingestion.
- You need explicit `UPSERT`/`DELETE` control from producers.

## Minimal YAML (copy/paste)

```yaml
apiVersion: sync.gemini.io/v1alpha1
kind: Connector
metadata:
  name: support-push
spec:
  mode: rest_push
  source:
    type: http
    secretRef: support-push-token
  mapping:
    idField: ticket_id
    titleField: title
    contentTemplate: "{{ subject }} {{ body }}"
  output:
    bucket: gs://company-gemini-sync
    prefix: support-push
    format: ndjson
  gemini:
    projectId: my-project
    location: global
    dataStoreId: support-ds
  reconciliation:
    deletePolicy: auto_delete_missing
```

## Full YAML (annotated)

```yaml
apiVersion: sync.gemini.io/v1alpha1
kind: Connector
metadata:
  name: support-push
spec:
  mode: rest_push
  source:
    type: http
    secretRef: support-push-token # schema-required in v1
  mapping:
    idField: ticket_id
    titleField: title
    contentTemplate: "{{ subject }} {{ body }}"
    uriTemplate: "https://support.internal/tickets/{{ ticket_id }}"
    mimeType: text/plain
    aclUsersField: allowed_users
    aclGroupsField: allowed_groups
    metadataFields:
      - queue
      - priority
  output:
    bucket: gs://company-gemini-sync
    prefix: support-push
    format: ndjson
  gemini:
    projectId: my-project
    location: global
    dataStoreId: support-ds
  reconciliation:
    deletePolicy: auto_delete_missing
```

## Field-by-field explanation

| Field | Meaning | Options |
|---|---|---|
| `spec.mode` | Enables push queue processing mode. | `rest_push` |
| `spec.source.type` | Must be HTTP in this mode. | `http` |
| `spec.source.secretRef` | Schema-required reference; ingress auth is not enforced in v1. | Any non-empty string. |
| `spec.mapping.*` | Used for draft validation/preview and consistency with other modes. | Same mapping fields as pull connectors. |
| `spec.reconciliation.deletePolicy` | Keep explicit to document delete intent. | `auto_delete_missing`, `soft_delete_only`, `never_delete` |

## Mode-specific decision matrix

| Producer behavior | Recommended `op` values | Use? | Why |
|---|---|---|---|
| Sends full current state on each push | `UPSERT` (and optional `DELETE`) | Yes | Deterministic index sync. |
| Sends deltas only | `UPSERT` + explicit `DELETE` | Yes (recommended) | Avoids ambiguity for removals. |
| Sends only UPSERT and never DELETE | `UPSERT` only | Yes | Works, but stale docs remain unless separately cleaned up. |

| Queue/run state | Expected result |
|---|---|
| Pending events exist | `run` consumes queue and writes upserts/deletes artifacts. |
| No pending events | Run completes with `upserts=0` and `deletes=0`. |

## Validation checklist

1. Connector mode is `rest_push`.
2. Push endpoint caller sets `Idempotency-Key`.
3. Payload documents contain canonical fields and `op` value.
4. Trigger processing run (`run now` in Studio or CLI/orchestrator run).
5. Run `python scripts/validate_connectors.py`.

## Common failures and fixes

- Missing `Idempotency-Key`
  - Add header on every producer request.
- Duplicate events applied unexpectedly
  - Reuse the same idempotency key for retries of the same batch.
- Push accepted but no ingestion happened
  - Trigger connector run to process pending queue.
- Confusion about `source.secretRef`
  - In v1 it is schema-required but not used as ingress authentication control.

## Provider notes and links

- HTTP provider details: `docs/connector-provider-http.md`
- API reference: `docs/api-reference.mdx`
- Full field table: `docs/connector-field-reference.md`
