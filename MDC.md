**Version:** v2.5.0  
**Last-Updated:** 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# MDC (Minimum Dev Contract) - IOA Ecosystem

**Last Updated:** 2025-01-06  
**Enforcement:** Mandatory across all IOA repositories

## 🚨 SDK-Only Contract

**CRITICAL:** All LLM, Memory Fabric, PolicyEngine, and Audit access MUST go through `ioa-sdk`. Direct imports of providers (OpenAI, Anthropic, Vertex AI, etc.) are **FORBIDDEN**.

### ❌ Forbidden Direct Imports
```python
# DON'T DO THIS - These are forbidden:
import openai
import anthropic
import vertexai
from langchain import LLMChain
from transformers import pipeline
```

### ✅ Required SDK Usage
```python
# DO THIS - Use ioa-sdk:
from ioa_sdk import llm, memory_fabric, policy_engine, audit
from ioa_sdk.llm import generate_text, chat_completion
from ioa_sdk.memory_fabric import store, retrieve, search
from ioa_sdk.policy_engine import validate_action
from ioa_sdk.audit import log_action
```

## 📊 LLM Usage Matrix

| Layer | LLM Required? | Examples | Governance Check |
|-------|---------------|----------|------------------|
| **Governance & Plumbing** | No | PHI redaction, jurisdiction checks | `PolicyEngine.enforce()` |
| **Understanding & Gen** | Yes | Explainers, dialog, content summaries | `ioa_sdk.llm` (with audit_id) |
| **Hybrid** | Optional | FHIR transforms, report formatting | Mock: simulate • Live: `sdk.llm` |

## 🔧 Implementation Guidelines

### 1. LLM Integration
```python
# Always use ioa-sdk for LLM calls
from ioa_sdk.llm import generate_text

# With proper audit tracking
response = generate_text(
    prompt="Your prompt here",
    model="gpt-4",
    audit_id=audit_id,
    user_id=user_id
)
```

### 2. Memory Fabric Access
```python
# Always use ioa-sdk for memory operations
from ioa_sdk.memory_fabric import store, retrieve

# Store conversation
store(
    content=conversation_data,
    metadata={"user_id": user_id, "session": session_id},
    memory_type="conversation"
)

# Retrieve context
context = retrieve(query="user preferences", limit=10)
```

### 3. Policy Enforcement
```python
# Always validate actions through policy engine
from ioa_sdk.policy_engine import validate_action

result = validate_action(
    action="fetch_user_data",
    context={"user_id": user_id, "resource": "profile"},
    user_id=user_id
)

if not result["allowed"]:
    # Use ExplainerBundle for user-friendly error
    from ioa_sdk.explain import create_explainer
    explainer = create_explainer("fetch_user_data", result)
    return explainer.get_user_facing_message()
```

### 4. Audit Logging
```python
# Always log actions through audit system
from ioa_sdk.audit import log_action

log_action(
    service="user_service",
    action="fetch_profile",
    user_id=user_id,
    inputs={"user_id": user_id},
    result={"success": True, "profile": profile_data},
    audit_id=audit_id
)
```

## 🛡️ ExplainerBundle Fallback

Every policy block MUST return a structured `ExplainerBundle` instead of raw errors:

```python
from ioa_sdk.explain import ExplainerBundle, ExplainerFactory

# For policy violations
if not policy_result["allowed"]:
    explainer = ExplainerBundle(
        event="user_data_fetch",
        policy_result=policy_result,
        audit_id=audit_id,
        user_id=user_id
    )
    return explainer.get_user_facing_message()

# For specific violations
explainer = ExplainerFactory.create_pii_violation(
    event="data_processing",
    audit_id=audit_id,
    user_id=user_id
)
```

## 🔍 CI Enforcement

The following CI guard runs on all repositories:

```bash
# Check for forbidden imports
python ioa-ops/dev/ci/forbidden_imports.py /path/to/repo

# Expected output: ✅ PASSED: No forbidden imports detected!
```

## 📋 Compliance Checklist

- [ ] No direct LLM provider imports (`openai`, `anthropic`, etc.)
- [ ] All LLM calls use `ioa_sdk.llm`
- [ ] All memory operations use `ioa_sdk.memory_fabric`
- [ ] All policy checks use `ioa_sdk.policy_engine`
- [ ] All audit logging uses `ioa_sdk.audit`
- [ ] Policy blocks return `ExplainerBundle`
- [ ] CI guard passes without violations
- [ ] Tests use mock providers when appropriate

## 🚀 Environment Configuration

### Development Mode
```bash
export IOA_LLM_MODE=mock  # Use mock providers for testing
export IOA_AUDIT_MODE=file  # Use file-based audit logging
export IOA_POLICY_MODE=enforce  # Enforce all policies
```

### Production Mode
```bash
export IOA_LLM_MODE=live  # Use live LLM providers
export IOA_AUDIT_MODE=memory_fabric  # Use Memory Fabric for audit
export IOA_POLICY_MODE=enforce  # Enforce all policies
```

## 📚 Additional Resources

- [IOA SDK Documentation](../../ioa-sdk/README.md)
- [Governance Guidelines](../../ioa-ops/docs/GOVERNANCE.md)
- [Audit Requirements](../../ioa-ops/docs/AUDIT.md)
- [Memory Fabric Usage](../../ioa-ops/docs/MEMORY_FABRIC.md)

## ⚠️ Violations

**Any violation of this contract will result in:**
1. CI build failure
2. Code review rejection
3. Potential security audit
4. Compliance violation report

**Remember:** SDK-only access ensures proper governance, audit trails, and policy enforcement across the entire IOA ecosystem.

---

**Questions?** Contact the IOA Governance Team or refer to the [IOA Ops Documentation](../../ioa-ops/README.md).
