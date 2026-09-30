from __future__ import annotations

import time
from typing import Any, Mapping
from urllib.parse import urlparse

import httpx

from .credentials import DEFAULT_BASE_URL, effective_credentials


class D1JiemaError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, response: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class D1JiemaClient:
    """GET client for the documented D1Jiema data.php API."""

    def __init__(self, *, token: str | None = None, base_url: str | None = None, timeout: float = 30.0, transport: httpx.BaseTransport | None = None):
        current = effective_credentials()
        self.token = (token or current["token"]).strip()
        self.base_url = (base_url or current["base_url"] or DEFAULT_BASE_URL).rstrip("?")
        self.timeout = timeout
        self._http = httpx.Client(timeout=timeout, transport=transport, follow_redirects=False)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "D1JiemaClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _require_token(self) -> None:
        if not self.token:
            raise D1JiemaError("Missing D1Jiema token. Run the local setup page or set D1JIEMA_API_TOKEN.")

    def request(self, code: str, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Call one documented code and normalize plain-text responses."""
        self._require_token()
        code = code.strip()
        if not code or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_" for ch in code):
            raise D1JiemaError("Invalid D1Jiema operation code")
        query: dict[str, Any] = {"code": code, "token": self.token}
        if params:
            query.update({key: value for key, value in params.items() if value is not None and value != ""})
        try:
            response = self._http.get(self.base_url, params=query)
        except httpx.HTTPError as exc:
            raise D1JiemaError(f"Network error calling D1Jiema: {exc}") from exc
        text = response.text.strip()
        if response.status_code >= 400:
            raise D1JiemaError(f"D1Jiema HTTP error ({response.status_code})", status_code=response.status_code, response=text[:2000])
        if text.startswith("ERROR:"):
            return {"ok": False, "code": code, "error": text[6:].strip(), "raw": text}
        return {"ok": True, "code": code, "data": text, "raw": text}

    def balance(self) -> dict[str, Any]:
        return self.request("leftAmount")

    def get_phone(self, *, key_word: str | None = None, phone: str | None = None, province: str | None = None, card_type: str | None = None) -> dict[str, Any]:
        return self.request("getPhone", {"keyWord": key_word, "phone": phone, "province": province, "cardType": card_type})

    def get_sms(self, *, phone: str, key_word: str) -> dict[str, Any]:
        if not phone.strip() or not key_word.strip():
            raise D1JiemaError("phone and keyWord are required for getMsg")
        return self.request("getMsg", {"phone": phone, "keyWord": key_word})

    def release(self, phone: str) -> dict[str, Any]:
        return self.request("release", {"phone": phone})

    def block(self, phone: str) -> dict[str, Any]:
        return self.request("block", {"phone": phone})

    def send_sms(self, *, phone: str, to_phone: str, content: str, proj_id: str | None = None) -> dict[str, Any]:
        return self.request("send", {"phone": phone, "toPhone": to_phone, "content": content, "projId": proj_id})

    def history(self) -> dict[str, Any]:
        return self.request("queryUsed")

    def safe_url_host(self) -> str:
        return urlparse(self.base_url).netloc
