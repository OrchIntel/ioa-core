**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# IOA Core

IOA (Intelligent Orchestration Architecture) Core is an open‑source platform for orchestrating modular AI agents with memory‑driven collaboration and governance mechanisms. This repository provides the core engine under an Apache‑2.0 license.

> **⚠️ IOA Core Status**: This is a development and evaluation framework. For production deployments requiring enterprise-grade security, compliance, and advanced features, consider [IOA Enterprise](mailto:enterprise@orchintel.com).

## Quick Start

### Installation

Install IOA Core using pip:

```bash
pip install ioa-core
```

Or install from source:

```bash
git clone https://github.com/ioa-project/ioa-core.git
cd ioa-core
pip install -e .
```

### Boot a New Project

Generate a new project directory using the bootloader:

> **Note**: Some commands below are examples for future functionality.

```bash
# ioa-boot
# or
python -m src.bootloader
```

Follow the interactive prompts to choose a project type and name. A new `<project>.ioa` directory will be created with configuration, schemas and boot prompts.

### Run the CLI

To start the command‑line interface for an existing project:

> **Note**: Some commands below are examples for future functionality.

```bash
# Example (not currently implemented): ioa --project-path <path_to_project>
# or
python src/cli_interface.py --project-path <path_to_project>
```

## Core Features

IOA Core provides a foundation for multi-agent orchestration with:

- **Memory Engine (`memory_engine.py` v2.4.8)**: Persistent memory with pattern recognition and confidence scoring
- **Agent Router (`agent_router.py` v2.4.8)**: Routes tasks by capabilities and trust levels
- **Pattern Weaver (`pattern_weaver.py` v2.4.8)**: Discovers patterns through NLP clustering
- **Roundtable Executor (`roundtable_executor.py` v2.4.8)**: Manages multi-agent collaboration
- **Governance Framework (`pattern_governance.py` v2.4.8)**: Basic pattern validation and versioning

## Architecture Overview

IOA Core implements a memory-driven orchestration pattern:

1. **Input Processing**: Raw inputs are processed through the digestor module
2. **Memory Storage**: Structured entries are stored with confidence scoring
3. **Pattern Recognition**: The pattern weaver identifies recurring themes
4. **Agent Coordination**: The roundtable executor manages multi-agent workflows
5. **Governance**: Pattern governance ensures consistency and evolution

## Security and Trust Warnings

### 🚨 Development-Only Trust System

The trust signature system in IOA Core uses **example keys for development only**:
- Trust registry contains sample SHA-256 hashes
- No cryptographic verification is implemented
- Agent onboarding provides basic validation only

**For production use**, implement proper:
- Certificate-based authentication
- Hardware Security Modules (HSM)
- Multi-tenant isolation
- Comprehensive audit trails

See [SECURITY.md](SECURITY.md) for detailed security considerations.

### Agent Code Execution

IOA Core executes agent code without sandboxing. Only run trusted agents in development environments.

## Data Privacy and Compliance

### GDPR and Data Erasure

IOA Core includes basic data handling capabilities:

- **Data Portability**: Export memory entries in JSON format
- **Data Erasure**: `memory_engine.purge_entries()` provides basic deletion capability

**⚠️ Important**: The `purge_entries()` method is currently a stub implementation. For GDPR-compliant erasure, additional implementation is required:

```python
# Current stub - requires implementation for compliance
def purge_entries(self, criteria: Dict[str, Any]) -> int:
    """
    Purge memory entries matching criteria.
    
    WARNING: This is a stub implementation for development.
    GDPR-compliant erasure requires proper implementation.
    """
    raise NotImplementedError("GDPR erasure requires enterprise implementation")
```

For compliance with data protection regulations, contact [enterprise@orchintel.com](mailto:enterprise@orchintel.com).

## Testing

Run the test suite:

```bash
pytest tests/
```

For development with coverage:

```bash
pip install -e .[dev]
pytest tests/ --cov=src --cov-report=html
```

## Contributing

We welcome contributions! Please see:
- [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community standards
- [SECURITY.md](SECURITY.md) for security vulnerability reporting

Ways to contribute:
- Adding LLM adapters in `llm_adapter.py`
- Enhancing pattern definitions in `patterns.json`
- Improving documentation and examples
- Writing tests and fixing bugs

By contributing, you agree to license your work under Apache 2.0.

## Core vs. Enterprise

IOA Core is designed for:
- Development and evaluation
- Community collaboration
- Educational use
- Proof-of-concept implementations

IOA Enterprise adds:
- Production-grade security and compliance
- Advanced cognitive features (mood engine, enhanced NLP)
- Enterprise storage backends (cold storage, database integration)
- Professional support and SLA

See [FEATURE_MATRIX.md](FEATURE_MATRIX.md) for detailed comparison.

## Roadmap and Compliance Path

### Current Status
- ✅ Basic multi-agent orchestration
- ✅ Memory-driven pattern recognition
- ✅ Development-friendly setup
- ⚠️ Security features in development
- ⚠️ Compliance features require implementation

### Upcoming Releases
- **v2.5**: Enhanced security model, spaCy NLP integration, S3 storage adapters
- **v3.0**: Production-ready security, comprehensive compliance tools, web dashboard

### Compliance Roadmap
- **GDPR**: Complete data erasure and portability implementation
- **SOC2**: Audit trail and access control framework  
- **Industry Standards**: Healthcare (HIPAA), Financial (SOX) adapters

## Community and Support

### Community Resources
- **GitHub**: [ioa-project/ioa-core](https://github.com/ioa-project/ioa-core)
- **Discussions**: [GitHub Discussions](https://github.com/ioa-project/ioa-core/discussions)
- **Issues**: [Bug Reports and Feature Requests](https://github.com/ioa-project/ioa-core/issues)

### Enterprise Support
- **Email**: [enterprise@orchintel.com](mailto:enterprise@orchintel.com)
- **Security Issues**: [security@orchintel.com](mailto:security@orchintel.com)

## License

Apache 2.0 License. See [LICENSE](LICENSE) for full terms.

© 2025 OrchIntel Systems Ltd. IOA™ and OrchIntel™ are trademarks of OrchIntel Systems Ltd.

## Comparison with Other Frameworks

IOA Core differentiates from other multi-agent frameworks through:

- **Memory-Driven Architecture**: Persistent memory with pattern evolution vs. stateless chains
- **Governance Framework**: Built-in pattern validation and agent behavior rules
- **Modular Trust System**: Configurable agent trust and capability routing

For detailed comparisons with LangChain, CrewAI, and AutoGen, see our [framework comparison guide](docs/COMPARISON.md).

---

**Disclaimer**: IOA Core is beta software intended for development and evaluation. Production use requires careful security review and may benefit from enterprise features. The project makes no warranties about suitability for any particular purpose.
