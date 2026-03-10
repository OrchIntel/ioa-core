# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
"""
IOA Module: src/memory_fabric/__init__.py
Version: v2.5.0
Last-Updated: 2025-09-10
Agents: Cursor assist
Summary: Memory Fabric - modular memory system with multiple backends
"""

from .fabric import MemoryFabric
from .schema import MemoryRecordV1, EmbeddingV1, StorageTier, MemoryType
from .stores.base import MemoryStore
from .stores.local_jsonl import LocalJSONLStore
from .stores.sqlite import SQLiteStore
from .stores.s3 import S3Store
from .metrics import MemoryFabricMetrics
from .crypto import MemoryCrypto

__all__ = [
    "MemoryFabric",
    "MemoryRecordV1", 
    "EmbeddingV1",
    "StorageTier",
    "MemoryType",
    "MemoryStore",
    "LocalJSONLStore",
    "SQLiteStore", 
    "S3Store",
    "MemoryFabricMetrics",
    "MemoryCrypto"
]

__version__ = "1.0.0"
__schema_version__ = "1.0"
