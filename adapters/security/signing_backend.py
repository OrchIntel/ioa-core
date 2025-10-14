"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

from __future__ import annotations

import base64
import logging
import os
from typing import Optional

from .signature_engine import SignatureEngine as DevSignatureEngine
from ..audit.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, get_circuit_breaker

logger = logging.getLogger(__name__)


class KmsSignatureEngine:
    """
    KMS-backed signature engine (stub implementation).

    Notes:
    - Uses AWS KMS if boto3 is available; otherwise raises at runtime when used.
    - Verification is best-effort and may require external PK retrieval; can be skipped via IOA_KMS_VERIFY_SKIP=1.
    """

    def __init__(self, key_id: str) -> None:
        self.key_id = key_id
        self._kms = None

        # Circuit breaker for KMS operations
        cb_config = CircuitBreakerConfig(
            failure_threshold=int(os.getenv('IOA_KMS_FAILURE_THRESHOLD', '3')),
            recovery_timeout=int(os.getenv('IOA_KMS_RECOVERY_TIMEOUT', '60')),
            success_threshold=int(os.getenv('IOA_KMS_SUCCESS_THRESHOLD', '2')),
            timeout=float(os.getenv('IOA_KMS_TIMEOUT', '15.0'))
        )
        self.circuit_breaker = get_circuit_breaker(f"kms-{key_id}", cb_config)

        try:
            import boto3  # type: ignore
            self._kms = boto3.client("kms")
            logger.info(f"KMS signature engine initialized for key {key_id}")
        except Exception as e:  # pragma: no cover - optional dependency
            logger.warning("KMS engine initialized without boto3: %s", e)
            self._kms = None

    def sign(self, data: bytes) -> bytes:
        """Sign data with circuit breaker protection."""
        if self._kms is None:
            raise RuntimeError("AWS KMS not available (missing boto3 or credentials)")

        def _kms_sign():
            resp = self._kms.sign(
                KeyId=self.key_id,
                Message=data,
                MessageType="RAW",
                SigningAlgorithm="RSASSA_PSS_SHA_256",
            )
            return resp["Signature"]

        return self.circuit_breaker.call(_kms_sign)

    def verify(self, data: bytes, signature: bytes) -> bool:
        """Verify signature with circuit breaker protection."""
        # Optionally skip verification in environments without PK infra
        if os.getenv("IOA_KMS_VERIFY_SKIP", "0") in ("1", "true", "TRUE"):
            logger.info("KMS verify skipped via IOA_KMS_VERIFY_SKIP")
            return True

        if self._kms is None:
            raise RuntimeError("AWS KMS not available for verification")

        def _kms_verify():
            resp = self._kms.verify(
                KeyId=self.key_id,
                Message=data,
                Signature=signature,
                MessageType="RAW",
                SigningAlgorithm="RSASSA_PSS_SHA_256",
            )
            return bool(resp.get("SignatureValid", False))

        try:
            return self.circuit_breaker.call(_kms_verify)
        except Exception as e:
            logger.warning("KMS verify failed: %s", e)
            return False


def get_signature_engine():
    """
    Factory for signature engines.

    Env:
      IOA_SIGNING_BACKEND: dev_rsa (default) | aws_kms
      IOA_KMS_KEY_ID: required when IOA_SIGNING_BACKEND=aws_kms
    """
    backend = os.getenv("IOA_SIGNING_BACKEND", "dev_rsa").lower()
    if backend == "aws_kms":
        key_id = os.getenv("IOA_KMS_KEY_ID")
        if not key_id:
            raise RuntimeError("IOA_KMS_KEY_ID must be set for aws_kms backend")
        logger.info("Using KMS signature backend (key_id=%s)", key_id)
        return KmsSignatureEngine(key_id)
    logger.info("Using dev RSA signature backend")
    return DevSignatureEngine()


