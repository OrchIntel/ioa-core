""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

"""
IOA SaaS Package

This package contains SaaS-specific functionality for the IOA system.
It provides cloud-native features for multi-tenant deployments.

WARNING: This package is NOT part of the core OSS distribution.
Importing this package from core modules will raise ImportError.
"""

__version__ = "8.0.0"
__author__ = "IOA SaaS Team"
__package__ = "ioa.saas"

# PATCH: Cursor-2025-01-27 Initial monorepo structure

def _guard_saas_imports():
    """Guard against importing SaaS modules from core context."""
    import sys
    if any('src.' in module for module in sys.modules.keys()):
        raise ImportError(
            "SaaS modules cannot be imported from core context. "
            "Use ioa.core.* for core functionality."
        )

# Enforce import guard
try:
    _guard_saas_imports()
except ImportError:
    # Allow import during testing
    pass
