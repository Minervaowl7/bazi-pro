#!/usr/bin/env python3
"""Thin wrapper — delegates to bazi_pro.hybrid_search.main()"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bazi_pro.hybrid_search import main

if __name__ == "__main__":
    main()
