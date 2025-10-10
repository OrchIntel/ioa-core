""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Optional

from ..core.interfaces import MemoryEntry, MemoryStats, StorageError, HotStore


class SQLiteHotStore(HotStore):
	def __init__(self, db_path: str = ":memory:", max_cache_size: int = 1000) -> None:
		self.db_path = db_path
		self.max_cache_size = max_cache_size
		self.logger = logging.getLogger(__name__)
		self._cache: Dict[str, MemoryEntry] = {}
		self._init_db()
		self._load_cache()

	@contextmanager
	def _conn(self):
		conn = sqlite3.connect(self.db_path)
		try:
			conn.execute("PRAGMA journal_mode=WAL;")
			yield conn
		finally:
			conn.close()

	def _init_db(self) -> None:
		try:
			with self._conn() as conn:
				conn.execute(
					"""
					CREATE TABLE IF NOT EXISTS memory_entries (
						id TEXT PRIMARY KEY,
						content TEXT NOT NULL,
						metadata TEXT,
						timestamp TEXT NOT NULL,
						tags TEXT,
						storage_tier TEXT DEFAULT 'hot',
						access_count INTEGER DEFAULT 0,
						last_accessed TEXT
					)
					"""
				)
				conn.commit()
		except Exception as exc:
			self.logger.error("Failed to initialize hot store DB: %s", exc)
			raise StorageError(str(exc))

	def _row_to_entry(self, row) -> MemoryEntry:
		metadata = json.loads(row[2]) if row[2] else {}
		tags = json.loads(row[4]) if row[4] else []
		entry = MemoryEntry(
			id=row[0],
			content=row[1],
			metadata=metadata,
			timestamp=datetime.fromisoformat(row[3]),
			tags=tags,
			storage_tier=row[5] or "hot",
			access_count=row[6] or 0,
		)
		if row[7]:
			entry.last_accessed = datetime.fromisoformat(row[7])
		return entry

	def _entry_to_row(self, entry: MemoryEntry) -> tuple:
		return (
			entry.id,
			entry.content,
			json.dumps(entry.metadata),
			entry.timestamp.isoformat(),
			json.dumps(entry.tags),
			entry.storage_tier,
			entry.access_count,
			entry.last_accessed.isoformat() if entry.last_accessed else None,
		)

	def _load_cache(self) -> None:
		try:
			with self._conn() as conn:
				rows = conn.execute("SELECT * FROM memory_entries").fetchall()
				for row in rows:
					entry = self._row_to_entry(row)
					self._cache[entry.id] = entry
					if len(self._cache) >= self.max_cache_size:
						break
		except Exception as exc:
			self.logger.warning("Failed to load hot cache: %s", exc)

	# HotStore ----------------------------------------------------------------
	def store(self, entry: MemoryEntry) -> bool:
		self._cache[entry.id] = entry
		try:
			with self._conn() as conn:
				conn.execute(
					"""
					INSERT OR REPLACE INTO memory_entries
					(id, content, metadata, timestamp, tags, storage_tier, access_count, last_accessed)
					VALUES (?, ?, ?, ?, ?, ?, ?, ?)
					""",
					self._entry_to_row(entry),
				)
				conn.commit()
			return True
		except Exception as exc:
			self.logger.error("Hot store write failed: %s", exc)
			raise StorageError(str(exc))

	def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
		entry = self._cache.get(entry_id)
		if entry:
			entry.access_count += 1
			entry.last_accessed = datetime.now()
			try:
				with self._conn() as conn:
					conn.execute(
						"UPDATE memory_entries SET access_count=?, last_accessed=? WHERE id=?",
						(entry.access_count, entry.last_accessed.isoformat(), entry_id),
					)
					conn.commit()
			except Exception:
				pass
			return entry
		try:
			with self._conn() as conn:
				row = conn.execute("SELECT * FROM memory_entries WHERE id=?", (entry_id,)).fetchone()
				return self._row_to_entry(row) if row else None
		except Exception as exc:
			self.logger.error("Hot store read failed: %s", exc)
			return None

	def search(self, query: str, limit: int = 10) -> List[MemoryEntry]:
		try:
			with self._conn() as conn:
				rows = conn.execute(
					"""
					SELECT * FROM memory_entries
					WHERE content LIKE ? OR tags LIKE ?
					ORDER BY access_count DESC, timestamp DESC
					LIMIT ?
					""",
					(f"%{query}%", f"%{query}%", limit),
				).fetchall()
				return [self._row_to_entry(r) for r in rows]
		except Exception as exc:
			self.logger.error("Hot store search failed: %s", exc)
			return []

	def delete(self, entry_id: str) -> bool:
		self._cache.pop(entry_id, None)
		try:
			with self._conn() as conn:
				conn.execute("DELETE FROM memory_entries WHERE id=?", (entry_id,))
				conn.commit()
			return True
		except Exception as exc:
			self.logger.error("Hot store delete failed: %s", exc)
			return False

	def list_all(self) -> List[MemoryEntry]:
		try:
			with self._conn() as conn:
				rows = conn.execute("SELECT * FROM memory_entries ORDER BY timestamp DESC").fetchall()
				return [self._row_to_entry(r) for r in rows]
		except Exception as exc:
			self.logger.error("Hot store list_all failed: %s", exc)
			return []

	def get_stats(self) -> MemoryStats:
		try:
			with self._conn() as conn:
				total = conn.execute("SELECT COUNT(*) FROM memory_entries").fetchone()[0]
				tiers = dict(
					conn.execute(
						"SELECT storage_tier, COUNT(*) FROM memory_entries GROUP BY storage_tier"
					).fetchall()
				)
				avg_access = conn.execute("SELECT AVG(access_count) FROM memory_entries").fetchone()[0] or 0
				return MemoryStats(
					total_entries=total,
					storage_tier_distribution=tiers,
					avg_processing_time=float(avg_access),
				)
		except Exception:
			return MemoryStats()


