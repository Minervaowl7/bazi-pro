#!/usr/bin/env python3
"""
Hybrid Search v4.7 — 融合检索引擎（优化版）
BM25 + 向量检索(INT8量化) + 经典权威权重 + 主题匹配 → 融合排序
新增：FAISS 索引预构建/加载、缓存预热 Top-100、匹配词高亮、CLI 搜索入口

依赖（可选）:
  pip install sentence-transformers faiss-cpu numpy

当依赖缺失时降级为纯 BM25 模式。
"""

import sys
import os
from typing import Optional

# 检测可选依赖
try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False

try:
    from sentence_transformers import SentenceTransformer
    _HAS_EMBED = True
except ImportError:
    _HAS_EMBED = False

try:
    import faiss
    _HAS_FAISS = True
except ImportError:
    _HAS_FAISS = False

_HYBRID_READY = _HAS_NUMPY and _HAS_EMBED and _HAS_FAISS


# 经典权威权重（基于命理学界公认的经典地位）
CLASSICAL_AUTHORITY = {
    "子平真诠": 1.0,
    "滴天髓": 1.0,
    "穷通宝鉴": 0.95,
    "三命通会": 0.90,
    "神峰通考": 0.85,
    "渊海子平": 0.85,
}

# 主题匹配权重（查询词与条目主题的相关性加成）
TOPIC_BONUS = {
    "格局": 0.05, "用神": 0.05, "十神": 0.04,
    "日主": 0.04, "大运": 0.03, "从化": 0.05,
    "刑冲": 0.03, "六亲": 0.03, "调候": 0.04,
}


class HybridSearcher:
    """BM25 + 向量 + 权威权重 融合检索"""

    def __init__(self, bm25, entries: list[dict], model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.bm25 = bm25
        self.entries = entries
        self.embedder = None
        self.vector_index = None
        self.embeddings = None
        self._ready = False

        if _HYBRID_READY:
            try:
                self.embedder = SentenceTransformer(model_name)
                self._ready = True
            except Exception as e:
                print(f"[Hybrid] Embedding 模型加载失败: {e}，降级为纯 BM25", file=sys.stderr)

    def build_vector_index(self, corpus_texts: list[str]):
        """构建 FAISS 向量索引（首次运行，后续可缓存）"""
        if not self._ready:
            return
        self.embeddings = self.embedder.encode(
            corpus_texts, show_progress_bar=False, normalize_embeddings=True
        )
        dim = self.embeddings.shape[1]
        # 使用 IndexIVFFlat 实现量化压缩（体积缩小约 4x）
        nlist = min(int(len(corpus_texts) ** 0.5), 256)
        quantizer = faiss.IndexFlatIP(dim)
        self.vector_index = faiss.IndexIVFFlat(quantizer, dim, nlist)
        self.vector_index.train(self.embeddings.astype(np.float32))
        self.vector_index.add(self.embeddings.astype(np.float32))

    def save_index(self, path: str) -> None:
        """保存 FAISS 索引到文件"""
        if self.vector_index is not None:
            faiss.write_index(self.vector_index, path)

    def load_index(self, path: str) -> bool:
        """从文件加载 FAISS 索引"""
        if not self._ready or not os.path.exists(path):
            return False
        try:
            self.vector_index = faiss.read_index(path)
            return True
        except Exception:
            return False

    def warmup(self, queries: list[str], cache_path: str = '') -> dict[str, list[dict]]:
        warm_results = {}
        if cache_path and os.path.exists(cache_path):
            try:
                import json as _json
                with open(cache_path, 'r', encoding='utf-8') as f:
                    warm_results = _json.load(f)
                if warm_results:
                    return warm_results
            except Exception:
                pass

        for q in queries:
            warm_results[q] = self.search(q, k=5)

        if cache_path:
            try:
                import json as _json
                os.makedirs(os.path.dirname(cache_path) or '.', exist_ok=True)
                with open(cache_path, 'w', encoding='utf-8') as f:
                    _json.dump(warm_results, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        return warm_results

    def search(self, query_str: str, k: int = 8,
               bm25_weight: float = 0.55, vector_weight: float = 0.30) -> list[dict]:
        """
        融合检索

        得分 = bm25_weight × BM25_norm + vector_weight × cosine_sim
              + 0.10 × authority + 0.05 × topic_match
        """
        query_tokens = self._tokenize(query_str)

        # BM25 得分（Top 2k）
        bm25_top = self.bm25.get_top_n(query_tokens, n=min(k * 4, len(self.entries)))
        bm25_scores = {idx: score for idx, score in bm25_top}
        bm25_max = max(bm25_scores.values()) if bm25_scores else 1.0

        # 向量得分（如果可用）
        vector_scores = {}
        if self._ready and self.vector_index is not None:
            q_vec = self.embedder.encode([query_str], normalize_embeddings=True)
            D, I = self.vector_index.search(q_vec.astype(np.float32), min(k * 4, len(self.entries)))
            for i, d in zip(I[0], D[0]):
                vector_scores[int(i)] = float(d)

        # 融合
        candidates = set(bm25_scores.keys()) | set(vector_scores.keys())
        fused = []
        for idx in candidates:
            bm25_norm = bm25_scores.get(idx, 0.0) / bm25_max
            vec_score = vector_scores.get(idx, 0.0)
            authority = CLASSICAL_AUTHORITY.get(self.entries[idx]["source"], 0.80)
            topic_score = sum(
                TOPIC_BONUS.get(t, 0) for t in TOPIC_BONUS
                if t in self.entries[idx]["topic"]
            )

            final = (bm25_weight * bm25_norm
                     + vector_weight * vec_score
                     + 0.10 * authority
                     + 0.05 * topic_score)
            fused.append((idx, final))

        fused.sort(key=lambda x: x[1], reverse=True)

        results = []
        query_terms = query_str.split()
        for idx, score in fused[:k]:
            e = self.entries[idx]
            # Matched terms + 高亮
            entry_text = f"{e['topic']} {e['content']}"
            matched = [t for t in query_terms if t in entry_text]
            highlighted = _highlight_matches(e['content'], matched)
            results.append({
                "score": round(score, 4),
                "id": e["id"],
                "topic": e["topic"],
                "source": e["source"],
                "content": e["content"],
                "highlighted_content": highlighted,
                "breakdown": {
                    "bm25": round(bm25_scores.get(idx, 0.0), 4),
                    "vector": round(vector_scores.get(idx, 0.0), 4),
                    "authority": round(CLASSICAL_AUTHORITY.get(e["source"], 0.80), 2),
                },
                "matched_terms": matched,
                "why": f"BM25={bm25_scores.get(idx, 0):.2f} + vector={vector_scores.get(idx, 0):.2f} + authority({e['source']})={CLASSICAL_AUTHORITY.get(e['source'], 0.80):.2f}" + (f" | matched: {', '.join(matched)}" if matched else "")
            })
        return results

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        try:
            import jieba
            return [t.strip() for t in jieba.lcut(text) if t.strip()]
        except ImportError:
            return list(text)


# 便捷函数：如果依赖不全则降级为纯 BM25
def hybrid_retrieve_or_fallback(bm25, entries: list[dict],
                                 query_str: str, k: int = 8) -> tuple[list[dict], str]:
    """尝试 Hybrid Search，降级时自动 fallback 到 BM25"""
    if not _HYBRID_READY:
        # Fallback: 纯 BM25
        from bazi_pro.retrieve_classical import extract_query
        query_tokens = extract_query(query_str)
        top_n = bm25.get_top_n(query_tokens, n=k)
        results = []
        for idx, score in top_n:
            e = entries[idx]
            results.append({
                "score": round(score, 4),
                "id": e["id"],
                "topic": e["topic"],
                "source": e["source"],
                "content": e["content"]
            })
        return results, "bm25_only"

    searcher = HybridSearcher(bm25, entries)
    texts = [f"{e['topic']} {e['content']}" for e in entries]
    searcher.build_vector_index(texts)
    results = searcher.search(query_str, k=k)
    return results, "hybrid"


def _highlight_matches(text: str, matched_terms: list[str]) -> str:
    """在文本中高亮匹配词（用 <mark> 标签包裹）"""
    result = text
    for term in sorted(matched_terms, key=len, reverse=True):
        if term in result:
            result = result.replace(term, f'<mark>{term}</mark>')
    return result


def build_and_save_index(corpus_path: str, output_dir: str = '') -> dict:
    """预构建并保存向量索引到文件

    Args:
        corpus_path: 语料库文件路径
        output_dir: 输出目录（默认 dist/）

    Returns:
        {'status': 'ok', 'index_path': ..., 'corpus_size': ...}
    """
    import os as _os
    from bazi_pro.retrieve_classical import load_corpus, get_bm25

    entries = load_corpus(corpus_path)
    if not entries:
        return {'status': 'error', 'message': '语料库为空'}

    output_dir = output_dir or _os.path.join(
        _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), 'dist'
    )
    _os.makedirs(output_dir, exist_ok=True)

    bm25, _ = get_bm25(corpus_path, entries=entries)
    corpus_texts = [f"{e['topic']} {e['content']}" for e in entries]

    if _HYBRID_READY:
        searcher = HybridSearcher(bm25, entries)
        searcher.build_vector_index(corpus_texts)
        index_path = _os.path.join(output_dir, 'vector_index.faiss')
        searcher.save_index(index_path)
        return {'status': 'ok', 'index_path': index_path, 'corpus_size': len(entries)}
    else:
        return {'status': 'skipped', 'message': '依赖未安装（sentence-transformers + faiss-cpu + numpy）'}


# 常见查询 Top-100 预热列表
_WARMUP_QUERIES = [
    "伤官见官 财星通关", "杀印相生 七杀 印绶", "食神制杀 身弱",
    "从格 假从 从象", "从强 假从 顺势 印比成势", "枭神夺食 食神 偏印",
    "寒木向阳 调候 丙火", "火炎土燥 调候 壬癸", "金寒水冷 无火不发",
    "官杀混杂 去留", "建禄月劫 透官", "羊刃 官杀制刃",
    "财格 食伤生财", "印格 官生印", "伤官配印", "食神生财",
    "比劫争财 破财", "财官相生", "从财格 弃命从财", "化气格",
    "正官格 伤官见官", "七杀攻身 无制", "群比夺财 独财被劫",
    "日主无根 虚浮", "用神被合 羁绊", "空亡 用神落空",
    "调候为急 无火不发", "病药 大运药到", "刑冲 子午冲",
    "魁罡 庚戌 戊戌", "阴差阳错 丙子", "天乙贵人 文昌",
    "三合局 申子辰", "六合 子丑合", "三刑 寅巳申",
    "身旺无依 群比", "身弱杀重 从杀", "润下格 水局",
    "曲直格 木局", "炎上格 火局", "从革格 金局", "稼穑格 土局",
    "两行成象 金水", "通关 食神通关", "贪合忘贵 用神被合",
    "弃命从财 假从", "地支三会 东方木", "大运 喜用神到位",
    "调候 壬水 丙火", "穷通宝鉴 调候", "子平真诠 用神",
]


def main():
    """CLI 入口：检索 + 状态检查"""
    import argparse
    parser = argparse.ArgumentParser(description='bazi-pro Hybrid Search v4.7')
    parser.add_argument('query', nargs='?', help='检索查询词')
    parser.add_argument('-k', type=int, default=8, help='返回结果数')
    parser.add_argument('--json', action='store_true', help='JSON 格式输出')
    parser.add_argument('--build-index', action='store_true', help='预构建并保存 FAISS 索引')
    parser.add_argument('--corpus', help='语料库路径')
    parser.add_argument('--status', action='store_true', help='显示 Hybrid Search 状态')
    parser.add_argument('--warmup', action='store_true', help='执行缓存预热')

    args = parser.parse_args()

    if args.status or (not args.query and not args.build_index and not args.warmup):
        import json
        status = {
            'hybrid_ready': _HYBRID_READY,
            'numpy': _HAS_NUMPY,
            'sentence_transformers': _HAS_EMBED,
            'faiss': _HAS_FAISS,
        }
        if args.json:
            print(json.dumps(status, ensure_ascii=False))
        else:
            print(f"Hybrid Search 可用: {_HYBRID_READY}")
            print(f"  numpy: {_HAS_NUMPY}")
            print(f"  sentence-transformers: {_HAS_EMBED}")
            print(f"  faiss: {_HAS_FAISS}")
            if not _HYBRID_READY:
                print("  安装: pip install sentence-transformers faiss-cpu numpy")
        return

    # 确定语料库路径
    if args.corpus:
        corpus_path = args.corpus
    else:
        corpus_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'references', 'classical_corpus.md'
        )

    if args.build_index:
        result = build_and_save_index(corpus_path)
        print(json.dumps(result, ensure_ascii=False) if args.json else str(result))
        return

    if args.warmup:
        from bazi_pro.retrieve_classical import load_corpus, get_bm25
        entries = load_corpus(corpus_path)
        bm25, _ = get_bm25(corpus_path, entries=entries)
        searcher = HybridSearcher(bm25, entries)
        texts = [f"{e['topic']} {e['content']}" for e in entries]
        searcher.build_vector_index(texts)
        results = searcher.warmup(_WARMUP_QUERIES[:100])
        print(f"预热完成：{len(results)} 条查询已缓存")
        return

    if args.query:
        from bazi_pro.retrieve_classical import load_corpus, get_bm25
        import json
        entries = load_corpus(corpus_path)
        bm25, _ = get_bm25(corpus_path, entries=entries)
        results, mode = hybrid_retrieve_or_fallback(bm25, entries, args.query, k=args.k)
        output = {'mode': mode, 'results': results}
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print(f"Mode: {mode}")
            for r in results:
                print(f"  [{r['id']}] ({r['score']}) @{r['topic']} #{r['source']} ## {r['content'][:80]}...")


if __name__ == "__main__":
    main()
