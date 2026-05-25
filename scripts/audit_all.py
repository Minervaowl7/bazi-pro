#!/usr/bin/env python3
"""全量审计主控脚本

依次运行所有 4 个专项审计 + Schema 验证。
用法:
  python scripts/audit_all.py
  python scripts/audit_all.py --quick    # 只跑 Agent A + Schema
"""

import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent

SCRIPTS = {
    "A - 数据表": str(PROJECT / "scripts" / "audit_data_tables.py"),
    "B - 推导链": str(PROJECT / "scripts" / "audit_logic_chain.py"),
    "C - SKILL合约": str(PROJECT / "scripts" / "audit_skill_consistency.py"),
    "D - Golden用例": str(PROJECT / "scripts" / "audit_golden_cases.py"),
    "Schema": str(PROJECT / "tests" / "validate_output_schema.py"),
}


def main():
    quick = "--quick" in sys.argv
    verbose = "--verbose" in sys.argv

    if quick:
        keys = ["A - 数据表", "Schema"]
    else:
        keys = list(SCRIPTS.keys())

    print("=" * 60)
    print(" bazi-pro 全量审计")
    print(f" 模式: {'快速' if quick else '完整'} ({len(keys)} 项)")
    print("=" * 60)

    failed = []
    for name in keys:
        path = SCRIPTS[name]
        print(f"\n── {name} ──")
        r = subprocess.run(
            [sys.executable, path] + (["--verbose"] if verbose else []),
            cwd=str(PROJECT), capture_output=True, text=True, timeout=30,
        )
        output = (r.stdout + r.stderr).strip()
        for line in output.splitlines():
            print(f"   {line}")
        if r.returncode != 0:
            failed.append(name)

    print("\n" + "=" * 60)
    if failed:
        print(f" ❌ {len(failed)}/{len(keys)} 项失败: {', '.join(failed)}")
        return 1
    print(f" ✅ 全部 {len(keys)} 项通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
