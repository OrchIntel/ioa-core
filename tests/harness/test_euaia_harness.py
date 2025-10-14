"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

from __future__ import annotations

from pathlib import Path

from ioa.cartridges.eu_ai_act_v1.config import load_config
from ioa.cartridges.eu_ai_act_v1.enforcement import preflight_check, postflight_record


def test_euaia_harness_metrics_written(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("IOA_ENABLE_ENTERPRISE", "1")
    cfg = load_config()
    cfg["scope"]["default_mode"] = "monitor"

    # Simulate 100 records across categories
    categories = ["employment_hr", "biometric_identification", "ads", "minimal"]
    total = 0
    for cat in categories:
        for i in range(25):
            actions, ev = preflight_check({"use_case": cat}, cfg)
            rec = postflight_record(f"trace-{cat}-{i}", actions, cfg, {"ok": True})
            total += 1

    metrics_file = Path("artifacts/lens/euaia/metrics.jsonl")
    assert metrics_file.exists()
    # Basic sanity: at least N lines
    with metrics_file.open() as f:
        lines = sum(1 for _ in f)
    assert lines >= total


