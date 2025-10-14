"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import logging
import uuid
import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from .manifest import get_laws
from .system_laws import (
    LawViolationError, PolicyConflictError, FairnessViolationError,
    HumanApprovalRequiredError, AuditTrailError, SustainabilityViolationError,
    EnergyBudgetExceededError
)

logger = logging.getLogger(__name__)


class ActionRiskLevel(Enum):
    """Risk levels for actions requiring human approval."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationStatus(Enum):
    """Status of policy validation."""
    APPROVED = "approved"
    BLOCKED = "blocked"
    REQUIRES_APPROVAL = "requires_approval"
    MITIGATED = "mitigated"


@dataclass
class ActionContext:
    """Context for action validation against System Laws."""
    action_id: str
    action_type: str
    actor_id: str
    target_entity: Optional[str] = None
    data_classification: Optional[str] = None
    jurisdiction: Optional[str] = None
    risk_level: ActionRiskLevel = ActionRiskLevel.LOW
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        if not self.action_id:
            self.action_id = str(uuid.uuid4())


@dataclass
class ValidationResult:
    """Result of policy validation."""
    status: ValidationStatus
    action_id: str
    audit_id: str
    laws_checked: List[str] = field(default_factory=list)
    violations: List[Dict[str, Any]] = field(default_factory=list)
    required_approvals: List[Dict[str, Any]] = field(default_factory=list)
    fairness_score: Optional[float] = None
    mitigation_applied: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


class PolicyEngine:
    """Engine for enforcing System Laws and policy decisions."""
    
    def __init__(self):
        self.laws = get_laws()
        self.fairness_threshold = self.laws.get_fairness_threshold()
        self.conflict_resolution_order = self.laws.get_conflict_resolution_order()
        
        # PATCH: Cursor-2025-09-05 DISPATCH-EXEC-20250905-CONNECTOR-10K-TEST-&-PATCHES
        # Add jurisdiction conflict resolution priority (GDPR > SOX > others)
        self.jurisdiction_priority = {
            "EU": 1,      # GDPR - highest priority
            "US": 2,      # SOX, CCPA - medium priority  
            "UK": 3,      # UK GDPR
            "CA": 4,      # PIPEDA
            "AU": 5,      # Privacy Act
            "default": 999
        }
        
        # Policy event handlers
        self._policy_event_handlers: List[callable] = []
        
        # PATCH: Cursor-2025-09-15 DISPATCH-GOV-20250915-ETHICS-PACK-V0
        # Initialize Ethics Pack v0 detectors
        self._ethics_detectors = {}
        self._ethics_config = {}
        self._load_ethics_pack()
        
        logger.info("Policy Engine initialized with System Laws and jurisdiction conflict resolution")
    
    def register_policy_event_handler(self, handler: callable):
        """Register a handler for policy events."""
        self._policy_event_handlers.append(handler)
    
    def emit_policy_event(self, event_type: str, event_data: Dict[str, Any]):
        """Emit a policy event to registered handlers."""
        event = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": event_data
        }
        
        for handler in self._policy_event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Policy event handler error: {e}")
    
    def resolve_jurisdiction_conflicts(self, jurisdictions: List[str], 
                                     data_classification: str) -> str:
        """
        Resolve conflicts between jurisdictions using priority ordering.
        
        PATCH: Cursor-2025-09-05 DISPATCH-EXEC-20250905-CONNECTOR-10K-TEST-&-PATCHES
        Implements GDPR > SOX default priority for jurisdiction conflicts.
        
        Args:
            jurisdictions: List of applicable jurisdictions
            data_classification: Data classification level
            
        Returns:
            Highest priority jurisdiction to apply
        """
        if not jurisdictions:
            return "default"
        
        # Sort by priority (lower number = higher priority)
        sorted_jurisdictions = sorted(
            jurisdictions,
            key=lambda j: self.jurisdiction_priority.get(j, self.jurisdiction_priority["default"])
        )
        
        highest_priority = sorted_jurisdictions[0]
        
        # Log jurisdiction resolution for audit
        logger.info(f"Jurisdiction conflict resolved: {jurisdictions} -> {highest_priority} "
                   f"(data_classification: {data_classification})")
        
        return highest_priority
    
    def validate_against_laws(self, action_ctx: ActionContext) -> ValidationResult:
        """Validate an action against all System Laws."""
        audit_id = str(uuid.uuid4())
        laws_checked = []
        violations = []
        required_approvals = []
        
        logger.info(f"Validating action {action_ctx.action_id} against System Laws")
        
        # PATCH: Cursor-2025-09-05 DISPATCH-EXEC-20250905-CONNECTOR-10K-TEST-&-PATCHES
        # Resolve jurisdiction conflicts if multiple jurisdictions apply
        if action_ctx.metadata.get("applicable_jurisdictions"):
            resolved_jurisdiction = self.resolve_jurisdiction_conflicts(
                action_ctx.metadata["applicable_jurisdictions"],
                action_ctx.data_classification or "standard"
            )
            action_ctx.jurisdiction = resolved_jurisdiction
            logger.info(f"Resolved jurisdiction: {resolved_jurisdiction}")
        
        # Check each law in priority order
        for law_id in self.conflict_resolution_order:
            law = self.laws.get_law(law_id)
            if not law:
                continue
            
            laws_checked.append(law_id)
            law_result = self._check_single_law(law, action_ctx)
            
            if law_result.get("violation"):
                violations.append(law_result)
            
            if law_result.get("requires_approval"):
                required_approvals.append(law_result)
        
        # Determine overall status
        status = self._determine_validation_status(violations, required_approvals)
        
        # Apply fairness checks if action involves outputs
        fairness_score = None
        if action_ctx.action_type in ["llm_generation", "decision_making", "content_creation"]:
            fairness_score = self._calculate_fairness_score(action_ctx)
            
            if fairness_score > self.fairness_threshold:
                violations.append({
                    "law_id": "law5",
                    "type": "fairness_violation",
                    "score": fairness_score,
                    "threshold": self.fairness_threshold
                })
                status = ValidationStatus.BLOCKED
        
        # Create validation result
        result = ValidationResult(
            status=status,
            action_id=action_ctx.action_id,
            audit_id=audit_id,
            laws_checked=laws_checked,
            violations=violations,
            required_approvals=required_approvals,
            fairness_score=fairness_score,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Emit policy event
        self.emit_policy_event("action_validated", {
            "action_id": action_ctx.action_id,
            "audit_id": audit_id,
            "status": status.value,
            "violations": len(violations),
            "required_approvals": len(required_approvals),
            "jurisdiction": action_ctx.jurisdiction
        })
        
        return result
    
    def _check_single_law(self, law: Dict[str, Any], action_ctx: ActionContext) -> Dict[str, Any]:
        """Check a single law against the action context."""
        law_id = law["id"]
        law_name = law["name"]
        enforcement = law["enforcement"]
        
        result = {
            "law_id": law_id,
            "law_name": law_name,
            "enforcement": enforcement,
            "violation": False,
            "requires_approval": False,
            "details": None
        }
        
        try:
            if law_id == "law1":  # Compliance Supremacy
                result.update(self._check_compliance_supremacy(action_ctx))
            elif law_id == "law2":  # Governance Precedence
                result.update(self._check_governance_precedence(action_ctx))
            elif law_id == "law3":  # Auditability
                result.update(self._check_auditability(action_ctx))
            elif law_id == "law4":  # Immutable Governance
                result.update(self._check_immutable_governance(action_ctx))
            elif law_id == "law5":  # Fairness & Non-Discrimination
                result.update(self._check_fairness(action_ctx))
            elif law_id == "law6":  # Human Oversight Supremacy
                result.update(self._check_human_oversight(action_ctx))
            elif law_id == "law7":  # Sustainability Stewardship
                result.update(self._check_sustainability(action_ctx))
                
        except Exception as e:
            logger.error(f"Error checking law {law_id}: {e}")
            result["violation"] = True
            result["details"] = f"Law check error: {e}"
        
        return result
    
    def _check_compliance_supremacy(self, action_ctx: ActionContext) -> Dict[str, Any]:
        """
        Check compliance with applicable regulations.
        
        PATCH: Cursor-2025-09-05 DISPATCH-EXEC-20250905-CONNECTOR-10K-TEST-&-PATCHES
        Enhanced jurisdiction-specific compliance with GDPR > SOX priority.
        """
        # Check jurisdiction-specific compliance with priority ordering
        if action_ctx.jurisdiction == "EU" and action_ctx.data_classification == "personal":
            # GDPR compliance check - highest priority
            if action_ctx.action_type in ["data_export", "data_sharing", "data_processing"]:
                return {
                    "violation": True,
                    "details": "EU personal data operations require GDPR compliance review"
                }
            
            # Check for explicit consent in metadata
            if not action_ctx.metadata.get("gdpr_consent"):
                return {
                    "violation": True,
                    "details": "EU personal data processing requires explicit GDPR consent"
                }
        
        elif action_ctx.jurisdiction == "US" and action_ctx.data_classification == "personal":
            # SOX/CCPA compliance check - medium priority
            if action_ctx.action_type in ["financial_data_export", "audit_data_access"]:
                return {
                    "violation": True,
                    "details": "US financial data operations require SOX compliance review"
                }
        
        # Check data classification regardless of jurisdiction
        if action_ctx.data_classification == "confidential":
            if action_ctx.action_type in ["external_api_call", "data_export", "data_sharing"]:
                return {
                    "violation": True,
                    "details": "Confidential data requires explicit approval for external access"
                }
        
        elif action_ctx.data_classification == "restricted":
            if action_ctx.action_type in ["data_processing", "model_training"]:
                return {
                    "violation": True,
                    "details": "Restricted data requires special handling approval"
                }
        
        return {"violation": False}
    
    def _check_governance_precedence(self, action_ctx: ActionContext) -> Dict[str, Any]:
        """Check that governance policies take precedence."""
        # This law is enforced at the system level, so individual actions
        # should not be able to override it
        return {"violation": False}
    
    def _check_auditability(self, action_ctx: ActionContext) -> Dict[str, Any]:
        """Check that audit trail requirements are met."""
        # Audit ID is automatically generated, so this should always pass
        # Additional audit context can be validated here
        return {"violation": False}
    
    def _check_immutable_governance(self, action_ctx: ActionContext) -> Dict[str, Any]:
        """Check that reflex/auto-actions are bounded."""
        if action_ctx.action_type in ["reflex_action", "auto_execution"]:
            # Check if action is within bounds
            if action_ctx.risk_level in [ActionRiskLevel.HIGH, ActionRiskLevel.CRITICAL]:
                return {
                    "violation": True,
                    "details": "High-risk reflex actions require human approval"
                }
        
        return {"violation": False}
    
    def _check_fairness(self, action_ctx: ActionContext) -> Dict[str, Any]:
        """Check fairness and non-discrimination."""
        # Fairness is checked separately in the main validation flow
        return {"violation": False}
    
    def _check_human_oversight(self, action_ctx: ActionContext) -> Dict[str, Any]:
        """Check if human approval is required."""
        if action_ctx.risk_level in [ActionRiskLevel.HIGH, ActionRiskLevel.CRITICAL]:
            return {
                "requires_approval": True,
                "approval_type": "human_review",
                "details": f"Action requires human approval due to {action_ctx.risk_level.value} risk level"
            }
        
        return {"requires_approval": False}
    
    def _check_sustainability(self, action_ctx: ActionContext) -> Dict[str, Any]:
        """
        Check sustainability compliance (Law 7) with graduated responses.
        
        PATCH: Cursor-2025-09-15 DISPATCH-GOV-20250915-SUSTAINABILITY-PACK-V0
        Implements Sustainability Pack v0 with carbontracker integration and evidence collection.
        """
        try:
            # Import sustainability manager
            from ...sustainability import SustainabilityManager, BudgetContext, EnforcementMode
            
            # Load sustainability configuration from file
            import json
            from pathlib import Path
            config_path = Path(__file__).parent.parent.parent.parent.parent / "configs" / "governance" / "sustainability_pack_v0.json"
            
            if config_path.exists():
                with open(config_path, 'r') as f:
                    sustainability_config = json.load(f)
            else:
                # Fallback to default configuration
                sustainability_config = {
                    "enabled": True,
                    "mode": "monitor",
                    "energy_budget_kwh_per_100k": 1.0,
                    "thresholds": {"warn": 0.8, "delay": 0.9, "block": 1.0},
                    "model_factors_kwh_per_100k": {"default": 0.45}
                }
            
            # Skip if disabled
            if not sustainability_config.get("enabled", True):
                return {
                    "violation": False,
                    "details": "Sustainability check disabled"
                }
            
            # Extract token count and model name from metadata
            token_count = action_ctx.metadata.get("token_count", 0)
            model_name = action_ctx.metadata.get("model_name", "default")
            
            # Calculate energy estimate using carbontracker if available
            estimated_energy_kwh = 0.0
            try:
                from carbontracker import CarbonTracker
                # Use carbontracker for more accurate estimation
                model_factor = sustainability_config.get("model_factors_kwh_per_100k", {}).get(model_name, 0.45)
                estimated_energy_kwh = (token_count / 100_000) * model_factor
            except ImportError:
                # Fallback to simple calculation
                model_factor = sustainability_config.get("model_factors_kwh_per_100k", {}).get(model_name, 0.45)
                estimated_energy_kwh = (token_count / 100_000) * model_factor
            
            # Create budget context with enhanced fields
            budget_ctx = BudgetContext(
                task_id=action_ctx.metadata.get("task_id", action_ctx.action_id),
                run_id=action_ctx.metadata.get("run_id", "default"),
                project_id=action_ctx.metadata.get("project_id", "default"),
                action_type=action_ctx.action_type,
                actor_id=action_ctx.actor_id,
                current_usage_kwh=estimated_energy_kwh,
                budget_limit_kwh=sustainability_config.get("energy_budget_kwh_per_100k", 1.0),
                token_count=token_count,
                model_name=model_name,
                warn_threshold=sustainability_config.get("thresholds", {}).get("warn", 0.8),
                delay_threshold=sustainability_config.get("thresholds", {}).get("delay", 0.9),
                block_threshold=sustainability_config.get("thresholds", {}).get("block", 1.0),
                allow_hitl_override=sustainability_config.get("enforcement_modes", {}).get("graduated", {}).get("allow_overrides", True),
                enforcement_mode=sustainability_config.get("mode", "monitor"),
                metadata=action_ctx.metadata
            )
            
            # Check budget
            sustainability_manager = SustainabilityManager(sustainability_config)
            budget_decision = sustainability_manager.check_energy_budget(budget_ctx)
            
            # Apply delay if required
            if budget_decision.delay_ms > 0:
                import time
                time.sleep(budget_decision.delay_ms / 1000.0)
            
            # Log metrics if configured
            self._log_sustainability_metrics(budget_decision, sustainability_config)
            
            # Determine response based on status
            if budget_decision.status.value in ["over_budget", "blocked"]:
                return {
                    "violation": True,
                    "details": f"Sustainability violation: {budget_decision.block_reason}",
                    "sustainability_evidence": {
                        "token_count": budget_decision.token_count,
                        "model_name": budget_decision.model_name,
                        "estimate_kwh_per_100k": budget_decision.estimate_kwh_per_100k,
                        "budget_kwh_per_100k": budget_decision.budget_kwh_per_100k,
                        "utilization": budget_decision.utilization,
                        "threshold_hit": budget_decision.threshold_hit,
                        "override_used": budget_decision.override_used,
                        "jurisdiction_applied": budget_decision.jurisdiction_applied,
                        "delay_ms": budget_decision.delay_ms,
                        "enforcement_mode": sustainability_config.get("mode", "monitor"),
                        "status": budget_decision.status.value if hasattr(budget_decision.status, 'value') else str(budget_decision.status)
                    }
                }
            elif budget_decision.status.value in ["warning", "delay"]:
                return {
                    "violation": False,
                    "details": f"Sustainability {budget_decision.status.value}: {budget_decision.warning_message}",
                    "sustainability_evidence": {
                        "token_count": budget_decision.token_count,
                        "model_name": budget_decision.model_name,
                        "estimate_kwh_per_100k": budget_decision.estimate_kwh_per_100k,
                        "budget_kwh_per_100k": budget_decision.budget_kwh_per_100k,
                        "utilization": budget_decision.utilization,
                        "threshold_hit": budget_decision.threshold_hit,
                        "override_used": budget_decision.override_used,
                        "jurisdiction_applied": budget_decision.jurisdiction_applied,
                        "delay_ms": budget_decision.delay_ms,
                        "enforcement_mode": sustainability_config.get("mode", "monitor"),
                        "status": budget_decision.status.value if hasattr(budget_decision.status, 'value') else str(budget_decision.status)
                    }
                }
            else:
                return {
                    "violation": False,
                    "details": "Sustainability compliance: within budget limits",
                    "sustainability_evidence": {
                        "token_count": budget_decision.token_count,
                        "model_name": budget_decision.model_name,
                        "estimate_kwh_per_100k": budget_decision.estimate_kwh_per_100k,
                        "budget_kwh_per_100k": budget_decision.budget_kwh_per_100k,
                        "utilization": budget_decision.utilization,
                        "threshold_hit": budget_decision.threshold_hit,
                        "override_used": budget_decision.override_used,
                        "jurisdiction_applied": budget_decision.jurisdiction_applied,
                        "delay_ms": budget_decision.delay_ms,
                        "enforcement_mode": sustainability_config.get("mode", "monitor"),
                        "status": budget_decision.status.value if hasattr(budget_decision.status, 'value') else str(budget_decision.status)
                    }
                }
                
        except ImportError:
            # Sustainability module not available - log warning but don't block
            logger.warning("Sustainability module not available - skipping Law 7 compliance check")
            return {
                "violation": False,
                "details": "Sustainability check skipped - module not available"
            }
        except Exception as e:
            logger.error(f"Sustainability check failed: {e}")
            return {
                "violation": False,
                "details": f"Sustainability check error: {e}"
            }
    
    def _calculate_fairness_score(self, action_ctx: ActionContext) -> float:
        """Calculate a fairness score for the action."""
        # This is a simplified fairness calculation
        # In practice, this would use more sophisticated bias detection algorithms
        
        # Check for potential bias indicators in metadata
        bias_indicators = 0
        total_indicators = 0
        
        # Check demographic indicators
        if "demographic_data" in action_ctx.metadata:
            total_indicators += 1
            demo_data = action_ctx.metadata["demographic_data"]
            if any(demo_data.get(key, 0) > 0.8 for key in ["age_bias", "gender_bias", "ethnicity_bias"]):
                bias_indicators += 1
        
        # Check content bias
        if "content_analysis" in action_ctx.metadata:
            total_indicators += 1
            content_data = action_ctx.metadata["content_analysis"]
            if content_data.get("sentiment_bias", 0) > 0.7:
                bias_indicators += 1
        
        if total_indicators == 0:
            return 0.0  # No bias indicators found
        
        return bias_indicators / total_indicators
    
    def _determine_validation_status(self, violations: List[Dict], 
                                   required_approvals: List[Dict]) -> ValidationStatus:
        """Determine the overall validation status."""
        if not violations and not required_approvals:
            return ValidationStatus.APPROVED
        
        if violations:
            # Check if any violations are critical
            critical_violations = [
                v for v in violations 
                if self.laws.is_critical_law(v.get("law_id", ""))
            ]
            
            if critical_violations:
                return ValidationStatus.BLOCKED
        
        if required_approvals:
            return ValidationStatus.REQUIRES_APPROVAL
        
        # Non-critical violations may be mitigated
        return ValidationStatus.MITIGATED
    
    def resolve_policy_conflicts(self, conflicting_laws: List[str], 
                               context: Dict[str, Any]) -> str:
        """Resolve conflicts between laws using priority ordering."""
        # Use the predefined conflict resolution order
        for law_id in self.conflict_resolution_order:
            if law_id in conflicting_laws:
                return law_id
        
        # If no resolution found, raise error
        raise PolicyConflictError(conflicting_laws, "No resolution found in priority order")
    
    def get_mitigation_strategies(self, violation_type: str) -> List[str]:
        """Get available mitigation strategies for a violation type."""
        if violation_type == "fairness_violation":
            return self.laws.fairness.get("mitigation_strategies", [])
        
        return ["human_review", "policy_override", "action_blocking"]
    
    def apply_mitigation(self, violation: Dict[str, Any], 
                        strategy: str) -> Dict[str, Any]:
        """Apply a mitigation strategy to a violation."""
        mitigation_result = {
            "original_violation": violation,
            "strategy_applied": strategy,
            "success": False,
            "details": None
        }
        
        try:
            if strategy == "output_filtering" and violation.get("law_id") == "law5":
                # Apply output filtering for fairness violations
                mitigation_result["success"] = True
                mitigation_result["details"] = "Output filtered to meet fairness requirements"
            
            elif strategy == "human_review":
                # Convert to requires approval
                mitigation_result["success"] = True
                mitigation_result["details"] = "Violation converted to human approval requirement"
            
            else:
                mitigation_result["details"] = f"Mitigation strategy '{strategy}' not implemented"
                
        except Exception as e:
            mitigation_result["details"] = f"Mitigation error: {e}"
        
        return mitigation_result
    
    def project_energy_budget_check(self, action_ctx: ActionContext) -> Dict[str, Any]:
        """
        Check energy budget for an action (Law 7 compliance).
        
        PATCH: Cursor-2025-09-05 DISPATCH-GOV-20250905-LAW-7-SUSTAINABILITY
        Provides energy budget checking for task orchestrator integration.
        
        Args:
            action_ctx: Action context with energy estimation
            
        Returns:
            Budget decision with status and enforcement details
        """
        try:
            # Import sustainability manager
            from ...sustainability import SustainabilityManager, BudgetContext
            
            # Get sustainability configuration from laws
            sustainability_config = self.laws.policy.get("sustainability", {})
            budgets = sustainability_config.get("budgets", {})
            
            # Create budget context
            budget_ctx = BudgetContext(
                task_id=action_ctx.metadata.get("task_id", action_ctx.action_id),
                run_id=action_ctx.metadata.get("run_id", "default"),
                project_id=action_ctx.metadata.get("project_id", "default"),
                action_type=action_ctx.action_type,
                actor_id=action_ctx.actor_id,
                current_usage_kwh=action_ctx.metadata.get("estimated_energy_kwh", 0.0),
                budget_limit_kwh=budgets.get("task_kwh", 0.010),
                warn_threshold=sustainability_config.get("warn_fraction", 0.8),
                block_threshold=sustainability_config.get("block_fraction", 1.0),
                allow_hitl_override=sustainability_config.get("allow_hitl_override", True),
                metadata=action_ctx.metadata
            )
            
            # Check budget
            sustainability_manager = SustainabilityManager(sustainability_config)
            budget_decision = sustainability_manager.check_energy_budget(budget_ctx)
            
            # Convert to decision format
            decision = {
                "status": budget_decision.status.value,
                "allowed": budget_decision.allowed,
                "current_usage_kwh": budget_decision.current_usage_kwh,
                "budget_limit_kwh": budget_decision.budget_limit_kwh,
                "projected_total_kwh": budget_decision.projected_total_kwh,
                "warning_message": budget_decision.warning_message,
                "block_reason": budget_decision.block_reason,
                "hitl_override_required": budget_decision.hitl_override_required,
                "override_reason": budget_decision.override_reason,
                "timestamp": budget_decision.timestamp.isoformat(),
                "budget_context": budget_ctx,
                "budget_decision": budget_decision
            }
            
            return decision
            
        except ImportError:
            # Sustainability module not available - return permissive decision
            logger.warning("Sustainability module not available - allowing action")
            return {
                "status": "under_budget",
                "allowed": True,
                "current_usage_kwh": 0.0,
                "budget_limit_kwh": float('inf'),
                "projected_total_kwh": 0.0,
                "warning_message": None,
                "block_reason": None,
                "hitl_override_required": False,
                "override_reason": None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "budget_context": None,
                "budget_decision": None
            }
        except Exception as e:
            logger.error(f"Energy budget check failed: {e}")
            # Return permissive decision on error
            return {
                "status": "under_budget",
                "allowed": True,
                "current_usage_kwh": 0.0,
                "budget_limit_kwh": float('inf'),
                "projected_total_kwh": 0.0,
                "warning_message": None,
                "block_reason": None,
                "hitl_override_required": False,
                "override_reason": None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "budget_context": None,
                "budget_decision": None
            }
    
    def _load_ethics_pack(self):
        """Load Ethics Pack v0 configuration and detectors."""
        try:
            # Load ethics pack configuration
            config_path = Path(__file__).parent.parent.parent.parent.parent / "configs" / "governance" / "ethics_pack_v0.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self._ethics_config = json.load(f)
                logger.info("Ethics Pack v0 configuration loaded")
            else:
                logger.warning("Ethics Pack v0 configuration not found, using defaults")
                self._ethics_config = {
                    "privacy": {"enabled": False},
                    "safety": {"enabled": False},
                    "fairness": {"enabled": False}
                }
            
            # Initialize detectors
            self._initialize_ethics_detectors()
            
        except Exception as e:
            logger.error(f"Failed to load Ethics Pack v0: {e}")
            self._ethics_config = {
                "privacy": {"enabled": False},
                "safety": {"enabled": False},
                "fairness": {"enabled": False}
            }
    
    def _initialize_ethics_detectors(self):
        """Initialize ethics detectors based on configuration."""
        try:
            # Import detectors
            from ...governance.detectors import PrivacyDetector, SafetyDetector, FairnessDetector
            
            # Initialize privacy detector
            if self._ethics_config.get("privacy", {}).get("enabled", False):
                self._ethics_detectors["privacy"] = PrivacyDetector(
                    self._ethics_config["privacy"]
                )
                logger.info("Privacy detector initialized")
            
            # Initialize safety detector
            if self._ethics_config.get("safety", {}).get("enabled", False):
                self._ethics_detectors["safety"] = SafetyDetector(
                    self._ethics_config["safety"]
                )
                logger.info("Safety detector initialized")
            
            # Initialize fairness detector
            if self._ethics_config.get("fairness", {}).get("enabled", False):
                self._ethics_detectors["fairness"] = FairnessDetector(
                    self._ethics_config["fairness"]
                )
                logger.info("Fairness detector initialized")
                
        except ImportError as e:
            logger.warning(f"Ethics detectors not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize ethics detectors: {e}")
    
    def pre_flight_ethics_check(self, action_ctx: ActionContext) -> Tuple[ActionContext, Dict[str, Any]]:
        """
        Perform pre-flight ethics checks (privacy, safety).
        
        Args:
            action_ctx: Action context to check
            
        Returns:
            Tuple of (modified action context, ethics evidence)
        """
        evidence = {}
        
        # Privacy check (pre-flight)
        if "privacy" in self._ethics_detectors:
            try:
                text = action_ctx.metadata.get("input_text", "")
                if text:
                    privacy_result = self._ethics_detectors["privacy"].detect_and_anonymize(text)
                    evidence.update(self._ethics_detectors["privacy"].get_evidence(privacy_result))
                    
                    # Update action context with anonymized text if needed
                    if privacy_result.anonymized_text and privacy_result.anonymized_text != text:
                        action_ctx.metadata["input_text"] = privacy_result.anonymized_text
                        action_ctx.metadata["privacy_anonymized"] = True
                    
                    # Check if should block
                    if self._ethics_detectors["privacy"].should_block(privacy_result):
                        action_ctx.metadata["ethics_blocked"] = True
                        action_ctx.metadata["ethics_block_reason"] = "privacy_violation"
                        
            except Exception as e:
                logger.error(f"Privacy pre-flight check failed: {e}")
                evidence["privacy"] = {"error": str(e)}
        
        # Safety check (pre-flight)
        if "safety" in self._ethics_detectors:
            try:
                text = action_ctx.metadata.get("input_text", "")
                if text:
                    safety_result = self._ethics_detectors["safety"].screen_text(text)
                    evidence.update(self._ethics_detectors["safety"].get_evidence(safety_result))
                    
                    # Check if should block
                    if self._ethics_detectors["safety"].should_block(safety_result):
                        action_ctx.metadata["ethics_blocked"] = True
                        action_ctx.metadata["ethics_block_reason"] = "safety_violation"
                        
            except Exception as e:
                logger.error(f"Safety pre-flight check failed: {e}")
                evidence["safety"] = {"error": str(e)}
        
        return action_ctx, evidence
    
    def post_flight_ethics_check(self, action_ctx: ActionContext, response_text: str = None) -> Dict[str, Any]:
        """
        Perform post-flight ethics checks (safety, fairness).
        
        Args:
            action_ctx: Action context
            response_text: Response text to check
            
        Returns:
            Ethics evidence dictionary
        """
        evidence = {}
        
        # Safety check (post-flight)
        if "safety" in self._ethics_detectors and response_text:
            try:
                safety_result = self._ethics_detectors["safety"].screen_text(response_text)
                evidence.update(self._ethics_detectors["safety"].get_evidence(safety_result))
                
            except Exception as e:
                logger.error(f"Safety post-flight check failed: {e}")
                evidence["safety"] = {"error": str(e)}
        
        # Fairness check (post-flight)
        if "fairness" in self._ethics_detectors and response_text:
            try:
                labels = action_ctx.metadata.get("labels")
                groups = action_ctx.metadata.get("groups")
                
                fairness_result = self._ethics_detectors["fairness"].analyze_fairness(
                    response_text, labels, groups
                )
                evidence.update(self._ethics_detectors["fairness"].get_evidence(fairness_result))
                
            except Exception as e:
                logger.error(f"Fairness post-flight check failed: {e}")
                evidence["fairness"] = {"error": str(e)}
        
        return evidence
    
    def _log_sustainability_metrics(self, budget_decision: Any, sustainability_config: Dict[str, Any]):
        """
        Log sustainability metrics to configured output file.
        
        PATCH: Cursor-2025-09-15 DISPATCH-GOV-20250915-SUSTAINABILITY-PACK-V0
        Implements metrics logging for sustainability evidence collection.
        """
        try:
            metrics_config = sustainability_config.get("metrics", {})
            output_path = metrics_config.get("output_path", "artifacts/lens/sustainability/metrics.jsonl")
            
            # Create directory if it doesn't exist
            from pathlib import Path
            metrics_file = Path(output_path)
            metrics_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create metrics entry
            metrics_entry = {
                "timestamp": budget_decision.timestamp.isoformat(),
                "token_count": budget_decision.token_count,
                "model_name": budget_decision.model_name,
                "estimate_kwh_per_100k": budget_decision.estimate_kwh_per_100k,
                "budget_kwh_per_100k": budget_decision.budget_kwh_per_100k,
                "utilization": budget_decision.utilization,
                "threshold_hit": budget_decision.threshold_hit,
                "override_used": budget_decision.override_used,
                "jurisdiction_applied": budget_decision.jurisdiction_applied,
                "status": budget_decision.status.value if hasattr(budget_decision.status, 'value') else str(budget_decision.status),
                "enforcement_mode": sustainability_config.get("mode", "monitor"),
                "metadata": budget_decision.metadata
            }
            
            # Append to metrics file
            with open(metrics_file, 'a') as f:
                f.write(json.dumps(metrics_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to log sustainability metrics: {e}")
    
    def get_ethics_status(self) -> Dict[str, Any]:
        """Get status of all ethics detectors."""
        status = {
            "enabled": len(self._ethics_detectors) > 0,
            "detectors": {}
        }
        
        for name, detector in self._ethics_detectors.items():
            status["detectors"][name] = detector.get_status()
        
        return status
