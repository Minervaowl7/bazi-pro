#!/usr/bin/env python3
"""
分析追踪与证据链构建器 v4.3
TraceBuilder: 逐步构建可回放的分析 trace JSON
Validator: 校验 trace schema 完整性
"""

import json
import os
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


SCHEMA_VERSION = "trace.v1"
CORPUS_HASH = None  # lazy load


def _get_corpus_hash() -> str:
    global CORPUS_HASH
    if CORPUS_HASH is None:
        corpus = Path(__file__).resolve().parent.parent / "references" / "classical_corpus.md"
        if corpus.exists():
            CORPUS_HASH = hashlib.md5(corpus.read_bytes()).hexdigest()[:12]
        else:
            CORPUS_HASH = "unknown"
    return CORPUS_HASH


class TraceBuilder:
    """逐步构建 analysis_trace.json"""

    def __init__(self, run_id: Optional[str] = None):
        self._trace = {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ-demo"),
            "engine": {
                "name": "bazi-pro",
                "version": "4.3.0",
                "corpus_size": 2964,
                "corpus_hash": _get_corpus_hash(),
            },
            "input": {},
            "stages": [],
            "evidence": [],
            "artifacts": {},
        }

    def set_input(self, day_master: str = "", pillars: list[str] = None,
                  source: str = "", **kwargs):
        self._trace["input"] = {
            "day_master": day_master,
            "pillars": pillars or [],
            "source": source,
            **kwargs,
        }

    def add_stage(self, stage_id: str, *, title: str = "", summary: str = "",
                  status: str = "done", confidence: float = None,
                  claims: list[str] = None, evidence_ids: list[str] = None,
                  decision: str = "", outputs: dict = None, results: list[dict] = None):
        stage = {
            "id": stage_id,
            "title": title,
            "status": status,
            "summary": summary,
        }
        if confidence is not None:
            stage["confidence"] = round(confidence, 2)
        if claims:
            stage["claims"] = claims
        if evidence_ids:
            stage["evidence_ids"] = evidence_ids
        if decision:
            stage["decision"] = decision
        if outputs:
            stage["outputs"] = outputs
        if results:
            stage["results"] = results
        self._trace["stages"].append(stage)

    def add_evidence(self, ev_id: str, *, claim: str = "", confidence: float = None,
                     basis_mcp: list[str] = None, basis_rules: list[str] = None,
                     basis_classics: list[str] = None,
                     counter_evidence: list[str] = None, final_decision: str = ""):
        ev = {
            "id": ev_id,
            "claim": claim,
            "basis": {
                "mcp_fields": basis_mcp or [],
                "rules": basis_rules or [],
                "classics": basis_classics or [],
            },
        }
        if confidence is not None:
            ev["confidence"] = round(confidence, 2)
        if counter_evidence:
            ev["counter_evidence"] = counter_evidence
        if final_decision:
            ev["final_decision"] = final_decision
        self._trace["evidence"].append(ev)

    def set_artifacts(self, report_html: str = "", report_md: str = "", **kwargs):
        self._trace["artifacts"] = {
            "report_html": report_html,
            "report_md": report_md,
            **kwargs,
        }

    def build(self) -> dict:
        return self._trace

    def write(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._trace, f, ensure_ascii=False, indent=2)


def validate_trace(path: str) -> tuple[bool, list[str]]:
    """校验 trace JSON schema，返回 (valid, errors)"""
    errors = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            trace = json.load(f)
    except Exception as e:
        return False, [f"无法读取文件: {e}"]

    # Schema version
    if trace.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version 应为 {SCHEMA_VERSION}，实际: {trace.get('schema_version')}")

    # Stages
    stages = trace.get("stages", [])
    if len(stages) < 3:
        errors.append(f"stages 数量应 >= 3，实际: {len(stages)}")

    required_stage_fields = {"id", "title", "summary", "status"}
    for i, s in enumerate(stages):
        missing = required_stage_fields - set(s.keys())
        if missing:
            errors.append(f"stage[{i}] 缺少字段: {missing}")

    # Evidence cross-reference
    evidence_map = {e["id"] for e in trace.get("evidence", [])}
    for s in stages:
        for ev_id in s.get("evidence_ids", []):
            if ev_id not in evidence_map:
                errors.append(f"stage '{s['id']}' 引用了不存在的 evidence_id: {ev_id}")

    # Engine
    engine = trace.get("engine", {})
    if engine.get("corpus_size", 0) < 2900:
        errors.append(f"engine.corpus_size 应 >= 2900，实际: {engine.get('corpus_size')}")

    return len(errors) == 0, errors


def demo_trace() -> dict:
    """生成 sample_trace.json"""
    tb = TraceBuilder(run_id="demo-sample")
    tb.set_input(
        day_master="丁火",
        pillars=["壬午", "乙巳", "丁亥", "癸卯"],
        source="examples/sample_bazi_mcp.json",
        gender="女",
        solar_date="2002-05-19 06:14",
    )

    tb.add_evidence("ev_parse_001", claim="命盘解析完成",
                    basis_mcp=["yearPillar", "monthPillar", "dayPillar", "hourPillar"],
                    basis_rules=["MCP字段解析", "十神推导"])

    tb.add_stage("parse", title="命盘解析", status="done",
                 summary="提取四柱、日主、五行、十神基础信息。",
                 outputs={"day_master": "丁火", "month_branch": "巳"})

    tb.add_evidence("ev_strength_001", claim="日主偏旺",
                    confidence=0.82,
                    basis_mcp=["dayMaster", "monthBranch", "fiveElements"],
                    basis_rules=["得令+3(帝旺)", "得地4分(≥3)", "得势5.5分(≥4)"],
                    basis_classics=["DTM_00082", "SMTH_01164"],
                    counter_evidence=["官杀三重透干，但双干共享一弱根"],
                    final_decision="身旺偏强，不从")

    tb.add_stage("strength", title="旺衰裁决", status="done",
                 summary="综合月令、根气、帮扶判断日主强弱。",
                 confidence=0.82,
                 claims=["日主身旺偏强，不从"],
                 evidence_ids=["ev_strength_001"])

    tb.add_stage("retrieval_positive", title="顺向古籍检索", status="done",
                 summary="检索支持当前裁决方向的古籍依据。",
                 results=[
                     {"id": "SMTH_01164", "source": "三命通会", "score": 15.23,
                      "matched_terms": ["建禄", "比劫", "财官"]},
                     {"id": "ZPZ_00031", "source": "子平真诠", "score": 14.56,
                      "matched_terms": ["建禄月劫", "本身不可为用"]},
                 ])

    tb.add_stage("retrieval_counterfactual", title="反事实检索", status="done",
                 summary="检索可能推翻当前裁决的相反证据。",
                 results=[
                     {"id": "DTM_00082", "source": "滴天髓", "score": 15.65,
                      "matched_terms": ["假从", "从象"]},
                 ])

    tb.add_evidence("ev_geju_001", claim="建禄月劫之格，透官煞，印化通关",
                    confidence=0.80,
                    basis_mcp=["monthBranch", "hiddenStems", "surfaceStems"],
                    basis_rules=["月令劫财不透→建禄月劫", "年壬官+时癸煞→官煞混杂", "月乙印通关"],
                    basis_classics=["ZPZ_00031", "SMTH_01164"])

    tb.add_stage("pattern", title="格局筛查", status="done",
                 summary="六层筛查：从格不成立→层3建禄月劫，透官煞，印化通关。",
                 confidence=0.80,
                 evidence_ids=["ev_geju_001"],
                 decision="建禄月劫之格，透官煞，印化通关")

    tb.add_stage("yongshen", title="喜用神裁决", status="done",
                 summary="四层架构裁决：格局用神火+病药土+扶抑水/土/金→格局主导，用神=火，喜神=木。",
                 confidence=0.80,
                 decision="用神火，喜神木，忌神水")

    tb.add_stage("final_decision", title="最终裁决", status="done",
                 summary="建禄月劫，透官煞，印化通关。格局评分55/100中下等。用神火喜神木忌神水。",
                 confidence=0.79,
                 decision="建禄月劫之格，印化官煞，用火喜木忌水")

    tb.set_artifacts(report_html="sample_dashboard.html", report_md="sample_report.md")
    return tb.build()


def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        print(json.dumps(demo_trace(), ensure_ascii=False, indent=2))
    elif len(sys.argv) > 2 and sys.argv[1] == "validate":
        ok, errors = validate_trace(sys.argv[2])
        if ok:
            print("✅ Trace valid")
        else:
            print("❌ Validation errors:")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)
    else:
        print("用法: bazi-trace demo | bazi-trace validate <trace.json>")

if __name__ == "__main__":
    main()
