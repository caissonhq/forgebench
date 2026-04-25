from pathlib import Path
import unittest

from forgebench.diff_parser import parse_diff_file


FIXTURES = Path(__file__).parent / "fixtures"


class DiffParserTests(unittest.TestCase):
    def test_extracts_changed_files(self) -> None:
        diff = parse_diff_file(FIXTURES / "simple.patch")

        self.assertEqual(diff.changed_files, ["src/calculator.py", "README.md"])

    def test_identifies_added_and_deleted_lines(self) -> None:
        diff = parse_diff_file(FIXTURES / "simple.patch")
        calculator = diff.files[0]

        self.assertIn("    result = a + b", calculator.added_lines)
        self.assertIn("    return a - b", calculator.deleted_lines)
        self.assertEqual(calculator.added_line_count, 2)
        self.assertEqual(calculator.deleted_line_count, 1)

    def test_handles_realistic_git_diff_edge_cases(self) -> None:
        diff = parse_diff_file(FIXTURES / "parser_edge_cases.patch")

        self.assertEqual(
            diff.changed_files,
            [
                "docs/New Release Notes.md",
                "src/new module.py",
                "src/old_module.py",
                "assets/logo.png",
            ],
        )

        renamed = diff.files[0]
        self.assertTrue(renamed.is_renamed)
        self.assertEqual(renamed.old_path, "docs/Old Release Notes.md")
        self.assertEqual(len(renamed.hunks), 2)
        self.assertIn("New intro", renamed.added_lines)
        self.assertIn("Old intro", renamed.deleted_lines)

        added = diff.files[1]
        self.assertTrue(added.is_added)
        self.assertEqual(added.path, "src/new module.py")
        self.assertEqual(added.added_line_count, 3)

        deleted = diff.files[2]
        self.assertTrue(deleted.is_deleted)
        self.assertEqual(deleted.deleted_line_count, 2)

        binary = diff.files[3]
        self.assertTrue(binary.is_binary)
        self.assertTrue(binary.is_added)


if __name__ == "__main__":
    unittest.main()
