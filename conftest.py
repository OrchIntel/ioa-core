# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""IOA Core Test Configuration

Pytest configuration and fixtures for IOA Core test suite.
"""

import sys
import os
from pathlib import Path

# PATCH: Cursor-2025-10-04 DISPATCH-GPT-20251004-002 - Add adapters to Python path for import compatibility
project_root = Path(__file__).parent
adapters_path = project_root / "adapters"
if adapters_path.exists():
    sys.path.insert(0, str(adapters_path))

# Create src symlink for backward compatibility
src_link = project_root / "src"
if not src_link.exists() and adapters_path.exists():
    try:
        os.symlink("adapters", "src")
    except OSError:
        pass  # Symlink may fail on some systems

# PATCH: Cursor-2025-08-15 CL-P4-Final-Green - Clean benchmark plugin handling

def pytest_configure(config):
    """Configure pytest to handle plugins cleanly."""
    # If this is an xdist worker, disable benchmark plugin cleanly
    if hasattr(config, "workerinput"):
        # Best-effort disable without emitting warnings
        try:
            config.option.benchmark_disable = True
        except Exception:
            import os
            os.environ["BENCHMARK_DISABLE"] = "1"

    # PATCH: Cursor-2025-08-19 DISPATCH-GPT-20250819-015 <auto full-trace in non-interactive>
    import os as _os
    if _os.getenv("IOA_NON_INTERACTIVE") == "1":
        # Ensure full tracebacks are shown to aid CI triage
        try:
            config.option.fulltrace = True
        except Exception:
            pass

    # PATCH: Cursor-2025-08-19 DISPATCH-GPT-20250819-015 <write basic pytest report artifacts>
    # Minimal report hook to emit a summary file when requested
    _report_suite = _os.getenv("IOA_REPORT_SUITE")
    if _report_suite == "pytest":
        try:
            from datetime import datetime, timezone
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            _os.environ.setdefault("IOA_REPORT_STAMP", stamp)
        except Exception:
            pass

def pytest_sessionfinish(session, exitstatus):
    """Emit a minimal summary artifact when IOA_REPORT_SUITE=pytest."""
    import os as _os
    if _os.getenv("IOA_REPORT_SUITE") == "pytest":
        try:
            from datetime import datetime, timezone
            stamp = _os.getenv("IOA_REPORT_STAMP") or datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            out_dir = _os.path.join("reports", "pytest", stamp)
            _os.makedirs(out_dir, exist_ok=True)
            summary_path = _os.path.join(out_dir, "summary.md")
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(f"# Pytest Summary\n\nExit status: {exitstatus}\n")
        except Exception:
            pass
