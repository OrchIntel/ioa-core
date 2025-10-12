# IOA Core v2.5.1

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10–3.12-brightgreen.svg)]()
[![Build](https://img.shields.io/github/actions/workflow/status/OrchIntel/ioa-core/build.yml?branch=main)](https://github.com/OrchIntel/ioa-core/actions/workflows/build.yml)
[![Docs](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://ioa.systems/docs)
[![Discord](https://img.shields.io/discord/1426192731679621316?label=Discord&logo=discord&color=7289da)](https://discord.gg/Fzxa5GG9)

IOA Core is the **open-source framework for governed AI orchestration** —  
bringing verifiable policy, evidence, and trust to every workflow.

## 🚀 Quick Start

Get up and running in minutes:

```bash
# Install IOA Core
pip install ioa-core

# Bootstrap a new project
python examples/00_bootstrap/boot_project.py my-ai-system

# Run a simple governed workflow
python examples/10_workflows/run_workflow.py

# Run vendor-neutral roundtable with quorum policy
python examples/20_roundtable/roundtable_quorum.py "Analyze this code for security issues (ok)"

# Check system health
python examples/30_doctor/doctor_check.py
```

> **Note**: Examples run offline by default with mock providers. Set `IOA_LIVE=1` and configure API keys for live testing (not executed in CI).

For complete tutorials, see [docs/examples/QUICKSTART.md](docs/examples/QUICKSTART.md).

## 🎯 Vendor-Neutral Quorum Policy

IOA Core v2.5.0 introduces vendor-neutral quorum policy for multi-agent consensus with graceful scaling from 1→N providers:

### Key Features

- **Provider-Agnostic Roster Building**: Automatically builds agent rosters based on available providers
- **Sibling Model Weighting**: Votes from same provider/model family count with reduced weight (0.6x)
- **Auditor Fallback Selection**: M2 baseline validation with automatic provider selection
- **Quorum Diagnostics**: Comprehensive metrics for consensus evaluation
- **Law Evidence Fields**: Built-in compliance with Laws 1, 5, and 7

### Usage Examples

> **Note**: Some commands below are examples for future functionality.

```bash
# Basic vendor-neutral roundtable
# Example (not currently implemented): ioa demo vendor-neutral-roundtable --task "Create a marketing strategy for our product"

# With custom quorum configuration
# Example (not currently implemented): ioa demo vendor-neutral-roundtable \
#   --quorum-config config/custom_quorum.yaml \
#   --min-agents 3 \
#   --strong-quorum 4 \
#   --auditor openai \
#   --task "Review this code for bugs"

# Auto-detect providers and quorum settings
# Example (not currently implemented): ioa demo vendor-neutral-roundtable --task "Analyze market trends"
```

### Quorum Configuration

Configure quorum behavior in `config/quorum.yaml`:

```yaml
# Provider fallback order (editable)
fallback_order:
  - "openai"
  - "anthropic" 
  - "gemini"
  - "deepseek"
  - "xai"
  - "ollama"

# Quorum thresholds
min_agents: 2
strong_quorum:
  min_agents: 3
  min_providers: 2

# Sibling weighting (same provider models get reduced weight)
sibling_weight: 0.6

# Consensus threshold
consensus_threshold: 0.67
```

### Quorum Types

- **Single Provider**: Creates 2+ sibling agents with 0.6x weight
- **2-Node**: 1+ agents per provider, full weight
- **Strong Quorum**: 3+ providers, equal weights, enhanced validation

## 📦 Installation

### Quick Install

```bash
# Install from PyPI (recommended for production)
pip install ioa-core

# Or install from source (recommended for development)
git clone https://github.com/orchintel/ioa-core.git
cd ioa-core
pip install -e ".[dev]"
```

### Automated Setup

> **Note**: Some commands below are examples for future functionality.

```bash
# Use our setup script for development
git clone https://github.com/orchintel/ioa-core.git
cd ioa-core
# ./scripts/dev_local_setup.sh
```

For detailed installation instructions, see our [Installation Guide](docs/getting-started/installation.md).

## ✨ Core Features

IOA Core provides production-ready capabilities for governed AI orchestration:

### 🔒 Audit & Governance
- **Immutable Audit Chains**: Cryptographically verified audit logging
- **System Laws Framework**: Seven governing principles for AI orchestration
- **Data Redaction**: Automatic redaction of sensitive data in logs
- **Compliance-Ready**: Educational framework for regulatory requirements

### 💾 Memory System
- **Multi-Tier Storage**: Hot (in-memory) and cold (persistent) storage
- **Multiple Backends**: SQLite, S3, Local JSONL
- **AES-GCM Encryption**: At-rest encryption for sensitive data
- **4D Tiering** (Preview): Educational preview of tiered memory management

### 🤖 LLM Provider Support
Supports 6 major LLM providers with unified interface:
- **OpenAI** (GPT-4, GPT-3.5)
- **Anthropic** (Claude 3.x)
- **Google Gemini** (Gemini 1.5)
- **DeepSeek** (DeepSeek Chat)
- **XAI** (Grok Beta)
- **Ollama** (Local models with turbo mode)

### 🎯 Provider Features
- Zero-retention data handling
- Rate limiting and cost controls
- Fallback routing and error handling
- Live smoke testing for all providers

For a complete feature comparison, see [FEATURE_MATRIX.md](FEATURE_MATRIX.md).

## 📚 Examples & Tutorials

IOA Core includes working examples for all core features. All examples run offline by default.

### Quick Examples

```bash
# Bootstrap a project
python examples/00_bootstrap/boot_project.py my-project

# Run governed workflow
python examples/10_workflows/run_workflow.py

# Multi-agent quorum voting
python examples/20_roundtable/roundtable_quorum.py "Your task (ok)"

# System health check
python examples/30_doctor/doctor_check.py

# Provider smoke test
IOA_PROVIDER=mock python examples/40_providers/provider_smoketest.py

# Ollama turbo mode
python examples/50_ollama/turbo_mode_demo.py turbo_cloud
```

### Comprehensive Tutorials

- **[Quick Start](docs/examples/QUICKSTART.md)** - Get started in minutes
- **[Workflows Guide](docs/examples/WORKFLOWS.md)** - Build governed workflows
- **[Roundtable Guide](docs/examples/ROUNDTABLE.md)** - Multi-agent consensus
- **[Provider Setup](docs/examples/PROVIDERS.md)** - Configure LLM providers
- **[Ollama Turbo](docs/examples/OLLAMA.md)** - Local model optimization

### Live Testing

Examples run offline by default. For live testing with real providers:

```bash
# Set your API keys
export OPENAI_API_KEY=your-key
export ANTHROPIC_API_KEY=your-key

# Enable live mode
IOA_LIVE=1 IOA_PROVIDER=openai python examples/40_providers/provider_smoketest.py
```

> **Note**: Live tests are not executed in CI. All CI tests use offline mocks.

## 🔧 Setup LLM Providers

Configure your LLM providers using the unified CLI:

> **Note**: Some commands below are examples for future functionality.

```bash
# Interactive setup (recommended for first-time users)
# Example (not currently implemented): ioa onboard setup

# Verify your configuration (no live calls)
# Example (not currently implemented): ioa doctor

# Optional 1-token pings
# Example (not currently implemented): ioa smoketest providers --provider openai --live

# Resilient form if entrypoint issues
python -m ioa_core.cli onboard setup
```

This will create configuration files in `~/.ioa/config/` for managing multiple LLM providers and roundtable settings.

### API Keys Setup

IOA Core supports multiple LLM providers. Set up your API keys using one of these methods:

#### Method 1: Environment Variables (Recommended)

```bash
# Set API keys in your shell
export OPENAI_API_KEY="sk-your-openai-key"
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key"
export XAI_API_KEY="xai-your-xai-key"
export GOOGLE_API_KEY="your-google-key"
export DEEPSEEK_API_KEY="your-deepseek-key"

# For local Ollama (no API key needed)
export OLLAMA_HOST="http://localhost:11434"
```

#### Method 2: .env.local File

> **Note**: Some commands below are examples for future functionality.

```bash
# Copy the example file
# cp .env.local.example .env.local

# Edit .env.local and add your actual API keys
# nano .env.local
```

#### Getting API Keys

- **OpenAI**: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Anthropic**: [https://console.anthropic.com/](https://console.anthropic.com/)
- **XAI/Grok**: [https://console.x.ai/](https://console.x.ai/)
- **Google Gemini**: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- **DeepSeek**: [https://platform.deepseek.com/](https://platform.deepseek.com/)

#### Verify Setup

> **Note**: Some commands below are examples for future functionality.

```bash
# Check provider configuration
# Example (not currently implemented): ioa doctor

# Test specific provider
# Example (not currently implemented): ioa smoketest providers --provider xai
```

### Supported Providers

IOA Core supports multiple LLM providers with automatic fallback and offline mode:

- **OpenAI** (GPT-4, GPT-3.5) - Set `OPENAI_API_KEY`
- **Anthropic** (Claude 3) - Set `ANTHROPIC_API_KEY`
- **XAI/Grok** - Set `XAI_API_KEY` or `GROK_API_KEY`
- **Google Gemini** - Set `GOOGLE_API_KEY`
- **DeepSeek** - Set `DEEPSEEK_API_KEY`
- **Ollama** (local) - Set `OLLAMA_HOST` (no API key required)

### Offline Mode

For development and testing, enable offline mode:

> **Note**: Some commands below are examples for future functionality.

```bash
export IOA_OFFLINE=true
# Example (not currently implemented): ioa smoketest providers
```

### Test Connectivity

Test your provider setup:

> **Note**: Some commands below are examples for future functionality.

```bash
# Test all providers offline (default)
# Example (not currently implemented): ioa smoketest providers

# Test specific provider live
# Example (not currently implemented): ioa smoketest providers --provider openai --live
# Note: OpenAI connectivity requires `openai` SDK v1+ and uses `gpt-4o-mini` by default (override with `--openai-model` or `OPENAI_MODEL`). The v1 client pattern is `from openai import OpenAI; client = OpenAI()` and `client.chat.completions.create(...)`.

# Non-interactive mode (for CI/automated tests)
# Example (not currently implemented): ioa smoketest providers --non-interactive
export IOA_SMOKETEST_NON_INTERACTIVE=1
# Example (not currently implemented): ioa smoketest providers
```

#### Cost Control and Model Overrides

Control costs and customize models for live testing:

> **Note**: Some commands below are examples for future functionality.

```bash
# Set cost ceiling (default: $0.25)
# Example (not currently implemented): ioa smoketest providers --live --max-usd 0.10

# Override models for specific providers
# Example (not currently implemented): ioa smoketest providers --live --openai-model gpt-3.5-turbo --anthropic-model claude-3-haiku

# Use environment variables for configuration
export IOA_SMOKETEST_MAX_USD=0.05
export OPENAI_MODEL=gpt-4
export ANTHROPIC_MODEL=claude-3-opus
# Example (not currently implemented): ioa smoketest providers --live
```

**Cost Ceiling Features:**
- Prevents surprise token spend during live provider checks
- Default ceiling: $0.25 USD
- Configurable via `--max-usd` flag or `IOA_SMOKETEST_MAX_USD` env var
- Shows cost usage and ceiling status in output
- Skips remaining providers when ceiling is reached

**Model Override Features:**
- Override models per provider via CLI flags or environment variables
- Supported providers: OpenAI, Anthropic, Google, DeepSeek, XAI
- Environment variables: `OPENAI_MODEL`, `ANTHROPIC_MODEL`, `GEMINI_MODEL`, `DEEPSEEK_MODEL`, `XAI_MODEL`
- Default models are cost-optimized (e.g., gpt-3.5-turbo, claude-3-haiku)

#### Ollama Turbo Mode

IOA Core automatically detects Ollama Turbo (cloud) vs local turbo preset:

- **turbo_cloud**: Ollama Turbo (cloud) - requires `OLLAMA_API_BASE` and `OLLAMA_API_KEY`
- **local_preset**: Local turbo preset for low-latency inference (default)
- **auto**: Auto-detect based on environment variables

The smoketest will show the detected mode in the status report:

> **Note**: Some commands below are examples for future functionality.

```bash
# Local preset mode
# ✅ Ollama: Host: http://localhost:11434, Mode: local_preset (no API key required)
#   📊 Mode: local_preset
#   📝 Notes: Ollama local_preset mode detected

# Cloud Turbo mode
# ✅ Ollama: Host: https://api.ollama.ai/v1, Mode: turbo_cloud (API key configured)
#   📊 Mode: turbo_cloud
#   📝 Notes: Ollama turbo_cloud mode detected
```

#### Ollama Configuration Examples

**Local Preset Mode (default):**
> **Note**: Some commands below are examples for future functionality.

```bash
# .env.local
# OLLAMA_HOST=http://localhost:11434
# OLLAMA_MODEL=llama3.1:8b
# IOA_OLLAMA_MODE=local_preset

# Run smoketest
# Example (not currently implemented): ioa smoketest --provider ollama --ollama-mode local_preset
```

**Cloud Turbo Mode:**
> **Note**: Some commands below are examples for future functionality.

```bash
# .env.local
# OLLAMA_API_BASE=https://api.ollama.ai/v1
# OLLAMA_API_KEY=your-ollama-cloud-api-key-here
# IOA_OLLAMA_MODE=turbo_cloud

# Run smoketest
# Example (not currently implemented): ioa smoketest --provider ollama --ollama-mode turbo_cloud
```

**Auto-detect Mode:**
> **Note**: Some commands below are examples for future functionality.

```bash
# .env.local
# Set either local or cloud credentials
# OLLAMA_HOST=http://localhost:11434  # OR
# OLLAMA_API_BASE=https://api.ollama.ai/v1
# OLLAMA_API_KEY=your-key-here

# Run smoketest (auto-detects based on available credentials)
# Example (not currently implemented): ioa smoketest --provider ollama --ollama-mode auto
```

For more information about Ollama Turbo, see the [Ollama Turbo documentation](https://ollama.com/turbo).

## 🏗️ Project Creation

Generate a new project directory using the bootloader:

> **Note**: Some commands below are examples for future functionality.

```bash
# Interactive project creation
# Example (not currently implemented): ioa boot

# Non-interactive creation
# Example (not currently implemented): ioa boot --project-name my-project --template basic
```

Follow the interactive prompts to choose a project type and name. A new `<project>.ioa` directory will be created with configuration, schemas and boot prompts.

## 🤖 Agent Onboarding

Add new agents to your project using the onboarding API. The example below shows how to onboard a simple legal research agent with proper error handling. The `AgentOnboarding` class will validate the manifest against the schema, verify the trust signature and ensure tenant isolation. It raises specific exceptions when onboarding fails (e.g., `ManifestValidationError`, `TrustVerificationError`, `TenantIsolationError`) so you can respond accordingly.

```python
from src.agent_onboarding import AgentOnboarding, AgentOnboardingError

# Load your agent manifest from disk or construct it dynamically. For example,
# a legal research assistant might declare the following capabilities:
manifest_json = {
    "agent_id": "LegalResearcher",
    "adapter_class": "src.llm_adapter.LLMService",
    "capabilities": ["analysis", "legal_research", "citation"],
    "tenant_id": "default",
    # Generate a trust signature using a secure secret and SHA‑256 (see sample in
    # agent_onboarding.py)
    "trust_signature": "5d19bd2b8a301f97f4e219df349d697498d0785bd761a8c069ad5fd69380bfb4"
}

onboarder = AgentOnboarding(base_dir="<project>.ioa")

try:
    result = onboarder.onboard_agent(manifest_json)
    print(f"Onboarding succeeded for {result.agent_id}:", result)
except AgentOnboardingError as e:
    # Handle onboarding errors gracefully – inspect the exception type to
    # differentiate between validation, trust and isolation errors.
    print(f"Onboarding failed: {e}")
```

The onboarding process validates the manifest, verifies trust signatures, enforces tenant isolation and records KPI metrics.

## 🔄 Execute Roundtable Tasks

The roundtable executor orchestrates tasks across multiple agents:

```python
import asyncio
from src.roundtable_executor import RoundtableExecutor
from src.agent_router import AgentRouter
from src.storage_adapter import InMemoryStorageService

router = AgentRouter(governance_config={})
storage = InMemoryStorageService()
roundtable = RoundtableExecutor(router, storage)

async def run_task():
    result = await roundtable.execute_roundtable(
        task="Summarize updates",
        agents=["agent1", "agent2"]
    )
    print(result)

asyncio.run(run_task())
```

A `RoundtableResult` is returned with aggregated responses and consensus information.

## 📚 Documentation

- **[Getting Started](docs/getting-started/)** - Installation and quickstart guides
- **[Tutorials](docs/tutorials/)** - Step-by-step tutorials and examples
- **[User Guide](docs/user-guide/)** - CLI reference and configuration
- **[API Reference](docs/api/)** - Developer documentation
- **[Operations](docs/external/OPS_GUIDES.md)** - Deployment and operations guides

## 🧪 Testing & Development

### Quick Tests

> **Note**: Some commands below are examples for future functionality.

```bash
# Run quick test suite
# ./scripts/dev_test_quick.sh

# Run specific test categories
pytest tests/unit/ -v
pytest tests/smoke/ -m smoke
pytest tests/integration/ -v
```

### Performance Testing

> **Note**: Some commands below are examples for future functionality.

```bash
# Run 100k performance test locally
pytest tests/performance/test_100k.py -v

# Run authoritative EC2 test
# ./scripts/ec2_100k_gate.sh
```

### Development Setup

> **Note**: Some commands below are examples for future functionality.

```bash
# Setup development environment
# ./scripts/dev_local_setup.sh

# Use development helper
# ./dev.sh help
```

### Environment Sync

Keep Cursor and local environments in sync with our automated environment synchronization system:

#### One-Liners for Local Development

> **Note**: Some commands below are examples for future functionality.

```bash
# Sync your local environment with the latest
# make dev.sync

# Create environment snapshot
# make env.snap

# Apply environment from lock
# make env.apply

# Run quick smoketest
# make smoke.quick
```

#### Environment Lock System

IOA Core uses `.ioa/env.lock.json` to ensure reproducible environments across Cursor and local development:

> **Note**: Some commands below are examples for future functionality.

```bash
# Create environment lock with current state
# make env.snap

# Apply locked environment (creates/refreshes venv)
# make env.apply

# Check for environment drift
# Example (not currently implemented): ioa doctor --strict
```

#### CI/CD Integration

The environment sync system is integrated into CI/CD:

- **Repository Hygiene Check**: Validates entrypoint and environment consistency
- **Environment Lock**: CI uses the same lock file as local development
- **Self-Healing**: Automatic environment repair on drift detection

#### Troubleshooting Environment Issues

> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# Check environment status
# Example (not currently implemented): ioa doctor --strict

# Force environment refresh
# rm -rf venv .ioa/env.lock.json
# make env.snap
# make env.apply

# Verify entrypoint works
python tools/ci/check_entrypoint.py --venv-path ./venv --strict
```

## 🔐 Security & Governance

### Secret Scanning

IOA Core uses [detect-secrets](https://github.com/Yelp/detect-secrets) to scan for accidentally committed secrets and API keys.

**How we handle secret scanning:**
- All secrets are detected and tracked in `.secrets.baseline`
- New secrets trigger CI failures to prevent accidental commits
- Example files like `docs/env.example` are allowlisted for documentation
- To update the baseline after auditing: `detect-secrets scan --update .secrets.baseline`

**Running locally:**
> **Note**: Some commands below are examples for future functionality.

```bash
# Install detect-secrets
pip install detect-secrets

# Scan for secrets
# detect-secrets scan

# Audit existing baseline
# detect-secrets audit .secrets.baseline
```

### Zero-Retention Controls

IOA Core enforces best-effort "zero retention" policy when calling external LLM providers:

- Outbound requests include retention-off hints in provider-specific ways
- JSON `metadata`: `{ "retain": false, "data_retention": false }`
- Header: `X-Data-Retention-Opt-Out: true`
- Not all providers currently expose explicit retention controls

### Audit Logging

- All operations are logged with structured JSON
- Sensitive data (tokens, emails) are automatically redacted
- Audit logs rotate based on size (~10MB) with SHA-256 integrity
- Immutable JSONL audit rotation policy with configurable size/time limits
- Hash-based integrity verification for all audit entries

### PKI Integration

- Agent trust verification via digital signatures
- Tenant isolation enforcement
- Manifest validation against schemas
- AES-256 encryption at rest for cold storage (feature-flagged)
- Configurable encryption key management via environment variables

### Compliance & Regulatory Support

IOA Core provides hooks and frameworks for compliance with major regulatory standards:

- **GDPR Compliance**: Data retention controls, audit logging, and privacy-by-design architecture
- **HIPAA Compliance**: Healthcare data handling with encryption and access controls
- **SOC2 Compliance**: Security controls and audit trails for enterprise deployments
- **EU AI Act Compliance**: AI governance and transparency requirements

For detailed compliance guidance, see [docs/COMPLIANCE_CHECKLIST.md](docs/COMPLIANCE_CHECKLIST.md).

## ⚖️ Compliance Philosophy — Open Source Edition

IOA Core (Open Source Edition) provides **governance primitives** (evidence logging, policy hooks, redaction, signing) and **educational preview stubs** for certain frameworks.

It does **not** ship full legal/compliance logic. Full policy packs for regulated frameworks are delivered in the **Restricted Edition**, subject to access terms.

- *Why this split?**
- Keeps the OSS code legally safe and universally usable.
- Allows regulated frameworks to evolve under change control with audits, SBOMs, and regulator-facing evidence.
- *Can I build my own cartridges on OSS?** Yes. IOA Core is extensible; third parties can build custom cartridges. However, **IOA badges/claims only cover IOA-authored and signed policy packs**. External cartridges are marked with their own origin and are not representations of legal compliance by IOA.

> OSS Versioning: The canonical OSS tag is **v2.5.0**. Per-file version and "last updated" are tracked by Git; we avoid duplicating them in headers to prevent drift.

## 🔒 Immutable Audit Logs

IOA Core v2.5.0 introduces enterprise-grade immutable audit logging with tamper-evidence verification:

### Key Features

- **Hash-Chained Integrity**: Each log entry contains its own SHA-256 hash and the hash of the previous entry
- **Tamper Detection**: Any modification breaks the hash chain and is immediately detectable
- **Canonical JSON**: Deterministic serialization ensures consistent hashing across systems
- **Multi-Backend Support**: Local filesystem and S3 storage with automatic detection
- **Verification CLI**: Comprehensive `ioa audit verify` command for integrity checking
- **Anchoring Support**: External publication of root hashes for additional security

### Quick Start

> **Note**: Some commands below are examples for future functionality.

```bash
# Generate and verify an audit chain
# Example (not currently implemented): ioa demo roundtable --task "Hello world"
# Example (not currently implemented): ioa audit verify audit_chain/20250910/run_001.jsonl

# Verify with S3 backend
# Example (not currently implemented): ioa audit verify s3://my-bucket/audit-chains/ --s3-bucket my-bucket

# Generate detailed JSON report
# Example (not currently implemented): ioa audit verify audit_chain/ --out audit_report.json

# Verify specific chain with anchor file
# Example (not currently implemented): ioa audit verify audit_chain/ --chain-id run_001 --anchor-file anchors/root.json
```

### Storage Layout

**Local Filesystem:**
```
audit_chain/
├── 20250910/
│   ├── run_001.jsonl          # Raw audit log
│   ├── run_001_receipt.json   # Hash receipt
│   ├── run_002.jsonl
│   └── run_002_receipt.json
└── anchors/
    └── 2025/09/10/
        └── run_001_root.json
```

**S3 Storage:**
```
s3://bucket/audit_chain/
├── 20250910/
│   ├── run_001.jsonl
│   ├── run_001_receipt.json
│   ├── run_002.jsonl
│   └── run_002_receipt.json
└── anchors/2025/09/10/
    └── run_001_root.json
```

### Verification Examples

> **Note**: Some commands below are examples for future functionality.

```bash
# Basic verification
# Example (not currently implemented): ioa audit verify audit_chain/20250910/run_001.jsonl

# Verify all chains for a date
# Example (not currently implemented): ioa audit verify audit_chain/20250910/

# Verify with S3 backend
# Example (not currently implemented): ioa audit verify s3://my-bucket/audit_chain/20250910/ --s3-bucket my-bucket

# Advanced options
# Example (not currently implemented): ioa audit verify audit_chain/ \
#   --chain-id run_001 \
#   --anchor-file anchors/2025/09/10/run_001_root.json \
#   --start-after evt_123 \
#   --since 2025-09-10 \
#   --backend s3 \
#   --s3-bucket my-bucket \
#   --threads 4 \
#   --strict \
#   --out report.json
```

### CLI Options

- `--chain-id`: Verify specific chain (if multiple chains in path)
- `--anchor-file`: External anchor file containing published root hash
- `--start-after`: Start verification after specific event ID
- `--since`: Start verification after specific date (YYYY-MM-DD)
- `--backend`: Storage backend (fs/s3/auto, default: auto)
- `--s3-bucket`/`--s3-prefix`: S3 configuration
- `--out`: Write JSON report to file
- `--threads`: I/O concurrency (default: 1)
- `--strict`: Reject unknown fields and schema drift
- `--ignore-signatures`: Verify only hash chain if signatures missing
- `--fail-fast`/`--no-fail-fast`: Stop on first error (default: True)
- `--quiet`: Summary only output

### Documentation

- **[Why Immutable Logs Matter](docs/external/AUDIT_GUIDES.md)** - Understanding the importance of immutable audit logs
- **[Quickstart: Run + Verify](docs/external/AUDIT_GUIDES.md)** - How to enable and use audit logging
- **[Storage Layout](docs/external/AUDIT_GUIDES.md)** - File organization and retention strategies
- **[S3 Backend](docs/external/AUDIT_GUIDES.md)** - Enterprise S3 storage configuration
- **[Tamper Detection](docs/external/AUDIT_GUIDES.md)** - How tamper detection works
- **[Reading Receipts](docs/external/AUDIT_GUIDES.md)** - Understanding receipt files
- **[Enterprise Extensions](docs/external/AUDIT_GUIDES.md)** - Advanced features for enterprise

### Examples

> **Note**: Some commands below are examples for future functionality.

```bash
# Run a simple roundtable with audit logging
# Example (not currently implemented): ioa demo roundtable --task "Analyze this code for security issues"

# Verify the generated audit chain
# Example (not currently implemented): ioa audit verify audit_chain/$(date +%Y%m%d)/run_*.jsonl

# Check for tampering (this will fail)
echo "tampered" >> audit_chain/$(date +%Y%m%d)/run_*.jsonl
# Example (not currently implemented): ioa audit verify audit_chain/$(date +%Y%m%d)/run_*.jsonl
```

## 🧠 Memory Fabric

IOA Core v2.5.0 introduces the Memory Fabric - a modular memory system with multiple backends, encryption, and advanced querying capabilities:

### Key Features

- **Modular Backends**: Local JSONL, SQLite, and S3 storage options
- **Schema Versioning**: Future-proof data structures with version tags
- **AES-GCM Encryption**: Automatic encryption when keys are provided
- **Advanced Querying**: Full-text search and filtering capabilities
- **Migration Tools**: Seamless migration from legacy memory systems
- **Metrics & Monitoring**: Comprehensive performance and usage metrics
- **PII Redaction**: Built-in privacy protection for logging and examples

### Quick Start

> **Note**: Some commands below are examples for future functionality.

```bash
# Check memory fabric health
# Example (not currently implemented): ioa fabric doctor --backend sqlite

# Migrate from old memory system
# Example (not currently implemented): ioa fabric migrate --backend sqlite

# Basic usage
python -c "
# from memory_fabric import MemoryFabric
# fabric = MemoryFabric(backend='sqlite')
# record_id = fabric.store('Hello, Memory Fabric!')
# print(fabric.retrieve(record_id).content)
# fabric.close()
# "
```

### Backend Comparison

| Backend | Best For | Features |
|---------|----------|----------|
| **local_jsonl** | Development, small datasets | Simple, no dependencies, human-readable |
| **sqlite** | Production, medium datasets | Fast queries, ACID compliance, full-text search |
| **s3** | Cloud deployments, large datasets | Scalable, distributed, durable |

### Migration from Legacy Memory Systems

The legacy `memory_engine` module is deprecated and will be removed in v2.7.0:

```python
# Old (deprecated)
from memory_engine import MemoryEngine
engine = MemoryEngine()  # Shows deprecation warning

# New (recommended)
from memory_fabric import MemoryFabric
fabric = MemoryFabric(backend="sqlite")
```

For detailed documentation, see [docs/memory/](docs/memory/).

## 📖 CLI Commands

The IOA Core CLI provides comprehensive commands for managing your system:

> **Note**: Some commands below are examples for future functionality.

```bash
# System information
# Example (not currently implemented): ioa --version
# Example (not currently implemented): ioa health --detailed

# LLM Provider Management
# Example (not currently implemented): ioa onboard setup                    # Interactive setup wizard
# Example (not currently implemented): ioa doctor                          # Diagnose configuration issues
# Example (not currently implemented): ioa smoketest providers             # Test provider connectivity
# Example (not currently implemented): ioa keys verify                     # Verify all provider keys

# Vector Search
# Example (not currently implemented): ioa vectors --index patterns.json --query "AI agent" --k 5

# Audit Chain Verification
# Example (not currently implemented): ioa audit verify logs/audit_chain-*.jsonl
# Example (not currently implemented): ioa audit verify s3://my-bucket/audit-chains/ --s3-bucket my-bucket
# Example (not currently implemented): ioa audit verify logs/ --out audit_report.json

# Project management (coming soon)
# ioa boot --project-name my-project
# ioa workflows run --file workflow.yaml
```

For complete CLI reference, see [docs/user-guide/cli-reference.md](docs/user-guide/cli-reference.md).

## 🏗️ Architecture

### Core Components

- **Memory Engine**: Hot/cold storage with intelligent pruning
- **Agent Router**: Task routing and governance integration
- **Governance**: Audit logging, PKI verification, compliance
- **Workflow DSL**: YAML-based workflow definition and execution
- **Multi-Provider LLM**: OpenAI, Anthropic, Gemini, DeepSeek, XAI, Ollama

### Key Features

- **Memory-Driven**: Persistent memory across sessions
- **Governance-First**: Built-in security and compliance
- **Multi-Provider**: Automatic fallback and offline mode
- **Performance**: 100k test harness with performance gates
- **Extensible**: Plugin architecture for custom agents

## 🤝 Contributing

We welcome community contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on submitting pull requests, branch naming conventions and license compliance. By contributing you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

### Running CI Gates Locally

Before submitting a pull request, run our comprehensive CI Gates validation system:

> **Note**: Some commands below are examples for future functionality.

```bash
# Quick local check (recommended before every commit)
# Example (not currently implemented): ioa gates doctor

# Run specific gates
# Example (not currently implemented): ioa gates run --gates governance,security

# Generate detailed report
# Example (not currently implemented): ioa gates report --format md --open
```

CI Gates validates:
- **Governance:** Laws 1-7 compliance (ethics, sustainability, harness)
- **Security:** Bandit scanning, TruffleHog secrets detection, hygiene checks
- **Docs:** CLI validation, MkDocs build verification
- **Hygiene:** Forbidden pattern detection

See [CI Gates v1 Documentation](docs/CI_GATE_STRUCTURE.md) for complete details.

### Documentation Standards
All documentation contributions must follow our **[IOA Style Guide](docs/external/OPS_GUIDES.md)** which ensures:
- Professional, engineering-grade language
- Consistent terminology and formatting
- Governance-first compliance
- Non-interactive execution in CI

See [CONTRIBUTING.md](CONTRIBUTING.md) for complete documentation governance rules.

## 📂 Repository Layout

```
/                    # Minimal top-level: README, LICENSE, CHANGELOG, CONTRIBUTING, SECURITY, pyproject.toml
├── .github/         # GitHub Actions workflows, issue templates, CODEOWNERS
├── src/             # ioa_core source code
├── tests/           # Test suites (unit, integration, feature proofs, performance)
├── docs/            # All documentation
│   ├── ops/         # Operational docs & dispatch reports
│   ├── reference/   # Reference materials (scaling, maintainers, trademarks)
│   ├── examples/    # Tutorial documentation
│   └── ...
├── examples/        # Runnable examples with READMEs
├── tools/           # Helper scripts (non-CI)
├── monitoring/      # Monitoring configuration & runbooks
└── cartridges/      # Compliance cartridge frameworks
```

**Key Principles**:
- **Root is clean**: Only essential project files at top level
- **Docs are organized**: Operational, reference, and tutorial docs properly categorized
- **Examples are runnable**: All examples include READMEs and are tested in CI
- **Tools are separate**: Helper scripts live in `/tools`, CI workflows in `/.github/workflows`

For detailed file locations and organization, see [docs/ops/WHERE_THINGS_LIVE.md](docs/ops/WHERE_THINGS_LIVE.md).

## 📄 License

This project is licensed under the [Apache 2.0 License](LICENSE). See the license file for details.

---

© 2025 OrchIntel Systems Ltd. Contributors. Built by the IOA Project Contributors.

## ⚖️ Compliance Philosophy (Open-Source Edition)

The IOA Core open-source edition provides educational and structural tools for AI governance. It demonstrates how governance logic, evidence, and runtime observability can be embedded in machine intelligence systems.

It does not represent legal compliance with any regulatory framework (e.g., EU AI Act, HIPAA, SOX). Validated cartridges for regulated deployments are distributed separately under restricted access.

Developers are free to create their own cartridges using the IOA API structure, provided they:
- Clearly identify their origin and version,
- Do not misrepresent them as regulator-certified modules, and
- Acknowledge that IOA Core offers a technical framework, not legal certification.

"Compliance" in OSS refers to adherence to IOA's governance principles — transparency, traceability, and accountability — not legal conformity.

## 🔍 Core vs Extensions

IOA Core includes the publicly available orchestration engine, governance configuration and baseline tests. Proprietary cognitive science extensions and advanced experimental modules will be released separately under a private license. The public core is intended to serve as a foundation for community collaboration and transparency.

## 📊 Feature Matrix

For a side‑by‑side comparison of which modules are available in the open‑source core versus the enterprise edition, see [docs/feature-matrix.md](docs/feature-matrix.md).