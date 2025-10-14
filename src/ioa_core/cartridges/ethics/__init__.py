# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# Part of IOA Core (Open Source Edition).

"""
Ethics Cartridge (Aletheia-inspired) – IOA Original

NOTE: Inspired by public ethics frameworks such as Aletheia v2.0 (CC BY-ND 4.0).
This is NOT a derivative or implementation of Aletheia; it uses IOA-original criteria names.

This cartridge provides runtime ethics hooks for AI systems without reproducing
Aletheia content, names, or graphics. It serves as a starting point for developers
to implement ethical governance in their AI applications.

Attribution: Aletheia Framework v2.0 by Rolls-Royce Civil Aerospace (CC BY-ND 4.0)
Reference: https://www.rolls-royce.com/innovation/the-aletheia-framework.aspx
"""

from .policy_ethics import EthicsDecision, precheck

__all__ = ["EthicsDecision", "precheck"]
