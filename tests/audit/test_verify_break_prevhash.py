""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
Test audit chain verification for prev_hash continuity breaks.

Tests the system's ability to detect when the prev_hash chain
is broken, indicating tampering or corruption.
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
def broken_chain(temp_audit_dir):
    """Create an audit chain with prev_hash break."""
    storage = FileSystemStorage(temp_audit_dir)
    
    # Create chain directory
    chain_dir = temp_audit_dir / "chains" / "broken_chain"
    chain_dir.mkdir(parents=True)
    
    # Create entries with broken prev_hash chain
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
        
        # Break the chain on the second entry
        if i == 1:
            entry_data["prev_hash"] = "1" * 64  # Wrong prev_hash
        
        # Compute hash (exclude the hash field itself)
        entry_data_for_hash = entry_data.copy()
        entry_data_for_hash.pop('hash', None)
        entry_data["hash"] = compute_hash(entry_data_for_hash)
        
        prev_hash = entry_data["hash"]
        
        # Write entry file
        entry_file = chain_dir / f"{i+1:06d}_test_event.json"
        with entry_file.open('w') as f:
            json.dump(entry_data, f, indent=2)
        
        entries.append(entry_data)
    
    # Create manifest
    manifest = AuditManifest(
        chain_id="broken_chain",
        root_hash=entries[0]["hash"],
        tip_hash=entries[-1]["hash"],
        length=len(entries),
        created_at=datetime.now(timezone.utc),
        last_event_id=entries[-1]["event_id"],
        anchor_refs=[]
    )
    
    storage.write_manifest("broken_chain", manifest)
    
    return storage, "broken_chain", entries


def test_verify_chain_with_prev_hash_break(broken_chain):
    """Test verification detects prev_hash break."""
    storage, chain_id, entries = broken_chain
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id)
    
    assert result.ok is False
    assert len(result.breaks) > 0
    
    # Check that the break is detected
    prev_hash_breaks = [b for b in result.breaks if b["issue_type"] == "chain_break"]
    assert len(prev_hash_breaks) > 0
    
    # Check break details
    break_info = prev_hash_breaks[0]
    assert break_info["entry_index"] == 1  # Second entry (0-indexed)
    assert "expected_prev_hash" in break_info["details"]
    assert "actual_prev_hash" in break_info["details"]


def test_verify_chain_with_prev_hash_break_no_fail_fast(broken_chain):
    """Test verification with fail-fast disabled finds all breaks."""
    storage, chain_id, entries = broken_chain
    
    verifier = AuditVerifier(storage=storage, fail_fast=False)
    result = verifier.verify_chain(chain_id)
    
    assert result.ok is False
    assert len(result.breaks) > 0
    
    # Should find the prev_hash break
    prev_hash_breaks = [b for b in result.breaks if b["issue_type"] == "chain_break"]
    assert len(prev_hash_breaks) > 0


def test_verify_chain_with_missing_prev_hash(temp_audit_dir):
    """Test verification with missing prev_hash."""
    storage = FileSystemStorage(temp_audit_dir)
    
    # Create chain directory
    chain_dir = temp_audit_dir / "chains" / "missing_prev_hash"
    chain_dir.mkdir(parents=True)
    
    # Create entry with missing prev_hash
    entry_data = {
        "event_id": "evt_001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prev_hash": None,  # Missing prev_hash
        "hash": "",
        "payload": {
            "event_type": "test_event",
            "data": "test_data"
        },
        "writer": "test_service"
    }
    
    # Compute hash (exclude the hash field itself)
    entry_data_for_hash = entry_data.copy()
    entry_data_for_hash.pop('hash', None)
    entry_data["hash"] = compute_hash(entry_data_for_hash)
    
    # Write entry file
    entry_file = chain_dir / "000001_test_event.json"
    with entry_file.open('w') as f:
        json.dump(entry_data, f, indent=2)
    
    # Create manifest
    manifest = AuditManifest(
        chain_id="missing_prev_hash",
        root_hash=entry_data["hash"],
        tip_hash=entry_data["hash"],
        length=1,
        created_at=datetime.now(timezone.utc),
        last_event_id=entry_data["event_id"],
        anchor_refs=[]
    )
    
    storage.write_manifest("missing_prev_hash", manifest)
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain("missing_prev_hash")
    
    # Should pass for first entry (prev_hash can be null)
    assert result.ok is True


def test_verify_chain_with_invalid_prev_hash_format(temp_audit_dir):
    """Test verification with invalid prev_hash format."""
    storage = FileSystemStorage(temp_audit_dir)
    
    # Create chain directory
    chain_dir = temp_audit_dir / "chains" / "invalid_prev_hash"
    chain_dir.mkdir(parents=True)
    
    # Create entry with invalid prev_hash format
    entry_data = {
        "event_id": "evt_001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prev_hash": "invalid_hash",  # Invalid format
        "hash": "",
        "payload": {
            "event_type": "test_event",
            "data": "test_data"
        },
        "writer": "test_service"
    }
    
    # Compute hash (exclude the hash field itself)
    entry_data_for_hash = entry_data.copy()
    entry_data_for_hash.pop('hash', None)
    entry_data["hash"] = compute_hash(entry_data_for_hash)
    
    # Write entry file
    entry_file = chain_dir / "000001_test_event.json"
    with entry_file.open('w') as f:
        json.dump(entry_data, f, indent=2)
    
    # Create manifest
    manifest = AuditManifest(
        chain_id="invalid_prev_hash",
        root_hash=entry_data["hash"],
        tip_hash=entry_data["hash"],
        length=1,
        created_at=datetime.now(timezone.utc),
        last_event_id=entry_data["event_id"],
        anchor_refs=[]
    )
    
    storage.write_manifest("invalid_prev_hash", manifest)
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain("invalid_prev_hash")
    
    # Should fail due to invalid hash format
    assert result.ok is False
    assert len(result.breaks) > 0


def test_verify_chain_with_circular_prev_hash(temp_audit_dir):
    """Test verification with circular prev_hash reference."""
    storage = FileSystemStorage(temp_audit_dir)
    
    # Create chain directory
    chain_dir = temp_audit_dir / "chains" / "circular_prev_hash"
    chain_dir.mkdir(parents=True)
    
    # Create entries with circular prev_hash
    entries = []
    prev_hash = "0" * 64
    
    for i in range(3):
        entry_data = {
            "event_id": f"evt_{i+1:03d}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prev_hash": prev_hash,
            "hash": "",
            "payload": {
                "event_type": f"test_event_{i+1}",
                "data": f"test_data_{i+1}"
            },
            "writer": "test_service"
        }
        
        # Create circular reference on last entry
        if i == 2:
            entry_data["prev_hash"] = entries[0]["hash"]  # Points to first entry
        
        # Compute hash (exclude the hash field itself)
        entry_data_for_hash = entry_data.copy()
        entry_data_for_hash.pop('hash', None)
        entry_data["hash"] = compute_hash(entry_data_for_hash)
        
        prev_hash = entry_data["hash"]
        
        # Write entry file
        entry_file = chain_dir / f"{i+1:06d}_test_event.json"
        with entry_file.open('w') as f:
            json.dump(entry_data, f, indent=2)
        
        entries.append(entry_data)
    
    # Create manifest
    manifest = AuditManifest(
        chain_id="circular_prev_hash",
        root_hash=entries[0]["hash"],
        tip_hash=entries[-1]["hash"],
        length=len(entries),
        created_at=datetime.now(timezone.utc),
        last_event_id=entries[-1]["event_id"],
        anchor_refs=[]
    )
    
    storage.write_manifest("circular_prev_hash", manifest)
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain("circular_prev_hash")
    
    # Should fail due to circular reference
    assert result.ok is False
    assert len(result.breaks) > 0
    
    # Check that the circular reference is detected
    chain_breaks = [b for b in result.breaks if b["issue_type"] == "chain_break"]
    assert len(chain_breaks) > 0
