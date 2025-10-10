#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""
Module: tools/docops_prose_format.py
Purpose: Phase 4 — Documentation Language & Formatting Consistency

- Check canonical README section order
- Run markdownlint (if installed) and prettier (if installed) in dry-run
- Flag forbidden terms in OSS context (e.g., "Enterprise" claims)
- Emit docs/reports/PROSE_FORMAT_AUDIT.md
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import List
from datetime import datetime, timezone

README_ORDER = [
    "# ",  # title
    "## 🚀 Quick Start",
    "## Installation",
    "## Usage",
    "## Contributing",
    "## License",
    "## Security",
]

FORBIDDEN_TERMS = [
    re.compile(r"\bEnterprise\b", re.I),
]


def has_section_order(text: str, order: List[str]) -> bool:
    idx = -1
    for marker in order:
        pos = text.find(marker)
        if pos == -1 or pos < idx:
            return False
        idx = pos
    return True


def shell(cmd: str) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return p.returncode, (p.stdout + "\n" + p.stderr)
    except Exception as e:
        return 1, str(e)


def main() -> int:
    root = Path(os.environ.get("DOCOPS_REPO_ROOT", ".")).resolve()
    reports = root / "docs" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    md: List[str] = []
    md.append("# Prose & Formatting Audit\n\n")
    md.append(f"Generated: {datetime.now(timezone.utc).isoformat()}\n\n")

    # README order
    readme = root / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8", errors="ignore")
        order_ok = has_section_order(text, README_ORDER)
        md.append(f"README canonical order: {'OK' if order_ok else 'MISMATCH'}\n\n")
    else:
        md.append("README.md not found\n\n")

    # Forbidden terms pass
    violations: List[str] = []
    for p in (root / "docs").rglob("*.md"):
        txt = p.read_text(encoding="utf-8", errors="ignore")
        for pat in FORBIDDEN_TERMS:
            if pat.search(txt):
                violations.append(str(p))
                break
    md.append(f"Forbidden term violations: {len(violations)}\n\n")
    if violations:
        md.append("## Violations\n")
        for v in violations[:200]:
            md.append(f"- {v}\n")
        md.append("\n")

    # markdownlint/prettier (if available)
    if shutil.which("markdownlint"):
        code, out = shell("markdownlint docs/**/*.md")
        md.append("markdownlint: " + ("OK" if code == 0 else "ISSUES FOUND") + "\n\n")
        if code != 0:
            md.append("```")
            md.append(out[:4000])
            md.append("```\n\n")
    else:
        md.append("markdownlint: not installed\n\n")

    if shutil.which("prettier"):
        code, out = shell("prettier -c docs/**/*.md")
        md.append("prettier: " + ("OK" if code == 0 else "ISSUES FOUND") + "\n\n")
        if code != 0:
            md.append("```")
            md.append(out[:4000])
            md.append("```\n\n")
    else:
        md.append("prettier: not installed\n\n")

    (reports / "PROSE_FORMAT_AUDIT.md").write_text("".join(md), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
