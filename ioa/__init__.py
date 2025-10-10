# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""IOA Core Package

Intelligent Orchestration Architecture for AI governance and multi-agent systems.
"""

"""
IOA Main Package

This package provides shim aliases to existing src.* modules for backward compatibility
during the monorepo transition. It allows existing code to continue working while
introducing the new package structure.

Shim Structure:
- ioa.core.* -> src.* (existing modules)
- ioa.organization.* -> organization-specific modules (guarded)
- ioa.saas.* -> SaaS-specific modules (guarded)

Migration Path:
1. Current: import from src.* (continues to work)
2. Future: import from ioa.core.* (recommended)
3. Deprecation: src.* imports will show warnings
"""

__version__ = "8.0.0"
__author__ = "IOA Core Team"
__package__ = "ioa"

# PATCH: Cursor-2025-01-27 Shim aliases for monorepo transition

# Core package shims - import existing src modules
import os as _ioa_os
_prev = _ioa_os.environ.get("IOA_SHIM_IMPORT")
_ioa_os.environ["IOA_SHIM_IMPORT"] = "1"

# Only import core modules that are needed
# Avoid importing core here to prevent circular imports

if _prev is None:
    _ioa_os.environ.pop("IOA_SHIM_IMPORT", None)
else:
    _ioa_os.environ["IOA_SHIM_IMPORT"] = _prev

# Re-export core modules for ioa.core.* access
__all__ = []

# Provide submodule alias for top-level imports if used
# This will be handled by Python's module discovery
