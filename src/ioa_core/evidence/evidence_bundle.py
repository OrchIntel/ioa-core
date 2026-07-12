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
import uuid
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
    model_provenance: List[Dict[str, Any]] = None
    evidence_chain_id: Optional[str] = None
    related_bundle_ids: List[str] = None
    signature: Optional[Union[str, Dict[str, str]]] = None
    signature_status: str = "unsigned"
    evidence_hash: str = ""

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()
        if self.metadata is None:
            self.metadata = {}
        if self.validations is None:
            self.validations = []
        if self.model_provenance is None:
            self.model_provenance = []
        if self.related_bundle_ids is None:
            self.related_bundle_ids = []
        if not self.evidence_chain_id:
            self.evidence_chain_id = f"chain-{uuid.uuid4().hex}"
        if not self.evidence_hash:
            self.evidence_hash = self._calculate_hash()

    def _calculate_hash(self) -> str:
        """Calculate SHA256 hash of the evidence bundle."""
        # Create a copy without the hash field for calculation
        bundle_data = asdict(self)
        bundle_data.pop("evidence_hash", None)
        bundle_data.pop("signature", None)
        bundle_data.pop("signature_status", None)

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

        self._invalidate_signature()
        self.validations.append(validation)
        self.validations_count = len(self.validations)
        self.evidence_hash = self._calculate_hash()

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the bundle."""
        self._invalidate_signature()
        self.metadata[key] = value
        self.evidence_hash = self._calculate_hash()

    def add_related_bundle(self, bundle_id: str) -> None:
        """Link another evidence bundle in the same cross-domain chain."""
        if bundle_id and bundle_id not in self.related_bundle_ids:
            self._invalidate_signature()
            self.related_bundle_ids.append(bundle_id)
            self.evidence_hash = self._calculate_hash()

    def add_model_provenance(self, provenance: Dict[str, Any]) -> None:
        """Add normalized model provenance metadata to the bundle."""
        if not isinstance(provenance, dict):
            raise EvidenceBundleError("Model provenance must be a dictionary")

        normalized = {
            "provider": provenance.get("provider", "unknown"),
            "model_name": provenance.get(
                "model_name",
                provenance.get("model", provenance.get("model_id", "unknown")),
            ),
            "model_id": provenance.get(
                "model_id",
                provenance.get("model_name", provenance.get("model", "unknown")),
            ),
            "model_version": provenance.get(
                "model_version", provenance.get("model_snapshot")
            ),
            "endpoint": provenance.get("endpoint", provenance.get("deployment_id")),
            "temperature": provenance.get("temperature"),
            "top_p": provenance.get("top_p"),
            "input_token_count": provenance.get(
                "input_token_count",
                provenance.get("prompt_tokens", provenance.get("input_tokens")),
            ),
            "output_token_count": provenance.get(
                "output_token_count",
                provenance.get("completion_tokens", provenance.get("output_tokens")),
            ),
            "total_token_count": provenance.get(
                "total_token_count",
                provenance.get("total_tokens"),
            ),
            "latency_ms": provenance.get("latency_ms"),
            "cost_estimate_usd": provenance.get("cost_estimate_usd"),
            "offline_mock": provenance.get(
                "offline_mock",
                provenance.get("simulated", provenance.get("offline")),
            ),
            "prompt_template_id": provenance.get("prompt_template_id"),
            "policy_version": provenance.get("policy_version"),
            "roundtable_role": provenance.get("roundtable_role"),
            "recorded_at": provenance.get(
                "recorded_at", datetime.now(timezone.utc).isoformat()
            ),
        }

        for key, value in provenance.items():
            normalized.setdefault(key, value)

        self._invalidate_signature()
        self.model_provenance.append(normalized)
        self.evidence_hash = self._calculate_hash()

    def _invalidate_signature(self) -> None:
        if self.signature is not None or self.signature_status == "signed":
            self.signature = None
            self.signature_status = "unsigned"

    def generate_signature(
        self,
        signer: str = "ioa-core",
        private_key_path: Optional[str] = None,
    ) -> Dict[str, str]:
        """Generate a real Ed25519 signature using an operator-provided key."""
        del signer  # Kept for source compatibility; key identity is in the envelope.
        from .signing import sign_bundle

        envelope = sign_bundle(self, private_key_path=private_key_path)
        self.signature = envelope
        self.signature_status = "signed"
        return envelope

    def to_dict(self) -> Dict[str, Any]:
        """Convert bundle to dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert bundle to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save_to_file(self, filepath: str) -> None:
        """Save bundle to JSON file."""
        with open(filepath, "w") as f:
            f.write(self.to_json())

    def verify_signature(self, public_key_path: Optional[str] = None) -> bool:
        """Verify a new signature, or classify a legacy checksum as unsigned."""
        if not self.signature:
            self.signature_status = "unsigned"
            return False
        if isinstance(self.signature, str) and self.signature.startswith("SIGv1:"):
            self.signature_status = "unsigned_legacy"
            return False
        if not isinstance(self.signature, dict) or not public_key_path:
            self.signature_status = "unverified"
            return False
        from .signing import load_public_key, verify_bundle

        try:
            verified = verify_bundle(self, load_public_key(public_key_path))
        except Exception:
            verified = False
        self.signature_status = "signed" if verified else "invalid"
        return verified

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceBundle":
        """Create EvidenceBundle from dictionary."""
        normalized = dict(data)
        signature = normalized.get("signature")
        if isinstance(signature, str) and signature.startswith("SIGv1:"):
            normalized["signature_status"] = "unsigned_legacy"
        elif isinstance(signature, dict):
            normalized["signature_status"] = "unverified"
        else:
            normalized["signature_status"] = "unsigned"
        return cls(**normalized)

    @classmethod
    def from_json(cls, json_str: str) -> "EvidenceBundle":
        """Create EvidenceBundle from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def from_file(cls, filepath: str) -> "EvidenceBundle":
        """Create EvidenceBundle from JSON file."""
        with open(filepath, "r") as f:
            return cls.from_json(f.read())
