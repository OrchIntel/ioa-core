""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3
"""

PATCH: Cursor-2025-09-08 DISPATCH-OSS-20250908-DEMO-ROUNDTABLE
Fallback script for multi-agent roundtable demo.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ioa_core.demo_roundtable import run_roundtable_demo

if __name__ == "__main__":
    # Get environment variables
    non_interactive = os.getenv("IOA_SMOKETEST_NON_INTERACTIVE", "0") == "1"
    live = os.getenv("IOA_SMOKETEST_LIVE", "0") == "1"
    max_usd = float(os.getenv("IOA_SMOKETEST_MAX_USD", "0.10"))
    timeout_ms = int(os.getenv("IOA_SMOKETEST_TIMEOUT_MS", "12000"))
    
    # Model overrides from environment
    model_overrides = {}
    if os.getenv("OPENAI_MODEL"):
        model_overrides["openai"] = os.getenv("OPENAI_MODEL")
    if os.getenv("ANTHROPIC_MODEL"):
        model_overrides["anthropic"] = os.getenv("ANTHROPIC_MODEL")
    if os.getenv("GEMINI_MODEL"):
        model_overrides["google"] = os.getenv("GEMINI_MODEL")
    if os.getenv("DEEPSEEK_MODEL"):
        model_overrides["deepseek"] = os.getenv("DEEPSEEK_MODEL")
    if os.getenv("XAI_MODEL"):
        model_overrides["xai"] = os.getenv("XAI_MODEL")
    
    try:
        run_roundtable_demo(
            timeout_ms=timeout_ms,
            max_usd=max_usd,
            non_interactive=non_interactive,
            live=live,
            model_overrides=model_overrides
        )
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        sys.exit(1)
