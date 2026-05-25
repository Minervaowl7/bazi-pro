#!/usr/bin/env python3
"""Version consistency checker for bazi-pro.

Reads the canonical version from pyproject.toml and verifies it matches:
- bazi_pro.__version__
- README.md header
- pyproject.toml [project] version

Usage:
    python scripts/check_version_consistency.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def get_pyproject_version() -> str:
    pyproject = ROOT / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not m:
        print(f"❌ Cannot find version in {pyproject}")
        sys.exit(1)
    return m.group(1)


def check_init_version(expected: str) -> bool:
    init = ROOT / "bazi_pro" / "__init__.py"
    text = init.read_text(encoding="utf-8")
    m = re.search(r'^__version__\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not m:
        print(f"❌ Cannot find __version__ in {init}")
        return False
    actual = m.group(1)
    if actual != expected:
        print(f"❌ bazi_pro/__init__.py version: {actual} != {expected}")
        return False
    print(f"✅ bazi_pro/__init__.py version: {actual}")
    return True


def check_readme_version(expected: str) -> bool:
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    short = f"v{expected.rsplit('.', 1)[0]}"
    if short not in text and expected not in text:
        print(f"❌ README.md does not mention version {expected} or {short}")
        return False
    print(f"✅ README.md mentions {short}")
    return True


def check_pyproject_version(expected: str) -> bool:
    pyproject = ROOT / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    if f'version = "{expected}"' not in text:
        print(f"❌ pyproject.toml does not contain version = \"{expected}\"")
        return False
    print(f"✅ pyproject.toml version: {expected}")
    return True


def main():
    version = get_pyproject_version()
    print(f"Canonical version from pyproject.toml: {version}\n")

    results = [
        check_pyproject_version(version),
        check_init_version(version),
        check_readme_version(version),
    ]

    if all(results):
        print(f"\n✅ All version checks passed for {version}")
        sys.exit(0)
    else:
        print("\n❌ Version consistency check failed")
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
