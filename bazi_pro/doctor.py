#!/usr/bin/env python3
"""
bazi doctor — 环境诊断工具
检查 bazi-pro v5.0 运行环境，列出各组件状态
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _check_python():
    v = sys.version_info
    ok = v >= (3, 10)
    return ok, f"{v.major}.{v.minor}.{v.micro}"


def _check_jieba():
    try:
        import jieba  # noqa: F401
        return True, "installed"
    except ImportError:
        return False, "missing (pip install jieba)"


def _check_corpus(corpus_path: str = None):
    if not corpus_path:
        candidates = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "classical_corpus.md"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "classical_corpus.md"),
            os.path.join(os.path.expanduser("~"), ".hermes", "skills", "bazi-pro", "references", "classical_corpus.md"),
        ]
        corpus_path = next((c for c in candidates if os.path.exists(c)), None)
    if not corpus_path or not os.path.exists(corpus_path):
        return False, "missing"
    with open(corpus_path, encoding="utf-8") as f:
        count = sum(1 for line in f if line.startswith("["))
    is_fallback = "references" in corpus_path
    detail = f"{count} entries"
    if is_fallback:
        detail += " (fallback: using references/ not package data)"
    return True, detail


def _check_bm25_cache(corpus_path: str = None):
    try:
        from bazi_pro.retrieve_classical import _cache_path, _resolve_corpus
        cp = corpus_path or _resolve_corpus()
        cf = _cache_path(cp)
        if os.path.exists(cf):
            size_kb = os.path.getsize(cf) / 1024
            return True, f"warm ({size_kb:.0f} KB)"
        return False, "cold (will build on first run)"
    except Exception:
        return False, "unknown"


def _check_dashboard():
    try:
        from bazi_pro.dashboard import generate_dashboard  # noqa: F401
        return True, "OK"
    except ImportError:
        return False, "missing"


def _check_markdown():
    try:
        import markdown  # noqa: F401
        return True, "installed"
    except ImportError:
        return True, "stdlib fallback"


def _check_weasyprint():
    try:
        import weasyprint  # noqa: F401
        return True, "installed"
    except (ImportError, OSError):
        return False, "PDF disabled"


def _check_hybrid():
    try:
        import faiss  # noqa: F401
        import numpy  # noqa: F401
        import sentence_transformers  # noqa: F401
        return True, "ready"
    except ImportError:
        return False, "downgraded to BM25-only"


def _check_examples():
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples")
    if os.path.isdir(d):
        files = os.listdir(d)
        return True, f"{len(files)} files"
    return False, "missing"


def check_pyproject_packages():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pyproject_path = os.path.join(project_root, "pyproject.toml")
    if not os.path.exists(pyproject_path):
        return "WARN", "pyproject.toml not found (wheel install — skip)"
    with open(pyproject_path, encoding="utf-8") as f:
        content = f.read()
    if "[tool.setuptools.packages.find]" in content:
        return "PASS", "auto-discovery configured"
    if "[tool.setuptools.packages]" in content:
        if "bazi_pro.core" in content:
            return "WARN", "manual list but bazi_pro.core included"
        return "FAIL", "manual list missing bazi_pro.core"
    return "WARN", "no package config found"


def check_core_imports():
    results = []
    specs = [
        ("bazi_pro.core", "full_analysis"),
        ("bazi_pro.core_rules", "full_analysis"),
        ("bazi_pro", "AnalysisEngine"),
    ]
    for mod_name, attr in specs:
        try:
            mod = __import__(mod_name, fromlist=[attr])
            obj = getattr(mod, attr, None)
            if obj is None:
                results.append((f"{mod_name}.{attr}", "FAIL (attribute missing)"))
            else:
                results.append((f"{mod_name}.{attr}", "PASS"))
        except ImportError as e:
            results.append((f"{mod_name}.{attr}", f"FAIL (import error: {e})"))
    any_fail = any("FAIL" in r[1] for r in results)
    detail = "; ".join(f"{name}: {status}" for name, status in results)
    return ("FAIL" if any_fail else "PASS"), detail


def check_analysis_engine():
    try:
        from bazi_pro import AnalysisEngine
        engine = AnalysisEngine(corpus_path='')
        result = engine.analyze({"八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁", "性别": "女"})
        if result.get("status") != "completed":
            return "FAIL", f"analyze returned status={result.get('status')}"
        required_keys = ["core_analysis", "pattern", "yongshen", "element_forces", "relations",
                         "elements", "quick_element_counts", "quick_element_pct"]
        missing = [k for k in required_keys if k not in result]
        if missing:
            return "FAIL", f"missing keys: {missing}"
        pattern_name = result.get("pattern", {}).get("name", "")
        if pattern_name == "待LLM分析":
            return "FAIL", "pattern name is LLM placeholder"
        ws = result.get("core_analysis", {}).get("wangshuai", {})
        verdict = ws.get("verdict", "")
        if not verdict:
            return "FAIL", "wangshuai verdict is empty"
        if '旺' in verdict and not ws.get("is_strong"):
            return "FAIL", f"wangshuai verdict='{verdict}' but is_strong=False"
        if '弱' in verdict and not ws.get("is_weak"):
            return "FAIL", f"wangshuai verdict='{verdict}' but is_weak=False"
        return "PASS", f"pattern={pattern_name}, wangshuai={verdict}"
    except Exception as e:
        return "FAIL", str(e)


def check_full_analysis_smoke():
    try:
        from bazi_pro.core_rules import full_analysis
        result = full_analysis({"八字": "壬午 乙巳 丁亥 癸卯", "日主": "丁"})
        if result.get("status") != "completed":
            return "FAIL", f"full_analysis returned status={result.get('status')}"
        required_keys = ["deling", "dedi", "deshi", "wangshuai", "element_forces",
                         "relations", "pattern", "yongshen", "pillars"]
        missing = [k for k in required_keys if k not in result]
        if missing:
            return "FAIL", f"missing keys: {missing}"
        ws = result["wangshuai"]
        if not ws.get("verdict"):
            return "FAIL", "wangshuai verdict is empty"
        if ws.get("is_extreme_strong") and ws.get("verdict") != "极旺":
            return "FAIL", f"is_extreme_strong=True but verdict='{ws['verdict']}'"
        if ws.get("is_extreme_weak") and ws.get("verdict") != "极弱":
            return "FAIL", f"is_extreme_weak=True but verdict='{ws['verdict']}'"
        return "PASS", f"wangshuai={ws['verdict']}, pattern={result['pattern']['pattern']}"
    except Exception as e:
        return "FAIL", str(e)


def check_golden_cases_count():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    golden_dir = os.path.join(project_root, "tests", "golden_cases")
    if not os.path.isdir(golden_dir):
        return "WARN", "golden_cases directory not found (wheel install — skip)"
    count = len([f for f in os.listdir(golden_dir) if f.endswith(".json")])
    if count < 12:
        return "FAIL", f"{count} (critical minimum: 12)"
    if count < 50:
        return "WARN", f"{count} (recommended: 50+)"
    return "PASS", f"{count}"


def check_no_llm_placeholder():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    found = []
    for search_dir in ["bazi_pro", "server"]:
        dir_path = os.path.join(project_root, search_dir)
        if not os.path.isdir(dir_path):
            continue
        for root, dirs, files in os.walk(dir_path):
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(root, fname)
                if fpath == os.path.abspath(__file__):
                    continue
                try:
                    with open(fpath, encoding="utf-8") as f:
                        for i, line in enumerate(f, 1):
                            if "待LLM分析" in line:
                                rel = os.path.relpath(fpath, project_root)
                                found.append(f"{rel}:{i}")
                except Exception:
                    pass
    if found:
        return "FAIL", f'found "待LLM分析" in {" ".join(found)}'
    return "PASS", "no LLM placeholders found"


def check_circular_deps():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    core_dir = os.path.join(project_root, "bazi_pro", "core")
    if not os.path.isdir(core_dir):
        return "FAIL", "bazi_pro/core/ not found"
    found = []
    for root, dirs, files in os.walk(core_dir):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        if re.search(r"from\s+bazi_pro\s+import", line):
                            rel = os.path.relpath(fpath, project_root)
                            found.append(f"{rel}:{i}")
            except Exception:
                pass
    if found:
        return "FAIL", "circular import in " + " ".join(found)
    return "PASS", "no circular deps in bazi_pro/core/"


def check_corpus_in_package():
    try:
        from importlib.resources import files
        data_dir = files("bazi_pro.data")
        corpus = data_dir.joinpath("classical_corpus.md")
        if corpus.is_file():
            return "PASS", "classical_corpus.md in bazi_pro.data"
        return "WARN", "classical_corpus.md not found in bazi_pro.data (using fallback path)"
    except Exception as e:
        return "WARN", f"importlib.resources check failed: {e}"


def main():
    print("bazi-pro v5.0 — 环境诊断")
    print("=" * 40)

    env_checks = [
        ("Python", *_check_python()),
        ("jieba", *_check_jieba()),
        ("Corpus", *_check_corpus()),
        ("BM25 cache", *_check_bm25_cache()),
        ("Dashboard", *_check_dashboard()),
        ("Markdown", *_check_markdown()),
        ("PDF (weasyprint)", *_check_weasyprint()),
        ("Hybrid Search", *_check_hybrid()),
        ("Examples", *_check_examples()),
    ]

    for name, ok, detail in env_checks:
        icon = "✅" if ok else "⚠️ "
        print(f"  {icon} {name}: {detail}")

    print()
    print("一致性检查")
    print("-" * 40)

    consistency_checks = [
        ("pyproject packages", check_pyproject_packages()),
        ("core imports", check_core_imports()),
        ("analysis engine", check_analysis_engine()),
        ("full_analysis smoke", check_full_analysis_smoke()),
        ("golden cases count", check_golden_cases_count()),
        ("no LLM placeholder", check_no_llm_placeholder()),
        ("circular deps", check_circular_deps()),
        ("corpus in package", check_corpus_in_package()),
    ]

    any_fail = False
    for name, (status, detail) in consistency_checks:
        if status == "PASS":
            tag = "[PASS]"
        elif status == "WARN":
            tag = "[WARN]"
        else:
            tag = "[FAIL]"
            any_fail = True
        print(f"  {tag} {name}: {detail}")

    print()
    if any_fail:
        print("❌ 存在 FAIL 项，请修复")
        return 1
    else:
        print("✅ 所有检查通过（可能有 WARN 项）")
        return 0


if __name__ == "__main__":
    sys.exit(main())
