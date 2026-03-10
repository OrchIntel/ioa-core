# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Compatibility shim for legacy ``src.vendor_neutral_roundtable`` imports."""

import sys

from ioa_core import vendor_neutral_roundtable as _impl

# Make this import path an alias to the canonical module so monkeypatch/patch
# calls against `src.vendor_neutral_roundtable.*` affect the same objects.
sys.modules[__name__] = _impl
