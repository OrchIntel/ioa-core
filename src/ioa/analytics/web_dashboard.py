""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

# IOA SDK ONLY
# No direct LLM imports • see MDC.md

"""
"""

"""
Web Dashboard Interface Module

Provides web-based interface for the Enterprise Analytics Dashboard.
Includes real-time monitoring, data visualization, and interactive reports.

Features:
- Real-time dashboard with WebSocket updates
- Interactive charts and visualizations
- Compliance monitoring interface
- Tenant management interface
- Custom report generation
"""

__version__ = "2.5.0"

import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import asdict

from .enterprise_dashboard import EnterpriseDashboard, DashboardConfig


class WebDashboardError(Exception):
    """Base exception for web dashboard operations."""
    pass


class WebDashboard:
    """
    Web interface for Enterprise Analytics Dashboard.
    
    Provides HTML/CSS/JavaScript interface for real-time monitoring,
    data visualization, and interactive reporting.
    """
    
    def __init__(
        self,
        dashboard: EnterpriseDashboard,
        static_dir: str = "static",
        templates_dir: str = "templates"
    ) -> None:
        """
        Initialize web dashboard.
        
        Args:
            dashboard: Enterprise dashboard instance
            static_dir: Directory for static assets
            templates_dir: Directory for HTML templates
        """
        self.dashboard = dashboard
        self.static_dir = Path(static_dir)
        self.templates_dir = Path(templates_dir)
        self.logger = logging.getLogger(__name__)
        
        # Create directories
        self.static_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        
        # Initialize dashboard
        self.dashboard.start_monitoring()
    
    def generate_dashboard_html(self, tenant_id: Optional[str] = None) -> str:
        """Generate complete dashboard HTML."""
        dashboard_data = self.dashboard.get_dashboard_data(tenant_id)
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IOA Enterprise Analytics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/date-fns@2.29.3/index.min.js"></script>
    <style>
        {self._get_dashboard_css()}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <header class="dashboard-header">
            <h1>IOA Enterprise Analytics Dashboard</h1>
            <div class="header-controls">
                <button id="refresh-btn" class="btn btn-primary">Refresh</button>
                <button id="export-btn" class="btn btn-secondary">Export Report</button>
                <div class="status-indicator" id="status-indicator">
                    <span class="status-dot"></span>
                    <span>Live</span>
                </div>
            </div>
        </header>
        
        <div class="dashboard-content">
            <div class="metrics-grid">
                {self._generate_system_health_cards(dashboard_data)}
                {self._generate_usage_analytics_cards(dashboard_data)}
                {self._generate_compliance_cards(dashboard_data)}
            </div>
            
            <div class="charts-section">
                <div class="chart-container">
                    <h3>System Performance</h3>
                    <canvas id="performance-chart"></canvas>
                </div>
                <div class="chart-container">
                    <h3>Usage Analytics</h3>
                    <canvas id="usage-chart"></canvas>
                </div>
                <div class="chart-container">
                    <h3>Compliance Metrics</h3>
                    <canvas id="compliance-chart"></canvas>
                </div>
            </div>
            
            <div class="reports-section">
                <h3>Compliance Reports</h3>
                <div class="reports-grid">
                    {self._generate_reports_section(dashboard_data)}
                </div>
            </div>
        </div>
    </div>
    
    <script>
        {self._get_dashboard_js(dashboard_data)}
    </script>
</body>
</html>
        """
        
        return html
    
    def _get_dashboard_css(self) -> str:
        """Get dashboard CSS styles."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f8fafc;
            color: #1a202c;
        }
        
        .dashboard-container {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .dashboard-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .dashboard-header h1 {
            font-size: 1.5rem;
            font-weight: 600;
        }
        
        .header-controls {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .btn {
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 0.375rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .btn-primary {
            background-color: #4299e1;
            color: white;
        }
        
        .btn-primary:hover {
            background-color: #3182ce;
        }
        
        .btn-secondary {
            background-color: #e2e8f0;
            color: #4a5568;
        }
        
        .btn-secondary:hover {
            background-color: #cbd5e0;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            background-color: #48bb78;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .dashboard-content {
            flex: 1;
            padding: 2rem;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .metric-card {
            background: white;
            border-radius: 0.5rem;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border-left: 4px solid #4299e1;
        }
        
        .metric-card h3 {
            font-size: 0.875rem;
            font-weight: 600;
            color: #718096;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #1a202c;
            margin-bottom: 0.25rem;
        }
        
        .metric-change {
            font-size: 0.875rem;
            color: #48bb78;
        }
        
        .metric-change.negative {
            color: #f56565;
        }
        
        .charts-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .chart-container {
            background: white;
            border-radius: 0.5rem;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .chart-container h3 {
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #2d3748;
        }
        
        .chart-container canvas {
            max-height: 300px;
        }
        
        .reports-section {
            background: white;
            border-radius: 0.5rem;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .reports-section h3 {
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #2d3748;
        }
        
        .reports-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
        }
        
        .report-card {
            border: 1px solid #e2e8f0;
            border-radius: 0.375rem;
            padding: 1rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .report-card:hover {
            border-color: #4299e1;
            box-shadow: 0 2px 8px rgba(66, 153, 225, 0.15);
        }
        
        .report-title {
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #2d3748;
        }
        
        .report-description {
            font-size: 0.875rem;
            color: #718096;
            margin-bottom: 0.75rem;
        }
        
        .report-status {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        .status-success {
            background-color: #c6f6d5;
            color: #22543d;
        }
        
        .status-warning {
            background-color: #faf089;
            color: #744210;
        }
        
        .status-error {
            background-color: #fed7d7;
            color: #742a2a;
        }
        
        @media (max-width: 768px) {
            .dashboard-header {
                flex-direction: column;
                gap: 1rem;
            }
            
            .dashboard-content {
                padding: 1rem;
            }
            
            .metrics-grid {
                grid-template-columns: 1fr;
            }
            
            .charts-section {
                grid-template-columns: 1fr;
            }
        }
        """
    
    def _generate_system_health_cards(self, data: Dict[str, Any]) -> str:
        """Generate system health metric cards."""
        health = data.get('system_health', {})
        
        return f"""
        <div class="metric-card">
            <h3>CPU Usage</h3>
            <div class="metric-value">{health.get('cpu_usage', 0):.1f}%</div>
            <div class="metric-change">System Load</div>
        </div>
        <div class="metric-card">
            <h3>Memory Usage</h3>
            <div class="metric-value">{health.get('memory_usage', 0):.1f}%</div>
            <div class="metric-change">RAM Utilization</div>
        </div>
        <div class="metric-card">
            <h3>Disk Usage</h3>
            <div class="metric-value">{health.get('disk_usage', 0):.1f}%</div>
            <div class="metric-change">Storage Utilization</div>
        </div>
        <div class="metric-card">
            <h3>Uptime</h3>
            <div class="metric-value">{self._format_uptime(health.get('uptime', 0))}</div>
            <div class="metric-change">System Uptime</div>
        </div>
        """
    
    def _generate_usage_analytics_cards(self, data: Dict[str, Any]) -> str:
        """Generate usage analytics metric cards."""
        usage = data.get('usage_analytics', {})
        
        return f"""
        <div class="metric-card">
            <h3>Active Users</h3>
            <div class="metric-value">{usage.get('active_users', 0)}</div>
            <div class="metric-change">Currently Online</div>
        </div>
        <div class="metric-card">
            <h3>Total Requests</h3>
            <div class="metric-value">{usage.get('total_requests', 0)}</div>
            <div class="metric-change">All Time</div>
        </div>
        <div class="metric-card">
            <h3>Avg Response Time</h3>
            <div class="metric-value">{usage.get('avg_response_time', 0):.2f}ms</div>
            <div class="metric-change">Performance</div>
        </div>
        <div class="metric-card">
            <h3>Error Rate</h3>
            <div class="metric-value">{usage.get('error_rate', 0):.2f}%</div>
            <div class="metric-change">Reliability</div>
        </div>
        """
    
    def _generate_compliance_cards(self, data: Dict[str, Any]) -> str:
        """Generate compliance metric cards."""
        compliance = data.get('compliance_metrics', {})
        
        gdpr_score = compliance.get('gdpr_compliance', 0)
        hipaa_score = compliance.get('hipaa_compliance', 0)
        sox_score = compliance.get('sox_compliance', 0)
        audit_score = compliance.get('audit_trail_completeness', 0)
        
        return f"""
        <div class="metric-card">
            <h3>GDPR Compliance</h3>
            <div class="metric-value">{gdpr_score:.1f}%</div>
            <div class="metric-change {'negative' if gdpr_score < 90 else ''}">Data Protection</div>
        </div>
        <div class="metric-card">
            <h3>HIPAA Compliance</h3>
            <div class="metric-value">{hipaa_score:.1f}%</div>
            <div class="metric-change {'negative' if hipaa_score < 90 else ''}">Health Data</div>
        </div>
        <div class="metric-card">
            <h3>SOX Compliance</h3>
            <div class="metric-value">{sox_score:.1f}%</div>
            <div class="metric-change {'negative' if sox_score < 90 else ''}">Financial Controls</div>
        </div>
        <div class="metric-card">
            <h3>Audit Completeness</h3>
            <div class="metric-value">{audit_score:.1f}%</div>
            <div class="metric-change {'negative' if audit_score < 90 else ''}">Trail Integrity</div>
        </div>
        """
    
    def _generate_reports_section(self, data: Dict[str, Any]) -> str:
        """Generate reports section."""
        return """
        <div class="report-card" onclick="generateReport('comprehensive')">
            <div class="report-title">Comprehensive Compliance Report</div>
            <div class="report-description">Complete compliance overview with recommendations</div>
            <span class="report-status status-success">Available</span>
        </div>
        <div class="report-card" onclick="generateReport('gdpr')">
            <div class="report-title">GDPR Compliance Report</div>
            <div class="report-description">Data protection and privacy compliance</div>
            <span class="report-status status-success">Available</span>
        </div>
        <div class="report-card" onclick="generateReport('hipaa')">
            <div class="report-title">HIPAA Compliance Report</div>
            <div class="report-description">Healthcare data protection compliance</div>
            <span class="report-status status-success">Available</span>
        </div>
        <div class="report-card" onclick="generateReport('sox')">
            <div class="report-title">SOX Compliance Report</div>
            <div class="report-description">Financial controls and audit compliance</div>
            <span class="report-status status-success">Available</span>
        </div>
        """
    
    def _get_dashboard_js(self, data: Dict[str, Any]) -> str:
        """Get dashboard JavaScript."""
        return f"""
        // Dashboard data
        const dashboardData = {json.dumps(data, indent=2)};
        
        // Chart configurations
        const performanceChart = new Chart(document.getElementById('performance-chart'), {{
            type: 'line',
            data: {{
                labels: {self._generate_time_labels()},
                datasets: [
                    {{
                        label: 'CPU Usage %',
                        data: {self._generate_cpu_data(data)},
                        borderColor: '#4299e1',
                        backgroundColor: 'rgba(66, 153, 225, 0.1)',
                        tension: 0.4
                    }},
                    {{
                        label: 'Memory Usage %',
                        data: {self._generate_memory_data(data)},
                        borderColor: '#48bb78',
                        backgroundColor: 'rgba(72, 187, 120, 0.1)',
                        tension: 0.4
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100
                    }}
                }}
            }}
        }});
        
        const usageChart = new Chart(document.getElementById('usage-chart'), {{
            type: 'bar',
            data: {{
                labels: {self._generate_feature_labels(data)},
                datasets: [{{
                    label: 'Feature Usage',
                    data: {self._generate_feature_data(data)},
                    backgroundColor: [
                        '#4299e1',
                        '#48bb78',
                        '#ed8936',
                        '#9f7aea',
                        '#f56565'
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
        
        const complianceChart = new Chart(document.getElementById('compliance-chart'), {{
            type: 'doughnut',
            data: {{
                labels: ['GDPR', 'HIPAA', 'SOX', 'Audit'],
                datasets: [{{
                    data: [
                        dashboardData.compliance_metrics.gdpr_compliance,
                        dashboardData.compliance_metrics.hipaa_compliance,
                        dashboardData.compliance_metrics.sox_compliance,
                        dashboardData.compliance_metrics.audit_trail_completeness
                    ],
                    backgroundColor: [
                        '#4299e1',
                        '#48bb78',
                        '#ed8936',
                        '#9f7aea'
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false
            }}
        }});
        
        // Event handlers
        document.getElementById('refresh-btn').addEventListener('click', function() {{
            location.reload();
        }});
        
        document.getElementById('export-btn').addEventListener('click', function() {{
            exportReport('comprehensive');
        }});
        
        // Auto-refresh every 30 seconds
        setInterval(function() {{
            location.reload();
        }}, 30000);
        
        // Report generation
        function generateReport(type) {{
            fetch('/api/reports/generate', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify({{ report_type: type }})
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.status === 'generated') {{
                    alert('Report generated successfully!');
                    // In a real implementation, would download the report
                }} else {{
                    alert('Error generating report');
                }}
            }})
            .catch(error => {{
                console.error('Error:', error);
                alert('Error generating report');
            }});
        }}
        
        function exportReport(type) {{
            // In a real implementation, would export data as CSV/PDF
            alert('Export functionality would be implemented here');
        }}
        """
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format."""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def _generate_time_labels(self) -> str:
        """Generate time labels for charts."""
        labels = []
        for i in range(24):
            time = datetime.now() - timedelta(hours=23-i)
            labels.append(time.strftime("%H:%M"))
        return json.dumps(labels)
    
    def _generate_cpu_data(self, data: Dict[str, Any]) -> str:
        """Generate CPU usage data for charts."""
        # Mock data - in real implementation would use historical data
        return json.dumps([25, 30, 28, 35, 32, 40, 38, 45, 42, 38, 35, 30, 28, 25, 30, 35, 40, 38, 35, 32, 28, 25, 30, 35])
    
    def _generate_memory_data(self, data: Dict[str, Any]) -> str:
        """Generate memory usage data for charts."""
        # Mock data - in real implementation would use historical data
        return json.dumps([60, 65, 62, 68, 70, 75, 72, 78, 80, 75, 70, 65, 62, 60, 65, 70, 75, 72, 70, 68, 65, 60, 65, 70])
    
    def _generate_feature_labels(self, data: Dict[str, Any]) -> str:
        """Generate feature labels for usage chart."""
        usage = data.get('usage_analytics', {})
        features = usage.get('feature_usage', {})
        return json.dumps(list(features.keys()))
    
    def _generate_feature_data(self, data: Dict[str, Any]) -> str:
        """Generate feature usage data for charts."""
        usage = data.get('usage_analytics', {})
        features = usage.get('feature_usage', {})
        return json.dumps(list(features.values()))
    
    def save_dashboard_html(self, file_path: str, tenant_id: Optional[str] = None) -> None:
        """Save dashboard HTML to file."""
        html_content = self.generate_dashboard_html(tenant_id)
        with open(file_path, 'w') as f:
            f.write(html_content)
        self.logger.info(f"Dashboard HTML saved to {file_path}")
    
    def __del__(self):
        """Cleanup on destruction."""
        if hasattr(self, 'dashboard'):
            self.dashboard.stop_monitoring()
