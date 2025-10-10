""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


import pytest
import sys
import os
from datetime import datetime, timezone

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from memory.core import (
    MemoryEntry, MemoryStats, MemoryStore, MemoryProcessor,
    MemoryEngineInterface, MemoryError, StorageError, ProcessingError
)

class TestMemoryEntry:
    """Test MemoryEntry data structure."""
    
    def test_memory_entry_creation(self):
        """Test creating a MemoryEntry."""
        entry = MemoryEntry(
            id="test-123",
            content="Test content",
            metadata={"source": "test"},
            tags=["test", "example"]
        )
        
        assert entry.id == "test-123"
        assert entry.content == "Test content"
        assert entry.metadata["source"] == "test"
        assert "test" in entry.tags
        assert entry.storage_tier == "hot"
        assert entry.access_count == 0
    
    def test_memory_entry_to_dict(self):
        """Test converting MemoryEntry to dictionary."""
        entry = MemoryEntry(
            id="test-456",
            content="Test content for dict",
            metadata={"key": "value"},
            tags=["tag1", "tag2"]
        )
        
        entry_dict = entry.to_dict()
        
        assert entry_dict["id"] == "test-456"
        assert entry_dict["content"] == "Test content for dict"
        assert entry_dict["metadata"]["key"] == "value"
        assert "tag1" in entry_dict["tags"]
        assert entry_dict["storage_tier"] == "hot"
        assert entry_dict["access_count"] == 0
    
    def test_memory_entry_from_dict(self):
        """Test creating MemoryEntry from dictionary."""
        entry_data = {
            "id": "test-789",
            "content": "Test content from dict",
            "metadata": {"from": "dict"},
            "tags": ["from", "dict"],
            "storage_tier": "cold",
            "access_count": 5
        }
        
        entry = MemoryEntry.from_dict(entry_data)
        
        assert entry.id == "test-789"
        assert entry.content == "Test content from dict"
        assert entry.metadata["from"] == "dict"
        assert "from" in entry.tags
        assert entry.storage_tier == "cold"
        assert entry.access_count == 5
    
    def test_memory_entry_timestamp_handling(self):
        """Test timestamp handling in MemoryEntry."""
        # Test with string timestamp
        entry_data = {
            "id": "test-time",
            "content": "Test content",
            "timestamp": "2025-01-27T10:00:00+00:00"
        }
        
        entry = MemoryEntry.from_dict(entry_data)
        assert isinstance(entry.timestamp, datetime)
        
        # Test with last_accessed
        entry_data["last_accessed"] = "2025-01-27T11:00:00+00:00"
        entry = MemoryEntry.from_dict(entry_data)
        assert isinstance(entry.last_accessed, datetime)

class TestMemoryStats:
    """Test MemoryStats data structure."""
    
    def test_memory_stats_creation(self):
        """Test creating MemoryStats."""
        stats = MemoryStats(
            total_entries=100,
            preserved_entries=80,
            digested_entries=20,
            failed_entries=0
        )
        
        assert stats.total_entries == 100
        assert stats.preserved_entries == 80
        assert stats.digested_entries == 20
        assert stats.failed_entries == 0
    
    def test_memory_stats_update(self):
        """Test updating MemoryStats."""
        stats = MemoryStats()
        
        stats.update_stats(
            total_entries=50,
            preserved_entries=30,
            digested_entries=20
        )
        
        assert stats.total_entries == 50
        assert stats.preserved_entries == 30
        assert stats.digested_entries == 20
    
    def test_memory_stats_defaults(self):
        """Test MemoryStats default values."""
        stats = MemoryStats()
        
        assert stats.total_entries == 0
        assert stats.preserved_entries == 0
        assert stats.digested_entries == 0
        assert stats.failed_entries == 0
        assert stats.avg_processing_time == 0.0
        assert stats.storage_tier_distribution == {"hot": 0, "cold": 0, "auto": 0}

class TestMemoryExceptions:
    """Test memory exception classes."""
    
    def test_memory_error_creation(self):
        """Test creating MemoryError."""
        error = MemoryError("Test error", "test_operation", "test-id")
        
        assert str(error) == "Test error"
        assert error.operation == "test_operation"
        assert error.entry_id == "test-id"
        assert hasattr(error, 'timestamp')
    
    def test_storage_error_inheritance(self):
        """Test StorageError inheritance."""
        error = StorageError("Storage failed", "store", "test-id")
        
        assert isinstance(error, MemoryError)
        assert error.operation == "store"
    
    def test_processing_error_inheritance(self):
        """Test ProcessingError inheritance."""
        error = ProcessingError("Processing failed", "process", "test-id")
        
        assert isinstance(error, MemoryError)
        assert error.operation == "process"

class TestMemoryInterfaces:
    """Test memory interface protocols."""
    
    def test_memory_store_protocol(self):
        """Test MemoryStore protocol compliance."""
        # This test ensures the protocol is properly defined
        # Actual implementations will be tested separately
        
        # Check that the protocol methods are defined
        assert hasattr(MemoryStore, '__call__')
        
        # The protocol should have these methods defined
        expected_methods = ['store', 'retrieve', 'search', 'delete', 'list_all', 'get_stats']
        for method in expected_methods:
            assert method in MemoryStore.__dict__ or hasattr(MemoryStore, method)
    
    def test_memory_processor_protocol(self):
        """Test MemoryProcessor protocol compliance."""
        # Check that the protocol methods are defined
        expected_methods = ['process', 'can_process']
        for method in expected_methods:
            assert method in MemoryProcessor.__dict__ or hasattr(MemoryProcessor, method)
    
    def test_memory_engine_interface(self):
        """Test MemoryEngineInterface abstract base class."""
        # This should be an abstract base class
        assert hasattr(MemoryEngineInterface, '__abstractmethods__')
        
        # Check that required methods are abstract
        expected_methods = ['store', 'retrieve', 'search', 'delete', 'get_stats', 'cleanup']
        for method in expected_methods:
            assert method in MemoryEngineInterface.__dict__ or hasattr(MemoryEngineInterface, method)
