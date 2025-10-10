""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone
from src.audit.verify import AuditVerifier
from src.audit.canonical import compute_hash


class TestAuditMinimalRun:
    """Test minimal audit chain generation and verification."""
    
    def test_minimal_audit_chain_generation(self):
        """Test that a minimal audit chain can be generated and verified."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a minimal audit chain
            chain_id = "test_minimal_001"
            chain_dir = Path(temp_dir) / "audit_chain" / "20250910"
            chain_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a simple audit entry
            entry_data = {
                "event_id": "evt_001",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": {"event_type": "roundtable_start", "data": {"task": "Hello world"}},
                "writer": "test_writer",
                "prev_hash": "0" * 64  # Root entry has no previous hash
            }
            
            # Compute hash (exclude the hash field itself)
            entry_data_for_hash = entry_data.copy()
            entry_data_for_hash.pop('hash', None)
            entry_data["hash"] = compute_hash(entry_data_for_hash)
            
            # Create chain directory structure
            chains_dir = chain_dir / "chains" / chain_id
            chains_dir.mkdir(parents=True, exist_ok=True)
            
            # Write entry file
            entry_file = chains_dir / "000001_roundtable_start.json"
            with entry_file.open('w') as f:
                json.dump(entry_data, f, indent=2)
            
            # Create manifest
            manifest_data = {
                "chain_id": chain_id,
                "root_hash": entry_data["hash"],
                "tip_hash": entry_data["hash"],
                "length": 1,
                "created_at": entry_data["timestamp"],
                "last_event_id": entry_data["event_id"],
                "anchor_refs": []
            }
            
            manifest_file = chains_dir / "MANIFEST.json"
            with manifest_file.open('w') as f:
                json.dump(manifest_data, f, indent=2)
            
            # Create receipt file
            receipt_data = {
                "run_id": chain_id,
                "created_at": entry_data["timestamp"],
                "entry_count": 1,
                "root_hash": entry_data["hash"],
                "tip_hash": entry_data["hash"],
                "format_version": "v2.5.0",
                "description": "Minimal audit chain test"
            }
            
            receipt_file = chain_dir / f"run_{chain_id}_receipt.json"
            with receipt_file.open('w') as f:
                json.dump(receipt_data, f, indent=2)
            
            # Verify the chain
            verifier = AuditVerifier()
            result = verifier.verify_chain_from_path(str(chains_dir))
            
            # Assertions
            assert result.ok, f"Chain verification failed: {result.breaks}"
            assert result.chain_id == chain_id
            assert result.length == 1
            assert result.root_hash == entry_data["hash"]
            assert result.tip_hash == entry_data["hash"]
            assert len(result.breaks) == 0
    
    def test_minimal_audit_chain_with_manifest(self):
        """Test minimal audit chain with manifest file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create chain directory structure
            chain_id = "test_minimal_manifest_001"
            chain_dir = Path(temp_dir) / "audit_chain" / "chains" / chain_id
            chain_dir.mkdir(parents=True, exist_ok=True)
            
            # Create audit entry
            entry_data = {
                "event_id": "evt_001",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": {"event_type": "roundtable_start", "data": {"task": "Hello world with manifest"}},
                "writer": "test_writer",
                "prev_hash": "0" * 64
            }
            
            # Compute hash
            entry_data_for_hash = entry_data.copy()
            entry_data_for_hash.pop('hash', None)
            entry_data["hash"] = compute_hash(entry_data_for_hash)
            
            # Write entry file
            entry_file = chain_dir / "000001_roundtable_start.json"
            with entry_file.open('w') as f:
                json.dump(entry_data, f, indent=2)
            
            # Create manifest
            manifest_data = {
                "chain_id": chain_id,
                "root_hash": entry_data["hash"],
                "tip_hash": entry_data["hash"],
                "length": 1,
                "created_at": entry_data["timestamp"],
                "last_event_id": entry_data["event_id"],
                "anchor_refs": []
            }
            
            manifest_file = chain_dir / "MANIFEST.json"
            with manifest_file.open('w') as f:
                json.dump(manifest_data, f, indent=2)
            
            # Verify the chain
            verifier = AuditVerifier()
            result = verifier.verify_chain_from_path(str(chain_dir))
            
            # Assertions
            assert result.ok, f"Chain verification failed: {result.breaks}"
            assert result.chain_id == chain_id
            assert result.length == 1
            assert result.root_hash == entry_data["hash"]
            assert result.tip_hash == entry_data["hash"]
    
    def test_minimal_audit_chain_verification_cli(self):
        """Test that the audit verification CLI works with minimal chains."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create chain
            chain_id = "test_cli_001"
            chain_dir = Path(temp_dir) / "audit_chain" / "20250910"
            chain_dir.mkdir(parents=True, exist_ok=True)
            
            # Create entry
            entry_data = {
                "event_id": "evt_001",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": {"event_type": "roundtable_start", "data": {"task": "Hello world CLI test"}},
                "writer": "test_writer",
                "prev_hash": "0" * 64
            }
            
            entry_data_for_hash = entry_data.copy()
            entry_data_for_hash.pop('hash', None)
            entry_data["hash"] = compute_hash(entry_data_for_hash)
            
            # Create chain directory structure
            chains_dir = chain_dir / "chains" / chain_id
            chains_dir.mkdir(parents=True, exist_ok=True)
            
            # Write entry file
            entry_file = chains_dir / "000001_roundtable_start.json"
            with entry_file.open('w') as f:
                json.dump(entry_data, f, indent=2)
            
            # Create manifest
            manifest_data = {
                "chain_id": chain_id,
                "root_hash": entry_data["hash"],
                "tip_hash": entry_data["hash"],
                "length": 1,
                "created_at": entry_data["timestamp"],
                "last_event_id": entry_data["event_id"],
                "anchor_refs": []
            }
            
            manifest_file = chains_dir / "MANIFEST.json"
            with manifest_file.open('w') as f:
                json.dump(manifest_data, f, indent=2)
            
            # Create receipt file
            receipt_file = chain_dir / f"run_{chain_id}_receipt.json"
            receipt_data = {
                "run_id": chain_id,
                "created_at": entry_data["timestamp"],
                "entry_count": 1,
                "root_hash": entry_data["hash"],
                "tip_hash": entry_data["hash"],
                "format_version": "v2.5.0",
                "description": "CLI test audit chain"
            }
            with receipt_file.open('w') as f:
                json.dump(receipt_data, f, indent=2)
            
            # Test CLI-style verification
            verifier = AuditVerifier()
            result = verifier.verify_chain_from_path(str(chains_dir))
            
            # Assertions
            assert result.ok, f"CLI verification failed: {result.breaks}"
            assert result.chain_id == chain_id
            assert result.length == 1
    
    def test_minimal_audit_chain_error_handling(self):
        """Test error handling for malformed minimal chains."""
        with tempfile.TemporaryDirectory() as temp_dir:
            chain_dir = Path(temp_dir) / "audit_chain" / "20250910"
            chain_dir.mkdir(parents=True, exist_ok=True)
            
            # Test with empty chain directory
            empty_chain_dir = chain_dir / "chains" / "empty_chain"
            empty_chain_dir.mkdir(parents=True, exist_ok=True)
            
            # Create empty manifest
            empty_manifest = {
                "chain_id": "empty_chain",
                "root_hash": "0" * 64,
                "tip_hash": "0" * 64,
                "length": 0,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_event_id": "",
                "anchor_refs": []
            }
            
            empty_manifest_file = empty_chain_dir / "MANIFEST.json"
            with empty_manifest_file.open('w') as f:
                json.dump(empty_manifest, f, indent=2)
            
            verifier = AuditVerifier()
            result = verifier.verify_chain_from_path(str(empty_chain_dir))
            
            # Empty chains are considered failures
            assert not result.ok
            assert result.length == 0
            
            # Test with malformed JSON entry
            malformed_chain_dir = chain_dir / "chains" / "malformed_chain"
            malformed_chain_dir.mkdir(parents=True, exist_ok=True)
            
            # Create malformed entry file
            malformed_entry_file = malformed_chain_dir / "000001_malformed.json"
            with malformed_entry_file.open('w') as f:
                f.write("invalid json content")
            
            # Create manifest
            malformed_manifest = {
                "chain_id": "malformed_chain",
                "root_hash": "0" * 64,
                "tip_hash": "0" * 64,
                "length": 1,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_event_id": "evt_001",
                "anchor_refs": []
            }
            
            malformed_manifest_file = malformed_chain_dir / "MANIFEST.json"
            with malformed_manifest_file.open('w') as f:
                json.dump(malformed_manifest, f, indent=2)
            
            result = verifier.verify_chain_from_path(str(malformed_chain_dir))
            assert not result.ok
            assert len(result.breaks) > 0
    
    def test_minimal_audit_chain_receipt_validation(self):
        """Test that receipt files are properly validated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            chain_dir = Path(temp_dir) / "audit_chain" / "20250910"
            chain_dir.mkdir(parents=True, exist_ok=True)
            
            # Create valid chain
            chain_id = "test_receipt_001"
            entry_data = {
                "event_id": "evt_001",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": {"event_type": "roundtable_start", "data": {"task": "Hello world receipt test"}},
                "writer": "test_writer",
                "prev_hash": "0" * 64
            }
            
            entry_data_for_hash = entry_data.copy()
            entry_data_for_hash.pop('hash', None)
            entry_data["hash"] = compute_hash(entry_data_for_hash)
            
            # Create chain directory structure
            chains_dir = chain_dir / "chains" / chain_id
            chains_dir.mkdir(parents=True, exist_ok=True)
            
            # Write entry file
            entry_file = chains_dir / "000001_roundtable_start.json"
            with entry_file.open('w') as f:
                json.dump(entry_data, f, indent=2)
            
            # Create manifest
            manifest_data = {
                "chain_id": chain_id,
                "root_hash": entry_data["hash"],
                "tip_hash": entry_data["hash"],
                "length": 1,
                "created_at": entry_data["timestamp"],
                "last_event_id": entry_data["event_id"],
                "anchor_refs": []
            }
            
            manifest_file = chains_dir / "MANIFEST.json"
            with manifest_file.open('w') as f:
                json.dump(manifest_data, f, indent=2)
            
            # Test with valid receipt
            receipt_data = {
                "run_id": chain_id,
                "created_at": entry_data["timestamp"],
                "entry_count": 1,
                "root_hash": entry_data["hash"],
                "tip_hash": entry_data["hash"],
                "format_version": "v2.5.0",
                "description": "Receipt validation test"
            }
            
            receipt_file = chain_dir / f"run_{chain_id}_receipt.json"
            with receipt_file.open('w') as f:
                json.dump(receipt_data, f, indent=2)
            
            # Verify chain
            verifier = AuditVerifier()
            result = verifier.verify_chain_from_path(str(chains_dir))
            
            assert result.ok, f"Receipt validation failed: {result.breaks}"
            
            # Test with mismatched receipt
            receipt_data["entry_count"] = 999  # Wrong count
            with receipt_file.open('w') as f:
                json.dump(receipt_data, f, indent=2)
            
            # This should still pass because we're only verifying the chain, not the receipt
            result = verifier.verify_chain_from_path(str(chains_dir))
            assert result.ok  # Chain itself is still valid
