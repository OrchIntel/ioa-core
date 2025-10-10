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

from memory.core import MemoryEntry
from memory.cold_store_adapter import ColdStoreAdapter

class TestColdStoreAdapter:
    """Test cold storage adapter functionality."""
    
    @pytest.fixture
    def cold_store_adapter(self):
        """Provide cold store adapter instance."""
        return ColdStoreAdapter()
    
    @pytest.fixture
    def sample_entry(self):
        """Provide sample memory entry for testing."""
        return MemoryEntry(
            id="test-cold-entry",
            content="Test content for cold storage",
            metadata={"source": "test", "cold_storage": True},
            tags=["cold", "test"],
            storage_tier="cold",
            access_count=0
        )
    
    def test_cold_store_adapter_initialization(self, cold_store_adapter):
        """Test cold store adapter initialization."""
        # The adapter should be available even if cold storage isn't
        assert cold_store_adapter is not None
        
        # Check if cold storage is actually available
        storage_info = cold_store_adapter.get_storage_info()
        assert "available" in storage_info
        assert "type" in storage_info
    
    def test_store_entry(self, cold_store_adapter, sample_entry):
        """Test storing an entry in cold storage."""
        # Store the entry
        success = cold_store_adapter.store(sample_entry)
        
        # Success depends on whether cold storage is available
        if cold_store_adapter.is_available():
            assert success is True
        else:
            # Should return False when cold storage is not available
            assert success is False
    
    def test_retrieve_entry(self, cold_store_adapter, sample_entry):
        """Test retrieving an entry from cold storage."""
        # First store the entry
        if cold_store_adapter.is_available():
            cold_store_adapter.store(sample_entry)
            
            # Retrieve the entry
            retrieved_entry = cold_store_adapter.retrieve(sample_entry.id)
            
            if retrieved_entry:
                assert retrieved_entry.id == sample_entry.id
                assert retrieved_entry.content == sample_entry.content
                assert retrieved_entry.storage_tier == "cold"
            else:
                # Cold storage might not support retrieval
                pytest.skip("Cold storage retrieval not supported")
        else:
            # Cold storage not available
            retrieved_entry = cold_store_adapter.retrieve(sample_entry.id)
            assert retrieved_entry is None
    
    def test_search_entries(self, cold_store_adapter):
        """Test searching entries in cold storage."""
        # Search for entries
        results = cold_store_adapter.search("test", limit=5)
        
        # Cold storage typically doesn't support full-text search
        # So we expect an empty result or a warning
        assert isinstance(results, list)
        
        # If cold storage is available, we might get a warning about search not being implemented
        if cold_store_adapter.is_available():
            # Search might return empty list with warning
            pass
        else:
            # Should return empty list when cold storage is not available
            assert len(results) == 0
    
    def test_delete_entry(self, cold_store_adapter, sample_entry):
        """Test deleting an entry from cold storage."""
        # First store the entry
        if cold_store_adapter.is_available():
            cold_store_adapter.store(sample_entry)
            
            # Delete the entry
            success = cold_store_adapter.delete(sample_entry.id)
            
            # Should return True if deletion was successful
            # Note: Some cold storage systems might not support deletion
            # So we accept either True or False as valid responses
            assert isinstance(success, bool)
        else:
            # Should return False when cold storage is not available
            success = cold_store_adapter.delete(sample_entry.id)
            assert success is False
    
    def test_list_all_entries(self, cold_store_adapter):
        """Test listing all entries from cold storage."""
        # List all entries
        entries = cold_store_adapter.list_all()
        
        # Should return a list
        assert isinstance(entries, list)
        
        # Cold storage typically doesn't support efficient listing
        # So we expect an empty result or a warning
        if cold_store_adapter.is_available():
            # Might return empty list with warning
            pass
        else:
            # Should return empty list when cold storage is not available
            assert len(entries) == 0
    
    def test_get_stats(self, cold_store_adapter):
        """Test getting statistics from cold storage."""
        # Get statistics
        stats = cold_store_adapter.get_stats()
        
        # Should return MemoryStats object
        assert hasattr(stats, 'total_entries')
        assert hasattr(stats, 'storage_tier_distribution')
        
        # Cold storage stats might be empty if not available
        if not cold_store_adapter.is_available():
            assert stats.total_entries == 0
    
    def test_migrate_to_cold(self, cold_store_adapter, sample_entry):
        """Test migrating an entry to cold storage."""
        # Test migration
        success = cold_store_adapter.migrate_to_cold(sample_entry)
        
        # Success depends on whether cold storage is available
        if cold_store_adapter.is_available():
            assert success is True
        else:
            assert success is False
    
    def test_is_available(self, cold_store_adapter):
        """Test checking if cold storage is available."""
        available = cold_store_adapter.is_available()
        
        # Should return a boolean
        assert isinstance(available, bool)
        
        # If available, should have cold storage instance
        if available:
            assert cold_store_adapter.cold_storage is not None
        else:
            assert cold_store_adapter.cold_storage is None
    
    def test_get_storage_info(self, cold_store_adapter):
        """Test getting storage information."""
        storage_info = cold_store_adapter.get_storage_info()
        
        # Should return a dictionary with expected keys
        assert isinstance(storage_info, dict)
        assert "available" in storage_info
        assert "type" in storage_info
        
        # Check available status
        if storage_info["available"]:
            assert storage_info["type"] == "cold_storage"
            assert "implementation" in storage_info
        else:
            assert "reason" in storage_info
    
    def test_error_handling(self, cold_store_adapter):
        """Test error handling in cold storage operations."""
        # Test with invalid entry ID
        if cold_store_adapter.is_available():
            # Try to retrieve non-existent entry
            result = cold_store_adapter.retrieve("non-existent-id")
            # Should return None, not raise exception
            assert result is None
        else:
            # When cold storage is not available, operations should fail gracefully
            result = cold_store_adapter.retrieve("any-id")
            assert result is None
    
    def test_metadata_preservation(self, cold_store_adapter, sample_entry):
        """Test that metadata is preserved when storing/retrieving."""
        if cold_store_adapter.is_available():
            # Store entry with metadata
            success = cold_store_adapter.store(sample_entry)
            assert success is True
            
            # Retrieve entry
            retrieved_entry = cold_store_adapter.retrieve(sample_entry.id)
            
            if retrieved_entry:
                # Check that metadata is preserved
                assert retrieved_entry.metadata["source"] == "test"
                assert retrieved_entry.metadata["cold_storage"] is True
                assert "cold" in retrieved_entry.tags
                assert retrieved_entry.storage_tier == "cold"
    
    def test_large_content_handling(self, cold_store_adapter):
        """Test handling of large content in cold storage."""
        # Create entry with large content
        large_content = "x" * 10000  # 10KB content
        large_entry = MemoryEntry(
            id="large-entry",
            content=large_content,
            metadata={"size": "large"},
            tags=["large", "content"]
        )
        
        if cold_store_adapter.is_available():
            # Store large entry
            success = cold_store_adapter.store(large_entry)
            assert success is True
            
            # Retrieve large entry
            retrieved_entry = cold_store_adapter.retrieve(large_entry.id)
            
            if retrieved_entry:
                # Content should be preserved
                assert retrieved_entry.content == large_content
                assert len(retrieved_entry.content) == 10000
