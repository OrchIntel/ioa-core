""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
Test S3 backend storage operations for audit chains.

Tests the S3 storage backend with mocked S3 operations to ensure
proper listing and fetching of audit chain data.
"""

import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from src.audit.storage import S3Storage
from src.audit.models import AuditEntry, AuditManifest, AuditAnchor


@pytest.fixture
def mock_s3_client():
    """Create a mocked S3 client."""
    client = Mock()
    return client


@pytest.fixture
def s3_storage(mock_s3_client):
    """Create S3Storage instance with mocked client."""
    with patch('boto3.client', return_value=mock_s3_client):
        storage = S3Storage("test-bucket", "test-prefix", "us-east-1")
        storage.s3_client = mock_s3_client
        return storage


def test_s3_list_chains(s3_storage, mock_s3_client):
    """Test listing chains from S3."""
    # Mock S3 response
    mock_s3_client.list_objects_v2.return_value = {
        'CommonPrefixes': [
            {'Prefix': 'test-prefix/chains/chain1/'},
            {'Prefix': 'test-prefix/chains/chain2/'},
            {'Prefix': 'test-prefix/chains/chain3/'}
        ]
    }
    
    chains = s3_storage.list_chains()
    
    assert chains == ['chain1', 'chain2', 'chain3']
    mock_s3_client.list_objects_v2.assert_called_once_with(
        Bucket='test-bucket',
        Prefix='test-prefix/chains',
        Delimiter='/'
    )


def test_s3_list_chains_empty(s3_storage, mock_s3_client):
    """Test listing chains when no chains exist."""
    mock_s3_client.list_objects_v2.return_value = {}
    
    chains = s3_storage.list_chains()
    
    assert chains == []


def test_s3_list_entries(s3_storage, mock_s3_client):
    """Test listing entries for a chain."""
    # Mock S3 response
    mock_s3_client.list_objects_v2.return_value = {
        'Contents': [
            {'Key': 'test-prefix/chains/chain1/000001_event.json'},
            {'Key': 'test-prefix/chains/chain1/000002_event.json'},
            {'Key': 'test-prefix/chains/chain1/MANIFEST.json'},
            {'Key': 'test-prefix/chains/chain1/000003_event.json'}
        ]
    }
    
    entries = s3_storage.list_entries('chain1')
    
    assert entries == ['000001_event.json', '000002_event.json', '000003_event.json']
    mock_s3_client.list_objects_v2.assert_called_once_with(
        Bucket='test-bucket',
        Prefix='test-prefix/chains/chain1'
    )


def test_s3_read_entry(s3_storage, mock_s3_client):
    """Test reading an audit entry from S3."""
    # Mock S3 response
    entry_data = {
        "event_id": "evt_001",
        "timestamp": "2025-09-10T10:00:00Z",
        "prev_hash": "0" * 64,
        "hash": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
        "payload": {
            "event_type": "test_event",
            "data": "test_data"
        },
        "writer": "test_service"
    }
    
    mock_response = Mock()
    mock_response.__getitem__ = Mock(return_value=Mock())
    mock_response['Body'].read.return_value = json.dumps(entry_data).encode('utf-8')
    mock_s3_client.get_object.return_value = mock_response
    
    entry = s3_storage.read_entry('chain1', '000001_event.json')
    
    assert isinstance(entry, AuditEntry)
    assert entry.event_id == "evt_001"
    assert entry.hash == "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
    
    mock_s3_client.get_object.assert_called_once_with(
        Bucket='test-bucket',
        Key='test-prefix/chains/chain1/000001_event.json'
    )


def test_s3_read_manifest(s3_storage, mock_s3_client):
    """Test reading a manifest from S3."""
    # Mock S3 response
    manifest_data = {
        "chain_id": "chain1",
        "root_hash": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
        "tip_hash": "f1e2d3c4b5a6978012345678901234567890abcdef1234567890abcdef123456",
        "length": 3,
        "created_at": "2025-09-10T10:00:00Z",
        "last_event_id": "evt_003",
        "anchor_refs": []
    }
    
    mock_response = Mock()
    mock_response.__getitem__ = Mock(return_value=Mock())
    mock_response['Body'].read.return_value = json.dumps(manifest_data).encode('utf-8')
    mock_s3_client.get_object.return_value = mock_response
    
    manifest = s3_storage.read_manifest('chain1')
    
    assert isinstance(manifest, AuditManifest)
    assert manifest.chain_id == "chain1"
    assert manifest.length == 3
    
    mock_s3_client.get_object.assert_called_once_with(
        Bucket='test-bucket',
        Key='test-prefix/chains/chain1/MANIFEST.json'
    )


def test_s3_write_manifest(s3_storage, mock_s3_client):
    """Test writing a manifest to S3."""
    manifest = AuditManifest(
        chain_id="chain1",
        root_hash="a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
        tip_hash="f1e2d3c4b5a6978012345678901234567890abcdef1234567890abcdef123456",
        length=3,
        created_at=datetime.now(timezone.utc),
        last_event_id="evt_003",
        anchor_refs=[]
    )
    
    s3_storage.write_manifest('chain1', manifest)
    
    mock_s3_client.put_object.assert_called_once()
    call_args = mock_s3_client.put_object.call_args
    assert call_args[1]['Bucket'] == 'test-bucket'
    assert call_args[1]['Key'] == 'test-prefix/chains/chain1/MANIFEST.json'
    assert call_args[1]['ContentType'] == 'application/json'


def test_s3_list_anchors(s3_storage, mock_s3_client):
    """Test listing anchor files from S3."""
    # Mock S3 response
    mock_s3_client.list_objects_v2.return_value = {
        'Contents': [
            {'Key': 'test-prefix/anchors/2025/09/10/chain1_root.json'},
            {'Key': 'test-prefix/anchors/2025/09/10/chain2_root.json'},
            {'Key': 'test-prefix/anchors/2025/09/11/chain1_root.json'}
        ]
    }
    
    anchors = s3_storage.list_anchors()
    
    assert anchors == [
        '2025/09/10/chain1_root.json',
        '2025/09/10/chain2_root.json',
        '2025/09/11/chain1_root.json'
    ]


def test_s3_list_anchors_with_chain_filter(s3_storage, mock_s3_client):
    """Test listing anchor files filtered by chain ID."""
    # Mock S3 response
    mock_s3_client.list_objects_v2.return_value = {
        'Contents': [
            {'Key': 'test-prefix/anchors/2025/09/10/chain1_root.json'},
            {'Key': 'test-prefix/anchors/2025/09/10/chain2_root.json'},
            {'Key': 'test-prefix/anchors/2025/09/11/chain1_root.json'}
        ]
    }
    
    anchors = s3_storage.list_anchors('chain1')
    
    assert anchors == [
        '2025/09/10/chain1_root.json',
        '2025/09/11/chain1_root.json'
    ]


def test_s3_read_anchor(s3_storage, mock_s3_client):
    """Test reading an anchor file from S3."""
    # Mock S3 response
    anchor_data = {
        "chain_id": "chain1",
        "root_hash": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
        "anchored_at": "2025-09-10T10:00:00Z",
        "anchor_type": "git",
        "anchor_ref": "commit_abc123",
        "metadata": {}
    }
    
    mock_response = Mock()
    mock_response.__getitem__ = Mock(return_value=Mock())
    mock_response['Body'].read.return_value = json.dumps(anchor_data).encode('utf-8')
    mock_s3_client.get_object.return_value = mock_response
    
    anchor = s3_storage.read_anchor('2025/09/10/chain1_root.json')
    
    assert isinstance(anchor, AuditAnchor)
    assert anchor.chain_id == "chain1"
    assert anchor.anchor_type == "git"
    
    mock_s3_client.get_object.assert_called_once_with(
        Bucket='test-bucket',
        Key='test-prefix/anchors/2025/09/10/chain1_root.json'
    )


def test_s3_error_handling(s3_storage, mock_s3_client):
    """Test S3 error handling."""
    # Mock S3 error
    mock_s3_client.list_objects_v2.side_effect = Exception("S3 error")
    
    with pytest.raises(RuntimeError, match="Failed to list chains"):
        s3_storage.list_chains()


def test_s3_get_key_method(s3_storage):
    """Test S3 key generation."""
    # Test with prefix
    key = s3_storage._get_key("chains", "chain1", "000001_event.json")
    assert key == "test-prefix/chains/chain1/000001_event.json"
    
    # Test without prefix
    storage_no_prefix = S3Storage("test-bucket", "", "us-east-1")
    key = storage_no_prefix._get_key("chains", "chain1", "000001_event.json")
    assert key == "chains/chain1/000001_event.json"


def test_s3_create_storage_with_env_vars():
    """Test S3Storage creation with environment variables."""
    with patch.dict('os.environ', {
        'IOA_AUDIT_S3_BUCKET': 'env-bucket',
        'IOA_AUDIT_S3_PREFIX': 'env-prefix',
        'AWS_REGION': 'us-west-2'
    }):
        with patch('boto3.client'):
            storage = S3Storage('env-bucket', 'env-prefix', 'us-west-2')
            assert storage.bucket == 'env-bucket'
            assert storage.prefix == 'env-prefix'
            assert storage.region == 'us-west-2'


def test_s3_create_storage_without_bucket():
    """Test S3Storage creation without bucket raises error."""
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(TypeError):
            S3Storage()
