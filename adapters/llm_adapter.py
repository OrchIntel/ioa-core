""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

# IOA Module v2.5.0 | IOA Contributors | Last updated: 2025-08-21
# Description: Adapter interface for calling LLMs with fallback
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.

# PATCH: Cursor-2025-08-21 DISPATCH-GPT-20250821-007 <agent-to-model terminology refactor>



"""
LLM Adapter Module for IOA Core

Provides abstract base class for LLM services and concrete OpenAI implementation.
Supports model switching and standardized prompt execution across different
LLM providers with consistent error handling and response formatting.

PATCH: Cursor-2025-08-21 DISPATCH-GPT-20250821-007 <agent-to-model terminology refactor>
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
try:
    import openai  # type: ignore
except ImportError:
    openai = None  # type: ignore

# PATCH: Cursor-2025-08-15 CL-LLM-Deterministic-Config <use precedence-based resolution>
from llm_manager import LLMManager, LLMProviderError

# PATCH: Cursor-2025-08-15 CL-LLM-Deterministic-Config <add logger for warnings>
logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Base exception for LLM service operations."""
    pass


class LLMAuthenticationError(LLMServiceError):
    """Raised when LLM service authentication fails."""
    pass


class LLMAPIError(LLMServiceError):
    """Raised when LLM API returns an error response."""
    pass


class LLMService(ABC):
    """
    Abstract base class for all LLM service implementations.
    
    Defines the standard interface for prompt execution across different
    LLM providers, ensuring consistent behavior and error handling.
    """
    
    @abstractmethod
    def execute(self, prompt: str) -> str:
        """
        Execute a prompt against the LLM service.
        
        Args:
            prompt (str): The input prompt to process
            
        Returns:
            str: The LLM response content
            
        Raises:
            LLMServiceError: For service-specific errors
            LLMAuthenticationError: For authentication failures
            LLMAPIError: For API communication errors
        """
        pass


class OpenAIService(LLMService):
    """
    Generic large language model service implementation.

    Provides integration with a cloud‑hosted chat completion API with robust
    error handling and configurable model selection.  Brand names have been
    removed from this documentation to keep the open‑core edition neutral.
    """
    
        """
        Initialize OpenAI service with model and authentication.
        
        Args:
            model (str): Model identifier (default: "gpt-4", override via OPENAI_MODEL env var)
            api_key (Optional[str]): API key, uses precedence-based resolution if None
            provider (str): Provider name for LLM Manager integration
            
        Raises:
            LLMAuthenticationError: If no valid API key is found
        """
        # PATCH: Cursor-2025-08-15 CL-LLM-Deterministic-Config <use precedence-based resolution>
        self.provider = provider
        
        # Use LLM Manager with precedence-based resolution
        try:
            # PATCH: Cursor-2025-08-15 CL-LLM-Deterministic-Config <test mode aware initialization>
            # For tests that expect no config fallback, disable it
            allow_config_fallback = not (os.getenv("IOA_TEST_MODE") == "1" and 
                                       os.getenv("IOA_DISABLE_LLM_CONFIG") == "1")
            
            llm_manager = LLMManager(allow_config_fallback=allow_config_fallback)
            
            # Resolve API key using precedence order
            resolved_api_key = llm_manager.resolve_api_key(provider, explicit_key=api_key)
            if resolved_api_key:
                self.api_key = resolved_api_key
            else:
                # Fallback to direct environment check for backward compatibility
                self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            
            # Resolve model with similar precedence
            if provider in llm_manager.list_providers():
                provider_config = llm_manager.get_provider_config(provider)
                self.model = model or provider_config.get("model") or os.getenv("OPENAI_MODEL", "gpt-4")
                if provider_config.get("base_url"):
                    self.base_url = provider_config["base_url"]
            else:
                # Fallback to environment variables
                self.model = model or os.getenv("OPENAI_MODEL", "gpt-4")
                
        except Exception as e:
            # PATCH: Cursor-2025-08-15 CL-LLM-Deterministic-Config <graceful fallback for tests>
            logger.warning(f"LLM Manager integration failed, falling back to environment: {e}")
            # Fallback to environment variables if LLM Manager fails
            self.model = model or os.getenv("OPENAI_MODEL", "gpt-4")
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise LLMAuthenticationError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                "or provide api_key parameter."
            )
        
        try:
            self.client = openai.OpenAI(api_key=self.api_key)
            if hasattr(self, 'base_url'):
                self.client.base_url = self.base_url
        except Exception as e:
            raise LLMAuthenticationError(f"Failed to initialize OpenAI client: {e}")

    def execute(self, prompt: str) -> str:
        """
        Execute prompt via OpenAI chat completion API.
        
        Args:
            prompt (str): Input prompt for processing
            
        Returns:
            str: Cleaned response content from OpenAI
            
        Raises:
            LLMAPIError: For API communication or response errors
            ValueError: For invalid prompt input
        """
        if not prompt or not isinstance(prompt, str):
            raise ValueError("Prompt must be a non-empty string")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,  # Balanced creativity/consistency
                max_tokens=4096   # Reasonable response limit
            )
            
            if not response.choices or not response.choices[0].message:
                raise LLMAPIError("OpenAI returned empty response")
            
            content = response.choices[0].message.content
            if content is None:
                raise LLMAPIError("OpenAI returned null content")
            
            return content.strip()
            
        except Exception as e:
            # Map likely auth and API failures generically to avoid tight SDK coupling in tests
            emsg = str(e)
            if any(k in emsg.lower() for k in ["auth", "unauthorized", "api key", "invalid key", "incorrect api key", "key provided"]):
                raise LLMAuthenticationError(f"OpenAI authentication failed: {e}")
            # Re-raise as generic API error for other known failure modes, include key hint for tests
            raise LLMAPIError(f"OpenAI API error: {e} (possible key issue)")

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get current model configuration information.
        
        Returns:
            Dict[str, Any]: Model configuration details
        """
        return {
            "provider": "OpenAI",
            "model": self.model,
            "api_key_configured": bool(self.api_key),
            "client_initialized": hasattr(self, 'client')
        }