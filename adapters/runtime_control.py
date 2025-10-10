""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Unified runtime control system for conscious, sleep, and nap mode orchestration
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.


"""
IOA Runtime Control System - Unified Mode Orchestration

Provides centralized runtime mode management for IOA system states including:
- Conscious runtime (active agent network operations)
- Sleep mode (deep memory defragmentation and stress decay)
- Nap mode (quick maintenance and pattern clustering)

Features:
- Intelligent idle detection and mode switching
- Structured logging with memory persistence
- Configurable runtime flags and scheduling
- Schema-compliant mode responses
- Integration-ready interface for bootloop
- Comprehensive error handling and recovery

Version 0.1.2 Changes:
- Consolidated runtime_scheduler, mode_logger, conscious_runtime, runtime_flags
- Added RuntimeController class for unified interface
- Enhanced logging with proper memory engine integration
- Improved idle detection with configurable thresholds
- Added comprehensive error handling and validation
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class RuntimeMode(Enum):
    """Available runtime modes for IOA system"""
    CONSCIOUS = "conscious"
    SLEEP = "sleep"
    NAP = "nap"
    IDLE = "idle"
    ERROR = "error"


@dataclass
class RuntimeConfig:
    """Configuration for runtime control system"""
    # Mode enablement flags
    conscious_runtime_enabled: bool = True
    sleep_mode_enabled: bool = False
    nap_mode_enabled: bool = True
    
    # Idle detection settings
    idle_threshold_minutes: int = 10
    deep_idle_threshold_minutes: int = 60
    
    # Logging configuration
    enable_runtime_logging: bool = True
    enable_memory_persistence: bool = True
    log_to_console: bool = True
    
    # Mode operation settings
    sleep_operations: List[str] = field(default_factory=lambda: ["defrag_memory", "decay_stress", "consolidate_patterns"])
    nap_operations: List[str] = field(default_factory=lambda: ["quick_defrag", "pattern_relevance_clustering", "refresh_hot_patterns"])
    
    # Integration hooks
    memory_engine_hook: Optional[Callable] = None
    agent_network_hook: Optional[Callable] = None


@dataclass
class RuntimeResponse:
    """Standardized response from runtime mode execution"""
    mode_name: str
    status: str
    operations: List[str] = field(default_factory=list)
    network: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "mode_name": self.mode_name,
            "status": self.status,
            "operations": self.operations,
            "network": self.network,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class RuntimeController:
    """Main controller for IOA runtime mode orchestration"""
    
    def __init__(self, config: Optional[RuntimeConfig] = None):
        """
        Initialize runtime controller with configuration.
        
        Args:
            config: Optional runtime configuration (uses defaults if None)
        """
        self.config = config or RuntimeConfig()
        self.logger = logging.getLogger(__name__)
        
        # Track system activity for idle detection
        self._last_activity_time = datetime.now()
        self._system_start_time = datetime.now()
        
        # Runtime state tracking
        self._current_mode = RuntimeMode.CONSCIOUS
        self._mode_history: List[Dict[str, Any]] = []
        self._error_count = 0
        
        # Mode handlers mapping
        self._mode_handlers = {
            RuntimeMode.CONSCIOUS: self._execute_conscious_mode,
            RuntimeMode.SLEEP: self._execute_sleep_mode,
            RuntimeMode.NAP: self._execute_nap_mode,
            RuntimeMode.IDLE: self._execute_idle_mode
        }
        
        self.logger.info("RuntimeController initialized with configuration")
    
    def update_activity_timestamp(self):
        """Update last known active timestamp (called when system processes tasks)"""
        self._last_activity_time = datetime.now()
        self.logger.debug("Activity timestamp updated")
    
    def is_idle(self, threshold_minutes: Optional[int] = None) -> bool:
        """
        Determine if system has been idle longer than threshold.
        
        Args:
            threshold_minutes: Override default idle threshold
            
        Returns:
            True if system is idle beyond threshold
        """
        threshold = threshold_minutes or self.config.idle_threshold_minutes
        idle_duration = datetime.now() - self._last_activity_time
        return idle_duration > timedelta(minutes=threshold)
    
    def is_deep_idle(self) -> bool:
        """Check if system has been idle long enough for deep sleep mode"""
        idle_duration = datetime.now() - self._last_activity_time
        return idle_duration > timedelta(minutes=self.config.deep_idle_threshold_minutes)
    
    def determine_runtime_mode(self) -> RuntimeMode:
        """
        Determine appropriate runtime mode based on system state and configuration.
        
        Returns:
            RuntimeMode enum value for current optimal mode
        """
        try:
            # Check if system is in deep idle state
            if self.is_deep_idle() and self.config.sleep_mode_enabled:
                return RuntimeMode.SLEEP
            
            # Check if system is idle but not deep idle
            elif self.is_idle() and self.config.nap_mode_enabled:
                return RuntimeMode.NAP
            
            # Check if conscious runtime is enabled and system is active
            elif not self.is_idle() and self.config.conscious_runtime_enabled:
                return RuntimeMode.CONSCIOUS
            
            # Fallback to idle mode
            else:
                return RuntimeMode.IDLE
                
        except Exception as e:
            self.logger.error(f"Error determining runtime mode: {e}")
            return RuntimeMode.ERROR
    
    def execute_runtime_mode(self, mode: Optional[RuntimeMode] = None) -> RuntimeResponse:
        """
        Execute the specified runtime mode or determine and execute optimal mode.
        
        Args:
            mode: Specific mode to execute (auto-determined if None)
            
        Returns:
            RuntimeResponse with execution results
        """
        if mode is None:
            mode = self.determine_runtime_mode()
        
        try:
            # Update current mode tracking
            self._current_mode = mode
            
            # Execute mode handler
            handler = self._mode_handlers.get(mode, self._execute_error_mode)
            response = handler()
            
            # Log and persist response
            self._log_mode_transition(response)
            
            # Update mode history
            self._update_mode_history(response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error executing runtime mode {mode}: {e}")
            self._error_count += 1
            
            error_response = RuntimeResponse(
                mode_name="error",
                status="failed",
                metadata={"error": str(e), "error_count": self._error_count}
            )
            
            self._log_mode_transition(error_response)
            return error_response
    
    def _execute_conscious_mode(self) -> RuntimeResponse:
        """Execute conscious runtime mode with active agent network"""
        try:
            # Get agent network if hook is available
            network = []
            if self.config.agent_network_hook:
                try:
                    agent_network = self.config.agent_network_hook()
                    network = [agent.agent_id for agent in agent_network] if agent_network else []
                except Exception as e:
                    self.logger.warning(f"Agent network hook failed: {e}")
                    network = ["single-agent"]
            else:
                network = ["single-agent"]
            
            return RuntimeResponse(
                mode_name="conscious",
                status="active",
                operations=["agent_coordination", "task_processing", "pattern_learning"],
                network=network,
                metadata={
                    "agent_count": len(network),
                    "network_type": "multi-agent" if len(network) > 1 else "single-agent"
                }
            )
            
        except Exception as e:
            self.logger.error(f"Conscious mode execution failed: {e}")
            raise
    
    def _execute_sleep_mode(self) -> RuntimeResponse:
        """Execute deep sleep mode with comprehensive system maintenance"""
        try:
            return RuntimeResponse(
                mode_name="sleep",
                status="active",
                operations=self.config.sleep_operations,
                network=["maintenance"],
                metadata={
                    "maintenance_type": "deep",
                    "idle_duration_minutes": int((datetime.now() - self._last_activity_time).total_seconds() / 60),
                    "operations_count": len(self.config.sleep_operations)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Sleep mode execution failed: {e}")
            raise
    
    def _execute_nap_mode(self) -> RuntimeResponse:
        """Execute nap mode with quick maintenance operations"""
        try:
            return RuntimeResponse(
                mode_name="nap",
                status="active",
                operations=self.config.nap_operations,
                network=["maintenance"],
                metadata={
                    "maintenance_type": "quick",
                    "idle_duration_minutes": int((datetime.now() - self._last_activity_time).total_seconds() / 60),
                    "operations_count": len(self.config.nap_operations)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Nap mode execution failed: {e}")
            raise
    
    def _execute_idle_mode(self) -> RuntimeResponse:
        """Execute idle mode when no other modes are appropriate"""
        return RuntimeResponse(
            mode_name="idle",
            status="waiting",
            operations=["monitor_activity"],
            network=["standby"],
            metadata={
                "reason": "no_appropriate_mode",
                "idle_duration_minutes": int((datetime.now() - self._last_activity_time).total_seconds() / 60)
            }
        )
    
    def _execute_error_mode(self) -> RuntimeResponse:
        """Handle error state when mode execution fails"""
        return RuntimeResponse(
            mode_name="error",
            status="failed",
            operations=["error_recovery"],
            network=["diagnostic"],
            metadata={
                "error_count": self._error_count,
                "last_successful_mode": self._current_mode.value if self._current_mode else None
            }
        )
    
    def _log_mode_transition(self, response: RuntimeResponse):
        """Log runtime mode transition with configured outputs"""
        if not self.config.enable_runtime_logging:
            return
        
        try:
            # Console logging
            if self.config.log_to_console:
                self.logger.info(f"Runtime mode transition: {response.mode_name} | Status: {response.status} | "
                               f"Operations: {len(response.operations)} | Network: {response.network}")
            
            # Memory persistence
            if self.config.enable_memory_persistence:
                self._persist_to_memory(response)
                
        except Exception as e:
            self.logger.error(f"Failed to log mode transition: {e}")
    
    def _persist_to_memory(self, response: RuntimeResponse):
        """Persist runtime mode response to memory engine"""
        try:
            if not self.config.memory_engine_hook:
                self.logger.debug("Memory engine hook not configured, skipping persistence")
                return
            
            memory_entry = {
                "id": str(uuid.uuid4()),
                "pattern_id": "runtime_mode_transition",
                "variables": {
                    "mode_name": response.mode_name,
                    "status": response.status,
                    "operations": response.operations,
                    "network": response.network,
                    "metadata": response.metadata
                },
                "metadata": {
                    "timestamp": response.timestamp,
                    "source": "runtime_controller",
                    "controller_id": id(self)
                }
            }
            
            # Call memory engine hook
            self.config.memory_engine_hook(memory_entry)
            self.logger.debug(f"Persisted mode transition to memory: {response.mode_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to persist to memory: {e}")
    
    def _update_mode_history(self, response: RuntimeResponse):
        """Update internal mode history for analysis"""
        try:
            history_entry = {
                "mode": response.mode_name,
                "status": response.status,
                "timestamp": response.timestamp,
                "duration": None  # Will be calculated on next transition
            }
            
            # Calculate duration of previous mode
            if self._mode_history:
                last_entry = self._mode_history[-1]
                last_time = datetime.fromisoformat(last_entry["timestamp"])
                current_time = datetime.fromisoformat(response.timestamp)
                last_entry["duration"] = (current_time - last_time).total_seconds()
            
            self._mode_history.append(history_entry)
            
            # Keep only last 100 entries
            if len(self._mode_history) > 100:
                self._mode_history = self._mode_history[-100:]
                
        except Exception as e:
            self.logger.error(f"Failed to update mode history: {e}")
    
    def get_runtime_status(self) -> Dict[str, Any]:
        """
        Get comprehensive runtime status information.
        
        Returns:
            Dictionary with current runtime state and statistics
        """
        try:
            idle_duration = datetime.now() - self._last_activity_time
            uptime = datetime.now() - self._system_start_time
            
            return {
                "current_mode": self._current_mode.value if self._current_mode else None,
                "is_idle": self.is_idle(),
                "is_deep_idle": self.is_deep_idle(),
                "idle_duration_seconds": int(idle_duration.total_seconds()),
                "uptime_seconds": int(uptime.total_seconds()),
                "error_count": self._error_count,
                "mode_transitions": len(self._mode_history),
                "last_activity": self._last_activity_time.isoformat(),
                "system_start": self._system_start_time.isoformat(),
                "config": {
                    "conscious_enabled": self.config.conscious_runtime_enabled,
                    "sleep_enabled": self.config.sleep_mode_enabled,
                    "nap_enabled": self.config.nap_mode_enabled,
                    "idle_threshold_minutes": self.config.idle_threshold_minutes,
                    "logging_enabled": self.config.enable_runtime_logging
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get runtime status: {e}")
            return {"error": str(e)}
    
    def get_mode_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent mode transition history.
        
        Args:
            limit: Maximum number of history entries to return
            
        Returns:
            List of recent mode transitions
        """
        return self._mode_history[-limit:] if self._mode_history else []
    
    def reset_error_count(self):
        """Reset error counter (for administrative use)"""
        self._error_count = 0
        self.logger.info("Runtime error count reset")
    
    def force_mode(self, mode: RuntimeMode) -> RuntimeResponse:
        """
        Force execution of a specific runtime mode (for testing/debugging).
        
        Args:
            mode: RuntimeMode to force execute
            
        Returns:
            RuntimeResponse from forced mode execution
        """
        self.logger.warning(f"Forcing runtime mode: {mode.value}")
        return self.execute_runtime_mode(mode)


# Factory and utility functions

def create_runtime_controller(
    conscious_enabled: bool = True,
    sleep_enabled: bool = False,
    nap_enabled: bool = True,
    idle_threshold: int = 10,
    memory_hook: Optional[Callable] = None,
    agent_network_hook: Optional[Callable] = None
) -> RuntimeController:
    """
    Factory function to create a configured runtime controller.
    
    Args:
        conscious_enabled: Enable conscious runtime mode
        sleep_enabled: Enable sleep mode
        nap_enabled: Enable nap mode
        idle_threshold: Idle threshold in minutes
        memory_hook: Optional memory engine hook function
        agent_network_hook: Optional agent network hook function
        
    Returns:
        Configured RuntimeController instance
    """
    config = RuntimeConfig(
        conscious_runtime_enabled=conscious_enabled,
        sleep_mode_enabled=sleep_enabled,
        nap_mode_enabled=nap_enabled,
        idle_threshold_minutes=idle_threshold,
        memory_engine_hook=memory_hook,
        agent_network_hook=agent_network_hook
    )
    
    return RuntimeController(config)


def create_memory_hook(remember_function: Callable) -> Callable:
    """
    Create a memory hook wrapper for integration with memory engine.
    
    Args:
        remember_function: The memory engine's remember() function
        
    Returns:
        Configured memory hook function
    """
    def memory_hook(memory_entry: Dict[str, Any]):
        """Hook function to persist runtime data to memory engine"""
        try:
            remember_function(memory_entry)
        except Exception as e:
            logging.getLogger(__name__).error(f"Memory hook failed: {e}")
    
    return memory_hook


# Legacy compatibility functions (for existing bootloop integration)

def runtime_scheduler() -> Dict[str, Any]:
    """
    Legacy compatibility function for existing bootloop integration.
    
    Returns:
        Runtime mode response dictionary
    """
    # Create default controller if none exists
    controller = create_runtime_controller()
    response = controller.execute_runtime_mode()
    
    return response.to_dict()


def is_idle(idle_threshold_minutes: int = 10) -> bool:
    """
    Legacy compatibility function for idle detection.
    
    Args:
        idle_threshold_minutes: Idle threshold in minutes
        
    Returns:
        True if system is considered idle
    """
    controller = create_runtime_controller(idle_threshold=idle_threshold_minutes)
    return controller.is_idle()


def update_activity_timestamp():
    """Legacy compatibility function for activity timestamp updates"""
    # This would need to be connected to a global controller instance
    # For now, just log the call
    logging.getLogger(__name__).info("Activity timestamp update requested (legacy call)")


# Testing and validation functions

def validate_runtime_control():
    """Validate runtime control system functionality"""
    try:
        # Test controller creation
        controller = create_runtime_controller()
        
        # Test mode determination
        mode = controller.determine_runtime_mode()
        
        # Test mode execution
        response = controller.execute_runtime_mode(mode)
        
        # Test status retrieval
        status = controller.get_runtime_status()
        
        return {
            "validation_passed": True,
            "controller_created": True,
            "mode_determined": mode.value,
            "response_generated": response.status,
            "status_retrieved": len(status) > 5
        }
        
    except Exception as e:
        return {
            "validation_passed": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Demo and validation
    print("=== IOA Runtime Control System Demo ===")
    
    # Validate system
    validation = validate_runtime_control()
    print(f"Validation result: {validation}")
    
    if validation.get("validation_passed"):
        # Create and test controller
        controller = create_runtime_controller()
        
        print(f"\nInitial status:")
        status = controller.get_runtime_status()
        print(f"  Current mode: {status['current_mode']}")
        print(f"  Is idle: {status['is_idle']}")
        print(f"  Uptime: {status['uptime_seconds']}s")
        
        # Test mode execution
        print(f"\nExecuting runtime mode...")
        response = controller.execute_runtime_mode()
        print(f"  Mode: {response.mode_name}")
        print(f"  Status: {response.status}")
        print(f"  Operations: {response.operations}")
        print(f"  Network: {response.network}")
        
        # Test forced mode
        print(f"\nForcing nap mode...")
        nap_response = controller.force_mode(RuntimeMode.NAP)
        print(f"  Mode: {nap_response.mode_name}")
        print(f"  Status: {nap_response.status}")
        print(f"  Operations: {nap_response.operations}")
    
    print("\n✅ Runtime control demo complete!")

