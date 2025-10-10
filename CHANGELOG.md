**Version:** v2.5.0  
**Last-Updated:** 2025-10-09

# Changelog
## [Unreleased]
### Added
- CI Remediation v1: profile-aware workflows (monitor PRs, release RC full), provider smoketest stub, docs hardening, assurance artifacts, audit CLI fixes, sustainability mock, detect-secrets PR-fast.

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
