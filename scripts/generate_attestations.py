#!/usr/bin/env python3
"""Generate SHA256 attestations and provenance manifest for release artifacts."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    dist = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    version = sys.argv[2] if len(sys.argv) > 2 else "0.9.0"
    artifacts: list[dict[str, str]] = []
    for path in sorted(dist.glob("*")):
        if not path.is_file():
            continue
        artifacts.append(
            {
                "name": path.name,
                "sha256": sha256_file(path),
                "size_bytes": str(path.stat().st_size),
            }
        )
    manifest = {
        "attestation_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "package": "forgebench",
        "version": version,
        "artifacts": artifacts,
        "provenance": {
            "build_system": "github-actions",
            "sbom": "sbom.json" if (dist / "sbom.json").exists() else None,
            "sigstore_ready": True,
        },
    }
    out = dist / "attestations.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {out} ({len(artifacts)} artifacts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())