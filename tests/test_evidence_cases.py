import glob
import json
import os

try:
    import pytest
except ImportError:
    import sys
    print("pytest not installed. Skipping tests.", file=sys.stderr)
    sys.exit(0)

from bazi_pro.evidence import build_analysis_evidence

EVIDENCE_CASES_DIR = os.path.join(os.path.dirname(__file__), "evidence_cases")

STAGE_PATTERNS = {
    "E1": lambda claim: "日主" in claim,
    "E2": lambda claim: "格局为" in claim,
    "E3": lambda claim: "用神=" in claim,
    "E4": lambda claim: "步大运中" in claim,
    "E5": lambda claim: "关键结构特征" in claim,
}


def _load_cases():
    cases = []
    for path in sorted(glob.glob(os.path.join(EVIDENCE_CASES_DIR, "*.json"))):
        with open(path, encoding="utf-8") as f:
            cases.append(json.load(f))
    return cases


def _detect_stages(evidence_chain):
    found = set()
    for ev in evidence_chain:
        claim = ev.get("claim", "")
        for stage_id, matcher in STAGE_PATTERNS.items():
            if matcher(claim):
                found.add(stage_id)
    return found


class TestEvidenceCases:

    @pytest.fixture(params=_load_cases(), ids=lambda c: c["id"])
    def case(self, request):
        return request.param

    def test_min_chains(self, case):
        result = build_analysis_evidence(**case["input"])
        chain = result["evidence_chain"]
        assert len(chain) >= case["expected"]["min_chains"], (
            f"{case['id']}: expected >= {case['expected']['min_chains']} chains, got {len(chain)}"
        )

    def test_completeness(self, case):
        result = build_analysis_evidence(**case["input"])
        actual = result["meta"]["evidence_chain_completeness"]
        expected = case["expected"]["completeness"]
        assert actual == expected, (
            f"{case['id']}: expected completeness '{expected}', got '{actual}'"
        )

    def test_must_have_stages(self, case):
        result = build_analysis_evidence(**case["input"])
        found = _detect_stages(result["evidence_chain"])
        for stage in case["expected"]["must_have_stages"]:
            assert stage in found, (
                f"{case['id']}: expected stage {stage} not found in evidence chain"
            )

    def test_meta_fields(self, case):
        result = build_analysis_evidence(**case["input"])
        meta = result["meta"]
        inp = case["input"]
        assert meta["day_master"] == inp["day_master"]
        assert meta["gender"] == inp["gender"]
        assert meta["bazi"] == inp["bazi"]
        assert meta["engine"] == "bazi-pro v5.0"

    def test_evidence_chain_structure(self, case):
        result = build_analysis_evidence(**case["input"])
        for ev in result["evidence_chain"]:
            assert "claim" in ev
            assert "confidence" in ev
            assert 0 <= ev["confidence"] <= 1
            assert "basis" in ev
            assert "mcp_fields" in ev["basis"]
            assert "classics" in ev["basis"]
            assert "rules" in ev["basis"]
            assert "counter_evidence" in ev
            assert "final_decision" in ev

    def test_classical_citations_truncated(self, case):
        result = build_analysis_evidence(**case["input"])
        for cit in result.get("classical_citations", []):
            assert "id" in cit
            assert "source" in cit
            assert "content" in cit
            assert cit["content"].endswith("...")
