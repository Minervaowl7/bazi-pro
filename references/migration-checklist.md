# 跨机器迁移检查清单

当将 bazi-pro skill 从一台机器复制到另一台机器时，按以下清单检查。

## 1. 环境依赖

```bash
# 检查 Python 版本 (需要 3.10+)
python3 --version

# 安装 jieba 分词库
python3 -m pip install jieba
```

## 2. 路径配置

### 方式 A：设置 SKILL_DIR 环境变量（推荐）

```bash
export SKILL_DIR=/path/to/bazi-pro
```

### 方式 B：使用相对路径

如果从 skill 根目录执行，脚本会自动使用 `./scripts/` 和 `./references/` 相对路径。

## 3. 语料库验证

```bash
# 验证语料库可读取（应显示约 2964 条记录）
python3 ${SKILL_DIR:-.}/scripts/retrieve_classical.py --stats --corpus ${SKILL_DIR:-.}/references/classical_corpus.md
```

## 4. 检索功能冒烟测试

```bash
python3 ${SKILL_DIR:-.}/scripts/retrieve_classical.py "从强 假从 顺势 印比成势" -k 5 --json
python3 ${SKILL_DIR:-.}/scripts/retrieve_classical.py "伤官见官 财星通关" -k 5 --json
python3 ${SKILL_DIR:-.}/scripts/retrieve_classical.py "杀印相生 七杀 印绶" -k 5 --json
```

每条命令应返回 JSON 数组，包含 `score`、`id`、`topic`、`source`、`content` 字段。

## 5. 参考文件完整性

确认以下文件存在且可读：

- `references/classical_corpus.md` — 古籍语料库
- `references/tiaohou.md` — 调候用神速查表
- `references/ETHICS.md` — 伦理准则
- `references/bazi-mcp-direct-call.md` — Bazi MCP 直接调用指南

## 6. Skill 加载验证

在 Agent 中加载 SKILL.md 后，确认：
- [ ] Skill 元数据（name、description）正确显示
- [ ] 环境变量 `SKILL_DIR` 在 Skill 上下文中已设置
- [ ] 古籍检索脚本可从 Skill 上下文中正常调用

## 7. 报告生成功能验证

```bash
# 验证报告生成脚本可用
python3 ${SKILL_DIR:-.}/scripts/generate_report.py --help

# 生成测试报告（管道输入）
echo "# 测试报告

## 基本信息

| 项目 | 内容 |
|------|------|
| 性别 | 男 |
| 阳历 | 1990年1月1日 |

测试内容。**粗体** *斜体*。

\`\`\`
木 ████████░░ 38%
\`\`\`
" | python3 ${SKILL_DIR:-.}/scripts/generate_report.py --output /tmp/test_report.html --title "测试报告"
```

验证:
- [ ] HTML 报告能在浏览器中正常打开
- [ ] 封面、标题、目录正常显示
- [ ] 表格样式、ASCII 图正常渲染
- [ ] 可通过浏览器"打印 → 另存为 PDF"生成 PDF

### PDF 依赖（可选）

```bash
# 高质量 PDF（Windows 需额外安装 GTK+，参考 weasyprint 文档）
pip install weasyprint

# 备选（需额外安装 wkhtmltopdf）
pip install pdfkit
```

## 常见问题

| 问题 | 解决方案 |
|------|---------|
| `jieba` 导入失败 | `pip install jieba` |
| 语料库文件不存在 | 检查 `--corpus` 参数路径，或设置 `SKILL_DIR` 环境变量 |
| Python 版本过低 | 升级到 Python 3.10+ |
| 检索结果为空 | 检查查询字符串是否包含有效的八字术语，或检查语料库文件编码（需 UTF-8） |
