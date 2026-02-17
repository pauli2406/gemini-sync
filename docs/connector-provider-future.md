# Future Provider Placeholders

This page documents roadmap placeholders only.

## Status

Not supported in current runtime.

## Planned placeholders

- BigQuery
- Snowflake
- Oracle

## Intended future shape

Expected direction for future provider support:

1. New `source.type` values in schema and runtime adapters.
2. Provider-specific auth/secret conventions.
3. Provider-specific extraction semantics and pagination/cursor behavior.
4. Mode compatibility definitions and reconciliation guidance.

## Workaround guidance (today)

Until these providers are implemented:

1. Use currently supported providers:
   - SQL: `postgres`, `mysql`, `mssql`
   - API: `http`
2. If source is unsupported, create an upstream export step that writes to a supported source:
   - push canonical docs via `rest_push`, or
   - expose a compatible REST endpoint for `rest_pull`.

## Important note

Do not configure unsupported `source.type` values in production connectors. Validation/runtime will reject unsupported provider types.
