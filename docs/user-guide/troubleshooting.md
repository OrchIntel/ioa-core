**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with IOA Core.

## Quick Diagnosis

Start with these commands to get an overview of your system:

> **Note**: Some commands below are examples for future functionality.

```bash
# Check system health
# Example (not currently implemented): ioa health --detailed

# Verify configuration
# Example (not currently implemented): ioa config show

# Check LLM providers
# Example (not currently implemented): ioa onboard llm list

# Test basic functionality
# Example (not currently implemented): ioa onboard llm smoke --offline
```

## Common Issues

### 1. Installation Problems

#### **"Command not found: ioa"**

**Symptoms:**
- `ioa: command not found` error
- `ioa --version` fails

**Causes:**
- IOA Core not installed
- Virtual environment not activated
- PATH not configured correctly

**Solutions:**
> **Note**: Some commands below are examples for future functionality.

```bash
# Check if installed
pip list | grep ioa

# Activate virtual environment
# source venv/bin/activate  # Linux/macOS
# or
# venv\Scripts\activate     # Windows

# Reinstall if needed
pip install -e ".[dev]"   # Source installation
# or
pip install ioa-core      # PyPI installation
```

#### **"Module not found" Errors**

**Symptoms:**
- Import errors during startup
- Missing dependency warnings

**Causes:**
- Incomplete installation
- Missing system dependencies
- Python version incompatibility

**Solutions:**
> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Check Python version
python3 --version  # Should be 3.9+

# Install system dependencies
# sudo apt install python3-dev build-essential  # Ubuntu/Debian
# sudo dnf install python3-devel gcc           # Fedora/CentOS
# brew install python3                         # macOS

# Reinstall IOA Core
pip uninstall ioa-core
pip install -e ".[dev]"
```

### 2. Configuration Issues

#### **"Configuration not found"**

**Symptoms:**
- `Configuration not found` error
- Default settings not working

**Causes:**
- Configuration directory missing
- Configuration files corrupted
- Permission issues

**Solutions:**
> **Note**: Some commands below are examples for future functionality.

```bash
# Check configuration directory
ls -la ~/.ioa/

# Reinitialize configuration
# Example (not currently implemented): ioa config init

# Check permissions
chmod 700 ~/.ioa/
chmod 600 ~/.ioa/config/*

# Verify configuration
# Example (not currently implemented): ioa config show
```

#### **"Invalid configuration"**

**Symptoms:**
- Configuration validation errors
- YAML/JSON syntax errors

**Causes:**
- Malformed configuration files
- Invalid values
- Schema violations

**Solutions:**
> **Note**: Some commands below are examples for future functionality.

```bash
# Validate configuration
# Example (not currently implemented): ioa config validate --verbose

# Check YAML syntax
# yamllint ~/.ioa/config/*.yaml

# Check JSON syntax
python -m json.tool ~/.ioa/config/*.json

# Reset to defaults
# Example (not currently implemented): ioa config reset
```

### 3. LLM Provider Issues

#### **"Provider not configured"**

**Symptoms:**
- `Provider not configured` error
- Live tests skip automatically

**Causes:**
- No API keys set
- Invalid API keys
- Configuration files missing

**Solutions:**
> **Note**: Some commands below are examples for future functionality.

```bash
# Check configured providers
# Example (not currently implemented): ioa onboard llm list

# Add provider
# Example (not currently implemented): ioa onboard llm add openai sk-your-api-key

# Test connectivity
# Example (not currently implemented): ioa onboard llm smoke --provider openai --live

# Check environment variables
# env | grep -i api
```

#### **"API key invalid"**

**Symptoms:**
- Authentication errors
- 401/403 HTTP responses
- Provider connection failures

**Causes:**
- Expired API keys
- Incorrect API keys
- Account suspended
- Rate limiting

**Solutions:**
> **Note**: Some commands below are examples for future functionality.

```bash
# Verify API key
# curl -H "Authorization: Bearer $OPENAI_API_KEY" \
#      https://api.openai.com/v1/models

# Check account status
# Visit provider dashboard

# Regenerate API key if needed
# Update configuration
# Example (not currently implemented): ioa onboard llm update openai sk-new-api-key
```

#### **"Connection timeout"**

**Symptoms:**
- Network timeouts
- Slow responses
- Connection refused errors

**Causes:**
- Network issues
- Firewall blocking
- Provider service down
- DNS resolution problems

**Solutions:**
> **Note**: Some commands below are examples for future functionality.

```bash
# Test network connectivity
# ping api.openai.com
# curl -v https://api.openai.com/v1/models

# Check firewall settings
# Verify proxy configuration

# Test with different network
# Contact network administrator
```

### 4. Workflow Execution Issues

#### **"Agent not found"**

**Symptoms:**
- `Agent not found` error
- Workflow fails to start

**Causes:**
- Agent not registered
- Agent configuration missing
- Agent type not supported

**Solutions:**
> **Note**: Some commands below are examples for future functionality.

```bash
# List available agents
# Example (not currently implemented): ioa agents list

# Check agent configuration
# Example (not currently implemented): ioa agents show <agent-id>

# Register agent if needed
# Example (not currently implemented): ioa agents create --manifest agent_manifest.json

# Verify agent types
# Example (not currently implemented): ioa agents types
```

#### **"Workflow validation failed"**

**Symptoms:**
- Workflow syntax errors
- Schema validation failures
- Invalid step definitions

**Causes:**
- YAML syntax errors
- Missing required fields
- Invalid step dependencies
- Schema violations

**Solutions:**
> **Note**: Some commands below are examples for future functionality.

```bash
# Validate workflow
# Example (not currently implemented): ioa workflows validate workflow.yaml --verbose

# Check YAML syntax
# yamllint workflow.yaml

# Fix common issues:
# - Check indentation
# - Verify step names are unique
# - Ensure dependencies exist
# - Validate agent names
```

#### **"Step execution failed"**

**Symptoms:**
- Individual steps fail
- Workflow stops at specific step
- Step timeout errors

**Causes:**
- Agent errors
- Resource constraints
- External service failures
- Configuration issues

**Solutions:**
> **Note**: Some commands below are examples for future functionality.

```bash
# Check step logs
# Example (not currently implemented): ioa workflows logs <workflow-id>

# Test individual agent
# Example (not currently implemented): ioa agents test <agent-id> --task "Test task"

# Check system resources
# Example (not currently implemented): ioa health --detailed

# Increase timeout if needed
# timeout: 60  # in workflow.yaml
```

### 5. Memory & Storage Issues

#### **"Memory full"**

**Symptoms:**
- Memory allocation errors
- Performance degradation
- Storage warnings

**Causes:**
- Memory limits reached
- Disk space full
- Memory leaks
- Large data accumulation

**Solutions:**
> **Note**: Some commands below are examples for future functionality.

```bash
# Check memory status
# Example (not currently implemented): ioa memory status

# Clear old entries
# Example (not currently implemented): ioa memory clear --type hot
# Example (not currently implemented): ioa memory clear --type cold

# Adjust memory limits
# Example (not currently implemented): ioa config set memory.hot_storage_size_mb 2048
# Example (not currently implemented): ioa config set memory.cold_storage_size_mb 20480

# Check disk space
# df -h
```

#### **"Audit log rotation failed"**

**Symptoms:**
- Audit logging errors
- Large log files
- Performance issues

**Causes:**
- Log rotation disabled
- Insufficient disk space
- Permission issues
- Configuration errors

**Solutions:**
> **Note**: Some commands below are examples for future functionality.

```bash
# Check audit configuration
# Example (not currently implemented): ioa config get governance.audit_enabled
# Example (not currently implemented): ioa config get governance.audit_rotation_size_mb

# Enable audit rotation
# Example (not currently implemented): ioa config set governance.audit_rotation_size_mb 10

# Check log directory permissions
ls -la ~/.ioa/logs/

# Clear old logs
# Example (not currently implemented): ioa governance audit clear --older-than 30d
```

### 6. Performance Issues

#### **"Workflow execution slow"**

**Symptoms:**
- Long execution times
- Timeout errors
- Resource exhaustion

**Causes:**
- Large data processing
- Network latency
- Resource constraints
- Inefficient workflows

**Solutions:**
> **Note**: Some commands below are examples for future functionality.

```bash
# Profile workflow execution
# Example (not currently implemented): ioa workflows run --file workflow.yaml --profile

# Check system resources
# top
# free -h
# df -h

# Optimize workflow
# - Reduce data size
# - Use parallel execution
# - Optimize agent tasks
# - Increase timeouts appropriately
```

#### **"Memory usage high"**

**Symptoms:**
- High memory consumption
- Slow response times
- System instability

**Causes:**
- Memory leaks
- Large data structures
- Inefficient algorithms
- Resource contention

**Solutions:**
> **Note**: Some commands below are examples for future functionality.

```bash
# Monitor memory usage
# Example (not currently implemented): ioa memory status --detailed

# Check for memory leaks
# Restart service if needed

# Optimize memory settings
# Example (not currently implemented): ioa config set memory.pruning_threshold 0.7
# Example (not currently implemented): ioa config set memory.cleanup_interval 30

# Use memory profiling tools
python -m memory_profiler script.py
```

### 7. Security & Governance Issues

#### **"Audit logging failed"**

**Symptoms:**
- Audit events not recorded
- Security warnings
- Compliance issues

**Causes:**
- Audit disabled
- Permission issues
- Storage problems
- Configuration errors

**Solutions:**
> **Note**: Some commands below are examples for future functionality.

```bash
# Enable audit logging
# Example (not currently implemented): ioa config set governance.audit_enabled true

# Check audit configuration
# Example (not currently implemented): ioa config show governance

# Verify permissions
ls -la ~/.ioa/logs/audit/

# Test audit functionality
# Example (not currently implemented): ioa governance audit test
```

#### **"PKI verification failed"**

**Symptoms:**
- Trust verification errors
- Agent onboarding failures
- Security warnings

**Causes:**
- Invalid signatures
- Expired certificates
- Key mismatches
- Configuration errors

**Solutions:**
> **Note**: Some commands below are examples for future functionality.

```bash
# Check PKI configuration
# Example (not currently implemented): ioa config get governance.pki_enabled

# Verify agent signatures
# Example (not currently implemented): ioa agents verify <agent-id>

# Regenerate keys if needed
# Update trust registry

# Check certificate validity
# openssl x509 -in cert.pem -text -noout
```

## Diagnostic Commands

### System Health Check

> **Note**: Some commands below are examples for future functionality.

```bash
# Comprehensive health check
# Example (not currently implemented): ioa health --detailed --timeout 60

# Check specific components
# Example (not currently implemented): ioa health --components memory,governance,agents

# Generate health report
# Example (not currently implemented): ioa health --output json > health_report.json
```

### Configuration Validation

> **Note**: Some commands below are examples for future functionality.

```bash
# Validate all configuration
# Example (not currently implemented): ioa config validate --verbose

# Check specific files
# Example (not currently implemented): ioa config validate --file ~/.ioa/config/ioa.yaml

# Export configuration for review
# Example (not currently implemented): ioa config export --format json > config_export.json
```

### Provider Testing

> **Note**: Some commands below are examples for future functionality.

```bash
# Test all providers
# Example (not currently implemented): ioa onboard llm smoke --verbose

# Test specific provider
# Example (not currently implemented): ioa onboard llm smoke --provider openai --live

# Diagnose provider issues
# Example (not currently implemented): ioa onboard llm doctor --verbose
```

### Workflow Testing

> **Note**: Some commands below are examples for future functionality.

```bash
# Validate workflow
# Example (not currently implemented): ioa workflows validate workflow.yaml --schema

# Test workflow in dry-run mode
# Example (not currently implemented): ioa workflows run --file workflow.yaml --dry-run

# Profile workflow execution
# Example (not currently implemented): ioa workflows run --file workflow.yaml --profile
```

## Log Analysis

### Finding Error Logs

> **Note**: Some commands below are examples for future functionality.

```bash
# Check application logs
# tail -f ~/.ioa/logs/ioa.log

# Check audit logs
# tail -f ~/.ioa/logs/audit/audit.log

# Check error logs
grep "ERROR" ~/.ioa/logs/ioa.log

# Check specific time period
grep "2025-08-19" ~/.ioa/logs/ioa.log
```

### Common Log Patterns

#### **Authentication Errors**
```
ERROR: Authentication failed for provider openai
ERROR: Invalid API key provided
ERROR: Rate limit exceeded
```

#### **Configuration Errors**
```
ERROR: Configuration file not found
ERROR: Invalid configuration value
ERROR: Schema validation failed
```

#### **Execution Errors**
```
ERROR: Agent execution failed
ERROR: Workflow step timeout
ERROR: Memory allocation failed
```

#### **Network Errors**
```
ERROR: Connection timeout
ERROR: Network unreachable
ERROR: SSL certificate error
```

## Performance Tuning

### Memory Optimization

```yaml
# ~/.ioa/config/performance.yaml
memory:
  hot_storage_size_mb: 1024      # Reduce if memory constrained
  cold_storage_size_mb: 5120     # Reduce if disk space limited
  pruning_threshold: 0.7         # More aggressive pruning
  cleanup_interval: 30           # More frequent cleanup
  max_entries: 5000             # Limit total entries
```

### Execution Optimization

```yaml
# ~/.ioa/config/performance.yaml
execution:
  max_workers: 2                 # Reduce if CPU constrained
  task_queue_size: 50            # Reduce if memory constrained
  task_timeout: 180              # Reduce if timeouts common
  retry_attempts: 2              # Reduce retry overhead
```

### Network Optimization

```yaml
# ~/.ioa/config/performance.yaml
network:
  http_timeout: 15               # Reduce timeout
  http_max_retries: 2            # Reduce retries
  http_backoff_factor: 1.5       # Faster backoff
  connection_pool_size: 5        # Limit connections
```

## Recovery Procedures

### Complete Reset

If all else fails, perform a complete reset:

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Backup current configuration
# cp -r ~/.ioa ~/.ioa.backup

# Remove configuration
# rm -rf ~/.ioa

# Reinstall IOA Core
pip uninstall ioa-core
pip install -e ".[dev]"

# Reinitialize configuration
# Example (not currently implemented): ioa config init

# Restore from backup if needed
# cp ~/.ioa.backup/config/* ~/.ioa/config/
```

### Partial Recovery

For specific component issues:

> **Note**: Some commands below are examples for future functionality.

```bash
# Reset specific configuration
# rm ~/.ioa/config/llm.json
# Example (not currently implemented): ioa onboard setup

# Reset memory
# Example (not currently implemented): ioa memory clear --type all

# Reset agents
# Example (not currently implemented): ioa agents reset

# Reset workflows
# Example (not currently implemented): ioa workflows reset
```

## Getting Help

### Self-Service Resources

1. **Documentation**: Check the [main docs](https://ioa-core.readthedocs.io/)
2. **FAQ**: Review [common questions](FAQ_IOA_CORE.md)
3. **Examples**: Look at [tutorials](../tutorials/) and examples
4. **CLI Help**: Use `ioa --help` and `ioa <command> --help`

### Community Support

1. **GitHub Issues**: [Report bugs](https://github.com/orchintel/ioa-core/issues)
2. **Discussions**: [Ask questions](https://github.com/orchintel/ioa-core/discussions)
3. **Documentation**: [Contribute improvements](https://github.com/orchintel/ioa-core)

### Professional Support

1. **Security Issues**: [security@orchintel.com](mailto:security@orchintel.com)
2. **Advanced Support**: [support@orchintel.com](mailto:support@orchintel.com)
3. **Consulting**: [consulting@orchintel.com](mailto:consulting@orchintel.com)

## Prevention

### Best Practices

1. **Regular Updates**: Keep IOA Core updated
2. **Monitoring**: Set up health checks and monitoring
3. **Backups**: Regular configuration and data backups
4. **Testing**: Test changes in development first
5. **Documentation**: Document custom configurations

### Monitoring Setup

> **Note**: Some commands below are examples for future functionality.

```bash
# Set up health monitoring
# crontab -e

# Add this line for hourly health checks
# 0 * * * * cd /path/to/ioa && ioa health --output json > health_$(date +\%Y\%m\%d_\%H).json
```

---

*For more help, see the [FAQ](FAQ_IOA_CORE.md) or [Community Support](https://github.com/orchintel/ioa-core/discussions)*
