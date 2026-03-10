# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""Async bias detector shim used by dependent applications."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ioa.governance.detectors.fairness_basic import FairnessDetector


class BiasDetector:
    """Thin async wrapper over the fairness detector."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        default_config = {
            "enabled": True,
            "mode": "monitor",
            "probes": ["counterfactual_swap"],
            "metrics": [],
            "thresholds": {"warn": 0.1, "block": 0.2},
        }
        self._detector = FairnessDetector({**default_config, **(config or {})})

    async def detect_bias(self, text: str) -> Dict[str, Any]:
        result = self._detector.analyze_fairness(text)
        return {
            "bias_detected": result.has_bias,
            "bias_score": result.bias_score,
            "confidence": result.bias_score,
            "counterfactual_deltas": result.counterfactual_deltas,
            "group_metrics": result.group_metrics,
            "action_taken": result.action_taken,
            "error": result.error,
        }
