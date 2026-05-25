# 任务：bazi-pro 项目自动修复与功能推进

## 项目身份

bazi-pro v5.0 — 专业八字命理分析引擎。**算析分离**：`bazi_pro/core/` 包含确定性命理计算（十神、藏干、五行力量、旺衰、格局、喜用神），LLM 只负责解读。核心组件：BM25 + jieba 古籍检索（2964条）、SKILL.md 10步执行流、evidence/trace/view_model 证据管道、FastAPI 服务、插件系统、TUI。

## 架构速览

```
Bazi MCP JSON
    │
    ▼
┌─────────────────────────────────────────────┐
│  Deterministic Core (bazi_pro/core/)         │
│  constants → stems/branches → hidden_stems   │
│  → ten_gods → relations → elements           │
│  → strength → patterns → yongshen            │
│  full_analysis() 主入口                       │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  Retrieval Layer                             │
│  retrieve_classical.py (BM25 + jieba)        │
│  hybrid_search.py (FAISS + authority)        │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  Interpretation (SKILL.md 10-step)           │
│  evidence.py → trace.py → view_model.py      │
└─────────────────────────────────────────────┘
    │
    ▼
  UI renderers (pillar_chart, timeline_river,
    reasoning_graph, verdict_seal, report, replay)
```

**单一真实来源**: `bazi_pro/__init__.py` → `__version__ = "5.0.0"`
**核心合约**: `SKILL.md`（不可修改流程）
**设计原则**: `CLAUDE.md` 第87-94行（算析分离、不编造古籍引用、推导/推算区分、线性执行、伦理优先、ViewModel 统一合约）
**新核心**: `bazi_pro/core/` 包含 11 个模块的确定性计算引擎。不要在这个目录中新增 LLM 解读逻辑——它只做确定性的命理计算。

## 你的工作流程（每轮迭代）

### Step 1: 了解当前状态
```bash
git log --oneline -5
git diff --stat
git status --short
```

### Step 2: 选择下一个任务
从下方任务列表中找到第一个 `[ ]` 未完成的任务。**只选一个**。

### Step 3: 读取相关文件
用 Read 工具读取任务涉及的文件，理解上下文。

### Step 4: 实现修复
- 遵循 `CLAUDE.md` 设计原则
- 最小改动——只改必须改的
- 版本字符串统一从 `bazi_pro.__version__` 或 `bazi_pro/__init__.py` 中的 `__version__` 读取
- 不做不相关的重构

### Step 5: 验证
```bash
python tests/run_golden.py      # 确认 golden cases 不退化
```

### Step 6: 提交
```bash
git add <你改的文件>
git commit -m "<描述性消息>"
```

### Step 7: 标记完成
将对应任务从 `[ ]` 改为 `[x]`。
在任务后面追加 `<!-- done: <commit-hash> -->`

---

## 任务列表

### 第一批：机械修复（单文件，低风险）

- [ ] **T1**: `plugins/__init__.py` — 创建空文件。`plugins/` 缺少 `__init__.py`，无法被作为 Python 包导入。创建一个只含 docstring 的文件：`"""bazi-pro plugin system v5.0"""`

- [ ] **T2**: `plugins/loader.py:68` — 排除 `examples/` 目录不被扫描为正式插件。代码注释说"跳过 examples/ 和 __pycache__"，但实际只跳过了 `_` 和 `.` 开头的目录。改为 `if entry.startswith('_') or entry.startswith('.') or entry == 'examples': continue`

- [ ] **T3**: `MANIFEST.in:6` — 删除 `recursive-include dist *.html`（dist/ 是构建产物，不在源码中，且被 .gitignore）。不添加新的 include 规则，除非发现具体遗漏。

- [ ] **T4**: `scripts/hybrid_search.py` — 改为真正的薄封装，委托给 `main()`。当前只导入 `_HYBRID_READY` 等布尔值并打印状态，不执行搜索。改为 `from bazi_pro.hybrid_search import main; main()`。

- [ ] **T5**: `plugins/examples/english/main.py:28` — `<div>` 注入到 `<head>` 内部（无效 HTML）。改为插入到 `</head>` 之后。将 `html[:head_end] + note + html[head_end:]` 改为 `html[:head_end + 7] + note + html[head_end + 7:]`（`</head>` 长度为 7）。

- [ ] **T6**: `CODE_WIKI.md:3,28,821` — 版本号 `v4.4.1` 更新为 `v5.0.0`。另外扫描文件中所有 `v4.x` 引用，确保更新到 `v5.0.0`。

### 第二批：插件防御性加固

- [ ] **T7**: `plugins/examples/fengshui/main.py` — 对 `vm.verdict.yongshen` 做防御性检查。在访问 `vm.verdict.yongshen` 前加 `hasattr(vm, 'verdict') and vm.verdict and hasattr(vm.verdict, 'yongshen')` 检查。同时验证 `yongshen` 是可迭代对象再切片。

- [ ] **T8**: `plugins/examples/tarot/main.py` — 修复类型假设。`for shen, card in TEN_GOD_TO_TAROT.items(): if shen in rule:` 这行假设 `rule` 是字符串。如果 `basis['rules']` 列表包含非字符串元素会崩溃。加 `isinstance(rule, str)` 检查。

- [ ] **T9**: `plugins/loader.py:46,90,92` — 异常被静默吞噬（`except Exception: pass`）。改为 `import logging; logging.warning(f"Plugin load failed: {e}")` 至少输出 warning 日志。

### 第三批：文档和兼容性

- [ ] **T10**: 更新 `ROADMAP.md` — 当前所有 4 个阶段仍标记为 "未开始"，但 Phase A-D 的功能文件实际已存在（`pillar_chart.py`、`timeline_river.py`、`compare_engine.py`、`liunian_sandbox.py`、`archive.py`、`calibration.py`、`plugin_api.py` 等）。核实文件存在性，将已完成阶段标记为 "✅ 已完成"，未完成的保持原样或标记实际状态。

- [ ] **T11**: 更新 `CLAUDE.md` — 同步与远程代码库的差异。确保 Key Files 表包含 `bazi_pro/core/` 及其子模块（`constants.py`、`stems.py`、`ten_gods.py` 等）。确保 `bazi_pro/core_rules.py`（向后兼容代理）也被列出。更新 `server/app.py` 的备注——它的 `main()` 已经存在且版本号已正确。

- [ ] **T12**: 检查 `bazi_pro/core/__init__.py` 和 `bazi_pro/core_rules.py` 的双重存在。`bazi_pro/__init__.py` line 94 导入了 `from bazi_pro.core_rules import full_analysis`，而 `bazi_pro/core/__init__.py` 也定义了 `full_analysis()`。确认这是有意的双层架构（core_rules.py 是向后兼容的 re-export），在 CODE_WIKI.md 或 CLAUDE.md 中记录这个关系。

### 第四批：最终验证

- [ ] **T13**: 运行 `python tests/run_golden.py` — 分析当前 golden cases 的通过率。如果部分失败，分析根因（可能是 core/ 引擎与测试预期不匹配），修复测试或标记为已知问题。目标：至少 2/4 通过。

- [ ] **T14**: 运行 `python scripts/doctor.py` — 确认 9 项（或更多项）环境诊断通过。修正任何非网络相关的失败。

- [ ] **T15**: 运行 `python -m bazi_pro.trace demo > /tmp/trace.json && python -m bazi_pro.trace validate /tmp/trace.json` — 确认 trace pipeline 正常，输出版本号为 "5.0.0"。

---

## 完成标准

1. 以上所有 `[ ]` 变为 `[x]`
2. `python tests/run_golden.py` 尽量接近 4/4 通过
3. `python scripts/doctor.py` 无致命错误
4. 每个任务有独立的有描述性的 commit
5. 所有完成后终端输出 **"DONE — Ralph says: I'm a winner!"**

---

## 熔断规则

1. **连续 3 次迭代失败**（测试不通过或命令报错）→ 停止。记录卡住的任务。
2. **同一任务尝试超 5 次** → 跳过，标记为 `[!]` 并记录原因。
3. **git push 失败** → 停止（可能需要人工处理认证）。

---

## 禁止事项

- ❌ 不要修改 `SKILL.md` 的流程逻辑（只改版本号）
- ❌ 不要添加新的 Python 依赖
- ❌ 不要修改 `references/classical_corpus.md`
- ❌ 不要改变任何 CLI 参数接口或 API 返回格式
- ❌ 不要一次修多个任务
- ❌ 不要跳过验证步骤
- ❌ 不要用 `git add -A`
- ❌ 不要在 `bazi_pro/core/` 中添加 LLM 解读逻辑——它只做确定性计算

---

## 关键文件路径

| 文件 | 用途 |
|------|------|
| `bazi_pro/__init__.py` | `__version__` 单一来源 + AnalysisEngine SDK |
| `bazi_pro/core/__init__.py` | `full_analysis()` 确定性计算主入口 |
| `bazi_pro/core_rules.py` | 向后兼容代理 → re-export from bazi_pro.core |
| `SKILL.md` | 核心运行时合约 |
| `CLAUDE.md` | 设计原则和协作指南 |
| `CODE_WIKI.md` | 完整架构文档 |
| `ROADMAP.md` | 版本路线图 |
| `pyproject.toml` | 依赖和入口点 |
| `server/app.py` | FastAPI Web 服务 + `main()` |
| `plugins/loader.py` | 插件发现和加载 |
| `bazi_pro/retrieve_classical.py` | BM25 古籍检索核心 |
| `bazi_pro/hybrid_search.py` | BM25 + FAISS 混合搜索 |
| `bazi_pro/generate_report.py` | 报告生成 |
| `bazi_pro/dashboard.py` | 仪表盘 |
| `bazi_pro/trace.py` | TraceBuilder + 验证 |
| `bazi_pro/doctor.py` | 环境诊断 |
| `tests/run_golden.py` | Golden case 回归测试 |
| `scripts/` | CLI 封装脚本 |
| `references/` | 参考文件和静态数据 |
