""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

"""
Base LLM Service Module for IOA Core

Defines the abstract interface and common functionality for all LLM service providers.
Includes HTTP utilities, API key masking, validation hooks, and offline mode support.
"""

import re
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from datetime import datetime, timezone

# PATCH: Cursor-2025-08-16 CL-LLM-Multiprovider-Base+Factory <add base service class>

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Base exception for LLM service operations."""
    pass


class LLMService(ABC):
    """
    Abstract base class for LLM service providers.
    
    Defines the interface that all LLM providers must implement, including
    execution methods, model information, and offline mode support.
    """
    
                 api_key: Optional[str] = None, offline: bool = False):
        """
        Initialize LLM service.
        
        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')
            api_key: API key for the provider
            offline: Whether to run in offline mode
        """
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.offline = offline
        self._validate_initialization()
    
    def _validate_initialization(self):
        """Validate service initialization parameters."""
        if not self.provider:
            raise LLMServiceError("Provider name is required")
        
        if not self.offline and not self.api_key and self._requires_api_key():
            logger.warning(f"No API key provided for {self.provider}, service may not function")
    
    def _requires_api_key(self) -> bool:
        """Check if this provider requires an API key."""
        return self.provider not in ["ollama"]
    
    @abstractmethod
    def execute(self, prompt: str, **kwargs) -> str:
        """
        Execute a prompt and return the response.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional provider-specific parameters
            
        Returns:
            The model's response as a string
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary containing model information
        """
        pass
    
    def is_available(self) -> bool:
        """
        Check if the service is available for use.
        
        Returns:
            True if the service can be used, False otherwise
        """
        if self.offline:
            return True
        return self._requires_api_key() and bool(self.api_key)
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get provider information and status.
        
        Returns:
            Dictionary containing provider information
        """
        return {
            "provider": self.provider,
            "model": self.model,
            "offline": self.offline,
            "requires_key": self._requires_api_key(),
            "has_key": bool(self.api_key),
            "available": self.is_available(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _mask_api_key(self, key: str) -> str:
        """
        Mask API key for logging and display.
        
        Args:
            key: The API key to mask
            
        Returns:
            Masked version of the key (first 4 chars + ... + last 4 chars)
        """
        if not key or len(key) < 8:
            return "***"
        return f"{key[:4]}...{key[-4:]}"
    
    def _validate_api_key_format(self, key: str) -> Dict[str, Any]:
        """
        Validate API key format for this provider.
        
        Args:
            key: The API key to validate
            
        Returns:
            Validation result dictionary
        """
        if not key:
            return {"valid": False, "reason": "empty", "can_force": False}
        
        if not self._requires_api_key():
            return {"valid": True, "reason": "not_required", "can_force": False}
        
        # Provider-specific validation patterns
        patterns = {
            "openai": r"^sk-[A-Za-z0-9]{20,}$",
            "anthropic": r"^sk-ant-[A-Za-z0-9_-]{20,}$",
            "xai": r"^xai-[A-Za-z0-9._-]{20,}$",
            "grok": r"^grok_[A-Za-z0-9._-]{20,}$",
            "google": r"^AIza[0-9A-Za-z_-]{30,}$",
            "deepseek": r"^sk-[A-Za-z0-9]{20,}$",
        }
        
        pattern = patterns.get(self.provider)
        if not pattern:
            # Unknown provider, assume valid
            return {"valid": True, "reason": "format", "can_force": True}
        
        if re.match(pattern, key):
            return {"valid": True, "reason": "format", "can_force": False}
        else:
            return {"valid": False, "reason": "format", "can_force": True}
    
    def _get_offline_response(self, prompt: str) -> str:
        """
        Generate offline response for testing and development.
        
        Args:
            prompt: The input prompt
            
        Returns:
            Deterministic offline response
        """
        # Handle None and empty prompts gracefully
        if prompt is None:
            prompt = ""
        
        # Echo first 20 characters of prompt as a deterministic response
        truncated = prompt[:20]
        if len(prompt) > 20:
            truncated += "..."
        return f"[OFFLINE-{self.provider.upper()}] {truncated}"
    
    def __str__(self) -> str:
        """String representation of the service."""
        status = "OFFLINE" if self.offline else "ONLINE"
        key_status = "NO_KEY" if not self.api_key else "HAS_KEY"
        return f"{self.provider}({self.model or 'default'})[{status},{key_status}]"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"LLMService(provider='{self.provider}', model='{self.model}', offline={self.offline})"
