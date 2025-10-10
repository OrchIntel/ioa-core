**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Configuration Guide

This guide covers advanced configuration options for IOA Core, including environment variables, configuration files, and system tuning.

## Configuration Hierarchy

IOA Core follows this configuration priority (highest to lowest):

1. **Environment Variables** - Take precedence, good for CI/CD
2. **Configuration Files** - Persistent settings, good for development
3. **Default Values** - Built-in defaults

## Environment Variables

### Core Configuration

```bash
# Environment
export IOA_ENV=development          # development, staging, production
export IOA_DEBUG=true               # Enable debug mode
export IOA_LOG_LEVEL=INFO           # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Paths
export IOA_CONFIG_DIR=~/.ioa/config # Configuration directory
export IOA_REGISTRY_PATH=./config/agent_trust_registry.json
export IOA_WORK_DIR=./work          # Working directory

# Performance
export IOA_MAX_WORKERS=4            # Maximum concurrent workers
export IOA_TASK_TIMEOUT=300         # Default task timeout (seconds)
export IOA_RETRY_ATTEMPTS=3         # Default retry attempts
```

### LLM Provider Configuration

```bash
# OpenAI
export OPENAI_API_KEY="sk-your-openai-key"
export OPENAI_ORG_ID="org-your-org-id"
export OPENAI_MODEL="gpt-4o-mini"
export OPENAI_BASE_URL="https://api.openai.com/v1"

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key"
export ANTHROPIC_MODEL="claude-3-haiku"

# Google Gemini
export GOOGLE_API_KEY="your-google-api-key"
export GOOGLE_MODEL="gemini-1.5-pro"

# DeepSeek
export DEEPSEEK_API_KEY="your-deepseek-key"
export DEEPSEEK_MODEL="deepseek-chat"

# XAI/Grok
export XAI_API_KEY="your-xai-key"
export GROK_API_KEY="your-grok-key"

# Ollama (Local)
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_MODEL="llama2"
```

### Security & Governance

```bash
# Audit Configuration
export IOA_AUDIT_ENABLED=true
export IOA_AUDIT_RETENTION_DAYS=90
export IOA_AUDIT_LOG_PATH=./logs/audit/
export IOA_AUDIT_ROTATION_SIZE_MB=10

# PKI Configuration
export IOA_PKI_ENABLED=true
export IOA_SIGNATURE_ALGORITHM=ed25519
export IOA_TRUST_VERIFICATION_REQUIRED=true

# Zero-Retention Controls
export IOA_ZERO_RETENTION_ENABLED=true
export IOA_DATA_RETENTION_DAYS=0

# Network Security
export IOA_HTTP_TIMEOUT=30
export IOA_HTTP_MAX_RETRIES=3
export IOA_HTTP_BACKOFF_FACTOR=2
```

### Memory Engine Configuration

```bash
# Storage Sizes
export IOA_HOT_STORAGE_SIZE_MB=1024
export IOA_COLD_STORAGE_SIZE_MB=10240
export IOA_MEMORY_PRUNING_THRESHOLD=0.8

# Memory Types
export IOA_MEMORY_HOT_ENABLED=true
export IOA_MEMORY_COLD_ENABLED=true
export IOA_MEMORY_AUDIT_ENABLED=true

# Pruning Configuration
export IOA_MEMORY_PRUNE_INTERVAL=300  # seconds
export IOA_MEMORY_MAX_ENTRIES=10000
```

## Configuration Files

### Main Configuration (`~/.ioa/config/ioa.yaml`)

```yaml
# Core settings
core:
  environment: development
  debug: false
  log_level: INFO
  max_workers: 4
  task_timeout: 300
  retry_attempts: 3

# Memory settings
memory:
  hot_storage_size_mb: 1024
  cold_storage_size_mb: 10240
  pruning_threshold: 0.8
  prune_interval: 300
  max_entries: 10000
  hot_enabled: true
  cold_enabled: true
  audit_enabled: true

# Governance settings
governance:
  audit_enabled: true
  audit_retention_days: 90
  audit_log_path: ./logs/audit/
  audit_rotation_size_mb: 10
  pki_enabled: true
  signature_algorithm: ed25519
  trust_verification_required: true

# Security settings
security:
  zero_retention_enabled: true
  data_retention_days: 0
  http_timeout: 30
  http_max_retries: 3
  http_backoff_factor: 2

# Performance settings
performance:
  max_concurrent_tasks: 10
  task_queue_size: 100
  memory_cleanup_interval: 60
  gc_threshold: 0.7
```

### LLM Configuration (`~/.ioa/config/llm.json`)

```json
{
  "version": 1,
  "default_provider": "openai",
  "providers": {
    "openai": {
      "api_key": "sk-...",
      "model": "gpt-4o-mini",
      "base_url": "https://api.openai.com/v1",
      "org_id": "org-...",
      "max_tokens": 4096,
      "temperature": 0.7,
      "timeout": 30
    },
    "anthropic": {
      "api_key": "sk-ant-...",
      "model": "claude-3-haiku",
      "max_tokens": 4096,
      "temperature": 0.7,
      "timeout": 30
    },
    "gemini": {
      "api_key": "...",
      "model": "gemini-1.5-pro",
      "max_tokens": 8192,
      "temperature": 0.7,
      "timeout": 30
    }
  },
  "fallback_strategy": "round_robin",
  "retry_on_failure": true,
  "max_retries": 3
}
```

### Roundtable Configuration (`~/.ioa/config/roundtable.json`)

```json
{
  "version": 1,
  "active": "default",
  "tables": {
    "default": {
      "quorum": 0.6,
      "merge_strategy": "vote_majority",
      "timeout": 300,
      "max_participants": 10,
      "participants": [
        {
          "provider": "openai",
          "model": "gpt-4o-mini",
          "weight": 1.0,
          "max_tokens": 512,
          "timeout": 30
        },
        {
          "provider": "anthropic",
          "model": "claude-3-haiku",
          "weight": 1.0,
          "max_tokens": 512,
          "timeout": 30
        }
      ]
    }
  },
  "voting_modes": {
    "majority": {
      "enabled": true,
      "tie_breaker": "confidence"
    },
    "weighted": {
      "enabled": true,
      "tie_breaker": "confidence"
    },
    "borda": {
      "enabled": true,
      "tie_breaker": "confidence"
    }
  }
}
```

### Governance Configuration (`~/.ioa/config/governance.yaml`)

```yaml
# Audit policies
audit:
  enabled: true
  retention_days: 90
  log_path: ./logs/audit/
  rotation_size_mb: 10
  compression: true
  encryption: false
  
  # Redaction patterns
  redaction:
    - pattern: "sk-[a-zA-Z0-9]{48}"
      replacement: "[API_KEY_REDACTED]"
    - pattern: "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
      replacement: "[EMAIL_REDACTED]"
    - pattern: "\\b\\d{3}-\\d{2}-\\d{4}\\b"
      replacement: "[SSN_REDACTED]"

# PKI policies
pki:
  enabled: true
  signature_algorithm: ed25519
  key_size: 256
  trust_verification_required: true
  certificate_authority: ./certs/ca.pem
  
  # Key rotation
  rotation:
    enabled: true
    interval_days: 90
    grace_period_days: 7

# Access control
access_control:
  enabled: true
  default_policy: deny
  rules:
    - resource: "agents/*"
      action: "read"
      roles: ["user", "admin"]
    - resource: "agents/*"
      action: "write"
      roles: ["admin"]
    - resource: "governance/*"
      action: "read"
      roles: ["admin"]
```

## Configuration Management

### Using the CLI

> **Note**: Some commands below are examples for future functionality.

```bash
# Show current configuration
# Example (not currently implemented): ioa config show

# Get specific value
# Example (not currently implemented): ioa config get core.environment

# Set configuration value
# Example (not currently implemented): ioa config set core.log_level DEBUG

# Validate configuration
# Example (not currently implemented): ioa config validate

# Export configuration
# Example (not currently implemented): ioa config export config_backup.yaml

# Import configuration
# Example (not currently implemented): ioa config import config_backup.yaml
```

### Configuration Validation

> **Note**: Some commands below are examples for future functionality.

```bash
# Validate all configuration files
# Example (not currently implemented): ioa config validate

# Validate specific file
# Example (not currently implemented): ioa config validate --file ~/.ioa/config/ioa.yaml

# Validate with schema
# Example (not currently implemented): ioa config validate --schema

# Check for conflicts
# Example (not currently implemented): ioa config validate --check-conflicts
```

### Environment-Specific Configuration

Create environment-specific configuration files:

> **Note**: Some commands below are examples for future functionality.

```bash
# Development
# ~/.ioa/config/ioa.dev.yaml

# Staging
# ~/.ioa/config/ioa.staging.yaml

# Production
# ~/.ioa/config/ioa.prod.yaml
```

Switch between environments:

> **Note**: Some commands below are examples for future functionality.

```bash
# Set environment
export IOA_ENV=production

# Or use config command
# Example (not currently implemented): ioa config set core.environment production
```

## Advanced Configuration

### Custom Agent Configuration

```yaml
# ~/.ioa/config/agents.yaml
    type: basic
    capabilities: ["greeting", "introduction"]
    parameters:
      tone: "friendly"
      language: "en"
      max_response_length: 500
    
    type: advanced
    capabilities: ["analysis", "insights", "summarization"]
    parameters:
      analysis_depth: "detailed"
      output_format: "json"
      include_confidence: true
      max_analysis_time: 60
```

### Workflow Templates

```yaml
# ~/.ioa/config/workflow_templates.yaml
templates:
  basic_analysis:
    name: "Basic Analysis Workflow"
    description: "Simple data analysis pipeline"
    steps:
      - name: data_collection
        task: "Collect data"
        timeout: 30
        
      - name: analysis
        task: "Analyze data"
        depends_on: [data_collection]
        timeout: 45
        
      - name: summary
        task: "Create summary"
        depends_on: [analysis]
        timeout: 30

  parallel_processing:
    name: "Parallel Processing"
    description: "Execute tasks in parallel"
    steps:
      - name: task_a
        task: "Process A"
        timeout: 30
        
      - name: task_b
        task: "Process B"
        timeout: 30
```

### Performance Tuning

```yaml
# ~/.ioa/config/performance.yaml
performance:
  # Memory management
  memory:
    hot_storage_size_mb: 2048
    cold_storage_size_mb: 20480
    pruning_threshold: 0.75
    cleanup_interval: 30
    
  # Task execution
  execution:
    max_workers: 8
    task_queue_size: 200
    task_timeout: 600
    retry_attempts: 5
    
  # Caching
  cache:
    enabled: true
    max_size_mb: 512
    ttl_seconds: 3600
    cleanup_interval: 300
```

## Security Configuration

### Network Security

```yaml
# ~/.ioa/config/security.yaml
security:
  # Network settings
  network:
    http_timeout: 30
    http_max_retries: 3
    http_backoff_factor: 2
    allow_insecure: false
    proxy_enabled: false
    proxy_url: null
    
  # Rate limiting
  rate_limiting:
    enabled: true
    requests_per_minute: 60
    burst_size: 10
    
  # TLS/SSL
  tls:
    enabled: true
    verify_ssl: true
    ca_cert_path: null
    client_cert_path: null
    client_key_path: null
```

### Access Control

```yaml
# ~/.ioa/config/access_control.yaml
access_control:
  enabled: true
  default_policy: deny
  
  # Role definitions
  roles:
    user:
      permissions: ["read:agents", "read:workflows", "execute:workflows"]
    admin:
      permissions: ["*"]
    auditor:
      permissions: ["read:audit", "read:governance"]
      
  # Resource policies
  resources:
      - resource: "agents/*"
        actions: ["read", "write", "delete"]
        roles: ["admin"]
      - resource: "agents/*"
        actions: ["read", "execute"]
        roles: ["user"]
        
    workflows:
      - resource: "workflows/*"
        actions: ["read", "write", "delete", "execute"]
        roles: ["admin"]
      - resource: "workflows/*"
        actions: ["read", "execute"]
        roles: ["user"]
```

## Monitoring & Logging

### Logging Configuration

```yaml
# ~/.ioa/config/logging.yaml
logging:
  level: INFO
  format: json
  output: file
  
  # File logging
  file:
    enabled: true
    path: ./logs/ioa.log
    max_size_mb: 100
    backup_count: 5
    rotation: size
    
  # Console logging
  console:
    enabled: true
    format: human
    
  # Structured logging
  structured:
    enabled: true
    include_timestamp: true
    include_level: true
    include_module: true
    include_function: true
    include_line: true
```

### Metrics Configuration

```yaml
# ~/.ioa/config/metrics.yaml
metrics:
  enabled: true
  backend: prometheus
  
  # Prometheus settings
  prometheus:
    port: 9090
    path: /metrics
    enable_histogram: true
    
  # Custom metrics
  custom:
    - name: "workflow_execution_time"
      type: "histogram"
      buckets: [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
      
    - name: "memory_usage_bytes"
      type: "gauge"
      
    - name: "active_agents"
      type: "counter"
```

## Troubleshooting

### Common Configuration Issues

#### 1. Configuration Not Found

> **Note**: Some commands below are examples for future functionality.

```bash
# Check configuration directory
ls -la ~/.ioa/config/

# Reinitialize configuration
# Example (not currently implemented): ioa config init

# Check environment variable
echo $IOA_CONFIG_DIR
```

#### 2. Permission Issues

```bash
# Check file permissions
ls -la ~/.ioa/config/

# Fix permissions
chmod 700 ~/.ioa/
chmod 600 ~/.ioa/config/*
```

#### 3. Configuration Conflicts

> **Note**: Some commands below are examples for future functionality.

```bash
# Check for conflicts
# Example (not currently implemented): ioa config validate --check-conflicts

# Show configuration sources
# Example (not currently implemented): ioa config show --sources

# Reset to defaults
# Example (not currently implemented): ioa config reset
```

#### 4. Validation Errors

> **Note**: Some commands below are examples for future functionality.

```bash
# Validate configuration
# Example (not currently implemented): ioa config validate --verbose

# Check YAML syntax
# yamllint ~/.ioa/config/*.yaml

# Check JSON syntax
python -m json.tool ~/.ioa/config/*.json
```

### Getting Help

> **Note**: Some commands below are examples for future functionality.

```bash
# Configuration help
# Example (not currently implemented): ioa config --help

# Validate configuration
# Example (not currently implemented): ioa config validate

# Show current settings
# Example (not currently implemented): ioa config show

# Export configuration for debugging
# Example (not currently implemented): ioa config export debug_config.yaml
```

## Best Practices

### 1. **Environment Separation**
- Use different configuration files for different environments
- Never commit production configuration to version control
- Use environment variables for sensitive settings

### 2. **Security First**
- Enable audit logging in production
- Use strong PKI configuration
- Implement proper access controls

### 3. **Performance Tuning**
- Monitor memory usage and adjust storage sizes
- Tune worker counts based on system resources
- Use appropriate timeouts for different operations

### 4. **Configuration Management**
- Use version control for configuration templates
- Document configuration changes
- Test configuration changes in development first

---

*For more configuration options, see the [CLI Reference](../user-guide/cli-reference.md) and [API Reference](../api/core.md)*
