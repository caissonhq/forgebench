from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from forgebench.adoption import record_milestone


class PresetError(ValueError):
    pass


@dataclass(frozen=True)
class PresetInfo:
    name: str
    title: str
    description: str
    stack: str
    path: Path


def presets_root() -> Path:
    bundled = Path(__file__).resolve().parent / "bundled_presets"
    if bundled.is_dir():
        return bundled
    return Path(__file__).resolve().parents[1] / "examples" / "presets"


def list_presets() -> list[PresetInfo]:
    root = presets_root()
    if not root.is_dir():
        return []
    items: list[PresetInfo] = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        manifest = entry / "preset.json"
        if not manifest.exists():
            continue
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        items.append(
            PresetInfo(
                name=entry.name,
                title=str(payload.get("title") or entry.name),
                description=str(payload.get("description") or ""),
                stack=str(payload.get("stack") or "generic"),
                path=entry,
            )
        )
    return items


def install_preset(name: str, *, repo_path: str | Path = ".", force: bool = False) -> Path:
    normalized = name.strip().lower()
    preset = next((item for item in list_presets() if item.name == normalized), None)
    if preset is None:
        available = ", ".join(item.name for item in list_presets()) or "(none bundled)"
        raise PresetError(f"unknown preset: {name}. Available: {available}")

    repo = Path(repo_path).resolve()
    if not repo.is_dir():
        raise PresetError(f"repo path does not exist: {repo}")

    target = repo / "forgebench.yml"
    source = preset.path / "forgebench.yml"
    if not source.exists():
        raise PresetError(f"preset missing forgebench.yml: {source}")
    if target.exists() and not force:
        raise PresetError(f"refusing to overwrite {target}. Re-run with --force.")

    shutil.copy2(source, target)
    extras = preset.path / "extras"
    if extras.is_dir():
        for item in extras.rglob("*"):
            if item.is_file():
                rel = item.relative_to(extras)
                dest = repo / rel
                if dest.exists() and not force:
                    continue
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)

    record_milestone("first_preset_installed")
    return target


def export_preset_bundle(guardrails_path: str | Path, *, output_dir: str | Path) -> dict[str, Any]:
    source = Path(guardrails_path)
    if not source.exists():
        raise PresetError(f"guardrails file not found: {source}")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    dest = out / "forgebench.yml"
    shutil.copy2(source, dest)
    manifest = {
        "export_version": 1,
        "title": source.parent.name,
        "description": "Exported ForgeBench policy bundle",
        "files": ["forgebench.yml"],
    }
    (out / "preset.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def format_preset_list(presets: list[PresetInfo]) -> str:
    if not presets:
        return "No presets found. See docs/presets-gallery.md"
    lines = ["ForgeBench guardrail presets", ""]
    for item in presets:
        lines.append(f"  {item.name:<20} {item.title} ({item.stack})")
        if item.description:
            lines.append(f"    {item.description}")
    lines.append("")
    lines.append("Install: forgebench presets install <name>")
    return "\n".join(lines)