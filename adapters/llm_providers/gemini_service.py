""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

"""
Google Gemini Service Module for IOA Core

Implements the LLMService interface for Google Gemini models with offline
mode support and consistent error handling.
"""

import logging
from typing import Dict, Any, Optional
from .base import LLMService, LLMServiceError

# PATCH: Cursor-2025-08-16 CL-LLM-Multiprovider-Base+Factory <add Google Gemini service implementation>

logger = logging.getLogger(__name__)


class GeminiService(LLMService):
    """
    Google Gemini service provider implementation.
    
    Supports Gemini 1.5 Pro, Flash, and other Google models with offline
    mode and consistent error handling.
    """
    
                 offline: bool = False):
        """
        Initialize Google Gemini service.
        
        Args:
            api_key: Google API key for Gemini
            offline: Whether to run in offline mode
        """
        if model is None:
            model = "gemini-1.5-flash"
        
        super().__init__("google", model, api_key, offline)
        self._client = None
        
        if not offline and api_key:
            try:
                self._initialize_client()
            except Exception as e:
                logger.warning(f"Failed to initialize Google Gemini client: {e}")
    
    def _initialize_client(self):
        """Initialize Google Gemini client."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._client = genai
            logger.debug("Google Gemini client initialized successfully")
        except ImportError:
            raise LLMServiceError("Google Generative AI package not installed. Install with: pip install google-generativeai")
        except Exception as e:
            raise LLMServiceError(f"Failed to initialize Google Gemini client: {e}")
    
    def execute(self, prompt: str, **kwargs) -> str:
        """
        Execute a prompt using Google Gemini API.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            The model's response as a string
        """
        if self.offline:
            return self._get_offline_response(prompt)
        
        if not self._client:
            raise LLMServiceError("Google Gemini client not initialized. Check API key and internet connection.")
        
        try:
            # Set default parameters - PATCH: Cursor-2025-09-09 DISPATCH-OSS-20250909-DEMO-LIVE-GEMINI-XAI-FIX remove timeout from GenerationConfig
            generation_config = {
                "temperature": kwargs.get("temperature", 0.7),
                "max_output_tokens": kwargs.get("max_tokens", 1000)
            }
            
            # Override with any additional kwargs (except timeout)
            for key, value in kwargs.items():
                if key not in ["timeout", "request_options"]:
                    generation_config[key] = value
            
            logger.debug(f"Executing Google Gemini request with model {self.model}")
            
            # Create model instance
            # PATCH: Cursor-2025-08-19 DISPATCH-GPT-20250819-023 enforce zero-retention if supported by Vertex/Gemini
            # Google Generative AI SDK supports safety, system params; retention isn't first-class,
            # but we include best-effort hints via request options
            request_options = kwargs.get("request_options", {})
            request_options.update({
                "headers": {"X-Data-Retention-Opt-Out": "true"},
                "timeout": kwargs.get("timeout", 30)
            })
            model = self._client.GenerativeModel(self.model, generation_config=generation_config)
            
            # Generate response
            response = model.generate_content(prompt, request_options=request_options)
            
            if response.text:
                logger.debug(f"Google Gemini response received: {len(response.text)} characters")
                return response.text
            else:
                raise LLMServiceError("No response content received from Google Gemini")
                
        except Exception as e:
            logger.error(f"Google Gemini API call failed: {e}")
            raise LLMServiceError(f"Google Gemini API call failed: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current Google Gemini model.
        
        Returns:
            Dictionary containing model information
        """
        return {
            "provider": "google",
            "model": self.model,
            "model_type": "generative",
            "supports_streaming": True,
            "max_tokens": 1000000,  # Gemini 1.5 Pro has 1M token context
            "supports_functions": True,
            "offline": self.offline,
            "available": self.is_available()
        }
    
    def _requires_api_key(self) -> bool:
        """Google Gemini always requires an API key."""
        return True
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to Google Gemini API.
        
        Returns:
            Connection test results
        """
        if self.offline:
            return {"status": "offline", "message": "Service running in offline mode"}
        
        if not self._client:
            return {"status": "error", "message": "Client not initialized"}
        
        try:
            # Simple test call with minimal tokens
            model = self._client.GenerativeModel(self.model)
            response = model.generate_content("Hello", generation_config={"max_output_tokens": 1})
            
            if response.text:
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
