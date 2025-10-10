""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""

PATCH: Cursor-2025-09-05 DISPATCH-EXEC-20250905-CONNECTOR-10K-TEST-&-PATCHES
- Added connector audit hooks for policy enforcement
- Added WASM sandbox stub for LocalOps execution security
- Integrated with PolicyEngine for System Laws compliance
"""

import logging
import uuid
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# IOA imports
from .ioa.core.governance.policy_engine import PolicyEngine, ActionContext, ValidationStatus, ActionRiskLevel
from .ioa.connectors.base import ConnectorBase, ConnectorContext

# PATCH: Cursor-2025-09-05 DISPATCH-GOV-20250905-LAW-7-SUSTAINABILITY
# Add sustainability integration
try:
    from .sustainability import SustainabilityManager, BudgetContext
    SUSTAINABILITY_AVAILABLE = True
except ImportError:
    SUSTAINABILITY_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class TaskContext:
    """Context for task execution with audit and compliance tracking."""
    task_id: str
    task_type: str
    connector_id: str
    actor_id: str
    target_entity: Optional[str] = None
    data_classification: Optional[str] = None
    jurisdiction: Optional[str] = None
    risk_level: ActionRiskLevel = ActionRiskLevel.LOW
    audit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # PATCH: Cursor-2025-09-05 DISPATCH-GOV-20250905-LAW-7-SUSTAINABILITY
    # Add sustainability fields
    project_id: str = "default"
    run_id: str = "default"
    estimated_energy_kwh: float = 0.0


@dataclass
class TaskResult:
    """Result of task execution with audit trail."""
    task_id: str
    success: bool
    result_data: Optional[Dict[str, Any]] = None
    execution_time_ms: float = 0.0
    audit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    compliance_checks: List[Dict[str, Any]] = field(default_factory=list)
    sandbox_events: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # PATCH: Cursor-2025-09-05 DISPATCH-GOV-20250905-LAW-7-SUSTAINABILITY
    # Add sustainability fields
    energy_kwh: float = 0.0
    energy_kwh_projected: float = 0.0
    co2e_g: float = 0.0
    budget_id: str = "default"
    budget_limit_kwh: float = 0.0
    sustainability_decision: str = "ALLOW"


class WASMSandbox:
    """
    WASM sandbox stub for LocalOps execution security.
    
    PATCH: Cursor-2025-09-05 DISPATCH-EXEC-20250905-CONNECTOR-10K-TEST-&-PATCHES
    Provides secure execution environment for untrusted LocalOps code.
    """
    
    def __init__(self, sandbox_config: Optional[Dict[str, Any]] = None):
        self.config = sandbox_config or {}
        self.is_active = True
        self.execution_count = 0
        self.blocked_operations = 0
        
        # Sandbox security policies
        self.allowed_operations = {
            "file_read": ["logs", "config", "public_data"],
            "network": ["localhost", "127.0.0.1"],
            "system": ["env_read", "time_read"],
            "blocked": ["file_write", "network_outbound", "system_exec"]
        }
        
        logger.info("WASM Sandbox initialized with security policies")
    
    def execute_wasm(self, wasm_bytes: bytes, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute WASM code in sandboxed environment.
        
        Args:
            wasm_bytes: Compiled WASM bytecode
            input_data: Input data for execution
            
        Returns:
            Execution result with security audit trail
        """
        if not self.is_active:
            raise RuntimeError("WASM sandbox is not active")
        
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"Executing WASM code in sandbox: {execution_id}")
        
        try:
            # PATCH: Cursor-2025-09-05 DISPATCH-EXEC-20250905-CONNECTOR-10K-TEST-&-PATCHES
            # Validate WASM code against security policies
            security_check = self._validate_wasm_security(wasm_bytes, input_data)
            
            if not security_check["allowed"]:
                self.blocked_operations += 1
                raise SecurityError(f"WASM execution blocked: {security_check['reason']}")
            
            # Simulate WASM execution (in production, this would use a real WASM runtime)
            execution_result = self._simulate_wasm_execution(wasm_bytes, input_data)
            
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Log successful execution
            self.execution_count += 1
            logger.info(f"WASM execution completed: {execution_id} in {execution_time:.2f}ms")
            
            return {
                "execution_id": execution_id,
                "success": True,
                "result": execution_result,
                "execution_time_ms": execution_time,
                "security_checks": security_check,
                "sandbox_events": self._get_sandbox_events()
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"WASM execution failed: {execution_id} - {e}")
            
            return {
                "execution_id": execution_id,
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time,
                "security_checks": security_check if 'security_check' in locals() else {},
                "sandbox_events": self._get_sandbox_events()
            }
    
    def _validate_wasm_security(self, wasm_bytes: bytes, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate WASM code against security policies."""
        # PATCH: Cursor-2025-09-05 DISPATCH-EXEC-20250905-CONNECTOR-10K-TEST-&-PATCHES
        # Basic security validation (in production, this would be more sophisticated)
        
        security_check = {
            "allowed": True,
            "reason": None,
            "checks_performed": []
        }
        
        # Check WASM bytecode size (prevent oversized payloads)
        if len(wasm_bytes) > 1024 * 1024:  # 1MB limit
            security_check["allowed"] = False
            security_check["reason"] = "WASM bytecode exceeds size limit"
            security_check["checks_performed"].append("size_check")
            return security_check
        
        # Check for suspicious patterns in input data
        if "system_exec" in str(input_data).lower():
            security_check["allowed"] = False
            security_check["reason"] = "Input data contains blocked operations"
            security_check["checks_performed"].append("input_validation")
            return security_check
        
        # Check for network operations
        if "network" in str(input_data).lower():
            security_check["checks_performed"].append("network_restriction")
        
        # Check for file operations
        if "file" in str(input_data).lower():
            security_check["checks_performed"].append("file_restriction")
        
        security_check["checks_performed"].append("basic_validation")
        return security_check
    
    def _simulate_wasm_execution(self, wasm_bytes: bytes, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate WASM execution for testing purposes."""
        # This is a stub implementation for testing
        # In production, this would use a real WASM runtime like wasmtime
        
        # Simulate processing time
        time.sleep(0.001)  # 1ms simulation
        
        # Return mock result
        return {
            "processed_data": input_data,
            "wasm_size": len(wasm_bytes),
            "simulation_mode": True
        }
    
    def _get_sandbox_events(self) -> List[Dict[str, Any]]:
        """Get current sandbox event log."""
        return [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "execution_count": self.execution_count,
                "blocked_operations": self.blocked_operations,
                "sandbox_active": self.is_active
            }
        ]
    
    def deactivate(self):
        """Deactivate the sandbox for maintenance."""
        self.is_active = False
        logger.warning("WASM sandbox deactivated")
    
    def activate(self):
        """Reactivate the sandbox."""
        self.is_active = True
        logger.info("WASM sandbox reactivated")
    
    def get_sandbox_stats(self) -> Dict[str, Any]:
        """Get sandbox statistics and health metrics."""
        return {
            "active": self.is_active,
            "execution_count": self.execution_count,
            "blocked_operations": self.blocked_operations,
            "security_policies": self.allowed_operations,
            "last_activity": datetime.now(timezone.utc).isoformat()
        }


class SecurityError(Exception):
    """Security violation in sandboxed execution."""
    pass


class TaskOrchestrator:
    """
    Task orchestrator with connector audit hooks and WASM sandbox integration.
    
    PATCH: Cursor-2025-09-05 DISPATCH-EXEC-20250905-CONNECTOR-10K-TEST-&-PATCHES
    Provides secure task execution with System Laws compliance and LocalOps sandboxing.
    """
    
    def __init__(self, policy_engine: Optional[PolicyEngine] = None):
        self.policy_engine = policy_engine or PolicyEngine()
        self.wasm_sandbox = WASMSandbox()
        
        # Task execution tracking
        self.executed_tasks: Dict[str, TaskResult] = {}
        self.connector_audit_log: List[Dict[str, Any]] = []
        
        # PATCH: Cursor-2025-09-05 DISPATCH-GOV-20250905-LAW-7-SUSTAINABILITY
        # Initialize sustainability manager if available
        self.sustainability_manager = None
        if SUSTAINABILITY_AVAILABLE:
            try:
                from .sustainability import SustainabilityManager
                self.sustainability_manager = SustainabilityManager()
                logger.info("Sustainability Manager initialized for Law 7 compliance")
            except Exception as e:
                logger.warning(f"Failed to initialize Sustainability Manager: {e}")
        
        # Register policy event handlers
        self.policy_engine.register_policy_event_handler(self._handle_policy_event)
        
        logger.info("Task Orchestrator initialized with audit hooks, WASM sandbox, and sustainability integration")
    
    def _handle_policy_event(self, event: Dict[str, Any]):
        """Handle policy events from the policy engine."""
        logger.info(f"Task Orchestrator received policy event: {event['event_type']}")
        
        # Log policy events for audit purposes
        if event["event_type"] == "action_validated":
            self._log_policy_decision(event["data"])
    
    def _log_policy_decision(self, decision_data: Dict[str, Any]):
        """Log policy decisions for audit purposes."""
        logger.info(
            f"Policy decision for action {decision_data['action_id']}: "
            f"{decision_data['status']} (audit_id: {decision_data['audit_id']})"
        )
        
        # Store in connector audit log
        self.connector_audit_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "policy_decision",
            "data": decision_data
        })
    
    def execute_connector_task(self, connector: ConnectorBase, 
                              task_ctx: TaskContext) -> TaskResult:
        """
        Execute a task through a connector with full audit and compliance tracking.
        
        PATCH: Cursor-2025-09-05 DISPATCH-EXEC-20250905-CONNECTOR-10K-TEST-&-PATCHES
        Implements connector audit hooks and policy enforcement.
        
        Args:
            connector: Connector instance to execute the task
            task_ctx: Task context with audit and compliance information
            
        Returns:
            TaskResult with execution details and audit trail
        """
        start_time = time.time()
        
        logger.info(f"Executing connector task: {task_ctx.task_id} via {task_ctx.connector_id}")
        
        # PATCH: Cursor-2025-09-05 DISPATCH-EXEC-20250905-CONNECTOR-10K-TEST-&-PATCHES
        # Step 1: Pre-execution compliance check
        compliance_result = self._check_pre_execution_compliance(connector, task_ctx)
        
        # PATCH: Cursor-2025-09-05 DISPATCH-GOV-20250905-LAW-7-SUSTAINABILITY
        # Step 1.5: Energy budget check
        energy_budget_result = self._check_energy_budget(task_ctx)
        if not energy_budget_result["allowed"]:
            execution_time = (time.time() - start_time) * 1000
            return TaskResult(
                task_id=task_ctx.task_id,
                success=False,
                execution_time_ms=execution_time,
                audit_id=task_ctx.audit_id,
                compliance_checks=[compliance_result, energy_budget_result],
                metadata={"blocked_reason": energy_budget_result["block_reason"]},
                energy_kwh=task_ctx.estimated_energy_kwh,
                energy_kwh_projected=energy_budget_result.get("projected_total_kwh", 0.0),
                budget_limit_kwh=energy_budget_result.get("budget_limit_kwh", 0.0),
                sustainability_decision="BLOCK"
            )
        
        if not compliance_result["allowed"]:
            execution_time = (time.time() - start_time) * 1000
            return TaskResult(
                task_id=task_ctx.task_id,
                success=False,
                execution_time_ms=execution_time,
                audit_id=task_ctx.audit_id,
                compliance_checks=[compliance_result, energy_budget_result],
                metadata={"blocked_reason": compliance_result["reason"]},
                energy_kwh=task_ctx.estimated_energy_kwh,
                energy_kwh_projected=energy_budget_result.get("projected_total_kwh", 0.0),
                budget_limit_kwh=energy_budget_result.get("budget_limit_kwh", 0.0),
                sustainability_decision="BLOCK"
            )
        
        # Step 2: Execute task with audit hooks
        try:
            # Create connector context for execution
            connector_ctx = ConnectorContext(
                connector_id=task_ctx.connector_id,
                action_type=task_ctx.task_type,
                actor_id=task_ctx.actor_id,
                target_entity=task_ctx.target_entity,
                data_classification=task_ctx.data_classification,
                jurisdiction=task_ctx.jurisdiction,
                risk_level=task_ctx.risk_level,
                audit_id=task_ctx.audit_id,
                metadata=task_ctx.metadata
            )
            
            # Execute task through connector
            execution_result = connector.execute_with_laws(connector_ctx)
            
            execution_time = (time.time() - start_time) * 1000
            
            # Step 3: Post-execution compliance validation
            post_compliance = self._check_post_execution_compliance(execution_result, task_ctx)
            
            # Create task result
            task_result = TaskResult(
                task_id=task_ctx.task_id,
                success=execution_result.get("success", False),
                result_data=execution_result.get("result", {}),
                execution_time_ms=execution_time,
                audit_id=task_ctx.audit_id,
                compliance_checks=[compliance_result, post_compliance],
                timestamp=datetime.now(timezone.utc),
                metadata={
                    "connector_id": task_ctx.connector_id,
                    "execution_result": execution_result
                },
                # PATCH: Cursor-2025-09-05 DISPATCH-GOV-20250905-LAW-7-SUSTAINABILITY
                # Add sustainability fields
                energy_kwh=task_ctx.estimated_energy_kwh,
                energy_kwh_projected=energy_budget_result.get("projected_total_kwh", 0.0),
                budget_limit_kwh=energy_budget_result.get("budget_limit_kwh", 0.0),
                sustainability_decision="ALLOW"
            )
            
            # Store result and log success
            self.executed_tasks[task_ctx.task_id] = task_result
            self._log_task_execution(task_ctx, task_result, "success")
            
            # PATCH: Cursor-2025-09-05 DISPATCH-GOV-20250905-LAW-7-SUSTAINABILITY
            # Record energy usage for sustainability tracking
            self._record_energy_usage(task_ctx, task_result)
            
            logger.info(f"Connector task completed: {task_ctx.task_id} in {execution_time:.2f}ms")
            
            return task_result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            # Log execution failure
            self._log_task_execution(task_ctx, None, "failure", str(e))
            
            logger.error(f"Connector task failed: {task_ctx.task_id} - {e}")
            
            return TaskResult(
                task_id=task_ctx.task_id,
                success=False,
                execution_time_ms=execution_time,
                audit_id=task_ctx.audit_id,
                compliance_checks=[compliance_result],
                metadata={"error": str(e)}
            )
    
    def execute_localops_task(self, wasm_code: bytes, task_ctx: TaskContext) -> TaskResult:
        """
        Execute a LocalOps task using WASM sandbox.
        
        PATCH: Cursor-2025-09-05 DISPATCH-EXEC-20250905-CONNECTOR-10K-TEST-&-PATCHES
        Provides secure LocalOps execution with WASM sandboxing.
        
        Args:
            wasm_code: Compiled WASM bytecode for LocalOps execution
            task_ctx: Task context with audit information
            
        Returns:
            TaskResult with execution details and sandbox events
        """
        start_time = time.time()
        
        logger.info(f"Executing LocalOps task: {task_ctx.task_id} via WASM sandbox")
        
        try:
            # Execute in WASM sandbox
            sandbox_result = self.wasm_sandbox.execute_wasm(wasm_code, {
                "task_id": task_ctx.task_id,
                "input_data": task_ctx.metadata.get("input_data", {}),
                "execution_context": {
                    "actor_id": task_ctx.actor_id,
                    "timestamp": task_ctx.timestamp.isoformat()
                }
            })
            
            execution_time = (time.time() - start_time) * 1000
            
            # Create task result
            task_result = TaskResult(
                task_id=task_ctx.task_id,
                success=sandbox_result["success"],
                result_data=sandbox_result.get("result", {}),
                execution_time_ms=execution_time,
                audit_id=task_ctx.audit_id,
                sandbox_events=sandbox_result.get("sandbox_events", []),
                timestamp=datetime.now(timezone.utc),
                metadata={
                    "execution_mode": "localops_wasm",
                    "sandbox_result": sandbox_result
                }
            )
            
            # Store result and log
            self.executed_tasks[task_ctx.task_id] = task_result
            self._log_task_execution(task_ctx, task_result, "localops_success")
            
            logger.info(f"LocalOps task completed: {task_ctx.task_id} in {execution_time:.2f}ms")
            
            return task_result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            # Log execution failure
            self._log_task_execution(task_ctx, None, "localops_failure", str(e))
            
            logger.error(f"LocalOps task failed: {task_ctx.task_id} - {e}")
            
            return TaskResult(
                task_id=task_ctx.task_id,
                success=False,
                execution_time_ms=execution_time,
                audit_id=task_ctx.audit_id,
                metadata={"error": str(e), "execution_mode": "localops_wasm"}
            )
    
    def _check_pre_execution_compliance(self, connector: ConnectorBase, 
                                       task_ctx: TaskContext) -> Dict[str, Any]:
        """Check compliance before task execution."""
        try:
            # Create action context for policy validation
            action_ctx = ActionContext(
                action_id=task_ctx.audit_id,
                action_type=task_ctx.task_type,
                actor_id=task_ctx.actor_id,
                target_entity=task_ctx.target_entity,
                data_classification=task_ctx.data_classification,
                jurisdiction=task_ctx.jurisdiction,
                risk_level=task_ctx.risk_level,
                metadata=task_ctx.metadata
            )
            
            # Validate against System Laws
            validation_result = self.policy_engine.validate_against_laws(action_ctx)
            
            # Check connector capabilities
            connector_validation = connector.validate_connector_caps(
                ConnectorContext(
                    connector_id=task_ctx.connector_id,
                    action_type=task_ctx.task_type,
                    actor_id=task_ctx.actor_id,
                    target_entity=task_ctx.target_entity,
                    data_classification=task_ctx.data_classification,
                    jurisdiction=task_ctx.jurisdiction,
                    risk_level=task_ctx.risk_level,
                    audit_id=task_ctx.audit_id,
                    metadata=task_ctx.metadata
                )
            )
            
            compliance_result = {
                "allowed": validation_result.status == ValidationStatus.APPROVED,
                "reason": None,
                "policy_validation": validation_result,
                "connector_validation": connector_validation,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            if not compliance_result["allowed"]:
                if validation_result.status == ValidationStatus.BLOCKED:
                    compliance_result["reason"] = "Policy violation blocked execution"
                elif validation_result.status == ValidationStatus.REQUIRES_APPROVAL:
                    compliance_result["reason"] = "Human approval required"
                else:
                    compliance_result["reason"] = "Compliance check failed"
            
            return compliance_result
            
        except Exception as e:
            logger.error(f"Pre-execution compliance check failed: {e}")
            return {
                "allowed": False,
                "reason": f"Compliance check error: {e}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _check_post_execution_compliance(self, execution_result: Dict[str, Any], 
                                        task_ctx: TaskContext) -> Dict[str, Any]:
        """Check compliance after task execution."""
        try:
            # Post-execution validation
            post_compliance = {
                "check_type": "post_execution",
                "allowed": True,
                "reason": None,
                "execution_verified": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Verify execution result integrity
            if not execution_result.get("success", False):
                post_compliance["execution_verified"] = False
                post_compliance["reason"] = "Task execution failed"
            
            # Check for any policy violations in results
            if "policy_violation" in execution_result:
                post_compliance["allowed"] = False
                post_compliance["reason"] = "Policy violations detected in results"
            
            return post_compliance
            
        except Exception as e:
            logger.error(f"Post-execution compliance check failed: {e}")
            return {
                "check_type": "post_execution",
                "allowed": False,
                "reason": f"Post-execution check error: {e}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _check_energy_budget(self, task_ctx: TaskContext) -> Dict[str, Any]:
        """
        Check energy budget for a task (Law 7 compliance).
        
        PATCH: Cursor-2025-09-05 DISPATCH-GOV-20250905-LAW-7-SUSTAINABILITY
        Implements energy budget checking using policy engine.
        """
        try:
            if not self.sustainability_manager:
                # Fallback to policy engine
                action_ctx = ActionContext(
                    action_id=task_ctx.audit_id,
                    action_type=task_ctx.task_type,
                    actor_id=task_ctx.actor_id,
                    target_entity=task_ctx.target_entity,
                    data_classification=task_ctx.data_classification,
                    jurisdiction=task_ctx.jurisdiction,
                    risk_level=task_ctx.risk_level,
                    metadata={
                        "task_id": task_ctx.task_id,
                        "run_id": task_ctx.run_id,
                        "project_id": task_ctx.project_id,
                        "estimated_energy_kwh": task_ctx.estimated_energy_kwh
                    }
                )
                
                budget_decision = self.policy_engine.project_energy_budget_check(action_ctx)
                return budget_decision
            
            # Use sustainability manager directly
            budget_ctx = BudgetContext(
                task_id=task_ctx.task_id,
                run_id=task_ctx.run_id,
                project_id=task_ctx.project_id,
                action_type=task_ctx.task_type,
                actor_id=task_ctx.actor_id,
                current_usage_kwh=task_ctx.estimated_energy_kwh,
                metadata=task_ctx.metadata
            )
            
            budget_decision = self.sustainability_manager.check_energy_budget(budget_ctx)
            
            return {
                "allowed": budget_decision.allowed,
                "status": budget_decision.status.value,
                "current_usage_kwh": budget_decision.current_usage_kwh,
                "budget_limit_kwh": budget_decision.budget_limit_kwh,
                "projected_total_kwh": budget_decision.projected_total_kwh,
                "warning_message": budget_decision.warning_message,
                "block_reason": budget_decision.block_reason,
                "hitl_override_required": budget_decision.hitl_override_required,
                "override_reason": budget_decision.override_reason,
                "timestamp": budget_decision.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Energy budget check failed: {e}")
            # Return permissive decision on error
            return {
                "allowed": True,
                "status": "under_budget",
                "current_usage_kwh": 0.0,
                "budget_limit_kwh": float('inf'),
                "projected_total_kwh": task_ctx.estimated_energy_kwh,
                "warning_message": None,
                "block_reason": None,
                "hitl_override_required": False,
                "override_reason": None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _record_energy_usage(self, task_ctx: TaskContext, task_result: TaskResult):
        """
        Record energy usage for sustainability tracking.
        
        PATCH: Cursor-2025-09-05 DISPATCH-GOV-20250905-LAW-7-SUSTAINABILITY
        Records actual energy usage for budget management.
        """
        try:
            if not self.sustainability_manager:
                return
            
            # Create budget context for recording
            budget_ctx = BudgetContext(
                task_id=task_ctx.task_id,
                run_id=task_ctx.run_id,
                project_id=task_ctx.project_id,
                action_type=task_ctx.task_type,
                actor_id=task_ctx.actor_id,
                current_usage_kwh=task_result.energy_kwh,
                metadata=task_ctx.metadata
            )
            
            # Record actual energy usage
            self.sustainability_manager.record_energy_usage(budget_ctx, task_result.energy_kwh)
            
            logger.debug(f"Recorded energy usage: {task_result.energy_kwh:.6f} kWh for task {task_ctx.task_id}")
            
        except Exception as e:
            logger.error(f"Failed to record energy usage: {e}")
    
    def _log_task_execution(self, task_ctx: TaskContext, task_result: Optional[TaskResult], 
                           status: str, error: Optional[str] = None):
        """Log task execution for audit purposes."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task_ctx.task_id,
            "connector_id": task_ctx.connector_id,
            "actor_id": task_ctx.actor_id,
            "status": status,
            "audit_id": task_ctx.audit_id,
            "execution_time_ms": task_result.execution_time_ms if task_result else 0,
            "compliance_checks": len(task_result.compliance_checks) if task_result else 0
        }
        
        if error:
            log_entry["error"] = error
        
        self.connector_audit_log.append(log_entry)
        
        logger.info(f"Task execution logged: {task_ctx.task_id} - {status}")
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get connector audit log."""
        return self.connector_audit_log[-limit:] if self.connector_audit_log else []
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get task execution statistics."""
        total_tasks = len(self.executed_tasks)
        successful_tasks = len([t for t in self.executed_tasks.values() if t.success])
        failed_tasks = total_tasks - successful_tasks
        
        avg_execution_time = 0.0
        if successful_tasks > 0:
            total_time = sum(t.execution_time_ms for t in self.executed_tasks.values() if t.success)
            avg_execution_time = total_time / successful_tasks
        
        return {
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0.0,
            "avg_execution_time_ms": avg_execution_time,
            "sandbox_stats": self.wasm_sandbox.get_sandbox_stats(),
            "last_activity": datetime.now(timezone.utc).isoformat()
        }
    
    def clear_audit_log(self):
        """Clear the audit log (use with caution)."""
        self.connector_audit_log.clear()
        logger.warning("Connector audit log cleared")
    
    def export_audit_data(self, export_path: Optional[str] = None) -> Dict[str, Any]:
        """Export audit data for analysis."""
        export_data = {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "2.5.0",
            "total_tasks": len(self.executed_tasks),
            "audit_log_entries": len(self.connector_audit_log),
            "execution_stats": self.get_execution_stats(),
            "audit_log": self.connector_audit_log,
            "executed_tasks": {
                task_id: {
                    "success": result.success,
                    "execution_time_ms": result.execution_time_ms,
                    "audit_id": result.audit_id,
                    "timestamp": result.timestamp.isoformat()
                }
                for task_id, result in self.executed_tasks.items()
            }
        }
        
        if export_path:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Audit data exported to {export_path}")
        
        return export_data
    
    # PATCH: Cursor-2025-09-05 DISPATCH-GOV-20250905-LAW-7-SUSTAINABILITY
    # Add sustainability methods
    
    def get_sustainability_summary(self, project_id: str, run_id: Optional[str] = None) -> Dict[str, Any]:
        """Get sustainability summary for a project or run."""
        if not self.sustainability_manager:
            return {"error": "Sustainability manager not available"}
        
        return self.sustainability_manager.get_usage_summary(project_id, run_id)
    
    def add_hitl_override(self, project_id: str, run_id: str, reason: str, duration_minutes: int = 15):
        """Add HITL override for sustainability budget enforcement."""
        if not self.sustainability_manager:
            raise RuntimeError("Sustainability manager not available")
        
        self.sustainability_manager.add_hitl_override(project_id, run_id, reason, duration_minutes)
    
    def forecast_energy_usage(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Forecast energy usage for a plan."""
        if not self.sustainability_manager:
            return {"error": "Sustainability manager not available"}
        
        return self.sustainability_manager.forecast_energy_usage(plan_data)
