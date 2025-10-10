**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Memory Fabric Quickstart

The Memory Fabric is IOA Core's modular memory system that provides flexible storage backends, encryption, and advanced querying capabilities.

## Quick Start

### Basic Usage

```python
from memory_fabric import MemoryFabric

# Initialize with default backend (local_jsonl)
fabric = MemoryFabric()

# Store content
record_id = fabric.store(
    content="Hello, Memory Fabric!",
    metadata={"source": "quickstart"},
    tags=["demo", "hello"]
)

# Retrieve content
record = fabric.retrieve(record_id)
print(record.content)  # "Hello, Memory Fabric!"

# Search content
results = fabric.search("hello")
print(f"Found {len(results)} results")

# Close when done
fabric.close()
```

### Using Different Backends

```python
# SQLite backend (recommended for production)
fabric = MemoryFabric(backend="sqlite")

# S3 backend (requires AWS credentials)
fabric = MemoryFabric(backend="s3", config={
    "bucket_name": "my-memory-bucket",
    "region": "us-west-2"
})
```

### Encryption

```python
# Enable encryption with a key
fabric = MemoryFabric(
    encryption_key="your-secret-key-here",
    backend="sqlite"
)

# Store encrypted content
record_id = fabric.store("Sensitive information")
# Content is automatically encrypted with AES-GCM
```

### Environment Configuration

Set these environment variables for automatic configuration:

```bash
export IOA_FABRIC_BACKEND=sqlite
export IOA_FABRIC_ROOT=./artifacts/memory/
export IOA_FABRIC_KEY=your-encryption-key
```

## CLI Commands

### Health Check

> **Note**: Some commands below are examples for future functionality.

```bash
# Check fabric health
# Example (not currently implemented): ioa fabric doctor

# Check specific backend
# Example (not currently implemented): ioa fabric doctor --backend sqlite --verbose
```

### Migration

> **Note**: Some commands below are examples for future functionality.

```bash
# Migrate from old memory_engine
# Example (not currently implemented): ioa fabric migrate --backend sqlite

# Dry run first
# Example (not currently implemented): ioa fabric migrate --dry-run --backend sqlite
```

### Deprecated Commands (use fabric instead)

> **Note**: Some commands below are examples for future functionality.

```bash
# These show deprecation warnings
# Example (not currently implemented): ioa memory doctor
# Example (not currently implemented): ioa memory migrate
```

## Next Steps

- [Backend Comparison](backends.md) - Choose the right backend
- [API Reference](api.md) - Detailed API documentation
- [Security Guide](security.md) - Encryption and security features
- [Migration Guide](migration.md) - Migrating from legacy memory systems
