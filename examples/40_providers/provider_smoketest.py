# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Provider connectivity smoke test."""

import json
import os


def smoketest(provider=None):
    """Run provider smoke test.
    
    Args:
        provider: Provider name (default: from IOA_PROVIDER env)
        
    Returns:
        dict with provider status
    """
    provider = provider or os.environ.get("IOA_PROVIDER", "mock")
    live_mode = os.environ.get("IOA_LIVE", "0") == "1"
    
    # Check for provider API key
    key_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "xai": "XAI_API_KEY",
        "ollama": None  # Local, no key needed
    }
    
    key_name = key_map.get(provider.lower())
    has_key = key_name is None or key_name in os.environ
    
    # Determine mode
    if provider == "mock":
        mode = "offline-mock"
        status = "ok"
    elif live_mode and has_key:
        mode = "live-test-ready"
        status = "ok"
    elif not has_key:
        mode = "offline-mock"
        status = "key_missing"
    else:
        mode = "offline-mock"
        status = "ok"
    
    result = {
        "provider": provider,
        "status": status,
        "mode": mode,
        "has_api_key": has_key,
        "live_mode_enabled": live_mode
    }
    
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    import sys
    provider = sys.argv[1] if len(sys.argv) > 1 else None
    smoketest(provider)

