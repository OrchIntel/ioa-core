""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
IOA Security: Signature Engine

Provides minimal RSA signing service for agent onboarding and attestations.
Keys are ephemeral in-memory; persistence can be added by callers if desired.
"""

from __future__ import annotations

import logging

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

logger = logging.getLogger(__name__)

class SignatureEngine:
    """
    Minimal RSA signing service for agent onboarding + attestations.
    Keys are ephemeral in-memory; persistence can be added by callers if desired.
    """
    def __init__(self, key_size: int = 2048) -> None:
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
        self.public_key = self.private_key.public_key()

    def sign(self, data: bytes) -> bytes:
        sig = self.private_key.sign(
            data,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )
        logger.info("signature_engine: signed %d bytes", len(data))
        return sig

    def verify(self, data: bytes, signature: bytes) -> bool:
        try:
            self.public_key.verify(
                signature,
                data,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256(),
            )
            logger.info("signature_engine: verification OK")
            return True
        except Exception as e:
            logger.warning("signature_engine: verification failed: %s", e)
            return False

    def export_public_pem(self) -> bytes:
        return self.public_key.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
