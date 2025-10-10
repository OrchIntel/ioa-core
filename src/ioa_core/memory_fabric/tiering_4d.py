# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.



import time
import math
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
"""Tiering 4D module."""



@dataclass
class Tier4DConfig:
    """Configuration for 4D-Tiering behavior."""
    max_age_hours: float = 24.0  # Temporal dimension: hours before cooling
    jurisdiction_boost: float = 0.25  # Spatial dimension: locality bonus
    risk_boost: float = 0.5  # Contextual dimension: high-risk bonus
    priority_weight: float = 0.1  # Priority dimension: base priority weight
    hot_threshold: float = 1.2  # Score threshold for HOT tier
    warm_threshold: float = 0.6  # Score threshold for WARM tier


class Tier4D:
    """
    4D-Tiering engine for dynamic memory tiering.

    Evaluates records across four dimensions:
    1. Temporal: How recent is the data?
    2. Spatial: Does it match jurisdictional locality?
    3. Contextual: Is it policy-critical or high-risk?
    4. Priority: What's its SLA/business impact?

    Returns suggested tier: HOT, WARM, or COLD.
    """

    def __init__(self, config: Optional[Tier4DConfig] = None, policy_ref: Optional[Dict[str, Any]] = None):
        """
        Initialize 4D-Tiering engine.

        Args:
            config: Tiering configuration parameters
            policy_ref: Reference policy for jurisdiction and context matching
        """
        self.config = config or Tier4DConfig()
        self.policy_ref = policy_ref or {}

    def classify(self, record: Any) -> str:
        """
        Classify a memory record into HOT, WARM, or COLD tier.

        Args:
            record: Memory record with metadata

        Returns:
            str: Suggested tier ('HOT', 'WARM', or 'COLD')
        """
        score = 0.0

        # Ensure record has metadata
        if not hasattr(record, 'metadata') and not hasattr(record, 'meta'):
            return "COLD"  # Default to cold for records without metadata

        meta = getattr(record, 'metadata', None) or getattr(record, 'meta', {})

        # 1. Temporal dimension: Recent data gets hotter
        age_hours = self._calculate_age_hours(meta.get("timestamp", meta.get("ts", time.time())))
        temporal_score = max(0.0, 1.0 - min(age_hours / self.config.max_age_hours, 1.0))
        score += temporal_score

        # 2. Spatial dimension: Jurisdiction locality match
        if self._matches_jurisdiction(meta):
            score += self.config.jurisdiction_boost

        # 3. Contextual dimension: Policy-critical or high-risk data
        if self._is_high_risk_context(meta):
            score += self.config.risk_boost

        # 4. Priority dimension: SLA and business impact weighting
        priority_score = meta.get("priority", 0.0) * self.config.priority_weight
        score += priority_score

        # Classify based on total score
        if score >= self.config.hot_threshold:
            return "HOT"
        elif score >= self.config.warm_threshold:
            return "WARM"
        else:
            return "COLD"

    def _calculate_age_hours(self, timestamp: Union[float, str, datetime]) -> float:
        """Calculate age in hours from timestamp."""
        if isinstance(timestamp, str):
            try:
                # Try ISO format
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).timestamp()
            except:
                # Fallback to current time
                timestamp = time.time()
        elif isinstance(timestamp, datetime):
            timestamp = timestamp.timestamp()

        return (time.time() - timestamp) / 3600.0

    def _matches_jurisdiction(self, meta: Dict[str, Any]) -> bool:
        """Check if record matches policy jurisdiction."""
        record_jurisdiction = meta.get("jurisdiction")
        policy_jurisdiction = self.policy_ref.get("jurisdiction")

        if not record_jurisdiction or not policy_jurisdiction:
            return False

        return record_jurisdiction.lower() == policy_jurisdiction.lower()

    def _is_high_risk_context(self, meta: Dict[str, Any]) -> bool:
        """Check if record has high-risk context."""
        risk_level = meta.get("risk_level", "").lower()
        context_tags = meta.get("context_tags", [])

        # Direct risk level check
        if risk_level in ("high", "critical", "urgent"):
            return True

        # Context tag checks
        high_risk_tags = ["gdpr", "hipaa", "confidential", "sensitive", "personal"]
        if any(tag.lower() in high_risk_tags for tag in context_tags):
            return True

        return False

    def get_tiering_metrics(self, record: Any) -> Dict[str, Any]:
        """
        Get detailed tiering metrics for a record.

        Returns:
            Dict with scores for each dimension and final classification
        """
        if not hasattr(record, 'metadata') and not hasattr(record, 'meta'):
            return {"tier": "COLD", "total_score": 0.0, "dimensions": {}}

        meta = getattr(record, 'metadata', None) or getattr(record, 'meta', {})

        age_hours = self._calculate_age_hours(meta.get("timestamp", meta.get("ts", time.time())))
        temporal_score = max(0.0, 1.0 - min(age_hours / self.config.max_age_hours, 1.0))
        spatial_score = self.config.jurisdiction_boost if self._matches_jurisdiction(meta) else 0.0
        contextual_score = self.config.risk_boost if self._is_high_risk_context(meta) else 0.0
        priority_score = meta.get("priority", 0.0) * self.config.priority_weight

        total_score = temporal_score + spatial_score + contextual_score + priority_score

        return {
            "tier": self.classify(record),
            "total_score": total_score,
            "dimensions": {
                "temporal": temporal_score,
                "spatial": spatial_score,
                "contextual": contextual_score,
                "priority": priority_score
            },
            "metadata": {
                "age_hours": age_hours,
                "jurisdiction_match": self._matches_jurisdiction(meta),
                "high_risk_context": self._is_high_risk_context(meta),
                "priority_value": meta.get("priority", 0.0)
            }
        }

