"""Offline tests for the local LLM bench, independent of legacy code review."""

from copy import deepcopy
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from forgebench.lab.cases import TRIALS, evaluate, fingerprint, validate_case
from forgebench.lab.engine import Bench
from forgebench.lab.provider import complete, validate_settings
from forgebench.lab.server import create_server
from forgebench.lab.store import Store


class CaseTests(unittest.TestCase):
    def test_all_bundled_cases_validate(self):
        for case in TRIALS:
            validate_case(case)

    def test_exact_ignores_only_outer_whitespace(self):
        self.assertTrue(evaluate(" READY\n", [{"type": "exact", "expected": "READY"}])[0]["passed"])
        self.assertFalse(evaluate("ready", [{"type": "exact", "expected": "READY"}])[0]["passed"])

    def test_contains_and_not_contains(self):
        checks = [{"type": "contains", "expected": "value"}, {"type": "not_contains", "expected": "invented"}]
        self.assertTrue(all(c["passed"] for c in evaluate("A value", checks)))

    def test_json_order_and_types(self):
        check = [{"type": "json_equals", "expected": '{"a":0,"b":null}'}]
        self.assertTrue(evaluate('{"b":null,"a":0}', check)[0]["passed"])
        self.assertFalse(evaluate('{"b":null,"a":false}', check)[0]["passed"])

    def test_json_rejects_fences_duplicates_and_nan(self):
        for response in ('```json\n{}\n```', '{"a":1,"a":2}', '{"a":NaN}'):
            self.assertFalse(evaluate(response, [{"type": "json_equals", "expected": '{}'}])[0]["passed"])

    def test_invalid_case_rejected(self):
        for invalid in ({}, [], {**TRIALS[0], "checks": []}, {**TRIALS[0], "category": "unknown"},
                        {**TRIALS[0], "checks": [{"type": "shell", "expected": "anything"}]}):
            with self.assertRaises(ValueError):
                validate_case(invalid)

    def test_changed_definition_changes_fingerprint(self):
        self.assertEqual(fingerprint(TRIALS[0]), fingerprint(deepcopy(TRIALS[0])))
        self.assertNotEqual(fingerprint(TRIALS[0]), fingerprint({**TRIALS[0], "prompt": "new"}))


class ProviderTests(unittest.TestCase):
    config = {"base_url": "http://localhost:11434/v1", "model": "test-model", "allow_remote": False}

    def test_remote_requires_consent_and_tls(self):
        with self.assertRaises(ValueError):
            validate_settings({**self.config, "base_url": "https://example.test/v1"})
        with self.assertRaises(ValueError):
            validate_settings({**self.config, "base_url": "http://example.test/v1", "allow_remote": True})
        self.assertTrue(validate_settings({**self.config, "base_url": "https://example.test/v1", "allow_remote": True})["allow_remote"])

    def test_credentials_queries_and_bad_ports_rejected(self):
        for url in ("http://user:pass@localhost/v1", "file:///tmp/test", "http://localhost/v1?token=x", "http://localhost:99999/v1"):
            with self.assertRaises(ValueError):
                validate_settings({**self.config, "base_url": url})

    @patch("forgebench.lab.provider.build_opener")
    def test_real_protocol_without_network(self, opener):
        opener.return_value.open.return_value.__enter__.return_value.read.return_value = json.dumps({"choices": [{"message": {"content": "READY"}}]}).encode()
        with patch.dict(os.environ, {"FORGEBENCH_LAB_API_KEY": "test-secret"}):
            self.assertEqual(complete(TRIALS[0], self.config), "READY")
        request = opener.return_value.open.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(request.full_url, "http://localhost:11434/v1/chat/completions")
        self.assertEqual(payload["messages"][1]["content"], TRIALS[0]["prompt"])
        self.assertNotIn("demo", payload)
        self.assertNotIn("checks", payload)
        self.assertEqual(request.get_header("Authorization"), "Bearer test-secret")

    @patch("forgebench.lab.provider.build_opener")
    def test_provider_error_does_not_expose_body(self, opener):
        opener.return_value.open.side_effect = HTTPError("https://secret", 401, "secret", {}, None)
        with self.assertRaisesRegex(ValueError, "HTTP 401") as error:
            complete(TRIALS[0], self.config)
        self.assertNotIn("secret", str(error.exception))

    @patch("forgebench.lab.provider.build_opener")
    def test_malformed_provider_response(self, opener):
        opener.return_value.open.return_value.__enter__.return_value.read.return_value = b'{"choices": []}'
        with self.assertRaisesRegex(ValueError, "invalid"):
            complete(TRIALS[0], self.config)

    def test_local_http_endpoint_end_to_end(self):
        received = []

        class Endpoint(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                received.append((self.path, json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
                body = json.dumps({"choices": [{"message": {"content": "READY"}}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Endpoint)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            config = {**self.config, "base_url": f"http://127.0.0.1:{server.server_port}/v1"}
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(complete(TRIALS[0], config), "READY")
            self.assertEqual(received[0][0], "/v1/chat/completions")
            self.assertEqual(received[0][1]["model"], "test-model")
        finally:
            server.shutdown()
            worker.join()
            server.server_close()

    @patch("forgebench.lab.provider.build_opener")
    def test_timeout_and_size_limit(self, opener):
        opener.return_value.open.side_effect = TimeoutError()
        with self.assertRaisesRegex(ValueError, "45 seconds"):
            complete(TRIALS[0], self.config)
        opener.return_value.open.side_effect = None
        opener.return_value.open.return_value.__enter__.return_value.read.return_value = b"x" * 1_048_577
        with self.assertRaisesRegex(ValueError, "1 MiB"):
            complete(TRIALS[0], self.config)


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.store = Store(self.tmp.name)
        self.bench = Bench(self.store, demo_delay=0)

    def tearDown(self):
        self.bench.close()
        self.tmp.cleanup()

    def run_bench(self, **kwargs):
        run = self.bench.start({"case_ids": [c["id"] for c in TRIALS], **kwargs})
        self.bench.worker.join(3)
        return self.store.get("run", run["id"])

    def test_candidate_is_explicit_demo_and_reproducible(self):
        a, b = self.run_bench(), self.run_bench()
        self.assertEqual((a["passed"], a["failed"], a["mode"]), (11, 1, "demo"))
        self.assertEqual(a["results"], b["results"])
        self.assertTrue(all(r["latency_ms"] is None for r in a["results"]))

    def test_baseline_differs(self):
        run = self.run_bench(profile="baseline")
        self.assertEqual(run["passed"], 3)

    def test_no_model_calls_for_demo(self):
        self.bench.completion = MagicMock(side_effect=AssertionError("Network called"))
        self.run_bench()
        self.bench.completion.assert_not_called()

    def test_no_run_on_bootstrap(self):
        self.assertEqual(self.bench.bootstrap()["runs"], [])
        self.assertIsNone(self.bench.worker)

    def test_custom_trial_persists_without_fabricated_demo(self):
        case = self.bench.save_case({**TRIALS[0], "id": None})
        self.assertNotIn("demo", case)
        run = self.run_bench(case_ids=[case["id"]])
        self.assertEqual(run["errors"], 1)
        self.assertIn("no demo fixture", run["results"][0]["error"])
        self.assertIn(case, Bench(self.store).cases())

    def test_edit_is_snapshot_and_restore_supported(self):
        run = self.run_bench(case_ids=[TRIALS[0]["id"]])
        self.bench.save_case({**TRIALS[0], "prompt": "Changed prompt"})
        self.assertEqual(run["results"][0]["case"]["prompt"], TRIALS[0]["prompt"])
        self.bench.delete_case(TRIALS[0]["id"])
        self.assertEqual(self.bench.cases()[0], TRIALS[0])

    def test_invalid_selections(self):
        for ids in ([], ["missing"], [TRIALS[0]["id"]] * 2, "wrong", [None]):
            with self.assertRaises(ValueError):
                self.bench.start({"case_ids": ids})

    def test_endpoint_requires_configuration(self):
        with self.assertRaises(ValueError):
            self.run_bench(mode="endpoint")

    def test_endpoint_results_and_evidence(self):
        self.bench.save_settings(ProviderTests.config)
        self.bench.completion = MagicMock(return_value="READY")
        run = self.run_bench(mode="endpoint", case_ids=[TRIALS[0]["id"]])
        self.assertEqual((run["passed"], run["mode"]), (1, "endpoint"))
        self.assertIsNotNone(run["results"][0]["latency_ms"])
        self.assertEqual(run["results"][0]["response"], "READY")

    def test_provider_failure_is_error_not_failed_assertion(self):
        self.bench.save_settings(ProviderTests.config)
        self.bench.completion = MagicMock(side_effect=ValueError("Unavailable"))
        run = self.run_bench(mode="endpoint", case_ids=[TRIALS[0]["id"]])
        self.assertEqual((run["errors"], run["failed"]), (1, 0))

    def test_cancel_and_concurrent_run_rejected(self):
        self.bench.demo_delay = 2
        run = self.bench.start({"case_ids": [c["id"] for c in TRIALS]})
        with self.assertRaisesRegex(ValueError, "already active"):
            self.bench.start({"case_ids": [TRIALS[0]["id"]]})
        self.bench.cancel(run["id"])
        self.bench.worker.join(3)
        saved = self.store.get("run", run["id"])
        self.assertEqual(saved["status"], "cancelled")
        self.assertTrue(all(r["status"] == "skipped" for r in saved["results"]))

    def test_restart_marks_unfinished_run_interrupted(self):
        run = self.run_bench()
        run["status"] = "running"
        self.store.put("run", run["id"], run)
        Bench(self.store)
        self.assertEqual(self.store.get("run", run["id"])["status"], "interrupted")

    def test_secrets_not_stored_in_settings_or_bootstrap(self):
        with patch.dict(os.environ, {"FORGEBENCH_LAB_API_KEY": "secret-value"}):
            self.bench.save_settings({**ProviderTests.config, "api_key": "secret-value"})
            data = self.bench.bootstrap()
        self.assertTrue(data["key_available"])
        self.assertNotIn("secret-value", json.dumps(data))


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.server = create_server(0, self.tmp.name)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.token = self.get("/api/bootstrap")["token"]

    def tearDown(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()
        self.server.bench.close()
        self.tmp.cleanup()

    def get(self, path):
        with urlopen(self.url + path) as response:
            return json.load(response)

    def post(self, path, body, **headers):
        return urlopen(Request(self.url + path, data=json.dumps(body).encode(), headers={
            "Origin": self.url, "X-ForgeBench-Token": self.token, "Content-Type": "application/json", **headers}))

    def test_serves_application_with_security_headers(self):
        with urlopen(self.url) as response:
            self.assertIn(b"ForgeBench", response.read())
            self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])

    def test_cross_origin_or_no_token_rejected(self):
        for headers in ({"Origin": "https://evil.test"}, {"X-ForgeBench-Token": "wrong"}):
            with self.assertRaises(HTTPError) as error:
                self.post("/api/runs", {}, **headers)
            self.assertEqual(error.exception.code, 403)
            error.exception.close()

    def test_bad_host_rejected(self):
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(self.url + "/api/bootstrap", headers={"Host": "evil.test"}))
        self.assertEqual(error.exception.code, 403)
        error.exception.close()

    def test_run_export(self):
        with self.post("/api/runs", {"case_ids": [TRIALS[0]["id"]]}) as response:
            run = json.load(response)
        self.server.bench.worker.join(3)
        with urlopen(self.url + "/api/runs/" + run["id"] + "/export") as response:
            self.assertIn("attachment", response.headers["Content-Disposition"])
            self.assertEqual(json.load(response)["passed"], 1)

    def test_path_traversal_rejected(self):
        with self.assertRaises(HTTPError) as error:
            urlopen(self.url + "/../provider.py")
        self.assertEqual(error.exception.code, 404)
        error.exception.close()

    def test_invalid_body_clear_error(self):
        with self.assertRaises(HTTPError) as error:
            self.post("/api/runs", [])
        self.assertEqual(error.exception.code, 400)
        error.exception.close()


if __name__ == "__main__":
    unittest.main()
