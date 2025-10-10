""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

# PATCH: Cursor-2025-01-27 DISPATCH-GPT-20250825-031 <memory engine modularization>

from .core import MemoryEntry, MemoryStats, MemoryStore, StorageError

try:
    from cold_storage import ColdStorage
    COLD_STORAGE_AVAILABLE = True
except ImportError:
    COLD_STORAGE_AVAILABLE = False
    ColdStorage = None

class ColdStoreAdapter(MemoryStore):
    """Adapter for cold storage system."""
    
    def __init__(self, cold_storage: Optional[ColdStorage] = None):
        """
        Initialize cold store adapter.
        
        Args:
            cold_storage: ColdStorage instance or None to create default
        """
        self.logger = logging.getLogger(__name__)
        
        if not COLD_STORAGE_AVAILABLE:
            self.logger.warning("Cold storage not available, using stub implementation")
            self.cold_storage = None
        else:
            self.cold_storage = cold_storage or ColdStorage()
    
    def store(self, entry: MemoryEntry) -> bool:
        """Store a memory entry in cold storage."""
        if not self.cold_storage:
            self.logger.warning("Cold storage not available, cannot store entry")
            return False
        
        try:
            # Convert MemoryEntry to cold storage format
            cold_data = {
                "id": entry.id,
                "content": entry.content,
                "metadata": entry.metadata,
                "timestamp": entry.timestamp.isoformat(),
                "tags": entry.tags,
                "storage_tier": "cold",
                "access_count": entry.access_count,
                "last_accessed": entry.last_accessed.isoformat() if entry.last_accessed else None
            }
            
            # Store in cold storage
            result = self.cold_storage.store(entry.id, cold_data)
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Failed to store entry {entry.id} in cold storage: {e}")
            raise StorageError(f"Cold storage operation failed: {e}", "store", entry.id)
    
    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry from cold storage."""
        if not self.cold_storage:
            self.logger.warning("Cold storage not available, cannot retrieve entry")
            return None
        
        try:
            # Retrieve from cold storage
            cold_data = self.cold_storage.retrieve(entry_id)
            
            if cold_data is None:
                return None
            
            # Convert to MemoryEntry
            entry = MemoryEntry(
                id=cold_data["id"],
                content=cold_data["content"],
                metadata=cold_data.get("metadata", {}),
                timestamp=datetime.fromisoformat(cold_data["timestamp"]),
                tags=cold_data.get("tags", []),
                storage_tier="cold",
                access_count=cold_data.get("access_count", 0)
            )
            
            if "last_accessed" in cold_data and cold_data["last_accessed"]:
                entry.last_accessed = datetime.fromisoformat(cold_data["last_accessed"])
            
            return entry
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve entry {entry_id} from cold storage: {e}")
            return None
    
    def search(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """Search for memory entries in cold storage."""
        if not self.cold_storage:
            self.logger.warning("Cold storage not available, cannot search")
            return []
        
        try:
            # Note: This is a simplified search - real cold storage might have different search capabilities
            # For now, we'll return an empty list as cold storage typically doesn't support full-text search
            self.logger.info(f"Search in cold storage not fully implemented for query: {query}")
            return []
            
        except Exception as e:
            self.logger.error(f"Search in cold storage failed: {e}")
            return []
    
    def delete(self, entry_id: str) -> bool:
        """Delete a memory entry from cold storage."""
        if not self.cold_storage:
            self.logger.warning("Cold storage not available, cannot delete entry")
            return False
        
        try:
            # Delete from cold storage
            result = self.cold_storage.delete(entry_id)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to delete entry {entry_id} from cold storage: {e}")
            return False
    
    def list_all(self) -> List[MemoryEntry]:
        """List all memory entries in cold storage."""
        if not self.cold_storage:
            self.logger.warning("Cold storage not available, cannot list entries")
            return []
        
        try:
            # Note: This might not be efficient for large cold storage systems
            # Consider implementing pagination or streaming for production use
            self.logger.info("Listing all entries from cold storage (may be slow)")
            
            # This is a placeholder - actual implementation depends on cold storage capabilities
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to list entries from cold storage: {e}")
            return []
    
    def get_stats(self) -> MemoryStats:
        """Get cold storage statistics."""
        if not self.cold_storage:
            return MemoryStats()
        
        try:
            # Get basic stats from cold storage
            # This is a simplified implementation - adjust based on actual cold storage capabilities
            stats = MemoryStats()
            
            # Try to get some basic information
            try:
                # This would need to be implemented based on actual cold storage interface
                # For now, return empty stats
                pass
            except Exception:
                self.logger.debug("Could not retrieve detailed cold storage stats")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get cold storage stats: {e}")
            return MemoryStats()
    
    def migrate_to_cold(self, entry: MemoryEntry) -> bool:
        """Migrate an entry to cold storage."""
        return self.store(entry)
    
    def is_available(self) -> bool:
        """Check if cold storage is available."""
        return COLD_STORAGE_AVAILABLE and self.cold_storage is not None
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about the cold storage system."""
        if not self.is_available():
            return {"available": False, "reason": "Cold storage not available"}
        
        try:
            return {
                "available": True,
                "type": "cold_storage",
                "implementation": self.cold_storage.__class__.__name__
            }
        except Exception as e:
            return {
                "available": False,
                "reason": f"Error getting storage info: {e}"
            }
