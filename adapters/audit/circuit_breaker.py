""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

from __future__ import annotations

import time
import logging
from enum import Enum
from typing import Any, Callable, Optional
from dataclasses import dataclass, field
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5       # Failures before opening
    recovery_timeout: int = 60       # Seconds before attempting recovery
    success_threshold: int = 3       # Successes needed to close circuit
    timeout: float = 10.0            # Operation timeout in seconds
    backoff_multiplier: float = 2.0  # Exponential backoff multiplier


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[float] = None
    state_changes: list = field(default_factory=list)


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation with exponential backoff and recovery testing.

    Prevents cascading failures by temporarily stopping calls to failing services.
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.CLOSED
        self.stats = CircuitBreakerStats()
        self._last_state_change = time.time()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to call
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenException: If circuit is open
        """
        if self.state == CircuitBreakerState.OPEN:
            if not self._should_attempt_recovery():
                raise CircuitBreakerOpenException(
                    f"Circuit breaker '{self.name}' is OPEN"
                )
            self._change_state(CircuitBreakerState.HALF_OPEN)

        try:
            result = self._execute_with_timeout(func, *args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _execute_with_timeout(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with timeout."""
        import threading
        import queue

        result_queue = queue.Queue()

        def target():
            try:
                result = func(*args, **kwargs)
                result_queue.put(('success', result))
            except Exception as e:
                result_queue.put(('error', e))

        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(timeout=self.config.timeout)

        if thread.is_alive():
            raise TimeoutError(f"Operation timed out after {self.config.timeout}s")

        status, value = result_queue.get_nowait()
        if status == 'error':
            raise value
        return value

    def _should_attempt_recovery(self) -> bool:
        """Check if we should attempt recovery from open state."""
        if self.state != CircuitBreakerState.OPEN:
            return False

        elapsed = time.time() - self._last_state_change
        return elapsed >= self.config.recovery_timeout

    def _on_success(self):
        """Handle successful operation."""
        self.stats.total_calls += 1
        self.stats.successful_calls += 1
        self.stats.consecutive_failures = 0
        self.stats.consecutive_successes += 1

        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.stats.consecutive_successes >= self.config.success_threshold:
                self._change_state(CircuitBreakerState.CLOSED)

    def _on_failure(self):
        """Handle failed operation."""
        self.stats.total_calls += 1
        self.stats.failed_calls += 1
        self.stats.consecutive_failures += 1
        self.stats.consecutive_successes = 0
        self.stats.last_failure_time = time.time()

        if self.state == CircuitBreakerState.HALF_OPEN:
            self._change_state(CircuitBreakerState.OPEN)
        elif (self.state == CircuitBreakerState.CLOSED and
              self.stats.consecutive_failures >= self.config.failure_threshold):
            self._change_state(CircuitBreakerState.OPEN)

    def _change_state(self, new_state: CircuitBreakerState):
        """Change circuit breaker state."""
        old_state = self.state
        self.state = new_state
        self._last_state_change = time.time()

        self.stats.state_changes.append({
            'timestamp': self._last_state_change,
            'from_state': old_state.value,
            'to_state': new_state.value,
            'reason': self._get_state_change_reason(old_state, new_state)
        })

        logger.info(
            f"Circuit breaker '{self.name}' state changed: {old_state.value} -> {new_state.value}"
        )

    def _get_state_change_reason(self, old_state: CircuitBreakerState, new_state: CircuitBreakerState) -> str:
        """Get reason for state change."""
        if old_state == CircuitBreakerState.CLOSED and new_state == CircuitBreakerState.OPEN:
            return f"Consecutive failures: {self.stats.consecutive_failures}"
        elif old_state == CircuitBreakerState.OPEN and new_state == CircuitBreakerState.HALF_OPEN:
            return f"Recovery timeout elapsed: {self.config.recovery_timeout}s"
        elif old_state == CircuitBreakerState.HALF_OPEN and new_state == CircuitBreakerState.CLOSED:
            return f"Consecutive successes: {self.stats.consecutive_successes}"
        elif old_state == CircuitBreakerState.HALF_OPEN and new_state == CircuitBreakerState.OPEN:
            return "Recovery attempt failed"
        return "Unknown"

    def get_status(self) -> dict:
        """Get circuit breaker status and statistics."""
        return {
            'name': self.name,
            'state': self.state.value,
            'config': {
                'failure_threshold': self.config.failure_threshold,
                'recovery_timeout': self.config.recovery_timeout,
                'success_threshold': self.config.success_threshold,
                'timeout': self.config.timeout
            },
            'stats': {
                'total_calls': self.stats.total_calls,
                'successful_calls': self.stats.successful_calls,
                'failed_calls': self.stats.failed_calls,
                'consecutive_failures': self.stats.consecutive_failures,
                'consecutive_successes': self.stats.consecutive_successes,
                'success_rate': (self.stats.successful_calls / self.stats.total_calls) if self.stats.total_calls > 0 else 0,
                'last_failure_time': self.stats.last_failure_time,
                'state_changes': len(self.stats.state_changes)
            },
            'last_state_change': self._last_state_change,
            'time_in_current_state': time.time() - self._last_state_change
        }


@contextmanager
def circuit_breaker_context(name: str, config: Optional[CircuitBreakerConfig] = None):
    """
    Context manager for circuit breaker protection.

    Usage:
        with circuit_breaker_context('s3_storage') as cb:
            result = cb.call(s3_client.get_object, **kwargs)
    """
    cb = CircuitBreaker(name, config)
    try:
        yield cb
    finally:
        # Log final status
        status = cb.get_status()
        logger.info(f"Circuit breaker '{name}' final status: {status}")


# Global circuit breaker registry
_circuit_breakers = {}


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get or create a circuit breaker instance."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]


def reset_circuit_breaker(name: str):
    """Reset a circuit breaker to closed state."""
    if name in _circuit_breakers:
        cb = _circuit_breakers[name]
        cb.state = CircuitBreakerState.CLOSED
        cb.stats = CircuitBreakerStats()
        cb._last_state_change = time.time()
        logger.info(f"Circuit breaker '{name}' reset to CLOSED state")


def get_all_circuit_breakers() -> dict:
    """Get status of all circuit breakers."""
    return {name: cb.get_status() for name, cb in _circuit_breakers.items()}
