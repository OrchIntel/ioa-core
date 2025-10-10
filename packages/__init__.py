""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""

PATCH: Cursor-2025-08-23 CI Strict Remediation - Package structure initialization
"""

"""
IOA Packages Root

This package provides access to the core, enterprise, and SaaS packages
in the IOA monorepo structure.
"""

__version__ = "2.5.0"
__package__ = "packages"

# Import subpackages to make them available
try:
    from . import core
except ImportError:
    pass

try:
    from . import enterprise
except ImportError:
    pass

try:
    from . import saas
except ImportError:
    pass

# PATCH: Cursor-2025-08-23 CI environment verification
