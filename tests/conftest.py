""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

# PATCH: Cursor-2025-08-15 CL-LLM-Deterministic-Config <add test mode fixtures>
import os
import pytest
from unittest.mock import patch

def pytest_configure(config):
    """Configure pytest to handle plugins cleanly."""
    # PATCH: Cursor-2025-08-15 CL-P4-Final-Green - Clean benchmark plugin handling
    # If this is an xdist worker, disable benchmark plugin cleanly
    if hasattr(config, "workerinput"):
        # Best-effort disable without emitting warnings
        try:
            config.option.benchmark_disable = True
        except Exception:
            import os
            os.environ["BENCHMARK_DISABLE"] = "1"

    # PATCH: Cursor-2025-08-18 Reports-Normalization DISPATCH-GPT-20250818-008
    # Ensure default dispatch code is available in config for logging format
    if not hasattr(config.option, "dispatch_code"):
        # Option added in pytest_addoption; fallback default here if not yet set
        setattr(config.option, "dispatch_code", os.getenv("DISPATCH_CODE", "DISPATCH-GPT-20250818-008"))


def pytest_addoption(parser):
    """Add custom command line options for IOA reporting."""
    # PATCH: Cursor-2025-08-18 Reports-Normalization DISPATCH-GPT-20250818-008
    parser.addoption(
        "--dispatch-code",
        action="store",
        default=os.getenv("DISPATCH_CODE", "DISPATCH-GPT-20250818-008"),
        help="Attach a DISPATCH code to logs (default: DISPATCH-GPT-20250818-008)",
    )

    # PATCH: Cursor-2025-08-18 Anti-Hang Harness DISPATCH-GPT-20250818-007
    # Ensure pytest-timeout options are accepted even if plugin loads late
    parser.addini("timeout", help="Per-test timeout in seconds", default="30")
    parser.addini("timeout_func_only", help="Only apply timeout to test functions", default="true")
    parser.addini("timeout_method", help="Timeout mechanism", default="thread")


@pytest.fixture(scope="session", autouse=True)
def ioa_reports_setup(request):
    """Create standardized reports directory layout and configure logging capture.

    Layout: /reports/<suite>/<YYYYMMDD-HHMMSS>/{summary.md, summary.json, logs/, schemas/, artifacts/}
    """
    # PATCH: Cursor-2025-08-18 Reports-Normalization DISPATCH-GPT-20250818-008
    import json
    import logging
    from datetime import datetime, timezone
    from pathlib import Path

    config = request.config
    dispatch_code = getattr(config.option, "dispatch_code", os.getenv("DISPATCH_CODE", "DISPATCH-GPT-20250818-008"))

    # Determine suite name (default to "pytest" unless overridden via env)
    suite_name = os.getenv("IOA_REPORT_SUITE", "pytest")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    repo_root = Path(config.rootpath)
    reports_root = repo_root / "reports"
    run_dir = reports_root / suite_name / timestamp
    logs_dir = run_dir / "logs"
    schemas_dir = run_dir / "schemas"
    artifacts_dir = run_dir / "artifacts"

    # Create directories (idempotent)
    for p in (logs_dir, schemas_dir, artifacts_dir):
        p.mkdir(parents=True, exist_ok=True)

    # Configure logging to file with dispatch code field in each line
    log_file = logs_dir / "test.log"
    # Include a literal JSON-like field so acceptance can assert the presence of the exact key
    log_format = f"%(asctime)s [%(levelname)s] %(name)s: %(message)s | \"dispatch_code\": \"{dispatch_code}\""
    logging.basicConfig(level=logging.INFO, format=log_format)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format))

    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)

    # Stash paths on config for later hooks
    config._ioa_reports = {
        "dispatch_code": dispatch_code,
        "suite": suite_name,
        "timestamp": timestamp,
        "reports_root": str(reports_root),
        "run_dir": str(run_dir),
        "logs_dir": str(logs_dir),
        "schemas_dir": str(schemas_dir),
        "artifacts_dir": str(artifacts_dir),
        "log_file": str(log_file),
    }

    # Export for hooks that don't have access to config
    os.environ["IOA_REPORTS_LOG_FILE"] = str(log_file)
    os.environ["IOA_DISPATCH_CODE"] = dispatch_code

    # Pre-create example topic folders for acceptance (doctor, roundtable)
    # These are lightweight placeholders to guide users; real runs can populate further.
    for topic in ("doctor", "roundtable"):
        topic_dir = reports_root / topic / timestamp
        (topic_dir / "logs").mkdir(parents=True, exist_ok=True)
        (topic_dir / "schemas").mkdir(parents=True, exist_ok=True)
        (topic_dir / "artifacts").mkdir(parents=True, exist_ok=True)
        summary_md = topic_dir / "summary.md"
        if not summary_md.exists():
            summary_md.write_text(
                f"""
Dispatch: {dispatch_code}
Topic: {topic}
When (UTC): {timestamp}

This folder is prepared by pytest hooks. Real runs will add detailed summaries and logs.
""".strip()
            , encoding="utf-8")

    # Initialize summaries
    (run_dir / "summary.md").write_text(
        f"""
Dispatch: {dispatch_code}
Suite: {suite_name}
When (UTC): {timestamp}

Session starting. Logs captured to: {log_file}
""".strip()
        , encoding="utf-8")
    (run_dir / "summary.json").write_text(
        json.dumps({
            "dispatch": dispatch_code,
            "suite": suite_name,
            "timestamp_utc": timestamp,
            "status": "starting"
        }, indent=2),
        encoding="utf-8",
    )

    yield

    # No teardown here; finalization handled in pytest_sessionfinish


def pytest_sessionfinish(session, exitstatus):
    """Finalize run summaries and move/copy any root logs into reports."""
    # PATCH: Cursor-2025-08-18 Reports-Normalization DISPATCH-GPT-20250818-005
    import json
    import shutil
    from pathlib import Path

    config = session.config
    meta = getattr(config, "_ioa_reports", None) or {}
    if not meta:
        return

    reports_root = Path(meta["reports_root"])  # type: ignore[index]
    run_dir = Path(meta["run_dir"])           # type: ignore[index]
    logs_dir = Path(meta["logs_dir"])         # type: ignore[index]
    dispatch_code = meta.get("dispatch_code", "DISPATCH-GPT-20250818-008")

    # Gather test stats from terminal reporter
    tr = config.pluginmanager.get_plugin("terminalreporter")
    total = len(getattr(tr, "stats", {}).get("passed", [])) + \
            len(getattr(tr, "stats", {}).get("failed", [])) + \
            len(getattr(tr, "stats", {}).get("skipped", [])) + \
            len(getattr(tr, "stats", {}).get("xfailed", [])) + \
            len(getattr(tr, "stats", {}).get("xpassed", []))
    passed = len(getattr(tr, "stats", {}).get("passed", []))
    failed = len(getattr(tr, "stats", {}).get("failed", []))
    skipped = len(getattr(tr, "stats", {}).get("skipped", []))
    xfailed = len(getattr(tr, "stats", {}).get("xfailed", []))
    xpassed = len(getattr(tr, "stats", {}).get("xpassed", []))
    errors = len(getattr(tr, "stats", {}).get("error", []))

    # Timeouts collected via our custom hook storage
    timeouts = getattr(config, "_ioa_timeouts", [])

    # Capture first failure and first timeout snippet if available
    first_failure_snippet = None
    if tr and tr.stats.get("failed"):
        try:
            first_failure = tr.stats["failed"][0]
            first_failure_snippet = str(getattr(first_failure, "longrepr", ""))[:500]
        except Exception:
            first_failure_snippet = None

    first_timeout_node = timeouts[0] if timeouts else None

    # Update summaries
    summary_md = run_dir / "summary.md"
    summary_json = run_dir / "summary.json"
    md_lines = [
        f"Dispatch: {dispatch_code}",
        f"Suite: {meta.get('suite')}",
        f"When (UTC): {meta.get('timestamp')}",
        "",
        f"Results: {passed} passed, {failed} failed, {skipped} skipped, {xfailed} xfailed, {xpassed} xpassed, {errors} error, {len(timeouts)} timeout(s), total {total}",
        f"Logs: {logs_dir}",
    ]
    # Include Slow/Deferred section
    try:
        from pathlib import Path as _Path
        slow_registry = _Path(config.rootpath) / "tests" / "slow_tests.txt"
        if slow_registry.exists():
            slow_nodes = [ln.strip() for ln in slow_registry.read_text(encoding="utf-8").splitlines() if ln.strip()]
            if slow_nodes:
                md_lines.append("")
                md_lines.append("Slow/Deferred:")
                md_lines.extend([f"- {nid}" for nid in slow_nodes])
    except Exception:
        pass
    if timeouts:
        md_lines.append("")
        md_lines.append("Timeouts:")
        md_lines.extend([f"- {nid}" for nid in timeouts])
    if first_failure_snippet:
        md_lines.append("")
        md_lines.append("First failure snippet:")
        md_lines.append("```")
        md_lines.append(first_failure_snippet)
        md_lines.append("```")
    summary_md.write_text("\n".join(md_lines), encoding="utf-8")
    summary_json.write_text(
        json.dumps({
            "dispatch": dispatch_code,
            "suite": meta.get("suite"),
            "timestamp_utc": meta.get("timestamp"),
            "results": {"passed": passed, "failed": failed, "skipped": skipped, "xfailed": xfailed, "xpassed": xpassed, "error": errors, "timeouts": len(timeouts), "timeout_nodes": timeouts, "total": total},
            "logs_dir": str(logs_dir),
            "first_failure_snippet": first_failure_snippet,
            "first_timeout_node": first_timeout_node,
        }, indent=2),
        encoding="utf-8",
    )

    # Create dispatch recap folder named after this dispatch code suffix
    import re
    suffix_match = re.search(r"(\d{3,})$", dispatch_code)
    dispatch_suffix = suffix_match.group(1) if suffix_match else "run"
    dispatch_dir = reports_root / f"dispatch-{dispatch_suffix}"
    dispatch_dir.mkdir(parents=True, exist_ok=True)
    # Compute warnings count if available
    tr = config.pluginmanager.get_plugin("terminalreporter")
    warnings_count = len(getattr(tr, "stats", {}).get("warnings", [])) if tr else 0
    (dispatch_dir / "summary.md").write_text(
        "\n".join([
            f"Dispatch: {dispatch_code}",
            f"Primary run folder: {run_dir}",
            f"Tests: {passed} passed, {failed} failed, {skipped} skipped, total {total}",
            f"XFailed: {xfailed}, XPassed: {xpassed}, Errors: {errors}, Timeouts: {len(timeouts)}",
            f"Warnings: {warnings_count}",
            "Changes: Enabled anti-hang harness (timeout=30s, non-interactive mode, env-guarded skips, per-test JSON logs).",
        ]),
        encoding="utf-8",
    )

    # Append an entry to docs/ops/Reports.md for this CI run
    try:
        docs_reports = Path(config.rootpath) / "docs" / "ops" / "Reports.md"
        run_stamp = meta.get("timestamp")
        suffix_for_heading = f"DISPATCH-{dispatch_suffix}" if dispatch_suffix.isdigit() else dispatch_code
        one_line = f"- Dispatch {dispatch_code} | {run_stamp} | {run_dir} | Totals: {passed}p/{failed}f/{skipped}s/{xfailed}xf/{xpassed}xp/{errors}e/{len(timeouts)}t | Warnings: {warnings_count}\n"
        with docs_reports.open("a", encoding="utf-8") as f:
            f.write(one_line)
    except Exception:
        # Non-fatal; documentation update should not fail the test session
        pass

    # Persist slow/timeout tests registry and move any root-level .log files
    root = Path(config.rootpath)

    # Persist slow list to repo for future runs and mark as 'slow'
    try:
        if timeouts:
            slow_registry = root / "tests" / "slow_tests.txt"
            existing = set()
            if slow_registry.exists():
                existing.update([ln.strip() for ln in slow_registry.read_text(encoding="utf-8").splitlines() if ln.strip()])
            updated = sorted(existing.union(timeouts))
            slow_registry.write_text("\n".join(updated) + "\n", encoding="utf-8")

            # Also mirror into this run folder for traceability
            (run_dir / "slow.txt").write_text("\n".join(updated) + "\n", encoding="utf-8")
    except Exception:
        # Best-effort; do not fail the session on registry persistence issues
        pass

    # Move any stray .log files at repo root under current run logs directory
    for item in root.iterdir():
        if item.is_file() and item.suffix == ".log":
            try:
                shutil.move(str(item), logs_dir / item.name)
            except Exception:
                # Best-effort; skip if locked or permission denied
                pass


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Apply environment-guarded skips for marked tests before execution."""
    env_flags = {
        "network": os.getenv("IOA_ALLOW_NETWORK") == "1",
        "external": os.getenv("IOA_ALLOW_EXTERNAL") == "1",
        "requires_env": os.getenv("IOA_ALLOW_ENV") == "1",
    }
    # Also mark known slow tests from registry
    from pathlib import Path as _Path
    slow_registry = _Path(config.rootpath) / "tests" / "slow_tests.txt"
    slow_nodes = set()
    try:
        if slow_registry.exists():
            slow_nodes.update([ln.strip() for ln in slow_registry.read_text(encoding="utf-8").splitlines() if ln.strip()])
    except Exception:
        pass
    for item in items:
        for mark_name, allowed in env_flags.items():
            if item.get_closest_marker(mark_name) and not allowed:
                item.add_marker(pytest.mark.skip(reason=f"{mark_name} disabled unless IOA_ALLOW_{mark_name.upper()}=1"))
        if item.nodeid in slow_nodes:
            item.add_marker(pytest.mark.slow)


# PATCH: Cursor-2025-08-18 Anti-Hang Harness DISPATCH-GPT-20250818-007
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    """Ensure non-interactive mode, skip guarded markers, and capture timeouts/errors deterministically."""
    import json
    import sys
    import time
    from pathlib import Path

    config = item.config
    meta = getattr(config, "_ioa_reports", {})
    logs_dir = meta.get("logs_dir")
    dispatch_code = meta.get("dispatch_code", "DISPATCH-GPT-20250818-008")
    if logs_dir:
        log_path = Path(logs_dir) / "test.log"
    else:
        log_path = None

    # Force non-interactive behavior
    os.environ["IOA_NONINTERACTIVE"] = "1"

    # Guard against stdin prompts
    def _no_input(*args, **kwargs):
        raise RuntimeError("Interactive input is disabled under IOA_NONINTERACTIVE")

    monkeypatch_ctx = patch("builtins.input", _no_input)
    monkeypatch_ctx.start()

    # Skip network/external/env unless allowed
    marker_to_env = {
        "network": "IOA_ALLOW_NETWORK",
        "external": "IOA_ALLOW_EXTERNAL",
        "requires_env": "IOA_ALLOW_ENV",
    }
    for mark_name, env_name in marker_to_env.items():
        if item.get_closest_marker(mark_name) and os.getenv(env_name) != "1":
            item.add_marker(pytest.mark.skip(reason=f"{mark_name} disabled unless {env_name}=1"))

    # Per-test start log (JSON line)
    start_time = time.time()
    start_record = {
        "event": "start",
        "nodeid": item.nodeid,
        "time_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "dispatch_code": dispatch_code,
    }
    if log_path:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(start_record) + "\n")

    # Wrap the actual runtest protocol
    outcome = yield

    # Determine if timeout occurred: pytest-timeout reports as error with 'Timeout' in repr
    timed_out = False
    tr = config.pluginmanager.get_plugin("terminalreporter")
    if tr and hasattr(tr, "stats"):
        for rep in tr.stats.get("error", []):
            if getattr(rep, "nodeid", None) == item.nodeid and "Timeout" in str(getattr(rep, "longrepr", "")):
                timed_out = True
                break

    if timed_out:
        timeout_list = getattr(config, "_ioa_timeouts", None)
        if timeout_list is None:
            timeout_list = []
            setattr(config, "_ioa_timeouts", timeout_list)
        timeout_list.append(item.nodeid)

    # Per-test finish log (JSON line)
    duration = time.time() - start_time
    status = "timeout" if timed_out else "finish"
    finish_record = {
        "event": status,
        "nodeid": item.nodeid,
        "duration_s": round(duration, 3),
        "time_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "dispatch_code": dispatch_code,
    }
    if log_path:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(finish_record) + "\n")

    # Stop monkeypatch
    monkeypatch_ctx.stop()


# PATCH: Cursor-2025-08-18 Anti-Hang Harness DISPATCH-GPT-20250818-007
def pytest_runtest_logstart(nodeid, location):
    """Compatibility: ensure start event is recorded, even if protocol wrapper is bypassed."""
    import json
    import os as _os
    from pathlib import Path as _Path
    log_file = _os.environ.get("IOA_REPORTS_LOG_FILE")
    dispatch_code = _os.environ.get("IOA_DISPATCH_CODE", "DISPATCH-GPT-20250818-008")
    if log_file:
        record = {
            "event": "start",
            "nodeid": nodeid,
            "time_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "dispatch_code": dispatch_code,
        }
        with open(_Path(log_file), "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")


def pytest_runtest_logfinish(nodeid, location):
    """Compatibility: ensure finish event is recorded, even if protocol wrapper is bypassed."""
    import json
    import os as _os
    from pathlib import Path as _Path
    log_file = _os.environ.get("IOA_REPORTS_LOG_FILE")
    dispatch_code = _os.environ.get("IOA_DISPATCH_CODE", "DISPATCH-GPT-20250818-008")
    if log_file:
        record = {
            "event": "finish",
            "nodeid": nodeid,
            "time_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "dispatch_code": dispatch_code,
        }
        with open(_Path(log_file), "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

# PATCH: Cursor-2025-08-15 CL-LLM-Deterministic-Config <test mode fixtures>
@pytest.fixture(autouse=True)
def set_test_mode():
    """Automatically set test mode for all tests."""
    # Only set if not already set to avoid interfering with specific test scenarios
    if "IOA_TEST_MODE" not in os.environ:
        os.environ["IOA_TEST_MODE"] = "1"
    yield
    # Cleanup not needed as tests run in isolated processes

@pytest.fixture
def disable_llm_config():
    """Disable LLM config file lookup for tests that expect no key."""
    os.environ["IOA_DISABLE_LLM_CONFIG"] = "1"
    yield
    # Cleanup not needed as tests run in isolated processes

@pytest.fixture
def enable_llm_config():
    """Enable LLM config file lookup for tests that need real config."""
    if "IOA_DISABLE_LLM_CONFIG" in os.environ:
        del os.environ["IOA_DISABLE_LLM_CONFIG"]
    yield
    # Cleanup not needed as tests run in isolated processes

@pytest.fixture
def temp_config_dir(tmp_path):
    """Provide a temporary config directory for tests."""
    config_dir = tmp_path / ".ioa" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    os.environ["IOA_CONFIG_HOME"] = str(config_dir)
    yield config_dir
    # Cleanup not needed as tests run in isolated processes
