""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


import json
import datetime
from typing import Dict, List, Any, Optional, Union, Protocol
from abc import ABC, abstractmethod
from datetime import timezone
from dataclasses import dataclass, field

# PATCH: Cursor-2025-01-27 DISPATCH-GPT-20250825-031 <memory engine modularization>

@dataclass
class MemoryEntry:
    """Core memory entry data structure."""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(timezone.utc))
    tags: List[str] = field(default_factory=list)
    storage_tier: str = "hot"  # hot, cold, auto
    access_count: int = 0
    last_accessed: Optional[datetime.datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "storage_tier": self.storage_tier,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create from dictionary representation."""
        entry = cls(
            id=data["id"],
            content=data["content"],
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            storage_tier=data.get("storage_tier", "hot"),
            access_count=data.get("access_count", 0)
        )
        
        # Parse timestamps
        if "timestamp" in data:
            entry.timestamp = datetime.datetime.fromisoformat(data["timestamp"])
        if "last_accessed" in data and data["last_accessed"]:
            entry.last_accessed = datetime.datetime.fromisoformat(data["last_accessed"])
        
        return entry

@dataclass
class MemoryStats:
    """Memory system statistics."""
    total_entries: int = 0
    preserved_entries: int = 0
    digested_entries: int = 0
    failed_entries: int = 0
    avg_processing_time: float = 0.0
    storage_tier_distribution: Dict[str, int] = field(default_factory=lambda: {"hot": 0, "cold": 0, "auto": 0})
    pattern_match_rate: float = 0.0
    preservation_rate: float = 0.0
    
    def update_stats(self, **kwargs):
        """Update statistics with new values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

class MemoryStore(Protocol):
    """Protocol for memory storage implementations."""
    
    def store(self, entry: MemoryEntry) -> bool:
        """Store a memory entry."""
        ...
    
    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by ID."""
        ...
    
    def search(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """Search for memory entries."""
        ...
    
    def delete(self, entry_id: str) -> bool:
        """Delete a memory entry."""
        ...
    
    def list_all(self) -> List[MemoryEntry]:
        """List all memory entries."""
        ...
    
    def get_stats(self) -> MemoryStats:
        """Get storage statistics."""
        ...

class MemoryProcessor(Protocol):
    """Protocol for memory processing implementations."""
    
    def process(self, entry: MemoryEntry) -> MemoryEntry:
        """Process a memory entry."""
        ...
    
    def can_process(self, entry: MemoryEntry) -> bool:
        """Check if this processor can handle the entry."""
        ...

class MemoryEngineInterface(ABC):
    """Abstract interface for memory engine implementations."""
    
    @abstractmethod
    def store(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store content in memory."""
        pass
    
    @abstractmethod
    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve content from memory."""
        pass
    
    @abstractmethod
    def search(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """Search memory for content."""
        pass
    
    @abstractmethod
    def delete(self, entry_id: str) -> bool:
        """Delete content from memory."""
        pass
    
    @abstractmethod
    def get_stats(self) -> MemoryStats:
        """Get memory system statistics."""
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """Perform memory cleanup operations."""
        pass

class MemoryError(Exception):
    """Base exception for memory operations."""
    
    def __init__(self, message: str, operation: Optional[str] = None, entry_id: Optional[str] = None):
        super().__init__(message)
        self.operation = operation
        self.entry_id = entry_id
        self.timestamp = datetime.datetime.now(timezone.utc)

class StorageError(MemoryError):
    """Raised when storage operations fail."""
    pass

class ProcessingError(MemoryError):
    """Raised when processing operations fail."""
    pass

class ValidationError(MemoryError):
    """Raised when validation fails."""
    pass
