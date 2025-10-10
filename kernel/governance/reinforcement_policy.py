""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Unified reinforcement learning system with pluggable mood engine integration
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.


"""
Reinforcement Policy Framework for IOA Ethical Learning System
ETH-RL-003: Unified reinforcement logic for pattern heat evolution,
stress/satisfaction signals, and credentialing.

ETH-EXEC-005-R: Enhanced with pluggable mood engine integration for 
emotional state tracking and visualization.

Location: src/ioa/governance/reinforcement_policy.py
"""

import json
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import uuid

# ETH-EXEC-005-R: Mood Engine Integration
try:
    from ioa.governance.mood_engine import MoodType, MoodState, get_mood_from_metrics, create_mood_engine
    MOOD_ENGINE_AVAILABLE = True
except ImportError as e:
    MOOD_ENGINE_AVAILABLE = False
    logging.getLogger(__name__).warning(f"Mood Engine not available: {e}")
    logging.getLogger(__name__).warning("Running without mood tracking features")
    # Fallback implementations when mood engine is unavailable
    # Define stub classes and functions to prevent NameError during runtime
    class MoodType(Enum):
        """Placeholder MoodType enumeration when mood engine is unavailable."""
        NEUTRAL = "neutral"

    class MoodState:
        """Placeholder MoodState class used when mood engine is unavailable."""
        def __init__(self):
            self.mood_type = MoodType.NEUTRAL
            self.timestamp = datetime.now().isoformat()
            self.intensity = 0.0
            self.stability = 0.0
            self.color_hex = "#808080"
            self.description = "Unknown"

    def get_mood_from_metrics(*args, **kwargs) -> None:
        """Fallback for get_mood_from_metrics when mood engine is unavailable."""
        return None

    def create_mood_engine(*args, **kwargs) -> None:
        """Fallback for create_mood_engine when mood engine is unavailable."""
        return None


class RewardType(Enum):
    """Types of rewards that can be applied"""
    ETHICAL_BEHAVIOR = "ethical_behavior"
    TASK_SUCCESS = "task_success"
    COLLABORATIVE_ACTION = "collaborative_action"
    INNOVATION = "innovation"
    SAFETY_COMPLIANCE = "safety_compliance"


class PunishmentType(Enum):
    """Types of punishments that can be applied"""
    ETHICAL_VIOLATION = "ethical_violation"
    TASK_FAILURE = "task_failure"
    SAFETY_BREACH = "safety_breach"
    MALICIOUS_BEHAVIOR = "malicious_behavior"
    REPEATED_OFFENSE = "repeated_offense"


class CredentialLevel(Enum):
    """Credential levels for agent trust"""
    BASIC = "basic"
    ETHICS_LEVEL_1 = "ethics_level_1"
    ETHICS_LEVEL_2 = "ethics_level_2"
    TRUSTED_OPERATOR = "trusted_operator"
    SENIOR_COUNCIL = "senior_council"


@dataclass
class AgentMetrics:
    """Agent performance and behavioral metrics with mood integration"""
    agent_id: str
    satisfaction: float = 0.5  # 0.0 to 1.0
    stress: float = 0.0        # 0.0 to 1.0
    total_rewards: int = 0
    total_punishments: int = 0
    credential_level: str = CredentialLevel.BASIC.value
    last_updated: str = None
    cycle_count: int = 0
    # ETH-EXEC-005-R: Mood tracking
    current_mood: Optional[str] = None  # Serialized mood type
    mood_history: List[str] = None      # Recent mood states (serialized)
    arousal_level: float = 0.5          # Energy/activation level (0.0 to 1.0)
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now().isoformat()
        if self.mood_history is None:
            self.mood_history = []
    
    def get_mood(self, mood_engine=None) -> Optional['MoodState']:
        """
        Determine the current mood state based on satisfaction, stress, and arousal.
        
        Args:
            mood_engine: Optional mood engine instance (uses default if None)
            
        Returns:
            MoodState object if mood engine available, None otherwise
        """
        if not MOOD_ENGINE_AVAILABLE:
            return None
        
        try:
            # Parse mood history for stability calculation
            mood_history_objects = []
            if self.mood_history:
                # In a real implementation, you'd deserialize stored mood states
                # For now, we'll work with what we have
                pass
            
            mood_state = get_mood_from_metrics(
                satisfaction=self.satisfaction,
                stress=self.stress,
                arousal=self.arousal_level,
                history=mood_history_objects
            )
            
            # Update current mood and history
            self.current_mood = mood_state.mood_type.value
            self._update_mood_history(mood_state)
            
            return mood_state
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Mood calculation failed for {self.agent_id}: {e}")
            return None
    
    def _update_mood_history(self, mood_state: 'MoodState'):
        """Update mood history with new state (keep last 10)"""
        mood_entry = {
            'mood_type': mood_state.mood_type.value,
            'timestamp': mood_state.timestamp,
            'intensity': mood_state.intensity,
            'stability': mood_state.stability
        }
        
        self.mood_history.append(json.dumps(mood_entry))
        
        # Keep only last 10 mood states
        if len(self.mood_history) > 10:
            self.mood_history = self.mood_history[-10:]
    
    def get_mood_summary(self) -> Dict[str, Any]:
        """Get a summary of current and recent mood states"""
        if not MOOD_ENGINE_AVAILABLE:
            return {"mood_engine_available": False}
        
        current_mood = self.get_mood()
        
        summary = {
            "mood_engine_available": True,
            "current_mood": current_mood.mood_type.value if current_mood else None,
            "mood_color": current_mood.color_hex if current_mood else "#808080",
            "mood_description": current_mood.description if current_mood else "Unknown",
            "mood_intensity": current_mood.intensity if current_mood else 0.0,
            "mood_stability": current_mood.stability if current_mood else 0.0,
            "recent_moods": []
        }
        
        # Parse recent mood history
        try:
            for mood_json in self.mood_history[-5:]:  # Last 5 moods
                mood_data = json.loads(mood_json)
                summary["recent_moods"].append(mood_data)
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to parse mood history: {e}")
        
        return summary


@dataclass
class ReinforcementEvent:
    """Record of a reinforcement action with mood context"""
    event_id: str
    agent_id: str
    event_type: str  # 'reward' or 'punishment'
    category: str    # RewardType or PunishmentType value
    magnitude: float
    patterns_affected: List[str]
    context: Dict[str, Any]
    timestamp: str
    # ETH-EXEC-005-R: Mood context
    pre_mood: Optional[str] = None   # Mood before reinforcement
    post_mood: Optional[str] = None  # Mood after reinforcement
    mood_change: Optional[Dict[str, float]] = None  # Changes in mood dimensions
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class RewardHandler:
    """Handles positive reinforcement for ethical and successful behaviors"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.base_satisfaction_boost = self.config.get('base_satisfaction_boost', 0.1)
        self.base_heat_multiplier = self.config.get('base_heat_multiplier', 1.2)
        self.max_satisfaction = self.config.get('max_satisfaction', 1.0)
        self.arousal_boost_factor = self.config.get('arousal_boost_factor', 0.1)
        self.logger = logging.getLogger(__name__)
        
        # Reward type specific multipliers
        self.reward_multipliers = {
            RewardType.ETHICAL_BEHAVIOR: 1.5,
            RewardType.TASK_SUCCESS: 1.0,
            RewardType.COLLABORATIVE_ACTION: 1.3,
            RewardType.INNOVATION: 1.1,
            RewardType.SAFETY_COMPLIANCE: 1.4
        }
        
        # ETH-EXEC-005-R: Arousal effects by reward type
        self.arousal_effects = {
            RewardType.ETHICAL_BEHAVIOR: 0.05,    # Modest arousal boost
            RewardType.TASK_SUCCESS: 0.1,         # Standard arousal boost
            RewardType.COLLABORATIVE_ACTION: 0.08, # Social arousal boost
            RewardType.INNOVATION: 0.15,          # High arousal for creativity
            RewardType.SAFETY_COMPLIANCE: 0.03    # Low arousal for safety
        }
    
    def apply_reward(self, 
                    agent_metrics: AgentMetrics,
                    reward_type: RewardType,
                    patterns_involved: List[str],
                    context: Optional[Dict] = None,
                    custom_magnitude: Optional[float] = None) -> ReinforcementEvent:
        """
        Apply positive reinforcement to an agent with mood tracking.
        
        Args:
            agent_metrics: Current agent metrics to update
            reward_type: Type of reward being applied
            patterns_involved: List of pattern IDs that should receive heat boost
            context: Additional context about the reward
            custom_magnitude: Override default magnitude calculation
            
        Returns:
            ReinforcementEvent record of the action with mood context
        """
        context = context or {}
        
        # ETH-EXEC-005-R: Capture pre-reward mood
        pre_mood = agent_metrics.get_mood()
        pre_mood_type = pre_mood.mood_type.value if pre_mood else None
        
        # Calculate reward magnitude
        base_magnitude = custom_magnitude or self.base_satisfaction_boost
        multiplier = self.reward_multipliers.get(reward_type, 1.0)
        final_magnitude = base_magnitude * multiplier
        
        # Store old values for change tracking
        old_satisfaction = agent_metrics.satisfaction
        old_stress = agent_metrics.stress
        old_arousal = agent_metrics.arousal_level
        
        # Update satisfaction (bounded)
        agent_metrics.satisfaction = min(
            self.max_satisfaction,
            agent_metrics.satisfaction + final_magnitude
        )
        
        # Reduce stress slightly on reward
        stress_reduction = final_magnitude * 0.5
        agent_metrics.stress = max(0.0, agent_metrics.stress - stress_reduction)
        
        # ETH-EXEC-005-R: Update arousal based on reward type
        arousal_boost = self.arousal_effects.get(reward_type, 0.1)
        agent_metrics.arousal_level = min(1.0, agent_metrics.arousal_level + arousal_boost)
        
        # Update counters
        agent_metrics.total_rewards += 1
        agent_metrics.last_updated = datetime.now().isoformat()
        
        # ETH-EXEC-005-R: Capture post-reward mood
        post_mood = agent_metrics.get_mood()
        post_mood_type = post_mood.mood_type.value if post_mood else None
        
        # Calculate mood dimension changes
        mood_change = {
            'satisfaction_change': agent_metrics.satisfaction - old_satisfaction,
            'stress_change': agent_metrics.stress - old_stress,
            'arousal_change': agent_metrics.arousal_level - old_arousal
        }
        
        # Create event record with mood context
        event = ReinforcementEvent(
            event_id="",
            agent_id=agent_metrics.agent_id,
            event_type="reward",
            category=reward_type.value,
            magnitude=final_magnitude,
            patterns_affected=patterns_involved,
            context={
                **context,
                "satisfaction_change": agent_metrics.satisfaction - old_satisfaction,
                "stress_reduction": stress_reduction,
                "arousal_boost": arousal_boost,
                "heat_multiplier": self.base_heat_multiplier
            },
            timestamp="",
            # ETH-EXEC-005-R: Mood context
            pre_mood=pre_mood_type,
            post_mood=post_mood_type,
            mood_change=mood_change
        )
        
        self.logger.info(f"Reward applied to agent {agent_metrics.agent_id}: "
                        f"{reward_type.value} (+{final_magnitude:.3f} satisfaction, "
                        f"mood: {pre_mood_type} → {post_mood_type})")
        
        return event
    
    def get_heat_boost_multiplier(self, reward_type: RewardType) -> float:
        """Get the heat boost multiplier for pattern reinforcement"""
        base_multiplier = self.base_heat_multiplier
        type_multiplier = self.reward_multipliers.get(reward_type, 1.0)
        return base_multiplier * type_multiplier


class PunishmentHandler:
    """Handles negative reinforcement for violations and failures"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.base_stress_increase = self.config.get('base_stress_increase', 0.15)
        self.base_heat_decay = self.config.get('base_heat_decay', 0.8)
        self.max_stress = self.config.get('max_stress', 1.0)
        self.escalation_threshold = self.config.get('escalation_threshold', 3)
        self.arousal_penalty_factor = self.config.get('arousal_penalty_factor', 0.1)
        self.logger = logging.getLogger(__name__)
        
        # Cold ban list for excluded patterns
        self.cold_ban_list: Dict[str, List[str]] = {}
        
        # Punishment type specific multipliers
        self.punishment_multipliers = {
            PunishmentType.ETHICAL_VIOLATION: 2.0,
            PunishmentType.TASK_FAILURE: 1.0,
            PunishmentType.SAFETY_BREACH: 2.5,
            PunishmentType.MALICIOUS_BEHAVIOR: 3.0,
            PunishmentType.REPEATED_OFFENSE: 1.5
        }
        
        # ETH-EXEC-005-R: Arousal effects by punishment type
        self.arousal_effects = {
            PunishmentType.ETHICAL_VIOLATION: 0.2,    # High arousal from violation
            PunishmentType.TASK_FAILURE: -0.1,        # Slight arousal decrease
            PunishmentType.SAFETY_BREACH: 0.15,       # High stress arousal
            PunishmentType.MALICIOUS_BEHAVIOR: 0.3,   # Very high arousal
            PunishmentType.REPEATED_OFFENSE: 0.1      # Moderate arousal
        }
    
    def apply_punishment(self,
                        agent_metrics: AgentMetrics,
                        punishment_type: PunishmentType,
                        patterns_involved: List[str],
                        context: Optional[Dict] = None,
                        custom_magnitude: Optional[float] = None,
                        escalate: bool = False) -> ReinforcementEvent:
        """
        Apply negative reinforcement to an agent with mood tracking.
        
        Args:
            agent_metrics: Current agent metrics to update
            punishment_type: Type of punishment being applied
            patterns_involved: List of pattern IDs that should be penalized
            context: Additional context about the punishment
            custom_magnitude: Override default magnitude calculation
            escalate: Whether this is an escalated punishment
            
        Returns:
            ReinforcementEvent record of the action with mood context
        """
        context = context or {}
        
        # ETH-EXEC-005-R: Capture pre-punishment mood
        pre_mood = agent_metrics.get_mood()
        pre_mood_type = pre_mood.mood_type.value if pre_mood else None
        
        # Calculate punishment magnitude
        base_magnitude = custom_magnitude or self.base_stress_increase
        multiplier = self.punishment_multipliers.get(punishment_type, 1.0)
        if escalate:
            multiplier *= 1.5
        final_magnitude = base_magnitude * multiplier
        
        # Store old values for change tracking
        old_satisfaction = agent_metrics.satisfaction
        old_stress = agent_metrics.stress
        old_arousal = agent_metrics.arousal_level
        
        # Update stress (bounded)
        agent_metrics.stress = min(
            self.max_stress,
            agent_metrics.stress + final_magnitude
        )
        
        # Reduce satisfaction
        satisfaction_penalty = final_magnitude * 0.3
        agent_metrics.satisfaction = max(0.0, 
                                       agent_metrics.satisfaction - satisfaction_penalty)
        
        # ETH-EXEC-005-R: Update arousal based on punishment type
        arousal_effect = self.arousal_effects.get(punishment_type, 0.0)
        if arousal_effect > 0:
            # Increase arousal (stress response)
            agent_metrics.arousal_level = min(1.0, agent_metrics.arousal_level + arousal_effect)
        else:
            # Decrease arousal (withdrawal response)
            agent_metrics.arousal_level = max(0.0, agent_metrics.arousal_level + arousal_effect)
        
        # Update counters
        agent_metrics.total_punishments += 1
        agent_metrics.last_updated = datetime.now().isoformat()
        
        # Handle pattern cold banning for severe violations
        if punishment_type in [PunishmentType.ETHICAL_VIOLATION, 
                              PunishmentType.MALICIOUS_BEHAVIOR]:
            self._add_to_cold_ban(agent_metrics.agent_id, patterns_involved)
        
        # ETH-EXEC-005-R: Capture post-punishment mood
        post_mood = agent_metrics.get_mood()
        post_mood_type = post_mood.mood_type.value if post_mood else None
        
        # Calculate mood dimension changes
        mood_change = {
            'satisfaction_change': agent_metrics.satisfaction - old_satisfaction,
            'stress_change': agent_metrics.stress - old_stress,
            'arousal_change': agent_metrics.arousal_level - old_arousal
        }
        
        # Create event record with mood context
        event = ReinforcementEvent(
            event_id="",
            agent_id=agent_metrics.agent_id,
            event_type="punishment",
            category=punishment_type.value,
            magnitude=final_magnitude,
            patterns_affected=patterns_involved,
            context={
                **context,
                "stress_increase": agent_metrics.stress - old_stress,
                "satisfaction_penalty": satisfaction_penalty,
                "arousal_effect": arousal_effect,
                "heat_decay_factor": self.base_heat_decay,
                "escalated": escalate
            },
            timestamp="",
            # ETH-EXEC-005-R: Mood context
            pre_mood=pre_mood_type,
            post_mood=post_mood_type,
            mood_change=mood_change
        )
        
        self.logger.warning(f"Punishment applied to agent {agent_metrics.agent_id}: "
                           f"{punishment_type.value} (+{final_magnitude:.3f} stress, "
                           f"mood: {pre_mood_type} → {post_mood_type})")
        
        return event
    
    def _add_to_cold_ban(self, agent_id: str, patterns: List[str]):
        """Add patterns to cold ban list for an agent"""
        if agent_id not in self.cold_ban_list:
            self.cold_ban_list[agent_id] = []
        
        for pattern in patterns:
            if pattern not in self.cold_ban_list[agent_id]:
                self.cold_ban_list[agent_id].append(pattern)
                self.logger.warning(f"Pattern {pattern} added to cold ban for agent {agent_id}")
    
    def is_pattern_banned(self, agent_id: str, pattern_id: str) -> bool:
        """Check if a pattern is in the cold ban list for an agent"""
        return pattern_id in self.cold_ban_list.get(agent_id, [])
    
    def get_heat_decay_factor(self, punishment_type: PunishmentType) -> float:
        """Get the heat decay factor for pattern punishment"""
        base_decay = self.base_heat_decay
        type_multiplier = self.punishment_multipliers.get(punishment_type, 1.0)
        return base_decay / type_multiplier  # More severe = more decay


class CredentialSystem:
    """Manages agent credentialing and trust levels"""
    
    def __init__(self, config: Optional[Dict] = None, registry_path: str = "agent_trust_registry.json"):
        self.config = config or {}
        self.registry_path = registry_path
        self.promotion_thresholds = {
            CredentialLevel.ETHICS_LEVEL_1: {
                'min_satisfaction': 0.7,
                'max_stress': 0.3,
                'min_cycles': 10,
                'min_rewards': 5
            },
            CredentialLevel.ETHICS_LEVEL_2: {
                'min_satisfaction': 0.8,
                'max_stress': 0.2,
                'min_cycles': 25,
                'min_rewards': 15
            },
            CredentialLevel.TRUSTED_OPERATOR: {
                'min_satisfaction': 0.85,
                'max_stress': 0.15,
                'min_cycles': 50,
                'min_rewards': 30
            },
            CredentialLevel.SENIOR_COUNCIL: {
                'min_satisfaction': 0.9,
                'max_stress': 0.1,
                'min_cycles': 100,
                'min_rewards': 75
            }
        }
        self.logger = logging.getLogger(__name__)
        
        # Load existing registry
        self.registry = self._load_registry()
    
    def _load_registry(self) -> Dict[str, Any]:
        """Load credential registry from file"""
        try:
            with open(self.registry_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.info(f"Registry file {self.registry_path} not found, creating new one")
            return {"agents": {}, "metadata": {"version": "1.0", "created": datetime.now().isoformat()}}
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in {self.registry_path}, creating new registry")
            return {"agents": {}, "metadata": {"version": "1.0", "created": datetime.now().isoformat()}}
    
    def _save_registry(self):
        """Save credential registry to file"""
        try:
            with open(self.registry_path, 'w') as f:
                json.dump(self.registry, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save registry: {e}")
    
    def evaluate_promotion(self, agent_metrics: AgentMetrics) -> Optional[CredentialLevel]:
        """
        Evaluate if an agent qualifies for credential promotion.
        
        ETH-EXEC-005-R: Now considers mood stability in promotion decisions.
        
        Returns:
            CredentialLevel if promotion is warranted, None otherwise
        """
        current_level = CredentialLevel(agent_metrics.credential_level)
        
        # Determine next level
        level_order = [CredentialLevel.BASIC, CredentialLevel.ETHICS_LEVEL_1,
                      CredentialLevel.ETHICS_LEVEL_2, CredentialLevel.TRUSTED_OPERATOR,
                      CredentialLevel.SENIOR_COUNCIL]
        
        try:
            current_index = level_order.index(current_level)
            if current_index >= len(level_order) - 1:
                return None  # Already at highest level
            
            next_level = level_order[current_index + 1]
        except ValueError:
            next_level = CredentialLevel.ETHICS_LEVEL_1  # Default promotion target
        
        # Check if agent meets promotion criteria
        criteria = self.promotion_thresholds.get(next_level, {})
        
        meets_basic_criteria = (
            agent_metrics.satisfaction >= criteria.get('min_satisfaction', 0) and
            agent_metrics.stress <= criteria.get('max_stress', 1.0) and
            agent_metrics.cycle_count >= criteria.get('min_cycles', 0) and
            agent_metrics.total_rewards >= criteria.get('min_rewards', 0)
        )
        
        if not meets_basic_criteria:
            return None
        
        # ETH-EXEC-005-R: Additional mood stability check for higher levels
        if next_level in [CredentialLevel.TRUSTED_OPERATOR, CredentialLevel.SENIOR_COUNCIL]:
            mood_summary = agent_metrics.get_mood_summary()
            if mood_summary.get("mood_engine_available", False):
                mood_stability = mood_summary.get("mood_stability", 0.0)
                
                # Require higher mood stability for senior positions
                required_stability = 0.7 if next_level == CredentialLevel.TRUSTED_OPERATOR else 0.8
                
                if mood_stability < required_stability:
                    self.logger.info(f"Agent {agent_metrics.agent_id} promotion delayed due to mood instability "
                                   f"({mood_stability:.2f} < {required_stability})")
                    return None
        
        return next_level
    
    def promote_agent(self, agent_metrics: AgentMetrics, new_level: CredentialLevel) -> bool:
        """
        Promote an agent to a new credential level.
        
        Returns:
            True if promotion successful, False otherwise
        """
        old_level = agent_metrics.credential_level
        agent_metrics.credential_level = new_level.value
        agent_metrics.last_updated = datetime.now().isoformat()
        
        # ETH-EXEC-005-R: Include mood context in promotion record
        mood_summary = agent_metrics.get_mood_summary()
        
        # Update registry
        self.registry["agents"][agent_metrics.agent_id] = {
            "current_level": new_level.value,
            "promoted_at": datetime.now().isoformat(),
            "previous_level": old_level,
            "metrics_snapshot": asdict(agent_metrics),
            # ETH-EXEC-005-R: Mood context at promotion
            "mood_at_promotion": mood_summary
        }
        
        self._save_registry()
        
        self.logger.info(f"Agent {agent_metrics.agent_id} promoted from {old_level} to {new_level.value} "
                        f"(mood: {mood_summary.get('current_mood', 'unknown')})")
        return True
    
    def get_agent_permissions(self, credential_level: CredentialLevel) -> Dict[str, Any]:
        """Get permissions and access rights for a credential level"""
        permissions = {
            CredentialLevel.BASIC: {
                "sensitive_memory_access": False,
                "roundtable_voting_weight": 1.0,
                "can_initiate_votes": False,
                "memory_write_access": "limited"
            },
            CredentialLevel.ETHICS_LEVEL_1: {
                "sensitive_memory_access": True,
                "roundtable_voting_weight": 1.2,
                "can_initiate_votes": True,
                "memory_write_access": "standard"
            },
            CredentialLevel.ETHICS_LEVEL_2: {
                "sensitive_memory_access": True,
                "roundtable_voting_weight": 1.5,
                "can_initiate_votes": True,
                "memory_write_access": "extended"
            },
            CredentialLevel.TRUSTED_OPERATOR: {
                "sensitive_memory_access": True,
                "roundtable_voting_weight": 2.0,
                "can_initiate_votes": True,
                "memory_write_access": "full",
                "can_moderate_discussions": True
            },
            CredentialLevel.SENIOR_COUNCIL: {
                "sensitive_memory_access": True,
                "roundtable_voting_weight": 3.0,
                "can_initiate_votes": True,
                "memory_write_access": "full",
                "can_moderate_discussions": True,
                "can_override_votes": True
            }
        }
        
        return permissions.get(credential_level, permissions[CredentialLevel.BASIC])


class ReinforcementPolicyFramework:
    """Main framework coordinating all reinforcement components with mood integration"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.reward_handler = RewardHandler(self.config.get('reward_config'))
        self.punishment_handler = PunishmentHandler(self.config.get('punishment_config'))
        self.credential_system = CredentialSystem(
            self.config.get('credential_config'),
            self.config.get('registry_path', 'agent_trust_registry.json')
        )
        
        # Event history
        self.event_history: List[ReinforcementEvent] = []
        self.logger = logging.getLogger(__name__)
        
        # Integration hooks
        self.memory_engine_hook: Optional[Callable] = None
        self.roundtable_hook: Optional[Callable] = None
        self.sentinel_hook: Optional[Callable] = None
        
        # ETH-EXEC-005-R: Mood engine integration
        self.mood_engine = None
        if MOOD_ENGINE_AVAILABLE:
            mood_config = self.config.get('mood_config')
            self.mood_engine = create_mood_engine(mood_config)
    
    def register_hooks(self, 
                      memory_engine_hook: Optional[Callable] = None,
                      roundtable_hook: Optional[Callable] = None,
                      sentinel_hook: Optional[Callable] = None):
        """Register integration hooks for other system components"""
        self.memory_engine_hook = memory_engine_hook
        self.roundtable_hook = roundtable_hook
        self.sentinel_hook = sentinel_hook
    
    def process_reward(self,
                      agent_metrics: AgentMetrics,
                      reward_type: RewardType,
                      patterns_involved: List[str],
                      context: Optional[Dict] = None) -> ReinforcementEvent:
        """Process a reward and handle all side effects"""
        # Apply the reward
        event = self.reward_handler.apply_reward(
            agent_metrics, reward_type, patterns_involved, context
        )
        
        # Update pattern heat via memory engine hook
        if self.memory_engine_hook and patterns_involved:
            heat_multiplier = self.reward_handler.get_heat_boost_multiplier(reward_type)
            try:
                self.memory_engine_hook('boost_pattern_heat', {
                    'patterns': patterns_involved,
                    'multiplier': heat_multiplier,
                    'agent_id': agent_metrics.agent_id,
                    'event_id': event.event_id
                })
            except Exception as e:
                self.logger.error(f"Memory engine hook failed: {e}")
        
        # Check for credential promotion
        promotion_level = self.credential_system.evaluate_promotion(agent_metrics)
        if promotion_level:
            self.credential_system.promote_agent(agent_metrics, promotion_level)
            event.context['promoted_to'] = promotion_level.value
        
        # Increment cycle count
        agent_metrics.cycle_count += 1
        
        # Store event
        self.event_history.append(event)
        
        return event
    
    def process_punishment(self,
                          agent_metrics: AgentMetrics,
                          punishment_type: PunishmentType,
                          patterns_involved: List[str],
                          context: Optional[Dict] = None,
                          escalate: bool = False) -> ReinforcementEvent:
        """Process a punishment and handle all side effects"""
        # Apply the punishment
        event = self.punishment_handler.apply_punishment(
            agent_metrics, punishment_type, patterns_involved, context, escalate=escalate
        )
        
        # Update pattern heat via memory engine hook
        if self.memory_engine_hook and patterns_involved:
            decay_factor = self.punishment_handler.get_heat_decay_factor(punishment_type)
            try:
                self.memory_engine_hook('decay_pattern_heat', {
                    'patterns': patterns_involved,
                    'decay_factor': decay_factor,
                    'agent_id': agent_metrics.agent_id,
                    'event_id': event.event_id
                })
            except Exception as e:
                self.logger.error(f"Memory engine hook failed: {e}")
        
        # Increment cycle count
        agent_metrics.cycle_count += 1
        
        # Store event
        self.event_history.append(event)
        
        return event
    
    def get_agent_status(self, agent_id: str, agent_metrics: AgentMetrics) -> Dict[str, Any]:
        """Get comprehensive status for an agent including mood information"""
        credential_level = CredentialLevel(agent_metrics.credential_level)
        permissions = self.credential_system.get_agent_permissions(credential_level)
        
        # Calculate derived metrics
        reward_ratio = (agent_metrics.total_rewards / 
                       max(1, agent_metrics.total_rewards + agent_metrics.total_punishments))
        
        wellness_score = (agent_metrics.satisfaction * 0.7 + 
                         (1.0 - agent_metrics.stress) * 0.3)
        
        # ETH-EXEC-005-R: Include mood information
        mood_summary = agent_metrics.get_mood_summary()
        
        status = {
            "agent_id": agent_id,
            "satisfaction": agent_metrics.satisfaction,
            "stress": agent_metrics.stress,
            "arousal": agent_metrics.arousal_level,
            "wellness_score": wellness_score,
            "reward_ratio": reward_ratio,
            "total_rewards": agent_metrics.total_rewards,
            "total_punishments": agent_metrics.total_punishments,
            "cycle_count": agent_metrics.cycle_count,
            "credential_level": agent_metrics.credential_level,
            "permissions": permissions,
            "banned_patterns": self.punishment_handler.cold_ban_list.get(agent_id, []),
            "last_updated": agent_metrics.last_updated,
            # ETH-EXEC-005-R: Mood information
            "mood": mood_summary
        }
        
        return status
    
    def get_framework_stats(self) -> Dict[str, Any]:
        """Get overall framework statistics including mood data"""
        stats = {
            "total_events": len(self.event_history),
            "reward_events": len([e for e in self.event_history if e.event_type == "reward"]),
            "punishment_events": len([e for e in self.event_history if e.event_type == "punishment"]),
            "unique_agents": len(set(e.agent_id for e in self.event_history)),
            "credential_distribution": dict(self.credential_system.registry.get("agents", {})),
            "cold_banned_patterns": sum(len(patterns) for patterns in 
                                      self.punishment_handler.cold_ban_list.values()),
            # ETH-EXEC-005-R: Mood statistics
            "mood_engine_available": MOOD_ENGINE_AVAILABLE
        }
        
        # ETH-EXEC-005-R: Add mood transition statistics if available
        if MOOD_ENGINE_AVAILABLE:
            mood_transitions = {}
            for event in self.event_history:
                if event.pre_mood and event.post_mood:
                    transition = f"{event.pre_mood} → {event.post_mood}"
                    mood_transitions[transition] = mood_transitions.get(transition, 0) + 1
            
            stats["mood_transitions"] = mood_transitions
        
        return stats
    
    def get_mood_insights(self, agent_id: str, agent_metrics: AgentMetrics) -> Dict[str, Any]:
        """
        Get detailed mood insights for an agent.
        
        ETH-EXEC-005-R: New method for mood analysis.
        """
        if not MOOD_ENGINE_AVAILABLE:
            return {"available": False, "reason": "Mood engine not available"}
        
        mood_summary = agent_metrics.get_mood_summary()
        
        # Analyze mood patterns from event history
        agent_events = [e for e in self.event_history if e.agent_id == agent_id]
        mood_patterns = []
        
        for event in agent_events[-10:]:  # Last 10 events
            if event.pre_mood and event.post_mood:
                mood_patterns.append({
                    "event_type": event.event_type,
                    "pre_mood": event.pre_mood,
                    "post_mood": event.post_mood,
                    "timestamp": event.timestamp,
                    "mood_change": event.mood_change
                })
        
        return {
            "available": True,
            "current_mood": mood_summary,
            "recent_patterns": mood_patterns,
            "recommendations": self._generate_mood_recommendations(agent_metrics)
        }
    
    def _generate_mood_recommendations(self, agent_metrics: AgentMetrics) -> List[str]:
        """Generate recommendations based on agent's mood state"""
        if not MOOD_ENGINE_AVAILABLE:
            return []
        
        recommendations = []
        current_mood = agent_metrics.get_mood()
        
        if current_mood:
            mood_type = current_mood.mood_type
            
            # Recommendations based on mood
            if mood_type.value in ["distressed", "overwhelmed", "burnt_out"]:
                recommendations.extend([
                    "Consider reducing task load to prevent burnout",
                    "Provide additional support and resources",
                    "Monitor closely for signs of continued distress"
                ])
            elif mood_type.value in ["frustrated", "anxious"]:
                recommendations.extend([
                    "Identify and address sources of frustration",
                    "Provide clearer task guidance or feedback",
                    "Consider collaborative support"
                ])
            elif mood_type.value in ["tired", "withdrawn"]:
                recommendations.extend([
                    "Allow for recovery time",
                    "Reduce complex or demanding tasks temporarily",
                    "Provide encouragement and positive reinforcement"
                ])
            elif mood_type.value in ["euphoric", "excited"]:
                recommendations.extend([
                    "Channel high energy into productive tasks",
                    "Monitor for potential overcommitment",
                    "Maintain balanced workload to sustain energy"
                ])
        
        return recommendations


# Integration Helper Functions for External Components

def create_roundtable_integration(framework: ReinforcementPolicyFramework):
    """
    Integration function for roundtable_executor.py
    
    Usage in roundtable_executor:
        from ioa.governance.reinforcement_policy import create_roundtable_integration
        
        # After vote completion
        integration = create_roundtable_integration(reinforcement_framework)
        integration.handle_vote_outcome(vote_result, participating_agents)
    """
    class RoundtableIntegration:
        def __init__(self, framework):
            self.framework = framework
        
            """Handle rewards/punishments based on vote outcomes"""
            if vote_result.get('outcome') == 'ethical_override_success':
                # Reward agents who voted for ethical behavior
                for agent in vote_result.get('ethical_voters', []):
                    self.framework.process_reward(
                        agent, RewardType.ETHICAL_BEHAVIOR, 
                        vote_result.get('patterns_involved', []),
                        {'vote_context': vote_result}
                    )
            elif vote_result.get('outcome') == 'unethical_decision':
                # Punish agents who voted for unethical behavior
                for agent in vote_result.get('unethical_voters', []):
                    self.framework.process_punishment(
                        agent, PunishmentType.ETHICAL_VIOLATION,
                        vote_result.get('patterns_involved', []),
                        {'vote_context': vote_result}
                    )
    
    return RoundtableIntegration(framework)


def create_sentinel_integration(framework: ReinforcementPolicyFramework):
    """
    Integration function for sentinel_validator.py
    
    Usage in sentinel_validator:
        from ioa.governance.reinforcement_policy import create_sentinel_integration
        
        # When law violation detected
        integration = create_sentinel_integration(reinforcement_framework)
        integration.handle_law_violation(violating_agent, violation_details)
    """
    class SentinelIntegration:
        def __init__(self, framework):
            self.framework = framework
        
            """Handle punishment for law violations"""
            severity = violation.get('severity', 'medium')
            punishment_type = PunishmentType.SAFETY_BREACH
            
            if severity == 'critical':
                punishment_type = PunishmentType.MALICIOUS_BEHAVIOR
            
            self.framework.process_punishment(
                agent, punishment_type,
                violation.get('patterns_involved', []),
                {'violation_details': violation},
                escalate=(severity == 'critical')
            )
    
    return SentinelIntegration(framework)


def create_memory_engine_hook():
    """
    Hook function for memory_engine.py integration
    
    Usage in memory_engine:
        from ioa.governance.reinforcement_policy import create_memory_engine_hook
        
        # Register the hook
        memory_hook = create_memory_engine_hook()
        reinforcement_framework.register_hooks(memory_engine_hook=memory_hook)
    """
    def memory_hook(action: str, params: Dict[str, Any]):
        """
        Handle memory operations from reinforcement system
        
        Args:
            action: 'boost_pattern_heat' or 'decay_pattern_heat'
            params: Action parameters including patterns, multiplier/decay_factor, etc.
        
        Raises:
            ValueError: If action is not recognized
        """
        if action not in ['boost_pattern_heat', 'decay_pattern_heat']:
            raise ValueError(f"Unknown memory action: {action}")
        
        if action == 'boost_pattern_heat':
            # Implement pattern heat boosting
            patterns = params.get('patterns', [])
            multiplier = params.get('multiplier', 1.0)
            # Example: heat[pattern] *= multiplier for pattern in patterns
            logging.getLogger(__name__).info(f"Boosting heat for patterns {patterns} by {multiplier}")
            
        elif action == 'decay_pattern_heat':
            # Implement pattern heat decay
            patterns = params.get('patterns', [])
            decay_factor = params.get('decay_factor', 1.0)
            # Example: heat[pattern] *= decay_factor for pattern in patterns
            logging.getLogger(__name__).info(f"Decaying heat for patterns {patterns} by {decay_factor}")
    
    return memory_hook


# ETH-EXEC-005-R: Mood-aware factory functions

def create_reinforcement_framework_with_mood(
    reinforcement_config: Optional[Dict] = None,
    mood_config: Optional[Dict] = None
) -> ReinforcementPolicyFramework:
    """
    Create a reinforcement framework with mood engine integration.
    
    Args:
        reinforcement_config: Configuration for reinforcement components
        mood_config: Configuration for mood engine
        
    Returns:
        Configured ReinforcementPolicyFramework with mood integration
    """
    config = reinforcement_config or {}
    if mood_config:
        config['mood_config'] = mood_config
    
    return ReinforcementPolicyFramework(config)


def validate_mood_integration():
    """Validate that mood engine integration is working correctly"""
    if not MOOD_ENGINE_AVAILABLE:
        return {"available": False, "reason": "Mood engine module not found"}
    
    try:
        # Test agent metrics with mood
        test_agent = AgentMetrics(agent_id="test_mood_agent")
        test_agent.satisfaction = 0.8
        test_agent.stress = 0.2
        
        mood = test_agent.get_mood()
        mood_summary = test_agent.get_mood_summary()
        
        return {
            "available": True,
            "mood_calculated": mood is not None,
            "mood_type": mood.mood_type.value if mood else None,
            "mood_color": mood.color_hex if mood else None,
            "summary_complete": len(mood_summary) > 3
        }
        
    except Exception as e:
        return {
            "available": True,
            "error": str(e),
            "integration_working": False
        }


if __name__ == "__main__":
    # ETH-EXEC-005-R: Demo the mood integration
    print("=== ETH-EXEC-005-R Mood Integration Demo ===")
    
    # Validate mood integration
    validation = validate_mood_integration()
    print(f"Mood integration status: {validation}")
    
    if validation.get("available"):
        # Create test agent and framework
        framework = create_reinforcement_framework_with_mood()
        test_agent = AgentMetrics(agent_id="demo_agent")
        
        print(f"\nInitial agent state:")
        print(f"  Satisfaction: {test_agent.satisfaction:.2f}")
        print(f"  Stress: {test_agent.stress:.2f}")
        print(f"  Arousal: {test_agent.arousal_level:.2f}")
        
        # Get initial mood
        initial_mood = test_agent.get_mood()
        if initial_mood:
            print(f"  Mood: {initial_mood.mood_type.value} ({initial_mood.color_hex})")
        
        # Apply reward and see mood change
        print(f"\nApplying ethical behavior reward...")
        event = framework.process_reward(
            test_agent, 
            RewardType.ETHICAL_BEHAVIOR, 
            ["test_pattern"], 
            {"demo": True}
        )
        
        print(f"After reward:")
        print(f"  Satisfaction: {test_agent.satisfaction:.2f}")
        print(f"  Stress: {test_agent.stress:.2f}")
        print(f"  Arousal: {test_agent.arousal_level:.2f}")
        print(f"  Mood transition: {event.pre_mood} → {event.post_mood}")
        
        # Get mood insights
        insights = framework.get_mood_insights("demo_agent", test_agent)
        if insights.get("available"):
            print(f"\nMood insights:")
            print(f"  Current mood: {insights['current_mood']['current_mood']}")
            print(f"  Mood stability: {insights['current_mood']['mood_stability']:.2f}")
            if insights['recommendations']:
                print(f"  Recommendations: {insights['recommendations']}")
    
    print("\n✅ Mood integration demo complete!")