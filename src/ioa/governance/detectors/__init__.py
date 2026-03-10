# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
"""
IOA Module: src/ioa/governance/detectors/__init__.py
Version: v2.5.0
Last-Updated: 2025-09-15
Agents: Cursor assist
Summary: Ethics Pack v0 detectors for privacy, safety, and fairness enforcement
"""

from .privacy_presidio import PrivacyDetector
from .safety_lexicon import SafetyDetector
from .fairness_basic import FairnessDetector

__all__ = ["PrivacyDetector", "SafetyDetector", "FairnessDetector"]
