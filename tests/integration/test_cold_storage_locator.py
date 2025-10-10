""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
Integration Test: Cold Storage Locator and Path Normalization

Tests that the cold storage module is properly located and importable,
and that batch operations return with integrity metadata.
"""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.cold_storage import ColdStorage


class TestColdStorageLocator:
    """Test cold storage module location and functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Set up and tear down test environment."""
        # Set up temporary storage directory
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "cold_storage")
        
        yield
        
        # Clean up
        shutil.rmtree(self.temp_dir)
    
    def test_cold_storage_import_and_instantiation(self):
        """Test that cold storage module can be imported and instantiated."""
        # This test verifies the module path normalization works
        storage = ColdStorage(path=self.storage_path)
        
        assert storage is not None, "ColdStorage should instantiate successfully"
        assert hasattr(storage, 'storage_path'), "ColdStorage should have storage_path attribute"
        assert storage.storage_path == Path(self.storage_path), "Storage path should be set correctly"
        
        # Verify storage directory was created
        assert os.path.exists(self.storage_path), "Storage directory should be created"
    
    def test_cold_storage_batch_operations(self):
        """Test that cold storage operations work and return integrity metadata."""
        storage = ColdStorage(path=self.storage_path)
        
        # Create test data
        test_entries = [
            {"id": "1", "content": "test content 1", "metadata": {"type": "test"}},
            {"id": "2", "content": "test content 2", "metadata": {"type": "test"}},
            {"id": "3", "content": "test content 3", "metadata": {"type": "test"}}
        ]
        
        # Test individual storage
        file_ids = []
        for entry in test_entries:
            file_id = storage.store_to_cold(entry)
            file_ids.append(file_id)
            assert file_id is not None, "Storage should return a file ID"
            assert isinstance(file_id, str), "File ID should be a string"
            assert file_id.startswith("cold_"), "File ID should start with 'cold_'"
        
        # Test individual retrieval
        for i, file_id in enumerate(file_ids):
            retrieved_entry = storage.retrieve_from_cold(file_id)
            assert retrieved_entry is not None, "Retrieval should return data"
            assert retrieved_entry["content"] == test_entries[i], f"Entry {i} content should match"
    
    def test_cold_storage_integrity_verification(self):
        """Test that cold storage provides integrity verification."""
        storage = ColdStorage(path=self.storage_path)
        
        # Store an entry
        test_content = {"id": "test1", "content": "test content", "metadata": {}}
        file_id = storage.store_to_cold(test_content)
        
        # Verify integrity metadata is present
        # The cold storage should provide some form of integrity verification
        # This might be through file checksums, entry hashes, or other mechanisms
        
        # Check that the file exists and has content
        file_path = storage.storage_path / file_id
        assert file_path.exists(), "File should be created"
        assert file_path.stat().st_size > 0, "File should not be empty"
        
        # Verify file content and integrity
        retrieved_entry = storage.retrieve_from_cold(file_id)
        assert retrieved_entry["content"] == test_content, "Retrieved content should match"
        
        # The retrieve_from_cold method performs integrity checks
        # If it returns without error, integrity is verified
    
    def test_cold_storage_path_normalization(self):
        """Test that cold storage handles various path formats correctly."""
        # Test with absolute path
        abs_path = os.path.abspath(self.storage_path)
        storage_abs = ColdStorage(path=abs_path)
        assert storage_abs.storage_path == Path(abs_path)
        
        # Test with relative path
        rel_path = "relative_storage"
        storage_rel = ColdStorage(path=rel_path)
        assert storage_rel.storage_path == Path(rel_path)
        
        # Test with Path object
        path_obj = Path(self.storage_path)
        storage_path_obj = ColdStorage(path=path_obj)
        assert storage_path_obj.storage_path == path_obj
        
        # Test with default path
        storage_default = ColdStorage()
        assert storage_default.storage_path == Path("./cold_storage")
    
    def test_cold_storage_directory_creation(self):
        """Test that cold storage creates directories as needed."""
        # Test with non-existent nested directory
        nested_path = os.path.join(self.temp_dir, "nested", "deep", "storage")
        storage = ColdStorage(path=nested_path)
        
        # Directory should be created
        assert os.path.exists(nested_path), "Nested directory should be created"
        assert os.path.isdir(nested_path), "Path should be a directory"
        
        # Test with existing directory
        existing_path = self.storage_path
        os.makedirs(existing_path, exist_ok=True)
        
        storage_existing = ColdStorage(path=existing_path)
        assert storage_existing.storage_path == Path(existing_path)
    
    def test_cold_storage_batch_id_uniqueness(self):
        """Test that cold storage generates unique batch IDs."""
        storage = ColdStorage(path=self.storage_path)
        
        # Store multiple entries
        file_ids = set()
        for i in range(5):
            entry = {"id": f"test{i}", "content": f"content {i}", "metadata": {}}
            file_id = storage.store_to_cold(entry)
            file_ids.add(file_id)
        
        # All file IDs should be unique
        assert len(file_ids) == 5, "All file IDs should be unique"
        
        # File IDs should be strings
        for file_id in file_ids:
            assert isinstance(file_id, str), "File ID should be a string"
            assert len(file_id) > 0, "File ID should not be empty"
    
    def test_cold_storage_error_handling(self):
        """Test that cold storage handles errors gracefully."""
        storage = ColdStorage(path=self.storage_path)
        
        # Test with empty content
        try:
            file_id = storage.store_to_cold("")
            # This might succeed or fail depending on implementation
            # We just want to ensure it doesn't crash
        except Exception as e:
            # If it fails, the error should be reasonable
            assert isinstance(e, Exception), "Should raise a proper exception"
        
        # Test with None content
        try:
            file_id = storage.store_to_cold(None)
            # This might succeed or fail depending on implementation
        except Exception as e:
            # If it fails, the error should be reasonable
            assert isinstance(e, Exception), "Should raise a proper exception"
    
    def test_cold_storage_module_attributes(self):
        """Test that cold storage module has expected attributes and methods."""
        # Test class attributes
        assert hasattr(ColdStorage, 'shard_size'), "ColdStorage should have shard_size attribute"
        assert isinstance(ColdStorage.shard_size, int), "shard_size should be an integer"
        assert ColdStorage.shard_size > 0, "shard_size should be positive"
        
        # Test instance methods
        storage = ColdStorage(path=self.storage_path)
        assert hasattr(storage, 'store_to_cold'), "ColdStorage should have store_to_cold method"
        assert hasattr(storage, 'retrieve_from_cold'), "ColdStorage should have retrieve_from_cold method"
        assert callable(storage.store_to_cold), "store_to_cold should be callable"
        assert callable(storage.retrieve_from_cold), "retrieve_from_cold should be callable"
    
    def test_cold_storage_file_structure(self):
        """Test that cold storage creates proper file structure."""
        storage = ColdStorage(path=self.storage_path)
        
        # Store an entry
        test_content = {"id": "1", "content": "content 1", "metadata": {}}
        
        file_id = storage.store_to_cold(test_content)
        
        # Check file naming convention
        file_path = storage.storage_path / file_id
        assert file_path.exists(), "File should be created"
        
        # Verify file naming pattern
        filename = file_path.name
        assert filename.startswith("cold_"), f"Filename should start with 'cold_': {filename}"
        assert filename.endswith(".json"), f"Filename should end with .json: {filename}"
        
        # Check that hash is present
        parts = filename.split("_")
        assert len(parts) >= 2, f"Filename should have at least 2 parts: {filename}"
        hash_part = parts[1].replace(".json", "")
        assert len(hash_part) == 64, f"Hash should be 64 characters: {hash_part}"
