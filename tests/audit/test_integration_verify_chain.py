""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
Integration tests for audit chain verification.

Tests the complete verification workflow including CLI integration,
file system operations, and end-to-end verification scenarios.
"""

import pytest
import tempfile
import json
import subprocess
import sys
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
def sample_chain_with_manifest(temp_audit_dir):
    """Create a complete sample audit chain with manifest."""
    storage = FileSystemStorage(temp_audit_dir)
    
    # Create chain directory
    chain_dir = temp_audit_dir / "chains" / "integration_test"
    chain_dir.mkdir(parents=True)
    
    # Create sample entries
    entries = []
    prev_hash = "0" * 64
    
    for i in range(5):
        entry_data = {
            "event_id": f"evt_{i+1:03d}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prev_hash": prev_hash,
            "hash": "",
            "payload": {
                "event_type": f"integration_test_{i+1}",
                "data": f"test_data_{i+1}",
                "sequence": i + 1
            },
            "writer": "integration_test_service"
        }
        
        # Compute hash (exclude the hash field itself)
        entry_data_for_hash = entry_data.copy()
        entry_data_for_hash.pop('hash', None)
        entry_data["hash"] = compute_hash(entry_data_for_hash)
        prev_hash = entry_data["hash"]
        
        # Write entry file
        entry_file = chain_dir / f"{i+1:06d}_integration_test.json"
        with entry_file.open('w') as f:
            json.dump(entry_data, f, indent=2)
        
        entries.append(entry_data)
    
    # Create manifest
    manifest = AuditManifest(
        chain_id="integration_test",
        root_hash=entries[0]["hash"],
        tip_hash=entries[-1]["hash"],
        length=len(entries),
        created_at=datetime.now(timezone.utc),
        last_event_id=entries[-1]["event_id"],
        anchor_refs=[]
    )
    
    storage.write_manifest("integration_test", manifest)
    
    return storage, "integration_test", entries, manifest


def test_integration_verify_complete_chain(sample_chain_with_manifest):
    """Test complete verification of a valid audit chain."""
    storage, chain_id, entries, manifest = sample_chain_with_manifest
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id)
    
    # Should pass verification
    assert result.ok is True
    assert result.chain_id == chain_id
    assert result.length == len(entries)
    assert result.root_hash == manifest.root_hash
    assert result.tip_hash == manifest.tip_hash
    assert len(result.breaks) == 0
    
    # Should have performance metrics
    assert "verification_time_seconds" in result.performance
    assert "entries_per_second" in result.performance
    assert result.performance["verification_time_seconds"] > 0
    assert result.performance["entries_per_second"] > 0
    
    # Should have coverage info
    assert "total_entries" in result.coverage
    assert "verified_entries" in result.coverage
    assert result.coverage["total_entries"] == len(entries)
    assert result.coverage["verified_entries"] == len(entries)


def test_integration_verify_with_anchor(sample_chain_with_manifest, temp_audit_dir):
    """Test verification with anchor file."""
    storage, chain_id, entries, manifest = sample_chain_with_manifest
    
    # Create anchor file
    anchor_dir = temp_audit_dir / "anchors" / "2025" / "09" / "10"
    anchor_dir.mkdir(parents=True)
    
    anchor_data = {
        "chain_id": chain_id,
        "root_hash": manifest.root_hash,
        "anchored_at": datetime.now(timezone.utc).isoformat(),
        "anchor_type": "git",
        "anchor_ref": "commit_integration_test",
        "metadata": {
            "test": "integration"
        }
    }
    
    anchor_file = anchor_dir / f"{chain_id}_root.json"
    with anchor_file.open('w') as f:
        json.dump(anchor_data, f, indent=2)
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id, anchor_file=str(anchor_file))
    
    # Should pass verification
    assert result.ok is True
    assert len(result.breaks) == 0


def test_integration_verify_with_anchor_mismatch(sample_chain_with_manifest, temp_audit_dir):
    """Test verification with mismatched anchor file."""
    storage, chain_id, entries, manifest = sample_chain_with_manifest
    
    # Create anchor file with wrong root hash
    anchor_dir = temp_audit_dir / "anchors" / "2025" / "09" / "10"
    anchor_dir.mkdir(parents=True)
    
    anchor_data = {
        "chain_id": chain_id,
        "root_hash": "1" * 64,  # Wrong root hash
        "anchored_at": datetime.now(timezone.utc).isoformat(),
        "anchor_type": "git",
        "anchor_ref": "commit_integration_test",
        "metadata": {}
    }
    
    anchor_file = anchor_dir / f"{chain_id}_root.json"
    with anchor_file.open('w') as f:
        json.dump(anchor_data, f, indent=2)
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id, anchor_file=str(anchor_file))
    
    # Should fail verification
    assert result.ok is False
    assert len(result.breaks) > 0
    
    # Should have anchor mismatch break
    anchor_breaks = [b for b in result.breaks if b["issue_type"] == "anchor_mismatch"]
    assert len(anchor_breaks) > 0


def test_integration_verify_with_tampered_entry(sample_chain_with_manifest, temp_audit_dir):
    """Test verification with tampered entry."""
    storage, chain_id, entries, manifest = sample_chain_with_manifest
    
    # Tamper with an entry
    chain_dir = temp_audit_dir / "chains" / chain_id
    entry_file = chain_dir / "000003_integration_test.json"
    
    # Read and modify the entry
    with entry_file.open('r') as f:
        entry_data = json.load(f)
    
    # Tamper with the payload
    entry_data["payload"]["data"] = "tampered_data"
    
    # Write back the tampered entry
    with entry_file.open('w') as f:
        json.dump(entry_data, f, indent=2)
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id)
    
    # Should fail verification
    assert result.ok is False
    assert len(result.breaks) > 0
    
    # Should have hash mismatch break
    hash_breaks = [b for b in result.breaks if b["issue_type"] == "hash_mismatch"]
    assert len(hash_breaks) > 0


def test_integration_verify_with_broken_chain(sample_chain_with_manifest, temp_audit_dir):
    """Test verification with broken prev_hash chain."""
    storage, chain_id, entries, manifest = sample_chain_with_manifest
    
    # Break the chain by modifying prev_hash
    chain_dir = temp_audit_dir / "chains" / chain_id
    entry_file = chain_dir / "000003_integration_test.json"
    
    # Read and modify the entry
    with entry_file.open('r') as f:
        entry_data = json.load(f)
    
    # Break the prev_hash chain
    entry_data["prev_hash"] = "1" * 64  # Wrong prev_hash
    
    # Update the hash to match the new content
    entry_data_for_hash = entry_data.copy()
    entry_data_for_hash.pop('hash', None)
    entry_data["hash"] = compute_hash(entry_data_for_hash)
    
    # Write back the modified entry
    with entry_file.open('w') as f:
        json.dump(entry_data, f, indent=2)
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id)
    
    # Should fail verification
    assert result.ok is False
    assert len(result.breaks) > 0
    
    # Should have chain break
    chain_breaks = [b for b in result.breaks if b["issue_type"] == "chain_break"]
    assert len(chain_breaks) > 0


def test_integration_verify_with_manifest_mismatch(sample_chain_with_manifest, temp_audit_dir):
    """Test verification with manifest length mismatch."""
    storage, chain_id, entries, manifest = sample_chain_with_manifest
    
    # Create manifest with wrong length
    wrong_manifest = AuditManifest(
        chain_id=chain_id,
        root_hash=manifest.root_hash,
        tip_hash=manifest.tip_hash,
        length=10,  # Wrong length (should be 5)
        created_at=manifest.created_at,
        last_event_id=manifest.last_event_id,
        anchor_refs=manifest.anchor_refs
    )
    
    storage.write_manifest(chain_id, wrong_manifest)
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id)
    
    # Should fail verification
    assert result.ok is False
    assert len(result.breaks) > 0
    
    # Should have length mismatch break
    length_breaks = [b for b in result.breaks if b["issue_type"] == "length_mismatch"]
    assert len(length_breaks) > 0


def test_integration_verify_with_fail_fast_disabled(sample_chain_with_manifest, temp_audit_dir):
    """Test verification with fail-fast disabled finds all issues."""
    storage, chain_id, entries, manifest = sample_chain_with_manifest
    
    # Create multiple issues
    chain_dir = temp_audit_dir / "chains" / chain_id
    
    # Tamper with entry 2
    entry_file_2 = chain_dir / "000002_integration_test.json"
    with entry_file_2.open('r') as f:
        entry_data = json.load(f)
    entry_data["payload"]["data"] = "tampered_data_2"
    with entry_file_2.open('w') as f:
        json.dump(entry_data, f, indent=2)
    
    # Tamper with entry 4
    entry_file_4 = chain_dir / "000004_integration_test.json"
    with entry_file_4.open('r') as f:
        entry_data = json.load(f)
    entry_data["payload"]["data"] = "tampered_data_4"
    with entry_file_4.open('w') as f:
        json.dump(entry_data, f, indent=2)
    
    verifier = AuditVerifier(storage=storage, fail_fast=False)
    result = verifier.verify_chain(chain_id)
    
    # Should fail verification
    assert result.ok is False
    assert len(result.breaks) > 0
    
    # Should find multiple hash mismatches
    hash_breaks = [b for b in result.breaks if b["issue_type"] == "hash_mismatch"]
    assert len(hash_breaks) >= 2


def test_integration_verify_from_path(sample_chain_with_manifest, temp_audit_dir):
    """Test verification from file path."""
    storage, chain_id, entries, manifest = sample_chain_with_manifest
    
    verifier = AuditVerifier()
    result = verifier.verify_chain_from_path(temp_audit_dir / "chains" / chain_id)
    
    # Should pass verification
    assert result.ok is True
    assert result.chain_id == chain_id
    assert result.length == len(entries)


def test_integration_verify_with_filters(sample_chain_with_manifest):
    """Test verification with entry filters."""
    storage, chain_id, entries, manifest = sample_chain_with_manifest
    
    verifier = AuditVerifier(storage=storage)
    
    # Test with start_after filter
    result = verifier.verify_chain(chain_id, start_after="evt_002")
    assert result.ok is True
    
    # Test with since filter
    result = verifier.verify_chain(chain_id, since="2025-09-09")
    assert result.ok is True


def test_integration_verify_with_strict_mode(sample_chain_with_manifest):
    """Test verification in strict mode."""
    storage, chain_id, entries, manifest = sample_chain_with_manifest
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id, strict=True)
    
    # Should pass verification
    assert result.ok is True
    assert len(result.breaks) == 0


def test_integration_verify_with_ignore_signatures(sample_chain_with_manifest):
    """Test verification with signature checking disabled."""
    storage, chain_id, entries, manifest = sample_chain_with_manifest
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id, ignore_signatures=True)
    
    # Should pass verification
    assert result.ok is True
    assert len(result.breaks) == 0


def test_integration_verify_performance_metrics(sample_chain_with_manifest):
    """Test that performance metrics are accurate."""
    storage, chain_id, entries, manifest = sample_chain_with_manifest
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id)
    
    # Should have reasonable performance metrics
    assert result.performance["verification_time_seconds"] > 0
    assert result.performance["entries_per_second"] > 0
    assert result.performance["fail_fast"] is True
    
    # Should verify all entries
    assert result.coverage["total_entries"] == len(entries)
    assert result.coverage["verified_entries"] == len(entries)


def test_integration_verify_error_handling(temp_audit_dir):
    """Test error handling in verification."""
    storage = FileSystemStorage(temp_audit_dir)
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain("nonexistent_chain")
    
    # Should fail gracefully
    assert result.ok is False
    assert len(result.breaks) > 0
    
    # Should have verification error
    error_breaks = [b for b in result.breaks if b["issue_type"] == "verification_error"]
    assert len(error_breaks) > 0


def test_integration_verify_json_output(sample_chain_with_manifest, temp_audit_dir):
    """Test JSON output format."""
    storage, chain_id, entries, manifest = sample_chain_with_manifest
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id)
    
    # Convert to dict for JSON serialization
    result_dict = result.model_dump()
    
    # Should be JSON serializable
    json_str = json.dumps(result_dict, default=str)
    parsed_result = json.loads(json_str)
    
    # Should have expected structure
    assert parsed_result["ok"] is True
    assert parsed_result["chain_id"] == chain_id
    assert parsed_result["length"] == len(entries)
    assert "performance" in parsed_result
    assert "coverage" in parsed_result
    assert "breaks" in parsed_result
