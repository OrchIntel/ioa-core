# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Ollama turbo mode performance demonstration."""

import json
import time


def run(mode="turbo_cloud"):
    """Demonstrate Ollama turbo mode with mock performance metrics.
    
    Args:
        mode: "turbo_cloud" or "local_preset"
        
    Returns:
        dict with performance metrics
    """
    # Mock performance delta (real results depend on hardware)
    # Turbo mode typically 20-40% faster
    t0 = time.time()
    
    if mode == "turbo_cloud":
        time.sleep(0.02)  # Simulate faster execution
        expected_improvement = "20-40%"
    else:
        time.sleep(0.04)  # Simulate baseline execution
        expected_improvement = "baseline"
    
    elapsed_ms = int((time.time() - t0) * 1000)
    
    result = {
        "mode": mode,
        "p50_ms": elapsed_ms,
        "expected_improvement": expected_improvement,
        "note": "Real performance depends on local hardware (CPU, GPU, RAM)",
        "optimizations": {
            "reduced_context_window": mode == "turbo_cloud",
            "lower_temperature": mode == "turbo_cloud",
            "optimized_batch_size": mode == "turbo_cloud"
        }
    }
    
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "turbo_cloud"
    run(mode)

