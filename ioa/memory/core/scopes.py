""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, List

from .interfaces import MemoryHandle, MemoryEntry, MemoryStats


@dataclass(frozen=True)
class Scope:
	project_id: Optional[str]
	user_id: Optional[str]
	agent_id: Optional[str]


class ScopedMemoryHandle(MemoryHandle):
	"""A decorator over a `MemoryHandle` that injects and enforces scope metadata.

	- Adds `project_id`, `user_id`, `agent_id` to metadata if missing
	- Filters retrieval/search results to the configured scope
	- Prevents cross‑tenant reads
	"""

	def __init__(self, inner: MemoryHandle, project_id: Optional[str] = None, user_id: Optional[str] = None, agent_id: Optional[str] = None) -> None:
		self._inner = inner
		self._scope = Scope(project_id=project_id, user_id=user_id, agent_id=agent_id)

	def _with_scope(self, metadata: Optional[Dict] = None) -> Dict:
		merged = dict(metadata or {})
		if self._scope.project_id is not None:
			merged.setdefault("project_id", self._scope.project_id)
		if self._scope.user_id is not None:
			merged.setdefault("user_id", self._scope.user_id)
		if self._scope.agent_id is not None:
			merged.setdefault("agent_id", self._scope.agent_id)
		return merged

	def _in_scope(self, entry: MemoryEntry) -> bool:
		md = entry.metadata or {}
		if self._scope.project_id is not None and md.get("project_id") != self._scope.project_id:
			return False
		if self._scope.user_id is not None and (entry.user_id or md.get("user_id")) != self._scope.user_id:
			return False
		if self._scope.agent_id is not None and md.get("agent_id") != self._scope.agent_id:
			return False
		return True

	# MemoryHandle -------------------------------------------------------------
	def store(self, content: str, metadata: Optional[Dict] = None) -> str:
		return self._inner.store(content, metadata=self._with_scope(metadata))

	def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
		entry = self._inner.retrieve(entry_id)
		return entry if (entry and self._in_scope(entry)) else None

	def search(self, query: str, limit: int = 10) -> List[MemoryEntry]:
		results = self._inner.search(query, limit=limit)
		return [e for e in results if self._in_scope(e)]

	def delete(self, entry_id: str) -> bool:
		# Allow delete if the entry would be visible within scope
		entry = self._inner.retrieve(entry_id)
		if entry and self._in_scope(entry):
			return self._inner.delete(entry_id)
		return False

	def get_stats(self) -> MemoryStats:
		# Stats remain global to avoid heavy scans; callers can compute scoped stats if needed
		return self._inner.get_stats()

	def cleanup(self) -> bool:
		return self._inner.cleanup()


__all__ = ["ScopedMemoryHandle"]


