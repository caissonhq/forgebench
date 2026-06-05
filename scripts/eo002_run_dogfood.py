#!/usr/bin/env python3
"""Run ForgeBench review-pr on a list of real GitHub PRs for EO-002 dogfood."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLONE_ROOT = Path("/tmp/forgebench-eo002-clones")
RUN_ROOT = ROOT / "dogfood_runs" / "eo002-2026-06-05"
FEEDBACK_LOG = RUN_ROOT / "feedback.jsonl"
SUMMARY_JSON = RUN_ROOT / "runs.json"


@dataclass(frozen=True)
class DogfoodTarget:
    slug: str
    repo: str
    number: int

    @property
    def url(self) -> str:
        return f"https://github.com/{self.repo}/pull/{self.number}"


TARGETS = [
    DogfoodTarget("caissonhq-forgebench-1", "caissonhq/forgebench", 1),
    DogfoodTarget("caissonhq-24hragent-1", "caissonhq/24hragent", 1),
    DogfoodTarget("vercel-workflow-2238", "vercel/workflow", 2238),
    DogfoodTarget("officebeats-beats-pm-kit-15", "officebeats/beats-pm-kit", 15),
    DogfoodTarget("hyperflow-5", "Mohammed-Abdelhady/hyperflow", 5),
    DogfoodTarget("bourdon-113", "getbourdon/bourdon", 113),
    DogfoodTarget("t3code-2973-cursor", "pingdotgg/t3code", 2973),
    DogfoodTarget("t3code-2968-effect", "pingdotgg/t3code", 2968),
    DogfoodTarget("t3code-2955-codex", "pingdotgg/t3code", 2955),
    DogfoodTarget("tsumi233-cc-switch-1", "tsumi233/cc-switch", 1),
]


def main() -> int:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    CLONE_ROOT.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []

    for target in TARGETS:
        print(f"\n=== {target.slug} ===", flush=True)
        result = _run_one(target)
        results.append(result)
        print(json.dumps({k: result[k] for k in ("slug", "ok", "posture", "finding_count")}, indent=2))

    SUMMARY_JSON.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {SUMMARY_JSON}")
    failed = [r for r in results if not r.get("ok")]
    return 1 if failed else 0


def _run_one(target: DogfoodTarget) -> dict[str, object]:
    slug_dir = RUN_ROOT / target.slug
    slug_dir.mkdir(parents=True, exist_ok=True)
    clone_dir = _ensure_clone(target.repo)
    out_dir = slug_dir / "forgebench-output"
    if out_dir.exists():
        shutil.rmtree(out_dir)

    cmd = [
        sys.executable,
        "-m",
        "forgebench",
        "review-pr",
        target.url,
        "--repo",
        str(clone_dir),
        "--out",
        str(out_dir),
        "--no-reviewers",
    ]
    cmd_with_reviewers = cmd[:-1]  # drop --no-reviewers

    # Primary run: reviewers enabled (default)
    cmd_reviewers = [
        sys.executable,
        "-m",
        "forgebench",
        "review-pr",
        target.url,
        "--repo",
        str(clone_dir),
        "--out",
        str(out_dir),
    ]
    (slug_dir / "command.txt").write_text(" ".join(cmd_reviewers) + "\n", encoding="utf-8")

    completed = subprocess.run(cmd_reviewers, cwd=ROOT, text=True, capture_output=True)
    (slug_dir / "stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (slug_dir / "stderr.txt").write_text(completed.stderr, encoding="utf-8")

    report_json = out_dir / "forgebench-report.json"
    meta_path = out_dir / "github-pr-metadata.json"
    record: dict[str, object] = {
        "slug": target.slug,
        "repo": target.repo,
        "number": target.number,
        "url": target.url,
        "ok": completed.returncode == 0,
        "exit_code": completed.returncode,
        "clone_dir": str(clone_dir),
        "output_dir": str(out_dir),
        "ran_at": datetime.now(timezone.utc).isoformat(),
    }

    if meta_path.exists():
        record["pr_metadata"] = json.loads(meta_path.read_text(encoding="utf-8"))

    if not report_json.exists():
        record["error"] = completed.stderr.strip() or "missing report json"
        return record

    report = json.loads(report_json.read_text(encoding="utf-8"))
    record["posture"] = report.get("posture")
    record["config_mode"] = report.get("config_mode")
    record["finding_ids"] = [f.get("id") for f in report.get("findings", [])]
    record["finding_kinds"] = [f.get("kind") or f.get("id") for f in report.get("findings", [])]
    record["finding_count"] = len(report.get("findings", []))
    record["reviewer_findings"] = _reviewer_finding_counts(report)
    record["summary"] = report.get("summary", "")

    # Copy patch/task for golden case authoring
    for name in ("patch.diff", "task.md"):
        src = out_dir / name
        if src.exists():
            shutil.copy2(src, slug_dir / name)

    return record


def _reviewer_finding_counts(report: dict[str, object]) -> dict[str, int]:
    reviewers = report.get("specialized_reviewers") or {}
    results = reviewers.get("results") or []
    counts: dict[str, int] = {}
    for item in results:
        if not isinstance(item, dict):
            continue
        reviewer_id = str(item.get("reviewer_id") or item.get("reviewer_name") or "unknown")
        findings = item.get("findings") or []
        counts[reviewer_id] = len(findings) if isinstance(findings, list) else 0
    return counts


def _ensure_clone(repo: str) -> Path:
    slug = repo.replace("/", "-").lower()
    clone_dir = CLONE_ROOT / slug
    if clone_dir.exists():
        return clone_dir
    url = f"https://github.com/{repo}.git"
    subprocess.run(
        ["git", "clone", "--depth", "1", url, str(clone_dir)],
        check=True,
        text=True,
        capture_output=True,
    )
    return clone_dir


if __name__ == "__main__":
    raise SystemExit(main())