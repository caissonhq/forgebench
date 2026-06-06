from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.analytics_dashboard import export_analytics_dashboard
from forgebench.product_analytics import (
    ProductAnalyticsError,
    disable_product_analytics,
    enable_product_analytics,
    export_product_analytics_bundle,
    is_product_analytics_enabled,
    record_product_event,
)


class ProductAnalyticsTests(unittest.TestCase):
    def test_disabled_by_default(self) -> None:
        with TemporaryDirectory() as tmp:
            flag = Path(tmp) / ".product-analytics-enabled"
            log = Path(tmp) / "product-analytics.jsonl"
            with _env_without_analytics(), _patch_paths(flag, log):
                self.assertFalse(is_product_analytics_enabled())
                self.assertIsNone(record_product_event("cli_command", {"command": "doctor"}))

    def test_enable_and_record_event(self) -> None:
        with TemporaryDirectory() as tmp:
            flag = Path(tmp) / ".product-analytics-enabled"
            log = Path(tmp) / "product-analytics.jsonl"
            with _patch_paths(flag, log):
                enable_product_analytics(flag_path=flag)
                record_product_event("cli_command", {"command": "demo", "repo_path": "/secret"})
                bundle = export_product_analytics_bundle(log_path=log)
            self.assertEqual(bundle["event_count"], 1)
            payload = bundle["events"][0]["payload"]
            self.assertEqual(payload["command"], "demo")
            self.assertNotIn("repo_path", payload)
            self.assertIn("separate from review telemetry", bundle["privacy_note"])

    def test_unsupported_event_raises(self) -> None:
        with TemporaryDirectory() as tmp, _env_analytics_on():
            flag = Path(tmp) / ".product-analytics-enabled"
            log = Path(tmp) / "product-analytics.jsonl"
            with _patch_paths(flag, log):
                with self.assertRaises(ProductAnalyticsError):
                    record_product_event("upload_raw_diffs", {})

    def test_analytics_dashboard_export(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "dashboard"
            result = export_analytics_dashboard(output_dir=out, include_review_telemetry=False)
            self.assertTrue(result.index_path.exists())
            self.assertTrue(result.manifest_path.exists())
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            self.assertIn("product_analytics", manifest)
            self.assertIn("license", manifest)

    def test_disable_removes_flag(self) -> None:
        with TemporaryDirectory() as tmp:
            flag = Path(tmp) / ".product-analytics-enabled"
            enable_product_analytics(flag_path=flag)
            disable_product_analytics(flag_path=flag)
            self.assertFalse(flag.exists())


def _patch_paths(flag: Path, log: Path):
    import forgebench.product_analytics as analytics

    return _AnalyticsPathPatch(analytics, flag, log)


class _AnalyticsPathPatch:
    def __init__(self, module, flag: Path, log: Path) -> None:
        self.module = module
        self.flag = flag
        self.log = log
        self.original_flag = module.PRODUCT_ANALYTICS_FLAG
        self.original_log = module.PRODUCT_ANALYTICS_LOG

    def __enter__(self) -> None:
        self.module.PRODUCT_ANALYTICS_FLAG = self.flag
        self.module.PRODUCT_ANALYTICS_LOG = self.log

    def __exit__(self, exc_type, exc, tb) -> None:
        self.module.PRODUCT_ANALYTICS_FLAG = self.original_flag
        self.module.PRODUCT_ANALYTICS_LOG = self.original_log


class _env_without_analytics:
    def __enter__(self) -> None:
        self.previous = os.environ.get("FORGEBENCH_PRODUCT_ANALYTICS")
        os.environ.pop("FORGEBENCH_PRODUCT_ANALYTICS", None)

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.previous is None:
            os.environ.pop("FORGEBENCH_PRODUCT_ANALYTICS", None)
        else:
            os.environ["FORGEBENCH_PRODUCT_ANALYTICS"] = self.previous


class _env_analytics_on:
    def __enter__(self) -> None:
        self.previous = os.environ.get("FORGEBENCH_PRODUCT_ANALYTICS")
        os.environ["FORGEBENCH_PRODUCT_ANALYTICS"] = "1"

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.previous is None:
            os.environ.pop("FORGEBENCH_PRODUCT_ANALYTICS", None)
        else:
            os.environ["FORGEBENCH_PRODUCT_ANALYTICS"] = self.previous


if __name__ == "__main__":
    unittest.main()