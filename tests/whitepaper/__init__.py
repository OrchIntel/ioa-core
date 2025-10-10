""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""

PATCH: Cursor-2025-09-13 DISPATCH-EXEC-20250913-WHITEPAPER-VALIDATION
Creates test package for validating whitepaper governance claims.
"""

__version__ = "2.5.0"
__author__ = "IOA Core Team"
__description__ = "Whitepaper validation test suite for governance-first claims"

# Test modules
__all__ = [
    "test_ethics_reduction",
    "test_agi_readiness_roundtable", 
    "test_cert_tamper_resistance",
    "test_sustainability_budget",
    "test_fairness_drift_guard"
]
