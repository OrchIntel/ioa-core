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


class TestAuditMultiProvider:
    """Test multi-provider audit chain generation and verification."""
    
    def test_multi_provider_audit_chain(self):
        """Test audit chain with multiple providers and hash chaining."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create chain directory
            chain_id = "test_multi_provider_001"
            chain_dir = Path(temp_dir) / "audit_chain" / "20250910"
            chain_dir.mkdir(parents=True, exist_ok=True)
            
            # Create multiple entries simulating different providers
            providers = ["openai", "anthropic", "gemini", "deepseek"]
            entries = []
            prev_hash = "0" * 64  # Root hash
            
            for i, provider in enumerate(providers):
                entry_data = {
                    "event_id": f"evt_{i+1:03d}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "event_type": "roundtable_response",
                        "data": {
                            "provider": provider,
                            "model": f"{provider}_model",
                            "response": f"Response from {provider}",
                            "tokens_used": 100 + i * 50
                        }
                    },
                    "writer": f"test_writer_{provider}",
                    "prev_hash": prev_hash
                }
                
                # Compute hash (exclude the hash field itself)
                entry_data_for_hash = entry_data.copy()
                entry_data_for_hash.pop('hash', None)
                entry_data["hash"] = compute_hash(entry_data_for_hash)
                
                entries.append(entry_data)
                prev_hash = entry_data["hash"]  # Chain to next entry
            
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
            
            # Create receipt file
            receipt_data = {
                "run_id": chain_id,
                "created_at": entries[0]["timestamp"],
                "entry_count": len(entries),
                "root_hash": entries[0]["hash"],
                "tip_hash": entries[-1]["hash"],
                "format_version": "v2.5.0",
                "description": "Multi-provider audit chain test",
                "metadata": {
                    "providers_used": providers,
                    "total_tokens": sum(entry["payload"]["data"]["tokens_used"] for entry in entries),
                    "operation_type": "roundtable"
                }
            }
            
            receipt_file = chain_dir / f"run_{chain_id}_receipt.json"
            with receipt_file.open('w') as f:
                json.dump(receipt_data, f, indent=2)
            
            # Verify the chain
            verifier = AuditVerifier()
            result = verifier.verify_chain_from_path(str(chains_dir))
            
            # Assertions
            assert result.ok, f"Multi-provider chain verification failed: {result.breaks}"
            assert result.chain_id == chain_id
            assert result.length == len(entries)
            assert result.root_hash == entries[0]["hash"]
            assert result.tip_hash == entries[-1]["hash"]
            assert len(result.breaks) == 0
    
    def test_multi_provider_chain_continuity(self):
        """Test that hash chain continuity is maintained across providers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            chain_id = "test_continuity_001"
            chain_dir = Path(temp_dir) / "audit_chain" / "20250910"
            chain_dir.mkdir(parents=True, exist_ok=True)
            
            # Create entries with proper hash chaining
            entries = []
            prev_hash = "0" * 64
            
            for i in range(5):
                entry_data = {
                    "event_id": f"evt_{i+1:03d}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "event_type": "roundtable_response",
                        "data": {
                            "provider": f"provider_{i % 3}",  # Cycle through 3 providers
                            "step": i + 1,
                            "content": f"Step {i+1} content"
                        }
                    },
                    "writer": f"test_writer_{i % 3}",
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
            
            # Verify chain
            verifier = AuditVerifier()
            result = verifier.verify_chain_from_path(str(chains_dir))
            
            assert result.ok, f"Chain continuity verification failed: {result.breaks}"
            assert result.length == 5
            
            # Verify each entry's prev_hash matches the previous entry's hash
            for i in range(1, len(entries)):
                assert entries[i]["prev_hash"] == entries[i-1]["hash"], \
                    f"Hash chain broken at entry {i}"
    
    def test_multi_provider_chain_with_manifest(self):
        """Test multi-provider chain with manifest file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            chain_id = "test_multi_manifest_001"
            chain_dir = Path(temp_dir) / "audit_chain" / "chains" / chain_id
            chain_dir.mkdir(parents=True, exist_ok=True)
            
            # Create entries
            providers = ["openai", "anthropic", "gemini"]
            entries = []
            prev_hash = "0" * 64
            
            for i, provider in enumerate(providers):
                entry_data = {
                    "event_id": f"evt_{i+1:03d}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "event_type": "roundtable_response",
                        "data": {
                            "provider": provider,
                            "response": f"Response from {provider}",
                            "confidence": 0.8 + i * 0.05
                        }
                    },
                    "writer": f"test_writer_{provider}",
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
            
            manifest_file = chain_dir / "MANIFEST.json"
            with manifest_file.open('w') as f:
                json.dump(manifest_data, f, indent=2)
            
            # Verify chain
            verifier = AuditVerifier()
            result = verifier.verify_chain_from_path(str(chain_dir))
            
            assert result.ok, f"Multi-provider manifest verification failed: {result.breaks}"
            assert result.chain_id == chain_id
            assert result.length == len(entries)
            assert result.root_hash == entries[0]["hash"]
            assert result.tip_hash == entries[-1]["hash"]
    
    def test_multi_provider_chain_break_detection(self):
        """Test that hash chain breaks are detected in multi-provider chains."""
        with tempfile.TemporaryDirectory() as temp_dir:
            chain_id = "test_break_detection_001"
            chain_dir = Path(temp_dir) / "audit_chain" / "20250910"
            chain_dir.mkdir(parents=True, exist_ok=True)
            
            # Create entries with a broken chain
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
                            "content": f"Content {i+1}"
                        }
                    },
                    "writer": f"test_writer_{i}",
                    "prev_hash": prev_hash
                }
                
                # Break the chain on the second entry
                if i == 1:
                    entry_data["prev_hash"] = "1" * 64  # Wrong prev_hash
                
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
            
            # Verify chain (should fail)
            verifier = AuditVerifier()
            result = verifier.verify_chain_from_path(str(chains_dir))
            
            assert not result.ok, "Chain break should have been detected"
            assert len(result.breaks) > 0
            assert any("chain_break" in str(break_info) for break_info in result.breaks)
    
    def test_multi_provider_chain_hash_mismatch(self):
        """Test that hash mismatches are detected in multi-provider chains."""
        with tempfile.TemporaryDirectory() as temp_dir:
            chain_id = "test_hash_mismatch_001"
            chain_dir = Path(temp_dir) / "audit_chain" / "20250910"
            chain_dir.mkdir(parents=True, exist_ok=True)
            
            # Create entries
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
                            "content": f"Content {i+1}"
                        }
                    },
                    "writer": f"test_writer_{i}",
                    "prev_hash": prev_hash
                }
                
                entry_data_for_hash = entry_data.copy()
                entry_data_for_hash.pop('hash', None)
                entry_data["hash"] = compute_hash(entry_data_for_hash)
                
                # Corrupt the hash on the second entry
                if i == 1:
                    entry_data["hash"] = "corrupted_hash"
                
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
            
            # Verify chain (should fail)
            verifier = AuditVerifier()
            result = verifier.verify_chain_from_path(str(chains_dir))
            
            assert not result.ok, f"Hash mismatch should have been detected: {result.breaks}"
            assert len(result.breaks) > 0
            # Check for any hash-related issues
            assert any("hash" in str(break_info).lower() for break_info in result.breaks)
    
    def test_multi_provider_chain_metadata_validation(self):
        """Test that metadata in multi-provider chains is properly validated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            chain_id = "test_metadata_001"
            chain_dir = Path(temp_dir) / "audit_chain" / "20250910"
            chain_dir.mkdir(parents=True, exist_ok=True)
            
            # Create entries with rich metadata
            providers = ["openai", "anthropic", "gemini"]
            entries = []
            prev_hash = "0" * 64
            
            for i, provider in enumerate(providers):
                entry_data = {
                    "event_id": f"evt_{i+1:03d}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "event_type": "roundtable_response",
                        "data": {
                            "provider": provider,
                            "model": f"{provider}_model",
                            "response": f"Response from {provider}",
                            "tokens_used": 100 + i * 50,
                            "confidence": 0.8 + i * 0.05,
                            "latency_ms": 1000 + i * 100
                        }
                    },
                    "writer": f"test_writer_{provider}",
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
            
            # Create receipt with metadata
            receipt_data = {
                "run_id": chain_id,
                "created_at": entries[0]["timestamp"],
                "entry_count": len(entries),
                "root_hash": entries[0]["hash"],
                "tip_hash": entries[-1]["hash"],
                "format_version": "v2.5.0",
                "description": "Multi-provider metadata test",
                "metadata": {
                    "providers_used": providers,
                    "total_tokens": sum(entry["payload"]["data"]["tokens_used"] for entry in entries),
                    "avg_confidence": sum(entry["payload"]["data"]["confidence"] for entry in entries) / len(entries),
                    "avg_latency_ms": sum(entry["payload"]["data"]["latency_ms"] for entry in entries) / len(entries),
                    "operation_type": "roundtable"
                }
            }
            
            receipt_file = chain_dir / f"run_{chain_id}_receipt.json"
            with receipt_file.open('w') as f:
                json.dump(receipt_data, f, indent=2)
            
            # Verify chain
            verifier = AuditVerifier()
            result = verifier.verify_chain_from_path(str(chains_dir))
            
            assert result.ok, f"Metadata validation failed: {result.breaks}"
            assert result.length == len(entries)
            
            # Verify metadata is accessible
            assert receipt_data["metadata"]["providers_used"] == providers
            assert receipt_data["metadata"]["total_tokens"] > 0
            assert receipt_data["metadata"]["avg_confidence"] > 0
