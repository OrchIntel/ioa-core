**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Memory Engine Quickstart Guide

**IOA Module**: `docs/user-guide/memory_quickstart.md`  
**Version**: v2.5.0  
**Last-Updated**: 2025-01-27  
**Agents**: Cursor assist  
**Summary**: Quick start guide for the IOA Core Memory Engine

## Overview

This guide provides a quick introduction to using the IOA Core Memory Engine. You'll learn how to store, retrieve, and manage data with GDPR compliance in just a few minutes.

## Prerequisites

- Python 3.10+
- IOA Core installed
- Basic understanding of async/await syntax

## Installation

The memory engine is included with IOA Core. No additional installation is required.

## Quick Start

### 1. Basic Setup

```python
from ioa.core.memory_engine import ModularMemoryEngine

# Create a memory engine instance
memory = ModularMemoryEngine(
    enable_gdpr=True,           # Enable GDPR features
    enable_monitoring=True,      # Enable performance tracking
    max_cache_size=1000         # Limit memory usage
)
```

### 2. Store Your First Entry

```python
# Store a simple text entry
entry_id = await memory.remember({
    "content": "Hello, World!",
    "user_id": "user_123",
    "metadata": {"category": "greeting"}
})

print(f"Stored entry with ID: {entry_id}")
```

### 3. Retrieve the Entry

```python
# Get the entry back
entry = await memory.retrieve(entry_id)

if entry:
    print(f"Content: {entry.content}")
    print(f"User: {entry.user_id}")
    print(f"Created: {entry.timestamp}")
    print(f"Metadata: {entry.metadata}")
else:
    print("Entry not found")
```

### 4. List All Entries

```python
# Get all stored entries
all_entries = memory.list_all()

print(f"Total entries: {len(all_entries)}")
for entry in all_entries:
    print(f"- {entry['id']}: {entry['content']}")
```

## Common Operations

### Storing Different Types of Data

```python
# Store text content
text_id = await memory.remember({
    "content": "This is a text note",
    "user_id": "user_123",
    "tags": ["note", "text"]
})

# Store structured data
data_id = await memory.remember({
    "content": {"name": "John Doe", "age": 30, "city": "New York"},
    "user_id": "user_123",
    "metadata": {"type": "user_profile", "priority": "high"}
})

# Store with custom ID
custom_id = await memory.remember({
    "id": "custom_entry_001",
    "content": "Custom identified entry",
    "user_id": "user_123"
})
```

### Retrieving and Updating

```python
# Retrieve by ID
entry = await memory.retrieve("custom_entry_001")

# Check if entry exists
if entry:
    print("Entry found!")
else:
    print("Entry not found")

# Get entry statistics
stats = await memory.stats()
print(f"Total entries: {stats.total_entries}")
print(f"Average processing time: {stats.avg_processing_time}ms")
```

### Deleting Entries

```python
# Delete a specific entry
success = await memory.forget("custom_entry_001")
if success:
    print("Entry deleted successfully")
else:
    print("Entry not found or already deleted")

# Verify deletion
entry = await memory.retrieve("custom_entry_001")
print(f"Entry after deletion: {entry}")  # Should be None
```

## GDPR Compliance

### Data Portability

```python
# Export all data for a user
export_data = await memory.export_user("user_123")

print(f"User has {export_data['total_entries']} entries")
print(f"Export timestamp: {export_data['export_timestamp']}")

# Access individual entries
for entry in export_data['entries']:
    print(f"Entry: {entry['content']}")
    print(f"Created: {entry['timestamp']}")
    print(f"Metadata: {entry['metadata']}")
```

### Right to be Forgotten

```python
# Delete all data for a user
deleted_count = await memory.forget_user("user_123")
print(f"Deleted {deleted_count} entries for user")

# Verify all user data is gone
remaining_entries = memory.list_all()
user_entries = [e for e in remaining_entries if e['user_id'] == 'user_123']
print(f"Remaining entries for user: {len(user_entries)}")
```

### Audit Trail

```python
# Get audit trail for user deletion
audit_trail = await memory.audit_forget("user_123")

print(f"User ID: {audit_trail['user_id']}")
print(f"Total forget requests: {len(audit_trail['forget_requests'])}")

for request in audit_trail['forget_requests']:
    print(f"Request ID: {request['id']}")
    print(f"Status: {request['status']}")
    print(f"Created: {request['created_at']}")
    print(f"Completed: {request['completed_at']}")
```

## Performance Monitoring

### Enable Monitoring

```python
# Create engine with monitoring enabled
monitored_memory = ModularMemoryEngine(
    enable_monitoring=True,
    max_cache_size=5000
)

# Perform operations
for i in range(100):
    await monitored_memory.remember({
        "content": f"Test entry {i}",
        "user_id": "test_user"
    })

# Get performance statistics
stats = await monitored_memory.stats()
print(f"Total entries: {stats.total_entries}")
print(f"Failed entries: {stats.failed_entries}")
print(f"Average processing time: {stats.avg_processing_time}ms")
```

### Cache Management

```python
# Large cache for high throughput
high_perf_memory = ModularMemoryEngine(max_cache_size=50000)

# Small cache for memory constraints
low_mem_memory = ModularMemoryEngine(max_cache_size=100)

# Check current usage
stats = await high_perf_memory.stats()
print(f"Cache usage: {stats.total_entries} entries")
```

## Error Handling

### Graceful Error Handling

```python
from ioa.core.memory_engine import MemoryError, StorageError, ProcessingError

try:
    # Attempt to store data
    entry_id = await memory.remember({
        "content": "Test content",
        "user_id": "user_123"
    })
    print(f"Successfully stored: {entry_id}")
    
except MemoryError as e:
    print(f"Memory error: {e.message}")
    print(f"Operation: {e.operation}")
    print(f"Entry ID: {e.entry_id}")
    
except StorageError as e:
    print(f"Storage error: {e.message}")
    
except ProcessingError as e:
    print(f"Processing error: {e.message}")
    
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Handling Missing Entries

```python
# Safe retrieval with error handling
entry_id = "nonexistent_id"
entry = await memory.retrieve(entry_id)

if entry is None:
    print(f"Entry {entry_id} not found")
else:
    print(f"Found entry: {entry.content}")

# Safe deletion
success = await memory.forget(entry_id)
if not success:
    print(f"Could not delete {entry_id} - entry not found")
```

## Best Practices

### 1. Use Appropriate Cache Sizes

```python
# For development/testing
dev_memory = ModularMemoryEngine(max_cache_size=1000)

# For production with high throughput
prod_memory = ModularMemoryEngine(max_cache_size=100000)

# For memory-constrained environments
constrained_memory = ModularMemoryEngine(max_cache_size=100)
```

### 2. Batch Operations

```python
# Efficient batch processing
async def batch_store(data_list):
    entry_ids = []
    for data in data_list:
        entry_id = await memory.remember(data)
        entry_ids.append(entry_id)
    return entry_ids

# Use the batch function
data_batch = [
    {"content": f"Item {i}", "user_id": "user_123"}
    for i in range(100)
]

entry_ids = await batch_store(data_batch)
print(f"Stored {len(entry_ids)} items")
```

### 3. Regular Cleanup

```python
# Clean up old or unused data
async def cleanup_old_data(days_old=30):
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.now() - timedelta(days=days_old)
    all_entries = memory.list_all()
    
    deleted_count = 0
    for entry in all_entries:
        if entry['timestamp'] < cutoff_date:
            success = await memory.forget(entry['id'])
            if success:
                deleted_count += 1
    
    print(f"Cleaned up {deleted_count} old entries")
    return deleted_count

# Run cleanup
deleted = await cleanup_old_data(7)  # Clean up entries older than 7 days
```

### 4. Monitor Performance

```python
# Regular performance checks
async def check_performance():
    stats = await memory.stats()
    
    # Alert if processing time is high
    if stats.avg_processing_time > 100:  # 100ms threshold
        print(f"Warning: High processing time: {stats.avg_processing_time}ms")
    
    # Alert if failure rate is high
    if stats.failed_entries > 0:
        failure_rate = stats.failed_entries / stats.total_entries
        if failure_rate > 0.01:  # 1% threshold
            print(f"Warning: High failure rate: {failure_rate:.2%}")
    
    return stats

# Check performance every hour (in production)
performance_stats = await check_performance()
```

## Testing Your Setup

### Run the Test Suite

```bash
# Test memory engine functionality
pytest tests/memory/test_memory_engine.py -v

# Test GDPR compliance
pytest tests/compliance/test_gdpr_hooks.py -v

# Run with coverage
pytest tests/memory/test_memory_engine.py --cov=ioa.core.memory_engine --cov-report=term-missing
```

### Run Benchmarks

```bash
# Test with 100k entries
cd benchmarks
python3 memory_bench_100k.py --size 100000 --timeout 90

# Test with custom size
python3 memory_bench_100k.py --size 10000 --timeout 30
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```python
   # Ensure correct import path
   from ioa.core.memory_engine import ModularMemoryEngine
   ```

2. **Async/Await Issues**
   ```python
   # Make sure to use await
   entry_id = await memory.remember(data)  # Correct
   entry_id = memory.remember(data)        # Incorrect
   ```

3. **Memory Issues**
   ```python
   # Reduce cache size if running out of memory
   memory = ModularMemoryEngine(max_cache_size=100)
   ```

4. **GDPR Errors**
   ```python
   # Ensure GDPR is enabled
   memory = ModularMemoryEngine(enable_gdpr=True)
   ```

### Debug Mode

```python
import logging

# Enable debug logging
logging.getLogger('ioa.core.memory_engine').setLevel(logging.DEBUG)

# Create memory engine with debug info
memory = ModularMemoryEngine(enable_monitoring=True)
```

## Next Steps

1. **Read the full documentation**: `docs/MEMORY_ENGINE.md`
2. **Explore the test suite**: `tests/memory/test_memory_engine.py`
3. **Check GDPR compliance**: `tests/compliance/test_gdpr_hooks.py`
4. **Run performance benchmarks**: `benchmarks/memory_bench_100k.py`
5. **Review the shim layer**: `src/memory_engine.py`

## Support

For additional help:

- Check the comprehensive API documentation
- Review the test examples
- Run the benchmark suite
- Check the migration guide for legacy code

---

*This quickstart guide provides the essential information to get started with the IOA Core Memory Engine. For detailed API reference and advanced usage patterns, refer to the main documentation.*
