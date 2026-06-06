from __future__ import annotations

import json
import time
import unittest
from pathlib import Path
from threading import Thread

from forgebench.policy_service.server import PolicyServiceConfig, _build_handler
from http.server import ThreadingHTTPServer


ROOT = Path(__file__).resolve().parents[1]


class PolicyServiceTests(unittest.TestCase):
    def test_health_endpoint_responds(self) -> None:
        guardrails = ROOT / "examples" / "policy_tests" / "fpl_docs_policy" / "forgebench.yml"
        config = PolicyServiceConfig(host="127.0.0.1", port=0, repo_path=ROOT, guardrails_path=guardrails)
        handler = _build_handler(config)
        server = ThreadingHTTPServer((config.host, 0), handler)
        host, port = server.server_address
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            time.sleep(0.2)
            import urllib.request

            with urllib.request.urlopen(f"http://{host}:{port}/health", timeout=2) as response:
                payload = json.loads(response.read().decode("utf-8"))
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual(payload["status"], "ok")


if __name__ == "__main__":
    unittest.main()