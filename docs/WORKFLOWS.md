**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

IOA Workflows 101 (v2.5.0)

This guide shows how to define a workflow in YAML and run it via the new WorkflowExecutor and CLI.

Minimal DSL

```yaml
kind: workflow
metadata:
  name: example_roundtable_workflow
  description: Minimal roundtable example
  created_at_utc: "${NOW_UTC}"
task:
  id: W-001
  type: analysis
  prompt: |
    Assess the performance impact of the proposed caching strategy.
  inputs:
    repo_path: ./
    scenario: baseline
orchestration:
  router: agent_router
  strategy: roundtable
  quorum: 0.6
  voting_mode: majority   # majority | weighted | borda
  timeout_s: 30
  - id: a1
    provider: mock
    weight: 1.0
  - id: a2
    provider: mock
    weight: 1.0
artifacts:
  save: [final_report, logs]
  output_dir: reports/workflows/${STAMP}/
```

Run the workflow

```bash
python -m src.cli.workflows run -f dsl/workflow_schema.yaml --json --log-file reports/workflows/$(date -u +%Y%m%d-%H%M%S)/run.jsonl
```

Outputs

- FinalReport JSON: `final_report.json` under `artifacts.output_dir`
- JSONL logs: `run.jsonl` under `artifacts.output_dir`

Voting modes

- majority: simple majority with tie-breaker logged by Roundtable
- weighted: weights and confidence contribute to scores
- borda: equal-rank approximation; tie-breaker logged

All logs conform to the universal `LogEntry` schema and include `dispatch_code="DISPATCH-GPT-20250818-010"`.


