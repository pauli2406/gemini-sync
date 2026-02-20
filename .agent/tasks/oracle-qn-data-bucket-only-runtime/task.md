# Task

- Task ID: oracle-qn-data-bucket-only-runtime
- Title: Add bucket-only connector mode, latest alias artifacts, and SQL-to-CSV export
- Planner Agent: Scoped per-connector ingestion toggle, latest alias strategy, and raw CSV export behavior.
- Implementer Agent: Updated schema, runtime pipeline, publisher, docs, tests, and eval scenario.
- Test/Eval Agent: Added schema/runtime unit tests and scenario registration.
- Docs Agent: Updated README and connector authoring/SQL pull guidance.
- Security Agent: Ensured no secret values introduced; secretRef model preserved.
- Release Agent: Classified runtime + schema changes with non-critical scenario addition.
- Risk Tier: Tier 2 (runtime/API + schema behavior)

## Intent

Support connectors that publish artifacts to GCS only (no Discovery Engine ingestion yet), optionally overwrite stable latest artifact aliases, and allow `sql_pull` connectors to export raw SQL rows as CSV without mapping.
