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
import uuid
from typing import Any, Dict, List, Optional

from .core.interfaces import (
	MemoryHandle,
	MemoryEntry,
	MemoryStats,
	HotStore,
	ColdStore,
	VectorIndex,
	ComplianceFilter,
)


class MemoryEngine(MemoryHandle):
	"""33D thin orchestrator; no business logic beyond composition.

	Profiles:
	- local: hot only
	- hybrid: hot + cold
	- cloud: cold only
	Vector/compliance are optional and fail soft.
	"""

	def __init__(
		self,
		hot_store: Optional[HotStore] = None,
		cold_store: Optional[ColdStore] = None,
		vector_index: Optional[VectorIndex] = None,
		compliance: Optional[ComplianceFilter] = None,
		profile: Optional[str] = None,
	):
		self._profile = (profile or os.getenv("MEMORY_ENGINE_PROFILE", "local")).lower()
		self._hot = hot_store
		self._cold = cold_store
		self._vector = vector_index
		self._compliance = compliance

	def _use_hot(self) -> bool:
		return self._profile in {"local", "hybrid"} and self._hot is not None

	def _use_cold(self) -> bool:
		return self._profile in {"hybrid", "cloud"} and self._cold is not None and self._cold.is_available()

	def _redact(self, text: str, metadata: Optional[Dict[str, Any]]) -> str:
		if self._compliance is None:
			return text
		masked, _ = self._compliance.redact(text, metadata)
		return masked

	# MemoryHandle -------------------------------------------------------------
	def store(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
		entry_id = str(uuid.uuid4())
		entry = MemoryEntry(id=entry_id, content=self._redact(content, metadata), metadata=metadata or {})
		stored = False
		if self._use_hot():
			stored = self._hot.store(entry) or stored
		if self._use_cold():
			# Optionally write‑through to cold for durability in cloud mode
			if self._profile == "cloud":
				stored = self._cold.store(entry) or stored
		if self._vector is not None and self._vector.is_available():
			try:
				self._vector.upsert(entry_id, entry.content, metadata)
			except Exception:
				pass
		return entry_id if stored or self._use_hot() or self._use_cold() else entry_id

	def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
		entry: Optional[MemoryEntry] = None
		if self._use_hot():
			entry = self._hot.retrieve(entry_id)
		if entry is None and self._use_cold():
			entry = self._cold.retrieve(entry_id)
		return entry

	def search(self, query: str, limit: int = 10) -> List[MemoryEntry]:
		results: List[MemoryEntry] = []
		if self._vector is not None and self._vector.is_available():
			# If vector available, prefer hybrid search by vector IDs then hydrate
			try:
				ids = [i for i, _ in self._vector.query(query, k=limit)]
				for eid in ids:
					found = self.retrieve(eid)
					if found:
						results.append(found)
				return results
			except Exception:
				results = []
		if self._use_hot():
			results.extend(self._hot.search(query, limit=limit))
		if self._use_cold():
			results.extend(self._cold.search(query, limit=max(0, limit - len(results))))
		return results[:limit]

	def delete(self, entry_id: str) -> bool:
		ok = False
		if self._use_hot():
			ok = self._hot.delete(entry_id) or ok
		if self._use_cold():
			ok = self._cold.delete(entry_id) or ok
		if self._vector is not None and self._vector.is_available():
			try:
				self._vector.delete(entry_id)
			except Exception:
				pass
		return ok

	def get_stats(self) -> MemoryStats:
		stats = MemoryStats()
		if self._use_hot():
			hs = self._hot.get_stats()
			stats.total_entries += hs.total_entries
			for k, v in hs.storage_tier_distribution.items():
				stats.storage_tier_distribution[k] = stats.storage_tier_distribution.get(k, 0) + v
		if self._use_cold():
			cs = self._cold.get_stats()
			stats.total_entries += cs.total_entries
			for k, v in cs.storage_tier_distribution.items():
				stats.storage_tier_distribution[k] = stats.storage_tier_distribution.get(k, 0) + v
		return stats

	def cleanup(self) -> bool:
		# Nothing to do for now; stores manage themselves
		return True


__all__ = ["MemoryEngine"]


