"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

from __future__ import annotations

import os
from pathlib import Path

from ioa.cartridges.eu_ai_act_v1.config import load_config
from ioa.cartridges.eu_ai_act_v1.classifier import classify_use_case
from ioa.cartridges.eu_ai_act_v1.enforcement import preflight_check


def test_config_feature_gate_off(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("IOA_ENABLE_ENTERPRISE", "0")
    cfg = load_config()
    assert cfg["enabled"] is False
    assert cfg["scope"]["default_mode"] == "monitor"


def test_config_feature_gate_on(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("IOA_ENABLE_ENTERPRISE", "1")
    cfg = load_config()
    assert cfg["enabled"] is True


def test_classifier_rules_match_high_risk():
    cfg = load_config()
    risk, details = classify_use_case("employment_hr", cfg)
    assert risk == "high_risk"
    assert details["matched"] == "employment_hr"


def test_preflight_prohibited_block_in_strict(monkeypatch):
    monkeypatch.setenv("IOA_ENABLE_ENTERPRISE", "1")
    cfg = load_config()
    cfg["scope"]["default_mode"] = "strict"
    actions, ev = preflight_check({"use_case": "social_scoring"}, cfg)
    assert actions["risk"] == "prohibited"
    assert actions["blocked"] is True


