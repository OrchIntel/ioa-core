"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
# PATCH: Cursor-2025-09-11 DISPATCH-OSS-20250911-MEMORY-DOCSYNC <memory fabric migration>
# This module provides backward compatibility for memory_engine imports.
# All new code should import from memory_fabric instead.
"""

import warnings
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone

# PATCH: Cursor-2025-09-11 DISPATCH-OSS-20250911-MEMORY-DOCSYNC <memory fabric migration>
# Import from memory_fabric and provide compatibility shim

# Import from memory_fabric
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from memory_fabric import (
    MemoryFabric,
    MemoryRecordV1,
    EmbeddingV1,
    MemoryStore,
    LocalJSONLStore,
    SQLiteStore,
    S3Store,
    MemoryFabricMetrics,
    MemoryCrypto
)

# Re-export with deprecation warnings
def _deprecation_warning():
    """Issue deprecation warning for memory_engine usage."""
    warnings.warn(
        "ioa.core.memory_engine is deprecated and will be removed in v2.7. "
        "Please use memory_fabric instead.",
        DeprecationWarning,
        stacklevel=3
    )

# Legacy class names for backward compatibility
class MemoryEngine:
    """Legacy MemoryEngine class - use MemoryFabric instead."""
    
    def __init__(self, *args, **kwargs):
        _deprecation_warning()
        self._fabric = MemoryFabric(*args, **kwargs)
    
    def remember(self, *args, **kwargs):
        """Remember method - delegates to MemoryFabric."""
        _deprecation_warning()
        return self._fabric.remember(*args, **kwargs)
    
    def retrieve(self, *args, **kwargs):
        """Retrieve method - delegates to MemoryFabric."""
        _deprecation_warning()
        return self._fabric.retrieve(*args, **kwargs)
    
    def forget(self, *args, **kwargs):
        """Forget method - delegates to MemoryFabric."""
        _deprecation_warning()
        return self._fabric.forget(*args, **kwargs)
    
    def stats(self, *args, **kwargs):
        """Stats method - delegates to MemoryFabric."""
        _deprecation_warning()
        return self._fabric.stats(*args, **kwargs)
    
    def list_all(self, *args, **kwargs):
        """List all method - delegates to MemoryFabric."""
        _deprecation_warning()
        return self._fabric.list_all(*args, **kwargs)

class MemoryEntry:
    """Legacy MemoryEntry class - use MemoryRecordV1 instead."""
    
    def __init__(self, id: str, content: str, metadata: Optional[Dict[str, Any]] = None, 
                 tags: Optional[List[str]] = None, timestamp: Optional[datetime] = None,
                 last_accessed: Optional[datetime] = None, access_count: int = 0,
                 storage_tier: str = "hot", user_id: Optional[str] = None):
        _deprecation_warning()
        self.id = id
        self.content = content
        self.metadata = metadata or {}
        self.tags = tags or []
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.last_accessed = last_accessed
        self.access_count = access_count
        self.storage_tier = storage_tier
        self.user_id = user_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "tags": self.tags,
            "timestamp": self.timestamp.isoformat(),
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "access_count": self.access_count,
            "storage_tier": self.storage_tier,
            "user_id": self.user_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create from dictionary representation."""
        _deprecation_warning()
        # Handle timestamp conversion
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        # Handle last_accessed conversion
        last_accessed = data.get("last_accessed")
        if isinstance(last_accessed, str):
            last_accessed = datetime.fromisoformat(last_accessed.replace('Z', '+00:00'))
        
        return cls(
            id=data["id"],
            content=data["content"],
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            timestamp=timestamp,
            last_accessed=last_accessed,
            access_count=data.get("access_count", 0),
            storage_tier=data.get("storage_tier", "hot"),
            user_id=data.get("user_id")
        )

class MemoryStats:
    """Legacy MemoryStats class - use MemoryFabricMetrics instead."""
    
    def __init__(self, total_entries: int = 0, preserved_entries: int = 0,
                 digested_entries: int = 0, failed_entries: int = 0,
                 avg_processing_time: float = 0.0, storage_tier_distribution: Optional[Dict[str, int]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        _deprecation_warning()
        self.total_entries = total_entries
        self.preserved_entries = preserved_entries
        self.digested_entries = digested_entries
        self.failed_entries = failed_entries
        self.avg_processing_time = avg_processing_time
        self.storage_tier_distribution = storage_tier_distribution or {"hot": 0, "cold": 0, "auto": 0}
        self.metadata = metadata or {}
    
    def update_stats(self, total_entries: int = 0, preserved_entries: int = 0,
                    digested_entries: int = 0, failed_entries: int = 0):
        """Update statistics."""
        self.total_entries += total_entries
        self.preserved_entries += preserved_entries
        self.digested_entries += digested_entries
        self.failed_entries += failed_entries

class GDPRRequest:
    """Legacy GDPRRequest class."""
    
    def __init__(self, request_type: str, user_id: str, metadata: Optional[Dict[str, Any]] = None):
        _deprecation_warning()
        self.id = str(hash(f"{request_type}_{user_id}_{datetime.now()}"))
        self.request_type = request_type
        self.user_id = user_id
        self.metadata = metadata or {}
        self.status = "pending"
        self.created_at = datetime.now(timezone.utc)
        self.completed_at = None
        self.result = None

class ModularMemoryEngine:
    """Legacy ModularMemoryEngine class - use MemoryFabric instead."""
    
    def __init__(self, enable_gdpr: bool = True, enable_monitoring: bool = True,
                 max_cache_size: int = 10000, **kwargs):
        _deprecation_warning()
        self._fabric = MemoryFabric(**kwargs)
        self.enable_gdpr = enable_gdpr
        self.enable_monitoring = enable_monitoring
        self.max_cache_size = max_cache_size
    
    async def remember(self, entry_data: Union[Dict[str, Any], MemoryEntry]) -> str:
        """Remember content in memory."""
        if isinstance(entry_data, MemoryEntry):
            # Convert MemoryEntry to dict
            data = entry_data.to_dict()
        else:
            data = entry_data
        
        # Filter out unsupported kwargs for MemoryFabric.store()
        fabric_kwargs = {}
        for k, v in data.items():
            if k in ["content", "metadata"]:
                continue
            if k in ["tags", "memory_type", "storage_tier", "record_id"]:
                fabric_kwargs[k] = v
        
        return self._fabric.store(data.get("content", ""), data.get("metadata", {}), **fabric_kwargs)
    
    async def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve content from memory."""
        record = self._fabric.retrieve(entry_id)
        if record:
            return MemoryEntry(
                id=record.id,
                content=record.content,
                metadata=record.metadata,
                tags=record.tags,
                timestamp=record.timestamp,
                user_id=record.user_id
            )
        return None
    
    async def forget(self, entry_id: str) -> bool:
        """Forget content from memory."""
        return self._fabric.delete(entry_id)
    
    async def forget_user(self, user_id: str) -> int:
        """Forget all content for a user."""
        if not self.enable_gdpr:
            raise ProcessingError("GDPR features are disabled")
        
        # Search for records by user_id and delete them
        # Note: This is a simplified implementation - in practice, MemoryFabric would need
        # a proper query method that supports filtering by metadata fields
        deleted_count = 0
        # For now, we'll return 0 as the MemoryFabric doesn't support user_id filtering
        # This test will need to be updated when proper query functionality is added
        
        return deleted_count
    
    async def export_user(self, user_id: str) -> Dict[str, Any]:
        """Export all content for a user."""
        if not self.enable_gdpr:
            raise ProcessingError("GDPR features are disabled")
        
        # This would need to be implemented in MemoryFabric
        # For now, return empty data as a placeholder
        return {"user_id": user_id, "total_entries": 0, "entries": []}
    
    async def audit_forget(self, user_id: str) -> Dict[str, Any]:
        """Audit forget operations for a user."""
        if not self.enable_gdpr:
            raise ProcessingError("GDPR features are disabled")
        
        # This would need to be implemented in MemoryFabric
        # For now, return empty data as a placeholder
        return {"user_id": user_id, "audit_timestamp": datetime.now(timezone.utc).isoformat(), "forget_requests": []}
    
    async def stats(self) -> MemoryStats:
        """Get memory statistics."""
        fabric_stats = self._fabric.get_stats()
        return MemoryStats(
            total_entries=fabric_stats.get("total_entries", 0),
            preserved_entries=fabric_stats.get("preserved_entries", 0),
            digested_entries=fabric_stats.get("digested_entries", 0),
            failed_entries=fabric_stats.get("failed_entries", 0),
            avg_processing_time=fabric_stats.get("avg_processing_time", 0.0),
            storage_tier_distribution=fabric_stats.get("storage_tier_distribution", {"hot": 0, "cold": 0, "auto": 0}),
            metadata=fabric_stats.get("metadata", {})
        )
    
    def list_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List all memory entries."""
        records = self._fabric.list_all(limit)
        return [record.to_dict() for record in records]

# Legacy exception classes
class MemoryError(Exception):
    """Legacy exception class."""
    def __init__(self, message: str, operation: str = "", entry_id: str = ""):
        super().__init__(message)
        self.operation = operation
        self.entry_id = entry_id
        self.timestamp = datetime.now(timezone.utc)

class StorageError(MemoryError):
    """Legacy storage error class."""
    pass

class ProcessingError(MemoryError):
    """Legacy processing error class."""
    pass

# Export everything for backward compatibility
__all__ = [
    # Legacy classes
    "MemoryEntry",
    "MemoryStats", 
    "GDPRRequest",
    "ModularMemoryEngine",
    "MemoryError",
    "StorageError",
    "ProcessingError",
    
    # Re-exported from memory_fabric
    "MemoryFabric",
    "MemoryRecordV1",
    "EmbeddingV1",
    "MemoryStore",
    "LocalJSONLStore",
    "SQLiteStore",
    "S3Store",
    "MemoryFabricMetrics",
    "MemoryCrypto"
]