from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.telemetry import (
    TelemetryError,
    anonymize_payload,
    disable_telemetry,
    enable_telemetry,
    export_telemetry_bundle,
    is_telemetry_enabled,
    record_telemetry_event,
    telemetry_status,
)


class TelemetryTests(unittest.TestCase):
    def test_disabled_by_default(self) -> None:
        with TemporaryDirectory() as tmp:
            flag = Path(tmp) / ".telemetry-enabled"
            log = Path(tmp) / "telemetry.jsonl"
            with _env_without_telemetry(), _patch_paths(flag, log):
                self.assertFalse(is_telemetry_enabled())
                self.assertIsNone(record_telemetry_event("review_completed", {"posture": "REVIEW"}))

    def test_enable_flag_and_record_event(self) -> None:
        with TemporaryDirectory() as tmp:
            flag = Path(tmp) / ".telemetry-enabled"
            log = Path(tmp) / "telemetry.jsonl"
            with _patch_paths(flag, log):
                enable_telemetry(flag_path=flag)
                self.assertTrue(is_telemetry_enabled())
                record_telemetry_event("benchmark_run", {"case_count": 47, "repo_path": "/secret/repo"})
                bundle = export_telemetry_bundle(log_path=log)
            self.assertEqual(bundle["event_count"], 1)
            payload = bundle["events"][0]["payload"]
            self.assertNotIn("repo_path", payload)
            self.assertIn("repo_path_hash", payload)

    def test_env_var_enables_telemetry(self) -> None:
        with TemporaryDirectory() as tmp, _env_telemetry_on():
            flag = Path(tmp) / ".telemetry-enabled"
            log = Path(tmp) / "telemetry.jsonl"
            with _patch_paths(flag, log):
                self.assertTrue(is_telemetry_enabled())
                record_telemetry_event("feedback_recorded", {"status": "dismissed"})
                status = telemetry_status(log_path=log)
            self.assertEqual(status.event_count, 1)

    def test_unsupported_event_type_raises(self) -> None:
        with TemporaryDirectory() as tmp, _env_telemetry_on():
            flag = Path(tmp) / ".telemetry-enabled"
            log = Path(tmp) / "telemetry.jsonl"
            with _patch_paths(flag, log):
                with self.assertRaises(TelemetryError):
                    record_telemetry_event("upload_everything", {})

    def test_anonymize_payload_redacts_paths(self) -> None:
        payload = anonymize_payload({"note": "/Users/me/project/file.py", "posture": "REVIEW"})
        self.assertEqual(payload["posture"], "REVIEW")
        self.assertEqual(payload["note"], "<redacted-path>")

    def test_disable_removes_flag(self) -> None:
        with TemporaryDirectory() as tmp:
            flag = Path(tmp) / ".telemetry-enabled"
            enable_telemetry(flag_path=flag)
            disable_telemetry(flag_path=flag)
            self.assertFalse(flag.exists())


def _patch_paths(flag: Path, log: Path):
    import forgebench.telemetry as telemetry

    return _TelemetryPathPatch(telemetry, flag, log)


class _TelemetryPathPatch:
    def __init__(self, module, flag: Path, log: Path) -> None:
        self.module = module
        self.flag = flag
        self.log = log
        self.original_flag = module.TELEMETRY_FLAG
        self.original_log = module.TELEMETRY_LOG

    def __enter__(self) -> None:
        self.module.TELEMETRY_FLAG = self.flag
        self.module.TELEMETRY_LOG = self.log

    def __exit__(self, exc_type, exc, tb) -> None:
        self.module.TELEMETRY_FLAG = self.original_flag
        self.module.TELEMETRY_LOG = self.original_log


class _env_without_telemetry:
    def __enter__(self) -> None:
        self.previous = os.environ.get("FORGEBENCH_TELEMETRY")
        os.environ.pop("FORGEBENCH_TELEMETRY", None)

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.previous is None:
            os.environ.pop("FORGEBENCH_TELEMETRY", None)
        else:
            os.environ["FORGEBENCH_TELEMETRY"] = self.previous


class _env_telemetry_on:
    def __enter__(self) -> None:
        self.previous = os.environ.get("FORGEBENCH_TELEMETRY")
        os.environ["FORGEBENCH_TELEMETRY"] = "1"

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.previous is None:
            os.environ.pop("FORGEBENCH_TELEMETRY", None)
        else:
            os.environ["FORGEBENCH_TELEMETRY"] = self.previous


if __name__ == "__main__":
    unittest.main()