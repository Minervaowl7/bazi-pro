# 报告生成器跨平台字体配置

## 问题背景

`scripts/generate_report.py` 生成的 HTML 和 PDF 报告在跨平台环境下会出现乱码/缺字问题，
根因是 CSS 字体栈引用了仅存在于特定操作系统的字体名。

## 已修复项（v3.4.1）

### 1. 中文字体名修正

| 旧值 | 新值 | 原因 |
|------|------|------|
| `"Noto Serif SC"` | `"Noto Serif CJK SC"` | Linux 实际字体名带 CJK 后缀 |
| `"SimSun"` | 移至回退链末尾 | Windows 字体，Linux 下不存在 |
| `"STSong"` | 同上 | 同上 |
| `"Microsoft YaHei"` | 同上 | 同上 |
| 新增 | `"DejaVu Serif"` | Linux 通用衬线字体回退 |

### 2. 等宽字体修正

| 旧值 | 新值 | 原因 |
|------|------|------|
| `"Courier New", "SimHei"` | `"DejaVu Sans Mono", "Noto Sans Mono", "Courier New", "SimHei"` | Linux 下 Courier New 通常不存在 |

### 3. Emoji 渲染方案

**HTML（浏览器）**：安装 `fonts-noto-color-emoji` 后，浏览器原生渲染彩色 emoji。

**PDF（weasyprint）**：weasyprint 对彩色 emoji 字体支持有限，PDF 中 emoji 会变灰/变乱码。
解决方案：`strip_emoji_for_pdf()` 函数在生成 PDF 前将 emoji 替换为 ASCII/Unicode 文本符号。

#### Emoji → 文本降级表

| Emoji | PDF 替代 | 含义 |
|-------|---------|------|
| ⭐ 🔮 🌟 | ★ | 重点标记 |
| ⚠️ ⚠ | ⚠ | 警告（U+26A0，变体选择符已剥离） |
| 🔴 🟢 🟡 | ● | 圆点标记 |
| ✅ ✔️ ✔ | ✓ | 确认 |
| ❌ ✖️ ✖ | ✗ | 否定 |
| 🌊 💧 | ≈ | 水/波浪 |
| 🔥 | ! | 火/极 |
| 📈 | ↑ | 上升 |
| 🚀 | ↑↑ | 爆发 |
| 🩺 | + | 药/修复 |
| ⏳ | ~ | 等待/变动 |
| ⛔ | ⊗ | 禁止 |

### 4. 安装步骤

```bash
# WSL / Linux 环境必须安装 emoji 字体
sudo apt-get install -y fonts-noto-color-emoji

# 刷新字体缓存
fc-cache -fv

# 验证
fc-list "Noto Color Emoji"
fc-list "Noto Serif CJK SC"
fc-list "DejaVu Sans Mono"
```

### 5. 字体覆盖验证

`scripts/generate_report.py` 使用的字符需以下字体覆盖：

| 字符类型 | 示例 | 所需字体 | 覆盖情况 |
|---------|------|---------|---------|
| 中文 | 八字命理 | Noto Serif CJK SC | ✅ |
| 表格框线 | │├└┬┴─ | DejaVu Sans Mono | ✅ |
| 块元素 | █░ | DejaVu Sans Mono | ✅ |
| Emoji | ⭐⚠🔮 | Noto Color Emoji (HTML) / 文本替代 (PDF) | ✅ |
| 数学符号 | ≈↑→ | DejaVu Serif | ✅ |

### 6. 故障排查

| 症状 | 原因 | 解决 |
|------|------|------|
| PDF 中文变豆腐块 | `Noto Serif CJK SC` 未安装 | `sudo apt install fonts-noto-cjk` |
| PDF 表格框线缺失 | `DejaVu Sans Mono` 未安装 | `sudo apt install fonts-dejavu-mono` |
| PDF emoji 变豆腐块 | 预期行为 — emoji 已降级为文本符号 | 检查 `strip_emoji_for_pdf()` 是否覆盖所有 emoji |
| HTML emoji 不显示 | `fonts-noto-color-emoji` 未安装 | `sudo apt install fonts-noto-color-emoji` |

### 7. weasyprint 错误调试

v3.4.1 已将 `try_generate_pdf()` 中的静默 `pass` 改为 stderr 输出：
```python
except Exception as e:
    print(f'  [weasyprint] 渲染异常: {e}', file=sys.stderr)
```

遇到 PDF 生成问题时可查看 weasyprint 的具体错误信息。
