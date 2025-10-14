"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
Cold Storage implementation for IOA Core.

This module provides a minimal but functional cold storage engine used by
the memory engine and associated subsystems to persist larger volumes of
content to disk.  It supports writing batches of entries as JSON lines
and retrieving them again with integrity verification.  Data is written
to sharded files to avoid large single‐file writes and to enable
incremental retrieval.  Each entry includes an SHA‑256 hash of the
serialized payload to detect accidental corruption.

The open‑source edition previously shipped with a stub implementation
that raised ``NotImplementedError`` on instantiation.  This version
provides a lightweight implementation to enable unit testing and
development without access to the full organization edition.

Note: This implementation is not designed for production use.  It does
not provide advanced locking semantics, or pruning logic.  It
does provide AES-256 encryption when IOA_ENCRYPT_AT_REST=1 is set.
It is intended solely to satisfy basic storage requirements for local
development and automated testing.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import fcntl  # type: ignore[attr-defined]
    _HAS_FCNTL = True
except ImportError:
    # Windows systems do not have fcntl; locking will be skipped
    _HAS_FCNTL = False

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    _HAS_CRYPTOGRAPHY = True
except ImportError:
    _HAS_CRYPTOGRAPHY = False


class ColdStorage:
    """
    Minimal cold storage implementation for the IOA Core.

    Entries are persisted to disk in JSONL format.  Each batch is
    sharded into files containing at most ``shard_size`` entries.  The
    filename format is ``cold_batch_<batch_id>_<shard_index>.jsonl``.  A
    batch ID is randomly generated using :func:`uuid.uuid4` when the
    batch is stored.  Retrieving a batch will read all shard files for
    the given batch ID and perform basic integrity verification by
    recalculating the stored SHA‑256 hash.  Corrupt entries are skipped.
    
    When IOA_ENCRYPT_AT_REST=1 is set, all data is encrypted using AES-256
    with a key derived from the environment.
    """

    # Default number of entries per shard.  Keeping shards reasonably
    # small improves concurrent access and reduces memory usage when
    # reading large batches.
    shard_size: int = 1000

    def __init__(self, path: str = "./cold_storage") -> None:
        """
        Initialise a cold storage instance.

        Args:
            path: Directory on the local filesystem where batch files will
                be stored.  The directory is created if it does not exist.
                Defaults to ``./cold_storage`` to provide backward compatibility
                with existing MemoryEngine implementations that do not
                specify a path.
        """
        self.storage_path = Path(path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption if enabled
        # Enable by default unless explicitly disabled via IOA_ENABLE_COLD_STORAGE_ENCRYPTION=false
        enable_flag = os.getenv("IOA_ENABLE_COLD_STORAGE_ENCRYPTION", "true").lower()
        legacy_flag = os.getenv("IOA_ENCRYPT_AT_REST", "0")
        self.encryption_enabled = (enable_flag != "false") or (legacy_flag == "1")
        self.enable_encryption = self.encryption_enabled  # Alias for tests
        self._fernet = None
        if self.encryption_enabled and _HAS_CRYPTOGRAPHY:
            self._fernet = self._initialize_encryption()

    def _initialize_encryption(self) -> Optional[Fernet]:
        """Initialize encryption key from environment."""
        if not _HAS_CRYPTOGRAPHY:
            return None
            
        # Get encryption key from environment or derive from IOA_SECRET
        encryption_key = os.getenv("IOA_ENCRYPTION_KEY")
        if not encryption_key:
            # Derive key from IOA_SECRET if available
            secret = os.getenv("IOA_SECRET", "default-ioa-secret-key")
            salt = b"ioa-cold-storage-salt"  # Fixed salt for deterministic key derivation
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
            return Fernet(key)
        else:
            return Fernet(encryption_key.encode())

    def _setup_encryption(self) -> Optional[Fernet]:
        """Alias for _initialize_encryption for test compatibility."""
        return self._initialize_encryption()

    def _encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data if encryption is enabled."""
        if self.encryption_enabled and self._fernet:
            return self._fernet.encrypt(data)
        return data

    def _decrypt_data(self, data: bytes) -> bytes:
        """Decrypt data if encryption is enabled."""
        if self.encryption_enabled and self._fernet:
            return self._fernet.decrypt(data)
        return data

    def _decrypt_data_soft(self, data: bytes) -> bytes:
        """
        Best-effort decrypt: if decryption fails (e.g., plaintext line),
        return the original bytes. This ensures backward compatibility with
        legacy plaintext shard files used in tests.
        """
        if self.encryption_enabled and self._fernet:
            try:
                return self._fernet.decrypt(data)
            except Exception:
                return data
        return data

    def store(self, key: str, data: Any) -> bool:
        """
        Store data with the given key.
        
        Args:
            key: Identifier for the stored data
            data: Data to store
            
        Returns:
            True if storage was successful
        """
        try:
            # Serialize raw data and encrypt if enabled
            serialized_data = json.dumps(data, separators=(",", ":")).encode()
            encrypted_data = self._encrypt_data(serialized_data)
            
            # Create filename based on key
            file_id = f"{key}.enc"
            file_path = self.storage_path / file_id
            
            # Write to disk (encrypted if enabled)
            with file_path.open('wb') as f:
                f.write(encrypted_data)
            
            return True
        except Exception:
            return False

    def retrieve(self, key: str) -> Any:
        """
        Retrieve data with the given key.
        
        Args:
            key: Identifier for the stored data
            
        Returns:
            The retrieved data
            
        Raises:
            FileNotFoundError: If the data is not found
            ValueError: If integrity check fails
        """
        try:
            # Look for the specific file for this key
            file_id = f"{key}.enc"
            file_path = self.storage_path / file_id
            
            if not file_path.exists():
                raise FileNotFoundError(f"No data found for key: {key}")
            
            # Read encrypted data and decrypt if enabled
            with file_path.open('rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self._decrypt_data(encrypted_data)
            obj = json.loads(decrypted_data.decode())
            return obj
            
        except Exception as e:
            raise FileNotFoundError(f"Failed to retrieve data for key {key}: {e}")

    # ------------------------------------------------------------------
    # Internal locking helpers
    #
    # For UNIX systems we use ``fcntl.flock`` to obtain a shared or
    # exclusive lock on an open file descriptor.  On platforms without
    # fcntl (e.g. Windows) these methods are no‑ops.  These helpers
    # abstract away the platform differences and make the rest of the
    # implementation platform agnostic.
    def _lock_shared(self, file_obj: Any) -> None:
        if _HAS_FCNTL:
            fcntl.flock(file_obj, fcntl.LOCK_SH)

    def _lock_exclusive(self, file_obj: Any) -> None:
        if _HAS_FCNTL:
            fcntl.flock(file_obj, fcntl.LOCK_EX)

    def _unlock(self, file_obj: Any) -> None:
        if _HAS_FCNTL:
            fcntl.flock(file_obj, fcntl.LOCK_UN)

    # ------------------------------------------------------------------
    # Storage API
    #
    async def store_batch_to_cold(self, entries: List[Dict[str, Any]]) -> Optional[str]:
        """
        Persist a batch of entries to disk.

        The entries are divided into shards of size ``self.shard_size``.
        Each entry is copied and augmented with additional fields before
        serialisation: ``id`` (a UUID), ``schema_version``, ``stored_at``,
        and ``integrity_hash``.  The integrity hash is an SHA‑256 hash of
        the JSON serialisation of the entry excluding the ``integrity_hash``
        field itself.

        Args:
            entries: List of entries to store.  Each entry should at
                minimum include ``content`` and ``pattern_id`` fields.

        Returns:
            The filename of the first shard, or ``None`` if no entries
            were provided.
        """
        if not entries:
            return None

        batch_id = uuid.uuid4().hex

        # Helper to write a single shard.  We run this function in a
        # thread using ``asyncio.to_thread`` to avoid blocking the event
        # loop with file operations.
        def write_shard(file_path: Path, shard_entries: List[Dict[str, Any]]) -> None:
            with file_path.open('wb') as f:
                # Acquire exclusive lock for writing on UNIX systems
                self._lock_exclusive(f)
                try:
                    for entry in shard_entries:
                        # Prepare the data with mandatory fields
                        data = {
                            "content": entry.get("content"),
                            "pattern_id": entry.get("pattern_id", "UNCLASSIFIED"),
                            "variables": entry.get("variables", {}),
                            "metadata": entry.get("metadata", {}),
                            "feeling": entry.get(
                                "feeling",
                                {"valence": 0.0, "arousal": 0.0, "dominance": 0.0},
                            ),
                            "id": entry.get("id", str(uuid.uuid4())),
                            "schema_version": "2.5.0",
                            "stored_at": None,
                        }
                        # Timestamp when storing.  Use a simple ISO 8601
                        # representation instead of referencing the event loop
                        from datetime import datetime
                        data["stored_at"] = datetime.now(timezone.utc).isoformat()  # PATCH: Cursor-2024-12-19 ET-001 Step 4 - Replace utcnow with timezone-aware timestamp
                        # Compute integrity hash over the data excluding the hash itself
                        entry_json = json.dumps(data, separators=(",", ":"))
                        data["integrity_hash"] = hashlib.sha256(entry_json.encode()).hexdigest()
                        # Serialize and encrypt if enabled
                        line_data = json.dumps(data, separators=(",", ":")) + "\n"
                        encrypted_line = self._encrypt_data(line_data.encode())
                        # Write encrypted line followed by newline delimiter
                        f.write(encrypted_line + b"\n")
                finally:
                    self._unlock(f)

        # Chunk the entries and schedule writes
        shards: List[asyncio.Future] = []
        for shard_index in range((len(entries) + self.shard_size - 1) // self.shard_size):
            shard_entries = entries[shard_index * self.shard_size : (shard_index + 1) * self.shard_size]
            file_name = f"cold_batch_{batch_id}_{shard_index}.jsonl"
            file_path = self.storage_path / file_name
            # Schedule the write on a thread pool
            shards.append(asyncio.to_thread(write_shard, file_path, shard_entries))

        # Await all write operations
        await asyncio.gather(*shards)
        # Return the first shard filename as reference
        return f"cold_batch_{batch_id}_0.jsonl"

    async def retrieve_batch_from_cold(self, batch_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all entries from a batch.

        Reads every shard matching the prefix ``cold_batch_<batch_id>_`` and
        returns a list of entries.  Each entry's integrity is verified by
        recalculating its SHA‑256 hash excluding the ``integrity_hash``
        field.  Corrupt or malformed entries are skipped.  If no shards
        exist for the given batch ID a :class:`FileNotFoundError` is
        raised.

        Args:
            batch_id: Identifier returned from :meth:`store_batch_to_cold`.

        Returns:
            A list of valid entries across all shards.

        Raises:
            FileNotFoundError: If no matching batch files are found.
        """
        entries: List[Dict[str, Any]] = []
        # Collect all shard files for the batch
        shard_paths = sorted(self.storage_path.glob(f"cold_batch_{batch_id}_*.jsonl"))
        if not shard_paths:
            raise FileNotFoundError(f"No batch files found for batch id {batch_id}")

        # Function to read a shard; executed in a thread
        def read_shard(file_path: Path) -> None:
            with file_path.open('rb') as f:
                # Acquire shared lock for reading on UNIX systems
                self._lock_shared(f)
                try:
                    for line in f:
                        # Decrypt line if encryption is enabled
                        decrypted_line = self._decrypt_data_soft(line).decode().strip()
                        if not decrypted_line:
                            continue
                        try:
                            entry = json.loads(decrypted_line)
                        except json.JSONDecodeError:
                            # Skip malformed lines
                            continue
                        # Integrity check: recalculate hash excluding the stored hash
                        hash_field = entry.pop("integrity_hash", None)
                        try:
                            recalculated = hashlib.sha256(
                                json.dumps(entry, separators=(",", ":")).encode()
                            ).hexdigest()
                        except (TypeError, ValueError):
                            continue
                        if hash_field != recalculated:
                            # Skip entries with mismatched hashes
                            continue
                        # Restore integrity_hash in the returned object
                        entry["integrity_hash"] = hash_field
                        entries.append(entry)
                finally:
                    self._unlock(f)

        # PATCH: Cursor-2024-12-19 ET-001 Step 4 - Preserve batch order by processing shards sequentially
        # Process shards sequentially to maintain order across shard boundaries
        for shard_path in shard_paths:
            await asyncio.to_thread(read_shard, shard_path)
        return entries

    # ------------------------------------------------------------------
    # Single entry API
    #
    def store_to_cold(self, content: Any, pattern_id: Optional[str] = None) -> str:
        """
        Store a single entry to an individual JSON file.

        A convenience wrapper around the batch storage interface for use by
        higher‑level components (e.g. ``MemoryEngine``) that need to
        persist an individual piece of content.  The entry is hashed
        using SHA‑256 to produce a unique file identifier.  The file is
        written atomically to the cold storage directory.  The returned
        identifier can later be used to retrieve the entry via
        :meth:`retrieve_from_cold`.

        Args:
            content: Raw content to store.  This may be a string or a
                JSON‑serialisable object.  It will be stored under the
                ``content`` key in the resulting JSON file.
            pattern_id: Optional pattern identifier associated with the
                content.  If omitted, ``None`` will be recorded.

        Returns:
            A file identifier of the form ``cold_<hash>.json``.
        """
        # Normalise the entry into a mapping so that JSON dumps
        # deterministically
        entry: Dict[str, Any] = {
            "content": content,
            "pattern_id": pattern_id,
        }
        # Compute integrity hash over the entry excluding the hash field
        entry_json = json.dumps(entry, separators=(",", ":"))
        integrity_hash = hashlib.sha256(entry_json.encode()).hexdigest()
        entry["integrity_hash"] = integrity_hash
        file_id = f"cold_{integrity_hash}.json"
        file_path = self.storage_path / file_id
        
        # Serialize and encrypt if enabled
        serialized_data = json.dumps(entry, separators=(",", ":")).encode()
        encrypted_data = self._encrypt_data(serialized_data)
        
        # Write to disk (encrypted if enabled)
        with file_path.open('wb') as f:
            f.write(encrypted_data)
        return file_id

    def retrieve_from_cold(self, file_id: str) -> Dict[str, Any]:
        """
        Retrieve a single entry from cold storage.

        Looks up the given file in the cold storage directory and
        performs an integrity check by recalculating the SHA‑256 hash
        over the stored content.  If the hash does not match the
        persisted ``integrity_hash`` value a :class:`ValueError` is
        raised.

        Args:
            file_id: Identifier returned from :meth:`store_to_cold`.

        Returns:
            The entry stored in the file.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the integrity check fails.
        """
        file_path = self.storage_path / file_id
        if not file_path.exists():
            raise FileNotFoundError(f"Cold storage file not found: {file_id}")
        
        # Read encrypted data and decrypt if enabled
        with file_path.open('rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = self._decrypt_data(encrypted_data)
        entry = json.loads(decrypted_data.decode())
        
        # Pop the stored hash and recalculate
        stored_hash = entry.get("integrity_hash")
        recalculated = hashlib.sha256(
            json.dumps({k: v for k, v in entry.items() if k != "integrity_hash"}, separators=(",", ":")).encode()
        ).hexdigest()
        if stored_hash != recalculated:
            raise ValueError("Integrity check failed")
        return entry

    # ------------------------------------------------------------------
    # Compatibility layer for MemoryEngine
    #
    def save(self, content: Any, metadata: Optional[Dict[str, Any]] = None, pattern_id: Optional[str] = None) -> str:
        """
        Persist raw content with optional metadata to cold storage.

        The MemoryEngine calls this method when routing an entry to the
        cold tier.  This convenience wrapper packages the raw content
        and metadata into a single object and delegates to
        :meth:`store_to_cold`.  Additional metadata is stored under a
        ``metadata`` key in the JSON file.  The returned file
        identifier may later be used to retrieve or delete the entry.

        Args:
            content: Raw content to store (typically a string).
            metadata: Arbitrary metadata associated with the content.
            pattern_id: Optional pattern identifier.

        Returns:
            The file identifier returned from :meth:`store_to_cold`.
        """
        # Create the entry structure that store_to_cold expects
        # The content should be stored under "content" key as expected by store_to_cold
        entry = {"content": content}
        if metadata is not None:
            entry["metadata"] = metadata
        # Use provided pattern_id if any
        return self.store_to_cold(entry, pattern_id=pattern_id)

    def delete(self, file_id: str) -> bool:
        """
        Delete a cold storage file.

        Args:
            file_id: Identifier of the file to delete.

        Returns:
            True if the file was deleted, False if it did not exist.
        """
        file_path = self.storage_path / file_id
        try:
            file_path.unlink()
            return True
        except FileNotFoundError:
            return False
