from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from forgebench.crm.pipeline import PipelineEntry


LINEAR_API_URL = "https://api.linear.app/graphql"


def linear_api_key() -> str:
    return os.environ.get("LINEAR_API_KEY", "").strip()


def linear_team_id() -> str:
    return os.environ.get("LINEAR_TEAM_ID", "").strip()


def maybe_sync_pipeline_to_linear(entry: PipelineEntry) -> dict[str, Any] | None:
    if not linear_api_key() or not linear_team_id():
        return None
    title = f"[ForgeBench] {entry.stage}: {entry.organization}"
    description = "\n".join(
        [
            f"**Stage:** {entry.stage}",
            f"**Tier:** {entry.tier}",
            f"**Seats:** {entry.seats}",
            f"**Source:** {entry.source}",
            f"**Updated:** {entry.updated_at}",
        ]
    )
    return create_linear_issue(title=title, description=description)


def create_linear_issue(*, title: str, description: str) -> dict[str, Any]:
    key = linear_api_key()
    team = linear_team_id()
    if not key or not team:
        raise RuntimeError("LINEAR_API_KEY and LINEAR_TEAM_ID required.")
    query = """
    mutation IssueCreate($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue { id identifier url }
      }
    }
    """
    variables = {
        "input": {
            "teamId": team,
            "title": title,
            "description": description,
        }
    }
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(
        LINEAR_API_URL,
        data=payload,
        headers={
            "Authorization": key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Linear API error ({exc.code}): {detail}") from exc
    return body if isinstance(body, dict) else {"raw": body}