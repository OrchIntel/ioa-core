""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""

This script measures key performance metrics for the 4D Memory Scheduler:
- Revival latency
- Percentage of stale revived items
- Consensus stability with/without VAD/mood weighting
"""

import time
import random
import statistics
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import json
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from cold_storage import ColdStorage, create_cold_storage
    from cold_storage.audit_log import AuditLogger, create_audit_logger
except ImportError:
    print("Warning: cold_storage modules not available. Using mock implementations.")
    # Mock implementations for testing
    class MockColdStorage:
        def __init__(self, *args, **kwargs):
            self.storage = {}
        def store(self, key, data, **kwargs):
            self.storage[key] = data
            return True
        def retrieve(self, key):
            return self.storage.get(key)
        def delete(self, key):
            if key in self.storage:
                del self.storage[key]
                return True
            return False
    
    class MockAuditLogger:
        def __init__(self, *args, **kwargs):
            self.logs = []
        def log(self, *args, **kwargs):
            self.logs.append(args)
            return True
    
    ColdStorage = MockColdStorage
    create_cold_storage = lambda *args, **kwargs: MockColdStorage()
    create_audit_logger = lambda *args, **kwargs: MockAuditLogger()

@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""
    test_name: str
    duration_ms: float
    success_count: int
    total_count: int
    error_count: int
    metrics: Dict[str, Any]
    timestamp: datetime

class FourDSchedulerBenchmark:
    """Benchmark suite for 4D Memory Scheduler."""
    
    def __init__(self, storage_path: str = "./benchmark_data"):
        """Initialize benchmark environment."""
        self.storage_path = storage_path
        self.cold_storage = create_cold_storage(storage_path)
        self.audit_logger = create_audit_logger(storage_path)
        
        # Test data
        self.test_keys = [f"test_key_{i}" for i in range(1000)]
        self.test_data = {key: self._generate_test_data() for key in self.test_keys}
        
        # Benchmark results
        self.results: List[BenchmarkResult] = []
    
    def _generate_test_data(self) -> Dict[str, Any]:
        """Generate test data with 4D characteristics."""
        return {
            'temporal_score': random.uniform(0.0, 1.0),
            'spatial_score': random.uniform(0.0, 1.0),
            'contextual_score': random.uniform(0.0, 1.0),
            'priority_score': random.uniform(0.0, 1.0),
            'content': f"Test content {random.randint(1, 10000)}",
            'metadata': {
                'category': random.choice(['high', 'medium', 'low']),
                'tags': random.sample(['ai', 'ml', 'data', 'compute'], random.randint(1, 3))
            }
        }
    
    def benchmark_revival_latency(self, iterations: int = 100) -> BenchmarkResult:
        """Benchmark memory revival latency."""
        print(f"Running revival latency benchmark ({iterations} iterations)...")
        
        start_time = time.time()
        success_count = 0
        error_count = 0
        latencies = []
        
        for i in range(iterations):
            try:
                # Store data
                key = random.choice(self.test_keys)
                data = self.test_data[key]
                
                store_start = time.time()
                success = self.cold_storage.store(key, data)
                store_time = (time.time() - store_start) * 1000
                
                if success:
                    # Retrieve data (revival)
                    retrieve_start = time.time()
                    retrieved = self.cold_storage.retrieve(key)
                    retrieve_time = (time.time() - retrieve_start) * 1000
                    
                    if retrieved:
                        latencies.append(retrieve_time)
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
                print(f"Error in iteration {i}: {e}")
        
        total_time = (time.time() - start_time) * 1000
        
        metrics = {
            'avg_latency_ms': statistics.mean(latencies) if latencies else 0,
            'min_latency_ms': min(latencies) if latencies else 0,
            'max_latency_ms': max(latencies) if latencies else 0,
            'p95_latency_ms': statistics.quantiles(latencies, n=20)[-1] if len(latencies) >= 20 else 0,
            'total_latencies': len(latencies)
        }
        
        result = BenchmarkResult(
            test_name="revival_latency",
            duration_ms=total_time,
            success_count=success_count,
            total_count=iterations,
            error_count=error_count,
            metrics=metrics,
            timestamp=datetime.now(timezone.utc)
        )
        
        self.results.append(result)
        return result
    
    def benchmark_stale_revival_rate(self, iterations: int = 100) -> BenchmarkResult:
        """Benchmark percentage of stale revived items."""
        print(f"Running stale revival rate benchmark ({iterations} iterations)...")
        
        start_time = time.time()
        success_count = 0
        error_count = 0
        stale_count = 0
        
        # Create time-based test data
        for i in range(iterations):
            try:
                key = f"stale_test_{i}"
                
                # Store data with old timestamp
                old_data = {
                    'temporal_score': 0.1,  # Low temporal score (stale)
                    'spatial_score': random.uniform(0.0, 1.0),
                    'contextual_score': random.uniform(0.0, 1.0),
                    'priority_score': random.uniform(0.0, 1.0),
                    'timestamp': (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat(),
                    'content': f"Stale content {i}"
                }
                
                success = self.cold_storage.store(key, old_data)
                
                if success:
                    # Retrieve and check if stale
                    retrieved = self.cold_storage.retrieve(key)
                    if retrieved:
                        # Check if data is considered stale (temporal_score < 0.3)
                        if retrieved.get('data', {}).get('temporal_score', 1.0) < 0.3:
                            stale_count += 1
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
                print(f"Error in iteration {i}: {e}")
        
        total_time = (time.time() - start_time) * 1000
        
        stale_percentage = (stale_count / success_count * 100) if success_count > 0 else 0
        
        metrics = {
            'stale_percentage': stale_percentage,
            'stale_count': stale_count,
            'fresh_count': success_count - stale_count,
            'total_retrieved': success_count
        }
        
        result = BenchmarkResult(
            test_name="stale_revival_rate",
            duration_ms=total_time,
            success_count=success_count,
            total_count=iterations,
            error_count=error_count,
            metrics=metrics,
            timestamp=datetime.now(timezone.utc)
        )
        
        self.results.append(result)
        return result
    
    def benchmark_consensus_stability(self, iterations: int = 100) -> BenchmarkResult:
        """Benchmark consensus stability with/without VAD/mood weighting."""
        print(f"Running consensus stability benchmark ({iterations} iterations)...")
        
        start_time = time.time()
        success_count = 0
        error_count = 0
        consensus_changes = []
        
        # Simulate consensus decisions with different weighting schemes
        for i in range(iterations):
            try:
                # Generate multiple agent decisions
                agent_decisions = []
                for agent_id in range(5):  # 5 agents
                    decision = {
                        'agent_id': f"agent_{agent_id}",
                        'confidence': random.uniform(0.5, 1.0),
                        'vad_score': random.uniform(0.0, 1.0),  # Voice Activity Detection
                        'mood_score': random.uniform(0.0, 1.0),  # Emotional state
                        'decision': random.choice(['approve', 'reject', 'modify'])
                    }
                    agent_decisions.append(decision)
                
                # Calculate consensus without VAD/mood weighting
                unweighted_consensus = self._calculate_unweighted_consensus(agent_decisions)
                
                # Calculate consensus with VAD/mood weighting
                weighted_consensus = self._calculate_weighted_consensus(agent_decisions)
                
                # Check if consensus changed
                consensus_changed = unweighted_consensus != weighted_consensus
                consensus_changes.append(consensus_changed)
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"Error in iteration {i}: {e}")
        
        total_time = (time.time() - start_time) * 1000
        
        stability_percentage = (1 - (sum(consensus_changes) / len(consensus_changes))) * 100 if consensus_changes else 100
        
        metrics = {
            'stability_percentage': stability_percentage,
            'consensus_changes': sum(consensus_changes),
            'total_decisions': len(consensus_changes),
            'unweighted_consensus': unweighted_consensus if 'unweighted_consensus' in locals() else None,
            'weighted_consensus': weighted_consensus if 'weighted_consensus' in locals() else None
        }
        
        result = BenchmarkResult(
            test_name="consensus_stability",
            duration_ms=total_time,
            success_count=success_count,
            total_count=iterations,
            error_count=error_count,
            metrics=metrics,
            timestamp=datetime.now(timezone.utc)
        )
        
        self.results.append(result)
        return result
    
    def _calculate_unweighted_consensus(self, decisions: List[Dict[str, Any]]) -> str:
        """Calculate consensus without VAD/mood weighting."""
        decision_counts = {}
        for decision in decisions:
            decision_value = decision['decision']
            decision_counts[decision_value] = decision_counts.get(decision_value, 0) + 1
        
        # Return most common decision
        return max(decision_counts.items(), key=lambda x: x[1])[0]
    
    def _calculate_weighted_consensus(self, decisions: List[Dict[str, Any]]) -> str:
        """Calculate consensus with VAD/mood weighting."""
        decision_scores = {}
        
        for decision in decisions:
            decision_value = decision['decision']
            confidence = decision['confidence']
            vad_score = decision['vad_score']
            mood_score = decision['mood_score']
            
            # Weighted score: confidence * VAD * mood
            weighted_score = confidence * vad_score * mood_score
            
            if decision_value not in decision_scores:
                decision_scores[decision_value] = 0
            decision_scores[decision_value] += weighted_score
        
        # Return decision with highest weighted score
        return max(decision_scores.items(), key=lambda x: x[1])[0]
    
    def run_all_benchmarks(self, iterations: int = 100) -> List[BenchmarkResult]:
        """Run all benchmarks."""
        print("Starting 4D Memory Scheduler benchmarks...")
        print(f"Iterations per benchmark: {iterations}")
        print("-" * 50)
        
        # Run benchmarks
        self.benchmark_revival_latency(iterations)
        self.benchmark_stale_revival_rate(iterations)
        self.benchmark_consensus_stability(iterations)
        
        print("-" * 50)
        print("All benchmarks completed!")
        
        return self.results
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive benchmark report."""
        if not self.results:
            return {"error": "No benchmark results available"}
        
        report = {
            "benchmark_info": {
                "version": "v2.5.0",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_tests": len(self.results),
                "storage_path": self.storage_path
            },
            "results": [],
            "summary": {
                "total_duration_ms": sum(r.duration_ms for r in self.results),
                "total_success": sum(r.success_count for r in self.results),
                "total_errors": sum(r.error_count for r in self.results),
                "success_rate": sum(r.success_count for r in self.results) / sum(r.total_count for r in self.results) * 100 if any(r.total_count for r in self.results) else 0
            }
        }
        
        for result in self.results:
            report["results"].append({
                "test_name": result.test_name,
                "duration_ms": result.duration_ms,
                "success_count": result.success_count,
                "total_count": result.total_count,
                "error_count": result.error_count,
                "metrics": result.metrics,
                "timestamp": result.timestamp.isoformat()
            })
        
        return report
    
    def save_report(self, filename: str = "4d_scheduler_benchmark_report.json"):
        """Save benchmark report to file."""
        report = self.generate_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Benchmark report saved to: {filename}")
        return filename

def main():
    """Main benchmark execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="4D Memory Scheduler Benchmark")
    parser.add_argument("--iterations", "-i", type=int, default=100,
                       help="Number of iterations per benchmark (default: 100)")
    parser.add_argument("--storage-path", "-s", type=str, default="./benchmark_data",
                       help="Storage path for benchmark data (default: ./benchmark_data)")
    parser.add_argument("--output", "-o", type=str, default="4d_scheduler_benchmark_report.json",
                       help="Output report filename (default: 4d_scheduler_benchmark_report.json)")
    
    args = parser.parse_args()
    
    # Run benchmarks
    benchmark = FourDSchedulerBenchmark(args.storage_path)
    results = benchmark.run_all_benchmarks(args.iterations)
    
    # Generate and save report
    report_file = benchmark.save_report(args.output)
    
    # Print summary
    print(f"Total tests: {len(results)}")
    print(f"Total duration: {sum(r.duration_ms for r in results):.2f} ms")
    print(f"Success rate: {sum(r.success_count for r in results) / sum(r.total_count for r in results) * 100:.1f}%")
    
    # Print key metrics
    for result in results:
        print(f"\n{result.test_name}:")
        for key, value in result.metrics.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.3f}")
            else:
                print(f"  {key}: {value}")

if __name__ == "__main__":
    main()
