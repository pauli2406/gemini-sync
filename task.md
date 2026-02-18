# Task

- Task ID: file-pull-csv-support
- Title: Add `file_pull` mode with CSV file-storage extraction and extensible parser contract
- Owner Role: planner
- Risk Tier: tier_2

## Intent

Extend connector authoring and runtime from API/DB pull sources to local file-storage pull sources, starting with CSV, while preserving YAML mapping semantics and introducing a future parser extension hook.

## Acceptance Criteria

1. Connector contract supports `spec.mode=file_pull` and `spec.source.type=file`.
2. `file_pull` allows optional `source.secretRef`; existing modes keep `secretRef` required.
3. `file_pull` requires `source.path`, `source.glob`, `source.format=csv`, and `source.csv` config.
4. Runtime extracts CSV with `documentMode=row|file` and injects flat synthetic file metadata fields.
5. `file_pull` checkpoint persists compact JSON (`v/rw/fc/lm/fh`) in existing watermark column and accepts legacy plain watermark fallback.
6. Duplicate normalized `doc_id` values in `file_pull` fail the run.
7. Studio wizard and proposal generation support `file_pull`, including mode-switch pruning.
8. New tests/evals/docs/sample connector/artifacts are added and all local gates pass.

## Specialist Role Mapping

1. Planner Agent
   - Finalized scope, risk tier, acceptance criteria, and rollout constraints.
2. Implementer Agent
   - Updated schema, Pydantic contract, extractor logic, pipeline dispatch, Studio UI/logic, and sample connector.
3. Test/Eval Agent
   - Added schema/runtime/pipeline/studio tests and registered new scenario evals.
4. Docs Agent
   - Added file mode/provider docs and updated architecture/authoring/readme/sidebar/reference docs.
5. Security Agent
   - Preserved prompt-injection protections, validated non-recursive glob behavior, and passed policy/dependency/security gates.
6. Release Agent
   - Captured gate outcomes and rollout/rollback guidance in risk artifact.

## Scope

- In scope:
  - `file_pull` mode and CSV parser controls.
  - Compact checkpoint format in existing `connector_checkpoints.watermark`.
  - Studio authoring support, test/eval coverage, and docs updates.
- Out of scope:
  - PDF/unstructured parser implementation.
  - DB schema migration for structured checkpoint columns.
  - Non-local file sources (no direct `gs://` source reads).
