# LLM Provider Setup Guide

**IOA v2.5.0 — Multi-Provider LLM Validation**

This guide shows how to configure all 6 supported LLM providers for IOA's multi-provider orchestration and round-table consensus system.

---

## Quick Start

### 1. Export All Your API Keys

```bash
# In your terminal (or add to ~/.zshrc for persistence)
export OPENAI_API_KEY="sk-proj-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="AIzaSy..."
export XAI_API_KEY="xai-..."
export DEEPSEEK_API_KEY="sk-..."
# Ollama runs locally, no key needed
```

### 2. Run the Validator

```bash
cd /Users/ryan/OrchIntelWorkspace/ioa-core-internal
python3 tests/validation/llm_validator.py
```

### 3. Check the Reports

- `tests/validation/LLM_CONNECTIVITY_REPORT.md` — Human-readable status
- `tests/validation/ROUND_TABLE_RESULTS.json` — Machine-readable results

---

## Supported Providers (6 Total)

### 1. OpenAI (GPT Models)

**Environment Variable:** `OPENAI_API_KEY`

**Get Your Key:**
1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Copy and export: `export OPENAI_API_KEY=sk-proj-...`

**Models Tested:** gpt-3.5-turbo, gpt-4

**API Endpoint:** https://api.openai.com/v1

---

### 2. Anthropic (Claude Models)

**Environment Variable:** `ANTHROPIC_API_KEY`

**Get Your Key:**
1. Go to https://console.anthropic.com/
2. Settings → API Keys
3. Create key and export: `export ANTHROPIC_API_KEY=sk-ant-...`

**Models Tested:** claude-3-opus, claude-3-sonnet

**API Endpoint:** https://api.anthropic.com

---

### 3. Google (Gemini Models)

**Environment Variable:** `GOOGLE_API_KEY` (or `GEMINI_API_KEY`)

**Get Your Key:**
1. Go to https://aistudio.google.com/app/apikey
2. Create API key
3. Export: `export GOOGLE_API_KEY=AIzaSy...`

**Models Tested:** gemini-pro, gemini-1.5-flash

**API Endpoint:** Uses Google AI SDK

**Note:** You may see harmless gRPC warnings - these are normal and don't affect connectivity.

---

### 4. Ollama (Local Models)

**Environment Variable:** `OLLAMA_HOST` (optional, defaults to http://localhost:11434)

**Setup:**
1. Install Ollama: https://ollama.ai/
2. Start the service: `ollama serve`
3. Pull models: `ollama pull llama3.1:8b`

**Models Available:** Any models you've pulled locally

**No API Key Required** — Runs locally, no cloud costs!

**Benefits:**
- ✅ Free (no API charges)
- ✅ Private (data never leaves your machine)
- ✅ Fast (local network, ~40ms response)

---

### 5. xAI (Grok Models)

**Environment Variable:** `XAI_API_KEY`

**Get Your Key:**
1. Go to https://x.ai/api
2. Sign up for API access
3. Generate key and export: `export XAI_API_KEY=xai-...`

**Models Tested:** grok-beta

**API Endpoint:** https://api.x.ai/v1 (OpenAI-compatible)

---

### 6. DeepSeek (DeepSeek Models) ⭐ NEW

**Environment Variable:** `DEEPSEEK_API_KEY`

**Get Your Key:**
1. Go to https://platform.deepseek.com/
2. Create account and navigate to API keys
3. Generate key and export: `export DEEPSEEK_API_KEY=sk-...`

**Models Tested:** deepseek-chat, deepseek-coder

**API Endpoint:** https://api.deepseek.com (OpenAI-compatible)

**Note:** DeepSeek offers competitive pricing and strong coding capabilities.

---

## Persistent Configuration

### Option 1: Add to Shell Profile (Recommended)

```bash
# Add to ~/.zshrc (or ~/.bashrc for bash)
cat >> ~/.zshrc << 'EOF'

# IOA LLM Provider API Keys
export OPENAI_API_KEY="sk-proj-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="AIzaSy..."
export XAI_API_KEY="xai-..."
export DEEPSEEK_API_KEY="sk-..."

EOF

# Reload your shell
source ~/.zshrc
```

### Option 2: Use Environment File

```bash
# Create .env file
cat > /Users/ryan/OrchIntelWorkspace/ioa-core-internal/.env << 'EOF'
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIzaSy...
XAI_API_KEY=xai-...
DEEPSEEK_API_KEY=sk-...
EOF

# Load before running
set -a; source .env; set +a
python3 tests/validation/llm_validator.py
```

### Option 3: Session-Only (Temporary)

```bash
# Export for current terminal session only
export OPENAI_API_KEY="sk-proj-..."
export ANTHROPIC_API_KEY="sk-ant-..."
# etc...

# Lost when terminal closes
```

---

## Validation Output

### Example: All Providers Configured

```
🔍 Testing LLM Provider Connectivity...

Testing OpenAI...
Testing Anthropic...
Testing Google...
Testing Ollama...
Testing xAI...
Testing DeepSeek...

Testing Round-Table with 6 available providers...

============================================================
📊 Validation Complete
============================================================
Available Providers: 6/6
  ✅ OpenAI: Connected successfully
  ✅ Anthropic: Client initialized successfully
  ✅ Google: Connected successfully
  ✅ Ollama: Connected successfully
  ✅ xAI: Connected successfully
  ✅ DeepSeek: Connected successfully

📄 Reports generated:
  - tests/validation/LLM_CONNECTIVITY_REPORT.md
  - tests/validation/ROUND_TABLE_RESULTS.json
```

### Example: Partial Configuration

```
Available Providers: 3/6
  ❌ OpenAI: Missing env vars: OPENAI_API_KEY
  ✅ Anthropic: Client initialized successfully
  ✅ Google: Connected successfully
  ✅ Ollama: Connected successfully
  ❌ xAI: Missing env vars: XAI_API_KEY
  ❌ DeepSeek: Missing env vars: DEEPSEEK_API_KEY
```

---

## Round-Table Orchestration

**What is Round-Table?**
- Submits the same query to multiple LLM providers
- Compares responses for consensus
- Provides confidence scoring based on agreement
- Identifies outliers and dissenting opinions

**Requirements:**
- At least 2 providers must be available
- Providers must all respond successfully
- Quorum logic: majority agreement (n/2 + 1)

**Example Use Case:**
```python
# Query: "Is this code safe?"
# OpenAI: YES (confidence: 0.9)
# Anthropic: YES (confidence: 0.85)
# Google: NO (confidence: 0.7)
# DeepSeek: YES (confidence: 0.8)
# Ollama: YES (confidence: 0.75)
# Result: Consensus = YES (4 of 5 agree, 80%)
```

---

## Troubleshooting

### Google API Warnings

**Symptom:**
```
E0000 ... ALTS creds ignored. Not running on GCP
E0000 ... Plugin added invalid metadata value
```

**Solution:** These are **normal warnings**, not errors. Google's SDK tries multiple auth methods. Your connection still works fine.

---

### "Missing env vars" Error

**Check if variable is set:**
```bash
echo $GOOGLE_API_KEY
# Should print your key, not blank
```

**If blank, export it:**
```bash
export GOOGLE_API_KEY=AIzaSy...
```

**Verify it worked:**
```bash
echo $GOOGLE_API_KEY
# Should now show your key
```

---

### Ollama Not Detected

**Check if running:**
```bash
curl http://localhost:11434/api/tags
```

**If error, start Ollama:**
```bash
ollama serve
```

**In another terminal, pull a model:**
```bash
ollama pull llama3.1:8b
```

---

### Provider Shows "Connection timeout"

**Possible causes:**
1. Invalid API key
2. Network firewall blocking
3. Service temporarily down
4. Rate limit exceeded

**Debug:**
```bash
# Test manually
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

## Cost Considerations

| Provider | Pricing | Notes |
|----------|---------|-------|
| **OpenAI** | $0.50-$30 per 1M tokens | Most expensive, highest quality |
| **Anthropic** | $3-$15 per 1M tokens | Mid-range, excellent reasoning |
| **Google** | $0.35-$7 per 1M tokens | Cheapest cloud option |
| **xAI** | TBD | Beta pricing, contact for rates |
| **DeepSeek** | $0.14-$0.28 per 1M tokens | Very competitive, good for coding |
| **Ollama** | **FREE** | Local only, no cloud costs |

**Recommendation:** Use Ollama for development, cloud providers for production.

---

## Security Best Practices

### ✅ DO:
- Store keys in environment variables
- Use `.env` files (add to `.gitignore`)
- Rotate keys regularly
- Use separate keys for dev/prod
- Monitor API usage

### ❌ DON'T:
- Hardcode keys in source code
- Commit keys to Git
- Share keys publicly
- Use production keys in development
- Leave unused providers enabled

---

## Next Steps

### 1. Configure Your Providers
```bash
# Start with one or two
export GOOGLE_API_KEY=AIzaSy...
export DEEPSEEK_API_KEY=sk-...

# Add more as needed
```

### 2. Run Validation
```bash
python3 tests/validation/llm_validator.py
```

### 3. Check Reports
```bash
cat tests/validation/LLM_CONNECTIVITY_REPORT.md
```

### 4. Test Round-Table
```bash
# Once you have 2+ providers configured
# Round-table tests will automatically run
```

### 5. Integrate with IOA
```bash
# Use validated providers in your IOA orchestration
# Round-table consensus in policy decisions
# Multi-provider evidence generation
```

---

## Support

**Documentation:**
- `LLM_CONNECTIVITY_REPORT.md` — Status of all providers
- `ROUND_TABLE_RESULTS.json` — Detailed test results
- `LLM_VALIDATION_SUMMARY.md` — Implementation guide

**Validator Script:**
- `tests/validation/llm_validator.py` — Main validation script

**Issues:**
- Check environment variables first
- Verify API keys are valid
- Test individual providers manually
- Review provider-specific documentation

---

**IOA v2.5.0 — Ready for Multi-Provider Orchestration** ✅

