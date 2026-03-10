# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""Async PII detector shim used by dependent applications."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ioa.governance.detectors.privacy_presidio import PrivacyDetector


class PIIDetector:
    """Thin async wrapper over the privacy detector."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        default_config = {
            "enabled": True,
            "mode": "monitor",
            "pii_entities": ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN"],
            "action": "mask",
        }
        self._detector = PrivacyDetector({**default_config, **(config or {})})

    async def detect_pii(self, text: str) -> Dict[str, Any]:
        result = self._detector.detect_and_anonymize(text)
        return {
            "pii_detected": result.has_pii,
            "entities": result.entities_found,
            "anonymized_text": result.anonymized_text,
            "action_taken": result.action_taken,
            "confidence_scores": result.confidence_scores or {},
            "error": result.error,
        }
