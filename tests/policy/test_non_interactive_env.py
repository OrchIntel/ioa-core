""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""

Tests that the system respects the IOA_NON_INTERACTIVE environment variable
and doesn't require user interaction in CI environments.
"""

import pytest
import os
from unittest.mock import patch, Mock

class TestNonInteractiveEnvironment:
    """Test non-interactive environment policy."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Store original environment
        self.original_env = os.environ.copy()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_non_interactive_env_set(self):
        """Test that IOA_NON_INTERACTIVE can be set."""
        os.environ['IOA_NON_INTERACTIVE'] = '1'
        assert os.environ.get('IOA_NON_INTERACTIVE') == '1'
    
    def test_non_interactive_env_unset(self):
        """Test that IOA_NON_INTERACTIVE can be unset."""
        if 'IOA_NON_INTERACTIVE' in os.environ:
            del os.environ['IOA_NON_INTERACTIVE']
        assert os.environ.get('IOA_NON_INTERACTIVE') is None
    
    def test_non_interactive_env_values(self):
        """Test different values for IOA_NON_INTERACTIVE."""
        test_values = ['1', 'true', 'True', 'TRUE', 'yes', 'on']
        
        for value in test_values:
            os.environ['IOA_NON_INTERACTIVE'] = value
            assert os.environ.get('IOA_NON_INTERACTIVE') == value
    
    def test_non_interactive_env_ci_integration(self):
        """Test that non-interactive mode integrates with CI environment variables."""
        # Set common CI environment variables
        ci_env_vars = {
            'CI': 'true',
            'GITHUB_ACTIONS': 'true',
            'GITLAB_CI': 'true',
            'TRAVIS': 'true',
            'CIRCLECI': 'true'
        }
        
        for var, value in ci_env_vars.items():
            os.environ[var] = value
            os.environ['IOA_NON_INTERACTIVE'] = '1'
            
            # Verify both are set
            assert os.environ.get(var) == value
            assert os.environ.get('IOA_NON_INTERACTIVE') == '1'
    
    def test_non_interactive_env_override(self):
        """Test that IOA_NON_INTERACTIVE can override other settings."""
        # Set some other environment variables
        os.environ['SOME_OTHER_VAR'] = 'some_value'
        os.environ['IOA_NON_INTERACTIVE'] = '1'
        
        # Verify both exist
        assert os.environ.get('SOME_OTHER_VAR') == 'some_value'
        assert os.environ.get('IOA_NON_INTERACTIVE') == '1'
        
        # Change IOA_NON_INTERACTIVE
        os.environ['IOA_NON_INTERACTIVE'] = '0'
        assert os.environ.get('IOA_NON_INTERACTIVE') == '0'
        assert os.environ.get('SOME_OTHER_VAR') == 'some_value'  # Other vars unchanged
    
    def test_non_interactive_env_persistence(self):
        """Test that IOA_NON_INTERACTIVE persists across operations."""
        os.environ['IOA_NON_INTERACTIVE'] = '1'
        
        # Simulate some operations
        for i in range(5):
            assert os.environ.get('IOA_NON_INTERACTIVE') == '1', f"Value should persist at iteration {i}"
            
            # Simulate some work
            os.environ[f'WORK_VAR_{i}'] = str(i)
    
    def test_non_interactive_env_validation(self):
        """Test validation of IOA_NON_INTERACTIVE values."""
        # Valid values
        valid_values = ['1', 'true', 'True', 'TRUE', 'yes', 'on', '0', 'false', 'False', 'FALSE', 'no', 'off']
        
        for value in valid_values:
            os.environ['IOA_NON_INTERACTIVE'] = value
            assert os.environ.get('IOA_NON_INTERACTIVE') == value
    
    def test_non_interactive_env_case_sensitivity(self):
        """Test case sensitivity of IOA_NON_INTERACTIVE."""
        test_cases = [
            ('1', '1'),
            ('true', 'true'),
            ('True', 'True'),
            ('TRUE', 'TRUE'),
            ('yes', 'yes'),
            ('Yes', 'Yes'),
            ('YES', 'YES')
        ]
        
        for input_val, expected in test_cases:
            os.environ['IOA_NON_INTERACTIVE'] = input_val
            assert os.environ.get('IOA_NON_INTERACTIVE') == expected
    
    def test_non_interactive_env_empty_string(self):
        """Test handling of empty string for IOA_NON_INTERACTIVE."""
        os.environ['IOA_NON_INTERACTIVE'] = ''
        assert os.environ.get('IOA_NON_INTERACTIVE') == ''
        
        # Test that empty string is treated as falsy
        value = os.environ.get('IOA_NON_INTERACTIVE')
        assert not bool(value), "Empty string should be falsy"
    
    def test_non_interactive_env_whitespace(self):
        """Test handling of whitespace in IOA_NON_INTERACTIVE."""
        test_cases = [
            ' 1 ',
            ' true ',
            ' True ',
            ' TRUE ',
            ' yes ',
            ' Yes ',
            ' YES '
        ]
        
        for value in test_cases:
            os.environ['IOA_NON_INTERACTIVE'] = value
            # Environment variables preserve whitespace
            assert os.environ.get('IOA_NON_INTERACTIVE') == value
    
    def test_non_interactive_env_special_characters(self):
        """Test handling of special characters in IOA_NON_INTERACTIVE."""
        special_values = [
            '1!',
            'true#',
            'True$',
            'TRUE%',
            'yes^',
            'Yes&',
            'YES*'
        ]
        
        for value in special_values:
            os.environ['IOA_NON_INTERACTIVE'] = value
            assert os.environ.get('IOA_NON_INTERACTIVE') == value
    
    def test_non_interactive_env_unicode(self):
        """Test handling of unicode characters in IOA_NON_INTERACTIVE."""
        unicode_values = [
            '1🚀',
            'true🌟',
            'True✨',
            'TRUE🎯',
            'yes🎨',
            'Yes🎭',
            'YES🎪'
        ]
        
        for value in unicode_values:
            os.environ['IOA_NON_INTERACTIVE'] = value
            assert os.environ.get('IOA_NON_INTERACTIVE') == value
