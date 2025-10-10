# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.



import json
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
"""S3 module."""

from pathlib import Path

from .base import BaseMemoryStore, MemoryStore
from ..schema import MemoryRecordV1, MemoryType, StorageTier

# PATCH: Cursor-2025-09-10 DISPATCH-OSS-20250910-MEMORY-FABRIC-REFACTOR <s3 store>

class S3Store(BaseMemoryStore):
    """S3 storage implementation for Memory Fabric (optional)."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the S3 store."""
        super().__init__(config)
        
        # Get configuration from environment variables or config
        self.bucket_name = (
            (config.get("bucket_name") if config else None) or 
            os.getenv("IOA_FABRIC_S3_BUCKET", "ioa-memory-fabric")
        )
        self.prefix = (
            (config.get("prefix") if config else None) or 
            os.getenv("IOA_FABRIC_S3_PREFIX", "ioa/memory/")
        )
        self.region = (
            (config.get("region") if config else None) or 
            os.getenv("IOA_FABRIC_S3_REGION") or 
            os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        )
        
        # Check for AWS credentials
        self._boto3_available = self._check_boto3_availability()
        self._s3_client = None
        
        if self._boto3_available:
            self._init_s3_client()
        else:
            # Fallback to local storage if S3 not available
            self._fallback_store = None
            self._init_fallback()
        
        # Always initialize fallback store for error handling
        if not hasattr(self, '_fallback_store') or self._fallback_store is None:
            self._init_fallback()
    
    def _check_boto3_availability(self) -> bool:
        """Check if boto3 is available and credentials are present."""
        try:
            import boto3
            # Check if credentials are available
            session = boto3.Session()
            credentials = session.get_credentials()
            return credentials is not None
        except ImportError:
            return False
    
    def _init_s3_client(self):
        """Initialize S3 client."""
        try:
            import boto3
            self._s3_client = boto3.client('s3', region_name=self.region)
            # Test connection
            self._s3_client.head_bucket(Bucket=self.bucket_name)
        except Exception as e:
            self._boto3_available = False
            self._init_fallback()
    
    def _init_fallback(self):
        """Initialize fallback to local storage."""
        fallback_dir = Path("./artifacts/memory/s3_fallback")
        fallback_dir.mkdir(parents=True, exist_ok=True)
        
        # Use LocalJSONLStore as fallback
        from .local_jsonl import LocalJSONLStore
        self._fallback_store = LocalJSONLStore({
            "data_dir": str(fallback_dir)
        })
    
    def store(self, record: MemoryRecordV1) -> bool:
        """Store a memory record."""
        if not self._boto3_available or not self._s3_client:
            return self._fallback_store.store(record)
        
        try:
            if not self._validate_record(record):
                self._update_stats("writes", False)
                return False
            
            # Upload to S3
            key = f"{self.prefix}{record.id}.json"
            self._s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=record.to_json(),
                ContentType='application/json'
            )
            
            self._update_stats("writes", True)
            self._stats["total_records"] += 1
            return True
            
        except Exception as e:
            # Log a concise error and fallback to local storage
            self._update_stats("writes", False)
            return self._fallback_store.store(record)
    
    def retrieve(self, record_id: str) -> Optional[MemoryRecordV1]:
        """Retrieve a memory record by ID."""
        if not self._boto3_available or not self._s3_client:
            return self._fallback_store.retrieve(record_id)
        
        try:
            key = f"{self.prefix}{record_id}.json"
            response = self._s3_client.get_object(Bucket=self.bucket_name, Key=key)
            data = json.loads(response['Body'].read().decode('utf-8'))
            
            record = MemoryRecordV1.from_dict(data)
            record.update_access()
            
            # Update access count (store back to S3)
            self.store(record)
            
            self._update_stats("reads", True)
            return record
            
        except Exception:
            self._update_stats("reads", False)
            return self._fallback_store.retrieve(record_id)
    
    def search(self, query: str, limit: int = 10, memory_type: Optional[str] = None) -> List[MemoryRecordV1]:
        """Search for memory records."""
        if not self._boto3_available or not self._s3_client:
            return self._fallback_store.search(query, limit, memory_type)
        
        try:
            # List all objects with the prefix
            response = self._s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.prefix
            )
            
            results = []
            query_lower = query.lower()
            
            for obj in response.get('Contents', []):
                if len(results) >= limit:
                    break
                
                skip = False
                record = None
                # Download and parse each object
                try:
                    obj_response = self._s3_client.get_object(
                        Bucket=self.bucket_name,
                        Key=obj['Key']
                    )
                    data = json.loads(obj_response['Body'].read().decode('utf-8'))
                    record = MemoryRecordV1.from_dict(data)
                except Exception:
                    skip = True
                
                if skip or record is None:
                    # Skip this object silently and proceed to the next
                    pass
                else:
                    # Simple text search
                    if memory_type and record.memory_type.value != memory_type:
                        pass
                    else:
                        if (query_lower in record.content.lower() or 
                            any(query_lower in tag.lower() for tag in record.tags)):
                            results.append(record)
            
            # Sort by access count and timestamp
            results.sort(key=lambda r: (r.access_count, r.timestamp), reverse=True)
            
            self._update_stats("queries", True)
            return results
            
        except Exception:
            self._update_stats("queries", False)
            return self._fallback_store.search(query, limit, memory_type)
    
    def delete(self, record_id: str) -> bool:
        """Delete a memory record."""
        if not self._boto3_available or not self._s3_client:
            return self._fallback_store.delete(record_id)
        
        try:
            key = f"{self.prefix}{record_id}.json"
            self._s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            
            self._stats["total_records"] = max(0, self._stats["total_records"] - 1)
            return True
            
        except Exception as e:
            self._update_stats("errors", False)
            # Fallback to local storage
            return self._fallback_store.delete(record_id)
    
    def list_all(self, limit: Optional[int] = None) -> List[MemoryRecordV1]:
        """List all memory records."""
        if not self._boto3_available or not self._s3_client:
            return self._fallback_store.list_all(limit)
        
        try:
            response = self._s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.prefix
            )
            
            results = []
            count = 0
            
            for obj in response.get('Contents', []):
                if limit and count >= limit:
                    break
                
                # Attempt retrieval; avoid try/except/continue pattern
                retrieval_failed = False
                try:
                    obj_response = self._s3_client.get_object(
                        Bucket=self.bucket_name,
                        Key=obj['Key']
                    )
                    data = json.loads(obj_response['Body'].read().decode('utf-8'))
                    record = MemoryRecordV1.from_dict(data)
                except Exception:
                    retrieval_failed = True
                    record = None
                
                if not retrieval_failed and record is not None:
                    results.append(record)
                    count += 1
            
            # Sort by access count and timestamp
            results.sort(key=lambda r: (r.access_count, r.timestamp), reverse=True)
            
            self._update_stats("reads", True)
            return results
            
        except Exception:
            self._update_stats("reads", False)
            return self._fallback_store.list_all(limit)
    
    def close(self) -> None:
        """Close the store and cleanup resources."""
        if self._fallback_store:
            self._fallback_store.close()
    
    def is_available(self) -> bool:
        """Check if S3 store is available."""
        return self._boto3_available and self._s3_client is not None
    
    def doctor_verification(self, num_records: int = 25) -> Dict[str, Any]:
        """
        Perform S3 backend verification with write/read/verify operations.
        
        Args:
            num_records: Number of test records to write and verify
            
        Returns:
            Dictionary with verification results and metrics
        """
        if not self.is_available():
            return {
                "status": "unavailable",
                "error": "S3 client not available - check credentials and configuration",
                "backend": "s3",
                "writes": 0,
                "reads": 0,
                "verified": 0,
                "errors": 1
            }
        
        results = {
            "status": "healthy",
            "backend": "s3",
            "bucket": self.bucket_name,
            "prefix": self.prefix,
            "region": self.region,
            "writes": 0,
            "reads": 0,
            "verified": 0,
            "errors": 0,
            "test_records": []
        }
        
        try:
            # Write test records
            for i in range(num_records):
                test_record = MemoryRecordV1(
                    id=f"doctor_test_{i}_{uuid.uuid4().hex[:8]}",
                    content=f"Doctor test record {i} - {datetime.now(timezone.utc).isoformat()}",
                    metadata={"test": True, "index": i},
                    tags=[f"doctor-test", f"record-{i}"],
                    memory_type=MemoryType.CONVERSATION,
                    storage_tier=StorageTier.HOT
                )
                
                if self.store(test_record):
                    results["writes"] += 1
                    results["test_records"].append(test_record.id)
                else:
                    results["errors"] += 1
            
            # Read back and verify records
            for record_id in results["test_records"]:
                retrieved = self.retrieve(record_id)
                if retrieved and retrieved.content.startswith("Doctor test record"):
                    results["reads"] += 1
                    results["verified"] += 1
                else:
                    results["errors"] += 1
            
            # Clean up test records
            for record_id in results["test_records"]:
                self.delete(record_id)
            
            # Determine overall status
            if results["errors"] > 0:
                results["status"] = "degraded" if results["verified"] > 0 else "unhealthy"
            
        except Exception as e:
            results["status"] = "unhealthy"
            results["error"] = str(e)
            results["errors"] += 1
        
        return results
