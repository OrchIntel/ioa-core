"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List
import yaml


def emit_markdown(manifest_path: Path) -> str:
    data = yaml.safe_load(manifest_path.read_text()) or {}
    title = f"# {data.get('cartridge', 'UNKNOWN')} Mapping vs System Laws\n"
    header = "\n| System Law | Requirement | Evidence | Test |\n\n|---|---|---|---|\n"
    rows: List[str] = []
    for row in data.get("rows", []):
        rows.append(
            f"| {row.get('system_law','')} | {row.get('requirement','')} | {row.get('evidence_path','')} | {row.get('test_path','')} |"
        )
    return title + header + "\n".join(rows) + "\n"


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    md = emit_markdown(Path(args.manifest))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(md, encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
