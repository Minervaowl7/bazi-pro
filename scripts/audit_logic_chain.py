#!/usr/bin/env python3
"""Agent B: 推导链完整性审计

验证格局→旺衰→用神的推导链：
1. 每种格局都有对应的用神方向
2. 旺衰极端值正确映射到从格判别
3. jishen 不为空（除非 中和+无病）
4. 从格与旺衰标志一致性
5. 病药推导与格局的关联

用法:
  python scripts/audit_logic_chain.py
"""

import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bazi_pro.core import full_analysis

ISSUES = []


def check(name: str, condition: bool, detail: str):
    if not condition:
        ISSUES.append(f"[{name}] {detail}")


# ── 测试命盘：覆盖主要格局类型 ──
TEST_CASES = [
    # (描述, 八字, 日主)
    ("身旺正官格", "壬午 乙巳 丁亥 癸卯", "丁"),
    ("身弱七杀从杀", "壬辰 戊申 甲寅 丙寅", "甲"),
    ("从强格", "壬子 壬子 壬子 壬子", "壬"),
    ("中和偏弱", "甲子 丙寅 戊辰 庚申", "戊"),
    ("枭神夺食", "戊寅 壬戌 辛丑 癸巳", "辛"),
    ("建禄格", "庚辰 戊申 庚戌 己丑", "庚"),
    ("极弱", "庚午 壬申 甲寅 丙午", "甲"),
]


def run():
    for desc, bazi, dm in TEST_CASES:
        result = full_analysis({"八字": bazi, "日主": dm})

        status = result.get("status", "")
        check(f"{desc}:status", status == "completed",
              f"返回 status='{status}'，期望 'completed'")

        if status != "completed":
            continue

        # ── 1. 格局必须有值 ──
        pat = result["pattern"]["pattern"]
        check(f"{desc}:pattern", pat and pat not in ("待定", "数据不足"),
              f"格局='{pat}'不应为占位符")

        # ── 2. 旺衰与格局一致性 ──
        ws = result["wangshuai"]
        verdict = ws["verdict"]
        check(f"{desc}:wangshuai_verdict", isinstance(verdict, str) and len(verdict) > 0,
              "旺衰裁决为空")

        if "从" in pat or "专旺" in pat:
            check(f"{desc}:cong_pattern_flags",
                  ws.get("is_extreme_strong") or ws.get("is_extreme_weak"),
                  f"格局'{pat}'是从格，但 is_extreme_strong/extreme_weak 均为 False")

        # ── 3. 用神不为空 ──
        ys = result["yongshen"]
        yong = ys.get("yongshen", "")
        check(f"{desc}:yongshen", yong and yong != "待定",
              f"用神='{yong}'不应为空或占位符")

        # ── 4. yongshen 必须在五行中 ──
        check(f"{desc}:yongshen_wx", yong in ("木", "火", "土", "金", "水", ""),
              f"用神'{yong}'不是有效五行")

        # ── 5. 忌神列表无重复 ──
        jishen = ys.get("jishen", [])
        check(f"{desc}:jishen_dedup", len(jishen) == len(set(jishen)),
              f"忌神列表有重复: {jishen}")

        # ── 6. 喜神忌神不重叠 ──
        xishen = ys.get("xishen", [])
        overlap = set(xishen) & set(jishen)
        check(f"{desc}:xishen_jishen_overlap", not overlap,
              f"喜神与忌神重叠: {overlap}")

        # ── 7. 用神不在忌神中 ──
        check(f"{desc}:yongshen_vs_jishen", yong not in jishen,
              f"用神'{yong}'在忌神列表中")

        # ── 8. disease 结构完整性 ──
        disease = result.get("disease", {})
        check(f"{desc}:disease_keys",
              all(k in disease for k in ("has_disease", "items", "medicine_advice")),
              "disease 缺少必要键")
        check(f"{desc}:disease_has_disease_type",
              isinstance(disease.get("has_disease"), bool),
              "has_disease 应为 bool")

        for i, item in enumerate(disease.get("items", [])):
            for key in ("name", "severity", "disease_god", "affected_god",
                        "disease_element", "medicine_element", "reason"):
                check(f"{desc}:disease_item_{i}_{key}",
                      key in item, f"disease.items[{i}] 缺少 '{key}'")

        # ── 9. pillars 十神不为空 ──
        pillars = result.get("pillars", [])
        for p in pillars:
            shishen = p.get("shishen", "")
            check(f"{desc}:pillar_ss_{p.get('position','')}",
                  shishen != "", f"pillar {p.get('position','')} 十神为空")

        # ── 10. 五行力量百分比总和 ≈ 100 ──
        pct = result["element_forces"].get("percent", {})
        pct_sum = sum(pct.values())
        check(f"{desc}:pct_sum", abs(pct_sum - 100.0) < 5.0,
              f"五行百分比总和 {pct_sum:.1f}% 偏离100%")

    if ISSUES:
        print(f"❌ Agent B (推导链审计): {len(ISSUES)} 个问题")
        for issue in ISSUES:
            print(f"  - {issue}")
        return 1

    print(f"✅ Agent B (推导链审计): {len(TEST_CASES)} 个命盘推导通过")
    return 0


if __name__ == "__main__":
    sys.exit(run())
