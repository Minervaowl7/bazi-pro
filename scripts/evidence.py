#!/usr/bin/env python3
"""Thin wrapper — delegates to bazi_pro.evidence"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bazi_pro.evidence import main

if __name__ == "__main__":
    sys.exit(main())
