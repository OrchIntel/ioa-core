""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional
import asyncio
import threading


class AuditLogger:
    """File‑based audit logger with simple event routing and proper resource management."""

    def __init__(self,
                 log_dir: str = "logs",
                 max_log_size: int = 10 * 1024 * 1024,
                 backup_count: int = 5) -> None:
        """
        Initialise the audit logger.

        Args:
            log_dir: Directory in which to place log files.  It will be
                created if it does not already exist.
            max_log_size: Maximum size in bytes for any single log file
                before rotation occurs.
            backup_count: Number of rotated log files to retain.
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create rotating handlers for each supported category
        self.batch_log = RotatingFileHandler(
            self.log_dir / "batch.log",
            maxBytes=max_log_size,
            backupCount=backup_count,
        )
        self.handlers: Dict[str, RotatingFileHandler] = {
            'system': RotatingFileHandler(self.log_dir / "system.log", maxBytes=max_log_size, backupCount=backup_count),
            'gdpr': RotatingFileHandler(self.log_dir / "gdpr.log", maxBytes=max_log_size, backupCount=backup_count),
            'trust': RotatingFileHandler(self.log_dir / "trust.log", maxBytes=max_log_size, backupCount=backup_count),
            'ethics': RotatingFileHandler(self.log_dir / "ethics.log", maxBytes=max_log_size, backupCount=backup_count),
            'error': RotatingFileHandler(self.log_dir / "error.log", maxBytes=max_log_size, backupCount=backup_count),
        }
        # Ensure each handler writes raw messages without formatting
        for handler in list(self.handlers.values()) + [self.batch_log]:
            handler.setFormatter(logging.Formatter('%(message)s'))

        # Protect concurrent writes
        self._lock = threading.RLock()
        self._closed = False

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure cleanup."""
        self.close()

    def close(self) -> None:
        """Close all file handlers and release resources."""
        if self._closed:
            return
        
        with self._lock:
            # Close all handlers
            for handler in self.handlers.values():
                handler.close()
            self.batch_log.close()
            self._closed = True

    async def log(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Write a structured event to the appropriate log file.

        Args:
            event_type: Category of event.  Recognised categories are
                ``system``, ``gdpr``, ``trust``, ``ethics``, ``error`` and
                ``batch_storage``.  Unrecognised categories default to
                ``system``.
            event_data: Arbitrary mapping describing the event.  A
                timestamp will be injected automatically.
        """
        if self._closed:
            raise RuntimeError("AuditLogger is closed")
            
        # Choose the correct handler
        if event_type == 'batch_storage':
            handler = self.batch_log
        else:
            handler = self.handlers.get(event_type, self.handlers['system'])

        # Copy data and append timestamp
        payload = dict(event_data)
        payload['timestamp'] = datetime.now(timezone.utc).isoformat()

        # Serialize outside the lock to minimize time spent holding it
        message = json.dumps(payload, separators=(",", ":"))
        record = logging.makeLogRecord({'msg': message, 'level': logging.INFO})

        # Emit record under lock to prevent interleaving messages
        with self._lock:
            handler.emit(record)

    # Convenience wrappers -------------------------------------------------
    def _schedule_log(self, category: str, payload: Dict[str, Any]) -> None:
        """
        Internal helper to schedule an asynchronous log call from a
        synchronous context.  If there is an active event loop, the call
        will be scheduled on it; otherwise a temporary event loop is
        created to run the coroutine.
        """
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.log(category, payload))
        except RuntimeError:
            # No running loop; run synchronously
            asyncio.run(self.log(category, payload))

    def log_system_event(self, event_type: str, data: Dict[str, Any]) -> None:
        self._schedule_log('system', {'event_type': event_type, **data})

    def log_gdpr_event(self, event_type: str, data: Dict[str, Any]) -> None:
        self._schedule_log('gdpr', {'event_type': event_type, **data})

    def log_trust_update(self, event_type: str, data: Dict[str, Any]) -> None:
        self._schedule_log('trust', {'event_type': event_type, **data})

    def log_ethics_violation(self, event_type: str, data: Dict[str, Any]) -> None:
        self._schedule_log('ethics', {'event_type': event_type, **data})

    def log_error(self, event_type: str, data: Dict[str, Any]) -> None:
        self._schedule_log('error', {'event_type': event_type, **data})
