"""数据集下载器"""
import urllib.request
from pathlib import Path

from benchmarks.config import BAZIQA_DIR, BAZIQA_URLS, MINGLI_DIR, MINGLI_URL


def download_file(url: str, dest: Path) -> bool:
    if dest.exists():
        print(f"  已存在: {dest.name}")
        return False
    print(f"  下载: {url}")
    try:
        urllib.request.urlretrieve(url, str(dest))
        print(f"  完成: {dest.name}")
        return True
    except Exception as e:
        print(f"  失败: {e}")
        return False


def download_baziqa():
    print("=== 下载 BaziQA 数据集 ===")
    BAZIQA_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for url in BAZIQA_URLS:
        filename = url.split("/")[-1]
        dest = BAZIQA_DIR / filename
        if download_file(url, dest):
            count += 1
    print(f"BaziQA: 新下载 {count} 个文件\n")


def download_mingli():
    print("=== 下载 MingLi-Bench 数据集 ===")
    MINGLI_DIR.mkdir(parents=True, exist_ok=True)
    dest = MINGLI_DIR / "data.json"
    download_file(MINGLI_URL, dest)
    fortune_url = "https://raw.githubusercontent.com/DestinyLinker/MingLi-Bench/main/data/fortune_api_results.json"
    download_file(fortune_url, MINGLI_DIR / "fortune_api_results.json")
    print()


def download_all():
    download_baziqa()
    download_mingli()
    print("全部下载完成!")


if __name__ == "__main__":
    download_all()
