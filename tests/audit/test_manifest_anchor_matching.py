""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
Test audit chain verification with manifest and anchor matching.

Tests the system's ability to verify manifest integrity and
anchor file matching for complete chain validation.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timezone

from src.audit.verify import AuditVerifier
from src.audit.storage import FileSystemStorage
from src.audit.models import AuditManifest, AuditAnchor
from src.audit.canonical import compute_hash


@pytest.fixture
def temp_audit_dir():
    """Create temporary audit directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def chain_with_manifest(temp_audit_dir):
    """Create an audit chain with manifest."""
    storage = FileSystemStorage(temp_audit_dir)
    
    # Create chain directory
    chain_dir = temp_audit_dir / "chains" / "test_chain"
    chain_dir.mkdir(parents=True)
    
    # Create sample entries
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
        chain_id="test_chain",
        root_hash=entries[0]["hash"],
        tip_hash=entries[-1]["hash"],
        length=len(entries),
        created_at=datetime.now(timezone.utc),
        last_event_id=entries[-1]["event_id"],
        anchor_refs=[]
    )
    
    storage.write_manifest("test_chain", manifest)
    
    return storage, "test_chain", entries, manifest


def test_verify_manifest_matching(chain_with_manifest):
    """Test verification with correct manifest."""
    storage, chain_id, entries, manifest = chain_with_manifest
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id)
    
    assert result.ok is True
    assert result.root_hash == manifest.root_hash
    assert result.tip_hash == manifest.tip_hash
    assert result.length == manifest.length


def test_verify_manifest_length_mismatch(temp_audit_dir):
    """Test verification with manifest length mismatch."""
    storage = FileSystemStorage(temp_audit_dir)
    
    # Create chain directory
    chain_dir = temp_audit_dir / "chains" / "length_mismatch"
    chain_dir.mkdir(parents=True)
    
    # Create entries
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
    
    # Create manifest with wrong length
    manifest = AuditManifest(
        chain_id="length_mismatch",
        root_hash=entries[0]["hash"],
        tip_hash=entries[-1]["hash"],
        length=5,  # Wrong length (should be 3)
        created_at=datetime.now(timezone.utc),
        last_event_id=entries[-1]["event_id"],
        anchor_refs=[]
    )
    
    storage.write_manifest("length_mismatch", manifest)
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain("length_mismatch")
    
    assert result.ok is False
    assert len(result.breaks) > 0
    
    # Check that length mismatch is detected
    length_breaks = [b for b in result.breaks if b["issue_type"] == "length_mismatch"]
    assert len(length_breaks) > 0


def test_verify_manifest_root_hash_mismatch(temp_audit_dir):
    """Test verification with manifest root hash mismatch."""
    storage = FileSystemStorage(temp_audit_dir)
    
    # Create chain directory
    chain_dir = temp_audit_dir / "chains" / "root_hash_mismatch"
    chain_dir.mkdir(parents=True)
    
    # Create entries
    entries = []
    prev_hash = "0" * 64
    
    for i in range(2):
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
    
    # Create manifest with wrong root hash
    manifest = AuditManifest(
        chain_id="root_hash_mismatch",
        root_hash="1" * 64,  # Wrong root hash
        tip_hash=entries[-1]["hash"],
        length=len(entries),
        created_at=datetime.now(timezone.utc),
        last_event_id=entries[-1]["event_id"],
        anchor_refs=[]
    )
    
    storage.write_manifest("root_hash_mismatch", manifest)
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain("root_hash_mismatch")
    
    # Manifest root hash should be verified against entries; mismatch should fail
    assert result.ok is False
    hash_breaks = [b for b in result.breaks if b["issue_type"] == "hash_mismatch"]
    assert len(hash_breaks) > 0


def test_verify_anchor_matching(chain_with_manifest, temp_audit_dir):
    """Test verification with matching anchor file."""
    storage, chain_id, entries, manifest = chain_with_manifest
    
    # Create anchor file
    anchor_dir = temp_audit_dir / "anchors" / "2025" / "09" / "10"
    anchor_dir.mkdir(parents=True)
    
    anchor_data = {
        "chain_id": chain_id,
        "root_hash": manifest.root_hash,  # Matching root hash
        "anchored_at": datetime.now(timezone.utc).isoformat(),
        "anchor_type": "git",
        "anchor_ref": "commit_abc123",
        "metadata": {}
    }
    
    anchor_file = anchor_dir / f"{chain_id}_root.json"
    with anchor_file.open('w') as f:
        json.dump(anchor_data, f, indent=2)
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id, anchor_file=str(anchor_file))
    
    assert result.ok is True
    assert len(result.breaks) == 0


def test_verify_anchor_mismatch(chain_with_manifest, temp_audit_dir):
    """Test verification with mismatched anchor file."""
    storage, chain_id, entries, manifest = chain_with_manifest
    
    # Create anchor file with wrong root hash
    anchor_dir = temp_audit_dir / "anchors" / "2025" / "09" / "10"
    anchor_dir.mkdir(parents=True)
    
    anchor_data = {
        "chain_id": chain_id,
        "root_hash": "1" * 64,  # Wrong root hash
        "anchored_at": datetime.now(timezone.utc).isoformat(),
        "anchor_type": "git",
        "anchor_ref": "commit_abc123",
        "metadata": {}
    }
    
    anchor_file = anchor_dir / f"{chain_id}_root.json"
    with anchor_file.open('w') as f:
        json.dump(anchor_data, f, indent=2)
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id, anchor_file=str(anchor_file))
    
    assert result.ok is False
    assert len(result.breaks) > 0
    
    # Check that anchor mismatch is detected
    anchor_breaks = [b for b in result.breaks if b["issue_type"] == "anchor_mismatch"]
    assert len(anchor_breaks) > 0


def test_verify_missing_anchor_file(chain_with_manifest, temp_audit_dir):
    """Test verification with missing anchor file."""
    storage, chain_id, entries, manifest = chain_with_manifest
    
    # Create non-existent anchor file path
    anchor_file = temp_audit_dir / "anchors" / "missing_anchor.json"
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id, anchor_file=str(anchor_file))
    
    # Should pass verification (missing anchor file is not an error)
    assert result.ok is True


def test_verify_corrupted_anchor_file(chain_with_manifest, temp_audit_dir):
    """Test verification with corrupted anchor file."""
    storage, chain_id, entries, manifest = chain_with_manifest
    
    # Create corrupted anchor file
    anchor_dir = temp_audit_dir / "anchors" / "2025" / "09" / "10"
    anchor_dir.mkdir(parents=True)
    
    anchor_file = anchor_dir / f"{chain_id}_root.json"
    with anchor_file.open('w') as f:
        f.write('{"corrupted": json file}')  # Invalid JSON
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id, anchor_file=str(anchor_file))
    
    # Should pass verification (corrupted anchor file is not an error)
    assert result.ok is True


def test_verify_anchor_wrong_chain_id(chain_with_manifest, temp_audit_dir):
    """Test verification with anchor file for different chain."""
    storage, chain_id, entries, manifest = chain_with_manifest
    
    # Create anchor file for different chain
    anchor_dir = temp_audit_dir / "anchors" / "2025" / "09" / "10"
    anchor_dir.mkdir(parents=True)
    
    anchor_data = {
        "chain_id": "different_chain",  # Different chain ID
        "root_hash": manifest.root_hash,
        "anchored_at": datetime.now(timezone.utc).isoformat(),
        "anchor_type": "git",
        "anchor_ref": "commit_abc123",
        "metadata": {}
    }
    
    anchor_file = anchor_dir / f"different_chain_root.json"
    with anchor_file.open('w') as f:
        json.dump(anchor_data, f, indent=2)
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id, anchor_file=str(anchor_file))
    
    # Should pass verification (anchor chain ID mismatch is not checked)
    assert result.ok is True


def test_verify_manifest_missing_file(temp_audit_dir):
    """Test verification with missing manifest file."""
    storage = FileSystemStorage(temp_audit_dir)
    
    # Create chain directory without manifest
    chain_dir = temp_audit_dir / "chains" / "missing_manifest"
    chain_dir.mkdir(parents=True)
    
    # Create entry without manifest
    entry_data = {
        "event_id": "evt_001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prev_hash": "0" * 64,
        "hash": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
        "payload": {
            "event_type": "test_event",
            "data": "test_data"
        },
        "writer": "test_service"
    }
    
    entry_file = chain_dir / "000001_test_event.json"
    with entry_file.open('w') as f:
        json.dump(entry_data, f, indent=2)
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain("missing_manifest")
    
    # Should fail due to missing manifest
    assert result.ok is False
    assert len(result.breaks) > 0
