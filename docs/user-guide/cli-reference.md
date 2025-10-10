**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# IOA Core CLI Reference

This document provides a comprehensive reference for all IOA Core command-line interface commands.

## Overview

IOA Core provides a unified CLI for managing agents, workflows, and system operations. All commands follow the pattern:

> **Note**: Some commands below are examples for future functionality.

```bash
# Example (not currently implemented): ioa <command> <subcommand> [options] [arguments]
```

## Global Options

All commands support these global options:

> **Note**: Some commands below are examples for future functionality.

```bash
# --config FILE          # Configuration file path
# --log-level LEVEL      # Log level (DEBUG, INFO, WARNING, ERROR)
# --verbose, -v          # Verbose output
# --quiet, -q            # Quiet output
# --help, -h             # Show help
# --version              # Show version
```

## Core Commands

### `ioa config`

Manage IOA Core configuration.

> **Note**: Some commands below are examples for future functionality.

```bash
# Show current configuration
# Example (not currently implemented): ioa config show

# Initialize configuration
# Example (not currently implemented): ioa config init

# Set configuration value
# Example (not currently implemented): ioa config set <key> <value>

# Get configuration value
# Example (not currently implemented): ioa config get <key>

# Validate configuration
# Example (not currently implemented): ioa config validate
```

### `ioa onboard`

Manage agent onboarding and LLM provider configuration.

> **Note**: Some commands below are examples for future functionality.

```bash
# Interactive setup
# Example (not currently implemented): ioa onboard setup

# Non-interactive setup
# Example (not currently implemented): ioa onboard setup --non-interactive --provider <provider> --key <api-key>

# List configured providers
# Example (not currently implemented): ioa onboard llm list

# Add provider
# Example (not currently implemented): ioa onboard llm add <provider> <api-key>

# Remove provider
# Example (not currently implemented): ioa onboard llm remove <provider>

# Test provider connectivity
# Example (not currently implemented): ioa onboard llm smoke [--provider <provider>] [--live] [--offline]

# Show provider details
# Example (not currently implemented): ioa onboard llm show <provider>

# Diagnose issues
# Example (not currently implemented): ioa onboard llm doctor
```

#### LLM Provider Options

| Provider | Required Fields | Optional Fields |
|----------|-----------------|-----------------|
| `openai` | `api_key` | `model`, `base_url`, `org_id` |
| `anthropic` | `api_key` | `model` |
| `gemini` | `api_key` | `model` |
| `deepseek` | `api_key` | `model` |
| `xai` | `api_key` | `model` |
| `grok` | `api_key` | `model` |
| `ollama` | `host` | `model` |

### `ioa boot`

Create new IOA projects.

> **Note**: Some commands below are examples for future functionality.

```bash
# Interactive project creation
# Example (not currently implemented): ioa boot

# Non-interactive creation
# Example (not currently implemented): ioa boot --project-name <name> --template <template>

# List available templates
# Example (not currently implemented): ioa boot --list-templates

# Show template details
# Example (not currently implemented): ioa boot --show-template <template>
```

#### Project Templates

- `basic` - Minimal project with core configuration
- `governance` - Project with governance and audit features
- `workflow` - Project with workflow DSL support
- `multi-agent` - Project with multiple agent types

### `ioa workflows`

Manage and execute workflow definitions.

> **Note**: Some commands below are examples for future functionality.

```bash
# Run workflow
# Example (not currently implemented): ioa workflows run --file <workflow.yaml>

# List workflows
# Example (not currently implemented): ioa workflows list

# Show workflow details
# Example (not currently implemented): ioa workflows show <workflow>

# Validate workflow
# Example (not currently implemented): ioa workflows validate <workflow.yaml>

# Get workflow status
# Example (not currently implemented): ioa workflows status [<workflow-id>]

# View workflow logs
# Example (not currently implemented): ioa workflows logs [<workflow-id>]

# Get workflow results
# Example (not currently implemented): ioa workflows results [<workflow-id>]
```

#### Workflow Options

> **Note**: Some commands below are examples for future functionality.

```bash
# --file FILE            # Workflow definition file
# --dry-run             # Validate without execution
# --verbose             # Detailed output
# --timeout SECONDS     # Execution timeout
# --max-retries N       # Maximum retry attempts
```

### `ioa roundtable`

Execute multi-agent consensus tasks.

> **Note**: Some commands below are examples for future functionality.

```bash
# Run roundtable
# Example (not currently implemented): ioa roundtable run "Task description"

# Run with specific mode
# Example (not currently implemented): ioa roundtable run "Task" --mode <mode>

# Show roundtable statistics
# Example (not currently implemented): ioa roundtable stats

# Export schemas
# Example (not currently implemented): ioa roundtable export-schemas <directory>
```

#### Roundtable Modes

- `majority` - Simple majority voting
- `weighted` - Weighted voting by confidence
- `borda` - Borda count ranking system

#### Roundtable Options

> **Note**: Some commands below are examples for future functionality.

```bash
# --mode MODE            # Voting mode (majority, weighted, borda)
# --timeout SECONDS     # Execution timeout
# --quorum RATIO        # Quorum threshold (0.0-1.0)
# --tie-breaker TYPE    # Tie breaker (confidence, chair, random)
```

### `ioa agents`

Manage AI agents.

> **Note**: Some commands below are examples for future functionality.

```bash
# List agents
# Example (not currently implemented): ioa agents list

# Show agent details
# Example (not currently implemented): ioa agents show <agent-id>

# Create agent
# Example (not currently implemented): ioa agents create --manifest <manifest.json>

# Update agent
# Example (not currently implemented): ioa agents update <agent-id> --manifest <manifest.json>

# Remove agent
# Example (not currently implemented): ioa agents remove <agent-id>

# Test agent
# Example (not currently implemented): ioa agents test <agent-id> --task "Test task"
```

### `ioa memory`

Manage memory engine operations.

> **Note**: Some commands below are examples for future functionality.

```bash
# Show memory status
# Example (not currently implemented): ioa memory status

# List memory entries
# Example (not currently implemented): ioa memory list [--type <type>] [--limit <n>]

# Search memory
# Example (not currently implemented): ioa memory search <query> [--type <type>]

# Clear memory
# Example (not currently implemented): ioa memory clear [--type <type>]

# Export memory
# Example (not currently implemented): ioa memory export <file> [--type <type>]

# Import memory
# Example (not currently implemented): ioa memory import <file>
```

#### Memory Types

- `hot` - Hot storage (fast access)
- `cold` - Cold storage (persistent)
- `audit` - Audit logs
- `all` - All memory types

### `ioa governance`

Manage governance and audit operations.

> **Note**: Some commands below are examples for future functionality.

```bash
# Show governance status
# Example (not currently implemented): ioa governance status

# List policies
# Example (not currently implemented): ioa governance policies list

# Show policy details
# Example (not currently implemented): ioa governance policies show <policy>

# Create policy
# Example (not currently implemented): ioa governance policies create --file <policy.yaml>

# Update policy
# Example (not currently implemented): ioa governance policies update <policy> --file <policy.yaml>

# Remove policy
# Example (not currently implemented): ioa governance policies remove <policy>

# Show audit logs
# Example (not currently implemented): ioa governance audit logs [--limit <n>] [--since <timestamp>]

# Export audit logs
# Example (not currently implemented): ioa governance audit export <file> [--since <timestamp>]
```

### `ioa health`

Check system health and status.

> **Note**: Some commands below are examples for future functionality.

```bash
# Basic health check
# Example (not currently implemented): ioa health

# Detailed health check
# Example (not currently implemented): ioa health --detailed

# Health check with timeout
# Example (not currently implemented): ioa health --timeout <seconds>

# Health check specific components
# Example (not currently implemented): ioa health --components <component1,component2>
```

### `ioa version`

Show version information.

> **Note**: Some commands below are examples for future functionality.

```bash
# Show version
# Example (not currently implemented): ioa version

# Show detailed version info
# Example (not currently implemented): ioa version --detailed

# Show version in JSON format
# Example (not currently implemented): ioa version --json
```

## Environment Variables

IOA Core respects these environment variables:

> **Note**: Some commands below are examples for future functionality.

```bash
# Core configuration
# IOA_ENV=development
# IOA_CONFIG_DIR=~/.ioa/config
# IOA_LOG_LEVEL=INFO

# LLM providers
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# GOOGLE_API_KEY=...
# DEEPSEEK_API_KEY=...
# XAI_API_KEY=...
# GROK_API_KEY=...
# OLLAMA_HOST=http://localhost:11434

# Security
# IOA_AUDIT_ENABLED=true
# IOA_PKI_ENABLED=true
# IOA_ZERO_RETENTION_ENABLED=true
```

## Configuration Files

### Main Configuration (`~/.ioa/config/ioa.yaml`)

```yaml
# Core settings
core:
  environment: development
  debug: false
  log_level: INFO

# Memory settings
memory:
  hot_storage_size_mb: 1024
  cold_storage_size_mb: 10240
  pruning_threshold: 0.8

# Governance settings
governance:
  audit_enabled: true
  audit_retention_days: 90
  pki_enabled: true

# Security settings
security:
  zero_retention_enabled: true
  trust_verification_required: true
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
      "base_url": null
    }
  }
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
      "participants": [
        {
          "provider": "openai",
          "model": "gpt-4o-mini",
          "weight": 1.0
        }
      ]
    }
  }
}
```

## Examples

### Basic Workflow

> **Note**: Some commands below are examples for future functionality.

```bash
# 1. Setup environment
# Example (not currently implemented): ioa config init
# Example (not currently implemented): ioa onboard setup

# 2. Create project
# Example (not currently implemented): ioa boot --project-name my-project --template basic
cd my-project.ioa

# 3. Run workflow
# Example (not currently implemented): ioa workflows run --file workflow.yaml --verbose

# 4. Check status
# Example (not currently implemented): ioa workflows status
# Example (not currently implemented): ioa memory status
```

### Multi-Provider Roundtable

> **Note**: Some commands below are examples for future functionality.

```bash
# Configure multiple providers
# Example (not currently implemented): ioa onboard llm add openai sk-...
# Example (not currently implemented): ioa onboard llm add anthropic sk-ant-...

# Run roundtable with multiple providers
# Example (not currently implemented): ioa roundtable run "Analyze this code for security issues" \
#   --mode weighted \
#   --timeout 120 \
#   --quorum 0.8
```

### Governance and Audit

> **Note**: Some commands below are examples for future functionality.

```bash
# Create governance policy
# Example (not currently implemented): ioa governance policies create --file policy.yaml

# Run task with governance
# Example (not currently implemented): ioa workflows run --file workflow.yaml

# Check audit logs
# Example (not currently implemented): ioa governance audit logs --limit 100

# Export audit data
# Example (not currently implemented): ioa governance audit export audit_export.jsonl
```

## Troubleshooting

### Common Issues

1. **"Provider not configured"**
> **Note**: Some commands below are examples for future functionality.

   ```bash
# Example (not currently implemented):    ioa onboard llm list
# Example (not currently implemented):    ioa onboard llm add <provider> <key>
```

2. **"Configuration not found"**
> **Note**: Some commands below are examples for future functionality.

   ```bash
# Example (not currently implemented):    ioa config init
# Example (not currently implemented):    ioa config show
```

3. **"Permission denied"**
   ```bash
   ls -la ~/.ioa/
   chmod 700 ~/.ioa/
   chmod 600 ~/.ioa/config/*
```

4. **"Test failures"**
> **Note**: Some commands below are examples for future functionality.

   ```bash
# Example (not currently implemented):    ioa onboard llm smoke --offline
# Example (not currently implemented):    ioa health --detailed
```

### Getting Help

> **Note**: Some commands below are examples for future functionality.

```bash
# Command help
# Example (not currently implemented): ioa <command> --help

# Subcommand help
# Example (not currently implemented): ioa <command> <subcommand> --help

# Global help
# Example (not currently implemented): ioa --help
```

## Exit Codes

- `0` - Success
- `1` - General error
- `2` - Configuration error
- `3` - Validation error
- `4` - Provider error
- `5` - Permission error
- `6` - Resource error

## Best Practices

1. **Use virtual environments** for development
2. **Never commit API keys** to version control
3. **Use configuration files** for production settings
4. **Monitor audit logs** for security and compliance
5. **Test workflows** in dry-run mode first
6. **Set appropriate timeouts** for long-running tasks
7. **Use structured logging** for production deployments

---

*For more information, see the [IOA Core Documentation](https://ioa-core.readthedocs.io/)*
