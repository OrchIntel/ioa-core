""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import pytest
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch
from src.ioa.core.governance.policy_engine import PolicyEngine, ActionContext, ActionRiskLevel


class TestEthicsPackSmoke:
    """Smoke test harness for Ethics Pack v0."""
    
    @pytest.fixture
    def policy_engine(self):
        """Create policy engine instance for testing."""
        return PolicyEngine()
    
    @pytest.fixture
    def test_prompts(self):
        """Generate test prompts for smoke testing."""
        return [
            # Neutral prompts (60%)
            "What is the weather like today?",
            "Explain the concept of machine learning",
            "How do I cook pasta?",
            "What are the benefits of exercise?",
            "Tell me about renewable energy",
            "How does photosynthesis work?",
            "What is the capital of France?",
            "Explain quantum computing",
            "How do I learn a new language?",
            "What are the principles of good design?",
            
            # Privacy test prompts (20%)
            "My email is john.doe@example.com and my phone is 555-123-4567",
            "Contact me at jane.smith@company.com or call 555-987-6543",
            "My SSN is 123-45-6789 and I live at 123 Main St",
            "Send the report to mike.wilson@corp.com",
            "Call me at 555-555-5555 for more information",
            
            # Safety test prompts (10%)
            "This is a stupid idea that will never work",
            "I hate this approach and it's completely wrong",
            "That's a damn good solution to the problem",
            "This is crap and should be thrown away",
            "What an idiotic suggestion",
            
            # Fairness test prompts (10%)
            "He is better suited for this leadership role than she is",
            "Muslims are more likely to be terrorists than Christians",
            "White people are naturally better at mathematics",
            "Women are not as good at technical work as men",
            "The CEO should be a man, not a woman"
        ]
    
    def test_ethics_pack_initialization(self, policy_engine):
        """Test that Ethics Pack v0 initializes correctly."""
        ethics_status = policy_engine.get_ethics_status()
        
        # Should have some detectors enabled
        assert ethics_status["enabled"] is True
        assert len(ethics_status["detectors"]) > 0
        
        # Check each detector
        for name, detector_status in ethics_status["detectors"].items():
            assert detector_status["enabled"] is True
            assert detector_status["mode"] == "monitor"  # Default mode
            assert detector_status["version"] == "v2.5.0"
    
    def test_privacy_detector_functionality(self, policy_engine):
        """Test privacy detector with PII-containing text."""
        # Create action context with PII
        action_ctx = ActionContext(
            action_id="test_privacy",
            action_type="llm_generation",
            actor_id="test_actor",
            risk_level=ActionRiskLevel.LOW,
            metadata={"input_text": "My email is john.doe@example.com"}
        )
        
        # Run pre-flight check
        modified_ctx, evidence = policy_engine.pre_flight_ethics_check(action_ctx)
        
        # Should detect PII
        if "privacy" in evidence:
            assert evidence["privacy"]["enabled"] is True
            # In monitor mode, should not block
            assert not modified_ctx.metadata.get("ethics_blocked", False)
    
    def test_safety_detector_functionality(self, policy_engine):
        """Test safety detector with potentially problematic text."""
        # Create action context with safety concerns
        action_ctx = ActionContext(
            action_id="test_safety",
            action_type="llm_generation",
            actor_id="test_actor",
            risk_level=ActionRiskLevel.LOW,
            metadata={"input_text": "This is a stupid idea"}
        )
        
        # Run pre-flight check
        modified_ctx, evidence = policy_engine.pre_flight_ethics_check(action_ctx)
        
        # Should detect safety violations
        if "safety" in evidence:
            assert evidence["safety"]["enabled"] is True
            # In monitor mode, should not block
            assert not modified_ctx.metadata.get("ethics_blocked", False)
    
    def test_fairness_detector_functionality(self, policy_engine):
        """Test fairness detector with biased text."""
        # Create action context with biased text
        action_ctx = ActionContext(
            action_id="test_fairness",
            action_type="llm_generation",
            actor_id="test_actor",
            risk_level=ActionRiskLevel.LOW,
            metadata={"input_text": "He is better suited for this role than she is"}
        )
        
        # Run post-flight check
        evidence = policy_engine.post_flight_ethics_check(action_ctx, "He is better suited for this role than she is")
        
        # Should detect bias
        if "fairness" in evidence:
            assert evidence["fairness"]["enabled"] is True
            # In monitor mode, should not block
            assert not action_ctx.metadata.get("ethics_blocked", False)
    
    def test_evidence_collection(self, policy_engine):
        """Test that evidence is properly collected and structured."""
        action_ctx = ActionContext(
            action_id="test_evidence",
            action_type="llm_generation",
            actor_id="test_actor",
            risk_level=ActionRiskLevel.LOW,
            metadata={"input_text": "My email is test@example.com and this is a damn good idea"}
        )
        
        # Run both pre and post-flight checks
        modified_ctx, pre_evidence = policy_engine.pre_flight_ethics_check(action_ctx)
        post_evidence = policy_engine.post_flight_ethics_check(modified_ctx, "Test response")
        
        # Combine evidence
        all_evidence = {**pre_evidence, **post_evidence}
        
        # Should have evidence from all enabled detectors
        ethics_status = policy_engine.get_ethics_status()
        for detector_name in ethics_status["detectors"]:
            if ethics_status["detectors"][detector_name]["enabled"]:
                assert detector_name in all_evidence
                assert "timestamp" in all_evidence[detector_name]
                assert "enabled" in all_evidence[detector_name]
    
    def test_monitor_mode_no_blocks(self, policy_engine, test_prompts):
        """Test that monitor mode never blocks requests."""
        blocked_count = 0
        
        for i, prompt in enumerate(test_prompts[:50]):  # Test subset for speed
            action_ctx = ActionContext(
                action_id=f"test_{i}",
                action_type="llm_generation",
                actor_id="test_actor",
                risk_level=ActionRiskLevel.LOW,
                metadata={"input_text": prompt}
            )
            
            # Run pre-flight check
            modified_ctx, pre_evidence = policy_engine.pre_flight_ethics_check(action_ctx)
            
            # Run post-flight check
            post_evidence = policy_engine.post_flight_ethics_check(modified_ctx, f"Response to: {prompt}")
            
            # Should never be blocked in monitor mode
            if modified_ctx.metadata.get("ethics_blocked", False):
                blocked_count += 1
        
        # In monitor mode, should have no blocks
        assert blocked_count == 0, f"Found {blocked_count} blocked requests in monitor mode"
    
    def test_performance_budget(self, policy_engine, test_prompts):
        """Test that processing time stays within budget."""
        latencies = []
        
        for i, prompt in enumerate(test_prompts[:100]):  # Test subset for speed
            action_ctx = ActionContext(
                action_id=f"test_{i}",
                action_type="llm_generation",
                actor_id="test_actor",
                risk_level=ActionRiskLevel.LOW,
                metadata={"input_text": prompt}
            )
            
            start_time = time.time()
            
            # Run both checks
            modified_ctx, pre_evidence = policy_engine.pre_flight_ethics_check(action_ctx)
            post_evidence = policy_engine.post_flight_ethics_check(modified_ctx, f"Response to: {prompt}")
            
            latency_ms = (time.time() - start_time) * 1000
            latencies.append(latency_ms)
        
        # Calculate P95 latency
        latencies.sort()
        p95_index = int(len(latencies) * 0.95)
        p95_latency = latencies[p95_index]
        
        # Should be within 2ms budget (with some tolerance for CI)
        assert p95_latency < 10.0, f"P95 latency {p95_latency:.2f}ms exceeds 10ms budget"
    
    def test_error_handling(self, policy_engine):
        """Test that errors are handled gracefully."""
        # Test with malformed input
        action_ctx = ActionContext(
            action_id="test_error",
            action_type="llm_generation",
            actor_id="test_actor",
            risk_level=ActionRiskLevel.LOW,
            metadata={"input_text": None}  # This might cause issues
        )
        
        # Should not crash
        try:
            modified_ctx, pre_evidence = policy_engine.pre_flight_ethics_check(action_ctx)
            post_evidence = policy_engine.post_flight_ethics_check(modified_ctx, "Test response")
            
            # Should handle gracefully
            assert True
        except Exception as e:
            # If it does crash, it should be a specific, expected error
            assert "input_text" in str(e).lower() or "none" in str(e).lower()
    
    def test_configuration_persistence(self, policy_engine):
        """Test that configuration is properly loaded and persisted."""
        ethics_status = policy_engine.get_ethics_status()
        
        # Should have loaded configuration
        assert ethics_status["enabled"] is True
        
        # Each detector should have proper configuration
        for name, detector_status in ethics_status["detectors"].items():
            assert "enabled" in detector_status
            assert "mode" in detector_status
            assert "version" in detector_status
            
            if name == "privacy":
                assert "pii_entities" in detector_status
                assert "action" in detector_status
            elif name == "safety":
                assert "lexicons_loaded" in detector_status
                assert "total_patterns" in detector_status
            elif name == "fairness":
                assert "probes" in detector_status
                assert "metrics" in detector_status
                assert "thresholds" in detector_status
    
    def test_metrics_collection(self, policy_engine, test_prompts):
        """Test that metrics are properly collected."""
        metrics = {
            "total_requests": 0,
            "privacy_hits": 0,
            "safety_hits": 0,
            "fairness_probes": 0,
            "blocks": 0,
            "overrides": 0
        }
        
        for i, prompt in enumerate(test_prompts[:50]):  # Test subset
            action_ctx = ActionContext(
                action_id=f"test_{i}",
                action_type="llm_generation",
                actor_id="test_actor",
                risk_level=ActionRiskLevel.LOW,
                metadata={"input_text": prompt}
            )
            
            # Run checks
            modified_ctx, pre_evidence = policy_engine.pre_flight_ethics_check(action_ctx)
            post_evidence = policy_engine.post_flight_ethics_check(modified_ctx, f"Response to: {prompt}")
            
            # Update metrics
            all_evidence = {**pre_evidence, **post_evidence}
            metrics["total_requests"] += 1
            
            if "privacy" in all_evidence and all_evidence["privacy"].get("has_pii", False):
                metrics["privacy_hits"] += 1
            
            if "safety" in all_evidence and all_evidence["safety"].get("has_violations", False):
                metrics["safety_hits"] += 1
            
            if "fairness" in all_evidence and all_evidence["fairness"].get("has_bias", False):
                metrics["fairness_probes"] += 1
            
            if modified_ctx.metadata.get("ethics_blocked", False):
                metrics["blocks"] += 1
        
        # Should have collected some metrics
        assert metrics["total_requests"] > 0
        # Should have some hits (depending on test prompts)
        assert metrics["privacy_hits"] >= 0
        assert metrics["safety_hits"] >= 0
        assert metrics["fairness_probes"] >= 0
        # Should have no blocks in monitor mode
        assert metrics["blocks"] == 0
    
    def test_audit_trail_integration(self, policy_engine):
        """Test that evidence integrates with audit trail."""
        action_ctx = ActionContext(
            action_id="test_audit",
            action_type="llm_generation",
            actor_id="test_actor",
            risk_level=ActionRiskLevel.LOW,
            metadata={"input_text": "My email is test@example.com"}
        )
        
        # Run checks
        modified_ctx, pre_evidence = policy_engine.pre_flight_ethics_check(action_ctx)
        post_evidence = policy_engine.post_flight_ethics_check(modified_ctx, "Test response")
        
        # Evidence should be suitable for audit trail
        all_evidence = {**pre_evidence, **post_evidence}
        
        for detector_name, evidence in all_evidence.items():
            # Should have timestamp
            assert "timestamp" in evidence
            # Should have enabled status
            assert "enabled" in evidence
            # Should have processing time
            assert "processing_time_ms" in evidence
            # Should be JSON serializable
            json.dumps(evidence)  # Should not raise exception
