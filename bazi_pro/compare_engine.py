#!/usr/bin/env python3
"""
bazi-pro 命盘对比引擎 v4.8
双命盘并排对比：四柱、五行、喜用神、合化关系、兼容性评分
"""

from dataclasses import dataclass, field


@dataclass
class CompareResult:
    """对比结果"""
    chart_a: dict
    chart_b: dict
    pillar_diff: list[dict] = field(default_factory=list)
    wuxing_overlap: dict = field(default_factory=dict)
    yongshen_diff: dict = field(default_factory=dict)
    relation_analysis: list[dict] = field(default_factory=list)
    compatibility_score: int = 0
    compatibility_note: str = ''


class CompareEngine:
    """命盘对比引擎

    加载两个 MCP JSON 命盘，分析异同和兼容性
    """

    def __init__(self):
        self.chart_a: dict = {}
        self.chart_b: dict = {}

    def load_chart_a(self, json_path: str) -> None:
        import json
        with open(json_path, 'r', encoding='utf-8') as f:
            self.chart_a = json.load(f)

    def load_chart_b(self, json_path: str) -> None:
        import json
        with open(json_path, 'r', encoding='utf-8') as f:
            self.chart_b = json.load(f)

    def compare(self) -> CompareResult:
        """执行完整对比"""
        result = CompareResult(
            chart_a=self.chart_a,
            chart_b=self.chart_b,
        )

        result.pillar_diff = self.compare_pillars()
        result.wuxing_overlap = self.compare_wuxing()
        result.yongshen_diff = self.compare_yongshen()
        result.relation_analysis = self.compare_relations()
        score, note = self.compatibility_score()
        result.compatibility_score = score
        result.compatibility_note = note

        return result

    def compare_pillars(self) -> list[dict]:
        """并排四柱对比"""
        a_bz = self.chart_a.get('八字', '')
        b_bz = self.chart_b.get('八字', '')
        a_parts = a_bz.split()
        b_parts = b_bz.split()

        diffs = []
        labels = ['年柱', '月柱', '日柱', '时柱']
        for i, label in enumerate(labels):
            a_val = a_parts[i] if i < len(a_parts) else '?'
            b_val = b_parts[i] if i < len(b_parts) else '?'
            same = a_val == b_val
            diffs.append({
                'position': label,
                'chart_a': a_val,
                'chart_b': b_val,
                'same': same,
            })
        return diffs

    def compare_wuxing(self) -> dict:
        """五行雷达图叠加数据"""
        a_dm = self.chart_a.get('日主', '')
        b_dm = self.chart_b.get('日主', '')
        return {
            'day_master_a': a_dm,
            'day_master_b': b_dm,
            'note': '精确五行对比需由 MCP 提供 stem_branch_forces 数据',
        }

    def compare_yongshen(self) -> dict:
        """喜用神差异"""
        return {
            'chart_a_yongshen': '待分析',
            'chart_b_yongshen': '待分析',
            'conflict': False,
            'note': '喜用神对比需由 LLM 完成完整分析后填充',
        }

    def compare_relations(self) -> list[dict]:
        """合化关系分析（合婚/合作场景）"""
        a_dm_wx = self._daymaster_wuxing(self.chart_a)
        b_dm_wx = self._daymaster_wuxing(self.chart_b)

        relations = []
        # 五行相生相克关系
        interactions = {
            ('木', '火'): '相生', ('火', '土'): '相生', ('土', '金'): '相生',
            ('金', '水'): '相生', ('水', '木'): '相生',
            ('木', '土'): '相克', ('土', '水'): '相克', ('水', '火'): '相克',
            ('火', '金'): '相克', ('金', '木'): '相克',
        }
        rel = interactions.get((a_dm_wx, b_dm_wx), '平')
        relations.append({
            'type': '日主互动',
            'relation': rel,
            'description': f'A日主{a_dm_wx} vs B日主{b_dm_wx}：{rel}',
        })

        return relations

    def compatibility_score(self) -> tuple[int, str]:
        """综合兼容性评分（0-100）"""
        score = 70  # 默认基准
        note = '精确兼容性评分需由 LLM 综合多维度分析后填充'
        return score, note

    @staticmethod
    def _daymaster_wuxing(chart: dict) -> str:
        dm = chart.get('日主', '')
        return {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
                '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}.get(dm, '')
