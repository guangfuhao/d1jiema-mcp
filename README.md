# d1jiema-mcp

`d1jiema-mcp` 是 D1Jiema `data.php` API 的 Codex/MCP 插件，支持余额、取号、取码、释放、拉黑、发送短信和历史记录。

## 一句话安装

> 从 GitHub 安装并运行 `guangfuhao/d1jiema-mcp` 插件；首次使用打开本地 D1Jiema 配置页让我输入 API Token，然后查询余额确认连接。

## 首次配置

插件使用 D1Jiema 网页个人中心创建的 API Token。宿主支持原生设置页时，可直接填写；当前 Codex 本地插件页如果只显示技能，`d1jiema-setup` 会调用 `d1jiema_setup_local`，启动只监听 `127.0.0.1` 的临时配置页。保存后服务自动关闭，Token 写入当前用户的本地配置并设置为 `0600`。

无图形界面的环境使用 `D1JIEMA_API_TOKEN`，可选 `D1JIEMA_BASE_URL`。Token 不写入代码、README、GitHub、日志或普通聊天消息。

## 能力

- `d1jiema_balance`：查询余额；
- `d1jiema_login`：打开本地 Token 配置流程（Token 在 D1Jiema 网页个人中心创建）；
- `d1jiema_get_phone`：按关键词、指定号码、省份、实卡/虚卡/全部取号；
- `d1jiema_get_sms`：按手机号和关键词取码；
- `d1jiema_release`：释放号码，需要 `confirm=true`；
- `d1jiema_block`：拉黑号码，需要 `confirm=true`；
- `d1jiema_send_sms`：发送短信，需要 `confirm=true`；
- `d1jiema_history`：查询最近 24 小时历史，需要确认一分钟频率限制；
- `d1jiema_request`：调用文档中的其他 GET code。

所有接口都使用 `https://api.d1jiema.com/zc/data.php`，参数会自动进行 URL 编码。上游返回 `ERROR:` 时，工具返回结构化错误，不会把 Token 返回给调用方。

## 安全边界

发送短信、拉黑、释放会改变账户或产生实际通信行为，插件默认拒绝，只有明确传入确认参数才会发出请求。`queryUsed` 按文档限制每分钟最多调用一次。

English documentation: [README.en.md](README.en.md)
