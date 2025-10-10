""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

# PATCH: Cursor-2025-09-10 DISPATCH-OSS-20250910-MEMORY-FABRIC-REFACTOR <metrics module>

@dataclass
class OperationMetrics:
    """Metrics for a single operation."""
    operation: str
    start_time: float
    end_time: float
    success: bool
    error_message: Optional[str] = None
    
    @property
    def duration_ms(self) -> float:
        """Get operation duration in milliseconds."""
        return (self.end_time - self.start_time) * 1000

class MemoryFabricMetrics:
    """Metrics collection and reporting for Memory Fabric."""
    
    def __init__(self, output_dir: str = "./artifacts/lens/memory_fabric"):
        """Initialize metrics collector."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.metrics_file = self.output_dir / "metrics.jsonl"
        self._operation_times: List[float] = []
        self._current_metrics = {
            "backend": "unknown",
            "ops": {"reads": 0, "writes": 0, "queries": 0},
            "latency_ms": {"p50": 0, "p95": 0},
            "encryption": "none",
            "errors": 0,
            "total_records": 0
        }
    
    def set_backend(self, backend: str):
        """Set the current backend."""
        self._current_metrics["backend"] = backend
    
    def set_encryption_mode(self, mode: str):
        """Set the encryption mode."""
        self._current_metrics["encryption"] = mode
    
    def record_operation(self, operation: str, success: bool, duration_ms: float, error_message: Optional[str] = None):
        """Record an operation."""
        # Update operation counts
        if operation in self._current_metrics["ops"]:
            self._current_metrics["ops"][operation] += 1
        
        # Record latency
        self._operation_times.append(duration_ms)
        
        # Update error count
        if not success:
            self._current_metrics["errors"] += 1
        
        # Calculate percentiles
        if self._operation_times:
            sorted_times = sorted(self._operation_times)
            n = len(sorted_times)
            # For median, use the middle value or average of two middle values
            if n % 2 == 0:
                self._current_metrics["latency_ms"]["p50"] = (sorted_times[n//2-1] + sorted_times[n//2]) / 2
            else:
                self._current_metrics["latency_ms"]["p50"] = sorted_times[n//2]
            self._current_metrics["latency_ms"]["p95"] = sorted_times[int(n * 0.95)]
        
        # Write to JSONL file
        self._write_metrics_entry({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "success": success,
            "duration_ms": duration_ms,
            "error_message": error_message,
            "backend": self._current_metrics["backend"],
            "encryption": self._current_metrics["encryption"]
        })
    
    def update_record_count(self, count: int):
        """Update the total record count."""
        self._current_metrics["total_records"] = count
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        return self._current_metrics.copy()
    
    def get_operation_times(self) -> List[float]:
        """Get all recorded operation times."""
        return self._operation_times.copy()
    
    def reset_metrics(self):
        """Reset all metrics."""
        self._current_metrics = {
            "backend": "unknown",
            "ops": {"reads": 0, "writes": 0, "queries": 0},
            "latency_ms": {"p50": 0, "p95": 0},
            "encryption": "none",
            "errors": 0,
            "total_records": 0
        }
        self._operation_times.clear()
    
    def _write_metrics_entry(self, entry: Dict[str, Any]):
        """Write a metrics entry to the JSONL file."""
        try:
            with open(self.metrics_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            # Silently fail if metrics writing fails
            pass
    
    def export_metrics(self, output_file: Optional[str] = None) -> str:
        """Export current metrics to a file."""
        if output_file is None:
            output_file = self.output_dir / f"metrics_export_{int(time.time())}.json"
        
        export_data = {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "current_metrics": self.get_current_metrics(),
            "operation_times": self.get_operation_times(),
            "total_operations": len(self._operation_times)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
        
        return str(output_file)
    
    def get_metrics_summary(self) -> str:
        """Get a human-readable metrics summary."""
        metrics = self.get_current_metrics()
        
        summary = f"""
=============================
Backend: {metrics['backend']}
Encryption: {metrics['encryption']}
Total Records: {metrics['total_records']}

Operations:
- Reads: {metrics['ops']['reads']}
- Writes: {metrics['ops']['writes']}
- Queries: {metrics['ops']['queries']}

Latency (ms):
- P50: {metrics['latency_ms']['p50']:.2f}
- P95: {metrics['latency_ms']['p95']:.2f}

Errors: {metrics['errors']}
Total Operations: {len(self._operation_times)}
        """.strip()
        
        return summary

class MetricsCollector:
    """Context manager for collecting operation metrics."""
    
    def __init__(self, metrics: MemoryFabricMetrics, operation: str):
        """Initialize metrics collector."""
        self.metrics = metrics
        self.operation = operation
        self.start_time = None
        self.success = False
        self.error_message = None
    
    def __enter__(self):
        """Enter context manager."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self.start_time is None:
            return
        
        end_time = time.time()
        duration_ms = (end_time - self.start_time) * 1000
        
        if exc_type is None:
            self.success = True
        else:
            self.success = False
            self.error_message = str(exc_val) if exc_val else "Unknown error"
        
        self.metrics.record_operation(
            self.operation,
            self.success,
            duration_ms,
            self.error_message
        )
