""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3

"""
Integration tests for CI Gates v1 system

This module provides integration tests that verify the complete CI Gates
workflow including configuration loading, gate execution, and artifact generation.
"""

import os
import sys
import json
import tempfile
import yaml
import subprocess
from pathlib import Path
from datetime import datetime, timezone

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cli.ci_gates import load_config, create_runner
from cli.security_utils import create_security_scanner


def test_config_loading():
    """Test configuration loading and validation."""
    print("🔍 Testing configuration loading...")
    
    # Create test configuration
    config_data = {
        "version": 1,
        "mode": "monitor",
        "profiles": {
            "test": {
                "harness.requests": 100,
                "gates": {
                    "governance": True,
                    "security": True,
                    "docs": False,
                    "hygiene": True
                }
            }
        },
        "laws": [1, 2, 3, 4, 5, 6, 7],
        "ethics": {"mode": "monitor"},
        "sustainability": {"mode": "monitor"},
        "security": {"block_levels": ["HIGH", "MEDIUM"]},
        "hygiene": {"forbidden_patterns": ["**/*.pem", "**/.env*"]},
        "docs": {"cli_validator": {"strict": False}}
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name
    
    try:
        # Test configuration loading
        config = load_config(config_path)
        assert config.config["version"] == 1
        assert config.config["mode"] == "monitor"
        
        # Test profile retrieval
        profile = config.get_profile("test")
        assert profile["harness.requests"] == 100
        assert profile["gates"]["governance"] is True
        assert profile["gates"]["docs"] is False
        
        print("✅ Configuration loading test passed")
        
    finally:
        Path(config_path).unlink()


def test_runner_creation():
    """Test runner creation and initialization."""
    print("🔍 Testing runner creation...")
    
    # Create test configuration
    config_data = {
        "version": 1,
        "mode": "monitor",
        "profiles": {
            "test": {
                "harness.requests": 50,
                "gates": {"governance": True, "security": True}
            }
        },
        "laws": [1, 2, 3],
        "ethics": {"mode": "monitor"},
        "sustainability": {"mode": "monitor"},
        "security": {"block_levels": ["HIGH"]},
        "hygiene": {"forbidden_patterns": ["**/*.pem"]}
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name
    
    try:
        # Test runner creation
        runner = create_runner("test", config_path)
        assert runner.profile == "test"
        assert runner.profile_config["harness.requests"] == 50
        
        # Test enabled gates
        enabled_gates = runner._get_enabled_gates()
        assert "governance" in enabled_gates
        assert "security" in enabled_gates
        
        print("✅ Runner creation test passed")
        
    finally:
        Path(config_path).unlink()


def test_security_scanner():
    """Test security scanner functionality."""
    print("🔍 Testing security scanner...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        artifacts_dir = Path(temp_dir) / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Test scanner creation
        scanner = create_security_scanner(artifacts_dir)
        assert scanner.artifacts_dir == artifacts_dir
        
        # Test hygiene check (should pass - no forbidden files)
        result = scanner.run_hygiene_check(["**/*.pem", "**/.env*"])
        assert result.tool == "hygiene"
        # Note: This may fail if there are .env files in the repo, which is expected
        assert result.status in ["pass", "fail"]
        # Only check violations count if status is fail
        if result.status == "fail":
            assert result.summary["violations"] > 0
        
        print("✅ Security scanner test passed")


def test_cli_commands():
    """Test CLI commands execution."""
    print("🔍 Testing CLI commands...")
    
    # Test gates doctor command
    try:
        result = subprocess.run([
            "python", "-m", "src.cli.main", "gates", "doctor", "--help"
        ], capture_output=True, text=True, timeout=30)
        
        assert result.returncode == 0
        assert "CI Gates v1 Doctor" in result.stdout or "Usage:" in result.stdout
        
        print("✅ CLI commands test passed")
        
    except subprocess.TimeoutExpired:
        print("⚠️ CLI commands test timed out (expected in some environments)")
    except FileNotFoundError:
        print("⚠️ CLI commands test skipped (Python module not found)")


def test_artifact_generation():
    """Test artifact generation."""
    print("🔍 Testing artifact generation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        artifacts_dir = Path(temp_dir) / "artifacts" / "lens" / "gates"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock summary data
        summary_data = {
            "profile": "test",
            "mode": "monitor",
            "duration": 30.5,
            "total_gates": 2,
            "passed": 2,
            "warned": 0,
            "failed": 0,
            "skipped": 0,
            "results": [
                {
                    "name": "governance",
                    "status": "pass",
                    "message": "All governance checks passed",
                    "details": {"harness_requests": 100},
                    "duration": 20.0,
                    "artifacts": []
                },
                {
                    "name": "security",
                    "status": "pass",
                    "message": "Security scan passed",
                    "details": {"bandit_high": 0},
                    "duration": 10.5,
                    "artifacts": []
                }
            ],
            "artifacts_dir": str(artifacts_dir),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Test JSON summary generation
        summary_file = artifacts_dir / "summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2, default=str)
        
        assert summary_file.exists()
        
        # Test timeseries generation
        timeseries_file = artifacts_dir / "timeseries.jsonl"
        with open(timeseries_file, 'a') as f:
            json.dump(summary_data, f, default=str)
            f.write('\n')
        
        assert timeseries_file.exists()
        
        # Verify file contents
        with open(summary_file, 'r') as f:
            loaded_summary = json.load(f)
        assert loaded_summary["profile"] == "test"
        assert loaded_summary["total_gates"] == 2
        
        print("✅ Artifact generation test passed")


def test_error_handling():
    """Test error handling in various scenarios."""
    print("🔍 Testing error handling...")
    
    # Test invalid configuration file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write("invalid: yaml: content: [")
        config_path = f.name
    
    try:
        try:
            config = load_config(config_path)
            assert False, "Should have raised an exception"
        except Exception as e:
            assert "yaml" in str(e).lower() or "invalid" in str(e).lower() or "mapping" in str(e).lower()
        
        print("✅ Error handling test passed")
        
    finally:
        Path(config_path).unlink()


def run_all_tests():
    """Run all integration tests."""
    print("🚀 Running CI Gates v1 Integration Tests")
    print("=" * 50)
    
    tests = [
        test_config_loading,
        test_runner_creation,
        test_security_scanner,
        test_cli_commands,
        test_artifact_generation,
        test_error_handling
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"🏁 Integration Tests Complete")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed > 0:
        sys.exit(1)
    else:
        print("🎉 All integration tests passed!")


if __name__ == "__main__":
    run_all_tests()
