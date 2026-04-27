from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import yaml


class InitError(ValueError):
    pass


@dataclass(frozen=True)
class InitResult:
    path: Path
    repo_path: Path
    detected: list[str]


VALID_PRESETS = {"auto", "python", "node", "nextjs", "swift", "rust"}


def write_starter_guardrails(
    repo_path: str | Path = ".",
    output_path: str | Path = "forgebench.yml",
    force: bool = False,
    preset: str = "auto",
) -> InitResult:
    repo = Path(repo_path)
    if not repo.exists() or not repo.is_dir():
        raise InitError(f"repo path does not exist or is not a directory: {repo}")
    normalized_preset = preset.strip().lower()
    if normalized_preset not in VALID_PRESETS:
        raise InitError(f"unknown preset: {preset}. Expected one of: {', '.join(sorted(VALID_PRESETS))}.")

    output = _resolve_output_path(repo, Path(output_path))
    if output.exists() and not force:
        raise InitError(f"refusing to overwrite existing file: {output}. Re-run with --force to replace it.")

    checks, detected, risk_medium = _preset_parts(repo, normalized_preset)
    payload = _starter_payload(repo, checks, risk_medium)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_render_yaml(payload, normalized_preset), encoding="utf-8")
    return InitResult(path=output, repo_path=repo, detected=detected)


def _resolve_output_path(repo: Path, output: Path) -> Path:
    if output.is_absolute():
        return output
    return repo / output


def _detect_checks(repo: Path) -> tuple[dict[str, str | None], list[str]]:
    detected: list[str] = []
    checks: dict[str, str | None] = {
        "build": None,
        "test": None,
        "lint": None,
        "typecheck": None,
    }

    package_json = repo / "package.json"
    if package_json.exists():
        detected.append("package.json")
        scripts = _read_package_scripts(package_json)
        for name in ("build", "test", "lint", "typecheck"):
            if name in scripts:
                checks[name] = f"npm run {name}"
        return checks, detected

    if (repo / "pyproject.toml").exists():
        detected.append("pyproject.toml")
        checks["test"] = "python3 -m unittest discover -s tests"
        return checks, detected

    if (repo / "Cargo.toml").exists():
        detected.append("Cargo.toml")
        checks["build"] = "cargo build"
        checks["test"] = "cargo test"
        return checks, detected

    if (repo / "Package.swift").exists():
        detected.append("Package.swift")
        checks["build"] = "swift build"
        checks["test"] = "swift test"
        return checks, detected

    return checks, detected


def _preset_parts(repo: Path, preset: str) -> tuple[dict[str, str | None], list[str], list[str]]:
    if preset == "auto":
        checks, detected = _detect_checks(repo)
        return checks, detected, _detect_codeowners(repo)

    checks = _empty_checks()
    detected = [f"preset:{preset}"]
    risk_medium = _detect_codeowners(repo)
    if preset == "python":
        checks["test"] = "python3 -m unittest discover -s tests"
        risk_medium.extend(["src/**", "**/*.py"])
    elif preset == "node":
        checks.update(_checks_from_package_json(repo / "package.json"))
        risk_medium.extend(["src/**", "lib/**"])
    elif preset == "nextjs":
        checks.update(_checks_from_package_json(repo / "package.json"))
        risk_medium.extend(["app/**", "pages/**", "components/**", "src/**"])
    elif preset == "swift":
        if (repo / "Package.swift").exists():
            checks["build"] = "swift build"
            checks["test"] = "swift test"
        risk_medium.extend(["Sources/**", "Tests/**"])
    elif preset == "rust":
        checks["build"] = "cargo build"
        checks["test"] = "cargo test"
        risk_medium.extend(["src/**", "tests/**"])
    return checks, detected, sorted(set(risk_medium))


def _empty_checks() -> dict[str, str | None]:
    return {
        "build": None,
        "test": None,
        "lint": None,
        "typecheck": None,
    }


def _checks_from_package_json(path: Path) -> dict[str, str | None]:
    checks = _empty_checks()
    if not path.exists():
        return checks
    scripts = _read_package_scripts(path)
    for name in ("build", "test", "lint", "typecheck"):
        if name in scripts:
            checks[name] = f"npm run {name}"
    return checks


def _read_package_scripts(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    scripts = payload.get("scripts") if isinstance(payload, dict) else None
    return scripts if isinstance(scripts, dict) else {}


def _detect_codeowners(repo: Path) -> list[str]:
    candidates = [
        "CODEOWNERS",
        ".github/CODEOWNERS",
        "docs/CODEOWNERS",
    ]
    return [candidate for candidate in candidates if (repo / candidate).exists()]


def _starter_payload(repo: Path, checks: dict[str, str | None], risk_medium: list[str]) -> dict[str, object]:
    return {
        "project": repo.resolve().name,
        "protected_behavior": [],
        "forbidden_patterns": [],
        "risk_files": {
            "high": [],
            "medium": risk_medium,
        },
        "checks": checks,
        "check_timeout_seconds": 120,
        "policy": {
            "path_categories": {
                "docs": {
                    "patterns": [
                        "README.md",
                        "CHANGELOG.md",
                        "CONTRIBUTING.md",
                        "SECURITY.md",
                        "docs/**",
                        "**/*.md",
                    ],
                    "default_severity": "advisory",
                },
                "assets": {
                    "patterns": [
                        "**/*.png",
                        "**/*.jpg",
                        "**/*.jpeg",
                        "**/*.gif",
                        "**/*.webp",
                        "**/*.svg",
                        "**/*.ico",
                        "**/*.icns",
                        "**/Assets.xcassets/**",
                    ],
                    "default_severity": "advisory",
                },
            },
            "advisory_only": [
                "README.md",
                "docs/**",
                "**/*.md",
            ],
        },
    }


def _render_yaml(payload: dict[str, object], preset: str) -> str:
    header = (
        "# Generated by 'forgebench init'.\n"
        "# Edit freely.\n"
        "# Schema: docs/forgebench-yml-schema.md.\n"
        f"# Preset: {preset}.\n"
        "# protected_behavior and forbidden_patterns must be edited by a human.\n"
        "# risk_files.high is intentionally empty by default; add repo-specific high-risk paths.\n"
        "# Null checks mean ForgeBench found no safe default command for that slot.\n"
        "# Checks only run when --run-checks is explicitly passed.\n\n"
    )
    return header + yaml.safe_dump(payload, sort_keys=False, default_flow_style=False)
