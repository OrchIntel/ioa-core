"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
IOA adapters.audit namespace.
"""


"""
IOA Audit Verification System

Provides immutable log verification capabilities for IOA Core's audit chains.
Includes hash chain validation, canonical JSON processing, and multi-backend storage support.
"""

from .verify import AuditVerifier
from .storage import AuditStorage, FileSystemStorage, S3Storage
from .canonical import canonicalize_json, compute_hash
from .models import AuditEntry, AuditManifest, AuditAnchor

__all__ = [
    "AuditVerifier",
    "AuditStorage", 
    "FileSystemStorage",
    "S3Storage",
    "canonicalize_json",
    "compute_hash",
    "AuditEntry",
    "AuditManifest", 
    "AuditAnchor"
]
