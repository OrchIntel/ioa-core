# Operations Reports

This page documents where operational reports are written and how they are handled in the public `ioa-core` repository.

## Current Behavior

- Runtime-generated pytest summaries are redirected to a temporary runtime artifacts root by default.
- Benchmark and workflow artifacts should not be committed into the repository.
- Public documentation may link to operational report paths, but the report contents themselves are generated at runtime.

## Runtime Artifacts Root

Set `IOA_RUNTIME_ARTIFACTS_ROOT` to override the default temporary directory used for generated reports and summaries.

## Status Reports

Operational status reports are written under `docs/ops/status_reports/` only when a tool explicitly requests a checked-in report. Routine local runs should keep those outputs outside the tracked tree.
