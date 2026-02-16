# Contributing

## Development Setup

1. Create a Python 3.11 virtual environment.
2. Install dependencies:
   ```bash
   pip install -e .[dev]
   ```
3. Run tests:
   ```bash
   pytest
   ```

## Agentic Workflow

- Follow `/Users/marcelpochert/Programming/ai/gemini-sync/AGENTS.md`.
- Use Red -> Green -> Refactor for code and scenario evals.
- Update mapped docs per `/Users/marcelpochert/Programming/ai/gemini-sync/docs/doc_sync_map.yaml`.

## Local Verification Commands

```bash
python scripts/validate_connectors.py
ruff check .
python scripts/check_tdd_guardrails.py
python scripts/check_docs_drift.py
python scripts/check_security_policy.py
python scripts/run_dependency_audit.py
pytest --cov=gemini_sync_bridge --cov-report=xml --cov-fail-under=60
diff-cover coverage.xml --compare-branch=origin/main --fail-under=92
python scripts/run_scenario_evals.py --registry evals/eval_registry.yaml --baseline evals/baseline.json
```

## Pull Request Checklist

- Add or update tests for behavior changes.
- Run the full local verification command set above.
- Keep connector schemas backward compatible unless the PR explicitly includes a version bump.
- Document operational changes in `README.md` and mapped docs.

## Commit Style

Use conventional commit prefixes (`feat:`, `fix:`, `docs:`, `chore:`) where practical.
