**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Live Smoke Testing Tutorial

This tutorial guides you through testing IOA Core with live LLM providers using real API keys.

## Prerequisites

- IOA Core installed and configured
- Valid API keys for at least one LLM provider
- Network access to provider APIs

## Quick Start (5 minutes)

### Step 1: Configure API Keys

Set your API keys as environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Google Gemini
export GOOGLE_API_KEY="AIza..."

# DeepSeek
export DEEPSEEK_API_KEY="sk-..."

# XAI/Grok
export XAI_API_KEY="xai-..."

# Ollama (local)
export OLLAMA_BASE_URL="http://localhost:11434"
```

### Step 2: Run Live Smoke Tests

> **Note**: Some commands below are examples for future functionality.

```bash
# Test all configured providers
# Example (not currently implemented): ioa onboard llm smoke --live

# Test specific provider
# Example (not currently implemented): ioa onboard llm smoke --provider openai --live

# Test with verbose output
# Example (not currently implemented): ioa onboard llm smoke --provider anthropic --live --verbose
```

### Step 3: Verify Results

> **Note**: Some commands below are examples for future functionality.

```bash
# Check test results
# Example (not currently implemented): ioa onboard llm list

# View detailed status
# Example (not currently implemented): ioa health --detailed
```

## Detailed Walkthrough

### 1. Provider Configuration

IOA Core supports multiple LLM providers. Each has specific configuration requirements:

#### OpenAI Configuration

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_ORGANIZATION="org-..."  # Optional
export OPENAI_BASE_URL="https://api.openai.com/v1"  # Optional, for custom endpoints
```

**Supported Models:**
- `gpt-4o-mini` (recommended for testing)
- `gpt-4o`
- `gpt-4-turbo`
- `gpt-3.5-turbo`

#### Anthropic Configuration

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export ANTHROPIC_BASE_URL="https://api.anthropic.com"  # Optional
```

**Supported Models:**
- `claude-3-haiku` (recommended for testing)
- `claude-3-sonnet`
- `claude-3-opus`

#### Google Gemini Configuration

```bash
export GOOGLE_API_KEY="AIza..."
export GOOGLE_BASE_URL="https://generativelanguage.googleapis.com"  # Optional
```

**Supported Models:**
- `gemini-1.5-flash` (recommended for testing)
- `gemini-1.5-pro`
- `gemini-1.0-pro`

#### DeepSeek Configuration

```bash
export DEEPSEEK_API_KEY="sk-..."
export DEEPSEEK_BASE_URL="https://api.deepseek.com"  # Optional
```

**Supported Models:**
- `deepseek-chat`
- `deepseek-coder`

#### XAI/Grok Configuration

```bash
export XAI_API_KEY="xai-..."
export XAI_BASE_URL="https://api.x.ai"  # Optional
```

**Supported Models:**
- `grok-beta`
- `grok-2`

#### Ollama Configuration (Local)

```bash
export OLLAMA_BASE_URL="http://localhost:11434"
# No API key required for local Ollama
```

**Supported Models:**
- Any model available in your local Ollama installation
- Common models: `llama3.2`, `mistral`, `codellama`

### 2. Running Live Tests

#### Test All Providers

> **Note**: Some commands below are examples for future functionality.

```bash
# Test all configured providers
# Example (not currently implemented): ioa onboard llm smoke --live

# Expected output:
# ✅ OpenAI: Connected successfully (gpt-4o-mini)
# ✅ Anthropic: Connected successfully (claude-3-haiku)
# ⚠️ Gemini: No API key configured
# ⚠️ DeepSeek: No API key configured
# ⚠️ XAI: No API key configured
# ⚠️ Ollama: Connection failed (service not running)
```

#### Test Specific Provider

> **Note**: Some commands below are examples for future functionality.

```bash
# Test OpenAI only
# Example (not currently implemented): ioa onboard llm smoke --provider openai --live

# Test with specific model
# Example (not currently implemented): ioa onboard llm smoke --provider openai --live --model gpt-4o

# Test with timeout
# Example (not currently implemented): ioa onboard llm smoke --provider openai --live --timeout 30
```

#### Verbose Testing

> **Note**: Some commands below are examples for future functionality.

```bash
# Get detailed test information
# Example (not currently implemented): ioa onboard llm smoke --provider anthropic --live --verbose

# Output includes:
# - API endpoint being tested
# - Request/response details
# - Performance metrics
# - Error details if any
```

### 3. Test Scenarios

#### Basic Connectivity Test

> **Note**: Some commands below are examples for future functionality.

```bash
# Simple connection test
# Example (not currently implemented): ioa onboard llm smoke --provider openai --live --test-type connectivity

# Tests:
# - API key validation
# - Network connectivity
# - Service availability
```

#### Model Availability Test

> **Note**: Some commands below are examples for future functionality.

```bash
# Test specific model
# Example (not currently implemented): ioa onboard llm smoke --provider openai --live --model gpt-4o

# Tests:
# - Model availability
# - Model permissions
# - Rate limits
```

#### Performance Test

> **Note**: Some commands below are examples for future functionality.

```bash
# Run performance benchmark
# Example (not currently implemented): ioa onboard llm smoke --provider openai --live --test-type performance

# Tests:
# - Response time
# - Throughput
# - Token usage
```

#### Zero-Retention Test

> **Note**: Some commands below are examples for future functionality.

```bash
# Test zero-retention flags
# Example (not currently implemented): ioa onboard llm smoke --provider openai --live --test-type zero-retention

# Tests:
# - Zero-retention flag support
# - Data handling compliance
```

### 4. Troubleshooting Live Tests

#### Common Issues

**1. "No API key configured"**

```bash
# Check environment variables
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Set missing keys
export OPENAI_API_KEY="sk-..."
```

**2. "Connection failed"**

> **Note**: Some commands below are examples for future functionality.

```bash
# Check network connectivity
# curl -I https://api.openai.com/v1/models

# Check firewall/proxy settings
# Verify API endpoint URLs
```

**3. "Rate limit exceeded"**

```bash
# Wait for rate limit reset
# Check provider dashboard for current usage
# Consider upgrading plan if needed
```

**4. "Model not available"**

> **Note**: Some commands below are examples for future functionality.

```bash
# Check model availability
# Example (not currently implemented): ioa onboard llm list --provider openai

# Use fallback model
# Example (not currently implemented): ioa onboard llm smoke --provider openai --live --model gpt-4o-mini
```

#### Debug Mode

> **Note**: Some commands below are examples for future functionality.

```bash
# Enable debug logging
export IOA_DEBUG=true
export IOA_LOG_LEVEL=DEBUG

# Run test with debug output
# Example (not currently implemented): ioa onboard llm smoke --provider openai --live --verbose
```

### 5. Test Results Analysis

#### Success Indicators

> **Note**: Some commands below are examples for future functionality.

```bash
# All tests passed
# ✅ OpenAI: Connected successfully (gpt-4o-mini)
# ✅ Anthropic: Connected successfully (claude-3-haiku)
# ✅ Gemini: Connected successfully (gemini-1.5-flash)

# Performance metrics
# Response Time: 1.2s (OpenAI), 0.8s (Anthropic), 1.5s (Gemini)
# Token Usage: 150 (OpenAI), 120 (Anthropic), 180 (Gemini)
```

#### Warning Indicators

> **Note**: Some commands below are examples for future functionality.

```bash
# Provider not configured
# ⚠️ DeepSeek: No API key configured

# Service unavailable
# ⚠️ Ollama: Connection failed (service not running)

# Rate limit approaching
# ⚠️ OpenAI: Rate limit at 80% (wait 15 minutes)
```

#### Error Indicators

> **Note**: Some commands below are examples for future functionality.

```bash
# Authentication failed
# ❌ OpenAI: Authentication failed (invalid API key)

# Network error
# ❌ Anthropic: Connection timeout (30s)

# Service error
# ❌ Gemini: Service unavailable (503)
```

### 6. Advanced Testing

#### Batch Testing

> **Note**: Some commands below are examples for future functionality.

```bash
# Test multiple providers in parallel
# Example (not currently implemented): ioa onboard llm smoke --live --parallel --timeout 60

# Test with custom test suite
# Example (not currently implemented): ioa onboard llm smoke --live --test-suite custom_tests.yaml
```

#### Load Testing

> **Note**: Some commands below are examples for future functionality.

```bash
# Run concurrent tests
# Example (not currently implemented): ioa onboard llm smoke --provider openai --live --concurrent 5 --iterations 10

# Monitor performance
# Example (not currently implemented): ioa onboard llm smoke --provider openai --live --monitor --duration 300
```

#### Integration Testing

> **Note**: Some commands below are examples for future functionality.

```bash
# Test with workflow execution
# Example (not currently implemented): ioa workflows run --file test_workflow.yaml --providers openai,anthropic

# Test with roundtable execution
# Example (not currently implemented): ioa roundtable execute --task "Test task" --agents agent1,agent2 --providers openai
```

### 7. Continuous Testing

#### Automated Testing

> **Note**: Some commands below are examples for future functionality.

```bash
# Run tests in CI/CD pipeline
# Example (not currently implemented): ioa onboard llm smoke --live --ci --output-format json

# Generate test report
# Example (not currently implemented): ioa onboard llm smoke --live --report --output-file smoke_report.json
```

#### Scheduled Testing

> **Note**: Some commands below are examples for future functionality.

```bash
# Set up cron job for regular testing
# 0 */6 * * * /usr/local/bin/ioa onboard llm smoke --live --report --output-file /var/log/ioa/smoke_$(date +\%Y\%m\%d_\%H\%M).json
```

#### Monitoring Integration

> **Note**: Some commands below are examples for future functionality.

```bash
# Send metrics to monitoring system
# Example (not currently implemented): ioa onboard llm smoke --live --metrics --endpoint http://monitoring:8080/metrics

# Alert on failures
# Example (not currently implemented): ioa onboard llm smoke --live --alert --webhook https://hooks.slack.com/...
```

## Best Practices

### 1. **API Key Management**
- Use environment variables, never hardcode keys
- Rotate keys regularly
- Use least-privilege access
- Monitor key usage

### 2. **Testing Strategy**
- Test during off-peak hours
- Use appropriate timeouts
- Monitor rate limits
- Test all supported models

### 3. **Error Handling**
- Implement retry logic
- Log all errors
- Set up alerts for failures
- Document common issues

### 4. **Performance Monitoring**
- Track response times
- Monitor token usage
- Set performance baselines
- Alert on degradation

## Example Test Scripts

### Basic Test Script

> **Note**: Some commands below are examples for future functionality.

```bash
#!/bin/bash
# test_providers.sh

# set -e

echo "Testing IOA Core LLM Providers..."

# Test OpenAI
# if [ -n "$OPENAI_API_KEY" ]; then
    echo "Testing OpenAI..."
# Example (not currently implemented):     ioa onboard llm smoke --provider openai --live --verbose
# else
    echo "⚠️ OpenAI API key not configured"
# fi

# Test Anthropic
# if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "Testing Anthropic..."
# Example (not currently implemented):     ioa onboard llm smoke --provider anthropic --live --verbose
# else
    echo "⚠️ Anthropic API key not configured"
# fi

echo "Provider testing completed"
```

### Advanced Test Script

> **Note**: Some commands below are examples for future functionality.

```bash
#!/bin/bash
# advanced_smoke_test.sh

# set -e

# PROVIDERS=("openai" "anthropic" "gemini" "deepseek" "xai")
# RESULTS_DIR="./test_results/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo "Starting advanced smoke testing..."

# for provider in "${PROVIDERS[@]}"; do
    echo "Testing $provider..."
    
    # Check if provider is configured
#     if ioa onboard llm list --provider "$provider" | grep -q "configured"; then
        # Run live test
#         if ioa onboard llm smoke --provider "$provider" --live --verbose --timeout 60; then
            echo "✅ $provider: Test passed"
            echo "PASS" > "$RESULTS_DIR/${provider}_result.txt"
#         else
            echo "❌ $provider: Test failed"
            echo "FAIL" > "$RESULTS_DIR/${provider}_result.txt"
#         fi
#     else
        echo "⚠️ $provider: Not configured"
        echo "SKIP" > "$RESULTS_DIR/${provider}_result.txt"
#     fi
# done

# Generate summary report
echo "Generating test summary..."
echo "Test Results Summary - $(date)" > "$RESULTS_DIR/summary.txt"
echo "================================" >> "$RESULTS_DIR/summary.txt"

# for provider in "${PROVIDERS[@]}"; do
#     if [ -f "$RESULTS_DIR/${provider}_result.txt" ]; then
#         result=$(cat "$RESULTS_DIR/${provider}_result.txt")
        echo "$provider: $result" >> "$RESULTS_DIR/summary.txt"
#     fi
# done

echo "Advanced smoke testing completed. Results saved to $RESULTS_DIR"
```

## Next Steps

After completing live smoke tests:

1. **Review Results**: Analyze test outcomes and performance metrics
2. **Fix Issues**: Address any failures or warnings
3. **Optimize Configuration**: Tune provider settings for best performance
4. **Set Up Monitoring**: Implement continuous testing and alerting
5. **Document Findings**: Record provider-specific behaviors and limitations

## Related Documentation

- [CLI Reference](../user-guide/cli-reference.md)
- [Configuration Guide](../user-guide/configuration.md)
- [Troubleshooting Guide](../user-guide/troubleshooting.md)
- [Provider API](../api/providers.md)

---

*For more information about specific providers, see the [Provider Configuration](../user-guide/configuration.md#llm-provider-configuration) section*
