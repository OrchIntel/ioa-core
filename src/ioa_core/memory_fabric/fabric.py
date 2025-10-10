# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.



import os
import logging
import asyncio
import zlib
import sqlite3
"""Fabric module."""

import json
import hashlib
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone
from contextlib import nullcontext

from .schema import MemoryRecordV1, MemoryType, StorageTier
from .stores.base import MemoryStore
from .stores.local_jsonl import LocalJSONLStore
from .stores.sqlite import SQLiteStore
from .stores.s3 import S3Store
from .crypto import MemoryCrypto
from .metrics import MemoryFabricMetrics, MetricsCollector
from .tiering_4d import Tier4D, Tier4DConfig

# PATCH: Cursor-2025-09-10 DISPATCH-OSS-20250910-MEMORY-FABRIC-REFACTOR <main fabric>

class MemoryFabric:
    """Main Memory Fabric facade providing CRUD and query operations."""
    
    def __init__(
        self,
        backend: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        encryption_key: Optional[str] = None,
        enable_metrics: bool = True
    ):
        # Durability settings
        self.durability_enabled = False
        self.durability_checksums = {}

        # Performance optimization flags (default to current behavior)
        self.perf_tune_enabled = os.getenv("IOA_PERF_TUNE", "0") == "1"
        self.commit_every = int(os.getenv("IOA_COMMIT_EVERY", "1"))
        self.precompile_schema = os.getenv("IOA_PRECOMPILE_SCHEMA", "0") == "1"
        self.fourd_cache_size = int(os.getenv("IOA_4D_CACHE_SIZE", "0"))
        
        # Sharding configuration
        self.shards = int(os.getenv("IOA_SHARDS", "1"))
        self.stage_size = int(os.getenv("IOA_STAGE_SIZE", "20000"))
        self.progress_telemetry = int(os.getenv("IOA_PROGRESS_T", "10"))  # Progress every N seconds

        # Performance optimization state
        self._pending_commits = []
        self._schema_validators = {}
        self._fourd_cache = {}
        
        # Sharding state
        self._stores = []
        self._shard_connections = []
        self._shard_writers = []
        self._shard_queues = []

        """
        Initialize Memory Fabric.
        
        Args:
            backend: Storage backend ('local_jsonl', 'sqlite', 's3')
            config: Backend-specific configuration
            encryption_key: Optional encryption key for AES-GCM
            enable_metrics: Enable metrics collection
        """
        self.logger = logging.getLogger(__name__)
        
        # Get backend from environment or parameter
        self.backend_name = backend or os.getenv("IOA_FABRIC_BACKEND", "local_jsonl")
        
        # Get root directory from environment
        self.root_dir = os.getenv("IOA_FABRIC_ROOT", "./artifacts/memory/")
        
        # Initialize configuration
        self.config = config or {}
        self.config.setdefault("data_dir", self.root_dir)

        # Pass performance tuning flags to store
        self.config.update({
            "perf_tune_enabled": self.perf_tune_enabled,
            "commit_every": self.commit_every
        })
        
        # Initialize encryption
        self.crypto = MemoryCrypto(encryption_key or os.getenv("IOA_FABRIC_KEY"))
        
        # Initialize metrics
        self.metrics = MemoryFabricMetrics() if enable_metrics else None
        if self.metrics:
            self.metrics.set_backend(self.backend_name)
            self.metrics.set_encryption_mode(self.crypto.get_encryption_mode())

        # Initialize 4D-Tiering (production-enabled with profiles)
        # Default ON for v1.2, with profile-based configuration
        self.use_4d_tiering = os.getenv("USE_4D_TIERING", "true").lower() == "true"
        self.tiering_profile = os.getenv("IOA_4D_PROFILE", "balanced")  # throughput, governance, balanced

        if self.use_4d_tiering:
            # Configure tiering based on profile
            if self.tiering_profile == "throughput":
                # Relaxed weights for better performance
                tiering_config = Tier4DConfig(
                    max_age_hours=12.0,  # Faster cooling
                    jurisdiction_boost=0.15,  # Reduced boost
                    risk_boost=0.3,  # Lower risk priority
                    hot_threshold=1.5  # Easier to reach hot
                )
            elif self.tiering_profile == "governance":
                # Strict settings for compliance
                tiering_config = Tier4DConfig(
                    max_age_hours=168.0,  # Week-long retention
                    jurisdiction_boost=0.4,  # Strong jurisdiction boost
                    risk_boost=0.7,  # High risk priority
                    hot_threshold=1.0  # Harder to reach hot
                )
            else:  # balanced (default)
                tiering_config = Tier4DConfig()  # Standard config

            # Load policy reference from environment or config
            policy_ref = {
                "jurisdiction": os.getenv("IOA_POLICY_JURISDICTION", "global")
            }
            self.tiering_engine = Tier4D(config=tiering_config, policy_ref=policy_ref)
            self.logger.info(f"4D-Tiering enabled (profile: {self.tiering_profile})")
        else:
            self.tiering_engine = None
            self.logger.info("4D-Tiering disabled")

        # Precompile schemas if enabled
        if self.precompile_schema:
            try:
                import jsonschema
                # Import audit schema and precompile validator
                from ..governance.audit_chain import AUDIT_SCHEMA
                self._schema_validators['audit'] = jsonschema.Draft7Validator(AUDIT_SCHEMA)
                self.logger.info("Precompiled audit schema validator")
            except ImportError:
                self.logger.warning("jsonschema not available, schema precompilation disabled")
            except Exception as e:
                self.logger.warning(f"Schema precompilation failed: {e}")

        # Initialize store
        self._store = self._create_store()
        
        # Initialize sharding if enabled
        if self.shards > 1:
            self._initialize_sharding()
            self._start_shard_writers()
        
        self.logger.info(f"Memory Fabric initialized with {self.backend_name} backend")
        if self.shards > 1:
            self.logger.info(f"Sharding enabled with {self.shards} shards, stage size {self.stage_size}")
        if self.crypto.is_encryption_enabled():
            self.logger.info("Encryption enabled with AES-GCM")
    
    def _create_store(self) -> MemoryStore:
        """Create the appropriate store based on backend."""
        if self.backend_name == "local_jsonl":
            return LocalJSONLStore(self.config)
        elif self.backend_name == "sqlite":
            return SQLiteStore(self.config)
        elif self.backend_name == "s3":
            return S3Store(self.config)
        else:
            raise ValueError(f"Unknown backend: {self.backend_name}")
    
    def _initialize_sharding(self):
        """Initialize sharded SQLite connections for high-scale operations."""
        try:
            # Create shard databases
            for i in range(self.shards):
                db_path = os.path.join(self.config.get("data_dir", "./artifacts/memory/"), f"mf_shard_{i}.db")
                
                # Create connection with performance tuning
                conn = sqlite3.connect(db_path, timeout=30.0)
                
                # Apply performance PRAGMAs
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=-8192")
                conn.execute("PRAGMA temp_store=MEMORY")
                conn.execute("PRAGMA mmap_size=268435456")
                conn.execute("PRAGMA busy_timeout=5000")
                
                # Create table if not exists with blake3 primary key for uniqueness
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS memory_records (
                        pk TEXT PRIMARY KEY,
                        id TEXT NOT NULL,
                        content TEXT NOT NULL,
                        metadata TEXT NOT NULL,
                        tags TEXT,
                        memory_type TEXT,
                        storage_tier TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create unique index on primary key for deduplication
                conn.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS uq_records_pk ON memory_records(pk)
                """)
                
                # Create indexes for performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_records(memory_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_storage_tier ON memory_records(storage_tier)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON memory_records(created_at)")
                
                self._shard_connections.append(conn)
                
            self.logger.info(f"Initialized {self.shards} shard databases")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize sharding: {e}")
            # Fallback to single store
            self.shards = 1
            self._shard_connections = []
    
    def _generate_record_pk(self, record_data: Dict[str, Any]) -> str:
        """Generate blake3 primary key for record uniqueness."""
        # Create canonical JSON representation
        canonical_data = {
            "content": record_data.get("content", ""),
            "metadata": record_data.get("metadata", {}),
            "tags": record_data.get("tags", []),
            "memory_type": record_data.get("memory_type", "conversation"),
            "storage_tier": record_data.get("storage_tier", "hot")
        }
        
        # Sort keys for consistent hashing
        canonical_json = json.dumps(canonical_data, sort_keys=True, separators=(',', ':'))
        
        # Generate blake3 hash (32 bytes = 64 hex chars)
        blake3_hash = hashlib.blake2b(canonical_json.encode(), digest_size=32).hexdigest()
        return blake3_hash
    
    def _start_shard_writers(self):
        """Start dedicated asyncio writers for each shard."""
        try:
            for i in range(self.shards):
                # Create queue for this shard
                queue = asyncio.Queue()
                self._shard_queues.append(queue)
                
                # Start writer task
                writer_task = asyncio.create_task(self._shard_writer(i, queue))
                self._shard_writers.append(writer_task)
                
            self.logger.info(f"Started {self.shards} shard writers")
            
        except Exception as e:
            self.logger.error(f"Failed to start shard writers: {e}")
            self._shard_writers = []
            self._shard_queues = []
    
    async def _shard_writer(self, shard_index: int, queue: asyncio.Queue):
        """Dedicated writer for a specific shard."""
        conn = self._shard_connections[shard_index]
        batch_size = self.commit_every
        batch = []
        
        try:
            while True:
                try:
                    # Get record from queue with timeout
                    record_data = await asyncio.wait_for(queue.get(), timeout=1.0)
                    
                    if record_data is None:  # Shutdown signal
                        break
                    
                    batch.append(record_data)
                    
                    # Commit batch when full
                    if len(batch) >= batch_size:
                        await self._commit_shard_batch(conn, batch)
                        batch.clear()
                        
                except asyncio.TimeoutError:
                    # Commit any pending records
                    if batch:
                        await self._commit_shard_batch(conn, batch)
                        batch.clear()
                        
        except Exception as e:
            self.logger.error(f"Shard writer {shard_index} failed: {e}")
        finally:
            # Final commit
            if batch:
                await self._commit_shard_batch(conn, batch)
    
    async def _commit_shard_batch(self, conn, batch):
        """Commit a batch of records to a shard with deduplication."""
        try:
            for record_data in batch:
                pk = record_data['pk']
                record_id = record_data['id']
                content = record_data['content']
                metadata = record_data['metadata']
                tags = record_data['tags']
                memory_type = record_data['memory_type']
                storage_tier = record_data['storage_tier']
                
                # Use INSERT ... ON CONFLICT DO NOTHING for deduplication
                conn.execute("""
                    INSERT OR IGNORE INTO memory_records 
                    (pk, id, content, metadata, tags, memory_type, storage_tier)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (pk, record_id, content, metadata, tags, memory_type, storage_tier))
            
            conn.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to commit shard batch: {e}")
            conn.rollback()
            raise
    
    def store(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        memory_type: Union[str, MemoryType] = MemoryType.CONVERSATION,
        storage_tier: Union[str, StorageTier] = StorageTier.HOT,
        record_id: Optional[str] = None
    ) -> str:
        """
        Store content in memory fabric.
        
        Args:
            content: Content to store
            metadata: Optional metadata
            tags: Optional tags
            memory_type: Type of memory
            storage_tier: Storage tier preference
            record_id: Optional custom record ID
            
        Returns:
            Record ID
        """
        with MetricsCollector(self.metrics, "writes") if self.metrics else nullcontext():
            try:
                # Prepare metadata
                record_metadata = metadata or {}
                record_metadata.update({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "memory_type": memory_type if isinstance(memory_type, str) else memory_type.value,
                })

                # Apply 4D-Tiering if enabled (experimental)
                if self.use_4d_tiering and self.tiering_engine:
                    # Create cache key from metadata for performance optimization
                    cache_key = None
                    if self.fourd_cache_size > 0:
                        # Create deterministic cache key from relevant metadata
                        cache_parts = [
                            record_metadata.get("jurisdiction", ""),
                            record_metadata.get("risk_level", ""),
                            record_metadata.get("memory_type", ""),
                            str(record_metadata.get("content_length", 0))
                        ]
                        cache_key = "|".join(cache_parts)

                        # Check cache first
                        if cache_key in self._fourd_cache:
                            suggested_tier = self._fourd_cache[cache_key]
                            tiering_metrics = {"total_score": 0.5, "dimensions": {"cached": True}}  # Default for cached
                            self.logger.debug(f"4D-Tiering cache hit: {suggested_tier}")
                        else:
                            # Calculate tiering
                            temp_record = type('TempRecord', (), {'metadata': record_metadata})()
                            suggested_tier = self.tiering_engine.classify(temp_record)
                            tiering_metrics = self.tiering_engine.get_tiering_metrics(temp_record)

                            # Cache result (LRU-style by limiting cache size)
                            if len(self._fourd_cache) >= self.fourd_cache_size:
                                # Remove oldest entry (simple FIFO)
                                oldest_key = next(iter(self._fourd_cache))
                                del self._fourd_cache[oldest_key]
                            self._fourd_cache[cache_key] = suggested_tier
                    else:
                        # No caching - calculate directly
                        temp_record = type('TempRecord', (), {'metadata': record_metadata})()
                        suggested_tier = self.tiering_engine.classify(temp_record)
                        tiering_metrics = self.tiering_engine.get_tiering_metrics(temp_record)

                    # Override storage tier with 4D suggestion if different
                    if suggested_tier != storage_tier:
                        # Map 4D tiers to StorageTier enum values
                        tier_mapping = {
                            "HOT": StorageTier.HOT,
                            "WARM": StorageTier.HOT,  # Map WARM to HOT for storage
                            "COLD": StorageTier.COLD
                        }
                        storage_tier = tier_mapping.get(suggested_tier, StorageTier.AUTO)
                        self.logger.debug(f"4D-Tiering adjusted tier to {suggested_tier} (was {storage_tier})")

                    # Add tiering metadata
                    record_metadata.update({
                        "tiering_4d": {
                            "enabled": True,
                            "suggested_tier": suggested_tier,
                            "score": tiering_metrics.get("total_score", 0.5),
                            "dimensions": tiering_metrics.get("dimensions", {})
                        }
                    })

                # Create memory record
                record = MemoryRecordV1(
                    id=record_id or "",
                    content=content,
                    metadata=record_metadata,
                    tags=tags or [],
                    memory_type=MemoryType(memory_type) if isinstance(memory_type, str) else memory_type,
                    storage_tier=StorageTier(storage_tier) if isinstance(storage_tier, str) else storage_tier
                )

                # Encrypt content if encryption is enabled
                if self.crypto.is_encryption_enabled():
                    encrypted_content, encryption_mode = self.crypto.encrypt_content(content)
                    record.content = encrypted_content
                    record.metadata["encryption_mode"] = encryption_mode
                
                # Store record with batch commit optimization
                success = self._store.store(record)
                if not success:
                    raise Exception("Failed to store record")

                # Track checksum for durability if enabled
                if self.durability_enabled:
                    import hashlib
                    checksum = hashlib.sha256(content.encode()).hexdigest()
                    self.durability_checksums[record.id] = checksum

                # Batch commit logic (only if tuning enabled)
                if self.commit_every > 1 and hasattr(self._store, '_connection'):
                    self._pending_commits.append(record.id)
                    if len(self._pending_commits) >= self.commit_every:
                        # Commit the batch
                        self._store._connection.commit()
                        self._pending_commits.clear()
                        self.logger.debug(f"Committed batch of {self.commit_every} records")
                else:
                    # Immediate commit (default behavior)
                    if hasattr(self._store, '_connection'):
                        self._store._connection.commit()

                # Update metrics
                if self.metrics:
                    self.metrics.update_record_count(len(self.list_all()))

                self.logger.debug(f"Stored record {record.id}")
                return record.id

            except Exception as e:
                self.logger.error(f"Failed to store record: {e}")
                raise

    async def store_batch(self, records: List[Dict[str, Any]]) -> List[str]:
        """
        Store multiple records with sharding and batching for high-scale performance.

        Args:
            records: List of record dictionaries with 'content', 'metadata', etc.

        Returns:
            List of record IDs
        """
        if self.shards > 1 and self._shard_connections:
            return await self._store_batch_sharded(records)
        else:
            return await self._store_batch_standard(records)
    
    async def _store_batch_standard(self, records: List[Dict[str, Any]]) -> List[str]:
        """Standard batch storage without sharding."""
        async def store_single(record_data):
            content = record_data.get("content", "")
            metadata = record_data.get("metadata", {})
            tags = record_data.get("tags")
            memory_type = record_data.get("memory_type", MemoryType.CONVERSATION)
            storage_tier = record_data.get("storage_tier", StorageTier.AUTO)

            return self.store(
                content=content,
                metadata=metadata,
                tags=tags,
                memory_type=memory_type,
                storage_tier=storage_tier
            )

        # Execute all stores concurrently
        tasks = [store_single(record) for record in records]
        record_ids = await asyncio.gather(*tasks)

        self.logger.info(f"Batch stored {len(records)} records")
        return record_ids
    
    async def _store_batch_sharded(self, records: List[Dict[str, Any]]) -> List[str]:
        """Sharded batch storage for high-scale operations with integrity fixes."""
        import json
        import time
        
        record_ids = []
        total_records = len(records)
        start_time = time.time()
        last_progress_time = start_time
        
        self.logger.info(f"Starting sharded batch storage of {total_records} records across {self.shards} shards")
        
        # Process records in non-overlapping chunks
        for chunk_start in range(0, total_records, self.stage_size):
            chunk_end = min(chunk_start + self.stage_size, total_records)
            chunk_records = records[chunk_start:chunk_end]
            
            # Prepare records for shard distribution
            shard_tasks = {i: [] for i in range(self.shards)}
            
            for i, record_data in enumerate(chunk_records):
                # Generate blake3 primary key for uniqueness
                pk = self._generate_record_pk(record_data)
                
                # Use xxhash64 for better distribution (fallback to zlib if xxhash not available)
                try:
                    import xxhash
                    shard_index = xxhash.xxh64(pk.encode(), seed=42).intdigest() % self.shards
                except ImportError:
                    # Fallback to zlib if xxhash not available
                    shard_index = zlib.crc32(pk.encode()) % self.shards
                
                # Prepare record for shard storage
                record_id = f"shard_{shard_index}_{chunk_start}_{i}"
                metadata = record_data.get("metadata", {})
                metadata.update({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "shard": shard_index,
                    "chunk": chunk_start // self.stage_size
                })
                
                # Prepare record data for shard writer
                shard_record = {
                    "pk": pk,
                    "id": record_id,
                    "content": record_data.get("content", ""),
                    "metadata": json.dumps(metadata),
                    "tags": json.dumps(record_data.get("tags", [])),
                    "memory_type": record_data.get("memory_type", "conversation"),
                    "storage_tier": record_data.get("storage_tier", "hot")
                }
                
                shard_tasks[shard_index].append(shard_record)
                record_ids.append(record_id)
            
            # Distribute records to shard queues
            for shard_index, shard_records in shard_tasks.items():
                if shard_records:
                    for record in shard_records:
                        await self._shard_queues[shard_index].put(record)
            
            # Progress telemetry
            current_time = time.time()
            if current_time - last_progress_time >= self.progress_telemetry:
                progress_pct = (chunk_end / total_records) * 100
                elapsed = current_time - start_time
                rate = chunk_end / elapsed if elapsed > 0 else 0
                
                progress_data = {
                    "phase": "store",
                    "done": chunk_end,
                    "total": total_records,
                    "progress_pct": round(progress_pct, 2),
                    "elapsed_sec": round(elapsed, 2),
                    "rate_per_sec": round(rate, 2),
                    "shards": self.shards,
                    "stage_size": self.stage_size
                }
                
                self.logger.info(f"Progress: {progress_pct:.1f}% ({chunk_end}/{total_records}) - {rate:.0f} records/sec")
                
                # Write progress to file for external monitoring
                try:
                    with open("progress.log", "a") as f:
                        f.write(json.dumps(progress_data) + "\n")
                except Exception as e:
                    self.logger.warning(f"Failed to write progress log: {e}")
                
                last_progress_time = current_time
        
        # Wait for all shard writers to finish
        await self._flush_shard_writers()
        
        total_time = time.time() - start_time
        rate = total_records / total_time if total_time > 0 else 0
        
        self.logger.info(f"Sharded batch storage completed: {total_records} records in {total_time:.2f}s ({rate:.0f} records/sec)")
        return record_ids
    
    async def _flush_shard_writers(self):
        """Flush all shard writers and wait for completion."""
        try:
            # Send shutdown signals to all writers
            for queue in self._shard_queues:
                await queue.put(None)
            
            # Wait for all writers to complete
            await asyncio.gather(*self._shard_writers, return_exceptions=True)
            
            # WAL checkpoint for all shards
            for conn in self._shard_connections:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                
        except Exception as e:
            self.logger.error(f"Failed to flush shard writers: {e}")
    
    async def _store_to_shard(self, shard_index: int, record_id: str, content: str, 
                            metadata: str, tags: str, memory_type: str, storage_tier: str):
        """Store a single record to a specific shard."""
        try:
            conn = self._shard_connections[shard_index]
            conn.execute("""
                INSERT OR REPLACE INTO memory_records 
                (id, content, metadata, tags, memory_type, storage_tier)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (record_id, content, metadata, tags, memory_type, storage_tier))
        except Exception as e:
            self.logger.error(f"Failed to store record {record_id} to shard {shard_index}: {e}")
            raise

    def retrieve(self, record_id: str) -> Optional[MemoryRecordV1]:
        """
        Retrieve a memory record by ID.
        
        Args:
            record_id: Record ID to retrieve
            
        Returns:
            Memory record or None if not found
        """
        with MetricsCollector(self.metrics, "reads") if self.metrics else nullcontext():
            try:
                record = self._store.retrieve(record_id)
                if not record:
                    return None
                
                # Decrypt content if encrypted
                if self.crypto.is_encryption_enabled() and record.metadata.get("encryption_mode") == "aes-gcm":
                    decrypted_content = self.crypto.decrypt_content(record.content, "aes-gcm")
                    record.content = decrypted_content
                
                self.logger.debug(f"Retrieved record {record_id}")
                return record
                
            except Exception as e:
                self.logger.error(f"Failed to retrieve record {record_id}: {e}")
                return None
    
    def search(
        self,
        query: str,
        limit: int = 10,
        memory_type: Optional[str] = None,
        storage_tier: Optional[str] = None
    ) -> List[MemoryRecordV1]:
        """
        Search for memory records.
        
        Args:
            query: Search query
            limit: Maximum number of results
            memory_type: Filter by memory type
            storage_tier: Filter by storage tier
            
        Returns:
            List of matching records
        """
        with MetricsCollector(self.metrics, "queries") if self.metrics else nullcontext():
            try:
                results = self._store.search(query, limit, memory_type)
                
                # Decrypt results if encryption is enabled
                if self.crypto.is_encryption_enabled():
                    for record in results:
                        if record.metadata.get("encryption_mode") == "aes-gcm":
                            decrypted_content = self.crypto.decrypt_content(record.content, "aes-gcm")
                            record.content = decrypted_content
                
                # Filter by storage tier if specified
                if storage_tier:
                    results = [r for r in results if r.storage_tier.value == storage_tier]
                
                self.logger.debug(f"Search returned {len(results)} results for query: {query}")
                return results
                
            except Exception as e:
                self.logger.error(f"Failed to search: {e}")
                return []
    
    def delete(self, record_id: str) -> bool:
        """
        Delete a memory record.
        
        Args:
            record_id: Record ID to delete
            
        Returns:
            True if deleted, False otherwise
        """
        with MetricsCollector(self.metrics, "writes") if self.metrics else nullcontext():
            try:
                success = self._store.delete(record_id)
                if success and self.metrics:
                    self.metrics.update_record_count(len(self.list_all()))
                
                self.logger.debug(f"Deleted record {record_id}")
                return success
                
            except Exception as e:
                self.logger.error(f"Failed to delete record {record_id}: {e}")
                return False
    
    def list_all(self, limit: Optional[int] = None) -> List[MemoryRecordV1]:
        """
        List all memory records.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of all records
        """
        with MetricsCollector(self.metrics, "reads") if self.metrics else nullcontext():
            try:
                results = self._store.list_all(limit)
                
                # Decrypt results if encryption is enabled
                if self.crypto.is_encryption_enabled():
                    for record in results:
                        if record.metadata.get("encryption_mode") == "aes-gcm":
                            decrypted_content = self.crypto.decrypt_content(record.content, "aes-gcm")
                            record.content = decrypted_content
                
                return results
                
            except Exception as e:
                self.logger.error(f"Failed to list records: {e}")
                return []

    def enable_durability(self, enabled: bool = True):
        """
        Enable or disable durability mode with checksum verification.

        Args:
            enabled: Whether to enable durability checks
        """
        self.durability_enabled = enabled
        if enabled:
            self.durability_checksums = {}
            self.logger.info("Durability mode enabled")
        else:
            self.durability_checksums = {}
            self.logger.info("Durability mode disabled")

    def verify_durability(self) -> bool:
        """
        Verify durability by checking all stored records against checksums.

        Returns:
            True if all records pass durability checks, False otherwise
        """
        if not self.durability_enabled:
            self.logger.warning("Durability verification requested but durability not enabled")
            return False

        try:
            all_records = self.list_all()
            verified_count = 0

            for record in all_records:
                # Calculate current checksum
                import hashlib
                current_checksum = hashlib.sha256(record.content.encode()).hexdigest()

                # Check against stored checksum
                record_id = record.id
                if record_id in self.durability_checksums:
                    stored_checksum = self.durability_checksums[record_id]
                    if current_checksum == stored_checksum:
                        verified_count += 1
                    else:
                        self.logger.error(f"Durability check failed for record {record_id}")
                        return False
                else:
                    # Store checksum for future verification
                    self.durability_checksums[record_id] = current_checksum
                    verified_count += 1

            integrity = (verified_count / len(all_records)) * 100 if all_records else 100
            self.logger.info(f"Durability verification: {verified_count}/{len(all_records)} records ({integrity:.1f}% integrity)")
            return True

        except Exception as e:
            self.logger.error(f"Durability verification failed: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get memory fabric statistics."""
        stats = self._store.get_stats()
        
        if self.metrics:
            metrics = self.metrics.get_current_metrics()
            stats.update(metrics)
        
        return stats
    
    def flush(self):
        """Flush any pending batch commits."""
        if self._pending_commits and hasattr(self._store, '_connection'):
            try:
                self._store._connection.commit()
                self.logger.debug(f"Flushed {len(self._pending_commits)} pending commits")
                self._pending_commits.clear()
            except Exception as e:
                self.logger.error(f"Failed to flush pending commits: {e}")

    def close(self):
        """Close the memory fabric and cleanup resources."""
        # Flush any pending commits before closing
        self.flush()

        # Stop shard writers
        if self._shard_writers:
            try:
                # Send shutdown signals
                for queue in self._shard_queues:
                    asyncio.create_task(queue.put(None))
                
                # Wait for writers to complete
                asyncio.gather(*self._shard_writers, return_exceptions=True)
                
            except Exception as e:
                self.logger.warning(f"Error stopping shard writers: {e}")
            finally:
                self._shard_writers.clear()
                self._shard_queues.clear()

        # Close shard connections
        for conn in self._shard_connections:
            try:
                conn.close()
            except Exception as e:
                self.logger.warning(f"Error closing shard connection: {e}")
        self._shard_connections.clear()

        if self._store:
            self._store.close()

        if self.metrics:
            self.logger.info(self.metrics.get_metrics_summary())
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the memory fabric."""
        health = {
            "status": "healthy",
            "backend": self.backend_name,
            "encryption": self.crypto.get_encryption_mode(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Test basic operations
            test_id = self.store("test_health_check", {"test": True})
            retrieved = self.retrieve(test_id)
            
            if retrieved and retrieved.content == "test_health_check":
                health["operations"] = "working"
                self.delete(test_id)  # Cleanup
            else:
                health["status"] = "degraded"
                health["operations"] = "failed"
                
        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
        
        return health

# Context manager for null operations
class nullcontext:
    """Null context manager for when metrics are disabled."""
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
