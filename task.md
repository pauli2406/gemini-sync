# Task

- Task ID: docs-hard-cutover-diataxis
- Title: Full docs hard-cutover rewrite (Diataxis + Docusaurus + README + llm)
- Owner Role: planner
- Risk Tier: tier_2

## Intent

Execute a full, English-only docs rewrite with hard URL cutover to Diataxis structure, while keeping generated reference artifacts and drift gates intact.

## Acceptance Criteria

1. Docs are fully reorganized into tutorials/how-to/concepts/reference/contributing sections.
2. Legacy flat docs files are removed after migration.
3. Docusaurus nav uses `Docs`, `Reference`, `Contributing`, `Changelog`.
4. Connector reference export/check defaults point to `docs/reference/connector-fields.md`.
5. README and llm.txt are fully rewritten to the new model.
6. Docs drift mapping is updated to new paths and required consistency tokens remain enforced.
7. Required quality/security/docs checks pass.

## Specialist Role Mapping

1. Planner Agent
   - Finalized cutover scope, constraints, and acceptance criteria.
2. Test/Eval Agent
   - Added default-path tests for connector reference scripts.
   - Updated connector reference drift scenario expectations.
3. Implementer Agent
   - Rewrote docs tree and Docusaurus navigation/homepage.
   - Updated script defaults and governance map.
4. Docs Agent
   - Reauthored all pages under new IA and added changelog page.
5. Security Agent
   - Runs policy and dependency audit in validation set.
6. Release Agent
   - Confirms docs build and gate outcomes; tier 2 merge constraints apply.
