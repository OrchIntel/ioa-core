""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

from datetime import datetime, timezone
from typing import Dict, Any

import pytest

from src.ioa.core.governance.policy_engine import PolicyEngine


class TestSoxGdprConflict:
    """Validate SOX vs GDPR conflict resolution behavior."""

    def test_gdpr_precedence_over_sox(self):
        engine = PolicyEngine()

        # Simulate conflicting jurisdictions for EU data subject with US audit retention
        jurisdictions = ["US", "EU"]  # Order shouldn't matter; engine must pick EU (GDPR)
        data_classification = "pii"

        resolved = engine.resolve_jurisdiction_conflicts(jurisdictions, data_classification)

        assert resolved == "EU", "GDPR (EU) must take precedence over SOX (US) per compliance supremacy"

        # Emit a policy event for audit evidence
        engine.emit_policy_event(
            "compliance_conflict_resolved",
            {
                "jurisdictions": jurisdictions,
                "data_classification": data_classification,
                "resolved": resolved,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )


