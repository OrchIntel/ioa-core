# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Compatibility re-export for legacy `ioa.core.governance.manifest` imports."""

import sys

from ioa_core.governance import manifest as _impl

# Ensure patching `ioa.core.governance.manifest.*` affects the canonical module.
sys.modules[__name__] = _impl
