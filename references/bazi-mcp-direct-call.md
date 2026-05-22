# Bazi MCP 直接调用方案

## 问题场景

Bazi MCP 已在 config.yaml 中配置（stdio transport），但 MCP 工具未在会话中注册为可用工具。直接调用 `mcp_bazi_getBaziDetail` 等工具会报 `Tool 'mcp_bazi_*' does not exist`。

## 根因

MCP 工具注册是会话级别的，某些情况下服务器未成功启动或工具未同步。

## 解决方案

直接在 Bazi MCP 的 Node.js 模块目录下编写调用脚本，通过 `terminal` 执行。

### 前置：定位 MCP 模块路径

```bash
# 优先：检查环境变量
echo "$BAZI_MCP_PATH"

# 其次：搜索常见安装位置
find "$HOME" -name "index.js" -path "*bazi-mcp*" 2>/dev/null
find "$HOME/.npm" -name "index.js" -path "*bazi-mcp*" 2>/dev/null
```

将找到的路径记为 `<BAZI_MCP_DIR>`（`dist/index.js` 所在目录的上一级目录的上一级，即包含 `package.json` 的目录）。

### 脚本模板

创建 `/tmp/bazi-query.mjs`：

```js
import { getBaziDetail } from '<BAZI_MCP_DIR>/dist/index.js';

const result = await getBaziDetail({
  solarDatetime: 'YYYY-MM-DDTHH:mm:ss+08:00',  // ISO 格式公历时间
  gender: 0,  // 0=女, 1=男
  eightCharProviderSect: 2  // 1=23点日柱算明天, 2=算当天（默认）
});

console.log(JSON.stringify(result, null, 2));
```

### 简化单行调用（推荐）

无需创建临时 .mjs 文件，直接在 MCP 模块目录下用 `node -e` 单行调用：

```bash
cd <BAZI_MCP_DIR> && node -e "
import('./dist/index.js').then(m => {
  m.getBaziDetail({
    solarDatetime: '2002-05-19T06:14:00+08:00',
    gender: 0,
    eightCharProviderSect: 2
  }).then(r => console.log(JSON.stringify(r, null, 2)));
});
"
```

> 此方式免去创建 `/tmp/bazi-query.mjs` 的步骤，适合一次性排盘。

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `solarDatetime` | ISO 8601 公历时间 | `2001-12-17T12:00:00+08:00` |
| `lunarDatetime` | 农历时间（与 solarDatetime 二选一） | `2000-5-5 12:00:00` |
| `gender` | 0=女性，1=男性 | `0` |
| `eightCharProviderSect` | 早晚子时配置，默认2 | `2` |

### 返回 JSON 关键字段

参考实际返回结构：
- `性别`, `阳历`, `农历`, `八字`, `生肖`, `日主`
- `年柱`, `月柱`, `日柱`, `时柱`（各含：天干/地支/藏干/纳音/旬/空亡/星运/自坐）
- `胎元`, `胎息`, `命宫`, `身宫`
- `神煞`（按柱分组的数组）
- `大运`（含起运日期、起运年龄、10步大运详细列表）
- `刑冲合会`（按柱组织的刑冲合害关系）

### 常见 Bazi MCP 安装路径参考

按优先级：

1. `npx` 缓存：`~/.npm/_npx/<hash>/node_modules/bazi-mcp/`
2. 手动安装：`~/mcp-servers/bazi-mcp/`
3. 全局 npm：`$(npm root -g)/bazi-mcp/`
4. 环境变量：`$BAZI_MCP_PATH`

> **提示**：可将路径设为环境变量 `export BAZI_MCP_PATH=...` 以便脚本引用。

### 注意事项

- 必须先 `cd` 到 `bazi-mcp` **模块根目录**（包含 `package.json` 的目录），否则模块路径解析可能失败
- 脚本临时存放在 `/tmp/`，用完可删除
- 如果 MCP 工具已注册，优先使用原生 MCP 工具调用
