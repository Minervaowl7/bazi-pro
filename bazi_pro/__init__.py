"""bazi-pro — 可审计、可交互、可视化的八字命理分析引擎"""

__version__ = "5.0.0"

from bazi_pro.retrieve_classical import retrieve, retrieve_batch, load_corpus
from bazi_pro.evidence import build_analysis_evidence, new_evidence


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
        """古籍条文检索

        Args:
            query: 中文检索查询词
            k: 返回结果数量

        Returns:
            检索结果列表
        """
        corpus = self._resolve_corpus()
        result = retrieve(corpus, query, k=k)
        return result.get('results', [])

    def analyze(self, mcp_json: dict, detail_level: str = 'standard') -> dict:
        """执行八字命理分析

        Args:
            mcp_json: Bazi MCP 返回的 JSON 数据
            detail_level: 'brief' | 'standard' | 'detailed'

        Returns:
            分析结果 dict，含 validation, strength, pattern, elements 等字段
        """
        # 简化的同步分析流程
        bazi = mcp_json.get('八字', '')
        day_master = mcp_json.get('日主', '')
        gender = mcp_json.get('性别', '')

        # Step 0: 检索古籍
        query = f'{day_master} {bazi} 格局 旺衰 用神'
        retrieval_results = self.retrieve(query, k=8)

        # Step 1: 数据校验
        validation = {
            'valid': all([bazi, day_master, gender]),
            'bazi': bazi,
            'day_master': day_master,
            'gender': gender,
        }

        return {
            'status': 'completed',
            'detail_level': detail_level,
            'validation': validation,
            'retrieval': {
                'count': len(retrieval_results),
                'results': retrieval_results,
            },
            'strength': {'day_master': day_master, 'level': '待LLM分析'},
            'pattern': {'name': '待LLM分析'},
            'elements': {'note': '精确五行力量需LLM根据SKILL.md第五步计算'},
            'note': '完整分析需由 LLM 按照 SKILL.md 执行流完成。AnalysisEngine 提供了数据预处理框架。',
        }

    def generate_report(self, analysis: dict, format: str = 'html') -> str:
        """生成分析报告

        Args:
            analysis: analyze() 返回的分析结果
            format: 'html' | 'markdown' | 'dashboard'

        Returns:
            报告内容字符串
        """
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
    def _format_analysis_body(analysis: dict) -> str:
        lines = ['# 八字命理分析报告', '']
        v = analysis.get('validation', {})
        lines.append(f"**八字**: {v.get('bazi', '')}")
        lines.append(f"**日主**: {v.get('day_master', '')}")
        lines.append('')
        lines.append('## 古籍检索结果')
        for r in analysis.get('retrieval', {}).get('results', []):
            lines.append(f"- [{r['id']}] ({r.get('source', '')}) {r.get('content', '')[:100]}")
        return '\n'.join(lines)
