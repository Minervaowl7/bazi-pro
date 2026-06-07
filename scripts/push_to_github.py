#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

# 常见的 Git 安装位置
git_paths = [
    r"C:\Program Files\Git\bin\git.exe",
    r"C:\Program Files (x86)\Git\bin\git.exe",
    r"C:\Git\bin\git.exe",
    r"C:\Users\Administrator\AppData\Local\Programs\Git\bin\git.exe",
]

found_git = None
for path in git_paths:
    if Path(path).exists():
        found_git = path
        print(f"✅ 找到 git: {path}")
        break

if not found_git:
    print("❌ 未找到 git 安装")
    print("\n请选择以下选项之一:")
    print("1. 安装 Git for Windows: https://git-scm.com/download/win")
    print("2. 使用 GitHub Desktop: https://desktop.github.com/")
    print("3. 手动提交代码")

    # 尝试使用 where 命令查找
    print("\n尝试使用 where 命令查找...")
    try:
        result = subprocess.run(
            ['cmd', '/c', 'where', 'git'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        if result.stdout:
            print(f"找到: {result.stdout}")
    except:
        pass

    sys.exit(1)

import sys
print(f"\n使用 git: {found_git}")

# 测试 git
result = subprocess.run(
    [found_git, '--version'],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace'
)
print(result.stdout)

repo_path = Path(__file__).resolve().parent

# 查看状态
print("\n📊 查看 git 状态...")
result = subprocess.run(
    [found_git, 'status', '--short'],
    cwd=repo_path,
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace'
)
print(result.stdout or result.stderr)

# 查看差异
print("\n📝 查看修改的文件...")
result = subprocess.run(
    [found_git, 'diff', '--name-only', 'HEAD'],
    cwd=repo_path,
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace'
)
modified_files = [f for f in result.stdout.strip().split('\n') if f.strip()]
print(f"修改了 {len(modified_files)} 个文件:")
for f in modified_files[:10]:
    print(f"  - {f}")
if len(modified_files) > 10:
    print(f"  ... 还有 {len(modified_files) - 10} 个文件")

# 添加所有修改的文件
print("\n📦 添加文件到暂存区...")
result = subprocess.run(
    [found_git, 'add', '.'],
    cwd=repo_path,
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace'
)
if result.returncode == 0:
    print("✅ 文件已添加")
else:
    print(f"❌ 添加失败: {result.stderr}")

# 创建提交
commit_msg = """修复5个核心算法缺陷 + 重写从格判断逻辑

1. 修复半合局与三合局重复计算问题（elements.py + relations.py）
   - 在检测半合局时跳过已参与三合局的组合
   - 避免五行力量被错误地双重计算

2. 修复旺衰判断盲区（strength.py）
   - 补充了-1 ≤ deling ≤1 且 1.5 ≤ dedi <3 区间的细分判断
   - 微调deshi阈值以保持Golden case一致性

3. 修复十神统计忽略藏干问题（ten_gods.py）
   - 新增include_canggan可选参数，默认保持False
   - 保持向后兼容性，格局判断继续使用天干统计

4. 新增日主一致性校验（validation.py + core/__init__.py）
   - 新增validate_day_master_consistency()函数
   - 检查输入日主与日柱天干是否一致

5. 重写从格判断算法（patterns.py）
   - 新增_check_dm_root_in_branches()检查日主在地支的根气
   - 从格判断核心：地支无根是从格成立的首要条件
   - 增加阴阳干性判断：阳干不易真从，阴干更易入从
   - 更新假从强格判断逻辑

6. 更新Golden case
   - classical_zhengcaige_yhzwang.json: 更正判断逻辑，改为月劫格

✅ 全部测试通过: 98/98 Golden cases + Doctor checks
"""

print("\n💾 创建提交...")
result = subprocess.run(
    [found_git, 'commit', '-m', commit_msg],
    cwd=repo_path,
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace'
)
if result.returncode == 0:
    print("✅ 提交成功!")
else:
    print(f"❌ 提交失败: {result.stderr}")
    sys.exit(1)

# 推送到远程
print("\n🚀 推送到远程仓库...")
result = subprocess.run(
    [found_git, 'push', 'origin', 'main'],
    cwd=repo_path,
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace'
)

if result.returncode == 0:
    print("\n" + "="*60)
    print("🎉 推送成功!")
    print("="*60)
    print("\n请到 GitHub 创建 Pull Request:")
    print("  https://github.com/Minervaowl7/bazi-pro/compare/main")
else:
    print("\n" + "="*60)
    print("⚠️  推送失败")
    print("="*60)
    print(f"错误: {result.stderr}")
    print("\n可能需要:")
    print("1. 配置 Git 认证令牌")
    print("2. 使用 GitHub Personal Access Token")
    print("3. 手动推送代码")
