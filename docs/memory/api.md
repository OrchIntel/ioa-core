**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Memory Fabric API Reference

Complete API reference for the Memory Fabric system.

## Core Classes

### MemoryFabric

Main facade class for Memory Fabric operations.

```python
from memory_fabric import MemoryFabric

fabric = MemoryFabric(
    backend="sqlite",           # Storage backend
    config={"data_dir": "./artifacts/memory"},  # Backend config
    encryption_key="secret",    # Optional encryption key
    enable_metrics=True         # Enable metrics collection
)
```

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `backend` | str | `"local_jsonl"` | Storage backend (`local_jsonl`, `sqlite`, `s3`) |
| `config` | dict | `{}` | Backend-specific configuration |
| `encryption_key` | str | `None` | AES-GCM encryption key |
| `enable_metrics` | bool | `True` | Enable metrics collection |

#### Methods

##### store(content, metadata=None, tags=None, memory_type="conversation", storage_tier="hot", record_id=None)

Store content in memory fabric.

**Parameters:**
- `content` (str): Content to store
- `metadata` (dict, optional): Metadata dictionary
- `tags` (list, optional): List of tags
- `memory_type` (str): Type of memory (`conversation`, `knowledge`, `context`, `metadata`)
- `storage_tier` (str): Storage tier (`hot`, `cold`, `auto`)
- `record_id` (str, optional): Custom record ID

**Returns:** `str` - Record ID

**Example:**
```python
record_id = fabric.store(
    content="User asked about pricing",
    metadata={"user_id": "123", "session": "abc"},
    tags=["pricing", "support"],
    memory_type="conversation"
)
```

##### retrieve(record_id)

Retrieve a memory record by ID.

**Parameters:**
- `record_id` (str): Record ID to retrieve

**Returns:** `MemoryRecordV1` or `None` if not found

**Example:**
```python
record = fabric.retrieve("abc123")
if record:
    print(record.content)
    print(record.metadata)
```

##### search(query, limit=10, memory_type=None, storage_tier=None)

Search for memory records.

**Parameters:**
- `query` (str): Search query
- `limit` (int): Maximum number of results
- `memory_type` (str, optional): Filter by memory type
- `storage_tier` (str, optional): Filter by storage tier

**Returns:** `List[MemoryRecordV1]` - List of matching records

**Example:**
```python
results = fabric.search("pricing", limit=5, memory_type="conversation")
for record in results:
    print(f"{record.id}: {record.content}")
```

##### delete(record_id)

Delete a memory record.

**Parameters:**
- `record_id` (str): Record ID to delete

**Returns:** `bool` - True if deleted, False otherwise

**Example:**
```python
success = fabric.delete("abc123")
```

##### list_all(limit=None)

List all memory records.

**Parameters:**
- `limit` (int, optional): Maximum number of records

**Returns:** `List[MemoryRecordV1]` - List of all records

**Example:**
```python
all_records = fabric.list_all(limit=100)
print(f"Total records: {len(all_records)}")
```

##### get_stats()

Get memory fabric statistics.

**Returns:** `dict` - Statistics dictionary

**Example:**
```python
stats = fabric.get_stats()
print(f"Total records: {stats['total_records']}")
print(f"Reads: {stats['reads']}")
print(f"Writes: {stats['writes']}")
```

##### health_check()

Perform health check on the memory fabric.

**Returns:** `dict` - Health status dictionary

**Example:**
```python
health = fabric.health_check()
print(f"Status: {health['status']}")
print(f"Backend: {health['backend']}")
```

##### close()

Close the memory fabric and cleanup resources.

**Example:**
```python
fabric.close()
```

## Schema Classes

### MemoryRecordV1

Main data structure for memory records.

```python
from memory_fabric import MemoryRecordV1

record = MemoryRecordV1(
    id="abc123",
    content="Hello world",
    metadata={"source": "test"},
    tags=["demo"],
    memory_type="conversation",
    storage_tier="hot"
)
```

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | str | Unique record identifier |
| `content` | str | Record content |
| `metadata` | dict | Metadata dictionary |
| `timestamp` | datetime | Creation timestamp |
| `tags` | list | List of tags |
| `storage_tier` | StorageTier | Storage tier enum |
| `memory_type` | MemoryType | Memory type enum |
| `access_count` | int | Number of accesses |
| `last_accessed` | datetime | Last access timestamp |
| `embedding` | EmbeddingV1 | Optional embedding vector |
| `__schema_version__` | str | Schema version |

#### Methods

##### to_dict()

Convert record to dictionary.

**Returns:** `dict` - Dictionary representation

##### from_dict(data)

Create record from dictionary.

**Parameters:**
- `data` (dict): Dictionary data

**Returns:** `MemoryRecordV1` - Record instance

##### redacted_view(redact_pii=True)

Get redacted view for logging.

**Parameters:**
- `redact_pii` (bool): Whether to redact PII

**Returns:** `MemoryRecordV1` - Redacted record

##### update_access()

Update access tracking.

##### is_expired(ttl_seconds=None)

Check if record is expired.

**Parameters:**
- `ttl_seconds` (int, optional): Time-to-live in seconds

**Returns:** `bool` - True if expired

### EmbeddingV1

Embedding vector data structure.

```python
from memory_fabric import EmbeddingV1

embedding = EmbeddingV1(
    vector=[0.1, 0.2, 0.3],
    model="text-embedding-ada-002",
    dimension=3
)
```

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `vector` | list | Embedding vector |
| `model` | str | Model used for embedding |
| `dimension` | int | Vector dimension |
| `__schema_version__` | str | Schema version |

## Storage Backends

### LocalJSONLStore

File-based storage using JSONL format.

```python
from memory_fabric.stores import LocalJSONLStore

store = LocalJSONLStore({
    "data_dir": "./artifacts/memory"
})
```

### SQLiteStore

SQLite-based storage with FTS.

```python
from memory_fabric.stores import SQLiteStore

store = SQLiteStore({
    "data_dir": "./artifacts/memory"
})
```

### S3Store

AWS S3-based storage.

```python
from memory_fabric.stores import S3Store

store = S3Store({
    "bucket_name": "my-bucket",
    "region": "us-west-2",
    "prefix": "memory/"
})
```

## Encryption

### MemoryCrypto

Encryption utilities for memory records.

```python
from memory_fabric import MemoryCrypto

crypto = MemoryCrypto("your-secret-key")

# Encrypt content
encrypted, mode = crypto.encrypt_content("sensitive data")

# Decrypt content
decrypted = crypto.decrypt_content(encrypted, mode)

# Redact PII
redacted = crypto.redact_pii("Email: user@example.com")
```

## Metrics

### MemoryFabricMetrics

Metrics collection and reporting.

```python
from memory_fabric import MemoryFabricMetrics

metrics = MemoryFabricMetrics()

# Record operation
metrics.record_operation("store", True, 15.5)

# Get current metrics
stats = metrics.get_current_metrics()

# Export metrics
export_file = metrics.export_metrics()
```

## Error Handling

### Common Exceptions

```python
from memory_fabric import MemoryFabric

try:
    fabric = MemoryFabric(backend="invalid")
except ValueError as e:
    print(f"Invalid backend: {e}")

try:
    record = fabric.retrieve("nonexistent")
except Exception as e:
    print(f"Retrieval failed: {e}")
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `IOA_FABRIC_BACKEND` | Default backend | `local_jsonl` |
| `IOA_FABRIC_ROOT` | Data directory | `./artifacts/memory/` |
| `IOA_FABRIC_KEY` | Encryption key | `None` |

## Examples

### Basic Usage

```python
from memory_fabric import MemoryFabric

# Initialize
fabric = MemoryFabric(backend="sqlite")

# Store data
record_id = fabric.store("Hello, world!", tags=["greeting"])

# Retrieve data
record = fabric.retrieve(record_id)
print(record.content)

# Search data
results = fabric.search("hello")
print(f"Found {len(results)} results")

# Cleanup
fabric.close()
```

### With Encryption

```python
from memory_fabric import MemoryFabric

# Initialize with encryption
fabric = MemoryFabric(
    backend="sqlite",
    encryption_key="my-secret-key"
)

# Store encrypted data
record_id = fabric.store("Sensitive information")

# Data is automatically encrypted/decrypted
record = fabric.retrieve(record_id)
print(record.content)  # "Sensitive information"

fabric.close()
```

### Custom Configuration

```python
from memory_fabric import MemoryFabric

# Custom SQLite configuration
fabric = MemoryFabric(
    backend="sqlite",
    config={
        "data_dir": "/custom/path",
        "wal_mode": True,
        "cache_size": 2000
    }
)

# Custom S3 configuration
fabric = MemoryFabric(
    backend="s3",
    config={
        "bucket_name": "my-memory-bucket",
        "region": "us-west-2",
        "prefix": "production/memory/"
    }
)
```
