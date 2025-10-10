""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
Test audit chain verification for hash mismatches.

Tests the system's ability to detect when entry hashes don't match
their computed values, indicating content tampering.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timezone

from src.audit.verify import AuditVerifier
from src.audit.storage import FileSystemStorage
from src.audit.models import AuditManifest
from src.audit.canonical import compute_hash


@pytest.fixture
def temp_audit_dir():
    """Create temporary audit directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def tampered_chain(temp_audit_dir):
    """Create an audit chain with tampered content."""
    storage = FileSystemStorage(temp_audit_dir)
    
    # Create chain directory
    chain_dir = temp_audit_dir / "chains" / "tampered_chain"
    chain_dir.mkdir(parents=True)
    
    # Create entries with tampered content
    entries = []
    prev_hash = "0" * 64
    
    for i in range(3):
        entry_data = {
            "event_id": f"evt_{i+1:03d}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prev_hash": prev_hash,
            "hash": "",  # Will be computed
            "payload": {
                "event_type": f"test_event_{i+1}",
                "data": f"test_data_{i+1}"
            },
            "writer": "test_service"
        }
        
        # Compute correct hash (exclude the hash field itself)
        entry_data_for_hash = entry_data.copy()
        entry_data_for_hash.pop('hash', None)
        correct_hash = compute_hash(entry_data_for_hash)
        
        # Tamper with the hash on the second entry
        if i == 1:
            entry_data["hash"] = "1" * 64  # Wrong hash
        else:
            entry_data["hash"] = correct_hash
        
        prev_hash = correct_hash  # Use correct hash for chain continuity
        
        # Write entry file
        entry_file = chain_dir / f"{i+1:06d}_test_event.json"
        with entry_file.open('w') as f:
            json.dump(entry_data, f, indent=2)
        
        entries.append(entry_data)
    
    # Create manifest
    manifest = AuditManifest(
        chain_id="tampered_chain",
        root_hash=entries[0]["hash"],
        tip_hash=entries[-1]["hash"],
        length=len(entries),
        created_at=datetime.now(timezone.utc),
        last_event_id=entries[-1]["event_id"],
        anchor_refs=[]
    )
    
    storage.write_manifest("tampered_chain", manifest)
    
    return storage, "tampered_chain", entries


def test_verify_chain_with_hash_mismatch(tampered_chain):
    """Test verification detects hash mismatch."""
    storage, chain_id, entries = tampered_chain
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id)
    
    assert result.ok is False
    assert len(result.breaks) > 0
    
    # Check that the hash mismatch is detected
    hash_breaks = [b for b in result.breaks if b["issue_type"] == "hash_mismatch"]
    assert len(hash_breaks) > 0
    
    # Check break details
    break_info = hash_breaks[0]
    assert break_info["entry_index"] == 1  # Second entry (0-indexed)
    assert "entry_hash" in break_info["details"]
    assert "computed_hash" in break_info["details"]


def test_verify_chain_with_hash_mismatch_no_fail_fast(tampered_chain):
    """Test verification with fail-fast disabled finds all hash mismatches."""
    storage, chain_id, entries = tampered_chain
    
    verifier = AuditVerifier(storage=storage, fail_fast=False)
    result = verifier.verify_chain(chain_id)
    
    assert result.ok is False
    assert len(result.breaks) > 0
    
    # Should find the hash mismatch
    hash_breaks = [b for b in result.breaks if b["issue_type"] == "hash_mismatch"]
    assert len(hash_breaks) > 0


def test_verify_chain_with_tampered_payload(temp_audit_dir):
    """Test verification with tampered payload content."""
    storage = FileSystemStorage(temp_audit_dir)
    
    # Create chain directory
    chain_dir = temp_audit_dir / "chains" / "tampered_payload"
    chain_dir.mkdir(parents=True)
    
    # Create entry with tampered payload
    entry_data = {
        "event_id": "evt_001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prev_hash": "0" * 64,
        "hash": "",
        "payload": {
            "event_type": "test_event",
            "data": "original_data"
        },
        "writer": "test_service"
    }
    
    # Compute correct hash (exclude the hash field itself)
    entry_data_for_hash = entry_data.copy()
    entry_data_for_hash.pop('hash', None)
    correct_hash = compute_hash(entry_data_for_hash)
    entry_data["hash"] = correct_hash
    
    # Write entry file
    entry_file = chain_dir / "000001_test_event.json"
    with entry_file.open('w') as f:
        json.dump(entry_data, f, indent=2)
    
    # Tamper with the file content
    with entry_file.open('r') as f:
        content = f.read()
    
    # Replace original data with tampered data
    tampered_content = content.replace("original_data", "tampered_data")
    
    with entry_file.open('w') as f:
        f.write(tampered_content)
    
    # Create manifest
    manifest = AuditManifest(
        chain_id="tampered_payload",
        root_hash=correct_hash,
        tip_hash=correct_hash,
        length=1,
        created_at=datetime.now(timezone.utc),
        last_event_id=entry_data["event_id"],
        anchor_refs=[]
    )
    
    storage.write_manifest("tampered_payload", manifest)
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain("tampered_payload")
    
    # Should fail due to hash mismatch
    assert result.ok is False
    assert len(result.breaks) > 0
    
    # Check that the hash mismatch is detected
    hash_breaks = [b for b in result.breaks if b["issue_type"] == "hash_mismatch"]
    assert len(hash_breaks) > 0


def test_verify_chain_with_tampered_timestamp(temp_audit_dir):
    """Test verification with tampered timestamp."""
    storage = FileSystemStorage(temp_audit_dir)
    
    # Create chain directory
    chain_dir = temp_audit_dir / "chains" / "tampered_timestamp"
    chain_dir.mkdir(parents=True)
    
    # Create entry with tampered timestamp
    entry_data = {
        "event_id": "evt_001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prev_hash": "0" * 64,
        "hash": "",
        "payload": {
            "event_type": "test_event",
            "data": "test_data"
        },
        "writer": "test_service"
    }
    
    # Compute correct hash (exclude the hash field itself)
    entry_data_for_hash = entry_data.copy()
    entry_data_for_hash.pop('hash', None)
    correct_hash = compute_hash(entry_data_for_hash)
    entry_data["hash"] = correct_hash
    
    # Write entry file
    entry_file = chain_dir / "000001_test_event.json"
    with entry_file.open('w') as f:
        json.dump(entry_data, f, indent=2)
    
    # Tamper with the timestamp in the file
    with entry_file.open('r') as f:
        content = f.read()
    
    # Replace timestamp with different value
    original_timestamp = entry_data["timestamp"]
    tampered_timestamp = "2025-01-01T00:00:00Z"
    tampered_content = content.replace(original_timestamp, tampered_timestamp)
    
    with entry_file.open('w') as f:
        f.write(tampered_content)
    
    # Create manifest
    manifest = AuditManifest(
        chain_id="tampered_timestamp",
        root_hash=correct_hash,
        tip_hash=correct_hash,
        length=1,
        created_at=datetime.now(timezone.utc),
        last_event_id=entry_data["event_id"],
        anchor_refs=[]
    )
    
    storage.write_manifest("tampered_timestamp", manifest)
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain("tampered_timestamp")
    
    # Should fail due to hash mismatch
    assert result.ok is False
    assert len(result.breaks) > 0
    
    # Check that the hash mismatch is detected
    hash_breaks = [b for b in result.breaks if b["issue_type"] == "hash_mismatch"]
    assert len(hash_breaks) > 0


def test_verify_chain_with_invalid_hash_format(temp_audit_dir):
    """Test verification with invalid hash format."""
    storage = FileSystemStorage(temp_audit_dir)
    
    # Create chain directory
    chain_dir = temp_audit_dir / "chains" / "invalid_hash_format"
    chain_dir.mkdir(parents=True)
    
    # Create entry with invalid hash format
    entry_data = {
        "event_id": "evt_001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prev_hash": "0" * 64,
        "hash": "invalid_hash",  # Invalid format
        "payload": {
            "event_type": "test_event",
            "data": "test_data"
        },
        "writer": "test_service"
    }
    
    # Write entry file
    entry_file = chain_dir / "000001_test_event.json"
    with entry_file.open('w') as f:
        json.dump(entry_data, f, indent=2)
    
    # Create manifest with valid hash format (the entry will have invalid hash)
    manifest = AuditManifest(
        chain_id="invalid_hash_format",
        root_hash="0" * 64,  # Valid hash format
        tip_hash="0" * 64,   # Valid hash format
        length=1,
        created_at=datetime.now(timezone.utc),
        last_event_id=entry_data["event_id"],
        anchor_refs=[]
    )
    
    storage.write_manifest("invalid_hash_format", manifest)
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain("invalid_hash_format")
    
    # Should fail due to invalid hash format
    assert result.ok is False
    assert len(result.breaks) > 0


def test_verify_chain_with_corrupted_json(temp_audit_dir):
    """Test verification with corrupted JSON file."""
    storage = FileSystemStorage(temp_audit_dir)
    
    # Create chain directory
    chain_dir = temp_audit_dir / "chains" / "corrupted_json"
    chain_dir.mkdir(parents=True)
    
    # Create corrupted JSON file
    entry_file = chain_dir / "000001_test_event.json"
    with entry_file.open('w') as f:
        f.write('{"corrupted": json file}')  # Invalid JSON
    
    # Create manifest
    manifest = AuditManifest(
        chain_id="corrupted_json",
        root_hash="0" * 64,
        tip_hash="0" * 64,
        length=1,
        created_at=datetime.now(timezone.utc),
        last_event_id="evt_001",
        anchor_refs=[]
    )
    
    storage.write_manifest("corrupted_json", manifest)
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain("corrupted_json")
    
    # Should fail due to corrupted JSON
    assert result.ok is False
    assert len(result.breaks) > 0
    
    # Check that the read error is detected
    read_errors = [b for b in result.breaks if b["issue_type"] == "read_error"]
    assert len(read_errors) > 0
