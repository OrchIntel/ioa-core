**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Installation Guide

This guide will walk you through installing IOA Core on your system.

## Prerequisites

Before installing IOA Core, ensure you have:

- **Python 3.9 or newer** installed
- **pip** (Python package installer) available
- **Git** (for source installation)
- **4GB RAM minimum** (8GB recommended)
- **2GB free disk space**

### Check Your System

> **Note**: Some commands below are examples for future functionality.

```bash
# Check Python version
python3 --version

# Check pip
pip3 --version

# Check Git
git --version

# Check available memory (Linux/macOS)
# free -h  # Linux
# vm_stat   # macOS

# Check disk space
# df -h
```

## Installation Methods

### Method 1: Install from Source (Recommended for Development)

This method gives you the latest development version and allows you to contribute to the project.

> **Note**: Some commands below are examples for future functionality.

```bash
# Clone the repository
git clone https://github.com/orchintel/ioa-core.git
cd ioa-core

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# source venv/bin/activate  # Linux/macOS
# or
# venv\Scripts\activate     # Windows

# Install in development mode
pip install -e ".[dev]"
```

**Benefits:**
- Latest features and bug fixes
- Ability to modify source code
- Development tools included
- Easy to update with `git pull`

### Method 2: Install from PyPI (Production)

This method installs the latest stable release from the Python Package Index.

> **Note**: Some commands below are examples for future functionality.

```bash
# Create virtual environment
python3 -m venv ioa-env
# source ioa-env/bin/activate

# Install from PyPI
pip install ioa-core
```

**Benefits:**
- Stable, tested releases
- Automatic dependency management
- Easy to install and update
- Production-ready

### Method 3: Use the Setup Script

IOA Core provides an automated setup script for quick installation.

> **Note**: Some commands below are examples for future functionality.

```bash
# Clone the repository
git clone https://github.com/orchintel/ioa-core.git
cd ioa-core

# Run the setup script
chmod +x scripts/dev_local_setup.sh
# ./scripts/dev_local_setup.sh
```

**Benefits:**
- Automated setup process
- Creates development environment
- Installs all dependencies
- Sets up configuration

## Platform-Specific Instructions

### Linux (Ubuntu/Debian)

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Update package list
# sudo apt update

# Install system dependencies
# sudo apt install python3 python3-pip python3-venv git

# Install IOA Core
git clone https://github.com/orchintel/ioa-core.git
cd ioa-core
python3 -m venv venv
# source venv/bin/activate
pip install -e ".[dev]"
```

### Linux (CentOS/RHEL/Fedora)

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Install system dependencies
# sudo dnf install python3 python3-pip python3-venv git  # Fedora
# or
# sudo yum install python3 python3-pip python3-venv git  # CentOS/RHEL

# Install IOA Core
git clone https://github.com/orchintel/ioa-core.git
cd ioa-core
python3 -m venv venv
# source venv/bin/activate
pip install -e ".[dev]"
```

### macOS

> **Note**: Some commands below are examples for future functionality.

```bash
# Install Homebrew (if not already installed)
# /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python and Git
# brew install python git

# Install IOA Core
git clone https://github.com/orchintel/ioa-core.git
cd ioa-core
python3 -m venv venv
# source venv/bin/activate
pip install -e ".[dev]"
```

### Windows

#### Using WSL (Recommended)

> **Note**: Some commands below are examples for future functionality.

```bash
# Install WSL2
# wsl --install

# Restart and open WSL terminal
# Follow Linux instructions above
```

#### Using Windows Native

> **Note**: Some commands below are examples for future functionality.

```bash
# Install Python from https://python.org
# Install Git from https://git-scm.com

# Open Command Prompt or PowerShell
git clone https://github.com/orchintel/ioa-core.git
cd ioa-core

# Create virtual environment
python -m venv venv

# Activate virtual environment
# venv\Scripts\activate

# Install IOA Core
pip install -e ".[dev]"
```

## Docker Installation

If you prefer using Docker:

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

# Run with volume mount for persistence
# docker run -it --rm \
#   -v $(pwd):/app \
#   -w /app \
#   orchintel/ioa-core:latest
```

## Verification

After installation, verify that IOA Core is working correctly:

> **Note**: Some commands below are examples for future functionality.

```bash
# Check version
# Example (not currently implemented): ioa --version

# Check installation
# Example (not currently implemented): ioa health

# Run basic tests
pytest tests/smoke/ -m smoke --offline
```

Expected output:
```
IOA Core v2.5.0
✅ System health check passed
🧪 5 tests passed, 0 failed
```

## Configuration

### Initial Setup

> **Note**: Some commands below are examples for future functionality.

```bash
# Initialize configuration
# Example (not currently implemented): ioa config init

# Show current configuration
# Example (not currently implemented): ioa config show

# Set basic configuration
# Example (not currently implemented): ioa config set environment development
# Example (not currently implemented): ioa config set log_level INFO
```

### LLM Provider Setup

> **Note**: Some commands below are examples for future functionality.

```bash
# Interactive setup
# Example (not currently implemented): ioa onboard setup

# Or set environment variables
export OPENAI_API_KEY="sk-your-api-key"
export ANTHROPIC_API_KEY="sk-ant-your-api-key"
```

## Troubleshooting

### Common Installation Issues

#### 1. Python Version Too Old

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Error: "Python 3.9+ required"
python3 --version

# Solution: Install newer Python version
# Ubuntu/Debian
# sudo apt install python3.9 python3.9-venv python3.9-pip

# macOS
# brew install python@3.9

# Windows: Download from python.org
```

#### 2. Permission Denied

> **Note**: Some commands below are examples for future functionality.

```bash
# Error: "Permission denied"
# Solution: Use virtual environment
python3 -m venv venv
# source venv/bin/activate
pip install ioa-core
```

#### 3. Missing Dependencies

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Error: "Module not found"
# Solution: Install system dependencies
# sudo apt install python3-dev build-essential  # Ubuntu/Debian
# sudo dnf install python3-devel gcc           # Fedora/CentOS
# brew install python3                         # macOS
```

#### 4. Virtual Environment Issues

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Error: "venv module not found"
# Solution: Install venv module
# sudo apt install python3-venv  # Ubuntu/Debian
# sudo dnf install python3-venv  # Fedora/CentOS
```

### Getting Help

If you encounter issues:

1. **Check the logs:**
> **Note**: Some commands below are examples for future functionality.

   ```bash
# Example (not currently implemented):    ioa health --detailed
```

2. **Verify installation:**
> **Note**: Some commands below are examples for future functionality.

   ```bash
   pip list | grep ioa
#    which ioa
```

3. **Check system resources:**
> **Note**: Some commands below are examples for future functionality.

   ```bash
#    free -h      # Memory
#    df -h        # Disk space
#    nproc        # CPU cores
```

4. **Community support:**
   - [GitHub Issues](https://github.com/orchintel/ioa-core/issues)
   - [Discussions](https://github.com/orchintel/ioa-core/discussions)

## Next Steps

After successful installation:

1. **[Quickstart Guide](quickstart.md)** - Get up and running in minutes
2. **[Configuration Guide](configuration.md)** - Customize your setup
3. **[Hello World Tutorial](../tutorials/hello-world.md)** - Create your first workflow
4. **[CLI Reference](../user-guide/cli-reference.md)** - Learn all commands

## Updating IOA Core

### Source Installation

```bash
# Navigate to project directory
cd ioa-core

# Pull latest changes
git pull origin main

# Reinstall
pip install -e ".[dev]"
```

### PyPI Installation

> **Note**: Some commands below are examples for future functionality.

```bash
# Update to latest version
pip install --upgrade ioa-core

# Check version
# Example (not currently implemented): ioa --version
```

### Docker Installation

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Pull latest image
# docker pull orchintel/ioa-core:latest

# Remove old container (if running)
# docker stop <container-id>
# docker rm <container-id>

# Run new container
# docker run -it --rm orchintel/ioa-core:latest
```

---

*Need help? Check the [FAQ](../user-guide/FAQ_IOA_CORE.md) or [Community Support](https://github.com/orchintel/ioa-core/discussions)*
