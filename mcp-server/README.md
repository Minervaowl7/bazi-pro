# bazi-pro MCP Server

将八字排盘计算暴露为 MCP 工具，可在 Claude Desktop / Cursor / Claude Code 中直接调用。

## 工具列表

| 工具 | 说明 |
|------|------|
| `bazi_paipan` | 八字排盘 — 输入阳历时间+性别，返回四柱/日主/生肖/大运 |
| `bazi_analyze` | 全面分析 — 旺衰/格局/用神/十神/五行/刑冲合害 |
| `bazi_daily_fortune` | 每日运势 — 六维度确定性运势计算 |

## 配置 Claude Desktop

在 `claude_desktop_config.json` 中添加:

```json
{
  "mcpServers": {
    "bazi-pro": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/bazi-pro"
    }
  }
}
```

## 运行

```bash
cd /path/to/bazi-pro
python -m mcp_server.server
```
