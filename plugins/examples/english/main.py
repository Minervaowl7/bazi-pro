#!/usr/bin/env python3
"""英文翻译示例插件"""

from bazi_pro.plugin_api import BaziPlugin


class EnglishTranslationPlugin(BaziPlugin):
    name = 'english'
    version = '1.0.0'
    description = '将八字解读结果翻译为英文'

    def on_retrieve(self, query: str, results: list[dict]) -> list[dict]:
        return results  # 检索不做翻译

    def on_evidence(self, evidence: dict) -> dict:
        return evidence  # 证据不做翻译

    def on_render(self, html: str, vm) -> str:
        # 示例：简单地在 HTML 头部注入翻译提示
        note = (
            '<div class="plugin-english-note" style="padding:8px 12px;'
            'background:rgba(196,168,108,0.1);border:1px solid #c4a86c;'
            'border-radius:8px;margin:12px 0;font-size:12px;color:#c4a86c">'
            'English Plugin loaded. Translation service requires API key configuration.'
            '</div>'
        )
        head_end = html.find('</head>')
        if head_end > 0:
            return html[:head_end + 7] + note + html[head_end + 7:]
        return html
