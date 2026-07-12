# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""Offline Ed25519 signing helpers for evidence bundles."""

from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Union

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from ioa_core.audit.canonical import canonicalize_json, compute_hash


class EvidenceSigningError(ValueError):
    """Raised when an evidence signature cannot be created or verified."""


def _as_dict(bundle: Union[Mapping[str, Any], Any]) -> Dict[str, Any]:
    if is_dataclass(bundle):
        return asdict(bundle)
    if isinstance(bundle, Mapping):
        return dict(bundle)
    raise EvidenceSigningError("Evidence bundle must be a mapping or dataclass")


def unsigned_bundle_dict(bundle: Union[Mapping[str, Any], Any]) -> Dict[str, Any]:
    """Return the signed material without mutable signature presentation fields."""
    data = _as_dict(bundle)
    data.pop("signature", None)
    data.pop("signature_status", None)
    return data


def canonical_bundle_bytes(bundle: Union[Mapping[str, Any], Any]) -> bytes:
    """Return the exact canonical bytes covered by the Ed25519 signature."""
    return canonicalize_json(unsigned_bundle_dict(bundle)).encode("utf-8")


def canonical_bundle_hash(bundle: Union[Mapping[str, Any], Any]) -> str:
    return compute_hash(unsigned_bundle_dict(bundle))


def _load_private_key(
    private_key_path: Optional[Union[str, Path]] = None,
    private_key_pem: Optional[bytes] = None,
) -> Ed25519PrivateKey:
    path_value = private_key_path or os.getenv("IOA_EVIDENCE_PRIVATE_KEY_PATH")
    pem = private_key_pem
    if pem is None and path_value:
        pem = Path(path_value).read_bytes()
    if pem is None:
        encoded = os.getenv("IOA_EVIDENCE_PRIVATE_KEY_B64", "").strip()
        if encoded:
            try:
                pem = base64.b64decode(encoded, validate=True)
            except (ValueError, TypeError) as exc:
                raise EvidenceSigningError(
                    "IOA_EVIDENCE_PRIVATE_KEY_B64 is invalid"
                ) from exc
    if pem is None:
        raise EvidenceSigningError(
            "No evidence signing key configured; set IOA_EVIDENCE_PRIVATE_KEY_PATH "
            "or IOA_EVIDENCE_PRIVATE_KEY_B64"
        )
    try:
        key = serialization.load_pem_private_key(pem, password=None)
    except (ValueError, TypeError) as exc:
        raise EvidenceSigningError("Unable to load evidence signing key") from exc
    if not isinstance(key, Ed25519PrivateKey):
        raise EvidenceSigningError("Evidence signing key must be Ed25519")
    return key


def load_public_key(public_key_path: Union[str, Path]) -> Ed25519PublicKey:
    try:
        key = serialization.load_pem_public_key(Path(public_key_path).read_bytes())
    except (OSError, ValueError, TypeError) as exc:
        raise EvidenceSigningError("Unable to load evidence public key") from exc
    if not isinstance(key, Ed25519PublicKey):
        raise EvidenceSigningError("Evidence public key must be Ed25519")
    return key


def public_key_id(public_key: Ed25519PublicKey) -> str:
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return hashlib.sha256(raw).hexdigest()[:16]


def sign_bundle(
    bundle: Union[Mapping[str, Any], Any],
    *,
    private_key_path: Optional[Union[str, Path]] = None,
    private_key_pem: Optional[bytes] = None,
    signed_at: Optional[str] = None,
) -> Dict[str, str]:
    """Sign a bundle using an operator-provided Ed25519 private key."""
    key = _load_private_key(private_key_path, private_key_pem)
    canonical = canonical_bundle_bytes(bundle)
    return {
        "sig_version": "ed25519-v1",
        "algo": "Ed25519",
        "public_key_id": public_key_id(key.public_key()),
        "signature": base64.b64encode(key.sign(canonical)).decode("ascii"),
        "canonical_hash": hashlib.sha256(canonical).hexdigest(),
        "signed_at": signed_at or datetime.now(timezone.utc).isoformat(),
    }


def verify_bundle(
    bundle: Union[Mapping[str, Any], Any], public_key: Ed25519PublicKey
) -> bool:
    """Verify an Ed25519 evidence envelope entirely offline."""
    data = _as_dict(bundle)
    envelope = data.get("signature")
    if not isinstance(envelope, Mapping):
        return False
    if envelope.get("sig_version") != "ed25519-v1" or envelope.get("algo") != "Ed25519":
        return False
    if envelope.get("public_key_id") != public_key_id(public_key):
        return False
    canonical = canonical_bundle_bytes(data)
    if envelope.get("canonical_hash") != hashlib.sha256(canonical).hexdigest():
        return False
    try:
        signature = base64.b64decode(str(envelope.get("signature", "")), validate=True)
        public_key.verify(signature, canonical)
    except (ValueError, TypeError):
        return False
    return True
