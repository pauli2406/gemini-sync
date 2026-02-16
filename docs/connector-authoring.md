# Connector Authoring Guide

## Required Fields

Every connector file under `connectors/` must include:

- `apiVersion: sync.gemini.io/v1alpha1`
- `kind: Connector`
- `metadata.name`
- `spec.mode`
- `spec.source`
- `spec.mapping`
- `spec.output`
- `spec.gemini`
- `spec.reconciliation`

## Mode Selection

- `sql_pull`: query databases with watermark-based incremental extraction.
- `rest_pull`: pull data from APIs, optionally with cursor pagination.
- `rest_push`: receive canonical docs via API and process queued batches.

## Secret Resolution

`spec.source.secretRef` maps to env vars:

- `secretRef: hr-db-credentials` -> `SECRET_HR_DB_CREDENTIALS`

## Mapping Semantics

- `idField`: unique per source record.
- `titleField`: title text.
- `contentTemplate`: Jinja2 template from source fields.
- `uriTemplate`: optional source URI.
- `aclUsersField` / `aclGroupsField`: optional ACL fields.

## Validation

Run before committing connector changes:

```bash
python scripts/validate_connectors.py
```

## Example

See:
- `connectors/hr-employees.yaml`
- `connectors/kb-rest.yaml`
- `connectors/support-push.yaml`
