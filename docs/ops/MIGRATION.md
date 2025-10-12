**Version:** v2.5.0  
**Last-Updated:** 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# IOA Core Internal - Migration Log

**Date**: 2025-09-28  
**Source**: Legacy IOA monorepo  
**Target**: IOA-Core-Internal (staging for OSS Core)

## Repository Structure

This repository follows the canonical OSS Core structure as recommended by ChatGPT's analysis:

```
/kernel/                     # Policy engine, interceptors, audit/event APIs
/adapters/                   # Open providers (OpenAI/Bedrock/Vertex/HTTP/Kafka, etc.)
/cartridges/baseline/        # Minimal/open reference policies (no proprietary mappings)
/laws/                       # Laws 1–7 reference + executable examples
/cli/                        # ioa CLI (bootstrap, run, test, score)
/sdk/{ts,py}/               # Language SDKs (TypeScript, Python)
/specs/                      # Schemas (policy/evidence/audit/assurance-score schema)
/examples/                   # Small, runnable examples & notebooks
/tests/                      # Unit + conformance (open subset)
/docs/                       # OSS docs (Getting Started, Architecture, Laws)
```

## Migration Mapping

| Source Path | Destination | Rationale |
|-------------|-------------|-----------|
| `src/ioa/` | `/kernel/` | Core policy engine and governance kernel |
| `src/` | `/adapters/` | Provider adapters and integrations |
| `cartridges/` | `/cartridges/baseline/` | OSS baseline cartridges only |
| `ioa_cli.py` | `/cli/` | Command-line interface |
| `schemas/` | `/specs/` | Public schemas and specifications |
| `examples/` | `/examples/` | Runnable examples and tutorials |
| `tests/` | `/tests/` | Unit and conformance tests |
| `docs/` | `/docs/` | OSS documentation |

## What Was Excluded (Moved to Enterprise)

- Enterprise cartridges (GDPR/HIPAA/SOC2/ISO27001/CCPA/HITRUST/EU AI Act/NIST AI RMF/ISO 42001)
- Enterprise UI, auditor portals, Assurance Score server implementation
- SSO/SAML/OIDC, multi-tenant controls, observability pipelines
- Deployment blueprints (Terraform/Helm/SAM/CDK)
- Cloud keys/secrets, SES/email code, infrastructure lambdas
- Marketing sites, design system assets
- MAS runbooks/evidence exporters

## Next Steps

1. **Development**: Continue work in this repository
2. **Release Preparation**: When ready for OSS launch, mirror content to `ioa-core`
3. **Versioning**: Use semantic versioning for releases
4. **CI/CD**: Ensure only public CI (lint+test) - no cloud deploy jobs

## Compliance

This repository structure follows:
- **Law 1 (Compliance Supremacy)**: Policy precedence and runtime enforcement in Core
- **OSS Best Practices**: Clean separation of concerns
- **Industry Standards**: Professional repository organization
- **ChatGPT Recommendations**: Canonical structure for OSS projects

## Related Repositories

- **ioa-core**: Public OSS mirror (created but not populated yet)
- **ioa-enterprise**: Enterprise features and commercial components
- **ioa-websites**: All three public sites (orchintel.com, ioa.systems, ioaproject.org)
- **ioa-design-system**: Tokens, themes, and components
- **ioa-web-infra**: Infrastructure glue (contact/newsletter/API)