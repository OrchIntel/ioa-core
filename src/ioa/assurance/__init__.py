# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
"""
IOA Module: Assurance Score v1
Version: v2.5.0
Last-Updated: 2025-09-20
Agents: Cursor assist
Summary: Assurance scoring system with assurance mirror for compatibility
"""

from .score import AssuranceScore, compute_assurance_score

__all__ = ['AssuranceScore', 'compute_assurance_score']