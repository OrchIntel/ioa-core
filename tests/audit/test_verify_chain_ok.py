""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
Test audit chain verification for successful cases.

Tests the core verification functionality with valid audit chains
to ensure the system correctly identifies intact chains.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timezone


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

from src.audit.verify import AuditVerifier
from src.audit.storage import FileSystemStorage
from src.audit.models import AuditEntry, AuditManifest
from src.audit.canonical import compute_hash


@pytest.fixture
def temp_audit_dir():
    """Create temporary audit directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_chain(temp_audit_dir):
    """Create a sample audit chain for testing."""
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
            "hash": "",  # Will be computed
            "payload": {
                "event_type": f"test_event_{i+1}",
                "data": f"test_data_{i+1}"
            },
            "writer": "test_service"
        }
        
        # Compute hash on data without hash field
        hash_data = entry_data.copy()
        hash_data.pop('hash', None)
        entry_data["hash"] = compute_hash(hash_data)
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
    
    return storage, "test_chain", entries


def test_verify_intact_chain(sample_chain):
    """Test verification of an intact audit chain."""
    storage, chain_id, entries = sample_chain
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id)
    
    assert result.ok is True
    assert result.chain_id == chain_id
    assert result.length == len(entries)
    assert result.root_hash == entries[0]["hash"]
    assert result.tip_hash == entries[-1]["hash"]
    assert len(result.breaks) == 0


def test_verify_chain_with_anchor(sample_chain, temp_audit_dir):
    """Test verification with anchor file."""
    storage, chain_id, entries = sample_chain
    
    # Create anchor file
    anchor_dir = temp_audit_dir / "anchors" / "2025" / "09" / "10"
    anchor_dir.mkdir(parents=True)
    
    anchor_data = {
        "chain_id": chain_id,
        "root_hash": entries[0]["hash"],
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


def test_verify_chain_performance_metrics(sample_chain):
    """Test that performance metrics are recorded."""
    storage, chain_id, entries = sample_chain
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id)
    
    assert result.ok is True
    assert "verification_time_seconds" in result.performance
    assert "entries_per_second" in result.performance
    assert result.performance["verification_time_seconds"] > 0
    assert result.performance["entries_per_second"] > 0


def test_verify_chain_coverage_info(sample_chain):
    """Test that coverage information is recorded."""
    storage, chain_id, entries = sample_chain
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id)
    
    assert result.ok is True
    assert "total_entries" in result.coverage
    assert "verified_entries" in result.coverage
    assert result.coverage["total_entries"] == len(entries)
    assert result.coverage["verified_entries"] == len(entries)


def test_verify_chain_ignore_signatures(sample_chain):
    """Test verification with signature checking disabled."""
    storage, chain_id, entries = sample_chain
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id, ignore_signatures=True)
    
    assert result.ok is True
    assert len(result.breaks) == 0


def test_verify_chain_strict_mode(sample_chain):
    """Test verification in strict mode."""
    storage, chain_id, entries = sample_chain
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain(chain_id, strict=True)
    
    assert result.ok is True
    assert len(result.breaks) == 0


def test_verify_chain_no_fail_fast(sample_chain):
    """Test verification with fail-fast disabled."""
    storage, chain_id, entries = sample_chain
    
    verifier = AuditVerifier(storage=storage, fail_fast=False)
    result = verifier.verify_chain(chain_id)
    
    assert result.ok is True
    assert len(result.breaks) == 0


def test_verify_chain_from_path(sample_chain, temp_audit_dir):
    """Test verification from file path."""
    storage, chain_id, entries = sample_chain
    
    verifier = AuditVerifier()
    result = verifier.verify_chain_from_path(temp_audit_dir / "chains" / chain_id)
    
    assert result.ok is True
    assert result.chain_id == chain_id
    assert result.length == len(entries)


def test_verify_empty_chain(temp_audit_dir):
    """Test verification of empty chain."""
    storage = FileSystemStorage(temp_audit_dir)
    
    # Create empty chain directory
    chain_dir = temp_audit_dir / "chains" / "empty_chain"
    chain_dir.mkdir(parents=True)
    
    # Create empty manifest
    manifest = AuditManifest(
        chain_id="empty_chain",
        root_hash="0" * 64,
        tip_hash="0" * 64,
        length=0,
        created_at=datetime.now(timezone.utc),
        last_event_id="",
        anchor_refs=[]
    )
    
    storage.write_manifest("empty_chain", manifest)
    
    verifier = AuditVerifier(storage=storage)
    result = verifier.verify_chain("empty_chain")
    
    assert result.ok is False
    assert len(result.breaks) > 0
    assert any(break_info["issue_type"] == "empty_chain" for break_info in result.breaks)
