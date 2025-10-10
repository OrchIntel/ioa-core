""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

"""
Anthropic Service Module for IOA Core

Implements the LLMService interface for Anthropic Claude models with offline
mode support and consistent error handling.
"""

import logging
from typing import Dict, Any, Optional
from .base import LLMService, LLMServiceError

# PATCH: Cursor-2025-08-16 CL-LLM-Multiprovider-Base+Factory <add Anthropic service implementation>

logger = logging.getLogger(__name__)


class AnthropicService(LLMService):
    """
    Anthropic service provider implementation.
    
    Supports Claude 3 Haiku, Sonnet, Opus, and other Anthropic models with
    offline mode and consistent error handling.
    """
    
                 offline: bool = False):
        """
        Initialize Anthropic service.
        
        Args:
            api_key: Anthropic API key
            offline: Whether to run in offline mode
        """
        if model is None:
            model = "claude-3-sonnet"
        
        super().__init__("anthropic", model, api_key, offline)
        self._client = None
        
        if not offline and api_key:
            try:
                self._initialize_client()
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client: {e}")
    
    def _initialize_client(self):
        """Initialize Anthropic client."""
        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
            logger.debug("Anthropic client initialized successfully")
        except ImportError:
            raise LLMServiceError("Anthropic package not installed. Install with: pip install anthropic")
        except Exception as e:
            raise LLMServiceError(f"Failed to initialize Anthropic client: {e}")
    
    def execute(self, prompt: str, **kwargs) -> str:
        """
        Execute a prompt using Anthropic API.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            The model's response as a string
        """
        if self.offline:
            return self._get_offline_response(prompt)
        
        if not self._client:
            raise LLMServiceError("Anthropic client not initialized. Check API key and internet connection.")
        
        try:
            # Set default parameters
            params = {
                "model": self.model,
                "max_tokens": kwargs.get("max_tokens", 1000),
                "temperature": kwargs.get("temperature", 0.7),
                "timeout": kwargs.get("timeout", 30)
            }
            
            # Anthropic uses 'messages' format
            messages = [{"role": "user", "content": prompt}]
            
            logger.debug(f"Executing Anthropic request with model {self.model}")
            response = self._client.messages.create(
                messages=messages,
                **params
            )
            
            # Extract response content
            if response.content and len(response.content) > 0:
                content = response.content[0].text
                logger.debug(f"Anthropic response received: {len(content)} characters")
                return content
            else:
                raise LLMServiceError("No response content received from Anthropic")
                
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise LLMServiceError(f"Anthropic API call failed: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current Anthropic model.
        
        Returns:
            Dictionary containing model information
        """
        return {
            "provider": "anthropic",
            "model": self.model,
            "model_type": "chat",
            "supports_streaming": True,
            "max_tokens": 200000,  # Claude 3 models have very high token limits
            "supports_functions": True,
            "offline": self.offline,
            "available": self.is_available()
        }
    
    def _requires_api_key(self) -> bool:
        """Anthropic always requires an API key."""
        return True
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to Anthropic API.
        
        Returns:
            Connection test results
        """
        if self.offline:
            return {"status": "offline", "message": "Service running in offline mode"}
        
        if not self._client:
            return {"status": "error", "message": "Client not initialized"}
        
        try:
            # Simple test call with minimal tokens
            response = self._client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1,
                timeout=10
            )
            
            if response.content and len(response.content) > 0:
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
