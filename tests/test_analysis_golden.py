#!/usr/bin/env python3
from pathlib import Path

try:
    import pytest
except ImportError:
    import sys
    print("pytest not installed. Skipping tests.", file=sys.stderr)
    sys.exit(0)
import yaml

from bazi_pro.core import full_analysis

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
CASES_FILE = GOLDEN_DIR / "analysis_cases.yaml"


def _load_cases():
    if not CASES_FILE.exists():
        return []
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _check_layer(case_id: str, layer: str, expected: dict, actual_value: str) -> list[str]:
    failures = []
    if "allowed" in expected:
        if actual_value not in expected["allowed"]:
            failures.append(
                f"case={case_id} layer={layer} "
                f"expected one of {expected['allowed']}, got='{actual_value}'"
            )
    if "forbidden" in expected:
        if actual_value in expected["forbidden"]:
            failures.append(
                f"case={case_id} layer={layer} "
                f"forbidden value '{actual_value}' appeared"
            )
    return failures


def _check_required_any(case_id: str, layer: str, required_any: list[str], actual_value: str) -> list[str]:
    if not required_any:
        return []
    matched = any(kw in actual_value for kw in required_any)
    if not matched:
        return [
            f"case={case_id} layer={layer} "
            f"expected any of {required_any} in '{actual_value[:80]}'"
        ]
    return []


def _check_forbidden_keywords(case_id: str, layer: str, forbidden: list[str], actual_value: str) -> list[str]:
    failures = []
    for kw in forbidden:
        if kw in actual_value:
            failures.append(
                f"case={case_id} layer={layer} "
                f"forbidden keyword '{kw}' found in '{actual_value[:80]}'"
            )
    return failures


def _check_forbidden_outputs(case_id: str, forbidden_outputs: list[str], result_str: str) -> list[str]:
    failures = []
    for kw in forbidden_outputs:
        if kw in result_str:
            failures.append(
                f"case={case_id} layer=forbidden_output "
                f"forbidden output '{kw}' found in result"
            )
    return failures


def _check_evidence_terms(case_id: str, required_terms_any: list[str], result: dict) -> list[str]:
    if not required_terms_any:
        return []
    result_str = str(result)
    matched = any(term in result_str for term in required_terms_any)
    if not matched:
        return [
            f"case={case_id} layer=evidence "
            f"expected any of {required_terms_any} in result"
        ]
    return []


def _validate_case(case: dict) -> list[str]:
    case_id = case["id"]
    inp = case["input"]
    expected = case["expected"]
    failures = []

    mcp_json = {
        "八字": inp["八字"],
        "日主": inp["日主"],
        "性别": inp.get("性别", "男"),
    }
    if "大运" in inp:
        mcp_json["大运"] = inp["大运"]

    result = full_analysis(mcp_json)

    if result.get("status") != "completed":
        failures.append(
            f"case={case_id} layer=status expected='completed', got='{result.get('status')}'"
        )
        return failures

    if "day_master" in expected:
        actual_dm = result.get("day_master", "")
        if actual_dm != expected["day_master"]:
            failures.append(
                f"case={case_id} layer=day_master "
                f"expected='{expected['day_master']}', got='{actual_dm}'"
            )

    if "strength" in expected:
        ws = result.get("wangshuai", {})
        verdict = ws.get("verdict", "")
        failures.extend(_check_layer(case_id, "strength", expected["strength"], verdict))

    if "pattern" in expected:
        pat = result.get("pattern", {})
        pattern_str = pat.get("pattern", "")
        reason = pat.get("reason", "")
        combined = pattern_str + reason

        if "required_any" in expected["pattern"]:
            failures.extend(
                _check_required_any(case_id, "pattern", expected["pattern"]["required_any"], combined)
            )
        if "forbidden" in expected["pattern"]:
            failures.extend(
                _check_forbidden_keywords(case_id, "pattern", expected["pattern"]["forbidden"], combined)
            )

    if "yongshen" in expected:
        ys = result.get("yongshen", {})
        ys_str = str(ys)
        if "required_any" in expected["yongshen"]:
            failures.extend(
                _check_required_any(case_id, "yongshen", expected["yongshen"]["required_any"], ys_str)
            )

    if "evidence" in expected:
        terms = expected["evidence"].get("required_terms_any", [])
        failures.extend(_check_evidence_terms(case_id, terms, result))

    if "forbidden_outputs" in expected:
        result_str = str(result)
        failures.extend(_check_forbidden_outputs(case_id, expected["forbidden_outputs"], result_str))

    return failures


def _make_test_id(case):
    return case["id"]


_cases = _load_cases()


@pytest.mark.parametrize("case", _cases, ids=_make_test_id)
def test_analysis_golden(case):
    if case.get("xfail_reason"):
        pytest.xfail(case["xfail_reason"])

    failures = _validate_case(case)
    if failures:
        pytest.fail("\n".join(failures))


def test_analysis_golden_count():
    assert len(_cases) >= 20, f"Expected at least 20 analysis golden cases, got {len(_cases)}"


def test_analysis_golden_type_coverage():
    required_types = [
        "身强", "身弱", "中和", "从强", "从弱",
        "建禄", "羊刃", "伤官见官", "食伤生财",
        "财官印", "官杀混杂", "印旺", "财旺",
        "食伤旺", "比劫旺", "月令", "藏干",
        "合化", "冲刑害", "大运",
    ]
    titles = " ".join(c.get("title", "") for c in _cases)
    missing = []
    for t in required_types:
        if t not in titles:
            missing.append(t)
    assert not missing, f"Missing type coverage: {missing}"
