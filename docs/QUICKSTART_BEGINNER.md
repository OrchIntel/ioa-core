# Beginner Quick Start Guide

**Complete step-by-step setup for Windows, macOS, and Linux**

---

## Prerequisites

- **Python 3.10 or higher** (3.10, 3.11, 3.12, or 3.13)
- **pip** (Python package installer)
- **500 MB disk space** (100 MB install + 200 MB examples/tests)
- **512 MB RAM minimum** (2 GB recommended)

---

## Step 1: Check Python Version

### macOS / Linux
```bash
python3 --version
```

### Windows
```cmd
python --version
```

**Expected Output**: `Python 3.10.x` or higher

### If Python is Not Installed

- **macOS**: `brew install python@3.10` (install Homebrew first: https://brew.sh)
- **Linux (Ubuntu/Debian)**: `sudo apt update && sudo apt install python3.10 python3.10-venv`
- **Windows**: Download from https://www.python.org/downloads/ (check "Add Python to PATH")

---

## Step 2: Create a Virtual Environment

### macOS / Linux
```bash
# Create virtual environment
python3 -m venv ioa-env

# Activate it
source ioa-env/bin/activate
```

### Windows
```cmd
# Create virtual environment
python -m venv ioa-env

# Activate it
ioa-env\Scripts\activate
```

**You'll see `(ioa-env)` in your terminal prompt when activated.**

---

## Step 3: Install IOA Core

### Option A: Install from PyPI (Recommended)
```bash
pip install ioa-core
```

### Option B: Install from Source (for Development)
```bash
# Clone repository
git clone https://github.com/orchintel/ioa-core.git
cd ioa-core

# Install in editable mode
pip install -e ".[dev]"
```

**Verify Installation**:
```bash
python -c "import ioa_core; print('IOA Core installed successfully!')"
```

---

## Step 4: Run Your First Example

### Bootstrap a Project
```bash
python examples/00_bootstrap/boot_project.py my-first-project
```

**Output**:
```
✅ Project scaffolded at ./my-first-project
   - my-first-project/ioa.yaml (configuration)
   - my-first-project/README.md (project docs)
```

### Run System Health Check
```bash
python examples/30_doctor/doctor_check.py
```

**Expected Output**:
```json
{
  "python_version_ok": true,
  "overall_health": "healthy"
}
```

### Run a Governed Workflow
```bash
python examples/10_workflows/run_workflow.py
```

**Output**: JSON with task, policy, evidence_id

### Try Multi-Agent Quorum
```bash
python examples/20_roundtable/roundtable_quorum.py "Analyze this code (ok)"
```

**Output**: JSON showing 3 votes and quorum status

---

## Step 5: Run Tests (Optional)

```bash
# Install pytest if not already installed
pip install pytest

# Run all tests
pytest -q

# Run just example tests (fast)
python tests/examples/test_workflow.py
python tests/examples/test_roundtable.py
python tests/examples/test_doctor.py
```

**All tests should pass** ✅

---

## Step 6: Explore Tutorials

- **[QUICKSTART.md](examples/QUICKSTART.md)** - Comprehensive quick start
- **[WORKFLOWS.md](examples/WORKFLOWS.md)** - Build governed workflows
- **[ROUNDTABLE.md](examples/ROUNDTABLE.md)** - Multi-agent consensus
- **[PROVIDERS.md](examples/PROVIDERS.md)** - Configure LLM providers

---

## Step 7: (Optional) Configure Live Providers

Examples run offline by default. For live testing with real LLMs:

### Get API Keys

1. **OpenAI**: https://platform.openai.com/api-keys
2. **Anthropic**: https://console.anthropic.com/
3. **Google**: https://makersuite.google.com/app/apikey

### Set Environment Variables

#### macOS / Linux
```bash
export OPENAI_API_KEY=your-key-here
export ANTHROPIC_API_KEY=your-key-here
```

#### Windows
```cmd
set OPENAI_API_KEY=your-key-here
set ANTHROPIC_API_KEY=your-key-here
```

### Run Live Test
```bash
IOA_LIVE=1 IOA_PROVIDER=openai python examples/40_providers/provider_smoketest.py
```

---

## Troubleshooting

### "Python not found" or "Command not found"

- **macOS/Linux**: Use `python3` instead of `python`
- **Windows**: Reinstall Python and check "Add Python to PATH"

### "No module named 'ioa_core'"

- Make sure virtual environment is activated: `(ioa-env)` in prompt
- Re-run: `pip install ioa-core`

### "Permission denied" (macOS/Linux)

- Don't use `sudo` with pip in a virtual environment
- Make sure you activated the venv first

### Examples fail with "File not found"

- Run examples from the repository root directory (`ioa-core/`)
- Example: `cd ioa-core && python examples/30_doctor/doctor_check.py`

### "SSL Certificate" errors

- Update pip: `pip install --upgrade pip`
- Update certifi: `pip install --upgrade certifi`

---

## Uninstalling

### Remove IOA Core
```bash
pip uninstall ioa-core
```

### Delete Virtual Environment
```bash
# Deactivate first
deactivate

# Remove directory
rm -rf ioa-env  # macOS/Linux
rmdir /s ioa-env  # Windows
```

---

## Next Steps

1. ✅ Read the [FAQ](FAQ.md) for common questions
2. ✅ Check the [Glossary](REFERENCE_GLOSSARY.md) for term definitions
3. ✅ Review [FEATURE_MATRIX.md](../FEATURE_MATRIX.md) for capabilities
4. ✅ Join discussions on [GitHub](https://github.com/orchintel/ioa-core/discussions)
5. ✅ Report bugs via [Issues](https://github.com/orchintel/ioa-core/issues)

---

## Platform-Specific Notes

### macOS
- Requires Xcode Command Line Tools: `xcode-select --install`
- Homebrew recommended for Python: `brew install python@3.10`

### Linux
- Ubuntu/Debian: `sudo apt install python3.10-venv python3.10-dev`
- Fedora/RHEL: `sudo dnf install python3.10 python3.10-devel`

### Windows
- Use PowerShell or Command Prompt (not Git Bash for pip)
- Windows Subsystem for Linux (WSL) also works great

---

**Got stuck?** Open an issue: https://github.com/orchintel/ioa-core/issues

**Last Updated:** 2025-10-10

