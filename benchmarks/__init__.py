"""bazi-pro 命理评测系统

支持三个数据集：
- BaziQA: 八字命理选择题评测（450题，90命主）
- MingLi-Bench: 八字+紫微斗数评测（160题）
- fate_benchmark: 完整评测工具链

用法:
    python -m benchmarks download          # 下载数据集
    python -m benchmarks run baziqa        # 运行 BaziQA 评测
    python -m benchmarks run ziwei         # 运行紫微斗数评测
    python -m benchmarks score             # 评分
    python -m benchmarks stats             # 统计报告
"""
