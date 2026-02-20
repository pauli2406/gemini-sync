# Risk Tier

- Assigned Tier: Tier 2
- Rationale:
  - Runtime behavior changed in `gemini_sync_bridge/services/pipeline.py` and `gemini_sync_bridge/services/publisher.py`.
  - Connector contract changed in `schemas/connector.schema.json`.
- Required Controls:
  - Schema validation, targeted pytest coverage, eval scenario registration, docs synchronization.
- Merge Constraints:
  - Tier 2 requires all quality gates plus reviewer bot and human review per policy.
