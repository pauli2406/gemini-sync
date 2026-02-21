# AGENTS.md

## Purpose

This repository is operated with an AI-agent-first workflow. This document defines the mandatory operating contract for autonomous and semi-autonomous agents contributing to IngestRelay.

## Scope and Boundaries

- Agents may propose and implement code, tests, docs, CI, and infrastructure changes.
- Agents must not bypass merge protections or quality gates.
- Agents must not write or expose secrets in code, tests, docs, logs, or artifacts.
- Tier 3 risk changes are never auto-merged.

## Mandatory Specialist Roles

Every non-trivial change must explicitly map work to these roles:

1. Planner Agent
- Owns problem framing, acceptance criteria, and task decomposition.

2. Implementer Agent
- Owns production code and config changes.

3. Test/Eval Agent
- Owns failing-first tests and scenario eval updates.

4. Docs Agent
- Owns `README.md`, `/docs`, and roadmap updates.

5. Security Agent
- Owns policy compliance and security checks.

6. Release Agent
- Owns canary gate and rollback decisions.

## Required Handoff Artifacts

Each task branch must include these artifacts under `.agent/templates`-based outputs:

- `task.md`
- `changes.md`
- `test_evidence.md`
- `docs_evidence.md`
- `risk_tier.md`

## Development Workflow (EDD + TDD)

1. Plan
- Define expected behavior and risk tier before coding.

2. Red (tests/evals first)
- Add or update tests in `/tests` and scenario evals in `/evals/scenarios` first.
- Tests/evals must fail before implementation for behavior-impacting changes.

3. Green
- Implement the minimal change to pass tests/evals.

4. Refactor
- Improve design without changing behavior.

5. Docs Sync
- Update mapped docs according to `/docs/doc_sync_map.yaml`.

6. Verify
- Run all local gates listed in `CONTRIBUTING.md`.

## Risk Tiers and Merge Policy

Risk tier definitions and required approvals are in `.agent/risk_policy.yaml`.

Default policy:

- Tier 0 (docs/chore/tests): auto-merge allowed after all gates pass.
- Tier 1 (connector/config): auto-merge allowed after all gates pass.
- Tier 2 (runtime/API): auto-merge requires all gates + reviewer bot + one human reviewer.
- Tier 3 (security/release/infra critical): never auto-merge; human approval required.

## Definition of Done

A change is not done unless all are true:

- Production-impacting change has matching test updates.
- Behavior-impacting change has matching scenario eval updates.
- Docs are updated or change is exempt by policy.
- All CI gates pass (lint, schema, TDD gate, docs drift gate, tests, diff coverage, security checks).
- Handoff artifacts are present and updated.
- Risk tier classification is documented.

## Tool and Security Policy

Tool restrictions and command allow/deny lists are defined in `.agent/tool_policy.yaml`.

Mandatory security checks:

- Secret scanning
- Dependency vulnerability audit
- Policy conformance validation
- Prompt-injection regression checks

## File Ownership Map

Use `/docs/doc_sync_map.yaml` to decide which docs must be updated per code-area change.

## PR Evidence Requirements

PR description must include:

- Failing test/eval evidence before implementation.
- Test/eval pass evidence after implementation.
- Docs changed and why.
- Assigned risk tier and gate outcome.
