**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Memory Fabric Migration Guide

This guide covers migrating from the legacy `memory_engine` to the new `memory_fabric` system.

## Overview

The Memory Fabric is a complete rewrite of the memory system with:
- Modular backend architecture
- Schema versioning
- Encryption support
- Advanced querying
- Better performance

## Migration Process

### 1. Pre-Migration Checklist

- [ ] Backup existing memory data
- [ ] Identify data locations
- [ ] Choose target backend (recommend `sqlite`)
- [ ] Test migration with dry run

### 2. Run Migration

#### Dry Run First
> **Note**: Some commands below are examples for future functionality.

```bash
# Test migration without making changes
# Example (not currently implemented): ioa fabric migrate --dry-run --backend sqlite
```

#### Actual Migration
> **Note**: Some commands below are examples for future functionality.

```bash
# Migrate to SQLite backend
# Example (not currently implemented): ioa fabric migrate --backend sqlite

# Or migrate to local JSONL
# Example (not currently implemented): ioa fabric migrate --backend local_jsonl
```

### 3. Verify Migration

> **Note**: Some commands below are examples for future functionality.

```bash
# Check fabric health
# Example (not currently implemented): ioa fabric doctor --backend sqlite --verbose

# Test basic operations
python -c "
# from memory_fabric import MemoryFabric
# fabric = MemoryFabric(backend='sqlite')
# print('Records:', len(fabric.list_all()))
# fabric.close()
# "
```

## Migration Tool Details

The migration tool (`tools/migrate_memory_engine_to_fabric.py`) provides:

### Features
- **Automatic Discovery**: Finds memory data in common locations
- **Dry Run Mode**: Test migration without changes
- **Backup Creation**: Creates backups before migration
- **Migration Receipts**: JSON receipts with checksums and metadata
- **Rollback Support**: Restore from backups if needed

### Data Discovery
The tool searches for memory data in:
- `./artifacts/memory/`
- `./data/memory/`
- `./logs/memory/`
- `./_internal/memory/`
- Any `.jsonl` files with "memory" in the name

### Migration Receipts
Located in `./artifacts/migrations/memory_fabric/`:

```json
{
  "migration_id": "migration_1694123456",
  "timestamp": "2025-09-10T12:34:56Z",
  "source_locations": [...],
  "target_backend": "sqlite",
  "records_migrated": 1250,
  "errors": [],
  "checksums": {...},
  "backup_paths": [...]
}
```

## Rollback Process

If migration fails or you need to revert:

```bash
# Rollback using receipt file
python tools/migrate_memory_engine_to_fabric.py --rollback artifacts/migrations/memory_fabric/migration_1694123456-receipt.json
```

The rollback process:
1. Restores original data from backups
2. Removes migrated data
3. Preserves original file structure

## Code Migration

### Old Code (memory_engine)
```python
from memory_engine import MemoryEngine

engine = MemoryEngine()
record_id = engine.store("content", {"meta": "data"})
record = engine.retrieve(record_id)
```

### New Code (memory_fabric)
```python
from memory_fabric import MemoryFabric

fabric = MemoryFabric(backend="sqlite")
record_id = fabric.store("content", metadata={"meta": "data"})
record = fabric.retrieve(record_id)
```

### Compatibility Shim
The old `memory_engine` module still works but shows deprecation warnings:

```python
# This still works but shows warnings
from memory_engine import MemoryEngine
engine = MemoryEngine()  # Shows deprecation warning
```

## Schema Changes

### Legacy Format
```json
{
  "id": "abc123",
  "content": "Hello world",
  "metadata": {"source": "test"},
  "timestamp": "2025-09-10T12:00:00Z"
}
```

### New Format (MemoryRecordV1)
```json
{
  "id": "abc123",
  "content": "Hello world",
  "metadata": {"source": "test"},
  "timestamp": "2025-09-10T12:00:00Z",
  "tags": [],
  "storage_tier": "hot",
  "memory_type": "conversation",
  "access_count": 0,
  "last_accessed": null,
  "embedding": null,
  "__schema_version__": "1.0"
}
```

## Performance Improvements

### Query Performance
- **SQLite**: 10-100x faster queries with FTS
- **S3**: Better scalability for large datasets
- **Local JSONL**: Simpler but slower for large datasets

### Memory Usage
- **SQLite**: Better memory management with WAL
- **S3**: Streaming operations reduce memory usage
- **Local JSONL**: File-based, minimal memory usage

## Troubleshooting

### Common Issues

#### Migration Fails
> **Note**: Some commands below are examples for future functionality.

```bash
# Check for permission issues
ls -la artifacts/memory/

# Run with verbose output
# Example (not currently implemented): ioa fabric migrate --verbose --backend sqlite
```

#### Data Not Found
```bash
# Manually specify data locations
python tools/migrate_memory_engine_to_fabric.py --help
```

#### Rollback Issues
```bash
# Check backup files exist
ls -la artifacts/memory/*.backup_*

# Verify receipt file
cat artifacts/migrations/memory_fabric/*-receipt.json
```

### Getting Help

1. Check the migration receipt for error details
2. Run `ioa fabric doctor` to check system health
3. Review logs in `./logs/` directory
4. Use dry run mode to test changes

## Timeline

- **v2.5.0**: Memory Fabric available alongside memory_engine
- **v2.6.0**: memory_engine shows deprecation warnings
- **v2.7.0**: memory_engine removed, only Memory Fabric available

## Best Practices

1. **Test First**: Always run dry run before actual migration
2. **Backup Data**: Keep backups until migration is verified
3. **Monitor Performance**: Check query performance after migration
4. **Update Code**: Migrate to new APIs gradually
5. **Use SQLite**: Recommended backend for most use cases
