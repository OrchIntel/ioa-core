"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
Unit tests for the AuditLogger batch routing.

These tests verify that events of type ``batch_storage`` are written to
the dedicated ``batch.log`` file and that other event types are routed
to the correct log files.  They also ensure that the logger does not
crash when invoked concurrently from multiple tasks.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
import tempfile
import pytest
import gc
import logging
import atexit

# Add src directory to Python path for imports
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from audit_logger import AuditLogger


def read_lines(path: Path) -> list:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def test_batch_event_routing() -> None:
    """Ensure batch events go to batch.log and not to system.log."""
    with tempfile.TemporaryDirectory() as tmp:
        with AuditLogger(log_dir=tmp, max_log_size=1024 * 1024, backup_count=1) as logger:
            # Log a batch event
            asyncio.run(logger.log('batch_storage', {'entry_count': 1}))
            # Log a system event
            asyncio.run(logger.log('system', {'msg': 'hello'}))
        
        # Inspect log files after logger is closed
        batch_lines = read_lines(Path(tmp) / 'batch.log')
        system_lines = read_lines(Path(tmp) / 'system.log')
        # There should be exactly one line in each
        assert len(batch_lines) == 1
        assert len(system_lines) == 1
        # Verify that batch log contains entry_count field
        batch_record = json.loads(batch_lines[0])
        assert batch_record['entry_count'] == 1
        # Verify that system log contains msg field
        system_record = json.loads(system_lines[0])
        assert system_record['msg'] == 'hello'


def test_concurrent_logging() -> None:
    """Ensure concurrent logging does not corrupt log files."""
    with tempfile.TemporaryDirectory() as tmp:
        with AuditLogger(log_dir=tmp, max_log_size=1024 * 1024, backup_count=1) as logger:

            async def worker(event_type: str, idx: int) -> None:
                await logger.log(event_type, {'idx': idx})

            async def run_tasks():
                tasks = []
                # Mix of event types
                for i in range(10):
                    event = 'batch_storage' if i % 2 == 0 else 'system'
                    tasks.append(asyncio.create_task(worker(event, i)))
                await asyncio.gather(*tasks)

            asyncio.run(run_tasks())
        
        # Verify counts after logger is closed
        batch_lines = read_lines(Path(tmp) / 'batch.log')
        system_lines = read_lines(Path(tmp) / 'system.log')
        # Expect 5 batch events and 5 system events
        assert len(batch_lines) == 5
        assert len(system_lines) == 5


def test_file_handles_closed() -> None:
    """Ensure all file handles are properly closed after use."""
    with tempfile.TemporaryDirectory() as tmp:
        with AuditLogger(log_dir=tmp, max_log_size=1024 * 1024, backup_count=1) as logger:
            asyncio.run(logger.log('system', {'test': 'data'}))
        
        # Force garbage collection to clean up any remaining references
        gc.collect()
        
        # Verify logger is marked as closed
        assert logger._closed is True
        
        # Verify all handlers are properly closed (don't try to flush/close already closed handlers)
        for h in list(logger.handlers.values()) + [logger.batch_log]:
            assert h._closed is True, f"Handler {h} should be closed"
        
        # Ensure global logging cleanup for ResourceWarning-free runs
        logging.shutdown()


def test_batch_logger_cleanup(tmp_path):
    """Test that file handles are properly closed after use."""
    from audit_logger import AuditLogger
    with AuditLogger(tmp_path) as logger:
        asyncio.run(logger.log('system', {"msg": "test"}))
    
    # After context manager exits, all file handles should be closed
    # We can verify this by checking that the logger is marked as closed
    assert logger._closed is True
    
    # Verify all handlers are properly closed
    for h in list(logger.handlers.values()) + [logger.batch_log]:
        assert h._closed is True, f"Handler {h} should be closed"