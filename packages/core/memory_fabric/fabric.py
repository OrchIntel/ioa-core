""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import os
import logging
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone

from .schema import MemoryRecordV1, MemoryType, StorageTier
from .stores.base import MemoryStore
from .stores.local_jsonl import LocalJSONLStore
from .stores.sqlite import SQLiteStore
from .stores.s3 import S3Store
from .crypto import MemoryCrypto
from .metrics import MemoryFabricMetrics, MetricsCollector

# PATCH: Cursor-2025-09-10 DISPATCH-OSS-20250910-MEMORY-FABRIC-REFACTOR <main fabric>

class MemoryFabric:
    """Main Memory Fabric facade providing CRUD and query operations."""
    
    def __init__(
        self,
        backend: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        encryption_key: Optional[str] = None,
        enable_metrics: bool = True
    ):
        """
        Initialize Memory Fabric.
        
        Args:
            backend: Storage backend ('local_jsonl', 'sqlite', 's3')
            config: Backend-specific configuration
            encryption_key: Optional encryption key for AES-GCM
            enable_metrics: Enable metrics collection
        """
        self.logger = logging.getLogger(__name__)
        
        # Get backend from environment or parameter
        self.backend_name = backend or os.getenv("IOA_FABRIC_BACKEND", "local_jsonl")
        
        # Get root directory from environment
        self.root_dir = os.getenv("IOA_FABRIC_ROOT", "./artifacts/memory/")
        
        # Initialize configuration
        self.config = config or {}
        self.config.setdefault("data_dir", self.root_dir)
        
        # Initialize encryption
        self.crypto = MemoryCrypto(encryption_key or os.getenv("IOA_FABRIC_KEY"))
        
        # Initialize metrics
        self.metrics = MemoryFabricMetrics() if enable_metrics else None
        if self.metrics:
            self.metrics.set_backend(self.backend_name)
            self.metrics.set_encryption_mode(self.crypto.get_encryption_mode())
        
        # Initialize store
        self._store = self._create_store()
        
        self.logger.info(f"Memory Fabric initialized with {self.backend_name} backend")
        if self.crypto.is_encryption_enabled():
            self.logger.info("Encryption enabled with AES-GCM")
    
    def _create_store(self) -> MemoryStore:
        """Create the appropriate store based on backend."""
        if self.backend_name == "local_jsonl":
            return LocalJSONLStore(self.config)
        elif self.backend_name == "sqlite":
            return SQLiteStore(self.config)
        elif self.backend_name == "s3":
            return S3Store(self.config)
        else:
            raise ValueError(f"Unknown backend: {self.backend_name}")
    
    def store(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        memory_type: Union[str, MemoryType] = MemoryType.CONVERSATION,
        storage_tier: Union[str, StorageTier] = StorageTier.HOT,
        record_id: Optional[str] = None
    ) -> str:
        """
        Store content in memory fabric.
        
        Args:
            content: Content to store
            metadata: Optional metadata
            tags: Optional tags
            memory_type: Type of memory
            storage_tier: Storage tier preference
            record_id: Optional custom record ID
            
        Returns:
            Record ID
        """
        with MetricsCollector(self.metrics, "writes") if self.metrics else nullcontext():
            try:
                # Create memory record
                record = MemoryRecordV1(
                    id=record_id or "",
                    content=content,
                    metadata=metadata or {},
                    tags=tags or [],
                    memory_type=MemoryType(memory_type) if isinstance(memory_type, str) else memory_type,
                    storage_tier=StorageTier(storage_tier) if isinstance(storage_tier, str) else storage_tier
                )
                
                # Encrypt content if encryption is enabled
                if self.crypto.is_encryption_enabled():
                    encrypted_content, encryption_mode = self.crypto.encrypt_content(content)
                    record.content = encrypted_content
                    record.metadata["encryption_mode"] = encryption_mode
                
                # Store record
                success = self._store.store(record)
                if not success:
                    raise Exception("Failed to store record")
                
                # Update metrics
                if self.metrics:
                    self.metrics.update_record_count(len(self.list_all()))
                
                self.logger.debug(f"Stored record {record.id}")
                return record.id
                
            except Exception as e:
                self.logger.error(f"Failed to store record: {e}")
                raise
    
    def retrieve(self, record_id: str) -> Optional[MemoryRecordV1]:
        """
        Retrieve a memory record by ID.
        
        Args:
            record_id: Record ID to retrieve
            
        Returns:
            Memory record or None if not found
        """
        with MetricsCollector(self.metrics, "reads") if self.metrics else nullcontext():
            try:
                record = self._store.retrieve(record_id)
                if not record:
                    return None
                
                # Decrypt content if encrypted
                if self.crypto.is_encryption_enabled() and record.metadata.get("encryption_mode") == "aes-gcm":
                    decrypted_content = self.crypto.decrypt_content(record.content, "aes-gcm")
                    record.content = decrypted_content
                
                self.logger.debug(f"Retrieved record {record_id}")
                return record
                
            except Exception as e:
                self.logger.error(f"Failed to retrieve record {record_id}: {e}")
                return None
    
    def search(
        self,
        query: str,
        limit: int = 10,
        memory_type: Optional[str] = None,
        storage_tier: Optional[str] = None
    ) -> List[MemoryRecordV1]:
        """
        Search for memory records.
        
        Args:
            query: Search query
            limit: Maximum number of results
            memory_type: Filter by memory type
            storage_tier: Filter by storage tier
            
        Returns:
            List of matching records
        """
        with MetricsCollector(self.metrics, "queries") if self.metrics else nullcontext():
            try:
                results = self._store.search(query, limit, memory_type)
                
                # Decrypt results if encryption is enabled
                if self.crypto.is_encryption_enabled():
                    for record in results:
                        if record.metadata.get("encryption_mode") == "aes-gcm":
                            decrypted_content = self.crypto.decrypt_content(record.content, "aes-gcm")
                            record.content = decrypted_content
                
                # Filter by storage tier if specified
                if storage_tier:
                    results = [r for r in results if r.storage_tier.value == storage_tier]
                
                self.logger.debug(f"Search returned {len(results)} results for query: {query}")
                return results
                
            except Exception as e:
                self.logger.error(f"Failed to search: {e}")
                return []
    
    def delete(self, record_id: str) -> bool:
        """
        Delete a memory record.
        
        Args:
            record_id: Record ID to delete
            
        Returns:
            True if deleted, False otherwise
        """
        with MetricsCollector(self.metrics, "writes") if self.metrics else nullcontext():
            try:
                success = self._store.delete(record_id)
                if success and self.metrics:
                    self.metrics.update_record_count(len(self.list_all()))
                
                self.logger.debug(f"Deleted record {record_id}")
                return success
                
            except Exception as e:
                self.logger.error(f"Failed to delete record {record_id}: {e}")
                return False
    
    def list_all(self, limit: Optional[int] = None) -> List[MemoryRecordV1]:
        """
        List all memory records.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of all records
        """
        with MetricsCollector(self.metrics, "reads") if self.metrics else nullcontext():
            try:
                results = self._store.list_all(limit)
                
                # Decrypt results if encryption is enabled
                if self.crypto.is_encryption_enabled():
                    for record in results:
                        if record.metadata.get("encryption_mode") == "aes-gcm":
                            decrypted_content = self.crypto.decrypt_content(record.content, "aes-gcm")
                            record.content = decrypted_content
                
                return results
                
            except Exception as e:
                self.logger.error(f"Failed to list records: {e}")
                return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory fabric statistics."""
        stats = self._store.get_stats()
        
        if self.metrics:
            metrics = self.metrics.get_current_metrics()
            stats.update(metrics)
        
        return stats
    
    def close(self):
        """Close the memory fabric and cleanup resources."""
        if self._store:
            self._store.close()
        
        if self.metrics:
            self.logger.info(self.metrics.get_metrics_summary())
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the memory fabric."""
        health = {
            "status": "healthy",
            "backend": self.backend_name,
            "encryption": self.crypto.get_encryption_mode(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Test basic operations
            test_id = self.store("test_health_check", {"test": True})
            retrieved = self.retrieve(test_id)
            
            if retrieved and retrieved.content == "test_health_check":
                health["operations"] = "working"
                self.delete(test_id)  # Cleanup
            else:
                health["status"] = "degraded"
                health["operations"] = "failed"
                
        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
        
        return health

# Context manager for null operations
class nullcontext:
    """Null context manager for when metrics are disabled."""
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
