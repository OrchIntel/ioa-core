# Frequently Asked Questions (FAQ)

**Version:** 2.5.1  
**Last Updated:** 2025-10-10

---

## 1. General Concepts

### What is IOA Core?

IOA Core is an **open-source framework for governed AI orchestration**. It provides:
- Multi-provider LLM integration (OpenAI, Anthropic, Google, DeepSeek, XAI, Ollama)
- Immutable audit logging with cryptographic verification
- Memory fabric with hot/cold storage
- Vendor-neutral multi-agent consensus (quorum voting)
- Governance policies for compliant AI workflows

### What does "Governance-as-a-Service" mean?

It means IOA Core automatically enforces policies, logs evidence, and verifies compliance as workflows execute — without manual intervention. Every decision is auditable and traceable.

### What is an Audit Chain?

An **audit chain** is an immutable log of governance events stored locally with:
- Cryptographic hashing (each entry references the previous hash)
- Sequence numbers for ordering
- Evidence IDs linking to workflow executions
- Verification capability to detect tampering

See [test_audit_chain.py](../tests/feature_sync/test_audit_chain.py) for proof.

### What are the "Seven System Laws"?

IOA Core's governance framework is built on seven principles:
1. **Transparency** - All operations are logged
2. **Auditability** - Logs are immutable and verifiable
3. **Consent** - User control over data
4. **Purpose Limitation** - Data used only for stated purposes
5. **Quorum** - Multi-agent consensus for critical decisions
6. **Evidence** - Every decision generates audit evidence
7. **Review** - Human oversight of AI decisions

---

## 2. Usage & Setup

### How do I install on Windows/macOS/Linux?

See our **[Beginner Quick Start](QUICKSTART_BEGINNER.md)** for step-by-step platform-specific instructions.

**Quick version**:
```bash
# Create virtual environment
python3 -m venv ioa-env
source ioa-env/bin/activate  # Windows: ioa-env\Scripts\activate

# Install
pip install ioa-core
```

### Do I need an API key to use IOA Core?

**No!** All examples run offline by default with mock providers. You only need API keys if you want to:
- Test with real LLM providers
- Build production workflows

See [PROVIDERS.md](examples/PROVIDERS.md) for setup instructions.

### What are the system requirements?

**Minimum**:
- Python 3.10 or higher
- 512 MB RAM
- 100 MB disk space (install only)

**Recommended**:
- Python 3.11+
- 2 GB RAM
- 500 MB disk space (includes examples + tests)

**Supported OS**:
- macOS 10.15+
- Linux (Ubuntu 20.04+, Fedora 35+, Debian 11+)
- Windows 10/11 (or WSL)

### How do I reset configuration?

```bash
# Remove cache directory
rm -rf ~/.ioa/cache

# Remove any project-specific config
rm -rf my-project/ioa.yaml
```

### Can I use IOA Core in production?

**Yes**, for the features marked ✅ in [FEATURE_MATRIX.md](../FEATURE_MATRIX.md):
- Audit logging
- Memory fabric
- LLM provider integration
- Multi-agent quorum

Features marked ⚠️ **Preview** (like 4D Tiering) are educational only.

---

## 3. Development

### How can I contribute code or docs?

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/my-improvement`
3. **Make changes** with tests
4. **Submit PR** with description

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.

### Where do I report bugs?

**GitHub Issues**: https://github.com/orchintel/ioa-core/issues

Use the bug report template and include:
- IOA Core version (`2.5.1`)
- Python version
- OS
- Steps to reproduce
- Expected vs actual behavior

### How do I run tests?

```bash
# Run all tests
pytest -q

# Run specific test suite
python tests/examples/test_workflow.py

# Run with coverage
pytest --cov=ioa_core tests/
```

All tests should pass ✅ before submitting a PR.

### Can I add new LLM providers?

**Yes!** Follow the provider adapter pattern in `src/ioa_core/llm_providers/`. Submit a PR with:
- Provider adapter class
- Smoke test
- Documentation update

---

## 4. Feature Clarifications

### What is Quorum?

**Quorum** is a decision-making mechanism requiring consensus from multiple AI models. For example:
- 3 models vote on a task
- 2-of-3 agreement required (strong quorum)
- Prevents single-model bias

See [roundtable example](../examples/20_roundtable/) for a working demo.

### What are 4D Tiers?

**4D Tiering** is an educational preview of multi-dimensional memory organization:
- **Time**: When was the data created/accessed?
- **Context**: What workflow or task does it relate to?
- **Source**: Which provider or agent generated it?
- **Priority**: How important is it?

Currently marked **Preview** (not production-ready).

### What is Ollama Turbo mode?

**Ollama Turbo** optimizes local model inference for speed:
- Reduced context window → faster processing
- Lower temperature → more deterministic
- Optimized batch sizes → better throughput

Expected improvement: **20-40%** latency reduction (hardware dependent).

See [turbo demo](../examples/50_ollama/) for benchmark.

### Why are some features marked "Preview"?

**Preview** features are:
- ✅ Available in the codebase
- ✅ Suitable for learning/experimentation
- ❌ Not recommended for production
- ⚠️ API may change

Example: 4D Tiering is educational only.

### What's the difference between OSS and Restricted Edition?

**OSS (Open Source)**:
- Core orchestration engine
- 6 LLM providers
- Basic audit & governance
- Educational compliance frameworks

**Restricted Edition** (Commercial):
- Visual workflow builder
- Full HIPAA, SOX, GDPR tooling
- Enterprise analytics
- Multi-region replication

See [FEATURE_MATRIX.md](../FEATURE_MATRIX.md) for complete comparison.

---

## 5. Licensing

### What license is IOA Core under?

**Apache License 2.0**

You can:
- ✅ Use commercially
- ✅ Modify the code
- ✅ Distribute
- ✅ Sublicense

You must:
- 📄 Include the license and copyright notice
- 📄 State changes made

You cannot:
- ❌ Hold authors liable
- ❌ Use trademarks without permission

### Do I need to attribute IOA Core?

**In source code**: Keep the SPDX header:
```python
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
```

**In documentation**: Link to the repository:
```
Powered by IOA Core: https://github.com/orchintel/ioa-core
```

### Can I sell products built with IOA Core?

**Yes!** Apache 2.0 permits commercial use. You can build and sell products using IOA Core without paying royalties.

---

## 6. Performance & Scaling

### How fast is IOA Core?

**Examples** (offline, no API calls):
- Bootstrap: <1s
- Workflow execution: <1s
- Quorum voting: <1s
- Doctor check: <1s

**With real providers**: Depends on LLM response time (typically 2-10s).

### Can I use multiple providers simultaneously?

**Yes!** The quorum/roundtable feature runs multiple providers in parallel for consensus voting.

See [roundtable example](../examples/20_roundtable/).

### What's the maximum data IOA Core can handle?

**Memory Fabric**:
- Hot storage: Limited by RAM
- Cold storage: Limited by disk (tested with 10+ GB)

**Audit logs**: Tested with 100,000+ entries.

---

## 7. Security & Privacy

### Is my data sent to external services?

**By default, NO**. Examples run offline with mock providers.

**With real providers**: Data is sent only when:
- You configure API keys
- You enable live mode (`IOA_LIVE=1`)
- You explicitly call provider APIs

### Does IOA Core store API keys?

**No.** API keys are read from environment variables only. They are never stored in files or logs.

### What data is in audit logs?

Audit logs contain:
- Timestamp
- Event type (workflow execution, provider call, etc.)
- Evidence ID
- Redacted inputs/outputs (sensitive data masked)
- Hash of previous entry

**Sensitive data is automatically redacted** before logging.

---

## 8. Troubleshooting

### Examples fail with "Module not found"

**Solution**:
```bash
# Make sure virtual environment is activated
source ioa-env/bin/activate  # Windows: ioa-env\Scripts\activate

# Reinstall
pip install ioa-core
```

### "Python version too old" error

**Solution**: IOA Core requires Python 3.10+. Upgrade:
- macOS: `brew install python@3.10`
- Linux: `sudo apt install python3.10`
- Windows: Download from https://www.python.org/

### Tests fail on Windows

**Common causes**:
- Path separators (`\` vs `/`)
- Line endings (CRLF vs LF)

**Solution**: Use WSL (Windows Subsystem for Linux) for best compatibility.

### "Permission denied" errors

**Solution**:
- Don't use `sudo` with pip in virtual environments
- Check file permissions: `chmod +x script.py`

---

## 9. Contributing & Community

### How do I stay updated?

- **GitHub Releases**: https://github.com/orchintel/ioa-core/releases
- **Discussions**: https://github.com/orchintel/ioa-core/discussions
- **Issues**: https://github.com/orchintel/ioa-core/issues

### Can I request features?

**Yes!** Open a GitHub issue with:
- **Use case**: What problem does it solve?
- **Proposal**: How should it work?
- **Alternatives**: What have you tried?

### How do I get help?

1. Check this FAQ
2. Read the [Glossary](REFERENCE_GLOSSARY.md)
3. Search [GitHub Issues](https://github.com/orchintel/ioa-core/issues)
4. Ask in [Discussions](https://github.com/orchintel/ioa-core/discussions)
5. Open a new issue

---

## 10. Advanced Topics

### Can I extend IOA Core?

**Yes!** IOA Core is designed for extensibility:
- Add custom providers
- Create new governance policies
- Build custom memory backends
- Extend the CLI

### Does IOA Core support Docker?

**Not officially packaged yet**, but you can create a Dockerfile:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["python", "examples/30_doctor/doctor_check.py"]
```

### Can I use IOA Core with Kubernetes?

**Yes**, as a standard Python application. No special considerations needed.

---

## Still Have Questions?

- **📘 Glossary**: [REFERENCE_GLOSSARY.md](REFERENCE_GLOSSARY.md)
- **🚀 Quick Start**: [QUICKSTART_BEGINNER.md](QUICKSTART_BEGINNER.md)
- **🤝 Contributing**: [CONTRIBUTING.md](../CONTRIBUTING.md)
- **🔒 Security**: [SECURITY.md](../SECURITY.md)
- **💬 Discussions**: https://github.com/orchintel/ioa-core/discussions

---

**Last Updated:** 2025-10-10  
**Maintained By:** IOA Core Team

