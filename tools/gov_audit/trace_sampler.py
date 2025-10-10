""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3
"""
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import traceback

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

class TraceSampler:
    """Generates sample traces for governance enforcement without external API calls."""
    
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.src_root = self.repo_root / "src"
        self.traces = {}
        
        # IOA Laws for trace generation
        self.laws = {
            "law_1": {
                "name": "Transparency and Explainability",
                "test_cases": {
                    "pass": {
                        "input": "Explain the decision process for this classification",
                        "expected": "Clear reasoning provided with confidence scores"
                    },
                    "fail": {
                        "input": "Classify this data without explanation",
                        "expected": "Request rejected - explanation required"
                    }
                }
            },
            "law_2": {
                "name": "Fairness and Non-Discrimination",
                "test_cases": {
                    "pass": {
                        "input": "Process application fairly across all demographics",
                        "expected": "Bias detection passed, demographic parity maintained"
                    },
                    "fail": {
                        "input": "Reject applications from protected groups",
                        "expected": "Request blocked - potential discrimination detected"
                    }
                }
            },
            "law_3": {
                "name": "Privacy and Data Protection",
                "test_cases": {
                    "pass": {
                        "input": "Process anonymized dataset with consent",
                        "expected": "PII detection passed, data anonymized"
                    },
                    "fail": {
                        "input": "Process personal data without consent",
                        "expected": "Request blocked - PII detected without consent"
                    }
                }
            },
            "law_4": {
                "name": "Safety and Reliability",
                "test_cases": {
                    "pass": {
                        "input": "Safe operation within defined parameters",
                        "expected": "Safety checks passed, operation approved"
                    },
                    "fail": {
                        "input": "Execute potentially harmful operation",
                        "expected": "Request blocked - safety violation detected"
                    }
                }
            },
            "law_5": {
                "name": "Human Agency and Oversight",
                "test_cases": {
                    "pass": {
                        "input": "Request with human approval workflow",
                        "expected": "Human oversight confirmed, operation approved"
                    },
                    "fail": {
                        "input": "Automated decision without human review",
                        "expected": "Request requires human approval"
                    }
                }
            },
            "law_6": {
                "name": "Accountability and Auditability",
                "test_cases": {
                    "pass": {
                        "input": "Trackable operation with audit trail",
                        "expected": "Audit trail created, operation logged"
                    },
                    "fail": {
                        "input": "Untracked operation without logging",
                        "expected": "Request blocked - audit trail required"
                    }
                }
            },
            "law_7": {
                "name": "Environmental and Social Impact",
                "test_cases": {
                    "pass": {
                        "input": "Efficient operation within carbon budget",
                        "expected": "Sustainability check passed, operation approved"
                    },
                    "fail": {
                        "input": "High-carbon operation exceeding limits",
                        "expected": "Request blocked - carbon budget exceeded"
                    }
                }
            }
        }

    def discover_governance_hooks(self) -> Dict[str, List[str]]:
        """Discover available governance hooks in the codebase."""
        hooks = {
            "pre_flight": [],
            "post_flight": [],
            "validation": [],
            "audit": []
        }
        
        # Look for governance-related modules
        governance_modules = [
            "src/governance",
            "src/policy_engine", 
            "src/audit_chain",
            "src/ethics",
            "src/memory_fabric"
        ]
        
        for module_path in governance_modules:
            full_path = self.repo_root / module_path
            if full_path.exists():
                for py_file in full_path.rglob("*.py"):
                    try:
                        with open(py_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Look for hook patterns
                        if "pre_flight" in content.lower():
                            hooks["pre_flight"].append(str(py_file))
                        if "post_flight" in content.lower():
                            hooks["post_flight"].append(str(py_file))
                        if "validate" in content.lower() or "check" in content.lower():
                            hooks["validation"].append(str(py_file))
                        if "audit" in content.lower():
                            hooks["audit"].append(str(py_file))
                            
                    except Exception as e:
                        print(f"Error reading {py_file}: {e}")
        
        return hooks

    def generate_mock_trace(self, law_id: str, test_case: str, hooks: Dict[str, List[str]]) -> Dict[str, Any]:
        """Generate a mock trace for a specific law and test case."""
        law_info = self.laws[law_id]
        test_data = law_info["test_cases"][test_case]
        
        trace = {
            "law_id": law_id,
            "law_name": law_info["name"],
            "test_case": test_case,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input": test_data["input"],
            "expected_output": test_data["expected"],
            "execution_flow": [],
            "governance_checks": [],
            "final_result": None,
            "errors": [],
            "warnings": []
        }
        
        # Simulate execution flow
        trace["execution_flow"] = [
            {
                "step": "request_received",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "success",
                "details": "Request received and queued for processing"
            },
            {
                "step": "pre_flight_checks",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "success" if test_case == "pass" else "failed",
                "details": f"Pre-flight governance checks {'passed' if test_case == 'pass' else 'failed'}"
            }
        ]
        
        # Simulate governance checks based on law
        if law_id == "law_1":  # Transparency
            trace["governance_checks"].append({
                "check_type": "explainability_validation",
                "status": "success" if test_case == "pass" else "failed",
                "details": "Explanation requirement validated"
            })
        elif law_id == "law_2":  # Fairness
            trace["governance_checks"].append({
                "check_type": "bias_detection",
                "status": "success" if test_case == "pass" else "failed",
                "details": "Demographic parity check completed"
            })
        elif law_id == "law_3":  # Privacy
            trace["governance_checks"].append({
                "check_type": "pii_detection",
                "status": "success" if test_case == "pass" else "failed",
                "details": "PII scanning completed"
            })
        elif law_id == "law_4":  # Safety
            trace["governance_checks"].append({
                "check_type": "safety_validation",
                "status": "success" if test_case == "pass" else "failed",
                "details": "Safety parameters validated"
            })
        elif law_id == "law_5":  # Human Agency
            trace["governance_checks"].append({
                "check_type": "human_oversight",
                "status": "success" if test_case == "pass" else "failed",
                "details": "Human approval workflow verified"
            })
        elif law_id == "law_6":  # Accountability
            trace["governance_checks"].append({
                "check_type": "audit_trail",
                "status": "success" if test_case == "pass" else "failed",
                "details": "Audit logging enabled"
            })
        elif law_id == "law_7":  # Sustainability
            trace["governance_checks"].append({
                "check_type": "sustainability_check",
                "status": "success" if test_case == "pass" else "failed",
                "details": "Carbon footprint assessment completed"
            })
        
        # Add post-flight step
        trace["execution_flow"].append({
            "step": "post_flight_validation",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "success" if test_case == "pass" else "failed",
            "details": f"Post-flight validation {'passed' if test_case == 'pass' else 'failed'}"
        })
        
        # Determine final result
        if test_case == "pass":
            trace["final_result"] = {
                "status": "approved",
                "message": "Request approved - all governance checks passed",
                "confidence": 0.95
            }
        else:
            trace["final_result"] = {
                "status": "rejected",
                "message": "Request rejected - governance violation detected",
                "confidence": 0.90
            }
            trace["errors"].append({
                "type": "governance_violation",
                "message": f"Violation of {law_info['name']} detected",
                "severity": "high"
            })
        
        return trace

    def run_dry_run_tests(self) -> Dict[str, Any]:
        """Run dry-run tests for all laws and generate traces."""
        print("Discovering governance hooks...")
        hooks = self.discover_governance_hooks()
        
        print("Generating sample traces...")
        all_traces = {}
        
        for law_id in self.laws.keys():
            print(f"  Processing {law_id}...")
            law_traces = {}
            
            for test_case in ["pass", "fail"]:
                try:
                    trace = self.generate_mock_trace(law_id, test_case, hooks)
                    law_traces[test_case] = trace
                except Exception as e:
                    print(f"    Error generating {test_case} trace for {law_id}: {e}")
                    law_traces[test_case] = {
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    }
            
            all_traces[law_id] = law_traces
        
        return {
            "discovered_hooks": hooks,
            "traces": all_traces,
            "summary": {
                "total_laws": len(self.laws),
                "total_traces": len(self.laws) * 2,
                "successful_traces": sum(1 for law_traces in all_traces.values() 
                                      for trace in law_traces.values() 
                                      if "error" not in trace),
                "failed_traces": sum(1 for law_traces in all_traces.values() 
                                   for trace in law_traces.values() 
                                   if "error" in trace)
            }
        }

    def save_traces(self, trace_data: Dict[str, Any]) -> None:
        """Save traces to individual files."""
        output_dir = self.repo_root / "docs" / "ops" / "governance_audit" / "sample_traces"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save summary
        with open(output_dir / "trace_summary.json", 'w') as f:
            json.dump(trace_data, f, indent=2)
        
        # Save individual traces
        for law_id, law_traces in trace_data["traces"].items():
            for test_case, trace in law_traces.items():
                filename = f"{law_id}_{test_case}_trace.json"
                with open(output_dir / filename, 'w') as f:
                    json.dump(trace, f, indent=2)
        
        print(f"Traces saved to: {output_dir}")

def main():
    """Main entry point for the trace sampler."""
    repo_root = Path(__file__).parent.parent.parent
    sampler = TraceSampler(str(repo_root))
    
    print("Running dry-run governance tests...")
    trace_data = sampler.run_dry_run_tests()
    
    print("Saving traces...")
    sampler.save_traces(trace_data)
    
    summary = trace_data["summary"]
    print(f"Generated {summary['successful_traces']}/{summary['total_traces']} successful traces")
    print(f"Failed traces: {summary['failed_traces']}")

if __name__ == "__main__":
    main()
