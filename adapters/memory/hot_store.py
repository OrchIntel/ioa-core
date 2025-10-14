"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.


import sqlite3
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timezone

# PATCH: Cursor-2025-01-27 DISPATCH-GPT-20250825-031 <memory engine modularization>

from .core import MemoryEntry, MemoryStats, MemoryStore, StorageError

class HotStore(MemoryStore):
    """Hot storage implementation using in-memory cache with SQLite persistence."""
    
    def __init__(self, db_path: str = ":memory:", max_cache_size: int = 1000):
        """
        Initialize hot store.
        
        Args:
            db_path: SQLite database path (use ":memory:" for in-memory only)
            max_cache_size: Maximum number of entries to keep in memory cache
        """
        self.db_path = db_path
        self.max_cache_size = max_cache_size
        self.logger = logging.getLogger(__name__)
        
        # In-memory cache for fast access
        self._cache: Dict[str, MemoryEntry] = {}
        
        # Initialize database
        self._init_db()
        
        # Load existing entries into cache
        self._load_cache()
    
    def _init_db(self):
        """Initialize SQLite database schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
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
                """)
                conn.commit()
            finally:
                conn.close()
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise StorageError(f"Database initialization failed: {e}", "init_db")
    
    def _load_cache(self):
        """Load entries from database into memory cache."""
        try:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute("SELECT * FROM memory_entries")
                rows = cursor.fetchall()
                
                for row in rows:
                    entry = self._row_to_entry(row)
                    self._cache[entry.id] = entry
                    
                    # Respect cache size limit
                    if len(self._cache) >= self.max_cache_size:
                        break
            finally:
                conn.close()
                        
        except Exception as e:
            self.logger.error(f"Failed to load cache: {e}")
            # Continue with empty cache rather than failing completely
    
    def _row_to_entry(self, row) -> MemoryEntry:
        """Convert database row to MemoryEntry."""
        metadata = json.loads(row[2]) if row[2] else {}
        tags = json.loads(row[4]) if row[4] else []
        
        entry = MemoryEntry(
            id=row[0],
            content=row[1],
            metadata=metadata,
            timestamp=datetime.fromisoformat(row[3]),
            tags=tags,
            storage_tier=row[5] or "hot",
            access_count=row[6] or 0
        )
        
        if row[7]:  # last_accessed
            entry.last_accessed = datetime.fromisoformat(row[7])
        
        return entry
    
    def _entry_to_row(self, entry: MemoryEntry) -> tuple:
        """Convert MemoryEntry to database row."""
        return (
            entry.id,
            entry.content,
            json.dumps(entry.metadata),
            entry.timestamp.isoformat(),
            json.dumps(entry.tags),
            entry.storage_tier,
            entry.access_count,
            entry.last_accessed.isoformat() if entry.last_accessed else None
        )
    
    def store(self, entry: MemoryEntry) -> bool:
        """Store a memory entry."""
        try:
            # Update cache
            self._cache[entry.id] = entry
            
            # Persist to database
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO memory_entries 
                    (id, content, metadata, timestamp, tags, storage_tier, access_count, last_accessed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, self._entry_to_row(entry))
                conn.commit()
            finally:
                conn.close()
            
            # Maintain cache size
            if len(self._cache) > self.max_cache_size:
                self._evict_oldest()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store entry {entry.id}: {e}")
            raise StorageError(f"Store operation failed: {e}", "store", entry.id)
    
    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by ID."""
        # Check cache first
        if entry_id in self._cache:
            entry = self._cache[entry_id]
            entry.access_count += 1
            entry.last_accessed = datetime.now(timezone.utc)
            
            # Update access stats in database
            try:
                conn = sqlite3.connect(self.db_path)
                try:
                    conn.execute("""
                        UPDATE memory_entries 
                        SET access_count = ?, last_accessed = ?
                        WHERE id = ?
                    """, (entry.access_count, entry.last_accessed.isoformat(), entry_id))
                    conn.commit()
                finally:
                    conn.close()
            except Exception as e:
                self.logger.warning(f"Failed to update access stats: {e}")
            
            return entry
        
        # Fallback to database
        try:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute("SELECT * FROM memory_entries WHERE id = ?", (entry_id,))
                row = cursor.fetchone()
                
                if row:
                    entry = self._row_to_entry(row)
                    # Add to cache
                    self._cache[entry_id] = entry
                    return entry
            finally:
                conn.close()
                    
        except Exception as e:
            self.logger.error(f"Failed to retrieve entry {entry_id}: {e}")
        
        return None
    
    def search(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """Search for memory entries."""
        try:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute("""
                    SELECT * FROM memory_entries 
                    WHERE content LIKE ? OR tags LIKE ?
                    ORDER BY access_count DESC, timestamp DESC
                    LIMIT ?
                """, (f"%{query}%", f"%{query}%", limit))
                
                rows = cursor.fetchall()
                results = []
                
                for row in rows:
                    entry = self._row_to_entry(row)
                    results.append(entry)
                    # Add to cache
                    self._cache[entry.id] = entry
                
                return results
            finally:
                conn.close()
                
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []
    
    def delete(self, entry_id: str) -> bool:
        """Delete a memory entry."""
        try:
            # Remove from cache
            if entry_id in self._cache:
                del self._cache[entry_id]
            
            # Remove from database
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("DELETE FROM memory_entries WHERE id = ?", (entry_id,))
                conn.commit()
            finally:
                conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete entry {entry_id}: {e}")
            return False
    
    def list_all(self) -> List[MemoryEntry]:
        """List all memory entries."""
        try:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute("SELECT * FROM memory_entries ORDER BY timestamp DESC")
                rows = cursor.fetchall()
                
                entries = []
                for row in rows:
                    entry = self._row_to_entry(row)
                    entries.append(entry)
                    # Add to cache
                    self._cache[entry.id] = entry
                
                return entries
            finally:
                conn.close()
                
        except Exception as e:
            self.logger.error(f"Failed to list entries: {e}")
            return []
    
    def get_stats(self) -> MemoryStats:
        """Get storage statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            try:
                # Get total count
                cursor = conn.execute("SELECT COUNT(*) FROM memory_entries")
                total = cursor.fetchone()[0]
                
                # Get tier distribution
                cursor = conn.execute("""
                    SELECT storage_tier, COUNT(*) 
                    FROM memory_entries 
                    GROUP BY storage_tier
                """)
                tier_dist = dict(cursor.fetchall())
                
                # Get access stats
                cursor = conn.execute("SELECT AVG(access_count) FROM memory_entries")
                avg_access = cursor.fetchone()[0] or 0
                
                return MemoryStats(
                    total_entries=total,
                    storage_tier_distribution=tier_dist,
                    avg_processing_time=avg_access
                )
            finally:
                conn.close()
                
        except Exception as e:
            self.logger.error(f"Failed to get stats: {e}")
            return MemoryStats()
    
    def _evict_oldest(self):
        """Evict oldest entries from cache to maintain size limit."""
        if len(self._cache) <= self.max_cache_size:
            return
        
        # Sort by last accessed and remove oldest
        sorted_entries = sorted(
            self._cache.values(),
            key=lambda x: x.last_accessed or x.timestamp
        )
        
        entries_to_remove = len(self._cache) - self.max_cache_size
        for entry in sorted_entries[:entries_to_remove]:
            del self._cache[entry.id]
    
    def clear_cache(self):
        """Clear the in-memory cache."""
        self._cache.clear()
    
    def sync_cache(self):
        """Synchronize cache with database."""
        self._cache.clear()
        self._load_cache()
