""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

"""
LLM Provider Factory Module for IOA Core

Creates LLM service instances with proper precedence resolution for API keys,
offline mode support, and automatic provider selection based on configuration.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from .base import LLMService, LLMServiceError

# PATCH: Cursor-2025-08-16 CL-LLM-Multiprovider-Base+Factory <add provider factory>

logger = logging.getLogger(__name__)


class ProviderFactoryError(Exception):
    """Exception raised when provider creation fails."""
    pass


                   api_key: Optional[str] = None, config_dir: Optional[Path] = None, 
                   offline: bool = None) -> LLMService:
    """
    Create an LLM service provider with precedence-based configuration.
    
    Args:
        provider: Provider name (e.g., 'openai', 'anthropic')
        api_key: Explicit API key (highest precedence)
        config_dir: Configuration directory for fallback
        offline: Whether to force offline mode (defaults to IOA_OFFLINE env var)
    
    Returns:
        Configured LLM service instance
        
    Raises:
        ProviderFactoryError: If provider creation fails
    """
    # PATCH: Cursor-2025-08-16 CL-LLM-Multiprovider-Base+Factory <implement precedence-based provider creation>
    
    # Determine offline mode
    if offline is None:
        offline = os.getenv("IOA_OFFLINE", "false").lower() in ("true", "1", "yes")
    
    # Resolve API key with precedence
    resolved_key = _resolve_api_key(provider, api_key, config_dir)
    
    # Create provider instance
    try:
        service = _create_provider_instance(provider, model, resolved_key, offline)
        logger.info(f"Created {provider} service: {service}")
        return service
    except Exception as e:
        raise ProviderFactoryError(f"Failed to create {provider} service: {e}") from e


def _resolve_api_key(provider: str, explicit_key: Optional[str], 
                    config_dir: Optional[Path]) -> Optional[str]:
    """
    Resolve API key with precedence order.
    
    Precedence (highest → lowest):
    1. Explicit key passed in call
    2. Environment variable
    3. Config file (if config_dir provided)
    4. None (no key)
    """
    # 1. Explicit key takes highest precedence
    if explicit_key and explicit_key.strip():
        return explicit_key
    
    # 2. Environment variable
    env_key = _get_env_api_key(provider)
    if env_key and env_key.strip():
        return env_key
    
    # 3. Config file (if config_dir provided)
    if config_dir:
        config_key = _get_config_api_key(provider, config_dir)
        if config_key and config_key.strip():
            return config_key
    
    # 4. No valid key found
    return None


def _get_env_api_key(provider: str) -> Optional[str]:
    """Get API key from environment variables."""
    env_mappings = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "xai": "XAI_API_KEY",
        "grok": "GROK_API_KEY",  # Also support GROK_API_KEY for Grok
        "google": "GOOGLE_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "ollama": "OLLAMA_HOST",  # For Ollama, this is the host, not a key
    }
    
    env_var = env_mappings.get(provider)
    if not env_var:
        return None
    
    value = os.getenv(env_var)
    
    # For Ollama, return the host value as the "api_key" parameter
    # (this will be handled specially in the Ollama service)
    if provider == "ollama":
        return value
    
    return value


def _get_config_api_key(provider: str, config_dir: Path) -> Optional[str]:
    """Get API key from configuration file."""
    try:
        config_file = config_dir / "llm.json"
        if not config_file.exists():
            return None
        
        import json
        with open(config_file) as f:
            config = json.load(f)
        
        providers = config.get("providers", {})
        provider_config = providers.get(provider, {})
        return provider_config.get("api_key")
        
    except Exception as e:
        logger.debug(f"Failed to read config for {provider}: {e}")
        return None


                            api_key: Optional[str], offline: bool) -> LLMService:
    """Create the actual provider instance."""
    provider = provider.lower()
    
    if provider == "openai":
        from .openai_service import OpenAIService
        return OpenAIService(model=model, api_key=api_key, offline=offline)
    
    elif provider == "anthropic":
        from .anthropic_service import AnthropicService
        return AnthropicService(model=model, api_key=api_key, offline=offline)
    
    elif provider in ["xai", "grok"]:
        from .xai_service import XAIService
        return XAIService(model=model, api_key=api_key, offline=offline)
    
    elif provider == "google":
        from .gemini_service import GeminiService
        return GeminiService(model=model, api_key=api_key, offline=offline)
    
    elif provider == "ollama":
        from .ollama_service import OllamaService
        return OllamaService(model=model, api_key=api_key, offline=offline)
    
    elif provider == "deepseek":
        from .deepseek_service import DeepSeekService
        return DeepSeekService(model=model, api_key=api_key, offline=offline)
    
    else:
        raise ProviderFactoryError(f"Unknown provider: {provider}")


def list_available_providers() -> Dict[str, Dict[str, Any]]:
    """
    List all available providers with their configuration requirements.
    
    Returns:
        Dictionary mapping provider names to their configuration info
    """
    return {
        "openai": {
            "name": "OpenAI",
            "description": "GPT models (GPT-4, GPT-3.5)",
            "env_var": "OPENAI_API_KEY",
            "requires_key": True,
            "default_model": "gpt-4"
        },
        "anthropic": {
            "name": "Anthropic",
            "description": "Claude models (Claude 3 Haiku, Sonnet, Opus)",
            "env_var": "ANTHROPIC_API_KEY",
            "requires_key": True,
            "default_model": "claude-3-sonnet"
        },
        "xai": {
            "name": "XAI",
            "description": "Grok models (Grok-1, Grok-2)",
            "env_var": "XAI_API_KEY",
            "requires_key": True,
            "default_model": "grok-1"
        },
        "grok": {
            "name": "Grok",
            "description": "Grok models (Grok-1, Grok-2)",
            "env_var": "GROK_API_KEY",
            "requires_key": True,
            "default_model": "grok-1"
        },
        "google": {
            "name": "Google Gemini",
            "description": "Gemini models (Gemini 1.5 Pro, Flash)",
            "env_var": "GOOGLE_API_KEY",
            "requires_key": True,
            "default_model": "gemini-1.5-pro"
        },
        "ollama": {
            "name": "Ollama",
            "description": "Local models (Llama, Mistral, CodeLlama)",
            "env_var": "OLLAMA_HOST",
            "requires_key": False,
            "default_model": "llama3"
        },
        "deepseek": {
            "name": "DeepSeek",
            "description": "DeepSeek models (DeepSeek Coder, DeepSeek Chat)",
            "env_var": "DEEPSEEK_API_KEY",
            "requires_key": True,
            "default_model": "deepseek-coder"
        }
    }
