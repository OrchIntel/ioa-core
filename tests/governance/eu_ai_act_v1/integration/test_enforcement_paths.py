""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

from __future__ import annotations

from pathlib import Path

from ioa.cartridges.eu_ai_act_v1.config import load_config
from ioa.cartridges.eu_ai_act_v1.enforcement import preflight_check


def test_high_risk_requires_oversight(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("IOA_ENABLE_ENTERPRISE", "1")
    cfg = load_config()
    cfg["scope"]["default_mode"] = "monitor"
    actions, ev = preflight_check({"use_case": "employment_hr"}, cfg)
    assert actions["risk"] == "high_risk"
    assert actions["oversight_required"] is True
    assert actions["blocked"] is False


def test_prohibited_blocked_in_strict(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("IOA_ENABLE_ENTERPRISE", "1")
    cfg = load_config()
    cfg["scope"]["default_mode"] = "strict"
    actions, ev = preflight_check({"use_case": "social_scoring"}, cfg)
    assert actions["risk"] == "prohibited"
    assert actions["blocked"] is True


def test_limited_transparency_only(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("IOA_ENABLE_ENTERPRISE", "1")
    cfg = load_config()
    cfg["scope"]["default_mode"] = "monitor"
    actions, ev = preflight_check({"use_case": "ads"}, cfg)
    assert actions["risk"] in ("limited", "minimal")
    assert actions["transparency_on"] is True
    assert actions["blocked"] is False


