"""bazi-pro 评测系统 CLI 入口

用法:
    python -m benchmarks download              # 下载数据集
    python -m benchmarks run baziqa            # 运行 BaziQA 评测
    python -m benchmarks run baziqa --year 2025 --max 5
    python -m benchmarks run ziwei             # 运行紫微斗数评测
    python -m benchmarks score                 # 评分
    python -m benchmarks stats                 # 统计报告
    python -m benchmarks list                  # 列出已有结果
    python -m benchmarks calibrate baseline    # 基线跑分报告
    python -m benchmarks calibrate analyze     # 错题分析
    python -m benchmarks calibrate convert     # 错题转 golden case
"""
import argparse
import json
import sys


def cmd_download(args):
    from benchmarks.download import download_all
    download_all()


def cmd_run(args):
    benchmark = args.benchmark
    if benchmark == "baziqa":
        from benchmarks.runners.baziqa_runner import run_baziqa
        years = [int(y) for y in args.year.split(",")] if args.year else None
        run_baziqa(years=years, max_persons=args.max, school=args.school)
    elif benchmark == "ziwei":
        from benchmarks.runners.ziwei_runner import run_ziwei
        years = [int(y) for y in args.year.split(",")] if args.year else None
        run_ziwei(years=years, max_persons=args.max)
    else:
        print(f"未知评测: {benchmark}")
        print("可用评测: baziqa, ziwei")
        sys.exit(1)


def cmd_score(args):
    from benchmarks.scoring.extractor import extract_answer, load_ground_truth
    from benchmarks.config import BAZIQA_DIR, RESULTS_DIR

    results = sorted(RESULTS_DIR.glob("baziqa_*.json"), reverse=True)
    if not results:
        print("未找到评测结果，请先运行: python -m benchmarks run baziqa")
        sys.exit(1)

    result = json.loads(results[0].read_text(encoding="utf-8"))
    dataset = []
    for f in sorted(BAZIQA_DIR.glob("*.json")):
        try:
            dataset.extend(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass

    gt = load_ground_truth(dataset)
    total = 0
    correct = 0
    details = []

    for person in result.get("results", []):
        if person.get("status") != "completed":
            continue
        for qid, reply in person.get("answers", {}).items():
            if qid not in gt:
                continue
            extracted = extract_answer(reply)
            is_correct = extracted == gt[qid]
            total += 1
            if is_correct:
                correct += 1
            details.append({
                "question_id": qid,
                "expected": gt[qid],
                "extracted": extracted,
                "correct": is_correct,
                "reply_preview": reply[:100],
            })

    score_output = {
        "total": total,
        "correct": correct,
        "accuracy": correct / total if total > 0 else 0,
        "details": details,
    }
    from benchmarks.config import RESULTS_DIR
    out = RESULTS_DIR / "baziqa_score.json"
    out.write_text(json.dumps(score_output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n评分完成: {correct}/{total} = {score_output['accuracy']:.1%}")
    print(f"详细结果: {out}")


def cmd_stats(args):
    from benchmarks.scoring.stats import compute_stats, print_stats, save_stats
    stats = compute_stats()
    if stats:
        print_stats(stats)
        save_stats(stats)


def cmd_list(args):
    from benchmarks.config import RESULTS_DIR
    files = sorted(RESULTS_DIR.glob("*.json"), reverse=True)
    if not files:
        print("暂无评测结果")
        return
    print(f"\n{'文件名':<45} {'大小':>8}")
    print("-" * 55)
    for f in files[:20]:
        size = f.stat().st_size
        print(f"  {f.name:<43} {size:>7}B")


def cmd_calibrate(args):
    action = args.cal_action
    if action == "baseline":
        from benchmarks.calibrator.baseline import compute_baseline, generate_markdown_report, save_report
        from benchmarks.calibrator.baseline import load_dataset, load_latest_result
        result = load_latest_result()
        if not result:
            print("未找到评测结果，请先运行: python -m benchmarks run baziqa")
            sys.exit(1)
        dataset = load_dataset()
        baseline = compute_baseline(result, dataset)
        report = generate_markdown_report(baseline)
        save_report(baseline, report)
        print(report)
    elif action == "analyze":
        from benchmarks.calibrator.baseline import compute_baseline, load_dataset, load_latest_result
        from benchmarks.calibrator.analyzer import analyze_errors, print_error_report
        result = load_latest_result()
        if not result:
            print("未找到评测结果，请先运行: python -m benchmarks run baziqa")
            sys.exit(1)
        dataset = load_dataset()
        baseline = compute_baseline(result, dataset)
        clusters = analyze_errors(baseline)
        print_error_report(clusters)
    elif action == "convert":
        from benchmarks.calibrator.baseline import compute_baseline, load_dataset, load_latest_result
        from benchmarks.calibrator.case_converter import convert_errors_to_golden_cases
        from benchmarks.config import RESULTS_DIR
        result = load_latest_result()
        if not result:
            print("未找到评测结果，请先运行: python -m benchmarks run baziqa")
            sys.exit(1)
        dataset = load_dataset()
        baseline = compute_baseline(result, dataset)
        output_dir = RESULTS_DIR / "golden_cases"
        output_dir.mkdir(parents=True, exist_ok=True)
        count = convert_errors_to_golden_cases(baseline, dataset, output_dir)
        print(f"已生成 {count} 个 golden case 到 {output_dir}")
    else:
        print(f"未知校准操作: {action}")
        print("可用操作: baseline, analyze, convert")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(prog="benchmarks", description="bazi-pro 命理评测系统")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("download", help="下载数据集")

    p_run = sub.add_parser("run", help="运行评测")
    p_run.add_argument("benchmark", choices=["baziqa", "ziwei"], help="评测类型")
    p_run.add_argument("--year", help="年份过滤，逗号分隔")
    p_run.add_argument("--max", type=int, default=0, help="最大命主数")
    p_run.add_argument("--school", default="ziping", help="流派")

    sub.add_parser("score", help="评分")
    sub.add_parser("stats", help="统计报告")
    sub.add_parser("list", help="列出已有结果")

    p_cal = sub.add_parser("calibrate", help="校准工具")
    p_cal.add_argument("cal_action", choices=["baseline", "analyze", "convert"], help="校准操作")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmds = {
        "download": cmd_download,
        "run": cmd_run,
        "score": cmd_score,
        "stats": cmd_stats,
        "list": cmd_list,
        "calibrate": cmd_calibrate,
    }
    cmds[args.command](args)


if __name__ == "__main__":
    main()
