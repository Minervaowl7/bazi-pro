"""评测系统配置"""
import os
from pathlib import Path

BENCHMARKS_DIR = Path(__file__).parent
DATA_DIR = BENCHMARKS_DIR / "data"
BAZIQA_DIR = DATA_DIR / "baziqa"
MINGLI_DIR = DATA_DIR / "mingli"
RESULTS_DIR = BENCHMARKS_DIR / "results"

API_BASE = os.environ.get("BAZI_API_BASE", "http://127.0.0.1:8711")
API_KEY = os.environ.get("BAZI_API_KEY", "")

BAZIQA_URLS = [
    "https://raw.githubusercontent.com/ChenJiangxi/BaziQA/main/data/contest8_2021.json",
    "https://raw.githubusercontent.com/ChenJiangxi/BaziQA/main/data/contest8_2022.json",
    "https://raw.githubusercontent.com/ChenJiangxi/BaziQA/main/data/contest8_2023.json",
    "https://raw.githubusercontent.com/ChenJiangxi/BaziQA/main/data/contest8_2024.json",
    "https://raw.githubusercontent.com/ChenJiangxi/BaziQA/main/data/contest8_2025.json",
    "https://raw.githubusercontent.com/ChenJiangxi/BaziQA/main/data/celebrity50_zh.json",
]

MINGLI_URL = "https://raw.githubusercontent.com/DestinyLinker/MingLi-Bench/main/data/data.json"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
