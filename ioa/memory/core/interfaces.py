"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
Module responsibilities:
- Define DTOs (`MemoryEntry`, `MemoryStats`) used across memory components
- Define abstract interfaces (`MemoryHandle`, `HotStore`, `ColdStore`, `VectorIndex`, `ComplianceFilter`)
- Keep external behavior stable; raise only typed exceptions from this module
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Protocol, Tuple
from abc import ABC, abstractmethod


# DTOs -----------------------------------------------------------------------

@dataclass
class MemoryEntry:
	"""A single item of memory content.

	Fields must remain backward compatible with 33C.
	"""
	id: str
	content: str
	metadata: Dict[str, Any] = field(default_factory=dict)
	timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
	last_accessed: Optional[datetime] = None
	access_count: int = 0
	storage_tier: str = "hot"  # hot|cold|auto
	user_id: Optional[str] = None
	tags: List[str] = field(default_factory=list)

	def to_dict(self) -> Dict[str, Any]:
		return {
			"id": self.id,
			"content": self.content,
			"metadata": self.metadata,
			"timestamp": self.timestamp.isoformat(),
			"last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
			"access_count": self.access_count,
			"storage_tier": self.storage_tier,
			"user_id": self.user_id,
			"tags": self.tags,
		}

	@staticmethod
	def from_dict(data: Dict[str, Any]) -> "MemoryEntry":
		# Preserve permissive parsing of timestamps
		ts = data.get("timestamp")
		if isinstance(ts, str):
			try:
				ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
			except Exception:
				ts = datetime.now(timezone.utc)
		elif ts is None:
			ts = datetime.now(timezone.utc)

		la = data.get("last_accessed")
		if isinstance(la, str):
			try:
				la = datetime.fromisoformat(la.replace("Z", "+00:00"))
			except Exception:
				la = None

		return MemoryEntry(
			id=data["id"],
			content=data["content"],
			metadata=data.get("metadata", {}),
			timestamp=ts,
			last_accessed=la,
			access_count=int(data.get("access_count", 0)),
			storage_tier=data.get("storage_tier", "hot"),
			user_id=data.get("user_id"),
			tags=list(data.get("tags", [])),
		)


@dataclass
class MemoryStats:
	"""Aggregated metrics for memory operations."""
	total_entries: int = 0
	preserved_entries: int = 0
	digested_entries: int = 0
	failed_entries: int = 0
	avg_processing_time: float = 0.0
	storage_tier_distribution: Dict[str, int] = field(
		default_factory=lambda: {"hot": 0, "cold": 0, "auto": 0}
	)
	metadata: Dict[str, Any] = field(default_factory=dict)


# Exceptions -----------------------------------------------------------------

class MemoryError(Exception):
	"""Base error for memory operations."""

class StorageError(MemoryError):
	"""Storage backend error."""

class ProcessingError(MemoryError):
	"""Processing/redaction/compliance error."""


# Interfaces -----------------------------------------------------------------

class MemoryHandle(ABC):
	"""Stable interface exposed to call‑sites.

	Implementations may be local, hybrid, or cloud, but the API remains stable.
	"""

	@abstractmethod
	def store(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
		"""Store content and return entry id."""

	@abstractmethod
	def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
		"""Retrieve by id, or None."""

	@abstractmethod
	def search(self, query: str, limit: int = 10) -> List[MemoryEntry]:
		"""Content or tag search, best‑effort across tiers."""

	@abstractmethod
	def delete(self, entry_id: str) -> bool:
		"""Delete entry across tiers if present."""

	@abstractmethod
	def get_stats(self) -> MemoryStats:
		"""High‑level stats across tiers."""

	@abstractmethod
	def cleanup(self) -> bool:
		"""Housekeeping (vacuum, GC)."""


class HotStore(Protocol):
	def store(self, entry: MemoryEntry) -> bool: ...
	def retrieve(self, entry_id: str) -> Optional[MemoryEntry]: ...
	def search(self, query: str, limit: int = 10) -> List[MemoryEntry]: ...
	def delete(self, entry_id: str) -> bool: ...
	def list_all(self) -> List[MemoryEntry]: ...
	def get_stats(self) -> MemoryStats: ...


class ColdStore(Protocol):
	def store(self, entry: MemoryEntry) -> bool: ...
	def retrieve(self, entry_id: str) -> Optional[MemoryEntry]: ...
	def search(self, query: str, limit: int = 10) -> List[MemoryEntry]: ...
	def delete(self, entry_id: str) -> bool: ...
	def list_all(self) -> List[MemoryEntry]: ...
	def get_stats(self) -> MemoryStats: ...
	def is_available(self) -> bool: ...
	def get_storage_info(self) -> Dict[str, Any]: ...


class VectorIndex(Protocol):
	def upsert(self, entry_id: str, content: str, metadata: Dict[str, Any] | None = None) -> bool: ...
	def query(self, text: str, k: int = 5) -> List[Tuple[str, float]]: ...
	def delete(self, entry_id: str) -> bool: ...
	def is_available(self) -> bool: ...


class ComplianceFilter(Protocol):
	def redact(self, text: str, metadata: Dict[str, Any] | None = None) -> Tuple[str, Dict[str, Any]]: ...
	def apply_retention(self, entries: Iterable[MemoryEntry]) -> List[MemoryEntry]: ...
	def emit_audit(self, event: Dict[str, Any]) -> None: ...


__all__ = [
	"MemoryEntry",
	"MemoryStats",
	"MemoryHandle",
	"HotStore",
	"ColdStore",
	"VectorIndex",
	"ComplianceFilter",
]


