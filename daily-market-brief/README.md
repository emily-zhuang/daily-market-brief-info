# 每日美国、中国与加密货币市场简报

GitHub Actions 每天按北京时间 08:30 运行（`00:30 UTC`），收集前 24 小时的美国/中国经济与股市新闻，以及加密货币新闻和 CoinMarketCap 行情，生成 DOCX 并发送到 `975471498@qq.com`。

## GitHub Secrets

在仓库 `Settings → Secrets and variables → Actions` 添加：

- `GMAIL_CLIENT_ID`
- `GMAIL_CLIENT_SECRET`
- `GMAIL_REFRESH_TOKEN`
- `COINMARKETCAP_API_KEY`

Gmail OAuth refresh token 只放在 GitHub Secrets，不提交到仓库。首次配置后可用 `workflow_dispatch` 手动测试。

## 来源口径

新闻使用 Reuters、CNBC、Yahoo Finance、SCMP、China Daily、CoinDesk、Cointelegraph 和 Google News RSS 等主流媒体/公开摘要；不要求逐条交叉验证，报告保留来源链接并区分摘要级信息。加密行情优先使用 CoinMarketCap API。

## 运行边界

本项目只生成研究简报和发送邮件，不执行交易、不保存 Binance API 密钥。`grill-me` 与制作阶段参考的 GitHub 金融 skill 只用于首次设计和验收，工作流每日运行不加载或检查它们。

