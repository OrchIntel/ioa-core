**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# IOA Core Onboarding Guide

**Welcome to IOA Core!** This guide will help you get started with setting up and using the platform.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [First-Time Setup](#first-time-setup)
4. [LLM Provider Configuration](#llm-provider-configuration)
5. [Project Creation](#project-creation)
6. [Running Your First Workflow](#running-your-first-workflow)
7. [Testing & Validation](#testing--validation)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **Python**: 3.9 or newer
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Storage**: 2GB free space
- **OS**: Linux, macOS, or Windows (WSL recommended for Windows)

### Python Environment
We recommend using a virtual environment:

> **Note**: Some commands below are examples for future functionality.

```bash
# Create virtual environment
python -m venv ioa-env

# Activate (Linux/macOS)
# source ioa-env/bin/activate

# Activate (Windows)
# ioa-env\Scripts\activate
```

### Optional: FAISS Installation
For enhanced vector search performance, install FAISS:
> **Note**: Some commands below are examples for future functionality.

```bash
# Using pip (CPU-only)
pip install faiss-cpu

# Using conda (CPU-only)
# conda install -c conda-forge faiss-cpu

# Using conda (GPU support)
# conda install -c conda-forge faiss-gpu
```
*Note: FAISS is optional; the system will automatically fall back to TF-IDF vector search if not available.*

## Installation

### Option 1: Install from Source (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/orchintel/ioa-core.git
cd ioa-core

# Install in development mode
pip install -e ".[dev]"
```

### Option 2: Install from PyPI (Production)

```bash
pip install ioa-core
```

### Option 3: Install with Docker

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Pull the image
# docker pull orchintel/ioa-core:latest

# Run a container
# docker run -it --rm orchintel/ioa-core:latest
```

## First-Time Setup

### 1. Initialize Configuration

> **Note**: Some commands below are examples for future functionality.

```bash
# Create configuration directory
mkdir -p ~/.ioa/config

# Generate default configuration
# Example (not currently implemented): ioa config init
```

### 2. Verify Installation

> **Note**: Some commands below are examples for future functionality.

```bash
# Check version
# Example (not currently implemented): ioa --version

# Check configuration
# Example (not currently implemented): ioa config show

# Run health check
# Example (not currently implemented): ioa health
```

## LLM Provider Configuration

IOA Core supports multiple LLM providers. You can configure one or more based on your needs.

### Environment Variables

Create a `.env` file in your project root:

> **Note**: Some commands below are examples for future functionality.

```bash
# OpenAI
# OPENAI_API_KEY=sk-your-openai-key

# Anthropic
# ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Google Gemini
# GOOGLE_API_KEY=your-google-api-key

# DeepSeek
# DEEPSEEK_API_KEY=your-deepseek-key

# XAI/Grok
# XAI_API_KEY=your-xai-key

# Ollama (local)
# OLLAMA_HOST=http://localhost:11434
```

### Interactive Setup

Use the interactive setup command:

> **Note**: Some commands below are examples for future functionality.

```bash
# Interactive setup
# Example (not currently implemented): ioa onboard setup

# Non-interactive setup
# Example (not currently implemented): ioa onboard setup --non-interactive --provider openai --key sk-your-key
```

### Provider-Specific Configuration

#### OpenAI
```bash
export OPENAI_API_KEY="sk-your-key"
export OPENAI_ORG_ID="org-your-org-id"  # Optional
```

#### Anthropic
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key"
```

#### Google Gemini
```bash
export GOOGLE_API_KEY="your-google-api-key"
```

#### DeepSeek
```bash
export DEEPSEEK_API_KEY="your-deepseek-key"
```

#### XAI/Grok
```bash
export XAI_API_KEY="your-xai-key"
export GROK_API_KEY="your-grok-key"  # Alternative
```

#### Ollama (Local)
> **Note**: Some commands below are examples for future functionality.

```bash
# Install Ollama first
# curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
# ollama serve

# Pull a model
# ollama pull llama2

# Set host (optional, defaults to localhost:11434)
export OLLAMA_HOST="http://localhost:11434"
```

### Test Provider Connectivity

> **Note**: Some commands below are examples for future functionality.

```bash
# Test all providers
# Example (not currently implemented): ioa onboard llm smoke

# Test specific provider
# Example (not currently implemented): ioa onboard llm smoke --provider openai --live

# Test offline mode
# Example (not currently implemented): ioa onboard llm smoke --offline
```

## Project Creation

### 1. Create New Project

> **Note**: Some commands below are examples for future functionality.

```bash
# Interactive project creation
# Example (not currently implemented): ioa boot

# Non-interactive creation
# Example (not currently implemented): ioa boot --project-name my-ai-system --template basic
```

### 2. Project Structure

A new project will create:

```
my-ai-system.ioa/
├── config/
│   ├── agents.json
│   ├── workflows.yaml
│   └── governance.json
├── schemas/
│   └── message_schema.json
├── agents/
│   └── README.md
└── README.md
```

### 3. Navigate to Project

> **Note**: Some commands below are examples for future functionality.

```bash
cd my-ai-system.ioa
# Example (not currently implemented): ioa status
```

## Running Your First Workflow

### 1. Simple Hello World

Create a basic workflow file `workflow.yaml`:

```yaml
name: Hello World
description: Simple workflow to test IOA Core

steps:
  - name: greet
    task: "Say hello to the world"
    timeout: 30

  - name: respond
    task: "Respond to the greeting"
    depends_on: [greet]
    timeout: 30
```

### 2. Run the Workflow

> **Note**: Some commands below are examples for future functionality.

```bash
# Run workflow
# Example (not currently implemented): ioa workflows run --file workflow.yaml

# Run with verbose output
# Example (not currently implemented): ioa workflows run --file workflow.yaml --verbose

# Run in dry-run mode
# Example (not currently implemented): ioa workflows run --file workflow.yaml --dry-run
```

### 3. Monitor Execution

> **Note**: Some commands below are examples for future functionality.

```bash
# Check workflow status
# Example (not currently implemented): ioa workflows status

# View logs
# Example (not currently implemented): ioa workflows logs

# Get results
# Example (not currently implemented): ioa workflows results
```

## Testing & Validation

### 1. Unit Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/smoke/
```

### 2. Performance Tests

```bash
# Run performance tests
pytest tests/performance/ -m performance

# Run 100k test locally
pytest tests/performance/test_100k.py -v
```

### 3. Smoke Tests

```bash
# Run smoke tests (no live keys required)
pytest tests/smoke/ -m smoke

# Run live smoke tests (requires API keys)
pytest tests/smoke/test_multi_provider_live.py -v
```

### 4. Integration Tests

```bash
# Run integration tests
pytest tests/integration/ -m integration

# Test specific integrations
pytest tests/integration/test_audit_hooks.py
pytest tests/integration/test_pki_verification.py
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
> **Note**: Some commands below are examples for future functionality.

```bash
# Ensure you're in the right environment
# which python
pip list | grep ioa

# Reinstall if needed
pip uninstall ioa-core
pip install -e .
```

#### 2. Configuration Issues
> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Check configuration
# Example (not currently implemented): ioa config show

# Reset configuration
# rm -rf ~/.ioa
# Example (not currently implemented): ioa config init
```

#### 3. Provider Connection Issues
> **Note**: Some commands below are examples for future functionality.

```bash
# Test connectivity
# Example (not currently implemented): ioa onboard llm smoke --provider openai --live

# Check environment variables
# env | grep -i api

# Verify API keys are valid
# curl -H "Authorization: Bearer $OPENAI_API_KEY" \
#      https://api.openai.com/v1/models
```

#### 4. Permission Issues
```bash
# Check file permissions
ls -la ~/.ioa/

# Fix permissions if needed
chmod 700 ~/.ioa/
chmod 600 ~/.ioa/config/*
```

### Getting Help

- **Documentation**: [docs/]()
- **GitHub Issues**: [Report bugs](https://github.com/orchintel/ioa-core/issues)
- **Discussions**: [Community Q&A](https://github.com/orchintel/ioa-core/discussions)
- **Security**: [security@orchintel.com](mailto:security@orchintel.com)

## Next Steps

Now that you're set up, explore:

1. **[Tutorials](tutorials/)** - Step-by-step guides
2. **[CLI Reference](user-guide/cli-reference.md)** - Command reference
3. **[API Documentation](api/)** - Developer guides
4. **[Examples](examples/)** - Sample projects and configurations

## Advanced Configuration

### Custom Governance Policies

```yaml
# governance.yaml
policies:
  audit:
    enabled: true
    retention_days: 90
    redaction:
      - "api_key"
      - "email"
      - "phone"
  
  security:
    max_concurrent_tasks: 10
    require_trust_verification: true
```

### Performance Tuning

```yaml
# performance.yaml
memory:
  hot_storage_size: "1GB"
  cold_storage_size: "10GB"
  pruning_threshold: 0.8

execution:
  max_workers: 4
  task_timeout: 300
  retry_attempts: 3
```

---

*Happy orchestrating! 🚀*
