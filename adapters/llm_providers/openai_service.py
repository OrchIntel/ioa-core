"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

"""
OpenAI Service Module for IOA Core

Implements the LLMService interface for OpenAI GPT models, wrapping existing
OpenAI client logic with offline mode support and consistent error handling.
"""

import logging
from typing import Dict, Any, Optional
from .base import LLMService, LLMServiceError

# PATCH: Cursor-2025-08-16 CL-LLM-Multiprovider-Base+Factory <add OpenAI service implementation>

logger = logging.getLogger(__name__)


class OpenAIService(LLMService):
    """
    OpenAI service provider implementation.
    
    Supports GPT-4, GPT-3.5, and other OpenAI models with offline mode
    and consistent error handling.
    """
    
                 offline: bool = False):
        """
        Initialize OpenAI service.
        
        Args:
            api_key: OpenAI API key
            offline: Whether to run in offline mode
        """
        if model is None:
            model = "gpt-4"
        
        super().__init__("openai", model, api_key, offline)
        self._client = None
        
        if not offline and api_key:
            try:
                self._initialize_client()
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
    
    def _initialize_client(self):
        """Initialize OpenAI client (SDK v1)."""
        try:
            from openai import OpenAI  # SDK v1 client
            self._client = OpenAI(api_key=self.api_key)
            logger.debug("OpenAI client initialized successfully (v1)")
        except ImportError:
            raise LLMServiceError("OpenAI package not installed. Install with: pip install openai>=1.0.0")
        except Exception as e:
            raise LLMServiceError(f"Failed to initialize OpenAI client: {e}")
    
    def execute(self, prompt: str, **kwargs) -> str:
        """
        Execute a prompt using OpenAI API.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            The model's response as a string
        """
        if self.offline:
            return self._get_offline_response(prompt)
        
        if not self._client:
            raise LLMServiceError("OpenAI client not initialized. Check API key and internet connection.")
        
        try:
            # Set default parameters
            params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 1000),
                "timeout": kwargs.get("timeout", 30)
            }
            
            # Override with any additional kwargs
            params.update(kwargs)
            
            # NOTE: The OpenAI v1 API does not accept custom metadata fields like
            # booleans for data retention hints. Avoid sending unsupported params
            # to prevent 400 invalid_request_error responses.

            logger.debug(f"Executing OpenAI request with model {self.model}")
            # SDK v1 chat completion
            response = self._client.chat.completions.create(**params)
            
            # Extract response content
            if response and getattr(response, "choices", None) and len(response.choices) > 0:
                content = response.choices[0].message.content
                logger.debug(f"OpenAI response received: {len(content)} characters")
                return content
            else:
                raise LLMServiceError("No response content received from OpenAI")
                
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise LLMServiceError(f"OpenAI API call failed: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current OpenAI model.
        
        Returns:
            Dictionary containing model information
        """
        return {
            "provider": "openai",
            "model": self.model,
            "model_type": "chat",
            "supports_streaming": True,
            "max_tokens": 8192 if "gpt-4" in self.model else 4096,
            "supports_functions": True,
            "offline": self.offline,
            "available": self.is_available()
        }
    
    def _requires_api_key(self) -> bool:
        """OpenAI always requires an API key."""
        return True
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to OpenAI API.
        
        Returns:
            Connection test results
        """
        if self.offline:
            return {"status": "offline", "message": "Service running in offline mode"}
        
        if not self._client:
            return {"status": "error", "message": "Client not initialized"}
        
        try:
            # Simple test call with minimal tokens
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1,
                timeout=10
            )
            
            if response.choices and len(response.choices) > 0:
                return {
                    "status": "success", 
                    "message": "Connection successful",
                    "model": self.model,
                    "response_time": "fast"
                }
            else:
                return {"status": "error", "message": "No response received"}
                
        except Exception as e:
            return {"status": "error", "message": f"Connection failed: {e}"}
