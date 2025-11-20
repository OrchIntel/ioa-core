# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""
Canonical Evidence Bundle Implementation

Provides standardized evidence bundle generation for compliance and audit
requirements across all IOA systems.
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict


class EvidenceBundleError(Exception):
    """Base exception for evidence bundle operations."""
    pass


@dataclass
class EvidenceBundle:
    """
    Canonical evidence bundle for compliance and audit requirements.
    
    Provides standardized evidence generation with cryptographic signatures
    and audit trail capabilities across all IOA systems.
    """
    
    bundle_id: str
    version: str = "1.0.0"
    framework: str = "IOA_7LAWS"
    generated_at: str = ""
    validations_count: int = 0
    metadata: Dict[str, Any] = None
    validations: List[Dict[str, Any]] = None
    signature: Optional[str] = None
    evidence_hash: str = ""
    
    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()
        if self.metadata is None:
            self.metadata = {}
        if self.validations is None:
            self.validations = []
        if not self.evidence_hash:
            self.evidence_hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """Calculate SHA256 hash of the evidence bundle."""
        # Create a copy without the hash field for calculation
        bundle_data = asdict(self)
        bundle_data.pop('evidence_hash', None)
        
        # Sort keys for consistent hashing
        bundle_json = json.dumps(bundle_data, sort_keys=True)
        return hashlib.sha256(bundle_json.encode()).hexdigest()
    
    def add_validation(self, validation: Dict[str, Any]) -> None:
        """Add a validation result to the bundle."""
        if not isinstance(validation, dict):
            raise EvidenceBundleError("Validation must be a dictionary")
        
        # Ensure required fields
        if "validation_id" not in validation:
            validation["validation_id"] = f"val_{len(self.validations) + 1}"
        if "timestamp" not in validation:
            validation["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        self.validations.append(validation)
        self.validations_count = len(self.validations)
        self.evidence_hash = self._calculate_hash()
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the bundle."""
        self.metadata[key] = value
        self.evidence_hash = self._calculate_hash()
    
    def generate_signature(self, signer: str = "ioa-core") -> str:
        """Generate a cryptographic signature for the bundle."""
        sig_payload = {
            "version": "SIGv1",
            "algorithm": "SHA256",
            "evidence_hash": self.evidence_hash,
            "signer": signer,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        sig_data = json.dumps(sig_payload, sort_keys=True).encode()
        signature = f"SIGv1:{hashlib.sha256(sig_data).hexdigest()}"
        self.signature = signature
        
        return signature
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert bundle to dictionary."""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert bundle to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def save_to_file(self, filepath: str) -> None:
        """Save bundle to JSON file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())
    
    def verify_signature(self) -> bool:
        """Verify the bundle's signature."""
        if not self.signature:
            return False
        
        try:
            # Extract signature components
            if not self.signature.startswith("SIGv1:"):
                return False
            
            sig_hash = self.signature[6:]  # Remove "SIGv1:" prefix
            
            # Recreate signature payload
            sig_payload = {
                "version": "SIGv1",
                "algorithm": "SHA256", 
                "evidence_hash": self.evidence_hash,
                "signer": "ioa-core",  # This should be stored in metadata
                "timestamp": self.generated_at
            }
            
            # Calculate expected hash
            sig_data = json.dumps(sig_payload, sort_keys=True).encode()
            expected_hash = hashlib.sha256(sig_data).hexdigest()
            
            return sig_hash == expected_hash
            
        except Exception:
            return False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvidenceBundle':
        """Create EvidenceBundle from dictionary."""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'EvidenceBundle':
        """Create EvidenceBundle from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def from_file(cls, filepath: str) -> 'EvidenceBundle':
        """Create EvidenceBundle from JSON file."""
        with open(filepath, 'r') as f:
            return cls.from_json(f.read())
