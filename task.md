# Task

- Task ID: stage2-module-hard-cutover
- Title: Full Python module rename from gemini_sync_bridge to ingest_relay
- Owner Role: planner
- Risk Tier: tier_3

## Intent

Complete stage 2 of the IngestRelay rename by hard-cutover renaming the Python package directory and namespace from `gemini_sync_bridge` to `ingest_relay`, including imports, packaging metadata, workflow paths, coverage flags, and governance gate patterns.

## Acceptance Criteria

1. Package directory is renamed to `ingest_relay/` and no active runtime/tests/scripts import `gemini_sync_bridge`.
2. `pyproject.toml` console script points to `ingest_relay.cli:app` and wheel package/include paths use `ingest_relay/**`.
3. Uvicorn app path in CLI uses `ingest_relay.api:app`.
4. CI/docs/workflows use `--cov=ingest_relay` and docs deploy trigger path `ingest_relay/api.py`.
5. Governance patterns are updated from `gemini_sync_bridge/**` to `ingest_relay/**` in gate/policy mapping files.
6. Red phase evidence captures expected failure before package move; full gate suite is green after cutover.
7. Historical `.agent/tasks/*` files remain unchanged.

## Specialist Role Mapping

1. Planner Agent
   - Sequenced hard-cutover namespace migration and governed scope (active files only).
2. Implementer Agent
   - Renamed package directory, updated imports/references, and migrated packaging/workflow paths.
3. Test/Eval Agent
   - Updated tests first, captured failing-first import error, then validated green test/eval gates.
4. Docs Agent
   - Updated active docs and references to `ingest_relay` paths and coverage commands.
5. Security Agent
   - Re-ran security policy and dependency audit checks after namespace migration.
6. Release Agent
   - Maintained Tier 3 classification and verified all required gates for release readiness.
