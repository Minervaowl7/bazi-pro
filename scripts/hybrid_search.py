#!/usr/bin/env python3
"""
Hybrid Search 骨架 v4.0
BM25 + 向量检索 + 经典权威权重 + 主题匹配 → 融合排序

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
        self.vector_index = faiss.IndexFlatIP(dim)
        self.vector_index.add(self.embeddings.astype(np.float32))

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
        for idx, score in fused[:k]:
            e = self.entries[idx]
            # Matched terms
            entry_text = f"{e['topic']} {e['content']}"
            query_terms = query_str.split()
            matched = [t for t in query_terms if t in entry_text]
            results.append({
                "score": round(score, 4),
                "id": e["id"],
                "topic": e["topic"],
                "source": e["source"],
                "content": e["content"],
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
        from retrieve_classical import extract_query
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


if __name__ == "__main__":
    print(f"Hybrid Search 可用: {_HYBRID_READY}")
    print(f"  numpy: {_HAS_NUMPY}")
    print(f"  sentence-transformers: {_HAS_EMBED}")
    print(f"  faiss: {_HAS_FAISS}")
    if not _HYBRID_READY:
        print("  安装: pip install sentence-transformers faiss-cpu numpy")
