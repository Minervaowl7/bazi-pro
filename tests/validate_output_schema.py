#!/usr/bin/env python3
"""full_analysis() 输出 Schema 验证器

在 CI 中运行，确保 full_analysis() 的返回结构不被意外破坏。
不验证具体值——只验证键名、类型、嵌套结构是否完整。

用法:
  python tests/validate_output_schema.py
"""

import sys

# ── 顶层键名和类型 ──
TOP_LEVEL = {
    "status": str,
    "day_master": str,
    "deling": dict,
    "dedi": dict,
    "deshi": dict,
    "wangshuai": dict,
    "element_forces": dict,
    "relations": list,
    "pattern": dict,
    "yongshen": dict,
    "disease": dict,
    "pillars": list,
}

# ── 各子结构的键名和类型 ──
DELING_KEYS = {"status": str, "score": int}
DEDI_KEYS = {"score": (int, float), "details": list, "level": str}
DEDI_DETAIL_KEYS = {"zhi": str, "canggan_gan": str, "qi_level": str, "weight": (int, float), "wuxing": str}
DESHI_KEYS = {"score": (int, float), "details": list, "level": str}
DESHI_DETAIL_KEYS = {"zhi", "canggan_gan", "shishen", "qi_level", "score", "position", "gan", "distance"}
WANGSHUAI_KEYS = {"verdict": str, "deling_score": int, "dedi_score": (int, float),
                  "deshi_score": (int, float), "is_weak": bool, "is_strong": bool,
                  "is_extreme_weak": bool, "is_extreme_strong": bool}
ELEMENT_FORCES_KEYS = {"raw": dict, "percent": dict, "total": (int, float),
                       "percent_adjusted": dict, "hehua": dict}
HEHUA_KEYS = {"gan_he": list, "zhi_sanhe": list, "zhi_banhe": list, "zhi_huifang": list}
RELATION_KEYS = {"type", "elements", "result", "hua_wuxing", "disease_god", "disease_gan",
                 "disease_position", "affected_god", "affected_gan", "affected_position", "severity"}
PATTERN_KEYS = {"pattern": str, "candidates": list, "layer": int, "type": str,
                "confidence": (int, float), "reason": str, "yongshen_direction": str, "wangshuai": dict}
YONGSHEN_KEYS = {"yongshen": str, "yongshen_gan": str, "xishen": list, "xishen_gan": list,
                 "jishen": list, "jishen_gan": list, "confidence": (int, float),
                 "pattern_basis": str, "note": str, "trace": dict}
DISEASE_KEYS = {"has_disease": bool, "items": list, "medicine_advice": str}
PILLAR_KEYS = {"position": str, "gan": str, "zhi": str, "wuxing_gan": str, "wuxing_zhi": str,
               "shishen": str, "canggan": list}
CANGGAN_KEYS = {"gan": str, "qi": str, "wuxing": str, "shishen": str}

WUXING_SET = {"木", "火", "土", "金", "水"}


def _type_str(t):
    if isinstance(t, tuple):
        return "|".join(x.__name__ for x in t)
    return t.__name__


def validate_keys(data: dict, required: dict, path: str, errors: list):
    for key, expected_type in required.items():
        if key not in data:
            errors.append(f"{path}: 缺少键 '{key}'")
            continue
        value = data[key]
        if not isinstance(value, expected_type):
            errors.append(
                f"{path}.{key}: 类型错误，期望 {_type_str(expected_type)}，实际 {type(value).__name__}"
            )


def validate(output: dict) -> list[str]:
    errors: list[str] = []

    if not isinstance(output, dict):
        return ["根值不是 dict"]

    # ── 支持两种状态：completed 和 invalid_input ──
    status = output.get("status", "")
    if status not in ("completed", "invalid_input"):
        errors.append(f"status 值非法: '{status}'")
        return errors

    if status == "invalid_input":
        if "errors" not in output or not isinstance(output["errors"], list):
            errors.append("status=invalid_input 时缺少 errors 列表")
        return errors

    # ── 顶层键 ──
    validate_keys(output, TOP_LEVEL, "", errors)

    # ── deling ──
    if isinstance(output.get("deling"), dict):
        validate_keys(output["deling"], DELING_KEYS, "deling", errors)

    # ── dedi ──
    if isinstance(output.get("dedi"), dict):
        validate_keys(output["dedi"], DEDI_KEYS, "dedi", errors)
        for i, detail in enumerate(output["dedi"].get("details", [])):
            if isinstance(detail, dict):
                validate_keys(detail, DEDI_DETAIL_KEYS, f"dedi.details[{i}]", errors)

    # ── deshi ──
    if isinstance(output.get("deshi"), dict):
        validate_keys(output["deshi"], DESHI_KEYS, "deshi", errors)
        for i, detail in enumerate(output["deshi"].get("details", [])):
            if isinstance(detail, dict):
                if "gan" in detail:
                    for k in ("position", "gan", "shishen", "distance", "score"):
                        if k not in detail:
                            errors.append(f"deshi.details[{i}]: 缺少键 '{k}'")
                else:
                    for k in ("zhi", "canggan_gan", "shishen", "qi_level", "score"):
                        if k not in detail:
                            errors.append(f"deshi.details[{i}]: 缺少键 '{k}'")

    # ── wangshuai ──
    if isinstance(output.get("wangshuai"), dict):
        validate_keys(output["wangshuai"], WANGSHUAI_KEYS, "wangshuai", errors)

    # ── element_forces ──
    if isinstance(output.get("element_forces"), dict):
        validate_keys(output["element_forces"], ELEMENT_FORCES_KEYS, "element_forces", errors)
        for pct_key in ("percent", "percent_adjusted"):
            pct = output["element_forces"].get(pct_key, {})
            if isinstance(pct, dict):
                for wx in WUXING_SET:
                    if wx not in pct:
                        errors.append(f"element_forces.{pct_key}: 缺少五行 '{wx}'")
            raw = output["element_forces"].get("raw", {})
            if isinstance(raw, dict):
                for wx in WUXING_SET:
                    if wx not in raw:
                        errors.append(f"element_forces.raw: 缺少五行 '{wx}'")
            hehua = output["element_forces"].get("hehua", {})
            if isinstance(hehua, dict):
                validate_keys(hehua, HEHUA_KEYS, "element_forces.hehua", errors)

    # ── relations ──
    relations = output.get("relations", [])
    if isinstance(relations, list):
        for i, rel in enumerate(relations):
            if not isinstance(rel, dict):
                errors.append(f"relations[{i}]: 不是 dict")
                continue
            if "type" not in rel:
                errors.append(f"relations[{i}]: 缺少 'type'")

    # ── pattern ──
    if isinstance(output.get("pattern"), dict):
        validate_keys(output["pattern"], PATTERN_KEYS, "pattern", errors)

    # ── yongshen ──
    if isinstance(output.get("yongshen"), dict):
        validate_keys(output["yongshen"], YONGSHEN_KEYS, "yongshen", errors)

    # ── disease ──
    if isinstance(output.get("disease"), dict):
        validate_keys(output["disease"], DISEASE_KEYS, "disease", errors)

    # ── pillars ──
    pillars = output.get("pillars", [])
    if isinstance(pillars, list):
        if len(pillars) not in (0, 4):
            errors.append(f"pillars 长度应为 0 或 4，实际 {len(pillars)}")
        for i, p in enumerate(pillars):
            if not isinstance(p, dict):
                errors.append(f"pillars[{i}]: 不是 dict")
                continue
            validate_keys(p, PILLAR_KEYS, f"pillars[{i}]", errors)
            for j, cg in enumerate(p.get("canggan", [])):
                if isinstance(cg, dict):
                    validate_keys(cg, CANGGAN_KEYS, f"pillars[{i}].canggan[{j}]", errors)

    return errors


def main():
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
    from bazi_pro.core import full_analysis

    # 正常命盘
    result = full_analysis({"八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁"})
    errors = validate(result)
    if errors:
        print(f"❌ Schema 验证失败 ({len(errors)} 个错误):")
        for e in errors:
            print(f"  - {e}")
        return 1

    # 无效输入
    invalid = full_analysis({"八字": "", "日主": ""})
    errors2 = validate(invalid)
    if errors2:
        print(f"❌ Invalid input schema 验证失败 ({len(errors2)} 个错误):")
        for e in errors2:
            print(f"  - {e}")
        return 1

    print("✅ Schema 验证通过")
    print(f"   正常命盘: {len(result.keys())} 个顶层键")
    print("   invalid_input: 正确返回 errors 列表")
    return 0


if __name__ == "__main__":
    sys.exit(main())
