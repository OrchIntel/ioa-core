**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# IOA System Laws Key Management

**Last Updated:** 2025-09-03  
**Status:** Active - OSS Launch Gate

## Overview

This document provides comprehensive guidance for managing cryptographic keys used to sign and verify the IOA System Laws manifest. Proper key management is critical for maintaining the integrity and trustworthiness of the governance framework.

## Key Types and Algorithms

### Supported Algorithms

The IOA System Laws framework supports the following signature algorithms:

- **RS256** - RSA with SHA-256 (Recommended for production)
- **ES256** - ECDSA with SHA-256 (Good for performance)
- **PS256** - RSA-PSS with SHA-256 (Enhanced security)

### Key Sizes

- **RSA Keys:** Minimum 2048 bits, recommended 4096 bits
- **ECDSA Keys:** P-256 (secp256r1) or P-384 (secp384r1)
- **Key Rotation:** Every 12-24 months for production keys

## Development Environment

### Development Keypair

For development and testing purposes, a development RSA keypair is provided:

> **Note**: Some commands below are examples for future functionality.

```bash
# Location
# src/ioa/core/governance/signing_keys/

# Files
# dev_private_key.pem    # Development private key (NEVER use in production)
# dev_public_key.pem     # Development public key for verification
# README.md              # Key management documentation
```

### Generating New Development Keys

If you need to generate new development keys:

> **Note**: Some commands below are examples for future functionality.

```bash
cd src/ioa/core/governance/signing_keys/

# Generate new RSA private key
# openssl genrsa -out dev_private_key.pem 2048

# Extract public key
# openssl rsa -in dev_private_key.pem -pubout -out dev_public_key.pem

# Set appropriate permissions
chmod 600 dev_private_key.pem
chmod 644 dev_public_key.pem
```

### Signing the Development Manifest

After generating new keys, sign the manifest:

```python
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import json
import base64

# Load private key
with open('dev_private_key.pem', 'rb') as f:
    private_key = serialization.load_pem_private_key(f.read(), password=None)

# Load manifest (without signature)
with open('../system_laws.json', 'r') as f:
    manifest = json.load(f)

# Remove existing signature
manifest.pop('signature', None)
manifest_str = json.dumps(manifest, sort_keys=True, separators=(',', ':'))

# Sign
signature = private_key.sign(
    manifest_str.encode('utf-8'),
    padding.PKCS1v15(),
    hashes.SHA256()
)

# Add signature
manifest['signature']['value'] = base64.b64encode(signature).decode('utf-8')

# Save signed manifest
with open('../system_laws.json', 'w') as f:
    json.dump(manifest, f, indent=2)
```

## Production Environment

### Critical Security Requirements

**NEVER** store production private keys in:
- Source code repositories
- Configuration files
- Environment variables
- Docker images
- Deployment packages

### Production Key Storage

Use secure key management systems:

#### AWS KMS

```python
import boto3
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

# Use KMS for signing
kms_client = boto3.client('kms')

def sign_with_kms(manifest_data, key_id):
    """Sign manifest using AWS KMS."""
    # Remove signature for signing
    manifest_copy = manifest_data.copy()
    manifest_copy.pop('signature', None)
    manifest_str = json.dumps(manifest_copy, sort_keys=True, separators=(',', ':'))
    
    # Sign with KMS
    response = kms_client.sign(
        KeyId=key_id,
        Message=manifest_str.encode('utf-8'),
        MessageType='RAW',
        SigningAlgorithm='RSASSA_PKCS1_V1_5_SHA_256'
    )
    
    return base64.b64encode(response['Signature']).decode('utf-8')
```

#### Azure Key Vault

```python
from azure.keyvault.keys import KeyClient
from azure.identity import DefaultAzureCredential

def sign_with_azure_keyvault(manifest_data, key_name, vault_url):
    """Sign manifest using Azure Key Vault."""
    credential = DefaultAzureCredential()
    client = KeyClient(vault_url=vault_url, credential=credential)
    
    # Remove signature for signing
    manifest_copy = manifest_data.copy()
    manifest_copy.pop('signature', None)
    manifest_str = json.dumps(manifest_copy, sort_keys=True, separators=(',', ':'))
    
    # Sign with Key Vault
    result = client.sign(
        key_name,
        'RS256',
        manifest_str.encode('utf-8')
    )
    
    return base64.b64encode(result.signature).decode('utf-8')
```

#### HashiCorp Vault

```python
import hvac

def sign_with_vault(manifest_data, key_path, vault_url, token):
    """Sign manifest using HashiCorp Vault."""
    client = hvac.Client(url=vault_url, token=token)
    
    # Remove signature for signing
    manifest_copy = manifest_data.copy()
    manifest_copy.pop('signature', None)
    manifest_str = json.dumps(manifest_copy, sort_keys=True, separators=(',', ':'))
    
    # Sign with Vault
    response = client.secrets.transit.sign_data(
        name=key_path,
        plaintext=base64.b64encode(manifest_str.encode('utf-8')).decode('utf-8'),
        hash_algorithm='sha2-256'
    )
    
    return response['data']['signature']
```

### Environment Configuration

Configure production keys via environment variables:

```bash
# Key management system configuration
export IOA_LAWS_KEY_PROVIDER="aws-kms"  # or "azure-keyvault", "hashicorp-vault"
export IOA_LAWS_KEY_ID="alias/ioa-system-laws"
export IOA_LAWS_VAULT_URL="https://your-vault.vault.azure.net/"
export IOA_LAWS_VAULT_TOKEN="your-vault-token"

# Optional: Override default key path
export IOA_LAWS_KEY_PATH="/path/to/production/public-key.pem"
```

## Key Rotation

### Rotation Schedule

- **Development Keys:** Rotate as needed (no schedule)
- **Production Keys:** Every 12-24 months
- **Emergency Rotation:** Immediately upon compromise

### Rotation Process

#### 1. Generate New Keypair

> **Note**: Some commands below are examples for future functionality.

```bash
# Generate new production keypair
# openssl genrsa -out new_private_key.pem 4096
# openssl rsa -in new_private_key.pem -pubout -out new_public_key.pem

# Verify key integrity
# openssl rsa -in new_private_key.pem -check
```

#### 2. Update Key Management System

```bash
# Upload new private key to KMS/Key Vault/Vault
# Update public key in deployment configuration
# Update key ID references
```

#### 3. Sign New Manifest

```python
# Sign manifest with new key
new_signature = sign_with_production_key(manifest_data, new_key_id)

# Update manifest signature
manifest['signature']['value'] = new_signature
manifest['signature']['kid'] = new_key_id
manifest['signature']['timestamp'] = datetime.now(timezone.utc).isoformat()
```

#### 4. Deploy and Verify

```bash
# Deploy updated manifest
# Verify signature validation works
# Monitor for any verification failures
```

#### 5. Cleanup

```bash
# Remove old keys after successful rotation
# Update documentation and procedures
# Archive old keys for audit purposes
```

### Emergency Rotation

In case of key compromise:

1. **Immediate Actions:**
   - Revoke compromised key
   - Generate new keypair
   - Sign new manifest
   - Deploy immediately

2. **Communication:**
   - Notify stakeholders
   - Update key rotation schedule
   - Document incident and response

3. **Recovery:**
   - Verify all systems using new key
   - Monitor for verification failures
   - Update incident response procedures

## Monitoring and Alerting

### Key Health Monitoring

Monitor key status and usage:

```python
# Key usage metrics
key_usage_count = get_key_usage_metrics(key_id)
key_last_used = get_key_last_used_timestamp(key_id)
key_rotation_due = check_key_rotation_schedule(key_id)

# Alert on key issues
if key_rotation_due:
    send_alert("Key rotation due", key_id)
if key_usage_count > threshold:
    send_alert("Unusual key usage", key_id)
```

### Signature Verification Monitoring

Monitor signature verification success rates:

```python
# Verification metrics
verification_success_rate = get_verification_success_rate()
verification_failure_count = get_verification_failure_count()

# Alert on verification failures
if verification_failure_count > 0:
    send_alert("Signature verification failures detected")
```

## Compliance and Audit

### Key Management Compliance

Maintain compliance with:

- **NIST SP 800-57:** Key management guidelines
- **ISO 27001:** Information security management
- **SOC 2:** Security controls and procedures
- **GDPR:** Data protection requirements

### Audit Requirements

Document and maintain:

- **Key Generation:** Date, method, and personnel
- **Key Distribution:** How keys are shared and stored
- **Key Usage:** Monitoring and logging of key operations
- **Key Destruction:** Secure disposal procedures
- **Incident Response:** Key compromise procedures

### Audit Trail

Maintain complete audit trail:

```json
{
  "key_id": "ioa-system-laws-2025-09",
  "generated": "2025-09-01T00:00:00Z",
  "algorithm": "RS256",
  "key_size": 4096,
  "generated_by": "security-team",
  "approved_by": "governance-council",
  "deployed": "2025-09-03T00:00:00Z",
  "rotation_due": "2026-09-01T00:00:00Z",
  "status": "active"
}
```

## Best Practices

### Security

1. **Key Isolation:** Use separate keys for different environments
2. **Access Control:** Limit key access to authorized personnel
3. **Monitoring:** Monitor all key operations and usage
4. **Backup:** Secure backup of key management systems
5. **Testing:** Regular testing of key rotation procedures

### Operations

1. **Automation:** Automate key rotation where possible
2. **Documentation:** Maintain current key management procedures
3. **Training:** Regular training for key management personnel
4. **Testing:** Test key management procedures regularly
5. **Recovery:** Document and test disaster recovery procedures

### Compliance

1. **Standards:** Follow industry key management standards
2. **Auditing:** Regular internal and external audits
3. **Reporting:** Regular compliance reporting
4. **Updates:** Keep procedures current with regulations
5. **Validation:** Validate compliance with governance requirements

## Troubleshooting

### Common Issues

#### Key Loading Failures

> **Note**: Some commands below are examples for future functionality.

```bash
# Check file permissions
ls -la signing_keys/
chmod 600 dev_private_key.pem
chmod 644 dev_public_key.pem

# Verify key format
# openssl rsa -in dev_private_key.pem -check
# openssl rsa -in dev_public_key.pem -pubin -text -noout
```

#### Signature Verification Errors

```bash
# Check key algorithm compatibility
# Verify manifest integrity
# Check timestamp validity
# Validate key ID references
```

#### Performance Issues

```bash
# Monitor key operation performance
# Check key size impact on performance
# Optimize key management system configuration
```

### Support Resources

- **Documentation:** [IOA Governance Documentation](../GOVERNANCE.md)
- **System Laws Spec:** [System Laws Specification](SYSTEM_LAWS.md)
- **Conformance Guide:** [Conformance Guide](CONFORMANCE.md)
- **Community:** IOA Governance Forum
- **Support:** governance-support@ioa.org

## Conclusion

Proper key management is essential for maintaining the integrity and trustworthiness of the IOA System Laws framework. Follow these guidelines to ensure secure, compliant, and auditable key management practices.

For questions about key management or security best practices, contact the IOA Security Team or refer to the supporting documentation.

**Remember:** Key management is not a one-time setup but an ongoing process that requires regular attention, monitoring, and updates to maintain security and compliance.
