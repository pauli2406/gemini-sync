from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

from ingest_relay.studio_schemas import ProposalAction, ProposalResponse
from ingest_relay.utils.http_clients import create_httpx_client


def build_branch_name(action: str, connector_id: str, timestamp: str | None = None) -> str:
    ts = timestamp or datetime.now(tz=UTC).strftime("%Y%m%d-%H%M%S")
    return f"studio/{action}/{connector_id}/{ts}"


def create_proposal_result(
    *,
    action: ProposalAction,
    connector_id: str,
    changed_files: list[str],
    github_repo: str,
    branch_name: str,
    proposal_id: str | None = None,
    github_pr_url_override: str | None = None,
) -> ProposalResponse:
    if github_pr_url_override:
        pr_url = github_pr_url_override
    elif github_repo:
        pr_url = f"https://github.com/{github_repo}/pull/new/{branch_name}"
    else:
        pr_url = f"local://proposal/{branch_name}"

    return ProposalResponse(
        proposal_id=proposal_id or branch_name.replace("/", "-"),
        branch_name=branch_name,
        pr_url=pr_url,
        changed_files=sorted(changed_files),
        connector_id=connector_id,
        action=action,
    )


@dataclass
class GitHubPRService:
    github_repo: str
    github_token: str = ""
    github_base_branch: str = "main"

    def _repo_parts(self) -> tuple[str, str]:
        if "/" not in self.github_repo:
            raise ValueError("GITHUB_REPO must be in the form 'owner/repo'")
        owner, repo = self.github_repo.split("/", 1)
        if not owner or not repo:
            raise ValueError("GITHUB_REPO must be in the form 'owner/repo'")
        return owner, repo

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.github_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _get_file_sha(
        self,
        client: httpx.Client,
        *,
        owner: str,
        repo: str,
        path: str,
        branch_name: str,
    ) -> str | None:
        response = client.get(
            f"/repos/{owner}/{repo}/contents/{path}",
            headers=self._headers(),
            params={"ref": branch_name},
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        payload = response.json()
        sha = payload.get("sha")
        return str(sha) if sha else None

    def _commit_file_changes(
        self,
        client: httpx.Client,
        *,
        owner: str,
        repo: str,
        branch_name: str,
        action: ProposalAction,
        connector_id: str,
        proposal_id: str,
        file_changes: dict[str, str | None],
        commit_message: str | None,
    ) -> list[str]:
        changed_files = sorted(file_changes.keys())
        message = commit_message or f"{action}: {connector_id} ({proposal_id})"

        for path in changed_files:
            content = file_changes[path]
            current_sha = self._get_file_sha(
                client,
                owner=owner,
                repo=repo,
                path=path,
                branch_name=branch_name,
            )

            if content is None:
                if not current_sha:
                    continue
                response = client.request(
                    "DELETE",
                    f"/repos/{owner}/{repo}/contents/{path}",
                    headers=self._headers(),
                    json={
                        "message": message,
                        "sha": current_sha,
                        "branch": branch_name,
                    },
                )
                response.raise_for_status()
                continue

            encoded_content = base64.b64encode(content.encode("utf-8")).decode("ascii")
            payload: dict[str, Any] = {
                "message": message,
                "content": encoded_content,
                "branch": branch_name,
            }
            if current_sha:
                payload["sha"] = current_sha
            response = client.put(
                f"/repos/{owner}/{repo}/contents/{path}",
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()

        return changed_files

    def _create_pull_request(
        self,
        client: httpx.Client,
        *,
        owner: str,
        repo: str,
        branch_name: str,
        action: ProposalAction,
        connector_id: str,
        pr_title: str | None,
        pr_body: str | None,
    ) -> str:
        response = client.post(
            f"/repos/{owner}/{repo}/pulls",
            headers=self._headers(),
            json={
                "title": pr_title or f"{action}: {connector_id}",
                "head": branch_name,
                "base": self.github_base_branch,
                "body": pr_body or "Generated by Connector Studio",
            },
        )
        response.raise_for_status()
        payload = response.json()
        pr_url = payload.get("html_url")
        if not pr_url:
            raise ValueError("GitHub pull request response missing html_url")
        return str(pr_url)

    def create_proposal(
        self,
        *,
        action: ProposalAction,
        connector_id: str,
        changed_files: list[str],
        branch_name: str,
        proposal_id: str,
        file_changes: dict[str, str | None] | None = None,
        commit_message: str | None = None,
        pr_title: str | None = None,
        pr_body: str | None = None,
    ) -> ProposalResponse:
        if not self.github_repo or not self.github_token or not file_changes:
            return create_proposal_result(
                action=action,
                connector_id=connector_id,
                changed_files=changed_files,
                github_repo=self.github_repo,
                branch_name=branch_name,
                proposal_id=proposal_id,
            )

        owner, repo = self._repo_parts()
        pr_url = ""

        try:
            with create_httpx_client(base_url="https://api.github.com", timeout=30.0) as client:
                branch_response = client.get(
                    f"/repos/{owner}/{repo}/git/ref/heads/{self.github_base_branch}",
                    headers=self._headers(),
                )
                branch_response.raise_for_status()
                base_sha = branch_response.json()["object"]["sha"]

                create_branch = client.post(
                    f"/repos/{owner}/{repo}/git/refs",
                    headers=self._headers(),
                    json={"ref": f"refs/heads/{branch_name}", "sha": base_sha},
                )
                if create_branch.status_code not in {201, 422}:
                    create_branch.raise_for_status()

                changed_files = self._commit_file_changes(
                    client,
                    owner=owner,
                    repo=repo,
                    branch_name=branch_name,
                    action=action,
                    connector_id=connector_id,
                    proposal_id=proposal_id,
                    file_changes=file_changes,
                    commit_message=commit_message,
                )
                pr_url = self._create_pull_request(
                    client,
                    owner=owner,
                    repo=repo,
                    branch_name=branch_name,
                    action=action,
                    connector_id=connector_id,
                    pr_title=pr_title,
                    pr_body=pr_body,
                )
        except (KeyError, httpx.HTTPError, ValueError) as exc:
            raise ValueError(f"Failed to create GitHub PR proposal: {exc}") from exc

        return create_proposal_result(
            action=action,
            connector_id=connector_id,
            changed_files=changed_files,
            github_repo="",
            branch_name=branch_name,
            proposal_id=proposal_id,
            github_pr_url_override=pr_url,
        )
