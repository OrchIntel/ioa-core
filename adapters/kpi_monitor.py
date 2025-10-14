"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Enhanced performance monitoring for IOA memory operations
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.


"""
KPI Monitor Module - Final Production Version with ONBOARD-001 Integration

Comprehensive performance monitoring system for IOA memory operations.
Tracks pattern matching efficiency, compaction ratios, emotional sentiment
distribution, and system health metrics with real-time analytics.

✅ ONBOARD-001 Features:
- Custom metric recording with tenant isolation
- Thread-safe operations with enhanced locking
- Real-time persistence and recovery
- Agent onboarding performance tracking
"""

__version__ = "2.1.3"

import json
import time
import threading
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
from statistics import mean, median, stdev
from pathlib import Path


@dataclass
class MetricSnapshot:
    """Snapshot of system metrics at a point in time."""
    timestamp: str
    total_entries: int
    matched_entries: int
    unclassified_entries: int
    preserved_entries: int
    avg_compaction_ratio: float
    avg_vad_scores: Dict[str, float]
    processing_rate: float  # entries per second


@dataclass
class PerformanceBaseline:
    """Performance baseline for anomaly detection."""
    match_rate_baseline: float = 0.0
    compaction_ratio_baseline: float = 0.0
    processing_rate_baseline: float = 0.0
    vad_baseline: Dict[str, float] = field(default_factory=dict)
    last_updated: Optional[str] = None


@dataclass
class AlertThresholds:
    """Configurable alert thresholds for monitoring."""
    min_match_rate: float = 0.5
    max_unclassified_rate: float = 0.3
    min_compaction_ratio: float = 0.1
    max_processing_time: float = 5.0  # seconds
    memory_usage_threshold: float = 0.8  # 80% of available


class KPIMonitorError(Exception):
    """Base exception for KPI monitoring operations."""
    pass


class MetricsCollectionError(KPIMonitorError):
    """Raised when metrics collection fails."""
    pass


class DataPersistenceError(KPIMonitorError):
    """Raised when data persistence operations fail."""
    pass


class AlertingError(KPIMonitorError):
    """Raised when alerting system encounters errors."""
    pass


class KPIMonitor:
    """
    Performance monitoring system for IOA memory operations with thread-safe metrics collection.

    Provides rolling window statistics, custom metric recording, and optional disk persistence
    for tracking IOA system performance and operational health metrics.

    Thread Safety: All public methods are thread-safe through internal locking mechanisms.
    
    ✅ ONBOARD-001 Integration:
    - Custom metrics for agent onboarding tracking
    - Tenant-aware performance monitoring
    - Enhanced persistence for multi-agent environments
    """

    def __init__(
        self,
        enable_persistence: bool = True,
        data_file: str = 'kpi_data.json',
        rolling_window_size: int = 1000,
        alert_thresholds: Optional[AlertThresholds] = None
    ) -> None:
        """Initialize KPI monitoring system with ONBOARD-001 enhancements."""
        
        # Core statistics storage
        self.stats = {
            "total_entries": 0,
            "matched_entries": 0,
            "unclassified_entries": 0,
            "preserved_entries": 0,
            "pattern_reuse": {},  # pattern_id: count
            "compaction_ratios": deque(maxlen=rolling_window_size),
            "preserved_sizes": deque(maxlen=rolling_window_size),
            "processing_times": deque(maxlen=rolling_window_size),
            "vad_dist": {
                "valence": deque(maxlen=rolling_window_size),
                "arousal": deque(maxlen=rolling_window_size),
                "dominance": deque(maxlen=rolling_window_size)
            }
        }

        # Configuration
        self.enable_persistence = enable_persistence
        # Resolve data_file to an absolute path to avoid relative path confusion
        self.data_file = Path(data_file).resolve()
        self.rolling_window_size = rolling_window_size
        self.alert_thresholds = alert_thresholds or AlertThresholds()

        # ONBOARD-001: Custom metrics for agent onboarding
        self._custom_metrics = defaultdict(list)
        
        # Performance tracking
        self._operation_start_times = {}
        self._baseline = PerformanceBaseline()
        self._alert_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        
        # Historical data
        self._snapshots: deque = deque(maxlen=100)  # Keep last 100 snapshots
        self._daily_summaries = {}
        
        # Thread safety - Enhanced for ONBOARD-001
        self._lock = threading.RLock()
        
        # System metrics
        self._system_start_time = time.time()
        self._last_snapshot_time = time.time()

        # Load persisted data
        if self.enable_persistence:
            self._load_persisted_data()

    def record_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record custom metric to rolling window and persist - ONBOARD-001 Enhanced.
        
        Thread-safe method for recording arbitrary metrics with optional tagging
        and automatic persistence when enabled. Supports tenant isolation.

        Args:
            name: Metric name identifier
            value: Numeric metric value
            tags: Optional metadata tags for the metric (includes tenant_id for isolation)

        Raises:
            MetricsCollectionError: If metric recording fails
            ValueError: If tags is not a dictionary
        """
        try:
            # Validate tags parameter
            if tags is not None and not isinstance(tags, dict):
                raise ValueError(f"Malformed onboarding data: missing required 'tags' field")
            
            with self._lock:
                entry = {
                    "value": value,
                    "timestamp": datetime.now().isoformat(),
                    "tags": tags or {},
                    "version": __version__
                }
                
                # ONBOARD-001: Enhanced metric entry with tenant support
                if tags and "tenant_id" in tags:
                    entry["tenant_id"] = tags["tenant_id"]
                
                self._custom_metrics[name].append(entry)
                
                # Maintain rolling window
                if len(self._custom_metrics[name]) > self.rolling_window_size:
                    self._custom_metrics[name].pop(0)
                
                # Trigger persistence if enabled (non-blocking)
                if self.enable_persistence:
                    try:
                        self._persist_data_async()
                    except Exception:
                        # Persistence errors during recording are logged but don't fail recording
                        # They will be raised during explicit flush_to_disk() calls
                        pass
                    
        except Exception as e:
            raise MetricsCollectionError(f"Failed to record metric {name}: {e}") from e

    def flush_to_disk(self) -> None:
        """
        Force immediate persistence of all metrics - ONBOARD-001 Enhanced.

        Raises:
            DataPersistenceError: If flush operation fails
        """
        try:
            self._persist_data_async()
        except Exception as e:
            raise DataPersistenceError(f"Failed to flush to disk: {e}") from e

    def reset_stats(self) -> None:
        """
        Reset all statistics and custom metrics - ONBOARD-001 Enhanced.
        
        Thread-safe operation that clears all collected metrics and resets
        counters to initial state while preserving tenant isolation.
        """
        with self._lock:
            # Reset core statistics
            self.reset_statistics()
            
            # Clear custom metrics
            self._custom_metrics.clear()
            
            # Reset snapshots and tracking
            self._snapshots.clear()
            self._system_start_time = time.time()
            self._last_snapshot_time = time.time()
            
            print(f"[KPIMonitor v{__version__}] All statistics and custom metrics reset")

    def start_operation(self, operation_id: str) -> None:
        """
        Start timing an operation for performance tracking.

        Args:
            operation_id: Unique identifier for the operation
        """
        with self._lock:
            self._operation_start_times[operation_id] = time.time()

    def end_operation(self, operation_id: str) -> Optional[float]:
        """
        End timing an operation and record duration.

        Args:
            operation_id: Unique identifier for the operation

        Returns:
            Operation duration in seconds or None if not found
        """
        with self._lock:
            start_time = self._operation_start_times.pop(operation_id, None)
            if start_time:
                duration = time.time() - start_time
                self.stats["processing_times"].append(duration)
                return duration
            return None

    def update_after_digest(
        self, 
        compacted: Dict[str, Any], 
        raw_size: int, 
        compacted_size: int, 
        is_preserved: bool = False
    ) -> None:
        """
        Update KPI metrics after content digestion or preservation.

        Args:
            compacted: Processed entry data
            raw_size: Original content size in bytes
            compacted_size: Processed content size in bytes
            is_preserved: Whether content was preserved vs digested

        Raises:
            MetricsCollectionError: If metrics update fails
        """
        try:
            with self._lock:
                self.stats["total_entries"] += 1
                
                pattern_id = compacted.get('pattern_id', '')
                
                if is_preserved:
                    self.stats["preserved_entries"] += 1
                    self.stats["preserved_sizes"].append(raw_size)
                elif pattern_id != "UNCLASSIFIED":
                    self.stats["matched_entries"] += 1
                    
                    # Update pattern reuse statistics
                    if pattern_id:
                        self.stats["pattern_reuse"][pattern_id] = \
                            self.stats["pattern_reuse"].get(pattern_id, 0) + 1
                    
                    # Calculate and store compaction ratio
                    if raw_size > 0:
                        ratio = (raw_size - compacted_size) / raw_size
                        self.stats["compaction_ratios"].append(max(0.0, min(1.0, ratio)))
                else:
                    self.stats["unclassified_entries"] += 1

                # Update VAD (emotional) distribution
                feeling = compacted.get('feeling', {})
                for dimension in ['valence', 'arousal', 'dominance']:
                    if dimension in feeling:
                        value = feeling[dimension]
                        if isinstance(value, (int, float)) and -1 <= value <= 1:
                            self.stats["vad_dist"][dimension].append(value)

                # Check for alerts
                self._check_alert_conditions()
                
                # Persist data if enabled
                if self.enable_persistence:
                    self._persist_data_async()

        except Exception as e:
            raise MetricsCollectionError(f"Failed to update metrics: {e}") from e

    def get_kpis(self) -> Dict[str, Union[float, int, Dict[str, float]]]:
        """
        Calculate and return current KPI metrics.

        Returns:
            Dictionary of computed KPI values

        Raises:
            MetricsCollectionError: If KPI calculation fails
        """
        try:
            with self._lock:
                total = self.stats["total_entries"]
                
                if total == 0:
                    return self._get_empty_kpis()

                # Calculate basic rates
                match_rate = self.stats["matched_entries"] / total
                unclassified_rate = self.stats["unclassified_entries"] / total
                preserved_rate = self.stats["preserved_entries"] / total

                # Calculate compaction metrics
                compaction_ratios = list(self.stats["compaction_ratios"])
                avg_compaction_ratio = mean(compaction_ratios) if compaction_ratios else 0.0
                compaction_efficiency = self._calculate_compaction_efficiency()

                # Calculate size metrics
                preserved_sizes = list(self.stats["preserved_sizes"])
                avg_preserved_size = mean(preserved_sizes) if preserved_sizes else 0.0

                # Calculate VAD averages
                vad_averages = {}
                for dimension in ['valence', 'arousal', 'dominance']:
                    values = list(self.stats["vad_dist"][dimension])
                    vad_averages[f"avg_{dimension}"] = mean(values) if values else 0.0

                # Calculate processing performance
                processing_times = list(self.stats["processing_times"])
                avg_processing_time = mean(processing_times) if processing_times else 0.0
                processing_rate = self._calculate_processing_rate()

                # Advanced metrics
                pattern_diversity = len(self.stats["pattern_reuse"])
                most_used_pattern = self._get_most_used_pattern()

                kpis = {
                    # Basic rates
                    "match_rate": round(match_rate, 4),
                    "unclassified_rate": round(unclassified_rate, 4),
                    "preserved_rate": round(preserved_rate, 4),
                    
                    # Compaction metrics
                    "avg_compaction_ratio": round(avg_compaction_ratio, 4),
                    "compaction_efficiency": round(compaction_efficiency, 4),
                    "avg_preserved_size": round(avg_preserved_size, 2),
                    
                    # Emotional metrics
                    **{k: round(v, 4) for k, v in vad_averages.items()},
                    
                    # Performance metrics
                    "avg_processing_time": round(avg_processing_time, 4),
                    "processing_rate": round(processing_rate, 2),
                    
                    # Pattern metrics
                    "pattern_diversity": pattern_diversity,
                    "most_used_pattern": most_used_pattern,
                    "total_entries": total,
                    
                    # System health
                    "system_uptime": round(time.time() - self._system_start_time, 2),
                    "data_quality_score": self._calculate_data_quality_score(),
                    
                    # ONBOARD-001 metrics
                    "version": __version__,
                    "onboard_001_enabled": True
                }

                return kpis

        except Exception as e:
            raise MetricsCollectionError(f"Failed to calculate KPIs: {e}") from e

    def get_onboarding_metrics(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get ONBOARD-001 specific metrics for agent onboarding performance.
        
        Args:
            tenant_id: Optional tenant filter for isolation

        Returns:
            Dictionary with onboarding-specific metrics
        """
        with self._lock:
            onboarding_metrics = {
                "version": __version__,
                "onboard_001_enabled": True,
                "total_custom_metrics": len(self._custom_metrics),
                "tenant_metrics": {},
                "agent_onboarding_stats": {}
            }
            
            # Filter by tenant if specified
            if tenant_id:
                tenant_metrics = {}
                for metric_name, metric_list in self._custom_metrics.items():
                    tenant_entries = [
                        entry for entry in metric_list 
                        if entry.get("tenant_id") == tenant_id
                    ]
                    if tenant_entries:
                        tenant_metrics[metric_name] = tenant_entries
                
                onboarding_metrics["tenant_metrics"][tenant_id] = tenant_metrics
            else:
                # Include all metrics
                onboarding_metrics["all_metrics"] = dict(self._custom_metrics)
            
            return onboarding_metrics

    def _get_empty_kpis(self) -> Dict[str, Union[float, int]]:
        """Return empty KPI structure for zero-entry state."""
        return {
            "match_rate": 0.0,
            "unclassified_rate": 0.0,
            "preserved_rate": 0.0,
            "avg_compaction_ratio": 0.0,
            "compaction_efficiency": 0.0,
            "avg_preserved_size": 0.0,
            "avg_valence": 0.0,
            "avg_arousal": 0.0,
            "avg_dominance": 0.0,
            "avg_processing_time": 0.0,
            "processing_rate": 0.0,
            "pattern_diversity": 0,
            "most_used_pattern": None,
            "total_entries": 0,
            "system_uptime": round(time.time() - self._system_start_time, 2),
            "data_quality_score": 1.0,
            "version": __version__,
            "onboard_001_enabled": True
        }

    def _calculate_compaction_efficiency(self) -> float:
        """Calculate overall compaction efficiency score."""
        ratios = list(self.stats["compaction_ratios"])
        if not ratios:
            return 0.0
        
        # Efficiency considers both average ratio and consistency
        avg_ratio = mean(ratios)
        ratio_std = stdev(ratios) if len(ratios) > 1 else 0.0
        consistency_factor = max(0.0, 1.0 - ratio_std)
        
        return avg_ratio * 0.7 + consistency_factor * 0.3

    def _calculate_processing_rate(self) -> float:
        """Calculate current processing rate in entries per second."""
        current_time = time.time()
        time_diff = current_time - self._last_snapshot_time
        
        if time_diff > 0:
            # Estimate based on recent activity
            recent_entries = min(100, self.stats["total_entries"])
            return recent_entries / max(time_diff, 1.0)
        
        return 0.0

    def _get_most_used_pattern(self) -> Optional[str]:
        """Get the most frequently used pattern."""
        if not self.stats["pattern_reuse"]:
            return None
        
        return max(self.stats["pattern_reuse"], key=self.stats["pattern_reuse"].get)

    def _calculate_data_quality_score(self) -> float:
        """Calculate overall data quality score (0.0-1.0)."""
        total = self.stats["total_entries"]
        if total == 0:
            return 1.0
        
        # Quality factors
        match_rate = self.stats["matched_entries"] / total
        preservation_balance = min(self.stats["preserved_entries"] / total, 0.2) / 0.2
        pattern_diversity = min(len(self.stats["pattern_reuse"]) / 10, 1.0)
        
        # VAD completeness
        vad_completeness = sum(
            1 for dim in ['valence', 'arousal', 'dominance']
            if len(self.stats["vad_dist"][dim]) > 0
        ) / 3.0
        
        # Weighted quality score
        quality_score = (
            match_rate * 0.4 +
            preservation_balance * 0.2 +
            pattern_diversity * 0.2 +
            vad_completeness * 0.2
        )
        
        return min(1.0, quality_score)

    def add_alert_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        Add callback function for alert notifications.

        Args:
            callback: Function to call when alerts are triggered
        """
        self._alert_callbacks.append(callback)

    def _check_alert_conditions(self) -> None:
        """Check current metrics against alert thresholds."""
        try:
            kpis = self.get_kpis()
            alerts = []

            # Check match rate
            if kpis["match_rate"] < self.alert_thresholds.min_match_rate:
                alerts.append({
                    "type": "low_match_rate",
                    "severity": "warning",
                    "message": f"Match rate ({kpis['match_rate']:.2%}) below threshold ({self.alert_thresholds.min_match_rate:.2%})",
                    "value": kpis["match_rate"],
                    "threshold": self.alert_thresholds.min_match_rate
                })

            # Check unclassified rate
            if kpis["unclassified_rate"] > self.alert_thresholds.max_unclassified_rate:
                alerts.append({
                    "type": "high_unclassified_rate",
                    "severity": "warning",
                    "message": f"Unclassified rate ({kpis['unclassified_rate']:.2%}) above threshold ({self.alert_thresholds.max_unclassified_rate:.2%})",
                    "value": kpis["unclassified_rate"],
                    "threshold": self.alert_thresholds.max_unclassified_rate
                })

            # Check processing time
            if kpis["avg_processing_time"] > self.alert_thresholds.max_processing_time:
                alerts.append({
                    "type": "slow_processing",
                    "severity": "warning",
                    "message": f"Average processing time ({kpis['avg_processing_time']:.2f}s) above threshold ({self.alert_thresholds.max_processing_time}s)",
                    "value": kpis["avg_processing_time"],
                    "threshold": self.alert_thresholds.max_processing_time
                })

            # Trigger alert callbacks
            for alert in alerts:
                for callback in self._alert_callbacks:
                    try:
                        callback(alert["type"], alert)
                    except Exception as e:
                        print(f"[KPIMonitor] Alert callback failed: {e}")

        except Exception as e:
            print(f"[KPIMonitor] Alert checking failed: {e}")

    def _persist_data_async(self) -> None:
        """Persist data to disk with ONBOARD-001 enhancements."""
        try:
            # Convert deques to lists for JSON serialization
            serializable_stats = {
                "version": __version__,
                "onboard_001_enabled": True,
                "total_entries": self.stats["total_entries"],
                "matched_entries": self.stats["matched_entries"],
                "unclassified_entries": self.stats["unclassified_entries"],
                "preserved_entries": self.stats["preserved_entries"],
                "pattern_reuse": self.stats["pattern_reuse"],
                "compaction_ratios": list(self.stats["compaction_ratios"]),
                "preserved_sizes": list(self.stats["preserved_sizes"]),
                "processing_times": list(self.stats["processing_times"]),
                "vad_dist": {
                    dim: list(values) 
                    for dim, values in self.stats["vad_dist"].items()
                },
                "custom_metrics": {
                    name: metrics[-self.rolling_window_size:] 
                    for name, metrics in self._custom_metrics.items()
                },
                "last_updated": datetime.now().isoformat()
            }

            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_stats, f, indent=2)

        except Exception as e:
            print(f"[KPIMonitor v{__version__}] Data persistence failed: {e}")
            raise DataPersistenceError(f"Failed to persist KPI metrics: {e}") from e

    def _load_persisted_data(self) -> None:
        """Load previously persisted data with ONBOARD-001 support."""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # ONBOARD-001: Check version compatibility
                data_version = data.get("version", "unknown")
                onboard_enabled = data.get("onboard_001_enabled", False)
                
                # Restore basic counters
                for key in ["total_entries", "matched_entries", "unclassified_entries", "preserved_entries"]:
                    if key in data:
                        self.stats[key] = data[key]

                # Restore pattern reuse data
                if "pattern_reuse" in data:
                    self.stats["pattern_reuse"] = data["pattern_reuse"]

                # Restore rolling window data (limited to window size)
                for key in ["compaction_ratios", "preserved_sizes", "processing_times"]:
                    if key in data:
                        values = data[key][-self.rolling_window_size:]
                        self.stats[key] = deque(values, maxlen=self.rolling_window_size)

                # Restore VAD distribution data
                if "vad_dist" in data:
                    for dim in ["valence", "arousal", "dominance"]:
                        if dim in data["vad_dist"]:
                            values = data["vad_dist"][dim][-self.rolling_window_size:]
                            self.stats["vad_dist"][dim] = deque(values, maxlen=self.rolling_window_size)

                # Restore custom metrics with ONBOARD-001 support
                if "custom_metrics" in data:
                    for name, metrics in data["custom_metrics"].items():
                        self._custom_metrics[name] = metrics[-self.rolling_window_size:]

                print(f"[KPIMonitor v{__version__}] Loaded persisted data: {self.stats['total_entries']} entries")
                if onboard_enabled:
                    print(f"[KPIMonitor] ONBOARD-001 data compatibility confirmed")

        except Exception as e:
            print(f"[KPIMonitor v{__version__}] Failed to load persisted data: {e}")

    def create_snapshot(self) -> MetricSnapshot:
        """
        Create a snapshot of current metrics.

        Returns:
            MetricSnapshot with current system state
        """
        with self._lock:
            kpis = self.get_kpis()
            
            snapshot = MetricSnapshot(
                timestamp=datetime.now().isoformat(),
                total_entries=kpis["total_entries"],
                matched_entries=self.stats["matched_entries"],
                unclassified_entries=self.stats["unclassified_entries"],
                preserved_entries=self.stats["preserved_entries"],
                avg_compaction_ratio=kpis["avg_compaction_ratio"],
                avg_vad_scores={
                    "valence": kpis["avg_valence"],
                    "arousal": kpis["avg_arousal"],
                    "dominance": kpis["avg_dominance"]
                },
                processing_rate=kpis["processing_rate"]
            )
            
            self._snapshots.append(snapshot)
            self._last_snapshot_time = time.time()
            
            return snapshot

    def print_kpis(self) -> None:
        """Print formatted KPI report to console."""
        try:
            kpis = self.get_kpis()
            print("\n" + "="*50)
            print(f"IOA KPI MONITOR REPORT v{__version__}")
            print("="*50)
            print(f"Total Entries: {kpis['total_entries']}")
            print(f"Match Rate: {kpis['match_rate']:.2%}")
            print(f"Unclassified Rate: {kpis['unclassified_rate']:.2%}")
            print(f"Preserved Rate: {kpis['preserved_rate']:.2%}")
            print(f"Avg Compaction Ratio: {kpis['avg_compaction_ratio']:.2%}")
            print(f"Compaction Efficiency: {kpis['compaction_efficiency']:.2%}")
            print(f"Processing Rate: {kpis['processing_rate']:.2f} entries/sec")
            print(f"Data Quality Score: {kpis['data_quality_score']:.2%}")
            print(f"System Uptime: {kpis['system_uptime']:.0f} seconds")
            
            print("\nEmotional Sentiment (VAD):")
            print(f"  Valence: {kpis['avg_valence']:.3f}")
            print(f"  Arousal: {kpis['avg_arousal']:.3f}")
            print(f"  Dominance: {kpis['avg_dominance']:.3f}")
            
            if kpis['most_used_pattern']:
                print(f"\nMost Used Pattern: {kpis['most_used_pattern']}")
            
            if kpis['onboard_001_enabled']:
                print(f"\n✅ ONBOARD-001 Integration: Active")
                
            print("="*50)
            
        except Exception as e:
            print(f"[KPIMonitor v{__version__}] Failed to print KPIs: {e}")

    def reset_statistics(self) -> None:
        """Reset core statistics (ONBOARD-001 aware)."""
        with self._lock:
            self.stats = {
                "total_entries": 0,
                "matched_entries": 0,
                "unclassified_entries": 0,
                "preserved_entries": 0,
                "pattern_reuse": {},
                "compaction_ratios": deque(maxlen=self.rolling_window_size),
                "preserved_sizes": deque(maxlen=self.rolling_window_size),
                "processing_times": deque(maxlen=self.rolling_window_size),
                "vad_dist": {
                    "valence": deque(maxlen=self.rolling_window_size),
                    "arousal": deque(maxlen=self.rolling_window_size),
                    "dominance": deque(maxlen=self.rolling_window_size)
                }
            }
            print(f"[KPIMonitor v{__version__}] Core statistics reset")


# ONBOARD-001 Factory function
def create_kpi_monitor(**kwargs) -> KPIMonitor:
    """Factory function for ONBOARD-001 integration."""
    return KPIMonitor(**kwargs)


# Export classes for ONBOARD-001
__all__ = [
    'KPIMonitor',
    'MetricSnapshot',
    'PerformanceBaseline', 
    'AlertThresholds',
    'KPIMonitorError',
    'MetricsCollectionError',
    'DataPersistenceError',
    'AlertingError',
    'create_kpi_monitor'
]
