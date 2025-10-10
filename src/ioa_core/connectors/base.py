# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.



import uuid
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
"""Base module."""

from typing import Dict, Any, Optional, List, Callable

from ..governance.policy_engine import PolicyEngine, ActionContext, ValidationStatus, ActionRiskLevel
from ..governance.system_laws import SystemLawsError

logger = logging.getLogger(__name__)


@dataclass
class ConnectorCapabilities:
    """Capabilities and constraints of a connector."""
    name: str
    supported_actions: List[str] = field(default_factory=list)
    data_classifications: List[str] = field(default_factory=list)
    jurisdictions: List[str] = field(default_factory=list)
    rate_limits: Dict[str, Any] = field(default_factory=dict)
    security_clearance: str = "standard"
    audit_required: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectorContext:
    """Context for connector execution with System Laws awareness."""
    connector_id: str
    action_type: str
    actor_id: str
    target_entity: Optional[str] = None
    data_classification: Optional[str] = None
    jurisdiction: Optional[str] = None
    risk_level: ActionRiskLevel = ActionRiskLevel.LOW
    audit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConnectorBase(ABC):
    """Base class for all IOA connectors with System Laws enforcement."""
    
    def __init__(self, connector_id: str, capabilities: ConnectorCapabilities):
        self.connector_id = connector_id
        self.capabilities = capabilities
        self.policy_engine = PolicyEngine()
        
        # Register policy event handler
        self.policy_engine.register_policy_event_handler(self._handle_policy_event)
        
        logger.info(f"Connector {connector_id} initialized with capabilities: {capabilities.name}")
    
    def _handle_policy_event(self, event: Dict[str, Any]):
        """Handle policy events from the policy engine."""
        logger.info(f"Connector {self.connector_id} received policy event: {event['event_type']}")
        
        # Log policy events for audit purposes
        if event["event_type"] == "action_validated":
            self._log_policy_decision(event["data"])
    
    def _log_policy_decision(self, decision_data: Dict[str, Any]):
        """Log policy decisions for audit purposes."""
        logger.info(
            f"Policy decision for action {decision_data['action_id']}: "
            f"{decision_data['status']} (audit_id: {decision_data['audit_id']})"
        )
    
    def validate_connector_caps(self, laws_ctx: ConnectorContext) -> 'ValidationResult':
        """Validate connector capabilities against System Laws."""
        # Create action context for policy validation
        action_ctx = ActionContext(
            action_id=laws_ctx.audit_id,
            action_type=laws_ctx.action_type,
            actor_id=laws_ctx.actor_id,
            target_entity=laws_ctx.target_entity,
            data_classification=laws_ctx.data_classification,
            jurisdiction=laws_ctx.jurisdiction,
            risk_level=laws_ctx.risk_level,
            metadata=laws_ctx.metadata
        )
        
        # Validate against System Laws
        validation_result = self.policy_engine.validate_against_laws(action_ctx)
        
        # Additional connector-specific validation
        connector_validation = self._validate_connector_specific_rules(laws_ctx)
        
        if connector_validation:
            validation_result.metadata["connector_validation"] = connector_validation
            
            # Check if connector validation failed and override status if needed
            if not connector_validation["capability_check"] or not connector_validation["security_check"]:
                validation_result.status = ValidationStatus.BLOCKED
            elif not connector_validation["rate_limit_check"]:
                # Rate limit violations might just require approval
                if validation_result.status == ValidationStatus.APPROVED:
                    validation_result.status = ValidationStatus.REQUIRES_APPROVAL
        
        return validation_result
    
    def _validate_connector_specific_rules(self, ctx: ConnectorContext) -> Optional[Dict[str, Any]]:
        """Validate connector-specific rules and constraints."""
        validation_result = {
            "capability_check": True,
            "rate_limit_check": True,
            "security_check": True,
            "details": []
        }
        
        # Check if action is supported
        if ctx.action_type not in self.capabilities.supported_actions:
            validation_result["capability_check"] = False
            validation_result["details"].append(f"Action type '{ctx.action_type}' not supported")
        
        # Check data classification compatibility
        if (ctx.data_classification and 
            ctx.data_classification not in self.capabilities.data_classifications):
            validation_result["capability_check"] = False
            validation_result["details"].append(
                f"Data classification '{ctx.data_classification}' not supported"
            )
        
        # Check jurisdiction compatibility
        if (ctx.jurisdiction and 
            ctx.jurisdiction not in self.capabilities.jurisdictions):
            validation_result["capability_check"] = False
            validation_result["details"].append(
                f"Jurisdiction '{ctx.jurisdiction}' not supported"
            )
        
        # Check rate limits
        if self.capabilities.rate_limits:
            rate_check = self._check_rate_limits(ctx)
            if not rate_check["allowed"]:
                validation_result["rate_limit_check"] = False
                validation_result["details"].append(rate_check["reason"])
        
        # Check security clearance
        if ctx.risk_level == ActionRiskLevel.CRITICAL:
            if self.capabilities.security_clearance != "high":
                validation_result["security_check"] = False
                validation_result["details"].append(
                    f"Critical risk actions require high security clearance"
                )
        
        return validation_result
    
    def _check_rate_limits(self, ctx: ConnectorContext) -> Dict[str, Any]:
        """Check if the action is within rate limits."""
        # This is a simplified rate limit check
        # In practice, this would use a proper rate limiting system
        
        current_time = datetime.now(timezone.utc)
        action_key = f"{ctx.actor_id}:{ctx.action_type}"
        
        # Get current usage from metadata or external rate limiter
        current_usage = ctx.metadata.get("rate_limit_usage", {})
        
        if action_key in current_usage:
            last_action_time = current_usage[action_key].get("last_action")
            action_count = current_usage[action_key].get("count", 0)
            
            # Check if within time window
            if last_action_time:
                time_diff = (current_time - last_action_time).total_seconds()
                if time_diff < 60:  # 1 minute window
                    if action_count >= 10:  # 10 actions per minute limit
                        return {
                            "allowed": False,
                            "reason": "Rate limit exceeded: 10 actions per minute"
                        }
        
        return {"allowed": True}
    
    def execute_with_laws(self, action_type: str, actor_id: str, 
                         **kwargs) -> Dict[str, Any]:
        """Execute connector action with System Laws validation."""
        # Create connector context
        ctx = ConnectorContext(
            connector_id=self.connector_id,
            action_type=action_type,
            actor_id=actor_id,
            target_entity=kwargs.get("target_entity"),
            data_classification=kwargs.get("data_classification"),
            jurisdiction=kwargs.get("jurisdiction"),
            risk_level=kwargs.get("risk_level", ActionRiskLevel.LOW),
            metadata=kwargs
        )
        
        # Validate against System Laws
        validation_result = self.validate_connector_caps(ctx)
        
        if validation_result.status.value == "blocked":
            raise SystemLawsError(
                f"Action blocked by System Laws: {validation_result.violations}",
                context={"validation_result": validation_result.__dict__}
            )
        
        if validation_result.status.value == "requires_approval":
            # Create HITL ticket
            hitl_ticket = self._create_hitl_ticket(ctx, validation_result)
            raise SystemLawsError(
                f"Action requires human approval. HITL ticket: {hitl_ticket['ticket_id']}",
                context={"hitl_ticket": hitl_ticket, "validation_result": validation_result.__dict__}
            )
        
        # Execute the action
        try:
            result = self._execute_action(action_type, ctx, **kwargs)
            
            # Add audit information
            result["audit_id"] = ctx.audit_id
            result["policy_validation"] = validation_result.__dict__
            result["timestamp"] = ctx.timestamp.isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Connector execution error: {e}")
            raise
    
    def _create_hitl_ticket(self, ctx: ConnectorContext, 
                           validation_result: 'ValidationResult') -> Dict[str, Any]:
        """Create a Human-in-the-Loop ticket for approval."""
        ticket_id = str(uuid.uuid4())
        
        ticket = {
            "ticket_id": ticket_id,
            "connector_id": self.connector_id,
            "action_type": ctx.action_type,
            "actor_id": ctx.actor_id,
            "required_approvals": validation_result.required_approvals,
            "risk_level": ctx.risk_level.value,
            "created_at": ctx.timestamp.isoformat(),
            "status": "pending",
            "audit_id": ctx.audit_id
        }
        
        # In practice, this would be stored in a database or queue
        logger.info(f"Created HITL ticket {ticket_id} for action {ctx.action_type}")
        
        return ticket
    
    @abstractmethod
    def _execute_action(self, action_type: str, ctx: ConnectorContext, 
                       **kwargs) -> Dict[str, Any]:
        """Execute the actual connector action. Must be implemented by subclasses."""
        pass
    
    def get_capabilities(self) -> ConnectorCapabilities:
        """Get the connector's capabilities."""
        return self.capabilities
    
    def update_capabilities(self, new_capabilities: ConnectorCapabilities):
        """Update connector capabilities (requires revalidation)."""
        # Validate new capabilities against System Laws
        validation_ctx = ConnectorContext(
            connector_id=self.connector_id,
            action_type="capability_update",
            actor_id="system",
            risk_level=ActionRiskLevel.MEDIUM
        )
        
        # Check if update is allowed
        validation_result = self.validate_connector_caps(validation_ctx)
        
        if validation_result.status.value == "blocked":
            raise SystemLawsError(
                "Capability update blocked by System Laws",
                context={"validation_result": validation_result.__dict__}
            )
        
        self.capabilities = new_capabilities
        logger.info(f"Updated capabilities for connector {self.connector_id}")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the connector."""
        return {
            "connector_id": self.connector_id,
            "status": "healthy",
            "capabilities": self.capabilities.__dict__,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
