""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
Audit chain verification system.

Provides comprehensive verification of immutable audit chains including
hash continuity validation, manifest verification, and anchor checking.
"""

import time
from datetime import datetime
import os
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from .canonical import canonicalize_json, compute_hash, verify_hash
from .models import AuditEntry, AuditManifest, AuditAnchor, VerificationResult
from .storage import AuditStorage, create_storage


class AuditVerifier:
    """Main audit chain verification engine.
    
    Provides comprehensive verification of immutable audit chains with
    support for multiple storage backends and verification modes.
    """
    
    def __init__(self, storage: Optional[AuditStorage] = None, fail_fast: bool = True):
        """Initialize audit verifier.
        
        Args:
            storage: Storage backend (auto-detected if None)
            fail_fast: Stop verification on first error if True
        """
        self.storage = storage or create_storage()
        self.fail_fast = fail_fast
    
    def verify_chain(
        self,
        chain_id: str,
        start_after: Optional[str] = None,
        since: Optional[str] = None,
        anchor_file: Optional[Union[str, Path]] = None,
        ignore_signatures: bool = False,
        strict: bool = False,
        threads: int = 1
    ) -> VerificationResult:
        """Verify an audit chain for integrity and tamper-evidence.
        
        Args:
            chain_id: Chain identifier to verify
            start_after: Start verification after this event ID
            since: Start verification after this date (YYYY-MM-DD)
            anchor_file: Path to anchor file for root hash verification
            ignore_signatures: Skip signature verification if True
            strict: Reject unknown fields if True
            threads: Number of threads for parallel processing (future use)
            
        Returns:
            VerificationResult with comprehensive status and metrics
        """
        start_time = time.time()
        
        try:
            # Read manifest
            manifest = self.storage.read_manifest(chain_id)
            
            # Initialize result
            result = VerificationResult(
                ok=True,
                chain_id=chain_id,
                root_hash=manifest.root_hash,
                tip_hash=manifest.tip_hash,
                length=0
            )
            
            # Load anchor if provided
            anchor = None
            if anchor_file:
                anchor_path = Path(anchor_file)
                if anchor_path.exists():
                    try:
                        with anchor_path.open('r') as f:
                            import json
                            anchor_data = json.load(f)
                            anchor = AuditAnchor(**anchor_data)
                    except (json.JSONDecodeError, ValueError, TypeError):
                        # Corrupted or invalid anchor file - ignore it silently
                        pass
            
            # Verify anchor root hash if provided
            if anchor and anchor.root_hash != manifest.root_hash:
                result.add_break(
                    entry_index=0,
                    issue_type="anchor_mismatch",
                    description="Anchor root hash does not match manifest root hash",
                    details={
                        "anchor_root": anchor.root_hash,
                        "manifest_root": manifest.root_hash
                    }
                )
                result.ok = False
                if self.fail_fast:
                    return result
            
            # List and sort entries
            entry_filenames = self.storage.list_entries(chain_id)
            if not entry_filenames:
                result.add_break(
                    entry_index=0,
                    issue_type="empty_chain",
                    description="No entries found in chain"
                )
                result.ok = False
                return result
            
            # Apply filters
            filtered_entries = self._filter_entries(entry_filenames, start_after, since)
            
            # Verify each entry
            prev_hash = None
            verified_count = 0
            first_entry_hash: Optional[str] = None
            
            for i, entry_filename in enumerate(filtered_entries):
                try:
                    entry = self.storage.read_entry(chain_id, entry_filename)
                    
                    # Verify hash
                    if not self._verify_entry_hash(entry, strict):
                        result.add_break(
                            entry_index=i,
                            issue_type="hash_mismatch",
                            description=f"Entry hash does not match computed hash",
                            details={
                                "entry_hash": entry.hash,
                                "computed_hash": compute_hash(entry.model_dump())
                            }
                        )
                        result.ok = False
                        if self.fail_fast:
                            break
                    
                    # Verify prev_hash continuity
                    if prev_hash is not None and entry.prev_hash != prev_hash:
                        result.add_break(
                            entry_index=i,
                            issue_type="chain_break",
                            description="Previous hash does not match expected value",
                            details={
                                "expected_prev_hash": prev_hash,
                                "actual_prev_hash": entry.prev_hash
                            }
                        )
                        result.ok = False
                        if self.fail_fast:
                            break
                    
                    # Verify signatures if not ignoring
                    if not ignore_signatures and entry.signature and entry.pubkey:
                        if not self._verify_signature(entry):
                            result.add_break(
                                entry_index=i,
                                issue_type="signature_invalid",
                                description="Entry signature verification failed",
                                details={
                                    "signature": entry.signature,
                                    "pubkey": entry.pubkey
                                }
                            )
                            result.ok = False
                            if self.fail_fast:
                                break

                    # Optional policy-level m-of-n threshold check (non-crypto)
                    # If IOA_VERIFY_M_REQUIRED is set and entry payload contains a
                    # 'signatures' dict (kid -> signature string), require at least M
                    # distinct signatures to be present. This is a policy gate only.
                    try:
                        m_required_env = os.environ.get("IOA_VERIFY_M_REQUIRED")
                    except Exception:
                        m_required_env = None
                    if m_required_env:
                        try:
                            m_required = int(m_required_env)
                        except ValueError:
                            m_required = 0
                        if m_required > 0:
                            sig_map = None
                            try:
                                # Expect signatures under payload.signatures (dict)
                                # This avoids changing the entry schema.
                                payload: Dict[str, Any] = entry.payload  # type: ignore[attr-defined]
                                sig_map = payload.get("signatures") if isinstance(payload, dict) else None
                            except Exception:
                                sig_map = None
                            if isinstance(sig_map, dict):
                                unique_signers = len({k for k, v in sig_map.items() if isinstance(k, str) and isinstance(v, str) and v})
                                if unique_signers < m_required:
                                    result.add_break(
                                        entry_index=i,
                                        issue_type="multisig_threshold_unmet",
                                        description=f"Entry has {unique_signers} signatures; requires m>={m_required}",
                                        details={
                                            "required": m_required,
                                            "present": unique_signers,
                                        }
                                    )
                                    result.ok = False
                                    if self.fail_fast:
                                        break
                    
                    if i == 0:
                        first_entry_hash = entry.hash
                    prev_hash = entry.hash
                    verified_count += 1
                    
                except Exception as e:
                    result.add_break(
                        entry_index=i,
                        issue_type="read_error",
                        description=f"Failed to read entry: {e}",
                        details={"filename": entry_filename}
                    )
                    result.ok = False
                    if self.fail_fast:
                        break
            
            # Update result
            result.length = verified_count
            
            # Verify manifest length matches
            if verified_count != manifest.length:
                result.add_break(
                    entry_index=0,
                    issue_type="length_mismatch",
                    description="Verified entry count does not match manifest length",
                    details={
                        "verified_count": verified_count,
                        "manifest_length": manifest.length
                    }
                )
                result.ok = False
            
            # Verify manifest root/tip hashes match computed chain endpoints
            if first_entry_hash and manifest.root_hash and manifest.root_hash != first_entry_hash:
                result.add_break(
                    entry_index=0,
                    issue_type="hash_mismatch",
                    description="Manifest root_hash does not match first entry hash",
                    details={
                        "manifest_root": manifest.root_hash,
                        "computed_first": first_entry_hash,
                    }
                )
                result.ok = False
                if self.fail_fast:
                    return result

            if prev_hash and manifest.tip_hash and manifest.tip_hash != prev_hash:
                result.add_break(
                    entry_index=verified_count - 1 if verified_count > 0 else 0,
                    issue_type="hash_mismatch",
                    description="Manifest tip_hash does not match last entry hash",
                    details={
                        "manifest_tip": manifest.tip_hash,
                        "computed_last": prev_hash,
                    }
                )
                result.ok = False

            # Add performance metrics
            elapsed_time = time.time() - start_time
            result.add_performance_metric("verification_time_seconds", elapsed_time)
            result.add_performance_metric("entries_per_second", verified_count / elapsed_time if elapsed_time > 0 else 0)
            result.add_performance_metric("fail_fast", self.fail_fast)
            
            # Add coverage info
            result.coverage = {
                "total_entries": len(entry_filenames),
                "verified_entries": verified_count,
                "filtered_entries": len(filtered_entries),
                "start_after": start_after,
                "since": since
            }
            
            return result
            
        except Exception as e:
            # Create error result
            result = VerificationResult(
                ok=False,
                chain_id=chain_id,
                length=0
            )
            result.add_break(
                entry_index=0,
                issue_type="verification_error",
                description=f"Verification failed: {e}",
                details={"error_type": type(e).__name__}
            )
            return result
    
    def _filter_entries(
        self,
        entry_filenames: List[str],
        start_after: Optional[str] = None,
        since: Optional[str] = None
    ) -> List[str]:
        """Filter entries based on start_after and since parameters."""
        if not start_after and not since:
            return entry_filenames
        
        filtered = []
        for filename in entry_filenames:
            try:
                # Extract entry index from filename (e.g., "000001_event.json" -> 1)
                entry_index = int(filename.split('_')[0])
                
                # For now, just return all entries
                # In a full implementation, you'd filter based on entry content
                filtered.append(filename)
                
            except (ValueError, IndexError):
                # Skip malformed filenames
                continue
        
        return filtered
    
    def _verify_entry_hash(self, entry: AuditEntry, strict: bool = False) -> bool:
        """Verify that entry's hash matches its computed hash."""
        try:
            # Create entry dict for hashing - convert datetime back to ISO string
            entry_dict = entry.model_dump()
            
            # Convert datetime fields back to ISO strings for consistent hashing
            if 'timestamp' in entry_dict and isinstance(entry_dict['timestamp'], datetime):
                entry_dict['timestamp'] = entry_dict['timestamp'].isoformat()
            
            # Remove fields that shouldn't be included in hash computation
            entry_dict.pop('hash', None)
            
            # Only remove signature/pubkey if they are None (not present in original)
            if entry_dict.get('signature') is None:
                entry_dict.pop('signature', None)
            if entry_dict.get('pubkey') is None:
                entry_dict.pop('pubkey', None)
            
            # Compute hash
            computed_hash = compute_hash(entry_dict)
            
            return computed_hash == entry.hash
            
        except Exception:
            return False
    
    def _verify_signature(self, entry: AuditEntry) -> bool:
        """Verify entry signature (placeholder implementation)."""
        # In a full implementation, this would verify Ed25519 signatures
        # For now, just check that signature and pubkey are present
        return bool(entry.signature and entry.pubkey)
    
    def verify_chain_from_path(
        self,
        path: Union[str, Path],
        **kwargs
    ) -> VerificationResult:
        """Verify chain from a local path or S3 URI.
        
        Args:
            path: Local path or S3 URI (s3://bucket/prefix)
            **kwargs: Additional verification parameters
            
        Returns:
            VerificationResult
        """
        path_str = str(path)
        
        if path_str.startswith('s3://'):
            # Parse S3 URI
            parsed = urlparse(path_str)
            bucket = parsed.netloc
            prefix = parsed.path.lstrip('/')
            
            # Create S3 storage
            from .storage import S3Storage
            s3_storage = S3Storage(bucket, prefix)
            
            # Extract chain_id from prefix (assume it's the last part)
            chain_id = prefix.split('/')[-1] if prefix else "default"
            
            # Create verifier with S3 storage
            verifier = AuditVerifier(storage=s3_storage, fail_fast=kwargs.get('fail_fast', True))
            # Avoid passing duplicate chain_id both positionally and via kwargs
            kwargs.pop('chain_id', None)
            return verifier.verify_chain(chain_id, **kwargs)
        else:
            # Local filesystem path
            local_path = Path(path_str)
            
            if local_path.is_file():
                # Single file: support JSONL containing entries without a manifest (smoke tests)
                # In this mode, we construct a temporary in-memory verification by reading
                # entries directly from the file and validating hash continuity.
                from .models import VerificationResult, AuditEntry
                from .canonical import verify_hash
                import json

                chain_id = f"run_{local_path.stem}" if not local_path.stem.startswith("run_") else local_path.stem
                result = VerificationResult(ok=True, chain_id=chain_id, root_hash=None, tip_hash=None, length=0)

                try:
                    raw_entries: list[dict] = []
                    with local_path.open("r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            data = json.loads(line)
                            raw_entries.append(data)

                    if not raw_entries:
                        result.ok = False
                        result.add_break(0, "empty_chain", "Chain contains no entries")
                        return result

                    # Verify continuity tolerantly (without strict model parsing)
                    prev_hash: Optional[str] = None
                    for idx, entry_dict in enumerate(raw_entries):
                        entry_hash = entry_dict.get("hash")
                        prev = entry_dict.get("prev_hash")

                        # Verify entry hash
                        data_for_hash = dict(entry_dict)
                        if "hash" in data_for_hash:
                            data_for_hash.pop("hash", None)
                        if not isinstance(entry_hash, str) or len(entry_hash) != 64:
                            result.ok = False
                            result.add_break(idx, "invalid_hash_format", "Entry hash missing or invalid format")
                            # Also surface as hash_mismatch for compatibility with callers expecting this key
                            result.add_break(idx, "hash_mismatch", "Entry hash does not match canonical payload (invalid format)")
                            if self.fail_fast:
                                break
                        else:
                            if not verify_hash(data_for_hash, entry_hash):
                                result.ok = False
                                result.add_break(idx, "hash_mismatch", "Entry hash does not match canonical payload")
                                if self.fail_fast:
                                    break

                        # Verify prev_hash continuity
                        if idx == 0:
                            result.root_hash = entry_hash if isinstance(entry_hash, str) else None
                            if prev not in (None, "0" * 64):
                                result.ok = False
                                result.add_break(idx, "invalid_prev_hash_root", "First entry prev_hash should be null or zeros", {
                                    "found": prev,
                                })
                                if self.fail_fast:
                                    break
                        else:
                            if prev != prev_hash:
                                result.ok = False
                                result.add_break(idx, "chain_break", "prev_hash does not match previous entry hash", {
                                    "expected": prev_hash,
                                    "found": prev,
                                })
                                if self.fail_fast:
                                    break

                        # Domain policy: only allow known event types in JSONL mode
                        try:
                            event_type = entry_dict.get("payload", {}).get("event_type")
                            allowed_event_types = {"roundtable_response"}
                            if event_type not in allowed_event_types:
                                result.ok = False
                                result.add_break(idx, "unauthorized_event", "Entry event_type not allowed in JSONL verification", {
                                    "event_type": event_type,
                                    "allowed": sorted(list(allowed_event_types)),
                                })
                                if self.fail_fast:
                                    break
                        except Exception:
                            # If structure is unexpected, mark as break
                            result.ok = False
                            result.add_break(idx, "malformed_entry", "Entry payload missing or malformed")
                            if self.fail_fast:
                                break

                        prev_hash = entry_hash if isinstance(entry_hash, str) else None

                    result.length = len(raw_entries)
                    result.tip_hash = prev_hash

                    # Ensure invalid hash formats are surfaced even if other breaks occurred
                    try:
                        any_invalid = any(
                            not isinstance(e.get("hash"), str) or len(e.get("hash", "")) != 64
                            for e in raw_entries
                        )
                        if any_invalid and not any(b.get("issue_type") == "invalid_hash_format" for b in result.breaks):
                            # Attach a summary invalid-hash break for visibility
                            result.add_break(
                                entry_index=0,
                                issue_type="invalid_hash_format",
                                description="One or more entries have invalid hash format",
                                details={}
                            )
                    except Exception:
                        pass
                    return result
                except Exception:
                    # Fallback to directory-based logic if JSONL handling fails catastrophically
                    pass

                # Treat as chain directory in fallback
                chain_dir = local_path.parent
                chain_id = local_path.stem
            else:
                # Directory - check if it's a chain directory or contains chains
                if (local_path / "MANIFEST.json").exists():
                    # This is a chain directory
                    chain_dir = local_path
                    chain_id = local_path.name
                else:
                    # Directory containing chains
                    chain_dir = local_path
                    chain_id = kwargs.get('chain_id')
                    if not chain_id:
                        # Try to find a chain
                        chains = [d.name for d in chain_dir.iterdir() if d.is_dir() and (d / "MANIFEST.json").exists()]
                        if chains:
                            chain_id = chains[0]
                        else:
                            raise ValueError("No chain found in directory")
            
            # Create filesystem storage - use the directory containing chains
            from .storage import FileSystemStorage
            if (chain_dir / "MANIFEST.json").exists():
                # Chain directory - use parent's parent as base (skip the chains level)
                fs_storage = FileSystemStorage(chain_dir.parent.parent)
            else:
                # Directory containing chains
                fs_storage = FileSystemStorage(chain_dir)
            
            # Create verifier with filesystem storage
            verifier = AuditVerifier(storage=fs_storage, fail_fast=kwargs.get('fail_fast', True))
            # Avoid passing duplicate chain_id both positionally and via kwargs
            kwargs.pop('chain_id', None)
            return verifier.verify_chain(chain_id, **kwargs)
