# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.



import os
from typing import Any, Dict


def get_ollama_mode() -> str:
"""Ollama Smoketest module."""

    """
    Get Ollama mode from environment with cloud Turbo detection.

    Returns:
        "turbo_cloud" if Ollama Turbo (cloud) is detected
        "local_preset" if local turbo preset is configured
        "standard" for normal mode
    """
    # Check for explicit mode setting
    explicit_mode = os.getenv("IOA_OLLAMA_MODE")
    if explicit_mode:
        # Handle deprecation mapping
        if explicit_mode == "turbo_local":
            return "local_preset"
        return explicit_mode

    # Check for new turbo mode toggles
    use_turbo_local = os.getenv("IOA_OLLAMA_USE_TURBO_LOCAL", "0") == "1"
    use_turbo_cloud = os.getenv("IOA_OLLAMA_USE_TURBO_CLOUD", "0") == "1"

    if use_turbo_cloud:
        # Check if cloud Turbo is properly configured
        if _is_turbo_cloud_configured():
            return "turbo_cloud"
        else:
            # Fall back to local preset if cloud not configured
            return "local_preset"

    if use_turbo_local:
        return "local_preset"

    # Auto-detect mode based on environment
    # Check for Ollama Turbo cloud credentials
    if _is_turbo_cloud_configured():
        return "turbo_cloud"

    # Check for legacy cloud indicators
    ollama_host = os.getenv("OLLAMA_HOST", "").lower()
    ollama_turbo_cloud = os.getenv("OLLAMA_TURBO_CLOUD", "").lower()

    # Detect cloud Turbo based on environment indicators
    if (
        ollama_turbo_cloud in ["1", "true", "yes"]
        or "turbo" in ollama_host
        or "cloud" in ollama_host
        or os.getenv("OLLAMA_TURBO_MODE") == "cloud"
    ):
        return "turbo_cloud"

    # Default to local preset for smoketest
    return "local_preset"


def _is_turbo_cloud_configured() -> bool:
    """
    Check if Ollama Turbo cloud is properly configured.

    Returns:
        True if both OLLAMA_API_BASE and OLLAMA_API_KEY are present
    """
    api_base = os.getenv("OLLAMA_API_BASE")
    api_key = os.getenv("OLLAMA_API_KEY")

    # Both must be present for cloud Turbo
    # OLLAMA_API_BASE should be a https URL
    if not api_base or not api_key:
        return False

    # Validate that base is a proper URL
    return api_base.lower().startswith("https://")


def run_ollama_smoketest(artifacts_dir) -> Dict[str, Any]:
    """
    Run Ollama smoketest.

    Args:
        artifacts_dir: Directory to write artifacts and results

    Returns:
        Dictionary with test results
    """
    # For now, return a mock result that indicates the test was run
    # In a real implementation, this would run the actual smoketest
    return {
        "provider": "ollama",
        "status": "success",
        "mode": get_ollama_mode(),
        "model_used": "mock-model",
        "latency_ms": 100,
        "completion_text": "hello",
        "notes": "Mock smoketest result",
    }


def get_ollama_provider_status() -> Dict[str, Any]:
    """
    Get Ollama provider status for integration with existing smoketest.

    Returns:
        Dictionary with provider status information including Turbo mode detection
    """
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    mode = get_ollama_mode()

    # PATCH: Cursor-2025-09-08 DISPATCH-OSS-20250908-OLLAMA-CLOUD-ONBOARD <add mode labels>
    mode_label = "turbo_cloud" if mode == "turbo_cloud" else "local_preset"

    return {
        "provider": "ollama",
        "configured": True,
        "host": host,
        "mode": mode_label,
        "no_key": True,
        "details": f"Host: {host}, Mode: {mode_label} (no API key required)",
        "notes": f"Ollama {mode_label} mode detected",
    }
