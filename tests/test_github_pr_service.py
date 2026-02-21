from __future__ import annotations

from gemini_sync_bridge.services.github_pr import (
    GitHubPRService,
    build_branch_name,
    create_proposal_result,
)


def test_branch_name_is_deterministic_prefix() -> None:
    name = build_branch_name(
        action="create",
        connector_id="hr-employees",
        timestamp="20260216-120000",
    )
    assert name == "studio/create/hr-employees/20260216-120000"


def test_create_proposal_result_uses_repo_when_present() -> None:
    result = create_proposal_result(
        action="edit",
        connector_id="kb-rest",
        changed_files=["connectors/kb-rest.yaml"],
        github_repo="acme/ingest-relay",
        branch_name="studio/edit/kb-rest/20260216-120000",
    )

    assert result.action == "edit"
    assert result.connector_id == "kb-rest"
    assert result.changed_files == ["connectors/kb-rest.yaml"]
    assert "github.com/acme/ingest-relay/pull/new/" in result.pr_url


def test_github_service_falls_back_when_token_missing() -> None:
    service = GitHubPRService(github_repo="acme/ingest-relay", github_token="")
    result = service.create_proposal(
        action="edit",
        connector_id="kb-rest",
        changed_files=["connectors/kb-rest.yaml"],
        branch_name="studio/edit/kb-rest/20260216-120000",
        proposal_id="p-1",
        file_changes={"connectors/kb-rest.yaml": "apiVersion: sync.gemini.io/v1alpha1\n"},
    )

    assert result.proposal_id == "p-1"
    assert "github.com/acme/ingest-relay/pull/new/" in result.pr_url
