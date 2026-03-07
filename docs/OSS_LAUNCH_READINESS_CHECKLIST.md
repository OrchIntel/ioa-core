# IOA Core OSS Launch Readiness Checklist

Date: 2026-03-07
Status: In progress

This checklist defines the bar IOA Core should meet before it is marketed broadly
as a polished stable open-source product.

## Broad-launch bar

All of the following should be true at the same time:

- the package version, README, changelog, docs, and badges agree
- the main README only documents implemented behavior
- installation and first-run paths work as written
- core examples run on supported Python versions
- core tests pass cleanly in CI
- the OSS boundary is clear and does not feel like an upsell wrapper
- one canonical demo shows policy, evidence, and audit outputs end to end

## Current strengths

- Evidence bundle implementation exists in `src/ioa_core/evidence/evidence_bundle.py`
- Immutable audit chain implementation exists in `src/ioa_core/governance/audit_chain.py`
- Working example scripts exist for workflow, roundtable, doctor, provider smoke test, and Ollama demo
- Click CLI entrypoint exists and basic commands like `--help` and `--version` run

## Current blockers

### Release truthfulness

- Release metadata is not fully aligned across the repo
- Current public versioning is still release-candidate shaped
- Some public surfaces previously implied stronger stability than the repo currently demonstrates

### Documentation honesty

- Primary docs contained roadmap and not-yet-implemented CLI examples
- OSS-facing docs still contain some commercial-boundary language that distracts from the open-source core

### Verification

- Targeted local pytest collection currently fails in this checkout
- Some tests still reference legacy import paths
- Supported-version verification needs to be demonstrated consistently in CI

### First-run polish

- A single canonical five-minute getting-started path needs to be the default experience
- Example outputs should be shown directly in the README or linked docs
- Live-provider setup should remain optional and clearly separated from offline examples

### Provenance and trust

- Model provenance support now exists in core evidence and audit paths, but it is not yet rolled out consistently across all producers
- Governance observability is still more implicit than visible

## Required work before broad stable marketing

1. Align release metadata
- choose and publish a stable version
- align package metadata, README title, changelog, docs site, and CLI version output

2. Fix public onboarding
- keep top-level README limited to verified commands
- move roadmap material into separate docs
- ensure install and quickstart paths are reproducible

3. Fix test and CI credibility
- make pytest collection pass on supported Python versions
- remove stale imports and dead tests
- expose CI status for install, examples, and core test matrix

4. Standardize evidence and audit provenance
- record provider and model identity consistently
- capture material inference settings and execution mode
- document the schema and example payloads

5. Clarify OSS positioning
- keep the public repo centered on the open-source core
- describe commercial extensions without making the OSS repo feel incomplete

## Recommended next implementation items

1. First-class model provenance in evidence bundles and audit events
2. A small governance observability surface for policy changes, review actions, and escalation events
3. A single architecture diagram showing IOA Core as the substrate for IOA Cloud and QIX frameworks

## Exit criteria

IOA Core is ready for broad polished stable OSS marketing when:

- `pip install` and repo quickstart both work as documented
- main examples pass and show expected outputs
- the README contains no speculative commands
- CI is green on supported Python versions
- release status is stable and consistently reflected everywhere
- the product story is clear in one sentence
