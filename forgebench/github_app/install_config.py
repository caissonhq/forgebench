from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class InstallationAutoConfigResult:
    installation_id: int
    account_login: str
    config_path: Path
    enforcement_path: Path
    readme_path: Path


def handle_installation_event(
    payload: dict[str, Any],
    *,
    output_dir: str | Path = "forgebench-output/github-app-installs",
) -> InstallationAutoConfigResult | None:
    action = str(payload.get("action") or "").strip().lower()
    if action not in {"created", "added"}:
        return None
    installation = payload.get("installation")
    if not isinstance(installation, dict):
        return None
    installation_id = _optional_int(installation.get("id"))
    if installation_id is None:
        return None
    account = installation.get("account") if isinstance(installation.get("account"), dict) else {}
    account_login = str(account.get("login") or "unknown-org")

    out = Path(output_dir)
    install_dir = out / f"installation-{installation_id}"
    install_dir.mkdir(parents=True, exist_ok=True)

    config_path = install_dir / "installation.json"
    enforcement_path = install_dir / "org-enforcement.json"
    readme_path = install_dir / "README.md"

    config_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "installation_id": installation_id,
                "account_login": account_login,
                "app_id": installation.get("app_id"),
                "target_type": installation.get("target_type"),
                "repository_selection": installation.get("repository_selection"),
                "auto_configured": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    enforcement = {
        "schema_version": "1.0.0",
        "org_id": account_login,
        "block_on_posture": "BLOCK",
        "require_review_on_posture": "REVIEW",
        "allow_low_concern": True,
        "audit_required": True,
        "notes": (
            "Auto-generated on GitHub App installation. "
            "Point forgebench github-app serve --config at this file."
        ),
    }
    enforcement_path.write_text(json.dumps(enforcement, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    readme_path.write_text(
        f"""# ForgeBench GitHub App — installation {installation_id}

Account: **{account_login}**

Auto-configuration created:

- `{config_path.name}` — installation metadata
- `{enforcement_path.name}` — org enforcement defaults

## Next steps

```bash
export FORGEBENCH_GITHUB_WEBHOOK_SECRET="<16+ chars>"
forgebench github-app serve --config {enforcement_path} --host 127.0.0.1 --port 8792
forgebench doctor --repo .
```

Ensure repos have `.github/forgebench.yml` on the default branch (run `forgebench team init` if needed).
""",
        encoding="utf-8",
    )

    return InstallationAutoConfigResult(
        installation_id=installation_id,
        account_login=account_login,
        config_path=config_path,
        enforcement_path=enforcement_path,
        readme_path=readme_path,
    )


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None