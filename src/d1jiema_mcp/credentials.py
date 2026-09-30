from __future__ import annotations

"""Owner-only local storage for the D1Jiema API token."""

import json
import os
from pathlib import Path
from typing import Any

MASKED_TOKEN = "••••••••"
DEFAULT_BASE_URL = "https://api.d1jiema.com/zc/data.php"


def _config_path() -> Path:
    configured = os.getenv("D1JIEMA_CONFIG_FILE", "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".config" / "d1jiema-mcp" / "credentials.json"


def load_stored_credentials() -> dict[str, str]:
    try:
        raw: Any = json.loads(_config_path().read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, ValueError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {field: value.strip() for field in ("token", "base_url") if isinstance(value := raw.get(field), str) and value.strip()}


def save_credentials(*, token: str, base_url: str = DEFAULT_BASE_URL) -> dict[str, str]:
    token = token.strip()
    if not token:
        raise ValueError("A D1Jiema API token is required")
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"token": token, "base_url": base_url.strip() or DEFAULT_BASE_URL}, indent=2) + "\n", encoding="utf-8")
    path.chmod(0o600)
    return {"base_url": base_url.strip() or DEFAULT_BASE_URL}


def effective_credentials() -> dict[str, str]:
    stored = load_stored_credentials()
    return {
        "token": os.getenv("D1JIEMA_API_TOKEN", "").strip() or stored.get("token", ""),
        "base_url": os.getenv("D1JIEMA_BASE_URL", "").strip() or stored.get("base_url", DEFAULT_BASE_URL),
    }


def settings_snapshot() -> dict[str, Any]:
    current = effective_credentials()
    return {
        "token": MASKED_TOKEN if current["token"] else "",
        "base_url": current["base_url"] or DEFAULT_BASE_URL,
        "token_configured": bool(current["token"]),
    }
