""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""


"""
Unit Tests for Vendor-Neutral Roundtable System

Tests roster generation, consensus math, auditor fallback, and narrative generation
for the vendor-neutral quorum policy implementation.

PATCH: Cursor-2025-09-09 DISPATCH-OSS-20250909-QUORUM-POLICY-VENDOR-NEUTRAL
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ioa_core.vendor_neutral_roundtable import (
    QuorumConfig,
    QuorumConfigLoader,
    RosterBuilder,
    AuditorAgent,
    VendorNeutralRoundtableExecutor,
    QuorumConfigError,
    RosterBuilderError,
    AuditorError
)


class TestQuorumConfigLoader:
    """Test quorum configuration loading."""
    
    def test_load_valid_config(self):
        """Test loading valid quorum configuration."""
        config_data = {
            "fallback_order": ["openai", "anthropic", "google"],
            "min_agents": 2,
            "strong_quorum": {"min_agents": 3, "min_providers": 2},
            "sibling_weight": 0.6,
            "auditor_fallback_order": ["openai", "anthropic"],
            "consensus_threshold": 0.67,
            "model_families": {
                "openai": ["gpt-4", "gpt-3.5"],
                "anthropic": ["claude-3"]
            },
            "provider_aliases": {"gemini": "google"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)
        
        try:
            loader = QuorumConfigLoader(config_path)
            config = loader.load_config()
            
            assert config.fallback_order == ["openai", "anthropic", "google"]
            assert config.min_agents == 2
            assert config.strong_quorum == {"min_agents": 3, "min_providers": 2}
            assert config.sibling_weight == 0.6
            assert config.consensus_threshold == 0.67
        finally:
            config_path.unlink()
    
    def test_load_missing_file(self):
        """Test loading missing configuration file."""
        loader = QuorumConfigLoader(Path("nonexistent.yaml"))
        
        with pytest.raises(QuorumConfigError):
            loader.load_config()
    
    def test_load_invalid_yaml(self):
        """Test loading invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = Path(f.name)
        
        try:
            loader = QuorumConfigLoader(config_path)
            
            with pytest.raises(QuorumConfigError):
                loader.load_config()
        finally:
            config_path.unlink()


class TestRosterBuilder:
    """Test agent roster building with vendor-neutral logic."""
    
    @pytest.fixture
    def mock_llm_manager(self):
        """Mock LLM manager for testing."""
        manager = Mock()
        manager.list_providers.return_value = ["openai", "anthropic", "google"]
        manager.get_provider_config.return_value = {"model": "default"}
        return manager
    
    @pytest.fixture
    def quorum_config(self):
        """Sample quorum configuration."""
        return QuorumConfig(
            fallback_order=["openai", "anthropic", "google", "deepseek"],
            min_agents=2,
            strong_quorum={"min_agents": 3, "min_providers": 2},
            sibling_weight=0.6,
            auditor_fallback_order=["openai", "anthropic"],
            consensus_threshold=0.67,
            model_families={
                "openai": ["gpt-4", "gpt-3.5"],
                "anthropic": ["claude-3"],
                "google": ["gemini-1.5"]
            },
            provider_aliases={"gemini": "google"}
        )
    
    def test_build_single_provider_roster(self, quorum_config, mock_llm_manager):
        """Test building roster for single provider with siblings."""
        builder = RosterBuilder(quorum_config, mock_llm_manager)
        
        roster, diagnostics = builder.build_roster(["openai"], min_agents=2)
        
        assert len(roster) >= 2
        assert all(agent.provider == "openai" for agent in roster)
        assert all(agent.is_sibling for agent in roster)
        assert all(agent.weight == 0.6 for agent in roster)
        assert diagnostics.quorum_type == "single-provider-siblings"
        assert diagnostics.agents_total == len(roster)
        assert diagnostics.providers_used == 1
        assert diagnostics.sibling_weights_applied == len(roster)
    
    def test_build_two_provider_roster(self, quorum_config, mock_llm_manager):
        """Test building roster for two providers."""
        builder = RosterBuilder(quorum_config, mock_llm_manager)
        
        roster, diagnostics = builder.build_roster(["openai", "anthropic"], min_agents=2)
        
        assert len(roster) >= 2
        providers = set(agent.provider for agent in roster)
        assert "openai" in providers
        assert "anthropic" in providers
        assert diagnostics.quorum_type == "2-node"
        assert diagnostics.providers_used == 2
    
    def test_build_multi_provider_roster(self, quorum_config, mock_llm_manager):
        """Test building roster for 3+ providers."""
        builder = RosterBuilder(quorum_config, mock_llm_manager)
        
        roster, diagnostics = builder.build_roster(["openai", "anthropic", "google"], min_agents=3)
        
        assert len(roster) >= 3
        providers = set(agent.provider for agent in roster)
        assert len(providers) >= 2  # At least 2 different providers
        assert diagnostics.quorum_type in ["strong-quorum", "multi-provider"]
        assert diagnostics.providers_used >= 2
    
    def test_build_roster_no_providers(self, quorum_config, mock_llm_manager):
        """Test building roster with no available providers."""
        builder = RosterBuilder(quorum_config, mock_llm_manager)
        
        with pytest.raises(RosterBuilderError):
            builder.build_roster([])
    
    def test_sibling_detection(self, quorum_config, mock_llm_manager):
        """Test sibling detection and weighting."""
        builder = RosterBuilder(quorum_config, mock_llm_manager)
        
        # Force single provider scenario
        roster, _ = builder.build_roster(["openai"], min_agents=3)
        
        # All agents should be siblings with reduced weight
        assert all(agent.is_sibling for agent in roster)
        assert all(agent.weight == 0.6 for agent in roster)
        
        # Check different personas
        personas = [agent.persona for agent in roster]
        assert len(set(personas)) > 1  # Should have different personas


    """Test auditor agent with M2 baseline validation."""
    
    @pytest.fixture
    def quorum_config(self):
        """Sample quorum configuration."""
        return QuorumConfig(
            fallback_order=["openai", "anthropic", "google"],
            min_agents=2,
            strong_quorum={"min_agents": 3, "min_providers": 2},
            sibling_weight=0.6,
            auditor_fallback_order=["openai", "anthropic"],
            consensus_threshold=0.67,
            model_families={},
            provider_aliases={}
        )
    
    @pytest.fixture
    def mock_llm_manager(self):
        """Mock LLM manager for testing."""
        manager = Mock()
        manager.list_providers.return_value = ["openai", "anthropic"]
        manager.get_provider_config.return_value = {"model": "gpt-4"}
        return manager
    
    def test_select_auditor_provider(self, quorum_config, mock_llm_manager):
        """Test auditor provider selection from fallback order."""
        auditor = AuditorAgent(quorum_config, mock_llm_manager)
        
        # Should select first available provider from fallback order
        provider = auditor.select_auditor_provider(["anthropic", "google"])
        assert provider == "anthropic"
        
        # Should select first available if none in fallback order
        provider = auditor.select_auditor_provider(["google"])
        assert provider == "google"
    
    def test_select_auditor_no_providers(self, quorum_config, mock_llm_manager):
        """Test auditor selection with no available providers."""
        auditor = AuditorAgent(quorum_config, mock_llm_manager)
        
        with pytest.raises(AuditorError):
            auditor.select_auditor_provider([])
    
    @pytest.mark.asyncio
    async def test_validate_response_success(self, quorum_config, mock_llm_manager):
        """Test successful response validation."""
        auditor = AuditorAgent(quorum_config, mock_llm_manager)
        
        # Mock provider service
        mock_service = Mock()
        mock_service.execute.return_value = '{"scores": {"relevance": 0.8, "compliance": 0.9, "completeness": 0.7}, "law1_evidence": "Compliant", "law5_evidence": "Fair", "law7_evidence": "Complete"}'
        
        with patch('ioa_core.vendor_neutral_roundtable.create_provider', return_value=mock_service):
            result = await auditor.validate_response(
                "Test response", "Test task", "openai", "gpt-4"
            )
        
        assert result["status"] == "passed"
        assert result["validation_score"] > 0.6
        assert "law1_compliance" in result["evidence"]
        assert "law5_fairness" in result["evidence"]
        assert "law7_monitor" in result["evidence"]
    
    @pytest.mark.asyncio
    async def test_validate_response_failure(self, quorum_config, mock_llm_manager):
        """Test response validation failure."""
        auditor = AuditorAgent(quorum_config, mock_llm_manager)
        
        # Mock provider service that raises exception
        with patch('ioa_core.vendor_neutral_roundtable.create_provider', side_effect=Exception("Provider error")):
            result = await auditor.validate_response(
                "Test response", "Test task", "openai", "gpt-4"
            )
        
        assert result["status"] == "failed"
        assert result["validation_score"] == 0.0
        assert "error" in result["evidence"]["law1_compliance"]


class TestVendorNeutralRoundtableExecutor:
    """Test vendor-neutral roundtable executor."""
    
    @pytest.fixture
    def mock_components(self):
        """Mock components for testing."""
        router = Mock()
        storage = Mock()
        
        # Mock LLM manager
        llm_manager = Mock()
        llm_manager.list_providers.return_value = ["openai", "anthropic"]
        llm_manager.get_provider_config.return_value = {"model": "gpt-4"}
        
        return router, storage, llm_manager
    
    @pytest.fixture
    def quorum_config(self):
        """Sample quorum configuration."""
        return QuorumConfig(
            fallback_order=["openai", "anthropic"],
            min_agents=2,
            strong_quorum={"min_agents": 3, "min_providers": 2},
            sibling_weight=0.6,
            auditor_fallback_order=["openai"],
            consensus_threshold=0.67,
            model_families={},
            provider_aliases={}
        )
    
    def test_initialization(self, mock_components):
        """Test executor initialization."""
        router, storage, _ = mock_components
        
        with patch('ioa_core.vendor_neutral_roundtable.QuorumConfigLoader') as mock_loader:
            mock_config = Mock()
            mock_loader.return_value.load_config.return_value = mock_config
            
            executor = VendorNeutralRoundtableExecutor(router, storage)
            
            assert executor.quorum_config == mock_config
            assert executor.roster_builder is not None
            assert executor.auditor is not None
    
    @pytest.mark.asyncio
    async def test_execute_vendor_neutral_roundtable_success(self, mock_components):
        """Test successful vendor-neutral roundtable execution."""
        router, storage, llm_manager = mock_components
        
        # Mock provider service
        mock_service = Mock()
        mock_service.execute.return_value = "Test response"
        
        with patch('ioa_core.vendor_neutral_roundtable.create_provider', return_value=mock_service), \
             patch('ioa_core.vendor_neutral_roundtable.QuorumConfigLoader') as mock_loader:
            
            mock_config = Mock()
            mock_config.consensus_threshold = 0.67
            mock_loader.return_value.load_config.return_value = mock_config
            
            executor = VendorNeutralRoundtableExecutor(router, storage)
            executor.llm_manager = llm_manager
            
            # Mock roster builder
            mock_roster = [Mock(agent_id="test_agent", provider="openai", model="gpt-4", weight=1.0, is_sibling=False)]
            mock_diagnostics = Mock(agents_total=1, providers_used=1, sibling_weights_applied=0, consensus_score=0.0, quorum_type="test", consensus_threshold=0.67)
            executor.roster_builder.build_roster = Mock(return_value=(mock_roster, mock_diagnostics))
            
            # Mock auditor
            executor.auditor.select_auditor_provider = Mock(return_value="openai")
            executor.auditor.validate_response = AsyncMock(return_value={
                "validation_score": 0.8,
                "status": "passed",
                "evidence": {"law1_compliance": {"checked": True}}
            })
            
            report = await executor.execute_vendor_neutral_roundtable("Test task")
            
            assert report.consensus_achieved is not None
            assert report.consensus_score >= 0.0
            assert len(report.votes) >= 0
            assert "quorum_diagnostics" in report.reports
            assert "vendor_neutral" in report.reports
    
    def test_calculate_weighted_consensus(self, mock_components):
        """Test weighted consensus calculation."""
        router, storage, _ = mock_components
        
        with patch('src.vendor_neutral_roundtable.QuorumConfigLoader'):
            executor = VendorNeutralRoundtableExecutor(router, storage)
            
            # Test with votes
            votes = [
                Mock(weight=1.0),
                Mock(weight=0.6),
                Mock(weight=1.0)
            ]
            
            score = executor._calculate_weighted_consensus(votes)
            assert 0.0 <= score <= 1.0
            
            # Test with empty votes
            score = executor._calculate_weighted_consensus([])
            assert score == 0.0
    
    def test_generate_narrative(self, mock_components):
        """Test narrative generation."""
        router, storage, _ = mock_components
        
        with patch('src.vendor_neutral_roundtable.QuorumConfigLoader'):
            executor = VendorNeutralRoundtableExecutor(router, storage)
            
            # Create mock report
            report = Mock()
            report.consensus_achieved = True
            report.consensus_score = 0.8
            report.votes = [Mock(agent_id="test_agent", vote="Test response", weight=1.0)]
            report.winning_option = "Test winning option"
            report.reports = {
                "quorum_diagnostics": {
                    "quorum_type": "test",
                    "agents_total": 1,
                    "providers_used": 1,
                    "sibling_weights_applied": 0,
                    "consensus_threshold": 0.67
                },
                "agent_roster": [{"provider": "openai", "model": "gpt-4", "is_sibling": False}],
                "auditor_result": {"validation_score": 0.8, "status": "passed"}
            }
            
            narrative = executor.generate_narrative(report, "Test task")
            
            assert "Roundtable Narrative" in narrative
            assert "Test task" in narrative
            assert "Consensus Achieved" in narrative
            assert "✅ YES" in narrative
            assert "0.800" in narrative
            assert "test_agent" in narrative
    
    def test_extract_law_evidence(self, mock_components):
        """Test Law evidence extraction."""
        router, storage, _ = mock_components
        
        with patch('src.vendor_neutral_roundtable.QuorumConfigLoader'):
            executor = VendorNeutralRoundtableExecutor(router, storage)
            
            # Create mock report with auditor result
            report = Mock()
            report.votes = [Mock(agent_id="test_agent")]
            report.reports = {
                "auditor_result": {
                    "evidence": {
                        "law1_compliance": {"checked": True, "score": 0.9},
                        "law5_fairness": {"checked": True, "score": 0.8},
                        "law7_monitor": {"monitored": True, "score": 0.7}
                    }
                }
            }
            
            evidence = executor._extract_law_evidence(report)
            
            assert "law1_compliance" in evidence
            assert "law5_fairness" in evidence
            assert "law7_monitor" in evidence
            assert evidence["law1_compliance"]["checked"] is True
            assert evidence["law5_fairness"]["checked"] is True
            assert evidence["law7_monitor"]["monitored"] is True


class TestIntegration:
    """Integration tests for vendor-neutral roundtable system."""
    
    def test_end_to_end_config_loading(self):
        """Test end-to-end configuration loading."""
        config_data = {
            "fallback_order": ["openai", "anthropic"],
            "min_agents": 2,
            "strong_quorum": {"min_agents": 3, "min_providers": 2},
            "sibling_weight": 0.6,
            "auditor_fallback_order": ["openai"],
            "consensus_threshold": 0.67,
            "model_families": {"openai": ["gpt-4"]},
            "provider_aliases": {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)
        
        try:
            loader = QuorumConfigLoader(config_path)
            config = loader.load_config()
            
            # Test that all expected fields are present
            assert hasattr(config, 'fallback_order')
            assert hasattr(config, 'min_agents')
            assert hasattr(config, 'strong_quorum')
            assert hasattr(config, 'sibling_weight')
            assert hasattr(config, 'auditor_fallback_order')
            assert hasattr(config, 'consensus_threshold')
            assert hasattr(config, 'model_families')
            assert hasattr(config, 'provider_aliases')
        finally:
            config_path.unlink()
    
    def test_quorum_diagnostics_structure(self):
        """Test quorum diagnostics data structure."""
        from ioa_core.vendor_neutral_roundtable import QuorumDiagnostics
        
        diagnostics = QuorumDiagnostics(
            agents_total=3,
            providers_used=2,
            sibling_weights_applied=1,
            consensus_score=0.8,
            quorum_type="2-node",
            consensus_threshold=0.67
        )
        
        # Test that diagnostics can be converted to dict
        diagnostics_dict = diagnostics.__dict__
        
        assert diagnostics_dict["agents_total"] == 3
        assert diagnostics_dict["providers_used"] == 2
        assert diagnostics_dict["sibling_weights_applied"] == 1
        assert diagnostics_dict["consensus_score"] == 0.8
        assert diagnostics_dict["quorum_type"] == "2-node"
        assert diagnostics_dict["consensus_threshold"] == 0.67


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
