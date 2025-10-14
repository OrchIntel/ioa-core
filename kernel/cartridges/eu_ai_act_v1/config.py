"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import os
import yaml


DEFAULT_CONFIG: Dict[str, Any] = {
    "version": 1,
    "enabled": True,
    "scope": {
        "jurisdictions": ["EU", "EEA"],
        "default_mode": "monitor",  # monitor | graduated | strict | shadow
        "apply_to_providers": ["*"]
    },
    "risk": {
        "classifier": {
            "strategy": "rules+labels",
            "prohibited_categories": [
                "subliminal_manipulation",
                "social_scoring",
                "biometric_categorization_sensitive",
            ],
        },
        "high_risk_categories": [
            "biometric_identification",
            "employment_hr",
            "critical_infrastructure",
        ],
        "default_category": "minimal",
    },
    "transparency": {
        "disclose_generated": True,
        "require_capability_card": True,
        "require_limitations": True,
    },
    "data_governance": {
        "accept_provenance_manifest": True,
        "require_manifest_for_high_risk": True,
        "mask_pii_preflight": True,
    },
    "oversight": {
        "required_for_high_risk": True,
        "hold_on_violation": True,
    },
    "robustness": {
        "min_accept_accuracy": 0.70,
        "drift_warn": 0.10,
        "fail_on_drift_in_strict": True,
    },
    "logging": {
        "evidence_level": "full",  # minimal | standard | full
        "append_to_audit_chain": True,
    },
    "post_market": {
        "incident_threshold_per_10k": 2,
        "weekly_summary_enabled": True,
    },
    "assurance": {
        "contribute_to_assurance_score": True,
        "weights": {"code": 0.25, "tests": 0.25, "runtime": 0.25, "docs": 0.25},
    },
}


def _feature_gate_enabled() -> bool:
    """Enterprise feature gate for the cartridge."""
    return os.getenv("IOA_ENABLE_ENTERPRISE", "0") in ("1", "true", "TRUE")


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load EU AI Act cartridge configuration, applying defaults and feature gating.

    If enterprise gate is disabled, returns defaults but forces monitor mode and enabled=False.
    """
    cfg: Dict[str, Any] = dict(DEFAULT_CONFIG)

    resolved_path: Optional[Path] = None
    if path:
        resolved_path = Path(path)
        if resolved_path.exists():
            with resolved_path.open("r") as f:
                try:
                    user_cfg = yaml.safe_load(f) or {}
                    if isinstance(user_cfg, dict):
                        # Shallow merge for v1
                        cfg.update(user_cfg)
                except Exception:
                    # Best-effort: keep defaults
                    pass

    # Apply feature gate
    if not _feature_gate_enabled():
        cfg = dict(cfg)
        cfg["enabled"] = False
        cfg.setdefault("scope", {})["default_mode"] = "monitor"

    # Stamp load metadata
    cfg.setdefault("_meta", {})["loaded_at"] = datetime.now(timezone.utc).isoformat()
    if resolved_path:
        cfg["_meta"]["source_path"] = str(resolved_path)
    else:
        cfg["_meta"]["source_path"] = "defaults"

    return cfg


