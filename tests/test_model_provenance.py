# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.

from ioa_core.evidence import EvidenceBundle
from ioa_core.governance.audit_chain import AuditChain


def test_evidence_bundle_records_model_provenance() -> None:
    bundle = EvidenceBundle(bundle_id="bundle-test")
    bundle.add_model_provenance(
        {
            "provider": "openai",
            "model_name": "gpt-4o-mini",
            "temperature": 0.2,
            "prompt_tokens": 12,
            "completion_tokens": 7,
        }
    )

    assert len(bundle.model_provenance) == 1
    entry = bundle.model_provenance[0]
    assert entry["provider"] == "openai"
    assert entry["model_name"] == "gpt-4o-mini"
    assert entry["model_id"] == "gpt-4o-mini"
    assert entry["input_token_count"] == 12
    assert entry["output_token_count"] == 7


def test_audit_chain_adds_model_provenance_when_provider_and_model_are_present(tmp_path) -> None:
    log_path = tmp_path / "audit.jsonl"
    chain = AuditChain(str(log_path))

    entry = chain.log(
        "llm_call",
        {
            "provider": "anthropic",
            "model": "claude-3-haiku",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            "latency_ms": 123.4,
        },
    )

    assert "model_provenance" in entry["data"]
    assert entry["data"]["model_provenance"][0]["provider"] == "anthropic"
    assert entry["data"]["model_provenance"][0]["model_name"] == "claude-3-haiku"
    assert entry["data"]["model_provenance"][0]["input_token_count"] == 10
    assert entry["data"]["model_provenance"][0]["output_token_count"] == 5
    assert entry["data"]["model_provenance"][0]["total_token_count"] == 15
