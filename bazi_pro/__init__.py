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


GAN_WUXING = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火',
    '戊': '土', '己': '土', '庚': '金', '辛': '金',
    '壬': '水', '癸': '水',
}
ZHI_WUXING = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木',
    '辰': '土', '巳': '火', '午': '火', '未': '土',
    '申': '金', '酉': '金', '戌': '土', '亥': '水',
}

GAN_SHISHEN_MAP = {
    ('甲', '甲'): '比肩', ('甲', '乙'): '劫财', ('甲', '丙'): '食神', ('甲', '丁'): '伤官',
    ('甲', '戊'): '偏财', ('甲', '己'): '正财', ('甲', '庚'): '七杀', ('甲', '辛'): '正官',
    ('甲', '壬'): '偏印', ('甲', '癸'): '正印',
    ('乙', '甲'): '劫财', ('乙', '乙'): '比肩', ('乙', '丙'): '伤官', ('乙', '丁'): '食神',
    ('乙', '戊'): '正财', ('乙', '己'): '偏财', ('乙', '庚'): '正官', ('乙', '辛'): '七杀',
    ('乙', '壬'): '正印', ('乙', '癸'): '偏印',
    ('丙', '甲'): '偏印', ('丙', '乙'): '正印', ('丙', '丙'): '比肩', ('丙', '丁'): '劫财',
    ('丙', '戊'): '食神', ('丙', '己'): '伤官', ('丙', '庚'): '偏财', ('丙', '辛'): '正财',
    ('丙', '壬'): '七杀', ('丙', '癸'): '正官',
    ('丁', '甲'): '正印', ('丁', '乙'): '偏印', ('丁', '丙'): '劫财', ('丁', '丁'): '比肩',
    ('丁', '戊'): '伤官', ('丁', '己'): '食神', ('丁', '庚'): '正财', ('丁', '辛'): '偏财',
    ('丁', '壬'): '正官', ('丁', '癸'): '七杀',
    ('戊', '甲'): '七杀', ('戊', '乙'): '正官', ('戊', '丙'): '偏印', ('戊', '丁'): '正印',
    ('戊', '戊'): '比肩', ('戊', '己'): '劫财', ('戊', '庚'): '食神', ('戊', '辛'): '伤官',
    ('戊', '壬'): '偏财', ('戊', '癸'): '正财',
    ('己', '甲'): '正官', ('己', '乙'): '七杀', ('己', '丙'): '正印', ('己', '丁'): '偏印',
    ('己', '戊'): '劫财', ('己', '己'): '比肩', ('己', '庚'): '伤官', ('己', '辛'): '食神',
    ('己', '壬'): '正财', ('己', '癸'): '偏财',
    ('庚', '甲'): '偏财', ('庚', '乙'): '正财', ('庚', '丙'): '七杀', ('庚', '丁'): '正官',
    ('庚', '戊'): '偏印', ('庚', '己'): '正印', ('庚', '庚'): '比肩', ('庚', '辛'): '劫财',
    ('庚', '壬'): '食神', ('庚', '癸'): '伤官',
    ('辛', '甲'): '正财', ('辛', '乙'): '偏财', ('辛', '丙'): '正官', ('辛', '丁'): '七杀',
    ('辛', '戊'): '正印', ('辛', '己'): '偏印', ('辛', '庚'): '劫财', ('辛', '辛'): '比肩',
    ('辛', '壬'): '伤官', ('辛', '癸'): '食神',
    ('壬', '甲'): '食神', ('壬', '乙'): '伤官', ('壬', '丙'): '偏财', ('壬', '丁'): '正财',
    ('壬', '戊'): '七杀', ('壬', '己'): '正官', ('壬', '庚'): '偏印', ('壬', '辛'): '正印',
    ('壬', '壬'): '比肩', ('壬', '癸'): '劫财',
    ('癸', '甲'): '伤官', ('癸', '乙'): '食神', ('癸', '丙'): '正财', ('癸', '丁'): '偏财',
    ('癸', '戊'): '正官', ('癸', '己'): '七杀', ('癸', '庚'): '正印', ('癸', '辛'): '偏印',
    ('癸', '壬'): '劫财', ('癸', '癸'): '比肩',
}


def derive_shishen(day_master: str, target_gan: str) -> str:
    return GAN_SHISHEN_MAP.get((day_master, target_gan), '')


def count_wuxing_from_bazi(bazi_str: str) -> dict[str, int]:
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

    def retrieve(self, query: str, k: int = 5) -> list[dict]:
        corpus = self._resolve_corpus()
        try:
            result = retrieve(corpus, query, k=k)
            return result.get('results', [])
        except SystemExit:
            return []
        except Exception:
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

        return {
            'status': 'completed',
            'detail_level': detail_level,
            'validation': validation,
            'retrieval': {
                'count': len(retrieval_results),
                'results': retrieval_results,
            },
            'core': core,
            'pillars': core.get('pillars', []),
            'shishen': {f"{p['position']}干": p.get('shishen', '')
                        for p in core.get('pillars', []) if p.get('gan')},
            'deling': core.get('deling', {}),
            'dedi': core.get('dedi', {}),
            'deshi': core.get('deshi', {}),
            'strength': {
                'day_master': day_master,
                'wangshuai': core.get('wangshuai', {}),
            },
            'element_forces': core.get('element_forces', {}),
            'relations': core.get('relations', []),
            'pattern': core.get('pattern', {}),
            'yongshen': core.get('yongshen', {}),
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

        elements = analysis.get('elements', {})
        pct = elements.get('percent', {})
        if pct:
            lines.append('## 五行力量（粗略统计）')
            lines.append('')
            for wx in ['木', '火', '土', '金', '水']:
                p = pct.get(wx, 0)
                bar_len = int(p / 5)
                bar = '█' * bar_len + '░' * (20 - bar_len)
                lines.append(f'{wx} {bar} {p}%')
            lines.append('')
            lines.append(f"⚠️ {elements.get('note', '')}")
            lines.append('')

        lines.append('## 古籍检索结果')
        for r in analysis.get('retrieval', {}).get('results', []):
            lines.append(f"- [{r['id']}] ({r.get('source', '')}) {r.get('content', '')[:100]}")

        return '\n'.join(lines)


_sheng_map = {
    '木': '水', '火': '木', '土': '火', '金': '土', '水': '金',
}
