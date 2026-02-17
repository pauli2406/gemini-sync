# Gemini Sync Bridge Roadmap

## Vision

Build the most reliable open-source bridge for enterprise connector ingestion into Gemini-backed knowledge systems, with a first-class agentic development lifecycle.

This roadmap is intentionally horizon-based and continuously updated. It is optimized for daily agent-driven execution, not fixed date commitments.

## Outcome Phases

### Now: Foundation Maturity

**Outcomes**

- Full EDD + TDD governance active in CI and nightly workflows.
- `AGENTS.md` contract adopted for all significant changes.
- Baseline scenario eval registry and critical scenario suite established.

**Exit Criteria**

- TDD guardrail, docs drift, scenario eval, security checks all blocking in CI/nightly.
- All new Tier 1+ changes include handoff artifacts and risk-tier classification.
- Diff coverage threshold met on all merged changes.

**Success Metrics**

- 100% of Tier 1+ PRs include test and docs evidence.
- 0 merges with broken docs-drift or TDD policies.

### Next: Reliability Maturity

**Outcomes**

- Expanded test matrix for SQL/REST adapters and failure modes.
- Deterministic replay and fault-injection harness for ingestion flows.
- Operational SLO dashboards tied to merge and release health gates.

**Progress**

- Implemented adapter matrix tests for SQL pull and REST pull pagination.
- Added replay artifact determinism and fault-injection tooling.
- Added SLO report generation and threshold gate with canary/nightly workflow integration.
- Added a read-only FastAPI + Jinja Ops UI (`/ops`) with JSON polling endpoints for connector/run visibility.
- Added ops run filtering/pagination and optional Splunk/Kestra run deep links by `run_id`.
- Added `hr-employees` connector contract regression coverage (test + scenario eval).
- Added hosted docs foundation (`website/`) with Docusaurus, Redoc API reference, OpenAPI drift gate, and Vercel preview/production deploy workflow.
- Added mode-specific and provider-specific connector documentation with schema-generated field reference and CI drift enforcement.

**Exit Criteria**

- Critical scenario pass rate sustained at 100% for 30 consecutive days.
- Mean time to recovery (MTTR) for connector failures < 30 minutes in staging.

**Success Metrics**

- Fewer than 1 unresolved regression per 50 merged PRs.
- Successful replay validation for all supported connector modes.

### Later: Scale Maturity

**Outcomes**

- Large-connector concurrency benchmark suite.
- Backpressure and queue-depth policy validation at scale.
- Cost/performance evals integrated into nightly regression runs.

**Exit Criteria**

- 100 mixed connectors run for 24h with no sustained backlog growth.
- Freshness objective (`<= 3h` for scheduled connectors) maintained under load.

**Success Metrics**

- Throughput and freshness regressions detected pre-merge.
- Stable p95 run durations across load suites.

### Later: Governance Maturity

**Outcomes**

- Versioned policy packs for risk, tools, and gate rules.
- Automated risk-tier classification support and audit trails.
- Immutable release evidence chain for every production release.

**Exit Criteria**

- All release artifacts contain reproducible metadata and gate evidence.
- Tier 3 changes consistently require and record human approval.

**Success Metrics**

- 100% auditability of merged and released artifacts.
- No policy bypass in protected branches.

### Later: Ecosystem Maturity

**Outcomes**

- Contributor kit for external connector pack authors.
- Reusable eval scenario templates for adopters.
- Reference deployment blueprints for common enterprise topologies.

**Exit Criteria**

- External contributors can ship connector packs with policy-compliant PRs.
- Documentation and templates reduce onboarding time materially.

**Success Metrics**

- Increased external contribution volume.
- Reduced time-to-first-connector for new users.

## Agent Work Queue Template

For daily execution, each item should include:

1. Intended outcome and risk tier.
2. Failing test/eval plan.
3. Implementation plan.
4. Required docs updates (`docs/doc_sync_map.yaml`).
5. Gate evidence required for merge.

## Roadmap Update Rule

Every merged Tier 1+ change must evaluate whether this roadmap needs a progress or scope update, and if so update this file in the same PR.
