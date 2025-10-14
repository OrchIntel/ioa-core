"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
PATCH: Cursor-2025-08-21 DISPATCH-GPT-20250821-007 <agent-to-model terminology refactor>
"""

"""
LLM Manager Module for IOA Core

Manages multiple LLM provider credentials, client creation, and roundtable configuration.
Provides secure storage of API keys, runtime client instantiation, and roundtable plan
management for collaborative AI execution.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
import stat

# PATCH: Cursor-2025-08-15 CL-LLM-Deterministic-Config <add precedence-based key resolution>
logger = logging.getLogger(__name__)


class LLMConfigError(Exception):
    """Base exception for LLM configuration operations."""
    pass


class LLMProviderError(LLMConfigError):
    """Raised when provider configuration is invalid."""
    pass


class LLMStorageError(LLMConfigError):
    """Raised when storage operations fail."""
    pass


# PATCH: Cursor-2025-08-16 CL-ONBOARD-Provider-Key-Fix+UX <add provider-specific key validation with force override>

class LLMManager:
    """
    Manages LLM provider credentials and client creation.
    
    Handles secure storage of API keys, provider configuration, and runtime
    client instantiation with support for multiple providers and roundtable
    configuration.
    """
    
    CONFIG_VERSION = 1
    CONFIG_DIR = ".ioa/config"
    LLM_CONFIG_FILE = "llm.json"
    ROUNDTABLE_CONFIG_FILE = "roundtable.json"
    
    # Provider-specific API key validation patterns
    PROVIDER_KEY_PATTERNS = {
        "openai": {
            "pattern": r"^sk-[A-Za-z0-9]{20,}$",
            "description": "OpenAI API keys start with 'sk-' and are 20+ characters",
            "examples": ["sk-...", "sk-test-...", "sk-live-...", "sk-proj-..."]
        },
        "anthropic": {
            "pattern": r"^sk-ant-[A-Za-z0-9_-]{20,}$",
            "description": "Anthropic API keys start with 'sk-ant-' and are 20+ characters",
            "examples": ["sk-ant-..."]
        },
        "xai": {
            "pattern": r"^xai-[A-Za-z0-9._-]{20,}$",
            "description": "XAI API keys start with 'xai-' and are 20+ characters",
            "examples": ["xai-..."]
        },
        "grok": {
            "pattern": r"^grok_[A-Za-z0-9._-]{20,}$",
            "description": "Grok API keys start with 'grok_' and are 20+ characters",
            "examples": ["grok_..."]
        },
        "google": {
            "pattern": r"^AIza[0-9A-Za-z_-]{30,}$",
            "description": "Google Gemini API keys start with 'AIza' and are ~39 characters",
            "examples": ["AIza..."]
        },
        "ollama": {
            "pattern": None,  # No key required
            "description": "Ollama is a local provider that doesn't require an API key",
            "examples": ["No key required"]
        }
    }
    
    def __init__(self, config_dir: Optional[str] = None, allow_config_fallback: bool = True):
        """
        Initialize LLM Manager.
        
        Args:
            config_dir: Optional custom config directory (defaults to ~/.ioa/config or $IOA_CONFIG_HOME)
            allow_config_fallback: Whether to allow fallback to disk config (defaults to True)
        """
        # PATCH: Cursor-2025-08-15 CL-LLM-Deterministic-Config <respect IOA_CONFIG_HOME and test mode>
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Honor $IOA_CONFIG_HOME override for tests
            ioa_config_home = os.getenv("IOA_CONFIG_HOME")
            if ioa_config_home:
                self.config_dir = Path(ioa_config_home)
            else:
                self.config_dir = Path(os.path.expanduser(f"~/{self.CONFIG_DIR}"))
        
        self.llm_config_path = self.config_dir / self.LLM_CONFIG_FILE
        self.roundtable_config_path = self.config_dir / self.ROUNDTABLE_CONFIG_FILE
        self.allow_config_fallback = allow_config_fallback
        
        # Ensure config directory exists only if we're allowing config fallback
        if self.allow_config_fallback:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Load configuration
            self._config = self._load_config()
            self._roundtable_config = self._load_roundtable_config()
            
            # Save default configurations if they don't exist
            if not self.llm_config_path.exists():
                self._save_config()
            if not self.roundtable_config_path.exists():
                self._save_roundtable_config()
        else:
            # Test mode: minimal config without disk access
            self._config = {
                "version": self.CONFIG_VERSION,
                "default_provider": "openai",
                "providers": {}
            }
            self._roundtable_config = {
                "version": 1,
                "active": "default",
                "tables": {}
            }
        
        logger.info(f"LLM Manager initialized with config dir: {self.config_dir}, allow_config_fallback: {self.allow_config_fallback}")
    
    def resolve_api_key(self, provider: str, explicit_key: Optional[str] = None) -> Optional[str]:
        """
        Resolve API key with explicit precedence order.
        
        Precedence (highest → lowest):
        1. Explicit key passed in call
        2. Environment variable
        3. Config files (only if allow_config_fallback=True and not in test mode)
        4. None (no key)
        
        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')
            explicit_key: Explicitly provided API key
            
        Returns:
            Resolved API key or None if not found
        """
        # PATCH: Cursor-2025-08-15 CL-LLM-QSF-Config-Audit <ensure None return for unset providers>
        
        # 1. Explicit key takes highest precedence
        if explicit_key:
            # Validate explicit key is not a placeholder
            if explicit_key.strip() and not self._is_placeholder_key(explicit_key):
                return explicit_key
            # If explicit key is placeholder, treat as no key
        
        # 2. Environment variable
        env_key = self._get_env_api_key(provider)
        if env_key and not self._is_placeholder_key(env_key):
            return env_key
        
        # 3. Config files (only if allowed and not in test mode)
        if self.allow_config_fallback and not self._is_test_mode_disabled():
            config_key = self._get_config_api_key(provider)
            if config_key and not self._is_placeholder_key(config_key):
                return config_key
        
        # 4. No valid key found
        return None
    
    def _is_test_mode_disabled(self) -> bool:
        """Check if test mode should disable config file lookup."""
        # PATCH: Cursor-2025-08-15 CL-LLM-Deterministic-Config <test mode guardrails>
        return (os.getenv("IOA_TEST_MODE") == "1" and 
                os.getenv("IOA_DISABLE_LLM_CONFIG") == "1")
    
    def _get_env_api_key(self, provider: str) -> Optional[str]:
        """Get API key from environment variables."""
        # PATCH: Cursor-2025-08-16 CL-ONBOARD-Provider-Key-Fix+UX <add XAI/Grok environment variable support>
        env_mappings = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
            "xai": "XAI_API_KEY",
            "grok": "GROK_API_KEY",  # Also support GROK_API_KEY for Grok
            "groq": "GROQ_API_KEY",
            "ollama": "OLLAMA_HOST"  # Ollama uses host, not API key
        }
        
        env_var = env_mappings.get(provider)
        if env_var:
            return os.getenv(env_var)
        return None
    
    def _get_config_api_key(self, provider: str) -> Optional[str]:
        """Get API key from config files."""
        if not self.allow_config_fallback or self._is_test_mode_disabled():
            return None
        
        provider_config = self._config.get("providers", {}).get(provider, {})
        return provider_config.get("api_key")
    
    def validate_api_key(self, provider: str, api_key: str, force: bool = False) -> Dict[str, Any]:
        """
        Validate API key format for a specific provider.
        
        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')
            api_key: API key to validate
            force: Whether to force acceptance even if validation fails
            
        Returns:
            Dict with validation result and details
        """
        # PATCH: Cursor-2025-08-16 CL-ONBOARD-Provider-Key-Fix+UX <implement provider-specific key validation>
        
        # Check if provider is supported
        if provider not in self.PROVIDER_KEY_PATTERNS:
            return {
                "valid": False,
                "error": f"Unknown provider '{provider}'",
                "can_force": False
            }
        
        provider_info = self.PROVIDER_KEY_PATTERNS[provider]
        
        # Ollama doesn't require a key
        if provider == "ollama":
            return {
                "valid": True,
                "message": "Ollama is a local provider that doesn't require an API key",
                "can_force": False
            }
        
        # Check for empty keys (only for providers that require keys)
        if not api_key or not api_key.strip():
            return {
                "valid": False,
                "error": "API key cannot be empty",
                "can_force": False
            }
        
        api_key = api_key.strip()
        
        # Check for placeholder keys
        if self._is_placeholder_key(api_key):
            return {
                "valid": False,
                "error": "This appears to be a placeholder or test key",
                "can_force": True,
                "suggestion": "Please provide a real API key from your provider"
            }
        
        # Validate against provider pattern
        if provider_info["pattern"]:
            import re
            if not re.match(provider_info["pattern"], api_key):
                return {
                    "valid": False,
                    "error": f"Invalid key format for {provider}",
                    "details": provider_info["description"],
                    "examples": provider_info["examples"],
                    "can_force": True,
                    "suggestion": f"Expected format: {provider_info['description']}"
                }
        
        # Key is valid
        return {
            "valid": True,
            "message": f"Valid {provider} API key",
            "can_force": False
        }
    
    def _is_placeholder_key(self, api_key: str) -> bool:
        """
        Check if an API key is a placeholder/test key.
        
        Args:
            api_key: API key to check
            
        Returns:
            True if key is a placeholder, False otherwise
        """
        # PATCH: Cursor-2025-08-15 CL-LLM-QSF-Config-Audit <detect placeholder API keys>
        if not api_key or not api_key.strip():
            return True
        
        api_key = api_key.strip()
        
        # Check for common placeholder patterns
        placeholder_patterns = [
            "sk-ant-test-key",  # Specific Anthropic test key
            "your-api-key-here",
            "placeholder",
            "example",
            "demo",
            "sk-...",
            "sk-ant-..."
        ]
        
        # Check for exact matches first
        for pattern in placeholder_patterns:
            if api_key.lower() == pattern.lower():
                return True
        
        # Check for common test key patterns that are actually valid
        # These are legitimate test keys that should not be flagged
        valid_test_patterns = [
            "sk-env-test",  # Environment test keys
            "sk-ant-env-test",  # Anthropic env test keys
            "sk-test",  # OpenAI test keys
            "google-env-test",  # Google env test keys
            "groq-env-test"  # Groq env test keys
        ]
        
        # If it matches a valid test pattern, it's not a placeholder
        for pattern in valid_test_patterns:
            if api_key.lower().startswith(pattern.lower()):
                return False
        
        # Check for generic "test" in the middle (likely a placeholder)
        if "test-key" in api_key.lower() or "test_key" in api_key.lower():
            return True
        
        return False
    
    def _load_config(self) -> Dict[str, Any]:
        """Load LLM configuration from file and environment."""
        # PATCH: Cursor-2025-08-15 CL-LLM-Deterministic-Config <respect test mode and allow_config_fallback>
        if not self.allow_config_fallback or self._is_test_mode_disabled():
            logger.info("Config fallback disabled or test mode detected, skipping disk config load")
            return {
                "version": self.CONFIG_VERSION,
                "default_provider": "openai",
                "providers": {}
            }
        
        config = {
            "version": self.CONFIG_VERSION,
            "default_provider": "openai",
            "providers": {}
        }
        
        # First merge with environment variables
        config = self._merge_env_config(config)
        
        # Then load from file if exists (file takes precedence for existing providers)
        if self.llm_config_path.exists():
            try:
                with open(self.llm_config_path, 'r') as f:
                    file_config = json.load(f)
                    # Update existing providers, but preserve env-only providers
                    for provider, provider_config in file_config.get("providers", {}).items():
                        if provider in config["providers"]:
                            # File takes precedence for existing providers
                            config["providers"][provider].update(provider_config)
                        else:
                            # Add new providers from file
                            config["providers"][provider] = provider_config
                    
                    # Update other config fields
                    if "default_provider" in file_config:
                        config["default_provider"] = file_config["default_provider"]
                    if "version" in file_config:
                        config["version"] = file_config["version"]
                    
                    logger.info(f"Loaded LLM config from {self.llm_config_path}")
            except Exception as e:
                logger.warning(f"Failed to load LLM config: {e}")
        
        return config
    
    def _merge_env_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge environment variables with file configuration."""
        # PATCH: Cursor-2025-08-16 CL-ONBOARD-Provider-Key-Fix+UX <add XAI/Grok environment variable support>
        env_mappings = {
            "OPENAI_API_KEY": ("openai", "api_key"),
            "OPENAI_MODEL": ("openai", "model"),
            "ANTHROPIC_API_KEY": ("anthropic", "api_key"),
            "ANTHROPIC_MODEL": ("anthropic", "model"),
            "GOOGLE_API_KEY": ("google", "api_key"),
            "GOOGLE_MODEL": ("google", "model"),
            "XAI_API_KEY": ("xai", "api_key"),
            "XAI_MODEL": ("xai", "model"),
            "GROK_API_KEY": ("grok", "api_key"),
            "GROK_MODEL": ("grok", "model"),
            "GROQ_API_KEY": ("groq", "api_key"),
            "GROQ_MODEL": ("groq", "model"),
            "OLLAMA_HOST": ("ollama", "host"),
            "OLLAMA_MODEL": ("ollama", "model")
        }
        
        for env_var, (provider, field) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                if provider not in config["providers"]:
                    config["providers"][provider] = {}
                config["providers"][provider][field] = env_value
        
        return config
    
    def _load_roundtable_config(self) -> Dict[str, Any]:
        """Load roundtable configuration from file."""
        # PATCH: Cursor-2025-08-15 CL-LLM-Deterministic-Config <respect allow_config_fallback>
        if not self.allow_config_fallback:
            logger.info("Config fallback disabled, using default roundtable config")
            return {
                "version": 1,
                "active": "default",
                "tables": {
                    "default": {
                        "quorum": 2,
                        "merge_strategy": "vote_majority",
                        "participants": [
                            {"provider": "openai", "model": "gpt-4o-mini", "weight": 1.0, "max_tokens": 512},
                            {"provider": "anthropic", "model": "claude-3-haiku", "weight": 1.0, "max_tokens": 512}
                        ]
                    }
                }
            }
        
        config = {
            "version": 1,
            "active": "default",
            "tables": {
                "default": {
                    "quorum": 2,
                    "merge_strategy": "vote_majority",
                    "participants": [
                        {"provider": "openai", "model": "gpt-4o-mini", "weight": 1.0, "max_tokens": 512},
                        {"provider": "anthropic", "model": "claude-3-haiku", "weight": 1.0, "max_tokens": 512}
                    ]
                }
            }
        }
        
        if self.roundtable_config_path.exists():
            try:
                with open(self.roundtable_config_path, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
                    logger.info(f"Loaded roundtable config from {self.roundtable_config_path}")
            except Exception as e:
                logger.warning(f"Failed to load roundtable config: {e}")
        
        return config
    
    def _save_config(self) -> None:
        """Save LLM configuration to file with secure permissions."""
        try:
            # Create backup of existing config
            if self.llm_config_path.exists():
                backup_path = self.llm_config_path.with_suffix('.json.backup')
                self.llm_config_path.rename(backup_path)
            
            # Write new config
            with open(self.llm_config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
            
            # Set secure file permissions
            self._set_secure_permissions(self.llm_config_path)
            
            logger.info(f"LLM config saved to {self.llm_config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save LLM config: {e}")
            raise LLMStorageError(f"Failed to save configuration: {e}")
    
    def _save_roundtable_config(self) -> None:
        """Save roundtable configuration to file."""
        try:
            with open(self.roundtable_config_path, 'w') as f:
                json.dump(self._roundtable_config, f, indent=2)
            
            self._set_secure_permissions(self.roundtable_config_path)
            logger.info(f"Roundtable config saved to {self.roundtable_config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save roundtable config: {e}")
            raise LLMStorageError(f"Failed to save roundtable configuration: {e}")
    
    def _set_secure_permissions(self, file_path: Path) -> None:
        """Set secure file permissions (600 on POSIX, best-effort on Windows)."""
        try:
            if os.name == 'posix':
                file_path.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 600
            # Windows: best-effort - file is readable by current user only
        except Exception as e:
            logger.warning(f"Failed to set secure permissions: {e}")
    
    def add_provider(self, provider: str, config: Dict[str, Any]) -> None:
        """
        Add or update a provider configuration.
        
        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')
            config: Provider configuration dictionary
        """
        if provider not in self._config["providers"]:
            self._config["providers"][provider] = {}
        
        self._config["providers"][provider].update(config)
        self._save_config()
        
        logger.info(f"Provider {provider} configuration updated")
    
    def remove_provider(self, provider: str, purge: bool = False) -> None:
        """
        Remove a provider configuration.
        
        Args:
            provider: Provider name to remove
            purge: If True, completely remove from config file
        """
        if provider in self._config["providers"]:
            del self._config["providers"][provider]
            
            # Update default provider if needed
            if self._config["default_provider"] == provider:
                available_providers = list(self._config["providers"].keys())
                self._config["default_provider"] = available_providers[0] if available_providers else "openai"
            
            self._save_config()
            logger.info(f"Provider {provider} removed")
            
            # PATCH: Cursor-2025-08-16 CL-Onboarding-CLI-Fix+Wizard <add purge functionality>
            if purge:
                # Force a clean save to remove any traces
                self._save_config()
                logger.info(f"Provider {provider} purged from config")
    
    def set_default_provider(self, provider: str) -> None:
        """
        Set the default provider.
        
        Args:
            provider: Provider name to set as default
            
        Raises:
            LLMProviderError: If provider is not configured or has invalid API key
        """
        # PATCH: Cursor-2025-08-15 CL-LLM-QSF-Config-Audit <only allow configured providers as default>
        if provider not in self._config["providers"]:
            raise LLMProviderError(f"Provider {provider} not found in configuration")
        
        if not self._is_provider_configured(provider):
            raise LLMProviderError(f"Provider {provider} is not properly configured (missing or invalid API key)")
        
        self._config["default_provider"] = provider
        self._save_config()
        logger.info(f"Default provider set to {provider}")
    
    def validate_default_provider(self) -> Optional[str]:
        """
        Validate that the current default provider is actually configured.
        
        Returns:
            Valid default provider name, or None if current default is invalid
        """
        # PATCH: Cursor-2025-08-15 CL-LLM-QSF-Config-Audit <validate default provider configuration>
        current_default = self._config.get("default_provider")
        if not current_default:
            return None
        
        if not self._is_provider_configured(current_default):
            logger.warning(f"Default provider '{current_default}' is not properly configured, clearing default")
            self._config["default_provider"] = None
            self._save_config()
            return None
        
        return current_default
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """
        Get provider configuration.
        
        Args:
            provider: Provider name
            
        Returns:
            Provider configuration dictionary
        """
        return self._config["providers"].get(provider, {})
    
    def list_providers(self) -> List[str]:
        """
        List all configured providers.
        
        A provider is considered "configured" only if it has a valid API key
        (non-empty after stripping whitespace).
        
        Returns:
            List of provider names that are actually configured
        """
        # PATCH: Cursor-2025-08-15 CL-LLM-QSF-Config-Audit <only list providers with valid API keys>
        configured_providers = []
        for provider, config in self._config["providers"].items():
            if self._is_provider_configured(provider):
                configured_providers.append(provider)
        return configured_providers
    
    def _is_provider_configured(self, provider: str) -> bool:
        """
        Check if a provider is actually configured with a valid API key.
        
        Args:
            provider: Provider name
            
        Returns:
            True if provider has a valid API key, False otherwise
        """
        # PATCH: Cursor-2025-08-15 CL-LLM-QSF-Config-Audit <validate API key presence and validity>
        
        # Check if provider exists in config
        if provider not in self._config["providers"]:
            return False
        
        provider_config = self._config["providers"][provider]
        
        # For Ollama, check host instead of api_key
        if provider == "ollama":
            host = provider_config.get("host")
            return bool(host and host.strip())
        
        # For other providers, check api_key
        api_key = provider_config.get("api_key")
        if not api_key:
            return False
        
        # API key must be non-empty after stripping whitespace
        # and not be a placeholder/test key
        api_key = api_key.strip()
        if not api_key:
            return False
        
        # Check for common placeholder patterns
        placeholder_patterns = [
            "sk-ant-test-key",
            "sk-test-",
            "test-key",
            "placeholder",
            "your-api-key-here",
            "sk-...",
            "sk-ant-..."
        ]
        
        for pattern in placeholder_patterns:
            if pattern in api_key.lower():
                return False
        
        return True
    
    def list_all_providers(self) -> List[str]:
        """
        List all providers in config, including unset ones.
        
        This is useful for debugging and showing the full state.
        
        Returns:
            List of all provider names in config
        """
        # PATCH: Cursor-2025-08-15 CL-LLM-QSF-Config-Audit <provide access to full provider list>
        return list(self._config["providers"].keys())
    
    def get_provider_status(self, provider: str) -> Dict[str, Any]:
        """
        Get detailed status of a provider including configuration state.
        
        Args:
            provider: Provider name
            
        Returns:
            Dictionary with provider status information
        """
        # PATCH: Cursor-2025-08-15 CL-LLM-QSF-Config-Audit <provide detailed provider status>
        if provider not in self._config["providers"]:
            return {"configured": False, "status": "not_found", "source": None}
        
        provider_config = self._config["providers"][provider]
        is_configured = self._is_provider_configured(provider)
        
        # Determine source of configuration
        source = "config_file"
        if provider == "ollama":
            env_value = os.getenv("OLLAMA_HOST")
            if env_value:
                source = "environment"
        else:
            env_mappings = {
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY", 
                "google": "GOOGLE_API_KEY",
                "groq": "GROQ_API_KEY"
            }
            env_var = env_mappings.get(provider)
            if env_var and os.getenv(env_var):
                source = "environment"
        
        return {
            "configured": is_configured,
            "status": "configured" if is_configured else "unset",
            "source": source,
            "config": provider_config
        }
    
    def get_default_provider(self) -> str:
        """
        Get the default provider name.
        
        Returns:
            Default provider name
        """
        return self._config["default_provider"]
    
    def get_client(self, provider: Optional[str] = None) -> Any:
        """
        Get a client instance for the specified provider.
        
        Args:
            provider: Provider name (uses default if None)
            
        Returns:
            Provider client instance
            
        Raises:
            LLMProviderError: If provider is not configured
        """
        provider = provider or self._config["default_provider"]
        
        if provider not in self._config["providers"]:
            raise LLMProviderError(f"Provider {provider} not configured")
        
        provider_config = self._config["providers"][provider]
        
        try:
            if provider == "openai":
                return self._create_openai_client(provider_config)
            elif provider == "anthropic":
                return self._create_anthropic_client(provider_config)
            elif provider == "google":
                return self._create_google_client(provider_config)
            elif provider == "groq":
                return self._create_groq_client(provider_config)
            elif provider == "ollama":
                return self._create_ollama_client(provider_config)
            else:
                raise LLMProviderError(f"Unsupported provider: {provider}")
        except Exception as e:
            logger.error(f"Failed to create client for {provider}: {e}")
            raise LLMProviderError(f"Failed to create client for {provider}: {e}")
    
    def _create_openai_client(self, config: Dict[str, Any]) -> Any:
        """Create OpenAI client."""
        try:
            import openai
            api_key = config.get("api_key")
            base_url = config.get("base_url")
            model = config.get("model", "gpt-4o-mini")
            
            if not api_key:
                raise LLMProviderError("OpenAI API key not configured")
            
            client = openai.OpenAI(api_key=api_key)
            if base_url:
                client.base_url = base_url
            
            # Store model in client for reference
            client.model = model
            return client
            
        except ImportError:
            raise LLMProviderError("OpenAI package not installed")
    
    def _create_anthropic_client(self, config: Dict[str, Any]) -> Any:
        """Create Anthropic client."""
        try:
            import anthropic
            api_key = config.get("api_key")
            model = config.get("model", "claude-3-haiku")
            
            if not api_key:
                raise LLMProviderError("Anthropic API key not configured")
            
            client = anthropic.Anthropic(api_key=api_key)
            client.model = model
            return client
            
        except ImportError:
            raise LLMProviderError("Anthropic package not installed")
    
    def _create_google_client(self, config: Dict[str, Any]) -> Any:
        """Create Google client."""
        try:
            import google.generativeai as genai
            api_key = config.get("api_key")
            model = config.get("model", "gemini-1.5-pro")
            
            if not api_key:
                raise LLMProviderError("Google API key not configured")
            
            genai.configure(api_key=api_key)
            client = genai.GenerativeModel(model)
            client.model = model
            return client
            
        except ImportError:
            raise LLMProviderError("Google Generative AI package not installed")
    
    def _create_groq_client(self, config: Dict[str, Any]) -> Any:
        """Create Groq client."""
        try:
            import groq
            api_key = config.get("api_key")
            model = config.get("model", "llama-3-8b")
            
            if not api_key:
                raise LLMProviderError("Groq API key not configured")
            
            client = groq.Groq(api_key=api_key)
            client.model = model
            return client
            
        except ImportError:
            raise LLMProviderError("Groq package not installed")
    
    def _create_ollama_client(self, config: Dict[str, Any]) -> Any:
        """Create Ollama client."""
        try:
            import ollama
            host = config.get("host", "http://localhost:11434")
            model = config.get("model", "llama3")
            
            client = ollama.Client(host=host)
            client.model = model
            return client
            
        except ImportError:
            raise LLMProviderError("Ollama package not installed")
    
    def get_roundtable(self, name: str = "default") -> Dict[str, Any]:
        """
        Get roundtable configuration by name.
        
        Args:
            name: Roundtable name (defaults to "default")
            
        Returns:
            Roundtable configuration dictionary
        """
        return self._roundtable_config["tables"].get(name, {})
    
    def create_roundtable(self, name: str, config: Dict[str, Any]) -> None:
        """
        Create or update a roundtable configuration.
        
        Args:
            name: Roundtable name
            config: Roundtable configuration
        """
        self._roundtable_config["tables"][name] = config
        self._save_roundtable_config()
        logger.info(f"Roundtable {name} configuration updated")
    
    def activate_roundtable(self, name: str) -> None:
        """
        Activate a roundtable configuration.
        
        Args:
            name: Roundtable name to activate
        """
        if name not in self._roundtable_config["tables"]:
            raise LLMConfigError(f"Roundtable {name} not found")
        
        self._roundtable_config["active"] = name
        self._save_roundtable_config()
        logger.info(f"Roundtable {name} activated")
    
    def list_roundtables(self) -> List[str]:
        """
        List all roundtable configurations.
        
        Returns:
            List of roundtable names
        """
        return list(self._roundtable_config["tables"].keys())
    
    def get_active_roundtable(self) -> str:
        """
        Get the active roundtable name.
        
        Returns:
            Active roundtable name
        """
        return self._roundtable_config["active"]
    
    def __str__(self) -> str:
        """String representation with masked secrets."""
        config_copy = self._config.copy()
        
        # Mask API keys in providers
        for provider_config in config_copy["providers"].values():
            if "api_key" in provider_config and provider_config["api_key"]:
                provider_config["api_key"] = "********"
        
        # Include masked config in string representation
        return f"LLMManager(config_dir={self.config_dir}, providers={list(config_copy['providers'].keys())}, config={config_copy})"
    
    def __repr__(self) -> str:
        """Detailed representation with masked secrets."""
        return self.__str__()
    
    # PATCH: Cursor-2025-08-16 CL-LLM-Multiprovider-Base+Factory <add create_service and get_service methods>
    
                      allow_config_fallback: bool = True, offline: bool = None) -> Any:
        """
        Create an LLM service using the provider factory.
        
        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')
            allow_config_fallback: Whether to allow config file fallback
            offline: Whether to force offline mode (defaults to IOA_OFFLINE env var)
            
        Returns:
            Configured LLM service instance
            
        Raises:
            LLMProviderError: If service creation fails
        """
        try:
            from .llm_providers.factory import create_provider
            
            # Determine config directory based on allow_config_fallback
            config_dir = self.config_dir if allow_config_fallback else None
            
            # Resolve API key with precedence
            api_key = self.resolve_api_key(provider)
            
            # Create service
            service = create_provider(
                provider=provider,
                model=model,
                api_key=api_key,
                config_dir=config_dir,
                offline=offline
            )
            
            logger.info(f"Created {provider} service: {service}")
            return service
            
        except ImportError:
            raise LLMProviderError(f"Provider package not available for {provider}")
        except Exception as e:
            raise LLMProviderError(f"Failed to create {provider} service: {e}")
    
        """
        Get an LLM service (simple wrapper around create_service).
        
        Args:
            provider: Provider name
            **kwargs: Additional arguments passed to create_service
            
        Returns:
            Configured LLM service instance
        """
        return self.create_service(provider, model, **kwargs)
