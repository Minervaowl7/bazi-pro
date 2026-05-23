#!/usr/bin/env python3
"""bazi-pro 命盘对比引擎 v5.0 (EXPERIMENTAL)"""

from dataclasses import dataclass, field
from bazi_pro import GAN_WUXING, derive_shishen, count_wuxing_from_bazi, wuxing_pct

EXPERIMENTAL = True


GAN_HE = {
    frozenset({'甲', '己'}): '土', frozenset({'乙', '庚'}): '金',
    frozenset({'丙', '辛'}): '水', frozenset({'丁', '壬'}): '木',
    frozenset({'戊', '癸'}): '火',
}

ZHI_HE = {
    frozenset({'子', '丑'}): '土', frozenset({'寅', '亥'}): '木',
    frozenset({'卯', '戌'}): '火', frozenset({'辰', '酉'}): '金',
    frozenset({'巳', '申'}): '水', frozenset({'午', '未'}): '土',
}

ZHI_CHONG = {
    frozenset({'子', '午'}): True, frozenset({'丑', '未'}): True,
    frozenset({'寅', '申'}): True, frozenset({'卯', '酉'}): True,
    frozenset({'辰', '戌'}): True, frozenset({'巳', '亥'}): True,
}

ZHI_HAI = {
    frozenset({'子', '未'}): True, frozenset({'丑', '午'}): True,
    frozenset({'寅', '巳'}): True, frozenset({'卯', '辰'}): True,
    frozenset({'申', '亥'}): True, frozenset({'酉', '戌'}): True,
}

ZHI_XING = {
    frozenset({'子', '卯'}): True, frozenset({'寅', '巳'}): True,
    frozenset({'丑', '戌'}): True, frozenset({'未', '戌'}): True,
    frozenset({'辰', '辰'}): True, frozenset({'午', '午'}): True,
    frozenset({'酉', '酉'}): True, frozenset({'亥', '亥'}): True,
}

WUXING_SHENG = {
    ('木', '火'): True, ('火', '土'): True, ('土', '金'): True,
    ('金', '水'): True, ('水', '木'): True,
}

WUXING_KE = {
    ('木', '土'): True, ('土', '水'): True, ('水', '火'): True,
    ('火', '金'): True, ('金', '木'): True,
}


@dataclass
class CompareResult:
    chart_a: dict
    chart_b: dict
    pillar_diff: list[dict] = field(default_factory=list)
    wuxing_overlap: dict = field(default_factory=dict)
    yongshen_diff: dict = field(default_factory=dict)
    relation_analysis: list[dict] = field(default_factory=list)
    compatibility_score: int = 0
    compatibility_note: str = ''
    experimental: bool = True
    compatibility_ci: str = ''


class CompareEngine:

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

    def load_chart_a_dict(self, data: dict) -> None:
        self.chart_a = data

    def load_chart_b_dict(self, data: dict) -> None:
        self.chart_b = data

    def compare(self) -> CompareResult:
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
        result.experimental = True
        result.compatibility_ci = f'{result.compatibility_score}±15'
        return result

    def compare_pillars(self) -> list[dict]:
        a_bz = self.chart_a.get('八字', '')
        b_bz = self.chart_b.get('八字', '')
        a_parts = a_bz.split()
        b_parts = b_bz.split()
        a_dm = self.chart_a.get('日主', '')
        b_dm = self.chart_b.get('日主', '')

        diffs = []
        labels = ['年柱', '月柱', '日柱', '时柱']
        for i, label in enumerate(labels):
            a_val = a_parts[i] if i < len(a_parts) else '?'
            b_val = b_parts[i] if i < len(b_parts) else '?'
            same = a_val == b_val
            a_gan = a_val[0] if len(a_val) >= 1 else ''
            b_gan = b_val[0] if len(b_val) >= 1 else ''
            a_zhi = a_val[1] if len(a_val) >= 2 else ''
            b_zhi = b_val[1] if len(b_val) >= 2 else ''

            entry = {
                'position': label,
                'chart_a': a_val,
                'chart_b': b_val,
                'same': same,
            }

            if a_gan and b_gan:
                he_result = GAN_HE.get(frozenset({a_gan, b_gan}))
                if he_result:
                    entry['gan_he'] = f'{a_gan}合{b_gan}→{he_result}'

            if a_zhi and b_zhi:
                pair = frozenset({a_zhi, b_zhi})
                if pair in ZHI_CHONG:
                    entry['zhi_chong'] = f'{a_zhi}冲{b_zhi}'
                if pair in ZHI_HE:
                    entry['zhi_he'] = f'{a_zhi}合{b_zhi}'
                if pair in ZHI_HAI:
                    entry['zhi_hai'] = f'{a_zhi}害{b_zhi}'
                if pair in ZHI_XING:
                    entry['zhi_xing'] = f'{a_zhi}刑{b_zhi}'

            if a_dm and b_gan:
                entry['shishen_a_to_b'] = derive_shishen(a_dm, b_gan)
            if b_dm and a_gan:
                entry['shishen_b_to_a'] = derive_shishen(b_dm, a_gan)

            diffs.append(entry)
        return diffs

    def compare_wuxing(self) -> dict:
        a_bz = self.chart_a.get('八字', '')
        b_bz = self.chart_b.get('八字', '')
        a_dm = self.chart_a.get('日主', '')
        b_dm = self.chart_b.get('日主', '')

        a_counts = count_wuxing_from_bazi(a_bz)
        b_counts = count_wuxing_from_bazi(b_bz)
        a_pct = wuxing_pct(a_counts)
        b_pct = wuxing_pct(b_counts)

        overlap = {}
        for wx in ['木', '火', '土', '金', '水']:
            overlap[wx] = {
                'chart_a_pct': a_pct.get(wx, 0),
                'chart_b_pct': b_pct.get(wx, 0),
                'diff_pct': round(a_pct.get(wx, 0) - b_pct.get(wx, 0), 1),
            }

        return {
            'day_master_a': a_dm,
            'day_master_b': b_dm,
            'overlap': overlap,
            'note': '基于天干地支本气的粗略统计，精确力量需含藏干中余气加权',
        }

    def compare_yongshen(self) -> dict:
        a_yongshen = self.chart_a.get('喜用神', '') or self.chart_a.get('用神', '')
        b_yongshen = self.chart_b.get('喜用神', '') or self.chart_b.get('用神', '')

        if not a_yongshen:
            a_yongshen = self._infer_yongshen_hint(self.chart_a)
        if not b_yongshen:
            b_yongshen = self._infer_yongshen_hint(self.chart_b)

        conflict = False
        conflict_desc = ''
        if a_yongshen and b_yongshen:
            a_wx_list = [GAN_WUXING.get(g, g) for g in a_yongshen if g in GAN_WUXING]
            b_wx_list = [GAN_WUXING.get(g, g) for g in b_yongshen if g in GAN_WUXING]
            for aw in a_wx_list:
                for bw in b_wx_list:
                    if WUXING_KE.get((aw, bw)):
                        conflict = True
                        conflict_desc = f'A喜{aw} vs B喜{bw}：{aw}克{bw}'

        return {
            'chart_a_yongshen': a_yongshen or 'insufficient_data',
            'chart_b_yongshen': b_yongshen or 'insufficient_data',
            'conflict': conflict,
            'conflict_desc': conflict_desc,
            'note': '喜用神数据缺失，请先通过 AnalysisEngine 获取完整分析结果',
        }

    def compare_relations(self) -> list[dict]:
        a_dm_wx = self._daymaster_wuxing(self.chart_a)
        b_dm_wx = self._daymaster_wuxing(self.chart_b)
        a_bz = self.chart_a.get('八字', '')
        b_bz = self.chart_b.get('八字', '')

        relations = []

        if a_dm_wx and b_dm_wx:
            if WUXING_SHENG.get((a_dm_wx, b_dm_wx)):
                relations.append({
                    'type': '日主互动',
                    'relation': '相生',
                    'description': f'A日主{a_dm_wx}生B日主{b_dm_wx}',
                    'confidence_interval': '±15%',
                })
            elif WUXING_SHENG.get((b_dm_wx, a_dm_wx)):
                relations.append({
                    'type': '日主互动',
                    'relation': '相生',
                    'description': f'B日主{b_dm_wx}生A日主{a_dm_wx}',
                    'confidence_interval': '±15%',
                })
            elif WUXING_KE.get((a_dm_wx, b_dm_wx)):
                relations.append({
                    'type': '日主互动',
                    'relation': '相克',
                    'description': f'A日主{a_dm_wx}克B日主{b_dm_wx}',
                    'confidence_interval': '±15%',
                })
            elif WUXING_KE.get((b_dm_wx, a_dm_wx)):
                relations.append({
                    'type': '日主互动',
                    'relation': '相克',
                    'description': f'B日主{b_dm_wx}克A日主{a_dm_wx}',
                    'confidence_interval': '±15%',
                })
            elif a_dm_wx == b_dm_wx:
                relations.append({
                    'type': '日主互动',
                    'relation': '比和',
                    'description': f'A与B日主同属{a_dm_wx}',
                    'confidence_interval': '±15%',
                })
            else:
                relations.append({
                    'type': '日主互动',
                    'relation': '平',
                    'description': f'A日主{a_dm_wx} vs B日主{b_dm_wx}',
                    'confidence_interval': '±15%',
                })

        a_gans = [p[0] for p in a_bz.split() if len(p) >= 1]
        b_gans = [p[0] for p in b_bz.split() if len(p) >= 1]
        for ag in a_gans:
            for bg in b_gans:
                he_result = GAN_HE.get(frozenset({ag, bg}))
                if he_result:
                    relations.append({
                        'type': '天干合',
                        'relation': '合化',
                        'description': f'A{ag}合B{bg}→化{he_result}',
                        'confidence_interval': '±15%',
                    })

        a_zhis = [p[1] for p in a_bz.split() if len(p) >= 2]
        b_zhis = [p[1] for p in b_bz.split() if len(p) >= 2]
        for az in a_zhis:
            for bz in b_zhis:
                pair = frozenset({az, bz})
                if pair in ZHI_CHONG:
                    relations.append({
                        'type': '地支冲',
                        'relation': '冲',
                        'description': f'A{az}冲B{bz}',
                        'confidence_interval': '±15%',
                    })
                if pair in ZHI_HE:
                    he_wx = ZHI_HE[pair]
                    relations.append({
                        'type': '地支合',
                        'relation': '合',
                        'description': f'A{az}合B{bz}→化{he_wx}',
                        'confidence_interval': '±15%',
                    })
                if pair in ZHI_HAI:
                    relations.append({
                        'type': '地支害',
                        'relation': '害',
                        'description': f'A{az}害B{bz}',
                        'confidence_interval': '±15%',
                    })
                if pair in ZHI_XING:
                    relations.append({
                        'type': '地支刑',
                        'relation': '刑',
                        'description': f'A{az}刑B{bz}',
                        'confidence_interval': '±15%',
                    })

        return relations

    def compatibility_score(self) -> tuple[int, str]:
        score = 50
        notes = []

        a_dm_wx = self._daymaster_wuxing(self.chart_a)
        b_dm_wx = self._daymaster_wuxing(self.chart_b)

        if a_dm_wx and b_dm_wx:
            if WUXING_SHENG.get((a_dm_wx, b_dm_wx)) or WUXING_SHENG.get((b_dm_wx, a_dm_wx)):
                score += 15
                notes.append('日主相生+15')
            elif WUXING_KE.get((a_dm_wx, b_dm_wx)) or WUXING_KE.get((b_dm_wx, a_dm_wx)):
                score -= 10
                notes.append('日主相克-10')
            elif a_dm_wx == b_dm_wx:
                score += 10
                notes.append('日主比和+10')

        relations = self.compare_relations()
        he_count = sum(1 for r in relations if r['type'] in ('天干合', '地支合'))
        chong_count = sum(1 for r in relations if r['type'] in ('地支冲',))
        hai_count = sum(1 for r in relations if r['type'] == '地支害')
        xing_count = sum(1 for r in relations if r['type'] == '地支刑')

        score += he_count * 5
        if he_count:
            notes.append(f'合化{he_count}组+{he_count * 5}')
        score -= chong_count * 8
        if chong_count:
            notes.append(f'冲{chong_count}组-{chong_count * 8}')
        score -= hai_count * 5
        if hai_count:
            notes.append(f'害{hai_count}组-{hai_count * 5}')
        score -= xing_count * 5
        if xing_count:
            notes.append(f'刑{xing_count}组-{xing_count * 5}')

        yongshen = self.compare_yongshen()
        if yongshen['conflict']:
            score -= 10
            notes.append(f'喜用神冲突-10: {yongshen["conflict_desc"]}')

        score = max(0, min(100, score))
        note = ' | '.join(notes) if notes else '基础评分（EXPERIMENTAL），置信区间±15%'
        return score, note

    @staticmethod
    def _daymaster_wuxing(chart: dict) -> str:
        dm = chart.get('日主', '')
        return GAN_WUXING.get(dm, '')

    @staticmethod
    def _infer_yongshen_hint(chart: dict) -> str:
        return ''
