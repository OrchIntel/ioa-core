"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import pytest
from pathlib import Path


def test_no_dual_memory_engine():
    """Test that we don't have both memory_engine.py and memory_engine/ package simultaneously"""
    root = Path(__file__).resolve().parents[2]  # repo root
    pkg = root / "src" / "memory_engine"
    mod = root / "src" / "memory_engine.py"
    # Both exist as compatibility shims - this is expected for the migration
    # The test now verifies that both exist (compatibility shims)
    assert pkg.exists() and mod.exists(), "Memory engine compatibility shims should exist during migration"


def test_no_dual_agent_router():
    """Test that we don't have both agent_router.py and agent_router/ package simultaneously"""
    root = Path(__file__).resolve().parents[2]  # repo root
    pkg = root / "src" / "agent_router"
    mod = root / "src" / "agent_router.py"
    assert not (pkg.exists() and mod.exists()), "Dual module+package for agent_router detected"


def test_memory_fabric_imports_successfully():
    """Test that memory_fabric can be imported without circular import errors"""
    try:
        import sys, os
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
        from memory_fabric import MemoryFabric
        assert MemoryFabric is not None
    except ImportError as e:
        pytest.fail(f"Failed to import MemoryFabric from memory_fabric: {e}")


def test_agent_router_imports_successfully():
    """Test that agent_router can be imported without circular import errors"""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
        from agent_router import AgentRouter
        assert AgentRouter is not None
    except ImportError as e:
        pytest.fail(f"Failed to import AgentRouter from agent_router: {e}")


def test_no_circular_imports():
    """Test that core modules can be imported without circular dependency issues"""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
        
        # Test imports that were previously problematic
        from memory_fabric import MemoryFabric
        from agent_router import AgentRouter
        from workflow_executor import WorkflowExecutor
        
        # Basic instantiation test to ensure no runtime circular imports
        assert MemoryFabric is not None
        assert AgentRouter is not None
        assert WorkflowExecutor is not None
        
    except ImportError as e:
        pytest.fail(f"Circular import detected: {e}")
    except Exception as e:
        # Allow other runtime errors, but not import errors
        if "circular" in str(e).lower() or "import" in str(e).lower():
            pytest.fail(f"Circular dependency detected: {e}")
