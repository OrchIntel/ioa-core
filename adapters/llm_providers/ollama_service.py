"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

"""
Ollama Service Module for IOA Core

Implements the LLMService interface for local Ollama models with offline
mode support, turbo preset for low-latency inference, and deterministic
model selection without remote pulls.
"""

import os
import logging
from typing import Dict, Any, Optional
from .base import LLMService, LLMServiceError
from .ollama_utils import OllamaTurboPreset, get_ollama_mode

# PATCH: Cursor-2025-08-16 CL-LLM-Multiprovider-Base+Factory <add Ollama service implementation>
# PATCH: Cursor-2025-09-07 DISPATCH-OSS-20250907-OLLAMA-FIX <add turbo preset and deterministic model selection>

logger = logging.getLogger(__name__)


class OllamaService(LLMService):
    """
    Ollama service provider implementation.
    
    Supports local Ollama models like Llama, Mistral, CodeLlama with offline
    mode and consistent error handling. No API key required.
    """
    
                 offline: bool = False):
        """
        Initialize Ollama service.
        
        Args:
            api_key: Not used for Ollama (local service)
            offline: Whether to run in offline mode
        """
        if model is None:
            model = "llama3"
        
        # For Ollama, api_key parameter contains the host
        # PATCH: Cursor-2025-09-10 DISPATCH-EXEC-20250910-PR006-FINAL-GREEN-REPAIR-v2
        # Do not assume localhost when OLLAMA_HOST is unset; treat as unavailable.
        host = api_key if api_key else self._get_ollama_host()
        
        super().__init__("ollama", model, None, offline)  # Always pass None as api_key
        self._host = host
        self._client = None
        
        if not offline and host:
            try:
                self._initialize_client()
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama client: {e}")
    
    def _get_ollama_host(self) -> Optional[str]:
        """Get Ollama host from environment; return None if not set."""
        return os.getenv("OLLAMA_HOST")
    
    def _initialize_client(self):
        """Initialize Ollama client."""
        try:
            import requests
            self._client = requests
            logger.debug(f"Ollama client initialized for host: {self._host}")
        except ImportError:
            raise LLMServiceError("Requests package not installed. Install with: pip install requests")
        except Exception as e:
            raise LLMServiceError(f"Failed to initialize Ollama client: {e}")
    
    def execute(self, prompt: str, **kwargs) -> str:
        """
        Execute a prompt using local Ollama API with turbo preset support.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            The model's response as a string
        """
        if self.offline:
            return self._get_offline_response(prompt)
        
        if not self._client:
            raise LLMServiceError("Ollama client not initialized. Check if Ollama is running.")
        
        try:
            # Ollama API endpoint
            url = f"{self._host}/api/generate"
            
            # Get mode and preset options
            mode = get_ollama_mode()
            if mode in ["turbo", "turbo_local", "turbo_cloud"]:
                preset_options = OllamaTurboPreset.get_turbo_options()
            else:
                preset_options = OllamaTurboPreset.get_standard_options()
            
            # Set default parameters with preset options
            params = {
                "model": self.model,
                "prompt": prompt,
                "options": preset_options,
                "timeout": kwargs.get("timeout", 30)
            }
            
            # Override with any additional kwargs (but preserve options structure)
            for key, value in kwargs.items():
                if key == "timeout":
                    params["timeout"] = value
                elif key in ["temperature", "max_tokens", "num_predict", "top_p", "repeat_penalty", "num_ctx", "num_thread", "cache", "mirostat"]:
                    params["options"][key] = value
            
            logger.debug(f"Executing Ollama request with model {self.model} in {mode} mode")
            response = self._client.post(url, json=params, timeout=params["timeout"])
            
            if response.status_code == 200:
                data = response.json()
                if data.get("response"):
                    content = data["response"]
                    logger.debug(f"Ollama response received: {len(content)} characters")
                    return content
                else:
                    raise LLMServiceError("No response content received from Ollama")
            else:
                raise LLMServiceError(f"Ollama API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            raise LLMServiceError(f"Ollama API call failed: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current Ollama model.
        
        Returns:
            Dictionary containing model information
        """
        return {
            "provider": "ollama",
            "model": self.model,
            "model_type": "local",
            "supports_streaming": True,
            "max_tokens": 4096,  # Typical for local models
            "supports_functions": False,  # Local models typically don't support functions
            "offline": self.offline,
            "available": self.is_available(),
            "host": self._host
        }
    
    def _requires_api_key(self) -> bool:
        """Ollama doesn't require an API key."""
        return False
    
    def is_available(self) -> bool:
        """
        Check if Ollama service is available.
        
        Returns:
            True if Ollama is running and accessible, False otherwise
        """
        if self.offline:
            return True
        
        # If no host is configured, service is not available by definition
        if not getattr(self, "_host", None):
            return False

        if not self._client:
            return False
        
        try:
            # Check if Ollama is running
            response = self._client.get(f"{self._host}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to Ollama service.
        
        Returns:
            Connection test results
        """
        if self.offline:
            return {"status": "offline", "message": "Service running in offline mode"}
        
        if not self._client:
            return {"status": "error", "message": "Client not initialized"}
        
        try:
            # Check if Ollama is running
            response = self._client.get(f"{self._host}/api/tags", timeout=5)
            
            if response.status_code == 200:
                return {
                    "status": "success", 
                    "message": "Ollama service is running",
                    "host": self._host,
                    "response_time": "fast"
                }
            else:
                return {"status": "error", "message": f"Ollama service error: {response.status_code}"}
                
        except Exception as e:
            return {"status": "error", "message": f"Connection failed: {e}"}
    
    def list_models(self) -> Dict[str, Any]:
        """
        List available Ollama models.
        
        Returns:
            Dictionary containing available models
        """
        if not self._client:
            return {"error": "Client not initialized"}
        
        try:
            response = self._client.get(f"{self._host}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "models": data.get("models", []),
                    "host": self._host
                }
            else:
                return {"error": f"Failed to list models: {response.status_code}"}
        except Exception as e:
            return {"error": f"Failed to list models: {e}"}
