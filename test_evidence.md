# Test Evidence

## Red Phase Evidence

- Behavior-impacting code was not changed, so failing-first runtime tests/evals were not required.
- Pre-change docs reference scan showed migration page links in docs/nav/map files.

## Green Phase Evidence

- `rg -n "migrate-custom-connectors|Migrate Custom Connectors" docs website llm.txt`
  - Result: no matches after the doc removal and link cleanup.
- `./.venv/bin/python scripts/check_docs_drift.py`
  - Result: pass.
- `npm --prefix website run build`
  - Result: pass; static docs build generated successfully.
- `cd website && vercel build --yes`
  - Result before workflow fix: fails reproducibly with `Error: spawn sh ENOENT`.
- Workflow update removes local `vercel build` usage and deploys with `vercel deploy` directly.

## Commands

```bash
./.venv/bin/python scripts/check_docs_drift.py
rg -n "migrate-custom-connectors|Migrate Custom Connectors" docs website llm.txt
npm --prefix website run build
cd website && vercel build --yes
```
