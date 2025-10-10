# Roundtable Quorum Guide

Multi-agent consensus with vendor-neutral voting.

## Basic Usage

```bash
python examples/20_roundtable/roundtable_quorum.py "Your task (ok)"
```

## Quorum Rules

- 3 agents vote
- 2-of-3 approval required (strong quorum)
- Vendor-neutral (simulates OpenAI, Anthropic, Google)

## Output

Returns votes from each agent plus quorum status.

See [examples/20_roundtable/README.md](../../examples/20_roundtable/README.md) for details.
