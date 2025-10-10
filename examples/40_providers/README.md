# Provider Smoketest Example

Quick connectivity check for LLM providers.

## Usage

```bash
# Test with mock provider (default)
IOA_PROVIDER=mock python examples/40_providers/provider_smoketest.py

# Test specific provider (offline mock)
IOA_PROVIDER=openai python examples/40_providers/provider_smoketest.py

# Test with live provider (requires API key)
IOA_LIVE=1 IOA_PROVIDER=openai python examples/40_providers/provider_smoketest.py
```

## Output

Returns JSON with:
- `provider` - Provider being tested
- `status` - "ok" or "key_missing"
- `mode` - "offline-mock" or "live-test-ready"
- `has_api_key` - Whether API key is configured
- `live_mode_enabled` - Whether live testing is enabled

## Supported Providers

- `openai` - OpenAI (GPT-4, GPT-3.5)
- `anthropic` - Anthropic (Claude)
- `google` - Google (Gemini)
- `deepseek` - DeepSeek
- `xai` - XAI (Grok)
- `ollama` - Ollama (local models)
- `mock` - Mock provider (default)

## Notes

- Defaults to offline mock mode (no API calls)
- Set `IOA_LIVE=1` to enable real API testing
- Checks for API keys in environment

