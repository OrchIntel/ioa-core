"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
# PATCH: Cursor-2025-09-11 DISPATCH-OSS-20250911-MEMORY-DOCSYNC <memory fabric migration>
# This file is now a backward compatibility shim for memory_fabric.
# New code should import from memory_fabric instead.
"""

import warnings
import os
import logging
from typing import Dict, List, Any, Optional, Union

# PATCH: Cursor-2025-09-11 DISPATCH-OSS-20250911-MEMORY-DOCSYNC <memory fabric migration>
# Import from memory_fabric
try:
    from memory_fabric import (
        MemoryFabric, MemoryRecordV1, EmbeddingV1,
        MemoryStore, LocalJSONLStore, SQLiteStore, S3Store,
        MemoryFabricMetrics, MemoryCrypto
    )
    MEMORY_FABRIC_AVAILABLE = True
except ImportError:
    MEMORY_FABRIC_AVAILABLE = False
    # Fallback imports for backward compatibility
    MemoryFabric = None
    MemoryRecordV1 = None
    MemoryStats = None
    MemoryError = Exception
    StorageError = Exception
    ProcessingError = Exception
    GDPRRequest = None

# Deprecation warnings are opt-in to keep CI zero-warning by default.
# Set IOA_EMIT_LEGACY_WARNINGS=1 locally to surface deprecation guidance.
if os.getenv("IOA_EMIT_LEGACY_WARNINGS") == "1" and os.getenv("IOA_SHIM_IMPORT") != "1":
    warnings.warn(
        "src.memory_engine is deprecated. Use memory_fabric.MemoryFabric instead.",
        DeprecationWarning,
        stacklevel=2
    )

# Monorepo transition warning (opt-in; see above)
if os.getenv("IOA_EMIT_LEGACY_WARNINGS") == "1" and os.getenv("IOA_SHIM_IMPORT") != "1":
    warnings.warn(
        "src.memory_engine import path is deprecated. Use memory_fabric for future compatibility.",
        DeprecationWarning,
        stacklevel=2
    )

# Backward compatibility shim
if MEMORY_FABRIC_AVAILABLE:
    # Simple shim that delegates to memory_fabric
    MemoryEngine = MemoryFabric
    MemoryEngineError = Exception
    StorageError = Exception
    PreservationError = Exception
    IntegrationError = Exception
else:
    # Fallback to stub implementation
    class MemoryEngine:
        """Stub implementation for backward compatibility."""
        
        def __init__(self, *args, **kwargs):
            warnings.warn(
                "Core memory engine not available. Using stub implementation.",
                RuntimeWarning,
                stacklevel=2
            )
            self.logger = logging.getLogger(__name__)
        
        def remember(self, *args, **kwargs):
            raise NotImplementedError("Core memory engine not available")
        
        def retrieve(self, *args, **kwargs):
            raise NotImplementedError("Core memory engine not available")
        
        def forget(self, *args, **kwargs):
            raise NotImplementedError("Core memory engine not available")
        
        def export_user(self, *args, **kwargs):
            raise NotImplementedError("Core memory engine not available")
        
        def forget_user(self, *args, **kwargs):
            raise NotImplementedError("Core memory engine not available")
        
        def audit_forget(self, *args, **kwargs):
            raise NotImplementedError("Core memory engine not available")
        
        def stats(self, *args, **kwargs):
            raise NotImplementedError("Core memory engine not available")
        
        def list_all(self, *args, **kwargs):
            raise NotImplementedError("Core memory engine not available")
    
    # Stub exception classes
    class MemoryEngineError(Exception):
        pass
    
    class StorageError(Exception):
        pass
    
    class PreservationError(Exception):
        pass
    
    class IntegrationError(Exception):
        pass

# Export the main class for backward compatibility
__all__ = [
    "MemoryEngine",
    "MemoryEngineError", 
    "StorageError",
    "PreservationError",
    "IntegrationError"
]

# PATCH: Cursor-2025-08-21 DISPATCH-GPT-20250821-008
# Add soft-redirect to 33D modular engine when available
try:
    from ioa.memory.engine import MemoryEngine as MemoryEngine33D  # noqa: F401
except Exception:
    pass

