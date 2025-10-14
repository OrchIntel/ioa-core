"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum

from .energy_calculator import EnergyCalculator, EnergyEstimate

logger = logging.getLogger(__name__)


class BudgetStatus(Enum):
    """Status of energy budget check."""
    UNDER_BUDGET = "under_budget"
    WARNING = "warning"
    DELAY = "delay"
    OVER_BUDGET = "over_budget"
    BLOCKED = "blocked"


class EnforcementMode(Enum):
    """Sustainability enforcement modes."""
    MONITOR = "monitor"      # Log only, no blocks
    GRADUATED = "graduated"  # Graduated responses
    STRICT = "strict"        # Immediate blocks


@dataclass
class BudgetContext:
    """Context for energy budget checking."""
    task_id: str
    run_id: str
    project_id: str
    action_type: str
    actor_id: str
    current_usage_kwh: float
    budget_limit_kwh: float
    token_count: int = 0
    model_name: str = "default"
    warn_threshold: float = 0.8
    delay_threshold: float = 0.9
    block_threshold: float = 1.0
    allow_hitl_override: bool = True
    enforcement_mode: str = "graduated"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BudgetDecision:
    """Decision result from energy budget check."""
    status: BudgetStatus
    allowed: bool
    current_usage_kwh: float
    budget_limit_kwh: float
    projected_total_kwh: float
    token_count: int = 0
    model_name: str = "default"
    estimate_kwh_per_100k: float = 0.0
    budget_kwh_per_100k: float = 0.0
    utilization: float = 0.0
    threshold_hit: str = "none"
    override_used: bool = False
    jurisdiction_applied: str = "default"
    delay_ms: int = 0
    warning_message: Optional[str] = None
    block_reason: Optional[str] = None
    hitl_override_required: bool = False
    override_reason: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


class SustainabilityManager:
    """Manager for sustainability enforcement and energy budgeting."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize sustainability manager.
        
        Args:
            config: Sustainability configuration from governance policy
        """
        self.config = config
        
        # PATCH: Cursor-2025-09-15 DISPATCH-GOV-20250915-SUSTAINABILITY-PACK-V0
        # Extract configuration with defaults for Sustainability Pack v0
        self.enabled = config.get("enabled", True)
        self.mode = config.get("mode", "monitor")
        
        # Energy budget per 100k tokens configuration
        self.energy_budget_kwh_per_100k = config.get("energy_budget_kwh_per_100k", 1.0)
        
        # Graduated response thresholds
        thresholds = config.get("thresholds", {"warn": 0.8, "delay": 0.9, "block": 1.0})
        self.warn_threshold = thresholds.get("warn", 0.8)
        self.delay_threshold = thresholds.get("delay", 0.9)
        self.block_threshold = thresholds.get("block", 1.0)
        
        # Override settings
        self.override_ttl_minutes = config.get("override_ttl_minutes", 30)
        
        # Model factors and energy calculator
        self.model_factors = config.get("model_factors_kwh_per_100k", {})
        self.energy_calculator = EnergyCalculator(model_factors=self.model_factors)
        
        # Enforcement mode
        enforcement_mode = config.get("mode", "monitor")
        if isinstance(enforcement_mode, str):
            self.enforcement_mode = EnforcementMode(enforcement_mode)
        else:
            self.enforcement_mode = enforcement_mode
        
        # Other settings
        self.allow_hitl_override = config.get("enforcement_modes", {}).get("graduated", {}).get("allow_overrides", True)
        self.region = config.get("region", "auto")
        
        # Jurisdiction overrides
        self.jurisdiction_overrides = config.get("jurisdiction_overrides", {
            "EU": 0.8,
            "US": 1.2
        })
        
        # Metrics configuration
        self.metrics_config = config.get("metrics", {})
        self.audit_config = config.get("audit", {})
        
        logger.info(f"Sustainability Pack v0 initialized with mode={self.mode}, "
                   f"enabled={self.enabled}, thresholds=({self.warn_threshold}, {self.delay_threshold}, {self.block_threshold})")
    
    def check_energy_budget(self, budget_ctx: BudgetContext) -> BudgetDecision:
        """
        Check if an action is within energy budget limits with graduated responses.
        
        PATCH: Cursor-2025-01-06 DISPATCH-GOV-20250906-SUSTAINABILITY
        Implements graduated responses: ≤80% log only, ≥80% warn, ≥90% delay, ≥100% block.
        
        Args:
            budget_ctx: Budget context for the action
            
        Returns:
            BudgetDecision with status and enforcement details
        """
        # Calculate projected total usage
        projected_total = budget_ctx.current_usage_kwh
        
        # Determine budget limit based on jurisdiction
        budget_limit = self._get_effective_budget_limit(budget_ctx)
        
        # Calculate utilization ratio
        utilization = projected_total / budget_limit if budget_limit > 0 else 0.0
        
        # Calculate per-100k metrics
        estimate_kwh_per_100k = (projected_total / budget_ctx.token_count * 100_000) if budget_ctx.token_count > 0 else 0.0
        budget_kwh_per_100k = self.energy_budget_kwh_per_100k
        
        # Determine threshold hit
        threshold_hit = "none"
        if utilization >= self.block_threshold:
            threshold_hit = "block"
        elif utilization >= self.delay_threshold:
            threshold_hit = "delay"
        elif utilization >= self.warn_threshold:
            threshold_hit = "warn"
        
        # Apply enforcement mode
        if self.enforcement_mode == "monitor" or self.enforcement_mode == EnforcementMode.MONITOR:
            # Monitor mode: log only, no blocks
            status = BudgetStatus.UNDER_BUDGET
            allowed = True
            warning_message = f"Monitor mode: {utilization:.1%} utilization"
            block_reason = None
            delay_ms = 0
            
        elif self.enforcement_mode == "graduated" or self.enforcement_mode == EnforcementMode.GRADUATED:
            # Graduated mode: warn → delay → block
            if utilization < self.warn_threshold:
                status = BudgetStatus.UNDER_BUDGET
                allowed = True
                warning_message = None
                block_reason = None
                delay_ms = 0
            elif utilization < self.delay_threshold:
                status = BudgetStatus.WARNING
                allowed = True
                warning_message = f"Energy usage approaching limit: {utilization:.1%} utilization"
                block_reason = None
                delay_ms = 0
            elif utilization < self.block_threshold:
                status = BudgetStatus.DELAY
                allowed = True
                warning_message = f"Energy usage high: {utilization:.1%} utilization - adding delay"
                block_reason = None
                delay_ms = 150  # 100-200ms delay
            else:
                status = BudgetStatus.OVER_BUDGET
                allowed = False
                warning_message = None
                block_reason = f"Energy budget exceeded: {utilization:.1%} utilization"
                delay_ms = 0
                
        else:  # STRICT mode
            # Strict mode: immediate blocks
            if utilization < self.block_threshold:
                status = BudgetStatus.UNDER_BUDGET
                allowed = True
                warning_message = None
                block_reason = None
                delay_ms = 0
            else:
                status = BudgetStatus.BLOCKED
                allowed = False
                warning_message = None
                block_reason = f"Energy budget exceeded: {utilization:.1%} utilization"
                delay_ms = 0
        
        # Check if HITL override is available
        hitl_override_required = False
        override_reason = None
        override_used = False
        
        if not allowed and self.allow_hitl_override and self.enforcement_mode not in ["monitor", EnforcementMode.MONITOR]:
            hitl_override_required = True
            override_reason = "Energy budget exceeded - human approval required"
            status = BudgetStatus.BLOCKED
        
        # Get jurisdiction applied
        jurisdiction_applied = budget_ctx.metadata.get("jurisdiction", "default")
        
        return BudgetDecision(
            status=status,
            allowed=allowed,
            current_usage_kwh=budget_ctx.current_usage_kwh,
            budget_limit_kwh=budget_limit,
            projected_total_kwh=projected_total,
            token_count=budget_ctx.token_count,
            model_name=budget_ctx.model_name,
            estimate_kwh_per_100k=estimate_kwh_per_100k,
            budget_kwh_per_100k=budget_kwh_per_100k,
            utilization=utilization,
            threshold_hit=threshold_hit,
            override_used=override_used,
            jurisdiction_applied=jurisdiction_applied,
            delay_ms=delay_ms,
            warning_message=warning_message,
            block_reason=block_reason,
            hitl_override_required=hitl_override_required,
            override_reason=override_reason,
            metadata={
                "task_id": budget_ctx.task_id,
                "run_id": budget_ctx.run_id,
                "project_id": budget_ctx.project_id,
                "action_type": budget_ctx.action_type,
                "actor_id": budget_ctx.actor_id,
                "enforcement_mode": self.enforcement_mode.value if hasattr(self.enforcement_mode, 'value') else str(self.enforcement_mode),
                "warn_threshold": self.warn_threshold,
                "delay_threshold": self.delay_threshold,
                "block_threshold": self.block_threshold,
                "jurisdiction": jurisdiction_applied
            }
        )
    
    def _get_effective_budget_limit(self, budget_ctx: BudgetContext) -> float:
        """
        Get effective budget limit considering jurisdiction overrides.
        
        Args:
            budget_ctx: Budget context with jurisdiction info
            
        Returns:
            Effective budget limit in kWh
        """
        # Get base budget limit
        base_limit = budget_ctx.budget_limit_kwh
        
        # Check for jurisdiction override
        jurisdiction = budget_ctx.metadata.get("jurisdiction", "default")
        if jurisdiction in self.jurisdiction_overrides:
            override_factor = self.jurisdiction_overrides[jurisdiction]
            effective_limit = base_limit * override_factor
            logger.debug(f"Applied jurisdiction override for {jurisdiction}: "
                        f"{base_limit:.6f} kWh * {override_factor} = {effective_limit:.6f} kWh")
            return effective_limit
        
        return base_limit
    
    def calculate_energy_proxy(self, 
                              tokens: int, 
                              model_name: str = "DEFAULT",
                              jurisdiction: Optional[str] = None) -> EnergyEstimate:
        """
        Calculate energy proxy for token processing with jurisdiction awareness.
        
        Args:
            tokens: Number of tokens to process
            model_name: AI model name
            jurisdiction: Jurisdiction for budget calculation
            
        Returns:
            EnergyEstimate with consumption details
        """
        # Determine region for carbon intensity
        region = self._get_region_for_jurisdiction(jurisdiction)
        
        # Calculate energy estimate
        estimate = self.energy_calculator.calculate_energy(tokens, model_name, region)
        
        # Add jurisdiction-specific metadata
        estimate.metadata.update({
            "jurisdiction": jurisdiction,
            "energy_budget_kwh_per_100k": self.energy_budget_kwh_per_100k,
            "applied_jurisdiction": jurisdiction or "default"
        })
        
        return estimate
    
    def _get_region_for_jurisdiction(self, jurisdiction: Optional[str]) -> str:
        """Map jurisdiction to carbon intensity region."""
        if not jurisdiction:
            return "global"
        
        # Simple mapping - in production, this could be more sophisticated
        jurisdiction_region_map = {
            "EU": "EU",
            "US": "US", 
            "CA": "CA",
            "AU": "AU",
            "CN": "CN",
            "IN": "IN"
        }
        
        return jurisdiction_region_map.get(jurisdiction, "global")
    
    def get_sustainability_score(self, 
                                energy_usage_kwh: float,
                                budget_limit_kwh: float) -> float:
        """
        Calculate sustainability score based on energy efficiency.
        
        Args:
            energy_usage_kwh: Actual energy usage
            budget_limit_kwh: Budget limit
            
        Returns:
            Sustainability score (0.0 = worst, 1.0 = best)
        """
        if budget_limit_kwh <= 0:
            return 0.0
        
        efficiency_ratio = energy_usage_kwh / budget_limit_kwh
        
        # Score decreases as we approach and exceed budget
        if efficiency_ratio <= 0.5:
            return 1.0  # Excellent efficiency
        elif efficiency_ratio <= 0.8:
            return 0.8  # Good efficiency
        elif efficiency_ratio <= 1.0:
            return 0.5  # Acceptable efficiency
        else:
            return 0.0  # Poor efficiency (over budget)
    
    def create_budget_context(self, 
                             task_id: str,
                             run_id: str,
                             project_id: str,
                             action_type: str,
                             actor_id: str,
                             estimated_energy_kwh: float = 0.0,
                             budget_type: str = "task",
                             jurisdiction: Optional[str] = None) -> BudgetContext:
        """
        Create a budget context for energy checking.
        
        Args:
            task_id: Unique task identifier
            run_id: Run identifier
            project_id: Project identifier
            action_type: Type of action being performed
            actor_id: Actor performing the action
            estimated_energy_kwh: Estimated energy consumption
            budget_type: Type of budget (task, run, project)
            jurisdiction: Jurisdiction for budget calculation
            
        Returns:
            BudgetContext for energy checking
        """
        # Get budget limit based on type
        budget_limit = self.budgets.get(f"{budget_type}_kwh", self.budgets["task_kwh"])
        
        return BudgetContext(
            task_id=task_id,
            run_id=run_id,
            project_id=project_id,
            action_type=action_type,
            actor_id=actor_id,
            current_usage_kwh=estimated_energy_kwh,
            budget_limit_kwh=budget_limit,
            warn_threshold=self.warn_fraction,
            block_threshold=self.block_fraction,
            allow_hitl_override=self.allow_hitl_override,
            metadata={
                "budget_type": budget_type,
                "jurisdiction": jurisdiction,
                "energy_budget_kwh_per_100k": self.energy_budget_kwh_per_100k
            }
        )
    
    def get_energy_budget_status(self, 
                                current_usage: float,
                                budget_limit: float,
                                jurisdiction: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive energy budget status.
        
        Args:
            current_usage: Current energy usage in kWh
            budget_limit: Budget limit in kWh
            jurisdiction: Jurisdiction for budget calculation
            
        Returns:
            Dictionary with budget status and recommendations
        """
        # Apply jurisdiction override if applicable
        effective_limit = budget_limit
        if jurisdiction and jurisdiction in self.jurisdiction_overrides:
            override_factor = self.jurisdiction_overrides[jurisdiction]
            effective_limit = budget_limit * override_factor
        
        # Calculate metrics
        usage_ratio = current_usage / effective_limit if effective_limit > 0 else 0
        sustainability_score = self.get_sustainability_score(current_usage, effective_limit)
        
        # Determine status
        if usage_ratio <= self.warn_fraction:
            status = "under_budget"
        elif usage_ratio <= self.block_fraction:
            status = "warning"
        else:
            status = "over_budget"
        
        return {
            "status": status,
            "current_usage_kwh": current_usage,
            "budget_limit_kwh": effective_limit,
            "usage_ratio": usage_ratio,
            "sustainability_score": sustainability_score,
            "jurisdiction": jurisdiction,
            "applied_jurisdiction": jurisdiction or "default",
            "energy_budget_kwh_per_100k": self.energy_budget_kwh_per_100k,
            "warn_threshold": self.warn_fraction,
            "block_threshold": self.block_fraction,
            "hitl_override_available": self.allow_hitl_override
        }
