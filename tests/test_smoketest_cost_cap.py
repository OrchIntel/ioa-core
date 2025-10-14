"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
PATCH: Cursor-2025-01-08 DISPATCH-OSS-20250908-SMOKETEST-COST-CAP-MODEL-OVERRIDES
Unit and integration tests for cost cap and model override features.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from ioa_core.cli import app, _estimate_cost_usd, _run_provider_microcall


class TestCostEstimation:
    """Test cost estimation functionality."""
    
    def test_estimate_cost_openai_gpt4(self):
        """Test cost estimation for OpenAI GPT-4."""
        cost = _estimate_cost_usd("openai", "gpt-4", 1000, 500)
        # GPT-4: $0.03/1K input, $0.06/1K output
        expected = (1000/1000.0 * 0.03) + (500/1000.0 * 0.06)
        assert cost == expected
        assert cost > 0
    
    def test_estimate_cost_anthropic_haiku(self):
        """Test cost estimation for Anthropic Claude-3-Haiku."""
        cost = _estimate_cost_usd("anthropic", "claude-3-haiku", 1000, 500)
        # Claude-3-Haiku: $0.00025/1K input, $0.00125/1K output
        expected = (1000/1000.0 * 0.00025) + (500/1000.0 * 0.00125)
        assert cost == expected
        assert cost > 0
    
    def test_estimate_cost_google_gemini(self):
        """Test cost estimation for Google Gemini Pro."""
        cost = _estimate_cost_usd("google", "gemini-pro", 1000, 500)
        # Gemini Pro: $0.0005/1K input, $0.0015/1K output
        expected = (1000/1000.0 * 0.0005) + (500/1000.0 * 0.0015)
        assert cost == expected
        assert cost > 0
    
    def test_estimate_cost_deepseek(self):
        """Test cost estimation for DeepSeek."""
        cost = _estimate_cost_usd("deepseek", "deepseek-chat", 1000, 500)
        # DeepSeek: $0.00014/1K input, $0.00028/1K output
        expected = (1000/1000.0 * 0.00014) + (500/1000.0 * 0.00028)
        assert cost == expected
        assert cost > 0
    
    def test_estimate_cost_xai(self):
        """Test cost estimation for XAI Grok."""
        cost = _estimate_cost_usd("xai", "grok-beta", 1000, 500)
        # XAI: $0.0001/1K input, $0.0001/1K output
        expected = (1000/1000.0 * 0.0001) + (500/1000.0 * 0.0001)
        assert cost == expected
        assert cost > 0
    
    def test_estimate_cost_ollama(self):
        """Test cost estimation for Ollama (local, no cost)."""
        cost = _estimate_cost_usd("ollama", "llama3.1:8b", 1000, 500)
        assert cost == 0.0
    
    def test_estimate_cost_unknown_provider(self):
        """Test cost estimation for unknown provider uses default pricing."""
        cost = _estimate_cost_usd("unknown", "model", 1000, 500)
        # Default: $0.01/1K input, $0.02/1K output
        expected = (1000/1000.0 * 0.01) + (500/1000.0 * 0.02)
        assert cost == expected
    
    def test_estimate_cost_unknown_model(self):
        """Test cost estimation for unknown model uses provider default."""
        cost = _estimate_cost_usd("openai", "unknown-model", 1000, 500)
        # OpenAI default: $0.01/1K input, $0.02/1K output
        expected = (1000/1000.0 * 0.01) + (500/1000.0 * 0.02)
        assert cost == expected


class TestModelOverrides:
    """Test model override functionality."""
    
    def test_model_override_from_cli(self):
        """Test model override from CLI flags."""
        runner = CliRunner()
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch('ioa_core.cli._run_provider_microcall') as mock_call:
                mock_call.return_value = {
                    "provider": "openai",
                    "status": "passed",
                    "latency_ms": 100,
                    "tokens_in": 2,
                    "tokens_out": 1,
                    "model_used": "gpt-3.5-turbo",
                    "estimated_usd": 0.000005,
                    "http_status": 200,
                    "error": None
                }
                
                result = runner.invoke(app, [
                    'smoketest', '--live', '--openai-model', 'gpt-3.5-turbo', 'providers'
                ])
                
                assert result.exit_code == 0
                # Verify the model override was passed
                mock_call.assert_called()
                call_args = mock_call.call_args
                assert call_args[1]['model_overrides']['openai'] == 'gpt-3.5-turbo'
    
    def test_model_override_from_env(self):
        """Test model override from environment variables."""
        runner = CliRunner()
        
        with patch.dict(os.environ, {
            'IOA_SMOKETEST_LIVE': '1',
            'OPENAI_MODEL': 'gpt-4',
            'ANTHROPIC_MODEL': 'claude-3-opus',
            'OPENAI_API_KEY': 'test-key'
        }):
            with patch('ioa_core.cli._run_provider_microcall') as mock_call:
                mock_call.return_value = {
                    "provider": "openai",
                    "status": "passed",
                    "latency_ms": 100,
                    "tokens_in": 2,
                    "tokens_out": 1,
                    "model_used": "gpt-4",
                    "estimated_usd": 0.0001,
                    "http_status": 200,
                    "error": None
                }
                
                result = runner.invoke(app, ['smoketest', 'providers'])
                
                assert result.exit_code == 0
                # Verify the model overrides were applied
                mock_call.assert_called()
                call_args = mock_call.call_args
                assert call_args[1]['model_overrides']['openai'] == 'gpt-4'
                assert call_args[1]['model_overrides']['anthropic'] == 'claude-3-opus'


class TestCostCeiling:
    """Test cost ceiling functionality."""
    
    def test_cost_ceiling_from_cli(self):
        """Test cost ceiling from CLI flag."""
        runner = CliRunner()
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch('ioa_core.cli._run_provider_microcall') as mock_call:
                # Mock expensive calls that exceed ceiling
                mock_call.return_value = {
                    "provider": "openai",
                    "status": "passed",
                    "latency_ms": 100,
                    "tokens_in": 1000,
                    "tokens_out": 500,
                    "model_used": "gpt-4",
                    "estimated_usd": 0.06,  # Exceeds 0.01 ceiling
                    "http_status": 200,
                    "error": None
                }
                
                result = runner.invoke(app, [
                    'smoketest', '--live', '--max-usd', '0.01', 'providers'
                ])
                
                assert result.exit_code == 0
                assert "Cost ceiling" in result.output
    
    def test_cost_ceiling_from_env(self):
        """Test cost ceiling from environment variable."""
        runner = CliRunner()
        
        with patch.dict(os.environ, {
            'IOA_SMOKETEST_LIVE': '1',
            'IOA_SMOKETEST_MAX_USD': '0.005',
            'OPENAI_API_KEY': 'test-key'
        }):
            with patch('ioa_core.cli._run_provider_microcall') as mock_call:
                mock_call.return_value = {
                    "provider": "openai",
                    "status": "passed",
                    "latency_ms": 100,
                    "tokens_in": 1000,
                    "tokens_out": 500,
                    "model_used": "gpt-4",
                    "estimated_usd": 0.06,  # Exceeds 0.005 ceiling
                    "http_status": 200,
                    "error": None
                }
                
                result = runner.invoke(app, ['smoketest', 'providers'])
                
                assert result.exit_code == 0
                assert "Cost ceiling" in result.output
    
    def test_cost_ceiling_skips_remaining_providers(self):
        """Test that cost ceiling skips remaining providers."""
        runner = CliRunner()
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key', 'ANTHROPIC_API_KEY': 'test-key'}):
            call_count = 0
            def mock_call_side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    # First call succeeds but uses up most of the budget
                    return {
                        "provider": "openai",
                        "status": "passed",
                        "latency_ms": 100,
                        "tokens_in": 1000,
                        "tokens_out": 500,
                        "model_used": "gpt-4",
                        "estimated_usd": 0.05,  # Uses most of 0.06 budget
                        "http_status": 200,
                        "error": None
                    }
                else:
                    # Subsequent calls should be skipped due to cost cap
                    return {
                        "provider": "anthropic",
                        "status": "skipped",
                        "latency_ms": 0,
                        "tokens_in": 0,
                        "tokens_out": 0,
                        "model_used": "skipped",
                        "estimated_usd": 0.0,
                        "http_status": None,
                        "error": None
                    }
            
            with patch('ioa_core.cli._run_provider_microcall', side_effect=mock_call_side_effect):
                result = runner.invoke(app, [
                    'smoketest', '--live', '--max-usd', '0.06', 'providers'
                ])
                
                assert result.exit_code == 0
                assert "Cost ceiling" in result.output
                # Should make calls until budget is exceeded
                assert call_count >= 1


class TestProviderMicrocall:
    """Test provider microcall with model overrides."""
    
    @patch('ioa_core.llm_manager.LLMManager')
    def test_model_override_application(self, mock_manager_class):
        """Test that model overrides are applied correctly."""
        mock_manager = MagicMock()
        mock_service = MagicMock()
        mock_service.execute.return_value = "pong"
        mock_manager.create_service.return_value = mock_service
        mock_manager_class.return_value = mock_manager
        
        model_overrides = {"openai": "gpt-4"}
        
        result = _run_provider_microcall(
            "openai", 
            model=None, 
            max_tokens=3, 
            timeout_ms=12000,
            model_overrides=model_overrides
        )
        
        assert result["model_used"] == "gpt-4"
        assert result["status"] == "passed"
        assert result["estimated_usd"] > 0
    
    @patch('ioa_core.llm_manager.LLMManager')
    def test_default_model_selection(self, mock_manager_class):
        """Test default model selection when no override provided."""
        mock_manager = MagicMock()
        mock_service = MagicMock()
        mock_service.execute.return_value = "pong"
        mock_manager.create_service.return_value = mock_service
        mock_manager_class.return_value = mock_manager
        
        result = _run_provider_microcall(
            "openai", 
            model=None, 
            max_tokens=3, 
            timeout_ms=12000,
            model_overrides=None
        )
        
        assert result["model_used"] == "gpt-4o-mini"  # Default for OpenAI
        assert result["status"] == "passed"
        assert result["estimated_usd"] > 0
    
    def test_cost_estimation_in_microcall(self):
        """Test that cost estimation is included in microcall results."""
        with patch('ioa_core.llm_manager.LLMManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_service = MagicMock()
            mock_service.execute.return_value = "pong"
            mock_manager.create_service.return_value = mock_service
            mock_manager_class.return_value = mock_manager
            
            result = _run_provider_microcall(
                "openai", 
                model="gpt-3.5-turbo", 
                max_tokens=3, 
                timeout_ms=12000
            )
            
            assert "estimated_usd" in result
            assert result["estimated_usd"] > 0
            assert result["model_used"] == "gpt-3.5-turbo"


class TestIntegration:
    """Integration tests for the complete smoketest functionality."""
    
    def test_full_smoketest_with_cost_cap_and_overrides(self):
        """Test complete smoketest with cost cap and model overrides."""
        runner = CliRunner()
        
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-key',
            'ANTHROPIC_API_KEY': 'test-key'
        }):
            with patch('ioa_core.cli._run_provider_microcall') as mock_call:
                def mock_call_side_effect(provider_id, *args, **kwargs):
                    if provider_id == "openai":
                        return {
                            "provider": "openai",
                            "status": "passed",
                            "latency_ms": 100,
                            "tokens_in": 2,
                            "tokens_out": 1,
                            "model_used": "gpt-3.5-turbo",
                            "estimated_usd": 0.000005,
                            "http_status": 200,
                            "error": None
                        }
                    else:
                        return {
                            "provider": provider_id,
                            "status": "skipped",
                            "latency_ms": 0,
                            "tokens_in": 0,
                            "tokens_out": 0,
                            "model_used": "skipped",
                            "estimated_usd": 0.0,
                            "skip_reason": "cost_cap",
                            "http_status": None,
                            "error": None
                        }
                
                mock_call.side_effect = mock_call_side_effect
                
                result = runner.invoke(app, [
                    'smoketest', 
                    '--live', 
                    '--max-usd', '0.00001',  # Very low ceiling
                    '--openai-model', 'gpt-3.5-turbo',
                    'providers'
                ])
                
                assert result.exit_code == 0
                assert "Cost ceiling" in result.output
                assert "gpt-3.5-turbo" in result.output
                assert "PASSED" in result.output


if __name__ == "__main__":
    pytest.main([__file__])
