**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->


# IOA Memory Engine Modularization

## Overview

The IOA Memory Engine has been refactored from a monolithic architecture to a modular, pluggable system that supports hot/cold tier storage, vector indexing, and compliance features. This document provides the complete API reference and usage patterns for the new modular architecture.

## Architecture Components

### Core Interfaces (`ioa.memory.core.interfaces`)

The foundation of the modular system provides stable interfaces and data structures:

```python
from ioa.memory.core.interfaces import (
    MemoryStore,
    MemoryProcessor,
    MemoryEngineInterface,
    MemoryEntry,
    MemoryStats
)

# Core data structures
entry = MemoryEntry(
    id="entry_123",
    content="Sample memory content",
    metadata={"source": "user_input", "timestamp": "2025-08-30T10:00:00Z"},
    tags=["conversation", "user_query"]
)

# Interface contracts
class MyCustomStore(MemoryStore):
    def store(self, entry: MemoryEntry) -> str:
        """Store a memory entry and return its ID"""
        pass
    
    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by ID"""
        pass
```

### Scoped Memory Handles (`ioa.memory.core.scopes`)

Enforce tenancy and access control through scoped handles:

```python
from ioa.memory.core.scopes import ScopedMemoryHandle

# Create scoped handles for different contexts
project_handle = ScopedMemoryHandle(
    project_id="project_abc",
    user_id="user_123",
    agent_id="agent_xyz"
)

# Scoped operations automatically apply context
memory_engine.store_with_scope(entry, project_handle)
```

### Hot Store (`ioa.memory.hot.sqlite_store`)

Fast in-memory cache with SQLite persistence:

```python
from ioa.memory.hot.sqlite_store import SQLiteHotStore

hot_store = SQLiteHotStore(
    db_path=":memory:",  # In-memory for testing
    max_entries=10000,
    ttl_seconds=3600
)

# Fast operations
entry_id = hot_store.store(entry)
retrieved = hot_store.retrieve(entry_id)
```

### Cold Store (`ioa.memory.cold.s3_store`)

Long-term storage with S3/MinIO backend:

```python
from ioa.memory.cold.s3_store import S3ColdStore

cold_store = S3ColdStore(
    bucket_name="ioa-memory-archive",
    region="us-west-2",
    prefix="project_abc/"
)

# Graceful fallback when not configured
if cold_store.is_configured():
    cold_store.archive(entry)
else:
    logger.warning("Cold storage not configured, skipping archive")
```

### Vector Index (`ioa.memory.vector.faiss_index`)

Semantic search capabilities with FAISS:

```python
from ioa.memory.vector.faiss_index import FaissIndex

vector_index = FaissIndex(
    dimension=768,  # Embedding dimension
    index_type="IVFFlat"
)

# Index operations
vector_index.add_vectors(embeddings, ids)
similar_ids = vector_index.search(query_embedding, k=10)
```

### Compliance Engine (`ioa.memory.compliance.policy_chain`)

GDPR compliance and data governance:

```python
from ioa.memory.compliance.policy_chain import PolicyChain

policy_chain = PolicyChain(
    redaction_rules=["pii", "phi", "financial"],
    retention_policy="7_years",
    audit_enabled=True
)

# Compliance operations
redacted_entry = policy_chain.apply_redaction(entry)
policy_chain.process_gdpr_request("user_123", "erasure")
```

## Main Engine (`ioa.memory.engine`)

The orchestrator that coordinates all components:

```python
from ioa.memory.engine import ModularMemoryEngine

# Create engine with custom configuration
memory_engine = MemoryEngine(
    hot_store=SQLiteHotStore(),
    cold_store=S3ColdStore(),
    vector_index=FaissIndex(),
    policy_chain=PolicyChain(),
    tiering_strategy="hybrid"  # local, hybrid, cloud
)

# High-level operations
entry_id = memory_engine.remember(
    content="User query about project status",
    metadata={"context": "project_management"},
    tags=["query", "project"]
)

# Semantic search
results = memory_engine.search_semantic(
    query="What's the current project status?",
    limit=5
)

# GDPR compliance
export_data = memory_engine.export_user_data("user_123")
memory_engine.delete_user_data("user_123")
```

## Configuration Profiles

### Local Profile (Development/Testing)
```python
from ioa.memory import create_memory_engine

# Local-only configuration
local_engine = create_memory_engine(
    profile="local",
    hot_store_config={"db_path": "local_memory.db"}
)
```

### Hybrid Profile (Production)
```python
# Hybrid configuration with both tiers
hybrid_engine = create_memory_engine(
    profile="hybrid",
    hot_store_config={"max_entries": 50000},
    cold_store_config={"bucket": "ioa-prod-archive"},
    vector_index_config={"dimension": 1536}
)
```

### Cloud Profile (Serverless)
```python
# Cloud-only configuration
cloud_engine = create_memory_engine(
    profile="cloud",
    cold_store_config={"bucket": "ioa-serverless"},
    vector_index_config={"dimension": 768}
)
```

## Migration from Legacy

### Backward Compatibility

The legacy `src/memory_engine.py` remains as a compatibility layer:

```python
# Legacy imports still work
from src.memory_engine import MemoryEngine

# But emit deprecation warnings
import warnings
warnings.filterwarnings("default", category=DeprecationWarning)
```

### Gradual Migration

```python
# Step 1: Use new imports alongside legacy
from ioa.memory.engine import MemoryEngine
from src.memory_engine import MemoryEngine as LegacyEngine

# Step 2: Migrate configuration
new_engine = MemoryEngine.from_legacy_config(legacy_config)

# Step 3: Update code to use new APIs
# Legacy: engine.store(entry)
# New: engine.remember(content=entry.content, metadata=entry.metadata)
```

## Testing

### Unit Testing Individual Components

```python
import pytest
from ioa.memory.hot.sqlite_store import SQLiteHotStore
from ioa.memory.core.interfaces import MemoryEntry

def test_hot_store_operations():
    store = SQLiteHotStore(":memory:")
    entry = MemoryEntry(id="test_1", content="test content")
    
    # Test store
    stored_id = store.store(entry)
    assert stored_id == "test_1"
    
    # Test retrieve
    retrieved = store.retrieve("test_1")
    assert retrieved.content == "test content"
```

### Integration Testing

```python
def test_memory_engine_integration():
    engine = MemoryEngine(
        hot_store=SQLiteHotStore(":memory:"),
        vector_index=FaissIndex(dimension=128)
    )
    
    # Test end-to-end workflow
    entry_id = engine.remember("test content")
    results = engine.search_semantic("test content")
    
    assert len(results) > 0
    assert results[0].id == entry_id
```

## Performance Characteristics

### Memory Usage
- **Hot Store**: ~1KB per entry (in-memory + SQLite)
- **Cold Store**: ~500 bytes per entry (compressed)
- **Vector Index**: ~4 bytes per dimension per entry

### Throughput
- **Write**: 22,609 entries/sec (100k benchmark)
- **Read**: 127 entries/sec (100k benchmark)
- **Search**: 1,000 queries/sec (vector index)

### Scalability
- **Hot Store**: Up to 100k entries (configurable)
- **Cold Store**: Unlimited (S3/MinIO backed)
- **Vector Index**: Up to 1M entries (FAISS limits)

## Error Handling

### Graceful Degradation

```python
try:
    memory_engine.remember(content="important data")
except StorageError as e:
    # Fallback to hot store only
    logger.warning(f"Cold storage failed: {e}")
    hot_only_engine.remember(content="important data")
```

### Configuration Validation

```python
from ioa.memory.core.interfaces import ConfigurationError

try:
    engine = MemoryEngine(
        cold_store_config={"invalid": "config"}
    )
except ConfigurationError as e:
    logger.error(f"Invalid configuration: {e}")
    # Use safe defaults
    engine = MemoryEngine()
```

## Best Practices

### 1. Use Scoped Handles
Always use scoped handles for multi-tenant environments to prevent data leakage.

### 2. Configure TTLs
Set appropriate TTL values for hot store to prevent memory bloat.

### 3. Monitor Performance
Use the built-in metrics to monitor memory usage and performance.

### 4. Implement Fallbacks
Always implement fallback strategies for critical operations.

### 5. Regular Cleanup
Schedule regular cleanup of expired entries and old vector indices.

## Troubleshooting

### Common Issues

1. **Memory Leaks**: Check TTL configuration and implement cleanup schedules
2. **Performance Degradation**: Monitor hot store size and cold store latency
3. **Vector Search Failures**: Verify FAISS installation and dimension consistency
4. **GDPR Compliance**: Ensure audit logging is enabled and data retention policies are configured

### Debug Mode

```python
import logging
logging.getLogger("ioa.memory").setLevel(logging.DEBUG)

# Enable detailed logging for troubleshooting
memory_engine = MemoryEngine(debug_mode=True)
```

## Future Extensions

The modular architecture supports easy extension:

- **New Storage Backends**: Implement `MemoryStore` interface
- **Custom Processors**: Extend `MemoryProcessor` for specialized logic
- **Alternative Vector Indices**: Replace FAISS with other solutions
- **Enhanced Compliance**: Add new policy types and audit hooks

## API Reference

For complete API documentation, see the individual module docstrings and type hints. The modular architecture ensures that all public interfaces are stable and well-documented.
