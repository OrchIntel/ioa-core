**Version:** v2.5.0  
**Last-Updated:** 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Where Things Live - IOA Core Internal

This document provides an overview of the repository structure and where different components are located.

## Repository Overview

**IOA Core Internal** - Complete internal version with full history, operations reports, and enterprise features.

## Core Components

### Source Code
- **`src/`** - Main source code directory
  - `src/ioa/` - Core IOA modules
  - `src/llm_providers/` - LLM provider integrations
  - `src/memory/` - Memory management
  - `src/governance/` - Governance and compliance
  - `src/audit/` - Audit logging and verification

### Testing
- **`tests/`** - Complete test suite
  - `tests/unit/` - Unit tests
  - `tests/integration/` - Integration tests
  - `tests/smoke/` - Smoke tests
  - `tests/performance/` - Performance tests

### Documentation
- **`docs/`** - Complete documentation
  - `docs/getting-started/` - Quickstart guides
  - `docs/api/` - API documentation
  - `docs/tutorials/` - Tutorials and examples
  - `docs/ops/` - Operations documentation

### Operations
- **`ops/`** - Operations and reports
  - `ops/reports/` - Status reports and dispatches
  - `ops/qa/` - Quality assurance reports
  - `ops/qa_archive/` - Archived QA reports

### Configuration
- **`config/`** - Configuration files
  - `config/governance/` - Governance configurations
  - `config/lexicons/` - Lexicon definitions

### Tools
- **`tools/`** - Development and operational tools
  - `tools/inventory/` - Repository inventory tools
  - `tools/ci/` - CI/CD tools
  - `tools/gov_audit/` - Governance audit tools

### Compliance
- **`cartridges/`** - Compliance cartridges
  - `cartridges/eu-aia/` - EU AI Act compliance
  - `cartridges/gdpr/` - GDPR compliance

## Key Features

- **Complete History**: Full git history preserved from original monorepo
- **Internal Operations**: All operations reports and dispatches
- **Enterprise Features**: Advanced governance and compliance modules
- **Development Tools**: Complete suite of development and operational tools
- **Audit Trails**: Complete audit and compliance tracking

## Related Repositories

- **`ioa-core`** - Public OSS version (clean baseline)
- **`ioa-enterprise`** - Enterprise extensions and features
- **`ioa-saas`** - SaaS control plane and infrastructure
- **`ioa-cert-service`** - Certification and compliance service
- **`ioa-examples`** - Examples and tutorials
- **`ioa-websites`** - Marketing and documentation websites
- **`ioa-docs-site`** - Documentation site source

## Getting Started

> **Note**: Some commands below are examples for future functionality.

```bash
# Clone the repository
git clone https://github.com/OrchIntel/ioa-core-internal.git

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Check system health
# Example (not currently implemented): ioa doctor
```

## Support

For questions about the repository structure or components, contact the IOA Operations team.
