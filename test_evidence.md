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

## Commands

```bash
./.venv/bin/python scripts/check_docs_drift.py
rg -n "migrate-custom-connectors|Migrate Custom Connectors" docs website llm.txt
npm --prefix website run build
```
