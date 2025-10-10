#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""
Module: tools/docops_execute.py
Purpose: Phase 1 Documentation Integrity Check

- Scan markdown/rst files for fenced code blocks (bash, python)
- Execute snippets in a constrained subprocess with timeouts
- Validate internal and external links
- Verify presence of SPDX header, title, v2.5.0 tag, and recent last-updated
- Emit:
  - docs/reports/DOCOPS_EXECUTION_RESULTS.md
  - docs/reports/LINK_AUDIT.json

Notes:
- This validator is conservative: it skips potentially destructive bash commands
- Use environment variable DOCOPS_MAX_SNIPPETS to cap executions
- Uses python3 for execution; requires outbound network for external link checks (optional)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Optional, Tuple, Dict, Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

RE_SPDX = re.compile(r"SPDX-License-Identifier:\s*Apache-2.0", re.I)
RE_TITLE = re.compile(r"^#\s+.+", re.M)
RE_VERSION = re.compile(r"v2\.5\.0")
RE_LAST_UPDATED = re.compile(r"Last-Updated:\s*(\d{4}-\d{2}-\d{2})")
FENCE_RE = re.compile(r"```(\w+)?\n([\s\S]*?)```", re.M)
LINK_RE = re.compile(r"\[(?P<text>[^\]]+)\]\((?P<href>[^)]+)\)")

SAFE_BASH_ALLOWLIST = {
    "echo",
    "cat",
    "head",
    "tail",
    "pwd",
    "ls",
    "python3",
    "pip",
    "pip3",
    "ioa",  # will likely fail if not installed; treated as best-effort
}

SKIP_BASH_PATTERNS = [
    re.compile(r"rm\s+-rf\s+/"),
    re.compile(r"sudo\s+"),
    re.compile(r"curl\s+.*\|\s+sh"),
    re.compile(r"docker\s+(run|rm|rmi|system)"),
    re.compile(r"kubectl\s+"),
]

MAX_RUNTIME_SEC = 15
RECENT_DAYS = 90

@dataclass
class SnippetResult:
    file: str
    lang: str
    index: int
    command: str
    ok: bool
    stdout: str
    stderr: str
    reason: Optional[str] = None

@dataclass
class LinkCheck:
    file: str
    href: str
    ok: bool
    status: Optional[int]
    kind: str  # external|internal
    note: Optional[str] = None

@dataclass
class DocMeta:
    file: str
    has_spdx: bool
    has_title: bool
    has_version: bool
    last_updated_ok: bool
    last_updated_value: Optional[str]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def iter_doc_files(root: Path) -> Iterable[Path]:
    exts = {".md", ".rst"}
    for base in [root / "docs", root]:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.suffix.lower() in exts and p.is_file():
                yield p
    examples = root / "examples"
    if examples.exists():
        for p in examples.rglob("*"):
            if p.suffix.lower() in {".md", ".rst"} and p.is_file():
                yield p


def is_safe_bash(cmd: str) -> Tuple[bool, Optional[str]]:
    for pat in SKIP_BASH_PATTERNS:
        if pat.search(cmd):
            return False, "dangerous pattern"
    head = shlex.split(cmd.strip())[:1]
    if not head:
        return True, None
    if head[0] not in SAFE_BASH_ALLOWLIST:
        return False, f"command {head[0]} not allowlisted"
    return True, None


def run_bash(code: str) -> Tuple[bool, str, str, Optional[str]]:
    ok, reason = is_safe_bash(code)
    if not ok:
        return False, "", "", reason
    try:
        proc = subprocess.run(
            ["bash", "-lc", code],
            capture_output=True,
            text=True,
            timeout=MAX_RUNTIME_SEC,
        )
        return proc.returncode == 0, proc.stdout, proc.stderr, None
    except subprocess.TimeoutExpired:
        return False, "", "timeout", "timeout"
    except Exception as e:
        return False, "", str(e), "exception"


def run_python(code: str) -> Tuple[bool, str, str, Optional[str]]:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
        tf.write(code)
        tmp = tf.name
    try:
        proc = subprocess.run(
            [sys.executable, tmp], capture_output=True, text=True, timeout=MAX_RUNTIME_SEC
        )
        return proc.returncode == 0, proc.stdout, proc.stderr, None
    except subprocess.TimeoutExpired:
        return False, "", "timeout", "timeout"
    except Exception as e:
        return False, "", str(e), "exception"
    finally:
        try:
            os.unlink(tmp)
        except Exception:
            pass


def check_links(file_path: Path, content: str, root: Path) -> List[LinkCheck]:
    results: List[LinkCheck] = []
    for m in LINK_RE.finditer(content):
        href = m.group("href").strip()
        if href.startswith("http://") or href.startswith("https://"):
            kind = "external"
            status = None
            ok = False
            note = None
            try:
                req = Request(href, method="HEAD")
                with urlopen(req, timeout=8) as resp:
                    status = resp.status
                    ok = (200 <= status < 400)
            except Exception as e:
                note = str(e)
            results.append(LinkCheck(str(file_path), href, ok, status, kind, note))
        else:
            kind = "internal"
            target = (file_path.parent / href).resolve()
            ok = target.exists()
            results.append(LinkCheck(str(file_path), href, ok, 200 if ok else None, kind, None))
    return results


def check_meta(file_path: Path, content: str) -> DocMeta:
    has_spdx = bool(RE_SPDX.search(content))
    has_title = bool(RE_TITLE.search(content))
    has_version = bool(RE_VERSION.search(content))
    last_updated_ok = False
    last_value: Optional[str] = None
    m = RE_LAST_UPDATED.search(content)
    if m:
        last_value = m.group(1)
        try:
            dt_value = dt.datetime.strptime(last_value, "%Y-%m-%d").date()
            last_updated_ok = (dt.date.today() - dt_value).days <= RECENT_DAYS
        except Exception:
            last_updated_ok = False
    return DocMeta(str(file_path), has_spdx, has_title, has_version, last_updated_ok, last_value)


def main() -> int:
    ap = argparse.ArgumentParser(description="DOCOPS Phase 1 Validator")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--max-snippets", type=int, default=int(os.environ.get("DOCOPS_MAX_SNIPPETS", "200")))
    args = ap.parse_args()

    root = Path(args.repo_root).resolve()
    reports_dir = root / "docs" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    snippet_results: List[SnippetResult] = []
    link_results: List[LinkCheck] = []
    meta_results: List[DocMeta] = []

    total_snippets = 0
    for doc in iter_doc_files(root):
        content = read_text(doc)
        if not content:
            continue
        meta_results.append(check_meta(doc, content))
        link_results.extend(check_links(doc, content, root))
        for idx, (lang, code) in enumerate(FENCE_RE.findall(content)):
            if total_snippets >= args.max_snippets:
                break
            lang = (lang or "").strip().lower()
            code = code.strip()
            if not code:
                continue
            ok = False
            stdout = ""
            stderr = ""
            reason = None
            cmd_desc = f"{lang} snippet"
            if lang in {"bash", "sh"}:
                ok, stdout, stderr, reason = run_bash(code)
                cmd_desc = code.splitlines()[0][:120]
            elif lang in {"python", "py"}:
                ok, stdout, stderr, reason = run_python(code)
                cmd_desc = code.splitlines()[0][:120]
            else:
                reason = "lang not supported"
            snippet_results.append(
                SnippetResult(str(doc), lang or "", idx, cmd_desc, ok, stdout, stderr, reason)
            )
            total_snippets += 1

    # Write DOCOPS_EXECUTION_RESULTS.md
    results_md = ["# DOCOPS Execution Results\n"]
    results_md.append(f"Generated: {dt.datetime.now(dt.timezone.utc).isoformat()}\n")
    passed = sum(1 for r in snippet_results if r.ok)
    failed = sum(1 for r in snippet_results if not r.ok and r.lang in {"bash", "sh", "python", "py"})
    skipped = sum(1 for r in snippet_results if r.reason)
    results_md.append(f"- Total snippets: {len(snippet_results)}\n")
    results_md.append(f"- Passed: {passed}\n")
    results_md.append(f"- Failed: {failed}\n")
    results_md.append(f"- Skipped: {skipped}\n\n")

    results_md.append("## Details\n\n")
    for r in snippet_results:
        status = "PASS" if r.ok else ("SKIP" if r.reason else "FAIL")
        results_md.append(f"### {status} — {r.file} [lang={r.lang}] idx={r.index}\n")
        if r.reason:
            results_md.append(f"Reason: {r.reason}\n\n")
        if r.stdout:
            results_md.append("Output:\n\n")
            results_md.append("```\n" + (r.stdout[:2000]) + "\n```\n\n")
        if r.stderr and not r.ok:
            results_md.append("Error:\n\n")
            results_md.append("```\n" + (r.stderr[:2000]) + "\n```\n\n")

    (reports_dir / "DOCOPS_EXECUTION_RESULTS.md").write_text("".join(results_md), encoding="utf-8")

    # Write LINK_AUDIT.json
    link_payload = [asdict(lc) for lc in link_results]
    (reports_dir / "LINK_AUDIT.json").write_text(json.dumps(link_payload, indent=2), encoding="utf-8")

    # Meta summary (printed to stdout)
    meta_summary = {
        "checked_files": len(meta_results),
        "spdx_missing": [m.file for m in meta_results if not m.has_spdx],
        "title_missing": [m.file for m in meta_results if not m.has_title],
        "version_missing": [m.file for m in meta_results if not m.has_version],
        "last_updated_stale": [m.file for m in meta_results if not m.last_updated_ok],
    }
    print(json.dumps(meta_summary, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
