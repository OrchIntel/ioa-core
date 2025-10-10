**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Core API Reference

This document provides the core API reference for IOA Core, including the main modules, classes, and functions.

## Overview

IOA Core provides a comprehensive API for building AI agent systems with governance, memory management, and workflow orchestration.

## Core Modules

### `src.agent_onboarding`

Agent onboarding and management system.

#### `AgentOnboarding`

Main class for managing agent onboarding.

```python
from src.agent_onboarding import AgentOnboarding, AgentOnboardingError

# Initialize onboarding system
onboarder = AgentOnboarding(base_dir="project.ioa")

# Onboard a new agent
try:
    result = onboarder.onboard_agent(manifest_json)
    print(f"Agent {result.agent_id} onboarded successfully")
except AgentOnboardingError as e:
    print(f"Onboarding failed: {e}")
```

**Methods:**

- `onboard_agent(manifest: dict) -> AgentResult`: Onboard a new agent
- `remove_agent(agent_id: str) -> bool`: Remove an agent
- `list_agents() -> List[AgentInfo]`: List all onboarded agents
- `get_agent(agent_id: str) -> AgentInfo`: Get agent information
- `validate_manifest(manifest: dict) -> ValidationResult`: Validate agent manifest

**Exceptions:**

- `ManifestValidationError`: Manifest validation failed
- `TrustVerificationError`: Trust signature verification failed
- `TenantIsolationError`: Tenant isolation violation
- `AgentOnboardingError`: General onboarding error

#### `AgentResult`

Result of agent onboarding operation.

```python
class AgentResult:
    agent_id: str
    status: str
    capabilities: List[str]
    tenant_id: str
    created_at: datetime
    trust_signature: str
    metadata: Dict[str, Any]
```

### `src.agent_router`

Agent routing and task distribution system.

#### `AgentRouter`

Routes tasks to appropriate agents based on capabilities and policies.

```python
from src.agent_router import AgentRouter

# Initialize router with governance configuration
router = AgentRouter(governance_config={
    "audit_enabled": True,
    "pki_enabled": True
})

# Route a task to agents
task = "Analyze this document for key insights"
agents = ["analyst_agent", "summarizer_agent"]

result = router.route_task(task, agents)
print(f"Task routed to {result.selected_agents}")
```

**Methods:**

- `get_agent_capabilities(agent_id: str) -> List[str]`: Get agent capabilities
- `validate_task_assignment(task: str, agent_id: str) -> bool`: Validate task assignment
- `get_routing_statistics() -> RoutingStats`: Get routing statistics

#### `RoutingResult`

Result of task routing operation.

```python
class RoutingResult:
    task_id: str
    routing_reason: str
    governance_checks: List[GovernanceCheck]
    timestamp: datetime
```

### `src.memory_engine`

Memory management and storage system.

#### `MemoryEngine`

Manages hot and cold storage with intelligent pruning.

```python
from src.memory_engine import MemoryEngine

# Initialize memory engine
memory = MemoryEngine(
    hot_storage_size_mb=1024,
    cold_storage_size_mb=10240,
    pruning_threshold=0.8
)

# Store data
memory.store("user_query", "What is AI?", "hot")
memory.store("analysis_result", result_data, "cold")

# Retrieve data
query = memory.retrieve("user_query", "hot")
analysis = memory.retrieve("analysis_result", "cold")
```

**Methods:**

- `store(key: str, value: Any, storage_type: str) -> bool`: Store data
- `retrieve(key: str, storage_type: str) -> Any`: Retrieve data
- `delete(key: str, storage_type: str) -> bool`: Delete data
- `list_keys(storage_type: str) -> List[str]`: List stored keys
- `get_status() -> MemoryStatus`: Get memory status
- `prune() -> PruningResult`: Prune old data

#### `MemoryStatus`

Current status of memory engine.

```python
class MemoryStatus:
    hot_storage_used_mb: float
    hot_storage_total_mb: float
    cold_storage_used_mb: float
    cold_storage_total_mb: float
    hot_entries: int
    cold_entries: int
    last_pruning: datetime
    pruning_threshold: float
```

### `src.roundtable_executor`

Multi-agent consensus and decision-making system.

#### `RoundtableExecutor`

Executes tasks across multiple agents with voting mechanisms.

```python
from src.roundtable_executor import RoundtableExecutor

# Initialize roundtable executor
executor = RoundtableExecutor(router, storage)

# Execute roundtable task
result = await executor.execute_roundtable(
    task="Design a scalable architecture",
    agents=["architect_agent", "security_agent", "performance_agent"],
    mode="weighted",
    quorum=0.8
)

print(f"Consensus achieved: {result.consensus_achieved}")
print(f"Final decision: {result.final_decision}")
```

**Methods:**

- `get_voting_modes() -> List[str]`: Get available voting modes
- `get_statistics() -> RoundtableStats`: Get execution statistics

#### `RoundtableResult`

Result of roundtable execution.

```python
class RoundtableResult:
    task_id: str
    participants: List[str]
    voting_mode: str
    consensus_achieved: bool
    consensus_score: float
    final_decision: str
    individual_responses: List[AgentResponse]
    execution_time: float
    timestamp: datetime
```

### `src.workflow_executor`

Workflow definition and execution system.

#### `WorkflowExecutor`

Executes YAML-defined workflows with dependency management.

```python
from src.workflow_executor import WorkflowExecutor

# Initialize workflow executor
executor = WorkflowExecutor()

# Load and execute workflow
workflow = executor.load_workflow("workflow.yaml")
result = await executor.execute_workflow(workflow)

print(f"Workflow completed: {result.status}")
print(f"Execution time: {result.execution_time}s")
```

**Methods:**

- `load_workflow(file_path: str) -> Workflow`: Load workflow from file
- `execute_workflow(workflow: Workflow) -> WorkflowResult`: Execute workflow
- `validate_workflow(workflow: Workflow) -> ValidationResult`: Validate workflow
- `get_workflow_status(workflow_id: str) -> WorkflowStatus`: Get workflow status

#### `Workflow`

Workflow definition and configuration.

```python
class Workflow:
    name: str
    description: str
    steps: List[WorkflowStep]
    metadata: Dict[str, Any]
```

#### `WorkflowStep`

Individual step in a workflow.

```python
class WorkflowStep:
    name: str
    task: str
    timeout: int
    depends_on: List[str]
    parameters: Dict[str, Any]
    output_format: str
    retry_policy: RetryPolicy
```

## Governance & Security

### `src.governance.audit_chain`

Audit logging and compliance system.

#### `AuditChain`

Comprehensive audit logging with redaction and rotation.

```python
from src.governance.audit_chain import AuditChain

# Initialize audit chain
audit = AuditChain(
    log_path="./logs/audit/",
    rotation_size_mb=10,
    retention_days=90
)

# Log audit event
audit.log(
    event_type="agent_onboarding",
    user_id="user123",
    resource_id="agent456",
    action="create",
    details={"capabilities": ["analysis", "summary"]}
)
```

**Methods:**

- `log(event_type: str, **kwargs) -> str`: Log audit event
- `query(filters: Dict[str, Any]) -> List[AuditEvent]`: Query audit logs
- `export(file_path: str, filters: Dict[str, Any]) -> bool`: Export audit logs
- `rotate() -> bool`: Rotate audit logs
- `get_status() -> AuditStatus`: Get audit system status

#### `AuditEvent`

Individual audit log entry.

```python
class AuditEvent:
    event_id: str
    timestamp: datetime
    event_type: str
    user_id: str
    resource_id: str
    action: str
    details: Dict[str, Any]
    ip_address: str
    redacted: bool
```

### `src.governance.signature_engine`

PKI-based trust verification system.

#### `SignatureEngine`

Digital signature generation and verification.

```python
from src.governance.signature_engine import SignatureEngine

# Initialize signature engine
engine = SignatureEngine(algorithm="ed25519")

# Generate signature
private_key = engine.generate_key_pair()
signature = engine.sign("agent_manifest", private_key)

# Verify signature
is_valid = engine.verify("agent_manifest", signature, public_key)
print(f"Signature valid: {is_valid}")
```

**Methods:**

- `generate_key_pair() -> KeyPair`: Generate new key pair
- `sign(data: str, private_key: bytes) -> str`: Sign data
- `verify(data: str, signature: str, public_key: bytes) -> bool`: Verify signature
- `get_algorithm_info() -> AlgorithmInfo`: Get algorithm information

## LLM Provider Integration

### `src.llm_providers.base`

Base provider interface and common functionality.

#### `BaseLLMProvider`

Abstract base class for LLM providers.

```python
from src.llm_providers.base import BaseLLMProvider

class CustomProvider(BaseLLMProvider):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
    async def execute(self, prompt: str, **kwargs) -> ProviderResponse:
        # Implement provider-specific logic
        pass
```

**Abstract Methods:**

- `execute(prompt: str, **kwargs) -> ProviderResponse`: Execute prompt
- `validate_config(config: Dict[str, Any]) -> bool`: Validate configuration
- `get_capabilities() -> List[str]`: Get provider capabilities

#### `ProviderResponse`

Standardized response from LLM providers.

```python
class ProviderResponse:
    content: str
    usage: UsageInfo
    metadata: Dict[str, Any]
    confidence: float
    timestamp: datetime
```

### `src.llm_providers.openai`

OpenAI provider implementation.

```python
from src.llm_providers.openai import OpenAIProvider

# Initialize OpenAI provider
provider = OpenAIProvider({
    "api_key": "sk-...",
    "model": "gpt-4o-mini",
    "max_tokens": 4096
})

# Execute prompt
response = await provider.execute(
    "Explain quantum computing in simple terms",
    temperature=0.7
)

print(f"Response: {response.content}")
```

### `src.llm_providers.anthropic`

Anthropic provider implementation.

```python
from src.llm_providers.anthropic import AnthropicProvider

# Initialize Anthropic provider
provider = AnthropicProvider({
    "api_key": "sk-ant-...",
    "model": "claude-3-haiku"
})

# Execute prompt
response = await provider.execute(
    "Analyze this code for security vulnerabilities"
)

print(f"Analysis: {response.content}")
```

## Memory & Storage

### `src.storage.base`

Base storage interface and implementations.

#### `BaseStorage`

Abstract base class for storage backends.

```python
from src.storage.base import BaseStorage

class CustomStorage(BaseStorage):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
    async def store(self, key: str, value: Any) -> bool:
        # Implement storage logic
        pass
        
    async def retrieve(self, key: str) -> Any:
        # Implement retrieval logic
        pass
```

### `src.storage.memory`

In-memory storage implementation.

```python
from src.storage.memory import InMemoryStorage

# Initialize in-memory storage
storage = InMemoryStorage(max_size_mb=1024)

# Store and retrieve data
storage.store("key1", "value1")
value = storage.retrieve("key1")
```

### `src.storage.file`

File-based storage implementation.

```python
from src.storage.file import FileStorage

# Initialize file storage
storage = FileStorage(base_path="./data/")

# Store and retrieve data
storage.store("config", {"setting": "value"})
config = storage.retrieve("config")
```

## Configuration Management

### `src.config.manager`

Configuration loading and management system.

#### `ConfigManager`

Manages configuration loading, validation, and access.

```python
from src.config.manager import ConfigManager

# Initialize configuration manager
config = ConfigManager()

# Load configuration
config.load_from_file("config.yaml")
config.load_from_env()

# Access configuration values
debug_mode = config.get("core.debug", default=False)
log_level = config.get("core.log_level", default="INFO")

# Set configuration values
config.set("core.debug", True)
```

**Methods:**

- `load_from_file(file_path: str) -> bool`: Load from file
- `load_from_env() -> bool`: Load from environment variables
- `get(key: str, default: Any = None) -> Any`: Get configuration value
- `set(key: str, value: Any) -> bool`: Set configuration value
- `validate() -> ValidationResult`: Validate configuration
- `export(file_path: str) -> bool`: Export configuration

## Error Handling

### Common Exceptions

```python
from src.exceptions import (
    IOAError,
    ConfigurationError,
    ValidationError,
    ProviderError,
    GovernanceError,
    MemoryError,
    WorkflowError
)

try:
    # IOA Core operation
    result = await executor.execute_workflow(workflow)
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except ValidationError as e:
    print(f"Validation error: {e}")
except ProviderError as e:
    print(f"Provider error: {e}")
except IOAError as e:
    print(f"General error: {e}")
```

### Error Types

- `ConfigurationError`: Configuration-related errors
- `ValidationError`: Data validation errors
- `ProviderError`: LLM provider errors
- `GovernanceError`: Governance and security errors
- `MemoryError`: Memory and storage errors
- `WorkflowError`: Workflow execution errors
- `IOAError`: Base exception class

## Async Support

IOA Core is built with async/await support for high-performance operations.

```python
import asyncio
from src.workflow_executor import WorkflowExecutor

async def main():
    executor = WorkflowExecutor()
    
    # Execute multiple workflows concurrently
    workflows = [
        executor.execute_workflow(workflow1),
        executor.execute_workflow(workflow2),
        executor.execute_workflow(workflow3)
    ]
    
    results = await asyncio.gather(*workflows)
    
    for result in results:
        print(f"Workflow completed: {result.status}")

# Run async function
asyncio.run(main())
```

## Type Hints

IOA Core provides comprehensive type hints for better development experience.

```python
from typing import Dict, List, Optional, Any
from src.types import AgentID, TaskID, WorkflowID

def process_workflow(
    workflow_id: WorkflowID,
    parameters: Optional[Dict[str, Any]] = None
) -> WorkflowResult:
    # Function implementation
    pass
```

## Best Practices

### 1. **Error Handling**
- Always catch specific exception types
- Provide meaningful error messages
- Log errors for debugging

### 2. **Configuration Management**
- Use environment variables for sensitive data
- Validate configuration on startup
- Provide sensible defaults

### 3. **Resource Management**
- Use context managers for resources
- Implement proper cleanup
- Monitor resource usage

### 4. **Async Operations**
- Use async/await consistently
- Handle concurrent operations properly
- Implement proper error handling in async code

### 5. **Security**
- Validate all inputs
- Use audit logging for sensitive operations
- Implement proper access controls

## Examples

### Complete Workflow Example

```python
import asyncio
from src.workflow_executor import WorkflowExecutor
from src.agent_router import AgentRouter
from src.memory_engine import MemoryEngine

async def run_complete_workflow():
    # Initialize components
    memory = MemoryEngine()
    router = AgentRouter()
    executor = WorkflowExecutor()
    
    # Load workflow
    workflow = executor.load_workflow("analysis_workflow.yaml")
    
    # Execute workflow
    result = await executor.execute_workflow(workflow)
    
    # Store results
    memory.store("workflow_result", result, "cold")
    
    return result

# Run workflow
result = asyncio.run(run_complete_workflow())
print(f"Workflow completed: {result.status}")
```

### Custom Agent Implementation

```python
from src.llm_providers.base import BaseLLMProvider
from src.types import ProviderResponse

class CustomAnalysisAgent(BaseLLMProvider):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.specialized_knowledge = config.get("knowledge_domain", "general")
    
    async def execute(self, prompt: str, **kwargs) -> ProviderResponse:
        # Implement custom analysis logic
        enhanced_prompt = f"Domain: {self.specialized_knowledge}\nPrompt: {prompt}"
        
        # Call base provider
        response = await super().execute(enhanced_prompt, **kwargs)
        
        # Post-process response
        response.content = f"[{self.specialized_knowledge}] {response.content}"
        
        return response
```

---

*For more API details, see the [Provider API](providers.md) and [Governance API](governance.md) documentation*
