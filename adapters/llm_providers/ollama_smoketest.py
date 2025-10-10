""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

"""
Enhanced Ollama Smoketest Module for IOA Core

Provides comprehensive Ollama testing with deterministic model selection,
turbo preset, warm-loading, and hardened diagnostics for smoketest integration.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .ollama_utils import (
    OllamaModelSelector, 
    OllamaTurboPreset, 
    OllamaWarmLoader, 
    OllamaInferenceTester,
    get_ollama_mode,
    export_smoketest_model,
    check_ollama_health
)

# PATCH: Cursor-2025-09-07 DISPATCH-OSS-20250907-OLLAMA-FIX <add enhanced Ollama smoketest>

logger = logging.getLogger(__name__)


class OllamaSmoketest:
    """Enhanced Ollama smoketest with deterministic model selection and turbo preset."""
    
    def __init__(self, artifacts_dir: Path):
        self.artifacts_dir = artifacts_dir
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.model_selector = OllamaModelSelector(artifacts_dir)
        self.warm_loader = OllamaWarmLoader(artifacts_dir)
        self.inference_tester = OllamaInferenceTester(artifacts_dir)
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """
        Run comprehensive Ollama smoketest with all enhancements.
        
        PATCH: Cursor-2025-09-08 DISPATCH-OSS-20250908-OLLAMA-TURBO-VERIFY <add mode-specific testing>
        
        Returns:
            Dictionary with complete test results
        """
        # Get the current mode
        mode = get_ollama_mode()
        
        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "provider": "ollama",
            "mode": mode,
            "status": "failed",
            "model_selection": {},
            "warm_load": {},
            "inference_test": {},
            "diagnostics": {},
            "summary": {}
        }
        
        try:
            # Step 0: Health check
            logger.info("Step 0: Checking Ollama health...")
            host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            health_results = check_ollama_health(host)
            results["health_check"] = health_results
            
            # For turbo_cloud mode, check if cloud is properly configured
            if mode == "turbo_cloud":
                from .ollama_utils import _is_turbo_cloud_configured
                if not _is_turbo_cloud_configured():
                    results["status"] = "skipped"
                    results["summary"]["error"] = "cloud_not_configured"
                    results["summary"]["detection"] = {
                        "base_present": bool(os.getenv("OLLAMA_API_BASE")),
                        "key_present": bool(os.getenv("OLLAMA_API_KEY"))
                    }
                    self._write_mode_transcript(results, "turbo_cloud")
                    return results
            
            if health_results["status"] != "success":
                results["summary"]["error"] = f"Ollama health check failed: {health_results.get('error', 'unknown error')}"
                return results
            
            # Step 1: Detect and select model
            logger.info("Step 1: Detecting installed Ollama models...")
            detection_results = self.model_selector.detect_installed_models()
            results["diagnostics"] = detection_results
            
            selected_model = self.model_selector.select_model(detection_results)
            results["model_selection"] = {
                "selected_model": selected_model,
                "available_models": detection_results.get("models", []),
                "status": "success" if selected_model else "failed"
            }
            
                results["summary"]["error"] = "No suitable Ollama models found"
                return results
            
            # Export model for smoketest session
            export_smoketest_model(selected_model)
            
            # Set mode for smoketest (will be overridden by CLI if specified)
            if mode == "turbo_cloud":
                os.environ["IOA_OLLAMA_MODE"] = "turbo_cloud"
            else:
                os.environ["IOA_OLLAMA_MODE"] = "local_preset"
            
            # Step 2: Warm-load model
            logger.info(f"Step 2: Warm-loading model {selected_model}...")
            warm_load_results = self.warm_loader.warm_load_model(selected_model, host)
            results["warm_load"] = warm_load_results
            
            # Check if warm-load failed due to timeout
            if warm_load_results["status"] != "success":
                results["summary"]["error"] = f"Warm-load failed: {warm_load_results.get('error', 'unknown error')}"
                return results
            
            # Step 3: Test inference with turbo preset
            logger.info(f"Step 3: Testing inference with {selected_model} in turbo mode...")
            mode = get_ollama_mode()
            inference_results = self.inference_tester.test_inference(selected_model, host, mode)
            results["inference_test"] = inference_results
            
            # Determine overall status
            if (results["health_check"]["status"] == "success" and
                results["model_selection"]["status"] == "success" and 
                results["warm_load"]["status"] == "success" and
                results["inference_test"]["status"] == "success"):
                results["status"] = "success"
                results["summary"]["message"] = f"Ollama smoketest PASSED with {selected_model} in {mode} mode"
            else:
                results["status"] = "failed"
                results["summary"]["message"] = "Ollama smoketest FAILED"
                
                # Identify the first failure
                if results["health_check"]["status"] != "success":
                    results["summary"]["error"] = f"Health check failed: {results['health_check'].get('error', 'unknown error')}"
                elif results["model_selection"]["status"] != "success":
                    results["summary"]["error"] = "Model selection failed"
                elif results["warm_load"]["status"] != "success":
                    results["summary"]["error"] = f"Warm-load failed: {results['warm_load'].get('error', 'unknown error')}"
                elif results["inference_test"].get("error"):
                    results["summary"]["error"] = results["inference_test"]["error"]
            
            # Add performance metrics
            results["summary"]["health_latency_ms"] = results["health_check"].get("latency_ms", 0)
            results["summary"]["warm_load_latency_ms"] = results["warm_load"].get("latency_ms", 0)
            results["summary"]["inference_latency_ms"] = results["inference_test"].get("latency_ms", 0)
            results["summary"]["total_latency_ms"] = (
                results["summary"]["health_latency_ms"] + 
                results["summary"]["warm_load_latency_ms"] + 
                results["summary"]["inference_latency_ms"]
            )
            
        except Exception as e:
            logger.error(f"Ollama smoketest exception: {e}")
            results["status"] = "failed"
            results["summary"]["error"] = str(e)
        
        # Write comprehensive results
        self._write_results(results)
        
        # Write mode-specific transcript
        self._write_mode_transcript(results, mode)
        
        return results
    
    def _write_results(self, results: Dict[str, Any]) -> None:
        """Write comprehensive test results to artifacts."""
        try:
            results_path = self.artifacts_dir / "ollama_smoketest_results.json"
            with results_path.open('w') as f:
                json.dump(results, f, indent=2)
            logger.debug(f"Written Ollama smoketest results: {results_path}")
        except Exception as e:
            logger.warning(f"Failed to write Ollama smoketest results: {e}")
    
    def _write_mode_transcript(self, results: Dict[str, Any], mode: str) -> None:
        """
        Write mode-specific transcript for turbo verification.
        
        PATCH: Cursor-2025-09-08 DISPATCH-OSS-20250908-OLLAMA-TURBO-VERIFY <add mode transcripts>
        """
        try:
            # Create mode-specific transcript
            transcript = {
                "provider": "ollama",
                "mode": mode,
                "model_used": results.get("model_selection", {}).get("selected_model", "unknown"),
                "http_status": 200 if results.get("status") == "success" else None,
                "latency_ms": results.get("summary", {}).get("total_latency_ms", 0),
                "in_tokens": 0,  # Ollama doesn't provide token counts in response
                "out_tokens": 0,
                "completion_text": results.get("inference_test", {}).get("response", ""),
                "notes": results.get("summary", {}).get("message", ""),
                "timestamp": results.get("timestamp", ""),
                "status": results.get("status", "failed")
            }
            
            # Add error details if failed
            if results.get("status") == "failed":
                transcript["error"] = results.get("summary", {}).get("error", "unknown error")
            elif results.get("status") == "skipped":
                transcript["skip_reason"] = results.get("summary", {}).get("error", "unknown reason")
                if "detection" in results.get("summary", {}):
                    transcript["detection_details"] = results["summary"]["detection"]
            
            # Write transcript
            transcript_path = self.artifacts_dir / f"mode_{mode}_hello.json"
            with transcript_path.open('w') as f:
                json.dump(transcript, f, indent=2)
            logger.debug(f"Written mode transcript: {transcript_path}")
            
        except Exception as e:
            logger.warning(f"Failed to write mode transcript: {e}")


def run_ollama_smoketest(artifacts_dir: Path) -> Dict[str, Any]:
    """
    Run enhanced Ollama smoketest.
    
    Args:
        artifacts_dir: Directory to write artifacts and results
        
    Returns:
        Dictionary with test results
    """
    smoketest = OllamaSmoketest(artifacts_dir)
    return smoketest.run_comprehensive_test()


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
        "notes": f"Ollama {mode_label} mode detected"
    }
