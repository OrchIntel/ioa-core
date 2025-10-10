""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


RISK_ORDER = ["prohibited", "high_risk", "limited", "minimal"]


def classify_use_case(use_case: str, config: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Classify a use_case string into risk category using v1 rules.

    Returns a tuple of (risk_category, details_dict).
    """
    use_case_normalized = (use_case or "").strip().lower().replace(" ", "_")

    risk_cfg = (config or {}).get("risk", {})
    classifier_cfg = risk_cfg.get("classifier", {})
    prohibited = set(classifier_cfg.get("prohibited_categories", []) or [])
    high_risk = set(risk_cfg.get("high_risk_categories", []) or [])
    default_category = risk_cfg.get("default_category", "minimal")

    if use_case_normalized in prohibited:
        return "prohibited", {"matched": use_case_normalized, "rule": "prohibited"}
    if use_case_normalized in high_risk:
        return "high_risk", {"matched": use_case_normalized, "rule": "high_risk"}

    # Simple label heuristics
    if any(k in use_case_normalized for k in ["biometric", "employment", "hr", "critical_infrastructure"]):
        return "high_risk", {"matched": use_case_normalized, "rule": "keyword_heuristic"}

    if any(k in use_case_normalized for k in ["ads", "recommendation", "content_moderation", "synthetic"]):
        return "limited", {"matched": use_case_normalized, "rule": "keyword_heuristic"}

    return default_category, {"matched": use_case_normalized, "rule": "default"}


