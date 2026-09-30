from __future__ import annotations

import json

import httpx

from d1jiema_mcp.client import D1JiemaClient


def test_request_encodes_params_and_normalizes_success(monkeypatch):
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, text="验证码1234", request=request)

    monkeypatch.setenv("D1JIEMA_API_TOKEN", "token-for-test")
    client = D1JiemaClient(transport=httpx.MockTransport(handler))
    try:
        result = client.get_sms(phone="16500000000", key_word="毛竹")
    finally:
        client.close()
    assert result == {"ok": True, "code": "getMsg", "data": "验证码1234", "raw": "验证码1234"}
    query = dict(calls[0].url.params)
    assert query["token"] == "token-for-test"
    assert query["phone"] == "16500000000"
    assert query["keyWord"] == "毛竹"


def test_error_prefix_is_structured(monkeypatch):
    monkeypatch.setenv("D1JIEMA_API_TOKEN", "token-for-test")
    client = D1JiemaClient(transport=httpx.MockTransport(lambda request: httpx.Response(200, text="ERROR:余额不足", request=request)))
    try:
        result = client.balance()
    finally:
        client.close()
    assert result["ok"] is False
    assert result["error"] == "余额不足"
    assert "token-for-test" not in json.dumps(result)
