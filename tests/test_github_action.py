from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
ACTION_DIR = ROOT / "action"


class GitHubActionTests(unittest.TestCase):
    def test_action_yml_exists_and_declares_required_inputs_outputs(self) -> None:
        payload = yaml.safe_load((ACTION_DIR / "action.yml").read_text(encoding="utf-8"))

        self.assertEqual(payload["runs"]["using"], "docker")
        self.assertEqual(payload["runs"]["image"], "Dockerfile")
        for input_name in ["pr-url", "guardrails-path", "run-checks", "post-comment", "llm-review", "llm-command"]:
            self.assertIn(input_name, payload["inputs"])
        self.assertEqual(payload["inputs"]["post-comment"]["default"], "false")
        self.assertEqual(payload["inputs"]["run-checks"]["default"], "false")
        self.assertEqual(payload["inputs"]["llm-review"]["default"], "false")
        for output_name in ["posture", "report-path", "pr-comment-path"]:
            self.assertIn(output_name, payload["outputs"])

    def test_entrypoint_does_not_post_comment_by_default(self) -> None:
        result = _run_entrypoint({"INPUT_PR_URL": "https://github.com/owner/repo/pull/1"})

        self.assertEqual(result.returncode, 0, result.stderr)
        args = result.args
        self.assertIn("--dry-run", args)
        self.assertNotIn("--post-comment", args)

    def test_entrypoint_adds_post_comment_only_when_true(self) -> None:
        result = _run_entrypoint(
            {
                "INPUT_PR_URL": "https://github.com/owner/repo/pull/1",
                "INPUT_POST_COMMENT": "true",
            }
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        args = result.args
        self.assertIn("--post-comment", args)
        self.assertNotIn("--dry-run", args)

    def test_entrypoint_maps_run_checks_flag(self) -> None:
        result = _run_entrypoint(
            {
                "INPUT_PR_URL": "https://github.com/owner/repo/pull/1",
                "INPUT_RUN_CHECKS": "true",
            }
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--run-checks", result.args)

    def test_entrypoint_maps_llm_review_flag(self) -> None:
        result = _run_entrypoint(
            {
                "INPUT_PR_URL": "https://github.com/owner/repo/pull/1",
                "INPUT_LLM_REVIEW": "true",
                "INPUT_LLM_COMMAND": "python reviewer.py",
            }
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        args = result.args
        self.assertIn("--llm-review", args)
        self.assertIn("--llm-provider", args)
        self.assertIn("command", args)
        self.assertIn("--llm-command", args)
        self.assertIn("python reviewer.py", args)

    def test_entrypoint_sets_outputs(self) -> None:
        result = _run_entrypoint({"INPUT_PR_URL": "https://github.com/owner/repo/pull/1"})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("posture=REVIEW", result.github_output)
        self.assertIn("report-path=", result.github_output)
        self.assertIn("pr-comment-path=", result.github_output)

    def test_entrypoint_fails_when_pr_url_missing(self) -> None:
        result = _run_entrypoint({})

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("pr-url is required", result.stderr)


class EntrypointResult:
    def __init__(self, completed: subprocess.CompletedProcess[str], args: list[str], github_output: str) -> None:
        self.returncode = completed.returncode
        self.stdout = completed.stdout
        self.stderr = completed.stderr
        self.args = args
        self.github_output = github_output


def _run_entrypoint(extra_env: dict[str, str]) -> EntrypointResult:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        workspace = root / "workspace"
        workspace.mkdir()
        bin_dir = root / "bin"
        bin_dir.mkdir()
        capture_file = root / "args.json"
        output_file = root / "github-output.txt"
        fake = bin_dir / "forgebench"
        fake.write_text(_fake_forgebench_script(), encoding="utf-8")
        fake.chmod(0o755)
        env = os.environ.copy()
        env.update(
            {
                "PATH": f"{bin_dir}{os.pathsep}{env.get('PATH', '')}",
                "GITHUB_WORKSPACE": str(workspace),
                "GITHUB_OUTPUT": str(output_file),
                "CAPTURE_FILE": str(capture_file),
            }
        )
        env.update(extra_env)
        completed = subprocess.run(
            ["bash", str(ACTION_DIR / "entrypoint.sh")],
            cwd=workspace,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        args = json.loads(capture_file.read_text(encoding="utf-8")) if capture_file.exists() else []
        github_output = output_file.read_text(encoding="utf-8") if output_file.exists() else ""
        return EntrypointResult(completed, args, github_output)


def _fake_forgebench_script() -> str:
    return """#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

Path(os.environ["CAPTURE_FILE"]).write_text(json.dumps(sys.argv[1:]), encoding="utf-8")
args = sys.argv[1:]
out = Path.cwd() / "forgebench-output"
if "--out" in args:
    out = Path(args[args.index("--out") + 1])
out.mkdir(parents=True, exist_ok=True)
(out / "forgebench-report.json").write_text(json.dumps({"posture": "REVIEW"}), encoding="utf-8")
(out / "forgebench-report.md").write_text("# report\\n", encoding="utf-8")
(out / "pr-comment.md").write_text("comment\\n", encoding="utf-8")
print("fake forgebench ran")
"""

if __name__ == "__main__":
    unittest.main()
