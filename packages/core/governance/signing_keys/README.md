**Version:** v2.5.0  
**Last-Updated:** 2025-10-09

# IOA System Laws Signing Keys

This directory contains cryptographic keys for signing and verifying the IOA System Laws manifest.

## Development Keys

For development and testing purposes, we include a development RSA keypair:
- `dev_private_key.pem` - Development private key (NEVER use in production)
- `dev_public_key.pem` - Development public key for verification

## Production Keys

**CRITICAL**: Production keys are NEVER stored in this repository.

For production deployments:
1. Store private keys in secure key management systems (AWS KMS, Azure Key Vault, HashiCorp Vault)
2. Use environment variables or secure configuration to specify key paths
3. Implement key rotation procedures
4. Monitor key usage and access

## Key Management

### Development Setup
> **Note**: Some commands below are examples for future functionality.

```bash
# Generate new development keypair
# openssl genrsa -out dev_private_key.pem 2048
# openssl rsa -in dev_private_key.pem -pubout -out dev_public_key.pem

# Sign the manifest
python -c "
# from cryptography.hazmat.primitives import hashes, serialization
# from cryptography.hazmat.primitives.asymmetric import rsa, padding
# import json, base64

# Load private key
# with open('dev_private_key.pem', 'rb') as f:
#     private_key = serialization.load_pem_private_key(f.read(), password=None)

# Load manifest (without signature)
# with open('../system_laws.json', 'r') as f:
#     manifest = json.load(f)

# Remove existing signature
# manifest.pop('signature', None)
# manifest_str = json.dumps(manifest, sort_keys=True, separators=(',', ':'))

# Sign
# signature = private_key.sign(
#     manifest_str.encode('utf-8'),
#     padding.PKCS1v15(),
#     hashes.SHA256()
# )

# Add signature
# manifest['signature']['value'] = base64.b64encode(signature).decode('utf-8')

# Save signed manifest
# with open('../system_laws.json', 'w') as f:
#     json.dump(manifest, f, indent=2)
# "
```

### Production Setup
1. Generate production keypair in secure environment
2. Store private key in KMS/Vault
3. Deploy public key with application
4. Use secure key rotation procedures

## Security Notes

- Never commit private keys to version control
- Use strong key sizes (2048+ bits for RSA, 256+ bits for ECDSA)
- Implement proper key rotation schedules
- Monitor for unauthorized key usage
- Use hardware security modules (HSMs) for highest security requirements

## Environment Variables

- `IOA_LAWS_KEY_PATH` - Path to public key file (defaults to dev key)
- `IOA_LAWS_SIGNATURE_ALG` - Signature algorithm to use (defaults to RS256)
- `IOA_LAWS_VERIFICATION_STRICT` - Enable strict signature verification (default: true)
