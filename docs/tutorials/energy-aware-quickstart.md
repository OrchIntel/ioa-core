**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Energy-Aware Quickstart Tutorial


**PATCH:** Cursor-2025-09-05 DISPATCH-GOV-20250905-LAW-7-SUSTAINABILITY  
Energy-aware tutorial for Law 7 compliance.

## Overview

This tutorial demonstrates how to use IOA Core's energy-aware features to comply with Law 7 (Sustainability Stewardship). You'll learn how to:

- Check energy budgets before executing tasks
- Monitor energy usage during execution
- Handle budget violations with HITL overrides
- Generate energy reports and forecasts

## Prerequisites

- IOA Core v2.5.0+ installed
- Sustainability module available
- Basic understanding of IOA CLI

## Quick Start

### 1. Check System Health

First, verify that the sustainability module is available:

> **Note**: Some commands below are examples for future functionality.

```bash
# Example (not currently implemented): ioa health --detailed
```

You should see:
```
✅ Sustainability module available
```

### 2. View Sustainability Policies

Check current sustainability policies and budgets:

> **Note**: Some commands below are examples for future functionality.

```bash
# Example (not currently implemented): ioa policies show --sustainability
```

Output:
```
🌱 Sustainability Policies (Law 7)
==================================================
Task Budget: 0.010 kWh
Run Budget: 0.250 kWh
Project Budget: 5.000 kWh
Warning Threshold: 80%
Block Threshold: 100%
HITL Override: Enabled

Energy Estimation Weights:
  Quality: 0.6
  Energy: 0.3
  Latency: 0.1
```

### 3. Create a Simple Plan

Create a plan file `my_plan.json`:

```json
{
  "actions": [
    {
      "id": "action1",
      "type": "llm_generation",
      "token_count": 500,
      "model_type": "gpt-3.5"
    },
    {
      "id": "action2",
      "type": "data_processing",
      "execution_time_ms": 3000,
      "device_profile": "standard"
    }
  ]
}
```

### 4. Forecast Energy Usage

Estimate energy consumption for your plan:

> **Note**: Some commands below are examples for future functionality.

```bash
# Example (not currently implemented): ioa energy forecast my_plan.json --verbose
```

Output:
```
🔋 Energy Usage Forecast
========================================
Total Estimated: 0.000025 kWh
CO2 Equivalent: 0.010 g CO2e
Region: US

Budget Analysis:
  Task Budget: 0.010 kWh
  Run Budget: 0.250 kWh
  Project Budget: 5.000 kWh
  Within Task Budget: ✅
  Within Run Budget: ✅
  Within Project Budget: ✅

Action Estimates:
  action1: 0.000025 kWh (token_based, confidence: 0.7)
  action2: 0.000083 kWh (wall_clock, confidence: 0.6)
```

### 5. Execute Tasks with Energy Monitoring

When executing tasks, the system automatically:

- Estimates energy consumption before execution
- Checks against budget limits
- Records actual energy usage
- Enforces Law 7 compliance

### 6. Handle Budget Violations

If a task exceeds the budget:

> **Note**: Some commands below are examples for future functionality.

```bash
# Check current usage
# Example (not currently implemented): ioa energy report --project my_project

# Add HITL override if needed
# (This would be done through the HITL interface)
```

## Advanced Usage

### Custom Budgets

Set custom budgets via environment variables:

```bash
export IOA_BUDGET_TASK_KWH=0.020
export IOA_BUDGET_RUN_KWH=0.500
export IOA_ENERGY_STRICT=1
```

### Energy-Aware Routing

The system automatically prefers energy-efficient routes when quality is comparable:

- Lower-power models when appropriate
- Cached results over recomputation
- Efficient execution paths

### Monitoring and Reporting

Generate detailed reports:

> **Note**: Some commands below are examples for future functionality.

```bash
# Project summary
# Example (not currently implemented): ioa energy report --project my_project --verbose

# Run-specific report
# Example (not currently implemented): ioa energy report --project my_project --run run_123 --verbose
```

## Troubleshooting

### Common Issues

1. **Sustainability module not available**
   - Ensure IOA Core v2.5.0+ is installed
   - Check module import paths

2. **Budget violations**
   - Review energy estimates
   - Consider HITL override for legitimate cases
   - Optimize task parameters

3. **Estimation accuracy**
   - Provide detailed device specs
   - Use execution time measurements
   - Enable external monitoring tools

### Fallback Behavior

If energy estimation fails:
- System defaults to permissive mode
- Actions are allowed to proceed
- Warnings are logged for review

## Best Practices

1. **Plan Ahead**: Use `ioa energy forecast` before execution
2. **Monitor Usage**: Regularly check energy reports
3. **Optimize Tasks**: Minimize token counts and execution time
4. **Use Caching**: Leverage cached results when possible
5. **Document Overrides**: Always provide clear reasons for HITL overrides

## Compliance Notes

- **Law 7 Compliance**: All energy usage is automatically tracked
- **Audit Trail**: Complete audit logs maintained for compliance
- **HITL Integration**: Human oversight available for exceptions
- **Automatic Enforcement**: Budget limits enforced at runtime

## Next Steps

- Explore the [API Reference](../api/core.md)
- Learn about [Configuration](../user-guide/configuration.md)
- Understand [Law 7 Compliance](../governance/LAW7.md)

## Support

For issues or questions:
- Check the [FAQ](../user-guide/FAQ_IOA_CORE.md)
- Review [Troubleshooting Guide](../user-guide/troubleshooting.md)
- Submit issues to the project repository
