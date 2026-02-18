# Migration: Custom Connectors Out of Runtime Repo

This guide is for teams already using the previous structure where
environment-specific connector YAML files were committed directly in this
repository.

## What Changed

1. API, Ops, and Studio connector discovery now supports `CONNECTORS_DIR`.
2. This repo keeps curated examples under `connectors/`.
3. CI enforces:
   - allowlist drift check (`check_connector_examples_allowlist_drift.py`)
   - examples-only change guard (`check_connector_examples_only.py`)
4. Studio PR proposals should target a dedicated connector-config repository via `GITHUB_REPO`.

## Migration Goal

Move custom connector profiles to a separate connector-config repository (or an
external connectors directory) without changing connector schema or runtime
behavior.

## Preflight (Required)

Run from this runtime repo root:

```bash
python scripts/check_connector_examples_allowlist_drift.py
python scripts/check_connector_examples_only.py --changed-file connectors/examples-allowlist.txt
python scripts/validate_connectors.py
```

Expected:

1. allowlist drift check passes with empty `missing_in_allowlist` and `stale_allowlist_entries`.
2. examples-only guard passes for allowlist file touch.
3. connector schema validation passes.

## Step 1: Inventory Custom Connector Files

```bash
python - <<'PY'
from pathlib import Path

allowlist_path = Path("connectors/examples-allowlist.txt")
allowlisted = {
    line.strip()
    for line in allowlist_path.read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.strip().startswith("#")
}

existing = {f"connectors/{path.name}" for path in Path("connectors").glob("*.yaml")}
custom = sorted(existing - allowlisted)

print("Custom connectors to migrate:")
for item in custom:
    print(f"- {item}")

if not custom:
    print("- (none)")
PY
```

Expected:

1. Output lists only use-case-specific connector files under `Custom connectors to migrate`.
2. Curated examples (from allowlist) are not listed.

## Step 2: Create Connector-Config Repository Layout

Create a separate repository with this structure:

1. `connectors/*.yaml` for connector definitions.
2. Optional deployment metadata (if your org keeps config in the same repo).

Example path after clone:

`/srv/gemini-sync-connectors/connectors`

## Step 3: Copy Custom Connectors

Use this script to copy only non-allowlisted connector YAML files:

```bash
python - <<'PY'
from pathlib import Path
import shutil

target_root = Path("../gemini-sync-connectors").resolve()
target_connectors = target_root / "connectors"
target_connectors.mkdir(parents=True, exist_ok=True)

allowlisted = {
    line.strip()
    for line in Path("connectors/examples-allowlist.txt").read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.strip().startswith("#")
}

for source in sorted(Path("connectors").glob("*.yaml")):
    rel = f"connectors/{source.name}"
    if rel in allowlisted:
        continue
    shutil.copy2(source, target_connectors / source.name)
    print(f"Copied {source} -> {target_connectors / source.name}")
PY
```

Expected:

1. Each migrated connector is copied once.
2. No curated examples are copied.

## Step 4: Point Runtime Discovery to External Connectors

Set environment variables in staging deployment:

1. `CONNECTORS_DIR=/srv/gemini-sync-connectors/connectors`
2. `GITHUB_REPO=<org>/<connector-config-repo>`
3. Keep `GITHUB_TOKEN` and `GITHUB_BASE_BRANCH` as before.

Notes:

1. `gemini-sync-bridge run --connector <path>` already accepts explicit file paths.
2. Studio proposal payload paths remain `connectors/<connector-id>.yaml`, which aligns with the new connector-config repo structure.

## Step 5: Staging Verification Checklist

Validate at least one flow in each surface:

1. Studio catalog shows expected connectors: `GET /v1/studio/catalog`
2. Ops connector detail resolves migrated IDs: `GET /v1/ops/connectors/{connector_id}`
3. Manual run path resolves migrated connector definitions.
4. Studio proposal creates PRs in the connector-config repo.

Recommended verification commands:

```bash
curl -s http://localhost:8080/v1/studio/catalog | jq '.items | length'
curl -s http://localhost:8080/v1/ops/connectors/<connector_id> | jq '.connector_id'
gemini-sync-bridge run --connector /srv/gemini-sync-connectors/connectors/<connector_id>.yaml
```

Expected:

1. Studio returns items from external connector directory.
2. Ops connector detail resolves migrated connector IDs.
3. Manual run succeeds for migrated connector path.

## Step 6: Clean Runtime Repo Connector Folder

After staging verification:

1. Remove migrated custom connectors from this runtime repo.
2. Keep only curated examples listed in `connectors/examples-allowlist.txt`.
3. Keep future environment-specific connector edits in the connector-config repo.

Post-cleanup local checks:

```bash
python scripts/check_connector_examples_allowlist_drift.py
python scripts/check_connector_examples_only.py --changed-file connectors/examples-allowlist.txt
```

## Rollback

If issues appear after cutover:

1. Unset `CONNECTORS_DIR` (or set it back to `connectors`).
2. Temporarily point `GITHUB_REPO` back to prior target if needed.
3. Re-run a known-good connector from previous path.
4. Reapply migration after resolving path or permissions issues.

## Common Migration Issues

1. `404 Connector not found` in Studio/Ops:
`CONNECTORS_DIR` path is incorrect or not mounted in runtime environment.
2. Studio PR goes to wrong repo:
`GITHUB_REPO` is still set to runtime repo instead of connector-config repo.
3. CI fails with allowlist drift:
curated examples in `connectors/*.yaml` and `connectors/examples-allowlist.txt` are out of sync.
4. CI fails with examples-only connector guard:
custom connector edits are still being made under this repo `connectors/` folder.
