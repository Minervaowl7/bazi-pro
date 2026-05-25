#!/usr/bin/env python3
"""塔罗牌关联示例插件"""

from bazi_pro.plugin_api import BaziPlugin

# 十神 → 大阿尔卡纳映射
TEN_GOD_TO_TAROT = {
    '正官': 'The Emperor', '七杀': 'The Tower', '正印': 'The High Priestess',
    '偏印': 'The Hermit', '正财': 'The Empress', '偏财': 'The Wheel of Fortune',
    '食神': 'The Sun', '伤官': 'The Magician', '比肩': 'Strength',
    '劫财': 'The Chariot', '日主': 'The Fool',
}


class TarotCorrelationPlugin(BaziPlugin):
    name = 'tarot'
    version = '1.0.0'
    description = '将八字十神映射到塔罗大阿尔卡纳牌'

    def on_retrieve(self, query: str, results: list[dict]) -> list[dict]:
        return results

    def on_evidence(self, evidence: dict) -> dict:
        cards = set()
        for rule in evidence.get('basis', {}).get('rules', []):
            for shen, card in TEN_GOD_TO_TAROT.items():
                if isinstance(rule, str) and shen in rule:
                    cards.add(card)
        evidence['tarot_cards'] = list(cards)
        return evidence

    def on_render(self, html: str, vm) -> str:
        return html
