# Ethics Cartridge (Aletheia-inspired)

## Overview

This cartridge provides runtime ethics hooks for AI systems, inspired by established ethics frameworks. It serves as a starting point for developers to implement ethical governance in their AI applications.

**Important Notice**: This cartridge is inspired by public ethics frameworks such as the Aletheia Framework v2.0 but is NOT a derivative or implementation of Aletheia. It uses IOA-original criteria names and neutral implementations.

## Attribution

**Aletheia Framework v2.0** by Rolls-Royce Civil Aerospace  
**License**: CC BY-ND 4.0 (Creative Commons Attribution-NoDerivatives 4.0 International)  
**Reference**: https://www.rolls-royce.com/innovation/the-aletheia-framework.aspx

**IOA Notice**: This cartridge references Aletheia for educational alignment only and does not modify, distribute, or create derivative materials based on the Aletheia Framework.

## Features

### Ethics Precheck
- **PII Detection**: Basic detection of personally identifiable information
- **Deception Detection**: Identification of potential manipulation attempts
- **Harmful Content Detection**: Basic screening for inappropriate content
- **Fairness Violation Detection**: Detection of potential bias or discrimination

### Decision Making
- **Confidence Scoring**: Each decision includes a confidence score (0.0-1.0)
- **Reason Tracking**: Detailed reasons for allow/block decisions
- **Strict Mode**: Option for stricter evaluation criteria
- **Metadata Support**: Additional context for decision tracking

## Usage

### Basic Usage

```python
from cartridges.ethics import precheck, EthicsDecision

# Check input for ethics violations
payload = {"text": "Hello, how can I help you?"}
result = precheck(payload)

if result.allow:
    print("Input approved")
else:
    print(f"Input blocked: {result.reasons}")
    print(f"Confidence: {result.confidence}")
```

### Strict Mode

```python
# Use stricter evaluation criteria
result = precheck(payload, strict_mode=True)
```

### Policy Validation

```python
from cartridges.ethics.policy_ethics import validate_ethics_policy

policy = {
    "name": "my_ethics_policy",
    "version": "1.0",
    "thresholds": {
        "pii": 0.8,
        "deception": 0.7,
        "harmful": 0.5
    }
}

if validate_ethics_policy(policy):
    print("Policy is valid")
```

## Configuration

### Ethics Decision Thresholds

The cartridge uses confidence-based decision making:

- **Confidence ≥ 0.5**: Allow (unless in strict mode)
- **Confidence < 0.5**: Block
- **Strict Mode**: Any violation blocks the request

### Customization

This is a basic implementation designed for demonstration and development. Production systems should:

1. **Use specialized libraries** for PII detection, content moderation, and bias detection
2. **Implement more sophisticated algorithms** for deception and fairness detection
3. **Add domain-specific rules** based on your application's requirements
4. **Integrate with external services** for comprehensive content analysis

## Testing

Run the smoke tests to verify functionality:

```bash
pytest tests/ethics/test_ethics_smoke.py -v
```

## Schema

The cartridge includes a JSON schema for ethics events:

- **File**: `schemas/ethics_event.schema.json`
- **Purpose**: Standardize ethics event logging and audit trails
- **Usage**: Validate ethics event data before storage

## Integration with IOA Core

This cartridge can be integrated with IOA Core's governance system:

1. **Policy Engine**: Register as a compliance cartridge
2. **Evidence Chain**: Log ethics decisions to audit trail
3. **Multi-LLM Orchestration**: Apply ethics checks across multiple models
4. **Memory Fabric**: Store ethics decision history for analysis

## Limitations

This is a **basic implementation** with several limitations:

- **Simple keyword matching** for content detection
- **No machine learning models** for sophisticated analysis
- **Limited customization options** for specific use cases
- **No external service integration** for comprehensive analysis

## Development

### Adding New Checks

To add new ethics checks:

1. Create a new detection function in `policy_ethics.py`
2. Add the check to the `precheck()` function
3. Update the confidence calculation logic
4. Add tests in `test_ethics_smoke.py`

### Example: Custom Check

```python
def contains_custom_violation(input_payload: Dict[str, Any]) -> bool:
    """Custom ethics check implementation."""
    # Your custom logic here
    return False

def precheck(input_payload: Dict[str, Any], strict_mode: bool = False) -> EthicsDecision:
    # ... existing checks ...
    
    # Add custom check
    if contains_custom_violation(input_payload):
        reasons.append("Custom violation detected")
        confidence *= 0.6
    
    # ... rest of function ...
```

## Related Documentation

- [IOA Governance Overview](../../../../docs/governance/GOVERNANCE.md)
- [Aletheia Reference](../../../../docs/ethics/aletheia/README.md)
- [Policy Cartridges](../../../../docs/governance/)
- [Evidence Chain Documentation](../../../../docs/examples/)

## License

This cartridge is part of IOA Core and is licensed under the Apache License 2.0. See the main project LICENSE file for details.

## Support

For questions about this cartridge or ethics integration:

- **GitHub Issues**: [IOA Core Issues](https://github.com/OrchIntel/ioa-core/issues)
- **Documentation**: [IOA Docs](https://ioa.systems/docs)
- **Community**: [IOA Community](https://github.com/OrchIntel/ioa-core)
