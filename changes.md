# Changes

## Files Changed

- Removed:
  - `docs/how-to/migrate-custom-connectors.mdx`
- Updated docs content and links:
  - `docs/start-here.mdx`
  - `docs/how-to/connector-config-repo.mdx`
  - `docs/how-to/connector-studio.mdx`
- Updated docs navigation/maps:
  - `website/sidebars.ts`
  - `docs/doc_sync_map.yaml`
  - `llm.txt`
- Updated docs deployment workflow:
  - `.github/workflows/docs-deploy-vercel.yaml`
  - removed local `vercel build` steps
  - switched deploy commands from `--prebuilt` to direct `vercel deploy --yes`
- Updated handoff artifacts:
  - `task.md`
  - `changes.md`
  - `test_evidence.md`
  - `docs_evidence.md`
  - `risk_tier.md`

## Behavior Changes

- No runtime behavior changes.
- Docs site no longer presents migration guidance for custom connectors.
- Docs deploy pipeline now uses Vercel-hosted builds instead of local CLI prebuilds in CI.

## Non-Functional Changes

- Reduced unpublished documentation surface area.
- Removed stale/unused doc route and related references.
- Eliminated a reproducible CI failure path: `vercel build` -> `Error: spawn sh ENOENT`.
