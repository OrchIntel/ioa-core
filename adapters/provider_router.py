"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
PATCH: Cursor-2025-09-05 DISPATCH-GOV-20250905-LAW-7-SUSTAINABILITY
- Added energy-aware routing with quality/energy/latency scoring
- Added sustainability policy integration
- Added energy-efficient model selection
"""

from __future__ import annotations

import logging
import os
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Routing strategies for provider selection."""
    QUALITY_FIRST = "quality_first"
    ENERGY_FIRST = "energy_first"
    BALANCED = "balanced"
    SUSTAINABILITY_STRICT = "sustainability_strict"


@dataclass
class ProviderInfo:
    """Information about a provider for routing decisions."""
    provider_id: str
    model_name: str
    capabilities: List[str]
    quality_score: float
    energy_efficiency: float  # Lower is better
    latency_score: float  # Lower is better
    cost_per_token: float
    region: str
    sustainability_rating: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingDecision:
    """Decision from the energy-aware router."""
    selected_provider: str
    routing_strategy: RoutingStrategy
    quality_score: float
    energy_score: float
    latency_score: float
    overall_score: float
    alternatives: List[ProviderInfo]
    sustainability_impact: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EnergyAwareRouter:
    """Energy-aware provider router for Law 7 compliance."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Load sustainability configuration
        self.energy_weight = self.config.get("energy_weight", 0.3)
        self.quality_weight = self.config.get("quality_weight", 0.6)
        self.latency_weight = self.config.get("latency_weight", 0.1)
        
        # Sustainability thresholds
        self.energy_strict = self.config.get("energy_strict", False)
        self.quality_threshold = self.config.get("quality_threshold", 0.8)
        self.energy_preference_threshold = self.config.get("energy_preference_threshold", 0.1)
        
        # Provider registry
        self.providers: Dict[str, ProviderInfo] = {}
        
        # Initialize default providers
        self._initialize_default_providers()
        
        logger.info("Energy-Aware Router initialized for Law 7 compliance")
    
    def _initialize_default_providers(self):
        """Initialize default provider information."""
        default_providers = [
            ProviderInfo(
                provider_id="openai",
                model_name="gpt-4",
                capabilities=["text_generation", "reasoning", "coding"],
                quality_score=0.95,
                energy_efficiency=0.8,  # Higher efficiency
                latency_score=0.3,
                cost_per_token=0.03,
                region="global",
                sustainability_rating="good"
            ),
            ProviderInfo(
                provider_id="openai",
                model_name="gpt-3.5-turbo",
                capabilities=["text_generation", "reasoning"],
                quality_score=0.85,
                energy_efficiency=0.9,  # Very efficient
                latency_score=0.2,
                cost_per_token=0.002,
                region="global",
                sustainability_rating="excellent"
            ),
            ProviderInfo(
                provider_id="anthropic",
                model_name="claude-3-opus",
                capabilities=["text_generation", "reasoning", "coding"],
                quality_score=0.93,
                energy_efficiency=0.75,
                latency_score=0.4,
                cost_per_token=0.015,
                region="global",
                sustainability_rating="good"
            ),
            ProviderInfo(
                provider_id="anthropic",
                model_name="claude-3-sonnet",
                capabilities=["text_generation", "reasoning"],
                quality_score=0.88,
                energy_efficiency=0.85,
                latency_score=0.3,
                cost_per_token=0.003,
                region="global",
                sustainability_rating="excellent"
            ),
            ProviderInfo(
                provider_id="local",
                model_name="llama-3-8b",
                capabilities=["text_generation", "reasoning"],
                quality_score=0.75,
                energy_efficiency=0.95,  # Most efficient
                latency_score=0.8,
                cost_per_token=0.0,
                region="local",
                sustainability_rating="excellent"
            )
        ]
        
        for provider in default_providers:
            self.register_provider(provider)
    
    def register_provider(self, provider: ProviderInfo):
        """Register a provider with the router."""
        key = f"{provider.provider_id}:{provider.model_name}"
        self.providers[key] = provider
        logger.debug(f"Registered provider: {key}")
    
    def route_request(self, request: Dict[str, Any], 
                     strategy: RoutingStrategy = RoutingStrategy.BALANCED) -> RoutingDecision:
        """
        Route a request using energy-aware selection.
        
        Args:
            request: Request details including task type, quality requirements, etc.
            strategy: Routing strategy to use
            
        Returns:
            RoutingDecision with selected provider and sustainability impact
        """
        task_type = request.get("task_type", "text_generation")
        quality_requirement = request.get("quality_requirement", 0.8)
        energy_constraint = request.get("energy_constraint", None)
        region_preference = request.get("region_preference", "auto")
        
        # Filter providers by capabilities and requirements
        candidates = self._filter_candidates(task_type, quality_requirement, region_preference)
        
        if not candidates:
            raise ValueError(f"No suitable providers found for task type: {task_type}")
        
        # Score candidates based on strategy
        scored_candidates = self._score_candidates(candidates, strategy, request)
        
        # Select best provider
        best_candidate, best_score = scored_candidates[0]
        
        # Calculate sustainability impact
        sustainability_impact = self._calculate_sustainability_impact(best_candidate, request)
        
        # Create routing decision
        decision = RoutingDecision(
            selected_provider=best_candidate.provider_id,
            selected_model=best_candidate.model_name,
            routing_strategy=strategy,
            quality_score=best_candidate.quality_score,
            energy_score=best_candidate.energy_efficiency,
            latency_score=best_candidate.latency_score,
            overall_score=best_score,
            alternatives=candidates[:3],  # Top 3 alternatives
            sustainability_impact=sustainability_impact
        )
        
        logger.info(f"Routed request to {best_candidate.provider_id}:{best_candidate.model_name} "
                   f"using {strategy.value} strategy")
        
        return decision
    
    def _filter_candidates(self, task_type: str, quality_requirement: float, 
                          region_preference: str) -> List[ProviderInfo]:
        """Filter providers based on task requirements."""
        candidates = []
        
        for provider in self.providers.values():
            # Check capabilities
            if task_type not in provider.capabilities:
                continue
            
            # Check quality requirement
            if provider.quality_score < quality_requirement:
                continue
            
            # Check region preference
            if region_preference != "auto" and provider.region != region_preference:
                continue
            
            candidates.append(provider)
        
        return candidates
    
    def _score_candidates(self, candidates: List[ProviderInfo], strategy: RoutingStrategy,
                         request: Dict[str, Any]) -> List[Tuple[ProviderInfo, float]]:
        """Score candidates based on routing strategy."""
        scored = []
        
        for provider in candidates:
            if strategy == RoutingStrategy.QUALITY_FIRST:
                score = self._score_quality_first(provider, request)
            elif strategy == RoutingStrategy.ENERGY_FIRST:
                score = self._score_energy_first(provider, request)
            elif strategy == RoutingStrategy.SUSTAINABILITY_STRICT:
                score = self._score_sustainability_strict(provider, request)
            else:  # BALANCED
                score = self._score_balanced(provider, request)
            
            scored.append((provider, score))
        
        # Sort by score (higher is better)
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
    
    def _score_quality_first(self, provider: ProviderInfo, request: Dict[str, Any]) -> float:
        """Score for quality-first strategy."""
        quality_score = provider.quality_score * 0.7
        energy_score = provider.energy_efficiency * 0.2
        latency_score = (1.0 - provider.latency_score) * 0.1
        
        return quality_score + energy_score + latency_score
    
    def _score_energy_first(self, provider: ProviderInfo, request: Dict[str, Any]) -> float:
        """Score for energy-first strategy."""
        quality_score = provider.quality_score * 0.3
        energy_score = provider.energy_efficiency * 0.6
        latency_score = (1.0 - provider.latency_score) * 0.1
        
        return quality_score + energy_score + latency_score
    
    def _score_sustainability_strict(self, provider: ProviderInfo, request: Dict[str, Any]) -> float:
        """Score for sustainability-strict strategy."""
        # Prioritize energy efficiency and sustainability rating
        quality_score = provider.quality_score * 0.2
        energy_score = provider.energy_efficiency * 0.7
        latency_score = (1.0 - provider.latency_score) * 0.1
        
        # Bonus for excellent sustainability rating
        sustainability_bonus = 0.1 if provider.sustainability_rating == "excellent" else 0.0
        
        return quality_score + energy_score + latency_score + sustainability_bonus
    
    def _score_balanced(self, provider: ProviderInfo, request: Dict[str, Any]) -> float:
        """Score for balanced strategy using configured weights."""
        quality_score = provider.quality_score * self.quality_weight
        energy_score = provider.energy_efficiency * self.energy_weight
        latency_score = (1.0 - provider.latency_score) * self.latency_weight
        
        return quality_score + energy_score + latency_score
    
    def _calculate_sustainability_impact(self, provider: ProviderInfo, 
                                      request: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate sustainability impact of the routing decision."""
        estimated_tokens = request.get("estimated_tokens", 1000)
        
        # Estimate energy consumption (simplified)
        energy_per_token = {
            "gpt-4": 0.0000001,
            "gpt-3.5-turbo": 0.00000005,
            "claude-3-opus": 0.00000008,
            "claude-3-sonnet": 0.00000006,
            "llama-3-8b": 0.00000003
        }
        
        model_key = provider.model_name
        energy_per_token_kwh = energy_per_token.get(model_key, 0.0000001)
        total_energy_kwh = estimated_tokens * energy_per_token_kwh
        
        # Estimate CO2 equivalent (simplified)
        region_emission_factors = {
            "global": 400.0,  # g CO2e per kWh
            "local": 100.0,   # Local computation typically greener
            "EU": 300.0,
            "US": 400.0
        }
        
        emission_factor = region_emission_factors.get(provider.region, 400.0)
        co2e_g = total_energy_kwh * emission_factor
        
        return {
            "estimated_energy_kwh": total_energy_kwh,
            "estimated_co2e_g": co2e_g,
            "energy_efficiency": provider.energy_efficiency,
            "sustainability_rating": provider.sustainability_rating,
            "region": provider.region,
            "emission_factor_g_per_kwh": emission_factor
        }
    
    def get_provider_info(self, provider_id: str, model_name: str) -> Optional[ProviderInfo]:
        """Get information about a specific provider and model."""
        key = f"{provider_id}:{model_name}"
        return self.providers.get(key)
    
    def list_providers(self, filter_by: Optional[str] = None) -> List[ProviderInfo]:
        """List all registered providers, optionally filtered."""
        if filter_by:
            return [p for p in self.providers.values() if filter_by in p.provider_id]
        return list(self.providers.values())
    
    def update_provider_rating(self, provider_id: str, model_name: str, 
                             sustainability_rating: str):
        """Update the sustainability rating of a provider."""
        key = f"{provider_id}:{model_name}"
        if key in self.providers:
            self.providers[key].sustainability_rating = sustainability_rating
            logger.info(f"Updated sustainability rating for {key}: {sustainability_rating}")
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics and sustainability metrics."""
        total_providers = len(self.providers)
        avg_energy_efficiency = sum(p.energy_efficiency for p in self.providers.values()) / total_providers
        avg_quality_score = sum(p.quality_score for p in self.providers.values()) / total_providers
        
        sustainability_ratings = {}
        for provider in self.providers.values():
            rating = provider.sustainability_rating
            sustainability_ratings[rating] = sustainability_ratings.get(rating, 0) + 1
        
        return {
            "total_providers": total_providers,
            "avg_energy_efficiency": avg_energy_efficiency,
            "avg_quality_score": avg_quality_score,
            "sustainability_ratings": sustainability_ratings,
            "routing_weights": {
                "quality": self.quality_weight,
                "energy": self.energy_weight,
                "latency": self.latency_weight
            },
            "energy_strict_mode": self.energy_strict
        }


# Factory function for creating routers
def create_energy_aware_router(config: Optional[Dict[str, Any]] = None) -> EnergyAwareRouter:
    """Create an energy-aware router with the specified configuration."""
    return EnergyAwareRouter(config)


# Environment variable configuration
def load_router_config_from_env() -> Dict[str, Any]:
    """Load router configuration from environment variables."""
    config = {}
    
    # Energy weights
    if os.getenv("IOA_ENERGY_WEIGHT"):
        config["energy_weight"] = float(os.getenv("IOA_ENERGY_WEIGHT"))
    if os.getenv("IOA_QUALITY_WEIGHT"):
        config["quality_weight"] = float(os.getenv("IOA_QUALITY_WEIGHT"))
    if os.getenv("IOA_LATENCY_WEIGHT"):
        config["latency_weight"] = float(os.getenv("IOA_LATENCY_WEIGHT"))
    
    # Sustainability settings
    if os.getenv("IOA_ENERGY_STRICT"):
        config["energy_strict"] = bool(int(os.getenv("IOA_ENERGY_STRICT")))
    if os.getenv("IOA_QUALITY_THRESHOLD"):
        config["quality_threshold"] = float(os.getenv("IOA_QUALITY_THRESHOLD"))
    if os.getenv("IOA_ENERGY_PREFERENCE_THRESHOLD"):
        config["energy_preference_threshold"] = float(os.getenv("IOA_ENERGY_PREFERENCE_THRESHOLD"))
    
    return config
