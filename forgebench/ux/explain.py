from __future__ import annotations


EXPLANATIONS: dict[str, str] = {
    "run_checks requires": (
        "ForgeBench will not run shell commands from an untrusted PR-head forgebench.yml. "
        "Pass --guardrails .github/forgebench.yml (trusted base-branch policy) with --checkout-pr."
    ),
    "refusing to overwrite": "Use --force to replace an existing guardrails file, or pick a different --out path.",
    "GitHub PR intake requires": "Install GitHub CLI: https://cli.github.com — then run `gh auth login`.",
    "repo path does not exist": "Check --repo points to your project root (directory containing source code).",
    "guardrails file does not exist": "Run `forgebench init` or `forgebench init --enterprise` to create starter policy.",
    "diff file does not exist": "Export a unified diff: `git diff main...HEAD > patch.diff` and pass --diff with the file path.",
    "task file does not exist": "Save the original agent prompt to task.md and pass --task task.md",
    "FORGEBENCH_GITHUB_WEBHOOK_SECRET": "Set a 16+ character secret before `forgebench github-app serve`.",
    "Path '": "Policy paths must stay inside the repository. Check extends/include/fpl references.",
    "unknown preset": "Use --preset auto|python|node|nextjs|swift|rust",
    "review-pr requires": "Pass a GitHub PR URL: forgebench review-pr https://github.com/org/repo/pull/123",
    "run_checks requires --checkout-pr": "Add --checkout-pr so checks run against PR code, not your current checkout.",
    "Guardrails path must resolve": "Pin CI guardrails to .github/forgebench.yml on the base branch.",
}


def explain_error(message: str) -> str | None:
    lowered = message.lower()
    for key, explanation in EXPLANATIONS.items():
        if key.lower() in lowered:
            return explanation
    return None