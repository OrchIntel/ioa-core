# Root Cleanup Move Log

**Date**: 2025-10-11  
**Branch**: `chore/root-cleanup-20251011`  
**Goal**: Clean repository root, move dispatch/ops docs to proper folders

---

## Files Moved

### Dispatch Completion Reports → `docs/ops/dispatches/2025-10/`
- `DISPATCH_COMPLETE_LAUNCH.md` → `docs/ops/dispatches/2025-10/DISPATCH_COMPLETE_LAUNCH.md`
- `DISPATCH_COMPLETE_FEATURE_SYNC.md` → `docs/ops/dispatches/2025-10/DISPATCH_COMPLETE_FEATURE_SYNC.md`
- `DISPATCH_COMPLETE_FINAL.md` → `docs/ops/dispatches/2025-10/DISPATCH_COMPLETE_FINAL.md`
- `DISPATCH_COMPLETE_LOCAL_GATE.md` → `docs/ops/dispatches/2025-10/DISPATCH_COMPLETE_LOCAL_GATE.md`
- `DISPATCH_COMPLETE.md` → `docs/ops/dispatches/2025-10/DISPATCH_COMPLETE.md`
- `DISPATCH_STATUS_NO_SKIPS.md` → `docs/ops/dispatches/2025-10/DISPATCH_STATUS_NO_SKIPS.md`
- `OSS_FINAL_VALIDATION.md` → `docs/ops/dispatches/2025-10/OSS_FINAL_VALIDATION.md`
- `OSS_RELEASE_COMPLETE.md` → `docs/ops/dispatches/2025-10/OSS_RELEASE_COMPLETE.md`

### Ops Documentation → `docs/ops/`
- `CLI_SYNTAX_KNOWN_ISSUES.md` → `docs/ops/CLI_SYNTAX_KNOWN_ISSUES.md`
- `WHERE_THINGS_LIVE.md` → `docs/ops/WHERE_THINGS_LIVE.md`
- `MIGRATION.md` → `docs/ops/MIGRATION.md`
- `connector_validation.md` → `docs/ops/connector_validation.md`
- `MANIFEST.txt` → `docs/ops/MANIFEST.txt`
- `changed-md.txt` → `docs/ops/changed-md.txt`
- `api_keys_template.txt` → `docs/ops/api_keys_template.txt`

### Reference Documentation → `docs/reference/`
- `SCALING.md` → `docs/reference/SCALING.md`
- `MDC.md` → `docs/reference/MDC.md`
- `MAINTAINERS.md` → `docs/reference/MAINTAINERS.md`
- `CONTRIBUTORS.md` → `docs/reference/CONTRIBUTORS.md`
- `TRADEMARK.md` → `docs/reference/TRADEMARK.md`
- `TRADEMARK_NOTICE.md` → `docs/reference/TRADEMARK_NOTICE.md`

---

## Files Kept at Root

These are the **only** files that should remain at repository root:

### Essential Project Files
- ✅ `README.md` - Main project documentation
- ✅ `LICENSE` - Apache 2.0 license
- ✅ `CHANGELOG.md` - Version history
- ✅ `CONTRIBUTING.md` - Contribution guidelines
- ✅ `CODE_OF_CONDUCT.md` - Community standards
- ✅ `SECURITY.md` - Security policy
- ✅ `FEATURE_MATRIX.md` - Feature comparison (prominently linked)

### Build & Configuration
- ✅ `pyproject.toml` - Python project configuration
- ✅ `VERSION` - Version identifier
- ✅ `.gitignore` - Git ignore rules
- ✅ `pytest.ini` - Test configuration
- ✅ `requirements.txt` - Python dependencies
- ✅ `requirements-dev.txt` - Development dependencies
- ✅ `requirements-docs.txt` - Documentation dependencies

### Directories
- ✅ `.github/` - GitHub Actions, issue templates, CODEOWNERS
- ✅ `src/` - Source code
- ✅ `tests/` - Test suites
- ✅ `docs/` - Documentation
- ✅ `examples/` - Working examples
- ✅ `monitoring/` - Monitoring configuration
- ✅ `cartridges/` - Compliance cartridges

---

## Rationale

### Why Move Dispatch Reports?
- Dispatch completion reports are **operational artifacts**, not user-facing docs
- They document the development/release process, not the product itself
- Moving them to `docs/ops/dispatches/` keeps root clean while preserving history

### Why Move Ops Files?
- Files like `WHERE_THINGS_LIVE.md`, `MIGRATION.md`, and validation notes are **internal ops documentation**
- They're valuable for maintainers but clutter the root for new users
- `docs/ops/` is the proper home for operational/maintenance documentation

### Why Move Reference Files?
- Files like `SCALING.md`, `MDC.md`, and trademark notices are **reference material**
- They're important but not essential for getting started
- `docs/reference/` provides better discoverability through documentation structure

### Why Keep FEATURE_MATRIX.md at Root?
- Prominently linked from `README.md`
- Essential for users comparing OSS vs Restricted Edition
- High-visibility comparison document

---

## Impact on Links

After moving files, the following link updates were needed:
- Updated relative paths in documentation to reflect new locations
- No external links affected (all moves are internal)
- Link check verified: **0 broken links** after cleanup

---

## Repository Structure After Cleanup

```
/                    # Clean root with essential files only
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── FEATURE_MATRIX.md
├── pyproject.toml
├── VERSION
├── .gitignore
├── pytest.ini
├── requirements*.txt
├── .github/         # CI/CD, issue templates
├── src/             # Source code
├── tests/           # Test suites
├── docs/            # All documentation
│   ├── ops/         # Operational docs
│   │   └── dispatches/  # Dispatch reports by date
│   ├── reference/   # Reference material
│   ├── examples/    # Tutorial docs
│   └── ...
├── examples/        # Working code examples
└── tools/           # Helper scripts
```

---

**Result**: Clean, professional repository structure with clear organization and 0 broken links.

