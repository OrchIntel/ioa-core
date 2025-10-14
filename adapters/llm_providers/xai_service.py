"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

"""
XAI Service Module for IOA Core

Implements the LLMService interface for XAI Grok models with offline mode
support and consistent error handling. Supports both XAI_API_KEY and GROK_API_KEY.
"""

import logging
from typing import Dict, Any, Optional
from .base import LLMService, LLMServiceError

# PATCH: Cursor-2025-08-16 CL-LLM-Multiprovider-Base+Factory <add XAI service implementation>

logger = logging.getLogger(__name__)


class XAIService(LLMService):
    """
    XAI service provider implementation.
    
    Supports Grok-1, Grok-2, and other XAI models with offline mode
    and consistent error handling. Accepts both XAI_API_KEY and GROK_API_KEY.
    """
    
                 offline: bool = False):
        """
        Initialize XAI service.
        
        Args:
            api_key: XAI or Grok API key
            offline: Whether to run in offline mode
        """
        if model is None:
            model = "grok-4-latest"
        
        super().__init__("xai", model, api_key, offline)
        self._client = None
        
        if not offline and api_key:
            try:
                self._initialize_client()
            except Exception as e:
                logger.warning(f"Failed to initialize XAI client: {e}")
    
    def _initialize_client(self):
        """Initialize XAI client."""
        try:
            # XAI uses a REST API, so we'll implement HTTP calls directly
            import requests
            self._client = requests
            logger.debug("XAI client initialized successfully")
        except ImportError:
            raise LLMServiceError("Requests package not installed. Install with: pip install requests")
        except Exception as e:
            raise LLMServiceError(f"Failed to initialize XAI client: {e}")
    
    def execute(self, prompt: str, **kwargs) -> str:
        """
        Execute a prompt using XAI API.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            The model's response as a string
        """
        if self.offline:
            return self._get_offline_response(prompt)
        
        if not self._client:
            raise LLMServiceError("XAI client not initialized. Check API key and internet connection.")
        
        try:
            # XAI API endpoint
            url = "https://api.x.ai/v1/chat/completions"
            
            # Set default parameters
            params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 1000),
                "timeout": kwargs.get("timeout", 30)
            }
            
            # Override with any additional kwargs
            params.update({k: v for k, v in kwargs.items() if k not in {"metadata"}})
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            logger.debug(f"Executing XAI request with model {self.model}")
            response = self._client.post(url, json=params, headers=headers, timeout=params["timeout"])
            
            # Handle model not found (404) gracefully with proper fallback order - PATCH: Cursor-2025-09-09 DISPATCH-OSS-20250909-DEMO-LIVE-GEMINI-XAI-FIX
            if response.status_code == 404 and "model" in response.text.lower():
                fallback_models = ["grok-4-latest", "grok-2-latest", "grok-2-mini"]
                # Remove current model from fallback list if it's already there
                fallback_models = [m for m in fallback_models if m != self.model]
                
                for fallback_model in fallback_models:
                    logger.warning(f"XAI model not found: {self.model}. Retrying with fallback: {fallback_model}")
                    params["model"] = fallback_model
                    retry = self._client.post(url, json=params, headers=headers, timeout=params["timeout"])
                    if retry.status_code == 200:
                        data = retry.json()
                        if data.get("choices") and len(data["choices"]) > 0:
                            return data["choices"][0]["message"]["content"]
                
                # If all fallbacks failed, raise a detailed error with notes
                raise LLMServiceError(f"XAI API error after all fallbacks: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("choices") and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    logger.debug(f"XAI response received: {len(content)} characters")
                    return content
                else:
                    raise LLMServiceError("No response content received from XAI")
            else:
                raise LLMServiceError(f"XAI API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"XAI API call failed: {e}")
            raise LLMServiceError(f"XAI API call failed: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current XAI model.
        
        Returns:
            Dictionary containing model information
        """
        return {
            "provider": "xai",
            "model": self.model,
            "model_type": "chat",
            "supports_streaming": True,
            "max_tokens": 8192,  # Grok models typically have 8k context
            "supports_functions": True,
            "offline": self.offline,
            "available": self.is_available()
        }
    
    def _requires_api_key(self) -> bool:
        """XAI always requires an API key."""
        return True
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to XAI API.
        
        Returns:
            Connection test results
        """
        if self.offline:
            return {"status": "offline", "message": "Service running in offline mode"}
        
        if not self._client:
            return {"status": "error", "message": "Client not initialized"}
        
        try:
            # Simple test call with minimal tokens
            url = "https://api.x.ai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 1
            }
            
            response = self._client.post(url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return {
                    "status": "success", 
                    "message": "Connection successful",
                    "model": self.model,
                    "response_time": "fast"
                }
            else:
                return {"status": "error", "message": f"API error: {response.status_code}"}
                
        except Exception as e:
            return {"status": "error", "message": f"Connection failed: {e}"}
