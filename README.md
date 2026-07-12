# IOA Core v2.9.0

[![PyPI version](https://img.shields.io/pypi/v/ioa-core.svg)](https://pypi.org/project/ioa-core/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10–3.12-brightgreen.svg)]()
[![Build](https://img.shields.io/github/actions/workflow/status/OrchIntel/ioa-core/build.yml?branch=main)](https://github.com/OrchIntel/ioa-core/actions/workflows/build.yml)
[![Docs](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://ioa.systems/docs)

IOA Core is an open-source governance kernel for AI workflows.

It focuses on policy enforcement, evidence capture, immutable audit trails,
memory-backed orchestration, and multi-model review patterns.

## Release Status

This checkout targets `ioa-core` v2.9.0. The release is held for the final
GATE0 checks before publication to [PyPI](https://pypi.org/project/ioa-core/).

The core governance primitives (audit chains, evidence bundles, policy enforcement, memory fabric, multi-model quorum) are real and production-tested. Some advanced CLI surfaces and deeper docs continue to evolve — see [docs/OSS_LAUNCH_READINESS_CHECKLIST.md](docs/OSS_LAUNCH_READINESS_CHECKLIST.md) for the current status.

## What Is In Scope

- hash-chained audit logging
- evidence bundle generation
- operator-provided Ed25519 evidence signatures with offline verification
- policy and system-law framing
- memory fabric primitives
- offline and live provider smoke testing
- local examples for governed workflow and quorum-style review

For the current public feature boundary, see [FEATURE_MATRIX.md](FEATURE_MATRIX.md).

## Quick Start

```bash
pip install ioa-core
```

Then clone the examples and run them:

```bash
git clone https://github.com/orchintel/ioa-core.git
cd ioa-core

# Check the CLI entrypoint
ioa --help

# Scaffold a minimal project
python examples/00_bootstrap/boot_project.py /tmp/ioa-core-demo-project

# Run a governed workflow example
python examples/10_workflows/run_workflow.py

# Run an offline multi-model roundtable example
python examples/20_roundtable/roundtable_quorum.py "Analyze this code for security issues (ok)"

# Check environment health
python examples/30_doctor/doctor_check.py

# Smoke test the provider layer in offline mode
IOA_PROVIDER=mock python examples/40_providers/provider_smoketest.py

# Run the Ollama turbo-mode demo
python examples/50_ollama/turbo_mode_demo.py turbo_cloud
```

Examples run offline by default unless you explicitly enable live mode and set
provider credentials.

**For development** (editable install with dev tools):

```bash
git clone https://github.com/orchintel/ioa-core.git
cd ioa-core
pip install -e ".[dev]"
```

## Example Outputs

Governed workflow example:

```json
{
  "task": "Analyze code for security issues",
  "policy": "demo-governed",
  "result": "OK",
  "evidence_id": "ev-0001",
  "audit_chain_verified": true,
  "system_laws_applied": ["Law 1", "Law 5", "Law 7"]
}
```

Roundtable example:

```json
{
  "quorum_approved": true,
  "approve_count": 3,
  "total_votes": 3,
  "evidence_id": "ev-rt-0001"
}
```

## Core Components

### Audit and Evidence

- immutable audit chain with hash continuity
- redaction support for sensitive values
- append-only JSONL logging with rotation and replay protection
- evidence bundle object for validations, metadata, and signatures

### Governance

- system-law framing for governed execution
- policy hooks and validation paths
- support for audit-linked governance events

### Provider and Review Layer

- multi-provider abstractions
- offline mock mode for repeatable examples
- provider smoke testing
- quorum-style review examples for multi-model workflows

### Memory

- memory fabric package with hot and persistent stores
- SQLite, S3, and local JSONL backends
- encryption support for memory storage

## Recommended Docs

- [docs/examples/QUICKSTART.md](docs/examples/QUICKSTART.md)
- [docs/examples/WORKFLOWS.md](docs/examples/WORKFLOWS.md)
- [docs/examples/ROUNDTABLE.md](docs/examples/ROUNDTABLE.md)
- [docs/examples/PROVIDERS.md](docs/examples/PROVIDERS.md)
- [docs/examples/OLLAMA.md](docs/examples/OLLAMA.md)
- [docs/evidence-signing.md](docs/evidence-signing.md)
- [docs/OSS_LAUNCH_READINESS_CHECKLIST.md](docs/OSS_LAUNCH_READINESS_CHECKLIST.md)

## Live Provider Usage

Live provider tests are optional and require real API keys.

```bash
export OPENAI_API_KEY=your-key
IOA_LIVE=1 IOA_PROVIDER=openai python examples/40_providers/provider_smoketest.py
```

If live keys are not configured, stay in offline mode and treat results as
simulation/demo outputs rather than provider validation.

## Current Gaps

Before positioning IOA Core as a polished stable OSS product, the project still
needs:

- aligned release metadata and version reporting
- removal of roadmap-style commands from deeper onboarding docs
- clean test collection and supported-version CI proof
- consistent model provenance rollout across evidence and audit-producing call sites
- clearer governance observability surfaces

## Why IOA Core Exists

Most AI orchestration stacks optimize for routing and output generation.

IOA Core is built around a different requirement: important AI workflows should
also emit policy context, evidence, and auditable traces that can be inspected
later.

That core substrate is intended to support higher-level OrchIntel products
without forcing each downstream product to reinvent governance separately.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow and
[SECURITY.md](SECURITY.md) for vulnerability reporting.
