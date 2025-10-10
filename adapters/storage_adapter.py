""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""


# storage_adapter.py
# Abstract base class and concrete implementations for storage services.
# This decouples the MemoryEngine from the underlying database technology,
# enabling a plug-and-play architecture for memory persistence.

import json
import os
import sqlite3
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class StorageService(ABC):
    """
    Abstract Base Class for all storage services.
    It defines the standard interface (contract) for how the MemoryEngine
    will interact with any storage backend, be it a JSON file, a NoSQL database,
    or a vector store.
    """

    @abstractmethod
    def save(self, entry: Dict[str, Any]) -> str:
        """
        Saves a single memory entry to the storage backend.

        Args:
            entry (Dict[str, Any]): The data to be stored.

        Returns:
            str: A unique identifier for the saved entry.
        """
        pass

    @abstractmethod
    def load_all(self) -> List[Dict[str, Any]]:
        """
        Loads all memory entries from the storage backend.

        Returns:
            List[Dict[str, Any]]: A list of all memory entries.
        """
        pass

    @abstractmethod
    def query(self, key: str, value: Any) -> List[Dict[str, Any]]:
        """
        Searches for entries where a specific key matches a specific value.

        Args:
            key (str): The key to search for.
            value (Any): The value to match.

        Returns:
            List[Dict[str, Any]]: A list of matching entries.
        """
        pass

    @abstractmethod
    def delete(self, entry_id: str) -> bool:
        """
        Deletes a memory entry by its unique identifier.

        Args:
            entry_id (str): The unique ID of the entry to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        pass


class JSONStorageService(StorageService):
    """
    A concrete implementation of StorageService that uses a local JSON file.
    This is the default storage mechanism for the MVP, ensuring simplicity
    and portability.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._memory_cache = self._load_from_disk()

    def _load_from_disk(self) -> List[Dict[str, Any]]:
        """Loads the entire memory log from the JSON file."""
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save_to_disk(self):
        """Saves the entire memory log back to the JSON file."""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self._memory_cache, f, indent=4)

    def save(self, entry: Dict[str, Any]) -> str:
        """Appends an entry and saves the file."""
        # For JSON, we'll use the list index as a simple ID for now.
        # A more robust implementation would use UUIDs.
        entry_id = str(len(self._memory_cache))
        entry['id'] = entry_id
        self._memory_cache.append(entry)
        self._save_to_disk()
        return entry_id

    def load_all(self) -> List[Dict[str, Any]]:
        """Returns the cached memory."""
        return self._memory_cache

    def query(self, key: str, value: Any) -> List[Dict[str, Any]]:
        """Performs a simple key-value search."""
        return [entry for entry in self._memory_cache if entry.get(key) == value]

    def delete(self, entry_id: str) -> bool:
        """Deletes an entry by its index-based ID."""
        try:
            initial_len = len(self._memory_cache)
            # Find the entry with the matching ID
            self._memory_cache = [entry for entry in self._memory_cache if entry.get('id') != entry_id]
            if len(self._memory_cache) < initial_len:
                self._save_to_disk()
                return True
            return False
        except (ValueError, IndexError):
            return False


# --- Phase 2 Scaffolding ---

class MongoStorageService(StorageService):
    """
    (Phase 2 Stub) Concrete implementation for MongoDB.
    This will handle structured data storage at scale.
    """
    def save(self, entry: Dict[str, Any]) -> str:
        print("INFO: MongoStorageService.save() not yet implemented.")
        pass

    def load_all(self) -> List[Dict[str, Any]]:
        print("INFO: MongoStorageService.load_all() not yet implemented.")
        pass

    def query(self, key: str, value: Any) -> List[Dict[str, Any]]:
        print("INFO: MongoStorageService.query() not yet implemented.")
        pass

    def delete(self, entry_id: str) -> bool:
        print("INFO: MongoStorageService.delete() not yet implemented.")
        pass


class ChromaStorageService(StorageService):
    """
    (Phase 2 Stub) Concrete implementation for ChromaDB.
    This will handle vector embeddings for semantic search and RAG.
    """
    def save(self, entry: Dict[str, Any]) -> str:
        print("INFO: ChromaStorageService.save() not yet implemented.")
        pass

    def load_all(self) -> List[Dict[str, Any]]:
        print("INFO: ChromaStorageService.load_all() not yet implemented.")
        pass

    def query(self, key: str, value: Any) -> List[Dict[str, Any]]:
        # This query method will be adapted for semantic vector search
        print("INFO: ChromaStorageService.query() not yet implemented.")
        pass

    def delete(self, entry_id: str) -> bool:
        print("INFO: ChromaStorageService.delete() not yet implemented.")
        pass


# -----------------------------------------------------------------------------
# SQLiteStorageService
#
class SQLiteStorageService(StorageService):
    """
    Concrete implementation of StorageService using SQLite.

    This adapter stores memory entries in a lightweight SQLite database.  It
    creates a single table ``memory`` with ``id`` as a primary key and a
    JSON‑encoded ``data`` column.  Entries are upserted on save and can be
    queried by ID or by arbitrary key lookup using a simple scan.
    """

    def __init__(self, db_path: str = "ioa.db") -> None:
        """
        Initialise the SQLite storage service.

        Args:
            db_path: Path to the SQLite database file.  Defaults to
                ``ioa.db``.
        """
        # Open a dedicated connection; ensure it is closed on GC and provide explicit close
        self.conn = sqlite3.connect(db_path)
        try:
            # Enable foreign keys and row access as dictionaries
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS memory (id TEXT PRIMARY KEY, data TEXT)"
            )
        except Exception:
            # If initialization fails, close the connection before raising
            try:
                self.conn.close()
            finally:
                raise

    def save(self, entry: Dict[str, Any]) -> str:
        """
        Save or update an entry in the database.

        If the entry does not include an ``id`` key one will be generated
        using UUID4.  The entire entry is JSON‑encoded and stored under the
        ``data`` column.  Subsequent saves with the same ID will overwrite
        the previous record.

        Args:
            entry: The memory entry to persist.

        Returns:
            The ID of the stored entry.
        """
        entry_id = entry.get("id") or str(uuid.uuid4())
        # Ensure the ID is recorded in the entry itself
        entry["id"] = entry_id
        data_json = json.dumps(entry, default=str)
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO memory (id, data) VALUES (?, ?)",
                (entry_id, data_json),
            )
        return entry_id

    def load_all(self) -> List[Dict[str, Any]]:
        """Load all entries from the database."""
        cursor = self.conn.execute("SELECT data FROM memory")
        return [json.loads(row[0]) for row in cursor.fetchall()]

    def query(self, key: str, value: Any) -> List[Dict[str, Any]]:
        """
        Query entries by key/value pair.

        For the special case ``key == 'id'`` this method performs an
        efficient lookup in the primary key column.  For all other keys it
        performs a naive scan over all entries.  This is sufficient for
        testing and small deployments; production systems should use a more
        appropriate database and indexing strategy.

        Args:
            key: Field name to filter on.
            value: Field value to match.

        Returns:
            A list of matching entries.
        """
        results: List[Dict[str, Any]] = []
        if key == "id":
            cursor = self.conn.execute("SELECT data FROM memory WHERE id = ?", (value,))
            rows = cursor.fetchall()
            for row in rows:
                try:
                    results.append(json.loads(row[0]))
                except json.JSONDecodeError:
                    continue
            return results
        # Fallback: scan all entries
        for entry in self.load_all():
            if entry.get(key) == value:
                results.append(entry)
        return results

    def delete(self, entry_id: str) -> bool:
        """
        Delete an entry by ID.

        Args:
            entry_id: The ID of the entry to remove.

        Returns:
            True if a row was deleted, False otherwise.
        """
        with self.conn:
            cursor = self.conn.execute("DELETE FROM memory WHERE id = ?", (entry_id,))
        return cursor.rowcount > 0

    def close(self) -> None:
        """Close the underlying SQLite connection to avoid ResourceWarning leaks."""
        try:
            self.conn.close()
        except sqlite3.Error:
            # Connection may already be closed or invalid; ignore
            return
        except Exception:
            # Unknown close error; still avoid raising during cleanup
            return

    def delete_by_user(self, user_id: str) -> bool:
        """
        Delete all entries for a specific user.
        
        Args:
            user_id: The user ID whose entries should be deleted
            
        Returns:
            True if any entries were deleted, False otherwise
        """
        # PATCH: Cursor-2024-12-19 ET-001 Step 4 - Add delete_by_user method for SQLite
        try:
            with self.conn:
                cursor = self.conn.execute("DELETE FROM memory WHERE json_extract(data, '$.user_id') = ?", (user_id,))
            return cursor.rowcount > 0
        except sqlite3.Error:
            # Fallback: scan and delete if JSON extraction not supported
            entries = self.load_all()
            deleted_count = 0
            for entry in entries:
                if entry.get('user_id') == user_id:
                    if self.delete(entry.get('id', '')):
                        deleted_count += 1
            return deleted_count > 0

    def get_deleted_count(self) -> int:
        """
        Get count of deleted entries.
        
        Returns:
            Number of deleted entries (always 0 for SQLite as it doesn't track deletions)
        """
        # PATCH: Cursor-2024-12-19 ET-001 Step 4 - Add get_deleted_count method for SQLite
        # SQLite doesn't track deletion counts, so we return 0 as a safe default
        return 0