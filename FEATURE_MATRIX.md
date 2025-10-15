# IOA Core Feature Matrix

**Version:** 2.5.1  
**Last Updated:** 2025-10-10

This document lists proven, implemented features in IOA Core open-source edition.

---

## Core Features

### ✅ Audit & Governance

| Feature | Status | Description |
|---------|--------|-------------|
| **Audit Logging** | ✅ Available | Immutable audit chains with cryptographic verification |
| **Audit Chain Verification** | ✅ Available | Verify audit chain integrity and sequence |
| **Data Redaction** | ✅ Available | Automatic redaction of sensitive data in logs |
| **System Laws Framework** | ✅ Available | Seven governing principles for AI orchestration |
| **Ethics Frameworks** | ✅ Available | Reference integration with established ethics assessment tools (Aletheia v2.0 attribution; no derivatives) |

### ✅ Memory System

| Feature | Status | Description |
|---------|--------|-------------|
| **Hot Storage** | ✅ Available | In-memory storage for active data |
| **Cold Storage** | ✅ Available | Persistent storage for archived data |
| **Multiple Backends** | ✅ Available | SQLite, S3, Local JSONL |
| **Encryption (AES-GCM)** | ✅ Available | At-rest encryption for memory |
| **4D Tiering** | ⚠️ Preview | Educational preview of tiered memory management |

### ✅ LLM Provider Support

| Provider | Status | Notes |
|----------|--------|-------|
| **OpenAI** | ✅ Available | GPT-4, GPT-3.5 support |
| **Anthropic** | ✅ Available | Claude 3.x support |
| **Google Gemini** | ✅ Available | Gemini 1.5 support |
| **DeepSeek** | ✅ Available | DeepSeek Chat support |
| **XAI** | ✅ Available | Grok Beta support |
| **Ollama** | ✅ Available | Local model support with turbo mode |

**Ollama Turbo Mode**: Optimized preset for faster local inference (20-40% latency improvement on capable hardware, results vary).

### ✅ CLI Interface

| Command | Status | Description |
|---------|--------|-------------|
| `ioa --help` | ✅ Available | Main CLI help |
| `ioa smoketest-live` | ✅ Available | Live provider smoke testing |
| Provider management | ✅ Available | Configure and test LLM providers |

### ✅ Ethics Cartridge (Preview)

| Feature | Status | Description |
|---------|--------|-------------|
| **Ethics Precheck** | ✅ Available | Runtime ethics validation with confidence scoring |
| **PII Detection** | ✅ Available | Basic detection of personally identifiable information |
| **Deception Detection** | ✅ Available | Identification of potential manipulation attempts |
| **Harmful Content Detection** | ✅ Available | Basic screening for inappropriate content |
| **Fairness Violation Detection** | ✅ Available | Detection of potential bias or discrimination |
| **Policy Validation** | ✅ Available | Validate ethics policy configurations |

**Note**: Ethics cartridge (Aletheia-inspired) - IOA original implementation with neutral criteria names. Not a derivative of Aletheia Framework v2.0.

---

## Not in OSS (Restricted Edition)

The following features are available in Restricted Edition:

- **Workflow Engine (YAML DSL)** - Visual workflow builder
- **PKI Agent Onboarding** - Advanced agent management
- **Multi-region Replication** - Geo-distributed storage
- **Advanced Analytics** - Detailed usage and performance analytics
- **Compliance Frameworks** - Full HIPAA, SOX, GDPR tooling
- **Visual Builder** - Drag-and-drop workflow designer

---

## Feature Verification

All features listed as "✅ Available" have been verified with proof tests:

- `tests/feature_sync/test_audit_chain.py` - Audit logging
- `tests/feature_sync/test_memory_fabric.py` - Memory system
- `tests/feature_sync/test_encryption.py` - AES-GCM encryption
- `tests/feature_sync/test_providers.py` - LLM providers
- `tests/perf/test_ollama_turbo.py` - Ollama turbo mode

Run proof tests:
```bash
python3 tests/feature_sync/test_*.py
python3 tests/perf/test_ollama_turbo.py
```

---

## OSS vs Restricted Edition

| Category | OSS | Restricted Edition |
|----------|-----|-------------------|
| **Core Engine** | ✅ Full | ✅ Full |
| **LLM Providers** | ✅ 6 providers | ✅ 6+ providers |
| **Governance** | ✅ Basic | ✅ Advanced |
| **Memory System** | ✅ Hot/Cold | ✅ Multi-tier + Advanced |
| **Workflow Engine** | ❌ Future | ✅ Visual Builder |
| **Compliance** | ✅ Educational | ✅ Production-Ready |

---

**Note**: IOA Core OSS provides production-ready audit, memory, and multi-provider orchestration. Restricted Edition adds enterprise compliance, advanced analytics, and visual tooling.

For more information, see [README.md](README.md).
