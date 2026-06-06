from __future__ import annotations

import os
import unittest
from unittest import mock

from forgebench.ux.explain import explain_error
from forgebench.ux.output import is_rich_output_enabled


class UxTests(unittest.TestCase):
    def test_explain_error_known_message(self) -> None:
        hint = explain_error("refusing to overwrite existing file: forgebench.yml")
        self.assertIsNotNone(hint)
        self.assertIn("--force", hint or "")

    def test_explain_error_unknown_message(self) -> None:
        self.assertIsNone(explain_error("something completely unknown"))

    def test_plain_output_env_disables_rich(self) -> None:
        with mock.patch.dict(os.environ, {"FORGEBENCH_PLAIN_OUTPUT": "1"}):
            self.assertFalse(is_rich_output_enabled())

    def test_no_color_disables_rich(self) -> None:
        with mock.patch.dict(os.environ, {"NO_COLOR": "1"}, clear=False):
            self.assertFalse(is_rich_output_enabled())


if __name__ == "__main__":
    unittest.main()