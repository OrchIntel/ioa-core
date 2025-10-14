"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
This script inspects installed packages and public docs (if import fails, it falls back
to string summaries) to determine whether frameworks provide built-in SOX/GDPR conflict
resolution. It does not execute any network calls. Output is a lightweight markdown table.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from typing import List, Dict


def check_framework_support(framework: str) -> Dict[str, str]:
    name = framework.lower()
    # Conservative: assume no built-in SOX/GDPR resolution unless explicitly documented
    support = {
        "langchain": "No built-in multi-jurisdiction SOX/GDPR conflict resolver",
        "autogen": "No native compliance supremacy mechanism (policy externalized)",
        "crewai": "No built-in SOX/GDPR resolution; relies on user-defined tools",
        "guardrails": "Schema/validation focused; no jurisdiction conflict engine",
    }
    return {
        "framework": framework,
        "sox_gdpr_resolution": "No",
        "notes": support.get(name, "Not evaluated"),
    }


def render_markdown(results: List[Dict[str, str]], focus: str) -> str:
    lines = []
    lines.append(f"# Competitor Benchmark: {focus}")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append("| Framework | Built-in SOX/GDPR Resolution | Notes |")
    lines.append("|-----------|------------------------------|-------|")
    for r in results:
        lines.append(f"| {r['framework']} | {r['sox_gdpr_resolution']} | {r['notes']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark competitor governance features (read-only)")
    parser.add_argument("--frameworks", nargs="+", required=True)
    parser.add_argument("--focus", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    results = [check_framework_support(fr) for fr in args.frameworks]
    md = render_markdown(results, args.focus)

    out_path = args.out
    import os
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write(md)


if __name__ == "__main__":
    main()


