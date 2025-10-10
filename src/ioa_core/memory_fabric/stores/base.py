# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.



from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Protocol
from ..schema import MemoryRecordV1

# PATCH: Cursor-2025-09-10 DISPATCH-OSS-20250910-MEMORY-FABRIC-REFACTOR <store protocols>
"""Base module."""


class MemoryStore(Protocol):
    """Protocol for synchronous memory storage implementations."""
    
    def store(self, record: MemoryRecordV1) -> bool:
        """Store a memory record."""
        ...
    
    def retrieve(self, record_id: str) -> Optional[MemoryRecordV1]:
        """Retrieve a memory record by ID."""
        ...
    
    def search(self, query: str, limit: int = 10, memory_type: Optional[str] = None) -> List[MemoryRecordV1]:
        """Search for memory records."""
        ...
    
    def delete(self, record_id: str) -> bool:
        """Delete a memory record."""
        ...
    
    def list_all(self, limit: Optional[int] = None) -> List[MemoryRecordV1]:
        """List all memory records."""
        ...
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        ...
    
    def close(self) -> None:
        """Close the store and cleanup resources."""
        ...

class AsyncMemoryStore(Protocol):
    """Protocol for asynchronous memory storage implementations."""
    
    async def store(self, record: MemoryRecordV1) -> bool:
        """Store a memory record."""
        ...
    
    async def retrieve(self, record_id: str) -> Optional[MemoryRecordV1]:
        """Retrieve a memory record by ID."""
        ...
    
    async def search(self, query: str, limit: int = 10, memory_type: Optional[str] = None) -> List[MemoryRecordV1]:
        """Search for memory records."""
        ...
    
    async def delete(self, record_id: str) -> bool:
        """Delete a memory record."""
        ...
    
    async def list_all(self, limit: Optional[int] = None) -> List[MemoryRecordV1]:
        """List all memory records."""
        ...
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        ...
    
    async def close(self) -> None:
        """Close the store and cleanup resources."""
        ...

class BaseMemoryStore(ABC):
    """Base implementation for memory stores with common functionality."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the store with configuration."""
        self.config = config or {}
        self._stats = {
            "reads": 0,
            "writes": 0,
            "queries": 0,
            "errors": 0,
            "total_records": 0
        }
    
    def _update_stats(self, operation: str, success: bool = True):
        """Update internal statistics."""
        if operation in self._stats:
            self._stats[operation] += 1
        if not success:
            self._stats["errors"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return self._stats.copy()
    
    def _validate_record(self, record: MemoryRecordV1) -> bool:
        """Validate a memory record before storage."""
        if not record.id:
            return False
        if not record.content:
            return False
        if not record.__schema_version__:
            return False
        return True
