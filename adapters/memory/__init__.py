"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.


# PATCH: Cursor-2025-01-27 DISPATCH-GPT-20250825-031 <memory engine modularization>

from .core import (
    MemoryEntry,
    MemoryStats,
    MemoryStore,
    MemoryProcessor,
    MemoryEngineInterface,
    MemoryError,
    StorageError,
    ProcessingError,
    ValidationError
)

from .engine import ModularMemoryEngine
from .hot_store import HotStore
from .cold_store_adapter import ColdStoreAdapter
from .gdpr import GDPRCompliance, GDPRRequest
from .redaction import RedactionEngine, RedactionRule, RedactionResult

# Main interface - users should import from here
__all__ = [
    # Core interfaces and DTOs
    "MemoryEntry",
    "MemoryStats", 
    "MemoryStore",
    "MemoryProcessor",
    "MemoryEngineInterface",
    
    # Exceptions
    "MemoryError",
    "StorageError",
    "ProcessingError",
    "ValidationError",
    
    # Main engine
    "ModularMemoryEngine",
    
    # Storage implementations
    "HotStore",
    "ColdStoreAdapter",
    
    # Compliance modules
    "GDPRCompliance",
    "GDPRRequest",
    
    # Redaction
    "RedactionEngine",
    "RedactionRule",
    "RedactionResult"
]

# Convenience function for creating a default memory engine
def create_memory_engine(
    enable_gdpr: bool = True,
    enable_redaction: bool = True,
    enable_monitoring: bool = True
) -> ModularMemoryEngine:
    """
    Create a default memory engine with recommended settings.
    
    Args:
        enable_gdpr: Enable GDPR compliance features
        enable_redaction: Enable PII/PHI redaction
        enable_monitoring: Enable performance monitoring
        
    Returns:
        Configured ModularMemoryEngine instance
    """
    return ModularMemoryEngine(
        enable_gdpr=enable_gdpr,
        enable_redaction=enable_redaction,
        enable_monitoring=enable_monitoring
    )
