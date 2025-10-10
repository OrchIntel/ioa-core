""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3
# tools/inventory/inventory.py
import os, sys, re, json, csv, hashlib, subprocess, datetime
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
OUTDIR = ROOT / "ops" / "reports" / (datetime.date.today().isoformat() + "-file-inventory")
OUTDIR.mkdir(parents=True, exist_ok=True)

IGNORE_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", "node_modules", ".venv", "venv", ".DS_Store", ".idea", ".eggs", "dist", "build"}
TEXT_EXTS = {".py", ".md", ".yml", ".yaml", ".toml", ".json", ".txt", ".ini", ".cfg", ".env", ".sh", ".bat", ".js", ".ts", ".ipynb"}
BINARY_HINTS = {".png",".jpg",".jpeg",".gif",".pdf",".doc",".docx",".ppt",".pptx",".xls",".xlsx",".so",".dylib",".bin",".pb",".onnx",".tar",".gz",".zip"}

def is_text(path: Path) -> bool:
    suf = path.suffix.lower()
    if suf in TEXT_EXTS: return True
    if suf in BINARY_HINTS: return False
    try:
        with open(path, "rb") as f:
            chunk = f.read(2048)
        return b"\x00" not in chunk
    except Exception:
        return False

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(131072), b""):
            h.update(b)
    return h.hexdigest()

def git(*args):
    return subprocess.check_output(["git"]+list(args), cwd=ROOT, text=True).strip()

def last_commit_info(path: Path):
    try:
        out = git("log","-n","1","--pretty=%ci|%an","--", str(path.relative_to(ROOT)))
        ts, author = out.split("|", 1)
        return ts, author
    except Exception:
        return "", ""

def first_commit_info(path: Path):
    try:
        out = git("log","--diff-filter=A","--pretty=%ci|%an","--",str(path.relative_to(ROOT)))
        if out:
            first = out.splitlines()[-1]
            ts, author = first.split("|",1)
            return ts, author
    except Exception:
        pass
    return "", ""

def list_git_tracked():
    try:
        tracked = set(git("ls-files").splitlines())
    except Exception:
        tracked = set()
    return tracked

def list_git_untracked():
    try:
        untracked = set(git("ls-files","--others","--exclude-standard").splitlines())
    except Exception:
        untracked = set()
    return untracked

KEYWORDS = {
    "enterprise": re.compile(r"\b(HIPAA|SOC ?2 full|enterprise connector|salesforce|servicenow|sap)\b", re.I),
    "saas": re.compile(r"\b(multitenant|billing|quota|dashboard|control[- ]?plane)\b", re.I),
    "websites": re.compile(r"\b(docusaurus|mkdocs|hugo|next\.js|openGraph|website)\b", re.I),
    "cartridge": re.compile(r"\b(cartridge|EU ?AI|GDPR|CCPA|HIPAA|SOC ?2)\b", re.I),
    "framework": re.compile(r"\b(cartridge framework|mapping manifest|lifecycle hook)\b", re.I),
    "fabric": re.compile(r"\b(fabric|immutable audit|evidence log)\b", re.I),
    "connector": re.compile(r"\b(connector|postgres|s3|webhook|kafka|rabbitmq|fhir)\b", re.I),
    "assurance": re.compile(r"\b(assurance score|reality audit|harness)\b", re.I),
    "ops": re.compile(r"\b(ci|workflow|github actions|sbom|cosign|trufflehog|bandit)\b", re.I),
}

def classify(path: Path, preview: bytes):
    p = str(path).lower()

    def pick_repo(default="core"):
        if any(s in p for s in ("/website/", "/web/", "docusaurus.config", "mkdocs.yml")): return "websites"
        if "/examples/" in p or "/notebooks/" in p: return "examples"
        if "/ops/" in p or "/.github/workflows/" in p: return "core"
        if "/enterprise/" in p: return "enterprise"
        if "/saas/" in p: return "saas"
        txt = preview.decode("utf-8","ignore")
        if KEYWORDS["saas"].search(txt): return "saas"
        if KEYWORDS["enterprise"].search(txt): return "enterprise"
        if KEYWORDS["websites"].search(txt): return "websites"
        return default

    category = []
    txt = preview.decode("utf-8","ignore")
    for k, rx in KEYWORDS.items():
        if rx.search(txt) or k in p:
            category.append(k)

    repo_target = pick_repo()
    return repo_target, list(set(category)) or ["general"]

SECRET_RX = re.compile(r"(secret|token|apikey|api_key|password|passwd|aws_access_key_id|aws_secret_access_key|x-api-key)\s*[:=]", re.I)
PII_RX = re.compile(r"\b(\d{3}-\d{2}-\d{4}|[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})\b", re.I)

def risk_flags(path: Path, preview: bytes, size: int):
    flags = []
    suf = path.suffix.lower()
    if size > 50*1024*1024: flags.append("large_binary")
    if not is_text(path) and suf not in {".pdf",".png",".jpg",".jpeg",".gif"}: flags.append("binary_unknown")
    text = preview.decode("utf-8","ignore")
    if SECRET_RX.search(text): flags.append("secret_candidate")
    if PII_RX.search(text): flags.append("pii_candidate")
    if suf in {".pem",".key",".pfx"}: flags.append("secret_candidate")
    return flags

def main():
    tracked = list_git_tracked()
    untracked = list_git_untracked()
    all_paths = []
    for root, dirs, files in os.walk(ROOT):
        # prune ignored dirs
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for name in files:
            if name in IGNORE_DIRS: continue
            p = Path(root) / name
            try:
                rel = str(p.relative_to(ROOT))
            except ValueError:
                continue
            all_paths.append((p, rel))

    rows, checksums = [], {}
    for p, rel in sorted(all_paths, key=lambda t: t[1].lower()):
        try:
            size = p.stat().st_size
        except Exception:
            continue
        # lightweight preview
        try:
            with open(p, "rb") as f: preview = f.read(2048)
        except Exception:
            preview = b""
        textflag = "text" if is_text(p) else "binary"
        sha = sha256_file(p) if size < 200*1024*1024 else ""
        checksums.setdefault(sha, []).append(rel)
        status = "tracked" if rel in tracked else ("untracked" if rel in untracked else "unknown")
        last_ts, last_author = last_commit_info(p)
        first_ts, first_author = first_commit_info(p)
        repo_target, category = classify(p, preview)
        flags = risk_flags(p, preview, size)
        # line count for small text files
        lines = 0
        if textflag == "text" and size < 2*1024*1024:
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    lines = sum(1 for _ in f)
            except Exception:
                pass
        rows.append({
            "path": rel, "status": status, "size_bytes": size, "lines": lines,
            "sha256": sha, "text_or_binary": textflag,
            "last_commit_ts": last_ts, "last_author": last_author,
            "first_commit_ts": first_ts, "first_author": first_author,
            "guessed_feature": category, "guessed_repo_target": repo_target,
            "risk_flags": flags
        })

    # duplicate report
    dups = {h: ps for h, ps in checksums.items() if h and len(ps) > 1}

    # write JSON/CSV
    (OUTDIR / "FILE_INDEX.json").write_text(json.dumps(rows, indent=2))
    with open(OUTDIR / "FILE_INDEX.csv","w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        if rows: w.writeheader()
        for r in rows: w.writerow(r)

    (OUTDIR / "DUPLICATES.json").write_text(json.dumps(dups, indent=2))

    # quick stub reports (Cursor will replace with render_markdown.py later)
    summary = {
        "total_files": len(rows),
        "tracked": sum(1 for r in rows if r["status"]=="tracked"),
        "untracked": sum(1 for r in rows if r["status"]=="untracked"),
        "by_target": {t: sum(1 for r in rows if r["guessed_repo_target"]==t)
                      for t in ["core","enterprise","saas","websites","examples","docs"]},
        "risk_counts": {}
    }
    for r in rows:
        for f in r["risk_flags"]:
            summary["risk_counts"][f] = summary["risk_counts"].get(f,0)+1
    (OUTDIR / "SUMMARY.json").write_text(json.dumps(summary, indent=2))
    print(f"Wrote inventory to {OUTDIR}")

if __name__ == "__main__":
    main()
