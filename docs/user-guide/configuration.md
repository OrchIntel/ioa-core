**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# IOA Core Configuration Guide


## Overview

IOA Core provides flexible configuration options through environment variables, configuration files, and command-line arguments. This guide covers all available configuration options and their usage.

## Environment Variables

### Core System Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `IOA_NON_INTERACTIVE` | `0` | Set to `1` for non-interactive/CI environments |
| `IOA_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `IOA_CONFIG_DIR` | `./config` | Directory containing configuration files |
| `IOA_DATA_DIR` | `./data` | Directory for data storage |
| `IOA_CACHE_DIR` | `./cache` | Directory for caching |

### LLM Provider Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-...` |
| `GOOGLE_API_KEY` | Google AI API key | `AIza...` |
| `XAI_API_KEY` | xAI API key | `xai-...` |
| `GROK_API_KEY` | Grok API key | `grok-...` |
| `GROQ_API_KEY` | Groq API key | `gsk_...` |
| `OLLAMA_HOST` | Ollama server host | `http://localhost:11434` |

### Performance and Testing

| Variable | Default | Description |
|----------|---------|-------------|
| `IOA_100K_N` | `100000` | Number of iterations for performance tests |
| `IOA_REPORT_SUITE` | `pytest` | Test suite for reporting |
| `PYTHONWARNINGS` | `default` | Python warning level |

## Configuration Files

### Agent Onboarding Schema

Located at `config/agent_onboarding_schema.json`, this file defines the JSON schema for agent manifests:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["agent_id", "adapter_class", "capabilities", "tenant_id", "trust_signature"],
  "properties": {
    "agent_id": {"type": "string", "minLength": 3},
    "adapter_class": {"type": "string", "pattern": "^[a-z_]+\\.[A-Z][a-zA-Z]+$"},
    "capabilities": {"type": "array", "minItems": 1, "items": {"type": "string"}},
    "tenant_id": {"type": "string", "minLength": 2},
    "trust_signature": {"type": "string", "pattern": "^[A-Fa-f0-9]{64}$"},
    "metadata": {"type": "object"}
  }
}
```

### Governance Configuration

Located at `config/governance.config.yaml`, this file configures governance policies:

```yaml
governance:
  audit:
    enabled: true
    rotation_days: 30
    retention_days: 365
  
  reinforcement:
    enabled: true
    learning_rate: 0.01
    batch_size: 32
  
  compliance:
    gdpr_enabled: true
    data_retention_days: 90
    audit_logging: true
```

### Domain Profile Template

Located at `config/domain_profile_template.py`, this file provides templates for domain-specific configurations.

## CLI Configuration

### Onboarding Configuration

Use the `ioa onboard` command to configure LLM providers:

> **Note**: Some commands below are examples for future functionality.

```bash
# Add OpenAI provider
# Example (not currently implemented): ioa onboard add openai --key sk-your-key-here

# Add Anthropic provider
# Example (not currently implemented): ioa onboard add anthropic --key sk-ant-your-key-here

# Set default provider
# Example (not currently implemented): ioa onboard set-default openai

# List configured providers
# Example (not currently implemented): ioa onboard list

# Validate provider configuration
# Example (not currently implemented): ioa onboard validate openai
```

### Health Check Configuration

Use the `ioa health` command to check system health:

> **Note**: Some commands below are examples for future functionality.

```bash
# Basic health check
# Example (not currently implemented): ioa health

# Detailed health check
# Example (not currently implemented): ioa health --detailed

# Health check with specific modules
# Example (not currently implemented): ioa health --modules llm,governance,storage
```

## Configuration Best Practices

### Security

1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive configuration
3. **Set appropriate file permissions** (600 for config files)
4. **Rotate API keys** regularly
5. **Use secure storage** for production environments

### Performance

1. **Configure appropriate cache sizes** based on available memory
2. **Set reasonable timeouts** for API calls
3. **Use connection pooling** for database connections
4. **Monitor resource usage** and adjust limits accordingly

### Monitoring

1. **Enable audit logging** for compliance
2. **Set up metrics collection** for performance monitoring
3. **Configure alerting** for critical failures
4. **Regular health checks** in production

## Troubleshooting

### Common Configuration Issues

1. **Missing API keys**: Ensure environment variables are set correctly
2. **Permission errors**: Check file permissions on configuration files
3. **Path issues**: Verify configuration directory paths are correct
4. **Schema validation**: Ensure configuration files match expected schemas

### Debug Mode

Enable debug logging to troubleshoot configuration issues:

> **Note**: Some commands below are examples for future functionality.

```bash
export IOA_LOG_LEVEL=DEBUG
# Example (not currently implemented): ioa health --detailed
```

### Configuration Validation

Use the built-in validation tools:

> **Note**: Some commands below are examples for future functionality.

```bash
# Validate provider configuration
# Example (not currently implemented): ioa onboard validate

# Check system configuration
# Example (not currently implemented): ioa health --validate-config

# Test configuration loading
# Example (not currently implemented): ioa --config-test
```

## Examples

### Development Environment

> **Note**: Some commands below are examples for future functionality.

```bash
# Set development configuration
export IOA_LOG_LEVEL=DEBUG
export IOA_CONFIG_DIR=./config/dev
export IOA_DATA_DIR=./data/dev

# Run with development settings
# Example (not currently implemented): ioa health --detailed
```

### Production Environment

> **Note**: Some commands below are examples for future functionality.

```bash
# Set production configuration
export IOA_LOG_LEVEL=WARNING
export IOA_CONFIG_DIR=/etc/ioa/config
export IOA_DATA_DIR=/var/ioa/data
export IOA_NON_INTERACTIVE=1

# Run health check
# Example (not currently implemented): ioa health --detailed
```

### CI/CD Environment

```bash
# Set CI configuration
export IOA_NON_INTERACTIVE=1
export IOA_REPORT_SUITE=pytest
export PYTHONWARNINGS=error

# Run tests
python -m pytest tests/
```

## Related Documentation

- [CLI Reference](cli-reference.md) - Command-line interface reference
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
- [Getting Started](../getting-started/quickstart.md) - Quick start guide
- [Installation](../getting-started/installation.md) - Installation instructions
