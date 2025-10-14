"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, Optional


def _to_json(data: Any) -> str:
    if is_dataclass(data):
        return json.dumps(asdict(data))
    return json.dumps(data)


def run_cartridge_in_sandbox(module_path: str, func_name: str, context: Dict[str, Any], timeout_sec: int = 30) -> Dict[str, Any]:
    """
    Execute a cartridge function in a subprocess sandbox if IOA_CARTRIDGE_SANDBOX=1.

    Args:
        module_path: Python module path of the cartridge (e.g., "mycart.module")
        func_name: Callable name within the module (e.g., "enforce")
        context: Dict-like context passed to the callable
        timeout_sec: Execution timeout

    Returns:
        Dict response parsed from JSON
    """
    if os.getenv("IOA_CARTRIDGE_SANDBOX", "0") not in ("1", "true", "TRUE"):
        # Direct in-process execution
        mod = __import__(module_path, fromlist=[func_name])
        func = getattr(mod, func_name)
        result = func(context)
        if is_dataclass(result):
            return asdict(result)
        if isinstance(result, dict):
            return result
        return {"result": result}

    # Subprocess isolation runner
    runner_code = """
import json
import importlib.util
import sys

module_path = json.loads(sys.argv[1])
func_name = json.loads(sys.argv[2])
ctx = json.loads(sys.argv[3])

# Load module from file path
spec = importlib.util.spec_from_file_location("temp_module", module_path + ".py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

f = getattr(module, func_name)
res = f(ctx)
try:
    from dataclasses import asdict, is_dataclass
    if is_dataclass(res):
        print(json.dumps(asdict(res)))
    elif isinstance(res, dict):
        print(json.dumps(res))
    else:
        print(json.dumps({"result": str(res)}))
except Exception:
    print(json.dumps({"result": str(res)}))
"""

    cmd = [sys.executable, "-c", runner_code, json.dumps(module_path), json.dumps(func_name), json.dumps(context)]
    proc = subprocess.run(cmd, capture_output=True, timeout=timeout_sec, check=False)
    if proc.returncode != 0:
        raise RuntimeError("Sandboxed cartridge failed: " + proc.stderr.decode('utf-8', 'ignore'))
    stdout = proc.stdout.decode("utf-8").strip()
    try:
        return json.loads(stdout) if stdout else {}
    except Exception as exc:
        raise RuntimeError("Invalid sandbox output: " + str(exc) + "; output=" + stdout)


