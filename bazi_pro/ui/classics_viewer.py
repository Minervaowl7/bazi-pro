#!/usr/bin/env python3
"""
bazi-pro 古籍条文双栏展示 v5.0
左侧竖排原文（仿古纸张）+ 右侧白话解读 + 底部出处信息条
"""

from html import escape


def render_classics_viewer(classical_refs: list[dict]) -> str:
    """生成古籍条文双栏展示 HTML

    左侧：竖排原文（writing-mode: vertical-rl），仿古纸张背景，朱砂圈点
    右侧：白话解读 + 命盘命中原因
    底部：出处信息条（书名、卷数）

    Args:
        classical_refs: 检索结果列表，每项含 id, source, content, matched_terms 等

    Returns:
        双栏展示 HTML
    """
    if not classical_refs:
        return '<p class="empty-classics-placeholder">暂无匹配的古籍条文</p>'

    cards = ''
    for i, ref in enumerate(classical_refs[:10]):
        content = ref.get('content', '')
        source = ref.get('source', '')
        topic = ref.get('topic', '')
        ref_id = ref.get('id', '')
        matched = ref.get('matched_terms', [])
        score = ref.get('score', 0)
        highlighted = ref.get('highlighted_content', content)

        # 匹配词朱砂圈点（CSS text-decoration 模拟）
        matched_tags = ''.join(
            f'<span class="matched-tag">{escape(m)}</span>'
            for m in matched[:5]
        )

        cards += f'''<div class="classics-card">
<div class="classics-number">{i + 1:02d}</div>
<div class="classics-columns">
<div class="classics-original">
<div class="ancient-paper">
<div class="ancient-text">{escape(content)}</div>
</div>
</div>
<div class="classics-interpretation">
<div class="highlighted-text">{highlighted}</div>
<div class="matched-section">
<div class="matched-label">命盘命中词:</div>
<div class="matched-terms">{matched_tags or '—'}</div>
</div>
<div class="why-section">
<div class="why-label">命中原因:</div>
<div class="why-text">
BM25 得分 {score:.1f} | 主题: {escape(topic)} | 出处: {escape(source)}
</div>
</div>
</div>
</div>
<div class="classics-source-bar">
<span class="source-book">《{escape(source)}》</span>
<span class="source-id">{escape(ref_id)}</span>
<span class="source-topic">@{escape(topic)}</span>
</div>
</div>'''

    return f'''<div class="classics-viewer-container">
<style>
.classics-viewer-container {{ max-width: 780px; margin: 0 auto; padding: 16px; font-family: "Noto Serif SC", serif; }}
.classics-card {{ position: relative; background: var(--neo-surface, #1a1a2e);
  border: 1px solid var(--neo-border, #333);
  border-radius: var(--neo-radius-md, 12px); margin-bottom: 16px; overflow: hidden; }}
.classics-number {{ position: absolute; top: 12px; left: 12px;
  font-size: 24px; font-weight: 800; color: var(--neo-gold, #c4a86c); opacity: 0.5; }}
.classics-columns {{ display: grid; grid-template-columns: 1fr 2fr; gap: 0; min-height: 180px; }}
.classics-original {{ padding: 20px 16px; border-right: 1px solid var(--neo-border, #333); }}
.ancient-paper {{ background: linear-gradient(135deg, #f5f0e0, #efe8d0);
  border: 1px solid #c8b896; border-radius: 2px; padding: 16px 12px;
  box-shadow: inset 0 0 20px rgba(139, 119, 70, 0.08); }}
.ancient-text {{ writing-mode: vertical-rl; text-orientation: mixed;
  font-family: "Zhi Mang Xing", "Ma Shan Zheng", STKaiti, KaiTi, serif;
  font-size: 16px; line-height: 2; color: #3a2a1a; letter-spacing: 2px;
  max-height: 260px; overflow-y: auto; }}
.classics-interpretation {{ padding: 20px 16px; display: flex; flex-direction: column; gap: 12px; }}
.highlighted-text {{ font-size: 14px; line-height: 1.8; color: var(--neo-ink, #ddd); }}
.highlighted-text mark {{ background: rgba(196, 74, 74, 0.2); color: var(--neo-ink, #ddd);
  padding: 1px 4px; border-radius: 2px; border-bottom: 1.5px solid #c46a4a; }}
.matched-section {{ margin-top: 8px; }}
.matched-label {{ font-size: 10px; color: var(--neo-muted, #666); letter-spacing: 2px; margin-bottom: 4px; }}
.matched-terms {{ display: flex; gap: 6px; flex-wrap: wrap; }}
.matched-tag {{ padding: 2px 8px; background: rgba(196, 74, 74, 0.12); border: 1px solid rgba(196, 74, 74, 0.3);
  border-radius: 10px; font-size: 11px; color: #c46a4a; }}
.why-section {{ margin-top: auto; }}
.why-label {{ font-size: 10px; color: var(--neo-muted, #666); letter-spacing: 2px; margin-bottom: 4px; }}
.why-text {{ font-size: 11px; color: var(--neo-muted, #666); }}
.classics-source-bar {{ display: flex; align-items: center; gap: 12px;
  padding: 8px 16px; background: var(--neo-surface-2, #222);
  border-top: 1px solid var(--neo-border, #333); font-size: 11px; }}
.source-book {{ color: var(--neo-gold, #c4a86c); font-weight: 600; }}
.source-id {{ color: var(--neo-muted, #666); font-family: monospace; }}
.source-topic {{ color: var(--neo-muted, #666); margin-left: auto; }}
.empty-classics-placeholder {{ text-align: center; color: var(--neo-muted, #666); padding: 30px; }}

@media (max-width: 640px) {{
.classics-columns {{ grid-template-columns: 1fr; }}
.classics-original {{ border-right: none; border-bottom: 1px solid var(--neo-border, #333); }}
.ancient-text {{ writing-mode: horizontal-tb; max-height: 120px; }}
}}
</style>
{cards}
</div>'''
