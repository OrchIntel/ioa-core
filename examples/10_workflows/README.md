# Workflow Example

Run a simple governed workflow with audit evidence.

## Usage

```bash
# Run with default workflow
python examples/10_workflows/run_workflow.py

# Run with custom workflow file
python examples/10_workflows/run_workflow.py path/to/workflow.yaml
```

## Output

Returns JSON with:
- `task` - The task being executed
- `policy` - Governance policy applied
- `result` - Execution result
- `evidence_id` - Audit evidence identifier
- `audit_chain_verified` - Chain verification status
- `system_laws_applied` - Which System Laws were enforced

## Notes

- Runs offline with mock execution
- Demonstrates governed workflow pattern
- No real LLM calls (use IOA_LIVE=1 for live testing)

