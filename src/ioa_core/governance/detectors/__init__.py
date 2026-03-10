# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""Governance detector compatibility exports."""

from .bias_detector import BiasDetector
from .pii_detector import PIIDetector

__all__ = ["BiasDetector", "PIIDetector"]
