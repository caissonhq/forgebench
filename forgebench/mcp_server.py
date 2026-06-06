from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from forgebench.review import ReviewInputError, run_review
from forgebench.security.http_limits import MAX_MCP_BODY_BYTES


PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "forgebench"
SERVER_VERSION = "0.9.0"


class MCPProtocolError(ValueError):
    pass


def run_mcp_server() -> None:
    while True:
        message = _read_message()
        if message is None:
            return
        response = _handle_message(message)
        if response is not None:
            _write_message(response)


def _handle_message(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")
    if method is None:
        return None
    if request_id is None:
        _dispatch_notification(method, message.get("params") or {})
        return None
    try:
        result = _dispatch_request(method, message.get("params") or {})
    except MCPProtocolError as exc:
        return _error_response(request_id, -32602, str(exc))
    except ReviewInputError as exc:
        return _error_response(request_id, -32000, str(exc))
    except OSError as exc:
        return _error_response(request_id, -32000, str(exc))
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _dispatch_notification(method: str, params: dict[str, Any]) -> None:
    if method == "notifications/initialized":
        return
    return


def _dispatch_request(method: str, params: dict[str, Any]) -> dict[str, Any]:
    if method == "initialize":
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        }
    if method == "tools/list":
        return {"tools": [_tool_schema(name, spec) for name, spec in TOOL_SPECS.items()]}
    if method == "tools/call":
        tool_name = str(params.get("name") or "")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            raise MCPProtocolError("tools/call arguments must be an object.")
        if tool_name not in TOOL_SPECS:
            raise MCPProtocolError(f"Unknown tool: {tool_name}")
        return _call_tool(tool_name, arguments)
    if method == "ping":
        return {}
    raise MCPProtocolError(f"Unsupported method: {method}")


def _call_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if tool_name == "forgebench_review":
        payload = _run_review_tool(arguments)
    elif tool_name == "forgebench_repair_prompt":
        payload = _read_repair_prompt_tool(arguments)
    else:
        raise MCPProtocolError(f"Unknown tool: {tool_name}")
    return {
        "content": [{"type": "text", "text": json.dumps(payload, indent=2, sort_keys=True)}],
        "isError": False,
    }


def _run_review_tool(arguments: dict[str, Any]) -> dict[str, Any]:
    repo = _required_str(arguments, "repo")
    diff = _required_str(arguments, "diff")
    task = _required_str(arguments, "task")
    guardrails = _optional_str(arguments, "guardrails")
    output_dir = _optional_str(arguments, "output_dir") or "forgebench-output"
    run_checks = bool(arguments.get("run_checks", False))
    reviewers_enabled = not bool(arguments.get("no_reviewers", False))

    result = run_review(
        repo_path=repo,
        diff_path=diff,
        task_path=task,
        guardrails_path=guardrails,
        output_dir=output_dir,
        run_checks=run_checks,
        reviewers_enabled=reviewers_enabled,
    )
    repair_path = result.written_paths["repair_prompt"]
    repair_text = repair_path.read_text(encoding="utf-8", errors="replace")
    return {
        "posture": result.report.posture.value,
        "output_dir": str(result.output_dir),
        "report_markdown": str(result.written_paths["markdown"]),
        "report_json": str(result.written_paths["json"]),
        "repair_prompt_path": str(repair_path),
        "repair_prompt": repair_text,
        "finding_count": len(result.report.findings),
        "paste_instruction": (
            "Paste repair_prompt into your coding agent (Cursor, Codex, or Claude Code) "
            "and ask it to apply the smallest necessary fixes."
        ),
    }


def _read_repair_prompt_tool(arguments: dict[str, Any]) -> dict[str, Any]:
    output_dir = _optional_str(arguments, "output_dir") or "forgebench-output"
    repair_path = Path(output_dir) / "repair-prompt.md"
    if not repair_path.exists():
        raise MCPProtocolError(f"repair-prompt.md not found at {repair_path}. Run forgebench_review first.")
    repair_text = repair_path.read_text(encoding="utf-8", errors="replace")
    return {
        "repair_prompt_path": str(repair_path),
        "repair_prompt": repair_text,
        "paste_instruction": "Paste repair_prompt into your coding agent to repair the patch.",
    }


TOOL_SPECS: dict[str, dict[str, Any]] = {
    "forgebench_review": {
        "description": (
            "Run a ForgeBench merge-risk review on a local diff and task prompt. "
            "Returns merge posture and the repair prompt text ready to paste into a coding agent."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository root path."},
                "diff": {"type": "string", "description": "Path to unified git diff."},
                "task": {"type": "string", "description": "Path to original task prompt."},
                "guardrails": {"type": "string", "description": "Optional forgebench.yml path."},
                "output_dir": {"type": "string", "description": "Output directory. Defaults to forgebench-output."},
                "run_checks": {"type": "boolean", "description": "Run configured deterministic checks."},
                "no_reviewers": {"type": "boolean", "description": "Skip heuristic review lenses."},
            },
            "required": ["repo", "diff", "task"],
        },
    },
    "forgebench_repair_prompt": {
        "description": "Read repair-prompt.md from a prior ForgeBench review output directory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "output_dir": {
                    "type": "string",
                    "description": "ForgeBench output directory. Defaults to forgebench-output.",
                }
            },
        },
    },
}


def _tool_schema(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": name,
        "description": spec["description"],
        "inputSchema": spec["inputSchema"],
    }


def _required_str(arguments: dict[str, Any], key: str) -> str:
    value = arguments.get(key)
    if not isinstance(value, str) or not value.strip():
        raise MCPProtocolError(f"{key} is required.")
    return value.strip()


def _optional_str(arguments: dict[str, Any], key: str) -> str | None:
    value = arguments.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise MCPProtocolError(f"{key} must be a string.")
    stripped = value.strip()
    return stripped or None


def _read_message() -> dict[str, Any] | None:
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        decoded = line.decode("utf-8", errors="replace").strip()
        if not decoded:
            break
        if ":" not in decoded:
            continue
        key, value = decoded.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    try:
        content_length = int(headers.get("content-length", "0"))
    except ValueError as exc:
        raise MCPProtocolError("Invalid Content-Length header.") from exc
    if content_length <= 0:
        return None
    if content_length > MAX_MCP_BODY_BYTES:
        raise MCPProtocolError(f"MCP message exceeds limit of {MAX_MCP_BODY_BYTES} bytes.")
    body = sys.stdin.buffer.read(content_length)
    if not body:
        return None
    payload = json.loads(body.decode("utf-8"))
    if not isinstance(payload, dict):
        raise MCPProtocolError("MCP message must be a JSON object.")
    return payload


def _write_message(payload: dict[str, Any]) -> None:
    encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    header = f"Content-Length: {len(encoded)}\r\n\r\n".encode("ascii")
    sys.stdout.buffer.write(header)
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def _error_response(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }