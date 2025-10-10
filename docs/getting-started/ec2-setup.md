**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# EC2 Setup Guide

This guide covers setting up IOA Core on Amazon EC2 for production deployment and performance testing.

## Prerequisites

- AWS account with EC2 access
- Basic familiarity with AWS services
- SSH client (Terminal, PuTTY, etc.)

## Quick Start (15 minutes)

### 1. Launch EC2 Instance

> **Note**: Some commands below are examples for future functionality.

```bash
# Using AWS CLI
# aws ec2 run-instances \
#     --image-id ami-0c02fb55956c7d316 \
#     --instance-type t3.medium \
#     --key-name your-key-pair \
#     --security-group-ids sg-12345678 \
#     --subnet-id subnet-12345678 \
#     --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ioa-core-server}]'
```

### 2. Connect to Instance

> **Note**: Some commands below are examples for future functionality.

```bash
# SSH connection
# ssh -i your-key.pem ubuntu@your-instance-ip

# Verify connection
# whoami
pwd
```

### 3. Install IOA Core

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Update system
# sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
# sudo apt install -y python3 python3-pip python3-venv git

# Clone repository
git clone https://github.com/orchintel/ioa-core.git
cd ioa-core

# Create virtual environment
python3 -m venv venv
# source venv/bin/activate

# Install IOA Core
pip install -e ".[dev]"
```

## Detailed Setup

### Instance Selection

#### Recommended Instance Types

| Use Case | Instance Type | vCPU | Memory | Storage | Cost/Hour |
|----------|---------------|------|--------|---------|-----------|
| **Development** | t3.micro | 2 | 1 GB | EBS | ~$0.0104 |
| **Testing** | t3.small | 2 | 2 GB | EBS | ~$0.0208 |
| **Performance** | t3.medium | 2 | 4 GB | EBS | ~$0.0416 |
| **Production** | t3.large | 2 | 8 GB | EBS | ~$0.0832 |
| **High Performance** | c5.large | 2 | 4 GB | EBS | ~$0.085 |

#### Instance Configuration

> **Note**: Some commands below are examples for future functionality.

```bash
# Check instance specifications
# curl -s http://169.254.169.254/latest/meta-data/instance-type
# curl -s http://169.254.169.254/latest/meta-data/instance-id

# Check available resources
# free -h
# df -h
# nproc
```

### Security Configuration

#### Security Groups

> **Note**: Some commands below are examples for future functionality.

```bash
# Create security group
# aws ec2 create-security-group \
#     --group-name ioa-core-sg \
#     --description "Security group for IOA Core"

# Add SSH access
# aws ec2 authorize-security-group-ingress \
#     --group-name ioa-core-sg \
#     --protocol tcp \
#     --port 22 \
#     --cidr 0.0.0.0/0

# Add HTTP/HTTPS if needed
# aws ec2 authorize-security-group-ingress \
#     --group-name ioa-core-sg \
#     --protocol tcp \
#     --port 80 \
#     --cidr 0.0.0.0/0

# aws ec2 authorize-security-group-ingress \
#     --group-name ioa-core-sg \
#     --protocol tcp \
#     --port 443 \
#     --cidr 0.0.0.0/0
```

#### Key Pair Management

> **Note**: Some commands below are examples for future functionality.

```bash
# Generate new key pair
# aws ec2 create-key-pair \
#     --key-name ioa-core-key \
#     --query 'KeyMaterial' \
#     --output text > ioa-core-key.pem

# Set permissions
chmod 400 ioa-core-key.pem

# Connect using new key
# ssh -i ioa-core-key.pem ubuntu@your-instance-ip
```

### System Configuration

#### Operating System Setup

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Update system packages
# sudo apt update
# sudo apt upgrade -y

# Install essential packages
# sudo apt install -y \
#     build-essential \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
#     curl \
#     wget \
#     unzip \
#     htop \
#     tree \
#     vim \
#     nano

# Install additional dependencies
# sudo apt install -y \
#     libssl-dev \
#     libffi-dev \
#     libpq-dev \
#     libxml2-dev \
#     libxslt1-dev \
#     libjpeg-dev \
#     libpng-dev \
#     libfreetype6-dev
```

#### Python Environment

> **Note**: Some commands below are examples for future functionality.

```bash
# Check Python version
python3 --version
pip3 --version

# Create virtual environment
python3 -m venv ~/ioa-venv
# source ~/ioa-venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install development tools
pip install \
    pytest \
    pytest-cov \
#     black \
#     isort \
#     flake8 \
#     mypy \
#     bandit
```

### IOA Core Installation

#### Source Installation

> **Note**: Some commands below are examples for future functionality.

```bash
# Clone repository
git clone https://github.com/orchintel/ioa-core.git
cd ioa-core

# Check out specific version
git checkout v2.5.0

# Install in development mode
pip install -e ".[dev]"

# Verify installation
# Example (not currently implemented): ioa --version
# Example (not currently implemented): ioa health
```

#### Configuration Setup

> **Note**: Some commands below are examples for future functionality.

```bash
# Create configuration directory
mkdir -p ~/.ioa/config

# Create base configuration
cat > ~/.ioa/config/ioa.yaml << 'EOF'
# core:
#   environment: production
#   debug: false
#   log_level: INFO
#   log_path: "./logs/"

# storage:
#   type: "file"
#   base_path: "./data/"
#   max_size_mb: 10240

# governance:
#   audit_enabled: true
#   audit_log_path: "./logs/audit/"
#   pki_enabled: true
#   compliance_enabled: true
# EOF

# Set environment variables
echo 'export IOA_CONFIG_PATH="$HOME/.ioa/config"' >> ~/.bashrc
echo 'export IOA_LOG_PATH="$HOME/ioa-core/logs"' >> ~/.bashrc
echo 'export IOA_DATA_PATH="$HOME/ioa-core/data"' >> ~/.bashrc

# Reload shell
# source ~/.bashrc
```

### Performance Optimization

#### System Tuning

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Check current limits
# ulimit -a

# Set higher limits for file descriptors
echo '* soft nofile 65536' | sudo tee -a /etc/security/limits.conf
echo '* hard nofile 65536' | sudo tee -a /etc/security/limits.conf

# Optimize memory settings
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.dirty_ratio=15' | sudo tee -a /etc/sysctl.conf
echo 'vm.dirty_background_ratio=5' | sudo tee -a /etc/sysctl.conf

# Apply changes
# sudo sysctl -p
```

#### Python Optimization

> **Note**: Some commands below are examples for future functionality.

```bash
# Install performance packages
pip install \
#     uvloop \
#     orjson \
#     ujson \
#     cchardet \
#     aiodns

# Set environment variables for optimization
echo 'export PYTHONOPTIMIZE=2' >> ~/.bashrc
echo 'export PYTHONUNBUFFERED=1' >> ~/.bashrc
echo 'export PYTHONDONTWRITEBYTECODE=1' >> ~/.bashrc

# Reload shell
# source ~/.bashrc
```

## Testing and Validation

### Basic Functionality Test

> **Note**: Some commands below are examples for future functionality.

```bash
# Test IOA Core installation
# Example (not currently implemented): ioa --version
# Example (not currently implemented): ioa health --detailed

# Test configuration
# Example (not currently implemented): ioa config show
# Example (not currently implemented): ioa config validate

# Test basic commands
# Example (not currently implemented): ioa onboard llm list
# Example (not currently implemented): ioa governance audit status
```

### Performance Testing

#### 100k Test Harness

> **Note**: Some commands below are examples for future functionality.

```bash
# Run 100k performance test
cd ~/ioa-core
# ./scripts/ec2_100k_gate.sh

# Expected results:
# - Runtime: ~16.7 seconds
# - Success ratio: >=0.95
# - Memory usage: <2GB
# - CPU usage: <80%
```

#### Load Testing

> **Note**: Some commands below are examples for future functionality.

```bash
# Install load testing tools
pip install locust

# Create load test script
cat > load_test.py << 'EOF'
# from locust import HttpUser, task, between

# class IOACoreUser(HttpUser):
#     wait_time = between(1, 3)
    
#     @task
#     def health_check(self):
#         self.client.get("/health")
    
#     @task
#     def workflow_execution(self):
#         self.client.post("/workflows/execute", json={
#             "workflow": "test_workflow",
#             "parameters": {"test": "data"}
#         })
# EOF

# Run load test
# locust -f load_test.py --host=http://localhost:8000
```

### Monitoring and Logging

#### System Monitoring

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Install monitoring tools
# sudo apt install -y htop iotop nethogs

# Monitor system resources
# htop
# iotop
# nethogs

# Check IOA Core logs
# tail -f ~/ioa-core/logs/ioa.log
# tail -f ~/ioa-core/logs/audit/audit.log
```

#### Performance Metrics

> **Note**: Some commands below are examples for future functionality.

```bash
# Check system performance
# vmstat 1 10
# iostat 1 10
# netstat -i

# Monitor IOA Core metrics
# Example (not currently implemented): ioa health --detailed --timeout 60
# Example (not currently implemented): ioa governance audit summary --time-range "1h"
```

## Production Deployment

### Service Configuration

#### Systemd Service

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Create systemd service file
# sudo tee /etc/systemd/system/ioa-core.service << 'EOF'
# [Unit]
# Description=IOA Core Service
# After=network.target

# [Service]
# Type=simple
# User=ubuntu
# WorkingDirectory=/home/ubuntu/ioa-core
# Environment=PATH=/home/ubuntu/ioa-venv/bin
# ExecStart=/home/ubuntu/ioa-venv/bin/ioa start
# Restart=always
# RestartSec=10

# [Install]
# WantedBy=multi-user.target
# EOF

# Enable and start service
# sudo systemctl daemon-reload
# sudo systemctl enable ioa-core
# sudo systemctl start ioa-core

# Check service status
# sudo systemctl status ioa-core
```

#### Nginx Configuration (if needed)

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Install Nginx
# sudo apt install -y nginx

# Create Nginx configuration
# sudo tee /etc/nginx/sites-available/ioa-core << 'EOF'
# server {
#     listen 80;
#     server_name your-domain.com;

#     location / {
#         proxy_pass http://127.0.0.1:8000;
#         proxy_set_header Host $host;
#         proxy_set_header X-Real-IP $remote_addr;
#         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#         proxy_set_header X-Forwarded-Proto $scheme;
#     }
# }
# EOF

# Enable site
# sudo ln -s /etc/nginx/sites-available/ioa-core /etc/nginx/sites-enabled/
# sudo nginx -t
# sudo systemctl restart nginx
```

### Backup and Recovery

#### Data Backup

> **Note**: Some commands below are examples for future functionality.

```bash
# Create backup script
cat > backup_ioa.sh << 'EOF'
#!/bin/bash
# BACKUP_DIR="/home/ubuntu/backups/ioa-core"
# DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup configuration
# tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" -C ~/.ioa config/

# Backup data
# tar -czf "$BACKUP_DIR/data_$DATE.tar.gz" -C ~/ioa-core data/

# Backup logs
# tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" -C ~/ioa-core logs/

# Clean old backups (keep last 7 days)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR"
# EOF

chmod +x backup_ioa.sh

# Add to crontab
# (crontab -l 2>/dev/null; echo "0 2 * * * /home/ubuntu/backup_ioa.sh") | crontab -
```

#### Recovery Procedures

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Restore configuration
# tar -xzf config_20250819_143000.tar.gz -C ~/.ioa/

# Restore data
# tar -xzf data_20250819_143000.tar.gz -C ~/ioa-core/

# Restart service
# sudo systemctl restart ioa-core
```

## Troubleshooting

### Common Issues

#### Connection Problems

> **Note**: Some commands below are examples for future functionality.

```bash
# Check instance status
# aws ec2 describe-instances --instance-ids i-1234567890abcdef0

# Check security group rules
# aws ec2 describe-security-groups --group-names ioa-core-sg

# Test connectivity
# telnet your-instance-ip 22
```

#### Performance Issues

> **Note**: Some commands below are examples for future functionality.

```bash
# Check system resources
# free -h
# df -h
# iostat -x 1 5

# Check IOA Core logs
# tail -f ~/ioa-core/logs/ioa.log | grep ERROR

# Check system limits
# ulimit -a
cat /proc/sys/vm/swappiness
```

#### Service Issues

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Check service status
# sudo systemctl status ioa-core

# Check service logs
# sudo journalctl -u ioa-core -f

# Restart service
# sudo systemctl restart ioa-core
```

### Debug Mode

> **Note**: Some commands below are examples for future functionality.

```bash
# Enable debug logging
export IOA_DEBUG=true
export IOA_LOG_LEVEL=DEBUG

# Run with verbose output
# Example (not currently implemented): ioa health --detailed --verbose

# Check debug logs
# tail -f ~/ioa-core/logs/debug.log
```

## Cost Optimization

### Instance Scheduling

> **Note**: Some commands below are examples for future functionality.

```bash
# Create start/stop script
cat > schedule_instances.sh << 'EOF'
#!/bin/bash

# Start instances during business hours
# aws ec2 start-instances --instance-ids i-1234567890abcdef0

# Stop instances after hours
# aws ec2 stop-instances --instance-ids i-1234567890abcdef0
# EOF

# Add to crontab for automation
# Start at 8 AM UTC
# (crontab -l 2>/dev/null; echo "0 8 * * 1-5 /home/ubuntu/schedule_instances.sh start") | crontab -

# Stop at 6 PM UTC
# (crontab -l 2>/dev/null; echo "0 18 * * 1-5 /home/ubuntu/schedule_instances.sh stop") | crontab -
```

### Resource Monitoring

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Install CloudWatch agent
# sudo apt install -y amazon-cloudwatch-agent

# Configure CloudWatch
# sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard

# Start CloudWatch agent
# sudo systemctl start amazon-cloudwatch-agent
# sudo systemctl enable amazon-cloudwatch-agent
```

## Next Steps

1. **Performance Tuning**: Optimize based on your workload
2. **Monitoring Setup**: Implement comprehensive monitoring
3. **Backup Strategy**: Set up automated backup procedures
4. **Security Hardening**: Implement additional security measures
5. **Scaling**: Plan for horizontal scaling if needed

## Related Documentation

- [Installation Guide](installation.md)
- [Quickstart Guide](quickstart.md)
- [Performance Testing](../tutorials/ec2-100k-gate.md)
- [Configuration Guide](../user-guide/configuration.md)

---

*For production deployments, consider using AWS ECS, EKS, or other managed services for better scalability and management*
