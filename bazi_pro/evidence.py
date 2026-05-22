#!/usr/bin/env python3
"""
命理分析证据链对象 v4.2
将八字分析的结构化结论输出为 JSON Evidence Object，支持：
- 每个 claim 附带古籍依据（classical citation ID）
- 置信度评分
- 反事实证据（counter-evidence）
- 决策依据（basis: MCP字段 + 古籍 + 规则）
"""

import json
import sys
from typing import Optional


def new_evidence(
    claim: str,
    confidence: float,
    basis_mcp: list[str],
    basis_classics: list[str],
    basis_rules: list[str],
    counter_evidence: Optional[list[str]] = None,
    final_decision: str = ""
) -> dict:
    """创建一个证据链对象"""
    return {
        "claim": claim,
        "confidence": round(confidence, 2),
        "basis": {
            "mcp_fields": basis_mcp,
            "classics": basis_classics,
            "rules": basis_rules
        },
        "counter_evidence": counter_evidence or [],
        "final_decision": final_decision
    }


def build_analysis_evidence(
    # 基本信息
    day_master: str,
    gender: str,
    bazi: str,
    # 旺衰
    deling_score: int,
    dedi_score: float,
    deshi_score: float,
    wangshuai: str,
    # 格局
    pattern_name: str,
    pattern_score: int,
    pattern_tier: str,
    # 喜用神
    yongshen: str,
    xishen: str,
    jishen: str,
    # 古籍引用（来自 retrieve_classical.py 输出）
    classical_refs: list[dict],
    # 关键结构特征
    key_features: list[str],
    # 大运吉凶分布
    dayun_summary: list[dict],
) -> dict:
    """构建完整的分析证据链对象"""
    evidence_chain = []

    # E1: 日主旺衰
    evidence_chain.append(new_evidence(
        claim=f"日主{day_master}，{wangshuai}",
        confidence=_wangshuai_confidence(deling_score, dedi_score, deshi_score),
        basis_mcp=["dayMaster", "monthBranch"],
        basis_classics=_find_classical_ids(classical_refs, "旺衰"),
        basis_rules=[f"得令={deling_score}", f"得地={dedi_score}", f"得势={deshi_score}"],
        final_decision=wangshuai
    ))

    # E2: 格局
    evidence_chain.append(new_evidence(
        claim=f"格局为{pattern_name}，评分{pattern_score}/100（{pattern_tier}）",
        confidence=0.85 if pattern_score >= 60 else 0.70,
        basis_mcp=["monthBranch", "hiddenStems"],
        basis_classics=_find_classical_ids(classical_refs, "格局"),
        basis_rules=["六层筛查", f"评分={pattern_score}"],
        final_decision=pattern_name
    ))

    # E3: 喜用神
    evidence_chain.append(new_evidence(
        claim=f"用神={yongshen}，喜神={xishen}，忌神={jishen}",
        confidence=0.80,
        basis_mcp=["dayMaster", "fiveElements", "dayun"],
        basis_classics=_find_classical_ids(classical_refs, "用神"),
        basis_rules=["四层架构", "格局主导"],
        final_decision=f"用{yongshen}喜{xishen}忌{jishen}"
    ))

    # E4: 大运趋势
    if dayun_summary:
        ji_count = sum(1 for d in dayun_summary if d.get("ji", "") in ("吉", "大吉"))
        evidence_chain.append(new_evidence(
            claim=f"10步大运中{ji_count}步为吉运，{len(dayun_summary)-ji_count}步为平/凶运",
            confidence=0.75,
            basis_mcp=["dayun"],
            basis_classics=_find_classical_ids(classical_refs, "大运"),
            basis_rules=["大运上限原则", "病药突破"],
            final_decision=""
        ))

    # E5: 关键结构特征
    if key_features:
        evidence_chain.append(new_evidence(
            claim="关键结构特征: " + "; ".join(key_features),
            confidence=0.90,
            basis_mcp=["xingChongHeHai", "shensha", "kongwang"],
            basis_classics=_find_classical_ids(classical_refs, "刑冲"),
            basis_rules=["刑冲合害分析"],
            final_decision=""
        ))

    return {
        "meta": {
            "day_master": day_master,
            "gender": gender,
            "bazi": bazi,
            "engine": "bazi-pro v4.3",
            "evidence_chain_completeness": _completeness(classical_refs, evidence_chain)
        },
        "evidence_chain": evidence_chain,
        "classical_citations": [
            {"id": r["id"], "source": r["source"], "content": r["content"][:80] + "..."}
            for r in classical_refs[:10]
        ]
    }


def _wangshuai_confidence(deling: int, dedi: float, deshi: float) -> float:
    """基于三要素离散度估算旺衰判断置信度"""
    # 三要素方向一致性越高，置信度越高
    signs = [1 if deling >= 0 else -1, 1 if dedi >= 2 else -1, 1 if deshi >= 3 else -1]
    agreement = sum(1 for s in signs if s == max(set(signs), key=signs.count))
    return 0.65 + agreement * 0.10


def _find_classical_ids(refs: list[dict], topic_hint: str) -> list[str]:
    """从检索结果中筛选相关古籍 ID"""
    ids = []
    for r in refs:
        if topic_hint in r.get("topic", "") or topic_hint in r.get("content", ""):
            ids.append(r["id"])
    return ids[:3] if ids else [r["id"] for r in refs[:2]]


def _completeness(refs: list[dict], chain: list[dict]) -> str:
    """评估证据链完整度"""
    has_classics = len(refs) > 0
    has_chain = len(chain) >= 3
    avg_conf = sum(c["confidence"] for c in chain) / max(1, len(chain))
    if has_classics and has_chain and avg_conf > 0.75:
        return "High"
    elif has_chain:
        return "Medium"
    return "Low"


# CLI
def main():
    """Demo evidence object or write trace to file"""
    import argparse
    p = argparse.ArgumentParser(description="bazi-pro evidence/trace tool")
    p.add_argument("--trace-out", help="输出 analysis_trace.json 路径")
    p.add_argument("--validate", help="校验 trace JSON 文件")
    args = p.parse_args()

    if args.validate:
        from bazi_pro.trace import validate_trace
        ok, errors = validate_trace(args.validate)
        if ok:
            print("✅ Trace valid")
        else:
            print("❌ Validation errors:")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)
        return

    if args.trace_out:
        from bazi_pro.trace import demo_trace
        import json as _json
        trace = demo_trace()
        with open(args.trace_out, "w", encoding="utf-8") as f:
            _json.dump(trace, f, ensure_ascii=False, indent=2)
        print(f"✅ Trace saved: {args.trace_out}")
        return

    # Demo: 使用内置示例数据
    demo = build_analysis_evidence(
        day_master="丙火",
        gender="女",
        bazi="癸卯 壬戌 丙午 壬辰",
        deling_score=-2,
        dedi_score=2.3,
        deshi_score=2.9,
        wangshuai="身弱",
        pattern_name="暗食神格，官杀混杂",
        pattern_score=65,
        pattern_tier="中等",
        yongshen="土",
        xishen="木、火",
        jishen="水",
        classical_refs=[
            {"id": "SFTK_00068", "topic": "十神", "source": "神峰通考",
             "content": "杀星原有制神降，制旺身强贵必昌"},
            {"id": "SFTK_00120", "topic": "十神", "source": "神峰通考",
             "content": "官杀混杂当寿夭，去官留杀仔细寻"},
            {"id": "YHZ_00157", "topic": "十神", "source": "渊海子平",
             "content": "食神干旺，印绶天月二德，夫荣子贵"},
        ],
        key_features=["卯戌合火", "午戌半合火", "戌辰冲", "官杀三重", "阴差阳错+孤鸾"],
        dayun_summary=[
            {"ganzhi": "癸亥", "ji": "凶"},
            {"ganzhi": "甲子", "ji": "平偏吉"},
            {"ganzhi": "乙丑", "ji": "吉"},
            {"ganzhi": "丙寅", "ji": "大吉"},
            {"ganzhi": "丁卯", "ji": "大吉"},
        ]
    )
    print(json.dumps(demo, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
