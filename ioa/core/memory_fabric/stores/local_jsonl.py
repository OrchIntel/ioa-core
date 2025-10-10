""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pathlib import Path

from .base import BaseMemoryStore, MemoryStore
from ..schema import MemoryRecordV1

# PATCH: Cursor-2025-09-10 DISPATCH-OSS-20250910-MEMORY-FABRIC-REFACTOR <local jsonl store>

class LocalJSONLStore(BaseMemoryStore):
    """Local JSONL storage implementation for Memory Fabric."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the JSONL store."""
        super().__init__(config)
        self.data_dir = Path(config.get("data_dir", "./artifacts/memory"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create run-specific file
        run_id = str(uuid.uuid4())[:8]
        self.file_path = self.data_dir / f"memory_run_{run_id}.jsonl"
        self._records: Dict[str, MemoryRecordV1] = {}
        self._load_existing_records()
    
    def _load_existing_records(self):
        """Load existing records from JSONL file."""
        if not self.file_path.exists():
            return
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        record = MemoryRecordV1.from_dict(data)
                        self._records[record.id] = record
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        self._update_stats("errors", False)
                        continue
            
            self._stats["total_records"] = len(self._records)
        except Exception as e:
            self._update_stats("errors", False)
    
    def store(self, record: MemoryRecordV1) -> bool:
        """Store a memory record."""
        try:
            if not self._validate_record(record):
                self._update_stats("writes", False)
                return False
            
            self._records[record.id] = record
            
            # Append to JSONL file
            with open(self.file_path, 'a', encoding='utf-8') as f:
                f.write(record.to_json() + '\n')
            
            self._update_stats("writes", True)
            self._stats["total_records"] = len(self._records)
            return True
            
        except Exception as e:
            self._update_stats("writes", False)
            return False
    
    def retrieve(self, record_id: str) -> Optional[MemoryRecordV1]:
        """Retrieve a memory record by ID."""
        try:
            record = self._records.get(record_id)
            if record:
                record.update_access()
                self._update_stats("reads", True)
            else:
                self._update_stats("reads", False)
            return record
        except Exception as e:
            self._update_stats("reads", False)
            return None
    
    def search(self, query: str, limit: int = 10, memory_type: Optional[str] = None) -> List[MemoryRecordV1]:
        """Search for memory records."""
        try:
            results = []
            query_lower = query.lower()
            
            for record in self._records.values():
                if memory_type and record.memory_type.value != memory_type:
                    continue
                
                # Simple text search in content and tags
                if (query_lower in record.content.lower() or 
                    any(query_lower in tag.lower() for tag in record.tags)):
                    results.append(record)
                
                if len(results) >= limit:
                    break
            
            # Sort by access count and timestamp
            results.sort(key=lambda r: (r.access_count, r.timestamp), reverse=True)
            
            self._update_stats("queries", True)
            return results
            
        except Exception as e:
            self._update_stats("queries", False)
            return []
    
    def delete(self, record_id: str) -> bool:
        """Delete a memory record."""
        try:
            if record_id in self._records:
                del self._records[record_id]
                self._stats["total_records"] = len(self._records)
                
                # Rewrite the entire file (simple approach)
                self._rewrite_file()
                return True
            return False
        except Exception as e:
            self._update_stats("errors", False)
            return False
    
    def list_all(self, limit: Optional[int] = None) -> List[MemoryRecordV1]:
        """List all memory records."""
        try:
            records = list(self._records.values())
            if limit:
                records = records[:limit]
            
            self._update_stats("reads", True)
            return records
        except Exception as e:
            self._update_stats("reads", False)
            return []
    
    def _rewrite_file(self):
        """Rewrite the entire JSONL file with current records."""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                for record in self._records.values():
                    f.write(record.to_json() + '\n')
        except Exception as e:
            self._update_stats("errors", False)
    
    def close(self) -> None:
        """Close the store and cleanup resources."""
        # JSONL store doesn't need explicit cleanup
        pass
    
    def get_file_path(self) -> str:
        """Get the file path for this store."""
        return str(self.file_path)
