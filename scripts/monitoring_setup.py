#!/usr/bin/env python3
"""
IOA Monitoring Setup Script
Configures monitoring and alerting for staging rollout
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

class MonitoringSetup:
    def __init__(self):
        self.logger = self._setup_logging()
        self.metrics_config = {
            "auth_failures": {"threshold": 5, "window": "5m"},
            "cb_opens": {"threshold": 3, "window": "10m"},
            "backpressure_events": {"threshold": 10, "window": "5m"},
            "encryption_errors": {"threshold": 1, "window": "1m"},
            "kms_failures": {"threshold": 3, "window": "5m"},
            "s3_failures": {"threshold": 5, "window": "5m"},
            "audit_qps": {"threshold": 1000, "window": "1m"},
            "pending_batch": {"threshold": 500, "window": "1m"}
        }
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for monitoring"""
        logger = logging.getLogger("monitoring_setup")
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
        
    def create_prometheus_config(self) -> str:
        """Create Prometheus configuration for IOA metrics"""
        config = """
# IOA Prometheus Configuration
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "ioa_rules.yml"

scrape_configs:
  - job_name: 'ioa-audit-chain'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
    scrape_interval: 5s
    
  - job_name: 'ioa-policy-engine'
    static_configs:
      - targets: ['localhost:8081']
    metrics_path: '/metrics'
    scrape_interval: 5s
    
  - job_name: 'ioa-storage'
    static_configs:
      - targets: ['localhost:8082']
    metrics_path: '/metrics'
    scrape_interval: 5s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
"""
        return config
        
    def create_alert_rules(self) -> str:
        """Create Prometheus alert rules for IOA"""
        rules = f"""
groups:
- name: ioa.rules
  rules:
  # Authentication Alerts
  - alert: IOAAuthFailuresHigh
    expr: rate(ioa_auth_failures_total[5m]) > {self.metrics_config['auth_failures']['threshold']}
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "IOA Authentication failures are high"
      description: "Authentication failure rate is {{ $value }} failures/sec"
      
  # Circuit Breaker Alerts
  - alert: IOACircuitBreakerOpen
    expr: ioa_circuit_breaker_state{{service="s3"}} == 1
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "IOA S3 Circuit Breaker is OPEN"
      description: "S3 circuit breaker has been open for {{ $value }} seconds"
      
  - alert: IOACircuitBreakerOpen
    expr: ioa_circuit_breaker_state{{service="kms"}} == 1
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "IOA KMS Circuit Breaker is OPEN"
      description: "KMS circuit breaker has been open for {{ $value }} seconds"
      
  # Backpressure Alerts
  - alert: IOABackpressureHigh
    expr: rate(ioa_backpressure_events_total[5m]) > {self.metrics_config['backpressure_events']['threshold']}
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "IOA Backpressure events are high"
      description: "Backpressure event rate is {{ $value }} events/sec"
      
  # Encryption Alerts
  - alert: IOAEncryptionErrors
    expr: rate(ioa_encryption_errors_total[1m]) > {self.metrics_config['encryption_errors']['threshold']}
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "IOA Encryption errors detected"
      description: "Encryption error rate is {{ $value }} errors/sec"
      
  # KMS Alerts
  - alert: IOAKMSFailuresHigh
    expr: rate(ioa_kms_failures_total[5m]) > {self.metrics_config['kms_failures']['threshold']}
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "IOA KMS failures are high"
      description: "KMS failure rate is {{ $value }} failures/sec"
      
  # S3 Alerts
  - alert: IOAS3FailuresHigh
    expr: rate(ioa_s3_failures_total[5m]) > {self.metrics_config['s3_failures']['threshold']}
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "IOA S3 failures are high"
      description: "S3 failure rate is {{ $value }} failures/sec"
      
  # Performance Alerts
  - alert: IOAAuditQPSHigh
    expr: rate(ioa_audit_events_total[1m]) > {self.metrics_config['audit_qps']['threshold']}
    for: 1m
    labels:
      severity: warning
    annotations:
      summary: "IOA Audit QPS is high"
      description: "Audit QPS is {{ $value }} events/sec"
      
  - alert: IOAPendingBatchHigh
    expr: ioa_pending_batch_size > {self.metrics_config['pending_batch']['threshold']}
    for: 1m
    labels:
      severity: warning
    annotations:
      summary: "IOA Pending batch size is high"
      description: "Pending batch size is {{ $value }} events"
"""
        return rules
        
    def create_grafana_dashboard(self) -> Dict[str, Any]:
        """Create Grafana dashboard configuration for IOA"""
        dashboard = {
            "dashboard": {
                "id": None,
                "title": "IOA Staging Rollout Dashboard",
                "tags": ["ioa", "staging", "rollout"],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Audit QPS",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(ioa_audit_events_total[1m])",
                                "legendFormat": "Audit QPS"
                            }
                        ],
                        "yAxes": [
                            {"label": "Events/sec", "min": 0}
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                    },
                    {
                        "id": 2,
                        "title": "Circuit Breaker States",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "ioa_circuit_breaker_state",
                                "legendFormat": "{{service}} CB"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                    },
                    {
                        "id": 3,
                        "title": "Authentication Failures",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(ioa_auth_failures_total[5m])",
                                "legendFormat": "Auth Failures/sec"
                            }
                        ],
                        "yAxes": [
                            {"label": "Failures/sec", "min": 0}
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
                    },
                    {
                        "id": 4,
                        "title": "Backpressure Events",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(ioa_backpressure_events_total[5m])",
                                "legendFormat": "Backpressure Events/sec"
                            }
                        ],
                        "yAxes": [
                            {"label": "Events/sec", "min": 0}
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
                    },
                    {
                        "id": 5,
                        "title": "Pending Batch Size",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "ioa_pending_batch_size",
                                "legendFormat": "Pending Batch Size"
                            }
                        ],
                        "yAxes": [
                            {"label": "Events", "min": 0}
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}
                    },
                    {
                        "id": 6,
                        "title": "Encryption Errors",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(ioa_encryption_errors_total[1m])",
                                "legendFormat": "Encryption Errors/sec"
                            }
                        ],
                        "yAxes": [
                            {"label": "Errors/sec", "min": 0}
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
                    }
                ],
                "time": {
                    "from": "now-1h",
                    "to": "now"
                },
                "refresh": "5s"
            }
        }
        return dashboard
        
    def create_metrics_exporter(self) -> str:
        """Create Python metrics exporter for IOA components"""
        exporter_code = '''#!/usr/bin/env python3
"""
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
'''
        return exporter_code
        
    def create_monitoring_script(self) -> str:
        """Create monitoring script that watches metrics"""
        script = '''#!/usr/bin/env python3
"""
IOA Monitoring Script
Watches metrics and triggers alerts
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

class IOAMonitor:
    def __init__(self):
        self.logger = self._setup_logging()
        self.alerts = []
        
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger("ioa_monitor")
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
        
    def check_auth_failures(self) -> bool:
        """Check for high authentication failures"""
        # This would typically query Prometheus or metrics endpoint
        # For now, we'll simulate the check
        return False
        
    def check_circuit_breakers(self) -> bool:
        """Check circuit breaker states"""
        # This would typically query Prometheus or metrics endpoint
        # For now, we'll simulate the check
        return False
        
    def check_backpressure(self) -> bool:
        """Check for backpressure events"""
        # This would typically query Prometheus or metrics endpoint
        # For now, we'll simulate the check
        return False
        
    def run_monitoring_loop(self):
        """Run continuous monitoring"""
        self.logger.info("Starting IOA monitoring loop...")
        
        while True:
            try:
                # Check various metrics
                if self.check_auth_failures():
                    self.logger.warning("High authentication failures detected")
                    
                if self.check_circuit_breakers():
                    self.logger.warning("Circuit breaker issues detected")
                    
                if self.check_backpressure():
                    self.logger.warning("Backpressure events detected")
                    
                time.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped")
                break
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    monitor = IOAMonitor()
    monitor.run_monitoring_loop()
'''
        return script
        
    def setup_monitoring(self) -> Dict[str, str]:
        """Setup complete monitoring infrastructure"""
        self.logger.info("Setting up IOA monitoring infrastructure...")
        
        # Create monitoring directory
        monitoring_dir = Path("monitoring")
        monitoring_dir.mkdir(exist_ok=True)
        
        # Create Prometheus config
        prometheus_config = self.create_prometheus_config()
        prometheus_path = monitoring_dir / "prometheus.yml"
        with open(prometheus_path, 'w') as f:
            f.write(prometheus_config)
            
        # Create alert rules
        alert_rules = self.create_alert_rules()
        rules_path = monitoring_dir / "ioa_rules.yml"
        with open(rules_path, 'w') as f:
            f.write(alert_rules)
            
        # Create Grafana dashboard
        dashboard_config = self.create_grafana_dashboard()
        dashboard_path = monitoring_dir / "grafana_dashboard.json"
        with open(dashboard_path, 'w') as f:
            json.dump(dashboard_config, f, indent=2)
            
        # Create metrics exporter
        exporter_code = self.create_metrics_exporter()
        exporter_path = monitoring_dir / "metrics_exporter.py"
        with open(exporter_path, 'w') as f:
            f.write(exporter_code)
        os.chmod(exporter_path, 0o755)
        
        # Create monitoring script
        monitor_script = self.create_monitoring_script()
        monitor_path = monitoring_dir / "monitor.py"
        with open(monitor_path, 'w') as f:
            f.write(monitor_script)
        os.chmod(monitor_path, 0o755)
        
        # Create docker-compose for monitoring stack
        docker_compose = self.create_docker_compose()
        compose_path = monitoring_dir / "docker-compose.yml"
        with open(compose_path, 'w') as f:
            f.write(docker_compose)
            
        self.logger.info(f"Monitoring infrastructure created in {monitoring_dir}")
        
        return {
            "prometheus_config": str(prometheus_path),
            "alert_rules": str(rules_path),
            "grafana_dashboard": str(dashboard_path),
            "metrics_exporter": str(exporter_path),
            "monitor_script": str(monitor_path),
            "docker_compose": str(compose_path)
        }
        
    def create_docker_compose(self) -> str:
        """Create docker-compose.yml for monitoring stack"""
        compose = '''version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./ioa_rules.yml:/etc/prometheus/ioa_rules.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
      
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana
      - ./grafana_dashboard.json:/var/lib/grafana/dashboards/ioa.json
      
  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
      
  ioa-metrics:
    build: .
    ports:
      - "8080:8080"
    environment:
      - IOA_METRICS_PORT=8080
    volumes:
      - ../src:/app/src
      
volumes:
  grafana-storage:
'''
        return compose

def main():
    """Main monitoring setup function"""
    setup = MonitoringSetup()
    
    # Setup monitoring infrastructure
    files = setup.setup_monitoring()
    
    print("IOA Monitoring Setup Complete!")
    print("\nCreated files:")
    for name, path in files.items():
        print(f"  {name}: {path}")
        
    print("\nTo start monitoring:")
    print("  cd monitoring && docker-compose up -d")
    print("  python3 metrics_exporter.py &")
    print("  python3 monitor.py &")
    
    print("\nAccess points:")
    print("  Prometheus: http://localhost:9090")
    print("  Grafana: http://localhost:3000 (admin/admin)")
    print("  IOA Metrics: http://localhost:8080/metrics")

if __name__ == "__main__":
    main()
