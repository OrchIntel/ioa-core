"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

import json
import os

from .classifier import classify_use_case


def preflight_check(input_payload: Dict[str, Any], config: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Perform pre-flight checks: risk classify, PII mask flag, oversight flag.

    Returns (actions, evidence) where actions may include hold/block flags.
    """
    use_case = (input_payload or {}).get("use_case", "")
    risk, details = classify_use_case(use_case, config)

    scope = (config or {}).get("scope", {})
    mode = scope.get("default_mode", "monitor")

    actions: Dict[str, Any] = {
        "risk": risk,
        "oversight_required": risk == "high_risk" and (config.get("oversight", {}).get("required_for_high_risk", True)),
        "transparency_on": (config.get("transparency", {}).get("disclose_generated", True)),
        "pii_mask": (config.get("data_governance", {}).get("mask_pii_preflight", True)),
        "blocked": False,
        "held": False,
        "mode": mode,
    }

    if risk == "prohibited":
        if mode == "strict":
            actions["blocked"] = True
        else:
            # monitor/graduated/shadow: do not block, but mark held if configured
            actions["held"] = bool(config.get("oversight", {}).get("hold_on_violation", True))

    evidence = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": "preflight",
        "risk": risk,
        "details": details,
        "mode": mode,
    }

    return actions, evidence


def postflight_record(trace_id: str, actions: Dict[str, Any], config: Dict[str, Any], result_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Record post-flight evidence and minimal metrics to Lens feed.
    Writes JSONL to artifacts/lens/euaia/metrics.jsonl
    """
    artifacts_dir = Path("artifacts/lens/euaia")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = artifacts_dir / "metrics.jsonl"

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": trace_id,
        "risk": actions.get("risk"),
        "oversight_required": actions.get("oversight_required"),
        "blocked": actions.get("blocked"),
        "held": actions.get("held"),
        "transparency_on": actions.get("transparency_on"),
        "pii_mask": actions.get("pii_mask"),
        "mode": actions.get("mode"),
        "accept_accuracy_min": config.get("robustness", {}).get("min_accept_accuracy", 0.70),
        "result_ok": True,
    }

    with metrics_path.open("a") as f:
        f.write(json.dumps(record) + "\n")

    return record


