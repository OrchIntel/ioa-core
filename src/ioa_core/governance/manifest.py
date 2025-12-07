# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""IOA Core Governance Manifest

System Laws manifest loading and verification.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import base64

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding
    from cryptography.exceptions import InvalidSignature
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    logging.getLogger(__name__).warning("Cryptography library not available - signature verification disabled")

from .system_laws import (
    SystemIntegrityError, SignatureVerificationError, SystemLawsError
)

logger = logging.getLogger(__name__)

# Global cache for loaded manifest
_manifest_cache: Optional[Dict[str, Any]] = None
_manifest_loaded_at: Optional[datetime] = None
_manifest_instance: Optional["SystemLaws"] = None  # Reusable instance cache


class SystemLaws:
    """System Laws manifest with validation and enforcement capabilities."""
    
    def __init__(self, manifest_data: Dict[str, Any]):
        self.version = manifest_data.get("version")
        self.laws = manifest_data.get("laws", [])
        self.policy = manifest_data.get("policy", {})
        self.signature = manifest_data.get("signature", {})
        self.metadata = manifest_data.get("metadata", {})
        # Provide a manifest identifier for integrity checks
        self.manifest_id = self.metadata.get("id", self.version or "unknown")
        
        # Create law lookup
        self._laws_by_id = {law["id"]: law for law in self.laws}
        self._laws_by_name = {law["name"]: law for law in self.laws}
        
        # Policy configuration
        self.conflict_resolution = self.policy.get("conflict_resolution", [])
        self.jurisdiction = self.policy.get("jurisdiction", {})
        self.fairness = self.policy.get("fairness", {})
    
    def get_law(self, law_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific law by ID."""
        return self._laws_by_id.get(law_id)
    
    def get_law_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific law by name."""
        return self._laws_by_name.get(name)
    
    def is_critical_law(self, law_id: str) -> bool:
        """Check if a law has critical enforcement level."""
        law = self.get_law(law_id)
        return law is not None and law.get("enforcement") == "critical"
    
    def get_conflict_resolution_order(self) -> list:
        """Get the ordered list of laws for conflict resolution."""
        return self.conflict_resolution.copy()
    
    def get_fairness_threshold(self) -> float:
        """Get the fairness threshold for bias detection."""
        return self.fairness.get("threshold", 0.2)
    
    def get_jurisdiction_affinity(self) -> list:
        """Get the list of supported jurisdictions."""
        return self.jurisdiction.get("affinity", ["global"])
    
    def validate_manifest_structure(self) -> bool:
        """Validate the manifest structure against schema."""
        # Check that all required fields exist and have meaningful values
        if not self.manifest_id:
            return False
        if not self.laws:
            return False
        if not self.policy:
            return False
        if not self.signature:
            return False
        if not self.metadata:
            return False
        return True


def _get_default_key_path() -> Path:
    """Get the default path for the development public key."""
    current_dir = Path(__file__).parent
    return current_dir / "signing_keys" / "dev_public_key.pem"


def _load_public_key(key_path: Optional[str] = None) -> Any:
    """Load the public key for signature verification."""
    if not CRYPTOGRAPHY_AVAILABLE:
        raise SignatureVerificationError(
            "Cryptography library not available for signature verification"
        )
    
    if key_path is None:
        key_path = os.getenv("IOA_LAWS_KEY_PATH", str(_get_default_key_path()))
    
    key_path = Path(key_path)
    if not key_path.exists():
        raise SignatureVerificationError(f"Public key not found: {key_path}")
    
    try:
        with open(key_path, "rb") as f:
            key_data = f.read()
        
        # Try to load as RSA public key first
        try:
            return serialization.load_pem_public_key(key_data)
        except ValueError:
            # Try as ECDSA public key
            return serialization.load_pem_public_key(key_data)
            
    except Exception as e:
        raise SignatureVerificationError(f"Failed to load public key: {e}")


def verify_signature(manifest_data: Dict[str, Any], key_path: Optional[str] = None) -> bool:
    """Verify the signature of the System Laws manifest."""
    if not CRYPTOGRAPHY_AVAILABLE:
        logger.warning("Cryptography not available - skipping signature verification")
        return True
    
    signature_info = manifest_data.get("signature", {})
    if not signature_info:
        raise SignatureVerificationError("No signature found in manifest")
    
    # Remove signature for verification
    manifest_copy = manifest_data.copy()
    signature_value = manifest_copy.pop("signature")
    
    # Create canonical JSON string
    manifest_str = json.dumps(manifest_copy, sort_keys=True, separators=(',', ':'))
    
    try:
        public_key = _load_public_key(key_path)
        signature_alg = signature_info.get("alg", "RS256")
        signature_data = base64.b64decode(signature_info.get("value", ""))
        
        if signature_alg == "RS256":
            if not isinstance(public_key, rsa.RSAPublicKey):
                raise SignatureVerificationError("RSA key required for RS256 algorithm")
            
            public_key.verify(
                signature_data,
                manifest_str.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
        elif signature_alg == "ES256":
            if not isinstance(public_key, ec.EllipticCurvePublicKey):
                raise SignatureVerificationError("ECDSA key required for ES256 algorithm")
            
            public_key.verify(
                signature_data,
                manifest_str.encode('utf-8'),
                hashes.SHA256()
            )
        else:
            raise SignatureVerificationError(f"Unsupported signature algorithm: {signature_alg}")
        
        logger.info(f"Signature verification successful using {signature_alg}")
        return True
        
    except InvalidSignature:
        raise SignatureVerificationError("Signature verification failed")
    except Exception as e:
        raise SignatureVerificationError(f"Signature verification error: {e}")


def load_manifest(manifest_path: Optional[str] = None, 
                  verify_signature_flag: bool = True,
                  key_path: Optional[str] = None) -> SystemLaws:
    """Load and validate the System Laws manifest."""
    global _manifest_cache, _manifest_loaded_at
    
    if manifest_path is None:
        current_dir = Path(__file__).parent
        manifest_path = current_dir / "system_laws.json"
    
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise SystemIntegrityError(f"System Laws manifest not found: {manifest_path}")
    
    try:
        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)
        
        # Validate structure
        if not all(field in manifest_data for field in ["version", "laws", "policy", "signature", "metadata"]):
            raise SystemIntegrityError("Invalid manifest structure")
        
        # Verify signature if requested
        if verify_signature_flag:
            if not verify_signature(manifest_data, key_path):
                raise SystemIntegrityError("Manifest signature verification failed")
        
        # Create SystemLaws instance
        system_laws = SystemLaws(manifest_data)
        
        # Validate manifest
        if not system_laws.validate_manifest_structure():
            raise SystemIntegrityError("Manifest validation failed")
        
        # Check expiration
        expires_str = manifest_data.get("metadata", {}).get("expires")
        if expires_str:
            try:
                expires = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                if datetime.now(timezone.utc) > expires:
                    # PATCH: Cursor-2025-09-16 DISPATCH-EXEC-20250916-WHITEPAPER-VALIDATION-PATCH+EXT
                    # Expired manifests must raise SystemIntegrityError instead of logging warnings
                    raise SystemIntegrityError("System Laws manifest has expired", manifest_path=str(manifest_path))
            except ValueError:
                logger.warning("Could not parse manifest expiration date")
        
        # Cache the manifest (data and reusable instance)
        _manifest_cache = manifest_data
        _manifest_loaded_at = datetime.now(timezone.utc)
        # Reuse the same SystemLaws instance for callers to avoid re-instantiation
        global _manifest_instance
        _manifest_instance = system_laws
        
        logger.info(f"System Laws manifest loaded successfully: {manifest_path}")
        return system_laws
        
    except json.JSONDecodeError as e:
        raise SystemIntegrityError(f"Invalid JSON in manifest: {e}")
    except Exception as e:
        if isinstance(e, SystemLawsError):
            raise
        raise SystemIntegrityError(f"Failed to load manifest: {e}")


def get_laws() -> SystemLaws:
    """Get the cached System Laws manifest, loading if necessary."""
    global _manifest_cache, _manifest_loaded_at, _manifest_instance
    
    if _manifest_cache is None or _manifest_instance is None:
        # For development, disable signature verification
        return load_manifest(verify_signature_flag=False)
    
    # Check if cache is still valid (reload every hour)
    if _manifest_loaded_at and (datetime.now(timezone.utc) - _manifest_loaded_at).total_seconds() > 3600:
        logger.info("Reloading System Laws manifest (cache expired)")
        return load_manifest(verify_signature_flag=False)
    
    # Return the cached instance to ensure reuse
    return _manifest_instance


def reload_laws() -> SystemLaws:
    """Force reload of the System Laws manifest."""
    global _manifest_cache, _manifest_loaded_at, _manifest_instance
    _manifest_cache = None
    _manifest_loaded_at = None
    _manifest_instance = None
    return load_manifest()
