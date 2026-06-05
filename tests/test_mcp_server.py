from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from forgebench.mcp_server import _call_tool, _handle_message


FIXTURES = Path(__file__).parent / "fixtures"


class MCPServerTests(unittest.TestCase):
    def test_initialize_returns_capabilities(self) -> None:
        response = _handle_message({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})

        self.assertEqual(response["id"], 1)
        self.assertIn("protocolVersion", response["result"])
        self.assertEqual(response["result"]["serverInfo"]["name"], "forgebench")

    def test_tools_list_includes_review_tools(self) -> None:
        response = _handle_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        names = {tool["name"] for tool in response["result"]["tools"]}

        self.assertIn("forgebench_review", names)
        self.assertIn("forgebench_repair_prompt", names)

    def test_forgebench_review_tool_returns_repair_prompt(self) -> None:
        with TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "out"
            result = _call_tool(
                "forgebench_review",
                {
                    "repo": str(Path.cwd()),
                    "diff": str(FIXTURES / "simple.patch"),
                    "task": str(FIXTURES / "task.md"),
                    "output_dir": str(out_dir),
                },
            )
            payload = json.loads(result["content"][0]["text"])

        self.assertIn("posture", payload)
        self.assertIn("repair_prompt", payload)
        self.assertIn("You are repairing an AI-generated code change", payload["repair_prompt"])

    def test_forgebench_repair_prompt_reads_existing_file(self) -> None:
        with TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "out"
            out_dir.mkdir()
            (out_dir / "repair-prompt.md").write_text("repair body", encoding="utf-8")
            result = _call_tool("forgebench_repair_prompt", {"output_dir": str(out_dir)})
            payload = json.loads(result["content"][0]["text"])

        self.assertEqual(payload["repair_prompt"], "repair body")

    def test_read_message_parses_framed_json(self) -> None:
        body = json.dumps({"jsonrpc": "2.0", "id": 9, "method": "ping"}).encode("utf-8")
        stream = BytesIO(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body)
        stdin = mock.Mock()
        stdin.buffer = stream

        with mock.patch("forgebench.mcp_server.sys.stdin", stdin):
            from forgebench.mcp_server import _read_message

            message = _read_message()

        self.assertEqual(message["method"], "ping")


if __name__ == "__main__":
    unittest.main()