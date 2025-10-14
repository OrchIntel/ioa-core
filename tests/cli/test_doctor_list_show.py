"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from unittest.mock import Mock, patch, MagicMock
from ioa_core.onboard import OnboardingCLI


class TestDoctorListShow:
    """Test doctor, list, and show commands."""
    
    def setup_method(self):
        """Set up test environment."""
        # PATCH: Cursor-2025-08-16 CL-ONBOARD-Provider-Key-Fix+UX <add doctor/list/show command tests>
        self.cli = OnboardingCLI()
        # Mock the manager to avoid actual file operations
        self.cli.manager = Mock()
    
    def test_list_providers_configured(self):
        """Test listing configured providers."""
        # Mock provider status
        self.cli.manager.list_providers.return_value = ["openai", "anthropic"]
        self.cli.manager.list_all_providers.return_value = ["openai", "anthropic"]
        self.cli.manager.get_provider_status.side_effect = [
            {"configured": True, "source": "config"},
            {"configured": True, "source": "env"}
        ]
        self.cli.manager.get_default_provider.return_value = "openai"
        
        # Capture stdout to verify output
        with patch('builtins.print') as mock_print:
            self.cli.list_providers()
            
            # Verify output format
            calls = mock_print.call_args_list
            assert any("Provider" in str(call) for call in calls)
            assert any("Status" in str(call) for call in calls)
            assert any("Source" in str(call) for call in calls)
            assert any("openai" in str(call) for call in calls)
            assert any("anthropic" in str(call) for call in calls)
            assert any("Default provider: openai" in str(call) for call in calls)
    
    def test_list_providers_unset(self):
        """Test listing unset providers."""
        # Mock provider status
        self.cli.manager.list_providers.return_value = ["openai", "anthropic"]
        self.cli.manager.list_all_providers.return_value = ["openai", "anthropic"]
        self.cli.manager.get_provider_status.side_effect = [
            {"configured": False, "source": "config"},
            {"configured": False, "source": "config"}
        ]
        self.cli.manager.get_default_provider.return_value = None
        
        with patch('builtins.print') as mock_print:
            self.cli.list_providers()
            
            # Verify UNSET status is shown
            calls = mock_print.call_args_list
            assert any("UNSET" in str(call) for call in calls)
    
    def test_list_providers_include_unset(self):
        """Test listing all providers including unset ones."""
        # Mock provider status
        self.cli.manager.list_providers.return_value = ["openai", "anthropic"]
        self.cli.manager.list_all_providers.return_value = ["openai", "anthropic", "google"]
        self.cli.manager.get_provider_status.side_effect = [
            {"configured": True, "source": "config"},
            {"configured": False, "source": "config"},
            {"configured": True, "source": "env"}
        ]
        
        with patch('builtins.print') as mock_print:
            self.cli.list_providers(include_unset=True)
            
            # Should show all providers
            calls = mock_print.call_args_list
            assert any("openai" in str(call) for call in calls)
            assert any("anthropic" in str(call) for call in calls)
            assert any("google" in str(call) for call in calls)
    
    def test_show_provider_configured(self):
        """Test showing configured provider details."""
        # Mock provider config and status
        self.cli.manager.get_provider_config.return_value = {
            "api_key": "sk-ant-123456789012345678901234567890",
            "model": "claude-3-haiku-20240307"
        }
        self.cli.manager.get_provider_status.return_value = {
            "status": "CONFIGURED",
            "source": "config"
        }
        
        with patch('builtins.print') as mock_print:
            self.cli.show_provider("anthropic")
            
            # Verify masked API key
            calls = mock_print.call_args_list
            assert any("********" in str(call) for call in calls)
            assert any("claude-3-haiku-20240307" in str(call) for call in calls)
    
    def test_show_provider_unset(self):
        """Test showing unset provider details."""
        # Mock provider config and status
        self.cli.manager.get_provider_config.return_value = {}
        self.cli.manager.get_provider_status.return_value = {
            "status": "UNSET",
            "source": "config"
        }
        
        with patch('builtins.print') as mock_print:
            self.cli.show_provider("anthropic")
            
            # Verify unset status
            calls = mock_print.call_args_list
            assert any("UNSET" in str(call) for call in calls)
            assert any("No configuration found" in str(call) for call in calls)
    
    def test_show_provider_invalid(self):
        """Test showing invalid provider."""
        with pytest.raises(SystemExit):
            self.cli.show_provider("invalid_provider")
    
    def test_doctor_no_issues(self):
        """Test doctor command with no issues."""
        # Mock no issues
        self.cli.manager.list_all_providers.return_value = ["openai"]
        self.cli.manager.get_provider_status.return_value = {"configured": True}
        self.cli.manager.get_default_provider.return_value = "openai"
        
        # Mock file permissions check
        config_file = Mock()
        config_file.exists.return_value = True
        config_file.stat.return_value = Mock(st_mode=0o600)
        self.cli.manager.llm_config_path = config_file
        
        with patch('builtins.input', return_value="n"):
            with patch('builtins.print') as mock_print:
                self.cli.doctor()
            
            # Verify success message
            calls = mock_print.call_args_list
            assert any("No issues found" in str(call) for call in calls)
            assert any("Configuration is healthy" in str(call) for call in calls)
    
    def test_doctor_fixes_permissions(self):
        """Test doctor command fixing file permissions."""
        # Mock permission issues
        config_file = Mock()
        config_file.exists.return_value = True
        config_file.stat.return_value = Mock(st_mode=0o666)  # Too permissive
        config_file.chmod.return_value = None
        self.cli.manager.llm_config_path = config_file
        
        # Mock other checks pass
        self.cli.manager.list_all_providers.return_value = ["openai"]
        self.cli.manager.get_provider_status.return_value = {"configured": True}
        self.cli.manager.get_default_provider.return_value = "openai"
        
        with patch('builtins.print') as mock_print:
            self.cli.doctor()
            
            # Verify permission fix
            config_file.chmod.assert_called_once_with(0o600)
            calls = mock_print.call_args_list
            assert any("Fixed config file permissions" in str(call) for call in calls)
    
    def test_doctor_removes_unset_providers(self):
        """Test doctor command removing unset providers."""
        # Mock unset providers
        self.cli.manager.list_all_providers.return_value = ["openai", "anthropic"]
        self.cli.manager.get_provider_status.side_effect = [
            {"configured": True},  # openai is configured
            {"configured": False}  # anthropic is unset
        ]
        self.cli.manager.get_default_provider.return_value = "openai"
        
        # Mock file permissions check
        config_file = Mock()
        config_file.exists.return_value = True
        config_file.stat.return_value = Mock(st_mode=0o600)
        self.cli.manager.llm_config_path = config_file
        
        # Mock user input to remove unset provider
        with patch('builtins.input', return_value="y"):
            with patch('builtins.print') as mock_print:
                self.cli.doctor()
                
                # Verify provider removal
                self.cli.manager.remove_provider.assert_called_once_with("anthropic")
                calls = mock_print.call_args_list
                assert any("Removed unset provider" in str(call) for call in calls)
    
    def test_doctor_keeps_configured_providers(self):
        """Test doctor command keeps configured providers."""
        # Mock configured providers
        self.cli.manager.list_all_providers.return_value = ["openai", "anthropic"]
        self.cli.manager.get_provider_status.side_effect = [
            {"configured": True},  # openai is configured
            {"configured": True}   # anthropic is configured
        ]
        self.cli.manager.get_default_provider.return_value = "openai"
        
        # Mock file permissions check
        config_file = Mock()
        config_file.exists.return_value = True
        config_file.stat.return_value = Mock(st_mode=0o600)
        self.cli.manager.llm_config_path = config_file
        
        with patch('builtins.print') as mock_print:
            self.cli.doctor()
            
            # Verify no providers were removed
            self.cli.manager.remove_provider.assert_not_called()
            calls = mock_print.call_args_list
            assert any("No issues found" in str(call) for call in calls)
    
    def test_doctor_handles_invalid_default(self):
        """Test doctor command handling invalid default provider."""
        # Mock invalid default provider
        self.cli.manager.list_all_providers.return_value = ["openai"]
        self.cli.manager.get_provider_status.return_value = {"configured": False}
        self.cli.manager.get_default_provider.return_value = "openai"
        self.cli.manager.validate_default_provider.return_value = None
        
        # Mock file permissions check
        config_file = Mock()
        config_file.exists.return_value = True
        config_file.stat.return_value = Mock(st_mode=0o600)
        self.cli.manager.llm_config_path = config_file
        
        # Mock non-interactive check to allow testing
        with patch.object(self.cli, '_check_non_interactive'):
            with patch('builtins.print') as mock_print:
                self.cli.doctor()
                
                # Verify default provider validation
                self.cli.manager.validate_default_provider.assert_called_once()
                calls = mock_print.call_args_list
                assert any("Cleared invalid default provider" in str(call) for call in calls)
    
    def test_doctor_summary_report(self):
        """Test doctor command provides summary report."""
        # Mock basic setup
        self.cli.manager.list_all_providers.return_value = ["openai", "anthropic"]
        self.cli.manager.get_provider_status.return_value = {"configured": True}
        self.cli.manager.get_default_provider.return_value = "openai"
        
        # Mock file permissions check
        config_file = Mock()
        config_file.exists.return_value = True
        config_file.stat.return_value = Mock(st_mode=0o600)
        self.cli.manager.llm_config_path = config_file
        
        # Mock non-interactive check to allow testing
        with patch.object(self.cli, '_check_non_interactive'):
            with patch('builtins.print') as mock_print:
                self.cli.doctor()
                
                # Verify summary
                calls = mock_print.call_args_list
                assert any("2 providers total" in str(call) for call in calls)
    
    def test_placeholder_key_detection_in_doctor(self):
        """Test that doctor can detect and handle placeholder keys."""
        # Mock placeholder key detection
        with patch.object(self.cli, '_detect_placeholder_key') as mock_detect:
            mock_detect.return_value = True
            
            # Mock provider with placeholder key
            self.cli.manager.list_all_providers.return_value = ["anthropic"]
            self.cli.manager.get_provider_status.return_value = {"configured": False}
            self.cli.manager.get_default_provider.return_value = None
            
            # Mock provider config to return a placeholder key
            self.cli.manager.get_provider_config.return_value = {"api_key": "sk-ant-test-key"}
            
            # Mock file permissions check
            config_file = Mock()
            config_file.exists.return_value = True
            config_file.stat.return_value = Mock(st_mode=0o600)
            self.cli.manager.llm_config_path = config_file
            
            # Mock non-interactive check to allow testing
            with patch.object(self.cli, '_check_non_interactive'):
                with patch('builtins.input', return_value="y"):
                    with patch('builtins.print') as mock_print:
                        self.cli.doctor()
                        
                        # Verify placeholder detection was used
                        mock_detect.assert_called()
    
    def test_secure_permissions_handling(self):
        """Test secure permissions handling in doctor command."""
        # Mock permission issues that can't be fixed
        config_file = Mock()
        config_file.exists.return_value = True
        config_file.stat.return_value = Mock(st_mode=0o666)
        config_file.chmod.side_effect = PermissionError("Permission denied")
        self.cli.manager.llm_config_path = config_file
        
        # Mock other checks pass
        self.cli.manager.list_all_providers.return_value = ["openai"]
        self.cli.manager.get_provider_status.return_value = {"configured": True}
        self.cli.manager.get_default_provider.return_value = "openai"
        
        # Mock non-interactive check to allow testing
        with patch.object(self.cli, '_check_non_interactive'):
            with patch('builtins.print') as mock_print:
                self.cli.doctor()
                
                # Verify error handling
                calls = mock_print.call_args_list
                assert any("Cannot fix config file permissions" in str(call) for call in calls)
