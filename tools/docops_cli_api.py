#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""
Module: tools/docops_cli_api.py
Purpose: Phase 2 — CLI & API Parity Validation (regex-only)

- Extract all CLI commands referenced in documentation (patterns: `ioa ...` in bash fences)
- Enumerate actual CLI commands from src/ioa_core/cli.py using regex (no imports)
- Produce diff report of documented vs actual
- If OpenAPI spec found (openapi.*), list presence (no HTTP validation here)

Outputs:
  - docs/reports/CLI_API_DIFF.md
  - docs/reports/OPENAPI_VALIDATION.json
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set

DOC_CMD_RE = re.compile(r"^ioa\s+[\w:-]+(?:\s+[-\w=/:.]+)*", re.M)
FENCE_BASH = re.compile(r"```(?:bash|sh)\n([\s\S]*?)```", re.M)

# Regexes to infer click commands from source text
RE_GROUP_DEF = re.compile(r"@click\.group\((?:.|\n)*?\)\s*def\s+(?P<fn>\w+)\(")
RE_GROUP_NAME = re.compile(r"@click\.group\((?:.|\n)*?name=\"(?P<name>[^\"]+)\"(?:.|\n)*?\)\s*def\s+\w+\(")
RE_CMD_DEF = re.compile(r"@click\.command\((?:.|\n)*?\)\s*def\s+(?P<fn>\w+)\(")
RE_CMD_NAME = re.compile(r"@click\.(?:command|group)\((?:.|\n)*?name=\"(?P<name>[^\"]+)\"(?:.|\n)*?\)\s*def\s+\w+\(")
RE_ADD_CMD = re.compile(r"(?P<grp>\w+)\.add_command\(\s*(?P<fn>\w+)(?:\s*,\s*name=\"(?P<name>[^\"]+)\")?\s*\)")

@dataclass
class DiffReport:
    documented: List[str]
    implemented: List[str]
    missing_in_cli: List[str]
    undocumented: List[str]


def extract_doc_commands(root: Path) -> List[str]:
    candidates: List[Path] = []
    for base in [root / "docs", root]:
        if base.exists():
            candidates.extend(list(base.rglob("*.md")))
            candidates.extend(list(base.rglob("*.rst")))
    seen: Set[str] = set()
    commands: List[str] = []
    for p in candidates:
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in FENCE_BASH.findall(text):
            for cmd in DOC_CMD_RE.findall(m):
                cmd_norm = re.sub(r"\s+", " ", cmd.strip())
                if cmd_norm not in seen:
                    seen.add(cmd_norm)
                    commands.append(cmd_norm)
    return commands


def extract_cli_commands_from_source(cli_path: Path) -> List[str]:
    if not cli_path.exists():
        return []
    src = cli_path.read_text(encoding="utf-8", errors="ignore")
    implemented: Set[str] = set()

    # Named groups
    for m in RE_GROUP_NAME.finditer(src):
        implemented.add(f"ioa {m.group('name')}")
    for m in RE_GROUP_DEF.finditer(src):
        implemented.add(f"ioa {m.group('fn')}")

    # Named commands
    for m in RE_CMD_NAME.finditer(src):
        implemented.add(f"ioa {m.group('name')}")
    for m in RE_CMD_DEF.finditer(src):
        implemented.add(f"ioa {m.group('fn')}")

    # Added commands to groups
    for m in RE_ADD_CMD.finditer(src):
        name = m.group('name') or m.group('fn')
        if name:
            implemented.add(f"ioa {name}")

    return sorted(implemented)


def extract_all_cli_commands(repo_root: Path) -> List[str]:
    implemented: Set[str] = set()
    scan_dirs = ["src", "adapters", "cli", "ioa-core-public/src"]
    for d in scan_dirs:
        base = repo_root / d
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            try:
                src = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            # Quick filter to skip files without click decorators
            if "@click.command" not in src and "@click.group" not in src and ".add_command(" not in src:
                continue
            for cmd in extract_cli_commands_from_source(p):
                implemented.add(cmd)
    return sorted(implemented)


def find_openapi_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for pat in ("openapi.yaml", "openapi.yml", "openapi.json"):
        for p in root.rglob(pat):
            files.append(p)
    return files


def main() -> int:
    repo_root = Path(os.environ.get("DOCOPS_REPO_ROOT", ".")).resolve()
    reports_dir = repo_root / "docs" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    documented = extract_doc_commands(repo_root)
    implemented = extract_all_cli_commands(repo_root)

    missing_in_cli = sorted([c for c in documented if not any(c.startswith(impl) for impl in implemented)])
    undocumented = sorted([c for c in implemented if not any(doc.startswith(c) for doc in documented)])

    diff = DiffReport(documented, implemented, missing_in_cli, undocumented)

    md = ["# CLI ↔ Docs Parity Report\n\n"]
    md.append(f"- Documented commands: {len(documented)}\n")
    md.append(f"- Implemented commands: {len(implemented)}\n")
    md.append(f"- Missing in CLI: {len(missing_in_cli)}\n")
    md.append(f"- Undocumented: {len(undocumented)}\n\n")

    if missing_in_cli:
        md.append("## Missing in CLI\n")
        for c in missing_in_cli:
            md.append(f"- {c}\n")
        md.append("\n")
    if undocumented:
        md.append("## Undocumented CLI Commands\n")
        for c in undocumented:
            md.append(f"- {c}\n")
        md.append("\n")

    (reports_dir / "CLI_API_DIFF.md").write_text("".join(md), encoding="utf-8")

    # OpenAPI presence
    openapi_files = find_openapi_files(repo_root)
    openapi_report = {
        "found": [str(p) for p in openapi_files],
        "validated": [],
        "note": None if openapi_files else "No OpenAPI spec found in repository",
    }
    (reports_dir / "OPENAPI_VALIDATION.json").write_text(json.dumps(openapi_report, indent=2), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
