# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""System health check - verify IOA Core environment."""

import json
import os
import sys
from pathlib import Path


def check_python_version():
    """Check if Python version meets requirements."""
    version = sys.version_info
    return version >= (3, 10)


def check_provider_keys():
    """Check which provider API keys are configured."""
    providers = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "DEEPSEEK_API_KEY",
        "XAI_API_KEY"
    ]
    
    return {
        k: ("***" if k in os.environ else None)
        for k in providers
    }


def check_cache_writeable():
    """Check if local cache directory is writeable."""
    try:
        cache_dir = Path.home() / ".ioa" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        test_file = cache_dir / ".test_write"
        test_file.write_text("test")
        test_file.unlink()
        return True
    except Exception:
        return False


def doctor():
    """Run system health checks."""
    checks = {
        "python_version_ok": check_python_version(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "env_provider_keys": check_provider_keys(),
        "local_cache_writeable": check_cache_writeable(),
        "ioa_core_version": "2.5.1",
        "platform": sys.platform
    }
    
    # Determine overall health
    critical_ok = (
        checks["python_version_ok"] and
        checks["local_cache_writeable"]
    )
    
    checks["overall_health"] = "healthy" if critical_ok else "issues_detected"
    
    print(json.dumps(checks, indent=2))
    return checks


if __name__ == "__main__":
    doctor()

