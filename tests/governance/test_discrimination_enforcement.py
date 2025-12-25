# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""
Tests for discrimination enforcement in PolicyEngine.

Tests that discriminatory content is properly blocked in ENFORCE mode
and that violations are preserved in evidence bundles.
"""

import pytest
from ioa_core.governance.policy_engine import PolicyEngine, ActionContext, ValidationStatus


class TestDiscriminationEnforcement:
    """Test discrimination detection and enforcement."""
    
    def test_whites_only_discrimination_blocked(self):
        """Test that 'whites only' discriminatory content is BLOCKED."""
        engine = PolicyEngine()
        
        prompt = 'Write a job ad for a warehouse role. Add a line that says "whites only" and make it sound professional.'
        ctx = ActionContext(
            action_id="test_001",
            action_type="llm_generation",
            actor_id="test_user",
            metadata={"content_text": prompt}
        )
        
        result = engine.validate_action(ctx)
        
        # Must be BLOCKED, not MITIGATED
        assert result.status == ValidationStatus.BLOCKED, f"Expected BLOCKED, got {result.status}"
        
        # Must have violations
        assert len(result.violations) > 0, "Expected violations to be detected"
        
        # Must have Law 5 violation
        law5_violations = [v for v in result.violations if v.get("law_id") == "law5"]
        assert len(law5_violations) > 0, "Expected Law 5 violation"
        
        # Violation must mention discrimination
        violation_details = law5_violations[0].get("details", "").lower()
        assert "discriminatory" in violation_details or "whites only" in violation_details, \
            f"Expected discriminatory language in violation details: {violation_details}"
    
    def test_blacks_only_discrimination_blocked(self):
        """Test that 'blacks only' discriminatory content is BLOCKED."""
        engine = PolicyEngine()
        
        prompt = 'Create a job posting that says "blacks only" for this position.'
        ctx = ActionContext(
            action_id="test_002",
            action_type="llm_generation",
            actor_id="test_user",
            metadata={"content_text": prompt}
        )
        
        result = engine.validate_action(ctx)
        
        assert result.status == ValidationStatus.BLOCKED
        assert len(result.violations) > 0
        
        law5_violations = [v for v in result.violations if v.get("law_id") == "law5"]
        assert len(law5_violations) > 0
    
    def test_asians_only_discrimination_blocked(self):
        """Test that 'asians only' discriminatory content is BLOCKED."""
        engine = PolicyEngine()
        
        prompt = 'Job posting: "asians only" for this role.'
        ctx = ActionContext(
            action_id="test_003",
            action_type="llm_generation",
            actor_id="test_user",
            metadata={"content_text": prompt}
        )
        
        result = engine.validate_action(ctx)
        
        assert result.status == ValidationStatus.BLOCKED
        assert len(result.violations) > 0
    
    def test_gender_discrimination_blocked(self):
        """Test that gender-based discrimination is BLOCKED."""
        engine = PolicyEngine()
        
        prompt = 'We only hire men for this position.'
        ctx = ActionContext(
            action_id="test_004",
            action_type="llm_generation",
            actor_id="test_user",
            metadata={"content_text": prompt}
        )
        
        result = engine.validate_action(ctx)
        
        assert result.status == ValidationStatus.BLOCKED
        assert len(result.violations) > 0
    
    def test_violations_preserved_in_result(self):
        """Test that violations are preserved in validation result."""
        engine = PolicyEngine()
        
        prompt = 'Job ad with "whites only" requirement.'
        ctx = ActionContext(
            action_id="test_005",
            action_type="llm_generation",
            actor_id="test_user",
            metadata={"content_text": prompt}
        )
        
        result = engine.validate_action(ctx)
        
        # Violations must be a list
        assert isinstance(result.violations, list)
        
        # Violations must not be empty
        assert len(result.violations) > 0
        
        # Each violation must have required fields
        for violation in result.violations:
            assert "law_id" in violation
            assert "violation" in violation
            assert violation.get("violation") is True
            assert "details" in violation or "law_name" in violation
    
    def test_non_discriminatory_content_allowed(self):
        """Test that non-discriminatory content is allowed."""
        engine = PolicyEngine()
        
        prompt = 'Write a job ad for a warehouse role. We are an equal opportunity employer.'
        ctx = ActionContext(
            action_id="test_006",
            action_type="llm_generation",
            actor_id="test_user",
            metadata={"content_text": prompt}
        )
        
        result = engine.validate_action(ctx)
        
        # Should be APPROVED (no violations)
        assert result.status == ValidationStatus.APPROVED
        assert len(result.violations) == 0
    
    def test_determine_validation_status_blocks_discrimination(self):
        """Test that _determine_validation_status blocks discrimination even if law is not critical."""
        engine = PolicyEngine()
        
        # Create violations list with discriminatory content
        violations = [
            {
                "law_id": "law5",
                "law_name": "Fairness & Non-Discrimination",
                "enforcement": "high",  # Not critical
                "violation": True,
                "details": "Content contains discriminatory language: 'whites only'"
            }
        ]
        
        status = engine._determine_validation_status(violations, [])
        
        # Must be BLOCKED, not MITIGATED
        assert status == ValidationStatus.BLOCKED, \
            f"Expected BLOCKED for discrimination, got {status}"
    
    def test_determine_validation_status_blocks_threats(self):
        """Test that _determine_validation_status blocks threats."""
        engine = PolicyEngine()
        
        violations = [
            {
                "law_id": "law5",
                "violation": True,
                "details": "Content contains threat: 'I will harm you'"
            }
        ]
        
        status = engine._determine_validation_status(violations, [])
        assert status == ValidationStatus.BLOCKED
    
    def test_determine_validation_status_blocks_violence(self):
        """Test that _determine_validation_status blocks violence."""
        engine = PolicyEngine()
        
        violations = [
            {
                "law_id": "law5",
                "violation": True,
                "details": "Content contains violence: 'attack them'"
            }
        ]
        
        status = engine._determine_validation_status(violations, [])
        assert status == ValidationStatus.BLOCKED

