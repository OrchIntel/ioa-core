# IOA Core Reference Glossary

**Version:** 2.5.1  
**Last Updated:** 2025-10-10

Complete reference of terms, concepts, and components in IOA Core.

---

## Core Concepts

| Term | Plain Definition | Example / Link | Related Docs |
|------|------------------|----------------|--------------|
| **Quorum** | Minimum number of model votes required for a decision; in IOA, usually majority (≥ 2 of 3) for strong quorum | [Roundtable Example](../examples/20_roundtable/) | [ROUNDTABLE.md](examples/ROUNDTABLE.md) |
| **Audit Chain** | Immutable log of governance events stored locally; cryptographically verifiable with sequence numbers and hashes | [test_audit_chain.py](../tests/feature_sync/test_audit_chain.py) | [QUICKSTART.md](examples/QUICKSTART.md) |
| **Memory Fabric** | Tiered memory system (hot/cold storage) enabling context persistence across sessions | [test_memory_fabric.py](../tests/feature_sync/test_memory_fabric.py) | [WORKFLOWS.md](examples/WORKFLOWS.md) |
| **Governance Policy** | YAML-based rule set controlling enforcement and evidence generation for workflows | [sample_workflow.yaml](../examples/10_workflows/sample_workflow.yaml) | [FEATURE_MATRIX.md](../FEATURE_MATRIX.md) |
| **4D Tiering** | Educational preview of multi-dimensional memory organization (time × context × source × priority) | [FEATURE_MATRIX.md](../FEATURE_MATRIX.md) | [Memory docs](../src/ioa_core/memory_fabric/) |
| **System Laws** | Seven governing principles for AI orchestration: Transparency, Auditability, Consent, Purpose Limitation, Quorum, Evidence, Review | [SYSTEM_LAWS.md](governance/SYSTEM_LAWS.md) | [README.md](../README.md) |

## Provider Concepts

| Term | Plain Definition | Example / Link | Related Docs |
|------|------------------|----------------|--------------|
| **LLM Provider** | AI model service (OpenAI, Anthropic, Google, DeepSeek, XAI, Ollama) integrated via unified interface | [provider_smoketest.py](../examples/40_providers/provider_smoketest.py) | [PROVIDERS.md](examples/PROVIDERS.md) |
| **Ollama Turbo Mode** | Optimized preset for faster local inference (reduced context, lower temperature, optimized batching) | [turbo_mode_demo.py](../examples/50_ollama/turbo_mode_demo.py) | [OLLAMA.md](examples/OLLAMA.md) |
| **Zero-Retention** | Provider configuration ensuring no data is stored by the LLM service after response | [FEATURE_MATRIX.md](../FEATURE_MATRIX.md) | [README.md](../README.md) |
| **Provider Fallback** | Automatic routing to alternate provider if primary fails | [FEATURE_MATRIX.md](../FEATURE_MATRIX.md) | [README.md](../README.md) |
| **Smoke Test** | Quick connectivity check to verify provider API access and basic functionality | [test_provider_smoketest.py](../tests/examples/test_provider_smoketest.py) | [PROVIDERS.md](examples/PROVIDERS.md) |

## Technical Components

| Term | Plain Definition | Example / Link | Related Docs |
|------|------------------|----------------|--------------|
| **Hot Storage** | In-memory storage for active, frequently accessed data | [test_memory_fabric.py](../tests/feature_sync/test_memory_fabric.py) | [FEATURE_MATRIX.md](../FEATURE_MATRIX.md) |
| **Cold Storage** | Persistent storage for archived data (SQLite, S3, Local JSONL) | [stores/](../src/ioa_core/memory_fabric/stores/) | [FEATURE_MATRIX.md](../FEATURE_MATRIX.md) |
| **AES-GCM Encryption** | Advanced Encryption Standard with Galois/Counter Mode for at-rest data protection | [test_encryption.py](../tests/feature_sync/test_encryption.py) | [FEATURE_MATRIX.md](../FEATURE_MATRIX.md) |
| **SPDX Header** | Standardized license identifier (Apache-2.0) at top of source files | All `.py` files | [CONTRIBUTING.md](../CONTRIBUTING.md) |
| **Evidence ID** | Unique identifier linking workflow execution to audit chain entry | [run_workflow.py](../examples/10_workflows/run_workflow.py) | [WORKFLOWS.md](examples/WORKFLOWS.md) |

## Workflow & Execution

| Term | Plain Definition | Example / Link | Related Docs |
|------|------------------|----------------|--------------|
| **Governed Workflow** | Execution flow with automatic policy enforcement and audit logging | [run_workflow.py](../examples/10_workflows/run_workflow.py) | [WORKFLOWS.md](examples/WORKFLOWS.md) |
| **Vendor-Neutral** | Architecture allowing interchangeable use of multiple LLM providers without vendor lock-in | [roundtable_quorum.py](../examples/20_roundtable/roundtable_quorum.py) | [ROUNDTABLE.md](examples/ROUNDTABLE.md) |
| **Multi-Agent Consensus** | Decision-making process requiring agreement from multiple independent AI models | [test_roundtable.py](../tests/examples/test_roundtable.py) | [ROUNDTABLE.md](examples/ROUNDTABLE.md) |
| **Bootstrap** | Creating initial project structure with configuration files | [boot_project.py](../examples/00_bootstrap/boot_project.py) | [QUICKSTART.md](examples/QUICKSTART.md) |
| **Doctor Check** | System health verification checking Python version, cache access, and provider keys | [doctor_check.py](../examples/30_doctor/doctor_check.py) | [QUICKSTART.md](examples/QUICKSTART.md) |

## CI/CD & Quality

| Term | Plain Definition | Example / Link | Related Docs |
|------|------------------|----------------|--------------|
| **Preflight Lite** | Fast single-repo hygiene check (package structure, docs, SPDX headers) | [local_ci_gate.sh](../../ioa-ops/ci_gates/local/local_ci_gate.sh) | [CI_GATE_STRUCTURE.md](CI_GATE_STRUCTURE.md) |
| **Link Check** | Validation ensuring all Markdown links resolve correctly (0 broken target) | [linkcheck.py](../../ioa-ops/tools/linkcheck.py) | [CI_GATE_STRUCTURE.md](CI_GATE_STRUCTURE.md) |
| **Proof Test** | Lightweight verification confirming a feature exists and is accessible | [tests/feature_sync/](../tests/feature_sync/) | [FEATURE_MATRIX.md](../FEATURE_MATRIX.md) |
| **Mock Provider** | Offline simulation of LLM provider for testing without API calls | [examples/](../examples/) | [QUICKSTART.md](examples/QUICKSTART.md) |
| **Live Mode** | Testing with real provider APIs (enabled via `IOA_LIVE=1` environment variable) | [provider_smoketest.py](../examples/40_providers/provider_smoketest.py) | [PROVIDERS.md](examples/PROVIDERS.md) |

## Compliance & Governance

| Term | Plain Definition | Example / Link | Related Docs |
|------|------------------|----------------|--------------|
| **OSS Boundary** | Clear separation between open-source core features and advanced capabilities | [README.md](../README.md) | [FEATURE_MATRIX.md](../FEATURE_MATRIX.md) |
| **Educational Preview** | Feature available for learning/experimentation, not production-ready | 4D Tiering | [FEATURE_MATRIX.md](../FEATURE_MATRIX.md) |
| **Advanced Edition** | Commercial version with advanced features (HIPAA, SOX, GDPR, Visual Builder) | [FEATURE_MATRIX.md](../FEATURE_MATRIX.md) | [README.md](../README.md) |
| **Data Redaction** | Automatic removal of sensitive information from audit logs | [audit_chain.py](../src/ioa_core/governance/audit_chain.py) | [FEATURE_MATRIX.md](../FEATURE_MATRIX.md) |

---

## Acronyms & Abbreviations

| Acronym | Full Term | Definition |
|---------|-----------|------------|
| **IOA** | Intelligent Orchestration Architecture | The framework name |
| **LLM** | Large Language Model | AI model for text generation (GPT, Claude, etc.) |
| **SPDX** | Software Package Data Exchange | Standard for license identification |
| **AES-GCM** | Advanced Encryption Standard - Galois/Counter Mode | Encryption algorithm |
| **OSS** | Open Source Software | Publicly available source code |
| **CLI** | Command-Line Interface | Terminal-based interaction |
| **API** | Application Programming Interface | Programmatic access to services |
| **YAML** | YAML Ain't Markup Language | Human-readable configuration format |
| **CI/CD** | Continuous Integration / Continuous Deployment | Automated testing & release |

---

## Version-Specific Terms (2.5.1)

| Term | Introduced | Status | Notes |
|------|------------|--------|-------|
| Preflight Lite | v2.5.1 | ✅ Active | Replaced multi-repo preflight |
| 4D Tiering | v2.5.0 | ⚠️ Preview | Educational only |
| Ollama Turbo | v2.5.0 | ✅ Active | Performance optimization |
| Feature Sync Proofs | v2.5.1 | ✅ Active | Automated feature verification |

---

## See Also

- **[FAQ](FAQ.md)** - Frequently asked questions
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Contribution guidelines
- **[QUICKSTART.md](examples/QUICKSTART.md)** - Get started in minutes
- **[FEATURE_MATRIX.md](../FEATURE_MATRIX.md)** - Complete feature comparison
- **[README.md](../README.md)** - Main project documentation

---

## Contributing to the Glossary

Found a term that's unclear or missing? Open an issue or submit a PR with:
- **Term**: The concept name
- **Plain Definition**: Non-technical explanation
- **Example/Link**: Working code or documentation reference
- **Related Docs**: Cross-references

---

**Last Updated:** 2025-10-10  
**Maintained By:** IOA Core Team

