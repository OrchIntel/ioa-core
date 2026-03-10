# Where Things Live

This document summarizes the stable locations for code, docs, and generated outputs in `ioa-core`.

## Source

- `src/ioa_core/`: canonical IOA Core package
- `src/`: legacy compatibility modules retained for downstream integrations and tests
- `examples/`: runnable examples
- `tests/`: validation, regression, and performance coverage

## Documentation

- `README.md`: repository entry point
- `docs/`: published project documentation
- `docs/ops/`: operational guidance and stable report references

## Generated Output

- Runtime artifacts default to a temporary directory outside the repository
- `reports/` is intentionally not used for routine local test output in the public repository
- Set `IOA_RUNTIME_ARTIFACTS_ROOT` when you need deterministic artifact placement

## Configuration

- `pyproject.toml`: packaging and Python metadata
- `pytest.ini`: pytest import and marker configuration
- `config/`: checked-in configuration templates only
