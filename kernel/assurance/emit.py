"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from .schema import AssuranceRollup


def _assurance_dir() -> Path:
    d = Path("artifacts/lens/assurance")
    d.mkdir(parents=True, exist_ok=True)
    return d


def emit_summary(rollup: AssuranceRollup) -> Path:
    path = _assurance_dir() / "summary.json"
    with open(path, "w") as f:
        json.dump(rollup.model_dump() if hasattr(rollup, "model_dump") else rollup.__dict__, f, indent=2, default=str)
    return path


def emit_timeseries(rollup: AssuranceRollup) -> Path:
    path = _assurance_dir() / "timeseries.jsonl"
    record = rollup.model_dump() if hasattr(rollup, "model_dump") else rollup.__dict__
    with open(path, "a") as f:
        f.write(json.dumps(record, default=str) + "\n")
    return path


def render_markdown(rollup: AssuranceRollup) -> str:
    lines = []
    lines.append(f"# Assurance Score v1 Report")
    lines.append("")
    lines.append(f"**Overall Assurance Score:** {rollup.overall:.2f}/15")
    lines.append(f"**Status:** {rollup.status}")
    lines.append(f"**Timestamp (UTC):** {rollup.timestamp}")
    lines.append("")
    lines.append("## Per-Law Breakdown")
    for pls in rollup.per_law:
        lines.append(f"- {pls.law_id.upper()}: {pls.total:.2f} (code={pls.code}, tests={pls.tests}, runtime={pls.runtime}, docs={pls.docs})")
    lines.append("")
    lines.append("## Domain Means")
    for domain, mean in rollup.domain_means.items():
        lines.append(f"- {domain}: {mean:.2f}")
    lines.append("")
    lines.append("## Weights")
    lines.append(f"- code: {rollup.weights.code}")
    lines.append(f"- tests: {rollup.weights.tests}")
    lines.append(f"- runtime: {rollup.weights.runtime}")
    lines.append(f"- docs: {rollup.weights.docs}")
    lines.append("")
    lines.append("## Thresholds")
    lines.append(f"- pass_overall: {rollup.thresholds.pass_overall}")
    lines.append(f"- warn_overall: {rollup.thresholds.warn_overall}")
    return "\n".join(lines)


