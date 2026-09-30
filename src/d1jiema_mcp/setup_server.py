from __future__ import annotations

import argparse
import html
import os
import secrets
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .credentials import DEFAULT_BASE_URL, save_credentials


_STYLE = "body{font:16px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:560px;margin:48px auto;padding:0 20px;color:#172033;background:#f7f9fc}main{background:#fff;border:1px solid #e3e8f0;border-radius:16px;padding:28px;box-shadow:0 8px 28px #17203312}h1{font-size:24px;margin:0 0 8px}p{line-height:1.5;color:#566176}label{display:block;font-weight:600;margin:18px 0 7px}input{box-sizing:border-box;width:100%;padding:11px 12px;border:1px solid #c9d2df;border-radius:9px;font-size:16px}button{margin-top:24px;padding:11px 16px;border:0;border-radius:9px;background:#1769e0;color:#fff;font-size:16px;font-weight:600;cursor:pointer}.hint{font-size:13px;color:#6b7585;margin-top:16px}"


def _page(message: str = "", success: bool = False) -> bytes:
    alert = f'<p style="color:{"#18794e" if success else "#b42318"}">{html.escape(message)}</p>' if message else ""
    if success:
        content = f"<h1>D1Jiema is configured</h1>{alert}<p>You can close this tab. The temporary local setup service has stopped.</p>"
    else:
        content = f"""
<h1>D1Jiema setup</h1>
<p>Enter your API token locally. This page is served only from this computer and the temporary service closes after saving.</p>
{alert}
<form method="post">
  <label for="token">D1Jiema API token</label>
  <input id="token" name="token" type="password" autocomplete="current-password" required>
  <label for="base_url">API base URL</label>
  <input id="base_url" name="base_url" value="{DEFAULT_BASE_URL}" autocomplete="url">
  <button type="submit">Save securely</button>
</form>
<p class="hint">The token is written to the local D1Jiema configuration with owner-only permissions. It is never displayed back to the page.</p>
"""
    return f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>D1Jiema setup</title><style>{_STYLE}</style></head><body><main>{content}</main></body></html>".encode()


class _SetupServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, address: tuple[str, int], token: str, timeout: int):
        super().__init__(address, _SetupHandler)
        self.access_token = token
        self.timeout = timeout
        self.completed = False


class _SetupHandler(BaseHTTPRequestHandler):
    server: _SetupServer

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def _authorized(self) -> bool:
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
        return secrets.compare_digest(query.get("setup", [""])[0], self.server.access_token)

    def _send(self, body: bytes, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        self._send(_page() if self._authorized() else _page("This setup link is invalid or expired."), 200 if self._authorized() else 404)

    def do_POST(self) -> None:  # noqa: N802
        if not self._authorized():
            self._send(_page("This setup link is invalid or expired."), 404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if 0 < length <= 16 * 1024 else b""
            fields = urllib.parse.parse_qs(raw.decode("utf-8"), keep_blank_values=True)
            token = fields.get("token", [""])[0].strip()
            base_url = fields.get("base_url", [DEFAULT_BASE_URL])[0].strip() or DEFAULT_BASE_URL
            if not token:
                raise ValueError("token required")
            save_credentials(token=token, base_url=base_url)
        except (OSError, ValueError, UnicodeDecodeError):
            self._send(_page("The token could not be saved locally."), 400)
            return
        self.server.completed = True
        self._send(_page("Token saved locally.", success=True))
        threading.Thread(target=self.server.shutdown, daemon=True).start()


def _serve(timeout: int, open_browser: bool) -> int:
    setup_token = secrets.token_urlsafe(32)
    server = _SetupServer(("127.0.0.1", 0), setup_token, timeout)
    url = f"http://127.0.0.1:{server.server_port}/?setup={urllib.parse.quote(setup_token)}"
    rendezvous = f"/tmp/d1jiema-setup-{os.getpid()}.url"
    with open(rendezvous, "w", encoding="utf-8") as handle:
        handle.write(url + "\n")
    os.chmod(rendezvous, 0o600)
    if open_browser:
        try:
            webbrowser.open(url, new=2)
        except Exception:
            pass

    def stop_on_timeout() -> None:
        time.sleep(timeout)
        if not server.completed:
            server.shutdown()

    threading.Thread(target=stop_on_timeout, daemon=True).start()
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        server.server_close()
        try:
            os.unlink(rendezvous)
        except OSError:
            pass
    return 0


def launch_setup_service(*, open_browser: bool = True, timeout: int = 600) -> dict[str, Any]:
    process = subprocess.Popen(
        [sys.executable, "-m", "d1jiema_mcp.setup_server", "--serve", "--timeout", str(timeout), *(["--no-open"] if not open_browser else [])],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    rendezvous = f"/tmp/d1jiema-setup-{process.pid}.url"
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline and not os.path.exists(rendezvous):
        time.sleep(0.03)
    if not os.path.exists(rendezvous):
        return {"started": False, "error": "The local setup service did not start."}
    with open(rendezvous, encoding="utf-8") as handle:
        url = handle.read().strip()
    try:
        os.unlink(rendezvous)
    except OSError:
        pass
    return {"started": True, "pid": process.pid, "url": url, "expires_in_seconds": timeout, "message": "Complete the local form; the service exits after saving."}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()
    if args.serve:
        return _serve(max(30, min(args.timeout, 3600)), not args.no_open)
    result = launch_setup_service(open_browser=not args.no_open, timeout=args.timeout)
    if result.get("started"):
        print(result["url"])
        return 0
    print(result["error"], file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
