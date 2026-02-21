# Docs Evidence

## Updated Docs

- `README.md`
- `CONTRIBUTING.md`
- `llm.txt`
- `docs/contributing/testing-ci.mdx`
- `docs/reference/api-reference.mdx`
- `docs/doc_sync_map.yaml`
- `runtime/README.md`
- `test_evidence.md`
- `task.md`
- `changes.md`

## Why these docs were required

- Runtime source mapping changed from `gemini_sync_bridge/**` to `ingest_relay/**`, requiring doc-sync mapping updates.
- Public contributor guidance needed to reflect new coverage command (`--cov=ingest_relay`).
- API reference source path changed to `ingest_relay/api.py`.
- Stage-2 handoff artifacts required updated implementation/test/docs evidence aligned to module hard-cutover.
