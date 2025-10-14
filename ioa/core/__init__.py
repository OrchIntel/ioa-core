"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

"""
IOA Core Package

This package provides the core functionality of the IOA system through shim aliases
to existing src.* modules. This allows for backward compatibility while introducing
the new monorepo structure.

Shim Structure:
- ioa.core.agent_onboarding -> src.agent_onboarding
- ioa.core.memory_engine -> src.memory_engine
- ioa.core.llm_manager -> src.llm_manager
- etc.

Migration Path:
1. Current: import from src.* (continues to work)
2. Future: import from ioa.core.* (recommended)
3. Deprecation: src.* imports will show warnings
"""

__version__ = "8.0.0"
__author__ = "IOA Core Team"
__package__ = "ioa.core"

# PATCH: Cursor-2025-01-27 Shim aliases for monorepo transition

# Import the core modules directly
from . import memory_fabric
from . import governance

# Re-export core modules for ioa.core.* access
__all__ = [
    "memory_fabric",
    "governance",
]

# Ensure submodule aliasing works for importers
import sys as _ioa_core_sys
try:
    _ioa_core_sys.modules.setdefault('ioa.core.memory_fabric', memory_fabric)
    _ioa_core_sys.modules.setdefault('ioa.core.governance', governance)
except Exception:
    pass
