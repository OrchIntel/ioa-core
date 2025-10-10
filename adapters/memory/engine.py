""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

# PATCH: Cursor-2025-01-27 DISPATCH-GPT-20250825-031 <memory engine modularization>

from .core import (
    MemoryEntry, MemoryStats, MemoryEngineInterface, 
    MemoryError, StorageError, ProcessingError
)
from .hot_store import HotStore
from .cold_store_adapter import ColdStoreAdapter
from .gdpr import GDPRCompliance
from .redaction import RedactionEngine

class ModularMemoryEngine(MemoryEngineInterface):
    """Modular memory engine with hot/cold storage and compliance features."""
    
    def __init__(
        self,
        hot_store: Optional[HotStore] = None,
        cold_store: Optional[ColdStoreAdapter] = None,
        enable_gdpr: bool = True,
        enable_redaction: bool = True,
        enable_monitoring: bool = True
    ):
        """
        Initialize modular memory engine.
        
        Args:
            hot_store: Hot storage implementation
            cold_store: Cold storage adapter
            enable_gdpr: Enable GDPR compliance
            enable_redaction: Enable content redaction
            enable_monitoring: Enable performance monitoring
        """
        self.logger = logging.getLogger(__name__)
        self.enable_monitoring = enable_monitoring
        
        # Initialize storage backends
        self.hot_store = hot_store or HotStore()
        self.cold_store = cold_store or ColdStoreAdapter()
        
        # Initialize compliance modules
        self.gdpr = GDPRCompliance() if enable_gdpr else None
        self.redaction = RedactionEngine() if enable_redaction else None
        
        # Performance monitoring
        self._stats = MemoryStats()
        self._operation_times: List[float] = []
        
        self.logger.info("ModularMemoryEngine initialized successfully")
    
    def store(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store content in memory."""
        start_time = datetime.now()
        
        try:
            # Generate entry ID
            entry_id = str(uuid.uuid4())
            
            # Create memory entry
            entry = MemoryEntry(
                id=entry_id,
                content=content,
                metadata=metadata or {},
                timestamp=datetime.now(timezone.utc)
            )
            
            # Apply redaction if enabled
            if self.redaction:
                redaction_result = self.redaction.redact_content(content, metadata)
                if redaction_result.redaction_score > 0:
                    entry.content = redaction_result.redacted_content
                    entry.metadata["redaction_applied"] = True
                    entry.metadata["redaction_score"] = redaction_result.redaction_score
                    entry.metadata["redactions"] = redaction_result.redactions_applied
                    self.logger.info(f"Applied redaction to entry {entry_id}, score: {redaction_result.redaction_score}")
            
            # Identify data subject for GDPR if enabled
            if self.gdpr:
                data_subject_id = self.gdpr.identify_data_subject(content, metadata or {})
                if data_subject_id:
                    entry.metadata["data_subject_id"] = data_subject_id
                    entry.metadata["gdpr_tracked"] = True
            
            # Determine storage tier
            storage_tier = self._determine_storage_tier(entry)
            entry.storage_tier = storage_tier
            
            # Store in appropriate backend
            if storage_tier == "hot":
                success = self.hot_store.store(entry)
            else:
                success = self.cold_store.store(entry)
            
            if not success:
                raise StorageError(f"Failed to store entry {entry_id}", "store", entry_id)
            
            # Update statistics
            self._update_stats("store", entry)
            
            self.logger.info(f"Stored entry {entry_id} in {storage_tier} storage")
            return entry_id
            
        except Exception as e:
            self._update_stats("store_failed")
            self.logger.error(f"Failed to store content: {e}")
            raise
        
        finally:
            self._record_operation_time(start_time)
    
    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve content from memory."""
        start_time = datetime.now()
        
        try:
            # Try hot storage first
            entry = self.hot_store.retrieve(entry_id)
            
            if entry is None and self.cold_store.is_available():
                # Fallback to cold storage
                entry = self.cold_store.retrieve(entry_id)
                
                if entry:
                    # Move to hot storage for faster future access
                    entry.storage_tier = "hot"
                    self.hot_store.store(entry)
                    self.logger.debug(f"Moved entry {entry_id} from cold to hot storage")
            
            if entry:
                self._update_stats("retrieve", entry)
                self.logger.debug(f"Retrieved entry {entry_id}")
            
            return entry
            
        except Exception as e:
            self._update_stats("retrieve_failed")
            self.logger.error(f"Failed to retrieve entry {entry_id}: {e}")
            return None
        
        finally:
            self._record_operation_time(start_time)
    
    def search(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """Search memory for content."""
        start_time = datetime.now()
        
        try:
            # Search hot storage
            results = self.hot_store.search(query, limit)
            
            # If cold storage is available and we need more results
            if len(results) < limit and self.cold_store.is_available():
                cold_results = self.cold_store.search(query, limit - len(results))
                results.extend(cold_results)
            
            self._update_stats("search", results=len(results))
            self.logger.debug(f"Search returned {len(results)} results for query: {query}")
            
            return results
            
        except Exception as e:
            self._update_stats("search_failed")
            self.logger.error(f"Search failed for query '{query}': {e}")
            return []
        
        finally:
            self._record_operation_time(start_time)
    
    def delete(self, entry_id: str) -> bool:
        """Delete content from memory."""
        start_time = datetime.now()
        
        try:
            # Delete from both storage backends
            hot_success = self.hot_store.delete(entry_id)
            cold_success = self.cold_store.delete(entry_id)
            
            success = hot_success or cold_success
            
            if success:
                self._update_stats("delete")
                self.logger.info(f"Deleted entry {entry_id}")
            else:
                self.logger.warning(f"Entry {entry_id} not found for deletion")
            
            return success
            
        except Exception as e:
            self._update_stats("delete_failed")
            self.logger.error(f"Failed to delete entry {entry_id}: {e}")
            return False
        
        finally:
            self._record_operation_time(start_time)
    
    def get_stats(self) -> MemoryStats:
        """Get memory system statistics."""
        try:
            # Combine stats from all components
            hot_stats = self.hot_store.get_stats()
            cold_stats = self.cold_store.get_stats()
            
            # Merge statistics
            combined_stats = MemoryStats(
                total_entries=hot_stats.total_entries + cold_stats.total_entries,
                storage_tier_distribution={
                    "hot": hot_stats.total_entries,
                    "cold": cold_stats.total_entries
                }
            )
            
            # Add performance metrics
            if self._operation_times:
                combined_stats.avg_processing_time = sum(self._operation_times) / len(self._operation_times)
            
            # Add GDPR stats if available
            if self.gdpr:
                gdpr_requests = self.gdpr.list_gdpr_requests()
                combined_stats.metadata = {
                    "gdpr_requests_total": len(gdpr_requests),
                    "gdpr_requests_pending": len([r for r in gdpr_requests if r.status == "pending"]),
                    "gdpr_requests_completed": len([r for r in gdpr_requests if r.status == "completed"])
                }
            
            return combined_stats
            
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return MemoryStats()
    
    def cleanup(self) -> bool:
        """Perform memory cleanup operations."""
        try:
            # Clean up hot storage cache
            self.hot_store.clear_cache()
            
            # Clean up expired GDPR requests
            if self.gdpr:
                self.gdpr.cleanup_expired_requests()
            
            # Sync hot storage with database
            self.hot_store.sync_cache()
            
            self.logger.info("Memory cleanup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Memory cleanup failed: {e}")
            return False
    
    def _determine_storage_tier(self, entry: MemoryEntry) -> str:
        """Determine appropriate storage tier for an entry."""
        # Simple tiering logic - can be enhanced with ML-based decisions
        
        # Check metadata for explicit tier preference
        if "storage_tier" in entry.metadata:
            return entry.metadata["storage_tier"]
        
        # Size-based tiering
        content_size = len(entry.content)
        if content_size > 10000:  # Large content goes to cold storage
            return "cold"
        
        # Access pattern tiering
        if entry.metadata.get("frequently_accessed", False):
            return "hot"
        
        # Default to hot storage
        return "hot"
    
    def _update_stats(self, operation: str, entry: Optional[MemoryEntry] = None, results: Optional[int] = None):
        """Update operation statistics."""
        if not self.enable_monitoring:
            return
        
        if operation == "store":
            self._stats.total_entries += 1
            if entry and entry.storage_tier == "hot":
                self._stats.preserved_entries += 1
            else:
                self._stats.digested_entries += 1
        elif operation == "retrieve":
            if entry:
                entry.access_count += 1
                entry.last_accessed = datetime.now(timezone.utc)
        elif operation == "search":
            if results is not None:
                self._stats.pattern_match_rate = results / max(self._stats.total_entries, 1)
        elif operation.endswith("_failed"):
            self._stats.failed_entries += 1
    
    def _record_operation_time(self, start_time: datetime):
        """Record operation execution time."""
        if not self.enable_monitoring:
            return
        
        duration = (datetime.now() - start_time).total_seconds()
        self._operation_times.append(duration)
        
        # Keep only recent operation times
        if len(self._operation_times) > 100:
            self._operation_times = self._operation_times[-50:]
    
    def get_gdpr_compliance(self) -> Optional[GDPRCompliance]:
        """Get GDPR compliance handler."""
        return self.gdpr
    
    def get_redaction_engine(self) -> Optional[RedactionEngine]:
        """Get redaction engine."""
        return self.redaction
    
    def migrate_to_cold_storage(self, entry_id: str) -> bool:
        """Migrate an entry from hot to cold storage."""
        try:
            # Retrieve from hot storage
            entry = self.hot_store.retrieve(entry_id)
            if not entry:
                return False
            
            # Store in cold storage
            if self.cold_store.store(entry):
                # Delete from hot storage
                self.hot_store.delete(entry_id)
                entry.storage_tier = "cold"
                self.logger.info(f"Migrated entry {entry_id} to cold storage")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to migrate entry {entry_id} to cold storage: {e}")
            return False
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about storage backends."""
        return {
            "hot_store": {
                "type": "sqlite_cache",
                "available": True,
                "max_cache_size": getattr(self.hot_store, 'max_cache_size', 'unknown')
            },
            "cold_store": self.cold_store.get_storage_info() if self.cold_store else {"available": False},
            "gdpr_compliance": self.gdpr is not None,
            "redaction": self.redaction is not None
        }
