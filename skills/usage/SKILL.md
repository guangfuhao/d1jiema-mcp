---
name: d1jiema-usage
description: Use the D1Jiema SMS phone API safely through the installed MCP plugin.
---

# D1Jiema usage

Use the installed `d1jiema-mcp` server after `d1jiema-setup` has configured the token.

Safe read flow:

1. Call `d1jiema_balance` to verify the account.
2. Call `d1jiema_get_phone` with a keyword when acquiring a number.
3. Call `d1jiema_get_sms` with the exact phone and keyword.
4. Release with `confirm=true` only when the user explicitly requests it.

`d1jiema_block` and `d1jiema_send_sms` change account state and require explicit confirmation. `d1jiema_history` is rate-limited by the upstream API to one call per minute and requires `confirm_rate_limit=true`. Never print or request the API token in ordinary chat. Use `d1jiema_request` only for documented codes and preserve the same confirmation rules.
