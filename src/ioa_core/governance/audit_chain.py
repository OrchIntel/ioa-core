# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.



IOA Governance: Immutable Audit Chain

Provides append-only, hash-chained JSONL audit logging with schema validation.
Each entry includes prev_hash and content hash to create an immutable chain.
Entries are validated against AUDIT_SCHEMA before persistence.
"""
"""Audit Chain module."""


from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import asdict, dataclass
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from jsonschema import validate
except Exception as e:
    raise ImportError("jsonschema is required for audit_chain.py") from e

logger = logging.getLogger(__name__)

# PATCH: Cursor-2025-08-19 Added environment variable configuration for audit log path
AUDIT_LOG_PATH = os.environ.get("IOA_AUDIT_LOG", "./logs/audit_chain.jsonl")
# PATCH: Cursor-2025-08-19 Add rotation size configuration (bytes); default 10MB
AUDIT_ROTATE_BYTES = int(
    os.environ.get("IOA_AUDIT_ROTATE_BYTES", str(10 * 1024 * 1024))
)
# PATCH: Cursor-2025-10-08 Add batching and backpressure configuration
AUDIT_BATCH_SIZE = int(os.environ.get("IOA_AUDIT_BATCH_SIZE", "10"))
AUDIT_BACKPRESSURE_ENABLED = os.environ.get("IOA_AUDIT_BACKPRESSURE", "1") in ("1", "true", "TRUE")
AUDIT_BACKPRESSURE_THRESHOLD = int(os.environ.get("IOA_AUDIT_BACKPRESSURE_THRESHOLD", "100"))

AUDIT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "timestamp": {"type": "string", "format": "date-time"},
        "event": {"type": "string"},
        "data": {"type": "object"},
        "prev_hash": {"type": "string"},
        "hash": {"type": "string"},
        # Trusted timestamping evidence reference
        "tsa": {"type": "object"},
        # Replay protection fields (not strictly required for backward-compat)
        "nonce": {"type": "string"},
        "seq": {"type": "integer"},
    },
    "required": ["timestamp", "event", "data", "prev_hash", "hash"],
}


@dataclass
class AuditEntry:
    timestamp: str
    event: str
    data: Dict[str, Any]
    prev_hash: str
    hash: Optional[str] = None
    nonce: Optional[str] = None
    seq: Optional[int] = None

    def materialize(self) -> Dict[str, Any]:
        payload = asdict(self)
        # Compute hash deterministically ignoring None hash in input
        payload_no_hash = {k: v for k, v in payload.items() if k != "hash"}
        # PATCH: Cursor-2025-09-10 Use canonical JSON hashing for audit verification compatibility
        from ioa_core.audit.canonical import compute_hash

        digest = compute_hash(payload_no_hash)
        payload["hash"] = digest
        return payload


class AuditChain:
    """
    Append-only, hash-chained JSONL audit log.
    - Each entry includes prev_hash and content hash to create an immutable chain.
    - Entries are validated against AUDIT_SCHEMA before persistence.
    - Supports batching and backpressure for high-throughput scenarios.
    """

    def __init__(
        self, log_path: str = AUDIT_LOG_PATH, rotate_bytes: int = AUDIT_ROTATE_BYTES
    ) -> None:
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.prev_hash = self._recover_tail_hash() or ("0" * 64)
        self.rotate_bytes = rotate_bytes

        # PATCH: Cursor-2025-10-08 Add batching and backpressure support
        self._batch_size = AUDIT_BATCH_SIZE
        self._backpressure_enabled = AUDIT_BACKPRESSURE_ENABLED
        self._backpressure_threshold = AUDIT_BACKPRESSURE_THRESHOLD
        self._pending_batch: List[Dict[str, Any]] = []
        self._batch_lock = False  # Simple mutex for batch operations

        # Replay protection controls
        self._require_nonce = os.environ.get("IOA_AUDIT_REQUIRE_NONCE", "1") in ("1", "true", "TRUE")
        self._strict_replay_check = os.environ.get("IOA_AUDIT_REPLAY_STRICT", "0") in ("1", "true", "TRUE")
        self._nonce_index_path = self.log_path.with_suffix(".nonce")
        self._seen_nonces: set[str] = set()
        self._seq_counter = self._recover_next_sequence()
        self._load_nonce_index()

    # PATCH: Cursor-2025-10-08 Backpressure check for high-throughput scenarios
    def _should_apply_backpressure(self) -> bool:
        """Check if backpressure should be applied based on pending batch size."""
        if not self._backpressure_enabled:
            return False
        return len(self._pending_batch) >= self._backpressure_threshold

    def _flush_batch_if_needed(self) -> None:
        """Flush batch if it reaches the configured size."""
        if len(self._pending_batch) >= self._batch_size:
            self._flush_pending_batch()

    def _flush_pending_batch(self) -> None:
        """Flush all pending batch entries to disk."""
        if self._batch_lock or not self._pending_batch:
            return

        self._batch_lock = True
        try:
            # Rotate if needed
            self._maybe_rotate()

            with self.log_path.open("a", encoding="utf-8") as f:
                for entry in self._pending_batch:
                    f.write(json.dumps(entry, sort_keys=True) + "\n")
                    self.prev_hash = entry["hash"]

            batch_count = len(self._pending_batch)
            self._pending_batch.clear()
            logger.info("audit_chain: flushed batch of %d entries", batch_count)
        finally:
            self._batch_lock = False

    def flush(self) -> None:
        """Force flush any pending batched entries to disk."""
        self._flush_pending_batch()

    def __del__(self):
        """Ensure pending batches are flushed on destruction."""
        try:
            self.flush()
        except Exception:
            pass  # Ignore errors during cleanup

    # PATCH: Cursor-2025-08-19 Implement sensitive data redaction
    def _redact_value(self, value: Any) -> Any:
        """Redact sensitive scalar values such as tokens and emails."""
        try:
            if isinstance(value, str):
                # Mask common API key/token patterns
                lowered = value.lower()
                if any(
                    k in lowered
                    for k in [
                        "sk-",
                        "api_key",
                        "apikey",
                        "token",
                        "authorization",
                        "bearer ",
                    ]
                ):
                    return "[REDACTED]"
                # Simple email pattern
                if "@" in value and "." in value:
                    return "[REDACTED]" if " " not in value else value
            return value
        except Exception:
            return "[REDACTED]"

    def _redact(self, data: Any) -> Any:
        """Recursively redact sensitive fields in mappings and sequences."""
        try:
            if isinstance(data, dict):
                redacted: Dict[str, Any] = {}
                for k, v in data.items():
                    key_l = str(k).lower()
                    if any(
                        s in key_l
                        for s in [
                            "api_key",
                            "apikey",
                            "authorization",
                            "access_token",
                            "secret",
                            "email",
                            "password",
                            "token",
                        ]
                    ):
                        redacted[k] = "[REDACTED]"
                    else:
                        redacted[k] = self._redact(v)
                return redacted
            if isinstance(data, list):
                return [self._redact(v) for v in data]
            return self._redact_value(data)
        except Exception:
            return "[REDACTED]"

    # PATCH: Cursor-2025-08-19 Implement size-based rotation with SHA-256 suffix
    def _maybe_rotate(self) -> None:
        try:
            if not self.log_path.exists():
                return
            size = self.log_path.stat().st_size
            if size < self.rotate_bytes:
                return
            # Compute checksum
            sha256 = hashlib.sha256()
            with self.log_path.open("rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            digest = sha256.hexdigest()
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            rotated_name = (
                f"{self.log_path.stem}-{stamp}-{digest[:12]}{self.log_path.suffix}"
            )
            rotated_path = self.log_path.with_name(rotated_name)
            os.replace(self.log_path, rotated_path)
            # Reset current log file
            self.log_path.touch()
            self.prev_hash = "0" * 64
            logger.info("audit_chain: rotated log to %s (size=%d)", rotated_path, size)
        except Exception as e:
            logger.error("audit_chain: rotation failed: %s", e)

    def _recover_tail_hash(self) -> Optional[str]:
        if not self.log_path.exists():
            return None
        last = None
        with self.log_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    last = line
        if not last:
            return None
        try:
            payload = json.loads(last)
            return payload.get("hash")
        except Exception:
            logger.warning("Failed to recover tail hash; starting fresh.")
            return None

    def _recover_next_sequence(self) -> int:
        """Recover the next sequence number based on existing log entries."""
        try:
            if not self.log_path.exists():
                return 1
            count = 0
            with self.log_path.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        count += 1
            return count + 1
        except Exception as e:
            logger.warning(f"Failed to recover sequence counter: {e}")
            return 1

    def _load_nonce_index(self) -> None:
        """Load previously seen nonces from index file if present."""
        try:
            if self._nonce_index_path.exists():
                with self._nonce_index_path.open("r", encoding="utf-8") as f:
                    for line in f:
                        val = line.strip()
                        if val:
                            self._seen_nonces.add(val)
        except Exception as e:
            logger.warning(f"Failed to load nonce index: {e}")

    def _persist_nonce(self, nonce: str) -> None:
        try:
            with self._nonce_index_path.open("a", encoding="utf-8") as f:
                f.write(nonce + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist nonce index: {e}")

    def _nonce_already_used(self, nonce: str) -> bool:
        if nonce in self._seen_nonces:
            return True
        if self._strict_replay_check and self.log_path.exists():
            try:
                with self.log_path.open("r", encoding="utf-8") as f:
                    for line in f:
                        if nonce in line:
                            return True
            except Exception:
                # Fall through to best-effort detection
                pass
        return False

    def log(self, event: str, data: Dict[str, Any]) -> Dict[str, Any]:
        # PATCH: Cursor-2025-10-08 Check backpressure before logging
        if self._should_apply_backpressure():
            raise RuntimeError(f"Audit backpressure triggered (pending={len(self._pending_batch)}, threshold={self._backpressure_threshold})")

        # Redact sensitive values before logging
        safe_data = self._redact(data)

        # Operator identity tracking (optional fields)
        operator_id = os.environ.get("IOA_OPERATOR_ID")
        operator_role = os.environ.get("IOA_OPERATOR_ROLE")
        if operator_id and "operator" not in safe_data:
            safe_data["operator"] = {
                "id": operator_id,
                "role": operator_role or "unknown",
            }

        # Replay protection fields
        nonce = safe_data.get("nonce") or uuid.uuid4().hex
        if self._require_nonce and self._nonce_already_used(nonce):
            raise RuntimeError("Replay detected: nonce already used")

        seq = safe_data.get("seq") or self._seq_counter

        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event=event,
            data=safe_data,
            prev_hash=self.prev_hash,
            nonce=nonce,
            seq=seq,
        ).materialize()
        validate(entry, AUDIT_SCHEMA)

        # Optional TSA integration: timestamp the entry hash
        try:
            tsa_url = os.getenv("IOA_TSA_URL")
            if tsa_url:
                # Compute hex digest of entry hash for TSA request
                digest_hex = entry["hash"]
                # Try to import via adapters path; fallback to file-based import
                import sys
                from pathlib import Path as _P
                core_root = _P(__file__).resolve().parents[4]  # .../ioa-core-internal
                if str(core_root) not in sys.path:
                    sys.path.insert(0, str(core_root))
                from adapters.audit.timestamping import request_timestamp  # type: ignore

                ts_evd = request_timestamp(digest_hex, digest_alg="sha256")
                entry["tsa"] = {
                    "tsr_path": ts_evd.tsr_path,
                    "tsa_url": ts_evd.tsa_url,
                    "tsr_sha256": ts_evd.tsr_sha256,
                    "created_at": ts_evd.created_at,
                }
        except Exception as e:
            logger.warning(f"audit_chain: TSA timestamping failed: {e}")

        # PATCH: Cursor-2025-10-08 Add to batch instead of immediate write
        self._pending_batch.append(entry)
        self._flush_batch_if_needed()

        # Update prev_hash for next entry
        self.prev_hash = entry["hash"]
        # Update replay protection state
        self._seen_nonces.add(nonce)
        self._persist_nonce(nonce)
        self._seq_counter = seq + 1
        logger.info("audit_chain: batched %s (pending=%d)", self.prev_hash, len(self._pending_batch))
        return entry

    def log_sustainability_event(
        self, event: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Log sustainability-specific events with enhanced evidence fields.

        PATCH: Cursor-2025-01-06 DISPATCH-GOV-20250906-SUSTAINABILITY
        Enhanced audit logging for sustainability compliance tracking with graduated responses.

        Args:
            event: Event type (e.g., "sustainability_check", "energy_budget_exceeded")
            data: Event data including sustainability evidence fields

        Returns:
            Audit entry with sustainability evidence
        """
        # Ensure enhanced sustainability evidence fields are present
        sustainability_evidence = {
            "token_count": data.get("token_count", 0),
            "model_name": data.get("model_name", "default"),
            "estimate_kwh_per_100k": data.get("estimate_kwh_per_100k", 0.0),
            "budget_kwh_per_100k": data.get("budget_kwh_per_100k", 1.0),
            "utilization": data.get("utilization", 0.0),
            "threshold_hit": data.get("threshold_hit", "none"),
            "override_used": data.get("override_used", False),
            "jurisdiction_applied": data.get("jurisdiction_applied", "default"),
            "delay_ms": data.get("delay_ms", 0),
            "enforcement_mode": data.get("enforcement_mode", "graduated"),
            # Legacy fields for backward compatibility
            "sustainability_score": data.get("sustainability_score", 0.0),
            "energy_estimate": data.get("energy_estimate", 0.0),
            "budget_cap_kwh_per_100k": data.get("budget_cap_kwh_per_100k", 1.0),
            "applied_jurisdiction": data.get("applied_jurisdiction", "default"),
        }

        # Merge with existing data
        enhanced_data = {**data, **sustainability_evidence}

        return self.log(event, enhanced_data)


# PATCH: Cursor-2025-08-19 Added module-level singleton for integration wiring
_audit_chain_instance: Optional[AuditChain] = None


def get_audit_chain() -> AuditChain:
    """Get the singleton AuditChain instance for this process."""
    global _audit_chain_instance
    if _audit_chain_instance is None:
        _audit_chain_instance = AuditChain()
    return _audit_chain_instance
