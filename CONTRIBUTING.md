**Version:** v2.5.0  
**Last-Updated:** 2025-10-09

# Contributing to IOA Core

Thank you for your interest in contributing to IOA Core!  We welcome contributions from the community and appreciate your efforts to improve the project.

## How to Contribute

1. **Fork the repository.**  Create your own fork of the IOA Core repository and clone it locally.
2. **Create a branch.**  Use a descriptive branch name based on the change you are making, such as `feature/agent-router-improvements` or `bugfix/kpi-monitor-path`.
3. **Make your changes.**  Keep your changes focused and adhere to the existing code style.  Include tests where appropriate.
4. **Sign your work.**  By submitting a contribution you certify that you have the right to grant a licence for your contribution.  See the Developer Certificate of Origin (DCO) for details.
5. **Submit a pull request.**  Push your branch to your fork and open a pull request against the `main` branch of the IOA Core repository.  Provide a clear description of your changes and reference any related issues.
6. **Respond to feedback.**  Project maintainers may request changes or clarifications.  Please respond promptly to review comments to help us merge your contribution.

## Contribution Policy & Boundaries

### ✅ Encouraged Contributions

We welcome the following types of contributions:

- **Bug fixes** - Fixes for reproducible issues
- **Tests** - Unit tests, integration tests, proof tests
- **Documentation** - Tutorials, examples, guides, FAQ entries
- **OSS Features** - Features that don't imply regulatory compliance claims
- **Performance improvements** - Optimizations with benchmarks
- **Developer experience** - CLI improvements, error messages, tooling

### ⚠️ Requires Discussion First

Please open an issue for discussion before working on:

- **New modules** - Major architectural changes
- **Breaking changes** - API modifications affecting existing code
- **New dependencies** - Additional third-party packages
- **Major refactors** - Large-scale code restructuring

### ❌ Not Accepted

The following contributions cannot be merged into OSS:

- **Regulated framework implementations** - Full HIPAA, SOX, GDPR, CCPA compliance logic (educational stubs only)
- **Compliance guarantees** - Claims of regulatory compliance
- **Restricted Edition features** - Enterprise-only capabilities (visual builder, multi-region, etc.)
- **Production-ready compliance** - Frameworks requiring legal/audit validation

**Why?** IOA Core OSS provides **educational governance frameworks** and compliance-ready patterns. Production regulatory compliance requires legal review, audit trails, and enterprise support available in Restricted Edition.

### Pull Request Workflow

1. **Fork & Clone**
   ```bash
   git clone https://github.com/YOUR-USERNAME/ioa-core.git
   cd ioa-core
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/my-improvement
   ```

3. **Make Changes with Tests**
   - Write code following PEP 8
   - Add tests for new functionality
   - Update documentation

4. **Run CI Locally**
   ```bash
   # Run all tests
   pytest -q
   
   # Run local CI gate
   bash ../ioa-ops/ci_gates/local/local_ci_gate.sh
   ```

5. **Submit Pull Request**
   - **Title**: Brief description (e.g., "fix: resolve audit chain verification bug")
   - **Description**: 
     - What does this PR do?
     - Why is this change needed?
     - How was it tested?
     - Link to related issues
   - **Proof Tests**: Include test output showing functionality

6. **CI Must Pass**
   - ✅ All tests passing
   - ✅ 0 warnings, 0 skips
   - ✅ 0 broken links
   - ✅ 100% SPDX compliance

**Maintainers will review within 3-5 business days.**

## Code Style

* Follow Python PEP 8 guidelines.
* Include docstrings for public classes, methods and functions.
* Write descriptive commit messages and comments.
* Keep pull requests focused on a single topic or fix.

## License Compliance

By contributing code, you agree that your contribution will be licensed under the same Apache 2.0 licence that covers the IOA Core project.  Do not submit code that you do not have the right to license under Apache 2.0.

## Reporting Security Issues

If you discover a security vulnerability in IOA Core, please do not open a public issue.  Instead, email the maintainers at `security@ioaproject.org` with a detailed description of the vulnerability.  We will work with you to resolve the issue quickly and responsibly.

## Documentation Standards

### IOA Style Guide
All documentation must follow the **[IOA Style Guide](docs/external/OPS_GUIDES.md)** which establishes:
- **Professional Dialects:** Engineering-grade, precise language without marketing hype
- **Terminology Canon:** Exact names for components (System Laws, Command Deck, MediaGate, etc.)
- **Formatting Rules:** Code fences, CLI prompts, tables, and link standards
- **Security & Governance Language:** Proper System Laws references and audit trail citations

### Header Standardization
All documentation files must include the standardized IOA header format:

```markdown
**IOA Module:** [file_path]  
**Version:** v2.5.0  
**Last-Updated:** [YYYY-MM-DD]  
**Agents:** [authoring agents]  
**Summary:** [1–2 line purpose]
```

### Header Rules
- **NO agent-name attributions** in headers - use "Cursor assist" or similar generic terms
- **Standardized format** must be used for all new documentation
- **Version consistency** with current IOA Core version
- **Clear purpose** in summary line

### File Naming
- Use descriptive, lowercase names with underscores
- Include version numbers in filenames when appropriate
- Follow established naming conventions in the project

### Documentation Governance Rules
All documentation changes must comply with IOA's governance framework:

**Rule 1: Docs Never Lie**
- Any PR modifying README.md, docs/**, or docs/tutorials/** must pass all CI validation jobs
- Examples must run deterministically (mock paths allowed)
- STATUS_REPORT_YYYYMMDD_DOCS.md must be updated upon merge

**Rule 2: Style & Terminology Conformance**
- All docs must pass Vale (professional dialects, terminology) and markdownlint (structural hygiene)
- Must conform to [IOA Style Guide](docs/external/OPS_GUIDES.md)
- Non-conforming language fails CI with actionable hints

**Rule 3: Non-Interactive Execution**
All documentation and tutorials must be executable non-interactively in CI environments.

**Rule 4: Dispatch Completion Validation**
Dispatch completion requires CI ✅ check - no dispatch may be marked COMPLETE until all required CI jobs pass successfully.

**Key Requirements:**
- **No interactive prompts** in code blocks (passwords, confirmations, user input)
- **Install commands** must include non-interactive flags (--yes, --no-input, --quiet)
- **Secrets and credentials** must use environment variables or mocks
- **Elevated commands** must be tagged with `# [doc-test-needs-sudo]` if unavoidable

**Resources:**
- **[IOA Style Guide](docs/external/OPS_GUIDES.md)** - Authoritative style and terminology guide
- **[Documentation Authoring Guide](docs/external/OPS_GUIDES.md)** - Comprehensive writing guidelines
- **[IOA Ledger Rules](docs/external/OPS_GUIDES.md)** - Governance and compliance requirements
- **Local Validation:** Run `python scripts/validate_docs.py` before submitting
- **CI Gates:** "Docs Validate", "Docs Style & Terminology", and "Docs Non-Interactive Conformance" must pass before merge

**Examples:**
> **Warning**: The following contains potentially destructive commands. 
> Review carefully before execution.

> **Note**: Some commands below are examples for future functionality.

```bash
# ✅ Good: Non-interactive installation
pip install --no-input package

# ❌ Bad: Interactive installation
pip install package

# ✅ Good: Tagged elevated command
# [doc-test-needs-sudo] This command requires root access
# sudo systemctl start service
```

## Versioning & File Headers

- Use git tags (e.g., `v2.5.0`) for official versions.
- Do not put `Version:` or `Last-Updated:` in file headers; these drift.
- All source files must start with the SPDX Apache-2.0 header.
## Versioning & Release Policy

IOA Core follows **Semantic Versioning (SemVer)**:

- **MAJOR** (X.0.0): Breaking changes or architecture updates that may require migration.
- **MINOR** (X.Y.0): Backward-compatible feature additions or improvements.
- **PATCH** (X.Y.Z): Non-breaking fixes, performance, documentation, CI, or dependency updates.

### Release workflow
1. Development and fixes occur on feature branches or `dev`.
2. When stable, we open a release branch, run the full CI gate, and bump the version.
3. The version in:
   - `pyproject.toml`
   - `VERSION`
   - `README.md` (badge and header)
   **must match** the tag name (e.g., `v2.5.1`).
4. Tags are created only for production-ready builds.
5. The CI pre-tag hook enforces version sync before allowing a release push.

### Examples
- `2.5.1 → 2.5.2` — patch: doc or CI improvements.
- `2.5.1 → 2.6.0` — minor: new governance feature, no breaking changes.
- `2.x.x → 3.0.0` — major: structural changes requiring migration.

### Frequency
- Minor/patch releases are cut **as needed**, not per merge.
- Version bump only occurs on a **release branch/tag**, never per commit.

Maintainers should ensure:
- CI passes (`local_ci_gate.sh` all green).
- Documentation and changelog reflect the new version.
- The new tag is pushed **after** the CI gate and QA checks succeed.
