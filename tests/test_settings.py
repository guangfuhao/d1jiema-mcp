from __future__ import annotations

import json
import os

from d1jiema_mcp.credentials import save_credentials, settings_snapshot


def test_credentials_are_owner_only_and_masked(tmp_path, monkeypatch):
    path = tmp_path / "credentials.json"
    monkeypatch.setenv("D1JIEMA_CONFIG_FILE", str(path))
    save_credentials(token="secret-token")
    assert oct(path.stat().st_mode & 0o777) == "0o600"
    assert json.loads(path.read_text())["token"] == "secret-token"
    assert settings_snapshot()["token"] == "••••••••"
