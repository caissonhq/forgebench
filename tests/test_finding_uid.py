from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.models import Confidence, EvidenceType, Finding, REPORT_SCHEMA_VERSION, Severity
from forgebench.review import run_review


FIXTURES = Path(__file__).parent / "fixtures"


class FindingUidTests(unittest.TestCase):
    def test_same_finding_produces_same_uid_twice(self) -> None:
        first = _finding(files=["src/app.py"])
        second = _finding(files=["src/app.py"])

        self.assertEqual(first.uid, second.uid)
        self.assertEqual(first.kind, "implementation_without_tests")
        self.assertEqual(first.id, "implementation_without_tests")

    def test_file_path_change_changes_uid(self) -> None:
        first = _finding(files=["src/app.py"])
        second = _finding(files=["src/other.py"])

        self.assertNotEqual(first.uid, second.uid)

    def test_file_order_does_not_change_uid(self) -> None:
        first = _finding(files=["src/app.py", "src/other.py"])
        second = _finding(files=["src/other.py", "src/app.py"])

        self.assertEqual(first.uid, second.uid)

    def test_uid_does_not_expose_absolute_paths(self) -> None:
        finding = _finding(files=["/Users/example/private/project/src/app.py"])

        self.assertTrue(finding.uid.startswith("fnd_"))
        self.assertNotIn("Users", finding.uid)
        self.assertNotIn("private", finding.uid)
        self.assertNotIn("src/app.py", finding.uid)

    def test_json_report_includes_uid_kind_and_schema_version(self) -> None:
        with TemporaryDirectory() as tmp:
            result = run_review(
                repo_path=".",
                diff_path=FIXTURES / "simple.patch",
                task_path=FIXTURES / "task.md",
                output_dir=tmp,
            )
            payload = json.loads((Path(tmp) / "forgebench-report.json").read_text(encoding="utf-8"))

        self.assertEqual(payload["schema_version"], "1.2.0")
        self.assertEqual(REPORT_SCHEMA_VERSION, "1.2.0")
        self.assertTrue(payload["findings"])
        first = payload["findings"][0]
        self.assertTrue(first["uid"].startswith("fnd_"))
        self.assertEqual(first["kind"], first["id"])
        self.assertEqual({finding.kind for finding in result.report.findings}, {finding.id for finding in result.report.findings})


def _finding(files: list[str]) -> Finding:
    return Finding(
        id="implementation_without_tests",
        title="Implementation changed without tests",
        severity=Severity.MEDIUM,
        confidence=Confidence.MEDIUM,
        evidence_type=EvidenceType.STATIC,
        files=files,
        explanation="Implementation changed without corresponding tests.",
        suggested_fix="Add focused tests.",
    )


if __name__ == "__main__":
    unittest.main()
