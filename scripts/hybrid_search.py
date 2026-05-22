#!/usr/bin/env python3
"""Thin wrapper — delegates to bazi_pro.hybrid_search"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bazi_pro.hybrid_search import _HYBRID_READY, _HAS_NUMPY, _HAS_EMBED, _HAS_FAISS
if __name__ == "__main__":
    print(f"Hybrid Search 可用: {_HYBRID_READY}")
    print(f"  numpy: {_HAS_NUMPY}")
    print(f"  sentence-transformers: {_HAS_EMBED}")
    print(f"  faiss: {_HAS_FAISS}")
    if not _HYBRID_READY:
        print("  安装: pip install sentence-transformers faiss-cpu numpy")
