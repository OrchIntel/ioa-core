"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
PATCH: Cursor-2025-09-05 DISPATCH-GOV-20250905-LAW-7-SUSTAINABILITY
- Added energy estimation with pluggable estimators
- Added CO2 calculation with regional factors
- Added budget management and enforcement
- Added audit trail integration
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class EnergyUnit(Enum):
    """Energy units for measurement."""
    KWH = "kWh"
    WH = "Wh"
    JOULE = "J"


class BudgetStatus(Enum):
    """Budget status for sustainability enforcement."""
    UNDER_BUDGET = "under_budget"
    WARNING = "warning"
    AT_LIMIT = "at_limit"
    OVER_BUDGET = "over_budget"
    HITL_OVERRIDE = "hitl_override"


@dataclass
class EnergyEstimate:
    """Energy consumption estimate for an action."""
    estimated_kwh: float
    confidence: float = 0.8
    estimation_method: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CO2Estimate:
    """CO2 equivalent estimate for an action."""
    co2e_g: float
    region: str = "auto"
    emission_factor: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class BudgetContext:
    """Context for budget checking and enforcement."""
    task_id: str
    run_id: str
    project_id: str
    action_type: str
    actor_id: str
    current_usage_kwh: float = 0.0
    budget_limit_kwh: float = 0.0
    warn_threshold: float = 0.8
    block_threshold: float = 1.0
    allow_hitl_override: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BudgetDecision:
    """Decision from budget checking."""
    status: BudgetStatus
    allowed: bool
    current_usage_kwh: float
    budget_limit_kwh: float
    projected_total_kwh: float
    warning_message: Optional[str] = None
    block_reason: Optional[str] = None
    hitl_override_required: bool = False
    override_reason: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EnergyEstimator:
    """Base class for energy estimation with pluggable backends."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.estimators: List[Callable] = []
        self._setup_default_estimators()
    
    def _setup_default_estimators(self):
        """Setup default energy estimation methods."""
        self.estimators = [
            self._estimate_by_tokens,
            self._estimate_by_wall_clock,
            self._estimate_by_device_profile,
            self._estimate_by_external_adapter
        ]
    
    def estimate_energy_kwh(self, action_ctx: Dict[str, Any]) -> EnergyEstimate:
        """
        Estimate energy consumption for an action.
        
        Args:
            action_ctx: Action context with metadata for estimation
            
        Returns:
            EnergyEstimate with consumption and confidence
        """
        best_estimate = None
        best_confidence = 0.0
        
        for estimator in self.estimators:
            try:
                estimate = estimator(action_ctx)
                if estimate and estimate.confidence > best_confidence:
                    best_estimate = estimate
                    best_confidence = estimate.confidence
            except Exception as e:
                logger.debug(f"Estimator {estimator.__name__} failed: {e}")
                continue
        
        if not best_estimate:
            # Fallback to conservative estimate
            best_estimate = EnergyEstimate(
                estimated_kwh=0.001,  # 1 Wh default
                confidence=0.1,
                estimation_method="fallback"
            )
        
        return best_estimate
    
    def _estimate_by_tokens(self, action_ctx: Dict[str, Any]) -> Optional[EnergyEstimate]:
        """Estimate energy based on token counts for API calls."""
        if "token_count" not in action_ctx:
            return None
        
        token_count = action_ctx["token_count"]
        model_type = action_ctx.get("model_type", "unknown")
        
        # Energy per token estimates (kWh) - these are placeholders
        energy_per_token = {
            "gpt-4": 0.0000001,    # 0.1 μWh per token
            "gpt-3.5": 0.00000005, # 0.05 μWh per token
            "claude-3": 0.00000008, # 0.08 μWh per token
            "llama-3": 0.00000006,  # 0.06 μWh per token
            "default": 0.0000001    # 0.1 μWh per token
        }
        
        energy_kwh = token_count * energy_per_token.get(model_type, energy_per_token["default"])
        
        return EnergyEstimate(
            estimated_kwh=energy_kwh,
            confidence=0.7,
            estimation_method="token_based",
            metadata={
                "token_count": token_count,
                "model_type": model_type,
                "energy_per_token": energy_per_token.get(model_type, energy_per_token["default"])
            }
        )
    
    def _estimate_by_wall_clock(self, action_ctx: Dict[str, Any]) -> Optional[EnergyEstimate]:
        """Estimate energy based on wall clock time and device profile."""
        if "execution_time_ms" not in action_ctx:
            return None
        
        execution_time_s = action_ctx["execution_time_ms"] / 1000.0
        device_profile = action_ctx.get("device_profile", "default")
        
        # Power consumption estimates (W) - these are placeholders
        power_consumption = {
            "high_performance": 200.0,  # 200W sustained
            "standard": 100.0,          # 100W sustained
            "low_power": 50.0,          # 50W sustained
            "default": 100.0            # 100W default
        }
        
        power_w = power_consumption.get(device_profile, power_consumption["default"])
        energy_kwh = (power_w * execution_time_s) / 3600.0  # Convert to kWh
        
        return EnergyEstimate(
            estimated_kwh=energy_kwh,
            confidence=0.6,
            estimation_method="wall_clock",
            metadata={
                "execution_time_s": execution_time_s,
                "device_profile": device_profile,
                "power_consumption_w": power_w
            }
        )
    
    def _estimate_by_device_profile(self, action_ctx: Dict[str, Any]) -> Optional[EnergyEstimate]:
        """Estimate energy based on device hardware profile."""
        if "device_specs" not in action_ctx:
            return None
        
        device_specs = action_ctx["device_specs"]
        cpu_cores = device_specs.get("cpu_cores", 4)
        gpu_memory_gb = device_specs.get("gpu_memory_gb", 0)
        memory_gb = device_specs.get("memory_gb", 8)
        
        # Simplified power model based on hardware specs
        base_power = 20.0  # Base system power
        cpu_power = cpu_cores * 15.0  # 15W per CPU core
        gpu_power = gpu_memory_gb * 10.0  # 10W per GB GPU memory
        memory_power = memory_gb * 0.5  # 0.5W per GB RAM
        
        total_power_w = base_power + cpu_power + gpu_power + memory_power
        
        # Estimate execution time if not provided
        execution_time_s = action_ctx.get("execution_time_ms", 1000) / 1000.0
        energy_kwh = (total_power_w * execution_time_s) / 3600.0
        
        return EnergyEstimate(
            estimated_kwh=energy_kwh,
            confidence=0.5,
            estimation_method="device_profile",
            metadata={
                "device_specs": device_specs,
                "total_power_w": total_power_w,
                "execution_time_s": execution_time_s
            }
        )
    
    def _estimate_by_external_adapter(self, action_ctx: Dict[str, Any]) -> Optional[EnergyEstimate]:
        """Estimate energy using external adapters if available."""
        # Check for psutil (CPU monitoring)
        try:
            import psutil
            if "cpu_percent" in action_ctx:
                cpu_percent = action_ctx["cpu_percent"]
                execution_time_s = action_ctx.get("execution_time_ms", 1000) / 1000.0
                
                # Estimate power based on CPU utilization
                base_power = 50.0  # Base power at idle
                max_power = 150.0  # Max power at full utilization
                power_w = base_power + (cpu_percent / 100.0) * (max_power - base_power)
                energy_kwh = (power_w * execution_time_s) / 3600.0
                
                return EnergyEstimate(
                    estimated_kwh=energy_kwh,
                    confidence=0.8,
                    estimation_method="psutil_cpu",
                    metadata={
                        "cpu_percent": cpu_percent,
                        "power_w": power_w,
                        "execution_time_s": execution_time_s
                    }
                )
        except ImportError:
            pass
        
        # Check for NVIDIA GPU monitoring
        try:
            import pynvml
            if "gpu_utilization" in action_ctx:
                gpu_util = action_ctx["gpu_utilization"]
                execution_time_s = action_ctx.get("execution_time_ms", 1000) / 1000.0
                
                # GPU power estimation
                gpu_power_w = 200.0  # Typical GPU power
                power_w = gpu_power_w * (gpu_util / 100.0)
                energy_kwh = (power_w * execution_time_s) / 3600.0
                
                return EnergyEstimate(
                    estimated_kwh=energy_kwh,
                    confidence=0.7,
                    estimation_method="nvidia_gpu",
                    metadata={
                        "gpu_utilization": gpu_util,
                        "gpu_power_w": gpu_power_w,
                        "execution_time_s": execution_time_s
                    }
                )
        except ImportError:
            pass
        
        return None


class CO2Calculator:
    """CO2 equivalent calculator with regional emission factors."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._setup_emission_factors()
    
    def _setup_emission_factors(self):
        """Setup regional emission factors for electricity generation."""
        # CO2 emission factors in g CO2e per kWh
        # Source: IPCC and regional energy mix data (approximate)
        self.emission_factors = {
            "EU": 300.0,      # European Union average
            "US": 400.0,      # United States average
            "UK": 250.0,      # United Kingdom (more renewable)
            "CA": 150.0,      # Canada (hydro-heavy)
            "AU": 800.0,      # Australia (coal-heavy)
            "CN": 600.0,      # China (coal-heavy)
            "IN": 700.0,      # India (coal-heavy)
            "BR": 100.0,      # Brazil (hydro-heavy)
            "NO": 20.0,       # Norway (hydro-heavy)
            "FR": 50.0,       # France (nuclear-heavy)
            "DE": 400.0,      # Germany (coal + renewable mix)
            "default": 400.0  # Global average
        }
    
    def estimate_co2e_g(self, energy_kwh: float, region: str = "auto") -> CO2Estimate:
        """
        Estimate CO2 equivalent emissions for energy consumption.
        
        Args:
            energy_kwh: Energy consumption in kWh
            region: Geographic region for emission factors
            
        Returns:
            CO2Estimate with emissions and metadata
        """
        if region == "auto":
            region = self._detect_region()
        
        emission_factor = self.emission_factors.get(region, self.emission_factors["default"])
        co2e_g = energy_kwh * emission_factor
        
        return CO2Estimate(
            co2e_g=co2e_g,
            region=region,
            emission_factor=emission_factor,
            metadata={
                "energy_kwh": energy_kwh,
                "emission_factor_g_per_kwh": emission_factor
            }
        )
    
    def _detect_region(self) -> str:
        """Auto-detect region from environment variables or system."""
        # Check environment variable first
        env_region = os.getenv("IOA_REGION")
        if env_region and env_region in self.emission_factors:
            return env_region
        
        # Check timezone for rough geographic inference
        try:
            tz = time.tzname[time.daylight]
            if "UTC" in tz or "GMT" in tz:
                return "default"
            elif "EST" in tz or "PST" in tz or "CST" in tz or "MST" in tz:
                return "US"
            elif "CET" in tz or "CEST" in tz:
                return "EU"
            elif "JST" in tz:
                return "JP"
            elif "CST" in tz and "China" in str(time.tzname):
                return "CN"
        except Exception:
            return "default"
        
        return "default"


class BudgetManager:
    """Manager for energy budgets and enforcement."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.budgets: Dict[str, Dict[str, float]] = {}
        self.usage: Dict[str, Dict[str, float]] = {}
        self.hitl_overrides: Dict[str, Dict[str, Any]] = {}
        
        # Load configuration
        self.task_budget_kwh = self.config.get("task_kwh", 0.010)
        self.run_budget_kwh = self.config.get("run_kwh", 0.250)
        self.project_budget_kwh = self.config.get("project_kwh", 5.000)
        self.warn_fraction = self.config.get("warn_fraction", 0.8)
        self.block_fraction = self.config.get("block_fraction", 1.0)
        self.allow_hitl_override = self.config.get("allow_hitl_override", True)
    
    def check_budget(self, budget_ctx: BudgetContext) -> BudgetDecision:
        """
        Check if an action is within budget constraints.
        
        Args:
            budget_ctx: Budget context for the action
            
        Returns:
            BudgetDecision with status and enforcement details
        """
        # Initialize usage tracking if not exists
        if budget_ctx.project_id not in self.usage:
            self.usage[budget_ctx.project_id] = {
                "task": {},
                "run": {},
                "project": 0.0
            }
        
        if budget_ctx.run_id not in self.usage[budget_ctx.project_id]["run"]:
            self.usage[budget_ctx.project_id]["run"][budget_ctx.run_id] = 0.0
        
        if budget_ctx.task_id not in self.usage[budget_ctx.project_id]["task"]:
            self.usage[budget_ctx.project_id]["task"][budget_ctx.task_id] = 0.0
        
        # Get current usage
        current_task_usage = self.usage[budget_ctx.project_id]["task"][budget_ctx.task_id]
        current_run_usage = self.usage[budget_ctx.project_id]["run"][budget_ctx.run_id]
        current_project_usage = self.usage[budget_ctx.project_id]["project"]
        
        # Calculate projected totals
        projected_task_total = current_task_usage + budget_ctx.current_usage_kwh
        projected_run_total = current_run_usage + budget_ctx.current_usage_kwh
        projected_project_total = current_project_usage + budget_ctx.current_usage_kwh
        
        # Check task budget first (most restrictive)
        task_status = self._check_single_budget(
            projected_task_total, 
            self.task_budget_kwh, 
            "task"
        )
        
        # Check run budget
        run_status = self._check_single_budget(
            projected_run_total, 
            self.run_budget_kwh, 
            "run"
        )
        
        # Check project budget
        project_status = self._check_single_budget(
            projected_project_total, 
            self.project_budget_kwh, 
            "project"
        )
        
        # Determine overall status - task budget takes precedence
        if task_status == BudgetStatus.OVER_BUDGET:
            overall_status = BudgetStatus.OVER_BUDGET
        elif task_status == BudgetStatus.WARNING:
            overall_status = BudgetStatus.WARNING
        elif run_status == BudgetStatus.OVER_BUDGET:
            overall_status = BudgetStatus.OVER_BUDGET
        elif run_status == BudgetStatus.WARNING:
            overall_status = BudgetStatus.WARNING
        elif project_status == BudgetStatus.OVER_BUDGET:
            overall_status = BudgetStatus.OVER_BUDGET
        elif project_status == BudgetStatus.WARNING:
            overall_status = BudgetStatus.WARNING
        else:
            overall_status = BudgetStatus.UNDER_BUDGET
        
        # Check for HITL override
        if overall_status == BudgetStatus.OVER_BUDGET and self.allow_hitl_override:
            override_key = f"{budget_ctx.project_id}:{budget_ctx.run_id}"
            if override_key in self.hitl_overrides:
                override = self.hitl_overrides[override_key]
                if not self._is_override_expired(override):
                    overall_status = BudgetStatus.HITL_OVERRIDE
        
        # Create decision
        decision = BudgetDecision(
            status=overall_status,
            allowed=overall_status != BudgetStatus.OVER_BUDGET,
            current_usage_kwh=current_task_usage,  # Use task usage for decision
            budget_limit_kwh=self.task_budget_kwh,  # Use task budget for decision
            projected_total_kwh=projected_task_total,  # Use task projection for decision
            hitl_override_required=overall_status == BudgetStatus.OVER_BUDGET
        )
        
        # Add warning/block messages based on task budget
        if overall_status == BudgetStatus.WARNING:
            decision.warning_message = (
                f"Energy usage at {projected_task_total/self.task_budget_kwh*100:.1f}% "
                f"of task budget limit ({self.task_budget_kwh:.3f} kWh)"
            )
        elif overall_status == BudgetStatus.OVER_BUDGET:
            decision.block_reason = (
                f"Energy usage exceeds task budget limit: "
                f"{projected_task_total:.3f} kWh > {self.task_budget_kwh:.3f} kWh"
            )
        
        return decision
    
    def _check_single_budget(self, projected_total: float, budget_limit: float, budget_type: str) -> BudgetStatus:
        """Check a single budget constraint."""
        if projected_total < budget_limit * self.warn_fraction:
            return BudgetStatus.UNDER_BUDGET
        elif projected_total < budget_limit * self.block_fraction:
            return BudgetStatus.WARNING
        else:
            return BudgetStatus.OVER_BUDGET
    
    def _determine_overall_status(self, statuses: List[BudgetStatus]) -> BudgetStatus:
        """Determine overall budget status from individual checks."""
        if BudgetStatus.OVER_BUDGET in statuses:
            return BudgetStatus.OVER_BUDGET
        elif BudgetStatus.WARNING in statuses:
            return BudgetStatus.WARNING
        else:
            return BudgetStatus.UNDER_BUDGET
    
    def _is_override_expired(self, override: Dict[str, Any]) -> bool:
        """Check if a HITL override has expired."""
        expires_at = override.get("expires_at")
        if not expires_at:
            return False
        
        try:
            if isinstance(expires_at, str):
                expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            else:
                expires_dt = expires_at
            
            return datetime.now(timezone.utc) > expires_dt
        except Exception:
            return False
    
    def record_usage(self, budget_ctx: BudgetContext, actual_kwh: float):
        """Record actual energy usage for budget tracking."""
        if budget_ctx.project_id not in self.usage:
            self.usage[budget_ctx.project_id] = {
                "task": {},
                "run": {},
                "project": 0.0
            }
        
        if budget_ctx.run_id not in self.usage[budget_ctx.project_id]["run"]:
            self.usage[budget_ctx.project_id]["run"][budget_ctx.run_id] = 0.0
        
        if budget_ctx.task_id not in self.usage[budget_ctx.project_id]["task"]:
            self.usage[budget_ctx.project_id]["task"][budget_ctx.task_id] = 0.0
        
        # Update usage
        self.usage[budget_ctx.project_id]["task"][budget_ctx.task_id] += actual_kwh
        self.usage[budget_ctx.project_id]["run"][budget_ctx.run_id] += actual_kwh
        self.usage[budget_ctx.project_id]["project"] += actual_kwh
        
        logger.info(f"Recorded energy usage: {actual_kwh:.6f} kWh for task {budget_ctx.task_id}")
    
    def add_hitl_override(self, project_id: str, run_id: str, reason: str, 
                          duration_minutes: int = 15):
        """Add a HITL override for budget enforcement."""
        if not self.allow_hitl_override:
            raise ValueError("HITL overrides are not allowed")
        
        override_key = f"{project_id}:{run_id}"
        expires_at = datetime.now(timezone.utc).timestamp() + (duration_minutes * 60)
        expires_dt = datetime.fromtimestamp(expires_at, tz=timezone.utc)
        
        self.hitl_overrides[override_key] = {
            "reason": reason,
            "granted_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_dt.isoformat(),
            "duration_minutes": duration_minutes
        }
        
        logger.info(f"Added HITL override for {override_key}: {reason} (expires: {expires_dt})")
    
    def get_usage_summary(self, project_id: str, run_id: Optional[str] = None) -> Dict[str, Any]:
        """Get usage summary for a project or run."""
        if project_id not in self.usage:
            return {"error": "Project not found"}
        
        project_usage = self.usage[project_id]
        
        if run_id:
            if run_id not in project_usage["run"]:
                return {"error": "Run not found"}
            
            return {
                "project_id": project_id,
                "run_id": run_id,
                "run_usage_kwh": project_usage["run"][run_id],
                "run_budget_kwh": self.run_budget_kwh,
                "run_percentage": (project_usage["run"][run_id] / self.run_budget_kwh) * 100,
                "tasks": project_usage["task"]
            }
        else:
            return {
                "project_id": project_id,
                "project_usage_kwh": project_usage["project"],
                "project_budget_kwh": self.project_budget_kwh,
                "project_percentage": (project_usage["project"] / self.project_budget_kwh) * 100,
                "runs": len(project_usage["run"]),
                "tasks": len(project_usage["task"])
            }


class SustainabilityManager:
    """Main sustainability manager for Law 7 compliance."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.energy_estimator = EnergyEstimator(config)
        self.co2_calculator = CO2Calculator(config)
        self.budget_manager = BudgetManager(config)
        
        logger.info("Sustainability Manager initialized for Law 7 compliance")
    
    def estimate_action_energy(self, action_ctx: Dict[str, Any]) -> EnergyEstimate:
        """Estimate energy consumption for an action."""
        return self.energy_estimator.estimate_energy_kwh(action_ctx)
    
    def estimate_action_co2e(self, action_ctx: Dict[str, Any], region: str = "auto") -> CO2Estimate:
        """Estimate CO2 equivalent for an action."""
        energy_estimate = self.estimate_action_energy(action_ctx)
        return self.co2_calculator.estimate_co2e_g(energy_estimate.estimated_kwh, region)
    
    def check_energy_budget(self, budget_ctx: BudgetContext) -> BudgetDecision:
        """Check energy budget for an action."""
        return self.budget_manager.check_budget(budget_ctx)
    
    def record_energy_usage(self, budget_ctx: BudgetContext, actual_kwh: float):
        """Record actual energy usage."""
        self.budget_manager.record_usage(budget_ctx, actual_kwh)
    
    def add_hitl_override(self, project_id: str, run_id: str, reason: str, 
                          duration_minutes: int = 15):
        """Add HITL override for budget enforcement."""
        self.budget_manager.add_hitl_override(project_id, run_id, reason, duration_minutes)
    
    def get_usage_summary(self, project_id: str, run_id: Optional[str] = None) -> Dict[str, Any]:
        """Get usage summary."""
        return self.budget_manager.get_usage_summary(project_id, run_id)
    
    def forecast_energy_usage(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Forecast energy usage for a plan."""
        total_estimated_kwh = 0.0
        action_estimates = []
        
        for action in plan_data.get("actions", []):
            estimate = self.estimate_action_energy(action)
            total_estimated_kwh += estimate.estimated_kwh
            
            action_estimates.append({
                "action_id": action.get("id", "unknown"),
                "action_type": action.get("type", "unknown"),
                "estimated_kwh": estimate.estimated_kwh,
                "confidence": estimate.confidence,
                "estimation_method": estimate.estimation_method
            })
        
        # Estimate CO2 equivalent
        co2_estimate = self.co2_calculator.estimate_co2e_g(total_estimated_kwh)
        
        return {
            "total_estimated_kwh": total_estimated_kwh,
            "total_estimated_co2e_g": co2_estimate.co2e_g,
            "region": co2_estimate.region,
            "action_estimates": action_estimates,
            "budget_analysis": {
                "task_budget_kwh": self.budget_manager.task_budget_kwh,
                "run_budget_kwh": self.budget_manager.run_budget_kwh,
                "project_budget_kwh": self.budget_manager.project_budget_kwh,
                "within_task_budget": total_estimated_kwh <= self.budget_manager.task_budget_kwh,
                "within_run_budget": total_estimated_kwh <= self.budget_manager.run_budget_kwh,
                "within_project_budget": total_estimated_kwh <= self.budget_manager.project_budget_kwh
            }
        }
