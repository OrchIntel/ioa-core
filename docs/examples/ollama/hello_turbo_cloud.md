**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Ollama Turbo Cloud Example

This example demonstrates how to use Ollama Turbo (cloud) with IOA Core for accelerated inference.

## Prerequisites

1. **Ollama Cloud Account**: Sign up at [ollama.ai/cloud](https://ollama.ai/cloud)
2. **API Credentials**: Get your `OLLAMA_API_BASE` and `OLLAMA_API_KEY`
3. **IOA Core**: Install and configure IOA Core

## Configuration

### Environment Setup

Create a `.env.local` file with your Ollama Cloud credentials:

> **Note**: Some commands below are examples for future functionality.

```bash
# Ollama Turbo Cloud Configuration
# OLLAMA_API_BASE=https://api.ollama.ai/v1
# OLLAMA_API_KEY=your-ollama-cloud-api-key-here
# IOA_OLLAMA_MODE=turbo_cloud

# Optional: Model selection
# OLLAMA_MODEL=llama3.1:8b
```

### Security Notes

⚠️ **Important Security Reminders:**
- Never commit `.env.local` to version control
- Keep your `OLLAMA_API_KEY` secure
- Monitor usage and costs in your Ollama Cloud dashboard
- Rotate API keys regularly

## Python Example

```python
#!/usr/bin/env python3
"""
Ollama Turbo Cloud Example for IOA Core

This example demonstrates how to use Ollama Turbo (cloud) with IOA Core
for accelerated inference with proper error handling.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from ioa_core.llm_manager import LLMManager
from ioa_core.llm_providers.ollama_service import OllamaService

def main():
    """Main example function."""
    
    # Check if cloud credentials are configured
    api_base = os.getenv("OLLAMA_API_BASE")
    api_key = os.getenv("OLLAMA_API_KEY")
    
    if not api_base or not api_key:
        print("❌ Error: Ollama Cloud credentials not configured")
        print("Please set OLLAMA_API_BASE and OLLAMA_API_KEY environment variables")
        print("Example:")
        print("  export OLLAMA_API_BASE=https://api.ollama.ai/v1")
        print("  export OLLAMA_API_KEY=your-api-key-here")
        return 1
    
    # Validate API base URL
    if not api_base.lower().startswith("https://"):
        print("❌ Error: OLLAMA_API_BASE must be an HTTPS URL")
        print(f"Current value: {api_base}")
        return 1
    
    print(f"✅ Ollama Cloud configured: {api_base}")
    print(f"🔑 API Key: {'*' * (len(api_key) - 4) + api_key[-4:] if len(api_key) > 4 else '****'}")
    
    try:
        # Initialize LLM Manager
        print("\n🚀 Initializing LLM Manager...")
        manager = LLMManager()
        
        # Create Ollama service with cloud configuration
        print("🔧 Creating Ollama service...")
        ollama_service = OllamaService(
            model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
            offline=False
        )
        
        # Test the service
        print("🧪 Testing Ollama Turbo Cloud...")
        test_prompt = "Say 'hello' and nothing else."
        
        response = ollama_service.generate_response(
            prompt=test_prompt,
            max_tokens=16,
            temperature=0.0
        )
        
        print(f"✅ Response: {response}")
        print("🎉 Ollama Turbo Cloud test successful!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Verify your API credentials are correct")
        print("2. Check your internet connection")
        print("3. Ensure you have sufficient credits in your Ollama Cloud account")
        print("4. Try running: ioa smoketest --provider ollama --ollama-mode turbo_cloud")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

## CLI Example

### Basic Smoketest

> **Note**: Some commands below are examples for future functionality.

```bash
# Test Ollama Turbo Cloud connectivity
# Example (not currently implemented): ioa smoketest --provider ollama --ollama-mode turbo_cloud --live
```

### Auto-detect Mode

> **Note**: Some commands below are examples for future functionality.

```bash
# Let IOA Core auto-detect based on environment
# Example (not currently implemented): ioa smoketest --provider ollama --ollama-mode auto --live
```

### Non-interactive Mode

> **Note**: Some commands below are examples for future functionality.

```bash
# Run without interactive prompts
# IOA_SMOKETEST_NON_INTERACTIVE=1 ioa smoketest --provider ollama --ollama-mode turbo_cloud --live
```

## Expected Output

### Successful Connection

```
✅ Ollama: Host: https://api.ollama.ai/v1, Mode: turbo_cloud (API key configured)
  📊 Mode: turbo_cloud
  📝 Notes: Ollama turbo_cloud mode detected

🧪 Testing Ollama Turbo Cloud...
✅ Response: hello
🎉 Ollama Turbo Cloud test successful!
```

### Missing Credentials

```
❌ Error: Ollama Cloud credentials not configured
Please set OLLAMA_API_BASE and OLLAMA_API_KEY environment variables
Example:
  export OLLAMA_API_BASE=https://api.ollama.ai/v1
  export OLLAMA_API_KEY=your-api-key-here
```

### Cloud Not Configured (SKIP)

```
⚠️  Ollama: SKIP (cloud_not_configured)
  📊 Detection: base_present=false, key_present=false
  📝 Notes: Ollama Turbo Cloud not configured, falling back to local_preset
```

## Performance Comparison

| Mode | Latency | Use Case | Cost |
|------|---------|----------|------|
| `local_preset` | ~100-500ms | Local development, offline work | Free |
| `turbo_cloud` | ~50-200ms | Production, high-performance | Billed per request |

## Troubleshooting

### Common Issues

1. **Invalid API Key**: Verify your key is correct and active
2. **Network Issues**: Check your internet connection and firewall
3. **Rate Limits**: Check your Ollama Cloud usage limits
4. **Model Availability**: Ensure the model is available in your region

### Debug Commands

> **Note**: Some commands below are examples for future functionality.

```bash
# Check environment variables
# env | grep OLLAMA

# Test API connectivity
# curl -H "Authorization: Bearer $OLLAMA_API_KEY" \
#      -H "Content-Type: application/json" \
#      "$OLLAMA_API_BASE/version"

# Run with debug logging
# IOA_LOG_LEVEL=DEBUG ioa smoketest --provider ollama --ollama-mode turbo_cloud --live
```

## Next Steps

1. **Production Setup**: Configure proper key management
2. **Monitoring**: Set up usage and cost monitoring
3. **Scaling**: Consider load balancing for high-volume usage
4. **Security**: Implement proper authentication and authorization

For more information, see:
- [Ollama Cloud Documentation](https://ollama.com/cloud)
- [IOA Core Documentation](../README.md)
- [Environment Configuration](../env.example)
