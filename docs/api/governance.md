**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Governance API Reference

Governance and security API for IOA Core.

## Audit Chain

### `AuditChain`

Comprehensive audit logging with redaction and rotation.

```python
from src.governance.audit_chain import AuditChain

audit = AuditChain(
    log_path="./logs/audit/",
    rotation_size_mb=10,
    retention_days=90,
    redaction_enabled=True
)

# Log audit event
audit.log(
    event_type="agent_onboarding",
    user_id="admin",
    resource_id="agent_123",
    action="create",
    details={"capabilities": ["analysis"]}
)

# Query audit logs
events = audit.query({
    "event_type": "agent_onboarding",
    "start_date": "2025-01-01"
})
```

### `AuditEvent`

Individual audit log entry.

```python
@dataclass
class AuditEvent:
    event_id: str
    timestamp: datetime
    event_type: str
    user_id: str
    resource_id: str
    action: str
    details: Dict[str, Any]
    ip_address: str
    redacted: bool
    compliance_tags: List[str]
    risk_score: float
```

## PKI Engine

### `SignatureEngine`

Digital signature generation and verification.

```python
from src.governance.signature_engine import SignatureEngine

engine = SignatureEngine(algorithm="ed25519")

# Generate key pair
private_key, public_key = engine.generate_key_pair()

# Sign data
signature = engine.sign("agent_manifest", private_key)

# Verify signature
is_valid = engine.verify("agent_manifest", signature, public_key)
```

### `TrustRegistry`

Centralized storage of trusted public keys.

```python
from src.governance.trust_registry import TrustRegistry

registry = TrustRegistry()

# Register trusted key
registry.register_trusted_key(
    key_id="key_001",
    public_key=public_key,
    trust_level="verified"
)

# Check if key is trusted
is_trusted = registry.is_trusted_key(public_key)
```

## Policy Engine

### `PolicyEngine`

Rule-based access control and compliance.

```python
from src.governance.policy_engine import PolicyEngine

policy = PolicyEngine("governance_policy.yaml")

# Check policy compliance
result = policy.evaluate("data_access", {
    "user_id": "user123",
    "data_type": "sensitive",
    "user_trust_level": "verified"
})

if result.allowed:
    print("Access allowed")
else:
    print(f"Access denied: {result.reason}")
```

### Policy Definition

```yaml
# governance_policy.yaml
policies:
  - name: "Data Access Control"
    rules:
      - action: "data_access"
        conditions:
          - field: "data_type"
            operator: "in"
            values: ["sensitive", "confidential"]
          - field: "user_trust_level"
            operator: "gte"
            value: "verified"
        effect: "allow"
        audit: true
```

## Compliance Monitor

### `ComplianceMonitor`

Real-time policy violation detection.

```python
from src.governance.compliance_monitor import ComplianceMonitor

monitor = ComplianceMonitor(
    policies=["governance_policy.yaml"],
    alert_threshold=0.8,
    real_time=True
)

# Start monitoring
monitor.start()

# Register compliance hooks
@monitor.compliance_hook("data_access")
def monitor_data_access(event: AuditEvent):
    if "GDPR" in event.compliance_tags:
        # Check GDPR compliance
        if not verify_gdpr_compliance(event):
            monitor.raise_violation(
                "GDPR_VIOLATION",
                event,
                risk_score=0.9
            )
```

## Schema Validator

### `SchemaValidator`

Domain schema validation and enforcement.

```python
from src.governance.schema_validator import SchemaValidator

validator = SchemaValidator("domain_schema.yaml")

# Validate data
result = validator.validate("Dataset", {
    "id": "dataset_001",
    "name": "Sales Data",
    "size_mb": 15.5,
    "format": "csv"
})

if result.is_valid:
    print("✅ Data is valid")
else:
    print("❌ Validation errors:")
    for error in result.errors:
        print(f"  - {error.field}: {error.message}")
```

## Usage Examples

### Complete Governance Setup

```python
from src.governance.audit_chain import AuditChain
from src.governance.policy_engine import PolicyEngine
from src.governance.compliance_monitor import ComplianceMonitor

# Initialize components
audit = AuditChain(log_path="./logs/audit/")
policy = PolicyEngine("governance_policy.yaml")
compliance = ComplianceMonitor(policies=["governance_policy.yaml"])

# Enable governance
audit.enable_hooks()
policy.enable_enforcement()
compliance.start()

# Test governance system
audit.log(
    event_type="governance_setup",
    user_id="system",
    resource_id="governance_system",
    action="initialize"
)
```

### Policy Enforcement

```python
def check_policy_compliance(action: str, context: dict) -> PolicyResult:
    result = policy.evaluate(action, context)
    
    if result.allowed:
        audit.log(
            event_type="policy_check",
            user_id=context.get("user_id"),
            resource_id=context.get("resource_id"),
            action=action,
            details={"policy_result": "allowed"}
        )
        return result
    else:
        audit.log(
            event_type="policy_violation",
            user_id=context.get("user_id"),
            resource_id=context.get("resource_id"),
            action=action,
            details={"policy_result": "denied"}
        )
        return result
```

### Schema Validation

```python
class SchemaValidatedWorkflow:
    def __init__(self, schema_file: str):
        self.validator = SchemaValidator(schema_file)
    
    async def execute_step(self, step_name: str, data: dict) -> dict:
        # Validate input data
        validation_result = self.validator.validate(step_name, data)
        
        if not validation_result.is_valid:
            raise ValueError(f"Schema validation failed: {validation_result.errors}")
        
        # Execute step
        result = await self._execute_step_internal(step_name, data)
        
        # Validate output data
        output_validation = self.validator.validate(f"{step_name}_output", result)
        
        if not output_validation.is_valid:
            raise ValueError(f"Output validation failed: {output_validation.errors}")
        
        return result
```

## CLI Commands

### Audit Commands

> **Note**: Some commands below are examples for future functionality.

```bash
# Test audit logging
# Example (not currently implemented): ioa governance audit test

# Verify audit chain
# Example (not currently implemented): ioa governance audit verify

# Query audit logs
# Example (not currently implemented): ioa governance audit query --event-type agent_onboarding --start-date 2025-01-01
```

### PKI Commands

> **Note**: Some commands below are examples for future functionality.

```bash
# Generate key pair
# Example (not currently implemented): ioa governance pki generate --algorithm ed25519 --output-dir ./keys/

# List keys
# Example (not currently implemented): ioa governance pki list

# Export public key
# Example (not currently implemented): ioa governance pki export --key-id key_001 --output-file public.pem
```

### Policy Commands

> **Note**: Some commands below are examples for future functionality.

```bash
# Validate policy file
# Example (not currently implemented): ioa governance policy validate --file governance_policy.yaml

# Test policy enforcement
# Example (not currently implemented): ioa governance policy test --action data_access --context '{"user_id": "test"}'
```

### Schema Commands

> **Note**: Some commands below are examples for future functionality.

```bash
# Validate schema file
# Example (not currently implemented): ioa governance schema validate --file domain_schema.yaml

# Validate data against schema
# Example (not currently implemented): ioa governance schema validate --file domain_schema.yaml --data sample_data.json
```

## Error Handling

### Governance Errors

```python
from src.governance.exceptions import (
    GovernanceError, PolicyViolationError, SchemaValidationError
)

try:
    result = policy.evaluate("test_action", context)
except PolicyViolationError as e:
    print(f"Policy violation: {e}")
    audit.log(event_type="policy_violation", details={"error": str(e)})
except GovernanceError as e:
    print(f"Governance error: {e}")
```

## Best Practices

1. **Audit Management**
   - Log all sensitive operations
   - Use structured log formats
   - Regular log rotation

2. **Policy Design**
   - Start with least-privilege access
   - Clear, unambiguous rules
   - Regular policy reviews

3. **Compliance Monitoring**
   - Real-time violation detection
   - Automated response mechanisms
   - Clear escalation procedures

4. **Schema Validation**
   - Validate early and often
   - Clear error messages
   - Performance optimization

## Next Steps

1. Configure governance policies
2. Set up audit logging
3. Implement PKI verification
4. Test compliance monitoring
5. Monitor governance performance

## Related Docs

- [Core API Reference](core.md)
- [Governance Tutorial](../tutorials/governance-audit.md)
- [PKI Tutorial](../tutorials/pki-onboarding.md)
- [Schema Tutorial](../tutorials/domain-schema.md)
