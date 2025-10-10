# Roundtable Quorum Example

Vendor-neutral roundtable with multi-agent consensus voting.

## Usage

```bash
# Run with default task
python examples/20_roundtable/roundtable_quorum.py

# Run with custom task
python examples/20_roundtable/roundtable_quorum.py "Review this code for bugs (ok)"
```

## Output

Returns JSON with:
- `task` - The task being voted on
- `votes` - Array of votes from each model
- `quorum_approved` - Whether quorum was met (2 of 3)
- `evidence_id` - Audit evidence identifier
- `system_laws_applied` - Which System Laws enforced quorum

## Quorum Logic

- **Strong Quorum**: 2 out of 3 votes required
- **Deterministic Mock**: Votes "approve" if task contains "ok" or "good"
- **Vendor-Neutral**: Simulates OpenAI, Anthropic, Google providers

## Notes

- Runs offline with mock models
- Demonstrates quorum policy pattern
- Set IOA_LIVE=1 + provider keys for real multi-agent voting

