# LLM Connectivity Report
**Generated:** 2025-10-09T02:09:58.213548+00:00
**Version:** v2.5.0

## Summary

- **Total Providers Tested:** 6
- **Available:** 6
- **Unavailable:** 0

## Provider Status

| Provider | Status | Reason | Models | Response Time |
|----------|--------|--------|--------|---------------|
| OpenAI | ✅ | Connected successfully | gpt-3.5-turbo | 1724ms |
| Anthropic | ✅ | Client initialized successfully | claude-3-haiku-20240307 | 75ms |
| Google | ✅ | Connected successfully | gemini-pro, gemini-1.5-flash | 596ms |
| Ollama | ✅ | Connected successfully | llama3.1:8b, gpt-oss:20b | 10ms |
| xAI | ✅ | Connected successfully | grok-beta | 1933ms |
| DeepSeek | ✅ | Connected successfully | deepseek-chat, deepseek-coder | 345ms |

## Environment Variables

### OpenAI

**Present:**
- ✅ `OPENAI_API_KEY`

### Anthropic

**Present:**
- ✅ `ANTHROPIC_API_KEY`

### Google

**Present:**
- ✅ `GOOGLE_API_KEY`
**Missing:**
- ❌ `GEMINI_API_KEY`

### Ollama

**Missing:**
- ❌ `OLLAMA_HOST`

### xAI

**Present:**
- ✅ `XAI_API_KEY`

### DeepSeek

**Present:**
- ✅ `DEEPSEEK_API_KEY`

## Round-Table Orchestration

- **Providers Available:** 6
- **Consensus Achieved:** ✅ Yes
- **Total Time:** 0ms
- **Status:** PASS

> **Note:** Simulated round-table test (full test requires live API calls)

## Recommendations

✅ **Multiple providers available.** Ready for round-table orchestration and quorum validation.

