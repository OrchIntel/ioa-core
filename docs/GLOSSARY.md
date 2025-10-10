**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Glossary
Last Updated: 2025-08-08
Description: Comprehensive glossary of IOA Core terminology and concepts
License: IOA Dev Confidential – Internal Use Only

## Core Concepts

### Agent
An autonomous software component within the IOA system that processes tasks, maintains state, and collaborates with other agents. Each agent has defined capabilities, performance metrics, and operates under governance policies. Agents can be specialized for different functions like analysis, text generation, or code review.

### Agent Router
The central coordination system that manages agent registration, capability matching, and task distribution. The router evaluates available agents based on their capabilities, current load, and performance history to optimally assign incoming tasks.

### Capability
A specific skill or function that an agent can perform, such as "text_generation," "analysis," or "translation." Capabilities are used by the Agent Router to match tasks with appropriate agents and include proficiency scoring and performance metrics.

### Consensus Threshold
The minimum level of agreement required among participating agents before a collective decision is accepted. Typically set between 0.6-0.8, this threshold balances decision quality with operational efficiency in multi-agent scenarios.

### Governance Policy
Rules and procedures that control agent behavior, task routing, and system operations. Governance policies include bias detection mechanisms, reinforcement learning parameters, and compliance enforcement protocols.

## Memory System

### Memory Engine
The core system responsible for storing, organizing, and retrieving agent memories and interactions. The Memory Engine maintains persistent state across sessions and enables agents to learn from past experiences and build contextual understanding.

### Memory Entry
A single unit of stored information within the Memory Engine, containing content, metadata, timestamps, and relevance scores. Memory entries can represent conversations, learned patterns, or procedural knowledge.

### Memory Tier
Classification system for organizing memory entries based on importance and access frequency. Hot tier contains frequently accessed data, while cold tier stores less frequently used information for potential archival.

### Pattern
A recurring structure, theme, or behavior identified within agent memories or interactions. Patterns can represent conversation topics, decision-making approaches, or behavioral tendencies that emerge over time.

### Pattern Weaver
The system component responsible for identifying, analyzing, and managing patterns within the memory system. The Pattern Weaver helps detect emergent behaviors and maintains pattern evolution over time.

## Orchestration Components

### Roundtable
A collaborative decision-making mechanism where multiple agents contribute to problem-solving or consensus formation. Roundtable sessions involve structured discussion phases and weighted voting based on agent expertise and trust levels.

### Routing Weight
Numerical values used by the Agent Router to determine task assignment priority. Routing weights consider factors like agent capability proficiency, current load, historical performance, and trust scores.

### Sentinel
A monitoring and governance component that observes system operations, detects policy violations, and triggers corrective actions. Sentinels help maintain system integrity and enforce compliance with governance policies.

### Task Priority
Classification system for incoming tasks ranging from LOW to CRITICAL, affecting how quickly tasks are processed and which agents are selected. Higher priority tasks receive preferential routing and resource allocation.

## Performance and Trust

### Trust Score
A dynamic metric representing the reliability and performance history of an agent. Trust scores influence routing decisions, consensus weighting, and governance interventions. Scores are updated based on task success rates, adherence to policies, and peer evaluations.

### Satisfaction Score
Metric measuring the quality and appropriateness of agent responses or task completions. Satisfaction scores contribute to trust score calculations and help identify high-performing agents for similar future tasks.

### Stress Level
Indicator of agent workload and performance degradation risk. High stress levels may trigger load balancing, task redistribution, or temporary agent deactivation to maintain system stability.

### Reinforcement Policy
Learning mechanism that adjusts agent behavior through reward and punishment signals. Reinforcement policies help shape agent decision-making and promote desired behaviors while discouraging problematic patterns.

## Technical Infrastructure

### LLM Adapter
Interface layer that connects IOA agents with external language model services like OpenAI GPT, enabling standardized communication and response processing across different AI providers.

### Cold Storage
Archival system for long-term storage of infrequently accessed memory entries and historical data. Cold storage implementations vary between OSS (mock) and Organization (full-featured) versions.

### Digestor
Component responsible for processing and analyzing large volumes of agent memory data to extract insights, identify patterns, and generate summary reports. The Digestor supports both real-time and batch processing modes.

### Refinery
Data processing system that cleans, organizes, and optimizes memory storage for improved performance and retrieval accuracy. The Refinery applies data quality rules and maintains consistency across the memory system.

## Security and Compliance

### Trust Registry
Configuration system that defines which agents and adapters are authorized to operate within the IOA environment. The Trust Registry includes cryptographic signatures, capability restrictions, and audit trails.

### Signature Verification
Security mechanism that validates agent authenticity using cryptographic signatures. Note that IOA Core OSS uses demonstration-grade SHA-256 signatures while IOA Organization implements HSM-based verification.

### Tenant Isolation
Security feature that separates different user environments or projects within a shared IOA deployment. Tenant isolation ensures data privacy and prevents cross-contamination between different use cases.

### VAD (Voice Activity Detection) Analysis
Sentiment and emotion analysis component that evaluates the emotional content of agent interactions to detect bias, inappropriate behavior, or concerning patterns.

## Configuration and Deployment

### Agent Manifest
JSON configuration file that defines an agent's capabilities, parameters, trust requirements, and operational constraints. Manifests are used during agent onboarding and validation processes.

### Onboarding Schema
Validation framework that ensures agent manifests meet required standards and security policies before agents are registered and allowed to operate within the system.

### Governance Configuration
YAML file containing system-wide settings for consensus thresholds, pattern detection, monitoring levels, and debug flags. Governance configuration controls how the entire IOA system operates.

### Boot Prompt
Initial instruction set provided to newly onboarded agents that establishes their role, operational context, and behavioral guidelines within the IOA environment.

## Operational States

### Agent Status
Current operational condition of an agent, including AVAILABLE (ready for tasks), BUSY (processing work), OFFLINE (temporarily unavailable), ERROR (experiencing issues), and MAINTENANCE (undergoing updates).

### Roundtable Mode
System configuration that enables collaborative multi-agent decision-making. When enabled, complex tasks may be processed by multiple agents working together rather than single-agent processing.

### Debug Flags
Configuration options that enable detailed logging and monitoring for troubleshooting and system analysis. Common flags include trace-routing (showing agent selection logic) and log-memory-diff (tracking memory changes).

### Pattern Court
Governance mechanism that validates and manages the lifecycle of identified patterns, including deprecation of outdated patterns and promotion of valuable behavioral templates.

---

**Glossary Version**: v2.5.0  
**Last Updated**: 2025-08-07  
**Maintained by**: IOA Project Contributors

*For technical implementation details, refer to the source code documentation in `/src/` directories. For organization-specific terms and features, consult IOA Organization documentation.*