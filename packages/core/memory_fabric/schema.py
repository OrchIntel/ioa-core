""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum

# PATCH: Cursor-2025-09-10 DISPATCH-OSS-20250910-MEMORY-FABRIC-REFACTOR <schema versioning>

class StorageTier(str, Enum):
    """Storage tier enumeration."""
    HOT = "hot"
    COLD = "cold"
    AUTO = "auto"

class MemoryType(str, Enum):
    """Memory type enumeration."""
    CONVERSATION = "conversation"
    KNOWLEDGE = "knowledge"
    CONTEXT = "context"
    METADATA = "metadata"

@dataclass
class EmbeddingV1:
    """Embedding vector with versioning."""
    vector: List[float]
    dimension: int
    __schema_version__: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmbeddingV1':
        """Create from dictionary representation."""
        return cls(
            vector=data["vector"],
            model=data["model"],
            dimension=data["dimension"],
            __schema_version__=data.get("__schema_version__", "1.0")
        )

@dataclass
class MemoryRecordV1:
    """Memory record with schema versioning and redaction support."""
    id: str = ""
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = field(default_factory=list)
    storage_tier: StorageTier = StorageTier.HOT
    memory_type: MemoryType = MemoryType.CONVERSATION
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    embedding: Optional[EmbeddingV1] = None
    __schema_version__: str = "1.0"
    
    def __post_init__(self):
        """Post-initialization validation."""
        if not self.id:
            self.id = str(uuid.uuid4())
        if isinstance(self.storage_tier, str):
            self.storage_tier = StorageTier(self.storage_tier)
        if isinstance(self.memory_type, str):
            self.memory_type = MemoryType(self.memory_type)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        data = asdict(self)
        # Convert datetime objects to ISO format
        data["timestamp"] = self.timestamp.isoformat()
        if self.last_accessed:
            data["last_accessed"] = self.last_accessed.isoformat()
        # Convert enum values to strings
        data["storage_tier"] = self.storage_tier.value
        data["memory_type"] = self.memory_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryRecordV1':
        """Create from dictionary representation."""
        # Parse timestamps
        timestamp = datetime.fromisoformat(data["timestamp"]) if isinstance(data["timestamp"], str) else data["timestamp"]
        last_accessed = None
        if data.get("last_accessed"):
            last_accessed = datetime.fromisoformat(data["last_accessed"]) if isinstance(data["last_accessed"], str) else data["last_accessed"]
        
        # Parse embedding if present
        embedding = None
        if data.get("embedding"):
            embedding = EmbeddingV1.from_dict(data["embedding"])
        
        return cls(
            id=data["id"],
            content=data["content"],
            metadata=data.get("metadata", {}),
            timestamp=timestamp,
            tags=data.get("tags", []),
            storage_tier=StorageTier(data.get("storage_tier", "hot")),
            memory_type=MemoryType(data.get("memory_type", "conversation")),
            access_count=data.get("access_count", 0),
            last_accessed=last_accessed,
            embedding=embedding,
            __schema_version__=data.get("__schema_version__", "1.0")
        )
    
    def redacted_view(self, redact_pii: bool = True) -> 'MemoryRecordV1':
        """Return a redacted view of the memory record for logging/examples."""
        redacted_content = self.content
        redacted_metadata = self.metadata.copy()
        
        if redact_pii:
            # Use the crypto module for consistent redaction
            from .crypto import MemoryCrypto
            crypto = MemoryCrypto()
            redacted_content = crypto.redact_pii(self.content)
            
            # Redact sensitive metadata
            sensitive_keys = ['email', 'phone', 'ssn', 'credit_card', 'password', 'token', 'key']
            for key in sensitive_keys:
                if key in redacted_metadata:
                    redacted_metadata[key] = '[REDACTED]'
        
        return MemoryRecordV1(
            id=self.id,
            content=redacted_content,
            metadata=redacted_metadata,
            timestamp=self.timestamp,
            tags=self.tags,
            storage_tier=self.storage_tier,
            memory_type=self.memory_type,
            access_count=self.access_count,
            last_accessed=self.last_accessed,
            embedding=self.embedding,
            __schema_version__=self.__schema_version__
        )
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MemoryRecordV1':
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def update_access(self):
        """Update access tracking."""
        self.access_count += 1
        self.last_accessed = datetime.now(timezone.utc)
    
    def is_expired(self, ttl_seconds: Optional[int] = None) -> bool:
        """Check if the record is expired based on TTL."""
        if ttl_seconds is None:
            return False
        
        age = (datetime.now(timezone.utc) - self.timestamp).total_seconds()
        return age > ttl_seconds
