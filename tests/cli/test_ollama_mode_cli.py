"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

"""
Unit tests for Ollama mode CLI functionality including:
- Mode detection and mapping
- Cloud credential validation
- Deprecation handling
- CLI flag processing
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

# Import the CLI module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ioa_core.cli import app
from ioa_core.llm_providers.ollama_utils import get_ollama_mode, _is_turbo_cloud_configured


class TestOllamaModeDetection:
    """Test Ollama mode detection functionality."""
    
    def test_get_ollama_mode_explicit_local_preset(self):
        """Test explicit local_preset mode setting."""
        with patch.dict(os.environ, {"IOA_OLLAMA_MODE": "local_preset"}):
            assert get_ollama_mode() == "local_preset"
    
    def test_get_ollama_mode_explicit_turbo_cloud(self):
        """Test explicit turbo_cloud mode setting."""
        with patch.dict(os.environ, {"IOA_OLLAMA_MODE": "turbo_cloud"}):
            assert get_ollama_mode() == "turbo_cloud"
    
    def test_get_ollama_mode_deprecated_turbo_local(self):
        """Test deprecated turbo_local mode maps to local_preset."""
        with patch.dict(os.environ, {"IOA_OLLAMA_MODE": "turbo_local"}):
            assert get_ollama_mode() == "local_preset"
    
    def test_get_ollama_mode_auto_detect_cloud_configured(self):
        """Test auto-detection when cloud credentials are present."""
        with patch.dict(os.environ, {
            "OLLAMA_API_BASE": "https://api.ollama.ai/v1",
            "OLLAMA_API_KEY": "test-key-123"
        }):
            assert get_ollama_mode() == "turbo_cloud"
    
    def test_get_ollama_mode_auto_detect_local_fallback(self):
        """Test auto-detection falls back to local_preset when cloud not configured."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_ollama_mode() == "local_preset"
    
    def test_get_ollama_mode_use_turbo_local_flag(self):
        """Test IOA_OLLAMA_USE_TURBO_LOCAL flag."""
        with patch.dict(os.environ, {"IOA_OLLAMA_USE_TURBO_LOCAL": "1"}):
            assert get_ollama_mode() == "local_preset"
    
    def test_get_ollama_mode_use_turbo_cloud_flag(self):
        """Test IOA_OLLAMA_USE_TURBO_CLOUD flag."""
        with patch.dict(os.environ, {
            "IOA_OLLAMA_USE_TURBO_CLOUD": "1",
            "OLLAMA_API_BASE": "https://api.ollama.ai/v1",
            "OLLAMA_API_KEY": "test-key-123"
        }):
            assert get_ollama_mode() == "turbo_cloud"
    
    def test_get_ollama_mode_use_turbo_cloud_flag_not_configured(self):
        """Test IOA_OLLAMA_USE_TURBO_CLOUD flag falls back when not configured."""
        with patch.dict(os.environ, {"IOA_OLLAMA_USE_TURBO_CLOUD": "1"}):
            assert get_ollama_mode() == "local_preset"


class TestCloudCredentialValidation:
    """Test cloud credential validation functionality."""
    
    def test_is_turbo_cloud_configured_both_present(self):
        """Test cloud configuration when both base and key are present."""
        with patch.dict(os.environ, {
            "OLLAMA_API_BASE": "https://api.ollama.ai/v1",
            "OLLAMA_API_KEY": "test-key-123"
        }):
            assert _is_turbo_cloud_configured() is True
    
    def test_is_turbo_cloud_configured_missing_base(self):
        """Test cloud configuration when base is missing."""
        with patch.dict(os.environ, {
            "OLLAMA_API_KEY": "test-key-123"
        }):
            assert _is_turbo_cloud_configured() is False
    
    def test_is_turbo_cloud_configured_missing_key(self):
        """Test cloud configuration when key is missing."""
        with patch.dict(os.environ, {
            "OLLAMA_API_BASE": "https://api.ollama.ai/v1"
        }):
            assert _is_turbo_cloud_configured() is False
    
    def test_is_turbo_cloud_configured_invalid_base_url(self):
        """Test cloud configuration with invalid base URL."""
        with patch.dict(os.environ, {
            "OLLAMA_API_BASE": "http://api.ollama.ai/v1",  # Not HTTPS
            "OLLAMA_API_KEY": "test-key-123"
        }):
            assert _is_turbo_cloud_configured() is False
    
    def test_is_turbo_cloud_configured_empty_values(self):
        """Test cloud configuration with empty values."""
        with patch.dict(os.environ, {
            "OLLAMA_API_BASE": "",
            "OLLAMA_API_KEY": ""
        }):
            assert _is_turbo_cloud_configured() is False


class TestOllamaModeCLI:
    """Test Ollama mode CLI functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
    
    def test_ollama_mode_help_shows_new_modes(self):
        """Test that CLI help shows new mode options."""
        result = self.runner.invoke(app, ["smoketest", "providers", "--help"])
        assert result.exit_code == 0
        assert "local_preset" in result.output
        assert "turbo_cloud" in result.output
        assert "turbo_local" in result.output  # Deprecated but still supported
        assert "auto" in result.output
    
    def test_ollama_mode_deprecation_warning(self):
        """Test that using turbo_local shows deprecation warning."""
        with patch.dict(os.environ, {"OLLAMA_HOST": "http://localhost:11434"}):
            result = self.runner.invoke(app, [
                "smoketest", "providers", 
                "--provider", "ollama",
                "--ollama-mode", "turbo_local"
            ])
            assert "Warning: 'turbo_local' is deprecated" in result.output
            assert "Use 'local_preset' instead" in result.output
    
    def test_ollama_mode_local_preset_no_warning(self):
        """Test that using local_preset shows no deprecation warning."""
        with patch.dict(os.environ, {"OLLAMA_HOST": "http://localhost:11434"}):
            result = self.runner.invoke(app, [
                "smoketest", "providers", 
                "--provider", "ollama",
                "--ollama-mode", "local_preset"
            ])
            assert "Warning:" not in result.output
            assert "deprecated" not in result.output
    
    def test_ollama_mode_turbo_cloud_no_warning(self):
        """Test that using turbo_cloud shows no deprecation warning."""
        with patch.dict(os.environ, {
            "OLLAMA_API_BASE": "https://api.ollama.ai/v1",
            "OLLAMA_API_KEY": "test-key-123"
        }):
            result = self.runner.invoke(app, [
                "smoketest", "providers", 
                "--provider", "ollama",
                "--ollama-mode", "turbo_cloud"
            ])
            assert "Warning:" not in result.output
            assert "deprecated" not in result.output
    
    def test_ollama_mode_auto_detection(self):
        """Test auto mode detection."""
        with patch.dict(os.environ, {
            "OLLAMA_API_BASE": "https://api.ollama.ai/v1",
            "OLLAMA_API_KEY": "test-key-123"
        }):
            result = self.runner.invoke(app, [
                "smoketest", "providers", 
                "--provider", "ollama",
                "--ollama-mode", "auto"
            ])
            assert result.exit_code == 0
    
    def test_ollama_mode_invalid_mode(self):
        """Test invalid mode handling."""
        result = self.runner.invoke(app, [
            "smoketest", "providers", 
            "--provider", "ollama",
            "--ollama-mode", "invalid_mode"
        ])
        assert result.exit_code != 0
        assert "Invalid value" in result.output or "Choice" in result.output


class TestOllamaModeIntegration:
    """Test Ollama mode integration with smoketest."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
    
    @patch('ioa_core.llm_providers.ollama_smoketest.get_ollama_provider_status')
    def test_ollama_mode_passed_to_smoketest(self, mock_status):
        """Test that ollama mode is passed to smoketest."""
        mock_status.return_value = {
            "provider": "ollama",
            "configured": True,
            "host": "http://localhost:11434",
            "mode": "local_preset",
            "no_key": True,
            "details": "Host: http://localhost:11434, Mode: local_preset (no API key required)",
            "notes": "Ollama local_preset mode detected"
        }
        
        with patch.dict(os.environ, {"OLLAMA_HOST": "http://localhost:11434"}):
            result = self.runner.invoke(app, [
                "smoketest", "providers", 
                "--provider", "ollama",
                "--ollama-mode", "local_preset"
            ])
            assert result.exit_code == 0
            mock_status.assert_called_once()
    
    @patch('ioa_core.llm_providers.ollama_smoketest.get_ollama_provider_status')
    def test_ollama_mode_cloud_detection(self, mock_status):
        """Test cloud mode detection in smoketest."""
        mock_status.return_value = {
            "provider": "ollama",
            "configured": True,
            "host": "https://api.ollama.ai/v1",
            "mode": "turbo_cloud",
            "no_key": False,
            "details": "Host: https://api.ollama.ai/v1, Mode: turbo_cloud (API key configured)",
            "notes": "Ollama turbo_cloud mode detected"
        }
        
        with patch.dict(os.environ, {
            "OLLAMA_API_BASE": "https://api.ollama.ai/v1",
            "OLLAMA_API_KEY": "test-key-123"
        }):
            result = self.runner.invoke(app, [
                "smoketest", "providers", 
                "--provider", "ollama",
                "--ollama-mode", "turbo_cloud"
            ])
            assert result.exit_code == 0
            mock_status.assert_called_once()


class TestOllamaModeEnvironmentHandling:
    """Test environment variable handling for Ollama modes."""
    
    def test_environment_variable_precedence(self):
        """Test that explicit IOA_OLLAMA_MODE takes precedence."""
        with patch.dict(os.environ, {
            "IOA_OLLAMA_MODE": "turbo_cloud",
            "OLLAMA_API_BASE": "https://api.ollama.ai/v1",
            "OLLAMA_API_KEY": "test-key-123"
        }):
            assert get_ollama_mode() == "turbo_cloud"
    
    def test_environment_variable_clearing(self):
        """Test that clearing environment variables works correctly."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_ollama_mode() == "local_preset"
    
    def test_legacy_environment_variables(self):
        """Test legacy environment variable support."""
        with patch.dict(os.environ, {
            "OLLAMA_TURBO_CLOUD": "1",
            "OLLAMA_API_BASE": "https://api.ollama.ai/v1",
            "OLLAMA_API_KEY": "test-key-123"
        }):
            assert get_ollama_mode() == "turbo_cloud"
    
    def test_legacy_host_indicators(self):
        """Test legacy host-based indicators."""
        with patch.dict(os.environ, {
            "OLLAMA_HOST": "https://turbo.ollama.ai/v1"
        }):
            assert get_ollama_mode() == "turbo_cloud"


if __name__ == "__main__":
    pytest.main([__file__])
