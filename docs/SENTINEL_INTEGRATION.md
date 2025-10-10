**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# IOA Core Sentinel Integration Guide


## Overview

Sentinel integration provides real-time monitoring, alerting, and automated response capabilities for IOA Core systems. This guide covers the setup, configuration, and usage of Sentinel for governance, compliance, and operational monitoring.

## Sentinel Architecture

### Core Components

1. **Sentinel Core**: Central monitoring and alerting engine
2. **Data Collectors**: Gather metrics from IOA Core components
3. **Alert Rules**: Define conditions for triggering alerts
4. **Notification Channels**: Deliver alerts via various methods
5. **Response Actions**: Automated responses to detected issues

### Integration Points

```python
# Sentinel integration architecture
sentinel_architecture = {
    "core": "src/sentinel_validator.py",
    "collectors": [
        "src/kpi_monitor.py",
        "src/audit_logger.py",
        "governance/GOVERNANCE.md"
    ],
    "rules": "config/sentinel_rules.yaml",
    "notifications": "config/notification_channels.yaml",
    "actions": "config/response_actions.yaml"
}
```

## Setup and Configuration

### 1. Install Sentinel Dependencies

```bash
# Install required packages
pip install sentinel-core
pip install prometheus-client
pip install alertmanager-client

# Install IOA Core with Sentinel support
pip install -e .[sentinel]
```

### 2. Configure Sentinel Rules

Create `config/sentinel_rules.yaml`:

```yaml
# Sentinel monitoring rules
monitoring:
  # Performance thresholds
  performance:
    cpu_usage:
      warning: 80
      critical: 95
    memory_usage:
      warning: 85
      critical: 95
    response_time:
      warning: 1000  # ms
      critical: 5000  # ms
  
  # Governance thresholds
  governance:
    audit_failures:
      warning: 5
      critical: 20
    compliance_violations:
      warning: 1
      critical: 5
    trust_signature_failures:
      warning: 2
      critical: 10
  
  # Security thresholds
  security:
    failed_logins:
      warning: 3
      critical: 10
    suspicious_activities:
      warning: 1
      critical: 3
    api_rate_limit_exceeded:
      warning: 10
      critical: 50

# Alert rules
alerts:
  - name: "High CPU Usage"
    condition: "cpu_usage > 95"
    severity: "critical"
    notification: "slack"
    action: "scale_up"
  
  - name: "Audit Chain Failure"
    condition: "audit_failures > 20"
    severity: "critical"
    notification: "email"
    action: "investigate"
  
  - name: "Security Violation"
    condition: "suspicious_activities > 3"
    severity: "critical"
    notification: "pagerduty"
    action: "lockdown"
```

### 3. Configure Notification Channels

Create `config/notification_channels.yaml`:

```yaml
# Notification channel configuration
channels:
  slack:
    webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    channel: "#ioa-alerts"
    username: "IOA Sentinel"
    icon_emoji: ":warning:"
  
  email:
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: "alerts@yourcompany.com"
    password: "${EMAIL_PASSWORD}"
    recipients: ["admin@yourcompany.com", "ops@yourcompany.com"]
  
  pagerduty:
    service_key: "YOUR_PAGERDUTY_SERVICE_KEY"
    escalation_policy: "ioa-critical"
  
  webhook:
    url: "https://your-webhook-endpoint.com/alerts"
    headers:
      Authorization: "Bearer ${WEBHOOK_TOKEN}"
      Content-Type: "application/json"
```

## Implementation

### 1. Basic Sentinel Integration

```python
# Basic Sentinel integration
from src.sentinel_validator import SentinelValidator
from src.kpi_monitor import KPIMonitor

# Initialize Sentinel
sentinel = SentinelValidator(
    rules_file="config/sentinel_rules.yaml",
    notification_channels="config/notification_channels.yaml"
)

# Initialize KPI monitor
kpi_monitor = KPIMonitor()

# Start monitoring
sentinel.start_monitoring()
```

### 2. Custom Metrics Collection

```python
# Custom metrics collection
class CustomMetricsCollector:
    def __init__(self):
        self.metrics = {}
    
    def collect_ioa_metrics(self):
        """Collect IOA Core specific metrics."""
        metrics = {
            "ioa_core_version": "2.5.0",
            "active_agents": self._count_active_agents(),
            "workflow_executions": self._count_workflow_executions(),
            "audit_chain_health": self._check_audit_chain_health(),
            "governance_compliance": self._check_governance_compliance()
        }
        
        return metrics
    
    def _count_active_agents(self):
        """Count currently active agents."""
        # Implementation to count active agents
        return len(self._get_active_agents())
    
    def _count_workflow_executions(self):
        """Count workflow executions in the last hour."""
        # Implementation to count workflow executions
        return self._get_workflow_count(time_window="1h")
    
    def _check_audit_chain_health(self):
        """Check audit chain health status."""
        # Implementation to check audit chain
        return self._get_audit_chain_status()
    
    def _check_governance_compliance(self):
        """Check governance compliance status."""
        # Implementation to check compliance
        return self._get_compliance_status()
```

### 3. Alert Rule Implementation

```python
# Alert rule implementation
class AlertRuleEngine:
    def __init__(self, rules_config):
        self.rules = self._load_rules(rules_config)
        self.alert_history = []
    
    def evaluate_rules(self, current_metrics):
        """Evaluate all alert rules against current metrics."""
        triggered_alerts = []
        
        for rule in self.rules:
            if self._evaluate_rule(rule, current_metrics):
                alert = self._create_alert(rule, current_metrics)
                triggered_alerts.append(alert)
                
                # Record alert
                self.alert_history.append(alert)
        
        return triggered_alerts
    
    def _evaluate_rule(self, rule, metrics):
        """Evaluate a single alert rule."""
        condition = rule['condition']
        
        # Parse and evaluate condition
        # This is a simplified example - real implementation would be more robust
        if '>' in condition:
            metric_name, threshold = condition.split(' > ')
            metric_name = metric_name.strip()
            threshold = float(threshold.strip())
            
            return metrics.get(metric_name, 0) > threshold
        
        return False
    
    def _create_alert(self, rule, metrics):
        """Create an alert object."""
        return {
            'name': rule['name'],
            'severity': rule['severity'],
            'condition': rule['condition'],
            'timestamp': datetime.now(),
            'metrics': metrics,
            'notification_channel': rule['notification'],
            'action': rule['action']
        }
```

### 4. Notification System

```python
# Notification system implementation
class NotificationManager:
    def __init__(self, channels_config):
        self.channels = self._load_channels(channels_config)
    
    def send_notification(self, alert, channel_name):
        """Send notification via specified channel."""
        if channel_name not in self.channels:
            raise ValueError(f"Unknown notification channel: {channel_name}")
        
        channel = self.channels[channel_name]
        message = self._format_message(alert)
        
        if channel_name == 'slack':
            return self._send_slack_notification(channel, message)
        elif channel_name == 'email':
            return self._send_email_notification(channel, message)
        elif channel_name == 'pagerduty':
            return self._send_pagerduty_notification(channel, message)
        elif channel_name == 'webhook':
            return self._send_webhook_notification(channel, message)
    
    def _format_message(self, alert):
        """Format alert into notification message."""
        return {
            'title': f"IOA Core Alert: {alert['name']}",
            'severity': alert['severity'].upper(),
            'message': f"Condition '{alert['condition']}' triggered",
            'timestamp': alert['timestamp'].isoformat(),
            'metrics': alert['metrics'],
            'action_required': alert['action']
        }
    
    def _send_slack_notification(self, channel_config, message):
        """Send Slack notification."""
        import requests
        
        payload = {
            'text': f"*{message['title']}*",
            'attachments': [{
                'color': self._get_severity_color(message['severity']),
                'fields': [
                    {'title': 'Severity', 'value': message['severity'], 'short': True},
                    {'title': 'Action Required', 'value': message['action_required'], 'short': True},
                    {'title': 'Details', 'value': message['message'], 'short': False}
                ],
                'footer': f"IOA Core v2.5.0 | {message['timestamp']}"
            }]
        }
        
        response = requests.post(
            channel_config['webhook_url'],
            json=payload
        )
        
        return response.status_code == 200
```

## Advanced Features

### 1. Automated Response Actions

```python
# Automated response actions
class ResponseActionExecutor:
    def __init__(self, actions_config):
        self.actions = self._load_actions(actions_config)
    
    def execute_action(self, alert):
        """Execute the required action for an alert."""
        action_name = alert['action']
        
        if action_name not in self.actions:
            raise ValueError(f"Unknown action: {action_name}")
        
        action_config = self.actions[action_name]
        return self._execute_action(action_config, alert)
    
    def _execute_action(self, action_config, alert):
        """Execute a specific action."""
        action_type = action_config['type']
        
        if action_type == 'scale_up':
            return self._scale_up_resources(action_config, alert)
        elif action_type == 'investigate':
            return self._investigate_issue(action_config, alert)
        elif action_type == 'lockdown':
            return self._lockdown_system(action_config, alert)
        elif action_type == 'restart_service':
            return self._restart_service(action_config, alert)
    
    def _scale_up_resources(self, action_config, alert):
        """Scale up system resources."""
        # Implementation to scale up resources
        # This could involve AWS Auto Scaling, Kubernetes scaling, etc.
        pass
    
    def _investigate_issue(self, action_config, alert):
        """Investigate the reported issue."""
        # Implementation to investigate issues
        # This could involve running diagnostics, collecting logs, etc.
        pass
    
    def _lockdown_system(self, action_config, alert):
        """Lock down the system for security."""
        # Implementation to lockdown system
        # This could involve blocking access, stopping services, etc.
        pass
```

### 2. Dashboard and Visualization

```python
# Dashboard implementation
class SentinelDashboard:
    def __init__(self):
        self.metrics_history = []
        self.alerts_history = []
    
    def update_dashboard(self, current_metrics, current_alerts):
        """Update dashboard with current data."""
        self.metrics_history.append({
            'timestamp': datetime.now(),
            'metrics': current_metrics
        })
        
        self.alerts_history.extend(current_alerts)
        
        # Keep only last 24 hours of data
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.metrics_history = [
            m for m in self.metrics_history 
            if m['timestamp'] > cutoff_time
        ]
    
    def generate_dashboard_data(self):
        """Generate data for dashboard display."""
        return {
            'current_metrics': self._get_latest_metrics(),
            'metrics_trends': self._calculate_trends(),
            'alert_summary': self._generate_alert_summary(),
            'system_health': self._calculate_system_health()
        }
    
    def _get_latest_metrics(self):
        """Get the most recent metrics."""
        if not self.metrics_history:
            return {}
        return self.metrics_history[-1]['metrics']
    
    def _calculate_trends(self):
        """Calculate trends from metrics history."""
        # Implementation to calculate trends
        pass
    
    def _generate_alert_summary(self):
        """Generate summary of recent alerts."""
        recent_alerts = [
            a for a in self.alerts_history 
            if a['timestamp'] > datetime.now() - timedelta(hours=1)
        ]
        
        return {
            'total_alerts': len(recent_alerts),
            'critical_alerts': len([a for a in recent_alerts if a['severity'] == 'critical']),
            'warning_alerts': len([a for a in recent_alerts if a['severity'] == 'warning']),
            'alerts_by_type': self._group_alerts_by_type(recent_alerts)
        }
```

## Monitoring and Maintenance

### 1. Health Checks

```python
# Sentinel health checks
def check_sentinel_health():
    """Check Sentinel system health."""
    health_checks = {
        'rules_engine': check_rules_engine(),
        'notification_channels': check_notification_channels(),
        'metrics_collection': check_metrics_collection(),
        'response_actions': check_response_actions()
    }
    
    overall_health = all(health_checks.values())
    
    return {
        'overall_health': overall_health,
        'components': health_checks,
        'timestamp': datetime.now()
    }

def check_rules_engine():
    """Check rules engine functionality."""
    try:
        # Test rule evaluation
        test_rule = {'condition': 'test_metric > 0'}
        test_metrics = {'test_metric': 1}
        
        # This would call the actual rules engine
        # For now, just return True
        return True
    except Exception as e:
        logger.error(f"Rules engine health check failed: {e}")
        return False
```

### 2. Performance Monitoring

```python
# Performance monitoring
class SentinelPerformanceMonitor:
    def __init__(self):
        self.performance_metrics = {}
    
    def record_metric_collection_time(self, duration):
        """Record time taken to collect metrics."""
        if 'metric_collection_time' not in self.performance_metrics:
            self.performance_metrics['metric_collection_time'] = []
        
        self.performance_metrics['metric_collection_time'].append(duration)
        
        # Keep only last 100 measurements
        if len(self.performance_metrics['metric_collection_time']) > 100:
            self.performance_metrics['metric_collection_time'] = \
                self.performance_metrics['metric_collection_time'][-100:]
    
    def get_performance_summary(self):
        """Get performance summary."""
        summary = {}
        
        for metric_name, values in self.performance_metrics.items():
            if values:
                summary[metric_name] = {
                    'count': len(values),
                    'average': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'latest': values[-1]
                }
        
        return summary
```

## Best Practices

### 1. Rule Design

- Keep rules simple and focused
- Use appropriate thresholds based on system behavior
- Avoid alert fatigue with too many rules
- Test rules in development before production

### 2. Notification Management

- Use appropriate notification channels for different severity levels
- Implement escalation policies for critical alerts
- Provide actionable information in notifications
- Avoid notification spam

### 3. Performance Optimization

- Collect metrics efficiently without impacting system performance
- Use appropriate collection intervals
- Implement caching for frequently accessed metrics
- Monitor Sentinel's own performance

### 4. Security Considerations

- Secure notification channel credentials
- Implement access controls for dashboard access
- Audit all Sentinel actions
- Protect sensitive metrics data

## Troubleshooting

### Common Issues

1. **Metrics not being collected**
   - Check data collector configuration
   - Verify permissions and access
   - Check for errors in collector logs

2. **Alerts not being sent**
   - Verify notification channel configuration
   - Check network connectivity
   - Review notification channel logs

3. **High false positive rate**
   - Review and adjust alert thresholds
   - Add additional conditions to rules
   - Implement alert correlation

### Debug Mode

```python
# Enable debug mode
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('sentinel')

# Enable debug logging for specific components
logger.setLevel(logging.DEBUG)
```

## Conclusion

Sentinel integration provides powerful monitoring and alerting capabilities for IOA Core systems. By following this guide and implementing the provided examples, teams can build robust monitoring solutions that ensure system reliability, compliance, and operational excellence.

## Related Documentation

- [Governance Guide](GOVERNANCE.md) - Overall governance framework
- [Bias Mitigation](BIAS_MITIGATION.md) - Bias detection and mitigation
- [Governance Overview](governance/GOVERNANCE.md) - Audit and compliance monitoring
- [Performance Guide](PERFORMANCE.md) - Performance metrics collection
