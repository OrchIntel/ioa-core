""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3
"""
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from importlib.metadata import distributions # type: ignore
except Exception:
    distributions = None  # type: ignore


LICENSE_DENY = {"AGPL", "AGPL-3.0", "SSPL", "GPL-3.0", "GPLv3"}


def read_requirements_files(base: Path) -> List[str]:
    reqs: List[str] = []
    for fname in ("requirements.txt", "requirements-dev.txt", "requirements-docs.txt"):  # best-effort
        fpath = base / fname
        if fpath.exists():
            for line in fpath.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                reqs.append(line)
    return reqs


def parse_name_version(spec: str) -> Dict[str, Optional[str]]:
    # naive parse: package==version | package>=version | package
    m = re.split(r"[=<>!~]+", spec)
    name = m[0].strip()
    version = None
    if "==" in spec:
        parts = spec.split("==")
        if len(parts) == 2:
            version = parts[1].strip()
    return {"name": name, "version": version}


def get_installed_metadata() -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    if not distributions:
        return results
    for dist in distributions():  # type: ignore
        name = getattr(dist, "metadata", {}).get("Name") if hasattr(dist, "metadata") else dist.metadata["Name"]
        version = getattr(dist, "version", None) or dist.version
        license_str = None
        try:
            md = dist.metadata  # email.message.Message
            license_str = md.get("License") or md.get("Classifier", "")
        except Exception:
            license_str = None
        results.append({"name": name, "version": version, "license": license_str})
    return results


def license_policy(license_str: Optional[str]) -> str:
    if not license_str:
        return "unknown"
    up = license_str.upper()
    for bad in LICENSE_DENY:
        if bad in up:
            return "deny"
    return "allow"


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = repo_root / "docs/audit"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Build component list
    components: List[Dict[str, Any]] = []
    reqs = read_requirements_files(repo_root)
    if reqs:
        for spec in reqs:
            nv = parse_name_version(spec)
            components.append({
                "type": "library",
                "name": nv["name"],
                "version": nv["version"] or "*",
                "purl": f"pkg:pypi/{nv['name']}@{nv['version'] or '*'}",
                "licenses": []
            })
    else:
        # Fallback to installed dists in environment
        for meta in get_installed_metadata():
            components.append({
                "type": "library",
                "name": meta["name"],
                "version": meta.get("version") or "*",
                "purl": f"pkg:pypi/{meta['name']}@{meta.get('version') or '*'}",
                "licenses": [meta.get("license") or "unknown"],
            })

    sbom: Dict[str, Any] = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "name": "ioa-core-internal",
            }
        },
        "components": components,
    }

    # License report (best-effort)
    license_report: List[Dict[str, Any]] = []
    for comp in components:
        lic = (comp.get("licenses") or [None])[0]
        policy = license_policy(lic if isinstance(lic, str) else None)
        license_report.append({
            "name": comp["name"],
            "version": comp.get("version"),
            "license": lic or "unknown",
            "policy": policy,
        })

    (out_dir / "SBOM.cdx.json").write_text(json.dumps(sbom, indent=2))
    (out_dir / "LICENSE_REPORT.json").write_text(json.dumps(license_report, indent=2))
    # Markdown summary
    md_lines = [
        "# SBOM and License Summary\n",
        "\n## Components\n",
        f"Total components: {len(components)}\n",
        "\n## License Policy Findings\n",
    ]
    denies = [r for r in license_report if r["policy"] == "deny"]
    unknowns = [r for r in license_report if r["policy"] == "unknown"]
    md_lines.append(f"Deny: {len(denies)}; Unknown: {len(unknowns)}\n")
    (out_dir / "SBOM_LICENSE_SUMMARY.md").write_text("\n".join(md_lines))

    print(f"SBOM written to {out_dir/'SBOM.cdx.json'}")
    print(f"License report written to {out_dir/'LICENSE_REPORT.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


