""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


WORKFLOW_YAML = """
kind: workflow
metadata:
  name: cli_example
  description: demo
  created_at_utc: "${NOW_UTC}"
task:
  id: CLI-001
  type: analysis
  prompt: |
    Evaluate CLI path.
  inputs: { }
orchestration:
  router: agent_router
  strategy: roundtable
  quorum: 0.5
  voting_mode: majority
  timeout_s: 5
  - id: a1
    provider: mock
    weight: 1.0
  - id: a2
    provider: mock
    weight: 1.0
artifacts:
  save: [final_report, logs]
  output_dir: reports/workflows/${STAMP}/
"""


def test_cli_workflows_run(tmp_path: Path):
    wf = tmp_path / "cli.yaml"
    wf.write_text(WORKFLOW_YAML, encoding="utf-8")
    # Invoke CLI as a module to ensure sys.path includes project
    cmd = [sys.executable, "-m", "src.cli.workflows", "run", "-f", str(wf), "--json"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    # Validate JSON printed
    stdout = proc.stdout.strip()
    assert "Artifacts saved" in stdout or stdout.startswith("{")

