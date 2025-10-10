""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Tuple

from ..core.interfaces import ComplianceFilter, MemoryEntry
from src.audit_logger import AuditLogger


class PolicyChain(ComplianceFilter):
	"""Composable compliance filter that applies redaction and retention hooks.

	Fail‑soft by default; emits audits via `src.audit_logger.AuditLogger`.
	"""

	def __init__(self) -> None:
		self._redaction_enabled = os.getenv("IOA_REDACTION", "on").lower() not in {"off", "0", "false"}
		self._retention_days = int(os.getenv("IOA_RETENTION_DAYS", "0") or 0)
		self._auditor = AuditLogger()

	def redact(self, text: str, metadata: Dict | None = None) -> Tuple[str, Dict[str, any]]:  # type: ignore[override]
		if not self._redaction_enabled:
			return text, {"redacted": False}
		# Minimal example redaction: mask email‑like tokens
		import re
		masked = re.sub(r"[\w.\-]+@[\w.\-]+", "[REDACTED_EMAIL]", text)
		if masked != text:
			self.emit_audit({
				"event": "redaction",
				"changed": True,
				"meta": metadata or {},
			})
		return masked, {"redacted": masked != text}

	def apply_retention(self, entries: Iterable[MemoryEntry]) -> List[MemoryEntry]:
		if self._retention_days <= 0:
			return list(entries)
		cutoff = datetime.now(timezone.utc).timestamp() - (self._retention_days * 86400)
		kept: List[MemoryEntry] = []
		for e in entries:
			if e.timestamp.timestamp() >= cutoff:
				kept.append(e)
			else:
				self.emit_audit({"event": "retention_drop", "id": e.id})
		return kept

	def emit_audit(self, event):
		try:
			self._auditor.log_gdpr_event("compliance", event)
		except Exception:
			pass

__all__ = ["PolicyChain"]


