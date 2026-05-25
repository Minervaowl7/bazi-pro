#!/usr/bin/env python3
"""
Ralph Wiggum Loop — bazi-pro 持续测试看护器

用法:
  python scripts/ralph_loop.py                  # 运行一次全量测试
  python scripts/ralph_loop.py --watch          # 监视文件变更，自动重跑
  python scripts/ralph_loop.py --interval 30    # 每30秒轮询一次
  python scripts/ralph_loop.py --forever        # 无限循环，不管结果如何
  python scripts/ralph_loop.py --until-pass     # 一直跑到全部通过为止
  python scripts/ralph_loop.py --quick          # 只跑 golden cases
"""

import argparse
import subprocess
import sys
import time
import random
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RALPH_QUOTES = {
    "all_pass": [
        "I'm a winner! 我的猫的呼吸闻起来像猫粮！",
        "I'm happy! I'm helping! 所有测试绿了！",
        "Ms. Krabappel said I did good! 全部通过啦！",
        "I choo-choo-choose... all tests passing!",
        "Daddy says I'm special — 所有测试绿灯！",
        "My knob tastes like testing! (全都通过了！)",
        "I'm a unit test champion! Principal Skinner would be proud!",
        "Go banana! 零失败！",
        "The leprechaun says all tests are green! I found the gold!",
    ],
    "some_fail": [
        "I'm in danger! {fail_count} 个测试失败了！",
        "That's unpossible! {fail_count} failures...",
        "My doctor said I can't have failures, but I got {fail_count}...",
        "I ate the purple berries... and {fail_count} tests failed...",
        "Even my crayon sandwich won't fix {fail_count} failures!",
        "Hi Super Nintendo Chalmers! {fail_count} tests went boom!",
        "Principal Skinner, {fail_count} tests are burning!",
        "I'm a brick! ...and {fail_count} tests fell over!",
        "The children are wrong, and so are {fail_count} tests!",
        "I wet my arm and {fail_count} tests failed. I'm not happy.",
    ],
    "all_fail": [
        "OH NO, EVERYTHING IS ON FIRE! 全部 {total} 个测试都倒下了！",
        "The dandelion broke. All {total} tests failed!",
        "I'm scared! All {total} tests exploded like my baking soda volcano!",
        "I flunked the test! ALL {total} of them! Like me in school!",
    ],
    "start": [
        "Hi! I'm Ralph! Let's test bazi-pro!",
        "I'm going to push the test button! Here goes!",
        "It tastes like... testing! Running now!",
        "Me fail tests? That's unpossible! Let's go!",
        "I'm a scientist! Running bazi-pro tests now!",
        "My hair is on fire to test! Let's begin!",
        "Principal Skinner asked me to test this program! Starting!",
    ],
    "fix_hint": [
        "Help! I need a grown-up to look at the stack trace!",
        "Maybe try `git diff` to see what you broke?",
        "Principal Skinner says look at the last file you edited!",
        "My doctor said: `pytest -v --tb=long` would help!",
        "If you're stuck, `bazi-doctor` might know what's wrong!",
    ],
    "healing": [
        "I'm healing! Tests passed? No wait, that was before...",
        "My sandbox is recovering! Running again...",
        "Me and my glue stick will fix these tests! Re-running...",
        "The leprechaun told me to retry!",
    ],
}


def ralph_say(quote: str) -> str:
    """Wrap a quote in Ralph's speech bubble."""
    bar = "─" * min(len(quote) + 4, 72)
    return f"""
┌{bar}┐
│  {quote}  │
└{bar}┘
"""


def random_quote(category: str, **fmt) -> str:
    quotes = RALPH_QUOTES.get(category, ["..."])
    return random.choice(quotes).format(**fmt)


def run_tests(quick: bool = False) -> dict:
    """Run the project test suite. Returns {passed, failed, total, output}."""

    if quick:
        cmd = [sys.executable, str(PROJECT_ROOT / "tests" / "run_golden.py")]
    else:
        cmd = [
            sys.executable, "-m", "pytest",
            str(PROJECT_ROOT / "tests"),
            "-v", "--tb=short",
            "-p", "no:cacheprovider",
        ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return {"passed": 0, "failed": "?", "total": "?", "output": "TIMEOUT! Tests ran too long!", "crashed": True}

    # Parse test summary — supports both pytest and goldens formats
    passed = failed = total = 0
    import re

    for line in output.splitlines():
        m_pytest = re.search(r'(\d+)\s+passed.*?(\d+)\s+failed', line)
        if m_pytest:
            passed = int(m_pytest.group(1))
            failed = int(m_pytest.group(2))
            total = passed + failed
            break

    # Golden test format: "3/4 通过"
    if total == 0:
        m_gold = re.search(r'(\d+)/(\d+)\s*通过', output)
        if m_gold:
            passed = int(m_gold.group(1))
            total = int(m_gold.group(2))
            failed = total - passed

    # Fallback: count emoji result markers
    if total == 0:
        passed = output.count("✅") + output.count(" PASSED")
        failed = output.count("❌") + output.count(" FAILED")
        total = passed + failed

    # Detect pytest not installed or other issues
    if total == 0:
        if "No module named pytest" in output or "ModuleNotFoundError" in output:
            return {
                "passed": 0, "failed": 0, "total": 0,
                "output": output,
                "crashed": True,
                "hint": "pytest not installed. Try: pip install pytest\nOr use --quick for golden cases.",
            }

    return {"passed": passed, "failed": failed, "total": total, "output": output, "crashed": False}


def get_changed_files(watched_dirs: list[Path]) -> set:
    """Check for recently modified .py files (last 2 seconds)."""
    recent = set()
    cutoff = time.time() - 2
    for d in watched_dirs:
        if not d.exists():
            continue
        for f in d.rglob("*.py"):
            try:
                if f.stat().st_mtime > cutoff:
                    recent.add(f)
            except OSError:
                pass
    return recent


def print_banner():
    print(r"""
╔══════════════════════════════════════════════╗
║     RALPH WIGGUM TEST LOOP                  ║
║   bazi-pro 八字命理持续测试看护器              ║
║   "I'm helping!"                            ║
╚══════════════════════════════════════════════╝
""")


def main():
    parser = argparse.ArgumentParser(description="Ralph Wiggum Loop — bazi-pro 持续测试看护器")
    parser.add_argument("--watch", action="store_true", help="监视文件变更，自动重跑测试")
    parser.add_argument("--interval", type=int, default=10, help="轮询间隔（秒），默认 10")
    parser.add_argument("--forever", action="store_true", help="无限循环")
    parser.add_argument("--until-pass", action="store_true", help="一直跑到全部通过为止")
    parser.add_argument("--quick", action="store_true", help="只跑 golden cases（快速模式）")
    parser.add_argument("--count", type=int, default=0, help="跑 N 轮后退出（0=无限）")

    args = parser.parse_args()

    if not args.watch and not args.forever and not args.until_pass and args.count == 0:
        print_banner()
        print(ralph_say(random_quote("start")))
        result = run_tests(quick=args.quick)

        if result.get("crashed"):
            print(ralph_say("Tests went boom! Like my baking soda volcano!"))
            if result.get("hint"):
                print(f"  {result['hint']}")
            return 1

        print(f"\n  Passed: {result['passed']}  Failed: {result['failed']}")

        if result["failed"] == 0 and result["passed"] > 0:
            print(ralph_say(random_quote("all_pass")))
        elif result["failed"] > 0:
            print(ralph_say(random_quote("some_fail", fail_count=result["failed"])))
            print(ralph_say(random_quote("fix_hint")))

        return 0 if result["failed"] == 0 else 1

    # Loop mode
    print_banner()
    print(f"  Watch mode: {'ON' if args.watch else 'OFF'}")
    print(f"  Interval: {args.interval}s")
    print(f"  Mode: {'until-pass' if args.until_pass else 'forever' if args.forever else f'{args.count} rounds'}")
    print()

    watched_dirs = [
        PROJECT_ROOT / "bazi_pro",
        PROJECT_ROOT / "tests",
        PROJECT_ROOT / "server",
        PROJECT_ROOT / "plugins",
        PROJECT_ROOT / "scripts",
    ]

    round_num = 0
    total_passed = 0
    total_failed = 0
    streak = 0
    best_streak = 0

    try:
        while True:
            round_num += 1

            if args.watch:
                changed = get_changed_files(watched_dirs)
                if not changed:
                    sys.stdout.write(f"\r  Ralph is watching... (round {round_num}, streak: {streak})  ")
                    sys.stdout.flush()
                    time.sleep(args.interval)
                    continue
                print(f"\n  Detected changes: {len(changed)} file(s)")
                for f in sorted(changed):
                    print(f"     └─ {f.relative_to(PROJECT_ROOT)}")
                print()

            print(f"  -- Round {round_num} --")
            print(ralph_say(random_quote("start")))

            result = run_tests(quick=args.quick)

            if result.get("crashed"):
                print(ralph_say("Tests went boom! Like my baking soda volcano!"))
                if result.get("hint"):
                    print(f"  {result['hint']}")
                total_failed += 1
                streak = 0
                time.sleep(args.interval)
                continue

            print(f"  Passed: {result['passed']}  Failed: {result['failed']}")

            if result["failed"] == 0 and result["passed"] > 0:
                print(ralph_say(random_quote("all_pass")))
                streak += 1
                total_passed += 1
                if streak > best_streak:
                    best_streak = streak
                    if best_streak >= 3:
                        print(f"  New streak record: {best_streak} rounds without failure!")

                if args.until_pass:
                    print(f"\n  All passed after {round_num} rounds! Ralph is happy!")
                    print(f"  Best streak: {best_streak}")
                    return 0

            elif result["failed"] > 0:
                print(ralph_say(random_quote("some_fail", fail_count=result["failed"])))
                if random.random() < 0.3:
                    print(ralph_say(random_quote("fix_hint")))
                streak = 0
                total_failed += 1

                if args.until_pass and args.watch:
                    print(ralph_say(random_quote("healing")))

            print(f"  Summary: {total_passed} green | {total_failed} red | best streak: {best_streak}")
            print()

            if args.count > 0 and round_num >= args.count:
                print(f"  Reached {args.count} rounds. Ralph goes home now.")
                return 0 if total_failed == 0 else 1

            if not args.watch:
                time.sleep(args.interval)

    except KeyboardInterrupt:
        print(f"\n\n  Ralph says goodbye! {total_passed} wins, {total_failed} losses, best streak: {best_streak}")
        print("  'My cat's breath smells like cat food!'")
        return 0


if __name__ == "__main__":
    sys.exit(main())
