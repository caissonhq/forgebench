from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from forgebench.cli import main
from forgebench.guardrails import parse_guardrails
from forgebench.init import InitError, write_starter_guardrails


FIXTURES = Path(__file__).parent / "fixtures" / "init_repos"


class InitTests(unittest.TestCase):
    def test_python_repo_defaults_to_unittest(self) -> None:
        repo = _copy_fixture("python")

        result = write_starter_guardrails(repo)
        guardrails = parse_guardrails(result.path.read_text(encoding="utf-8"))

        self.assertEqual(guardrails.project, repo.name)
        self.assertEqual(guardrails.checks["test"], "python3 -m unittest discover -s tests")
        self.assertIsNone(guardrails.checks["build"])
        self.assertIn("pyproject.toml", result.detected)

    def test_node_repo_uses_existing_npm_scripts(self) -> None:
        repo = _copy_fixture("node")

        result = write_starter_guardrails(repo)
        guardrails = parse_guardrails(result.path.read_text(encoding="utf-8"))

        self.assertEqual(guardrails.checks["build"], "npm run build")
        self.assertEqual(guardrails.checks["test"], "npm run test")
        self.assertEqual(guardrails.checks["lint"], "npm run lint")
        self.assertEqual(guardrails.checks["typecheck"], "npm run typecheck")

    def test_rust_repo_defaults_to_cargo(self) -> None:
        repo = _copy_fixture("rust")

        result = write_starter_guardrails(repo)
        guardrails = parse_guardrails(result.path.read_text(encoding="utf-8"))

        self.assertEqual(guardrails.checks["build"], "cargo build")
        self.assertEqual(guardrails.checks["test"], "cargo test")

    def test_swift_repo_defaults_to_swift_package_commands(self) -> None:
        repo = _copy_fixture("swift")

        result = write_starter_guardrails(repo)
        guardrails = parse_guardrails(result.path.read_text(encoding="utf-8"))

        self.assertEqual(guardrails.checks["build"], "swift build")
        self.assertEqual(guardrails.checks["test"], "swift test")

    def test_unknown_repo_sets_all_checks_to_null(self) -> None:
        repo = _copy_fixture("unknown")

        result = write_starter_guardrails(repo)
        guardrails = parse_guardrails(result.path.read_text(encoding="utf-8"))

        self.assertEqual(guardrails.checks, {"build": None, "test": None, "lint": None, "typecheck": None})
        self.assertEqual(result.detected, [])

    def test_codeowners_is_added_as_medium_risk_path(self) -> None:
        repo = _copy_fixture("codeowners")

        result = write_starter_guardrails(repo)
        guardrails = parse_guardrails(result.path.read_text(encoding="utf-8"))

        self.assertEqual(guardrails.risk_files_medium, [".github/CODEOWNERS"])

    def test_no_overwrite_without_force(self) -> None:
        repo = _copy_fixture("python")
        write_starter_guardrails(repo)

        with self.assertRaises(InitError) as raised:
            write_starter_guardrails(repo)

        self.assertIn("refusing to overwrite", str(raised.exception))

    def test_overwrite_with_force(self) -> None:
        repo = _copy_fixture("python")
        first = write_starter_guardrails(repo)
        first.path.write_text("project: stale\n", encoding="utf-8")

        second = write_starter_guardrails(repo, force=True)
        guardrails = parse_guardrails(second.path.read_text(encoding="utf-8"))

        self.assertEqual(guardrails.project, repo.name)

    def test_missing_repo_errors_clearly(self) -> None:
        with self.assertRaises(InitError) as raised:
            write_starter_guardrails("/does/not/exist")

        self.assertIn("repo path does not exist", str(raised.exception))

    def test_cli_init_writes_parseable_yaml(self) -> None:
        repo = _copy_fixture("python")
        stdout = StringIO()

        with redirect_stdout(stdout):
            result = main(["init", "--repo", str(repo), "--out", "custom-forgebench.yml"])

        output = repo / "custom-forgebench.yml"
        self.assertEqual(result, 0)
        self.assertTrue(output.exists())
        self.assertIn("ForgeBench guardrails file created.", stdout.getvalue())
        parse_guardrails(output.read_text(encoding="utf-8"))

    def test_cli_init_missing_repo_exits_cleanly(self) -> None:
        stderr = StringIO()

        with self.assertRaises(SystemExit) as raised, redirect_stderr(stderr):
            main(["init", "--repo", "/does/not/exist"])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("repo path does not exist", stderr.getvalue())

    def test_each_explicit_preset_writes_valid_yaml(self) -> None:
        for preset in ("python", "node", "nextjs", "swift", "rust"):
            with self.subTest(preset=preset):
                repo = _copy_fixture("unknown")
                result = write_starter_guardrails(repo, preset=preset)
                guardrails = parse_guardrails(result.path.read_text(encoding="utf-8"))

                self.assertEqual(guardrails.project, repo.name)
                self.assertIn(f"preset:{preset}", result.detected)

    def test_nextjs_preset_uses_package_scripts_when_present(self) -> None:
        repo = _copy_fixture("node")

        result = write_starter_guardrails(repo, preset="nextjs")
        guardrails = parse_guardrails(result.path.read_text(encoding="utf-8"))

        self.assertEqual(guardrails.checks["build"], "npm run build")
        self.assertIn("app/**", guardrails.risk_files_medium)
        self.assertIn("components/**", guardrails.risk_files_medium)

    def test_unknown_preset_errors_clearly(self) -> None:
        repo = _copy_fixture("unknown")

        with self.assertRaises(InitError) as raised:
            write_starter_guardrails(repo, preset="rails")

        self.assertIn("unknown preset", str(raised.exception))

    def test_explicit_preset_does_not_run_subprocesses(self) -> None:
        repo = _copy_fixture("python")

        with patch("subprocess.run", side_effect=AssertionError("subprocess should not run")):
            result = write_starter_guardrails(repo, preset="python")

        parse_guardrails(result.path.read_text(encoding="utf-8"))

    def test_cli_init_accepts_preset(self) -> None:
        repo = _copy_fixture("unknown")
        stdout = StringIO()

        with redirect_stdout(stdout):
            result = main(["init", "--repo", str(repo), "--preset", "rust"])

        guardrails = parse_guardrails((repo / "forgebench.yml").read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(guardrails.checks["build"], "cargo build")
        self.assertIn("Detected: preset:rust", stdout.getvalue())


def _copy_fixture(name: str) -> Path:
    temp = TemporaryDirectory()
    repo = Path(temp.name) / name
    copytree(FIXTURES / name, repo)
    _TEMP_DIRS.append(temp)
    return repo


_TEMP_DIRS: list[TemporaryDirectory] = []


if __name__ == "__main__":
    unittest.main()
