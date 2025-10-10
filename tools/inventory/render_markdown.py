""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3
# tools/inventory/render_markdown.py
import json, os, sys
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

def load_inventory(inventory_dir):
    """Load FILE_INDEX.json and DUPLICATES.json"""
    with open(inventory_dir / "FILE_INDEX.json") as f:
        files = json.load(f)
    with open(inventory_dir / "DUPLICATES.json") as f:
        duplicates = json.load(f)
    return files, duplicates

def generate_migration_plan(files, outdir):
    """Generate MIGRATION_PLAN.md"""
    by_repo = defaultdict(list)
    for f in files:
        by_repo[f["guessed_repo_target"]].append(f)
    
    content = ["# Migration Plan", "", "## Overview", ""]
    
    for repo in sorted(by_repo.keys()):
        files_in_repo = by_repo[repo]
        content.append(f"### {repo.upper()} Repository ({len(files_in_repo)} files)")
        content.append("")
        content.append("| Current Path | Size | Status | Risk Flags |")
        content.append("|--------------|------|--------|------------|")
        
        for f in sorted(files_in_repo, key=lambda x: x["path"]):
            size_str = f"{f['size_bytes']:,} bytes" if f['size_bytes'] < 1024*1024 else f"{f['size_bytes']//1024//1024} MB"
            risk_str = ", ".join(f["risk_flags"]) if f["risk_flags"] else "none"
            content.append(f"| `{f['path']}` | {size_str} | {f['status']} | {risk_str} |")
        content.append("")
    
    (outdir / "MIGRATION_PLAN.md").write_text("\n".join(content))

def generate_gitignore_suggestions(files, outdir):
    """Generate GITIGNORE_SUGGESTIONS.md"""
    untracked = [f for f in files if f["status"] == "untracked"]
    large_binaries = [f for f in files if "large_binary" in f["risk_flags"]]
    generated = [f for f in files if any(x in f["path"].lower() for x in ["__pycache__", ".pyc", ".pyo", ".pyd", "build", "dist", ".egg-info"])]
    
    content = ["# Gitignore Suggestions", "", "## Untracked Files Analysis", ""]
    content.append(f"Found {len(untracked)} untracked files that should be considered for .gitignore")
    content.append("")
    
    # Group by pattern
    patterns = defaultdict(list)
    for f in untracked:
        if f["path"].endswith(".pyc"):
            patterns["*.pyc"].append(f["path"])
        elif "__pycache__" in f["path"]:
            patterns["__pycache__/"].append(f["path"])
        elif f["path"].startswith("test_results/"):
            patterns["test_results/"].append(f["path"])
        else:
            patterns[f["path"]].append(f["path"])
    
    content.append("### Recommended .gitignore additions:")
    content.append("```")
    for pattern, examples in sorted(patterns.items()):
        if len(examples) > 1:
            content.append(pattern)
        else:
            content.append(f"# {pattern}")
    content.append("```")
    content.append("")
    
    if large_binaries:
        content.append("## Large Binary Files")
        content.append(f"Found {len(large_binaries)} files > 50MB that should be excluded:")
        for f in large_binaries:
            content.append(f"- `{f['path']}` ({f['size_bytes']//1024//1024} MB)")
        content.append("")
    
    (outdir / "GITIGNORE_SUGGESTIONS.md").write_text("\n".join(content))

def generate_where_things_live(files, outdir):
    """Generate WHERE_THINGS_LIVE.md"""
    by_repo = defaultdict(list)
    for f in files:
        by_repo[f["guessed_repo_target"]].append(f)
    
    content = ["# Where Things Live - Repository Organization", "", "## Repository Structure", ""]
    
    repo_descriptions = {
        "core": "OSS kernel: laws/policy engine, framework, OSS cartridges, fabric primitives, CLI, assurance/harness, dev docs",
        "enterprise": "HIPAA runtime, full SOC2, extended privacy, enterprise connectors/agents/dashboards, proprietary assets",
        "saas": "Hosted control plane: multi-tenant runners, billing, dashboards, authn/z",
        "websites": "ioa.systems / ioaproject.org / orchintel.com content & build",
        "examples": "Tutorials, notebooks, sample connectors",
        "docs": "Long-form manuals/PDFs",
        "archive": "Old drafts, deprecated prototypes, large binaries not needed",
        "ignore": "Generated caches, build outputs, local state"
    }
    
    for repo in ["core", "enterprise", "saas", "websites", "examples", "docs", "archive", "ignore"]:
        files_in_repo = by_repo[repo]
        content.append(f"### {repo.upper()} ({len(files_in_repo)} files)")
        content.append(f"**Purpose:** {repo_descriptions.get(repo, 'TBD')}")
        content.append("")
        
        if files_in_repo:
            # Show top 10 files by size
            top_files = sorted(files_in_repo, key=lambda x: x["size_bytes"], reverse=True)[:10]
            content.append("**Key files:**")
            for f in top_files:
                size_str = f"{f['size_bytes']:,} bytes" if f['size_bytes'] < 1024*1024 else f"{f['size_bytes']//1024//1024} MB"
                content.append(f"- `{f['path']}` ({size_str})")
        content.append("")
    
    (outdir / "WHERE_THINGS_LIVE.md").write_text("\n".join(content))

def generate_repo_split_diagnosis(files, duplicates, outdir):
    """Generate REPO_SPLIT_DIAGNOSIS.md"""
    by_repo = defaultdict(list)
    risk_counts = Counter()
    for f in files:
        by_repo[f["guessed_repo_target"]].append(f)
        for risk in f["risk_flags"]:
            risk_counts[risk] += 1
    
    content = ["# Repository Split Diagnosis", "", f"**Generated:** {datetime.now().isoformat()}", ""]
    
    content.append("## Executive Summary")
    content.append(f"- **Total files:** {len(files):,}")
    content.append(f"- **Tracked files:** {sum(1 for f in files if f['status'] == 'tracked'):,}")
    content.append(f"- **Untracked files:** {sum(1 for f in files if f['status'] == 'untracked'):,}")
    content.append(f"- **Duplicate files:** {len(duplicates):,} groups")
    content.append("")
    
    content.append("## Repository Distribution")
    for repo in sorted(by_repo.keys()):
        count = len(by_repo[repo])
        total_size = sum(f["size_bytes"] for f in by_repo[repo])
        size_mb = total_size // 1024 // 1024
        content.append(f"- **{repo.upper()}:** {count:,} files ({size_mb:,} MB)")
    content.append("")
    
    content.append("## Risk Assessment")
    for risk, count in risk_counts.most_common():
        content.append(f"- **{risk}:** {count:,} files")
    content.append("")
    
    content.append("## 2-Day Split Plan")
    content.append("")
    content.append("### Day 1: Preparation")
    content.append("1. Review and validate file classifications")
    content.append("2. Create target repositories")
    content.append("3. Set up CI/CD for each repo")
    content.append("4. Test migration scripts on small subset")
    content.append("")
    content.append("### Day 2: Execution")
    content.append("1. Migrate core repository (largest)")
    content.append("2. Migrate enterprise and saas repositories")
    content.append("3. Migrate websites and examples")
    content.append("4. Update documentation and links")
    content.append("5. Archive original repository")
    content.append("")
    
    (outdir / "REPO_SPLIT_DIAGNOSIS.md").write_text("\n".join(content))

def generate_reality_check(files, outdir):
    """Generate REALITY_CHECK.md"""
    features = defaultdict(int)
    for f in files:
        for feature in f["guessed_feature"]:
            features[feature] += 1
    
    content = ["# Reality Check - Feature Inventory", "", "## Features Present in Codebase", ""]
    
    feature_descriptions = {
        "cartridge": "Compliance cartridges (EU AI, GDPR, HIPAA, SOC2)",
        "framework": "Cartridge framework and lifecycle management",
        "fabric": "Immutable audit fabric and evidence logging",
        "connector": "Data connectors and integrations",
        "assurance": "Assurance scoring and reality auditing",
        "ops": "CI/CD, workflows, and operational tooling",
        "enterprise": "Enterprise-specific features",
        "saas": "SaaS and multi-tenant features",
        "websites": "Website and documentation content"
    }
    
    for feature in sorted(features.keys()):
        count = features[feature]
        desc = feature_descriptions.get(feature, "Unknown feature")
        content.append(f"### {feature.upper()} ({count} files)")
        content.append(f"**Description:** {desc}")
        content.append("")
    
    content.append("## Missing Features (Not Found)")
    expected_features = set(feature_descriptions.keys())
    found_features = set(features.keys())
    missing = expected_features - found_features
    if missing:
        for feature in sorted(missing):
            content.append(f"- **{feature}:** {feature_descriptions[feature]}")
    else:
        content.append("All expected features are present in the codebase.")
    
    (outdir / "REALITY_CHECK.md").write_text("\n".join(content))

def generate_secrets_rotation_checklist(files, outdir):
    """Generate SECRETS_ROTATION_CHECKLIST.md"""
    secret_files = [f for f in files if "secret_candidate" in f["risk_flags"]]
    
    content = ["# Secrets Rotation Checklist", ""]
    
    if not secret_files:
        content.append("✅ No secret candidates found in the codebase.")
    else:
        content.append(f"⚠️  Found {len(secret_files)} files with potential secrets:")
        content.append("")
        for f in secret_files:
            content.append(f"### `{f['path']}`")
            content.append(f"- **Size:** {f['size_bytes']:,} bytes")
            content.append(f"- **Status:** {f['status']}")
            content.append(f"- **Last modified:** {f['last_commit_ts']}")
            content.append("")
            content.append("**Action required:**")
            content.append("1. Review file for actual secrets")
            content.append("2. Rotate any exposed credentials")
            content.append("3. Move secrets to secure storage")
            content.append("4. Update code to use environment variables")
            content.append("")
    
    (outdir / "SECRETS_ROTATION_CHECKLIST.md").write_text("\n".join(content))

def generate_duplicates_report(duplicates, outdir):
    """Generate DUPLICATES_REPORT.md"""
    content = ["# Duplicates Report", ""]
    
    if not duplicates:
        content.append("✅ No duplicate files found.")
    else:
        content.append(f"Found {len(duplicates)} groups of duplicate files:")
        content.append("")
        
        total_wasted = 0
        for sha, paths in duplicates.items():
            if len(paths) > 1:
                # Estimate wasted space (assuming all but one are duplicates)
                content.append(f"## SHA256: {sha[:16]}...")
                content.append(f"**Files ({len(paths)}):**")
                for path in sorted(paths):
                    content.append(f"- `{path}`")
                content.append("")
                total_wasted += len(paths) - 1
        
        content.append(f"**Total duplicate files:** {total_wasted}")
        content.append("**Recommendation:** Remove duplicates and use symlinks or shared references where appropriate.")
    
    (outdir / "DUPLICATES_REPORT.md").write_text("\n".join(content))

def generate_repo_map(files, outdir):
    """Generate repo_map.json for websites linkcheck"""
    repo_map = {}
    
    for f in files:
        if f["guessed_repo_target"] == "websites":
            # This would be the public URL mapping
            repo_map[f["path"]] = f"https://ioa.systems/{f['path']}"
        elif f["guessed_repo_target"] == "core":
            repo_map[f["path"]] = f"https://github.com/OrchIntel/ioa-core/{f['path']}"
        elif f["guessed_repo_target"] == "enterprise":
            repo_map[f["path"]] = f"https://github.com/OrchIntel/ioa-enterprise/{f['path']}"
        elif f["guessed_repo_target"] == "saas":
            repo_map[f["path"]] = f"https://github.com/OrchIntel/ioa-saas/{f['path']}"
    
    (outdir / "repo_map.json").write_text(json.dumps(repo_map, indent=2))

def main():
    if len(sys.argv) != 2:
        print("Usage: python render_markdown.py <inventory_dir>")
        sys.exit(1)
    
    inventory_dir = Path(sys.argv[1])
    files, duplicates = load_inventory(inventory_dir)
    
    print(f"Generating reports for {len(files)} files...")
    
    generate_migration_plan(files, inventory_dir)
    generate_gitignore_suggestions(files, inventory_dir)
    generate_where_things_live(files, inventory_dir)
    generate_repo_split_diagnosis(files, duplicates, inventory_dir)
    generate_reality_check(files, inventory_dir)
    generate_secrets_rotation_checklist(files, inventory_dir)
    generate_duplicates_report(duplicates, inventory_dir)
    generate_repo_map(files, inventory_dir)
    
    print(f"Reports generated in {inventory_dir}")

if __name__ == "__main__":
    main()
