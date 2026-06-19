#!/usr/bin/env python3
"""
变异测试脚本 — 使用 mutmut 对核心模块进行变异测试

用法：
    python scripts/run_mutation_test.py                    # 运行所有核心模块
    python scripts/run_mutation_test.py --module elements  # 运行指定模块
    python scripts/run_mutation_test.py --quick            # 快速模式（仅 10 个变异）

变异测试通过修改代码中的算术运算符、比较运算符、常量等，
检查测试套件是否能检测到这些变化（杀死变异体）。

变异得分 = 被杀死的变异体数 / 总变异体数 × 100%

目标：核心计算模块变异得分 ≥ 80%
"""

import argparse
import subprocess
import sys


CORE_MODULES = [
    'bazi_pro/core/elements.py',
    'bazi_pro/core/strength.py',
    'bazi_pro/core/patterns.py',
    'bazi_pro/core/yongshen.py',
    'bazi_pro/core/relations.py',
    'bazi_pro/core/disease.py',
    'bazi_pro/core/tiaohou.py',
    'bazi_pro/validation.py',
]

TEST_COMMAND = 'python -m pytest tests/test_core.py tests/test_validation.py tests/test_full_analysis.py -x -q'


def run_mutation_test(modules=None, quick=False, timeout=300):
    """运行变异测试

    Args:
        modules: 要测试的模块列表，默认为所有核心模块
        quick: 快速模式，仅运行少量变异
        timeout: 每个变异的超时时间（秒）
    """
    if modules is None:
        modules = CORE_MODULES

    print("=" * 60)
    print("bazi-pro 变异测试")
    print("=" * 60)
    print(f"\n目标模块: {', '.join(modules)}")
    print(f"测试命令: {TEST_COMMAND}")
    print(f"超时: {timeout}s")
    if quick:
        print("模式: 快速（仅 10 个变异）")
    print()

    # 检查 mutmut 是否安装
    try:
        subprocess.run(['mutmut', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ mutmut 未安装。请运行: pip install mutmut")
        sys.exit(1)

    # 构建 mutmut 命令
    cmd = ['mutmut', 'run']

    # 指定要变异的路径
    for module in modules:
        cmd.extend(['--paths-to-mutate', module])

    # 指定测试命令
    cmd.extend(['--tests-dir', 'tests'])

    # 快速模式
    if quick:
        cmd.extend(['--max-children', '10'])

    # 超时
    cmd.extend(['--timeout', str(timeout)])

    print(f"执行: {' '.join(cmd)}")
    print("-" * 60)

    try:
        result = subprocess.run(cmd, cwd='.', timeout=timeout * 20)
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        print(f"\n⚠️  变异测试超时（{timeout * 20}s）")
        exit_code = 1
    except KeyboardInterrupt:
        print("\n⚠️  用户中断")
        exit_code = 130

    # 显示结果
    print("\n" + "=" * 60)
    print("变异测试结果")
    print("=" * 60)

    try:
        result = subprocess.run(['mutmut', 'results'], capture_output=True, text=True)
        print(result.stdout)
    except Exception:
        pass

    return exit_code


def show_results():
    """显示变异测试结果"""
    try:
        subprocess.run(['mutmut', 'results'])
    except Exception as e:
        print(f"无法获取结果: {e}")


def main():
    parser = argparse.ArgumentParser(description='bazi-pro 变异测试')
    parser.add_argument('--module', '-m', nargs='+',
                        help='要测试的模块（默认：所有核心模块）')
    parser.add_argument('--quick', '-q', action='store_true',
                        help='快速模式（仅 10 个变异）')
    parser.add_argument('--timeout', '-t', type=int, default=300,
                        help='每个变异的超时时间（秒，默认 300）')
    parser.add_argument('--results', '-r', action='store_true',
                        help='仅显示上次测试结果')

    args = parser.parse_args()

    if args.results:
        show_results()
        return 0

    modules = args.module if args.module else None
    return run_mutation_test(modules=modules, quick=args.quick, timeout=args.timeout)


if __name__ == '__main__':
    sys.exit(main())
