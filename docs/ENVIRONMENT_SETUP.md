# Environment Setup Guide

**Complete environment requirements and setup instructions**

---

## Supported Platforms

### Operating Systems

| OS | Minimum Version | Tested |
|----|-----------------|--------|
| **macOS** | 10.15 (Catalina) | ✅ 13.x (Ventura), 14.x (Sonoma) |
| **Linux** | Ubuntu 20.04, Debian 11 | ✅ Ubuntu 22.04, Fedora 38 |
| **Windows** | 10, 11 | ✅ Windows 11, WSL2 recommended |

### Python Versions

| Version | Status | Notes |
|---------|--------|-------|
| **3.10** | ✅ Supported | Minimum required |
| **3.11** | ✅ Recommended | Best performance |
| **3.12** | ✅ Supported | Latest features |
| **3.13** | ⚠️ Experimental | May work but not tested |
| **3.9 or lower** | ❌ Not supported | Too old |

---

## System Requirements

### Minimum
- **CPU**: 1 core
- **RAM**: 512 MB
- **Disk**: 100 MB (install only)
- **Python**: 3.10+
- **pip**: 21.0+

### Recommended
- **CPU**: 2+ cores
- **RAM**: 2 GB
- **Disk**: 500 MB (with examples/tests)
- **Python**: 3.11+
- **pip**: Latest

### For Ollama (Local Models)
- **CPU**: 4+ cores
- **RAM**: 8 GB minimum, 16 GB recommended
- **Disk**: 5-20 GB per model
- **GPU**: Optional but recommended for performance

---

## Installation

### macOS

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11
brew install python@3.11

# Install IOA Core
python3.11 -m venv ioa-env
source ioa-env/bin/activate
pip install ioa-core
```

### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Python 3.10+
sudo apt install python3.10 python3.10-venv python3.10-dev

# Install IOA Core
python3.10 -m venv ioa-env
source ioa-env/bin/activate
pip install ioa-core
```

### Windows

```powershell
# Download Python from https://www.python.org/downloads/
# Check "Add Python to PATH" during installation

# Create virtual environment
python -m venv ioa-env

# Activate (PowerShell)
ioa-env\Scripts\Activate.ps1

# Activate (Command Prompt)
ioa-env\Scripts\activate.bat

# Install IOA Core
pip install ioa-core
```

---

## Optional Dependencies

### For AWS S3 Storage
```bash
pip install boto3
```

### For Development
```bash
pip install ioa-core[dev]
# Includes: pytest, ruff, mypy, coverage
```

### For Documentation
```bash
pip install ioa-core[docs]
# Includes: mkdocs, mkdocs-material
```

---

## Disk Space Requirements

| Component | Size |
|-----------|------|
| IOA Core install | ~100 MB |
| Examples | ~10 MB |
| Tests | ~20 MB |
| Documentation | ~50 MB |
| Cache (working) | ~50-200 MB |
| **Total Recommended** | **500 MB** |

---

## Network Requirements

### Offline Mode (Default)
- ✅ No network required
- ✅ All examples work offline
- ✅ Mock providers

### Live Mode (Optional)
- Internet connection required
- Provider API endpoints:
  - OpenAI: https://api.openai.com
  - Anthropic: https://api.anthropic.com
  - Google: https://generativelanguage.googleapis.com
  - DeepSeek: https://api.deepseek.com
  - XAI: https://api.x.ai
  - Ollama: http://localhost:11434 (local)

---

## Troubleshooting

### Python Not Found
- **macOS**: Use `python3` instead of `python`
- **Linux**: Install `python3-venv` package
- **Windows**: Reinstall Python with "Add to PATH" checked

### Permission Errors
- Don't use `sudo` with pip in virtual environments
- On macOS/Linux: `chmod +x script.py` if needed

### SSL/Certificate Errors
```bash
pip install --upgrade pip certifi
```

### Windows-Specific Issues
- Use PowerShell or Command Prompt (not Git Bash)
- Consider WSL2 for better compatibility

---

## See Also

- **[Beginner Quick Start](QUICKSTART_BEGINNER.md)** - Step-by-step setup
- **[FAQ](FAQ.md)** - Common questions
- **[CONTRIBUTING](../CONTRIBUTING.md)** - Development setup

---

**Last Updated:** 2025-10-10
