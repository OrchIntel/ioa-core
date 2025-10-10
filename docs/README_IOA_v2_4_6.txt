# IOA Project – README (v2.4.5)

## Overview
The IOA (Intelligent Orchestration Architecture) enables memory-driven collaboration between modular AI agents including internal agent, internal agent, internal agent, and internal agent. The architecture supports real-time orchestration, long-term memory, NLP metadata enrichment, and schema evolution.

## Core Modules
- memory_engine.py v2.2.3
- digestor.py v1.0.0 (standalone, schema-compliant)
- pattern_weaver.py v2.3.0 (NLP-enhanced)
- agent_router.py
- roundtable_executor.py v2.3.3 (reinforcement logic, schema-safe)
- nlp_module.py v0.1.0
- test_digestor_demo.py v1.0.0

## NLP Integration
- Added support for entity extraction, keyword clustering, multilingual fallback, and sentiment scoring (VAD).
- Future: spaCy integration for advanced parsing (v2.5+).

## Schema & Safety
- Memory schema v0.1.2 enforced across all modules
- internal agent validation: ✅ PASS
- All outputs include required fields: pattern_id, metadata, variables, feeling, raw_ref

## Security
- Agent role isolation enforced via boundaries
- Sentinel override hooks planned (v2.5+)
- External API safety under review


