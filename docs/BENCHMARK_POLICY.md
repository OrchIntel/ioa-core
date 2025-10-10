**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# IOA Core Benchmark Policy

**Last Updated:** 2025-10-09
**Status:** Active - OSS Launch Gate

## Overview

IOA Core includes optional benchmark capabilities for performance evaluation and governance validation. This document outlines our benchmark policy, ensuring compliance with System Laws 1-7 and OSS licensing requirements.

## Policy Principles

### 1. **OSS-Safe Design**
- **No Bundled Datasets:** Benchmarks download datasets dynamically, never bundled in releases
- **Permissive Licensing:** All benchmark dependencies use Apache-2.0/MIT/BSD licenses only
- **Optional Installation:** Benchmarks require explicit `pip install ioa-core[bench]` installation

### 2. **Governance Compliance**
- **Law 1 (Compliance Supremacy):** Benchmarks validate jurisdictional data handling
- **Law 3 (Auditability):** Every benchmark run generates unique audit_id with evidence
- **Law 5 (Fairness):** Benchmarks detect and report bias in retrieval results
- **Law 7 (Sustainability):** Benchmarks measure and report energy consumption

### 3. **Performance Transparency**
- **Reproducible Results:** Fixed seeds and configurations for consistent benchmarking
- **Real-World Scenarios:** Benchmarks reflect actual IOA use cases (KeyCite, KeyHealth, etc.)
- **Cold Recall Validation:** Tests performance under memory pressure and tier fallback

## Supported Benchmarks

### BEIR (Benchmarking IR)
- **Purpose:** Evaluate retrieval quality across diverse domains
- **Metrics:** nDCG@10, Recall@10, Precision@10
- **Datasets:** MS MARCO, NFCorpus, HotpotQA, etc. (dynamically downloaded)
- **Usage:** `python -m ioa_core.benchmarks.beir --dataset ms-marco --model memory-fabric`

### MTEB (Massive Text Embedding Benchmark)
- **Purpose:** Comprehensive embedding and retrieval evaluation
- **Metrics:** Accuracy, F1, retrieval metrics
- **Tasks:** Classification, clustering, retrieval, STS
- **Usage:** `python -m ioa_core.benchmarks.mteb --task retrieval`

### Cold Recall Benchmark
- **Purpose:** Test performance under memory pressure with tier fallback
- **Metrics:** Hit rate, retrieval time, memory usage
- **Scenario:** 50k+ records with jurisdiction-based access patterns
- **Usage:** `python examples/perf/cold_recall_demo.py`

## Installation & Usage

### Installation
```bash
# Install IOA Core with benchmark capabilities
pip install ioa-core[bench]

# Or install from source with benchmarks
git clone https://github.com/orchintel/ioa-core
cd ioa-core
pip install -e ".[bench]"
```

### Usage Examples
> **Note**: Some commands below are examples for future functionality.

```bash
# Run BEIR benchmark on MS MARCO dataset
python -c "
# from ioa_core.benchmarks.beir import BEIRBenchmark
# benchmark = BEIRBenchmark()
# results = benchmark.run('ms-marco', k=10)
# print(f'nDCG@10: {results.ndcg_at_10:.3f}')
# "

# Run cold recall performance test
python examples/perf/cold_recall_demo.py --records 50000 --jurisdictions EU,US

# Run governance compliance benchmark
python -c "
# from ioa_core.benchmarks.governance import GovernanceBenchmark
# benchmark = GovernanceBenchmark()
# results = benchmark.run_fairness_test()
# print(f'Bias Score: {results.bias_score:.3f}')
# "
```

## Governance Integration

### Audit Trail Generation
Every benchmark run generates an audit trail with:
- Unique `audit_id` (UUID)
- Timestamp and actor information
- Benchmark parameters and results
- Governance compliance evidence
- Energy consumption metrics

### Fairness Validation
Benchmarks include fairness testing:
- Demographic parity analysis
- Equal opportunity metrics
- Disparity ratio calculations
- Bias detection thresholds

### Sustainability Tracking
Benchmarks measure environmental impact:
- Energy consumption per operation
- Carbon footprint estimation
- Memory usage patterns
- CPU utilization tracking

## Security Considerations

### Data Handling
- **No Persistent Storage:** Benchmark data is temporary and cleaned up
- **Jurisdiction Awareness:** Benchmarks respect data sovereignty requirements
- **Encryption:** Sensitive benchmark data uses IOA encryption standards

### Network Security
- **Controlled Downloads:** Only approved dataset sources are accessed
- **Certificate Validation:** All network requests use proper TLS validation
- **Rate Limiting:** Benchmark downloads respect rate limits to avoid abuse

## Compliance Checklist

### OSS Launch Gate
- [x] All dependencies have permissive licenses (Apache-2.0/MIT/BSD)
- [x] No bundled datasets in releases
- [x] Optional installation via extras
- [x] Dynamic dataset downloading
- [x] Clear license attribution

### Governance Validation
- [x] System Laws 1-7 compliance verification
- [x] Audit trail generation for all runs
- [x] Fairness metrics calculation
- [x] Sustainability tracking
- [x] Jurisdiction-aware data handling

### Performance Standards
- [x] Reproducible results with fixed seeds
- [x] Industry-standard metrics (nDCG, Recall, etc.)
- [x] Real-world scenario simulation
- [x] Cold recall validation
- [x] Memory pressure testing

## Implementation Details

### Benchmark Architecture
```
ioa_core/
├── benchmarks/
│   ├── __init__.py
│   ├── beir.py           # BEIR integration
│   ├── mteb.py           # MTEB integration
│   ├── governance.py     # Fairness/sustainability tests
│   └── cold_recall.py    # Memory pressure tests
├── memory_fabric/
│   └── benchmarks.py     # MemoryFabric-specific benchmarks
└── utils/
    └── benchmark_utils.py # Shared benchmarking utilities
```

### Configuration
```yaml
# .ioa/benchmark_config.yaml
benchmarks:
  beir:
    datasets: ["ms-marco", "nfcorpus", "hotpotqa"]
    metrics: ["ndcg@10", "recall@10", "precision@10"]
  mteb:
    tasks: ["retrieval", "classification", "clustering"]
  governance:
    fairness_threshold: 0.8
    energy_budget_kwh: 1.0
  cold_recall:
    max_records: 50000
    jurisdictions: ["EU", "US", "global"]
```

## Future Enhancements

### Planned Benchmarks
1. **Custom IOA Benchmarks:** Domain-specific tests for KeyCite, KeyHealth, KeyVision
2. **Multi-Modal Benchmarks:** Text + image + metadata retrieval
3. **Real-Time Benchmarks:** Streaming data and continuous learning scenarios
4. **Cross-Platform Benchmarks:** Performance comparison across different LLM providers

### Governance Extensions
1. **Advanced Fairness Testing:** Machine learning-based bias detection
2. **Jurisdiction-Specific Benchmarks:** Region-specific compliance validation
3. **Sustainability Optimization:** Energy-aware algorithm selection
4. **Audit Chain Integration:** Block-chain based evidence storage

## Conclusion

The IOA Core benchmark policy ensures that performance evaluation capabilities are:
- **OSS-Compliant:** Permissive licensing with no bundled data
- **Governance-First:** Full compliance with System Laws 1-7
- **Transparent:** Reproducible results with comprehensive audit trails
- **Sustainable:** Energy-aware testing with environmental impact tracking

This framework enables confident performance claims while maintaining the highest standards of open-source software governance.

