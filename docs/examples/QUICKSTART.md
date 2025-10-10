# Quick Start Guide

Get up and running with IOA Core in minutes.

## Prerequisites

- Python 3.10 or higher
- pip or poetry
- (Optional) LLM provider API keys for live testing

## Installation

```bash
# Install from PyPI
pip install ioa-core

# Or install from source
git clone https://github.com/orchintel/ioa-core.git
cd ioa-core
pip install -e ".[dev]"
```

## System Health Check

Verify your environment:

```bash
python examples/30_doctor/doctor_check.py
```

Expected output:
```json
{
  "python_version_ok": true,
  "python_version": "3.10.0",
  "overall_health": "healthy"
}
```

## Bootstrap a Project

Create a new IOA project:

```bash
python examples/00_bootstrap/boot_project.py my-ai-system
```

This creates:
- `my-ai-system/ioa.yaml` - Configuration
- `my-ai-system/README.md` - Project docs

## Run Your First Workflow

Execute a governed workflow:

```bash
python examples/10_workflows/run_workflow.py
```

Output shows:
- Task executed
- Governance policy applied
- Audit evidence ID
- System Laws enforced

## Test Provider Connectivity

Check provider status:

```bash
# Mock provider (no API key needed)
IOA_PROVIDER=mock python examples/40_providers/provider_smoketest.py

# Real provider (requires API key)
IOA_LIVE=1 IOA_PROVIDER=openai python examples/40_providers/provider_smoketest.py
```

## Multi-Agent Quorum

Run vendor-neutral roundtable:

```bash
python examples/20_roundtable/roundtable_quorum.py "Analyze this code (ok)"
```

Demonstrates:
- 3-agent quorum voting
- 2-of-3 approval threshold
- Vendor-neutral consensus

## Next Steps

- [Workflows Guide](WORKFLOWS.md) - Build governed workflows
- [Roundtable Guide](ROUNDTABLE.md) - Multi-agent consensus
- [Provider Setup](PROVIDERS.md) - Configure LLM providers
- [Ollama Turbo](OLLAMA.md) - Local model optimization

## Getting Help

- Check `python examples/30_doctor/doctor_check.py` for environment issues
- See example READMEs in `examples/*/README.md`
- Review [docs/getting-started/](../getting-started/)

## Examples Run Offline

All examples run offline by default with mock providers. Set `IOA_LIVE=1` and configure API keys for live testing.

