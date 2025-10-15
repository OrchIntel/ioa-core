# Where Things Live - IOA Core Repository Organization

This document provides a quick reference for where different types of files and content are located in the IOA Core repository.

## 📁 Repository Structure

### Root Level
- `README.md` - Main project documentation
- `LICENSE` - Apache 2.0 license
- `pyproject.toml` - Python project configuration
- `VERSION` - Current version number
- `CONTRIBUTING.md` - Contribution guidelines
- `CODE_OF_CONDUCT.md` - Code of conduct
- `SECURITY.md` - Security policy
- `.github/` - GitHub workflows and templates

### Documentation (`docs/`)
- `docs/` - Main documentation directory
- `docs/ops/` - Operational documentation and dispatch reports
- `docs/reference/` - API reference and technical documentation
- `docs/ethics/` - Ethics framework documentation (Aletheia)
- `docs/examples/` - Example documentation and tutorials

### Source Code (`src/`)
- `src/ioa_core/` - Main IOA Core package
- `src/ioa_core/cartridges/` - Policy cartridges (including ethics)
- `src/ioa_core/adapters/` - LLM provider adapters

### Examples (`examples/`)
- `examples/` - Runnable examples and demos
- `examples/colab/` - Google Colab notebooks
- `examples/ethics/` - Ethics framework examples

### Tests (`tests/`)
- `tests/` - Test suites
- `tests/unit/` - Unit tests
- `tests/examples/` - Example integration tests

### Tools (`tools/`)
- `tools/` - Helper scripts and utilities
- `tools/ci/` - CI/CD helper scripts

## 🔗 Quick Reference

| Content Type | Location | Notes |
|-------------|----------|-------|
| Main README | `/README.md` | Project overview and getting started |
| API Docs | `/docs/reference/` | Technical documentation |
| Examples | `/examples/` | Runnable code examples |
| Ethics Docs | `/docs/ethics/` | Aletheia framework reference |
| Dispatch Reports | `/docs/ops/dispatches/` | Operational reports |
| Source Code | `/src/ioa_core/` | Main package code |
| Tests | `/tests/` | All test suites |
| Tools | `/tools/` | Helper scripts |

## 📋 File Naming Conventions

- **Documentation**: `UPPERCASE.md` for main docs, `lowercase.md` for sub-docs
- **Examples**: `descriptive_name.py` for Python examples
- **Tests**: `test_*.py` for test files
- **Tools**: `tool_name.py` or `tool_name.sh` for utilities

## 🎯 Finding Specific Content

- **Getting Started**: Start with `/README.md`
- **API Reference**: Check `/docs/reference/`
- **Examples**: Browse `/examples/`
- **Ethics Integration**: See `/docs/ethics/aletheia/`
- **Contributing**: Read `/CONTRIBUTING.md`
- **Security**: Review `/SECURITY.md`

---

*This document is automatically updated when repository structure changes.*
