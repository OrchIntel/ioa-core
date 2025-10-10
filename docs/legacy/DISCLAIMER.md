**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# IOA Core Disclaimer

The **Intelligent Orchestration Architecture (IOA)**, developed by OrchIntel Systems Ltd, is an open-source platform for agent orchestration infrastructure. This document clarifies limitations, appropriate use, and future development to ensure transparency for users and contributors.

## Key Clarifications
- **Not AGI or Advanced AI**: IOA is not an Artificial General Intelligence (AGI) system or "OS for AGI." It provides modular tools for orchestrating AI agents with basic memory and governance features. Cognitive elements (e.g., VAD sentiment, pattern clustering) are heuristic-based and do not constitute true intelligence. All pattern recognition and consensus are rule-based or statistical, not emergent reasoning. For alignment with societal values, IOA incorporates basic ethical frameworks, but users must implement production-grade safety (see NIST AI Risk Management Framework [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework)).

- **Development Stage**: IOA Core is in beta (v2.4.8) and intended for evaluation and development. It is not production-ready without customization. Features like consensus mechanisms (`roundtable_executor.py`) are stubbed for Phase 2 and may raise `NotImplementedError`. Do not use for critical applications without thorough testing and governance extensions.

- **Core vs. Enterprise Features**: IOA Core provides foundational orchestration, memory, and governance. Advanced capabilities (e.g., mood modeling, cold storage, enhanced NLP) are available in the proprietary IOA Enterprise edition under a commercial license. See [FEATURE_MATRIX.md](FEATURE_MATRIX.md) for details. This open-core model allows community contributions while offering enterprise support.

- **Limitations & Risks**:
  - **Security**: Trust systems use basic SHA-256 validation (`agent_onboarding.py`). Placeholders in examples are for demonstration—replace with secure implementations. No built-in encryption or access controls; users must add these for compliance (e.g., GDPR, HIPAA).
  - **Bias & Ethics**: Basic mitigation exists (e.g., VAD averaging in `refinery_utils.py`), but IOA does not guarantee fairness. Potential for amplified biases in multi-agent consensus—test with diverse datasets.
  - **Performance**: Tested to 10k entries (~850MB memory, 0.001s hot retrieval), but scales linearly. See [SCALING.md](SCALING.md) for details.
  - **Dependencies**: Relies on external LLMs (e.g., OpenAI)—API changes may break adapters (`llm_adapter.py`).

- **Intended Use**: For research, prototyping, and non-commercial development. Commercial use requires review of Apache 2.0 terms and potential enterprise licensing.

- **No Warranties**: OrchIntel Systems Ltd provides IOA Core "as is" without warranty. Users assume all risks. For enterprise-grade features, contact `enterprise@orchintel.com`.

## Safety & Alignment
IOA aligns with ethical AI principles (e.g., fairness/transparency from IEEE Ethically Aligned Design). Future phases will enhance safety (e.g., Phase 3: PID Homeostasis for stability). Report concerns to `security@orchintel.com`.

© 2025 OrchIntel Systems Ltd
