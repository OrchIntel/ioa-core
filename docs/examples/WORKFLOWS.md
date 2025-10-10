# Workflows Guide

Build governed workflows with audit evidence.

## Basic Workflow

```bash
python examples/10_workflows/run_workflow.py
```

## Custom Workflow

Create `my_workflow.yaml`:
```yaml
version: 1
task: "Your task here"
policy: "your-policy"
```

Run it:
```bash
python examples/10_workflows/run_workflow.py my_workflow.yaml
```

## Workflow Features

- Audit evidence tracking
- System Laws enforcement
- Governance policy application

See [examples/10_workflows/README.md](../../examples/10_workflows/README.md) for details.
