**Version:** v2.16.0  
**Last-Updated:** 2026-10-14

# Changelog
## [2.16.0] - 2026-10-14
### Added
- `ioa_core.health.policy` (evaluation only): versioned action policies with a definition fingerprint that excludes status and approval. `required_actions()` gives one requirement per occurrence group; `summary_by_gate()` is for presentation only. `require_live_approval()` refuses any policy that is not `approved`. The packaged default (`qixmind_default`, `2026.10.1-draft`) is a draft.
- `ioa_core.health.provenance.capture_session_provenance()`: profile id and definition fingerprint, live gate detector versions and ruleset fingerprint, the action policy applied (or that none was), and optionally the findings detector.
- `create_session_receipt(..., provenance=...)`: optional `metadata.provenance` block, validated, captured by the runtime only. Receipts without it are unchanged, and receipts with it verify with earlier verifiers. See `docs/qixmind/session-provenance.md`.
- `profile_definition_fingerprint()`, `canonical_fingerprint()` and `content_gates.ruleset_fingerprint()`.
### Changed
- Findings detector 0.2.0, frozen for held-out evaluation (`tests/health/fixtures/gate_eval/FREEZE.json`). Each finding keeps every distinct source, context and lexicon rule as `occurrences` (rule ids, never text); the headline fields are a summary. Reports carry `ruleset_sha256`. The 43-case set is now development data.

## [2.15.0] - 2026-10-14
### Added
- `ioa_core.health.findings` (evaluation only, not used by the live gates): `detect_findings()` reports one finding per declared gate with its sources (input, output or both), a context (`affirmed`, `uncertain`, `historical`, `third_person`, `negated`), whether an input finding was omitted from the output, and the review-output status. Nothing is cleared automatically: a negated or historical signal is still a finding, and anything the rules cannot classify is `uncertain`. No matched text is kept.
- Evaluation-only lexicon additions in `ioa_core/health/lexicons/eval/` (status `pending_clinical_review`) for indirect, colloquial and youth phrasing and imminence cues. The live lexicons are unchanged.
- `scripts/eval_gates.py` and a synthetic case set (`tests/health/fixtures/gate_eval/cases.json`, 43 cases, labels pending clinician adjudication) comparing the live gates, the live lexicons also run on the input, and the findings detector.

## [2.14.0] - 2026-10-14
### Added
- `assess_review_output()` and `ReviewOutputAssessment` classify an output as a produced review, empty, or a refusal (detector version 2026.10.1). Refusal wording counts only near the start of an output that has almost no review structure, so a full review that says it cannot diagnose is still a review. No output text is kept.
- `ContentGateEvaluator.evaluate(..., require_review_output=True)` holds an empty or refused output (`overall_action == "hold"`) and records the reason in the new `ContentGateReport.review_output`, while still recording every gate result. Previously a model refusal produced no gate signal, so it was reported as "pass" and could be signed off. The check is off unless requested, so existing callers are unchanged.

## [2.13.0] - 2026-10-13
### Changed
- Adult mental health profiles (`mental_health_nz`, `mental_health_au`) now gate `crisis_risk_to_self` and `risk_to_others` as well as `crisis_mandatory_reporting`, all at escalate severity, with a 24 hour escalation follow-up. Previously only crisis and mandatory reporting was gated (at the default acknowledge severity) and no follow-up deadline applied, so an adult session with risk-to-self language created no acknowledgement or follow-up obligation. `child_protection` remains youth only. Consent settings are unchanged.

## [2.12.1] - 2026-10-13
### Fixed
- Layered jurisdiction templates are now limited to the profile's care setting. `JurisdictionTemplate.care_settings` (empty means every care setting) scopes the Aged Care Act to aged care and each Mental Health Act (eight Australian states and territories, and the New Zealand 2026 transition) to mental health and youth mental health. `resolve_template_ids` and `build_health_session_context` skip templates that do not apply, so a youth mental health session no longer lists the Aged Care Act and a dental clinic no longer lists a Mental Health Act. `for_jurisdiction` and resolution without a profile are unchanged.

## [2.12.0] - 2026-10-13
### Added
- State-level jurisdictions for health profiles: `JurisdictionTemplateRegistry.for_jurisdiction(code, layered=True)` layers national templates under a sub-national code such as `AU-NSW`; `resolve_template_ids` and `build_health_session_context` use the layered lookup for the patient jurisdiction; `recommend()` falls back by country so an Australian state never resolves to an NZ profile; `SubcategoryContextProfile.supported_sub_jurisdictions`; `AU_STATE_CODES`, `GATE_JURISDICTION_TEMPLATES`, `gate_jurisdiction_text()`.
- 25 jurisdiction templates: child protection reporting, Mental Health Act boundaries and health privacy statutes for each Australian state and territory (NSW, VIC, QLD, WA, SA, TAS, ACT, NT), the Privacy Act automated decision-making transparency notice (effective 2026-12-10), and for New Zealand the Mental Health Act 2026 transition, Oranga Tamariki Act s 15, the Medical Council of New Zealand AI guidance (March 2026) and the Health New Zealand AI Pre-Implementation Evaluation Framework. Templates now carry `summary` (<= 300 chars) and `review_status`; the Australian state texts are `draft_pending_legal_review`.
- `healthcare-nz` policy pack (`system_laws_nz_health.json`, pack id `qix_health_nz`); `mental_health_nz` and `youth_mental_health_nz` now select it. A test fails CI when any bundled manifest is within 30 days of expiry.
- Session Evidence Receipt (schema unchanged, `qixmind.session-evidence-receipt.v1`): optional `episode`, `care_event`, `inference`, `withheld`, `review_state` and `disclosure` blocks with closed enumerations, emitted only when supplied; `session.jurisdiction` may be a structured block (`code`, `country`, `state`, `templates_shown` ids, `policy_pack`); `session.policy_pack`. Identifier-shaped episode ids and template text in `templates_shown` are rejected; `inference.category` values `triage_suggestion` and `diagnosis` are rejected in v1.

### Changed
- `youth_mental_health_au` and `mental_health_au` declare the eight Australian sub-jurisdictions and the ADM transparency template; the "untested" note is gone. The `child_protection` gate description is jurisdiction-neutral; the applicable state or NZ text comes from the templates.

## [2.11.0] - 2026-10-13
### Fixed
- Convergence release: the OP-14, OP-40 and OP-60 fixes that production QiXChat carried as a patched vendor tree (`2.6.2+op60`) are now on `main`, so every runtime can vendor a tagged release.
- Renewed the bundled System Laws manifest (`system_laws.json`): laws and policy unchanged, term 2026-10-04 to 2027-10-04. The previous term ended 2026-09-03, after which `PolicyEngine()` raised at startup and dependent governance checks stopped. A new test fails 60 days before any bundled manifest expires. The manifest signature remains the development placeholder; production signing is not yet in place.
- PrivacyDetector (`ioa.governance.detectors.privacy_presidio`) no longer reports a missing or placeholder Presidio engine as available. The analyzer is required to check text; a missing anonymizer yields `action_taken="mask_unavailable"` with `masking_error` instead of returning raw text as masked. Results and evidence carry a `status` (`checked`, `unavailable`, `error`, `disabled`) and `has_pii` is None when the text was not checked. Strict mode fails closed when the detector cannot check. `PIIDetector.detect_pii` returns `status`, `checked`, `should_block` and `pii_detected=None` when unchecked; `get_status()` added. New optional extra `privacy` (presidio-analyzer, presidio-anonymizer). Production incident 2026-10-04: the QiXChat image lacked presidio_anonymizer and every privacy check was recorded as "no PII".
- Memory Fabric search applies scope filters before the result limit. `MemoryFabric.search` and `SQLiteStore.search` accept `metadata_filter` (exact match, `{"$ne": v}` to exclude), `tags` (any match) and `order` (`relevance` or `recent`), evaluated in SQL ahead of `LIMIT`; an empty query returns rows by filters alone. Previously the SDK fetched `limit` rows globally and filtered afterwards, so other principals' records could crowd a caller's eligible records out of the candidate set (OP-60). Stores without pushdown are searched with a wider window and filtered in the fabric.
- Presidio analyzer is shared across runtime checks (`get_shared_analyzer`), so repeated privacy checks do not rebuild the NLP engine.
## [2.10.0] - 2026-10-13
### Added
- Health content gates are now enforceable: `ioa_core.health.content_gates` (`ContentGateEvaluator`, `GateResult`, `ContentGateReport`, `fail_closed_report`) screens model output against packaged lexicons, fails closed, and records gate name, severity and category only (never matched text).
- Packaged lexicons under `ioa_core.health.lexicons` (`crisis_risk_to_self`, `risk_to_others`, `child_protection`, `crisis_mandatory_reporting`), synthetic clinical-register phrasing, versioned for auditability.
- Health profiles `youth_mental_health_nz` and `youth_mental_health_au` (guardian consent, elevated de-identification, four escalate gates, 24 hour escalation follow-up). `SubcategoryContextProfile` gains `content_gate_policy`, `escalation_follow_up_hours`, `policy_pack_note`, `jurisdiction_notes`; `gate_severity_for()`.
- `ioa_core.health.follow_up`: deadline arithmetic, open/closed/overdue state and `FollowUpObligation.to_receipt_dict()`.
- `ioa_core.evidence.session_receipt`: the QiXMind Session Evidence Receipt (`qixmind.session-evidence-receipt.v1`), a signed evidence bundle that records what the model saw (hash), which gates fired, who acknowledged (by role) and whether escalation follow-up was confirmed in time. Hash-only, never emitted unsigned, verifiable offline with `ioa verify`, with a key registry (`qixmind.session-evidence-key-registry.v1`) and `QIXMIND_EVIDENCE_*` environment names.
- `EvidenceBundle.generate_signature()` accepts `private_key_pem`.

### Fixed
- `VERSION` file (2.7.0) now matches the package version.

### Known issues
- No NZ-specific policy pack exists; `mental_health_nz` and `youth_mental_health_nz` select `healthcare-au` and carry NZ obligations through jurisdiction templates.
- `SafetyDetector` resolves lexicons from `configs/lexicons/` relative to the repository, which is unusable from an installed wheel; the content gate evaluator does not depend on it.
- Several legacy test modules fail collection with `NameError: TaskMessage` (pre-existing, unrelated to this release).

## [Unreleased]
### Added
- CI Remediation v1: profile-aware workflows (monitor PRs, release RC full), provider smoketest stub, docs hardening, assurance artifacts, audit CLI fixes, sustainability mock, detect-secrets PR-fast.
- AU healthcare policy pack manifest and policy-pack selection via `IOA_POLICY_PACK` / `IOA_LAWS_POLICY_PACK`.
- Governance manifest loader now supports policy-pack-specific manifest selection.

### Security
- Secret detection: PR incremental scan; nightly full scan remains available.


All notable changes to IOA Core will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.6.0-rc.1] - 2025-01-11

### Added
- **Memory Fabric Architecture**: Complete modular memory management system with scalable components
- **DocSync Integration**: Document synchronization capabilities for distributed memory operations
- **Memory Fabric CLI**: New `ioa fabric` commands for memory management and health checks
- **Memory Stores**: Support for SQLite, Local JSONL, and S3 storage backends
- **Memory Crypto**: Encryption and security features for memory data
- **Memory Metrics**: Comprehensive metrics and monitoring for memory operations
- **Backward Compatibility**: Legacy memory engine shim for smooth migration
- **Hygiene Workflow**: Automated code quality checks and validation
- **Memory Documentation**: Complete API documentation and migration guides

### Changed
- **Memory Engine**: Migrated to Memory Fabric architecture with improved scalability
- **CLI Commands**: Enhanced memory commands with fabric-specific operations
- **Test Coverage**: Comprehensive test suite for memory fabric components
- **Import Paths**: Updated to use memory_fabric instead of legacy memory_engine
- **Directory Structure**: Reorganized apps/command-deck to apps/command_deck for Python compatibility

### Deprecated
- **Legacy Memory Engine**: `ioa.core.memory_engine` marked for removal in v2.7
- **Memory Commands**: `ioa memory doctor` deprecated in favor of `ioa fabric doctor`

## [2.5.0-rc3] - 2025-01-06

### Added
- **Complete System Laws Validation**: Validated all 7 System Laws with comprehensive testing and audit chain integrity verification
- **Sustainability Evidence Integration**: Full Law 7 implementation with graduated thresholds, jurisdiction overrides, and model fallback handling
- **Governance Validation Suite**: Complete test coverage for all System Laws including sustainability scenarios
- **Audit Chain Integrity**: Verified hash chain integrity across all governance test entries

### Changed
- **System Laws Documentation**: Updated with complete validation results and evidence paths
- **Master Execution Ledger**: Updated with DISPATCH-GOV-20250904-VALIDATION completion
- **Dispatch Ledger**: Added comprehensive governance validation metadata

## [2.5.0-rc1] - 2025-01-06

### Added
- **System Law 7 - Sustainability Stewardship**: Added energy budgeting and carbon tracking with jurisdiction overrides
- **Sustainability Module**: Complete sustainability management system with energy calculation and budget enforcement
- **Enhanced Audit Logging**: Sustainability-specific audit events with evidence fields
- **Governance Configuration**: Added governance_config.json with sustainability settings
- **xAI Provider Support**: Added xAI provider to doctor and smoketest commands
- **Environment Configuration**: Updated .env.local.example with XAI_API_KEY
- **CLI Documentation Validation**: 100% success rate on implemented commands

### Changed
- **System Laws Documentation**: Updated SYSTEM_LAWS.md with Law 7 specifications and examples
- **Governance Validation Tests**: Added sustainability pass/fail/override test cases
- **CLI Commands**: Enhanced doctor and smoketest to include xAI provider
- **Documentation**: Updated provider tables and environment examples

## [2.5.0] - 2025-08-19

### Added
- **Governance & Audit Chain**: Complete audit logging system with redaction and rotation
- **PKI Integration**: Signature engine for agent trust verification
- **Zero-Retention Flags**: Provider-level data retention controls
- **Multi-Provider Support**: OpenAI, Anthropic, Gemini, DeepSeek, XAI, Ollama
- **Roundtable Executor**: Consensus-based task orchestration with voting mechanisms
- **Workflow DSL**: YAML-based workflow definition and execution
- **Memory Engine**: Hot/cold storage with intelligent pruning and persistence
- **CLI Interface**: Comprehensive command-line interface with onboarding tools

### Changed
- **Repository Structure**: Reorganized for better OSS readiness and developer experience
- **Documentation**: Complete overhaul with tutorials, quickstarts, and API reference
- **Testing**: Enhanced test suite with performance gates and integration tests
- **Security**: Enhanced audit logging with token redaction and size-based rotation

### Fixed
- **Cold Storage**: Archive-before-delete logic and structured logging
- **Agent Router**: Task routing and governance integration
- **Schema Validation**: Runtime schema validation across all modules
- **Performance**: 100k test harness with ~16.7s runtime and >=0.95 success ratio

### Security
- **Audit Hardening**: Token redaction, email masking, and audit log rotation
- **Zero-Retention**: Provider-level data retention controls
- **Trust Verification**: PKI-based agent onboarding and verification

## [2.4.0] - 2025-08-15

### Added
- Basic memory engine with hot/cold storage
- Agent routing framework
- CLI interface foundation

### Changed
- Initial modular architecture
- Basic governance mechanisms

## [2.3.0] - 2025-08-10

### Added
- Core orchestration loop
- Basic agent management
- Configuration system

## [2.2.0] - 2025-08-05

### Added
- Cold storage implementation
- Basic CLI commands
- Configuration templates

## [2.1.0] - 2025-08-01

### Added
- Initial project structure
- Basic agent framework
- Test infrastructure

## [2.0.0] - 2025-07-25

### Added
- Project initialization
- Basic architecture design
- Development environment setup
