""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
Unit tests for CI Gates v1 system

This module provides comprehensive unit tests for the CI Gates validation system,
including configuration loading, gate execution, and artifact generation.
"""

import pytest
import json
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from ioa_core.ci_gates import (
    CIGatesConfig, CIGatesRunner, GateStatus, GateResult, GatesSummary,
    load_config, create_runner
)
from ioa_core.security_utils import SecurityScanner, SecurityScanResult
from ioa_core.pr_bot_utils import PRBotCommentGenerator, PRCommentData


class TestCIGatesConfig:
    """Test CI Gates configuration loading."""
    
    def test_load_config_success(self):
        """Test successful configuration loading."""
        config_data = {
            "version": 1,
            "mode": "monitor",
            "profiles": {
                "local": {"harness.requests": 500},
                "pr": {"harness.requests": 1000},
                "nightly": {"harness.requests": 10000}
            },
            "laws": [1, 2, 3, 4, 5, 6, 7],
            "gates": {
                "governance": True,
                "security": True,
                "docs": True,
                "hygiene": True
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            config = CIGatesConfig(config_path)
            assert config.config["version"] == 1
            assert config.config["mode"] == "monitor"
        finally:
            Path(config_path).unlink()
    
    def test_load_config_file_not_found(self):
        """Test configuration loading when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            CIGatesConfig("nonexistent.yml")
    
    def test_get_profile_success(self):
        """Test successful profile retrieval."""
        config_data = {
            "version": 1,
            "mode": "monitor",
            "profiles": {
                "local": {"harness.requests": 500}
            },
            "laws": [1, 2, 3, 4, 5, 6, 7],
            "gates": {"governance": True}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            config = CIGatesConfig(config_path)
            profile = config.get_profile("local")
            
            assert profile["harness.requests"] == 500
            assert profile["mode"] == "monitor"
            assert profile["laws"] == [1, 2, 3, 4, 5, 6, 7]
            assert profile["gates"]["governance"] is True
        finally:
            Path(config_path).unlink()
    
    def test_get_profile_not_found(self):
        """Test profile retrieval when profile doesn't exist."""
        config_data = {
            "version": 1,
            "profiles": {"local": {"harness.requests": 500}}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            config = CIGatesConfig(config_path)
            with pytest.raises(ValueError):
                config.get_profile("nonexistent")
        finally:
            Path(config_path).unlink()


class TestCIGatesRunner:
    """Test CI Gates runner functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.artifacts_dir = Path(self.temp_dir) / "artifacts"
        self.config_data = {
            "version": 1,
            "mode": "monitor",
            "profiles": {
                "local": {
                    "harness.requests": 500,
                    "gates": {
                        "governance": True,
                        "security": True,
                        "docs": True,
                        "hygiene": True
                    }
                }
            },
            "laws": [1, 2, 3, 4, 5, 6, 7],
            "ethics": {"mode": "monitor"},
            "sustainability": {"mode": "monitor"},
            "security": {"block_levels": ["HIGH", "MEDIUM"]},
            "hygiene": {"forbidden_patterns": ["**/*.pem"]},
            "docs": {"cli_validator": {"strict": True}}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(self.config_data, f)
            self.config_path = f.name
    
    def teardown_method(self):
        """Clean up test fixtures."""
        Path(self.config_path).unlink()
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_runner_initialization(self):
        """Test runner initialization."""
        config = CIGatesConfig(self.config_path)
        runner = CIGatesRunner(config, "local", self.artifacts_dir)
        
        assert runner.profile == "local"
        assert runner.profile_config["harness.requests"] == 500
        assert runner.artifacts_dir == self.artifacts_dir
    
    def test_get_enabled_gates(self):
        """Test getting enabled gates."""
        config = CIGatesConfig(self.config_path)
        runner = CIGatesRunner(config, "local", self.artifacts_dir)
        
        enabled_gates = runner._get_enabled_gates()
        expected_gates = ["governance", "security", "docs", "hygiene"]
        
        assert set(enabled_gates) == set(expected_gates)
    
    @patch('src.cli.ci_gates.subprocess.run')
    def test_run_command_success(self, mock_run):
        """Test successful command execution."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = b"Success"
        mock_result.stderr = b""
        mock_run.return_value = mock_result
        
        config = CIGatesConfig(self.config_path)
        runner = CIGatesRunner(config, "local")
        
        result = runner._run_command(["echo", "test"])
        
        assert result.returncode == 0
        assert result.stdout == b"Success"
        mock_run.assert_called_once()
    
    @patch('src.cli.ci_gates.subprocess.run')
    def test_run_command_failure(self, mock_run):
        """Test command execution failure."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = b""
        mock_result.stderr = b"Error"
        mock_run.return_value = mock_result
        
        config = CIGatesConfig(self.config_path)
        runner = CIGatesRunner(config, "local")
        
        result = runner._run_command(["false"])
        
        assert result.returncode == 1
        assert result.stderr == b"Error"
    
    @patch('src.cli.ci_gates.subprocess.run')
    def test_run_command_not_found(self, mock_run):
        """Test command execution when command not found."""
        mock_run.side_effect = FileNotFoundError()
        
        config = CIGatesConfig(self.config_path)
        runner = CIGatesRunner(config, "local")
        
        result = runner._run_command(["nonexistent_command"])
        
        assert result.returncode == 127
        assert result.stderr == "Command not found"


class TestSecurityUtils:
    """Test security utilities."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.artifacts_dir = Path(self.temp_dir) / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_security_scanner_initialization(self):
        """Test security scanner initialization."""
        scanner = SecurityScanner(self.artifacts_dir)
        assert scanner.artifacts_dir == self.artifacts_dir
    
    @patch('src.cli.security_utils.subprocess.run')
    def test_run_bandit_scan_success(self, mock_run):
        """Test successful Bandit scan."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = b""
        mock_result.stderr = b""
        mock_run.return_value = mock_result
        
        # Create mock Bandit results file
        bandit_results = {
            "results": [],
            "metrics": {
                "_totals": {
                    "SEVERITY.HIGH": 0,
                    "SEVERITY.MEDIUM": 0,
                    "SEVERITY.LOW": 2
                }
            }
        }
        
        bandit_file = self.artifacts_dir / "bandit_results.json"
        with open(bandit_file, 'w') as f:
            json.dump(bandit_results, f)
        
        scanner = SecurityScanner(self.artifacts_dir)
        result = scanner.run_bandit_scan()
        
        assert result.tool == "bandit"
        assert result.status == "pass"
        assert result.summary["HIGH"] == 0
        assert result.summary["MEDIUM"] == 0
        assert result.summary["LOW"] == 2
    
    @patch('src.cli.security_utils.subprocess.run')
    def test_run_bandit_scan_failure(self, mock_run):
        """Test Bandit scan with security issues."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = b""
        mock_result.stderr = b""
        mock_run.return_value = mock_result
        
        # Create mock Bandit results file with HIGH severity issues
        bandit_results = {
            "results": [],
            "metrics": {
                "_totals": {
                    "SEVERITY.HIGH": 2,
                    "SEVERITY.MEDIUM": 1,
                    "SEVERITY.LOW": 5
                }
            }
        }
        
        bandit_file = self.artifacts_dir / "bandit_results.json"
        with open(bandit_file, 'w') as f:
            json.dump(bandit_results, f)
        
        scanner = SecurityScanner(self.artifacts_dir)
        result = scanner.run_bandit_scan(config={"block_levels": ["HIGH", "MEDIUM"]})
        
        assert result.tool == "bandit"
        assert result.status == "fail"  # Should fail due to HIGH severity issues
        assert result.summary["HIGH"] == 2
    
    @patch('src.cli.security_utils.subprocess.run')
    def test_run_trufflehog_scan_success(self, mock_run):
        """Test successful TruffleHog scan."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = b""
        mock_result.stderr = b""
        mock_run.return_value = mock_result
        
        # Create mock TruffleHog results file
        trufflehog_results = []
        trufflehog_file = self.artifacts_dir / "trufflehog_results.json"
        with open(trufflehog_file, 'w') as f:
            json.dump(trufflehog_results, f)
        
        scanner = SecurityScanner(self.artifacts_dir)
        result = scanner.run_trufflehog_scan()
        
        assert result.tool == "trufflehog"
        assert result.status == "pass"
        assert result.summary["secrets"] == 0
    
    @patch('src.cli.security_utils.subprocess.run')
    def test_run_hygiene_check_success(self, mock_run):
        """Test successful hygiene check."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = b""  # No violations found
        mock_result.stderr = b""
        mock_run.return_value = mock_result
        
        scanner = SecurityScanner(self.artifacts_dir)
        result = scanner.run_hygiene_check(["**/*.pem"])
        
        assert result.tool == "hygiene"
        assert result.status == "pass"
        assert result.summary["violations"] == 0
    
    @patch('src.cli.security_utils.subprocess.run')
    def test_run_hygiene_check_violations(self, mock_run):
        """Test hygiene check with violations."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "test.pem\nsecret.key\n"  # Violations found
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        scanner = SecurityScanner(self.artifacts_dir)
        result = scanner.run_hygiene_check(["**/*.pem", "**/*.key"])
        
        assert result.tool == "hygiene"
        assert result.status == "fail"
        assert result.summary["violations"] == 4


class TestPRBotUtils:
    """Test PR bot utilities."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.artifacts_dir = Path(self.temp_dir) / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_pr_bot_generator_initialization(self):
        """Test PR bot generator initialization."""
        generator = PRBotCommentGenerator(self.artifacts_dir)
        assert generator.artifacts_dir == self.artifacts_dir
    
    def test_generate_comment(self):
        """Test PR comment generation."""
        summary_data = {
            "profile": "pr",
            "mode": "monitor",
            "duration": 45.2,
            "total_gates": 4,
            "passed": 3,
            "warned": 1,
            "failed": 0,
            "skipped": 0,
            "results": [
                {
                    "name": "governance",
                    "status": "pass",
                    "message": "All governance checks passed",
                    "details": {"harness_requests": 1000},
                    "duration": 30.1,
                    "artifacts": []
                },
                {
                    "name": "security",
                    "status": "warn",
                    "message": "Security scan passed with warnings",
                    "details": {"bandit_low": 2},
                    "duration": 10.5,
                    "artifacts": []
                }
            ],
            "artifacts_dir": "artifacts/lens/gates",
            "timestamp": "2025-09-19T10:00:00Z"
        }
        
        generator = PRBotCommentGenerator(self.artifacts_dir)
        comment = generator.generate_comment(summary_data, 123)
        
        assert "CI Gates v1 — Summary (PR #123)" in comment
        assert "**Profile:** pr" in comment
        assert "**Mode:** monitor" in comment
        assert "**Duration:** 45.20s" in comment
        assert "✅ Passed: 3" in comment
        assert "⚠️ Warned: 1" in comment
        assert "governance" in comment
        assert "security" in comment
    
    def test_generate_status_report(self):
        """Test status report generation."""
        summary_data = {
            "profile": "nightly",
            "mode": "monitor",
            "duration": 120.5,
            "total_gates": 4,
            "passed": 4,
            "warned": 0,
            "failed": 0,
            "skipped": 0,
            "results": [
                {
                    "name": "governance",
                    "status": "pass",
                    "message": "All governance checks passed",
                    "details": {},
                    "duration": 60.0,
                    "artifacts": []
                }
            ],
            "artifacts_dir": "artifacts/lens/gates",
            "timestamp": "2025-09-19T02:00:00Z"
        }
        
        generator = PRBotCommentGenerator(self.artifacts_dir)
        report = generator.generate_status_report(summary_data)
        
        assert "# CI Gates v1 Status Report" in report
        assert "**Profile:** nightly" in report
        assert "**Total Gates:** 4" in report
        assert "**✅ Passed:** 4" in report
        assert "governance" in report
    
    def test_save_comment(self):
        """Test saving PR comment to file."""
        comment = "Test PR comment"
        generator = PRBotCommentGenerator(self.artifacts_dir)
        
        comment_file = generator.save_comment(comment, "test_comment.md")
        
        assert comment_file.exists()
        assert comment_file.name == "test_comment.md"
        
        with open(comment_file, 'r') as f:
            content = f.read()
        assert content == comment
    
    def test_save_status_report(self):
        """Test saving status report to file."""
        report = "Test status report"
        generator = PRBotCommentGenerator(self.artifacts_dir)
        
        report_file = generator.save_status_report(report, "test_report.md")
        
        assert report_file.exists()
        assert report_file.name == "test_report.md"
        
        with open(report_file, 'r') as f:
            content = f.read()
        assert content == report


class TestIntegration:
    """Integration tests for CI Gates system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.artifacts_dir = Path(self.temp_dir) / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_data = {
            "version": 1,
            "mode": "monitor",
            "profiles": {
                "test": {
                    "harness.requests": 100,
                    "gates": {
                        "governance": True,
                        "security": True,
                        "docs": False,  # Disable for faster testing
                        "hygiene": True
                    }
                }
            },
            "laws": [1, 2, 3],
            "ethics": {"mode": "monitor"},
            "sustainability": {"mode": "monitor"},
            "security": {"block_levels": ["HIGH"]},
            "hygiene": {"forbidden_patterns": ["**/*.pem"]}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(self.config_data, f)
            self.config_path = f.name
    
    def teardown_method(self):
        """Clean up test fixtures."""
        Path(self.config_path).unlink()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_config_loading_integration(self):
        """Test configuration loading integration."""
        config = load_config(self.config_path)
        assert isinstance(config, CIGatesConfig)
        assert config.config["version"] == 1
    
    def test_runner_creation_integration(self):
        """Test runner creation integration."""
        runner = create_runner("test", self.config_path)
        assert isinstance(runner, CIGatesRunner)
        assert runner.profile == "test"
        assert runner.profile_config["harness.requests"] == 100


if __name__ == "__main__":
    pytest.main([__file__])
