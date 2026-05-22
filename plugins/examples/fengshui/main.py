#!/usr/bin/env python3
"""风水关联示例插件"""

from bazi_pro.plugin_api import BaziPlugin

# 五行→方位+颜色
WUXING_FENGSHUI = {
    '木': {'direction': '东方', 'color': '绿色/青色', 'element': '植物、木质家具'},
    '火': {'direction': '南方', 'color': '红色/紫色', 'element': '灯光、蜡烛'},
    '土': {'direction': '中央', 'color': '黄色/棕色', 'element': '陶瓷、石头'},
    '金': {'direction': '西方', 'color': '白色/金色', 'element': '金属装饰、铜器'},
    '水': {'direction': '北方', 'color': '黑色/蓝色', 'element': '水景、鱼缸'},
}


class FengShuiPlugin(BaziPlugin):
    name = 'fengshui'
    version = '1.0.0'
    description = '根据喜用神推荐风水方位和颜色'

    def on_retrieve(self, query: str, results: list[dict]) -> list[dict]:
        return results

    def on_evidence(self, evidence: dict) -> dict:
        return evidence

    def on_render(self, html: str, vm) -> str:
        yongshen = vm.verdict.yongshen
        if not yongshen:
            return html

        recs = []
        for ys in yongshen[:2]:
            if ys in WUXING_FENGSHUI:
                info = WUXING_FENGSHUI[ys]
                recs.append(f'{ys}→{info["direction"]} {info["color"]} {info["element"]}')

        if recs:
            fengshui_html = (
                '<div class="plugin-fengshui" style="margin:16px 0;padding:16px;'
                'background:var(--neo-surface,#1a1a2e);border:1px solid var(--neo-border);'
                'border-radius:12px">'
                '<h4 style="color:var(--neo-gold,#c4a86c);margin:0 0 8px">风水建议</h4>'
                + ''.join(f'<p style="margin:4px 0;color:var(--neo-ink-soft)">{r}</p>' for r in recs)
                + '<p style="font-size:10px;color:var(--neo-muted);margin-top:8px">'
                '以上为传统文化参考，非风水专业建议</p></div>'
            )
            body_close = html.find('</body>')
            if body_close > 0:
                return html[:body_close] + fengshui_html + html[body_close:]
        return html
