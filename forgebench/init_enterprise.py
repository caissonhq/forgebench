from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from forgebench.init import InitError, write_starter_guardrails
from forgebench.ux.output import heading, info, progress, success, write_kv


@dataclass(frozen=True)
class EnterpriseInitOptions:
    org_name: str = "Acme Engineering"
    team_slug: str = "platform"
    preset: str = "auto"
    enable_github_app: bool = True
    enable_ci: bool = True
    ci_provider: str = "github-actions"
    org_policy_dir: str = "org-policy"
    force: bool = False
    non_interactive: bool = False
    wizard_mode: str = "enterprise"
    agent_pr_mode: bool = True


@dataclass(frozen=True)
class EnterpriseInitResult:
    repo_path: Path
    guardrails_path: Path
    org_policy_path: Path
    ci_guardrails_path: Path | None
    workflow_path: Path | None
    onboarding_doc_path: Path
    readme_snippet_path: Path
    detected: list[str] = field(default_factory=list)


def run_enterprise_init(
    repo_path: str | Path = ".",
    *,
    options: EnterpriseInitOptions | None = None,
) -> EnterpriseInitResult:
    repo = Path(repo_path).resolve()
    if not repo.exists() or not repo.is_dir():
        raise InitError(f"repo path does not exist or is not a directory: {repo}")

    opts = options or _prompt_options(repo)
    title = "ForgeBench Team Init" if opts.wizard_mode == "team" else "ForgeBench Enterprise Init"
    heading(title)
    if opts.wizard_mode == "team":
        info("Magic team onboarding — org policy, CI, guardrails, and docs in one flow.")
    info(f"Repository: {repo}")
    write_kv("Organization", opts.org_name)
    write_kv("Team", opts.team_slug)
    write_kv("Preset", opts.preset)

    progress("Writing org policy layer")
    org_dir = repo / opts.org_policy_dir
    org_policy_path = org_dir / "forgebench-org.yml"
    _write_org_policy(org_policy_path, opts, force=opts.force)
    if opts.enable_github_app:
        _write_github_app_install_guide(repo / "docs" / "forgebench-github-app.md", opts, force=opts.force)

    progress("Writing repository guardrails")
    guardrails_path = repo / "forgebench.yml"
    init_result = write_starter_guardrails(
        repo_path=repo,
        output_path=guardrails_path,
        force=opts.force,
        preset=opts.preset,
    )
    _patch_repo_guardrails(guardrails_path, org_policy_path, opts)

    ci_guardrails_path: Path | None = None
    workflow_path: Path | None = None
    if opts.enable_ci and opts.ci_provider == "github-actions":
        progress("Generating GitHub Actions workflow and CI guardrails")
        ci_guardrails_path = repo / ".github" / "forgebench.yml"
        workflow_path = repo / ".github" / "workflows" / "forgebench.yml"
        _write_ci_guardrails(ci_guardrails_path, org_policy_path, opts, force=opts.force)
        _write_github_workflow(workflow_path, opts, force=opts.force)

    progress("Writing team onboarding guide")
    onboarding_doc_path = repo / "docs" / "forgebench-onboarding.md"
    _write_onboarding_doc(onboarding_doc_path, opts, force=opts.force)

    readme_snippet_path = repo / "docs" / "forgebench-readme-snippet.md"
    _write_readme_snippet(readme_snippet_path, opts, force=opts.force)

    success("Enterprise starter kit generated.")
    return EnterpriseInitResult(
        repo_path=repo,
        guardrails_path=guardrails_path,
        org_policy_path=org_policy_path,
        ci_guardrails_path=ci_guardrails_path,
        workflow_path=workflow_path,
        onboarding_doc_path=onboarding_doc_path,
        readme_snippet_path=readme_snippet_path,
        detected=init_result.detected,
    )


def _prompt_options(repo: Path) -> EnterpriseInitOptions:
    interactive = sys.stdin.isatty() and sys.stdout.isatty()
    if not interactive:
        return EnterpriseInitOptions(non_interactive=True)

    org_name = _prompt("Organization or team name", "Acme Engineering")
    team_slug = _prompt("Team slug (for policy paths)", "platform")
    preset = _prompt("Primary stack preset (auto|python|node|nextjs|swift|rust)", "auto")
    agent_pr_mode = _prompt_yes_no("Optimize guardrails for AI agent PRs?", default=True)
    enable_github_app = _prompt_yes_no("Include GitHub App install + auto-config notes?", default=True)
    enable_ci = _prompt_yes_no("Generate GitHub Actions CI workflow?", default=True)
    return EnterpriseInitOptions(
        org_name=org_name,
        team_slug=team_slug,
        preset=preset,
        enable_github_app=enable_github_app,
        enable_ci=enable_ci,
        non_interactive=False,
        wizard_mode="enterprise",
        agent_pr_mode=agent_pr_mode,
    )


def _prompt(label: str, default: str) -> str:
    raw = input(f"{label} [{default}]: ").strip()
    return raw or default


def _prompt_yes_no(label: str, *, default: bool) -> bool:
    hint = "Y/n" if default else "y/N"
    raw = input(f"{label} ({hint}): ").strip().lower()
    if not raw:
        return default
    return raw in {"y", "yes", "true", "1"}


def _write_text(path: Path, content: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise InitError(f"refusing to overwrite existing file: {path}. Re-run with --force.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_org_policy(path: Path, opts: EnterpriseInitOptions, *, force: bool) -> None:
    agent_behavior = ""
    if opts.agent_pr_mode:
        agent_behavior = (
            "  - Agent patches must stay within stated task scope\n"
            "  - Behavior changes require tests or explicit rationale in the PR\n"
        )
    content = f"""# Org-wide ForgeBench policy for {opts.org_name}
# Merge into repos via extends or FORGEBENCH_ORG_POLICY.
# Schema: https://forgebench.dev/docs/forgebench-yml-schema/

team:
  name: {opts.org_name}
  slug: {opts.team_slug}

protected_behavior:
  - No direct production database writes from agent-generated patches
  - No secrets, API keys, or credentials committed in diffs
  - Auth and payment flows require human review before merge
{agent_behavior}

forbidden_patterns:
  - eval(
  - exec(
  - subprocess\\.call\\(.*shell=True

risk_files:
  high:
    - "**/auth/**"
    - "**/payment/**"
    - "**/migrations/**"
    - ".github/workflows/**"
  medium:
    - "src/**"
    - "lib/**"
    - "app/**"

policy:
  path_categories:
    docs:
      patterns:
        - "README.md"
        - "docs/**"
        - "**/*.md"
      default_severity: advisory
"""
    _write_text(path, content, force=force)


def _write_github_app_install_guide(path: Path, opts: EnterpriseInitOptions, *, force: bool) -> None:
    content = f"""# ForgeBench GitHub App — install & auto-configuration

## 1. Export manifest

```bash
forgebench github-app manifest --out forgebench-output/github-app-manifest.json
```

## 2. Create the GitHub App

Use the manifest with GitHub's manifest flow or register manually with permissions from the JSON file.

## 3. Install on your organization

After install, ForgeBench auto-configuration creates:

- `.github/forgebench.yml` (trusted CI guardrails) — already present if you ran team init
- `.github/workflows/forgebench.yml` — PR review workflow
- Webhook target: your self-hosted `forgebench github-app serve` endpoint

## 4. Post-install verification

```bash
forgebench github-app enforce --config org-policy/github-app-enforcement.json --posture REVIEW
forgebench doctor --repo .
```

## 5. Secrets

Set `FORGEBENCH_GITHUB_WEBHOOK_SECRET` (16+ characters) on the webhook receiver host.

Team: {opts.org_name} · Docs: https://forgebench.dev/docs/github-app-listing.md
"""
    _write_text(path, content, force=force)


def _patch_repo_guardrails(path: Path, org_policy: Path, opts: EnterpriseInitOptions) -> None:
    text = path.read_text(encoding="utf-8")
    rel = _relative_path(path.parent, org_policy)
    if "extends:" in text:
        return
    header = (
        f"# Enterprise repo guardrails for {opts.org_name}\n"
        f"extends: {rel}\n"
        f"team:\n  name: {opts.org_name}\n  repo_team: {opts.team_slug}\n\n"
    )
    if text.startswith("# Generated by"):
        lines = text.splitlines()
        insert_at = 0
        for index, line in enumerate(lines):
            if line.startswith("#") or not line.strip():
                insert_at = index + 1
                continue
            break
        path.write_text("\n".join(lines[:insert_at]) + "\n" + header + "\n".join(lines[insert_at:]) + "\n", encoding="utf-8")
    else:
        path.write_text(header + text, encoding="utf-8")


def _write_ci_guardrails(path: Path, org_policy: Path, opts: EnterpriseInitOptions, *, force: bool) -> None:
    rel = _relative_path(path.parent, org_policy)
    content = f"""# Trusted CI guardrails — base-branch policy only.
# Do not accept PR-head forgebench.yml for --run-checks without explicit trust.
extends: {rel}
project: {opts.org_name} CI
checks:
  test: null
  build: null
  lint: null
  typecheck: null
check_timeout_seconds: 300
"""
    _write_text(path, content, force=force)


def _write_github_workflow(path: Path, opts: EnterpriseInitOptions, *, force: bool) -> None:
    content = """name: ForgeBench

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write
  checks: write

jobs:
  merge-risk-review:
    name: ForgeBench merge-risk review
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install ForgeBench
        run: pip install forgebench

      - name: Run ForgeBench PR review
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          forgebench review-pr "${{ github.event.pull_request.html_url }}" \\
            --repo . \\
            --guardrails .github/forgebench.yml \\
            --checkout-pr \\
            --run-checks \\
            --check-run \\
            --out forgebench-output
"""
    _write_text(path, content, force=force)


def _write_onboarding_doc(path: Path, opts: EnterpriseInitOptions, *, force: bool) -> None:
    github_app = ""
    if opts.enable_github_app:
        github_app = """
## GitHub App (org-wide)

1. Register a GitHub App with pull request and check run permissions.
2. Set `FORGEBENCH_GITHUB_WEBHOOK_SECRET` (16+ characters) on the webhook receiver.
3. Run `forgebench github-app serve` on your policy host or use the Helm chart in `deployments/helm/forgebench/`.
4. Point org repos at `.github/forgebench.yml` on the default branch for trusted checks.
"""
    content = f"""# ForgeBench team onboarding — {opts.org_name}

Welcome to ForgeBench. This guide gets your team from zero to confident merge-risk review.

## New engineer checklist

- [ ] Run `forgebench doctor` and fix any failed checks
- [ ] Run `forgebench demo` to see a realistic review locally
- [ ] Run `forgebench status` for a health summary of this repo
- [ ] Install the VS Code or JetBrains ForgeBench extension
- [ ] Read `forgebench.yml` and `org-policy/forgebench-org.yml`
- [ ] Run `forgebench policy test --tests examples/policy_tests` before changing policy

## Daily workflow

```bash
forgebench review-pr PR_URL --guardrails .github/forgebench.yml --checkout-pr --run-checks
forgebench repair --out forgebench-output   # paste into your coding agent
```

## CI

GitHub Actions workflow: `.github/workflows/forgebench.yml`

Trusted guardrails for CI: `.github/forgebench.yml`
{github_app}
## Support

- Docs: https://forgebench.dev
- Troubleshooting: see `forgebench doctor` and `forgebench status --explain`
"""
    _write_text(path, content, force=force)


def _write_readme_snippet(path: Path, opts: EnterpriseInitOptions, *, force: bool) -> None:
    content = f"""## Merge-risk review (ForgeBench)

{opts.org_name} uses [ForgeBench](https://forgebench.dev) for adversarial pre-merge QA on AI-generated diffs.

```bash
forgebench doctor
forgebench status
forgebench review-pr <PR_URL> --guardrails .github/forgebench.yml --checkout-pr --run-checks
```

Team onboarding: [docs/forgebench-onboarding.md](docs/forgebench-onboarding.md)
"""
    _write_text(path, content, force=force)


def _relative_path(from_dir: Path, target: Path) -> str:
    try:
        return str(target.relative_to(from_dir))
    except ValueError:
        return str(target)


def format_enterprise_init_result(result: EnterpriseInitResult) -> str:
    lines = [
        "ForgeBench enterprise init complete.",
        "",
        f"Repo: {result.repo_path}",
        f"Guardrails: {result.guardrails_path}",
        f"Org policy: {result.org_policy_path}",
    ]
    if result.ci_guardrails_path:
        lines.append(f"CI guardrails: {result.ci_guardrails_path}")
    if result.workflow_path:
        lines.append(f"Workflow: {result.workflow_path}")
    lines.extend(
        [
            f"Onboarding: {result.onboarding_doc_path}",
            f"README snippet: {result.readme_snippet_path}",
            "",
            "Next steps:",
            "  forgebench validate --file forgebench.yml",
            "  forgebench policy test --tests examples/policy_tests",
            "  forgebench status",
        ]
    )
    if result.detected:
        lines.append(f"Detected: {', '.join(result.detected)}")
    return "\n".join(lines) + "\n"


def enterprise_init_manifest(result: EnterpriseInitResult) -> dict[str, object]:
    return {
        "repo_path": str(result.repo_path),
        "guardrails_path": str(result.guardrails_path),
        "org_policy_path": str(result.org_policy_path),
        "ci_guardrails_path": str(result.ci_guardrails_path) if result.ci_guardrails_path else None,
        "workflow_path": str(result.workflow_path) if result.workflow_path else None,
        "onboarding_doc_path": str(result.onboarding_doc_path),
        "readme_snippet_path": str(result.readme_snippet_path),
        "detected": result.detected,
    }


def write_enterprise_manifest(result: EnterpriseInitResult, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(enterprise_init_manifest(result), indent=2) + "\n", encoding="utf-8")
    return path