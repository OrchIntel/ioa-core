"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

"""
Ollama Utilities Module for IOA Core

Provides deterministic model selection, turbo preset configuration, and
diagnostic utilities for Ollama service integration.
"""

import os
import json
import subprocess
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

# PATCH: Cursor-2025-09-07 DISPATCH-OSS-20250907-OLLAMA-FIX <add Ollama utilities>

logger = logging.getLogger(__name__)


class OllamaModelSelector:
    """Deterministic model selection for Ollama without remote pulls."""
    
    def __init__(self, artifacts_dir: Path):
        self.artifacts_dir = artifacts_dir
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    def detect_installed_models(self) -> Dict[str, Any]:
        """
        Detect installed Ollama models and capture system info.
        
        Returns:
            Dictionary with model detection results
        """
        results = {
            "ollama_list": None,
            "ollama_tags": None,
            "ollama_version": None,
            "sysinfo": None,
            "models": []
        }
        
        try:
            # Capture ollama list
            try:
                result = subprocess.run(
                    ["ollama", "list"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                if result.returncode == 0:
                    results["ollama_list"] = result.stdout.strip()
                    self._write_artifact("ollama_list.txt", result.stdout)
                else:
                    logger.warning(f"ollama list failed: {result.stderr}")
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                logger.warning(f"ollama list command failed: {e}")
            
            # Capture ollama API tags
            try:
                import requests
                host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
                response = requests.get(f"{host}/api/tags", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    results["ollama_tags"] = data
                    self._write_artifact("ollama_tags.json", json.dumps(data, indent=2))
                    
                    # Extract model names
                    for model in data.get("models", []):
                        results["models"].append({
                            "name": model.get("name", ""),
                            "size": model.get("size", 0),
                            "modified_at": model.get("modified_at", "")
                        })
                else:
                    logger.warning(f"Ollama API tags failed: {response.status_code}")
            except Exception as e:
                logger.warning(f"Ollama API tags request failed: {e}")
            
            # Capture ollama version
            try:
                import requests
                host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
                response = requests.get(f"{host}/api/version", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    results["ollama_version"] = data
                    self._write_artifact("ollama_version.json", json.dumps(data, indent=2))
                else:
                    logger.warning(f"Ollama API version failed: {response.status_code}")
            except Exception as e:
                logger.warning(f"Ollama API version request failed: {e}")
            
            # Capture system info
            try:
                sysinfo_lines = []
                
                # uname -a
                try:
                    result = subprocess.run(["uname", "-a"], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        sysinfo_lines.append(result.stdout.strip())
                except Exception:
                    pass
                
                # uptime
                try:
                    result = subprocess.run(["uptime"], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        sysinfo_lines.append(result.stdout.strip())
                except Exception:
                    pass
                
                if sysinfo_lines:
                    sysinfo = "\n".join(sysinfo_lines)
                    results["sysinfo"] = sysinfo
                    self._write_artifact("sysinfo.txt", sysinfo)
            except Exception as e:
                logger.warning(f"System info capture failed: {e}")
            
        except Exception as e:
            logger.error(f"Model detection failed: {e}")
        
        return results
    
    def select_model(self, detection_results: Dict[str, Any]) -> Optional[str]:
        """
        Select the best available model using deterministic policy.
        
        Policy (first present wins):
        1. llama3.1:8b
        2. gpt-oss:20b  
        3. Any other installed model (prefer smaller by parameter size)
        
        Args:
            detection_results: Results from detect_installed_models()
            
        Returns:
            Selected model name or None if no models available
        """
        models = detection_results.get("models", [])
        if not models:
            logger.warning("No Ollama models detected")
            return None
        
        # Policy 1: Prefer llama3.1:8b
        for model in models:
            if "llama3.1:8b" in model.get("name", ""):
                return model["name"]
        
        # Policy 2: Prefer gpt-oss:20b
        for model in models:
            if "gpt-oss:20b" in model.get("name", ""):
                return model["name"]
        
        # Policy 3: Any other model (prefer smaller by size)
        if models:
            # Sort by size (ascending) to prefer smaller models
            sorted_models = sorted(models, key=lambda x: x.get("size", float('inf')))
            selected = sorted_models[0]
            return selected["name"]
        
        return None
    
    def _write_artifact(self, filename: str, content: str) -> None:
        """Write content to artifacts directory."""
        try:
            artifact_path = self.artifacts_dir / filename
            with artifact_path.open('w') as f:
                f.write(content)
            logger.debug(f"Written artifact: {artifact_path}")
        except Exception as e:
            logger.warning(f"Failed to write artifact {filename}: {e}")


class OllamaTurboPreset:
    """Turbo preset configuration for low-latency Ollama inference."""
    
    @staticmethod
    def get_turbo_local_options() -> Dict[str, Any]:
        """
        Get turbo_local preset options for low-latency local inference.
        
        PATCH: Cursor-2025-09-08 DISPATCH-OSS-20250908-OLLAMA-TURBO-VERIFY <add turbo_local preset>
        
        Returns:
            Dictionary of Ollama API options for turbo_local mode
        """
        return {
            "num_predict": int(os.getenv("IOA_OLLAMA_NUM_PREDICT", "16")),
            "temperature": 0.0,
            "top_p": 0.9,
            "repeat_penalty": 1.05,
            "num_ctx": 2048,
            "num_thread": int(os.getenv("IOA_OLLAMA_NUM_THREADS", "0")),  # 0 = auto
            "cache": True,
            "mirostat": 0,
            "keep_alive": "5m"
        }
    
    @staticmethod
    def get_turbo_cloud_options() -> Dict[str, Any]:
        """
        Get turbo_cloud preset options for cloud-backed accelerated inference.
        
        PATCH: Cursor-2025-09-08 DISPATCH-OSS-20250908-OLLAMA-TURBO-VERIFY <add turbo_cloud preset>
        
        Returns:
            Dictionary of Ollama API options for turbo_cloud mode
        """
        return {
            "num_predict": int(os.getenv("IOA_OLLAMA_NUM_PREDICT", "16")),
            "temperature": 0.0,
            "top_p": 0.9,
            "repeat_penalty": 1.05,
            "num_ctx": 2048,
            "num_thread": int(os.getenv("IOA_OLLAMA_NUM_THREADS", "0")),  # 0 = auto
            "cache": True,
            "mirostat": 0
        }
    
    @staticmethod
    def get_turbo_options() -> Dict[str, Any]:
        """
        Get turbo preset options for low-latency inference (legacy compatibility).
        
        Returns:
            Dictionary of Ollama API options for turbo mode
        """
        return OllamaTurboPreset.get_turbo_local_options()
    
    @staticmethod
    def get_standard_options() -> Dict[str, Any]:
        """
        Get standard preset options for normal inference.
        
        Returns:
            Dictionary of Ollama API options for standard mode
        """
        return {
            "num_predict": int(os.getenv("IOA_OLLAMA_NUM_PREDICT", "100")),
            "temperature": 0.7,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
            "num_ctx": 4096,
            "num_thread": int(os.getenv("IOA_OLLAMA_NUM_THREADS", "0")),  # 0 = auto
            "cache": True,
            "mirostat": 0
        }


class OllamaWarmLoader:
    """Warm-load Ollama models for pre-caching."""
    
    def __init__(self, artifacts_dir: Path):
        self.artifacts_dir = artifacts_dir
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
    
        """
        Warm-load a model with a tiny prompt to pre-cache pages.
        
        PATCH: Cursor-2025-09-08 DISPATCH-OSS-20250908-SMOKETEST-LIVE-FIXUPS add IOA_OLLAMA_WARM_TIMEOUT support
        
        Args:
            host: Ollama host (defaults to OLLAMA_HOST or localhost:11434)
            
        Returns:
            Dictionary with warm-load results
        """
        if host is None:
            host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        
        # Get timeout from environment (support both legacy and new env names)
        warm_ms = os.getenv("IOA_OLLAMA_WARM_TIMEOUT") or os.getenv("IOA_OLLAMA_WARMLOAD_TIMEOUT_MS", "8000")
        try:
            timeout_ms = int(warm_ms)
        except ValueError:
            timeout_ms = 8000
        timeout_seconds = timeout_ms / 1000
        
        results = {
            "model": model,
            "host": host,
            "status": "failed",
            "latency_ms": 0,
            "error": None,
            "response": None,
            "timeout_ms": timeout_ms
        }
        
        # Honor skip-warm flag
        if os.getenv("IOA_OLLAMA_SKIP_WARM", "0") == "1":
            results["status"] = "skipped"
            results["error"] = None
            return results
        
        try:
            import requests
            
            # Set keep-alive for model
            os.environ["OLLAMA_KEEP_ALIVE"] = "5m"
            
            # Prepare request with deterministic model
            url = f"{host}/api/generate"
            payload = {
                "model": model,
                "prompt": "ping",
                "options": OllamaTurboPreset.get_turbo_local_options()
            }
            
            # Record request payload
            self._write_artifact("ollama_request.json", json.dumps(payload, indent=2))
            
            # Execute warm-load with configurable timeout
            start_time = time.time()
            response = requests.post(url, json=payload, timeout=timeout_seconds)
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            results["latency_ms"] = elapsed_ms
            
            # Check if timeout was exceeded
            if elapsed_ms > timeout_ms:
                results["error"] = f"Warm-load timeout exceeded: {elapsed_ms}ms > {timeout_ms}ms"
                logger.warning(f"Warm-load timeout for {model}: {results['error']}")
                return results
            
            if response.status_code == 200:
                # Handle streaming response from Ollama
                response_text = response.text.strip()
                if response_text:
                    # Parse the last line of streaming response
                    lines = response_text.split('\n')
                    last_line = lines[-1] if lines else ""
                    if last_line:
                        try:
                            data = json.loads(last_line)
                            results["status"] = "success"
                            results["response"] = data.get("response", "")
                            logger.info(f"Warm-load successful for {model}: {elapsed_ms}ms")
                        except json.JSONDecodeError:
                            results["error"] = f"Invalid JSON response: {last_line[:100]}"
                            logger.warning(f"Warm-load JSON parse failed for {model}: {results['error']}")
                    else:
                        results["error"] = "Empty response from Ollama"
                        logger.warning(f"Warm-load empty response for {model}")
                else:
                    results["error"] = "Empty response from Ollama"
                    logger.warning(f"Warm-load empty response for {model}")
            else:
                results["error"] = f"HTTP {response.status_code}: {response.text}"
                logger.warning(f"Warm-load failed for {model}: {results['error']}")
            
        except requests.exceptions.Timeout:
            results["error"] = f"Warm-load timeout ({timeout_seconds}s)"
            logger.error(f"Warm-load timeout for {model}: {results['error']}")
        except Exception as e:
            results["error"] = str(e)
            logger.error(f"Warm-load exception for {model}: {e}")
        
        # Record warm-load results
        self._write_artifact("ollama_warmload.json", json.dumps(results, indent=2))
        
        return results
    
    def _write_artifact(self, filename: str, content: str) -> None:
        """Write content to artifacts directory."""
        try:
            artifact_path = self.artifacts_dir / filename
            with artifact_path.open('w') as f:
                f.write(content)
            logger.debug(f"Written artifact: {artifact_path}")
        except Exception as e:
            logger.warning(f"Failed to write artifact {filename}: {e}")


class OllamaInferenceTester:
    """Hardened inference testing with timeouts and diagnostics."""
    
    def __init__(self, artifacts_dir: Path):
        self.artifacts_dir = artifacts_dir
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
    
        """
        Test Ollama inference with hardened timeouts and error handling.
        
        PATCH: Cursor-2025-09-08 DISPATCH-OSS-20250908-OLLAMA-CLOUD-ONBOARD <add cloud support and local_preset>
        Enhanced with configurable timeouts and deterministic model selection.
        
        Args:
            host: Ollama host (defaults to OLLAMA_HOST or localhost:11434)
            mode: Inference mode ("local_preset", "turbo_cloud", "turbo_local", "turbo", or "standard")
            
        Returns:
            Dictionary with test results
        """
        if host is None:
            # For turbo_cloud mode, use OLLAMA_API_BASE if available
            if mode == "turbo_cloud":
                host = os.getenv("OLLAMA_API_BASE", os.getenv("OLLAMA_HOST", "http://localhost:11434"))
            else:
                host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        
        # Get timeout from environment
        timeout_ms = int(os.getenv("IOA_OLLAMA_INFER_TIMEOUT_MS", "8000"))
        
        results = {
            "model": model,
            "host": host,
            "mode": mode,
            "status": "failed",
            "latency_ms": 0,
            "error": None,
            "response": None,
            "retry_attempted": False,
            "timeout_ms": timeout_ms
        }
        
        # Get options based on mode
        if mode in ["local_preset", "turbo_local"]:  # Handle both new and deprecated names
            options = OllamaTurboPreset.get_turbo_local_options()
        elif mode == "turbo_cloud":
            options = OllamaTurboPreset.get_turbo_cloud_options()
        elif mode == "turbo":
            options = OllamaTurboPreset.get_turbo_options()
        else:
            options = OllamaTurboPreset.get_standard_options()
        
        # Test with primary options
        test_result = self._run_inference_test(model, host, options, "primary", mode)
        results.update(test_result)
        
        # If failed, try with shorter num_predict
        if results["status"] == "failed" and not results["retry_attempted"]:
            logger.info(f"Primary test failed for {model}, trying shorter num_predict")
            retry_options = options.copy()
            retry_options["num_predict"] = 8
            retry_result = self._run_inference_test(model, host, retry_options, "retry", mode)
            results.update(retry_result)
            results["retry_attempted"] = True
        
        return results
    
                          attempt: str, mode: str = "turbo") -> Dict[str, Any]:
        """Run a single inference test attempt with configurable timeout."""
        # Get timeout from environment
        infer_ms = os.getenv("IOA_OLLAMA_INFER_TIMEOUT_MS", "8000")
        try:
            timeout_ms = int(infer_ms)
        except ValueError:
            timeout_ms = 8000
        timeout_seconds = timeout_ms / 1000
        
        results = {
            "status": "failed",
            "latency_ms": 0,
            "error": None,
            "response": None,
            "attempt": attempt,
            "timeout_ms": timeout_ms
        }
        
        try:
            import requests
            
            # Prepare request
            url = f"{host}/api/generate"
            payload = {
                "model": model,
                "prompt": "Say 'hello' and nothing else.",
                "options": options
            }
            
            # Add cloud API headers if in turbo_cloud mode
            headers = {}
            if mode == "turbo_cloud":
                api_key = os.getenv("OLLAMA_API_KEY")
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                    # Add content-type for cloud API
                    headers["Content-Type"] = "application/json"
            
            # Record request payload
            self._write_artifact("ollama_request.json", json.dumps(payload, indent=2))
            
            # Execute inference with configurable timeout
            start_time = time.time()
            response = requests.post(url, json=payload, headers=headers, timeout=timeout_seconds)
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            results["latency_ms"] = elapsed_ms
            
            # Check if timeout was exceeded
            if elapsed_ms > timeout_ms:
                results["error"] = f"Inference timeout exceeded: {elapsed_ms}ms > {timeout_ms}ms"
                logger.warning(f"Inference timeout for {model}: {results['error']}")
                return results
            
            if response.status_code == 200:
                # Handle streaming response from Ollama
                response_text = response.text.strip()
                if response_text:
                    # Parse the last line of streaming response
                    lines = response_text.split('\n')
                    last_line = lines[-1] if lines else ""
                    if last_line:
                        try:
                            data = json.loads(last_line)
                            results["status"] = "success"
                            results["response"] = data.get("response", "")
                            logger.info(f"Inference test {attempt} successful for {model}: {elapsed_ms}ms")
                        except json.JSONDecodeError:
                            results["error"] = f"Invalid JSON response: {last_line[:100]}"
                            logger.warning(f"Inference test {attempt} JSON parse failed for {model}: {results['error']}")
                    else:
                        results["error"] = "Empty response from Ollama"
                        logger.warning(f"Inference test {attempt} empty response for {model}")
                else:
                    results["error"] = "Empty response from Ollama"
                    logger.warning(f"Inference test {attempt} empty response for {model}")
            else:
                results["error"] = f"HTTP {response.status_code}: {response.text}"
                logger.warning(f"Inference test {attempt} failed for {model}: {results['error']}")
        
        except requests.exceptions.Timeout:
            results["error"] = f"Inference timeout ({timeout_seconds}s)"
            logger.error(f"Inference test {attempt} timeout for {model}: {results['error']}")
        except Exception as e:
            results["error"] = str(e)
            logger.error(f"Inference test {attempt} exception for {model}: {e}")
        
        # Write error log if failed
        if results["status"] == "failed":
            self._write_error_log(model, host, payload, results["error"], results["latency_ms"])
        
        return results
    
                        error: str, latency_ms: int) -> None:
        """Write detailed error log for debugging."""
        try:
            error_log = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "model": model,
                "host": host,
                "payload": payload,
                "error": error,
                "latency_ms": latency_ms,
                "system_info": {}
            }
            
            # Add system load info
            try:
                result = subprocess.run(["uptime"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    error_log["system_info"]["uptime"] = result.stdout.strip()
            except Exception:
                pass
            
            try:
                result = subprocess.run(["uname", "-a"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    error_log["system_info"]["uname"] = result.stdout.strip()
            except Exception:
                pass
            
            # Write error log
            error_path = self.artifacts_dir / "ollama_error.log"
            with error_path.open('w') as f:
                json.dump(error_log, f, indent=2)
            
            logger.debug(f"Written error log: {error_path}")
            
        except Exception as e:
            logger.warning(f"Failed to write error log: {e}")
    
    def _write_artifact(self, filename: str, content: str) -> None:
        """Write content to artifacts directory."""
        try:
            artifact_path = self.artifacts_dir / filename
            with artifact_path.open('w') as f:
                f.write(content)
            logger.debug(f"Written artifact: {artifact_path}")
        except Exception as e:
            logger.warning(f"Failed to write artifact {filename}: {e}")


def get_ollama_mode() -> str:
    """
    Get Ollama mode from environment with cloud Turbo detection.
    
    PATCH: Cursor-2025-09-08 DISPATCH-OSS-20250908-OLLAMA-CLOUD-ONBOARD <add cloud detection and local_preset>
    
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
    # PATCH: Cursor-2025-09-08 DISPATCH-OSS-20250908-OLLAMA-CLOUD-ONBOARD <add auto-detection>
    
    # Check for Ollama Turbo cloud credentials
    if _is_turbo_cloud_configured():
        return "turbo_cloud"
    
    # Check for legacy cloud indicators
    ollama_host = os.getenv("OLLAMA_HOST", "").lower()
    ollama_turbo_cloud = os.getenv("OLLAMA_TURBO_CLOUD", "").lower()
    
    # Detect cloud Turbo based on environment indicators
    if (ollama_turbo_cloud in ["1", "true", "yes"] or 
        "turbo" in ollama_host or 
        "cloud" in ollama_host or
        os.getenv("OLLAMA_TURBO_MODE") == "cloud"):
        return "turbo_cloud"
    
    # Default to local preset for smoketest
    return "local_preset"


def _is_turbo_cloud_configured() -> bool:
    """
    Check if Ollama Turbo cloud is properly configured.
    
    PATCH: Cursor-2025-09-08 DISPATCH-OSS-20250908-OLLAMA-CLOUD-ONBOARD <add cloud credential detection>
    
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


def check_ollama_health(host: str = None) -> Dict[str, Any]:
    """
    Check Ollama health with configurable timeout.
    
    PATCH: Cursor-2025-09-08 DISPATCH-OSS-20250908-SMOKETEST-LIVE-FIXUPS accept IOA_OLLAMA_WARM_TIMEOUT
    
    Args:
        host: Ollama host (defaults to OLLAMA_HOST or localhost:11434)
        
    Returns:
        Dictionary with health check results
    """
    if host is None:
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    # Get timeout from environment
    health_ms = os.getenv("IOA_OLLAMA_HEALTH_TIMEOUT_MS") or os.getenv("IOA_OLLAMA_WARM_TIMEOUT", "3000")
    try:
        timeout_ms = int(health_ms)
    except ValueError:
        timeout_ms = 3000
    timeout_seconds = timeout_ms / 1000
    
    results = {
        "host": host,
        "status": "failed",
        "latency_ms": 0,
        "error": None,
        "version": None,
        "timeout_ms": timeout_ms
    }
    
    try:
        import requests
        
        # Check Ollama health endpoint
        start_time = time.time()
        response = requests.get(f"{host}/api/version", timeout=timeout_seconds)
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        results["latency_ms"] = elapsed_ms
        
        # Check if timeout was exceeded
        if elapsed_ms > timeout_ms:
            results["error"] = f"Health check timeout exceeded: {elapsed_ms}ms > {timeout_ms}ms"
            logger.warning(f"Ollama health timeout: {results['error']}")
            return results
        
        if response.status_code == 200:
            data = response.json()
            results["status"] = "success"
            results["version"] = data.get("version", "unknown")
        else:
            results["error"] = f"HTTP {response.status_code}: {response.text}"
            logger.warning(f"Ollama health check failed: {results['error']}")
            
    except requests.exceptions.Timeout:
        results["error"] = f"Health check timeout ({timeout_seconds}s)"
        logger.error(f"Ollama health timeout: {results['error']}")
    except Exception as e:
        results["error"] = str(e)
        logger.error(f"Ollama health check exception: {e}")
    
    return results


    """Export selected model for smoketest session."""
    os.environ["IOA_SMOKETEST_OLLAMA_MODEL"] = model
