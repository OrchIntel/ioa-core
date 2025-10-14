"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import json
from pathlib import Path
import os

import pytest

from workflow_executor import WorkflowExecutor


VALID_YAML = """
kind: workflow
metadata:
  name: t1
  description: demo
  created_at_utc: "${NOW_UTC}"
task:
  id: T-001
  type: analysis
  prompt: |
    Evaluate the system.
  inputs: { }
orchestration:
  router: agent_router
  strategy: roundtable
  quorum: 0.6
  voting_mode: majority
  timeout_s: 5
  - id: a1
    provider: mock
    weight: 1.0
  - id: a2
    provider: mock
    weight: 1.0
evaluation:
  enabled: true
  policy: minimal
  success_threshold: 0.95
  capture_feedback: true
artifacts:
  save: [final_report, logs]
  output_dir: reports/workflows/${STAMP}/
"""


INVALID_YAML = """
kind: workflow
metadata:
  name: t1
task:
  id: T-001
  type: analysis
  prompt: "Run"
  inputs: { }
orchestration:
  router: agent_router
  strategy: roundtable
  quorum: 2.0   # invalid
  voting_mode: majority
  timeout_s: 5
artifacts:
  save: [final_report, logs]
  output_dir: reports/workflows/${STAMP}/
"""


def write_tmp(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "w.yaml"
    p.write_text(content, encoding="utf-8")
    return p


def test_parse_and_compile(tmp_path: Path):
    path = write_tmp(tmp_path, VALID_YAML)
    ex = WorkflowExecutor()
    spec = ex.parse_yaml(str(path))
    plan = ex.compile(spec)
    assert plan.voting_mode in ("majority", "weighted", "borda")
    assert plan.quorum == 0.6
    assert plan.timeout_s == 5
    assert plan.agents == ["a1", "a2"]


def test_invalid_schema_quorum(tmp_path: Path):
    path = write_tmp(tmp_path, INVALID_YAML)
    ex = WorkflowExecutor()
    with pytest.raises(Exception):
        ex.parse_yaml(str(path))


def test_run_and_artifacts(tmp_path: Path):
    path = write_tmp(tmp_path, VALID_YAML)
    ex = WorkflowExecutor()
    spec = ex.parse_yaml(str(path))
    plan = ex.compile(spec)
    # Force logs to tmp
    log_file = str(tmp_path / "run.jsonl")
    report = ex.run(plan, log_file=log_file)
    artifacts = ex.save_artifacts(report, log_path=log_file, out_dir=plan.artifacts_output_dir)
    assert Path(artifacts["final_report"]).exists()
    assert Path(artifacts["logs"]).exists()


def test_voting_modes_execute(tmp_path: Path):
    yaml_base = VALID_YAML
    for mode in ("majority", "weighted", "borda"):
        content = yaml_base.replace("voting_mode: majority", f"voting_mode: {mode}")
        path = write_tmp(tmp_path, content)
        ex = WorkflowExecutor()
        spec = ex.parse_yaml(str(path))
        plan = ex.compile(spec)
        report = ex.run(plan)
        assert report.voting_algorithm == mode


def test_artifacts_output_dir_stamp_expansion(tmp_path: Path):
    content = VALID_YAML.replace("reports/workflows/${STAMP}/", f"{tmp_path}/wf-${{STAMP}}/")
    path = write_tmp(tmp_path, content)
    ex = WorkflowExecutor()
    spec = ex.parse_yaml(str(path))
    plan = ex.compile(spec)
    assert "${STAMP}" not in plan.artifacts_output_dir
    assert str(tmp_path) in plan.artifacts_output_dir


def test_default_log_file_created(tmp_path: Path):
    path = write_tmp(tmp_path, VALID_YAML)
    ex = WorkflowExecutor()
    spec = ex.parse_yaml(str(path))
    plan = ex.compile(spec)
    report = ex.run(plan)
    # Default log path under artifacts dir
    default_log = Path(plan.artifacts_output_dir) / "run.jsonl"
    assert default_log.exists()


def test_compile_preserves_agent_order(tmp_path: Path):
    yaml_text = VALID_YAML.replace("- id: a1", "- id: x1").replace("- id: a2", "- id: y2")
    path = write_tmp(tmp_path, yaml_text)
    ex = WorkflowExecutor()
    spec = ex.parse_yaml(str(path))
    plan = ex.compile(spec)
    assert plan.agents == ["x1", "y2"]


def test_parse_expands_placeholders(tmp_path: Path):
    path = write_tmp(tmp_path, VALID_YAML)
    ex = WorkflowExecutor()
    spec = ex.parse_yaml(str(path))
    # created_at_utc should be expanded
    assert spec.metadata.created_at_utc is not None
    assert "T-001" == spec.task.id


def test_run_respects_timeout_and_quorum(tmp_path: Path):
    yaml_text = VALID_YAML.replace("timeout_s: 5", "timeout_s: 1").replace("quorum: 0.6", "quorum: 0.5")
    path = write_tmp(tmp_path, yaml_text)
    ex = WorkflowExecutor()
    spec = ex.parse_yaml(str(path))
    plan = ex.compile(spec)
    report = ex.run(plan)
    assert report.reports["quorum_threshold"] >= 1
    assert report.reports["execution_time"] >= 0.0


def test_save_artifacts_copies_log_when_outside_dir(tmp_path: Path):
    path = write_tmp(tmp_path, VALID_YAML)
    ex = WorkflowExecutor()
    spec = ex.parse_yaml(str(path))
    plan = ex.compile(spec)
    # Log outside artifacts dir
    external_log = tmp_path / "outer.jsonl"
    external_log.write_text("{}\n", encoding="utf-8")
    report = ex.run(plan, log_file=str(external_log))
    out = ex.save_artifacts(report, log_path=str(external_log), out_dir=plan.artifacts_output_dir)
    assert Path(out["logs"]).exists()
    assert Path(out["logs"]).parent == Path(plan.artifacts_output_dir)

