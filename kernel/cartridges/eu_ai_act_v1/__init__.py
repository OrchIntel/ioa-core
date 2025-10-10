""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

"""
EU AI Act Cartridge v1

Responsibilities:
- Provide configuration schema and defaults for EU AI Act enforcement (v1)
- Expose risk classification helpers and enforcement hooks
- Integrate with oversight and metrics evidence emitters

Key public objects:
- load_config(path: Optional[str]) -> Dict[str, Any]
- classify(use_case: str, config: Dict[str, Any]) -> str
- run_enforcement(preflight_input: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]

This module is enterprise-gated via IOA_ENABLE_ENTERPRISE=1. In OSS builds,
imports should not fail; functions will operate in monitor mode with minimal behavior.
"""

from typing import Any, Dict, Optional

from .config import load_config, DEFAULT_CONFIG
from .classifier import classify_use_case
from .enforcement import preflight_check, postflight_record

__all__ = [
    "load_config",
    "DEFAULT_CONFIG",
    "classify_use_case",
    "preflight_check",
    "postflight_record",
]


