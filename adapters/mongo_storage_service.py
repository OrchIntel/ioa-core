"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""


"""
MongoDB Storage Service Implementation

Provides MongoDB-based storage backend for IOA memory system with support
for structured queries, indexing, and scalable cloud deployment. Implements
the StorageService interface for seamless integration with memory engine.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
from dataclasses import dataclass

try:
    import pymongo
    from pymongo import MongoClient, ASCENDING, DESCENDING
    from pymongo.errors import ConnectionFailure, BulkWriteError, PyMongoError
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    MongoClient = None

from storage_adapter import StorageService
from memory_engine import StorageError


@dataclass
class MongoConfig:
    """MongoDB connection configuration."""
    host: str = "localhost"
    port: int = 27017
    database: str = "ioa_memory"
    collection: str = "entries"
    username: Optional[str] = None
    password: Optional[str] = None
    auth_database: Optional[str] = None
    connection_string: Optional[str] = None
    max_pool_size: int = 50
    timeout_ms: int = 5000


class MongoStorageError(StorageError):
    """MongoDB-specific storage error."""
    pass


class MongoStorageService(StorageService):
    """
    MongoDB storage service implementation for IOA memory system.
    
    Provides scalable, queryable storage with proper indexing and error handling.
    Supports both local MongoDB instances and cloud services like MongoDB Atlas.
    """
    
    def __init__(self, config: Optional[MongoConfig] = None):
        """
        Initialize MongoDB storage service.
        
        Args:
            config: MongoDB configuration object
            
        Raises:
            MongoStorageError: If pymongo is not available or connection fails
        """
        if not PYMONGO_AVAILABLE:
            raise MongoStorageError(
                "PyMongo is not installed. Install with: pip install pymongo"
            )
        
        self.logger = logging.getLogger(__name__)
        self.config = config or self._load_config_from_env()
        
        # Connection state
        self._client: Optional[MongoClient] = None
        self._database = None
        self._collection = None
        self._connected = False
        
        # Initialize connection
        self._connect()
        self._setup_indexes()
        
        self.logger.info(f"MongoStorageService initialized for database: {self.config.database}")

    def _load_config_from_env(self) -> MongoConfig:
        """Load MongoDB configuration from environment variables."""
        config = MongoConfig()
        
        # Connection string takes precedence
        connection_string = os.getenv('MONGODB_CONNECTION_STRING')
        if connection_string:
            config.connection_string = connection_string
        else:
            # Individual parameters
            config.host = os.getenv('MONGODB_HOST', 'localhost')
            config.port = int(os.getenv('MONGODB_PORT', '27017'))
            config.username = os.getenv('MONGODB_USERNAME')
            config.password = os.getenv('MONGODB_PASSWORD')
            config.auth_database = os.getenv('MONGODB_AUTH_DB', 'admin')
        
        config.database = os.getenv('MONGODB_DATABASE', 'ioa_memory')
        config.collection = os.getenv('MONGODB_COLLECTION', 'entries')
        
        return config

    def _connect(self):
        """Establish connection to MongoDB."""
        try:
            if self.config.connection_string:
                # Use connection string (for MongoDB Atlas, etc.)
                self._client = MongoClient(
                    self.config.connection_string,
                    maxPoolSize=self.config.max_pool_size,
                    serverSelectionTimeoutMS=self.config.timeout_ms
                )
            else:
                # Build connection from individual parameters
                connection_params = {
                    'host': self.config.host,
                    'port': self.config.port,
                    'maxPoolSize': self.config.max_pool_size,
                    'serverSelectionTimeoutMS': self.config.timeout_ms
                }
                
                if self.config.username and self.config.password:
                    connection_params.update({
                        'username': self.config.username,
                        'password': self.config.password,
                        'authSource': self.config.auth_database or 'admin'
                    })
                
                self._client = MongoClient(**connection_params)
            
            # Test connection
            self._client.admin.command('ping')
            
            # Get database and collection references
            self._database = self._client[self.config.database]
            self._collection = self._database[self.config.collection]
            
            self._connected = True
            self.logger.info("Successfully connected to MongoDB")
            
        except ConnectionFailure as e:
            raise MongoStorageError(f"Failed to connect to MongoDB: {e}")
        except Exception as e:
            raise MongoStorageError(f"Unexpected MongoDB connection error: {e}")

    def _setup_indexes(self):
        """Create indexes for optimal query performance."""
        if not self._connected:
            return
        
        try:
            # Index for pattern_id queries
            self._collection.create_index("pattern_id")
            
            # Index for timestamp queries
            self._collection.create_index("timestamp")
            
            # Compound index for pattern + timestamp
            self._collection.create_index([
                ("pattern_id", ASCENDING),
                ("timestamp", DESCENDING)
            ])
            
            # Text index for content search
            self._collection.create_index([
                ("raw_ref", "text"),
                ("variables", "text")
            ])
            
            # Index for confidence scoring
            self._collection.create_index("confidence")
            
            self.logger.info("MongoDB indexes created successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to create indexes: {e}")

    def save(self, entry: Dict[str, Any]) -> bool:
        """
        Save memory entry to MongoDB.
        
        Args:
            entry: Memory entry dictionary
            
        Returns:
            bool: True if save successful
            
        Raises:
            MongoStorageError: If save operation fails
        """
        if not self._connected:
            raise MongoStorageError("Not connected to MongoDB")
        
        try:
            # Add MongoDB-specific metadata
            entry_with_meta = entry.copy()
            entry_with_meta.update({
                '_saved_at': datetime.now(timezone.utc),  # PATCH: Cursor-2024-12-19 ET-001 Step 4 - Replace utcnow with timezone-aware timestamp
                '_version': '2.5.0'  # PATCH: Cursor-2024-12-19 ET-001 Step 4 - Update version
            })
            
            # Insert document
            result = self._collection.insert_one(entry_with_meta)
            
            if result.inserted_id:
                self.logger.debug(f"Saved entry with ID: {result.inserted_id}")
                return True
            else:
                raise MongoStorageError("Insert operation returned no ID")
                
        except PyMongoError as e:
            raise MongoStorageError(f"Failed to save entry: {e}")
        except Exception as e:
            raise MongoStorageError(f"Unexpected error during save: {e}")

    def save_all(self, entries: List[Dict[str, Any]]) -> bool:
        """
        Save multiple entries in a batch operation.
        
        Args:
            entries: List of memory entries
            
        Returns:
            bool: True if all saves successful
            
        Raises:
            MongoStorageError: If batch save fails
        """
        if not self._connected:
            raise MongoStorageError("Not connected to MongoDB")
        
        if not entries:
            return True
        
        try:
            # Add metadata to all entries
            entries_with_meta = []
            for entry in entries:
                entry_with_meta = entry.copy()
                entry_with_meta.update({
                    '_saved_at': datetime.now(timezone.utc),  # PATCH: Cursor-2024-12-19 ET-001 Step 4 - Replace utcnow with timezone-aware timestamp
                    '_version': '2.5.0'  # PATCH: Cursor-2024-12-19 ET-001 Step 4 - Update version
                })
                entries_with_meta.append(entry_with_meta)
            
            # Bulk insert
            result = self._collection.insert_many(entries_with_meta, ordered=False)
            
            success_count = len(result.inserted_ids)
            self.logger.info(f"Batch saved {success_count}/{len(entries)} entries")
            
            return success_count == len(entries)
            
        except BulkWriteError as e:
            # Some entries may have succeeded
            success_count = len(e.details.get('writeErrors', []))
            total_count = len(entries)
            self.logger.warning(f"Batch save partial success: {success_count}/{total_count}")
            return False
            
        except PyMongoError as e:
            raise MongoStorageError(f"Failed to batch save entries: {e}")
        except Exception as e:
            raise MongoStorageError(f"Unexpected error during batch save: {e}")

    def load_all(self) -> List[Dict[str, Any]]:
        """
        Load all memory entries from MongoDB.
        
        Returns:
            List of memory entries
            
        Raises:
            MongoStorageError: If load operation fails
        """
        if not self._connected:
            raise MongoStorageError("Not connected to MongoDB")
        
        try:
            # Find all documents, exclude MongoDB internal fields
            cursor = self._collection.find({}, {'_id': 0, '_saved_at': 0, '_version': 0})
            
            entries = list(cursor)
            self.logger.debug(f"Loaded {len(entries)} entries from MongoDB")
            
            return entries
            
        except PyMongoError as e:
            raise MongoStorageError(f"Failed to load entries: {e}")
        except Exception as e:
            raise MongoStorageError(f"Unexpected error during load: {e}")

    def query(self, **filters) -> List[Dict[str, Any]]:
        """
        Query memory entries with filters.
        
        Args:
            **filters: Query filters (pattern_id, confidence, etc.)
            
        Returns:
            List of matching entries
            
        Raises:
            MongoStorageError: If query operation fails
        """
        if not self._connected:
            raise MongoStorageError("Not connected to MongoDB")
        
        try:
            # Build MongoDB query from filters
            mongo_query = {}
            
            # Direct field matches
            for field in ['pattern_id', 'confidence', 'raw_ref']:
                if field in filters:
                    mongo_query[field] = filters[field]
            
            # Range queries
            if 'min_confidence' in filters:
                mongo_query.setdefault('confidence', {})['$gte'] = filters['min_confidence']
            if 'max_confidence' in filters:
                mongo_query.setdefault('confidence', {})['$lte'] = filters['max_confidence']
            
            # Date range queries
            if 'since' in filters:
                mongo_query.setdefault('timestamp', {})['$gte'] = filters['since']
            if 'until' in filters:
                mongo_query.setdefault('timestamp', {})['$lte'] = filters['until']
            
            # Text search
            if 'search' in filters:
                mongo_query['$text'] = {'$search': filters['search']}
            
            # Pattern list filtering
            if 'patterns' in filters:
                mongo_query['pattern_id'] = {'$in': filters['patterns']}
            
            # Execute query
            cursor = self._collection.find(mongo_query, {'_id': 0, '_saved_at': 0, '_version': 0})
            
            # Apply sorting
            if 'sort_by' in filters:
                sort_field = filters['sort_by']
                sort_direction = DESCENDING if filters.get('sort_desc', False) else ASCENDING
                cursor = cursor.sort(sort_field, sort_direction)
            
            # Apply limit
            if 'limit' in filters:
                cursor = cursor.limit(filters['limit'])
            
            results = list(cursor)
            self.logger.debug(f"Query returned {len(results)} entries")
            
            return results
            
        except PyMongoError as e:
            raise MongoStorageError(f"Failed to execute query: {e}")
        except Exception as e:
            raise MongoStorageError(f"Unexpected error during query: {e}")

    def delete(self, **filters) -> int:
        """
        Delete memory entries matching filters.
        
        Args:
            **filters: Deletion filters
            
        Returns:
            Number of deleted entries
            
        Raises:
            MongoStorageError: If delete operation fails
        """
        if not self._connected:
            raise MongoStorageError("Not connected to MongoDB")
        
        if not filters:
            raise MongoStorageError("Delete requires at least one filter for safety")
        
        try:
            # Build deletion query (reuse query logic)
            mongo_query = {}
            
            for field in ['pattern_id', 'confidence', 'raw_ref']:
                if field in filters:
                    mongo_query[field] = filters[field]
            
            if 'patterns' in filters:
                mongo_query['pattern_id'] = {'$in': filters['patterns']}
            
            # Execute deletion
            result = self._collection.delete_many(mongo_query)
            deleted_count = result.deleted_count
            
            self.logger.info(f"Deleted {deleted_count} entries from MongoDB")
            return deleted_count
            
        except PyMongoError as e:
            raise MongoStorageError(f"Failed to delete entries: {e}")
        except Exception as e:
            raise MongoStorageError(f"Unexpected error during delete: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics and health information.
        
        Returns:
            Dictionary with storage stats
        """
        if not self._connected:
            return {"status": "disconnected", "error": "Not connected to MongoDB"}
        
        try:
            # Collection stats
            stats = self._database.command("collStats", self.config.collection)
            
            # Count documents
            total_entries = self._collection.count_documents({})
            
            # Pattern distribution
            pipeline = [
                {"$group": {"_id": "$pattern_id", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            pattern_stats = list(self._collection.aggregate(pipeline))
            
            return {
                "status": "connected",
                "database": self.config.database,
                "collection": self.config.collection,
                "total_entries": total_entries,
                "storage_size_mb": round(stats.get("size", 0) / (1024 * 1024), 2),
                "index_count": stats.get("nindexes", 0),
                "avg_object_size": round(stats.get("avgObjSize", 0), 2),
                "top_patterns": pattern_stats,
                "last_updated": datetime.now(timezone.utc).isoformat()  # PATCH: Cursor-2024-12-19 ET-001 Step 4 - Replace utcnow with timezone-aware timestamp
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_checked": datetime.now(timezone.utc).isoformat()  # PATCH: Cursor-2024-12-19 ET-001 Step 4 - Replace utcnow with timezone-aware timestamp
            }

    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """
        Create a backup of the memory collection.
        
        Args:
            backup_name: Optional backup collection name
            
        Returns:
            Name of the backup collection
            
        Raises:
            MongoStorageError: If backup creation fails
        """
        if not self._connected:
            raise MongoStorageError("Not connected to MongoDB")
        
        try:
            # Generate backup name if not provided
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{self.config.collection}_backup_{timestamp}"
            
            # Copy all documents to backup collection
            pipeline = [{"$out": backup_name}]
            list(self._collection.aggregate(pipeline))
            
            self.logger.info(f"Created backup collection: {backup_name}")
            return backup_name
            
        except PyMongoError as e:
            raise MongoStorageError(f"Failed to create backup: {e}")
        except Exception as e:
            raise MongoStorageError(f"Unexpected error during backup: {e}")

    def optimize_storage(self) -> Dict[str, Any]:
        """
        Optimize storage by reindexing and compacting.
        
        Returns:
            Optimization results
        """
        if not self._connected:
            raise MongoStorageError("Not connected to MongoDB")
        
        try:
            results = {"operations": []}
            
            # Reindex collection
            self._collection.reindex()
            results["operations"].append("reindex_completed")
            
            # Compact collection (admin required)
            try:
                self._database.command("compact", self.config.collection)
                results["operations"].append("compact_completed")
            except Exception:
                results["operations"].append("compact_skipped_no_permission")
            
            results["status"] = "completed"
            results["timestamp"] = datetime.now(timezone.utc).isoformat()  # PATCH: Cursor-2024-12-19 ET-001 Step 4 - Replace utcnow with timezone-aware timestamp
            
            self.logger.info("Storage optimization completed")
            return results
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()  # PATCH: Cursor-2024-12-19 ET-001 Step 4 - Replace utcnow with timezone-aware timestamp
            }

    def close(self):
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            self._connected = False
            self.logger.info("MongoDB connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __del__(self):
        """Cleanup on deletion."""
        self.close()


# Factory function for easy instantiation
def create_mongo_storage(
    connection_string: Optional[str] = None,
    database: str = "ioa_memory",
    collection: str = "entries"
) -> MongoStorageService:
    """
    Create MongoDB storage service with simple configuration.
    
    Args:
        connection_string: MongoDB connection string
        database: Database name
        collection: Collection name
        
    Returns:
        Configured MongoStorageService instance
    """
    config = MongoConfig(
        database=database,
        collection=collection,
        connection_string=connection_string
    )
    
    return MongoStorageService(config)


# Export main classes
__all__ = [
    'MongoStorageService',
    'MongoConfig', 
    'MongoStorageError',
    'create_mongo_storage'
]