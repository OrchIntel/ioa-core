# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Minimal workflow runner demonstration."""

import json
from pathlib import Path

try:
    import yaml
except ImportError:
    # Fallback if yaml not available
    import json as yaml


def run(path="examples/10_workflows/sample_workflow.yaml"):
    """Run a simple workflow with audit evidence.
    
    Args:
        path: Path to workflow YAML file
    """
    workflow_file = Path(path)
    
    if not workflow_file.exists():
        # Fallback for when running from different directory
        workflow_file = Path(__file__).parent / "sample_workflow.yaml"
    
    content = workflow_file.read_text()
    
    # Simple YAML parsing (or fallback to basic parsing)
    try:
        cfg = yaml.safe_load(content)
    except AttributeError:
        # Very basic fallback parser
        cfg = {
            "task": "Analyze code for security issues",
            "policy": "demo-governed"
        }
    
    # Simulate a governed workflow execution with audit record
    result = {
        "task": cfg.get("task", "unknown"),
        "policy": cfg.get("policy", "demo"),
        "result": "OK",
        "evidence_id": "ev-0001",
        "audit_chain_verified": True,
        "system_laws_applied": ["Law 1", "Law 5", "Law 7"]
    }
    
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "examples/10_workflows/sample_workflow.yaml"
    run(path)

