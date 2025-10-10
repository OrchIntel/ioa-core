**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# EC2 100k Performance Test Tutorial


## Overview

This tutorial guides you through setting up and running the IOA Core 100k performance tests on AWS EC2. These tests validate system performance under high-load conditions and are essential for release validation.

## Prerequisites

- AWS account with EC2 access
- AWS CLI configured with appropriate permissions
- SSH key pair for EC2 access
- IOA Core v2.5.0 source code
- Basic familiarity with AWS services

## EC2 Instance Setup

### 1. Launch EC2 Instance

Launch an EC2 instance with the following specifications:

> **Note**: Some commands below are examples for future functionality.

```bash
# Recommended instance type for 100k tests
# Instance Type: c5.2xlarge or c5.4xlarge
# OS: Ubuntu 22.04 LTS
# Storage: 20GB GP3 SSD
# Security Group: Allow SSH (port 22) from your IP
```

### 2. Configure Security Groups

Create or modify security groups to allow:
- SSH access (port 22) from your IP
- HTTP/HTTPS (ports 80/443) for package downloads
- Custom ports if needed for specific services

### 3. Connect to Instance

> **Note**: Some commands below are examples for future functionality.

```bash
# Connect via SSH
# ssh -i your-key.pem ubuntu@your-instance-ip

# Verify connection
# whoami
pwd
```

## Environment Setup

### 1. Update System Packages

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Update package lists
# sudo apt update

# Upgrade existing packages
# sudo apt upgrade -y

# Install essential packages
# sudo apt install -y python3 python3-pip python3-venv git curl wget
```

### 2. Install Python Dependencies

> **Note**: Some commands below are examples for future functionality.

```bash
# Create virtual environment
python3 -m venv ioa-env

# Activate virtual environment
# source ioa-env/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install IOA Core dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Clone IOA Core Repository

```bash
# Clone the repository
git clone https://github.com/your-org/ioa-core.git
cd ioa-core

# Checkout the specific version
git checkout v2.5.0

# Verify installation
python -m pytest --version
```

## Performance Test Configuration

### 1. Environment Variables

Set the required environment variables:

```bash
# Set non-interactive mode for CI
export IOA_NON_INTERACTIVE=1

# Set performance test parameters
export IOA_100K_N=100000
export IOA_REPORT_SUITE=pytest
export PYTHONWARNINGS=error

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### 2. Test Configuration

Create a test configuration file:

> **Note**: Some commands below are examples for future functionality.

```bash
# Create test config
cat > test_config.yaml << EOF
# performance:
#   iterations: 100000
#   batch_size: 1000
#   timeout_seconds: 300
#   memory_limit_mb: 2048
  
# monitoring:
#   enable_metrics: true
#   log_level: INFO
#   save_results: true
  
# output:
#   results_dir: ./results
#   report_format: json
#   include_timestamps: true
# EOF
```

## Running the 100k Tests

### 1. Smoke Tests

Start with basic smoke tests to verify the environment:

```bash
# Run smoke tests
python -m pytest tests/smoke/ -v

# Expected output: All tests should pass
# 15 passed, 13 skipped in 0.34s
```

### 2. Integration Tests

Run integration tests to verify system components:

```bash
# Run integration tests
python -m pytest tests/integration/ -v

# Expected output: All tests should pass
# 29 passed in 5.37s
```

### 3. Performance Tests

Run the 100k performance tests:

> **Note**: Some commands below are examples for future functionality.

```bash
# Run performance tests
python -m pytest tests/performance/test_100k.py -v

# Monitor system resources
# htop
```

### 4. Full Test Suite

Run the complete test suite for comprehensive validation:

```bash
# Run full test suite
python -m pytest tests/ -v --tb=short

# Expected output: All tests should pass
# 548 passed, 13 skipped, 15 deselected in 39.65s
```

## Monitoring and Optimization

### 1. System Monitoring

Monitor system resources during tests:

> **Note**: Some commands below are examples for future functionality.

```bash
# Monitor CPU and memory
# htop

# Monitor disk I/O
# iotop

# Monitor network
# iftop

# Monitor system load
# uptime
```

### 2. Performance Optimization

Optimize system performance:

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Set CPU governor to performance
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Disable swap for better performance
# sudo swapoff -a

# Set process priority
# sudo nice -n -20 python -m pytest tests/performance/
```

### 3. Memory Management

Optimize memory usage:

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Check memory usage
# free -h

# Clear page cache if needed
# sudo sync && sudo echo 3 | sudo tee /proc/sys/vm/drop_caches

# Monitor memory during tests
# watch -n 1 'free -h'
```

## Results Collection

### 1. Test Results

Collect test results and reports:

> **Note**: Some commands below are examples for future functionality.

```bash
# Create results directory
mkdir -p results/$(date +%Y%m%d_%H%M%S)

# Run tests with results output
python -m pytest tests/performance/ --junitxml=results/results.xml --html=results/report.html

# Copy results to local machine
# scp -i your-key.pem -r ubuntu@your-instance-ip:~/ioa-core/results/ ./local-results/
```

### 2. Performance Metrics

Extract key performance metrics:

```bash
# Extract test execution time
grep "test session starts" results/report.html

# Extract memory usage
grep "memory" results/report.html

# Extract CPU usage
grep "cpu" results/report.html
```

### 3. Generate Reports

Create comprehensive performance reports:

```bash
# Generate performance summary
python scripts/generate_performance_report.py results/

# Create visualization charts
python scripts/create_performance_charts.py results/
```

## Troubleshooting

### Common Issues

1. **Memory Exhaustion**
> **Note**: Some commands below are examples for future functionality.

   ```bash
   # Check available memory
#    free -h
   
   # Reduce batch size in test config
   # Increase swap space if needed
```

2. **Timeout Errors**
   ```bash
   # Increase timeout in test config
   # Check network connectivity
   # Verify API rate limits
```

3. **Permission Errors**
   ```bash
   # Check file permissions
   ls -la
   
   # Fix permissions
   chmod 755 tests/
   chmod 644 *.py
```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Set debug logging
export IOA_LOG_LEVEL=DEBUG

# Run tests with verbose output
python -m pytest tests/performance/ -v -s --tb=long
```

## Cleanup

### 1. Terminate EC2 Instance

> **Note**: Some commands below are examples for future functionality.

```bash
# Stop the instance
# aws ec2 stop-instances --instance-ids i-1234567890abcdef0

# Terminate the instance
# aws ec2 terminate-instances --instance-ids i-1234567890abcdef0
```

### 2. Clean Up Resources

> **Note**: Some commands below are examples for future functionality.

```bash
# Remove security groups
# aws ec2 delete-security-group --group-id sg-1234567890abcdef0

# Remove key pair
# aws ec2 delete-key-pair --key-name your-key-name
```

## Best Practices

### 1. Instance Selection

- Use compute-optimized instances (c5, c6i) for CPU-intensive tests
- Use memory-optimized instances (r5, r6i) for memory-intensive tests
- Consider spot instances for cost optimization

### 2. Test Execution

- Run tests during off-peak hours for consistent performance
- Use dedicated instances for performance testing
- Monitor and log all system metrics during tests

### 3. Result Analysis

- Compare results across multiple runs
- Document system configuration and environment
- Share results with the development team

## Related Documentation

- [Configuration Guide](../user-guide/configuration.md) - System configuration options
- [Performance Guide](../PERFORMANCE.md) - Performance optimization tips
- [Troubleshooting](../user-guide/troubleshooting.md) - Common issues and solutions
- [Getting Started](../getting-started/quickstart.md) - Quick start guide
