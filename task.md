# Task

- Task ID: docs-remove-migrate-custom-connectors
- Title: Remove unpublished "Migrate Custom Connectors" documentation
- Owner Role: planner
- Risk Tier: tier_0

## Intent

Remove the standalone migration guide and all references to it, because version 1 is not published and there are no users who need migration instructions yet.

## Acceptance Criteria

1. `docs/how-to/migrate-custom-connectors.mdx` is removed.
2. No docs navigation or cross-links reference `/docs/how-to/migrate-custom-connectors`.
3. Docs mapping/index files do not reference the removed page.
4. Docs site build passes after removal.

## Specialist Role Mapping

1. Planner Agent
   - Scoped this as a Tier 0 docs-only removal and defined acceptance criteria around link/navigation cleanup.
2. Implementer Agent
   - Removed the migration page and updated docs content, sidebars, and doc maps.
3. Test/Eval Agent
   - Verified no dangling references remain and docs build stays green.
4. Docs Agent
   - Updated start pages and related guides to remove migration-specific links.
5. Security Agent
   - Confirmed no policy/security surface change from this documentation-only edit.
6. Release Agent
   - Marked as Tier 0 and ready for normal docs-only review flow.
