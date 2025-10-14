"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.


"""
IOA Governance: Immutable Audit Chain

Provides append-only, hash-chained JSONL audit logging with schema validation.
Each entry includes prev_hash and content hash to create an immutable chain.
Entries are validated against AUDIT_SCHEMA before persistence.
"""

from __future__ import annotations

import json
import hashlib
import logging
import os
from dataclasses import dataclass, asdict
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
AUDIT_ROTATE_BYTES = int(os.environ.get("IOA_AUDIT_ROTATE_BYTES", str(10 * 1024 * 1024)))

AUDIT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "timestamp": {"type": "string", "format": "date-time"},
        "event": {"type": "string"},
        "data": {"type": "object"},
        "prev_hash": {"type": "string"},
        "hash": {"type": "string"}
    },
    "required": ["timestamp", "event", "data", "prev_hash", "hash"]
}

@dataclass
class AuditEntry:
    timestamp: str
    event: str
    data: Dict[str, Any]
    prev_hash: str
    hash: Optional[str] = None

    def materialize(self) -> Dict[str, Any]:
        payload = asdict(self)
        # Compute hash deterministically ignoring None hash in input
        payload_no_hash = {k: v for k, v in payload.items() if k != "hash"}
        # PATCH: Cursor-2025-09-10 Use canonical JSON hashing for audit verification compatibility
        from adapters.audit.canonical import canonicalize_json, compute_hash
        digest = compute_hash(payload_no_hash)
        payload["hash"] = digest
        return payload

class AuditChain:
    """
    Append-only, hash-chained JSONL audit log.
    - Each entry includes prev_hash and content hash to create an immutable chain.
    - Entries are validated against AUDIT_SCHEMA before persistence.
    """
    def __init__(self, log_path: str = AUDIT_LOG_PATH, rotate_bytes: int = AUDIT_ROTATE_BYTES) -> None:
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.prev_hash = self._recover_tail_hash() or ("0" * 64)
        self.rotate_bytes = rotate_bytes

    # PATCH: Cursor-2025-08-19 Implement sensitive data redaction
    def _redact_value(self, value: Any) -> Any:
        """Redact sensitive scalar values such as tokens and emails."""
        try:
            if isinstance(value, str):
                # Mask common API key/token patterns
                lowered = value.lower()
                if any(k in lowered for k in ["sk-", "api_key", "apikey", "token", "authorization", "bearer "]):
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
                    if any(s in key_l for s in ["api_key", "apikey", "authorization", "access_token", "secret", "email", "password", "token"]):
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
            rotated_name = f"{self.log_path.stem}-{stamp}-{digest[:12]}{self.log_path.suffix}"
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

    def log(self, event: str, data: Dict[str, Any]) -> Dict[str, Any]:
        # Redact sensitive values before logging
        safe_data = self._redact(data)
        # Rotate if needed
        self._maybe_rotate()
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event=event,
            data=safe_data,
            prev_hash=self.prev_hash
        ).materialize()
        validate(entry, AUDIT_SCHEMA)
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")
        self.prev_hash = entry["hash"]
        logger.info("audit_chain: appended %s", self.prev_hash)
        return entry
    
    def log_sustainability_event(self, event: str, data: Dict[str, Any]) -> Dict[str, Any]:
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
            "applied_jurisdiction": data.get("applied_jurisdiction", "default")
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
