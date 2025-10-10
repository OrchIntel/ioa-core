#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""
Module: tools/docops_tutorial_audit.py
Purpose: Phase 3 — Tutorial Flow & Narrative Validation

- Locate onboarding/quickstart/tutorial docs
- Validate step order: Environment → Install → Initialize → Run → Audit → Verify
- Attempt dry-run commands (`ioa --help`) if available; otherwise rate clarity based on presence of commands and prerequisites
- Emit docs/reports/TUTORIAL_FLOW_AUDIT.md with ratings
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import List, Tuple
from datetime import datetime, timezone

SECTIONS_ORDER = [
    "environment", "install", "initialize", "run", "audit", "verify"
]

CANDIDATE_FILES = [
    "docs/getting-started/quickstart.md",
    "docs/getting-started/installation.md",
    "docs/ONBOARDING.md",
    "README.md",
]

LOWER = lambda s: s.lower()


def run_cmd(cmd: str, timeout: int = 8) -> Tuple[bool, str]:
    try:
        p = subprocess.run(cmd, shell=True, timeout=timeout, capture_output=True, text=True)
        return p.returncode == 0, (p.stdout + "\n" + p.stderr)[:1000]
    except Exception as e:
        return False, str(e)


def score_doc(path: Path, text: str) -> Tuple[str, List[str]]:
    lines = text.lower().splitlines()
    hits = {k: -1 for k in SECTIONS_ORDER}
    for i, ln in enumerate(lines):
        for k in SECTIONS_ORDER:
            if k in ln:
                if hits[k] == -1:
                    hits[k] = i
    order_ok = True
    last = -1
    for k in SECTIONS_ORDER:
        if hits[k] == -1:
            order_ok = False
            break
        if hits[k] < last:
            order_ok = False
            break
        last = hits[k]
    notes: List[str] = []
    if not order_ok:
        notes.append(f"Section order mismatch or missing: {hits}")
    # Check presence of typical commands
    has_install = "pip install" in text.lower() or "poetry add" in text.lower()
    has_ioa_help = "ioa --help" in text.lower()
    if not has_install:
        notes.append("Install step not clearly stated")
    if not has_ioa_help:
        notes.append("Missing ioa --help reference")
    rating = "✅ clear" if order_ok and has_install and has_ioa_help else ("⚠️ needs edit" if order_ok else "❌ broken")
    return rating, notes


def main() -> int:
    root = Path(os.environ.get("DOCOPS_REPO_ROOT", ".")).resolve()
    reports = root / "docs" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    md: List[str] = []
    md.append("# Tutorial Flow Audit\n\n")
    md.append(f"Generated: {datetime.now(timezone.utc).isoformat()}\n\n")

    # Try a dry-run CLI call if present
    ok, out = run_cmd("ioa --help")
    md.append(f"CLI availability: {'OK' if ok else 'NOT FOUND'}\n\n")

    for rel in CANDIDATE_FILES:
        p = root / rel
        if not p.exists():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        rating, notes = score_doc(p, text)
        md.append(f"## {rel}\n")
        md.append(f"Rating: {rating}\n\n")
        if notes:
            for n in notes:
                md.append(f"- {n}\n")
        md.append("\n")

    (reports / "TUTORIAL_FLOW_AUDIT.md").write_text("".join(md), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
