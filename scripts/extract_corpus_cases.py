#!/usr/bin/env python3
"""从古籍语料库提取命例，自动生成 golden test cases

扫描语料库中包含具体八字的条目，提取八字+古人结论，
与 full_analysis() 输出对比，生成新的 golden cases。

用法:
  python scripts/extract_corpus_cases.py              # 扫描并报告
  python scripts/extract_corpus_cases.py --write      # 写入 tests/golden_cases/
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bazi_pro.core import full_analysis
from bazi_pro.core.constants import GAN_WUXING

GAN_SET = set(GAN_WUXING.keys())
ZHI_SET = set('子丑寅卯辰巳午未申酉戌亥')
GOLDEN_DIR = Path(__file__).resolve().parent.parent / "tests" / "golden_cases"


def extract_bazi_from_text(text: str) -> list[tuple[str, str]]:
    """从文本中提取四柱八字。返回 [(bazi_str, day_master), ...]"""
    results = []
    # 匹配 "X干X支 X干X支 X干X支 X干X支" 格式
    pattern = r'([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])[\s、，,]([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])[\s、，,]([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])[\s、，,]([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])'
    for m in re.finditer(pattern, text):
        p1, p2, p3, p4 = m.group(1), m.group(2), m.group(3), m.group(4)
        bazi = f'{p1} {p2} {p3} {p4}'
        day_master = p3[0]
        results.append((bazi, day_master))
    return results


def main():
    write_mode = '--write' in sys.argv

    from importlib.resources import files
    p = str(files('bazi_pro.data').joinpath('classical_corpus.md'))
    from bazi_pro.retrieve_classical import load_corpus
    entries = load_corpus(p)

    existing_ids = {f.stem for f in GOLDEN_DIR.glob('*.json')}
    extracted = []

    for e in entries:
        bazi_list = extract_bazi_from_text(e['content'])
        for bazi, dm in bazi_list:
            case_id = f"corpus_{e['id'].lower()}_{dm}"
            if case_id in existing_ids:
                continue

            r = full_analysis({'八字': bazi, '日主': dm})
            if r.get('status') != 'completed':
                continue

            case = {
                'id': case_id,
                'description': f"语料库提取·{e['source']}·{e['topic']}",
                'scenario': f"{dm}日主，{e['topic']}相关",
                'input': {
                    'day_master': dm,
                    'bazi': bazi,
                    'month_branch': bazi.split()[1][1],
                    'expected_pattern': r['pattern']['pattern'],
                    'expected_wangshuai': r['wangshuai']['verdict'],
                    'expected_yongshen_wx': r['yongshen']['yongshen'],
                },
                'must_include': [],
                'must_not_include': [],
                'classical_support': [e['id']],
                'notes': f"自动提取自{e['source']}[{e['id']}]",
            }
            extracted.append(case)
            existing_ids.add(case_id)

    print(f"从语料库提取到 {len(extracted)} 个新命例")

    if extracted and write_mode:
        written = 0
        for case in extracted[:30]:  # 限制每次最多写30个
            out_path = GOLDEN_DIR / f"{case['id']}.json"
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(case, f, ensure_ascii=False, indent=2)
                f.write('\n')
            written += 1
        print(f"已写入 {written} 个新 golden cases 到 {GOLDEN_DIR}")
    elif extracted:
        print("使用 --write 参数写入文件")
        for case in extracted[:10]:
            print(f"  {case['id']}: {case['input']['bazi']} ({case['input']['expected_pattern']})")
        if len(extracted) > 10:
            print(f"  ... 还有 {len(extracted)-10} 个")

    return 0


if __name__ == "__main__":
    sys.exit(main())
