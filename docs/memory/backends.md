**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Memory Fabric Backends

Memory Fabric supports multiple storage backends, each optimized for different use cases.

## Backend Comparison

| Backend | Pros | Cons | Best For |
|---------|------|------|----------|
| **local_jsonl** | Simple, no dependencies, human-readable | No indexing, slower queries | Development, small datasets |
| **sqlite** | Fast queries, ACID compliance, full-text search | Single file, not distributed | Production, medium datasets |
| **s3** | Scalable, distributed, durable | Requires AWS credentials, network latency | Cloud deployments, large datasets |

## Local JSONL Backend

**Default backend** - stores data in JSONL files.

### Features
- No external dependencies
- Human-readable format
- Simple file-based storage
- Good for development and testing

### Configuration
```python
fabric = MemoryFabric(
    backend="local_jsonl",
    config={
        "data_dir": "./artifacts/memory"
    }
)
```

### File Structure
```
artifacts/memory/
└── memory_run_abc123.jsonl
```

## SQLite Backend

**Recommended for production** - uses SQLite with WAL mode.

### Features
- ACID compliance
- Full-text search (FTS5)
- Indexed queries
- WAL mode for better concurrency
- Automatic schema management

### Configuration
```python
fabric = MemoryFabric(
    backend="sqlite",
    config={
        "data_dir": "./artifacts/memory"
    }
)
```

### Database Schema
```sql
CREATE TABLE memory_records (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    metadata TEXT,
    timestamp TEXT NOT NULL,
    tags TEXT,
    storage_tier TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    access_count INTEGER DEFAULT 0,
    last_accessed TEXT,
    embedding TEXT,
    schema_version TEXT NOT NULL
);

CREATE VIRTUAL TABLE memory_fts USING fts5(
    content, tags, content='memory_records'
);
```

## S3 Backend

**For cloud deployments** - stores data in AWS S3.

### Features
- Scalable storage
- Distributed access
- Automatic fallback to local storage
- Bucket-based organization
- Client-side AES-GCM encryption support
- End-to-end verification with `ioa fabric doctor --backend s3`

### Configuration

#### Environment Variables
```bash
# Required
export IOA_FABRIC_BACKEND=s3
export IOA_FABRIC_S3_BUCKET=your-bucket-name
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key

# Optional
export IOA_FABRIC_S3_PREFIX=ioa/memory/  # Default: ioa/memory/
export IOA_FABRIC_S3_REGION=us-east-1   # Default: us-east-1 or AWS_DEFAULT_REGION
export IOA_FABRIC_KEY=your-encryption-key  # Enables AES-GCM encryption
```

#### Programmatic Configuration
```python
fabric = MemoryFabric(
    backend="s3",
    config={
        "bucket_name": "my-memory-bucket",
        "region": "us-west-2",
        "prefix": "ioa/memory/"
    },
    encryption_key="your-encryption-key"  # Optional
)
```

### Prerequisites
- AWS credentials configured (via environment variables or IAM role)
- S3 bucket created
- Appropriate IAM permissions (see below)

### IAM Policy (Least Privilege)
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name",
                "arn:aws:s3:::your-bucket-name/ioa/memory/*"
            ]
        }
    ]
}
```

### Performance & Cost Notes
- **Write Performance**: O(1) - single object upload per record
- **Read Performance**: O(1) - single object download per record
- **Search Performance**: O(n) - requires listing and downloading objects
- **Storage Cost**: Pay per GB stored + API requests
- **Network Cost**: Data transfer charges apply
- **Recommended**: Use for large datasets where durability and scalability are priorities

### Sample Bucket Layout
```
your-bucket/
└── ioa/
    └── memory/
        ├── record_abc123.json
        ├── record_def456.json
        └── ...
```

### Verification & Testing
> **Note**: Some commands below are examples for future functionality.

```bash
# Test S3 backend health
# Example (not currently implemented): ioa fabric doctor --backend s3

# With verbose output
# Example (not currently implemented): ioa fabric doctor --backend s3 --verbose
```

The doctor command performs:
- Write 25 test records to S3
- Read back and verify all records
- Clean up test records
- Emit metrics to `artifacts/lens/memory_fabric/metrics.jsonl`
- Exit codes: 0 (healthy), 1 (partial), 2 (misconfigured)

### Clean-up Tips
- Use S3 lifecycle policies to automatically delete old test records
- Monitor S3 costs via AWS Cost Explorer
- Consider S3 Intelligent-Tiering for cost optimization
- Use S3 versioning for data protection

### Fallback Behavior
If S3 is unavailable, the backend automatically falls back to local JSONL storage in `./artifacts/memory/s3_fallback/`.

## Performance Characteristics

### Local JSONL
- **Write**: O(1) - append to file
- **Read**: O(n) - scan all records
- **Search**: O(n) - linear scan
- **Memory**: Low - file-based

### SQLite
- **Write**: O(log n) - indexed insert
- **Read**: O(log n) - indexed lookup
- **Search**: O(log n) - FTS index
- **Memory**: Medium - in-memory cache

### S3
- **Write**: O(1) - single object upload
- **Read**: O(1) - single object download
- **Search**: O(n) - list + download objects
- **Memory**: Low - streaming operations

## Choosing a Backend

### Development
```python
# Use local_jsonl for simple development
fabric = MemoryFabric(backend="local_jsonl")
```

### Production
```python
# Use sqlite for production workloads
fabric = MemoryFabric(backend="sqlite")
```

### Cloud/Scale
```python
# Use s3 for cloud deployments
fabric = MemoryFabric(backend="s3")
```

## Migration Between Backends

You can migrate data between backends:

```python
# Read from one backend
source = MemoryFabric(backend="local_jsonl")
records = source.list_all()

# Write to another backend
target = MemoryFabric(backend="sqlite")
for record in records:
    target.store(
        record.content,
        record.metadata,
        record.tags,
        record.memory_type.value,
        record.storage_tier.value,
        record.id
    )
```
