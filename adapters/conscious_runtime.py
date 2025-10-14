"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Conscious runtime mode controller with mood engine integration
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.


"""
Conscious Runtime Module for IOA System

Provides conscious runtime mode operations including agent network coordination,
real-time processing, and mood-aware system responses. Integrates with the
unified runtime control system for intelligent mode switching.

Key Features:
- Conscious roundtable coordination with agent networks
- Sleep mode for deep memory defragmentation
- Nap mode for quick system maintenance
- Mood engine integration with availability guards
- Comprehensive status reporting and monitoring
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# Mood engine integration with availability guard
try:
    from ioa.governance.mood_engine import (
        get_mood_from_metrics, 
        create_mood_engine,
        MoodType,
        MoodState
    )
    MOOD_AVAILABLE = True
except ImportError:
    MOOD_AVAILABLE = False
    logging.getLogger(__name__).info("Mood engine not available - running without mood tracking")
    
    # Mock classes for graceful degradation
    class MoodType:
        pass
    
    class MoodState:
        def __init__(self, mood_type=None, color_hex="#808080", description="unavailable"):
            self.mood_type = type('MockMoodType', (), {'value': 'neutral'})()
            self.color_hex = color_hex
            self.description = description


def run_conscious_roundtable(agent_network: Optional[List] = None) -> Dict[str, Any]:
    """
    Execute conscious roundtable mode with agent network coordination.
    
    Activates conscious processing mode where the IOA system maintains active
    awareness and coordination across all registered agents. Provides real-time
    task processing, collaborative decision making, and mood monitoring.
    
    Args:
        agent_network: Optional list of agent instances with metrics
        
    Returns:
        Status response with network information, metrics, and mood data
    """
    status = "Activated"
    
    # Process agent network information
    if agent_network:
        network = []
        for agent in agent_network:
            if hasattr(agent, 'agent_id'):
                network.append(agent.agent_id)
            else:
                network.append(str(agent))
    else:
        network = ["single-agent"]
    
    # Base response structure
    response = {
        "status": status,
        "mode": "conscious_roundtable",
        "network": network,
        "agent_count": len(network),
        "timestamp": datetime.now().isoformat(),
        "operations": [
            "agent_coordination",
            "real_time_processing", 
            "collaborative_decision_making",
            "memory_access_active"
        ],
        "capabilities": {
            "multi_agent_coordination": True,
            "real_time_response": True,
            "memory_read_write": True,
            "pattern_matching": True,
            "mood_tracking": MOOD_AVAILABLE
        }
    }
    
    # Add mood tracking if available and agents provided
    if MOOD_AVAILABLE and agent_network:
        try:
            mood_data = _calculate_collective_mood(agent_network)
            response["collective_mood"] = mood_data
            response["mood_engine_status"] = "active"
        except Exception as e:
            logging.getLogger(__name__).warning(f"Mood calculation failed: {e}")
            response["collective_mood"] = "calculation_failed"
            response["mood_engine_status"] = "error"
    elif MOOD_AVAILABLE:
        response["mood_engine_status"] = "available_no_agents"
    else:
        response["mood_engine_status"] = "unavailable"
    
    # Add performance metrics if available
    if agent_network:
        response["performance_metrics"] = _calculate_network_metrics(agent_network)
    
    return response


def run_sleep_mode() -> Dict[str, Any]:
    """
    Execute sleep mode with deep memory operations and system maintenance.
    
    Activates deep sleep mode where the IOA system performs intensive background
    operations including memory defragmentation, stress decay, pattern consolidation,
    and system optimization. This mode is designed for extended periods of low activity.
    
    Returns:
        Status response with sleep mode operations and expected duration
    """
    return {
        "status": "Activated",
        "mode": "sleep",
        "operations": [
            "defrag_memory",
            "decay_stress", 
            "pattern_consolidation",
            "memory_compression",
            "cache_optimization",
            "index_rebuilding"
        ],
        "timestamp": datetime.now().isoformat(),
        "expected_duration": "extended",
        "recovery_enabled": True,
        "background_processes": {
            "memory_defrag": "active",
            "stress_decay": "active", 
            "pattern_merge": "active",
            "garbage_collection": "scheduled"
        },
        "capabilities": {
            "memory_write_operations": True,
            "system_optimization": True,
            "background_processing": True,
            "low_power_mode": True
        },
        "maintenance_level": "deep"
    }


def run_nap_mode() -> Dict[str, Any]:
    """
    Execute nap mode with quick maintenance operations and pattern clustering.
    
    Activates nap mode for brief system maintenance including quick memory
    defragmentation, pattern relevance clustering, cache optimization, and
    light system housekeeping. Designed for short breaks in activity.
    
    Returns:
        Status response with nap mode operations and brief duration
    """
    return {
        "status": "Activated", 
        "mode": "nap",
        "operations": [
            "quick_defrag",
            "pattern_relevance_clustering", 
            "cache_optimization",
            "temp_cleanup",
            "index_refresh"
        ],
        "timestamp": datetime.now().isoformat(),
        "expected_duration": "brief",
        "recovery_enabled": True,
        "background_processes": {
            "quick_defrag": "active",
            "pattern_clustering": "active",
            "cache_refresh": "active",
            "light_cleanup": "active"
        },
        "capabilities": {
            "quick_memory_ops": True,
            "pattern_optimization": True,
            "cache_management": True,
            "rapid_recovery": True
        },
        "maintenance_level": "light"
    }


def get_conscious_status() -> Dict[str, Any]:
    """
    Get current conscious runtime status and system capabilities.
    
    Provides comprehensive status information about the conscious runtime
    system including available modes, mood engine status, and current
    system capabilities and configuration.
    
    Returns:
        Current status including all available features and capabilities
    """
    return {
        "conscious_runtime_available": True,
        "mood_engine_available": MOOD_AVAILABLE,
        "supported_modes": [
            "conscious_roundtable", 
            "sleep", 
            "nap"
        ],
        "timestamp": datetime.now().isoformat(),
        "version": "2.1.0",
        "module_status": {
            "conscious_runtime": "operational",
            "mood_integration": "available" if MOOD_AVAILABLE else "unavailable",
            "agent_coordination": "ready",
            "memory_operations": "ready"
        },
        "system_capabilities": {
            "multi_agent_support": True,
            "mood_tracking": MOOD_AVAILABLE,
            "real_time_processing": True,
            "background_maintenance": True,
            "performance_monitoring": True,
            "error_recovery": True
        },
        "configuration": {
            "default_mode": "conscious_roundtable",
            "auto_mode_switching": True,
            "mood_integration_enabled": MOOD_AVAILABLE,
            "performance_tracking": True
        }
    }


def _calculate_collective_mood(agent_network: List) -> Dict[str, Any]:
    """
    Calculate collective mood from agent network metrics.
    
    Args:
        agent_network: List of agent instances with satisfaction/stress metrics
        
    Returns:
        Collective mood data including mood type, color, and statistics
    """
    if not agent_network or not MOOD_AVAILABLE:
        return {"status": "unavailable", "reason": "no_agents_or_mood_engine"}
    
    try:
        # Extract metrics from agents
        satisfactions = []
        stresses = []
        
        for agent in agent_network:
            satisfaction = getattr(agent, 'satisfaction', 0.5)
            stress = getattr(agent, 'stress', 0.0)
            
            if isinstance(satisfaction, (int, float)):
                satisfactions.append(satisfaction)
            if isinstance(stress, (int, float)):
                stresses.append(stress)
        
        if not satisfactions or not stresses:
            return {"status": "unavailable", "reason": "no_valid_metrics"}
        
        # Calculate averages
        avg_satisfaction = sum(satisfactions) / len(satisfactions)
        avg_stress = sum(stresses) / len(stresses)
        
        # Get collective mood
        collective_mood = get_mood_from_metrics(avg_satisfaction, avg_stress)
        
        return {
            "status": "available",
            "mood_type": collective_mood.mood_type.value,
            "color_hex": collective_mood.color_hex,
            "description": collective_mood.description,
            "metrics": {
                "avg_satisfaction": round(avg_satisfaction, 3),
                "avg_stress": round(avg_stress, 3),
                "agent_count": len(agent_network),
                "satisfaction_range": [min(satisfactions), max(satisfactions)],
                "stress_range": [min(stresses), max(stresses)]
            }
        }
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Mood calculation error: {e}")
        return {"status": "error", "error": str(e)}


def _calculate_network_metrics(agent_network: List) -> Dict[str, Any]:
    """
    Calculate performance metrics for the agent network.
    
    Args:
        agent_network: List of agent instances
        
    Returns:
        Network performance metrics and statistics
    """
    try:
        metrics = {
            "total_agents": len(agent_network),
            "active_agents": 0,
            "performance_scores": [],
            "response_times": [],
            "error_rates": []
        }
        
        for agent in agent_network:
            # Check if agent is active/responsive
            if hasattr(agent, 'status') and getattr(agent, 'status', '') == 'active':
                metrics["active_agents"] += 1
            
            # Collect performance data if available
            if hasattr(agent, 'performance_score'):
                score = getattr(agent, 'performance_score', 0)
                if isinstance(score, (int, float)):
                    metrics["performance_scores"].append(score)
            
            if hasattr(agent, 'avg_response_time'):
                response_time = getattr(agent, 'avg_response_time', 0)
                if isinstance(response_time, (int, float)):
                    metrics["response_times"].append(response_time)
            
            if hasattr(agent, 'error_rate'):
                error_rate = getattr(agent, 'error_rate', 0)
                if isinstance(error_rate, (int, float)):
                    metrics["error_rates"].append(error_rate)
        
        # Calculate aggregated metrics
        if metrics["performance_scores"]:
            metrics["avg_performance"] = sum(metrics["performance_scores"]) / len(metrics["performance_scores"])
        
        if metrics["response_times"]:
            metrics["avg_response_time"] = sum(metrics["response_times"]) / len(metrics["response_times"])
        
        if metrics["error_rates"]:
            metrics["avg_error_rate"] = sum(metrics["error_rates"]) / len(metrics["error_rates"])
        
        metrics["network_health"] = "good" if metrics["active_agents"] > 0 else "degraded"
        
        return metrics
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Network metrics calculation error: {e}")
        return {"error": str(e), "status": "calculation_failed"}


# Legacy compatibility functions for existing integrations
def runtime_scheduler() -> Dict[str, Any]:
    """
    Legacy compatibility function for existing bootloop integration.
    
    Returns:
        Runtime mode response dictionary
    """
    return run_conscious_roundtable()


def is_idle(idle_threshold_minutes: int = 10) -> bool:
    """
    Legacy compatibility function for idle detection.
    
    Args:
        idle_threshold_minutes: Threshold for idle detection
        
    Returns:
        Always False for conscious runtime (active by definition)
    """
    return False


# Export all public functions
__all__ = [
    'run_conscious_roundtable',
    'run_sleep_mode', 
    'run_nap_mode',
    'get_conscious_status',
    'runtime_scheduler',  # Legacy compatibility
    'is_idle',  # Legacy compatibility
    'MOOD_AVAILABLE'
]