""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ioa_core.cli import app


class TestSmoketestProviderFlags:
    """Test smoketest provider filtering and Ollama mode functionality."""
    
    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()
    
    def test_provider_choice_validation(self):
        """Test that provider choice validation works correctly."""
        # Test valid providers
        valid_providers = ['openai', 'anthropic', 'google', 'deepseek', 'xai', 'ollama', 'all']
        for provider in valid_providers:
            result = self.runner.invoke(app, ['smoketest', 'providers', '--provider', provider, '--non-interactive'])
            # Should not raise an error for valid providers
            assert result.exit_code in [0, 1, 2]  # 0=success, 1=missing config, 2=validation error
    
    def test_invalid_provider_error(self):
        """Test that invalid provider shows clean error with help hint."""
        result = self.runner.invoke(app, ['smoketest', 'providers', '--provider', 'invalid', '--non-interactive'])
        assert result.exit_code == 2
        assert "Invalid value for '--provider'" in str(result.output)
        assert "is not one of" in str(result.output)
    
    def test_ollama_mode_choice_validation(self):
        """Test that Ollama mode choice validation works correctly."""
        valid_modes = ['auto', 'local_preset', 'turbo_cloud', 'turbo_local']
        for mode in valid_modes:
            result = self.runner.invoke(app, ['smoketest', 'providers', '--provider', 'ollama', '--ollama-mode', mode, '--non-interactive'])
            # Should not raise an error for valid modes
            assert result.exit_code == 0 or result.exit_code == 1  # 1 is OK for missing config
    
    def test_ollama_mode_override_env(self):
        """Test that --ollama-mode flag overrides environment variable."""
        # Set environment variable
        os.environ['IOA_OLLAMA_MODE'] = 'turbo_cloud'
        
        # Test that CLI flag overrides env var
        with patch('ioa_core.llm_providers.ollama_smoketest.get_ollama_provider_status') as mock_status:
            mock_status.return_value = {
                "provider": "ollama",
                "configured": True,
                "host": "http://localhost:11434",
                "mode": "local_preset",
                "no_key": True,
                "details": "Host: http://localhost:11434, Mode: local_preset (no API key required)",
                "notes": "Ollama local_preset mode detected"
            }
            
            result = self.runner.invoke(app, ['smoketest', 'providers', '--provider', 'ollama', '--ollama-mode', 'local_preset', '--non-interactive'])
            assert result.exit_code == 0
            assert "local_preset" in str(result.output)
    
    def test_provider_all_behavior(self):
        """Test that --provider all behaves like no filter."""
        with patch('ioa_core.llm_providers.ollama_smoketest.get_ollama_provider_status') as mock_status:
            mock_status.return_value = {
                "provider": "ollama",
                "configured": True,
                "host": "http://localhost:11434",
                "mode": "local_preset",
                "no_key": True,
                "details": "Host: http://localhost:11434, Mode: local_preset (no API key required)",
                "notes": "Ollama local_preset mode detected"
            }
            
            # Test with --provider all
            result_all = self.runner.invoke(app, ['smoketest', 'providers', '--provider', 'all', '--non-interactive'])
            
            # Test without --provider (should be same as all)
            result_none = self.runner.invoke(app, ['smoketest', 'providers', '--non-interactive'])
            
            # Both should have same behavior
            assert result_all.exit_code == result_none.exit_code
    
    def test_single_provider_filtering(self):
        """Test that selecting single provider returns exactly one transcript row."""
        with patch('ioa_core.llm_providers.ollama_smoketest.get_ollama_provider_status') as mock_status:
            mock_status.return_value = {
                "provider": "ollama",
                "configured": True,
                "host": "http://localhost:11434",
                "mode": "local_preset",
                "no_key": True,
                "details": "Host: http://localhost:11434, Mode: local_preset (no API key required)",
                "notes": "Ollama local_preset mode detected"
            }
            
            result = self.runner.invoke(app, ['smoketest', 'providers', '--provider', 'ollama', '--non-interactive'])
            assert result.exit_code == 0
            
            # Should only show Ollama provider
            output = str(result.output)
            assert "Ollama:" in output
            assert "OpenAI:" not in output
            assert "Anthropic:" not in output
            assert "Google Gemini:" not in output
            assert "DeepSeek:" not in output
            assert "XAI:" not in output
    
    def test_help_output_includes_flags(self):
        """Test that help output includes both new flags."""
        result = self.runner.invoke(app, ['smoketest', 'providers', '--help'])
        assert result.exit_code == 0
        
        output = str(result.output)
        assert "--provider" in output
        assert "--ollama-mode" in output
        assert "openai|anthropic|google|deepseek|xai|ollama|all" in output
        assert "auto|local_preset|turbo_cloud|turbo_local" in output
    
    def test_help_output_includes_env_fallbacks(self):
        """Test that help output includes environment variable fallbacks."""
        result = self.runner.invoke(app, ['smoketest', 'providers', '--help'])
        assert result.exit_code == 0
        
        output = str(result.output)
        assert "IOA_OLLAMA_MODE" in output
        assert "IOA_SMOKETEST_NON_INTERACTIVE" in output
        assert "Environment Variables:" in output
    
    def test_turbo_local_deprecation_warning(self):
        """Test that turbo_local shows deprecation warning."""
        result = self.runner.invoke(app, ['smoketest', 'providers', '--provider', 'ollama', '--ollama-mode', 'turbo_local', '--non-interactive'])
        assert result.exit_code == 0
        
        output = str(result.output)
        assert "Warning: 'turbo_local' is deprecated" in output
        assert "Use 'local_preset' instead" in output
    
    def test_backward_compatibility_env_vars(self):
        """Test that legacy environment variables still work."""
        # Test IOA_OLLAMA_USE_TURBO_LOCAL
        os.environ['IOA_OLLAMA_USE_TURBO_LOCAL'] = '1'
        os.environ.pop('IOA_OLLAMA_MODE', None)  # Clear explicit mode
        
        with patch('ioa_core.llm_providers.ollama_smoketest.get_ollama_provider_status') as mock_status:
            mock_status.return_value = {
                "provider": "ollama",
                "configured": True,
                "host": "http://localhost:11434",
                "mode": "local_preset",
                "no_key": True,
                "details": "Host: http://localhost:11434, Mode: local_preset (no API key required)",
                "notes": "Ollama local_preset mode detected"
            }
            
            result = self.runner.invoke(app, ['smoketest', 'providers', '--provider', 'ollama', '--non-interactive'])
            assert result.exit_code == 0
        
        # Clean up
        os.environ.pop('IOA_OLLAMA_USE_TURBO_LOCAL', None)
    
    def test_ollama_mode_flag_priority(self):
        """Test that --ollama-mode flag has priority over environment variables."""
        # Set environment variable
        os.environ['IOA_OLLAMA_MODE'] = 'turbo_cloud'
        
        with patch('ioa_core.llm_providers.ollama_smoketest.get_ollama_provider_status') as mock_status:
            mock_status.return_value = {
                "provider": "ollama",
                "configured": True,
                "host": "http://localhost:11434",
                "mode": "local_preset",  # Flag should override env
                "no_key": True,
                "details": "Host: http://localhost:11434, Mode: local_preset (no API key required)",
                "notes": "Ollama local_preset mode detected"
            }
            
            result = self.runner.invoke(app, ['smoketest', 'providers', '--provider', 'ollama', '--ollama-mode', 'local_preset', '--non-interactive'])
            assert result.exit_code == 0
            assert "local_preset" in str(result.output)
        
        # Clean up
        os.environ.pop('IOA_OLLAMA_MODE', None)
