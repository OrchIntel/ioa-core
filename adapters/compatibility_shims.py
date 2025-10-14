"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.


# PATCH: Cursor-2025-08-21 DISPATCH-GPT-20250821-007 <agent-to-model terminology refactor>

"""
Backward Compatibility Shims for Agent → Model Terminology Refactor

This module provides backward compatibility for code that still uses the old
"agent" terminology when referring to LLM services. These shims will emit
deprecation warnings when IOA_EMIT_LEGACY_WARNINGS=1 is set.

Usage:
    # Old way (deprecated)
    from compatibility_shims import AgentAdapter
    agent = AgentAdapter()
    
    # New way
    from llm_adapter import ModelAdapter
    model = ModelAdapter()
"""

import os
import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from llm_adapter import LLMService, OpenAIService
    from llm_manager import LLMManager

def _emit_deprecation_warning(old_name: str, new_name: str, module: str = "unknown"):
    """Emit deprecation warning if legacy warnings are enabled."""
    if os.getenv("IOA_EMIT_LEGACY_WARNINGS") == "1":
        warnings.warn(
            f"{old_name} is deprecated and will be removed in a future version. "
            f"Use {new_name} from {module} instead.",
            DeprecationWarning,
            stacklevel=3
        )

# LLM Service Compatibility Shims
class AgentAdapter:
    """Deprecated: Use ModelAdapter from llm_adapter instead."""
    
    def __init__(self, *args, **kwargs):
        _emit_deprecation_warning("AgentAdapter", "ModelAdapter", "src.llm_adapter")
        from llm_adapter import LLMService
        self._service = LLMService(*args, **kwargs)
    
    def __getattr__(self, name):
        return getattr(self._service, name)

    """Deprecated: Use LLMModel from llm_adapter instead."""
    
    def __init__(self, *args, **kwargs):
        _emit_deprecation_warning("LLMAgent", "LLMModel", "src.llm_adapter")
        from llm_adapter import LLMService
        self._service = LLMService(*args, **kwargs)
    
    def __getattr__(self, name):
        return getattr(self._service, name)

# LLM Manager Compatibility Shims
class AgentManager:
    """Deprecated: Use ModelManager from llm_manager instead."""
    
    def __init__(self, *args, **kwargs):
        _emit_deprecation_warning("AgentManager", "ModelManager", "src.llm_manager")
        from llm_manager import LLMManager
        self._manager = LLMManager(*args, **kwargs)
    
    def __getattr__(self, name):
        return getattr(self._manager, name)

# Configuration Compatibility Shims
def get_agent_config():
    """Deprecated: Use get_model_config() instead."""
    _emit_deprecation_warning("get_agent_config", "get_model_config", "src.config.loader")
    from config.loader import get_model_config
    return get_model_config()

# Test Compatibility Shims
class MockAgentService:
    """Deprecated: Use MockModelService instead."""
    
    def __init__(self, *args, **kwargs):
        _emit_deprecation_warning("MockAgentService", "MockModelService", "tests")
        from tests.test_agent_router_final import MockLLMService
        self._service = MockLLMService(*args, **kwargs)
    
    def __getattr__(self, name):
        return getattr(self._service, name)

# Export all shims for backward compatibility
__all__ = [
    "AgentAdapter",
    "LLMAgent", 
    "AgentManager",
    "get_agent_config",
    "MockAgentService"
]
