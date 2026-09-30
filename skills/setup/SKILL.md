---
name: d1jiema-setup
description: Configure the D1Jiema API token after the plugin is installed.
---

# D1Jiema setup

Run this before any D1Jiema account or phone operation.

1. If the host exposes a native settings page, enter the D1Jiema API token there.
2. Otherwise call `d1jiema_setup_local` with `open_browser=true`. It starts a one-shot localhost form; the user enters the token in that page, and the service exits after saving.
3. Keep the documented API base URL unless the user explicitly provides another endpoint.
4. Confirm setup with a read-only balance request. Never place the token in chat, tool arguments, logs, repositories, or commits.

If the host cannot launch the local form, use `D1JIEMA_API_TOKEN` in its secure environment. Do not ask the user to paste the token into a normal conversation message.
