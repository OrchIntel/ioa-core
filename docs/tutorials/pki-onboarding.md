**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# PKI Onboarding Tutorial

This tutorial covers Public Key Infrastructure (PKI) for agent trust verification in IOA Core.

## Quick Start

### 1. Generate Keys
> **Note**: Some commands below are examples for future functionality.

```bash
# Generate signing key pair
# Example (not currently implemented): ioa governance pki generate --algorithm ed25519 --output-dir ./keys/

# List keys
# Example (not currently implemented): ioa governance pki list
```

### 2. Enable PKI
```bash
export IOA_PKI_ENABLED=true
export IOA_PKI_KEYS_PATH="./keys/"
```

### 3. Test System
> **Note**: Some commands below are examples for future functionality.

```bash
# Example (not currently implemented): ioa governance pki test
# Example (not currently implemented): ioa governance pki verify --test
```

## Key Management

### Supported Algorithms
- **Ed25519** (Recommended): Fast, secure
- **RSA-2048**: Widely supported
- **RSA-4096**: High security

### Key Operations
> **Note**: Some commands below are examples for future functionality.

```bash
# Generate key
# Example (not currently implemented): ioa governance pki generate --algorithm ed25519 --type signing

# Export public key
# Example (not currently implemented): ioa governance pki export --key-id key_001 --output-file public.pem

# Show key details
# Example (not currently implemented): ioa governance pki show --key-id key_001
```

## Digital Signatures

### Signing Process
```python
from src.governance.signature_engine import SignatureEngine

engine = SignatureEngine(algorithm="ed25519")

# Sign manifest
manifest = {"agent_id": "agent_001", "capabilities": ["analysis"]}
canonical = json.dumps(manifest, sort_keys=True)
signature = engine.sign(canonical, private_key)

# Verify signature
is_valid = engine.verify(canonical, signature, public_key)
```

### Agent Onboarding
```python
class PKIAgentOnboarding:
    def onboard_agent_with_pki(self, manifest, signature, public_key):
        # Verify signature
        if not self.verify_signature(manifest, signature, public_key):
            raise ValueError("Signature verification failed")
        
        # Validate manifest
        if not self.validate_manifest(manifest):
            raise ValueError("Manifest validation failed")
        
        # Register agent
        return self.register_agent(manifest, public_key)
```

## Trust Registry

### Trust Levels
- **unverified**: No verification
- **verified**: Basic verification
- **trusted**: Enhanced verification
- **certified**: Full certification

### Registry Operations
```python
from src.governance.trust_registry import TrustRegistry

registry = TrustRegistry()

# Register trusted key
registry.register_trusted_key(
    key_id="key_001",
    public_key=public_key,
    trust_level="verified"
)

# Check trust
is_trusted = registry.is_trusted_key(public_key)
```

## Integration Examples

### Workflow with PKI
```yaml
# pki_workflow.yaml
name: "PKI-Verified Processing"
governance:
  pki_required: true
  trust_level_minimum: "verified"

steps:
  - name: "data_validation"
    pki:
      required: true
      trust_level: "verified"
```

### Agent Implementation
```python
    def execute_task(self, task, data):
        # Verify trust before execution
        if not self.verify_trust():
            raise ValueError("Trust verification failed")
        
        # Execute and sign result
        result = self._execute_task(task, data)
        signature = self.sign_result(result)
        
        return {
            "result": result,
            "signature": signature,
            "pki_verified": True
        }
```

## Best Practices

1. **Key Management**
   - Use Ed25519 for best performance
   - Implement regular rotation
   - Secure private key storage

2. **Trust Verification**
   - Multi-level verification
   - Regular registry audits
   - Clear trust definitions

3. **Security**
   - Never expose private keys
   - Monitor key expiration
   - Implement compromise procedures

## Next Steps

1. Test PKI functionality
2. Deploy keys securely
3. Monitor system health
4. Plan key rotation
5. Regular security audits

## Related Docs

- [Governance Tutorial](governance-audit.md)
- [Security Policy](../SECURITY.md)
- [API Reference](../api/governance.md)
