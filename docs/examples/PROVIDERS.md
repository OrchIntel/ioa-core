# Provider Setup Guide

Configure LLM providers for IOA Core.

## Supported Providers

- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)
- DeepSeek
- XAI (Grok)
- Ollama (local models)

## Quick Test

```bash
IOA_PROVIDER=mock python examples/40_providers/provider_smoketest.py
```

## Live Testing

```bash
export OPENAI_API_KEY=your-key
IOA_LIVE=1 IOA_PROVIDER=openai python examples/40_providers/provider_smoketest.py
```

See [examples/40_providers/README.md](../../examples/40_providers/README.md) for details.
