""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Test Suite for Reinforcement Policy Framework
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.


"""
Test Suite for Reinforcement Policy Framework
Tests for ETH-RL-003 implementation

Location: tests/test_reinforcement_policy.py
"""

import pytest
import json
import tempfile
import os
import sys
from unittest.mock import Mock, patch
from datetime import datetime

# Add src directory to Python path for imports
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from ioa.governance.reinforcement_policy import (
    ReinforcementPolicyFramework,
    RewardHandler,
    PunishmentHandler,
    CredentialSystem,
    AgentMetrics,
    RewardType,
    PunishmentType,
    CredentialLevel,
    create_roundtable_integration,
    create_sentinel_integration,
    create_memory_engine_hook
)


class TestAgentMetrics:
    """Test AgentMetrics dataclass"""
    
    def test_agent_metrics_creation(self):
        metrics = AgentMetrics(agent_id="test_agent_001")
        
        assert metrics.agent_id == "test_agent_001"
        assert metrics.satisfaction == 0.5
        assert metrics.stress == 0.0
        assert metrics.total_rewards == 0
        assert metrics.total_punishments == 0
        assert metrics.credential_level == CredentialLevel.BASIC.value
        assert metrics.last_updated is not None
        assert metrics.cycle_count == 0
    
    def test_agent_metrics_custom_values(self):
        metrics = AgentMetrics(
            agent_id="test_agent_002",
            satisfaction=0.8,
            stress=0.2,
            total_rewards=5,
            credential_level=CredentialLevel.ETHICS_LEVEL_1.value
        )
        
        assert metrics.satisfaction == 0.8
        assert metrics.stress == 0.2
        assert metrics.total_rewards == 5
        assert metrics.credential_level == CredentialLevel.ETHICS_LEVEL_1.value


class TestRewardHandler:
    """Test RewardHandler functionality"""
    
    def setup_method(self):
        self.reward_handler = RewardHandler()
        self.agent_metrics = AgentMetrics(agent_id="test_agent")
    
    def test_basic_reward_application(self):
        initial_satisfaction = self.agent_metrics.satisfaction
        
        event = self.reward_handler.apply_reward(
            self.agent_metrics,
            RewardType.ETHICAL_BEHAVIOR,
            ["pattern_001", "pattern_002"]
        )
        
        # Check satisfaction increased
        assert self.agent_metrics.satisfaction > initial_satisfaction
        assert self.agent_metrics.total_rewards == 1
        assert event.event_type == "reward"
        assert event.category == RewardType.ETHICAL_BEHAVIOR.value
        assert event.patterns_affected == ["pattern_001", "pattern_002"]
    
    def test_reward_type_multipliers(self):
        ethical_event = self.reward_handler.apply_reward(
            self.agent_metrics,
            RewardType.ETHICAL_BEHAVIOR,
            ["pattern_001"]
        )
        
        # Reset metrics
        self.agent_metrics.satisfaction = 0.5
        
        task_event = self.reward_handler.apply_reward(
            self.agent_metrics,
            RewardType.TASK_SUCCESS,
            ["pattern_002"]
        )
        
        # Ethical behavior should have higher multiplier
        assert ethical_event.magnitude > task_event.magnitude
    
    def test_satisfaction_bounds(self):
        # Set satisfaction close to max
        self.agent_metrics.satisfaction = 0.95
        
        self.reward_handler.apply_reward(
            self.agent_metrics,
            RewardType.ETHICAL_BEHAVIOR,
            ["pattern_001"]
        )
        
        # Should not exceed 1.0
        assert self.agent_metrics.satisfaction <= 1.0
    
    def test_custom_magnitude(self):
        event = self.reward_handler.apply_reward(
            self.agent_metrics,
            RewardType.TASK_SUCCESS,
            ["pattern_001"],
            custom_magnitude=0.5
        )
        
        # Should use custom magnitude instead of default
        assert event.magnitude == 0.5
    
    def test_heat_boost_multiplier(self):
        multiplier = self.reward_handler.get_heat_boost_multiplier(RewardType.ETHICAL_BEHAVIOR)
        assert multiplier > self.reward_handler.base_heat_multiplier


class TestPunishmentHandler:
    """Test PunishmentHandler functionality"""
    
    def setup_method(self):
        self.punishment_handler = PunishmentHandler()
        self.agent_metrics = AgentMetrics(agent_id="test_agent")
    
    def test_basic_punishment_application(self):
        initial_stress = self.agent_metrics.stress
        initial_satisfaction = self.agent_metrics.satisfaction
        
        event = self.punishment_handler.apply_punishment(
            self.agent_metrics,
            PunishmentType.ETHICAL_VIOLATION,
            ["pattern_001"]
        )
        
        # Check stress increased and satisfaction decreased
        assert self.agent_metrics.stress > initial_stress
        assert self.agent_metrics.satisfaction < initial_satisfaction
        assert self.agent_metrics.total_punishments == 1
        assert event.event_type == "punishment"
        assert event.category == PunishmentType.ETHICAL_VIOLATION.value
    
    def test_cold_ban_functionality(self):
        self.punishment_handler.apply_punishment(
            self.agent_metrics,
            PunishmentType.MALICIOUS_BEHAVIOR,
            ["malicious_pattern_001"]
        )
        
        # Pattern should be cold banned
        assert self.punishment_handler.is_pattern_banned(
            self.agent_metrics.agent_id, 
            "malicious_pattern_001"
        )
        
        # Other patterns should not be banned
        assert not self.punishment_handler.is_pattern_banned(
            self.agent_metrics.agent_id,
            "safe_pattern_001"
        )
    
    def test_escalation(self):
        normal_event = self.punishment_handler.apply_punishment(
            self.agent_metrics,
            PunishmentType.TASK_FAILURE,
            ["pattern_001"]
        )
        
        # Reset metrics
        self.agent_metrics.stress = 0.0
        
        escalated_event = self.punishment_handler.apply_punishment(
            self.agent_metrics,
            PunishmentType.TASK_FAILURE,
            ["pattern_002"],
            escalate=True
        )
        
        # Escalated punishment should be more severe
        assert escalated_event.magnitude > normal_event.magnitude
    
    def test_stress_bounds(self):
        # Set stress close to max
        self.agent_metrics.stress = 0.95
        
        self.punishment_handler.apply_punishment(
            self.agent_metrics,
            PunishmentType.ETHICAL_VIOLATION,
            ["pattern_001"]
        )
        
        # Should not exceed 1.0
        assert self.agent_metrics.stress <= 1.0


class TestCredentialSystem:
    """Test CredentialSystem functionality"""
    
    def setup_method(self):
        # Create temporary registry file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.write('{"agents": {}, "metadata": {"version": "1.0"}}')
        self.temp_file.close()
        
        self.credential_system = CredentialSystem(registry_path=self.temp_file.name)
        self.agent_metrics = AgentMetrics(agent_id="test_agent")
    
    def teardown_method(self):
        # Clean up temp file
        os.unlink(self.temp_file.name)
    
    def test_promotion_evaluation_insufficient(self):
        # Agent with default metrics should not qualify for promotion
        promotion = self.credential_system.evaluate_promotion(self.agent_metrics)
        assert promotion is None
    
    def test_promotion_evaluation_qualified(self):
        # Set agent metrics to qualify for ETHICS_LEVEL_1
        self.agent_metrics.satisfaction = 0.8
        self.agent_metrics.stress = 0.2
        self.agent_metrics.cycle_count = 15
        self.agent_metrics.total_rewards = 10
        
        promotion = self.credential_system.evaluate_promotion(self.agent_metrics)
        assert promotion == CredentialLevel.ETHICS_LEVEL_1
    
    def test_agent_promotion(self):
        success = self.credential_system.promote_agent(
            self.agent_metrics,
            CredentialLevel.ETHICS_LEVEL_1
        )
        
        assert success
        assert self.agent_metrics.credential_level == CredentialLevel.ETHICS_LEVEL_1.value
        
        # Should be recorded in registry
        assert self.agent_metrics.agent_id in self.credential_system.registry["agents"]
    
    def test_permissions_by_level(self):
        basic_perms = self.credential_system.get_agent_permissions(CredentialLevel.BASIC)
        senior_perms = self.credential_system.get_agent_permissions(CredentialLevel.SENIOR_COUNCIL)
        
        # Basic agents should have limited access
        assert not basic_perms["sensitive_memory_access"]
        assert basic_perms["roundtable_voting_weight"] == 1.0
        
        # Senior council should have full access
        assert senior_perms["sensitive_memory_access"]
        assert senior_perms["roundtable_voting_weight"] == 3.0
        assert senior_perms.get("can_override_votes", False)


class TestReinforcementPolicyFramework:
    """Test main framework integration"""
    
    def setup_method(self):
        # Create temporary registry
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.write('{"agents": {}, "metadata": {"version": "1.0"}}')
        self.temp_file.close()
        
        config = {"registry_path": self.temp_file.name}
        self.framework = ReinforcementPolicyFramework(config)
        self.agent_metrics = AgentMetrics(agent_id="test_agent")
        
        # Mock memory engine hook
        self.memory_hook = Mock()
        self.framework.register_hooks(memory_engine_hook=self.memory_hook)
    
    def teardown_method(self):
        os.unlink(self.temp_file.name)
    
    def test_process_reward_integration(self):
        event = self.framework.process_reward(
            self.agent_metrics,
            RewardType.ETHICAL_BEHAVIOR,
            ["pattern_001", "pattern_002"]
        )
        
        # Check all side effects
        assert self.agent_metrics.satisfaction > 0.5  # Increased from default
        assert self.agent_metrics.cycle_count == 1    # Incremented
        assert len(self.framework.event_history) == 1  # Event recorded
        
        # Memory hook should have been called
        self.memory_hook.assert_called_once()
        call_args = self.memory_hook.call_args[0]
        assert call_args[0] == 'boost_pattern_heat'
        assert 'pattern_001' in call_args[1]['patterns']
    
    def test_process_punishment_integration(self):
        event = self.framework.process_punishment(
            self.agent_metrics,
            PunishmentType.ETHICAL_VIOLATION,
            ["bad_pattern_001"]
        )
        
        # Check all side effects
        assert self.agent_metrics.stress > 0.0        # Increased from default
        assert self.agent_metrics.cycle_count == 1    # Incremented
        assert len(self.framework.event_history) == 1  # Event recorded
        
        # Memory hook should have been called for decay
        self.memory_hook.assert_called_once()
        call_args = self.memory_hook.call_args[0]
        assert call_args[0] == 'decay_pattern_heat'
    
    def test_agent_status_comprehensive(self):
        # Apply some rewards and punishments
        self.framework.process_reward(
            self.agent_metrics,
            RewardType.ETHICAL_BEHAVIOR,
            ["pattern_001"]
        )
        self.framework.process_punishment(
            self.agent_metrics,
            PunishmentType.TASK_FAILURE,
            ["pattern_002"]
        )
        
        status = self.framework.get_agent_status(
            self.agent_metrics.agent_id,
            self.agent_metrics
        )
        
        # Check all status fields are present
        required_fields = [
            "agent_id", "satisfaction", "stress", "wellness_score",
            "reward_ratio", "total_rewards", "total_punishments",
            "cycle_count", "credential_level", "permissions",
            "banned_patterns", "last_updated"
        ]
        
        for field in required_fields:
            assert field in status
        
        # Check calculated fields
        assert 0.0 <= status["wellness_score"] <= 1.0
        assert 0.0 <= status["reward_ratio"] <= 1.0
    
    def test_framework_statistics(self):
        # Generate some activity
        self.framework.process_reward(
            self.agent_metrics,
            RewardType.ETHICAL_BEHAVIOR,
            ["pattern_001"]
        )
        
        agent2 = AgentMetrics(agent_id="test_agent_2")
        self.framework.process_punishment(
            agent2,
            PunishmentType.TASK_FAILURE,
            ["pattern_002"]
        )
        
        stats = self.framework.get_framework_stats()
        
        assert stats["total_events"] == 2
        assert stats["reward_events"] == 1
        assert stats["punishment_events"] == 1
        assert stats["unique_agents"] == 2


class TestIntegrationHelpers:
    """Test integration helper functions"""
    
    def setup_method(self):
        self.framework = ReinforcementPolicyFramework()
        self.agent_metrics = AgentMetrics(agent_id="test_agent")
    
    def test_roundtable_integration(self):
        integration = create_roundtable_integration(self.framework)
        
        vote_result = {
            "outcome": "ethical_override_success",
            "ethical_voters": [self.agent_metrics],
            "patterns_involved": ["pattern_001"]
        }
        
        initial_satisfaction = self.agent_metrics.satisfaction
        integration.handle_vote_outcome(vote_result, [self.agent_metrics])
        
        # Should have applied reward
        assert self.agent_metrics.satisfaction > initial_satisfaction
        assert len(self.framework.event_history) == 1
    
    def test_sentinel_integration(self):
        integration = create_sentinel_integration(self.framework)
        
        violation = {
            "severity": "critical",
            "patterns_involved": ["malicious_pattern_001"],
            "description": "Attempted unauthorized access"
        }
        
        initial_stress = self.agent_metrics.stress
        integration.handle_law_violation(self.agent_metrics, violation)
        
        # Should have applied punishment
        assert self.agent_metrics.stress > initial_stress
        assert len(self.framework.event_history) == 1
    
    def test_memory_engine_hook(self):
        hook = create_memory_engine_hook()
        
        # Should handle boost action without error
        hook('boost_pattern_heat', {
            'patterns': ['pattern_001'],
            'multiplier': 1.5
        })
        
        # Should handle decay action without error
        hook('decay_pattern_heat', {
            'patterns': ['pattern_002'],
            'decay_factor': 0.8
        })


if __name__ == "__main__":
    pytest.main([__file__])