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

## Pull Request Checklist

- Add or update tests for behavior changes.
- Run `pytest` and `ruff check .`.
- Keep connector schemas backward compatible unless the PR explicitly includes a version bump.
- Document operational changes in `README.md`.

## Commit Style

Use conventional commit prefixes (`feat:`, `fix:`, `docs:`, `chore:`) where practical.
