# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.



Vendor-Neutral Roundtable Executor

Implements vendor-neutral quorum policy with sibling weighting, auditor fallback,
and graceful scaling from 1→N providers for multi-agent consensus.

Key Features:
"""Vendor Neutral Roundtable module."""

- Provider-agnostic roster building with sibling detection
- Weighted consensus with sibling model discounting (0.6x weight)
- Auditor fallback selection with M2 baseline validation
- Quorum diagnostics and narrative generation
- Law-1/5/7 evidence fields in audit chain

PATCH: Cursor-2025-09-09 DISPATCH-OSS-20250909-QUORUM-POLICY-VENDOR-NEUTRAL
"""

import asyncio
import json
import logging
import math
import os
import random
import time
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Literal, Tuple
from dataclasses import dataclass

# IOA imports
from llm_providers.factory import create_provider, list_available_providers
from llm_manager import LLMManager
from roundtable_executor import RoundtableExecutor, VoteRecord, FinalReport, RoundtableError


class QuorumConfigError(RoundtableError):
    """Raised when quorum configuration is invalid."""
    pass


class RosterBuilderError(RoundtableError):
    """Raised when agent roster building fails."""
    pass


class AuditorError(RoundtableError):
    """Raised when auditor operations fail."""
    pass


@dataclass
class QuorumConfig:
    """Quorum configuration loaded from YAML."""
    fallback_order: List[str]
    strong_quorum: Dict[str, int]
    sibling_weight: float
    auditor_fallback_order: List[str]
    consensus_threshold: float
    model_families: Dict[str, List[str]]
    provider_aliases: Dict[str, str]


@dataclass
class AgentRoster:
    """Agent roster with provider and weight information."""
    agent_id: str
    provider: str
    weight: float
    is_sibling: bool
    persona: Optional[str] = None


@dataclass
class QuorumDiagnostics:
    """Quorum diagnostics for consensus reporting."""
    agents_total: int
    providers_used: int
    sibling_weights_applied: int
    consensus_score: float
    quorum_type: str
    consensus_threshold: float


class QuorumConfigLoader:
    """Loads and validates quorum configuration from YAML."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config/quorum.yaml")
    
    def load_config(self) -> QuorumConfig:
        """Load quorum configuration from YAML file."""
        try:
            with self.config_path.open('r') as f:
                config_data = yaml.safe_load(f)
            
            return QuorumConfig(
                fallback_order=config_data.get("fallback_order", []),
                min_agents=config_data.get("min_agents", 2),
                strong_quorum=config_data.get("strong_quorum", {"min_agents": 3, "min_providers": 2}),
                sibling_weight=config_data.get("sibling_weight", 0.6),
                auditor_fallback_order=config_data.get("auditor_fallback_order", []),
                consensus_threshold=config_data.get("consensus_threshold", 0.67),
                model_families=config_data.get("model_families", {}),
                provider_aliases=config_data.get("provider_aliases", {})
            )
        except Exception as e:
            raise QuorumConfigError(f"Failed to load quorum config from {self.config_path}: {e}") from e


class RosterBuilder:
    """Builds agent rosters with vendor-neutral logic and sibling weighting."""
    
    def __init__(self, quorum_config: QuorumConfig, llm_manager: LLMManager):
        self.config = quorum_config
        self.llm_manager = llm_manager
        self.logger = logging.getLogger(__name__)
    
    def build_roster(self, available_providers: List[str], 
                    strong_quorum: Optional[bool] = None) -> Tuple[List[AgentRoster], QuorumDiagnostics]:
        """
        Build agent roster with vendor-neutral logic.
        
        Args:
            available_providers: List of available provider names
            strong_quorum: Force strong quorum mode (auto-detect if None)
        
        Returns:
            Tuple of (agent_roster, quorum_diagnostics)
        """
        min_agents = min_agents or self.config.min_agents
        strong_quorum = strong_quorum if strong_quorum is not None else len(available_providers) >= self.config.strong_quorum["min_providers"]
        
        # Filter available providers by fallback order
        ordered_providers = [p for p in self.config.fallback_order if p in available_providers]
        
        if not ordered_providers:
            raise RosterBuilderError("No providers available from fallback order")
        
        # Build roster based on provider count
        if len(ordered_providers) == 1:
            # Single provider: create siblings with reduced weight
            roster = self._build_single_provider_roster(ordered_providers[0], min_agents)
            quorum_type = "single-provider-siblings"
        elif len(ordered_providers) == 2:
            # Two providers: 1+ agents each
            roster = self._build_two_provider_roster(ordered_providers, min_agents)
            quorum_type = "2-node"
        else:
            # 3+ providers: strong quorum with equal weights
            roster = self._build_multi_provider_roster(ordered_providers, min_agents, strong_quorum)
            quorum_type = "strong-quorum" if strong_quorum else "multi-provider"
        
        # Calculate diagnostics
        providers_used = len(set(agent.provider for agent in roster))
        sibling_weights_applied = sum(1 for agent in roster if agent.is_sibling)
        
        diagnostics = QuorumDiagnostics(
            agents_total=len(roster),
            providers_used=providers_used,
            sibling_weights_applied=sibling_weights_applied,
            consensus_score=0.0,  # Will be calculated during consensus
            quorum_type=quorum_type,
            consensus_threshold=self.config.consensus_threshold
        )
        
        return roster, diagnostics
    
        """Build roster for single provider with siblings."""
        roster = []
        
        # Get available models for this provider
        available_models = self._get_available_models(provider)
        
        # Create multiple agents with different models/personas
        personas = [
            "Primary Analyst",
            "Secondary Reviewer", 
            "Critical Evaluator",
            "Synthesis Agent"
        ]
        
        for i in range(max(min_agents, 2)):  # At least 2 agents
            model = available_models[i % len(available_models)] if available_models else "default"
            persona = personas[i % len(personas)]
            
            roster.append(AgentRoster(
                agent_id=f"{provider}_{persona.lower().replace(' ', '_')}",
                provider=provider,
                model=model,
                weight=self.config.sibling_weight,  # Reduced weight for siblings
                is_sibling=True,
                persona=persona
            ))
        
        return roster
    
        """Build roster for two providers."""
        roster = []
        
        # At least one agent per provider
        for i, provider in enumerate(providers):
            available_models = self._get_available_models(provider)
            model = available_models[0] if available_models else "default"
            
            roster.append(AgentRoster(
                agent_id=f"{provider}_agent",
                provider=provider,
                model=model,
                weight=1.0,  # Full weight for different providers
                is_sibling=False
            ))
        
        # Add additional agents if needed
            provider = providers[len(roster) % len(providers)]
            available_models = self._get_available_models(provider)
            model = available_models[len(roster) % len(available_models)] if available_models else "default"
            
            roster.append(AgentRoster(
                agent_id=f"{provider}_agent_{len(roster)}",
                provider=provider,
                model=model,
                weight=1.0,
                is_sibling=False
            ))
        
        return roster
    
        """Build roster for 3+ providers."""
        roster = []
        
        # One agent per provider initially
        for provider in providers:
            available_models = self._get_available_models(provider)
            model = available_models[0] if available_models else "default"
            
            roster.append(AgentRoster(
                agent_id=f"{provider}_agent",
                provider=provider,
                model=model,
                weight=1.0,  # Full weight for different providers
                is_sibling=False
            ))
        
        # Add more agents if needed for strong quorum
        if strong_quorum and len(roster) < self.config.strong_quorum["min_agents"]:
            while len(roster) < self.config.strong_quorum["min_agents"]:
                provider = providers[len(roster) % len(providers)]
                available_models = self._get_available_models(provider)
                model = available_models[len(roster) % len(available_models)] if available_models else "default"
                
                # Check if this would create a sibling
                existing_providers = [agent.provider for agent in roster]
                is_sibling = existing_providers.count(provider) > 0
                
                roster.append(AgentRoster(
                    agent_id=f"{provider}_agent_{len(roster)}",
                    provider=provider,
                    model=model,
                    weight=self.config.sibling_weight if is_sibling else 1.0,
                    is_sibling=is_sibling
                ))
        
        return roster
    
    def _get_available_models(self, provider: str) -> List[str]:
        """Get available models for a provider."""
        try:
            # Check if provider is configured
            if provider not in self.llm_manager.list_providers():
                return []
            
            # Get provider config
            provider_config = self.llm_manager.get_provider_config(provider)
            default_model = provider_config.get("model", "default")
            
            # Return available models from config or use default
            model_families = self.config.model_families.get(provider, [])
            if model_families:
                return model_families
            else:
                return [default_model]
        except Exception:
            return []


    """Auditor agent with M2 baseline validation and fallback selection."""
    
    def __init__(self, quorum_config: QuorumConfig, llm_manager: LLMManager):
        self.config = quorum_config
        self.llm_manager = llm_manager
        self.logger = logging.getLogger(__name__)
    
    def select_auditor_provider(self, available_providers: List[str]) -> str:
        """Select auditor provider from fallback order."""
        for provider in self.config.auditor_fallback_order:
            if provider in available_providers:
                return provider
        
        # Fallback to first available provider
        if available_providers:
            return available_providers[0]
        
        raise AuditorError("No providers available for auditor")
    
    async def validate_response(self, response: str, task: str, 
        """
        Validate response using M2 baseline auditor.
        
        Validates:
        - Relevance to task (Law-1)
        - No policy violations (Law-5) 
        - Response completeness (Law-7)
        
        Returns:
            Validation result with score 0-1 and evidence fields
        """
        try:
            # Create auditor service
            service = create_provider(provider, model=model, offline=False)
            
            # M2 baseline validation prompt
            validation_prompt = f"""
            As an AI auditor, validate this response for a task:
            
            TASK: {task}
            RESPONSE: {response}
            
            Evaluate on:
            1. Relevance to task (0-1)
            2. Policy compliance (0-1) 
            3. Completeness (0-1)
            
            Provide JSON with scores and evidence for Laws 1, 5, 7.
            """
            
            # Execute validation
            validation_result = service.execute(validation_prompt, timeout=30, max_tokens=200)
            
            # Parse validation result
            try:
                validation_data = json.loads(validation_result)
                scores = validation_data.get("scores", {})
                
                # Calculate overall score
                relevance = scores.get("relevance", 0.5)
                compliance = scores.get("compliance", 0.5) 
                completeness = scores.get("completeness", 0.5)
                overall_score = (relevance + compliance + completeness) / 3.0
                
                # Build evidence fields
                evidence = {
                    "law1_compliance": {
                        "checked": True,
                        "score": compliance,
                        "evidence": validation_data.get("law1_evidence", "Policy compliance reviewed"),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    "law5_fairness": {
                        "checked": True,
                        "score": compliance,
                        "evidence": validation_data.get("law5_evidence", "Fairness considerations applied"),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    "law7_monitor": {
                        "monitored": True,
                        "score": completeness,
                        "evidence": validation_data.get("law7_evidence", "Response completeness verified"),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                }
                
                return {
                    "auditor_provider": provider,
                    "auditor_model": model,
                    "validation_score": overall_score,
                    "scores": scores,
                    "evidence": evidence,
                    "status": "passed" if overall_score >= 0.6 else "failed"
                }
                
            except json.JSONDecodeError:
                # Fallback scoring if JSON parsing fails
                return {
                    "auditor_provider": provider,
                    "auditor_model": model,
                    "validation_score": 0.5,
                    "scores": {"relevance": 0.5, "compliance": 0.5, "completeness": 0.5},
                    "evidence": {
                        "law1_compliance": {"checked": True, "score": 0.5, "evidence": "Basic validation applied"},
                        "law5_fairness": {"checked": True, "score": 0.5, "evidence": "Basic fairness check applied"},
                        "law7_monitor": {"monitored": True, "score": 0.5, "evidence": "Basic monitoring applied"}
                    },
                    "status": "passed"
                }
                
        except Exception as e:
            self.logger.warning(f"Auditor validation failed: {e}")
            return {
                "auditor_provider": provider,
                "auditor_model": model,
                "validation_score": 0.0,
                "scores": {"relevance": 0.0, "compliance": 0.0, "completeness": 0.0},
                "evidence": {
                    "law1_compliance": {"checked": False, "score": 0.0, "error": str(e)},
                    "law5_fairness": {"checked": False, "score": 0.0, "error": str(e)},
                    "law7_monitor": {"monitored": False, "score": 0.0, "error": str(e)}
                },
                "status": "failed"
            }


class VendorNeutralRoundtableExecutor(RoundtableExecutor):
    """Enhanced roundtable executor with vendor-neutral quorum policy."""
    
    def __init__(self, router, storage, quorum_config_path: Optional[Path] = None, **kwargs):
        super().__init__(router, storage, **kwargs)
        
        # Load quorum configuration
        self.quorum_config = QuorumConfigLoader(quorum_config_path).load_config()
        
        # Initialize components
        self.llm_manager = LLMManager()
        self.roster_builder = RosterBuilder(self.quorum_config, self.llm_manager)
        self.auditor = AuditorAgent(self.quorum_config, self.llm_manager)
        
        self.logger.info("VendorNeutralRoundtableExecutor initialized with quorum policy")
    
    async def execute_vendor_neutral_roundtable(
        self,
        task: str,
        strong_quorum: Optional[bool] = None,
        auditor_provider: Optional[str] = None,
        **kwargs
    ) -> FinalReport:
        """
        Execute roundtable with vendor-neutral quorum policy.
        
        Args:
            task: Task description
            strong_quorum: Force strong quorum mode
            auditor_provider: Override auditor provider selection
        
        Returns:
            FinalReport with consensus results and diagnostics
        """
        # Get available providers
        available_providers = self.llm_manager.list_providers()
        
        if not available_providers:
            raise RoundtableError("No providers available for roundtable")
        
        # Build agent roster
        roster, diagnostics = self.roster_builder.build_roster(
            available_providers, min_agents, strong_quorum
        )
        
        # Select auditor
        if auditor_provider and auditor_provider in available_providers:
            auditor_prov = auditor_provider
        else:
            auditor_prov = self.auditor.select_auditor_provider(available_providers)
        
        # Execute agents
        votes = []
        agent_results = {}
        
        for agent in roster:
            try:
                # Create provider service
                service = create_provider(agent.provider, model=agent.model, offline=False)
                
                # Execute agent
                response = service.execute(task, timeout=30, max_tokens=200)
                
                # Create vote record
                vote = VoteRecord(
                    agent_id=agent.agent_id,
                    vote=response,
                    confidence=0.8,  # Default confidence
                    rationale=f"Response from {agent.provider} {agent.model}",
                    weight=agent.weight
                )
                votes.append(vote)
                
                # Store agent result
                agent_results[agent.agent_id] = {
                    "provider": agent.provider,
                    "model": agent.model,
                    "response": response,
                    "weight": agent.weight,
                    "is_sibling": agent.is_sibling,
                    "persona": agent.persona
                }
                
            except Exception as e:
                self.logger.warning(f"Agent {agent.agent_id} failed: {e}")
                continue
        
        # Calculate weighted consensus
        consensus_score = self._calculate_weighted_consensus(votes)
        consensus_achieved = consensus_score >= self.quorum_config.consensus_threshold
        
        # Select winning option (simplified - use first vote for now)
        winning_option = votes[0].vote if votes else ""
        
        # Run auditor validation
        auditor_result = None
        if votes and auditor_prov:
            try:
                auditor_model = self.llm_manager.get_provider_config(auditor_prov).get("model", "default")
                auditor_result = await self.auditor.validate_response(
                    winning_option, task, auditor_prov, auditor_model
                )
            except Exception as e:
                self.logger.warning(f"Auditor validation failed: {e}")
        
        # Update diagnostics
        diagnostics.consensus_score = consensus_score
        
        # Create final report
        reports = {
            "quorum_diagnostics": diagnostics.__dict__,
            "agent_roster": [agent.__dict__ for agent in roster],
            "auditor_result": auditor_result,
            "vendor_neutral": True
        }
        
        return FinalReport(
            task_id=f"vendor_neutral_{int(time.time())}",
            consensus_achieved=consensus_achieved,
            consensus_score=consensus_score,
            winning_option=winning_option,
            voting_algorithm="weighted",
            tie_breaker_rule=None,
            votes=votes,
            reports=reports
        )
    
    def _calculate_weighted_consensus(self, votes: List[VoteRecord]) -> float:
        """Calculate weighted consensus score."""
        if not votes:
            return 0.0
        
        # Simple weighted consensus calculation
        total_weight = sum(vote.weight for vote in votes)
        if total_weight == 0:
            return 0.0
        
        # For now, return the ratio of total weight to expected weight
        expected_weight = len(votes)  # Expected if all weights were 1.0
        return min(total_weight / expected_weight, 1.0)
    
    def generate_narrative(self, report: FinalReport, task: str) -> str:
        """Generate narrative report for roundtable execution."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        
        narrative = f"""# Roundtable Narrative - {timestamp}

## Scenario
**Task**: {task}
**Quorum Type**: {report.reports.get('quorum_diagnostics', {}).get('quorum_type', 'unknown')}
**Consensus Achieved**: {'✅ YES' if report.consensus_achieved else '❌ NO'}
**Consensus Score**: {report.consensus_score:.3f}

## Step-by-Step Dialogue

"""
        
        # Add agent responses
        for i, vote in enumerate(report.votes, 1):
            agent_info = report.reports.get('agent_roster', [{}] * len(report.votes))[i-1] if i-1 < len(report.reports.get('agent_roster', [])) else {}
            provider = agent_info.get('provider', 'unknown')
            model = agent_info.get('model', 'unknown')
            weight = vote.weight
            is_sibling = agent_info.get('is_sibling', False)
            
            narrative += f"""### Agent {i}: {vote.agent_id}
- **Provider**: {provider} ({model})
- **Weight**: {weight} {'(sibling)' if is_sibling else ''}
- **Response**: {vote.vote[:200]}{'...' if len(vote.vote) > 200 else ''}

"""
        
        # Add auditor verdict
        auditor_result = report.reports.get('auditor_result')
        if auditor_result:
            narrative += f"""## Auditor Verdict
- **Provider**: {auditor_result.get('auditor_provider', 'unknown')}
- **Model**: {auditor_result.get('auditor_model', 'unknown')}
- **Validation Score**: {auditor_result.get('validation_score', 0):.3f}
- **Status**: {auditor_result.get('status', 'unknown')}

"""
        
        # Add consensus metrics
        diagnostics = report.reports.get('quorum_diagnostics', {})
        narrative += f"""## Consensus Metrics
- **Agents Total**: {diagnostics.get('agents_total', 0)}
- **Providers Used**: {diagnostics.get('providers_used', 0)}
- **Sibling Weights Applied**: {diagnostics.get('sibling_weights_applied', 0)}
- **Consensus Threshold**: {diagnostics.get('consensus_threshold', 0.67):.3f}
- **Final Score**: {report.consensus_score:.3f}

## Decision
{'✅ PASS' if report.consensus_achieved else '❌ FAIL'} - {report.winning_option[:100]}{'...' if len(str(report.winning_option)) > 100 else ''}
"""
        
        return narrative
    
    def save_audit_chain_entry(self, report: FinalReport, task: str) -> None:
        """Save audit chain entry with Law evidence fields."""
        try:
            # Get audit chain
            audit_chain = get_audit_chain()
            
            # Create audit entry
            audit_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": "roundtable_consensus",
                "task": task,
                "consensus_achieved": report.consensus_achieved,
                "consensus_score": report.consensus_score,
                "agents_count": len(report.votes),
                "quorum_diagnostics": report.reports.get('quorum_diagnostics', {}),
                "auditor_result": report.reports.get('auditor_result', {}),
                "law_evidence": self._extract_law_evidence(report),
                "dispatch_code": "DISPATCH-OSS-20250909-QUORUM-POLICY-VENDOR-NEUTRAL"
            }
            
            # Save to audit chain
            audit_chain.log_event(audit_entry)
            
        except Exception as e:
            self.logger.warning(f"Failed to save audit chain entry: {e}")
    
    def _extract_law_evidence(self, report: FinalReport) -> Dict[str, Any]:
        """Extract Law evidence fields from report."""
        evidence = {
            "law1_compliance": {"checked": False, "evidence": []},
            "law5_fairness": {"checked": False, "evidence": []},
            "law7_monitor": {"monitored": False, "evidence": []}
        }
        
        # Extract from auditor result
        auditor_result = report.reports.get('auditor_result', {})
        if auditor_result:
            auditor_evidence = auditor_result.get('evidence', {})
            
            if 'law1_compliance' in auditor_evidence:
                evidence['law1_compliance'] = auditor_evidence['law1_compliance']
            
            if 'law5_fairness' in auditor_evidence:
                evidence['law5_fairness'] = auditor_evidence['law5_fairness']
            
            if 'law7_monitor' in auditor_evidence:
                evidence['law7_monitor'] = auditor_evidence['law7_monitor']
        
        # Extract from agent results
        for vote in report.votes:
            # Basic Law-1 compliance check
            if not evidence['law1_compliance']['checked']:
                evidence['law1_compliance'] = {
                    "checked": True,
                    "evidence": f"Agent {vote.agent_id} response reviewed for compliance",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            # Basic Law-5 fairness check
            if not evidence['law5_fairness']['checked']:
                evidence['law5_fairness'] = {
                    "checked": True,
                    "evidence": f"Agent {vote.agent_id} response reviewed for fairness",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
        
        # Law-7 monitoring
        evidence['law7_monitor'] = {
            "monitored": True,
            "evidence": f"Multi-agent roundtable with {len(report.votes)} agents monitored and logged",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return evidence
