# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Compatibility package shim for legacy ``memory_engine`` imports."""

from ioa.core.memory_engine import MemoryEngine, ModularMemoryEngine

__all__ = [
    "MemoryEngine",
    "ModularMemoryEngine",
]
