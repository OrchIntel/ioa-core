**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Provider API Reference

LLM provider integration API for IOA Core.

## Base Interface

### `BaseLLMProvider`
```python
from abc import ABC, abstractmethod
from src.types import ProviderResponse

class BaseLLMProvider(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_name = self.__class__.__name__
        self.model = config.get("model", "default")
        self.zero_retention = config.get("zero_retention", False)
    
    @abstractmethod
    async def execute(self, prompt: str, **kwargs) -> ProviderResponse:
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        pass
```

### `ProviderResponse`
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List
from src.types import ProviderResponse, UsageInfo

@dataclass
class ProviderResponse:
    content: str
    usage: Optional[UsageInfo]
    metadata: Dict[str, Any]
    confidence: float
    timestamp: datetime
    provider: str
    request_id: Optional[str] = None
    finish_reason: Optional[str] = None
    system_fingerprint: Optional[str] = None

@dataclass
class UsageInfo:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: Optional[float] = None
```

## Provider Implementations

### OpenAI Provider
```python
from src.llm_providers.openai import OpenAIProvider
from openai import OpenAI

provider = OpenAIProvider({
    "api_key": "sk-...",
    "model": "gpt-4o-mini",
    "zero_retention": True
})

response = await provider.execute("Explain quantum computing")

Note: Requires OpenAI SDK v1+. Use `OpenAI()` and `client.chat.completions.create(...)`. Legacy `openai.ChatCompletion.create` is not supported.
```

### Anthropic Provider
```python
from src.llm_providers.anthropic import AnthropicProvider
import anthropic

provider = AnthropicProvider({
    "api_key": "sk-ant-...",
    "model": "claude-3-haiku"
})

response = await provider.execute("Analyze this code")
```

### Google Gemini Provider
```python
from src.llm_providers.gemini import GeminiProvider
import google.generativeai as genai

provider = GeminiProvider({
    "api_key": "AIza...",
    "model": "gemini-1.5-flash"
})

response = await provider.execute("Generate a summary")
```

### DeepSeek Provider
```python
from src.llm_providers.deepseek import DeepSeekProvider
import requests

provider = DeepSeekProvider({
    "api_key": "sk-...",
    "model": "deepseek-chat"
})

response = await provider.execute("Code review this function")
```

### XAI/Grok Provider
```python
from src.llm_providers.xai import XAIProvider
import requests

provider = XAIProvider({
    "api_key": "xai-...",
    "model": "grok-beta"
})

response = await provider.execute("Search the web for latest news")
```

### Ollama Provider (Local)
```python
from src.llm_providers.ollama import OllamaProvider
import requests

provider = OllamaProvider({
    "base_url": "http://localhost:11434",
    "model": "llama3.2"
})

response = await provider.execute("Local AI processing")
```

## Provider Management

### `ProviderManager`
```python
from src.llm_providers.manager import ProviderManager
from typing import Dict, List, Optional

manager = ProviderManager()

# Register providers
manager.register_provider("openai", openai_provider)
manager.register_provider("anthropic", anthropic_provider)

# Execute with fallback
response = await manager.execute_with_fallback(
    prompt="Explain quantum computing",
    primary_provider="openai",
    fallback_providers=["anthropic", "ollama"]
)
```

## Configuration

### Environment Variables
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="AIza..."
export DEEPSEEK_API_KEY="sk-..."
export XAI_API_KEY="xai-..."
export OLLAMA_BASE_URL="http://localhost:11434"
```

### Configuration File
```yaml
# providers_config.yaml
providers:
  openai:
    enabled: true
    api_key: "${OPENAI_API_KEY}"
    zero_retention: true
  
  anthropic:
    enabled: true
    api_key: "${ANTHROPIC_API_KEY}"

default_provider: "openai"
fallback_providers: ["anthropic", "ollama"]
```

## Usage Examples

### Basic Usage
```python
# Initialize provider
provider = OpenAIProvider({
    "api_key": "sk-...",
    "model": "gpt-4o-mini"
})

# Execute prompt
response = await provider.execute(
    "Explain quantum computing in simple terms",
    temperature=0.7,
    max_tokens=1000
)

print(f"Response: {response.content}")
print(f"Provider: {response.provider}")
```

### Zero-Retention Usage
```python
# Configure zero-retention
zero_retention_config = {
    "api_key": "sk-...",
    "model": "gpt-4o-mini",
    "zero_retention": True
}

provider = OpenAIProvider(zero_retention_config)

# Execute with zero-retention
response = await provider.execute(
    "Process sensitive data",
    user="anonymous"
)
```

### Provider Fallback
```python
# Execute with fallback
try:
    response = await manager.execute_with_fallback(
        prompt="Important analysis task",
        primary_provider="openai",
        fallback_providers=["anthropic", "ollama"]
    )
    print(f"Success with {response.provider}")
except Exception as e:
    print(f"All providers failed: {e}")
```

## Error Handling

### Provider Errors
```python
from src.llm_providers.exceptions import (
    ProviderError, RateLimitError, AuthenticationError
)

try:
    response = await provider.execute("Test prompt")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
except ProviderError as e:
    print(f"Provider error: {e}")
```

### Retry Logic
```python
import asyncio
from typing import Callable, Any

async def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await func()
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            delay = 2 ** attempt
            await asyncio.sleep(delay)
```

## Testing

### Provider Testing
```python
import pytest
from unittest.mock import patch

class TestOpenAIProvider:
    @pytest.mark.asyncio
    async def test_execute_success(self, provider):
        with patch('openai.OpenAI') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Test response"
            mock_create.return_value = mock_response
            
            result = await provider.execute("Test prompt")
            assert result.content == "Test response"
```

## Best Practices

1. **Provider Selection**
   - Use appropriate models for tasks
   - Implement fallback mechanisms
   - Monitor provider performance

2. **Configuration**
   - Use environment variables for secrets
   - Validate configurations on startup
   - Implement zero-retention when needed

3. **Error Handling**
   - Implement retry logic
   - Handle rate limiting gracefully
   - Log provider errors

4. **Performance**
   - Cache responses when appropriate
   - Use async execution
   - Monitor usage and costs

## Next Steps

1. Configure providers with API keys
2. Test all provider integrations
3. Implement fallback mechanisms
4. Monitor usage and performance
5. Optimize for your use case

## Related Docs

- [Core API Reference](core.md)
- [Live Smoke Tutorial](../tutorials/live-smoke.md)
- [Configuration Guide](../user-guide/configuration.md)
