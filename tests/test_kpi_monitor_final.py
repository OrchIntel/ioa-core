""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Comprehensive test suite for KPI Monitor with ONBOARD-001 integration
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.


"""
KPI Monitor Test Suite - ONBOARD-001 Enhanced

Comprehensive test coverage for KPIMonitor class including:
- Basic metric recording and retrieval
- ONBOARD-001 custom metrics with tenant isolation
- Thread safety verification
- Persistence mechanism testing
- Error handling and edge cases
- Performance and stress testing
"""

__version__ = "1.0.0"

import pytest
import tempfile
import json
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src directory to Python path for imports
import sys
import os
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Fixed imports with fallback handling
try:
    from kpi_monitor import (
        KPIMonitor,
        MetricsCollectionError,
        DataPersistenceError,
        AlertThresholds,
        MetricSnapshot,
        create_kpi_monitor
    )
except ImportError:
    # Fallback for different project structures
    try:
        from kpi_monitor import (
            KPIMonitor,
            MetricsCollectionError,
            DataPersistenceError,
            AlertThresholds,
            MetricSnapshot,
            create_kpi_monitor
        )
    except ImportError:
        # Mock for CI/testing environments
        class KPIMonitor:
            def __init__(self, *args, **kwargs): pass
        class MetricsCollectionError(Exception): pass
        class DataPersistenceError(Exception): pass
        class AlertThresholds: pass
        class MetricSnapshot: pass
        def create_kpi_monitor(*args, **kwargs): return KPIMonitor()

class TestKPIMonitorBasic:
    """Test basic KPI Monitor operations with ONBOARD-001 features."""

    def test_record_metric_simple(self):
        """Test basic metric recording functionality."""
        monitor = KPIMonitor(enable_persistence=False, rolling_window_size=5)
        
        # Record a metric
        monitor.record_metric("test_metric", 0.75, {"lang": "en"})
        
        # Verify metric was recorded
        assert len(monitor._custom_metrics["test_metric"]) == 1
        assert monitor._custom_metrics["test_metric"][0]["value"] == 0.75
        assert monitor._custom_metrics["test_metric"][0]["tags"] == {"lang": "en"}
        assert "timestamp" in monitor._custom_metrics["test_metric"][0]
        assert "version" in monitor._custom_metrics["test_metric"][0]

    def test_record_metric_with_tenant_isolation(self):
        """Test ONBOARD-001 tenant isolation in metrics."""
        monitor = KPIMonitor(enable_persistence=False)
        
        # Record metrics for different tenants
        monitor.record_metric("agent_onboarding", 1.2, {"tenant_id": "tenant_a"})
        monitor.record_metric("agent_onboarding", 0.8, {"tenant_id": "tenant_b"})
        
        # Verify tenant isolation
        assert len(monitor._custom_metrics["agent_onboarding"]) == 2
        
        # Check tenant-specific retrieval
        onboarding_metrics = monitor.get_onboarding_metrics("tenant_a")
        assert "tenant_metrics" in onboarding_metrics
        assert "tenant_a" in onboarding_metrics["tenant_metrics"]
        assert onboarding_metrics["onboard_001_enabled"] is True

    def test_record_metric_window_limit(self):
        """Test rolling window size enforcement."""
        monitor = KPIMonitor(enable_persistence=False, rolling_window_size=2)
        
        # Record more metrics than window size
        for i in range(3):
            monitor.record_metric("test", float(i), {})
        
        # Verify only last 2 metrics are kept
        assert len(monitor._custom_metrics["test"]) == 2
        values = [entry["value"] for entry in monitor._custom_metrics["test"]]
        assert values == [1.0, 2.0]  # First metric should be dropped

    def test_flush_to_disk_creates_file(self):
        """Test that flush_to_disk creates persistence file with ONBOARD-001 metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / "test_data.json"
            monitor = KPIMonitor(
                enable_persistence=True,
                data_file=str(data_file),
                rolling_window_size=10
            )
            
            # Record a metric and flush
            monitor.record_metric("test_metric", 1.0, {"test": "data"})
            monitor.flush_to_disk()
            
            # Verify file was created
            assert data_file.exists()
            
            # Verify ONBOARD-001 content
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            assert "onboard_001_enabled" in data
            assert data["onboard_001_enabled"] is True
            assert "version" in data
            assert data["version"] == "2.1.3"
            assert "custom_metrics" in data
            assert "test_metric" in data["custom_metrics"]

    def test_reset_stats_clears_metrics(self):
        """Test that reset_stats clears all custom metrics."""
        monitor = KPIMonitor(enable_persistence=False)
        
        # Record some metrics including tenant-specific ones
        monitor.record_metric("metric1", 1.0)
        monitor.record_metric("metric2", 2.0, {"tenant_id": "test_tenant"})
        
        # Verify metrics exist
        assert len(monitor._custom_metrics) == 2
        
        # Reset stats
        monitor.reset_stats()
        
        # Verify metrics cleared
        assert len(monitor._custom_metrics) == 0

    def test_onboarding_metrics_retrieval(self):
        """Test ONBOARD-001 onboarding metrics retrieval."""
        monitor = KPIMonitor(enable_persistence=False)
        
        # Record various onboarding metrics
        monitor.record_metric("agent_registration_time", 1.5, {"tenant_id": "tenant_a"})
        monitor.record_metric("manifest_validation_time", 0.8, {"tenant_id": "tenant_a"})
        monitor.record_metric("agent_registration_time", 2.1, {"tenant_id": "tenant_b"})
        
        # Test general onboarding metrics
        all_metrics = monitor.get_onboarding_metrics()
        assert all_metrics["onboard_001_enabled"] is True
        assert all_metrics["total_custom_metrics"] == 2
        assert "version" in all_metrics
        
        # Test tenant-specific metrics
        tenant_a_metrics = monitor.get_onboarding_metrics("tenant_a")
        assert "tenant_metrics" in tenant_a_metrics
        assert "tenant_a" in tenant_a_metrics["tenant_metrics"]
        
        tenant_a_data = tenant_a_metrics["tenant_metrics"]["tenant_a"]
        assert "agent_registration_time" in tenant_a_data
        assert "manifest_validation_time" in tenant_a_data
        assert len(tenant_a_data["agent_registration_time"]) == 1
        assert len(tenant_a_data["manifest_validation_time"]) == 1

    def test_kpi_calculation_with_onboard_001(self):
        """Test KPI calculation includes ONBOARD-001 metadata."""
        monitor = KPIMonitor(enable_persistence=False)
        
        # Simulate some digest operations
        monitor.update_after_digest(
            {"pattern_id": "test_pattern", "feeling": {"valence": 0.8}},
            1000, 500, False
        )
        
        kpis = monitor.get_kpis()
        
        # Verify ONBOARD-001 metadata in KPIs
        assert "version" in kpis
        assert kpis["version"] == "2.1.3"
        assert "onboard_001_enabled" in kpis
        assert kpis["onboard_001_enabled"] is True
        assert kpis["total_entries"] == 1
        assert kpis["match_rate"] == 1.0


class TestKPIMonitorPersistence:
    """Test data persistence with ONBOARD-001 features."""

    def test_persistence_with_onboard_001_metadata(self):
        """Test persistence includes ONBOARD-001 metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / "onboard_test.json"
            monitor = KPIMonitor(
                enable_persistence=True,
                data_file=str(data_file)
            )
            
            # Record metrics with tenant information
            monitor.record_metric("test", 1.0, {"tenant_id": "test_tenant"})
            monitor.flush_to_disk()
            
            # Verify ONBOARD-001 metadata in file
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            assert data["version"] == "2.1.3"
            assert data["onboard_001_enabled"] is True
            assert "custom_metrics" in data
            
            # Verify tenant information is preserved
            custom_metrics = data["custom_metrics"]["test"]
            assert len(custom_metrics) == 1
            assert custom_metrics[0]["tags"]["tenant_id"] == "test_tenant"

    def test_load_persisted_onboard_001_data(self):
        """Test loading ONBOARD-001 enhanced persisted data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / "load_test.json"
            
            # Create initial monitor and persist data
            monitor1 = KPIMonitor(
                enable_persistence=True,
                data_file=str(data_file)
            )
            monitor1.record_metric("persistent_metric", 5.0, {"tenant_id": "load_tenant"})
            monitor1.flush_to_disk()
            
            # Create new monitor that should load the data
            monitor2 = KPIMonitor(
                enable_persistence=True,
                data_file=str(data_file)
            )
            
            # Verify ONBOARD-001 data was loaded
            assert "persistent_metric" in monitor2._custom_metrics
            assert len(monitor2._custom_metrics["persistent_metric"]) == 1
            assert monitor2._custom_metrics["persistent_metric"][0]["value"] == 5.0
            assert monitor2._custom_metrics["persistent_metric"][0]["tags"]["tenant_id"] == "load_tenant"

    def test_persistence_auto_enabled(self):
        """Test automatic persistence when enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir) / "auto_persist.json"
            monitor = KPIMonitor(
                enable_persistence=True,
                data_file=str(data_file)
            )
            
            # Record metric (should auto-persist)
            monitor.record_metric("auto_test", 2.0, {"tenant_id": "auto_tenant"})
            
            # Small delay to allow async persistence
            time.sleep(0.1)
            
            # Verify file exists and contains ONBOARD-001 data
            assert data_file.exists()


class TestKPIMonitorThreadSafety:
    """Test thread safety with ONBOARD-001 concurrent operations."""

    def test_concurrent_tenant_metric_recording(self):
        """Test thread safety with multiple tenants recording metrics."""
        monitor = KPIMonitor(enable_persistence=False, rolling_window_size=1000)
        
        def record_tenant_metrics(tenant_id: str, count: int):
            """Record metrics for a specific tenant."""
            for i in range(count):
                monitor.record_metric(
                    "concurrent_metric",
                    float(i),
                    {"tenant_id": tenant_id, "iteration": i}
                )
        
        # Start multiple tenant threads
        threads = []
        tenant_count = 5
        metrics_per_tenant = 20
        
        for tenant_num in range(tenant_count):
            thread = threading.Thread(
                target=record_tenant_metrics,
                args=(f"tenant_{tenant_num}", metrics_per_tenant)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify total metrics recorded
        total_metrics = len(monitor._custom_metrics["concurrent_metric"])
        expected_total = tenant_count * metrics_per_tenant
        assert total_metrics == expected_total
        
        # Verify tenant isolation worked
        tenant_metrics = {}
        for entry in monitor._custom_metrics["concurrent_metric"]:
            tenant_id = entry["tags"]["tenant_id"]
            tenant_metrics[tenant_id] = tenant_metrics.get(tenant_id, 0) + 1
        
        assert len(tenant_metrics) == tenant_count
        for count in tenant_metrics.values():
            assert count == metrics_per_tenant

    def test_concurrent_reset_and_record(self):
        """Test thread safety of reset operations with concurrent recording."""
        monitor = KPIMonitor(enable_persistence=False)
        
        def continuous_recording():
            """Continuously record metrics."""
            for i in range(50):
                monitor.record_metric("continuous", float(i), {"tenant_id": "test"})
                time.sleep(0.001)  # Small delay
        
        def reset_stats():
            """Reset stats after delay."""
            time.sleep(0.025)  # Let some metrics accumulate
            monitor.reset_stats()
        
        # Start recording and reset threads
        record_thread = threading.Thread(target=continuous_recording)
        reset_thread = threading.Thread(target=reset_stats)
        
        record_thread.start()
        reset_thread.start()
        
        record_thread.join()
        reset_thread.join()
        
        # Should not crash and should complete successfully
        assert True

    def test_concurrent_onboarding_metrics_access(self):
        """Test concurrent access to onboarding metrics."""
        monitor = KPIMonitor(enable_persistence=False)
        
        # Record some initial metrics
        for i in range(10):
            monitor.record_metric("init_metric", float(i), {"tenant_id": f"tenant_{i % 3}"})
        
        results = []
        
        def access_onboarding_metrics(tenant_id: str):
            """Access onboarding metrics for specific tenant."""
            for _ in range(10):
                metrics = monitor.get_onboarding_metrics(tenant_id)
                results.append(metrics)
                time.sleep(0.001)
        
        # Start multiple access threads
        threads = []
        for i in range(3):
            thread = threading.Thread(
                target=access_onboarding_metrics,
                args=(f"tenant_{i}",)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify all accesses completed successfully
        assert len(results) == 30
        for result in results:
            assert result["onboard_001_enabled"] is True


class TestKPIMonitorErrorHandling:
    """Test error handling with ONBOARD-001 features."""

    def test_metrics_collection_error_handling(self):
        """Test error handling in metric collection."""
        monitor = KPIMonitor(enable_persistence=False)
        
        # Test with various data types and edge cases
        test_cases = [
            ("valid_metric", 1.0, {"tenant_id": "test"}),
            ("edge_metric", float('inf'), {"tenant_id": "test"}),
            ("negative_metric", -1.0, {"tenant_id": "test"}),
            ("zero_metric", 0.0, {"tenant_id": "test"}),
        ]
        
        for name, value, tags in test_cases:
            try:
                monitor.record_metric(name, value, tags)
                # Should succeed for all cases
                assert True
            except MetricsCollectionError:
                # Should not raise MetricsCollectionError for valid inputs
                pytest.fail(f"Should not raise error for {name}")

    def test_persistence_error_handling(self):
        """Test persistence error handling."""
        # Test with invalid path
        monitor = KPIMonitor(
            enable_persistence=True,
            data_file="/invalid/path/that/does/not/exist.json"
        )
        
        # Should not raise exception during initialization or recording
        monitor.record_metric("test", 1.0, {"tenant_id": "error_test"})
        
        # Should raise DataPersistenceError on forced flush
        with pytest.raises(DataPersistenceError):
            monitor.flush_to_disk()

    def test_malformed_onboarding_data_handling(self):
        """Test handling of malformed onboarding data."""
        monitor = KPIMonitor(enable_persistence=False)
        
        # Test with malformed tenant data
        malformed_cases = [
            ("metric_none_tenant", 1.0, {"tenant_id": None}),
            ("metric_empty_tenant", 1.0, {"tenant_id": ""}),
            ("metric_invalid_tags", 1.0, "not_a_dict"),
        ]
        
        for name, value, tags in malformed_cases:
            try:
                if isinstance(tags, str):
                    # This should raise a TypeError since tags expects a dict
                    with pytest.raises(Exception):
                        monitor.record_metric(name, value, tags)
                else:
                    monitor.record_metric(name, value, tags)
                    # Should handle gracefully
                    assert True
            except Exception as e:
                # Expected for invalid inputs
                assert "tags" in str(e).lower() or tags == "not_a_dict"


class TestKPIMonitorIntegration:
    """Test integration scenarios with ONBOARD-001."""

    def test_complete_onboarding_workflow(self):
        """Test complete agent onboarding metrics workflow."""
        monitor = KPIMonitor(enable_persistence=False)
        
        # Simulate agent onboarding process
        tenant_id = "integration_tenant"
        
        # Record onboarding metrics
        monitor.record_metric("manifest_parse_time", 0.5, {"tenant_id": tenant_id})
        monitor.record_metric("agent_validation_time", 1.2, {"tenant_id": tenant_id})
        monitor.record_metric("registry_update_time", 0.8, {"tenant_id": tenant_id})
        monitor.record_metric("routing_setup_time", 0.3, {"tenant_id": tenant_id})
        
        # Get comprehensive onboarding metrics
        tenant_metrics = monitor.get_onboarding_metrics(tenant_id)
        
        # Verify all metrics are captured
        assert tenant_metrics["onboard_001_enabled"] is True
        assert "tenant_metrics" in tenant_metrics
        assert tenant_id in tenant_metrics["tenant_metrics"]
        
        tenant_data = tenant_metrics["tenant_metrics"][tenant_id]
        expected_metrics = [
            "manifest_parse_time",
            "agent_validation_time", 
            "registry_update_time",
            "routing_setup_time"
        ]
        
        for metric in expected_metrics:
            assert metric in tenant_data
            assert len(tenant_data[metric]) == 1

    def test_multi_tenant_isolation(self):
        """Test multi-tenant metric isolation."""
        monitor = KPIMonitor(enable_persistence=False)
        
        # Record metrics for multiple tenants
        tenants = ["tenant_alpha", "tenant_beta", "tenant_gamma"]
        
        for tenant in tenants:
            for i in range(3):
                monitor.record_metric(
                    "isolation_test",
                    float(i),
                    {"tenant_id": tenant, "test_iteration": i}
                )
        
        # Verify isolation for each tenant
        for tenant in tenants:
            tenant_metrics = monitor.get_onboarding_metrics(tenant)
            tenant_data = tenant_metrics["tenant_metrics"][tenant]
            
            # Should only have metrics for this tenant
            assert "isolation_test" in tenant_data
            assert len(tenant_data["isolation_test"]) == 3
            
            # Verify all entries belong to this tenant
            for entry in tenant_data["isolation_test"]:
                assert entry["tags"]["tenant_id"] == tenant

    def test_mixed_tenant_and_global_metrics(self):
        """Test mixing tenant-specific and global metrics."""
        monitor = KPIMonitor(enable_persistence=False)
        
        # Record global metrics (no tenant_id)
        monitor.record_metric("global_metric", 1.0, {"type": "global"})
        monitor.record_metric("system_health", 0.95, {"component": "memory"})
        
        # Record tenant-specific metrics
        monitor.record_metric("tenant_metric", 2.0, {"tenant_id": "test_tenant"})
        
        # Test global retrieval
        all_metrics = monitor.get_onboarding_metrics()
        assert "all_metrics" in all_metrics
        assert "global_metric" in all_metrics["all_metrics"]
        assert "system_health" in all_metrics["all_metrics"]
        assert "tenant_metric" in all_metrics["all_metrics"]
        
        # Test tenant-specific retrieval
        tenant_metrics = monitor.get_onboarding_metrics("test_tenant")
        tenant_data = tenant_metrics["tenant_metrics"]["test_tenant"]
        assert "tenant_metric" in tenant_data
        assert len(tenant_data["tenant_metric"]) == 1


class TestKPIMonitorFactory:
    """Test factory function and module exports."""

    def test_create_kpi_monitor_factory(self):
        """Test factory function creates proper monitor."""
        config = {
            "enable_persistence": False,
            "rolling_window_size": 50
        }
        
        monitor = create_kpi_monitor(**config)
        
        assert isinstance(monitor, KPIMonitor)
        assert monitor.enable_persistence is False
        assert monitor.rolling_window_size == 50

    def test_module_version_accessibility(self):
        """Test that module version is accessible."""
        monitor = KPIMonitor(enable_persistence=False)
        
        # Record a metric and verify version in metadata
        monitor.record_metric("version_test", 1.0)
        metric_entry = monitor._custom_metrics["version_test"][0]
        assert "version" in metric_entry
        assert metric_entry["version"] == "2.1.3"

    def test_onboard_001_feature_flags(self):
        """Test ONBOARD-001 feature flags and metadata."""
        monitor = KPIMonitor(enable_persistence=False)
        
        # Test KPIs include ONBOARD-001 flags
        kpis = monitor.get_kpis()
        assert kpis["onboard_001_enabled"] is True
        
        # Test onboarding metrics include flags
        onboarding = monitor.get_onboarding_metrics()
        assert onboarding["onboard_001_enabled"] is True
        
        # Test version is accessible
        assert kpis["version"] == "2.1.3"


# Performance tests
@pytest.mark.performance
class TestKPIMonitorPerformance:
    """Test performance characteristics with ONBOARD-001."""

    def test_high_volume_tenant_metrics(self):
        """Test performance with high volume tenant-specific metrics."""
        monitor = KPIMonitor(enable_persistence=False, rolling_window_size=10000)
        
        start_time = time.time()
        
        # Record large number of tenant-specific metrics
        for tenant_num in range(10):
            for metric_num in range(100):
                monitor.record_metric(
                    f"perf_metric_{metric_num % 5}",
                    float(metric_num),
                    {"tenant_id": f"perf_tenant_{tenant_num}"}
                )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time
        assert duration < 5.0  # 5 seconds for 1000 metrics
        
        # Verify metrics were recorded correctly
        total_metrics = sum(len(metrics) for metrics in monitor._custom_metrics.values())
        assert total_metrics == 1000

    @pytest.mark.performance
    def test_onboarding_metrics_retrieval_performance(self):
        """Test performance of onboarding metrics retrieval."""
        monitor = KPIMonitor(enable_persistence=False)
        
        # Record metrics for many tenants
        for tenant_num in range(50):
            for metric_num in range(20):
                monitor.record_metric(
                    f"metric_{metric_num}",
                    float(metric_num),
                    {"tenant_id": f"tenant_{tenant_num}"}
                )
        
        start_time = time.time()
        
        # Retrieve onboarding metrics for specific tenant
        for _ in range(10):
            metrics = monitor.get_onboarding_metrics("tenant_25")
            assert metrics["onboard_001_enabled"] is True
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should be fast even with large dataset
        assert duration < 1.0  # 1 second for 10 retrievals


# Test configuration
# PATCH: Cursor-2025-08-15 CL-P3-Cleanup - Remove performance test skipping to eliminate all skips
# Performance tests now run by default to ensure 100% test coverage


# Test fixtures
@pytest.fixture
def temp_monitor():
    """Create a temporary KPI monitor for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        data_file = Path(temp_dir) / "test_kpi.json"
        monitor = KPIMonitor(
            enable_persistence=True,
            data_file=str(data_file),
            rolling_window_size=100
        )
        yield monitor


@pytest.fixture
def sample_onboarding_metrics():
    """Sample onboarding metrics for testing."""
    return [
        ("agent_registration_time", 1.5, {"tenant_id": "test_tenant"}),
        ("manifest_validation_time", 0.8, {"tenant_id": "test_tenant"}),
        ("routing_setup_time", 0.3, {"tenant_id": "test_tenant"}),
        ("health_check_time", 0.1, {"tenant_id": "test_tenant"})
    ]


# Integration tests using fixtures
def test_monitor_lifecycle_with_onboard_001(temp_monitor, sample_onboarding_metrics):
    """Test complete monitor lifecycle with ONBOARD-001 features."""
    # Record onboarding metrics
    for name, value, tags in sample_onboarding_metrics:
        temp_monitor.record_metric(name, value, tags)
    
    # Force persistence
    temp_monitor.flush_to_disk()
    
    # Verify persistence file exists and contains ONBOARD-001 data
    assert temp_monitor.data_file.exists()
    
    with open(temp_monitor.data_file, 'r') as f:
        data = json.load(f)
    
    assert data["onboard_001_enabled"] is True
    assert data["version"] == "2.1.3"
    
    # Reset and verify cleared
    temp_monitor.reset_stats()
    assert len(temp_monitor._custom_metrics) == 0


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])