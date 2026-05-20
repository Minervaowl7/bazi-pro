#!/usr/bin/env python3
"""
八字命理古籍检索脚本
用法: python3 retrieve_classical.py <查询字符串> [-k 返回条数] [--corpus 语料库路径]
     python3 retrieve_classical.py "正官格 伤官 甲木身弱" -k 5
     python3 retrieve_classical.py --extract 正文文本
"""

import sys
import re
import os
import json
import math
from collections import Counter


def load_corpus(corpus_path: str) -> list[dict]:
    """加载语料库文件，解析每条记录为 {id, topic, source, content}"""
    entries = []
    with open(corpus_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("##"):
                continue
            # Format: [ID] @topic @source ## content
            m = re.match(r'\[(\w+)\]\s*@(\S+)\s*@(.+?)\s*##\s*(.*)', line)
            if m:
                entries.append({
                    "id": m.group(1),
                    "topic": m.group(2),
                    "source": m.group(3),
                    "content": m.group(4)
                })
    return entries


# ---------- 简易 jieba 替代：基于前缀词典的最大概率分词 ----------
# 不用 jieba 是为了零依赖也能跑。如果 jieba 可用则优先使用。

try:
    import jieba
    _HAS_JIEBA = True
except ImportError:
    _HAS_JIEBA = False


def tokenize(text: str) -> list[str]:
    """中文分词"""
    if _HAS_JIEBA:
        tokens = jieba.lcut(text)
    else:
        import sys
        print("[FATAL] jieba not installed. BM25 Chinese word segmentation requires jieba. n-gram fallback produces significantly degraded results (recall/precision drop >50%) and is not acceptable for production use. Install with: pip install jieba", file=sys.stderr)
        sys.exit(1)
    return [t.strip() for t in tokens if t.strip() and len(t.strip()) >= 1]


# ---------- BM25 ----------

class BM25:
    """BM25 Okapi 算法的纯 Python 实现"""
    def __init__(self, corpus: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.corpus = corpus
        self.N = len(corpus)
        self.k1 = k1
        self.b = b
        self.avgdl = sum(len(doc) for doc in corpus) / max(1, self.N)
        # DF: document frequency
        self.df = Counter()
        for doc in corpus:
            for term in set(doc):
                self.df[term] += 1
        self.idf = {}
        for term, freq in self.df.items():
            self.idf[term] = math.log((self.N - freq + 0.5) / (freq + 0.5) + 1.0)

    def score(self, query: list[str], doc: list[str]) -> float:
        score = 0.0
        doc_len = len(doc)
        tf = Counter(doc)
        for term in query:
            if term not in self.idf:
                continue
            idf = self.idf[term]
            term_tf = tf.get(term, 0)
            numerator = term_tf * (self.k1 + 1)
            denominator = term_tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
            score += idf * numerator / denominator
        return score

    def get_top_n(self, query: list[str], n: int = 5) -> list[tuple[int, float]]:
        scores = [(i, self.score(query, doc)) for i, doc in enumerate(self.corpus)]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:n]


# ---------- 查询构建 ----------

def build_query(entry: dict) -> list[str]:
    """将语料条目转为用于索引的 token 列表（搜索内容 + 主题 + 出处）"""
    text = f"{entry['topic']} {entry['content']} {entry['source']}"
    return tokenize(text)


def extract_query(features: str) -> list[str]:
    """从八字特征描述字符串中提取查询 token"""
    # features 如: "正官格 伤官见官 甲木 身弱 丙火调候"
    return tokenize(features)


def retrieve(corpus_path: str, query_str: str, k: int = 8) -> list[dict]:
    """核心检索函数：返回 top-K 条匹配的古籍条文"""
    if not os.path.isfile(corpus_path):
        raise FileNotFoundError(f"语料库文件不存在: {corpus_path}。请检查路径是否正确，或使用 --corpus 参数指定。")
    entries = load_corpus(corpus_path)
    if not entries:
        return []

    # 构建索引
    tokenized_corpus = [build_query(e) for e in entries]
    bm25 = BM25(tokenized_corpus)

    # 查询
    query_tokens = extract_query(query_str)
    top_n = bm25.get_top_n(query_tokens, n=min(k, len(entries)))

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
    return results


# ---------- CLI ----------

if __name__ == "__main__":
    # 确定语料库路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_corpus = os.path.join(script_dir, "..", "references", "classical_corpus.md")
    if not os.path.exists(default_corpus):
        # 检查 SKILL_DIR 环境变量
        skill_dir_env = os.environ.get("SKILL_DIR")
        if skill_dir_env:
            default_corpus = os.path.join(skill_dir_env, "references", "classical_corpus.md")
    if not os.path.exists(default_corpus):
        # 最后尝试 ~/.hermes 路径
        skill_dir = os.path.join(os.path.expanduser("~"), ".hermes", "skills", "bazi-pro")
        default_corpus = os.path.join(skill_dir, "references", "classical_corpus.md")

    import argparse
    parser = argparse.ArgumentParser(description="八字古籍检索 (BM25 + jieba)")
    parser.add_argument("query", nargs="?", default="", help="检索查询（八字特征描述）")
    parser.add_argument("-k", type=int, default=8, help="返回条数（默认 8）")
    parser.add_argument("--corpus", default=default_corpus, help=f"语料库路径（默认 {default_corpus}）")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--stats", action="store_true", help="显示语料库统计")
    args = parser.parse_args()

    if args.stats:
        entries = load_corpus(args.corpus)
        print(f"语料库: {args.corpus}")
        print(f"总条数: {len(entries)}")
        topics = Counter(e['topic'] for e in entries)
        print("主题分布:")
        for t, c in topics.most_common():
            print(f"  {t}: {c}")
        sys.exit(0)

    if not args.query:
        print("用法: python3 retrieve_classical.py '<八字特征查询>' [-k 返回条数] [--json]")
        print("示例: python3 retrieve_classical.py '正官格 伤官见官 甲木 身弱' -k 5")
        sys.exit(1)

    results = retrieve(args.corpus, args.query, args.k)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        if not results:
            print("(未检索到匹配条文)")
        else:
            for r in results:
                print(f"[{r['id']}] ({r['score']:.4f}) @{r['topic']}")
                print(f"    {r['content']}")
                print(f"    ——《{r['source']}》")
                print()
