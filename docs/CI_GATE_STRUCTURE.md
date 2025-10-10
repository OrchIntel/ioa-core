# IOA Core CI Gate Structure

**Version**: 2.5.0  
**Last Updated**: 2025-10-10

---

## Overview

IOA Core uses a **two-tier CI gate structure** to maintain clean public repository hygiene while ensuring comprehensive internal quality checks:

1. **Public CI Gates** - Run on GitHub Actions (visible to all)
2. **Local CI Gates** - Run locally before push (internal quality checks)

This separation ensures the public repository remains professional and focused on essential checks, while internal development maintains rigorous standards.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ioa-core-internal (Staging)                               │
│  ├── .git/hooks/pre-push  ────────────────┐               │
│  └── Source code                           │               │
│                                             │               │
│                                             ▼               │
│                              ┌──────────────────────────┐  │
│                              │  Local CI Gate           │  │
│                              │  (ioa-ops/ci_gates)      │  │
│                              │                          │  │
│                              │  • Preflight scan        │  │
│                              │  • Link check            │  │
│                              │  • Enterprise keywords   │  │
│                              │  • Security validation   │  │
│                              │  • Smoke tests           │  │
│                              └──────────────────────────┘  │
│                                             │               │
│                                             ▼               │
│                                    ┌────────────────┐      │
│                                    │ Mirror & Push  │      │
│                                    └────────────────┘      │
│                                             │               │
└─────────────────────────────────────────────┼───────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ioa-core (Public GitHub)                                  │
│  ├── .github/workflows/                                    │
│  │   ├── build.yml         (Build & test)                 │
│  │   ├── license-spdx.yml  (License compliance)           │
│  │   └── linkcheck.yml     (Documentation links)          │
│  └── Source code                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Public CI Gates (GitHub Actions)

**Location**: `ioa-core/.github/workflows/`

### 1. **build.yml**
- **Purpose**: Build and test the package
- **Runs On**: Python 3.10, 3.11, 3.12
- **Checks**:
  - Package installation
  - Basic linting (syntax errors only)
  - Smoke tests
  - Package build verification
- **Trigger**: Push to main/develop, Pull requests

### 2. **license-spdx.yml**
- **Purpose**: Ensure license compliance
- **Checks**:
  - SPDX headers in all Python files
  - LICENSE file presence
- **Trigger**: Push to main/develop, Pull requests

### 3. **linkcheck.yml**
- **Purpose**: Validate documentation links
- **Checks**:
  - Internal Markdown links
  - README link structure
- **Trigger**: Push to main/develop, Pull requests, Weekly schedule

---

## Local CI Gates (Pre-Push)

**Location**: `ioa-ops/ci_gates/local/`

### Script: `local_ci_gate.sh`

**Purpose**: Comprehensive internal quality checks before pushing to GitHub

**Phases**:

#### **Phase 1: Preflight Scan** (Canonical Compliance)
- Canonical naming conventions
- Branding consistency
- File structure validation
- Documentation standards
- **Status**: BLOCKING (fails push if critical issues found)

#### **Phase 2: Link Check**
- Internal documentation links
- Cross-reference validation
- Broken link detection
- **Status**: WARNING (logs issues, non-blocking)

#### **Phase 3: Enterprise Keywords Scan**
- Absolute local paths (platform-specific user directories)
- Enterprise references (excluding allowed contexts)
- Internal vendor names
- **Status**: BLOCKING (fails push if found)

#### **Phase 4: Security Validation**
- Secrets pattern detection
- API key exposure
- SPDX header compliance
- License file verification
- **Status**: BLOCKING (fails push if found)

#### **Phase 5: Smoke Tests**
- Basic import tests
- Core functionality checks
- CLI verification
- **Status**: WARNING (logs results, non-blocking)

---

## Usage

### Running Local CI Gate Manually

```bash
cd /Users/ryan/OrchIntelWorkspace/ioa-core
bash ../ioa-ops/ci_gates/local/local_ci_gate.sh
```

### Automatic Pre-Push Check

The pre-push hook automatically runs local CI gate:

```bash
# In ioa-core-internal
git push origin main
# → Pre-push hook runs local CI gate
# → If all checks pass, push proceeds
# → If any check fails, push is aborted
```

### Bypassing Pre-Push Hook (Not Recommended)

```bash
git push --no-verify origin main
```

**⚠️ Warning**: Bypassing checks may introduce issues into the public repository.

---

## What Gets Checked Where

| Check | Local CI Gate | Public CI |
|-------|---------------|-----------|
| **Build & Install** | ✅ (Smoke tests) | ✅ (Full test) |
| **SPDX Headers** | ✅ | ✅ |
| **License File** | ✅ | ✅ |
| **Absolute Paths** | ✅ | ❌ |
| **Enterprise Keywords** | ✅ | ❌ |
| **Secrets Detection** | ✅ | ❌ |
| **Canonical Compliance** | ✅ | ❌ |
| **Link Checking** | ✅ | ✅ |
| **Smoke Tests** | ✅ | ❌ |
| **Full Test Suite** | ❌ | ✅ |

---

## Excluded from Public Repository

**Workflow Files** (via `.gitignore`):
```
.github/workflows/no-enterprise-keywords.yml
.github/workflows/canonical-scan.yml
.github/workflows/preflight*.yml
.github/workflows/keyword-scan*.yml
```

These checks are **only** run locally through `ioa-ops/ci_gates/local/`.

---

## Rationale

### Why Separate Local and Public Gates?

1. **Public Professionalism**: Public CI should focus on standard OSS checks (build, tests, licenses)
2. **Internal Standards**: Advanced compliance checks (absolute paths, keywords) are internal concerns
3. **Security**: Prevents exposure of internal tooling and standards
4. **Performance**: Reduces public CI runtime and complexity
5. **Flexibility**: Local gates can be more strict without affecting public contributors

### Why Pre-Push Hook?

- **Early Detection**: Catches issues before they reach GitHub
- **Fast Feedback**: Immediate results (no waiting for CI)
- **Cost Effective**: Reduces GitHub Actions usage
- **Quality Gate**: Ensures only verified code reaches public repository

---

## Maintenance

### Adding New Checks

**Local CI Gate**:
1. Add check to `ioa-ops/ci_gates/local/local_ci_gate.sh`
2. Update this documentation
3. Test with `bash local_ci_gate.sh`

**Public CI**:
1. Create new workflow in `ioa-core/.github/workflows/`
2. Keep it focused and neutral (no internal logic)
3. Update this documentation
4. Test with a test commit

### Modifying Existing Checks

1. Update script or workflow file
2. Update documentation
3. Test locally before committing
4. Update `LOCAL_GATE_RESULTS.md` with new output

---

## Troubleshooting

### Pre-Push Hook Not Running
```bash
# Verify hook exists and is executable
ls -la ioa-core-internal/.git/hooks/pre-push
chmod +x ioa-core-internal/.git/hooks/pre-push
```

### Local CI Gate Failing
```bash
# Run with verbose output
bash -x ../ioa-ops/ci_gates/local/local_ci_gate.sh

# Check specific phase
cd ioa-core
python3 ../ioa-ops/tools/preflight_scan.py --workspace . --fail-on critical
```

### GitHub Actions Failing
```bash
# Check workflow syntax
cd ioa-core
cat .github/workflows/build.yml

# Test locally
act -j build  # Requires 'act' tool
```

---

## References

- **Local CI Gate Script**: `ioa-ops/ci_gates/local/local_ci_gate.sh`
- **Pre-Push Hook**: `ioa-core-internal/.git/hooks/pre-push`
- **Public Workflows**: `ioa-core/.github/workflows/`
- **Results Log**: `ioa-ops/ci_gates/LOCAL_GATE_RESULTS.md`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.5.0 | 2025-10-10 | Initial two-tier structure implemented |

---

**Maintained By**: IOA Core Team  
**Contact**: https://github.com/OrchIntel/ioa-core/issues

