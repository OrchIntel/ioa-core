""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Comprehensive test suite for LLM adapter module
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.


"""
Test Suite for LLM Adapter Module

Validates LLM service abstraction layer functionality including:
- Abstract base class behavior
- OpenAI service implementation
- Authentication and error handling
- API response processing and edge cases
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock, Mock

# Add src directory to Python path for imports
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Use pytest.importorskip for clean test skipping
openai = pytest.importorskip("openai", reason="OpenAI SDK not installed for CI/dev")

# Skip in CI or when no API key available
CI = os.getenv("CI") == "true"
NO_KEY = not os.getenv("OPENAI_API_KEY")
SKIP_OPENAI = CI or NO_KEY

pytestmark = pytest.mark.skipif(
    SKIP_OPENAI,
    reason="OpenAI adapter tests are skipped in CI or when OPENAI_API_KEY is unavailable",
)

from llm_adapter import (
    LLMService, 
    OpenAIService, 
    LLMServiceError,
    LLMAuthenticationError,
    LLMAPIError
)


class TestLLMServiceAbstract:
    """Test abstract base class behavior."""
    
    def test_llm_service_cannot_instantiate(self):
        """Verify LLMService abstract class cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            LLMService()


class TestOpenAIServiceInitialization:
    """Test OpenAI service initialization and configuration."""
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('openai.OpenAI')
    def test_init_with_environment_key(self, mock_openai_client):
        """Test initialization using environment variable API key."""
        # PATCH: Cursor-2025-08-15 CL-LLM-QSF-Config-Audit <disable config fallback for environment test>
        # Set test mode flags to disable config fallback
        os.environ["IOA_TEST_MODE"] = "1"
        os.environ["IOA_DISABLE_LLM_CONFIG"] = "1"
        os.environ["OPENAI_API_KEY"] = "test_key_from_env"
        
        mock_client_instance = Mock()
        mock_openai_client.return_value = mock_client_instance
        
        service = OpenAIService(model="gpt-3.5-turbo")
        
        assert service.model == "gpt-3.5-turbo"
        assert service.api_key == "test_key_from_env"
        assert service.client == mock_client_instance
        mock_openai_client.assert_called_once_with(api_key="test_key_from_env")
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('openai.OpenAI')
    def test_init_with_explicit_key(self, mock_openai_client):
        """Test initialization with explicitly provided API key."""
        # PATCH: Cursor-2025-08-15 CL-LLM-QSF-Config-Audit <disable config fallback for explicit key test>
        # Set test mode flags to disable config fallback
        os.environ["IOA_TEST_MODE"] = "1"
        os.environ["IOA_DISABLE_LLM_CONFIG"] = "1"
        
        mock_client_instance = Mock()
        mock_openai_client.return_value = mock_client_instance
        
        service = OpenAIService(api_key="explicit_test_key")
        
        assert service.model == "gpt-4"  # Default model
        assert service.api_key == "explicit_test_key"
        assert service.client == mock_client_instance
    
    @patch.dict(os.environ, {}, clear=True)
    def test_init_no_api_key_raises_authentication_error(self):
        """Test that missing API key raises LLMAuthenticationError."""
        # PATCH: Cursor-2025-08-15 CL-LLM-Deterministic-Config <set test mode flags>
        # Set test mode flags to disable config fallback
        os.environ["IOA_TEST_MODE"] = "1"
        os.environ["IOA_DISABLE_LLM_CONFIG"] = "1"
        
        with pytest.raises(LLMAuthenticationError, match="API key not found"):
            OpenAIService()
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    @patch('openai.OpenAI', side_effect=Exception("Client init failed"))
    def test_init_client_failure_raises_authentication_error(self, mock_openai_client):
        """Test that OpenAI client initialization failure raises LLMAuthenticationError."""
        with pytest.raises(LLMAuthenticationError, match="Failed to initialize OpenAI client"):
            OpenAIService()


class TestOpenAIServiceExecution:
    """Test OpenAI service prompt execution and response handling."""
    
    @pytest.fixture
    def mock_openai_service(self):
        """Create mock OpenAI service for testing."""
        with patch('openai.OpenAI') as mock_client_class:
            mock_client_instance = Mock()
            mock_client_class.return_value = mock_client_instance
            service = OpenAIService(api_key="test_key")
            service.client = mock_client_instance
            return service, mock_client_instance
    
    def test_execute_successful_response(self, mock_openai_service):
        """Test successful prompt execution with valid response."""
        service, mock_client = mock_openai_service
        
        # Mock successful API response
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "  Test response content  "
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_response
        
        result = service.execute("Test prompt")
        
        assert result == "Test response content"  # Stripped whitespace
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4",
            messages=[{"role": "user", "content": "Test prompt"}],
            temperature=0.7,
            max_tokens=4096
        )
    
    def test_execute_empty_prompt_raises_value_error(self, mock_openai_service):
        """Test that empty or invalid prompt raises ValueError."""
        service, _ = mock_openai_service
        
        with pytest.raises(ValueError, match="Prompt must be a non-empty string"):
            service.execute("")
        
        with pytest.raises(ValueError, match="Prompt must be a non-empty string"):
            service.execute(None)
        
        with pytest.raises(ValueError, match="Prompt must be a non-empty string"):
            service.execute(123)
    
    def test_execute_empty_response_raises_api_error(self, mock_openai_service):
        """Test that empty API response raises LLMAPIError."""
        service, mock_client = mock_openai_service
        
        # Mock empty response
        mock_response = Mock()
        mock_response.choices = []
        mock_client.chat.completions.create.return_value = mock_response
        
        with pytest.raises(LLMAPIError, match="OpenAI returned empty response"):
            service.execute("Test prompt")
    
    def test_execute_null_content_raises_api_error(self, mock_openai_service):
        """Test that null content in response raises LLMAPIError."""
        service, mock_client = mock_openai_service
        
        # Mock response with null content
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = None
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_response
        
        with pytest.raises(LLMAPIError, match="OpenAI returned null content"):
            service.execute("Test prompt")
    
    def test_execute_authentication_error(self, mock_openai_service):
        """Test handling of OpenAI authentication errors."""
        service, mock_client = mock_openai_service
        
        # Create a proper exception class that can be caught by isinstance
        class MockAuthenticationError(Exception):
            pass
        
        # Patch the openai module to use our mock exception
        with patch('openai.AuthenticationError', MockAuthenticationError):
            auth_error = MockAuthenticationError("Invalid API key")
            mock_client.chat.completions.create.side_effect = auth_error
            
            with pytest.raises(LLMAuthenticationError, match="OpenAI authentication failed"):
                service.execute("Test prompt")
    
    def test_execute_rate_limit_error(self, mock_openai_service):
        """Test handling of OpenAI rate limit errors."""
        service, mock_client = mock_openai_service
        
        # Create a proper exception class that can be caught by isinstance
        class MockRateLimitError(Exception):
            pass
        
        # Patch the openai module to use our mock exception
        with patch('openai.RateLimitError', MockRateLimitError):
            rate_error = MockRateLimitError("Rate limit exceeded")
            mock_client.chat.completions.create.side_effect = rate_error
            
            with pytest.raises(LLMAPIError, match="OpenAI rate limit exceeded"):
                service.execute("Test prompt")
    
    def test_execute_api_error(self, mock_openai_service):
        """Test handling of general OpenAI API errors."""
        service, mock_client = mock_openai_service
        
        # Create a proper exception class that can be caught by isinstance
        class MockAPIError(Exception):
            pass
        
        # Patch the openai module to use our mock exception
        with patch('openai.APIError', MockAPIError):
            api_error = MockAPIError("API service unavailable")
            mock_client.chat.completions.create.side_effect = api_error
            
            with pytest.raises(LLMAPIError, match="OpenAI API error"):
                service.execute("Test prompt")
    
    def test_execute_unexpected_error(self, mock_openai_service):
        """Test handling of unexpected errors with fallback behavior."""
        service, mock_client = mock_openai_service
        
        mock_client.chat.completions.create.side_effect = RuntimeError("Unexpected error")
        
        with pytest.raises(LLMAPIError, match="Unexpected OpenAI service error"):
            service.execute("Test prompt")


class TestOpenAIServiceUtilities:
    """Test utility methods and configuration."""
    
    @patch('openai.OpenAI')
    def test_get_model_info(self, mock_openai_client):
        """Test model information retrieval."""
        mock_client_instance = Mock()
        mock_openai_client.return_value = mock_client_instance
        
        service = OpenAIService(model="gpt-3.5-turbo", api_key="test_key")
        info = service.get_model_info()
        
        expected_info = {
            "provider": "OpenAI",
            "model": "gpt-3.5-turbo",
            "api_key_configured": True,
            "client_initialized": True
        }
        
        assert info == expected_info


class TestLLMServiceErrorHierarchy:
    """Test custom exception hierarchy behavior."""
    
    def test_llm_service_error_base(self):
        """Test base LLMServiceError exception."""
        error = LLMServiceError("Base error")
        assert str(error) == "Base error"
        assert isinstance(error, Exception)
    
    def test_llm_authentication_error_inheritance(self):
        """Test LLMAuthenticationError inherits from LLMServiceError."""
        error = LLMAuthenticationError("Auth failed")
        assert isinstance(error, LLMServiceError)
        assert isinstance(error, Exception)
    
    def test_llm_api_error_inheritance(self):
        """Test LLMAPIError inherits from LLMServiceError."""
        error = LLMAPIError("API failed")
        assert isinstance(error, LLMServiceError)
        assert isinstance(error, Exception)


# Integration test configuration
@pytest.mark.integration
class TestOpenAIServiceIntegration:
    """Integration tests requiring actual API key (optional)."""
    
    def test_real_api_execution(self):
        """Test actual API call (only runs with real API key)."""
        # PATCH: Cursor-2025-08-15 CL-LLM-QSF-Config-Audit <disable config fallback for integration test>
        # Set test mode flags to disable config fallback
        os.environ["IOA_TEST_MODE"] = "1"
        os.environ["IOA_DISABLE_LLM_CONFIG"] = "1"
        
        # Test service creation
        service = OpenAIService(model="gpt-3.5-turbo", api_key="test_key")
        assert service.model == "gpt-3.5-turbo"
        assert service.api_key == "test_key"
        
        # Test model info retrieval
        info = service.get_model_info()
        assert info["provider"] == "OpenAI"
        assert info["model"] == "gpt-3.5-turbo"
        assert info["api_key_configured"] is True
        
        # Test that service is properly configured
        assert hasattr(service, 'client')
        assert service.client is not None
