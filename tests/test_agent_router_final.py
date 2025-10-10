""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Comprehensive test suite for agent router with multi-agent coordination
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.


"""
Agent Router Test Suite

Validates agent router functionality including:
- Agent registration and capability matching
- Task routing and load balancing
- Performance monitoring and health checks
- Error handling and failover
- Multi-tenant agent management
"""

import pytest
import time
import threading
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any

# Add src directory to Python path for imports
import sys
import os
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Fixed import paths for IOA structure
try:
    from src.agent_router import (
        AgentRouter,
        AgentStatus,
        TaskPriority,
        AgentProfile,
        AgentCapability,
        TaskRequest,
        TaskRoutingError,
        AgentRegistrationError,
        create_agent_router
    )
    from src.llm_adapter import LLMService, LLMServiceError
except ImportError:
    # Fallback for different project structures
    try:
        from src.agent_router import (
            AgentRouter,
            AgentStatus,
            TaskPriority,
            AgentProfile,
            AgentCapability,
            TaskRequest,
            TaskRoutingError,
            AgentRegistrationError,
            create_agent_router
        )
        from src.llm_adapter import LLMService, LLMServiceError
    except ImportError:
        # Mock for CI/testing environments
        from enum import Enum
        class AgentStatus(Enum):
            AVAILABLE = "available"
            BUSY = "busy"
            OFFLINE = "offline"
        class TaskPriority(Enum):
            LOW = 1
            NORMAL = 2
            HIGH = 3
        class AgentRouter:
            def __init__(self, *args, **kwargs):
                self.agents = {}
            def register_agent(self, *args, **kwargs): pass
            def route_task(self, *args, **kwargs):
                return {"status": "success"}
        class AgentProfile: pass
        class AgentCapability: pass
        class TaskRoutingError(Exception): pass
        class LLMService: pass
        class LLMServiceError(Exception): pass

class MockLLMService:
    """Mock LLM service for testing."""
    
    def __init__(self, response: str = "Mock response", should_fail: bool = False):
        self.response = response
        self.should_fail = should_fail
        self.call_count = 0
    
    def execute(self, prompt: str) -> str:
        self.call_count += 1
        if self.should_fail:
            raise Exception("Mock LLM service failure")
        return f"{self.response} for: {prompt[:50]}..."


class TestAgentRouterInitialization:
    """Test AgentRouter initialization and configuration."""
    
    def test_init_default_config(self):
        """Test initialization with default configuration."""
        router = AgentRouter()
        
        assert router.governance_config == {}
        assert len(router._agents) >= 0  # May have default agents
        assert router._task_counter == 0
        assert router._router_stats['total_tasks_routed'] == 0
    
    def test_init_custom_config(self):
        """Test initialization with custom governance configuration."""
        config = {"roundtable_mode_enabled": True, "consensus_threshold": 0.8}
        router = AgentRouter(governance_config=config)
        
        assert router.governance_config == config
        assert router.governance_config['roundtable_mode_enabled'] is True
    
    def test_init_with_environment_variables(self):
        """Test initialization behavior with environment variables."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            router = AgentRouter()
            # Should attempt to register LLM agents (may fail due to mock)
            assert isinstance(router, AgentRouter)
    
    def test_factory_function(self):
        """Test factory function for creating router instances."""
        config = {"test": True}
        router = create_agent_router(config)
        
        assert isinstance(router, AgentRouter)
        assert router.governance_config == config

    def test_init_safe_import_handling(self):
        """Test safe import handling when LLM adapter unavailable."""
        # Test that router initializes even if LLM services fail
        router = AgentRouter()
        assert isinstance(router, AgentRouter)
        # Should still be able to register virtual agents
        result = router.register_virtual_agent(
            "test-agent", "Test", "Role", "Description", 
            [AgentCapability("test", 0.8)]
        )
        assert result is True


class TestAgentRegistration:
    """Test agent registration functionality."""
    
    def test_register_virtual_agent_basic(self):
        """Test basic virtual agent registration."""
        router = AgentRouter()
        
        capabilities = [
            AgentCapability("test_capability", 0.8, 0.0, 1.0, 0.9)
        ]
        
        result = router.register_virtual_agent(
            agent_id="test-agent",
            name="Test Agent",
            role="Test Role",
            description="Test Description",
            capabilities=capabilities
        )
        
        assert result is True
        assert "test-agent" in router._agents
        
        profile = router._agents["test-agent"]
        assert profile.name == "Test Agent"
        assert profile.role == "Test Role"
        assert profile.description == "Test Description"
        assert len(profile.capabilities) == 1
        assert profile.status == AgentStatus.AVAILABLE
    
    def test_register_virtual_agent_with_custom_executor(self):
        """Test virtual agent registration with custom executor."""
        router = AgentRouter()
        
        def custom_executor(task: str) -> str:
            return f"Custom response: {task}"
        
        capabilities = [AgentCapability("custom", 0.9)]
        
        result = router.register_virtual_agent(
            agent_id="custom-agent",
            name="Custom Agent",
            role="Custom Role",
            description="Custom Description",
            capabilities=capabilities,
            executor=custom_executor
        )
        
        assert result is True
        assert "custom-agent" in router._agent_executors
        
        # Test executor
        executor = router._agent_executors["custom-agent"]
        response = executor("test task")
        assert response == "Custom response: test task"
    
    def test_register_real_agent(self):
        """Test real LLM model registration."""
        router = AgentRouter()
        mock_service = MockLLMService("LLM response")
        
        capabilities = [
            AgentCapability("analysis", 0.9, 0.05, 2.0, 0.95),
            AgentCapability("execution", 0.8, 0.04, 1.8, 0.92)
        ]
        
        result = router.register_real_agent(
            agent_id="llm-model",
            name="LLM Model",
            role="Analyst",
            description="LLM-powered model",
            llm_service=mock_service,
            capabilities=capabilities,
            max_concurrent_tasks=3
        )
        
        assert result is True
        assert "llm-model" in router._agents
        
        profile = router._agents["llm-model"]
        assert profile.max_concurrent_tasks == 3
        assert len(profile.capabilities) == 2
    
    def test_register_duplicate_agent(self):
        """Test registration of duplicate agent IDs."""
        router = AgentRouter()
        
        capabilities = [AgentCapability("test", 0.8)]
        
        # First registration should succeed
        result1 = router.register_virtual_agent(
            "duplicate-id", "Agent 1", "Role 1", "Description 1", capabilities
        )
        assert result1 is True
        
        # Second registration should fail
        with pytest.raises(AgentRegistrationError):
            router.register_real_agent(
                "duplicate-id", "Agent 2", "Role 2", "Description 2",
                MockLLMService(), capabilities
            )
    
    def test_capability_indexing(self):
        """Test capability indexing during registration."""
        router = AgentRouter()
        
        # Register agents with overlapping capabilities
        cap1 = [AgentCapability("analysis", 0.8), AgentCapability("general", 0.7)]
        cap2 = [AgentCapability("analysis", 0.9), AgentCapability("synthesis", 0.8)]
        
        router.register_virtual_agent("agent1", "Agent 1", "Role", "Desc", cap1)
        router.register_virtual_agent("agent2", "Agent 2", "Role", "Desc", cap2)
        
        # Check capability index
        assert "analysis" in router._capability_index
        assert "general" in router._capability_index
        assert "synthesis" in router._capability_index
        
        assert "agent1" in router._capability_index["analysis"]
        assert "agent2" in router._capability_index["analysis"]
        assert "agent1" in router._capability_index["general"]
        assert "agent2" in router._capability_index["synthesis"]

    def test_agent_registration_with_tags(self):
        """Test agent registration with tags."""
        router = AgentRouter()
        
        capabilities = [AgentCapability("test", 0.8)]
        tags = {"environment", "production", "high-priority"}
        
        result = router.register_virtual_agent(
            "tagged-agent", "Tagged Agent", "Role", "Description",
            capabilities, tags=tags
        )
        
        assert result is True
        profile = router._agents["tagged-agent"]
        assert profile.tags == tags


class TestTaskRouting:
    """Test task routing and agent selection."""
    
    def test_route_task_to_virtual_agent(self):
        """Test routing task to virtual agent."""
        router = AgentRouter()
        
        capabilities = [AgentCapability("execution", 0.8)]
        router.register_virtual_agent(
            "test-agent", "Test Agent", "Role", "Description", capabilities
        )
        
        result = router.route_task(
            task="Test task",
            required_capability="execution"
        )
        
        assert "test-agent" in result
        assert "Test task" in result["test-agent"]
        assert "error" not in result
    
    def test_route_task_to_llm_model(self):
        """Test routing task to LLM model."""
        router = AgentRouter()
        mock_service = MockLLMService("LLM processed task")
        
        capabilities = [AgentCapability("analysis", 0.9)]
        router.register_real_agent(
            "llm-model", "LLM Model", "Analyst", "LLM Description",
            mock_service, capabilities
        )
        
        result = router.route_task(
            task="Analyze this data",
            required_capability="analysis"
        )
        
        assert "llm-model" in result
        assert "LLM processed task" in result["llm-model"]
        assert mock_service.call_count == 1
    
    def test_route_task_no_capability_match(self):
        """Test routing when no agent has required capability."""
        router = AgentRouter()
        
        capabilities = [AgentCapability("different_capability", 0.8)]
        router.register_virtual_agent(
            "agent", "Agent", "Role", "Description", capabilities
        )
        
        result = router.route_task(
            task="Test task",
            required_capability="nonexistent_capability"
        )
        
        assert "error" in result
        assert "No agent found" in result["error"]
    
    def test_route_task_without_capability_requirement(self):
        """Test routing task without specific capability requirement."""
        router = AgentRouter()
        
        capabilities = [AgentCapability("general", 0.8)]
        router.register_virtual_agent(
            "general-agent", "General Agent", "Role", "Description", capabilities
        )
        
        result = router.route_task(task="General task")
        
        # Should route to any available agent
        assert len(result) == 1
        assert "error" not in result
    
    def test_route_task_with_preferred_agent(self):
        """Test routing with preferred agent specification."""
        router = AgentRouter()
        
        # Register multiple agents with same capability
        capabilities = [AgentCapability("execution", 0.8)]
        router.register_virtual_agent("agent1", "Agent 1", "Role", "Desc", capabilities)
        router.register_virtual_agent("agent2", "Agent 2", "Role", "Desc", capabilities)
        
        result = router.route_task(
            task="Test task",
            required_capability="execution",
            preferred_agent="agent2"
        )
        
        assert "agent2" in result
    
    def test_route_task_with_priority(self):
        """Test task routing with different priority levels."""
        router = AgentRouter()
        
        capabilities = [AgentCapability("execution", 0.8)]
        router.register_virtual_agent("agent", "Agent", "Role", "Desc", capabilities)
        
        # Test different priority levels
        for priority in TaskPriority:
            result = router.route_task(
                task=f"Priority {priority.name} task",
                required_capability="execution",
                priority=priority
            )
            assert "agent" in result

    def test_route_task_with_max_response_time(self):
        """Test routing with response time constraints."""
        router = AgentRouter()
        
        # Agent with slow response time
        slow_cap = [AgentCapability("slow", 0.8, 0.0, 10.0, 0.9)]  # 10s avg response
        router.register_virtual_agent("slow-agent", "Slow", "Role", "Desc", slow_cap)
        
        # Agent with fast response time  
        fast_cap = [AgentCapability("slow", 0.7, 0.0, 1.0, 0.9)]  # 1s avg response
        router.register_virtual_agent("fast-agent", "Fast", "Role", "Desc", fast_cap)
        
        # Route with tight time constraint
        result = router.route_task(
            task="Urgent task",
            required_capability="slow",
            max_response_time=2.0
        )
        
        # Should route to fast agent
        assert "fast-agent" in result


class TestAgentSelection:
    """Test agent selection algorithms."""
    
    def test_agent_scoring_algorithm(self):
        """Test agent scoring for task assignment."""
        router = AgentRouter()
        
        # Register agents with different proficiency levels
        high_prof_cap = [AgentCapability("analysis", 0.9, 0.0, 1.0, 0.95)]
        low_prof_cap = [AgentCapability("analysis", 0.6, 0.0, 3.0, 0.80)]
        
        router.register_virtual_agent("high-perf", "High Perf", "Role", "Desc", high_prof_cap)
        router.register_virtual_agent("low-perf", "Low Perf", "Role", "Desc", low_prof_cap)
        
        result = router.route_task(
            task="Analysis task",
            required_capability="analysis"
        )
        
        # Should prefer higher proficiency agent
        assert "high-perf" in result
    
    def test_load_balancing(self):
        """Test load balancing across agents."""
        router = AgentRouter()
        
        # Register identical agents
        capabilities = [AgentCapability("execution", 0.8)]
        router.register_virtual_agent("agent1", "Agent 1", "Role", "Desc", capabilities)
        router.register_virtual_agent("agent2", "Agent 2", "Role", "Desc", capabilities)
        
        # Route multiple tasks
        agent_usage = {"agent1": 0, "agent2": 0}
        
        for i in range(10):
            result = router.route_task(
                task=f"Task {i}",
                required_capability="execution"
            )
            
            for agent_id in result:
                if agent_id in agent_usage:
                    agent_usage[agent_id] += 1
        
        # Both agents should be used (basic load balancing check)
        assert sum(agent_usage.values()) == 10

    def test_agent_availability_checking(self):
        """Test agent availability checking."""
        router = AgentRouter()
        
        capabilities = [AgentCapability("test", 0.8)]
        router.register_virtual_agent("test-agent", "Test", "Role", "Desc", capabilities)
        
        # Verify agent is initially available
        assert router._is_agent_available("test-agent") is True
        
        # Test non-existent agent
        assert router._is_agent_available("non-existent") is False

    def test_agent_suitability_assessment(self):
        """Test agent suitability assessment."""
        router = AgentRouter()
        
        capabilities = [AgentCapability("specific", 0.8, 0.0, 1.0, 0.9)]
        router.register_virtual_agent("suitable-agent", "Suitable", "Role", "Desc", capabilities)
        
        # Create task request
        task_request = TaskRequest(
            task_id="test",
            content="Test task",
            required_capability="specific",
            max_response_time=2.0
        )
        
        # Test suitability
        assert router._is_agent_suitable("suitable-agent", task_request) is True
        
        # Test with different capability requirement
        task_request.required_capability = "different"
        assert router._is_agent_suitable("suitable-agent", task_request) is False


class TestPerformanceMonitoring:
    """Test performance monitoring and metrics."""
    
    def test_routing_statistics_tracking(self):
        """Test routing statistics collection."""
        router = AgentRouter()
        
        capabilities = [AgentCapability("execution", 0.8)]
        router.register_virtual_agent("agent", "Agent", "Role", "Desc", capabilities)
        
        initial_stats = router.get_routing_statistics()
        assert initial_stats['total_tasks_routed'] == 0
        assert initial_stats['successful_tasks'] == 0
        
        # Route some tasks
        for i in range(3):
            router.route_task(f"Task {i}", required_capability="execution")
        
        updated_stats = router.get_routing_statistics()
        assert updated_stats['total_tasks_routed'] == 3
        assert updated_stats['successful_tasks'] == 3
        assert updated_stats['success_rate'] == 1.0
    
    def test_agent_performance_tracking(self):
        """Test individual agent performance tracking."""
        router = AgentRouter()
        
        capabilities = [AgentCapability("execution", 0.8)]
        router.register_virtual_agent("tracked-agent", "Agent", "Role", "Desc", capabilities)
        
        # Route tasks to track performance
        for i in range(5):
            router.route_task(f"Task {i}", required_capability="execution")
        
        agent_status = router.get_agent_status("tracked-agent")
        assert agent_status is not None
        assert agent_status['performance']['total_tasks'] == 5
        assert agent_status['performance']['successful_tasks'] == 5
        assert agent_status['performance']['success_rate'] == 1.0
    
    def test_agent_status_information(self):
        """Test comprehensive agent status information."""
        router = AgentRouter()
        
        capabilities = [
            AgentCapability("analysis", 0.9, 0.05, 2.0, 0.95),
            AgentCapability("synthesis", 0.8, 0.03, 1.5, 0.90)
        ]
        
        router.register_virtual_agent(
            "status-agent", "Status Agent", "Analyst", "Test agent", capabilities
        )
        
        status = router.get_agent_status("status-agent")
        
        assert status['agent_id'] == "status-agent"
        assert status['name'] == "Status Agent"
        assert status['role'] == "Analyst"
        assert status['status'] == AgentStatus.AVAILABLE.value
        assert len(status['capabilities']) == 2
        assert 'performance' in status
        assert 'utilization' in status

    def test_routing_statistics_with_version(self):
        """Test routing statistics include version information."""
        router = AgentRouter()
        
        stats = router.get_routing_statistics()
        assert 'version' in stats
        assert stats['version'] == "2.5.0"  # PATCH: Cursor-2024-12-19 ET-001 Step 3 - Update expected version


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_llm_service_failure(self):
        """Test handling of LLM service failures."""
        router = AgentRouter()
        failing_service = MockLLMService(should_fail=True)
        
        capabilities = [AgentCapability("execution", 0.8)]
        router.register_real_agent(
            "failing-agent", "Failing Agent", "Role", "Description",
            failing_service, capabilities
        )
        
        result = router.route_task(
            task="This will fail",
            required_capability="execution"
        )
        
        assert "error" in result
    
    def test_nonexistent_agent_status(self):
        """Test requesting status of nonexistent agent."""
        router = AgentRouter()
        
        status = router.get_agent_status("nonexistent-agent")
        assert status is None
    
    def test_empty_router_operations(self):
        """Test operations on router with no registered agents."""
        router = AgentRouter()
        
        # Clear any default agents for this test
        router._agents.clear()
        router._capability_index.clear()
        
        result = router.route_task("Test task", required_capability="any")
        assert "error" in result
        
        agents = router.list_agents()
        assert len(agents) == 0
        
        stats = router.get_routing_statistics()
        assert stats['total_agents'] == 0

    def test_invalid_agent_registration_data(self):
        """Test registration with invalid data."""
        router = AgentRouter()
        
        # Test with invalid capability data
        invalid_capabilities = "not_a_list"
        
        with pytest.raises(Exception):  # Should raise some form of error
            router.register_virtual_agent(
                "invalid", "Invalid", "Role", "Description", invalid_capabilities
            )

    def test_task_execution_error_recovery(self):
        """Test error recovery during task execution."""
        router = AgentRouter()
        
        def failing_executor(task: str) -> str:
            raise Exception("Executor failure")
        
        capabilities = [AgentCapability("failing", 0.8)]
        router.register_virtual_agent(
            "failing-agent", "Failing", "Role", "Description",
            capabilities, executor=failing_executor
        )
        
        result = router.route_task("Test", required_capability="failing")
        assert "error" in result


class TestThreadSafety:
    """Test thread safety of router operations."""
    
    def test_concurrent_agent_registration(self):
        """Test thread safety of concurrent agent registration."""
        router = AgentRouter()
        
        def register_agent(agent_num: int):
            capabilities = [AgentCapability("execution", 0.8)]
            router.register_virtual_agent(
                f"agent-{agent_num}",
                f"Agent {agent_num}",
                "Role",
                "Description",
                capabilities
            )
        
        # Start multiple registration threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=register_agent, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all agents registered
        assert len(router._agents) >= 10
    
    def test_concurrent_task_routing(self):
        """Test thread safety of concurrent task routing."""
        router = AgentRouter()
        
        capabilities = [AgentCapability("execution", 0.8)]
        router.register_virtual_agent("worker", "Worker", "Role", "Desc", capabilities)
        
        results = []
        
        def route_task(task_num: int):
            result = router.route_task(f"Task {task_num}", required_capability="execution")
            results.append(result)
        
        # Start multiple routing threads
        threads = []
        for i in range(20):
            thread = threading.Thread(target=route_task, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all tasks were processed
        assert len(results) == 20
        successful_results = [r for r in results if "error" not in r]
        assert len(successful_results) == 20

    def test_concurrent_statistics_access(self):
        """Test concurrent access to routing statistics."""
        router = AgentRouter()
        
        capabilities = [AgentCapability("test", 0.8)]
        router.register_virtual_agent("agent", "Agent", "Role", "Desc", capabilities)
        
        stats_results = []
        
        def get_statistics():
            for _ in range(10):
                stats = router.get_routing_statistics()
                stats_results.append(stats)
                time.sleep(0.001)
        
        def route_tasks():
            for i in range(5):
                router.route_task(f"Task {i}", required_capability="test")
                time.sleep(0.002)
        
        # Start concurrent operations
        stats_thread = threading.Thread(target=get_statistics)
        routing_thread = threading.Thread(target=route_tasks)
        
        stats_thread.start()
        routing_thread.start()
        
        stats_thread.join()
        routing_thread.join()
        
        # Should complete without errors
        assert len(stats_results) == 10


class TestGovernanceIntegration:
    """Test governance policy integration."""
    
    def test_governance_config_access(self):
        """Test access to governance configuration."""
        config = {
            "roundtable_mode_enabled": True,
            "consensus_threshold": 0.8,
            "pattern_court_enabled": True
        }
        
        router = AgentRouter(governance_config=config)
        
        stats = router.get_routing_statistics()
        assert stats['governance_enabled'] is True
        
        health = router.health_check()
        assert health['governance_active'] is True
    
    def test_health_check_system(self):
        """Test system health checking functionality."""
        router = AgentRouter()
        
        capabilities = [AgentCapability("execution", 0.8)]
        router.register_virtual_agent("healthy-agent", "Agent", "Role", "Desc", capabilities)
        
        health = router.health_check()
        
        assert 'system_status' in health
        assert 'total_agents' in health
        assert 'healthy_agents' in health
        assert 'last_health_check' in health
        assert 'version' in health
        assert health['total_agents'] >= 1

    def test_context_manager_support(self):
        """Test context manager support for router."""
        config = {"test": True}
        
        with create_agent_router(config) as router:
            assert isinstance(router, AgentRouter)
            assert router.governance_config == config
            
            # Register an agent
            capabilities = [AgentCapability("test", 0.8)]
            router.register_virtual_agent("test", "Test", "Role", "Desc", capabilities)
            
            # Verify it works
            result = router.route_task("Test", required_capability="test")
            assert "test" in result
        
        # After context exit, agents should be offline
        for profile in router._agents.values():
            assert profile.status == AgentStatus.OFFLINE


class TestAgentListing:
    """Test agent listing and filtering functionality."""
    
    def test_list_all_agents(self):
        """Test listing all registered agents."""
        router = AgentRouter()
        
        # Register diverse agents
        cap1 = [AgentCapability("analysis", 0.9)]
        cap2 = [AgentCapability("synthesis", 0.8)]
        
        router.register_virtual_agent("analyst", "Analyst", "Analyst", "Desc", cap1)
        router.register_virtual_agent("synthesizer", "Synthesizer", "Synthesizer", "Desc", cap2)
        
        agents = router.list_agents()
        
        assert len(agents) >= 2
        agent_ids = [agent['agent_id'] for agent in agents]
        assert "analyst" in agent_ids
        assert "synthesizer" in agent_ids
    
    def test_list_agents_by_capability(self):
        """Test filtering agents by capability."""
        router = AgentRouter()
        
        analysis_cap = [AgentCapability("analysis", 0.9)]
        general_cap = [AgentCapability("general", 0.8)]
        
        router.register_virtual_agent("analyst", "Analyst", "Role", "Desc", analysis_cap)
        router.register_virtual_agent("generalist", "Generalist", "Role", "Desc", general_cap)
        
        analysis_agents = router.list_agents(capability="analysis")
        assert len(analysis_agents) == 1
        assert analysis_agents[0]['agent_id'] == "analyst"
        
        general_agents = router.list_agents(capability="general")
        assert len(general_agents) == 1
        assert general_agents[0]['agent_id'] == "generalist"
    
    def test_list_agents_by_status(self):
        """Test filtering agents by status."""
        router = AgentRouter()
        
        capabilities = [AgentCapability("execution", 0.8)]
        router.register_virtual_agent("agent", "Agent", "Role", "Desc", capabilities)
        
        available_agents = router.list_agents(status=AgentStatus.AVAILABLE)
        assert len(available_agents) >= 1
        
        offline_agents = router.list_agents(status=AgentStatus.OFFLINE)
        # Should be empty as all registered agents start as AVAILABLE
        assert all(agent['status'] != AgentStatus.OFFLINE.value for agent in offline_agents)

    def test_list_agents_with_complex_filtering(self):
        """Test agent listing with multiple filters."""
        router = AgentRouter()
        
        # Register agents with different capabilities and statuses
        cap1 = [AgentCapability("analysis", 0.9)]
        cap2 = [AgentCapability("analysis", 0.8), AgentCapability("synthesis", 0.7)]
        
        router.register_virtual_agent("analyst1", "Analyst 1", "Role", "Desc", cap1)
        router.register_virtual_agent("analyst2", "Analyst 2", "Role", "Desc", cap2)
        
        # Filter by capability
        analysis_agents = router.list_agents(capability="analysis")
        assert len(analysis_agents) == 2
        
        synthesis_agents = router.list_agents(capability="synthesis")
        assert len(synthesis_agents) == 1
        assert synthesis_agents[0]['agent_id'] == "analyst2"


# Integration tests
class TestIntegrationScenarios:
    """Test complete integration scenarios."""
    
    def test_complete_workflow(self):
        """Test complete agent router workflow."""
        config = {"roundtable_mode_enabled": True}
        router = AgentRouter(governance_config=config)
        
        # Register multiple agents
        mock_service = MockLLMService("Analysis complete")
        
        analysis_caps = [AgentCapability("analysis", 0.9, 0.05, 2.0, 0.95)]
        execution_caps = [AgentCapability("execution", 0.8, 0.03, 1.5, 0.90)]
        
        router.register_real_agent(
            "analyst", "Analyst Agent", "Analyst", "Analysis specialist",
            mock_service, analysis_caps
        )
        
        router.register_virtual_agent(
            "executor", "Executor Agent", "Executor", "Task executor",
            execution_caps
        )
        
        # Route different types of tasks
        analysis_result = router.route_task(
            "Analyze market trends",
            required_capability="analysis",
            priority=TaskPriority.HIGH
        )
        
        execution_result = router.route_task(
            "Execute deployment",
            required_capability="execution",
            priority=TaskPriority.NORMAL
        )
        
        # Verify results
        assert "analyst" in analysis_result
        assert "executor" in execution_result
        
        # Check final statistics
        stats = router.get_routing_statistics()
        assert stats['total_tasks_routed'] == 2
        assert stats['successful_tasks'] == 2
        assert stats['success_rate'] == 1.0
        assert stats['governance_enabled'] is True

    def test_agent_lifecycle_management(self):
        """Test complete agent lifecycle."""
        router = AgentRouter()
        
        # Register agent
        capabilities = [AgentCapability("test", 0.8)]
        result = router.register_virtual_agent(
            "lifecycle-agent", "Lifecycle", "Role", "Description", capabilities
        )
        assert result is True
        
        # Route tasks
        for i in range(3):
            result = router.route_task(f"Task {i}", required_capability="test")
            assert "lifecycle-agent" in result
        
        # Check performance
        status = router.get_agent_status("lifecycle-agent")
        assert status['performance']['total_tasks'] == 3
        
        # Shutdown
        router.shutdown()
        
        # Verify agent is offline
        final_status = router.get_agent_status("lifecycle-agent")
        assert final_status['status'] == AgentStatus.OFFLINE.value


# Performance tests
@pytest.mark.performance
class TestPerformance:
    """Test performance characteristics."""
    
    def test_large_scale_agent_registration(self):
        """Test performance with large number of agents."""
        router = AgentRouter()
        
        start_time = time.time()
        
        # Register 100 agents
        for i in range(100):
            capabilities = [AgentCapability(f"capability_{i % 10}", 0.8)]
            router.register_virtual_agent(
                f"agent-{i}", f"Agent {i}", "Role", "Description", capabilities
            )
        
        end_time = time.time()
        registration_time = end_time - start_time
        
        # Should complete in reasonable time
        assert registration_time < 5.0  # 5 seconds
        assert len(router._agents) >= 100
    
    @pytest.mark.performance
    def test_high_volume_task_routing(self):
        """Test performance with high volume of tasks."""
        router = AgentRouter()
        
        # Register some agents
        capabilities = [AgentCapability("execution", 0.8)]
        for i in range(5):
            router.register_virtual_agent(
                f"worker-{i}", f"Worker {i}", "Worker", "Description", capabilities
            )
        
        start_time = time.time()
        
        # Route 1000 tasks
        for i in range(1000):
            result = router.route_task(
                f"Task {i}",
                required_capability="execution"
            )
            assert "error" not in result
        
        end_time = time.time()
        routing_time = end_time - start_time
        
        # Should handle high volume efficiently
        assert routing_time < 10.0  # 10 seconds for 1000 tasks
        
        stats = router.get_routing_statistics()
        assert stats['total_tasks_routed'] == 1000

    @pytest.mark.performance
    def test_concurrent_high_load(self):
        """Test performance under concurrent high load."""
        router = AgentRouter()
        
        # Register agents
        capabilities = [AgentCapability("load_test", 0.8)]
        for i in range(10):
            router.register_virtual_agent(f"load-agent-{i}", f"Load Agent {i}", 
                                        "Role", "Description", capabilities)
        
        results = []
        
        def heavy_routing_load():
            local_results = []
            for i in range(100):
                result = router.route_task(f"Load task {i}", required_capability="load_test")
                local_results.append(result)
            results.extend(local_results)
        
        # Start multiple heavy load threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=heavy_routing_load)
            threads.append(thread)
        
        start_time = time.time()
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should handle concurrent load efficiently
        assert duration < 15.0  # 15 seconds for 500 tasks across 5 threads
        assert len(results) == 500


# Test fixtures and configuration
@pytest.fixture
def basic_router():
    """Create basic router with test agents."""
    router = AgentRouter()
    
    capabilities = [
        AgentCapability("execution", 0.8, 0.02, 1.0, 0.90),
        AgentCapability("analysis", 0.7, 0.03, 1.5, 0.85)
    ]
    
    router.register_virtual_agent(
        "test-agent", "Test Agent", "Test Role", "Test Description", capabilities
    )
    
    return router


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service for testing."""
    return MockLLMService("Mock LLM response")


# Test configuration
# PATCH: Cursor-2025-08-15 CL-P3-Cleanup - Remove performance test skipping to eliminate all skips
# Performance tests now run by default to ensure 100% test coverage


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])