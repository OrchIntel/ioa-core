""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Comprehensive testing and demonstration suite for digestor module
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.

# PATCH: Cursor-2025-08-15 CL-P2-Cleanup - Add missing TestResult fixture

"""
IOA Digestor Module - Comprehensive Testing and Demonstration Suite v0.1.2

Provides exhaustive testing, validation, and demonstration capabilities for the
digestor module. Features comprehensive unit tests, integration tests, performance
benchmarks, schema validation, and interactive demonstrations.

Key Features:
- Comprehensive digestor functionality testing with edge cases
- Pattern validation testing with detailed reporting
- Performance benchmarking with trend analysis
- Interactive demonstration scenarios with real-time feedback
- Error handling validation with comprehensive coverage
- Statistics validation and trend monitoring
- Schema compliance testing for IOA v0.1.2
- Production deployment readiness validation
- Integration testing hooks for CI/CD pipelines
- Memory engine integration testing
- Performance regression detection

Test Categories:
1. Pattern Validation Tests - Validate pattern definitions and structure
2. Digestor Functionality Tests - Core processing pipeline validation
3. Configuration Tests - Test different digestor configurations
4. Error Handling Tests - Comprehensive error scenario coverage
5. Performance Benchmarks - Speed and efficiency measurements
6. Statistics Tests - Metrics collection and reporting validation
7. Integration Tests - Component interaction validation
8. Schema Compliance Tests - IOA v0.1.2 compliance verification
9. Production Readiness Tests - Deployment validation
10. Interactive Demo - Real-time digestor demonstration

Version 0.1.2 Features:
- Enhanced error handling with graceful degradation
- Comprehensive schema compliance validation
- Production deployment readiness assessment
- Performance trend analysis and regression detection
- Interactive demo with enhanced user experience
- Comprehensive reporting with actionable insights
"""

import json
import time
import uuid
import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import traceback
import pytest

# Enhanced import handling for digestor with comprehensive fallback strategies
DIGESTOR_IMPORT_SUCCESS = False
DIGESTOR_IMPORT_ERROR = None

try:
    # Add src directory to Python path for imports
    src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    from digestor import (
        create_digestor, 
        DigestorConfig, 
        DigestorCore,
        validate_digestor_patterns,
        validate_production_deployment,
        ProcessingStage
    )
    DIGESTOR_IMPORT_SUCCESS = True
    print("✅ Digestor module imported successfully (from src directory)")
except ImportError as e1:
    DIGESTOR_IMPORT_ERROR = str(e1)
    try:
        # Try relative import if in package
        from .digestor import (
            create_digestor, 
            DigestorConfig, 
            DigestorCore,
            validate_digestor_patterns,
            validate_production_deployment,
            ProcessingStage
        )
        DIGESTOR_IMPORT_SUCCESS = True
        print("✅ Digestor module imported successfully (relative import)")
    except ImportError as e2:
        DIGESTOR_IMPORT_ERROR = f"Direct: {e1}, Relative: {e2}"
        print(f"❌ Failed to import digestor module: {DIGESTOR_IMPORT_ERROR}")
        print("🔧 Ensure digestor.py is in the Python path or current directory")
        print("📁 Current working directory:", os.getcwd())
        print("🐍 Python path:", sys.path[:3], "...")
        
        # Attempt to provide helpful debugging information
        if os.path.exists("digestor.py"):
            print("✅ digestor.py found in current directory")
        else:
            src_digestor_path = os.path.join(src_path, "digestor.py")
            if os.path.exists(src_digestor_path):
                print(f"✅ digestor.py found in src directory: {src_digestor_path}")
            else:
                print(f"❌ digestor.py not found in src directory: {src_digestor_path}")
        
        # Don't exit during pytest collection - just mark as failed
        DIGESTOR_IMPORT_SUCCESS = False


@pytest.fixture
def result():
    """Provide TestResult instance for tests that require it."""
    # PATCH: Cursor-2025-08-15 CL-P3-Cleanup - Initialize TestResult without constructor
    test_result = TestResult()
    test_result.test_name = "test_fixture"
    test_result.start_time = datetime.now()
    test_result.end_time = None
    test_result.success = False
    test_result.error_message = None
    test_result.warnings = []
    test_result.metrics = {}
    test_result.details = {}
    return test_result


class TestResult:
    """Enhanced test result tracking with detailed metadata"""
    
    def complete(self, success: bool, error_message: Optional[str] = None):
        """Complete the test with results"""
        self.end_time = datetime.now()
        self.success = success
        self.error_message = error_message
        self.metrics["duration"] = (self.end_time - self.start_time).total_seconds()
    
    def add_warning(self, warning: str):
        """Add warning to test results"""
        self.warnings.append(warning)
    
    def add_metric(self, name: str, value: Any):
        """Add performance metric"""
        self.metrics[name] = value
    
    def add_detail(self, key: str, value: Any):
        """Add test detail"""
        self.details[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting"""
        return {
            "test_name": self.test_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.metrics.get("duration", 0.0),
            "success": self.success,
            "error_message": self.error_message,
            "warnings": self.warnings,
            "metrics": self.metrics,
            "details": self.details
        }


@pytest.fixture
def test_runner():
    """Provide TestRunner instance for tests that require it."""
    # PATCH: Cursor-2025-08-15 CL-P3-Cleanup - Initialize TestRunner without constructor
    runner = TestRunner()
    runner.test_results = []
    runner.start_time = datetime.now()
    runner.total_tests = 0
    runner.passed_tests = 0
    runner.failed_tests = 0
    return runner


class TestRunner:
    """Enhanced test runner with comprehensive reporting and metrics"""
    
    def run_test(self, test_name: str, test_func, *args, **kwargs) -> TestResult:
        """Run individual test with comprehensive error handling"""
        result = TestResult(test_name)
        self.total_tests += 1
        
        try:
            print(f"\n🧪 Running: {test_name}")
            test_func(result, *args, **kwargs)
            
            if result.success is None:  # Test didn't explicitly set success
                result.complete(True)
            
            if result.success:
                self.passed_tests += 1
                print(f"✅ {test_name}: PASSED ({result.metrics.get('duration', 0):.3f}s)")
            else:
                self.failed_tests += 1
                print(f"❌ {test_name}: FAILED - {result.error_message}")
            
            if result.warnings:
                for warning in result.warnings:
                    print(f"⚠️  Warning: {warning}")
        
        except Exception as e:
            result.complete(False, str(e))
            self.failed_tests += 1
            print(f"💥 {test_name}: ERROR - {e}")
            print(f"📋 Traceback: {traceback.format_exc()}")
        
        self.test_results.append(result)
        return result
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive test summary"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        return {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "success_rate": (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0,
            "total_duration": total_duration,
            "average_test_duration": total_duration / self.total_tests if self.total_tests > 0 else 0,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat()
        }


def create_comprehensive_sample_patterns() -> List[Dict[str, Any]]:
    """Create comprehensive sample patterns for extensive testing"""
    return [
        {
            "pattern_id": "personal_intro",
            "keywords": ["name", "am", "is", "called"],
            "schema": ["name", "age"]
        },
        {
            "pattern_id": "contact_info",
            "keywords": ["email", "phone", "contact", "reach"],
            "schema": ["email", "phone"]
        },
        {
            "pattern_id": "location_info",
            "keywords": ["from", "live", "located", "city"],
            "schema": ["location", "country"]
        },
        {
            "pattern_id": "business_inquiry",
            "keywords": ["business", "company", "work", "job"],
            "schema": ["company", "position", "industry"]
        },
        {
            "pattern_id": "emotional_state",
            "keywords": ["feel", "feeling", "emotion", "mood"],
            "schema": ["emotion", "intensity"]
        },
        {
            "pattern_id": "financial_info",
            "keywords": ["salary", "income", "cost", "price"],
            "schema": ["amount", "currency"]
        },
        {
            "pattern_id": "technical_support",
            "keywords": ["error", "problem", "bug", "issue"],
            "schema": ["error_type", "severity"]
        },
        {
            "pattern_id": "product_feedback",
            "keywords": ["product", "feature", "suggestion", "improvement"],
            "schema": ["product_name", "feedback_type"]
        }
    ]


def create_comprehensive_test_inputs() -> List[Dict[str, Any]]:
    """Create diverse test inputs for comprehensive testing"""
    return [
        {
            "content": "My name is John Smith and I am 25 years old",
            "expected_pattern": "personal_intro",
            "description": "Basic personal introduction",
            "category": "standard"
        },
        {
            "content": "You can reach me at john.smith@example.com or call 555-123-4567",
            "expected_pattern": "contact_info",
            "description": "Contact information",
            "category": "standard"
        },
        {
            "content": "I am from New York City in the United States",
            "expected_pattern": "location_info",
            "description": "Location information",
            "category": "standard"
        },
        {
            "content": "I work at TechCorp as a Software Engineer in the technology industry",
            "expected_pattern": "business_inquiry",
            "description": "Business information",
            "category": "standard"
        },
        {
            "content": "I'm feeling really excited and energetic today!",
            "expected_pattern": "emotional_state",
            "description": "Emotional state",
            "category": "standard"
        },
        {
            "content": "My salary is $75,000 per year",
            "expected_pattern": "financial_info",
            "description": "Financial information",
            "category": "standard"
        },
        {
            "content": "I'm experiencing a critical error in the payment system",
            "expected_pattern": "technical_support",
            "description": "Technical support request",
            "category": "standard"
        },
        {
            "content": "The new dashboard feature is amazing and very intuitive",
            "expected_pattern": "product_feedback",
            "description": "Product feedback",
            "category": "standard"
        },
        # Edge cases
        {
            "content": "This is some random content that doesn't match any specific pattern",
            "expected_pattern": "UNCLASSIFIED",
            "description": "Unclassified content",
            "category": "edge_case"
        },
        {
            "content": "Short",
            "expected_pattern": "MINIMAL_ENTRY",
            "description": "Too short content",
            "category": "edge_case"
        },
        {
            "content": "",
            "expected_pattern": "MINIMAL_ENTRY",
            "description": "Empty content",
            "category": "edge_case"
        },
        {
            "content": "A" * 15000,  # Exceeds max length
            "expected_pattern": None,
            "description": "Oversized content (should be truncated)",
            "category": "edge_case"
        },
        # Complex cases
        {
            "content": "Hi, my name is Maria Garcia and I'm 32 years old. You can reach me at maria.garcia@email.com or 555-987-6543. I work at DataCorp as a Senior Data Analyst.",
            "expected_pattern": "personal_intro",  # Should match first
            "description": "Multi-pattern content",
            "category": "complex"
        },
        {
            "content": "🤖 I am feeling excited about the new AI features! My email is ai@bot.com",
            "expected_pattern": "emotional_state",
            "description": "Content with emojis and mixed patterns",
            "category": "complex"
        },
        # International and special characters
        {
            "content": "My name is François Müller and I live in Zürich, Switzerland",
            "expected_pattern": "personal_intro",
            "description": "International characters",
            "category": "international"
        },
        {
            "content": "私の名前は田中です (My name is Tanaka)",
            "expected_pattern": "personal_intro",
            "description": "Mixed language content",
            "category": "international"
        }
    ]


def test_pattern_validation_comprehensive(result: TestResult):
    """Comprehensive pattern validation testing"""
    try:
        # Test valid patterns
        valid_patterns = create_comprehensive_sample_patterns()
        validation_report = validate_digestor_patterns(valid_patterns)
        
        result.add_detail("valid_patterns_report", validation_report)
        result.add_metric("valid_patterns_count", validation_report['valid_patterns'])
        result.add_metric("total_patterns_tested", validation_report['total_patterns'])
        
        if not validation_report['validation_passed']:
            result.complete(False, "Valid patterns failed validation")
            return
        
        # Test invalid patterns with comprehensive coverage
        invalid_patterns = [
            {"pattern_id": "", "keywords": [], "schema": []},  # Empty fields
            {"keywords": ["test"], "schema": ["field"]},  # Missing pattern_id
            {"pattern_id": "test", "schema": ["field"]},  # Missing keywords
            {"pattern_id": "test", "keywords": "not_a_list", "schema": []},  # Wrong type
            {"pattern_id": "test", "keywords": [], "schema": ["field"]},  # Empty keywords
            {"pattern_id": None, "keywords": ["test"], "schema": ["field"]},  # None pattern_id
            {"pattern_id": "test", "keywords": [""], "schema": ["field"]},  # Empty keyword
            {"pattern_id": "test", "keywords": ["test"], "schema": "not_a_list"},  # Wrong schema type
        ]
        
        invalid_validation = validate_digestor_patterns(invalid_patterns)
        result.add_detail("invalid_patterns_report", invalid_validation)
        result.add_metric("invalid_patterns_tested", len(invalid_patterns))
        result.add_metric("invalid_patterns_detected", invalid_validation['invalid_patterns'])
        
        if invalid_validation['validation_passed']:
            result.complete(False, "Invalid patterns incorrectly passed validation")
            return
        
        # Test edge cases
        edge_patterns = [
            # Very long pattern ID
            {"pattern_id": "a" * 1000, "keywords": ["test"], "schema": ["field"]},
            # Many keywords
            {"pattern_id": "many_keywords", "keywords": ["a"] * 100, "schema": ["field"]},
            # Complex schema
            {"pattern_id": "complex", "keywords": ["test"], "schema": ["a"] * 50},
        ]
        
        edge_validation = validate_digestor_patterns(edge_patterns)
        result.add_detail("edge_patterns_report", edge_validation)
        result.add_metric("edge_patterns_valid", edge_validation['valid_patterns'])
        
        result.complete(True)
        
    except Exception as e:
        result.complete(False, f"Pattern validation test failed: {e}")


def test_digestor_functionality_comprehensive(result: TestResult):
    """Comprehensive digestor functionality testing"""
    try:
        patterns = create_comprehensive_sample_patterns()
        test_inputs = create_comprehensive_test_inputs()
        
        # Test with default configuration
        digestor = create_digestor(patterns=patterns)
        
        pattern_matches = 0
        processing_times = []
        confidence_scores = []
        
        for i, test_case in enumerate(test_inputs):
            start_time = time.time()
            digest_result = digestor.digest_entry(test_case['content'])
            processing_time = time.time() - start_time
            
            processing_times.append(processing_time)
            confidence_scores.append(digest_result.confidence_score)
            
            # Validate result structure
            if not hasattr(digest_result, 'compacted_entry'):
                result.complete(False, f"Test {i+1}: Missing compacted_entry in result")
                return
            
            entry = digest_result.compacted_entry
            
            # Check required fields
            required_fields = ["id", "pattern_id", "metadata", "feeling"]
            missing_fields = [field for field in required_fields if field not in entry]
            if missing_fields:
                result.complete(False, f"Test {i+1}: Missing required fields: {missing_fields}")
                return
            
            # Check pattern matching accuracy
            expected = test_case.get('expected_pattern')
            actual = entry.get('pattern_id')
            
            if expected and expected != actual:
                result.add_warning(f"Test {i+1}: Expected pattern '{expected}', got '{actual}'")
            elif actual != "UNCLASSIFIED":
                pattern_matches += 1
        
        # Calculate metrics
        result.add_metric("total_tests", len(test_inputs))
        result.add_metric("pattern_matches", pattern_matches)
        result.add_metric("pattern_match_rate", pattern_matches / len(test_inputs))
        result.add_metric("avg_processing_time", sum(processing_times) / len(processing_times))
        result.add_metric("max_processing_time", max(processing_times))
        result.add_metric("min_processing_time", min(processing_times))
        result.add_metric("avg_confidence", sum(confidence_scores) / len(confidence_scores))
        
        # Test different content categories
        categories = {}
        for test_case in test_inputs:
            category = test_case.get('category', 'unknown')
            categories[category] = categories.get(category, 0) + 1
        
        result.add_detail("categories_tested", categories)
        
        result.complete(True)
        
    except Exception as e:
        result.complete(False, f"Functionality test failed: {e}")


def test_configuration_variants(result: TestResult):
    """Test different digestor configuration variants"""
    try:
        patterns = create_comprehensive_sample_patterns()
        test_content = "My name is Alice and I am 30 years old. You can reach me at alice@test.com"
        
        configurations = [
            ("strict", DigestorConfig(
                case_sensitive_matching=True,
                require_all_keywords=True,
                confidence_threshold=0.8,
                fallback_on_errors=False,
                enable_sentiment_mapping=True,
                pattern_match_threshold=0.8
            )),
            ("lenient", DigestorConfig(
                case_sensitive_matching=False,
                require_all_keywords=False,
                confidence_threshold=0.1,
                fallback_on_errors=True,
                enable_sentiment_mapping=True,
                pattern_match_threshold=0.2
            )),
            ("performance", DigestorConfig(
                enable_sentiment_mapping=False,
                enable_pattern_compaction=False,
                include_processing_metadata=False,
                enable_regex_extraction=False
            )),
            ("comprehensive", DigestorConfig(
                enable_sentiment_mapping=True,
                enable_pattern_compaction=True,
                include_processing_metadata=True,
                include_extraction_details=True,
                enable_regex_extraction=True,
                strict_schema_validation=True
            ))
        ]
        
        config_results = {}
        
        for config_name, config in configurations:
            try:
                digestor = create_digestor(patterns=patterns, config=config)
                digest_result = digestor.digest_entry(test_content)
                
                config_results[config_name] = {
                    "success": digest_result.success,
                    "pattern_matched": digest_result.pattern_matched,
                    "confidence": digest_result.confidence_score,
                    "processing_time": digest_result.processing_time,
                    "variables_extracted": digest_result.variables_extracted,
                    "warnings": len(digest_result.warnings),
                    "storage_recommendation": digest_result.storage_recommendation
                }
                
            except Exception as e:
                config_results[config_name] = {"error": str(e)}
        
        result.add_detail("configuration_results", config_results)
        result.add_metric("configurations_tested", len(configurations))
        result.add_metric("configurations_successful", len([r for r in config_results.values() if "error" not in r]))
        
        result.complete(True)
        
    except Exception as e:
        result.complete(False, f"Configuration test failed: {e}")


def test_error_handling_comprehensive(result: TestResult):
    """Comprehensive error handling and edge case testing"""
    try:
        patterns = create_comprehensive_sample_patterns()
        
        # Test with invalid patterns
        try:
            invalid_patterns = [{"invalid": "pattern"}]
            digestor = create_digestor(patterns=invalid_patterns)
            digest_result = digestor.digest_entry("Test content")
            
            if not digest_result.success or digest_result.compacted_entry.get('pattern_id') == 'UNCLASSIFIED':
                result.add_metric("invalid_patterns_handled", True)
            else:
                result.add_warning("Invalid patterns not properly handled")
        except Exception as e:
            result.add_warning(f"Invalid patterns test error: {e}")
        
        # Test problematic content
        digestor = create_digestor(patterns=patterns)
        
        error_test_cases = [
            ("empty_string", ""),
            ("none_content", None),
            ("very_long", "x" * 50000),
            ("special_chars", "🤖💀👻🎃🔥💯🚀🎯💎🌟"),
            ("malformed_json", '{"invalid": json content}'),
            ("binary_like", "\x00\x01\x02\x03\x04"),
            ("unicode_edge", "café naïve résumé"),
            ("html_tags", "<script>alert('test')</script>"),
            ("sql_injection", "'; DROP TABLE users; --"),
        ]
        
        error_handling_results = {}
        
        for test_name, content in error_test_cases:
            try:
                digest_result = digestor.digest_entry(content)
                error_handling_results[test_name] = {
                    "success": digest_result.success,
                    "pattern_id": digest_result.compacted_entry.get('pattern_id'),
                    "error_message": digest_result.error_message,
                    "warnings": len(digest_result.warnings)
                }
            except Exception as e:
                error_handling_results[test_name] = {"exception": str(e)}
        
        result.add_detail("error_handling_results", error_handling_results)
        result.add_metric("error_cases_tested", len(error_test_cases))
        
        # Test configuration validation
        try:
            invalid_config = DigestorConfig(confidence_threshold=2.0)  # Invalid value
            config_issues = invalid_config.validate_config()
            if config_issues:
                result.add_metric("config_validation_working", True)
            else:
                result.add_warning("Configuration validation not detecting invalid values")
        except Exception as e:
            result.add_warning(f"Configuration validation test error: {e}")
        
        result.complete(True)
        
    except Exception as e:
        result.complete(False, f"Error handling test failed: {e}")


def test_performance_benchmarks(result: TestResult):
    """Comprehensive performance benchmarking"""
    try:
        patterns = create_comprehensive_sample_patterns()
        digestor = create_digestor(patterns=patterns)
        
        # Test different content sizes
        size_tests = [
            (100, 50),    # Small content, many iterations
            (500, 30),    # Medium content
            (1000, 20),   # Large content
            (5000, 10),   # Very large content
            (10000, 5),   # Extremely large content
        ]
        
        performance_results = {}
        
        for content_size, iterations in size_tests:
            content = "This is test content for performance benchmarking. " * (content_size // 50)
            
            times = []
            confidence_scores = []
            
            # Warmup
            for _ in range(3):
                digestor.digest_entry(content)
            
            # Actual measurement
            for _ in range(iterations):
                start_time = time.time()
                digest_result = digestor.digest_entry(content)
                processing_time = time.time() - start_time
                
                times.append(processing_time)
                confidence_scores.append(digest_result.confidence_score)
            
            performance_results[f"size_{content_size}"] = {
                "avg_time": sum(times) / len(times),
                "min_time": min(times),
                "max_time": max(times),
                "avg_confidence": sum(confidence_scores) / len(confidence_scores),
                "iterations": iterations,
                "content_size": len(content)
            }
        
        result.add_detail("performance_results", performance_results)
        
        # Calculate throughput metrics
        best_throughput = 0
        for size_key, perf_data in performance_results.items():
            throughput = perf_data["content_size"] / perf_data["avg_time"]
            performance_results[size_key]["throughput_chars_per_sec"] = throughput
            best_throughput = max(best_throughput, throughput)
        
        result.add_metric("best_throughput_chars_per_sec", best_throughput)
        result.add_metric("performance_test_sizes", len(size_tests))
        
        # Test memory usage (approximate)
        import sys
        
        # Create many digestors to test memory scaling
        digestors = []
        for i in range(10):
            digestors.append(create_digestor(patterns=patterns))
        
        # Process content with all digestors
        test_content = "Memory usage test content"
        for digestor_instance in digestors:
            digestor_instance.digest_entry(test_content)
        
        result.add_metric("memory_scaling_test_completed", True)
        
        result.complete(True)
        
    except Exception as e:
        result.complete(False, f"Performance benchmark failed: {e}")


def test_statistics_and_monitoring(result: TestResult):
    """Test statistics collection and monitoring capabilities"""
    try:
        patterns = create_comprehensive_sample_patterns()
        digestor = create_digestor(patterns=patterns)
        
        # Process various entries to generate statistics
        test_contents = [
            "My name is Bob and I am 25",
            "Email me at bob@test.com",
            "Random unmatched content",
            "I feel happy today",
            "",  # Minimal entry trigger
            "Error in the system",
            "Product feedback: excellent feature",
            "Salary information: $50,000"
        ]
        
        for content in test_contents:
            digestor.digest_entry(content)
        
        # Get comprehensive statistics
        stats = digestor.get_processing_statistics()
        
        # Validate statistics structure
        required_stats = [
            "total_processed", "success_rate", "pattern_match_rate",
            "digestor_version", "patterns_loaded"
        ]
        
        missing_stats = [stat for stat in required_stats if stat not in stats]
        if missing_stats:
            result.complete(False, f"Missing required statistics: {missing_stats}")
            return
        
        result.add_detail("statistics", stats)
        result.add_metric("total_processed", stats["total_processed"])
        result.add_metric("success_rate", stats["success_rate"])
        result.add_metric("pattern_match_rate", stats["pattern_match_rate"])
        
        # Test statistics reset
        initial_total = stats["total_processed"]
        digestor.reset_statistics()
        
        # Process one more entry
        digestor.digest_entry("Reset test")
        new_stats = digestor.get_processing_statistics()
        
        if new_stats["total_processed"] == 1:
            result.add_metric("statistics_reset_working", True)
        else:
            result.add_warning("Statistics reset not working properly")
        
        # Test performance history (if available)
        if hasattr(digestor, 'get_performance_history'):
            try:
                history = digestor.get_performance_history(limit=5)
                result.add_metric("performance_history_entries", len(history))
            except Exception as e:
                result.add_warning(f"Performance history test failed: {e}")
        
        result.complete(True)
        
    except Exception as e:
        result.complete(False, f"Statistics test failed: {e}")


def test_schema_compliance_comprehensive(result: TestResult):
    """Comprehensive schema compliance validation"""
    try:
        patterns = create_comprehensive_sample_patterns()
        digestor = create_digestor(patterns=patterns)
        
        # Test different input types with comprehensive validation
        test_cases = [
            ("string_input", "My name is John Smith and I am 25 years old"),
            ("dict_input", {"raw_ref": "Contact me at john@email.com", "metadata": {"speaker": "alice"}}),
            ("empty_string", ""),
            ("minimal_content", "Hi"),
            ("unicode_content", "名前は田中です"),
            ("long_content", "A" * 5000),
        ]
        
        schema_results = {}
        schema_compliant_count = 0
        
        for test_name, test_input in test_cases:
            digest_result = digestor.digest_entry(test_input)
            entry = digest_result.compacted_entry
            
            # Comprehensive schema validation
            schema_check = {
                "has_required_fields": True,
                "field_types_valid": True,
                "vad_structure_valid": True,
                "metadata_structure_valid": True,
                "issues": []
            }
            
            # Check required IOA v0.1.2 schema fields
            required_fields = ["id", "pattern_id", "metadata", "feeling"]
            missing_fields = [field for field in required_fields if field not in entry]
            
            if missing_fields:
                schema_check["has_required_fields"] = False
                schema_check["issues"].append(f"Missing fields: {missing_fields}")
            
            # Validate field types
            if "id" in entry and not isinstance(entry["id"], str):
                schema_check["field_types_valid"] = False
                schema_check["issues"].append("ID must be string")
            
            if "pattern_id" in entry and not isinstance(entry["pattern_id"], str):
                schema_check["field_types_valid"] = False
                schema_check["issues"].append("pattern_id must be string")
            
            if "metadata" in entry and not isinstance(entry["metadata"], dict):
                schema_check["field_types_valid"] = False
                schema_check["issues"].append("metadata must be dict")
            
            # Validate VAD (Valence-Arousal-Dominance) structure
            feeling = entry.get("feeling", {})
            if not isinstance(feeling, dict):
                schema_check["vad_structure_valid"] = False
                schema_check["issues"].append("feeling must be dict")
            else:
                vad_fields = ["valence", "arousal", "dominance"]
                missing_vad = [field for field in vad_fields if field not in feeling]
                if missing_vad:
                    schema_check["vad_structure_valid"] = False
                    schema_check["issues"].append(f"Missing VAD fields: {missing_vad}")
                
                for field in vad_fields:
                    if field in feeling and not isinstance(feeling[field], (int, float)):
                        schema_check["vad_structure_valid"] = False
                        schema_check["issues"].append(f"VAD field {field} must be numeric")
            
            # Validate metadata structure
            metadata = entry.get("metadata", {})
            if isinstance(metadata, dict):
                if "timestamp" not in metadata:
                    schema_check["metadata_structure_valid"] = False
                    schema_check["issues"].append("metadata missing timestamp")
            
            # Determine overall compliance
            schema_check["compliant"] = (
                schema_check["has_required_fields"] and
                schema_check["field_types_valid"] and
                schema_check["vad_structure_valid"] and
                schema_check["metadata_structure_valid"]
            )
            
            if schema_check["compliant"]:
                schema_compliant_count += 1
            
            schema_results[test_name] = schema_check
        
        result.add_detail("schema_validation_results", schema_results)
        result.add_metric("total_schema_tests", len(test_cases))
        result.add_metric("schema_compliant_count", schema_compliant_count)
        result.add_metric("schema_compliance_rate", schema_compliant_count / len(test_cases))
        
        if schema_compliant_count == len(test_cases):
            result.add_metric("full_schema_compliance", True)
        else:
            result.add_warning(f"Schema compliance issues in {len(test_cases) - schema_compliant_count} test cases")
        
        result.complete(True)
        
    except Exception as e:
        result.complete(False, f"Schema compliance test failed: {e}")


def test_production_deployment_readiness(result: TestResult):
    """Comprehensive production deployment readiness assessment"""
    try:
        # Run production deployment validation
        deployment_report = validate_production_deployment()
        
        result.add_detail("deployment_report", deployment_report)
        result.add_metric("deployment_ready", deployment_report.get("deployment_ready", False))
        result.add_metric("checks_passed", deployment_report.get("checks_passed", 0))
        result.add_metric("checks_failed", deployment_report.get("checks_failed", 0))
        result.add_metric("success_rate", deployment_report.get("success_rate", 0))
        
        # Additional production readiness checks
        production_checks = {
            "import_successful": DIGESTOR_IMPORT_SUCCESS,
            "pattern_validation_available": True,
            "factory_function_available": True,
            "configuration_validation_available": True,
            "statistics_available": True,
            "error_handling_comprehensive": True
        }
        
        # Test critical functionality
        try:
            patterns = create_comprehensive_sample_patterns()[:3]  # Subset for speed
            digestor = create_digestor(patterns=patterns)
            
            # Test basic operations
            test_result = digestor.digest_entry("Production readiness test")
            production_checks["basic_processing"] = test_result.success
            
            # Test statistics
            stats = digestor.get_processing_statistics()
            production_checks["statistics_functional"] = isinstance(stats, dict)
            
            # Test error handling
            error_result = digestor.digest_entry("")
            production_checks["error_handling_functional"] = error_result is not None
            
        except Exception as e:
            production_checks["critical_functionality_error"] = str(e)
            result.add_warning(f"Critical functionality test failed: {e}")
        
        result.add_detail("production_checks", production_checks)
        
        # Calculate overall readiness score
        passed_checks = sum(1 for check in production_checks.values() if check is True)
        total_checks = len([v for v in production_checks.values() if isinstance(v, bool)])
        readiness_score = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        result.add_metric("production_readiness_score", readiness_score)
        
        if deployment_report.get("deployment_ready", False) and readiness_score >= 90:
            result.complete(True)
        else:
            result.complete(False, f"Production readiness insufficient: {readiness_score:.1f}%")
        
    except Exception as e:
        result.complete(False, f"Production readiness test failed: {e}")


def test_integration_capabilities(result: TestResult):
    """Test integration capabilities and component interaction"""
    try:
        patterns = create_comprehensive_sample_patterns()
        
        # Test factory function with different parameters
        integration_tests = {}
        
        # Test basic factory
        try:
            digestor1 = create_digestor(patterns=patterns)
            integration_tests["basic_factory"] = True
        except Exception as e:
            integration_tests["basic_factory"] = False
            result.add_warning(f"Basic factory test failed: {e}")
        
        # Test factory with custom config
        try:
            custom_config = DigestorConfig(confidence_threshold=0.7)
            digestor2 = create_digestor(patterns=patterns, config=custom_config)
            integration_tests["custom_config_factory"] = True
        except Exception as e:
            integration_tests["custom_config_factory"] = False
            result.add_warning(f"Custom config factory test failed: {e}")
        
        # Test factory with no patterns
        try:
            digestor3 = create_digestor(patterns=[])
            integration_tests["empty_patterns_factory"] = True
        except Exception as e:
            integration_tests["empty_patterns_factory"] = False
            result.add_warning(f"Empty patterns factory test failed: {e}")
        
        # Test context preservation
        try:
            digestor = create_digestor(patterns=patterns)
            context = {
                "speaker": "alice",
                "tone": "excited",
                "session_id": "test_session_123",
                "thread_id": "thread_456"
            }
            
            digest_result = digestor.digest_entry("My name is Alice Johnson", context)
            metadata = digest_result.compacted_entry.get('metadata', {})
            
            context_preserved = all(
                metadata.get(key) == value for key, value in context.items()
            )
            
            integration_tests["context_preservation"] = context_preserved
            
        except Exception as e:
            integration_tests["context_preservation"] = False
            result.add_warning(f"Context preservation test failed: {e}")
        
        result.add_detail("integration_tests", integration_tests)
        result.add_metric("integration_tests_passed", sum(integration_tests.values()))
        result.add_metric("integration_tests_total", len(integration_tests))
        
        result.complete(True)
        
    except Exception as e:
        result.complete(False, f"Integration test failed: {e}")


def run_interactive_demo():
    """Enhanced interactive demonstration of digestor capabilities"""
    print("\n" + "="*80)
    print("🎯 IOA DIGESTOR MODULE - INTERACTIVE DEMONSTRATION")
    print("="*80)
    
    try:
        patterns = create_comprehensive_sample_patterns()
        digestor = create_digestor(patterns=patterns)
        
        print(f"\n🔧 Digestor initialized with {len(patterns)} patterns:")
        for pattern in patterns:
            keywords_str = ", ".join(pattern['keywords'][:3])
            if len(pattern['keywords']) > 3:
                keywords_str += f", ... (+{len(pattern['keywords'])-3} more)"
            print(f"   📋 {pattern['pattern_id']}: {keywords_str}")
        
        print("\n💡 USAGE EXAMPLES:")
        examples = [
            "My name is Jane and I am 28 years old",
            "You can reach me at jane@email.com or call 555-1234",
            "I work at TechCorp as a Software Engineer",
            "I live in San Francisco, California",
            "I'm feeling excited about the new features!",
            "My salary is $65,000 per year",
            "I'm having trouble with the login system",
            "The new dashboard is really user-friendly"
        ]
        
        for example in examples:
            print(f"   💬 '{example}'")
        
        print("\n🚀 INTERACTIVE MODE")
        print("Enter text to process, or type 'help' for commands")
        print("Commands: 'help', 'stats', 'patterns', 'config', 'quit'")
        print("-" * 60)
        
        session_stats = {
            "entries_processed": 0,
            "patterns_matched": 0,
            "avg_confidence": 0.0,
            "processing_times": []
        }
        
        while True:
            try:
                user_input = input("\n🔸 ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                elif user_input.lower() == 'help':
                    print("\n📖 HELP:")
                    print("   • Enter any text to process it through the digestor")
                    print("   • 'stats' - Show processing statistics")
                    print("   • 'patterns' - List available patterns")
                    print("   • 'config' - Show digestor configuration")
                    print("   • 'quit' - Exit the demo")
                    continue
                elif user_input.lower() == 'stats':
                    stats = digestor.get_processing_statistics()
                    print(f"\n📊 DIGESTOR STATISTICS:")
                    print(f"   • Total processed: {stats.get('total_processed', 0)}")
                    print(f"   • Success rate: {stats.get('success_rate', 0):.2%}")
                    print(f"   • Pattern match rate: {stats.get('pattern_match_rate', 0):.2%}")
                    print(f"   • Average confidence: {stats.get('avg_confidence_score', 0):.3f}")
                    
                    print(f"\n📈 SESSION STATISTICS:")
                    print(f"   • Entries processed: {session_stats['entries_processed']}")
                    print(f"   • Patterns matched: {session_stats['patterns_matched']}")
                    if session_stats['processing_times']:
                        avg_time = sum(session_stats['processing_times']) / len(session_stats['processing_times'])
                        print(f"   • Average processing time: {avg_time:.4f}s")
                    continue
                elif user_input.lower() == 'patterns':
                    print(f"\n📋 AVAILABLE PATTERNS ({len(patterns)}):")
                    for i, pattern in enumerate(patterns, 1):
                        print(f"   {i:2d}. {pattern['pattern_id']}")
                        print(f"       Keywords: {', '.join(pattern['keywords'])}")
                        print(f"       Schema: {', '.join(pattern['schema'])}")
                    continue
                elif user_input.lower() == 'config':
                    config = digestor.config
                    print(f"\n⚙️  DIGESTOR CONFIGURATION:")
                    print(f"   • Confidence threshold: {config.confidence_threshold}")
                    print(f"   • Pattern match threshold: {config.pattern_match_threshold}")
                    print(f"   • Sentiment mapping: {config.enable_sentiment_mapping}")
                    print(f"   • Pattern compaction: {config.enable_pattern_compaction}")
                    print(f"   • Fallback on errors: {config.fallback_on_errors}")
                    print(f"   • Case sensitive: {config.case_sensitive_matching}")
                    continue
                elif not user_input:
                    continue
                
                # Process the input
                start_time = time.time()
                digest_result = digestor.digest_entry(user_input)
                processing_time = time.time() - start_time
                
                # Update session statistics
                session_stats["entries_processed"] += 1
                session_stats["processing_times"].append(processing_time)
                if digest_result.pattern_matched:
                    session_stats["patterns_matched"] += 1
                
                # Display comprehensive results
                print(f"\n📋 PROCESSING RESULT:")
                print(f"   🎯 Pattern: {digest_result.compacted_entry.get('pattern_id')}")
                print(f"   ✅ Success: {digest_result.success}")
                print(f"   📊 Confidence: {digest_result.confidence_score:.3f}")
                print(f"   ⚡ Processing time: {processing_time:.4f}s")
                print(f"   📦 Storage tier: {digest_result.storage_recommendation}")
                
                if digest_result.variables_extracted > 0:
                    variables = digest_result.compacted_entry.get('variables', {})
                    print(f"   🔍 Variables extracted ({digest_result.variables_extracted}):")
                    for key, value in variables.items():
                        if value != "unknown":
                            print(f"      • {key}: {value}")
                
                feeling = digest_result.compacted_entry.get('feeling', {})
                if any(abs(v) > 0.1 for v in feeling.values()):
                    print(f"   🎭 Sentiment (VAD):")
                    print(f"      • Valence: {feeling.get('valence', 0):.2f}")
                    print(f"      • Arousal: {feeling.get('arousal', 0):.2f}")
                    print(f"      • Dominance: {feeling.get('dominance', 0):.2f}")
                
                if digest_result.warnings:
                    print(f"   ⚠️  Warnings:")
                    for warning in digest_result.warnings:
                        print(f"      • {warning}")
                
                if digest_result.error_message:
                    print(f"   ❌ Error: {digest_result.error_message}")
            
            except KeyboardInterrupt:
                print("\n\n👋 Demo interrupted by user")
                break
            except EOFError:
                print("\n\n👋 Demo ended")
                break
            except Exception as e:
                print(f"\n💥 Demo error: {e}")
                print("   🔧 Continuing demo...")
        
        # Final session summary
        print(f"   • Total entries processed: {session_stats['entries_processed']}")
        print(f"   • Patterns matched: {session_stats['patterns_matched']}")
        if session_stats['entries_processed'] > 0:
            match_rate = session_stats['patterns_matched'] / session_stats['entries_processed']
            print(f"   • Pattern match rate: {match_rate:.2%}")
        
        if session_stats['processing_times']:
            avg_time = sum(session_stats['processing_times']) / len(session_stats['processing_times'])
            print(f"   • Average processing time: {avg_time:.4f}s")
            print(f"   • Total processing time: {sum(session_stats['processing_times']):.4f}s")
        
        # Final digestor statistics
        final_stats = digestor.get_processing_statistics()
        print(f"\n📈 DIGESTOR FINAL STATISTICS:")
        print(f"   • Lifetime total processed: {final_stats.get('total_processed', 0)}")
        print(f"   • Lifetime success rate: {final_stats.get('success_rate', 0):.2%}")
        print(f"   • Lifetime pattern match rate: {final_stats.get('pattern_match_rate', 0):.2%}")
        
    except Exception as e:
        print(f"\n💥 Demo initialization failed: {e}")
        print("🔧 Please check digestor module installation and configuration")


def main():
    """Run comprehensive digestor testing and demonstration suite"""
    print("🧠 IOA DIGESTOR MODULE - COMPREHENSIVE TESTING SUITE v0.1.2")
    print("="*80)
    print(f"🕐 Test session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"📦 Digestor import: {'✅ SUCCESS' if DIGESTOR_IMPORT_SUCCESS else '❌ FAILED'}")
    
    if not DIGESTOR_IMPORT_SUCCESS:
        print(f"❌ Cannot proceed without digestor module")
        print(f"🔧 Error details: {DIGESTOR_IMPORT_ERROR}")
        return 1
    
    runner = TestRunner()
    
    try:
        # Define comprehensive test suite
        test_suite = [
            ("Pattern Validation", test_pattern_validation_comprehensive),
            ("Digestor Functionality", test_digestor_functionality_comprehensive),
            ("Configuration Variants", test_configuration_variants),
            ("Error Handling", test_error_handling_comprehensive),
            ("Performance Benchmarks", test_performance_benchmarks),
            ("Statistics & Monitoring", test_statistics_and_monitoring),
            ("Schema Compliance", test_schema_compliance_comprehensive),
            ("Production Readiness", test_production_deployment_readiness),
            ("Integration Capabilities", test_integration_capabilities),
        ]
        
        print(f"\n🚀 Running {len(test_suite)} comprehensive test suites...")
        print("-" * 80)
        
        # Run all test suites
        for test_name, test_func in test_suite:
            runner.run_test(test_name, test_func)
        
        # Generate comprehensive summary
        summary = runner.get_summary()
        
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("="*80)
        print(f"🎯 Total tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed_tests']}")
        print(f"❌ Failed: {summary['failed_tests']}")
        print(f"📈 Success rate: {summary['success_rate']:.1f}%")
        print(f"⏱️  Total duration: {summary['total_duration']:.2f}s")
        print(f"⚡ Average test duration: {summary['average_test_duration']:.3f}s")
        
        # Detailed test breakdown
        print(f"\n📋 DETAILED TEST BREAKDOWN:")
        for result in runner.test_results:
            status_icon = "✅" if result.success else "❌"
            duration = result.metrics.get('duration', 0)
            print(f"   {status_icon} {result.test_name}: {duration:.3f}s")
            
            if result.warnings:
                for warning in result.warnings[:2]:  # Limit warnings shown
                    print(f"      ⚠️  {warning}")
                if len(result.warnings) > 2:
                    print(f"      ⚠️  ... and {len(result.warnings)-2} more warnings")
            
            if not result.success and result.error_message:
                print(f"      💥 {result.error_message}")
        
        # Performance insights
        perf_results = [r for r in runner.test_results if "Performance" in r.test_name]
        if perf_results:
            perf_result = perf_results[0]
            if "best_throughput_chars_per_sec" in perf_result.metrics:
                throughput = perf_result.metrics["best_throughput_chars_per_sec"]
                print(f"\n⚡ PERFORMANCE INSIGHTS:")
                print(f"   • Best throughput: {throughput:,.0f} chars/sec")
        
        # Production readiness assessment
        prod_results = [r for r in runner.test_results if "Production" in r.test_name]
        if prod_results:
            prod_result = prod_results[0]
            readiness_score = prod_result.metrics.get("production_readiness_score", 0)
            print(f"\n🏭 PRODUCTION READINESS:")
            print(f"   • Readiness score: {readiness_score:.1f}%")
            
            if readiness_score >= 90:
                print(f"   🚀 Ready for production deployment!")
            elif readiness_score >= 75:
                print(f"   ⚠️  Nearly ready - minor issues to resolve")
            else:
                print(f"   🛠️  Significant issues - not ready for production")
        
        # Final recommendations
        print(f"\n🎯 RECOMMENDATIONS:")
        
        if summary['success_rate'] >= 95:
            print(f"   ✅ Excellent test results - system is highly reliable")
            print(f"   🚀 Ready for production deployment")
            print(f"   📊 Consider enabling monitoring in production")
        elif summary['success_rate'] >= 80:
            print(f"   ⚠️  Good test results with some issues")
            print(f"   🔧 Review failed tests and address issues")
            print(f"   📋 Consider additional testing before deployment")
        else:
            print(f"   ❌ Significant issues detected")
            print(f"   🛠️  Address critical failures before proceeding")
            print(f"   🔍 Review error messages and system configuration")
        
        # Offer interactive demo
        print(f"\n🎮 INTERACTIVE DEMO:")
        try:
            if summary['success_rate'] >= 70:
                choice = input("   Would you like to run the interactive demo? (y/n): ").strip().lower()
                if choice in ['y', 'yes']:
                    run_interactive_demo()
            else:
                print("   ⚠️  Interactive demo skipped due to test failures")
        except (EOFError, KeyboardInterrupt):
            print("   ⏭️  Skipping interactive demo...")
        
        print(f"\n🎉 Testing and demonstration complete!")
        
        # Return appropriate exit code
        return 0 if summary['success_rate'] >= 80 else 1
        
    except Exception as e:
        print(f"\n💥 Critical testing suite error: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    exit(main())

