# IOA Core v2.6.0 - OSS Release Readiness

**Date**: 2026-03-11  
**Status**: Released and production-hardened

## Summary

`ioa-core` v2.6.0 is now in a public-release state for the open-source repository.

Validated outcomes:

- package build succeeds (`python -m build`)
- repository CI gate passes (`global_ci_gate.py --repo ioa-core`)
- core functional suite is green (`1149 passed, 51 skipped, 42 deselected`)
- bounded slow/perf/durability validation completes successfully
- downstream compatibility checks pass for `ioa-sdk`, `ioa-cloud`, `qixchat`, `qixhealth`, and `qixlaw`

## What Changed Since Prior Readiness Notes

The earlier OSS-readiness material in this repository described a pre-release posture. That is no longer current.

Current release posture:

- public package metadata aligned to `v2.6.0`
- compatibility shims restored for dependent repositories
- repo-local artifact generation redirected out of tracked paths
- benchmark/test defects fixed in the remaining slow and perf buckets
- public website/docs status aligned to the current release state

## Known Non-Blocking Limits

- full long-form benchmark runs still depend on machine size and should be run explicitly with environment overrides when you want true high-scale evidence
- some third-party dependency deprecation warnings remain outside the `ioa-core` runtime surface

## Release Guidance

For public communication, describe `ioa-core` as:

- open-source governance kernel for AI workflows
- stable public release on PyPI
- production-hardened core with bounded CI performance profiles validated

Do not describe the repository as pre-release, beta-only, or “95% ready”.
