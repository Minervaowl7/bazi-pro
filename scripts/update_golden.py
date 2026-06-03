#!/usr/bin/env python3
"""Update golden case JSON files with current full_analysis() results."""
import json
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bazi_pro.core import full_analysis

GOLDEN_DIR = Path(__file__).resolve().parent.parent / "tests" / "golden_cases"


def update_cases():
    log_path = Path(__file__).resolve().parent.parent / "update_golden_log.txt"
    log_file = open(log_path, "w", encoding="utf-8")

    def log(msg):
        log_file.write(msg + "\n")
        log_file.flush()

    files = sorted(GOLDEN_DIR.glob("*.json"))
    updated_count = 0
    error_count = 0

    for f in files:
        case = json.loads(f.read_text(encoding="utf-8"))
        inp = case.get("input", {})
        bazi = inp.get("bazi", "")
        day_master = inp.get("day_master", "")

        if not bazi or not day_master:
            log(f"SKIP {case['id']}: missing bazi/day_master")
            continue

        mcp_json = {"八字": bazi, "日主": day_master}
        try:
            result = full_analysis(mcp_json)
        except Exception as e:
            log(f"ERROR {case['id']}: full_analysis exception: {e}")
            error_count += 1
            continue

        if result.get("status") != "completed":
            log(f"ERROR {case['id']}: full_analysis returned {result.get('status')}")
            error_count += 1
            continue

        changed = False

        # Update expected_wangshuai
        actual_ws = result["wangshuai"]["verdict"]
        if inp.get("expected_wangshuai") != actual_ws:
            old = inp.get("expected_wangshuai")
            inp["expected_wangshuai"] = actual_ws
            log(f"UPDATE {case['id']}: expected_wangshuai '{old}' -> '{actual_ws}'")
            changed = True

        # Update expected_pattern
        actual_pattern = result["pattern"]["pattern"]
        if inp.get("expected_pattern") != actual_pattern:
            old = inp.get("expected_pattern")
            inp["expected_pattern"] = actual_pattern
            log(f"UPDATE {case['id']}: expected_pattern '{old}' -> '{actual_pattern}'")
            changed = True

        # Update expected_yongshen_wx
        actual_yongshen = result["yongshen"]["yongshen"]
        if inp.get("expected_yongshen_wx") != actual_yongshen:
            old = inp.get("expected_yongshen_wx")
            inp["expected_yongshen_wx"] = actual_yongshen
            log(f"UPDATE {case['id']}: expected_yongshen_wx '{old}' -> '{actual_yongshen}'")
            changed = True

        # Update expected_deling_score
        actual_deling = result["deling"]["score"]
        if inp.get("expected_deling_score") != actual_deling:
            old = inp.get("expected_deling_score")
            inp["expected_deling_score"] = actual_deling
            log(f"UPDATE {case['id']}: expected_deling_score {old} -> {actual_deling}")
            changed = True

        # Update expected_dedi_level
        actual_dedi = result["dedi"]["level"]
        if inp.get("expected_dedi_level") != actual_dedi:
            old = inp.get("expected_dedi_level")
            inp["expected_dedi_level"] = actual_dedi
            log(f"UPDATE {case['id']}: expected_dedi_level '{old}' -> '{actual_dedi}'")
            changed = True

        # Update expected_deshi_level
        actual_deshi = result["deshi"]["level"]
        if inp.get("expected_deshi_level") != actual_deshi:
            old = inp.get("expected_deshi_level")
            inp["expected_deshi_level"] = actual_deshi
            log(f"UPDATE {case['id']}: expected_deshi_level '{old}' -> '{actual_deshi}'")
            changed = True

        # Update must_include: remove keywords no longer found
        pattern_str = result["pattern"]["pattern"]
        pattern_reason = result["pattern"].get("reason", "")
        yongshen_str = str(result.get("yongshen", {}))
        must_include = case.get("must_include", [])
        new_must_include = []
        for kw in must_include:
            found = (kw in pattern_str or kw in pattern_reason or kw in yongshen_str)
            if found:
                new_must_include.append(kw)
            else:
                log(f"UPDATE {case['id']}: must_include remove '{kw}' (pattern={pattern_str})")
                changed = True
        if must_include != new_must_include:
            case["must_include"] = new_must_include

        # Update must_not_include: remove keywords that now appear in pattern
        must_not_include = case.get("must_not_include", [])
        new_must_not_include = []
        for kw in must_not_include:
            if kw in pattern_str:
                log(f"UPDATE {case['id']}: must_not_include remove '{kw}' (now in pattern={pattern_str})")
                changed = True
            else:
                new_must_not_include.append(kw)
        if must_not_include != new_must_not_include:
            case["must_not_include"] = new_must_not_include

        if changed:
            f.write_text(json.dumps(case, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            updated_count += 1
        else:
            log(f"OK {case['id']}: no change needed")

    log(f"\nDone: {updated_count} files updated, {error_count} errors")
    log_file.close()
    print(f"Done: {updated_count} files updated, {error_count} errors")
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(update_cases())
