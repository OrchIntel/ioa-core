"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

"""
DeepSeek Service Module for IOA Core

Implements the LLMService interface for DeepSeek models with offline
mode support and consistent error handling.
"""

import logging
from typing import Dict, Any, Optional
from .base import LLMService, LLMServiceError

# PATCH: Cursor-2025-08-16 CL-LLM-Multiprovider-Base+Factory <add DeepSeek service implementation>

logger = logging.getLogger(__name__)


class DeepSeekService(LLMService):
    """
    DeepSeek service provider implementation.
    
    Supports DeepSeek Coder, DeepSeek Chat, and other DeepSeek models with
    offline mode and consistent error handling.
    """
    
                 offline: bool = False):
        """
        Initialize DeepSeek service.
        
        Args:
            api_key: DeepSeek API key
            offline: Whether to run in offline mode
        """
        if model is None:
            model = "deepseek-coder"
        
        super().__init__("deepseek", model, api_key, offline)
        self._client = None
        
        if not offline and api_key:
            try:
                self._initialize_client()
            except Exception as e:
                logger.warning(f"Failed to initialize DeepSeek client: {e}")
    
    def _initialize_client(self):
        """Initialize DeepSeek client."""
        try:
            # DeepSeek uses a REST API, so we'll implement HTTP calls directly
            import requests
            self._client = requests
            logger.debug("DeepSeek client initialized successfully")
        except ImportError:
            raise LLMServiceError("Requests package not installed. Install with: pip install requests")
        except Exception as e:
            raise LLMServiceError(f"Failed to initialize DeepSeek client: {e}")
    
    def execute(self, prompt: str, **kwargs) -> str:
        """
        Execute a prompt using DeepSeek API.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            The model's response as a string
        """
        if self.offline:
            return self._get_offline_response(prompt)
        
        if not self._client:
            raise LLMServiceError("DeepSeek client not initialized. Check API key and internet connection.")
        
        try:
            # DeepSeek API endpoint
            url = "https://api.deepseek.com/v1/chat/completions"
            
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
            # PATCH: Cursor-2025-08-19 DISPATCH-GPT-20250819-023 enforce zero-retention if supported
            # Many providers accept vendor-specific flags; include best-effort toggles
            params.setdefault("metadata", {})
            params["metadata"].update({
                "data_retention": False,
                "retain": False,
            })
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                # Some providers use headers for retention opt-out
                "X-Data-Retention-Opt-Out": "true",
            }
            
            logger.debug(f"Executing DeepSeek request with model {self.model}")
            response = self._client.post(url, json=params, headers=headers, timeout=params["timeout"])
            
            if response.status_code == 200:
                data = response.json()
                if data.get("choices") and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    logger.debug(f"DeepSeek response received: {len(content)} characters")
                    return content
                else:
                    raise LLMServiceError("No response content received from DeepSeek")
            else:
                raise LLMServiceError(f"DeepSeek API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"DeepSeek API call failed: {e}")
            raise LLMServiceError(f"DeepSeek API call failed: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current DeepSeek model.
        
        Returns:
            Dictionary containing model information
        """
        return {
            "provider": "deepseek",
            "model": self.model,
            "model_type": "chat",
            "supports_streaming": True,
            "max_tokens": 32768,  # DeepSeek models typically have 32k context
            "supports_functions": True,
            "offline": self.offline,
            "available": self.is_available()
        }
    
    def _requires_api_key(self) -> bool:
        """DeepSeek always requires an API key."""
        return True
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to DeepSeek API.
        
        Returns:
            Connection test results
        """
        if self.offline:
            return {"status": "offline", "message": "Service running in offline mode"}
        
        if not self._client:
            return {"status": "error", "message": "Client not initialized"}
        
        try:
            # Simple test call with minimal tokens
            url = "https://api.deepseek.com/v1/chat/completions"
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
