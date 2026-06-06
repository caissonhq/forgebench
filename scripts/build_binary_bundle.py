#!/usr/bin/env python3
"""Build official ForgeBench binary release bundles (.tar.gz per OS/arch)."""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _platform_slug() -> str:
    system = platform.system().lower()
    mapping = {"darwin": "darwin", "linux": "linux", "windows": "windows"}
    return mapping.get(system, system)


def _arch_slug() -> str:
    machine = platform.machine().lower()
    if machine in {"x86_64", "amd64"}:
        return "x86_64"
    if machine in {"arm64", "aarch64"}:
        return "arm64"
    return machine


def build_bundle(*, version: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = f"{_platform_slug()}-{_arch_slug()}"
    bundle_name = f"forgebench-{version}-{slug}"
    stage = output_dir / bundle_name
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    venv_dir = stage / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    pip = venv_dir / ("Scripts" if platform.system() == "Windows" else "bin") / "pip"
    subprocess.run([str(pip), "install", "--upgrade", "pip"], check=True)
    wheel = next((ROOT / "dist").glob("forgebench-*.whl"), None)
    if wheel and wheel.exists():
        subprocess.run([str(pip), "install", str(wheel)], check=True)
    else:
        subprocess.run([str(pip), "install", str(ROOT)], check=True)

    bin_dir = stage / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    launcher = bin_dir / ("forgebench.cmd" if platform.system() == "Windows" else "forgebench")
    if platform.system() == "Windows":
        launcher.write_text(
            f'@echo off\r\nset FORGEBENCH_INSTALL=bundle\r\n"{venv_dir}\\Scripts\\python.exe" -m forgebench.cli %*\r\n',
            encoding="utf-8",
        )
    else:
        launcher.write_text(
            f"""#!/usr/bin/env bash
set -euo pipefail
export FORGEBENCH_INSTALL=bundle
ROOT="$(cd "$(dirname "${{BASH_SOURCE[0]}}")/.." && pwd)"
exec "${{ROOT}}/venv/bin/python" -m forgebench.cli "$@"
""",
            encoding="utf-8",
        )
        launcher.chmod(0o755)

    readme = stage / "README.txt"
    readme.write_text(
        f"""ForgeBench {version} binary bundle ({slug})

Install:
  export PATH="{stage / 'bin'}:$PATH"
  forgebench doctor
  forgebench quickstart

Upgrade: download a newer release bundle from GitHub Releases.
""",
        encoding="utf-8",
    )

    archive = output_dir / f"{bundle_name}.tar.gz"
    if archive.exists():
        archive.unlink()
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(stage, arcname=bundle_name)
    return archive


def main() -> int:
    parser = argparse.ArgumentParser(description="Build ForgeBench binary release bundle")
    parser.add_argument("--version", default=None, help="Release version (defaults to package version)")
    parser.add_argument("--out", default="dist", help="Output directory")
    args = parser.parse_args()
    version = args.version
    if not version:
        sys.path.insert(0, str(ROOT))
        from forgebench import __version__

        version = __version__
    archive = build_bundle(version=version, output_dir=Path(args.out))
    print(f"Built {archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())