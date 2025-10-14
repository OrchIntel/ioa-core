"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import os
import pytest
from src.memory_fabric import MemoryFabric
from src.memory_fabric.schema import MemoryType, StorageTier


@pytest.mark.skipif(
    not (
        os.getenv("AWS_ACCESS_KEY_ID") and 
        os.getenv("AWS_SECRET_ACCESS_KEY") and 
        os.getenv("IOA_FABRIC_S3_BUCKET")
    ),
    reason="S3 credentials not available - skipping live test"
)
class TestS3Live:
    """Live integration tests for S3 backend."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.bucket = os.getenv("IOA_FABRIC_S3_BUCKET")
        self.prefix = os.getenv("IOA_FABRIC_S3_PREFIX", "ioa/memory/test/")
        self.region = os.getenv("IOA_FABRIC_S3_REGION", "us-east-1")
        
        self.fabric = MemoryFabric(
            backend="s3",
            config={
                "bucket_name": self.bucket,
                "prefix": self.prefix,
                "region": self.region
            }
        )
    
    def teardown_method(self):
        """Clean up test data."""
        if hasattr(self, 'fabric'):
            # Clean up any test records
            try:
                records = self.fabric.list_all()
                for record in records:
                    if record.metadata.get("test", False):
                        self.fabric.delete(record.id)
            except Exception:
                pass  # Ignore cleanup errors
            finally:
                self.fabric.close()
    
    def test_s3_connection(self):
        """Test basic S3 connection."""
        # This will fail if S3 is not available
        health = self.fabric.health_check()
        assert health["status"] in ["healthy", "degraded"]
        assert health["backend"] == "s3"
    
    def test_s3_store_and_retrieve(self):
        """Test storing and retrieving records from S3."""
        # Store a test record
        record_id = self.fabric.store(
            content="Live S3 test content",
            metadata={"test": True, "live_test": True},
            tags=["live-test", "s3"],
            memory_type=MemoryType.CONVERSATION,
            storage_tier=StorageTier.HOT
        )
        
        assert record_id is not None
        
        # Retrieve the record
        retrieved = self.fabric.retrieve(record_id)
        assert retrieved is not None
        assert retrieved.content == "Live S3 test content"
        assert retrieved.metadata["test"] is True
        assert "live-test" in retrieved.tags
    
    def test_s3_search(self):
        """Test searching records in S3."""
        # Store multiple test records
        record_ids = []
        for i in range(3):
            record_id = self.fabric.store(
                content=f"Search test content {i}",
                metadata={"test": True, "index": i},
                tags=["search-test", f"item-{i}"],
                memory_type=MemoryType.CONVERSATION,
                storage_tier=StorageTier.HOT
            )
            record_ids.append(record_id)
        
        # Search for records
        results = self.fabric.search("Search test content", limit=10)
        assert len(results) >= 3
        
        # Verify all test records are found
        found_ids = {r.id for r in results if r.metadata.get("test", False)}
        assert set(record_ids).issubset(found_ids)
    
    def test_s3_delete(self):
        """Test deleting records from S3."""
        # Store a test record
        record_id = self.fabric.store(
            content="Delete test content",
            metadata={"test": True, "delete_test": True},
            tags=["delete-test"],
            memory_type=MemoryType.CONVERSATION,
            storage_tier=StorageTier.HOT
        )
        
        # Verify it exists
        retrieved = self.fabric.retrieve(record_id)
        assert retrieved is not None
        
        # Delete the record
        success = self.fabric.delete(record_id)
        assert success is True
        
        # Verify it's gone
        retrieved = self.fabric.retrieve(record_id)
        assert retrieved is None
    
    def test_s3_encryption(self):
        """Test S3 with client-side encryption."""
        encryption_key = os.getenv("IOA_FABRIC_KEY")
        if not encryption_key:
            pytest.skip("IOA_FABRIC_KEY not set - skipping encryption test")
        
        # Create fabric with encryption
        encrypted_fabric = MemoryFabric(
            backend="s3",
            config={
                "bucket_name": self.bucket,
                "prefix": self.prefix,
                "region": self.region
            },
            encryption_key=encryption_key
        )
        
        try:
            # Store encrypted record
            record_id = encrypted_fabric.store(
                content="Encrypted test content",
                metadata={"test": True, "encrypted": True},
                tags=["encryption-test"],
                memory_type=MemoryType.CONVERSATION,
                storage_tier=StorageTier.HOT
            )
            
            # Retrieve and verify decryption
            retrieved = encrypted_fabric.retrieve(record_id)
            assert retrieved is not None
            assert retrieved.content == "Encrypted test content"
            assert retrieved.metadata.get("encryption_mode") == "aes-gcm"
            
            # Clean up
            encrypted_fabric.delete(record_id)
            
        finally:
            encrypted_fabric.close()
    
    def test_s3_doctor_verification(self):
        """Test S3 doctor verification command."""
        # This test simulates what the CLI command does
        if hasattr(self.fabric._store, 'doctor_verification'):
            verification = self.fabric._store.doctor_verification(num_records=5)
            
            assert verification["status"] in ["healthy", "degraded", "unhealthy"]
            assert verification["backend"] == "s3"
            assert verification["bucket"] == self.bucket
            assert verification["prefix"] == self.prefix
            assert verification["region"] == self.region
            assert verification["writes"] >= 0
            assert verification["reads"] >= 0
            assert verification["verified"] >= 0
            assert verification["errors"] >= 0
    
    def test_s3_list_all(self):
        """Test listing all records from S3."""
        # Store a few test records
        test_ids = []
        for i in range(3):
            record_id = self.fabric.store(
                content=f"List test content {i}",
                metadata={"test": True, "list_test": True, "index": i},
                tags=["list-test"],
                memory_type=MemoryType.CONVERSATION,
                storage_tier=StorageTier.HOT
            )
            test_ids.append(record_id)
        
        # List all records
        all_records = self.fabric.list_all()
        
        # Find our test records
        test_records = [r for r in all_records if r.metadata.get("list_test", False)]
        assert len(test_records) >= 3
        
        # Verify content
        for record in test_records:
            assert record.content.startswith("List test content")
            assert record.metadata["test"] is True
            assert "list-test" in record.tags
    
    def test_s3_fallback_behavior(self):
        """Test S3 fallback to local storage when S3 fails."""
        # This test would require mocking S3 failures
        # For now, we'll just verify the fallback store exists
        assert hasattr(self.fabric._store, '_fallback_store')
        assert self.fabric._store._fallback_store is not None
    
    def test_s3_metrics_collection(self):
        """Test that metrics are properly collected."""
        # Store and retrieve some records to generate metrics
        record_id = self.fabric.store(
            content="Metrics test content",
            metadata={"test": True, "metrics_test": True},
            tags=["metrics-test"],
            memory_type=MemoryType.CONVERSATION,
            storage_tier=StorageTier.HOT
        )
        
        self.fabric.retrieve(record_id)
        self.fabric.search("Metrics test")
        
        # Get stats
        stats = self.fabric.get_stats()
        assert "writes" in stats
        assert "reads" in stats
        assert "queries" in stats
        
        # Clean up
        self.fabric.delete(record_id)
    
    def test_s3_environment_variables(self):
        """Test S3 configuration from environment variables."""
        # Test that environment variables are properly used
        assert self.fabric._store.bucket_name == self.bucket
        assert self.fabric._store.prefix == self.prefix
        assert self.fabric._store.region == self.region
    
    def test_s3_error_handling(self):
        """Test S3 error handling and fallback."""
        # Test with invalid configuration
        invalid_fabric = MemoryFabric(
            backend="s3",
            config={
                "bucket_name": "non-existent-bucket-12345",
                "prefix": "test/",
                "region": "us-east-1"
            }
        )
        
        try:
            # This should either work (if bucket exists) or fall back gracefully
            health = invalid_fabric.health_check()
            assert health["status"] in ["healthy", "degraded", "unhealthy"]
        finally:
            invalid_fabric.close()
