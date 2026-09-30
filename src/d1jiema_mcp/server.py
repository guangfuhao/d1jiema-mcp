from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field

from .client import D1JiemaClient, D1JiemaError
from .credentials import DEFAULT_BASE_URL, effective_credentials, save_credentials, settings_snapshot

mcp = FastMCP("D1Jiema SMS API")


class SettingsReadResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    schema_: dict[str, Any] = Field(alias="schema")
    values: dict[str, Any]
    layout: list[dict[str, Any]] = Field(default_factory=list)


class SettingsUpdateResult(BaseModel):
    values: dict[str, Any]


def _advertise_native_settings() -> None:
    original = mcp._mcp_server.create_initialization_options

    def create_initialization_options(notification_options: Any = None, experimental_capabilities: dict[str, dict[str, Any]] | None = None):
        capabilities = dict(experimental_capabilities or {})
        settings = dict(capabilities.get("openai/settings", {}))
        settings.setdefault("readTool", "d1jiema_settings_read")
        settings.setdefault("updateTool", "d1jiema_settings_update")
        capabilities["openai/settings"] = settings
        options = original(notification_options, capabilities)
        try:
            options.capabilities.extensions = {"openai/settings": settings}
        except (AttributeError, TypeError):
            pass
        return options

    mcp._mcp_server.create_initialization_options = create_initialization_options


_advertise_native_settings()


def _result(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _error(exc: Exception) -> str:
    if isinstance(exc, D1JiemaError):
        return _result({"ok": False, "error": str(exc), "status_code": exc.status_code, "response": exc.response})
    return _result({"ok": False, "error": str(exc)})


def _client() -> D1JiemaClient:
    return D1JiemaClient()


@mcp.tool(name="d1jiema_settings_read", title="D1Jiema settings", description="Read D1Jiema settings. The API token is always masked.", annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False), structured_output=True)
def d1jiema_settings_read() -> SettingsReadResult:
    snapshot = settings_snapshot()
    return SettingsReadResult(
        schema_={
            "type": "object",
            "properties": {
                "token": {"type": "string", "title": "D1Jiema API token", "description": "API token created in the D1Jiema web personal center.", "minLength": 1},
                "base_url": {"type": "string", "title": "API base URL", "description": "The documented data.php endpoint.", "minLength": 1},
            },
            "required": ["token"],
        },
        values={"token": snapshot["token"], "base_url": snapshot["base_url"]},
        layout=[{"kind": "group", "title": "D1Jiema account", "items": [{"kind": "property", "property": "token"}, {"kind": "property", "property": "base_url"}]}],
    )


@mcp.tool(name="d1jiema_settings_update", title="Save D1Jiema settings", description="Save the D1Jiema token from the settings page.", annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False), structured_output=True)
def d1jiema_settings_update(set: dict[str, str]) -> SettingsUpdateResult:
    allowed = {"token", "base_url"}
    unknown = set.keys() - allowed
    if unknown:
        raise ValueError(f"Unsupported D1Jiema settings: {', '.join(sorted(unknown))}")
    current = effective_credentials()
    token = set.get("token") or current["token"]
    base_url = set.get("base_url") or current["base_url"] or DEFAULT_BASE_URL
    save_credentials(token=token, base_url=base_url)
    snapshot = settings_snapshot()
    return SettingsUpdateResult(values={"token": snapshot["token"], "base_url": snapshot["base_url"]})


@mcp.tool(name="d1jiema_setup_local", title="Open D1Jiema local setup", description="Launch a one-shot localhost form for entering the D1Jiema API token. The form closes after saving.", annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False))
def d1jiema_setup_local(open_browser: bool = True) -> str:
    from .setup_server import launch_setup_service

    try:
        return _result(launch_setup_service(open_browser=open_browser))
    except Exception as exc:
        return _error(exc)


def _call(method_name: str, **kwargs: Any) -> str:
    client = _client()
    try:
        return _result(getattr(client, method_name)(**kwargs))
    except Exception as exc:
        return _error(exc)
    finally:
        client.close()


@mcp.tool(name="d1jiema_balance", description="Read the D1Jiema account balance using leftAmount.")
def d1jiema_balance() -> str:
    return _call("balance")


@mcp.tool(name="d1jiema_get_phone", description="Get a D1Jiema phone number. Optional keyword, exact phone, province, and card type filters are passed through.")
def d1jiema_get_phone(key_word: str | None = None, phone: str | None = None, province: str | None = None, card_type: str | None = None) -> str:
    return _call("get_phone", key_word=key_word, phone=phone, province=province, card_type=card_type)


@mcp.tool(name="d1jiema_get_sms", description="Fetch the SMS containing the required keyword for a phone number.")
def d1jiema_get_sms(phone: str, key_word: str) -> str:
    return _call("get_sms", phone=phone, key_word=key_word)


@mcp.tool(name="d1jiema_release", description="Release a D1Jiema phone. This changes account state; set confirm=true explicitly.")
def d1jiema_release(phone: str, confirm: bool = False) -> str:
    if not confirm:
        return _error(D1JiemaError("Release not sent: set confirm=true after reviewing the phone number"))
    return _call("release", phone=phone)


@mcp.tool(name="d1jiema_block", description="Block a D1Jiema phone. This is irreversible account state; set confirm=true explicitly.")
def d1jiema_block(phone: str, confirm: bool = False) -> str:
    if not confirm:
        return _error(D1JiemaError("Block not sent: set confirm=true after reviewing the phone number"))
    return _call("block", phone=phone)


@mcp.tool(name="d1jiema_send_sms", description="Send an SMS through D1Jiema. Use only for an explicitly authorized recipient and content; set confirm=true.")
def d1jiema_send_sms(phone: str, to_phone: str, content: str, proj_id: str | None = None, confirm: bool = False) -> str:
    if not confirm:
        return _error(D1JiemaError("SMS not sent: set confirm=true after reviewing the recipient and content"))
    return _call("send_sms", phone=phone, to_phone=to_phone, content=content, proj_id=proj_id)


@mcp.tool(name="d1jiema_history", description="Read the last 24 hours of D1Jiema history. The API allows at most one call per minute; set confirm_rate_limit=true.")
def d1jiema_history(confirm_rate_limit: bool = False) -> str:
    if not confirm_rate_limit:
        return _error(D1JiemaError("History not queried: D1Jiema documents a one-call-per-minute limit; set confirm_rate_limit=true"))
    return _call("history")


@mcp.tool(name="d1jiema_request", description="Call any documented D1Jiema GET operation by code. Write-like codes require confirm=true.")
def d1jiema_request(code: str, params: dict[str, Any] | None = None, confirm: bool = False) -> str:
    read_codes = {"leftAmount", "getPhone", "getMsg", "queryUsed"}
    if code not in read_codes and not confirm:
        return _error(D1JiemaError("This operation can change account state; set confirm=true after reviewing the parameters"))
    return _call("request", code=code, params=params)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
