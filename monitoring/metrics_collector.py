"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
IOA Advanced Metrics Collector
Enhanced metrics collection with detailed observability
"""

import os
import sys
import time
import json
import logging
import psutil
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from prometheus_client import start_http_server, Counter, Gauge, Histogram, Info

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class IOAMetricsCollector:
    def __init__(self, port: int = 8080):
        self.port = port
        self.logger = self._setup_logging()
        self.running = False
        
        # Prometheus metrics
        self._setup_metrics()
        
        # System metrics
        self.process = psutil.Process() if psutil else None
        
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger("ioa_metrics_collector")
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
        
    def _setup_metrics(self):
        """Setup all Prometheus metrics"""
        
        # Counters
        self.auth_failures = Counter('ioa_auth_failures_total', 'Total authentication failures')
        self.cb_opens = Counter('ioa_circuit_breaker_opens_total', 'Total circuit breaker opens', ['service'])
        self.backpressure_events = Counter('ioa_backpressure_events_total', 'Total backpressure events')
        self.encryption_errors = Counter('ioa_encryption_errors_total', 'Total encryption errors')
        self.kms_failures = Counter('ioa_kms_failures_total', 'Total KMS failures')
        self.s3_failures = Counter('ioa_s3_failures_total', 'Total S3 failures')
        self.audit_events = Counter('ioa_audit_events_total', 'Total audit events')
        self.policy_evaluations = Counter('ioa_policy_evaluations_total', 'Total policy evaluations')
        self.signature_operations = Counter('ioa_signature_operations_total', 'Total signature operations', ['operation'])
        
        # Gauges
        self.pending_batch = Gauge('ioa_pending_batch_size', 'Pending batch size')
        self.cb_state = Gauge('ioa_circuit_breaker_state', 'Circuit breaker state', ['service'])
        self.memory_usage = Gauge('ioa_memory_usage_bytes', 'Memory usage in bytes')
        self.cpu_usage = Gauge('ioa_cpu_usage_percent', 'CPU usage percentage')
        self.active_connections = Gauge('ioa_active_connections', 'Active connections')
        self.queue_depth = Gauge('ioa_queue_depth', 'Queue depth')
        
        # Histograms
        self.audit_latency = Histogram('ioa_audit_latency_seconds', 'Audit operation latency', 
                                     buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0])
        self.policy_latency = Histogram('ioa_policy_latency_seconds', 'Policy evaluation latency',
                                       buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0])
        self.signature_latency = Histogram('ioa_signature_latency_seconds', 'Signature operation latency',
                                          buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0])
        
        # Info
        self.build_info = Info('ioa_build_info', 'IOA build information')
        self.build_info.info({
            'version': '2.5.0',
            'build_date': datetime.now(timezone.utc).isoformat(),
            'environment': os.getenv('IOA_ENVIRONMENT', 'staging')
        })
        
    def collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            if self.process:
                # Memory usage
                memory_info = self.process.memory_info()
                self.memory_usage.set(memory_info.rss)
                
                # CPU usage
                cpu_percent = self.process.cpu_percent()
                self.cpu_usage.set(cpu_percent)
                
                # Active connections
                connections = len(self.process.connections())
                self.active_connections.set(connections)
                
        except Exception as e:
            self.logger.warning(f"Failed to collect system metrics: {e}")
            
    def simulate_metrics(self):
        """Simulate realistic metrics for testing"""
        import random
        
        # Simulate audit events
        events_per_second = random.randint(50, 200)
        self.audit_events.inc(events_per_second)
        
        # Simulate policy evaluations
        policy_evals = int(events_per_second * 0.8)
        self.policy_evaluations.inc(policy_evals)
        
        # Simulate signature operations
        sign_ops = int(events_per_second * 0.6)
        self.signature_operations.labels(operation='sign').inc(sign_ops)
        self.signature_operations.labels(operation='verify').inc(sign_ops * 2)
        
        # Simulate latency
        audit_latency = random.uniform(0.001, 0.1)
        self.audit_latency.observe(audit_latency)
        
        policy_latency = random.uniform(0.001, 0.05)
        self.policy_latency.observe(policy_latency)
        
        signature_latency = random.uniform(0.001, 0.2)
        self.signature_latency.observe(signature_latency)
        
        # Simulate occasional failures
        if random.random() < 0.01:  # 1% chance
            self.auth_failures.inc()
            
        if random.random() < 0.005:  # 0.5% chance
            self.encryption_errors.inc()
            
        if random.random() < 0.002:  # 0.2% chance
            self.kms_failures.inc()
            
        if random.random() < 0.003:  # 0.3% chance
            self.s3_failures.inc()
            
        # Simulate backpressure
        if events_per_second > 150:
            self.backpressure_events.inc()
            
        # Simulate pending batch
        batch_size = random.randint(10, 100)
        self.pending_batch.set(batch_size)
        
        # Simulate queue depth
        queue_depth = random.randint(0, 50)
        self.queue_depth.set(queue_depth)
        
        # Simulate circuit breaker states
        s3_cb_state = random.choice([0, 0, 0, 1])  # Mostly closed
        kms_cb_state = random.choice([0, 0, 0, 1])  # Mostly closed
        self.cb_state.labels(service='s3').set(s3_cb_state)
        self.cb_state.labels(service='kms').set(kms_cb_state)
        
        if s3_cb_state == 1:
            self.cb_opens.labels(service='s3').inc()
        if kms_cb_state == 1:
            self.cb_opens.labels(service='kms').inc()
            
    def start_metrics_collection(self):
        """Start metrics collection loop"""
        self.running = True
        self.logger.info("Starting IOA metrics collection...")
        
        def collect_loop():
            while self.running:
                try:
                    self.collect_system_metrics()
                    self.simulate_metrics()
                    time.sleep(1)  # Collect every second
                except Exception as e:
                    self.logger.error(f"Metrics collection error: {e}")
                    time.sleep(5)
                    
        # Start collection in background thread
        collection_thread = threading.Thread(target=collect_loop, daemon=True)
        collection_thread.start()
        
    def stop_metrics_collection(self):
        """Stop metrics collection"""
        self.running = False
        self.logger.info("Stopped IOA metrics collection")
        
    def start_server(self):
        """Start Prometheus metrics server"""
        start_http_server(self.port)
        self.logger.info(f"IOA metrics collector started on port {self.port}")
        
        # Start metrics collection
        self.start_metrics_collection()
        
        # Keep server running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Metrics collector stopped")
            self.stop_metrics_collection()

def main():
    """Main metrics collector function"""
    collector = IOAMetricsCollector()
    collector.start_server()

if __name__ == "__main__":
    main()
