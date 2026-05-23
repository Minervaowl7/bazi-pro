"""bazi-pro — 可审计、可交互、可视化的八字命理分析引擎"""

__version__ = "5.0.0"

__all__ = [
    'retrieve', 'retrieve_batch', 'load_corpus',
    'build_analysis_evidence', 'new_evidence',
    'GAN_WUXING', 'ZHI_WUXING', 'GAN_SHISHEN_MAP',
    'derive_shishen', 'count_wuxing_from_bazi', 'wuxing_pct',
    'AnalysisEngine',
]

from bazi_pro.retrieve_classical import retrieve, retrieve_batch, load_corpus
from bazi_pro.evidence import build_analysis_evidence, new_evidence


from bazi_pro.core.constants import (
    GAN_WUXING, ZHI_WUXING, GAN_SHISHEN_MAP, derive_shishen,
)


def count_wuxing_from_bazi(bazi_str: str) -> dict[str, int]:
    """Quick preview — 天干+地支本气计数，不用于最终旺衰裁决。正式分析请使用 core.element_forces"""
    counts = {'木': 0, '火': 0, '土': 0, '金': 0, '水': 0}
    for token in bazi_str.split():
        if len(token) >= 2:
            gan, zhi = token[0], token[1]
            wx_gan = GAN_WUXING.get(gan, '')
            wx_zhi = ZHI_WUXING.get(zhi, '')
            if wx_gan:
                counts[wx_gan] += 1
            if wx_zhi:
                counts[wx_zhi] += 1
    return counts


def wuxing_pct(counts: dict[str, int]) -> dict[str, float]:
    """Quick preview — 基于本气计数的粗略百分比，不用于最终旺衰裁决"""
    total = max(1, sum(counts.values()))
    return {k: round(v / total * 100, 1) for k, v in counts.items()}


class AnalysisEngine:
    """八字命理分析引擎 — 公共 SDK API

    用法:
        engine = AnalysisEngine()
        result = engine.analyze(mcp_json)
        report = engine.generate_report(result, format='html')
    """

    def __init__(self, corpus_path: str = '', use_hybrid: bool = True):
        self._corpus_path = corpus_path
        self._use_hybrid = use_hybrid
        self._retrieval_warnings: list[str] = []

    def retrieve(self, query: str, k: int = 5) -> list[dict]:
        corpus = self._resolve_corpus()
        self._retrieval_warnings = []
        if not corpus:
            self._retrieval_warnings.append('corpus path not found')
            return []
        try:
            result = retrieve(corpus, query, k=k)
            return result.get('results', [])
        except SystemExit as e:
            self._retrieval_warnings.append(f'retrieval SystemExit: {e}')
            return []
        except Exception as e:
            self._retrieval_warnings.append(f'retrieval error: {type(e).__name__}: {e}')
            return []

    def analyze(self, mcp_json: dict, detail_level: str = 'standard') -> dict:
        bazi = mcp_json.get('八字', '')
        day_master = mcp_json.get('日主', '')
        gender = mcp_json.get('性别', '')

        validation = {
            'valid': all([bazi, day_master, gender]),
            'bazi': bazi,
            'day_master': day_master,
            'gender': gender,
        }

        if not validation['valid']:
            return {
                'status': 'invalid_input',
                'detail_level': detail_level,
                'validation': validation,
                'missing': [f for f, v in [('八字', bazi), ('日主', day_master), ('性别', gender)] if not v],
            }

        from bazi_pro.core_rules import full_analysis as _full_analysis
        core = _full_analysis(mcp_json)

        query = f'{day_master} {bazi} 格局 旺衰 用神'
        retrieval_results = self.retrieve(query, k=8)

        wangshuai = core.get('wangshuai', {})
        pattern = core.get('pattern', {})
        yongshen = core.get('yongshen', {})
        element_forces = core.get('element_forces', {})

        pattern_name = pattern.get('pattern', '待定')
        if pattern_name in ('待定', '数据不足', ''):
            pattern_structured = {
                'name': 'unknown',
                'confidence': 0,
                'reason': 'deterministic_rules_insufficient',
                'need_llm_interpretation': True,
            }
        else:
            pattern_structured = {
                'name': pattern_name,
                'layer': pattern.get('layer', -1),
                'type': pattern.get('type', ''),
                'confidence': pattern.get('confidence', 0),
                'reason': pattern.get('reason', ''),
                'candidates': pattern.get('candidates', []),
                'yongshen_direction': pattern.get('yongshen_direction', '待定'),
                'need_llm_interpretation': False,
            }

        quick_counts = count_wuxing_from_bazi(bazi)
        quick_pct = wuxing_pct(quick_counts)

        return {
            'status': 'completed',
            'detail_level': detail_level,
            'validation': validation,
            'core_analysis': core,
            'pillars': core.get('pillars', []),
            'shishen': {f"{p['position']}干": p.get('shishen', '')
                        for p in core.get('pillars', []) if p.get('gan')},
            'deling': core.get('deling', {}),
            'dedi': core.get('dedi', {}),
            'deshi': core.get('deshi', {}),
            'strength': {
                'day_master': day_master,
                'wangshuai': wangshuai,
                'wuxing_quick': {
                    'counts': quick_counts,
                    'percent': quick_pct,
                },
            },
            'pattern': pattern_structured,
            'yongshen': yongshen,
            'element_forces': {
                'raw': {k: round(v, 2) for k, v in element_forces.get('raw', {}).items()},
                'percent': element_forces.get('percent', {}),
                'total': element_forces.get('total', 0),
            },
            'elements': {
                'counts': quick_counts,
                'percent': quick_pct,
            },
            'quick_element_counts': {
                'counts': quick_counts,
                'note': 'preview only, not for final judgment',
            },
            'quick_element_pct': {
                'percent': quick_pct,
                'note': 'preview only, not for final judgment',
            },
            'relations': core.get('relations', []),
            'retrieval': {
                'count': len(retrieval_results),
                'results': retrieval_results,
                'warnings': list(self._retrieval_warnings),
            },
            'note': '确定性推导（十神、藏干、旺衰、格局候选、喜用神候选、刑冲合害）已完成。调候用神需查穷通宝鉴，由LLM补充。',
        }

    def generate_report(self, analysis: dict, format: str = 'html') -> str:
        from bazi_pro.generate_report import generate_html_report

        meta = analysis.get('validation', {})
        body_text = self._format_analysis_body(analysis)

        if format == 'html':
            return generate_html_report(meta, body_text,
                                        '八字命理分析报告', '')
        elif format == 'markdown':
            from bazi_pro.generate_report import generate_enhanced_markdown
            return generate_enhanced_markdown(meta, body_text,
                                              '八字命理分析报告', '')
        elif format == 'dashboard':
            from bazi_pro.dashboard import generate_dashboard
            def _md_to_html(text): return text
            return generate_dashboard(meta, body_text,
                                      '八字命理分析报告', '', _md_to_html)
        return ''

    def _resolve_corpus(self) -> str:
        import os
        if self._corpus_path:
            return self._corpus_path
        candidates = [
            os.path.join(os.path.dirname(__file__), '..', 'references', 'classical_corpus.md'),
        ]
        for p in candidates:
            if os.path.exists(p):
                return os.path.abspath(p)
        return ''

    @staticmethod
    def _parse_pillars(bazi: str, day_master: str) -> list[dict]:
        parts = bazi.split()
        positions = ['年', '月', '日', '时']
        pillars = []
        for i, token in enumerate(parts):
            if len(token) >= 2:
                gan, zhi = token[0], token[1]
                pillars.append({
                    'position': positions[i] if i < 4 else '',
                    'gan': gan,
                    'zhi': zhi,
                    'wuxing_gan': GAN_WUXING.get(gan, ''),
                    'wuxing_zhi': ZHI_WUXING.get(zhi, ''),
                    'shishen': derive_shishen(day_master, gan),
                })
        return pillars

    @staticmethod
    def _derive_shishen_map(day_master: str, pillars: list[dict]) -> dict[str, str]:
        result = {}
        for p in pillars:
            pos = p.get('position', '')
            gan = p.get('gan', '')
            if gan:
                result[f'{pos}干'] = derive_shishen(day_master, gan)
        return result

    @staticmethod
    def _wuxing_quick_check(wuxing_counts: dict[str, int], day_master: str) -> dict:
        dm_wx = GAN_WUXING.get(day_master, '')
        if not dm_wx:
            return {'tendency': '未知', 'yin_bi_pct': 0, 'ke_xie_hao_pct': 0}

        sheng_wo = _sheng_map.get(dm_wx, '')
        tong_wo = dm_wx

        yin_bi = wuxing_counts.get(sheng_wo, 0) + wuxing_counts.get(tong_wo, 0)
        total = max(1, sum(wuxing_counts.values()))
        yin_bi_pct = round(yin_bi / total * 100, 1)
        ke_xie_hao_pct = round(100 - yin_bi_pct, 1)

        if yin_bi_pct >= 75:
            tendency = '极偏·印比主导'
        elif yin_bi_pct >= 60:
            tendency = '偏旺·印比偏重'
        elif yin_bi_pct <= 25:
            tendency = '极偏·克泄耗主导'
        elif yin_bi_pct <= 40:
            tendency = '偏弱·克泄耗偏重'
        else:
            tendency = '相对平衡'

        return {
            'tendency': tendency,
            'yin_bi_pct': yin_bi_pct,
            'ke_xie_hao_pct': ke_xie_hao_pct,
            'day_master_wuxing': dm_wx,
            'sheng_wo_wuxing': sheng_wo,
        }

    @staticmethod
    def _format_analysis_body(analysis: dict) -> str:
        lines = ['# 八字命理分析报告', '']
        v = analysis.get('validation', {})
        lines.append(f"**八字**: {v.get('bazi', '')}")
        lines.append(f"**日主**: {v.get('day_master', '')}")
        lines.append('')

        pillars = analysis.get('pillars', [])
        if pillars:
            lines.append('## 四柱十神')
            lines.append('')
            lines.append('| 柱 | 天干 | 十神 | 地支 | 天干五行 | 地支五行 |')
            lines.append('|----|------|------|------|---------|---------|')
            for p in pillars:
                lines.append(
                    f"| {p['position']} | {p['gan']} | {p.get('shishen', '')} "
                    f"| {p['zhi']} | {p.get('wuxing_gan', '')} | {p.get('wuxing_zhi', '')} |"
                )
            lines.append('')

        element_forces = analysis.get('element_forces', {})
        pct = element_forces.get('percent', {})
        if pct:
            lines.append('## 五行力量')
            lines.append('')
            for wx in ['木', '火', '土', '金', '水']:
                p = pct.get(wx, 0)
                bar_len = int(p / 5)
                bar = '█' * bar_len + '░' * (20 - bar_len)
                lines.append(f'{wx} {bar} {p}%')
            lines.append('')

        lines.append('## 古籍检索结果')
        for r in analysis.get('retrieval', {}).get('results', []):
            lines.append(f"- [{r['id']}] ({r.get('source', '')}) {r.get('content', '')[:100]}")

        return '\n'.join(lines)


_sheng_map = {
    '木': '水', '火': '木', '土': '火', '金': '土', '水': '金',
}
