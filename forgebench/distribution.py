from __future__ import annotations

import os
import platform
import shutil
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from forgebench import __version__

MIN_PYTHON = (3, 10)


class InstallMethod(str, Enum):
    PIP = "pip"
    PIPX = "pipx"
    HOMEBREW = "homebrew"
    BINARY = "binary"
    SOURCE = "source"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class InstallMethodInfo:
    method: InstallMethod
    title: str
    one_liner: str
    command: str
    pros: tuple[str, ...]
    cons: tuple[str, ...]
    best_for: str


INSTALL_METHODS: tuple[InstallMethodInfo, ...] = (
    InstallMethodInfo(
        method=InstallMethod.PIPX,
        title="pipx (recommended for CLI)",
        one_liner="Isolated CLI install — no dependency conflicts.",
        command="pipx install forgebench",
        pros=("Isolated from project venvs", "Clean PATH shim", "Easy upgrade"),
        cons=("Requires pipx pre-installed",),
        best_for="Solo developers and daily CLI use",
    ),
    InstallMethodInfo(
        method=InstallMethod.PIP,
        title="pip",
        one_liner="Install into active Python environment.",
        command="pip install forgebench",
        pros=("Familiar", "Works in CI images", "Project-local venv friendly"),
        cons=("Can conflict with other packages", "Tied to one Python"),
        best_for="CI, Docker, and project virtualenvs",
    ),
    InstallMethodInfo(
        method=InstallMethod.HOMEBREW,
        title="Homebrew",
        one_liner="Native macOS/Linux package manager install.",
        command="brew tap caissonhq/tap && brew install forgebench",
        pros=("System-wide CLI", "Managed upgrades", "git + gh recommended deps"),
        cons=("macOS/Linux only", "Requires Homebrew"),
        best_for="macOS and Linux workstation setup",
    ),
    InstallMethodInfo(
        method=InstallMethod.BINARY,
        title="Binary bundle",
        one_liner="Official .tar.gz with embedded runtime — no pip required.",
        command="curl -fsSL https://github.com/caissonhq/forgebench/releases/latest/download/forgebench-$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m).tar.gz | tar -xz && sudo mv forgebench-*/bin/forgebench /usr/local/bin/",
        pros=("No Python setup", "Pinned release artifact", "Air-gapped friendly"),
        cons=("Manual PATH setup", "Platform-specific download"),
        best_for="Locked-down laptops and offline installs",
    ),
    InstallMethodInfo(
        method=InstallMethod.SOURCE,
        title="From source",
        one_liner="Editable install for contributors.",
        command="git clone https://github.com/caissonhq/forgebench.git && cd forgebench && pip install -e .",
        pros=("Latest main branch", "Full test suite", "Contribute patches"),
        cons=("Manual updates", "Requires dev tooling"),
        best_for="Contributors and design partners",
    ),
)


@dataclass(frozen=True)
class EnvironmentProfile:
    os_name: str
    arch: str
    python_version: str
    forgebench_path: str | None
    detected_method: InstallMethod
    has_git: bool
    has_gh: bool
    has_pipx: bool
    has_brew: bool
    has_code: bool
    in_venv: bool
    recommended_method: InstallMethod


@dataclass(frozen=True)
class VersionStatus:
    current: str
    python_ok: bool
    upgrade_hint: str | None


def detect_environment() -> EnvironmentProfile:
    forgebench_path = _resolve_forgebench_path()
    detected = _detect_install_method(forgebench_path)
    os_name = platform.system().lower()
    return EnvironmentProfile(
        os_name=os_name,
        arch=platform.machine().lower(),
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        forgebench_path=forgebench_path,
        detected_method=detected,
        has_git=shutil.which("git") is not None,
        has_gh=shutil.which("gh") is not None,
        has_pipx=shutil.which("pipx") is not None,
        has_brew=shutil.which("brew") is not None,
        has_code=shutil.which("code") is not None,
        in_venv=_in_virtualenv(),
        recommended_method=_recommend_method(os_name, detected),
    )


def check_version_status() -> VersionStatus:
    python_ok = (sys.version_info.major, sys.version_info.minor) >= MIN_PYTHON
    env = detect_environment()
    hint = None
    if env.detected_method != InstallMethod.UNKNOWN:
        lines = upgrade_instructions(env.detected_method)
        if lines:
            hint = lines[0]
    return VersionStatus(current=__version__, python_ok=python_ok, upgrade_hint=hint)


def recommend_install_method(*, profile: EnvironmentProfile | None = None) -> InstallMethodInfo:
    env = profile or detect_environment()
    return next(item for item in INSTALL_METHODS if item.method == env.recommended_method)


def upgrade_instructions(method: InstallMethod) -> list[str]:
    mapping = {
        InstallMethod.PIP: ["pip install --upgrade forgebench"],
        InstallMethod.PIPX: ["pipx upgrade forgebench"],
        InstallMethod.HOMEBREW: ["brew update && brew upgrade forgebench"],
        InstallMethod.BINARY: [
            "Download the latest release bundle from GitHub Releases",
            "Replace your forgebench binary with the new bundle bin/forgebench",
        ],
        InstallMethod.SOURCE: ["cd forgebench && git pull && pip install -e ."],
        InstallMethod.UNKNOWN: ["pipx install forgebench  # or: pip install --upgrade forgebench"],
    }
    return mapping.get(method, mapping[InstallMethod.UNKNOWN])


def format_install_guide(*, profile: EnvironmentProfile | None = None) -> str:
    env = profile or detect_environment()
    rec = recommend_install_method(profile=env)
    lines = [
        "ForgeBench Install Guide",
        f"Version: {__version__}",
        "",
        f"Platform: {env.os_name} ({env.arch}) · Python {env.python_version}",
    ]
    if env.forgebench_path:
        lines.append(f"forgebench: {env.forgebench_path}")
        lines.append(f"Detected install: {env.detected_method.value}")
    else:
        lines.append("forgebench: not found on PATH")
    lines.extend(["", "Recommended method for your environment:", f"  {rec.title}", f"  {rec.command}", ""])
    if env.detected_method == InstallMethod.UNKNOWN:
        lines.append("Quick start after install:")
        lines.append("  forgebench quickstart")
        lines.append("  forgebench doctor --checklist")
    else:
        lines.append("You appear to have ForgeBench installed. Next steps:")
        lines.append("  forgebench quickstart")
        lines.append("  forgebench doctor --checklist")
        upgrade = upgrade_instructions(env.detected_method)
        if upgrade:
            lines.extend(["", "Upgrade:", f"  {upgrade[0]}"])
    lines.extend(["", "All methods: forgebench install methods", "Docs: https://forgebench.dev/docs/installation/"])
    return "\n".join(lines)


def format_methods_table() -> str:
    lines = [
        "ForgeBench install methods",
        "",
        f"{'Method':<12} {'Best for':<32} Command",
        "-" * 72,
    ]
    for item in INSTALL_METHODS:
        lines.append(f"{item.method.value:<12} {item.best_for:<32} {item.command}")
    lines.extend(["", "IDE extensions (require CLI on PATH):", "  VS Code: ext install caissonhq.forgebench", "  JetBrains: install ForgeBench plugin from Marketplace", ""])
    for item in INSTALL_METHODS:
        lines.extend([f"## {item.title}", "", item.one_liner, "", f"```bash", f"{item.command}", "```", "", "Pros:", *[f"  + {p}" for p in item.pros], "Cons:", *[f"  - {c}" for c in item.cons], ""])
    return "\n".join(lines)


def render_shell_completion(shell: str) -> str:
    normalized = shell.strip().lower()
    commands = (
        "doctor quickstart demo status init review review-pr repair validate "
        "feedback presets share-report install team license analytics telemetry "
        "benchmark policy github-app calibrate dashboard prove-it mutation mcp"
    ).split()
    if normalized == "bash":
        opts = " ".join(commands)
        return f"""# ForgeBench bash completion — add to ~/.bashrc:
# eval "$(forgebench install completions --shell bash)"

_forgebench_completions() {{
  local cur prev opts
  cur="${{COMP_WORDS[COMP_CWORD]}}"
  opts="{opts}"
  if [[ ${{COMP_CWORD}} -eq 1 ]]; then
    COMPREPLY=( $(compgen -W "${{opts}}" -- "${{cur}}") )
    return 0
  fi
}}
complete -F _forgebench_completions forgebench
"""
    if normalized == "zsh":
        opts = " ".join(commands)
        return f"""# ForgeBench zsh completion — add to ~/.zshrc:
# eval "$(forgebench install completions --shell zsh)"

_forgebench() {{
  local -a commands
  commands=({ " ".join(commands) })
  _describe 'forgebench command' commands
}}
compdef _forgebench forgebench
"""
    if normalized == "fish":
        lines = ["# ForgeBench fish completion"]
        for cmd in commands:
            lines.append(f"complete -c forgebench -n '__fish_use_subcommand' -a '{cmd}'")
        return "\n".join(lines) + "\n"
    raise ValueError(f"unsupported shell: {shell}. Use bash, zsh, or fish.")


def post_install_message(*, first_run: bool = False) -> str:
    prefix = "Welcome to ForgeBench!" if first_run else "ForgeBench"
    return "\n".join(
        [
            prefix,
            f"Version {__version__} — adversarial pre-merge QA for coding-agent output.",
            "",
            "Next steps:",
            "  forgebench quickstart     # ~2 min solo onboarding",
            "  forgebench doctor --checklist",
            "  forgebench install        # upgrade path & method help",
            "",
            "Docs: https://forgebench.dev/docs/installation/",
        ]
    )


def _resolve_forgebench_path() -> str | None:
    env_path = os.environ.get("FORGEBENCH_BIN", "").strip()
    if env_path and Path(env_path).exists():
        return str(Path(env_path).resolve())
    which = shutil.which("forgebench")
    if which:
        return str(Path(which).resolve())
    if sys.argv and Path(sys.argv[0]).name == "forgebench":
        candidate = Path(sys.argv[0]).resolve()
        if candidate.exists():
            return str(candidate)
    return None


def _detect_install_method(path: str | None) -> InstallMethod:
    if not path:
        return InstallMethod.UNKNOWN
    marker = os.environ.get("FORGEBENCH_INSTALL", "").strip().lower()
    if marker == "bundle":
        return InstallMethod.BINARY
    if marker == "homebrew":
        return InstallMethod.HOMEBREW
    lower = path.lower()
    if "/cellar/" in lower or "/homebrew/" in lower:
        return InstallMethod.HOMEBREW
    if "pipx" in lower:
        return InstallMethod.PIPX
    if "/forgebench-bundle/" in lower or "/opt/forgebench/" in lower:
        return InstallMethod.BINARY
    package_root = Path(__file__).resolve().parent
    try:
        import forgebench  # noqa: F401

        module_path = Path(forgebench.__file__).resolve()
        if "site-packages" not in str(module_path) and "dist-packages" not in str(module_path):
            if package_root in module_path.parents or module_path.parent == package_root:
                return InstallMethod.SOURCE
    except Exception:
        pass
    if _in_virtualenv():
        return InstallMethod.PIP
    if "site-packages" in lower or "dist-packages" in lower:
        return InstallMethod.PIP
    return InstallMethod.UNKNOWN


def _recommend_method(os_name: str, detected: InstallMethod) -> InstallMethod:
    if detected != InstallMethod.UNKNOWN:
        return detected
    if os_name == "darwin" and shutil.which("brew"):
        return InstallMethod.HOMEBREW
    if shutil.which("pipx"):
        return InstallMethod.PIPX
    if _in_virtualenv():
        return InstallMethod.PIP
    return InstallMethod.PIPX


def _in_virtualenv() -> bool:
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix) or bool(os.environ.get("VIRTUAL_ENV"))