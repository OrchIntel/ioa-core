# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""Audit compatibility layer for consumer repositories."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .canonical import canonicalize_json, compute_hash, validate_hash_format, verify_hash


class AuditLogger:
    """Simple JSONL-backed audit logger with a stable compatibility API."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, log_dir: Optional[str] = None) -> None:
        self.config = config or {}
        base_dir = Path(log_dir or self.config.get("log_dir", "logs"))
        base_dir.mkdir(parents=True, exist_ok=True)
        self._audit_file = base_dir / "audit.jsonl"

    def log_action(
        self,
        *,
        action: str,
        actor: Optional[str] = None,
        actor_id: Optional[str] = None,
        resource: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        outcome: str = "success",
        metadata: Optional[Dict[str, Any]] = None,
        **extra: Any,
    ) -> str:
        audit_id = str(uuid.uuid4())
        event = {
            "audit_id": audit_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "actor_id": actor_id or actor or "unknown",
            "resource_type": resource_type or resource,
            "resource_id": resource_id,
            "outcome": outcome,
            "metadata": metadata or {},
        }
        if extra:
            event["metadata"].update(extra)
        with self._audit_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, separators=(",", ":")) + "\n")
        return audit_id

    def get_audit_trail(
        self,
        *,
        actor_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if not self._audit_file.exists():
            return []

        start_dt = _parse_iso(start_date)
        end_dt = _parse_iso(end_date)
        events: List[Dict[str, Any]] = []
        for line in self._audit_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            event_dt = _parse_iso(event.get("timestamp"))
            if actor_id and event.get("actor_id") != actor_id:
                continue
            if resource_type and event.get("resource_type") != resource_type:
                continue
            if start_dt and event_dt and event_dt < start_dt:
                continue
            if end_dt and event_dt and event_dt > end_dt:
                continue
            events.append(event)
        return events


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


__all__ = [
    "AuditLogger",
    "canonicalize_json",
    "compute_hash",
    "validate_hash_format",
    "verify_hash",
]
