from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.policy_versioning import bump_policy_version, read_version_history, record_policy_version


class PolicyVersioningTests(unittest.TestCase):
    def test_bump_patch_version(self) -> None:
        self.assertEqual(bump_policy_version("1.2.3"), "1.2.4")

    def test_record_and_read_version_history(self) -> None:
        with TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "versions.jsonl"
            policy_file = Path(tmp) / "forgebench.yml"
            policy_file.write_text("project: demo\n", encoding="utf-8")
            record_policy_version(
                policy_id="demo",
                version="1.0.0",
                fingerprint="abc123",
                source_path=policy_file,
                manifest_path=manifest,
            )
            history = read_version_history(manifest)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].version, "1.0.0")


if __name__ == "__main__":
    unittest.main()