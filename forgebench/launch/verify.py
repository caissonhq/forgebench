from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from forgebench import __version__


ROOT = Path(__file__).resolve().parents[2]
TARGET_VERSION = "1.0.0"


@dataclass(frozen=True)
class LaunchCheck:
    name: str
    status: str  # pass, warn, fail
    message: str
    fix_hint: str | None = None


def verify_launch_readiness(*, repo_root: str | Path | None = None) -> list[LaunchCheck]:
    root = Path(repo_root) if repo_root else ROOT
    checks: list[LaunchCheck] = []

    checks.append(_check_version(root))
    checks.append(_check_changelog(root))
    checks.append(_check_release_workflow(root))
    checks.append(_check_release_notes(root))
    checks.append(_check_launch_docs(root))
    checks.append(_check_public_stats(root))
    checks.append(_check_mkdocs_config(root))
    checks.append(_check_marketplace_kits(root))
    checks.append(_check_announcements_final(root))
    checks.append(_check_git_tag(root))
    checks.append(_check_dist_artifacts(root))
    checks.append(_check_docs_build(root))

    return checks


def format_launch_report(checks: list[LaunchCheck]) -> str:
    passed = sum(1 for c in checks if c.status == "pass")
    warned = sum(1 for c in checks if c.status == "warn")
    failed = sum(1 for c in checks if c.status == "fail")
    lines = [
        f"ForgeBench launch readiness — v{__version__}",
        "",
        f"Checks: {passed} pass · {warned} warn · {failed} fail",
        "",
    ]
    for check in checks:
        icon = {"pass": "✓", "warn": "!", "fail": "✗"}.get(check.status, "?")
        lines.append(f"  [{icon}] {check.name}: {check.message}")
        if check.fix_hint and check.status != "pass":
            lines.append(f"      → {check.fix_hint}")
    lines.extend(
        [
            "",
            "Manual launch day:",
            "  docs/launch/LAUNCH_DAY_CHECKLIST.md",
            "  docs/launch/announcements-final.md",
            "  docs/launch/LAUNCH_FOLLOWUP.md",
        ]
    )
    return "\n".join(lines)


def launch_ready(checks: list[LaunchCheck]) -> bool:
    return all(c.status != "fail" for c in checks)


def _check_version(root: Path) -> LaunchCheck:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return LaunchCheck("version", "fail", "pyproject.toml missing")
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject.read_text(encoding="utf-8"), re.MULTILINE)
    version = match.group(1) if match else ""
    if version == TARGET_VERSION and __version__ == TARGET_VERSION:
        return LaunchCheck("version", "pass", f"{TARGET_VERSION} in pyproject.toml and package")
    return LaunchCheck(
        "version",
        "fail",
        f"expected {TARGET_VERSION}, got pyproject={version} package={__version__}",
        "Bump pyproject.toml to 1.0.0",
    )


def _check_changelog(root: Path) -> LaunchCheck:
    path = root / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if f"## {TARGET_VERSION}" in text or f"## {TARGET_VERSION} —" in text:
        return LaunchCheck("changelog", "pass", f"{TARGET_VERSION} section present")
    return LaunchCheck("changelog", "fail", f"CHANGELOG missing {TARGET_VERSION}", "Add release section to CHANGELOG.md")


def _check_release_workflow(root: Path) -> LaunchCheck:
    workflow = root / ".github" / "workflows" / "release.yml"
    if workflow.exists() and "tags:" in workflow.read_text(encoding="utf-8"):
        return LaunchCheck("release_pipeline", "pass", "release.yml tag trigger configured")
    return LaunchCheck("release_pipeline", "fail", "release.yml missing or incomplete")


def _check_release_notes(root: Path) -> LaunchCheck:
    path = root / "docs" / "launch" / "RELEASE_v1.0.0.md"
    if path.exists():
        return LaunchCheck("release_notes", "pass", str(path.relative_to(root)))
    return LaunchCheck("release_notes", "fail", "RELEASE_v1.0.0.md missing")


def _check_launch_docs(root: Path) -> LaunchCheck:
    required = [
        "docs/launch/LAUNCH_DAY_CHECKLIST.md",
        "docs/launch/announcements-final.md",
        "docs/launch/LAUNCH_FOLLOWUP.md",
        "docs/launch/BLOG_ANNOUNCEMENT.md",
        "docs/marketing-home.md",
    ]
    missing = [item for item in required if not (root / item).exists()]
    if not missing:
        return LaunchCheck("launch_docs", "pass", f"{len(required)} launch artifacts present")
    return LaunchCheck("launch_docs", "warn", f"missing: {', '.join(missing)}")


def _check_public_stats(root: Path) -> LaunchCheck:
    path = root / "examples" / "launch" / "public-stats.json"
    if not path.exists():
        return LaunchCheck("public_stats", "fail", "public-stats.json missing")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return LaunchCheck("public_stats", "fail", "public-stats.json malformed")
    if "launch_date" in payload and "github_stars" in payload:
        return LaunchCheck("public_stats", "pass", f"updated {payload.get('updated_at', '')}")
    return LaunchCheck("public_stats", "warn", "add launch_date after go-live", "forgebench launch stats --stars N")


def _check_mkdocs_config(root: Path) -> LaunchCheck:
    mkdocs = root / "mkdocs.yml"
    if mkdocs.exists() and (root / "site-docs" / "index.md").exists():
        return LaunchCheck("docs_site", "pass", "mkdocs.yml + site-docs/index.md")
    return LaunchCheck("docs_site", "fail", "MkDocs site incomplete")


def _check_marketplace_kits(root: Path) -> LaunchCheck:
    kits = [
        "integrations/vscode-forgebench/MARKETPLACE.md",
        "docs/vscode-marketplace-submission.md",
        "docs/github-marketplace-listing.md",
        ".github/workflows/vscode-marketplace.yml",
    ]
    missing = [k for k in kits if not (root / k).exists()]
    if len(missing) <= 1:
        return LaunchCheck("marketplace_kits", "pass", "VS Code / GitHub App listing kits ready")
    return LaunchCheck("marketplace_kits", "warn", f"missing kits: {', '.join(missing)}")


def _check_announcements_final(root: Path) -> LaunchCheck:
    path = root / "docs" / "launch" / "announcements-final.md"
    if path.exists() and "Show HN" in path.read_text(encoding="utf-8"):
        return LaunchCheck("announcements", "pass", "announcements-final.md ready to post")
    return LaunchCheck("announcements", "warn", "finalize announcements-final.md")


def _check_git_tag(root: Path) -> LaunchCheck:
    try:
        result = subprocess.run(
            ["git", "tag", "-l", f"v{TARGET_VERSION}"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if f"v{TARGET_VERSION}" in (result.stdout or ""):
            return LaunchCheck("git_tag", "pass", f"v{TARGET_VERSION} tag exists locally")
        return LaunchCheck(
            "git_tag",
            "warn",
            f"v{TARGET_VERSION} tag not found locally",
            f"git tag v{TARGET_VERSION} && git push origin v{TARGET_VERSION}",
        )
    except OSError:
        return LaunchCheck("git_tag", "warn", "git not available for tag check")


def _check_dist_artifacts(root: Path) -> LaunchCheck:
    dist = root / "dist"
    wheels = list(dist.glob("forgebench-*.whl")) if dist.is_dir() else []
    if wheels:
        return LaunchCheck("dist_artifacts", "pass", f"{len(wheels)} wheel(s) in dist/")
    return LaunchCheck(
        "dist_artifacts",
        "warn",
        "no local wheel in dist/ (CI builds on tag)",
        "python -m build  OR  push v1.0.0 tag",
    )


def _check_docs_build(root: Path) -> LaunchCheck:
    mkdocs = root / "mkdocs.yml"
    if not mkdocs.exists():
        return LaunchCheck("mkdocs_build", "fail", "mkdocs.yml missing")
    try:
        result = subprocess.run(
            ["mkdocs", "build", "--strict"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return LaunchCheck("mkdocs_build", "pass", "mkdocs build --strict succeeded")
        return LaunchCheck("mkdocs_build", "warn", "mkdocs build failed", "pip install mkdocs-material && mkdocs build --strict")
    except OSError:
        return LaunchCheck("mkdocs_build", "warn", "mkdocs not installed locally", "pip install mkdocs-material")