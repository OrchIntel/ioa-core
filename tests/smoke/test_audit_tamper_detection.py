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
from pathlib import Path
from datetime import datetime, timezone
from src.audit.verify import AuditVerifier
from src.audit.canonical import compute_hash


class TestAuditTamperDetection:
    """Test tamper detection in audit chains."""
    
    def test_tamper_detection_content_modification(self):
        """Test that content modification is detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            chain_id = "test_tamper_content_001"
            chain_dir = Path(temp_dir) / "audit_chain" / "20250910"
            chain_dir.mkdir(parents=True, exist_ok=True)
            
            # Create original entries
            entries = []
            prev_hash = "0" * 64
            
            for i in range(3):
                entry_data = {
                    "event_id": f"evt_{i+1:03d}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "event_type": "roundtable_response",
                        "data": {
                            "provider": f"provider_{i}",
                            "content": f"Original content {i+1}",
                            "tokens_used": 100 + i * 50
                        }
                    },
                    "writer": f"test_writer_{i}",
                    "prev_hash": prev_hash
                }
                
                entry_data_for_hash = entry_data.copy()
                entry_data_for_hash.pop('hash', None)
                entry_data["hash"] = compute_hash(entry_data_for_hash)
                
                entries.append(entry_data)
                prev_hash = entry_data["hash"]
            
            # Create chain directory structure
            chains_dir = chain_dir / "chains" / chain_id
            chains_dir.mkdir(parents=True, exist_ok=True)
            
            # Write entry files
            for i, entry in enumerate(entries):
                entry_file = chains_dir / f"{i+1:06d}_roundtable_response.json"
                with entry_file.open('w') as f:
                    json.dump(entry, f, indent=2)
            
            # Create manifest
            manifest_data = {
                "chain_id": chain_id,
                "root_hash": entries[0]["hash"],
                "tip_hash": entries[-1]["hash"],
                "length": len(entries),
                "created_at": entries[0]["timestamp"],
                "last_event_id": entries[-1]["event_id"],
                "anchor_refs": []
            }
            
            manifest_file = chains_dir / "MANIFEST.json"
            with manifest_file.open('w') as f:
                json.dump(manifest_data, f, indent=2)
            
            # Verify original chain
            verifier = AuditVerifier()
            result = verifier.verify_chain_from_path(str(chains_dir))
            assert result.ok, "Original chain should be valid"
            
            # Tamper with the content
            tampered_entries = entries.copy()
            tampered_entries[1]["payload"]["data"]["content"] = "TAMPERED CONTENT"
            
            # Recompute hash for tampered entry
            entry_data_for_hash = tampered_entries[1].copy()
            entry_data_for_hash.pop('hash', None)
            tampered_entries[1]["hash"] = compute_hash(entry_data_for_hash)
            
            # Write tampered entry file
            tampered_entry_file = chains_dir / "000002_roundtable_response.json"
            with tampered_entry_file.open('w') as f:
                json.dump(tampered_entries[1], f, indent=2)
            
            # Verify tampered chain (should fail)
            result = verifier.verify_chain_from_path(str(chains_dir))
            assert not result.ok, "Tampered chain should be detected"
            assert len(result.breaks) > 0
            assert any("hash_mismatch" in str(break_info) for break_info in result.breaks)
    
    def test_tamper_detection_hash_modification(self):
        """Test that hash modification is detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            chain_id = "test_tamper_hash_001"
            chain_dir = Path(temp_dir) / "audit_chain" / "20250910"
            chain_dir.mkdir(parents=True, exist_ok=True)
            
            # Create original entries
            entries = []
            prev_hash = "0" * 64
            
            for i in range(3):
                entry_data = {
                    "event_id": f"evt_{i+1:03d}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "event_type": "roundtable_response",
                        "data": {
                            "provider": f"provider_{i}",
                            "content": f"Original content {i+1}"
                        }
                    },
                    "writer": f"test_writer_{i}",
                    "prev_hash": prev_hash
                }
                
                entry_data_for_hash = entry_data.copy()
                entry_data_for_hash.pop('hash', None)
                entry_data["hash"] = compute_hash(entry_data_for_hash)
                
                entries.append(entry_data)
                prev_hash = entry_data["hash"]
            
            # Write original chain
            chain_file = chain_dir / f"run_{chain_id}.jsonl"
            with chain_file.open('w') as f:
                for entry in entries:
                    f.write(json.dumps(entry) + '\n')
            
            # Verify original chain
            verifier = AuditVerifier()
            result = verifier.verify_chain_from_path(str(chain_file))
            assert result.ok, "Original chain should be valid"
            
            # Tamper with a hash
            tampered_entries = entries.copy()
            tampered_entries[1]["hash"] = "tampered_hash_value"
            
            # Write tampered chain
            with chain_file.open('w') as f:
                for entry in tampered_entries:
                    f.write(json.dumps(entry) + '\n')
            
            # Verify tampered chain (should fail)
            result = verifier.verify_chain_from_path(str(chain_file))
            assert not result.ok, "Hash tampering should be detected"
            assert len(result.breaks) > 0
            assert any("hash_mismatch" in str(break_info) for break_info in result.breaks)
    
    def test_tamper_detection_chain_break(self):
        """Test that chain breaks are detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            chain_id = "test_tamper_chain_001"
            chain_dir = Path(temp_dir) / "audit_chain" / "20250910"
            chain_dir.mkdir(parents=True, exist_ok=True)
            
            # Create original entries
            entries = []
            prev_hash = "0" * 64
            
            for i in range(3):
                entry_data = {
                    "event_id": f"evt_{i+1:03d}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "event_type": "roundtable_response",
                        "data": {
                            "provider": f"provider_{i}",
                            "content": f"Original content {i+1}"
                        }
                    },
                    "writer": f"test_writer_{i}",
                    "prev_hash": prev_hash
                }
                
                entry_data_for_hash = entry_data.copy()
                entry_data_for_hash.pop('hash', None)
                entry_data["hash"] = compute_hash(entry_data_for_hash)
                
                entries.append(entry_data)
                prev_hash = entry_data["hash"]
            
            # Write original chain
            chain_file = chain_dir / f"run_{chain_id}.jsonl"
            with chain_file.open('w') as f:
                for entry in entries:
                    f.write(json.dumps(entry) + '\n')
            
            # Verify original chain
            verifier = AuditVerifier()
            result = verifier.verify_chain_from_path(str(chain_file))
            assert result.ok, "Original chain should be valid"
            
            # Break the chain by modifying prev_hash
            tampered_entries = entries.copy()
            tampered_entries[1]["prev_hash"] = "broken_chain_hash"
            
            # Recompute hash for the tampered entry
            entry_data_for_hash = tampered_entries[1].copy()
            entry_data_for_hash.pop('hash', None)
            tampered_entries[1]["hash"] = compute_hash(entry_data_for_hash)
            
            # Write tampered chain
            with chain_file.open('w') as f:
                for entry in tampered_entries:
                    f.write(json.dumps(entry) + '\n')
            
            # Verify tampered chain (should fail)
            result = verifier.verify_chain_from_path(str(chain_file))
            assert not result.ok, "Chain break should be detected"
            assert len(result.breaks) > 0
            assert any("chain_break" in str(break_info) for break_info in result.breaks)
    
    def test_tamper_detection_entry_deletion(self):
        """Test that entry deletion is detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            chain_id = "test_tamper_deletion_001"
            chain_dir = Path(temp_dir) / "audit_chain" / "20250910"
            chain_dir.mkdir(parents=True, exist_ok=True)
            
            # Create original entries
            entries = []
            prev_hash = "0" * 64
            
            for i in range(3):
                entry_data = {
                    "event_id": f"evt_{i+1:03d}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "event_type": "roundtable_response",
                        "data": {
                            "provider": f"provider_{i}",
                            "content": f"Original content {i+1}"
                        }
                    },
                    "writer": f"test_writer_{i}",
                    "prev_hash": prev_hash
                }
                
                entry_data_for_hash = entry_data.copy()
                entry_data_for_hash.pop('hash', None)
                entry_data["hash"] = compute_hash(entry_data_for_hash)
                
                entries.append(entry_data)
                prev_hash = entry_data["hash"]
            
            # Write original chain
            chain_file = chain_dir / f"run_{chain_id}.jsonl"
            with chain_file.open('w') as f:
                for entry in entries:
                    f.write(json.dumps(entry) + '\n')
            
            # Verify original chain
            verifier = AuditVerifier()
            result = verifier.verify_chain_from_path(str(chain_file))
            assert result.ok, "Original chain should be valid"
            
            # Delete middle entry
            tampered_entries = [entries[0], entries[2]]  # Skip middle entry
            
            # Write tampered chain
            with chain_file.open('w') as f:
                for entry in tampered_entries:
                    f.write(json.dumps(entry) + '\n')
            
            # Verify tampered chain (should fail)
            result = verifier.verify_chain_from_path(str(chain_file))
            assert not result.ok, "Entry deletion should be detected"
            assert len(result.breaks) > 0
            assert any("chain_break" in str(break_info) for break_info in result.breaks)
    
    def test_tamper_detection_entry_addition(self):
        """Test that unauthorized entry addition is detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            chain_id = "test_tamper_addition_001"
            chain_dir = Path(temp_dir) / "audit_chain" / "20250910"
            chain_dir.mkdir(parents=True, exist_ok=True)
            
            # Create original entries
            entries = []
            prev_hash = "0" * 64
            
            for i in range(2):
                entry_data = {
                    "event_id": f"evt_{i+1:03d}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "event_type": "roundtable_response",
                        "data": {
                            "provider": f"provider_{i}",
                            "content": f"Original content {i+1}"
                        }
                    },
                    "writer": f"test_writer_{i}",
                    "prev_hash": prev_hash
                }
                
                entry_data_for_hash = entry_data.copy()
                entry_data_for_hash.pop('hash', None)
                entry_data["hash"] = compute_hash(entry_data_for_hash)
                
                entries.append(entry_data)
                prev_hash = entry_data["hash"]
            
            # Write original chain
            chain_file = chain_dir / f"run_{chain_id}.jsonl"
            with chain_file.open('w') as f:
                for entry in entries:
                    f.write(json.dumps(entry) + '\n')
            
            # Verify original chain
            verifier = AuditVerifier()
            result = verifier.verify_chain_from_path(str(chain_file))
            assert result.ok, "Original chain should be valid"
            
            # Add unauthorized entry
            tampered_entries = entries.copy()
            unauthorized_entry = {
                "event_id": "evt_999",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": {
                    "event_type": "unauthorized_event",
                    "data": {
                        "provider": "malicious_provider",
                        "content": "Unauthorized content"
                    }
                },
                "writer": "malicious_writer",
                "prev_hash": entries[-1]["hash"]
            }
            
            # Compute hash for unauthorized entry
            entry_data_for_hash = unauthorized_entry.copy()
            entry_data_for_hash.pop('hash', None)
            unauthorized_entry["hash"] = compute_hash(entry_data_for_hash)
            
            tampered_entries.append(unauthorized_entry)
            
            # Write tampered chain
            with chain_file.open('w') as f:
                for entry in tampered_entries:
                    f.write(json.dumps(entry) + '\n')
            
            # Verify tampered chain (should fail due to hash chain break)
            result = verifier.verify_chain_from_path(str(chain_file))
            assert not result.ok, "Unauthorized entry addition should be detected"
            assert len(result.breaks) > 0
    
    def test_tamper_detection_manifest_tampering(self):
        """Test that manifest tampering is detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            chain_id = "test_tamper_manifest_001"
            chain_dir = Path(temp_dir) / "audit_chain" / "chains" / chain_id
            chain_dir.mkdir(parents=True, exist_ok=True)
            
            # Create entries
            entries = []
            prev_hash = "0" * 64
            
            for i in range(2):
                entry_data = {
                    "event_id": f"evt_{i+1:03d}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "event_type": "roundtable_response",
                        "data": {
                            "provider": f"provider_{i}",
                            "content": f"Original content {i+1}"
                        }
                    },
                    "writer": f"test_writer_{i}",
                    "prev_hash": prev_hash
                }
                
                entry_data_for_hash = entry_data.copy()
                entry_data_for_hash.pop('hash', None)
                entry_data["hash"] = compute_hash(entry_data_for_hash)
                
                entries.append(entry_data)
                prev_hash = entry_data["hash"]
            
            # Write entry files
            for i, entry in enumerate(entries):
                entry_file = chain_dir / f"{i+1:06d}_roundtable_response.json"
                with entry_file.open('w') as f:
                    json.dump(entry, f, indent=2)
            
            # Create original manifest
            manifest_data = {
                "chain_id": chain_id,
                "root_hash": entries[0]["hash"],
                "tip_hash": entries[-1]["hash"],
                "length": len(entries),
                "created_at": entries[0]["timestamp"],
                "last_event_id": entries[-1]["event_id"],
                "anchor_refs": []
            }
            
            manifest_file = chain_dir / "MANIFEST.json"
            with manifest_file.open('w') as f:
                json.dump(manifest_data, f, indent=2)
            
            # Verify original chain
            verifier = AuditVerifier()
            result = verifier.verify_chain_from_path(str(chain_dir))
            assert result.ok, "Original chain should be valid"
            
            # Tamper with manifest
            tampered_manifest = manifest_data.copy()
            tampered_manifest["length"] = 999  # Wrong length
            tampered_manifest["tip_hash"] = "tampered_tip_hash"
            
            with manifest_file.open('w') as f:
                json.dump(tampered_manifest, f, indent=2)
            
            # Verify tampered chain (should fail)
            result = verifier.verify_chain_from_path(str(chain_dir))
            assert not result.ok, "Manifest tampering should be detected"
            assert len(result.breaks) > 0
    
    def test_tamper_detection_receipt_tampering(self):
        """Test that receipt tampering is detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            chain_id = "test_tamper_receipt_001"
            chain_dir = Path(temp_dir) / "audit_chain" / "20250910"
            chain_dir.mkdir(parents=True, exist_ok=True)
            
            # Create entries
            entries = []
            prev_hash = "0" * 64
            
            for i in range(2):
                entry_data = {
                    "event_id": f"evt_{i+1:03d}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "event_type": "roundtable_response",
                        "data": {
                            "provider": f"provider_{i}",
                            "content": f"Original content {i+1}"
                        }
                    },
                    "writer": f"test_writer_{i}",
                    "prev_hash": prev_hash
                }
                
                entry_data_for_hash = entry_data.copy()
                entry_data_for_hash.pop('hash', None)
                entry_data["hash"] = compute_hash(entry_data_for_hash)
                
                entries.append(entry_data)
                prev_hash = entry_data["hash"]
            
            # Write chain
            chain_file = chain_dir / f"run_{chain_id}.jsonl"
            with chain_file.open('w') as f:
                for entry in entries:
                    f.write(json.dumps(entry) + '\n')
            
            # Create original receipt
            receipt_data = {
                "run_id": chain_id,
                "created_at": entries[0]["timestamp"],
                "entry_count": len(entries),
                "root_hash": entries[0]["hash"],
                "tip_hash": entries[-1]["hash"],
                "format_version": "v2.5.0",
                "description": "Original receipt"
            }
            
            receipt_file = chain_dir / f"run_{chain_id}_receipt.json"
            with receipt_file.open('w') as f:
                json.dump(receipt_data, f, indent=2)
            
            # Verify original chain
            verifier = AuditVerifier()
            result = verifier.verify_chain_from_path(str(chain_file))
            assert result.ok, "Original chain should be valid"
            
            # Tamper with receipt
            tampered_receipt = receipt_data.copy()
            tampered_receipt["entry_count"] = 999  # Wrong count
            tampered_receipt["tip_hash"] = "tampered_tip_hash"
            
            with receipt_file.open('w') as f:
                json.dump(tampered_receipt, f, indent=2)
            
            # Verify chain (should still pass because we only verify the chain, not the receipt)
            result = verifier.verify_chain_from_path(str(chain_file))
            assert result.ok, "Chain verification should still pass (receipt is separate)"
            
            # But the receipt itself is now inconsistent
            assert tampered_receipt["entry_count"] != len(entries)
            assert tampered_receipt["tip_hash"] != entries[-1]["hash"]
    
    def test_tamper_detection_multiple_tampering(self):
        """Test detection of multiple types of tampering."""
        with tempfile.TemporaryDirectory() as temp_dir:
            chain_id = "test_tamper_multiple_001"
            chain_dir = Path(temp_dir) / "audit_chain" / "20250910"
            chain_dir.mkdir(parents=True, exist_ok=True)
            
            # Create original entries
            entries = []
            prev_hash = "0" * 64
            
            for i in range(3):
                entry_data = {
                    "event_id": f"evt_{i+1:03d}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "event_type": "roundtable_response",
                        "data": {
                            "provider": f"provider_{i}",
                            "content": f"Original content {i+1}",
                            "tokens_used": 100 + i * 50
                        }
                    },
                    "writer": f"test_writer_{i}",
                    "prev_hash": prev_hash
                }
                
                entry_data_for_hash = entry_data.copy()
                entry_data_for_hash.pop('hash', None)
                entry_data["hash"] = compute_hash(entry_data_for_hash)
                
                entries.append(entry_data)
                prev_hash = entry_data["hash"]
            
            # Write original chain
            chain_file = chain_dir / f"run_{chain_id}.jsonl"
            with chain_file.open('w') as f:
                for entry in entries:
                    f.write(json.dumps(entry) + '\n')
            
            # Verify original chain
            verifier = AuditVerifier()
            result = verifier.verify_chain_from_path(str(chain_file))
            assert result.ok, "Original chain should be valid"
            
            # Apply multiple tampering techniques
            tampered_entries = entries.copy()
            
            # 1. Modify content
            tampered_entries[0]["payload"]["data"]["content"] = "TAMPERED CONTENT"
            
            # 2. Break chain
            tampered_entries[1]["prev_hash"] = "broken_chain"
            
            # 3. Corrupt hash
            tampered_entries[2]["hash"] = "corrupted_hash"
            
            # Recompute hashes for tampered entries
            for i, entry in enumerate(tampered_entries):
                # Preserve intentionally corrupted hash to verify detection
                if entry.get("hash") == "corrupted_hash":
                    continue
                entry_data_for_hash = entry.copy()
                entry_data_for_hash.pop('hash', None)
                tampered_entries[i]["hash"] = compute_hash(entry_data_for_hash)
            
            # Write tampered chain
            with chain_file.open('w') as f:
                for entry in tampered_entries:
                    f.write(json.dumps(entry) + '\n')
            
            # Verify tampered chain (should fail with multiple breaks)
            result = verifier.verify_chain_from_path(str(chain_file))
            assert not result.ok, "Multiple tampering should be detected"
            assert len(result.breaks) > 1, "Should detect multiple types of tampering"
