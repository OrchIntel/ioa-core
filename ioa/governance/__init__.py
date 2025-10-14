"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

"""Module docstring:
This package provides import-time shims so that imports like `ioa.governance.reinforcement_policy`
resolve correctly to the canonical implementations under `src.ioa.governance`.

Public objects are re-exported from the canonical modules for backward compatibility.

# PATCH: Cursor-2025-08-28 DISPATCH-GPT-20250828-033
Added governance import shims to satisfy tests expecting `ioa.governance.*` paths
without violating the "absolute imports from src.*" policy in implementation code.
"""

from typing import Any as _Any  # noqa: F401

# Intentionally minimal; concrete objects are provided by submodule shims.


