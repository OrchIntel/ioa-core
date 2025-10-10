""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pathlib import Path

from .base import BaseMemoryStore, MemoryStore
from ..schema import MemoryRecordV1

# PATCH: Cursor-2025-09-10 DISPATCH-OSS-20250910-MEMORY-FABRIC-REFACTOR <sqlite store>

class SQLiteStore(BaseMemoryStore):
    """SQLite storage implementation for Memory Fabric with WAL mode."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the SQLite store."""
        super().__init__(config)
        self.data_dir = Path(config.get("data_dir", "./artifacts/memory"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create run-specific database
        run_id = str(uuid.uuid4())[:8]
        self.db_path = self.data_dir / f"memory_run_{run_id}.db"
        self._connection = None
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with WAL mode and optional performance tuning."""
        try:
            self._connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._connection.execute("PRAGMA journal_mode=WAL")

            # Apply performance tuning if enabled
            if self.config.get("perf_tune_enabled", False):
                # Performance-optimized settings (integrity-preserving)
                self._connection.execute("PRAGMA synchronous=NORMAL")  # Faster than FULL, still durable
                self._connection.execute("PRAGMA cache_size=-8192")    # 8MB cache (was 1000 pages)
                self._connection.execute("PRAGMA wal_autocheckpoint=10000")  # Reduce checkpoint frequency
                self._connection.execute("PRAGMA temp_store=MEMORY")   # Temp tables in memory
                self._connection.execute("PRAGMA mmap_size=268435456") # 256MB memory mapping
                self._connection.execute("PRAGMA busy_timeout=5000")   # 5s busy timeout
            else:
                # Default conservative settings
                self._connection.execute("PRAGMA synchronous=NORMAL")
                self._connection.execute("PRAGMA cache_size=1000")
                self._connection.execute("PRAGMA temp_store=MEMORY")
            
            # Create tables
            self._connection.execute("""
                CREATE TABLE IF NOT EXISTS memory_records (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    timestamp TEXT NOT NULL,
                    tags TEXT,
                    storage_tier TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT,
                    embedding TEXT,
                    schema_version TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            self._connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_records(memory_type)
            """)
            self._connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_storage_tier ON memory_records(storage_tier)
            """)
            self._connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON memory_records(timestamp)
            """)
            self._connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_access_count ON memory_records(access_count)
            """)
            
            # Full-text search index
            self._connection.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                    content, tags, content='memory_records', content_rowid='rowid'
                )
            """)
            
            self._connection.commit()
            
            # Count existing records
            cursor = self._connection.execute("SELECT COUNT(*) FROM memory_records")
            self._stats["total_records"] = cursor.fetchone()[0]
            
        except Exception as e:
            self._update_stats("errors", False)
            raise
    
    def store(self, record: MemoryRecordV1) -> bool:
        """Store a memory record."""
        try:
            if not self._validate_record(record):
                self._update_stats("writes", False)
                return False
            
            # Convert to database format
            data = record.to_dict()
            
            cursor = self._connection.execute("""
                INSERT OR REPLACE INTO memory_records 
                (id, content, metadata, timestamp, tags, storage_tier, memory_type, 
                 access_count, last_accessed, embedding, schema_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.id,
                record.content,
                json.dumps(record.metadata),
                record.timestamp.isoformat(),
                json.dumps(record.tags),
                record.storage_tier.value,
                record.memory_type.value,
                record.access_count,
                record.last_accessed.isoformat() if record.last_accessed else None,
                json.dumps(record.embedding.to_dict()) if record.embedding else None,
                record.__schema_version__
            ))
            
            # Update FTS index
            self._connection.execute("""
                INSERT OR REPLACE INTO memory_fts (rowid, content, tags)
                VALUES (?, ?, ?)
            """, (
                cursor.lastrowid,
                record.content,
                " ".join(record.tags)
            ))
            
            self._connection.commit()
            self._update_stats("writes", True)
            self._stats["total_records"] += 1
            return True
            
        except Exception as e:
            self._connection.rollback()
            self._update_stats("writes", False)
            return False
    
    def retrieve(self, record_id: str) -> Optional[MemoryRecordV1]:
        """Retrieve a memory record by ID."""
        try:
            cursor = self._connection.execute("""
                SELECT id, content, metadata, timestamp, tags, storage_tier, memory_type,
                       access_count, last_accessed, embedding, schema_version
                FROM memory_records WHERE id = ?
            """, (record_id,))
            
            row = cursor.fetchone()
            if not row:
                self._update_stats("reads", False)
                return None
            
            # Convert from database format
            data = {
                "id": row[0],
                "content": row[1],
                "metadata": json.loads(row[2]) if row[2] else {},
                "timestamp": row[3],
                "tags": json.loads(row[4]) if row[4] else [],
                "storage_tier": row[5],
                "memory_type": row[6],
                "access_count": row[7],
                "last_accessed": row[8],
                "embedding": json.loads(row[9]) if row[9] else None,
                "__schema_version__": row[10]
            }
            
            record = MemoryRecordV1.from_dict(data)
            record.update_access()
            
            # Update access count in database
            self._connection.execute("""
                UPDATE memory_records 
                SET access_count = ?, last_accessed = ?
                WHERE id = ?
            """, (record.access_count, record.last_accessed.isoformat(), record_id))
            self._connection.commit()
            
            self._update_stats("reads", True)
            return record
            
        except Exception as e:
            self._update_stats("reads", False)
            return None
    
    def search(self, query: str, limit: int = 10, memory_type: Optional[str] = None) -> List[MemoryRecordV1]:
        """Search for memory records using FTS."""
        try:
            # Build query with optional memory_type filter
            sql = """
                SELECT m.id, m.content, m.metadata, m.timestamp, m.tags, m.storage_tier, 
                       m.memory_type, m.access_count, m.last_accessed, m.embedding, m.schema_version
                FROM memory_records m
                JOIN memory_fts f ON m.rowid = f.rowid
                WHERE memory_fts MATCH ?
            """
            params = [query]
            
            if memory_type:
                sql += " AND m.memory_type = ?"
                params.append(memory_type)
            
            sql += " ORDER BY m.access_count DESC, m.timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor = self._connection.execute(sql, params)
            results = []
            
            for row in cursor.fetchall():
                data = {
                    "id": row[0],
                    "content": row[1],
                    "metadata": json.loads(row[2]) if row[2] else {},
                    "timestamp": row[3],
                    "tags": json.loads(row[4]) if row[4] else [],
                    "storage_tier": row[5],
                    "memory_type": row[6],
                    "access_count": row[7],
                    "last_accessed": row[8],
                    "embedding": json.loads(row[9]) if row[9] else None,
                    "__schema_version__": row[10]
                }
                results.append(MemoryRecordV1.from_dict(data))
            
            self._update_stats("queries", True)
            return results
            
        except Exception as e:
            self._update_stats("queries", False)
            return []
    
    def delete(self, record_id: str) -> bool:
        """Delete a memory record."""
        try:
            cursor = self._connection.execute("SELECT rowid FROM memory_records WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            
            if not row:
                return False
            
            # Delete from main table
            self._connection.execute("DELETE FROM memory_records WHERE id = ?", (record_id,))
            
            # Delete from FTS index
            self._connection.execute("DELETE FROM memory_fts WHERE rowid = ?", (row[0],))
            
            self._connection.commit()
            self._stats["total_records"] = max(0, self._stats["total_records"] - 1)
            return True
            
        except Exception as e:
            self._connection.rollback()
            self._update_stats("errors", False)
            return False
    
    def list_all(self, limit: Optional[int] = None) -> List[MemoryRecordV1]:
        """List all memory records."""
        try:
            sql = """
                SELECT id, content, metadata, timestamp, tags, storage_tier, memory_type,
                       access_count, last_accessed, embedding, schema_version
                FROM memory_records
                ORDER BY access_count DESC, timestamp DESC
            """
            
            if limit:
                sql += " LIMIT ?"
                cursor = self._connection.execute(sql, (limit,))
            else:
                cursor = self._connection.execute(sql)
            
            results = []
            for row in cursor.fetchall():
                data = {
                    "id": row[0],
                    "content": row[1],
                    "metadata": json.loads(row[2]) if row[2] else {},
                    "timestamp": row[3],
                    "tags": json.loads(row[4]) if row[4] else [],
                    "storage_tier": row[5],
                    "memory_type": row[6],
                    "access_count": row[7],
                    "last_accessed": row[8],
                    "embedding": json.loads(row[9]) if row[9] else None,
                    "__schema_version__": row[10]
                }
                results.append(MemoryRecordV1.from_dict(data))
            
            self._update_stats("reads", True)
            return results
            
        except Exception as e:
            self._update_stats("reads", False)
            return []
    
    def close(self) -> None:
        """Close the store and cleanup resources."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def get_db_path(self) -> str:
        """Get the database file path."""
        return str(self.db_path)
