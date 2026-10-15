# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""
IOA Core Evidence Module

Provides canonical evidence bundle generation and management for compliance
and audit requirements across all IOA systems.
"""

from .evidence_bundle import EvidenceBundle, EvidenceBundleError
from .exporters import EvidenceExporter
from .sandbox_receipt import (
    SANDBOX_NOTICE,
    SANDBOX_RECEIPT_FRAMEWORK,
    SandboxReceiptError,
    check_sandbox_receipt,
    create_sandbox_receipt,
    verify_sandbox_receipt,
    verify_sandbox_receipt_from_registry,
)
from .session_receipt import (
    SessionReceiptError,
    create_session_receipt,
    receipt_json_bytes,
    verify_session_receipt,
    verify_session_receipt_from_registry,
)
from .signing import EvidenceSigningError, load_public_key, sign_bundle, verify_bundle

__all__ = [
    "EvidenceBundle",
    "EvidenceBundleError",
    "EvidenceExporter",
    "EvidenceSigningError",
    "SANDBOX_NOTICE",
    "SANDBOX_RECEIPT_FRAMEWORK",
    "SandboxReceiptError",
    "SessionReceiptError",
    "check_sandbox_receipt",
    "create_sandbox_receipt",
    "create_session_receipt",
    "load_public_key",
    "receipt_json_bytes",
    "sign_bundle",
    "verify_bundle",
    "verify_sandbox_receipt",
    "verify_sandbox_receipt_from_registry",
    "verify_session_receipt",
    "verify_session_receipt_from_registry",
]
