""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
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
