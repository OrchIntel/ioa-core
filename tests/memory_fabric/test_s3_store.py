""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import json
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from src.memory_fabric.stores.s3 import S3Store
from src.memory_fabric.schema import MemoryRecordV1, MemoryType, StorageTier


class TestS3Store:
    """Test S3 store functionality with mocked boto3 client."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "bucket_name": "test-bucket",
            "prefix": "test-prefix/",
            "region": "us-east-1"
        }
        
        # Mock boto3 client
        self.mock_s3_client = Mock()
        self.mock_s3_client.head_bucket.return_value = {}
        self.mock_s3_client.put_object.return_value = {"ETag": '"test-etag"'}
        self.mock_s3_client.get_object.return_value = {
            "Body": Mock(read=Mock(return_value=b'{"id": "test", "content": "test content"}'))
        }
        self.mock_s3_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "test-prefix/record1.json"},
                {"Key": "test-prefix/record2.json"}
            ]
        }
        self.mock_s3_client.delete_object.return_value = {}
    
    @patch('boto3.Session')
    @patch('boto3.client')
    def test_s3_store_initialization(self, mock_client, mock_session):
        """Test S3 store initialization with mocked boto3."""
        mock_session.return_value.get_credentials.return_value = Mock()
        mock_client.return_value = self.mock_s3_client
        
        store = S3Store(self.config)
        
        assert store.bucket_name == "test-bucket"
        assert store.prefix == "test-prefix/"
        assert store.region == "us-east-1"
        assert store.is_available() is True
    
    @patch('boto3.Session')
    @patch('boto3.client')
    def test_s3_store_initialization_with_env_vars(self, mock_client, mock_session):
        """Test S3 store initialization with environment variables."""
        mock_session.return_value.get_credentials.return_value = Mock()
        mock_client.return_value = self.mock_s3_client
        
        with patch.dict(os.environ, {
            'IOA_FABRIC_S3_BUCKET': 'env-bucket',
            'IOA_FABRIC_S3_PREFIX': 'env-prefix/',
            'IOA_FABRIC_S3_REGION': 'us-west-2'
        }):
            store = S3Store()
            
            assert store.bucket_name == "env-bucket"
            assert store.prefix == "env-prefix/"
            assert store.region == "us-west-2"
    
    @patch('boto3.Session')
    def test_s3_store_fallback_when_no_credentials(self, mock_session):
        """Test S3 store falls back to local storage when no credentials."""
        mock_session.return_value.get_credentials.return_value = None
        
        store = S3Store(self.config)
        
        assert store.is_available() is False
        assert store._fallback_store is not None
    
    @patch('boto3.Session', side_effect=ImportError("boto3 not available"))
    def test_s3_store_fallback_when_import_error(self, mock_session):
        """Test S3 store falls back when boto3 import fails."""
        store = S3Store(self.config)
        
        assert store.is_available() is False
        assert store._fallback_store is not None
    
    @patch('boto3.Session')
    @patch('boto3.client')
    def test_store_record_success(self, mock_client, mock_session):
        """Test successful record storage."""
        mock_session.return_value.get_credentials.return_value = Mock()
        mock_client.return_value = self.mock_s3_client
        
        store = S3Store(self.config)
        record = MemoryRecordV1(
            id="test-id",
            content="test content",
            metadata={"test": True},
            tags=["test"],
            memory_type=MemoryType.CONVERSATION,
            storage_tier=StorageTier.HOT
        )
        
        result = store.store(record)
        
        assert result is True
        self.mock_s3_client.put_object.assert_called_once()
        call_args = self.mock_s3_client.put_object.call_args
        assert call_args[1]["Bucket"] == "test-bucket"
        assert call_args[1]["Key"] == "test-prefix/test-id.json"
        assert call_args[1]["ContentType"] == "application/json"
    
    @patch('boto3.Session')
    @patch('boto3.client')
    def test_store_record_fallback(self, mock_client, mock_session):
        """Test record storage falls back to local when S3 fails."""
        mock_session.return_value.get_credentials.return_value = Mock()
        mock_client.return_value = self.mock_s3_client
        self.mock_s3_client.put_object.side_effect = Exception("S3 error")
        
        store = S3Store(self.config)
        record = MemoryRecordV1(
            id="test-id",
            content="test content",
            metadata={"test": True},
            tags=["test"],
            memory_type=MemoryType.CONVERSATION,
            storage_tier=StorageTier.HOT
        )
        
        # Mock the fallback store
        store._fallback_store = Mock()
        store._fallback_store.store.return_value = True
        
        result = store.store(record)
        
        assert result is True
        store._fallback_store.store.assert_called_once_with(record)
    
    @patch('boto3.Session')
    @patch('boto3.client')
    def test_retrieve_record_success(self, mock_client, mock_session):
        """Test successful record retrieval."""
        mock_session.return_value.get_credentials.return_value = Mock()
        mock_client.return_value = self.mock_s3_client
        
        # Mock the JSON response
        test_record = MemoryRecordV1(
            id="test-id",
            content="test content",
            metadata={"test": True},
            tags=["test"],
            memory_type=MemoryType.CONVERSATION,
            storage_tier=StorageTier.HOT
        )
        
        self.mock_s3_client.get_object.return_value = {
            "Body": Mock(read=Mock(return_value=test_record.to_json().encode('utf-8')))
        }
        
        store = S3Store(self.config)
        result = store.retrieve("test-id")
        
        assert result is not None
        assert result.id == "test-id"
        assert result.content == "test content"
        self.mock_s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test-prefix/test-id.json"
        )
    
    @patch('boto3.Session')
    @patch('boto3.client')
    def test_retrieve_record_fallback(self, mock_client, mock_session):
        """Test record retrieval falls back to local when S3 fails."""
        mock_session.return_value.get_credentials.return_value = Mock()
        mock_client.return_value = self.mock_s3_client
        self.mock_s3_client.get_object.side_effect = Exception("S3 error")
        
        store = S3Store(self.config)
        
        # Mock the fallback store
        test_record = MemoryRecordV1(
            id="test-id",
            content="test content",
            metadata={"test": True},
            tags=["test"],
            memory_type=MemoryType.CONVERSATION,
            storage_tier=StorageTier.HOT
        )
        store._fallback_store = Mock()
        store._fallback_store.retrieve.return_value = test_record
        
        result = store.retrieve("test-id")
        
        assert result == test_record
        store._fallback_store.retrieve.assert_called_once_with("test-id")
    
    @patch('boto3.Session')
    @patch('boto3.client')
    def test_search_records(self, mock_client, mock_session):
        """Test record search functionality."""
        mock_session.return_value.get_credentials.return_value = Mock()
        mock_client.return_value = self.mock_s3_client
        
        # Mock list_objects_v2 response
        self.mock_s3_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "test-prefix/record1.json"},
                {"Key": "test-prefix/record2.json"}
            ]
        }
        
        # Mock individual get_object responses
        test_record1 = MemoryRecordV1(
            id="record1",
            content="test content 1",
            metadata={"test": True},
            tags=["test"],
            memory_type=MemoryType.CONVERSATION,
            storage_tier=StorageTier.HOT
        )
        
        test_record2 = MemoryRecordV1(
            id="record2",
            content="different content",
            metadata={"test": True},
            tags=["test"],
            memory_type=MemoryType.CONVERSATION,
            storage_tier=StorageTier.HOT
        )
        
        def mock_get_object(Bucket, Key):
            if "record1" in Key:
                return {
                    "Body": Mock(read=Mock(return_value=test_record1.to_json().encode('utf-8')))
                }
            else:
                return {
                    "Body": Mock(read=Mock(return_value=test_record2.to_json().encode('utf-8')))
                }
        
        self.mock_s3_client.get_object.side_effect = mock_get_object
        
        store = S3Store(self.config)
        results = store.search("test content", limit=10)
        
        assert len(results) == 1
        assert results[0].content == "test content 1"
        self.mock_s3_client.list_objects_v2.assert_called_once_with(
            Bucket="test-bucket",
            Prefix="test-prefix/"
        )
    
    @patch('boto3.Session')
    @patch('boto3.client')
    def test_delete_record(self, mock_client, mock_session):
        """Test record deletion."""
        mock_session.return_value.get_credentials.return_value = Mock()
        mock_client.return_value = self.mock_s3_client
        
        store = S3Store(self.config)
        result = store.delete("test-id")
        
        assert result is True
        self.mock_s3_client.delete_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test-prefix/test-id.json"
        )
    
    @patch('boto3.Session')
    @patch('boto3.client')
    def test_doctor_verification_success(self, mock_client, mock_session):
        """Test doctor verification with successful operations."""
        mock_session.return_value.get_credentials.return_value = Mock()
        mock_client.return_value = self.mock_s3_client
        
        # Mock successful operations
        self.mock_s3_client.head_bucket.return_value = {}
        self.mock_s3_client.put_object.return_value = {"ETag": '"test-etag"'}
        
        # Mock get_object to return the actual stored record
        def mock_get_object(Bucket, Key):
            # Extract record_id from Key (remove prefix and .json)
            record_id = Key.replace("test-prefix/", "").replace(".json", "")
            return {
                "Body": Mock(read=Mock(return_value=json.dumps({
                    "id": record_id,
                    "content": f"Doctor test record {record_id.split('_')[2]}",
                    "metadata": {"test": True, "index": int(record_id.split('_')[2])},
                    "tags": ["doctor-test", f"record-{record_id.split('_')[2]}"],
                    "memory_type": "conversation",
                    "storage_tier": "hot",
                    "timestamp": "2025-01-01T00:00:00Z",
                    "access_count": 0
                }).encode('utf-8')))
            }
        
        self.mock_s3_client.get_object = mock_get_object
        self.mock_s3_client.delete_object.return_value = {}
        
        store = S3Store(self.config)
        result = store.doctor_verification(num_records=3)
        
        assert result["status"] == "healthy"
        assert result["backend"] == "s3"
        assert result["writes"] == 3
        assert result["reads"] == 3
        assert result["verified"] == 3
        assert result["errors"] == 0
        assert len(result["test_records"]) == 3
    
    @patch('boto3.Session')
    def test_doctor_verification_unavailable(self, mock_session):
        """Test doctor verification when S3 is unavailable."""
        mock_session.return_value.get_credentials.return_value = None
        
        store = S3Store(self.config)
        result = store.doctor_verification(num_records=3)
        
        assert result["status"] == "unavailable"
        assert result["backend"] == "s3"
        assert result["writes"] == 0
        assert result["reads"] == 0
        assert result["verified"] == 0
        assert result["errors"] == 1
        assert "error" in result
    
    @patch('boto3.Session')
    @patch('boto3.client')
    def test_doctor_verification_partial_failure(self, mock_client, mock_session):
        """Test doctor verification with partial failures."""
        mock_session.return_value.get_credentials.return_value = Mock()
        mock_client.return_value = self.mock_s3_client
        
        # Mock some operations to fail
        def mock_put_object(Bucket, Key, Body, ContentType):
            if "doctor_test_1_" in Key:
                raise Exception("S3 error")
            return {"ETag": '"test-etag"'}
        
        self.mock_s3_client.put_object.side_effect = mock_put_object
        self.mock_s3_client.get_object.return_value = {
            "Body": Mock(read=Mock(return_value=b'{"id": "test", "content": "Doctor test record 0"}'))
        }
        self.mock_s3_client.delete_object.return_value = {}
        
        store = S3Store(self.config)
        result = store.doctor_verification(num_records=3)
        
        assert result["status"] in ["degraded", "unhealthy"]
        assert result["writes"] == 3  # All writes succeed via fallback
        assert result["errors"] > 0
    
    def test_close_method(self):
        """Test store close method."""
        store = S3Store(self.config)
        store._fallback_store = Mock()
        
        store.close()
        
        store._fallback_store.close.assert_called_once()
