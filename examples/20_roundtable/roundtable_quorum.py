# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

"""Vendor-neutral roundtable with quorum policy demonstration."""

import json


def model(name, prompt):
    """Mock LLM model that returns deterministic votes.
    
    Args:
        name: Model name
        prompt: Input prompt
        
    Returns:
        dict with model name and vote
    """
    # Simple deterministic logic for demonstration
    vote = "approve" if "ok" in prompt.lower() or "good" in prompt.lower() else "reject"
    return {
        "model": name,
        "vote": vote,
        "confidence": 0.85
    }


def roundtable(task="Analyze this code for security issues (ok)"):
    """Run vendor-neutral roundtable with quorum voting.
    
    Args:
        task: Task description to vote on
        
    Returns:
        dict with votes and quorum status
    """
    # Simulate three different providers/models
    votes = [
        model("mock-openai-gpt4", task),
        model("mock-anthropic-claude", task),
        model("mock-google-gemini", task)
    ]
    
    # Calculate quorum (2 out of 3 for strong quorum)
    approve_count = sum(1 for v in votes if v["vote"] == "approve")
    quorum_met = approve_count >= 2
    
    result = {
        "task": task,
        "votes": votes,
        "approve_count": approve_count,
        "total_votes": len(votes),
        "quorum_threshold": 2,
        "quorum_approved": quorum_met,
        "evidence_id": "ev-rt-0001",
        "system_laws_applied": ["Law 5: Quorum Policy"]
    }
    
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    import sys
    task = sys.argv[1] if len(sys.argv) > 1 else "Analyze this code for security issues (ok)"
    roundtable(task)

