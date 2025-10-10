"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""ioa_core package namespace.

Provides compatibility re-exports for top-level modules so installed package
imports like `ioa_core.llm_manager` and `ioa_core.llm_adapter` resolve
without requiring PYTHONPATH hacks.
"""

__all__ = [
    "__version__",
]

# Optional version shim; kept minimal to avoid import side-effects
try:
    from .version import __version__  # type: ignore
except Exception:
    __version__ = "2.5.0"


"""
IOA Core Package

Intelligent Orchestration Architecture Core - Open-source platform for 
orchestrating modular AI agents with memory-driven collaboration and 
governance mechanisms.
"""

__version__ = "2.5.0"
__author__ = "IOA Project Contributors"
__license__ = "Apache-2.0"

# Import key modules for easy access
try:
    from .cli import main

    __all__ = ["main"]
except ImportError:
    # CLI not available in this environment
    __all__ = []
