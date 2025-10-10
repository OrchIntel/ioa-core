**Version:** v2.5.0  
Last-Updated: 2025-10-09

# Contributing to IOA Core

Thank you for contributing to **Intelligent Orchestration Architecture (IOA)**, developed by OrchIntel Systems Ltd! We welcome contributions to enhance IOA's multi-agent orchestration, memory, and governance. By participating, you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started
1. **Fork the Repository**:
   ```bash
   git clone https://github.com/ioa-project/ioa-core.git
   cd ioa-core
   git remote add upstream https://github.com/ioa-project/ioa-core.git
```

1. **Install Locally**:
   
   ```bash
   pip install -e .
```
   
   Use `setup.py` for development dependencies.

## Contribution Process

1. **Create a Branch**:
   
   ```bash
   git checkout -b feature/<your-feature>
```
2. **Make Changes**:
- Add adapters (`llm_adapter.py`—e.g., for new LLMs).
- Enhance patterns (`patterns.json`—submit schemas via PR).
- Improve governance (`reinforcement_policy.py`—extend reward rules).
- Update tests (`tests/`—aim 95% coverage with pytest).
3. **Commit**:
   
   ```bash
   git commit -m "feat: add new LLM adapter"
```
   
   Use conventional commits (feat/fix/docs/chore).
4. **Pull Request**:
- Push to fork: `git push origin feature/<your-feature>`.
- Open PR against upstream/main.
- Describe changes, reference issues, include tests/docs updates.
5. **Review & Merge**:
- Address feedback.
- PRs must pass CI/tests.

## Guidelines

- **Code Style**: PEP 8; use black/flake8/mypy (pre-commit hooks recommended).
- **Issues**: Use GitHub Issues for bugs/features. Templates in `.github/ISSUE_TEMPLATE`.
- **Pull Requests**: Templates in `.github/PULL_REQUEST_TEMPLATE.md`.
- **Security**: Report to `security@orchintel.com` (no public issues).
- **Best Practices**: See OSS guides (e.g., [Google OSS Best Practices](https://opensource.google/documentation/reference/best-practices)).

## Areas for Contribution

- Adapters for LLMs (e.g., DeepSeek in `llm_adapter.py`).
- Pattern schemas in `patterns.json`.
- Governance rules in `reinforcement_policy.py`.
- Tests/docs in `tests/` and `docs/`.

Thank you—your contributions shape IOA!

© 2025 OrchIntel Systems Ltd