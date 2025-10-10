# IOA Audit System Documentation

Comprehensive audit system documentation is available in the open-source distribution.

## Core Audit Documentation

The audit system is fully documented within this repository:

- **Overview**: See `docs/core/audit-chain.md`
- **Implementation**: Check the `src/ioa_core/governance/audit_chain.py` module
- **Examples**: Review test cases in `tests/audit/`

## Enterprise Extensions

Advanced audit features (S3 backends, tamper detection, enterprise integrations) are documented separately for authorized users.

## Quick Start

```python
from ioa_core.governance.audit_chain import AuditChain

# Create audit chain
chain = AuditChain()

# Log operations
chain.log_operation("action", {"key": "value"})

# Verify integrity
is_valid = chain.verify()
```

## Related Documentation

- [Governance System](../governance/SYSTEM_LAWS.md)
- [Seven Rules](../governance/SYSTEM_LAWS.md)
- [API Reference](../api/)

