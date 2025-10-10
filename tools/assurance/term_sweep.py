""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""Module docstring:
This tool performs a guarded terminology sweep replacing 'assurance' with 'assurance' in
living docs and UI copy, while excluding archives and historical materials.

Public CLI:
- python -m tools.assurance.term_sweep --dry-run
- python -m tools.assurance.term_sweep --apply
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List, Tuple

EXCLUDES = [
    "docs/ops/qa_archive/",
    "docs/ops/status_reports/STATUS_REPORT_GOV_assurance_SCORECARD_20250913.md",
    "docs/ops/status_reports/STATUS_REPORT_*20250913*.md",
    "artifacts/",
    "site/",
]

INCLUDES = [
    "README.md",
    "docs/ops/ci/CI_GATES_V1.md",
    "docs/ops/ci/CI_GATES_V1_COMMENT_TPL.md.j2",
    "docs/ops/status_reports/",
    "docs/governance/",
    "tools/ci/render_comment.py",
    "src/cli/main.py",
]

REPLACE_MAP = [
    ("assurance Score", "Assurance Score"),
    ("assurance score", "assurance score"),
    ("assurance", "assurance"),
]


def should_exclude(p: Path) -> bool:
    s = str(p)
    for ex in EXCLUDES:
        if ex.endswith("*"):
            if s.startswith(ex[:-1]):
                return True
        elif ex in s:
            return True
    return False


def should_include(p: Path) -> bool:
    root = Path.cwd()
    for inc in INCLUDES:
        ip = root / inc
        try:
            if ip.is_dir() and str(p).startswith(str(ip)):
                return True
            if ip.is_file() and p == ip:
                return True
        except Exception:
            continue
    return False


def sweep(dry_run: bool) -> List[Tuple[str, int]]:
    changes: List[Tuple[str, int]] = []
    root = Path.cwd()
    for path in root.rglob("*.*"):
        if not path.is_file():
            continue
        if should_exclude(path):
            continue
        if not should_include(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        original = text
        replaced_count = 0
        for old, new in REPLACE_MAP:
            text, n = text.replace(old, new), text.count(old)
            replaced_count += n
        if replaced_count > 0:
            changes.append((str(path), replaced_count))
            if not dry_run:
                path.write_text(text, encoding="utf-8")
    return changes


def main():
    parser = argparse.ArgumentParser(description="Guarded terminology sweep: assurance -> assurance")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without applying")
    parser.add_argument("--apply", action="store_true", help="Apply changes")
    args = parser.parse_args()

    if args.dry_run and args.apply:
        print("Use only one of --dry-run or --apply")
        raise SystemExit(2)

    dry = args.dry_run or not args.apply
    changes = sweep(dry)

    print("Terminology Sweep Summary")
    print("========================")
    total = 0
    for f, n in changes[:100]:
        print(f"- {f}: {n} replacements")
        total += n
    if len(changes) > 100:
        print(f"... and {len(changes)-100} more files")
    print(f"Total replacements: {total}")
    print(f"Mode: {'DRY-RUN' if dry else 'APPLY'}")


if __name__ == "__main__":
    main()
