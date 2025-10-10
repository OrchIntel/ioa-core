**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Memory Fabric Security Guide

This document covers security considerations and best practices for the Memory Fabric system.

## Encryption Options

### Client-Side AES-GCM Encryption

**Recommended for sensitive data** - encrypts data before sending to storage backends.

#### Configuration
```bash
# Set encryption key
export IOA_FABRIC_KEY=your-32-byte-encryption-key

# Or use a base64-encoded key
export IOA_FABRIC_KEY=$(openssl rand -base64 32)
```

#### Features
- **Algorithm**: AES-GCM (Galois/Counter Mode)
- **Key Size**: 256-bit (32 bytes)
- **Authentication**: Built-in authentication prevents tampering
- **Performance**: Minimal overhead, hardware-accelerated on modern CPUs
- **Compatibility**: Works with all storage backends (local, SQLite, S3)

#### Usage
```python
from memory_fabric import MemoryFabric

# Encryption is automatically enabled when IOA_FABRIC_KEY is set
fabric = MemoryFabric(
    backend="s3",
    encryption_key="your-encryption-key"  # Optional if set via env var
)

# Store encrypted data
record_id = fabric.store(
    content="Sensitive information",
    metadata={"user_id": "123"},
    tags=["confidential"]
)

# Retrieve and automatically decrypt
record = fabric.retrieve(record_id)
print(record.content)  # Automatically decrypted
```

### S3 Server-Side Encryption (SSE)

**For compliance requirements** - encrypts data at rest in S3.

#### SSE-S3 (Default)
```python
# Automatically enabled - no configuration needed
fabric = MemoryFabric(backend="s3")
```

#### SSE-KMS (Customer Managed Keys)
```python
# Configure S3 client with KMS key
import boto3

s3_client = boto3.client('s3')
s3_client.put_object(
    Bucket='your-bucket',
    Key='your-key',
    Body=data,
    ServerSideEncryption='aws:kms',
    SSEKMSKeyId='arn:aws:kms:region:account:key/key-id'
)
```

#### Comparison: Client-Side vs Server-Side

| Aspect | Client-Side (AES-GCM) | Server-Side (SSE) |
|--------|----------------------|-------------------|
| **Data Protection** | End-to-end encryption | At-rest only |
| **Key Management** | You control keys | AWS manages keys |
| **Performance** | Minimal overhead | No client overhead |
| **Compliance** | Stronger (data never unencrypted) | Good for most requirements |
| **Backend Support** | All backends | S3 only |
| **Key Rotation** | Manual | Automatic (KMS) |

## S3 Security Best Practices

### IAM Policies

#### Least Privilege Access
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::your-bucket/ioa/memory/*"
        },
        {
            "Effect": "Allow",
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::your-bucket",
            "Condition": {
                "StringLike": {
                    "s3:prefix": "ioa/memory/*"
                }
            }
        }
    ]
}
```

#### Deny Insecure Transport
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": "arn:aws:s3:::your-bucket/*",
            "Condition": {
                "Bool": {
                    "aws:SecureTransport": "false"
                }
            }
        }
    ]
}
```

### Bucket Security

#### Enable Versioning
> **Note**: Some commands below are examples for future functionality.

```bash
# aws s3api put-bucket-versioning \
#     --bucket your-bucket \
#     --versioning-configuration Status=Enabled
```

#### Enable MFA Delete (Optional)
> **Note**: Some commands below are examples for future functionality.

```bash
# aws s3api put-bucket-versioning \
#     --bucket your-bucket \
#     --versioning-configuration Status=Enabled,MfaDelete=Enabled
```

#### Block Public Access
> **Note**: Some commands below are examples for future functionality.

```bash
# aws s3api put-public-access-block \
#     --bucket your-bucket \
#     --public-access-block-configuration \
#     BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

## Object Lock (WORM) for Audit Evidence

**For compliance and audit requirements** - prevents data modification for specified periods.

### Configuration
> **Note**: Some commands below are examples for future functionality.

```bash
# Enable Object Lock on bucket
# aws s3api put-object-lock-configuration \
#     --bucket your-bucket \
#     --object-lock-configuration '{
#         "ObjectLockEnabled": "Enabled",
#         "Rule": {
#             "DefaultRetention": {
#                 "Mode": "COMPLIANCE",
#                 "Days": 2555
#             }
#         }
#     }'
```

### Usage with Memory Fabric
```python
# Store with Object Lock retention
fabric = MemoryFabric(backend="s3")

# Records will be automatically protected by Object Lock
record_id = fabric.store(
    content="Audit evidence data",
    metadata={"audit": True, "retention_days": 2555},
    tags=["audit", "compliance"]
)
```

### Benefits
- **Immutable Records**: Data cannot be modified or deleted during retention period
- **Compliance**: Meets regulatory requirements for data retention
- **Audit Trail**: Provides tamper-proof evidence
- **Legal Hold**: Can be extended for legal proceedings

## Key Management

### Generating Secure Keys

#### Using OpenSSL
> **Note**: Some commands below are examples for future functionality.

```bash
# Generate 32-byte (256-bit) key
# openssl rand -base64 32

# Generate and save to file
# openssl rand -base64 32 > encryption.key
chmod 600 encryption.key
```

#### Using Python
```python
import secrets
import base64

# Generate secure random key
key = secrets.token_bytes(32)
key_b64 = base64.b64encode(key).decode('utf-8')
print(f"IOA_FABRIC_KEY={key_b64}")
```

### Key Storage Best Practices

1. **Environment Variables**: Store in secure environment variable management
2. **Secret Management**: Use AWS Secrets Manager, Azure Key Vault, or similar
3. **Key Rotation**: Implement regular key rotation procedures
4. **Access Control**: Limit access to encryption keys
5. **Backup**: Secure backup of keys for disaster recovery

### Key Rotation Strategy

```python
# Example key rotation implementation
def rotate_encryption_key(old_key, new_key):
    """Rotate encryption key for all records."""
    fabric_old = MemoryFabric(backend="s3", encryption_key=old_key)
    fabric_new = MemoryFabric(backend="s3", encryption_key=new_key)
    
    # Read all records with old key
    records = fabric_old.list_all()
    
    # Re-encrypt with new key
    for record in records:
        # Decrypt with old key
        decrypted_content = fabric_old.crypto.decrypt_content(record.content, "aes-gcm")
        
        # Encrypt with new key
        encrypted_content, _ = fabric_new.crypto.encrypt_content(decrypted_content)
        record.content = encrypted_content
        
        # Store with new key
        fabric_new.store(
            content=record.content,
            metadata=record.metadata,
            tags=record.tags,
            memory_type=record.memory_type.value,
            storage_tier=record.storage_tier.value,
            record_id=record.id
        )
```

## Network Security

### VPC Endpoints
For enhanced security, use VPC endpoints for S3 access:

> **Note**: Some commands below are examples for future functionality.

```bash
# Create VPC endpoint for S3
# aws ec2 create-vpc-endpoint \
#     --vpc-id vpc-12345678 \
#     --service-name com.amazonaws.region.s3 \
#     --route-table-ids rtb-12345678
```

### TLS/SSL
- All S3 communication uses HTTPS by default
- Memory Fabric enforces secure transport
- No configuration needed for TLS

## Monitoring and Auditing

### CloudTrail Integration
> **Note**: Some commands below are examples for future functionality.

```bash
# Enable CloudTrail for S3 API calls
# aws cloudtrail create-trail \
#     --name memory-fabric-audit \
#     --s3-bucket-name your-audit-bucket
```

### S3 Access Logging
> **Note**: Some commands below are examples for future functionality.

```bash
# Enable S3 access logging
# aws s3api put-bucket-logging \
#     --bucket your-bucket \
#     --bucket-logging-status '{
#         "LoggingEnabled": {
#             "TargetBucket": "your-logging-bucket",
#             "TargetPrefix": "access-logs/"
#         }
#     }'
```

### Memory Fabric Metrics
> **Note**: Some commands below are examples for future functionality.

```bash
# View encryption metrics
# Example (not currently implemented): ioa fabric doctor --backend s3 --verbose

# Check metrics file
cat artifacts/lens/memory_fabric/metrics.jsonl
```

## Compliance Considerations

### GDPR
- Use client-side encryption for personal data
- Implement data retention policies
- Enable audit logging
- Consider data residency requirements

### HIPAA
- Use S3 with appropriate BAA
- Enable server-side encryption
- Implement access controls
- Regular security assessments

### SOC 2
- Document security controls
- Implement monitoring and alerting
- Regular access reviews
- Incident response procedures

## Security Checklist

- [ ] Encryption key properly generated and stored
- [ ] IAM policies follow least privilege principle
- [ ] S3 bucket has appropriate security settings
- [ ] Network access is properly configured
- [ ] Monitoring and logging are enabled
- [ ] Key rotation procedures are documented
- [ ] Compliance requirements are met
- [ ] Regular security assessments are performed