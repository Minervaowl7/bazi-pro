#!/usr/bin/env python3
"""
更新所有现有 golden cases 并创建新 golden cases 的脚本。

Task 1: 读取所有 JSON 文件，运行 full_analysis，更新 expected 字段
Task 2: 创建新的 golden case 文件覆盖缺失区域
"""
import json
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bazi_pro.core import full_analysis

GOLDEN_DIR = Path(__file__).resolve().parent.parent / "tests" / "golden_cases"


def run_analysis(bazi: str, day_master: str) -> dict:
    """运行 full_analysis 并返回结果"""
    mcp_json = {"八字": bazi, "日主": day_master}
    result = full_analysis(mcp_json)
    return result


def extract_expected(result: dict) -> dict:
    """从 full_analysis 结果中提取 expected 字段"""
    return {
        "expected_wangshuai": result["wangshuai"]["verdict"],
        "expected_pattern": result["pattern"]["pattern"],
        "expected_yongshen_wx": result["yongshen"]["yongshen"],
        "expected_deling_score": result["deling"]["score"],
        "expected_dedi_level": result["dedi"]["level"],
        "expected_deshi_level": result["deshi"]["level"],
    }


def validate_must_include(result: dict, must_include: list, must_not_include: list) -> tuple:
    """
    验证 must_include 和 must_not_include 是否仍然有效。
    返回 (updated_must_include, updated_must_not_include)
    """
    pattern_str = result["pattern"]["pattern"]
    pattern_reason = result["pattern"].get("reason", "")
    yongshen_str = str(result.get("yongshen", {}))

    new_must_include = []
    for kw in must_include:
        found = (kw in pattern_str or kw in pattern_reason or kw in yongshen_str)
        if found:
            new_must_include.append(kw)
        else:
            print(f"    ⚠️ must_include '{kw}' 不再命中 (格局={pattern_str})")

    new_must_not_include = []
    for kw in must_not_include:
        if kw not in pattern_str:
            new_must_not_include.append(kw)
        else:
            print(f"    ⚠️ must_not_include '{kw}' 现在出现在格局中 (格局={pattern_str})")

    return new_must_include, new_must_not_include


def task1_update_existing():
    """Task 1: 更新所有现有 golden cases"""
    print("=" * 60)
    print("Task 1: 更新所有现有 golden cases")
    print("=" * 60)

    json_files = sorted(GOLDEN_DIR.glob("*.json"))
    updated_count = 0
    unchanged_count = 0
    error_count = 0

    for json_file in json_files:
        case = json.loads(json_file.read_text(encoding='utf-8'))
        case_id = case.get("id", json_file.stem)
        inp = case.get("input", {})
        bazi = inp.get("bazi", "")
        day_master = inp.get("day_master", "")

        if not bazi or not day_master:
            print(f"  ⏭️ {case_id}: 缺少 bazi/day_master，跳过")
            continue

        try:
            result = run_analysis(bazi, day_master)

            if result.get("status") != "completed":
                print(f"  ❌ {case_id}: full_analysis 返回异常状态: {result.get('status')}")
                error_count += 1
                continue

            new_expected = extract_expected(result)
            changed = False

            # 更新 input 中的 expected 字段
            for key, new_val in new_expected.items():
                old_val = inp.get(key)
                if old_val != new_val:
                    inp[key] = new_val
                    changed = True
                    print(f"    🔄 {key}: {old_val} → {new_val}")

            # 验证并更新 must_include / must_not_include
            old_must_include = case.get("must_include", [])
            old_must_not_include = case.get("must_not_include", [])

            new_must_include, new_must_not_include = validate_must_include(
                result, old_must_include, old_must_not_include
            )

            if new_must_include != old_must_include:
                case["must_include"] = new_must_include
                changed = True
                print(f"    🔄 must_include: {old_must_include} → {new_must_include}")

            if new_must_not_include != old_must_not_include:
                case["must_not_include"] = new_must_not_include
                changed = True
                print(f"    🔄 must_not_include: {old_must_not_include} → {new_must_not_include}")

            if changed:
                json_file.write_text(
                    json.dumps(case, ensure_ascii=False, indent=2) + "\n",
                    encoding='utf-8'
                )
                updated_count += 1
                print(f"  ✅ {case_id}: 已更新")
            else:
                unchanged_count += 1
                print(f"  ✅ {case_id}: 无变化")

        except Exception as e:
            print(f"  ❌ {case_id}: 错误 - {e}")
            error_count += 1

    print(f"\nTask 1 完成: {updated_count} 更新, {unchanged_count} 无变化, {error_count} 错误")
    return error_count == 0


# 新 golden case 定义
NEW_CASES = [
    # === 化气格 (5 cases) ===
    {
        "id": "hua_tu_ge",
        "description": "化土格 — 甲己合化土，月令辰月土当令",
        "scenario": "甲木日主，甲己合化土，月令辰月土当令，真化",
        "input_bazi": "己巳 戊辰 甲辰 己巳",
        "input_day_master": "甲",
        "must_include": [],
        "must_not_include": [],
        "classical_support": ["ZPZY_00012"],
        "notes": "甲己合化土，月令辰月土当令，化土真格。《子平真诠》'化得真者只论化'"
    },
    {
        "id": "hua_jin_ge",
        "description": "化金格 — 乙庚合化金，月令申月金当令",
        "scenario": "乙木日主，乙庚合化金，月令申月金当令，真化",
        "input_bazi": "庚辰 甲申 乙酉 庚辰",
        "input_day_master": "乙",
        "must_include": [],
        "must_not_include": [],
        "classical_support": ["ZPZY_00012"],
        "notes": "乙庚合化金，月令申月金当令，化金真格。《子平真诠》'化得真者只论化'"
    },
    {
        "id": "hua_shui_ge",
        "description": "化水格 — 丙辛合化水，月令亥月水当令",
        "scenario": "丙火日主，丙辛合化水，月令亥月水当令，真化",
        "input_bazi": "辛亥 己亥 丙子 辛卯",
        "input_day_master": "丙",
        "must_include": [],
        "must_not_include": [],
        "classical_support": ["ZPZY_00012"],
        "notes": "丙辛合化水，月令亥月水当令，化水真格。《子平真诠》'化得真者只论化'"
    },
    {
        "id": "hua_mu_ge",
        "description": "化木格 — 丁壬合化木，月令寅月木当令",
        "scenario": "丁火日主，丁壬合化木，月令寅月木当令，真化",
        "input_bazi": "壬寅 壬寅 丁卯 壬寅",
        "input_day_master": "丁",
        "must_include": [],
        "must_not_include": [],
        "classical_support": ["ZPZY_00012"],
        "notes": "丁壬合化木，月令寅月木当令，化木真格。《子平真诠》'化得真者只论化'"
    },
    {
        "id": "hua_huo_ge",
        "description": "化火格 — 戊癸合化火，月令巳月火当令",
        "scenario": "戊土日主，戊癸合化火，月令巳月火当令，真化",
        "input_bazi": "癸巳 丁巳 戊午 癸亥",
        "input_day_master": "戊",
        "must_include": [],
        "must_not_include": [],
        "classical_support": ["ZPZY_00012"],
        "notes": "戊癸合化火，月令巳月火当令，化火真格。《子平真诠》'化得真者只论化'"
    },
    # === 从格 (4 cases) ===
    {
        "id": "congcai_ge_true",
        "description": "从财格（真从）— 日主无根，财星成势会财",
        "scenario": "甲木日主，地支无本气/中气根，财星成势",
        "input_bazi": "戊戌 甲子 甲午 己巳",
        "input_day_master": "甲",
        "must_include": [],
        "must_not_include": [],
        "classical_support": ["DTM_00030"],
        "notes": "甲木日主，地支戌子午巳，甲无本气/中气根，财星戊己土旺，从财格"
    },
    {
        "id": "congguansha_ge_true",
        "description": "从官杀格（真从）— 日主无根，官杀成势",
        "scenario": "甲木日主，地支无本气/中气根，官杀成势",
        "input_bazi": "辛酉 庚子 甲午 戊戌",
        "input_day_master": "甲",
        "must_include": [],
        "must_not_include": [],
        "classical_support": ["DTM_00030"],
        "notes": "甲木日主，地支酉子午戌，甲无本气/中气根，庚辛金官杀旺，从官杀格"
    },
    {
        "id": "conger_ge_true",
        "description": "从儿格（真从）— 日主无根，食伤成势",
        "scenario": "甲木日主，地支无本气/中气根，食伤成势",
        "input_bazi": "丁巳 丙午 甲戌 戊午",
        "input_day_master": "甲",
        "must_include": [],
        "must_not_include": [],
        "classical_support": ["DTM_00030"],
        "notes": "甲木日主，地支巳午戌午，甲无本气/中气根，丙丁火食伤极旺，从儿格"
    },
    {
        "id": "congshi_ge_true",
        "description": "从势格 — 日主无根，多行成势",
        "scenario": "甲木日主，地支无本气/中气根，财官食伤多行成势",
        "input_bazi": "辛酉 戊戌 甲午 庚午",
        "input_day_master": "甲",
        "must_include": [],
        "must_not_include": [],
        "classical_support": ["DTM_00030"],
        "notes": "甲木日主，地支酉戌午午，甲无本气/中气根，金土火多行成势，从势格"
    },
    # === 极弱 (1 case) ===
    {
        "id": "wangshuai_jiruo",
        "description": "极弱 — 乙木日主，申月绝地，不得地不得势",
        "scenario": "乙木日主，申月死地，地支酉申酉巳，全无根气",
        "input_bazi": "辛酉 庚申 乙酉 辛巳",
        "input_day_master": "乙",
        "must_include": [],
        "must_not_include": [],
        "notes": "乙木日主申月死地，地支酉申酉巳，乙无本气/中气根，极弱"
    },
    # === 破格 (6 cases) ===
    {
        "id": "poge_bijie_zhengcai",
        "description": "破格-比劫争财 — 正财格+比劫透出争财",
        "scenario": "丙火日主，月令酉金正财格，天干透丁火劫财争财",
        "input_bazi": "辛酉 丁酉 丙午 丁酉",
        "input_day_master": "丙",
        "must_include": [],
        "must_not_include": [],
        "classical_support": ["ZPZY_00008"],
        "notes": "丙火日主，月令酉金正财格，丁火劫财透干争财，财格破格"
    },
    {
        "id": "poge_caixing_poyin",
        "description": "破格-财星破印 — 正印格+财星破印(印轻)",
        "scenario": "甲木日主，月令丑月癸水中气透干正印格，戊土偏财破印",
        "input_bazi": "癸酉 己丑 甲寅 戊辰",
        "input_day_master": "甲",
        "must_include": [],
        "must_not_include": [],
        "classical_support": ["ZPZY_00008"],
        "notes": "甲木日主，月令丑月癸水中气透干成正印格，戊土偏财破印"
    },
    {
        "id": "poge_xiaoshen_duoshi",
        "description": "破格-枭神夺食 — 食神格+枭神透出夺食",
        "scenario": "甲木日主，月令巳火食神格，壬水枭神透出夺食",
        "input_bazi": "壬申 癸巳 甲午 壬申",
        "input_day_master": "甲",
        "must_include": [],
        "must_not_include": [],
        "classical_support": ["ZPZY_00008"],
        "notes": "甲木日主，月令巳火丙食神格，壬水枭神透干夺食，食神格破格"
    },
    {
        "id": "poge_zhenghe",
        "description": "破格-争合 — 化气格+争合破格",
        "scenario": "甲木日主，甲己合化土，但两己争合一甲，争合破格",
        "input_bazi": "己巳 己巳 甲辰 己巳",
        "input_day_master": "甲",
        "must_include": [],
        "must_not_include": [],
        "classical_support": ["ZPZY_00008"],
        "notes": "甲木日主，甲己合化土，但三己争合一甲，争合不化，破格"
    },
    {
        "id": "poge_kehuashen",
        "description": "破格-克化神 — 化气格+克化神破格",
        "scenario": "甲木日主，甲己合化土，但木旺克土，克化神破格",
        "input_bazi": "己巳 戊辰 甲寅 己巳",
        "input_day_master": "甲",
        "must_include": [],
        "must_not_include": [],
        "classical_support": ["ZPZY_00008"],
        "notes": "甲木日主，甲己合化土，但甲坐寅有根且木旺克土，克化神破格"
    },
    {
        "id": "poge_mingfeng_genqi",
        "description": "破格-命逢根气 — 从格+命逢根气破格",
        "scenario": "甲木日主极弱，本应从格，但日支寅木有根气",
        "input_bazi": "辛酉 庚子 甲寅 戊戌",
        "input_day_master": "甲",
        "must_include": [],
        "must_not_include": [],
        "classical_support": ["ZPZY_00008"],
        "notes": "甲木日主极弱，但日支寅中有甲本气根，命逢根气不从，破格"
    },
    # === 炎上格 (1 case) ===
    {
        "id": "yanshang_ge_true",
        "description": "炎上格 — 丙火日主，巳午未三会火局，月令午火当令",
        "scenario": "丙火日主，地支巳午未三会火局，月令午火当令，火行专旺",
        "input_bazi": "丁巳 甲午 丙午 丁未",
        "input_day_master": "丙",
        "must_include": [],
        "must_not_include": [],
        "notes": "丙火日主，地支巳午未三会火局，月令午火当令，炎上格"
    },
]


def task2_create_new():
    """Task 2: 创建新 golden cases"""
    print("\n" + "=" * 60)
    print("Task 2: 创建新 golden cases")
    print("=" * 60)

    created_count = 0
    error_count = 0

    for case_def in NEW_CASES:
        case_id = case_def["id"]
        bazi = case_def["input_bazi"]
        day_master = case_def["input_day_master"]

        # 提取月支
        bazi_parts = bazi.split()
        month_branch = bazi_parts[1][1] if len(bazi_parts[1]) >= 2 else ""

        try:
            result = run_analysis(bazi, day_master)

            if result.get("status") != "completed":
                print(f"  ❌ {case_id}: full_analysis 返回异常状态: {result.get('status')}")
                error_count += 1
                continue

            expected = extract_expected(result)

            # 根据 result 自动生成 must_include / must_not_include
            pattern_str = result["pattern"]["pattern"]
            wangshuai_str = result["wangshuai"]["verdict"]

            must_include = case_def.get("must_include", [])
            if not must_include:
                # 自动添加格局名到 must_include
                must_include = [pattern_str]

            must_not_include = case_def.get("must_not_include", [])

            new_case = {
                "id": case_id,
                "description": case_def["description"],
                "scenario": case_def["scenario"],
                "input": {
                    "day_master": day_master,
                    "bazi": bazi,
                    "month_branch": month_branch,
                    "expected_pattern": expected["expected_pattern"],
                    "expected_wangshuai": expected["expected_wangshuai"],
                    "expected_yongshen_wx": expected["expected_yongshen_wx"],
                    "expected_deling_score": expected["expected_deling_score"],
                    "expected_dedi_level": expected["expected_dedi_level"],
                    "expected_deshi_level": expected["expected_deshi_level"],
                },
                "must_include": must_include,
                "must_not_include": must_not_include,
                "notes": case_def.get("notes", ""),
            }

            if case_def.get("classical_support"):
                new_case["classical_support"] = case_def["classical_support"]

            out_path = GOLDEN_DIR / f"{case_id}.json"
            if out_path.exists():
                print(f"  ⚠️ {case_id}: 文件已存在，覆盖")

            out_path.write_text(
                json.dumps(new_case, ensure_ascii=False, indent=2) + "\n",
                encoding='utf-8'
            )
            created_count += 1
            print(f"  ✅ {case_id}: 已创建 (格局={pattern_str}, 旺衰={wangshuai_str}, 用神={expected['expected_yongshen_wx']})")

        except Exception as e:
            print(f"  ❌ {case_id}: 错误 - {e}")
            import traceback
            traceback.print_exc()
            error_count += 1

    print(f"\nTask 2 完成: {created_count} 创建, {error_count} 错误")
    return error_count == 0


def main():
    ok1 = task1_update_existing()
    ok2 = task2_create_new()

    if ok1 and ok2:
        print("\n✅ 所有任务完成")
        return 0
    else:
        print("\n❌ 部分任务失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
