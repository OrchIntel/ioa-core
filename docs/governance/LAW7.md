**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Law 7: Sustainability Stewardship


**PATCH:** Cursor-2025-09-05 DISPATCH-GOV-20250905-LAW-7-SUSTAINABILITY  
Law 7 governance documentation for sustainability stewardship.

## Overview

**Law 7: Sustainability Stewardship** establishes that IOA must minimize environmental impact while meeting task requirements. This law constrains energy and carbon usage, favors lower-footprint choices when quality is comparable, and captures auditable telemetry for enterprise and government certification.

## Core Principles

1. **Energy Budgeting**: All tasks, runs, and projects have energy budgets
2. **Green Routing**: Prefer energy-efficient models and paths when quality is comparable
3. **Waste Prevention**: Cap wasteful retries and concurrency
4. **Audit Trail**: All energy decisions and usage must be auditable
5. **Human Oversight**: Breaches require explicit HITL override with reason

## Enforcement Levels

- **WARNING**: Issued at 80% of budget limit
- **BLOCK**: Hard stop at 100% of budget limit
- **HITL OVERRIDE**: Available for legitimate exceptions with time-bound waivers

## Budget Limits

| Level | Default Limit | Purpose |
|-------|---------------|---------|
| Task | 0.010 kWh | Individual action energy cap |
| Run | 0.250 kWh | Execution session energy cap |
| Project | 5.000 kWh | Overall project energy cap |

## Energy Estimation Methods

### 1. Token-Based Estimation
- **Use Case**: API calls to LLM providers
- **Accuracy**: High confidence (0.7-0.8)
- **Models**: GPT-4, Claude-3, Llama-3, etc.
- **Calculation**: `tokens × energy_per_token`

### 2. Wall-Clock Estimation
- **Use Case**: Local computation and processing
- **Accuracy**: Medium confidence (0.6)
- **Calculation**: `execution_time × power_consumption / 3600`

### 3. Device Profile Estimation
- **Use Case**: Hardware-specific operations
- **Accuracy**: Medium confidence (0.5)
- **Calculation**: `(base_power + cpu_power + gpu_power + memory_power) × time`

### 4. External Adapter Estimation
- **Use Case**: When monitoring tools available
- **Accuracy**: High confidence (0.8)
- **Tools**: psutil, nvidia-smi, AMD ROCm
- **Fallback**: Conservative estimates if unavailable

## CO2 Calculation

### Regional Emission Factors

| Region | Factor (g CO2e/kWh) | Notes |
|--------|---------------------|-------|
| EU | 300 | European Union average |
| US | 400 | United States average |
| UK | 250 | More renewable energy |
| CA | 150 | Hydro-heavy generation |
| AU | 800 | Coal-heavy generation |
| Local | 100 | Local computation (greener) |

### Calculation Formula
```
CO2e (g) = Energy (kWh) × Emission Factor (g CO2e/kWh)
```

## Energy-Aware Routing

### Routing Strategies

1. **Balanced** (Default)
   - Quality: 60%
   - Energy: 30%
   - Latency: 10%

2. **Quality First**
   - Quality: 70%
   - Energy: 20%
   - Latency: 10%

3. **Energy First**
   - Quality: 30%
   - Energy: 60%
   - Latency: 10%

4. **Sustainability Strict**
   - Quality: 20%
   - Energy: 70%
   - Latency: 10%

### Provider Sustainability Ratings

- **Excellent**: Local models, efficient cloud models
- **Good**: Standard cloud models
- **Unknown**: Unrated providers

## HITL Override Process

### When Override is Required
- Task exceeds energy budget
- Run exceeds energy budget
- Project approaches budget limits

### Override Requirements
1. **Reason**: Explicit justification for energy usage
2. **Duration**: Time-bound waiver (default: 15 minutes)
3. **Approval**: Human approval through HITL interface
4. **Audit**: Complete logging of override decision

### Override Expiration
- Automatic expiration at end of duration
- Re-approval required for extensions
- All overrides logged for compliance

## Compliance Monitoring

### Automatic Checks
- Pre-execution budget validation
- Runtime energy usage tracking
- Post-execution compliance verification

### Audit Fields
- `energy_kwh`: Actual energy consumption
- `energy_kwh_projected`: Estimated consumption
- `co2e_g`: CO2 equivalent emissions
- `budget_id`: Budget context identifier
- `budget_limit_kwh`: Budget limit
- `decision`: ALLOW/WARN/BLOCK/HITL_OVERRIDE
- `override_reason`: Justification if overridden

### Reporting
- Real-time energy usage dashboards
- Budget compliance reports
- Sustainability impact summaries
- CO2 emission tracking

## Integration Points

### Task Orchestrator
- Pre-execution energy budget check
- Runtime energy monitoring
- Post-execution energy recording

### Policy Engine
- Law 7 compliance validation
- Budget enforcement decisions
- HITL override management

### CLI Interface
- Energy usage forecasting
- Budget status reporting
- Provider routing decisions

## Configuration

### Environment Variables
```bash
# Budget limits
export IOA_BUDGET_TASK_KWH=0.020
export IOA_BUDGET_RUN_KWH=0.500
export IOA_BUDGET_PROJECT_KWH=10.0

# Routing weights
export IOA_ENERGY_WEIGHT=0.4
export IOA_QUALITY_WEIGHT=0.5
export IOA_LATENCY_WEIGHT=0.1

# Sustainability mode
export IOA_ENERGY_STRICT=1
export IOA_REGION=EU
```

### Configuration File
```yaml
sustainability:
  budgets:
    task_kwh: 0.010
    run_kwh: 0.250
    project_kwh: 5.000
  warn_fraction: 0.8
  block_fraction: 1.0
  weights:
    quality: 0.6
    energy: 0.3
    latency: 0.1
  region: auto
  allow_hitl_override: true
```

## Best Practices

### For Developers
1. **Estimate First**: Use energy forecasting before execution
2. **Choose Efficiently**: Prefer energy-efficient models when appropriate
3. **Monitor Usage**: Track energy consumption during development
4. **Document Overrides**: Always provide clear reasons for HITL overrides

### For Operators
1. **Set Realistic Budgets**: Balance efficiency with operational needs
2. **Monitor Trends**: Track energy usage patterns over time
3. **Review Overrides**: Regularly audit HITL override decisions
4. **Optimize Workloads**: Identify and address energy-intensive operations

### For Compliance Officers
1. **Audit Regularly**: Review energy usage and compliance reports
2. **Validate Estimates**: Ensure energy estimates are accurate
3. **Track Overrides**: Monitor HITL override patterns and justifications
4. **Report Impact**: Generate sustainability impact reports for stakeholders

## Troubleshooting

### Common Issues

1. **Frequent Budget Violations**
   - Review energy estimates for accuracy
   - Adjust budget limits if appropriate
   - Optimize task parameters

2. **Poor Energy Estimation**
   - Provide detailed device specifications
   - Use execution time measurements
   - Enable external monitoring tools

3. **HITL Override Abuse**
   - Review override justifications
   - Implement stricter approval processes
   - Monitor override patterns

### Fallback Behavior
- If energy estimation fails, system defaults to permissive mode
- Actions are allowed to proceed with warnings
- All failures are logged for review and improvement

## Future Enhancements

### Planned Features
- Machine learning-based energy estimation
- Dynamic budget adjustment based on workload
- Integration with renewable energy APIs
- Advanced CO2 calculation with real-time grid data

### Research Areas
- Energy-efficient model architectures
- Green computing best practices
- Carbon offset integration
- Sustainability certification frameworks

## References

- [Energy-Aware Quickstart Tutorial](../tutorials/energy-aware-quickstart.md)
- [API Reference](../api/core.md)
- [System Laws Overview](SYSTEM_LAWS.md)
- [Governance Overview](GOVERNANCE.md)
