from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.cli import main
from forgebench.share_report import ShareReportError, export_shareable_report


class ShareReportTests(unittest.TestCase):
    def test_export_shareable_report(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "forgebench-report.md").write_text("# Report\nPosture REVIEW\n", encoding="utf-8")
            (out / "forgebench-report.json").write_text(
                '{"posture": "REVIEW", "findings": [{"uid": "fnd_1"}]}',
                encoding="utf-8",
            )
            result = export_shareable_report(output_dir=out)
            self.assertTrue(result.html_path.exists())
            html = result.html_path.read_text(encoding="utf-8")
            self.assertIn("REVIEW", html)
            self.assertIn("ForgeBench Merge-Risk Report", html)

    def test_missing_report_raises(self) -> None:
        with TemporaryDirectory() as tmp:
            with self.assertRaises(ShareReportError):
                export_shareable_report(output_dir=tmp)

    def test_cli_share_report(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "forgebench-report.md").write_text("hello", encoding="utf-8")
            stdout = StringIO()
            with redirect_stdout(stdout):
                result = main(["share-report", "--out", str(out)])
            self.assertEqual(result, 0)
            self.assertTrue((out / "forgebench-share.html").exists())