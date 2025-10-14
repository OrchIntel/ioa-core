"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
# PATCH: Cursor-2025-09-11 DISPATCH-OSS-20250911-MEMORY-DOCSYNC <memory fabric migration>
# Comprehensive tests for the Memory Fabric system.
"""

import pytest
import sys
import os
from datetime import datetime, timezone

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from memory_fabric import (
    MemoryFabric, MemoryRecordV1, EmbeddingV1,
    MemoryStore, LocalJSONLStore, SQLiteStore, S3Store,
    MemoryFabricMetrics, MemoryCrypto
)

class TestMemoryRecordV1:
    """Test MemoryRecordV1 data structure."""
    
    def test_memory_record_creation(self):
        """Test creating a MemoryRecordV1."""
        record = MemoryRecordV1(
            id="test-123",
            content="Test content",
            metadata={"source": "test"},
            tags=["test", "example"]
        )
        
        assert record.id == "test-123"
        assert record.content == "Test content"
        assert record.metadata["source"] == "test"
        assert "test" in record.tags
        assert record.storage_tier.value == "hot"
        assert record.access_count == 0
        assert isinstance(record.timestamp, datetime)
    
    def test_memory_record_to_dict(self):
        """Test converting MemoryRecordV1 to dictionary."""
        record = MemoryRecordV1(
            id="test-456",
            content="Test content for dict",
            metadata={"key": "value"},
            tags=["tag1", "tag2"]
        )
        
        record_dict = record.to_dict()
        
        assert record_dict["id"] == "test-456"
        assert record_dict["content"] == "Test content for dict"
        assert record_dict["metadata"]["key"] == "value"
        assert "tag1" in record_dict["tags"]
        assert record_dict["storage_tier"] == "hot"
        assert record_dict["access_count"] == 0
        assert record_dict["timestamp"] is not None
    
    def test_memory_record_from_dict(self):
        """Test creating MemoryRecordV1 from dictionary."""
        record_data = {
            "id": "test-789",
            "content": "Test content from dict",
            "metadata": {"from": "dict"},
            "tags": ["from", "dict"],
            "storage_tier": "cold",
            "access_count": 5,
            "timestamp": "2025-01-27T10:00:00+00:00"
        }
        
        record = MemoryRecordV1.from_dict(record_data)
        
        assert record.id == "test-789"
        assert record.content == "Test content from dict"
        assert record.metadata["from"] == "dict"
        assert "from" in record.tags
        assert record.storage_tier.value == "cold"
        assert record.access_count == 5

class TestMemoryFabric:
    """Test MemoryFabric functionality."""
    
    @pytest.fixture
    def memory_fabric(self):
        """Create a memory fabric instance for testing."""
        return MemoryFabric(
            backend="sqlite",
            config={"path": ":memory:"}
        )
    
    def test_store_content(self, memory_fabric):
        """Test storing content in memory fabric."""
        content = "Test content"
        metadata = {"source": "test"}
        tags = ["test"]
        
        record_id = memory_fabric.store(content, metadata, tags=tags)
        
        assert record_id is not None
        assert len(record_id) > 0
        
        # Verify record was stored
        stored_record = memory_fabric.retrieve(record_id)
        assert stored_record is not None
        assert stored_record.content == "Test content"
        assert stored_record.metadata["source"] == "test"
    
    def test_retrieve_nonexistent(self, memory_fabric):
        """Test retrieving a nonexistent record."""
        result = memory_fabric.retrieve("nonexistent-id")
        assert result is None
    
    def test_delete_record(self, memory_fabric):
        """Test deleting a record."""
        # First store a record
        record_id = memory_fabric.store("To be deleted", {"test": True})
        
        # Verify it exists
        assert memory_fabric.retrieve(record_id) is not None
        
        # Delete it
        success = memory_fabric.delete(record_id)
        assert success is True
        
        # Verify it's gone
        assert memory_fabric.retrieve(record_id) is None
    
    def test_delete_nonexistent(self, memory_fabric):
        """Test deleting a nonexistent record."""
        success = memory_fabric.delete("nonexistent-id")
        assert success is False
    
    def test_search_content(self, memory_fabric):
        """Test searching for content."""
        # Store some test content
        memory_fabric.store("Python programming language", {"topic": "programming"})
        memory_fabric.store("Machine learning algorithms", {"topic": "ai"})
        memory_fabric.store("Web development with Python", {"topic": "programming"})
        
        # Search for Python-related content
        results = memory_fabric.search("Python", limit=10)
        
        assert len(results) >= 2
        contents = [r.content for r in results]
        assert "Python programming language" in contents
        assert "Web development with Python" in contents
    
    def test_list_all_records(self, memory_fabric):
        """Test listing all records."""
        # Store some test records
        memory_fabric.store("Record 1", {"id": 1})
        memory_fabric.store("Record 2", {"id": 2})
        memory_fabric.store("Record 3", {"id": 3})
        
        # List all records
        all_records = memory_fabric.list_all()
        
        assert len(all_records) == 3
        contents = [r.content for r in all_records]
        assert "Record 1" in contents
        assert "Record 2" in contents
        assert "Record 3" in contents
    
    def test_get_stats(self, memory_fabric):
        """Test getting memory statistics."""
        # Store some test content
        memory_fabric.store("Test 1", {"user": "user1"})
        memory_fabric.store("Test 2", {"user": "user2"})
        
        stats = memory_fabric.get_stats()
        
        # Check that stats is a dictionary with expected keys
        assert isinstance(stats, dict)
        assert "backend" in stats
        assert "encryption" in stats
        assert "errors" in stats

class TestMemoryStores:
    """Test different memory store implementations."""
    
    def test_sqlite_store(self):
        """Test SQLite store."""
        store = SQLiteStore({"path": ":memory:"})
        assert store is not None
    
    def test_local_jsonl_store(self):
        """Test Local JSONL store."""
        store = LocalJSONLStore({"path": "/tmp/test.jsonl"})
        assert store is not None
    
    def test_memory_fabric_with_sqlite(self):
        """Test MemoryFabric with SQLite store."""
        fabric = MemoryFabric(
            backend="sqlite",
            config={"path": ":memory:"}
        )
        
        # Test basic operations
        record_id = fabric.store("Test content", {"test": True})
        assert record_id is not None
        
        record = fabric.retrieve(record_id)
        assert record is not None
        assert record.content == "Test content"
    
    def test_memory_fabric_with_jsonl(self):
        """Test MemoryFabric with JSONL store."""
        fabric = MemoryFabric(
            backend="local_jsonl",
            config={"path": "/tmp/test_fabric.jsonl"}
        )
        
        # Test basic operations
        record_id = fabric.store("Test content", {"test": True})
        assert record_id is not None
        
        record = fabric.retrieve(record_id)
        assert record is not None
        assert record.content == "Test content"

class TestMemoryFabricMetrics:
    """Test MemoryFabricMetrics functionality."""
    
    def test_metrics_creation(self):
        """Test creating MemoryFabricMetrics."""
        metrics = MemoryFabricMetrics()
        assert metrics is not None
    
    def test_metrics_tracking(self):
        """Test metrics tracking functionality."""
        metrics = MemoryFabricMetrics()
        
        # Test basic metrics operations
        metrics.record_operation("store", True, 0.1)
        metrics.record_operation("retrieve", True, 0.05)
        metrics.record_operation("search", True, 0.2)
        
        current_metrics = metrics.get_current_metrics()
        assert "ops" in current_metrics
        assert "latency_ms" in current_metrics

class TestMemoryCrypto:
    """Test MemoryCrypto functionality."""
    
    def test_crypto_creation(self):
        """Test creating MemoryCrypto."""
        crypto = MemoryCrypto()
        assert crypto is not None
    
    def test_encryption_decryption(self):
        """Test encryption and decryption."""
        crypto = MemoryCrypto("test_key")
        
        plaintext = "Sensitive data"
        encrypted, mode = crypto.encrypt_content(plaintext)
        decrypted = crypto.decrypt_content(encrypted, mode)
        
        assert decrypted == plaintext
        assert encrypted != plaintext