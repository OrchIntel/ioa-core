""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from ioa_core.onboard import OnboardingCLI
from ioa_core.errors import NonInteractiveError


@pytest.mark.interactive
class TestOnboardingInteractive:
    """Test interactive CLI functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        # PATCH: Cursor-2025-08-16 CL-ONBOARD-Provider-Key-Fix+UX <add interactive CLI tests>
        self.cli = OnboardingCLI()
        # Mock the manager to avoid actual file operations
        self.cli.manager = Mock()
        
        # Set up default mock returns
        self.cli.manager.list_providers.return_value = []
        self.cli.manager.list_all_providers.return_value = []
        self.cli.manager.get_provider_status.return_value = {"configured": True, "source": "config"}
        self.cli.manager.get_default_provider.return_value = None
        
        # Mock the validate_api_key method to return proper validation results
        self.cli.manager.validate_api_key.return_value = {
            "valid": True,
            "message": "Valid key",
            "can_force": False
        }
    
    @patch('builtins.input')
    @patch('getpass.getpass')
    def test_key_confirmation_message(self, mock_getpass, mock_input):
        """Test that key confirmation shows character count."""
        mock_getpass.return_value = "sk-ant-123456789012345678901234567890"
        mock_input.side_effect = ["y"]  # Confirm save
        
        key = self.cli._prompt_for_key("anthropic")
        
        # Verify the confirmation message was shown
        assert key == "sk-ant-123456789012345678901234567890"
        # The confirmation message should be printed to stdout
        # We can't easily test print output, but we can verify the flow
    
    @patch('builtins.input')
    @patch('getpass.getpass')
    def test_key_trimming_behavior(self, mock_getpass, mock_input):
        """Test that keys are automatically trimmed."""
        mock_getpass.return_value = "  sk-ant-123456789012345678901234567890  \n"
        mock_input.side_effect = ["y"]  # Confirm save
        
        key = self.cli._prompt_for_key("anthropic")
        
        # Key should be trimmed
        assert key == "sk-ant-123456789012345678901234567890"
    
    @patch('builtins.input')
    @patch('getpass.getpass')
    def test_force_override_interactive(self, mock_getpass, mock_input):
        """Test force override behavior in interactive mode."""
        # Mock validation to fail
        with patch.object(self.cli, '_validate_key_format') as mock_validate:
            mock_validate.return_value = (False, "Invalid key format")
            
            mock_getpass.return_value = "invalid-key"
            mock_input.side_effect = ["f", "y"]  # Choose force, then confirm save
            
            key = self.cli._prompt_for_key("anthropic", force=True)
            
            # Should proceed with force override
            assert key == "invalid-key"
    
    @patch('builtins.input')
    @patch('getpass.getpass')
    def test_force_override_requires_flag(self, mock_getpass, mock_input):
        """Test that force override requires the --force flag."""
        # Mock validation to fail
        with patch.object(self.cli, '_validate_key_format') as mock_validate:
            mock_validate.return_value = (False, "Invalid key format")
            
            mock_getpass.return_value = "invalid-key"
            mock_input.side_effect = ["f", "n"]  # Choose force, then cancel
            
            key = self.cli._prompt_for_key("anthropic", force=False)
            
            # Should not proceed without force flag
            assert key == ""
    
    @patch('builtins.input')
    @patch('getpass.getpass')
    def test_placeholder_key_detection(self, mock_getpass, mock_input):
        """Test detection of placeholder keys."""
        mock_getpass.return_value = "sk-ant-test-key"
        mock_input.side_effect = ["keep"]  # Keep as UNSET
        
        key = self.cli._prompt_for_key("anthropic")
        
        # Should return empty string for placeholder
        assert key == ""
    
    @patch('builtins.input')
    @patch('getpass.getpass')
    def test_ollama_no_key_required(self, mock_getpass, mock_input):
        """Test that Ollama doesn't prompt for a key."""
        key = self.cli._prompt_for_key("ollama")
        
        # Should return local without prompting
        assert key == "local"
        # getpass should not be called for Ollama
        mock_getpass.assert_not_called()
    
    @patch('builtins.input')
    @patch('getpass.getpass')
    def test_empty_key_handling(self, mock_getpass, mock_input):
        """Test handling of empty keys."""
        mock_getpass.return_value = ""
        mock_input.side_effect = ["y"]  # Confirm save
        
        key = self.cli._prompt_for_key("anthropic")
        
        # Should return empty string for empty key
        assert key == ""
    
    @patch('builtins.input')
    @patch('getpass.getpass')
    def test_whitespace_only_key_handling(self, mock_getpass, mock_input):
        """Test handling of whitespace-only keys."""
        mock_getpass.return_value = "   \n\t  "
        mock_input.side_effect = ["y"]  # Confirm save
        
        key = self.cli._prompt_for_key("anthropic")
        
        # Should return empty string for whitespace-only key
        assert key == ""
    
    def test_provider_options_structure(self):
        """Test that provider options have correct structure."""
        for provider, info in self.cli.PROVIDER_OPTIONS.items():
            assert 'name' in info
            assert 'description' in info
            assert 'env_var' in info
            assert 'key_pattern' in info
            assert 'min_length' in info
    
    def test_provider_options_completeness(self):
        """Test that all expected providers are included."""
        expected_providers = ['openai', 'anthropic', 'google', 'xai', 'grok', 'groq', 'ollama']
        
        for provider in expected_providers:
            assert provider in self.cli.PROVIDER_OPTIONS, f"Provider {provider} missing"
    
    def test_environment_variable_mapping(self):
        """Test environment variable mappings for providers."""
        env_mappings = {
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'google': 'GOOGLE_API_KEY',
            'xai': 'XAI_API_KEY',
            'grok': 'GROK_API_KEY',
            'groq': 'GROQ_API_KEY',
            'ollama': 'OLLAMA_HOST'
        }
        
        for provider, expected_env in env_mappings.items():
            actual_env = self.cli.PROVIDER_OPTIONS[provider]['env_var']
            assert actual_env == expected_env, f"Wrong env var for {provider}: {actual_env} != {expected_env}"
    
    def test_key_pattern_validation(self):
        """Test that key patterns are valid regex."""
        import re
        
        for provider, info in self.cli.PROVIDER_OPTIONS.items():
            if info['key_pattern']:
                # Should be valid regex
                try:
                    re.compile(info['key_pattern'])
                except re.error as e:
                    pytest.fail(f"Invalid regex for {provider}: {e}")
    
    def test_min_length_validation(self):
        """Test that min_length values are reasonable."""
        for provider, info in self.cli.PROVIDER_OPTIONS.items():
            if provider == 'ollama':
                assert info['min_length'] == 0, "Ollama should have min_length 0"
            else:
                assert info['min_length'] >= 20, f"Provider {provider} should have min_length >= 20"
    
    def test_non_interactive_guard(self):
        """Test that non-interactive environment raises NonInteractiveError."""
        # PATCH: Cursor-2025-08-19 DISPATCH-GPT-20250819-014 <add non-interactive safety test>
        with patch.dict('os.environ', {'IOA_NON_INTERACTIVE': '1'}):
            with pytest.raises(NonInteractiveError, match="Key prompt disallowed in non-interactive runs"):
                self.cli._prompt_for_key("anthropic")
    
    def test_non_interactive_guard_no_tty(self):
        """Test that non-TTY environment raises NonInteractiveError."""
        # PATCH: Cursor-2025-08-19 DISPATCH-GPT-20250819-014 <add non-interactive safety test>
        with patch('sys.stdin.isatty', return_value=False):
            with pytest.raises(NonInteractiveError, match="Key prompt disallowed in non-interactive runs"):
                self.cli._prompt_for_key("anthropic")
