#!/usr/bin/env python3
"""
八字命理古籍检索脚本 v4.1
- BM25 + jieba 分词检索（2964条，6部经典，约29.8万字）
- 索引缓存：首次构建后持久化到 .cache/，后续检索毫秒级
- 批量检索：--batch 一次传入多个 query，复用同一索引
- 性能输出：--json 模式下返回 cache_hit / latency_ms

用法:
  python3 retrieve_classical.py <查询字符串> [-k 返回条数] [--json]
  python3 retrieve_classical.py --batch "query1" "query2" "query3" -k 5 --json
  python3 retrieve_classical.py --stats
  python3 retrieve_classical.py --cache-info
"""

import sys
import re
import os
import json
import math
import time
import hashlib
import pickle
from collections import Counter


# ---------- Cache ----------

def _cache_dir():
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".cache")
    os.makedirs(d, exist_ok=True)
    return d


def _corpus_hash(corpus_path: str) -> str:
    stat = os.stat(corpus_path)
    raw = f"{corpus_path}:{stat.st_mtime}:{stat.st_size}".encode()
    return hashlib.md5(raw).hexdigest()[:12]


def _cache_path(corpus_path: str) -> str:
    return os.path.join(_cache_dir(), f"bm25_{_corpus_hash(corpus_path)}.pkl")


# ---------- Corpus loader ----------

def load_corpus(corpus_path: str) -> list[dict]:
    entries = []
    with open(corpus_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("##"):
                continue
            m = re.match(r'\[(\w+)\]\s*@(\S+)\s*@(.+?)\s*##\s*(.*)', line)
            if m:
                entries.append({
                    "id": m.group(1),
                    "topic": m.group(2),
                    "source": m.group(3),
                    "content": m.group(4)
                })
    return entries


# ---------- Tokenizer ----------

try:
    import jieba
    _HAS_JIEBA = True
except ImportError:
    _HAS_JIEBA = False


def tokenize(text: str) -> list[str]:
    if _HAS_JIEBA:
        tokens = jieba.lcut(text)
    else:
        print("[FATAL] jieba not installed. pip install jieba", file=sys.stderr)
        sys.exit(1)
    return [t.strip() for t in tokens if t.strip() and len(t.strip()) >= 1]


# ---------- BM25 ----------

class BM25:
    """BM25 Okapi with pickle support"""
    def __init__(self, corpus: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.corpus = corpus
        self.N = len(corpus)
        self.k1 = k1
        self.b = b
        self.avgdl = sum(len(doc) for doc in corpus) / max(1, self.N)
        self.df = Counter()
        for doc in corpus:
            for term in set(doc):
                self.df[term] += 1
        self.idf = {}
        for term, freq in self.df.items():
            self.idf[term] = math.log((self.N - freq + 0.5) / (freq + 0.5) + 1.0)

    def score(self, query: list[str], doc: list[str]) -> float:
        score_val = 0.0
        doc_len = len(doc)
        tf = Counter(doc)
        for term in query:
            if term not in self.idf:
                continue
            term_tf = tf.get(term, 0)
            numerator = term_tf * (self.k1 + 1)
            denominator = term_tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
            score_val += self.idf[term] * numerator / denominator
        return score_val

    def get_top_n(self, query: list[str], n: int = 5) -> list[tuple[int, float]]:
        scores = [(i, self.score(query, doc)) for i, doc in enumerate(self.corpus)]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:n]


# ---------- Query helpers ----------

def build_query(entry: dict) -> list[str]:
    return tokenize(f"{entry['topic']} {entry['content']} {entry['source']}")


def extract_query(features: str) -> list[str]:
    return tokenize(features)


# ---------- Cached BM25 ----------

def get_bm25(corpus_path: str, entries: list[dict],
             force_rebuild: bool = False) -> tuple[BM25, bool]:
    """获取 BM25 索引，返回 (bm25, cache_hit)"""
    cache_file = _cache_path(corpus_path)

    if not force_rebuild and os.path.exists(cache_file):
        try:
            with open(cache_file, "rb") as f:
                bm25 = pickle.load(f)
            if bm25.N == len(entries):
                return bm25, True
        except Exception:
            pass

    tokenized = [build_query(e) for e in entries]
    bm25 = BM25(tokenized)
    try:
        with open(cache_file, "wb") as f:
            pickle.dump(bm25, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        print(f"[WARN] cache write failed: {e}", file=sys.stderr)
    return bm25, False


# ---------- Core API ----------

def retrieve(corpus_path: str, query_str: str, k: int = 8,
             force_rebuild: bool = False) -> dict:
    """检索 + 性能元数据，返回 {results, cache_hit, latency_ms}"""
    t0 = time.time()
    if not os.path.isfile(corpus_path):
        raise FileNotFoundError(f"Corpus not found: {corpus_path}")
    entries = load_corpus(corpus_path)
    if not entries:
        return {"results": [], "cache_hit": False, "latency_ms": 0, "corpus_size": 0}

    bm25, cache_hit = get_bm25(corpus_path, entries, force_rebuild=force_rebuild)
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

    latency = round((time.time() - t0) * 1000)
    return {
        "mode": "bm25_cached" if cache_hit else "bm25_cold",
        "cache": "hit" if cache_hit else "miss",
        "latency_ms": latency,
        "corpus_size": len(entries),
        "results": results
    }


def retrieve_batch(corpus_path: str, queries: list[str], k: int = 8,
                   force_rebuild: bool = False) -> dict:
    """批量检索：一次加载索引，N 个 query 复用"""
    t0 = time.time()
    if not os.path.isfile(corpus_path):
        raise FileNotFoundError(f"Corpus not found: {corpus_path}")
    entries = load_corpus(corpus_path)
    if not entries:
        return {"results": [], "cache_hit": False, "latency_ms": 0, "corpus_size": 0}

    bm25, cache_hit = get_bm25(corpus_path, entries, force_rebuild=force_rebuild)

    all_results = []
    for q in queries:
        query_tokens = extract_query(q)
        top_n = bm25.get_top_n(query_tokens, n=min(k, len(entries)))
        q_results = []
        for idx, score in top_n:
            e = entries[idx]
            q_results.append({
                "score": round(score, 4),
                "id": e["id"],
                "topic": e["topic"],
                "source": e["source"],
                "content": e["content"]
            })
        all_results.append({"query": q, "results": q_results})

    latency = round((time.time() - t0) * 1000)
    return {
        "mode": "bm25_batch_cached" if cache_hit else "bm25_batch_cold",
        "cache": "hit" if cache_hit else "miss",
        "latency_ms": latency,
        "corpus_size": len(entries),
        "queries": all_results
    }


# ---------- resolve corpus ----------

def _resolve_corpus() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for candidate in [
        os.path.join(script_dir, "..", "references", "classical_corpus.md"),
        os.path.join(os.environ.get("SKILL_DIR", ""), "references", "classical_corpus.md"),
        os.path.join(os.path.expanduser("~"), ".hermes", "skills", "bazi-pro", "references", "classical_corpus.md"),
    ]:
        if os.path.exists(candidate):
            return candidate
    return os.path.join(script_dir, "..", "references", "classical_corpus.md")


# ---------- main (for CLI + pyproject entry point) ----------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="八字古籍检索 (BM25 + jieba) v4.1")
    parser.add_argument("query", nargs="*", default=[], help="检索查询")
    parser.add_argument("-k", type=int, default=8, help="返回条数")
    parser.add_argument("--corpus", default=_resolve_corpus(), help="语料库路径")
    parser.add_argument("--json", action="store_true", help="JSON 输出（含性能元数据）")
    parser.add_argument("--batch", action="store_true", help="批量模式：每个位置参数视为独立 query")
    parser.add_argument("--rebuild", action="store_true", help="强制重建索引缓存")
    parser.add_argument("--stats", action="store_true", help="语料库统计")
    parser.add_argument("--cache-info", action="store_true", help="缓存信息")
    args = parser.parse_args()

    if args.stats:
        entries = load_corpus(args.corpus)
        topics = Counter(e['topic'] for e in entries)
        print(f"语料库: {args.corpus}\n总条数: {len(entries)}\n主题分布:")
        for t, c in topics.most_common():
            print(f"  {t}: {c}")
        return

    if args.cache_info:
        cf = _cache_path(args.corpus)
        if os.path.exists(cf):
            print(f"缓存: {cf}\n大小: {os.path.getsize(cf)/1024:.1f} KB")
        else:
            print("缓存不存在，首次检索时构建")
        return

    if not args.query:
        print("用法: retrieve_classical.py '<查询>' [-k 8] [--json] [--batch] [--stats] [--cache-info]")
        return

    if args.batch:
        out = retrieve_batch(args.corpus, args.query, args.k, force_rebuild=args.rebuild)
    else:
        out = retrieve(args.corpus, args.query[0], args.k, force_rebuild=args.rebuild)
        # Wrap single query in batch format for consistent JSON
        out = {
            "mode": out["mode"],
            "cache": out["cache"],
            "latency_ms": out["latency_ms"],
            "corpus_size": out["corpus_size"],
            "queries": [{"query": args.query[0], "results": out["results"]}]
        }

    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"[{out['mode']}] cache={out['cache']} latency={out['latency_ms']}ms corpus={out['corpus_size']}")
        for q in out["queries"]:
            if len(out["queries"]) > 1:
                print(f"\n--- {q['query']} ---")
            if not q["results"]:
                print("  (未命中)")
            for r in q["results"]:
                print(f"  [{r['id']}] ({r['score']:.4f}) @{r['topic']} —《{r['source']}》")
                print(f"    {r['content']}")


if __name__ == "__main__":
    main()
