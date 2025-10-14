"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.


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
from datetime import datetime, timezone
from typing import List, Tuple, Dict
import threading
import time
import os

logger = logging.getLogger(__name__)

class SignatureEngine:
    """
    Minimal RSA signing service for agent onboarding + attestations.
    Keys are ephemeral in-memory; persistence can be added by callers if desired.
    """
    def __init__(self, key_size: int = 2048, max_verify_ring: int = 3) -> None:
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
        self.public_key = self.private_key.public_key()
        self.key_created_at = datetime.now(timezone.utc)
        # Verification ring of previous public keys (most recent first)
        self._verify_ring: List[Tuple[bytes, any]] = []  # list of (kid, public_key)
        # Allow env override for ring size
        env_ring = os.getenv("IOA_VERIFY_RING_SIZE")
        self._max_verify_ring = max(1, int(env_ring)) if env_ring else max(1, max_verify_ring)
        self._kid_counter = 1
        self._current_kid = self._generate_kid()

        # Auto-rotation controls (dev only)
        self._rotation_enabled = False
        self._rotation_thread: threading.Thread | None = None
        self._rotation_interval_sec = float(os.getenv("IOA_DEV_ROTATE_INTERVAL_SEC", "0") or 0)
        if self._rotation_interval_sec > 0:
            self.start_auto_rotation(self._rotation_interval_sec)

    def sign(self, data: bytes) -> bytes:
        sig = self.private_key.sign(
            data,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )
        logger.info("signature_engine: signed %d bytes (kid=%s)", len(data), self._current_kid.decode())
        return sig

    def verify(self, data: bytes, signature: bytes) -> bool:
        # Try current key first
        try:
            self.public_key.verify(
                signature,
                data,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256(),
            )
            logger.info("signature_engine: verification OK (current key)")
            return True
        except Exception:
            pass

        # Try verification ring
        for kid, pub in self._verify_ring:
            try:
                pub.verify(
                    signature,
                    data,
                    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                    hashes.SHA256(),
                )
                logger.info("signature_engine: verification OK (ring kid=%s)", kid.decode())
                return True
            except Exception:
                continue

        logger.warning("signature_engine: verification failed (all keys)")
        return False

    def export_public_pem(self) -> bytes:
        return self.public_key.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)

    def export_key_id(self) -> bytes:
        """Export current key identifier (kid)."""
        return self._current_kid

    # --- Multi-signature helpers (dev-level) ---
    @staticmethod
    def multisig_sign(data: bytes, engines: List["SignatureEngine"]) -> Dict[str, str]:
        """Sign the same payload with multiple engines.

        Returns a dict mapping kid -> base64(signature).
        """
        import base64
        signatures: Dict[str, str] = {}
        for eng in engines:
            sig = eng.sign(data)
            signatures[eng.export_key_id().decode()] = base64.b64encode(sig).decode()
        return signatures

    @staticmethod
    def multisig_verify(data: bytes, signatures: Dict[str, str], engines: List["SignatureEngine"], m_required: int) -> bool:
        """Verify multi-signature with m-of-n threshold.

        - signatures: dict of kid -> base64(signature)
        - engines: verification engines (their verify rings will be used implicitly)
        - m_required: threshold m
        """
        import base64
        if m_required <= 0:
            return False
        ok = 0
        for eng in engines:
            kid = eng.export_key_id().decode()
            # Prefer current kid match; also try ring kids
            candidates: List[Tuple[str, bytes]] = []
            if kid in signatures:
                candidates.append((kid, base64.b64decode(signatures[kid])))
            # Try ring kids
            for rkid, _ in getattr(eng, "_verify_ring", []):
                rk = rkid.decode()
                if rk in signatures:
                    candidates.append((rk, base64.b64decode(signatures[rk])))

            # Verify any signature that matches this engine's keys
            for _, sig in candidates:
                if eng.verify(data, sig):
                    ok += 1
                    break

            if ok >= m_required:
                return True
        return False

    def rotate(self, key_size: int = 2048) -> None:
        """Rotate the signing key and add previous public key to the verify ring.

        Keeps up to _max_verify_ring previous public keys for verification.
        """
        try:
            # Add current public key to ring
            if self.public_key is not None:
                self._verify_ring.insert(0, (self._current_kid, self.public_key))
                self._verify_ring = self._verify_ring[: self._max_verify_ring]

            # Generate new keypair
            self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
            self.public_key = self.private_key.public_key()
            self.key_created_at = datetime.now(timezone.utc)
            self._kid_counter += 1
            self._current_kid = self._generate_kid()
            logger.info("signature_engine: rotated key (new kid=%s)", self._current_kid.decode())
        except Exception as e:
            logger.error("signature_engine: key rotation failed: %s", e)
            raise

    def _generate_kid(self) -> bytes:
        """Generate a deterministic key identifier based on public key fingerprint."""
        # Compute SHA-256 fingerprint of the public key DER and truncate
        try:
            pub_der = self.public_key.public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)
            import hashlib
            fp = hashlib.sha256(pub_der).hexdigest()[:12]
        except Exception:
            fp = "unknown"
        stamp = self.key_created_at.strftime("%Y%m%d")
        return f"DEV-K{self._kid_counter}-{stamp}-{fp}".encode()

    # Auto-rotation (dev convenience)
    def start_auto_rotation(self, interval_seconds: float) -> None:
        """Start background auto-rotation on a daemon thread.

        Controlled by IOA_DEV_ROTATE_INTERVAL_SEC; intended for development.
        """
        if interval_seconds <= 0:
            return
        if self._rotation_thread and self._rotation_thread.is_alive():
            return
        self._rotation_enabled = True
        self._rotation_interval_sec = interval_seconds

        def _loop():
            while self._rotation_enabled:
                try:
                    time.sleep(self._rotation_interval_sec)
                    self.rotate()
                except Exception as e:
                    logger.warning("signature_engine: auto-rotation error: %s", e)
                    # continue loop
                    continue

        self._rotation_thread = threading.Thread(target=_loop, daemon=True)
        self._rotation_thread.start()

    def stop_auto_rotation(self) -> None:
        self._rotation_enabled = False
        # No join since daemon thread should exit on its own

    def __del__(self):
        try:
            self.stop_auto_rotation()
        except Exception:
            pass
