""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3
"""
"""

import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from memory_fabric import MemoryFabric, MemoryRecordV1

# PATCH: Cursor-2025-09-10 DISPATCH-OSS-20250910-MEMORY-FABRIC-REFACTOR <migration tool>

class MemoryMigrationTool:
    """Tool for migrating from memory_engine to memory_fabric."""
    
    def __init__(self, dry_run: bool = False):
        """Initialize migration tool."""
        self.dry_run = dry_run
        self.migration_id = f"migration_{int(time.time())}"
        self.receipts_dir = Path("./artifacts/migrations/memory_fabric")
        self.receipts_dir.mkdir(parents=True, exist_ok=True)
        
    def create_backup(self, source_path: str) -> str:
        """Create backup of source data."""
        backup_path = f"{source_path}.backup_{self.migration_id}"
        
        if os.path.exists(source_path):
            if not self.dry_run:
                shutil.copytree(source_path, backup_path)
            print(f"Created backup: {backup_path}")
            return backup_path
        return ""
    
    def discover_memory_data(self) -> List[Dict[str, Any]]:
        """Discover existing memory data locations."""
        locations = []
        
        # Check common memory engine locations
        common_paths = [
            "./artifacts/memory",
            "./data/memory", 
            "./logs/memory",
            "./_internal/memory"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                locations.append({
                    "path": path,
                    "type": "directory",
                    "size": self._get_directory_size(path)
                })
        
        # Check for JSONL files
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith(".jsonl") and "memory" in file.lower():
                    file_path = os.path.join(root, file)
                    locations.append({
                        "path": file_path,
                        "type": "file",
                        "size": os.path.getsize(file_path)
                    })
        
        return locations
    
    def _get_directory_size(self, path: str) -> int:
        """Get total size of directory."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size
    
    def migrate_data(self, source_locations: List[Dict[str, Any]], target_backend: str = "sqlite") -> Dict[str, Any]:
        """Migrate data from source locations to memory fabric."""
        migration_stats = {
            "migration_id": self.migration_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_locations": source_locations,
            "target_backend": target_backend,
            "records_migrated": 0,
            "errors": [],
            "checksums": {},
            "backup_paths": []
        }
        
        # Initialize target fabric
        fabric_config = {
            "data_dir": "./artifacts/memory_fabric"
        }
        
        if not self.dry_run:
            fabric = MemoryFabric(backend=target_backend, config=fabric_config)
        else:
            fabric = None
        
        # Process each source location
        for location in source_locations:
            try:
                if location["type"] == "directory":
                    records = self._migrate_directory(location["path"], fabric)
                elif location["type"] == "file":
                    records = self._migrate_file(location["path"], fabric)
                else:
                    continue
                
                migration_stats["records_migrated"] += len(records)
                migration_stats["checksums"][location["path"]] = self._calculate_checksum(location["path"])
                
                # Create backup
                backup_path = self.create_backup(location["path"])
                if backup_path:
                    migration_stats["backup_paths"].append(backup_path)
                
            except Exception as e:
                error_msg = f"Failed to migrate {location['path']}: {str(e)}"
                migration_stats["errors"].append(error_msg)
                print(f"ERROR: {error_msg}")
        
        if fabric:
            fabric.close()
        
        return migration_stats
    
    def _migrate_directory(self, dir_path: str, fabric: Optional[MemoryFabric]) -> List[MemoryRecordV1]:
        """Migrate data from a directory."""
        records = []
        
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if file.endswith((".json", ".jsonl")):
                    file_path = os.path.join(root, file)
                    file_records = self._migrate_file(file_path, fabric)
                    records.extend(file_records)
        
        return records
    
    def _migrate_file(self, file_path: str, fabric: Optional[MemoryFabric]) -> List[MemoryRecordV1]:
        """Migrate data from a file."""
        records = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.jsonl'):
                    # JSONL format
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            record = self._convert_to_memory_record(data)
                            if record and fabric:
                                fabric.store(
                                    record.content,
                                    record.metadata,
                                    record.tags,
                                    record.memory_type.value,
                                    record.storage_tier.value,
                                    record.id
                                )
                            records.append(record)
                        except (json.JSONDecodeError, KeyError) as e:
                            print(f"Warning: Failed to parse line in {file_path}: {e}")
                            continue
                else:
                    # JSON format
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            record = self._convert_to_memory_record(item)
                            if record and fabric:
                                fabric.store(
                                    record.content,
                                    record.metadata,
                                    record.tags,
                                    record.memory_type.value,
                                    record.storage_tier.value,
                                    record.id
                                )
                            records.append(record)
                    else:
                        record = self._convert_to_memory_record(data)
                        if record and fabric:
                            fabric.store(
                                record.content,
                                record.metadata,
                                record.tags,
                                record.memory_type.value,
                                record.storage_tier.value,
                                record.id
                            )
                        records.append(record)
        
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
        
        return records
    
    def _convert_to_memory_record(self, data: Dict[str, Any]) -> Optional[MemoryRecordV1]:
        """Convert legacy data to MemoryRecordV1."""
        try:
            # Handle different legacy formats
            if "content" in data:
                content = data["content"]
            elif "text" in data:
                content = data["text"]
            elif "message" in data:
                content = data["message"]
            else:
                return None
            
            # Extract metadata
            metadata = data.get("metadata", {})
            if "timestamp" in data:
                metadata["legacy_timestamp"] = data["timestamp"]
            
            # Extract tags
            tags = data.get("tags", [])
            if "category" in data:
                tags.append(data["category"])
            
            # Create record
            record = MemoryRecordV1(
                id=data.get("id", ""),
                content=content,
                metadata=metadata,
                tags=tags,
                memory_type=data.get("memory_type", "conversation"),
                storage_tier=data.get("storage_tier", "hot")
            )
            
            return record
            
        except Exception as e:
            print(f"Error converting record: {e}")
            return None
    
    def _calculate_checksum(self, path: str) -> str:
        """Calculate checksum for a file or directory."""
        import hashlib
        
        if os.path.isfile(path):
            with open(path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        else:
            # For directories, hash all file contents
            hasher = hashlib.sha256()
            for root, dirs, files in os.walk(path):
                for file in sorted(files):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'rb') as f:
                        hasher.update(f.read())
            return hasher.hexdigest()
    
    def save_receipt(self, migration_stats: Dict[str, Any]) -> str:
        """Save migration receipt."""
        receipt_file = self.receipts_dir / f"{self.migration_id}-receipt.json"
        
        if not self.dry_run:
            with open(receipt_file, 'w', encoding='utf-8') as f:
                json.dump(migration_stats, f, indent=2)
        
        print(f"Migration receipt saved: {receipt_file}")
        return str(receipt_file)
    
    def rollback(self, receipt_file: str) -> bool:
        """Rollback migration using receipt."""
        try:
            with open(receipt_file, 'r', encoding='utf-8') as f:
                receipt = json.load(f)
            
            print(f"Rolling back migration {receipt['migration_id']}")
            
            # Restore from backups
            for backup_path in receipt.get("backup_paths", []):
                if os.path.exists(backup_path):
                    original_path = backup_path.replace(f".backup_{receipt['migration_id']}", "")
                    
                    if os.path.exists(original_path):
                        shutil.rmtree(original_path)
                    
                    shutil.move(backup_path, original_path)
                    print(f"Restored: {original_path}")
            
            # Remove migrated data
            fabric_data_dir = Path("./artifacts/memory_fabric")
            if fabric_data_dir.exists():
                shutil.rmtree(fabric_data_dir)
                print("Removed migrated data")
            
            print("Rollback completed successfully")
            return True
            
        except Exception as e:
            print(f"Rollback failed: {e}")
            return False

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Migrate memory_engine to memory_fabric")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run without actual migration")
    parser.add_argument("--backend", choices=["local_jsonl", "sqlite", "s3"], default="sqlite", help="Target backend")
    parser.add_argument("--rollback", help="Rollback migration using receipt file")
    
    args = parser.parse_args()
    
    if args.rollback:
        tool = MemoryMigrationTool(dry_run=False)
        success = tool.rollback(args.rollback)
        sys.exit(0 if success else 1)
    
    tool = MemoryMigrationTool(dry_run=args.dry_run)
    
    print("Memory Engine to Memory Fabric Migration")
    print("=" * 40)
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")
        print()
    
    # Discover existing data
    print("Discovering existing memory data...")
    locations = tool.discover_memory_data()
    
    if not locations:
        print("No memory data found to migrate")
        sys.exit(0)
    
    print(f"Found {len(locations)} data locations:")
    for loc in locations:
        size_mb = loc["size"] / (1024 * 1024)
        print(f"  - {loc['path']} ({size_mb:.2f} MB)")
    
    print()
    
    # Perform migration
    print(f"Migrating to {args.backend} backend...")
    migration_stats = tool.migrate_data(locations, args.backend)
    
    # Save receipt
    receipt_file = tool.save_receipt(migration_stats)
    
    # Print summary
    print(f"  Records migrated: {migration_stats['records_migrated']}")
    print(f"  Errors: {len(migration_stats['errors'])}")
    print(f"  Receipt: {receipt_file}")
    
    if migration_stats["errors"]:
        print("\nErrors:")
        for error in migration_stats["errors"]:
            print(f"  - {error}")
    
    if args.dry_run:
        print("\nDry run completed - no changes made")
    else:
        print("\nMigration completed successfully")
        print(f"To rollback: python {__file__} --rollback {receipt_file}")

if __name__ == "__main__":
    main()
