""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
Audit data models for immutable log verification.

Defines the structure for audit entries, manifests, and anchors used in
IOA's tamper-evident audit chain system.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
import hashlib


class AuditEntry(BaseModel):
    """Individual audit entry in the immutable chain.
    
    Each entry contains event data, cryptographic hash, and chain continuity
    information to ensure tamper-evidence.
    """
    
    event_id: str = Field(..., description="Unique identifier for this event")
    timestamp: datetime = Field(..., description="When the event occurred")
    prev_hash: Optional[str] = Field(None, description="Hash of previous entry in chain")
    hash: str = Field(..., description="SHA-256 hash of this entry's canonical JSON")
    payload: Dict[str, Any] = Field(..., description="Event data payload")
    writer: str = Field(..., description="Service/component that wrote this entry")
    signature: Optional[str] = Field(None, description="Ed25519 signature if present")
    pubkey: Optional[str] = Field(None, description="Public key for signature verification")
    
    @field_validator('hash')
    @classmethod
    def validate_hash_format(cls, v):
        """Validate hash is 64-character hex string."""
        if not isinstance(v, str) or len(v) != 64:
            raise ValueError("Hash must be 64-character hex string")
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("Hash must be valid hexadecimal")
        return v
    
    @field_validator('prev_hash')
    @classmethod
    def validate_prev_hash_format(cls, v):
        """Validate prev_hash is 64-character hex string or None."""
        if v is None:
            return v
        if not isinstance(v, str) or len(v) != 64:
            raise ValueError("prev_hash must be 64-character hex string")
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("prev_hash must be valid hexadecimal")
        return v


class AuditManifest(BaseModel):
    """Manifest file containing chain metadata and root/tip hashes.
    
    Provides quick access to chain state without reading all entries.
    """
    
    chain_id: str = Field(..., description="Unique identifier for this audit chain")
    root_hash: str = Field(..., description="Hash of the first entry in chain")
    tip_hash: str = Field(..., description="Hash of the most recent entry")
    length: int = Field(..., description="Number of entries in chain")
    created_at: datetime = Field(..., description="When the chain was created")
    last_event_id: str = Field(..., description="ID of the most recent event")
    anchor_refs: List[Dict[str, str]] = Field(default_factory=list, description="External anchor references")
    
    @field_validator('root_hash', 'tip_hash')
    @classmethod
    def validate_hash_format(cls, v):
        """Validate hash is 64-character hex string."""
        if not isinstance(v, str) or len(v) != 64:
            raise ValueError("Hash must be 64-character hex string")
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("Hash must be valid hexadecimal")
        return v


class AuditAnchor(BaseModel):
    """External anchor point for chain verification.
    
    Represents a published snapshot of a chain's root hash at a specific time,
    used to detect complete history rewrites.
    """
    
    chain_id: str = Field(..., description="Chain this anchor references")
    root_hash: str = Field(..., description="Root hash at time of anchoring")
    anchored_at: datetime = Field(..., description="When this anchor was created")
    anchor_type: str = Field(..., description="Type of anchor (git, notion, blockchain, etc.)")
    anchor_ref: str = Field(..., description="Reference to external anchor (commit hash, page ID, etc.)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional anchor metadata")
    
    @field_validator('root_hash')
    @classmethod
    def validate_hash_format(cls, v):
        """Validate hash is 64-character hex string."""
        if not isinstance(v, str) or len(v) != 64:
            raise ValueError("Hash must be 64-character hex string")
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("Hash must be valid hexadecimal")
        return v


class VerificationResult(BaseModel):
    """Result of audit chain verification.
    
    Contains comprehensive verification status, detected issues,
    and performance metrics.
    """
    
    ok: bool = Field(..., description="Whether verification passed")
    chain_id: str = Field(..., description="Chain that was verified")
    root_hash: Optional[str] = Field(None, description="Root hash of verified chain")
    tip_hash: Optional[str] = Field(None, description="Tip hash of verified chain")
    length: int = Field(0, description="Number of entries verified")
    breaks: List[Dict[str, Any]] = Field(default_factory=list, description="List of detected issues")
    coverage: Dict[str, Any] = Field(default_factory=dict, description="Verification coverage info")
    performance: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics")
    verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="When verification completed")
    
    def add_break(self, entry_index: int, issue_type: str, description: str, details: Optional[Dict[str, Any]] = None):
        """Add a detected issue to the breaks list."""
        break_info = {
            "entry_index": entry_index,
            "issue_type": issue_type,
            "description": description,
            "details": details or {}
        }
        self.breaks.append(break_info)
    
    def add_performance_metric(self, metric_name: str, value: Any):
        """Add a performance metric."""
        self.performance[metric_name] = value
