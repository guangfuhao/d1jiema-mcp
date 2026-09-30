# d1jiema-mcp

`d1jiema-mcp` is a Codex/MCP plugin for the D1Jiema `data.php` API. It supports balance reads, phone acquisition, SMS retrieval, release, blocking, sending, and history.

## One-sentence install

> Install and run `guangfuhao/d1jiema-mcp` from GitHub; on first use open its local D1Jiema setup page so I can enter the API token, then verify the connection with a balance read.

## First-run configuration

Official links:

- [D1Jiema official website](https://www.d1jiema.com/appweb/main.html)
- [API Token creation page](https://www.d1jiema.com/apiCenter.html#)
- API base URL: `https://api.d1jiema.com/zc/data.php`

To obtain an API token, open the [API Token creation page](https://www.d1jiema.com/apiCenter.html#), sign in to D1Jiema, go to **Personal Center → Create API Token**, and copy the generated token. The plugin uses this token for API access and does not need to repeatedly log in through the plugin.

Hosts with native settings can render the token field there. When the current Codex local-plugin page only shows skills, `d1jiema-setup` calls `d1jiema_setup_local`, which starts a temporary form bound to `127.0.0.1`; the service exits after saving and stores the token with `0600` permissions.

Headless environments can use `D1JIEMA_API_TOKEN` and optionally `D1JIEMA_BASE_URL`. The token is never written to source, README files, GitHub, logs, or ordinary chat messages.

## Capabilities

- `d1jiema_balance`: read account balance;
- `d1jiema_login`: open the local token setup flow (tokens are created in the D1Jiema web personal center);
- `d1jiema_get_phone`: acquire a number with optional keyword, exact number, province, and card type;
- `d1jiema_get_sms`: retrieve a code by phone and keyword;
- `d1jiema_release`: release a number, requiring `confirm=true`;
- `d1jiema_block`: block a number, requiring `confirm=true`;
- `d1jiema_send_sms`: send an SMS, requiring `confirm=true`;
- `d1jiema_history`: read recent history after confirming the one-call-per-minute limit;
- `d1jiema_request`: call other documented GET codes.

Requests use `https://api.d1jiema.com/zc/data.php`, with URL encoding handled by the client. Upstream `ERROR:` responses become structured errors, and the Token is never returned to the caller.

## Safety boundaries

Sending, blocking, and releasing change account state or cause an external communication. The plugin refuses them by default and only sends them with explicit confirmation. `queryUsed` is rate-limited to one call per minute by the upstream documentation.

Chinese documentation: [README.md](README.md)
