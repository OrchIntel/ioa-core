**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->


# Assurance Score v1 (Canonical Spec)

This document defines the Assurance Score for IOA Core. It replaces prior “assurance” terminology to align with auditor‑friendly, evidence‑first reporting.

## Purpose

- Evidence‑backed readiness score surfaced in CLI and CI Gates
- Auditor‑friendly rubric; never hand‑edited

## Formula v1

- Dimensions per law (0–4):
  - Code enforcement present (per Law)
  - Tests + harness coverage
  - Runtime evidence (CI gates artifacts)
  - Documentation accuracy (CLI/doc drift = 0)
- Weights (configurable via `.ioa/assurance.yml`, defaults equal 0.25 each)
- Per‑law weighted sum scaled to 0–15
- Aggregation: Law mean → Domain mean (Governance, Security, Docs) → Overall 0–15

Per‑Law rubric: 0 (none) / 1 (hooks) / 2 (baseline) / 3 (provable) / 4 (provable + stress)

## Evidence Sources (v1)

- Governance: `artifacts/lens/ethics/metrics.jsonl`, `artifacts/lens/sustainability/metrics.jsonl`, `artifacts/harness/governance/metrics.jsonl`
- Security: Bandit/TruffleHog JSON (via CI) at `artifacts/security/*.json`
- Docs: CLI drift validator outputs at `artifacts/lens/docs/cli_drift.json`

## Configuration

`.ioa/assurance.yml`:

```yaml
weights:
  code: 0.25
  tests: 0.25
  runtime: 0.25
  docs: 0.25
thresholds:
  pass_overall: 10
  warn_overall: 8
```

If the file is missing, defaults above are applied.

## CLI

> **Note**: Some commands below are examples for future functionality.

```bash
# Example (not currently implemented): ioa assurance doctor
# Example (not currently implemented): ioa assurance compute --write
# Example (not currently implemented): ioa assurance report --format md|json
```

## CI Gates Integration (monitor mode)

- After governance/security/docs gates:

> **Note**: Some commands below are examples for future functionality.

```bash
# Example (not currently implemented): ioa assurance compute --write
# Example (not currently implemented): ioa assurance report --format md
```

- Artifacts: `artifacts/lens/assurance/{summary.json,timeseries.jsonl}`
- PR comment includes “Assurance Score: X/15”

## Roadmap

- Score improves as evidence grows; never hand‑edited
- Strict mode may block if overall < threshold


