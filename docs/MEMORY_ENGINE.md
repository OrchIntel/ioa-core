**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# IOA Core Memory Engine

**IOA Module**: `ioa.core.memory_engine`  
**Version**: v2.5.0  
**Last-Updated**: 2025-01-27  
**Agents**: Cursor assist  
**Summary**: Stable, async, GDPR-compliant memory engine for IOA Core

## Overview

The `ModularMemoryEngine` is a new, stable memory engine that provides async support, GDPR compliance, and performance monitoring. It replaces the legacy `src.memory_engine` implementation and serves as the foundation for future memory operations.

## Key Features

- **Async API**: All operations are asynchronous for better performance
- **GDPR Compliance**: Built-in support for data portability, right to be forgotten, and audit trails
- **Performance Monitoring**: Real-time statistics and operation timing
- **Configurable**: Enable/disable features based on requirements
- **Backward Compatible**: Shim layer maintains existing imports

## API Reference

### Core Classes

#### `ModularMemoryEngine`

The main memory engine class.

```python
from ioa.core.memory_engine import ModularMemoryEngine

engine = ModularMemoryEngine(
    enable_gdpr=True,           # Enable GDPR features
    enable_monitoring=True,      # Enable performance monitoring
    max_cache_size=10000        # Maximum entries in hot cache
)
```

#### `MemoryEntry`

Represents a single memory entry.

```python
from ioa.core.memory_engine import MemoryEntry

entry = MemoryEntry(
    id="unique_id",
    content="Entry content",
    metadata={"key": "value"},
    tags=["tag1", "tag2"],
    user_id="user_123"
)
```

#### `MemoryStats`

Performance and usage statistics.

```python
from ioa.core.memory_engine import MemoryStats

stats = await engine.stats()
print(f"Total entries: {stats.total_entries}")
print(f"Average processing time: {stats.avg_processing_time}ms")
```

### Core Methods

#### `remember(entry)`

Store a new entry in memory.

```python
# Store dictionary data
entry_id = await engine.remember({
    "content": "User message",
    "user_id": "user_123",
    "metadata": {"source": "chat"}
})

# Store MemoryEntry object
entry = MemoryEntry(
    id="custom_id",
    content="Structured data",
    user_id="user_456"
)
entry_id = await engine.remember(entry)
```

#### `retrieve(entry_id)`

Retrieve an entry by ID.

```python
entry = await engine.retrieve("entry_id_123")
if entry:
    print(f"Content: {entry.content}")
    print(f"User: {entry.user_id}")
    print(f"Created: {entry.timestamp}")
```

#### `forget(entry_id)`

Delete a specific entry.

```python
success = await engine.forget("entry_id_123")
if success:
    print("Entry deleted successfully")
```

#### `list_all()`

Get all entries (synchronous, for backward compatibility).

```python
all_entries = engine.list_all()
for entry in all_entries:
    print(f"ID: {entry['id']}, Content: {entry['content']}")
```

### GDPR Methods

#### `export_user(user_id)`

Export all data for a specific user (GDPR right to data portability).

```python
export_data = await engine.export_user("user_123")
print(f"User has {export_data['total_entries']} entries")
print(f"Export timestamp: {export_data['export_timestamp']}")

# Access individual entries
for entry in export_data['entries']:
    print(f"Entry: {entry['content']}")
```

#### `forget_user(user_id)`

Delete all data for a specific user (GDPR right to be forgotten).

```python
deleted_count = await engine.forget_user("user_123")
print(f"Deleted {deleted_count} entries for user")
```

#### `audit_forget(user_id)`

Get audit trail for user deletion operations.

```python
audit_trail = await engine.audit_forget("user_123")
print(f"User ID: {audit_trail['user_id']}")
print(f"Total forget requests: {len(audit_trail['forget_requests'])}")

for request in audit_trail['forget_requests']:
    print(f"Request ID: {request['id']}")
    print(f"Status: {request['status']}")
    print(f"Created: {request['created_at']}")
```

### Statistics and Monitoring

#### `stats()`

Get comprehensive performance statistics.

```python
stats = await engine.stats()
print(f"Total entries: {stats.total_entries}")
print(f"Failed entries: {stats.failed_entries}")
print(f"Average processing time: {stats.avg_processing_time}ms")
print(f"Storage tier distribution: {stats.storage_tier_distribution}")
```

## Configuration Options

### GDPR Settings

```python
# Enable full GDPR compliance
engine = ModularMemoryEngine(enable_gdpr=True)

# Disable GDPR features for performance
engine = ModularMemoryEngine(enable_gdpr=False)
```

### Monitoring Settings

```python
# Enable performance monitoring
engine = ModularMemoryEngine(enable_monitoring=True)

# Disable monitoring for production
engine = ModularMemoryEngine(enable_monitoring=False)
```

### Cache Settings

```python
# Large cache for high-throughput scenarios
engine = ModularMemoryEngine(max_cache_size=50000)

# Small cache for memory-constrained environments
engine = ModularMemoryEngine(max_cache_size=1000)
```

## Error Handling

The engine provides specific exception types for different error scenarios:

```python
from ioa.core.memory_engine import (
    MemoryError, StorageError, ProcessingError
)

try:
    await engine.remember({"content": "test"})
except MemoryError as e:
    print(f"Memory error: {e.message}")
    print(f"Operation: {e.operation}")
    print(f"Entry ID: {e.entry_id}")
except StorageError as e:
    print(f"Storage error: {e.message}")
except ProcessingError as e:
    print(f"Processing error: {e.message}")
```

## Migration from Legacy Engine

### Old Import Pattern

```python
# Legacy code (deprecated)
from src.memory_engine import MemoryEngine

engine = MemoryEngine(storage_service=storage)
```

### New Import Pattern

```python
# New code (recommended)
from ioa.core.memory_engine import ModularMemoryEngine

engine = ModularMemoryEngine(
    enable_gdpr=True,
    enable_monitoring=True
)
```

### Shim Compatibility

The legacy `src.memory_engine` module now acts as a shim, redirecting to the new core engine:

```python
# This still works but shows deprecation warnings
from src.memory_engine import MemoryEngine

# Set environment variable to see warnings
export IOA_EMIT_LEGACY_WARNINGS=1
```

## Performance Characteristics

### Benchmark Results

The engine has been tested with 100k entries:

- **Remember rate**: ~33,000 entries/second
- **Retrieve rate**: ~300 entries/second
- **GDPR operations**: Complete in under 6 seconds
- **Total benchmark time**: Under 12 seconds for 100k entries

### Memory Usage

- **Per entry**: ~200-500 bytes (depending on content size)
- **Cache overhead**: Minimal, optimized for in-memory operations
- **GDPR tracking**: Additional ~50 bytes per GDPR request

## Best Practices

### For High-Throughput Applications

```python
# Use larger cache sizes
engine = ModularMemoryEngine(max_cache_size=100000)

# Batch operations when possible
entry_ids = []
for data in batch_data:
    entry_id = await engine.remember(data)
    entry_ids.append(entry_id)
```

### For GDPR-Compliant Applications

```python
# Always enable GDPR features
engine = ModularMemoryEngine(enable_gdpr=True)

# Implement regular cleanup
deleted_count = await engine.forget_user("inactive_user_123")

# Maintain audit trails
audit_data = await engine.audit_forget("user_456")
```

### For Production Environments

```python
# Disable monitoring for production
engine = ModularMemoryEngine(enable_monitoring=False)

# Use appropriate cache sizes
engine = ModularMemoryEngine(max_cache_size=10000)

# Handle errors gracefully
try:
    result = await engine.remember(data)
except Exception as e:
    logger.error(f"Memory operation failed: {e}")
    # Implement fallback logic
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `ioa.core.memory_engine` is available
2. **Performance Issues**: Check cache size and monitoring settings
3. **GDPR Failures**: Verify GDPR features are enabled
4. **Memory Leaks**: Monitor cache size and implement cleanup

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging
logging.getLogger('ioa.core.memory_engine').setLevel(logging.DEBUG)
```

## Future Enhancements

- **Persistent Storage**: Integration with cold storage systems
- **Distributed Caching**: Multi-node memory coordination
- **Advanced Analytics**: Machine learning-based memory optimization
- **Real-time Streaming**: Event-driven memory updates

## Support

For issues and questions:

1. Check the test suite: `tests/memory/test_memory_engine.py`
2. Review GDPR compliance tests: `tests/compliance/test_gdpr_hooks.py`
3. Run benchmarks: `benchmarks/memory_bench_100k.py`
4. Check the shim compatibility: `src/memory_engine.py`
