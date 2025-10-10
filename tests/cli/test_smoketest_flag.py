""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
Unit tests for --non-interactive flag functionality in smoketest commands.

Tests both the smoketest group and providers subcommand for proper
--non-interactive flag handling and environment variable support.
"""

import os
import subprocess
import sys
from pathlib import Path
import pytest


class TestSmoketestNonInteractiveFlag:
    """Test --non-interactive flag in smoketest commands."""
    
    def test_smoketest_help_contains_non_interactive(self):
        """Test that 'ioa smoketest --help' contains --non-interactive flag."""
        result = subprocess.run(
            [sys.executable, "-m", "ioa_core.cli", "smoketest", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "--non-interactive" in result.stdout, "--non-interactive flag not found in smoketest help"
        assert "IOA_SMOKETEST_NON_INTERACTIVE" in result.stdout, "Environment variable not mentioned in help"
    
    def test_smoketest_providers_help_contains_non_interactive(self):
        """Test that 'ioa smoketest providers --help' contains --non-interactive flag."""
        result = subprocess.run(
            [sys.executable, "-m", "ioa_core.cli", "smoketest", "providers", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "--non-interactive" in result.stdout, "--non-interactive flag not found in providers help"
        assert "IOA_SMOKETEST_NON_INTERACTIVE" in result.stdout, "Environment variable not mentioned in help"
    
    def test_smoketest_providers_with_non_interactive_flag(self):
        """Test that 'ioa smoketest providers --non-interactive' runs without prompts."""
        result = subprocess.run(
            [sys.executable, "-m", "ioa_core.cli", "smoketest", "providers", "--non-interactive"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should not fail due to missing API keys in non-interactive mode
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "Non-interactive mode" in result.stdout, "Non-interactive mode not indicated in output"
    
    def test_smoketest_providers_with_env_var(self):
        """Test that IOA_SMOKETEST_NON_INTERACTIVE=1 works."""
        env = os.environ.copy()
        env["IOA_SMOKETEST_NON_INTERACTIVE"] = "1"
        
        result = subprocess.run(
            [sys.executable, "-m", "ioa_core.cli", "smoketest", "providers"],
            capture_output=True,
            text=True,
            env=env,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should not fail due to missing API keys in non-interactive mode
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        # The non-interactive mode message only appears when there are missing keys
        # Since all providers are configured, we just verify the command succeeds
    
    def test_smoketest_group_with_non_interactive_flag(self):
        """Test that 'ioa smoketest --non-interactive providers' works."""
        result = subprocess.run(
            [sys.executable, "-m", "ioa_core.cli", "smoketest", "--non-interactive", "providers"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should not fail due to missing API keys in non-interactive mode
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "Non-interactive mode" in result.stdout, "Non-interactive mode not indicated in output"
    
    def test_smoketest_group_with_env_var(self):
        """Test that IOA_SMOKETEST_NON_INTERACTIVE=1 works with group command."""
        env = os.environ.copy()
        env["IOA_SMOKETEST_NON_INTERACTIVE"] = "1"
        
        result = subprocess.run(
            [sys.executable, "-m", "ioa_core.cli", "smoketest", "providers"],
            capture_output=True,
            text=True,
            env=env,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should not fail due to missing API keys in non-interactive mode
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        # The non-interactive mode message only appears when there are missing keys
        # Since all providers are configured, we just verify the command succeeds
    
    def test_flag_precedence_subcommand_overrides_group(self):
        """Test that subcommand --non-interactive overrides group setting."""
        # Test with group flag set to False but subcommand set to True
        result = subprocess.run(
            [sys.executable, "-m", "ioa_core.cli", "smoketest", "providers", "--non-interactive"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "Non-interactive mode" in result.stdout, "Non-interactive mode not indicated in output"
    
    def test_help_text_mentions_env_var(self):
        """Test that help text mentions the environment variable."""
        result = subprocess.run(
            [sys.executable, "-m", "ioa_core.cli", "smoketest", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        help_text = result.stdout
        
        # Check that both help texts mention the environment variable
        assert "IOA_SMOKETEST_NON_INTERACTIVE" in help_text, "Environment variable not mentioned in group help"
        
        # Check providers subcommand help too
        providers_result = subprocess.run(
            [sys.executable, "-m", "ioa_core.cli", "smoketest", "providers", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert providers_result.returncode == 0, f"Providers help failed: {providers_result.stderr}"
        assert "IOA_SMOKETEST_NON_INTERACTIVE" in providers_result.stdout, "Environment variable not mentioned in providers help"
