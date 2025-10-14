"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
IOA Metrics Exporter
Exports IOA metrics to Prometheus format
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any
from prometheus_client import start_http_server, Counter, Gauge, Histogram

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class IOAMetricsExporter:
    def __init__(self, port: int = 8080):
        self.port = port
        self.logger = self._setup_logging()
        
        # Prometheus metrics
        self.auth_failures = Counter('ioa_auth_failures_total', 'Total authentication failures')
        self.cb_opens = Counter('ioa_circuit_breaker_opens_total', 'Total circuit breaker opens')
        self.backpressure_events = Counter('ioa_backpressure_events_total', 'Total backpressure events')
        self.encryption_errors = Counter('ioa_encryption_errors_total', 'Total encryption errors')
        self.kms_failures = Counter('ioa_kms_failures_total', 'Total KMS failures')
        self.s3_failures = Counter('ioa_s3_failures_total', 'Total S3 failures')
        self.audit_events = Counter('ioa_audit_events_total', 'Total audit events')
        self.pending_batch = Gauge('ioa_pending_batch_size', 'Pending batch size')
        self.cb_state = Gauge('ioa_circuit_breaker_state', 'Circuit breaker state', ['service'])
        
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger("ioa_metrics")
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
        
    def start_server(self):
        """Start Prometheus metrics server"""
        start_http_server(self.port)
        self.logger.info(f"IOA metrics exporter started on port {self.port}")
        
        # Keep server running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Metrics exporter stopped")

if __name__ == "__main__":
    exporter = IOAMetricsExporter()
    exporter.start_server()
