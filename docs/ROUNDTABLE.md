**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# IOA Core Roundtable Configuration

This document describes the roundtable system in IOA Core, which enables collaborative AI execution across multiple LLM providers.

## Overview

Roundtables allow you to execute tasks across multiple AI models simultaneously, then merge their responses using configurable strategies. This provides:

- **Diversity**: Multiple perspectives from different models
- **Reliability**: Consensus building and fallback options
- **Flexibility**: Configurable weights and merge strategies
- **Efficiency**: Parallel execution with configurable quorum

## Configuration Structure

Roundtables are configured in `~/.ioa/config/roundtable.json`:

```json
{
  "version": 1,
  "active": "default",
  "tables": {
    "default": {
      "quorum": 2,
      "merge_strategy": "vote_majority",
      "participants": [
        {
          "provider": "openai",
          "model": "gpt-4o-mini",
          "weight": 1.0,
          "max_tokens": 512
        },
        {
          "provider": "anthropic",
          "model": "claude-3-haiku",
          "weight": 1.0,
          "max_tokens": 512
        }
      ]
    }
  }
}
```

## Configuration Fields

### Top Level
- **`version`**: Configuration schema version (currently 1)
- **`active`**: Name of the currently active roundtable
- **`tables`**: Dictionary of roundtable configurations

### Roundtable Configuration
- **`quorum`**: Minimum number of participants required for consensus
- **`merge_strategy`**: Strategy for combining participant responses
- **`participants`**: List of AI models participating in the roundtable

### Participant Configuration
- **`provider`**: LLM provider name (must be configured in LLM Manager)
- **`model`**: Specific model to use from that provider
- **`weight`**: Relative importance of this participant (float)
- **`max_tokens`**: Maximum tokens for this participant's response

## Merge Strategies

### 1. Vote Majority (`vote_majority`)
Simple majority voting where the most common response wins.

**Use case**: When you need a single, consensus answer
**Example**: Classification tasks, yes/no questions

### 2. Concatenate Summaries (`concat_summaries`)
Combines truncated summaries from all participants.

**Use case**: When you want to see all perspectives
**Example**: Research tasks, brainstorming sessions

### 3. Confidence Weighted (`confidence_weighted`)
Weights responses by participant confidence scores.

**Use case**: When some models are more reliable than others
**Example**: Complex reasoning tasks, expert systems

## Creating Roundtables

### Via CLI (Interactive)
```bash
python -m src.cli.onboard setup
# Follow prompts to configure roundtable
```

### Via CLI (Programmatic)
```bash
# Create custom roundtable
python -m src.cli.onboard roundtable create custom
```

### Via Code
```python
from src.llm_manager import LLMManager

manager = LLMManager()

roundtable_config = {
    "quorum": 3,
    "merge_strategy": "confidence_weighted",
    "participants": [
        {
            "provider": "openai",
            "model": "gpt-4o",
            "weight": 1.0,
            "max_tokens": 1024
        },
        {
            "provider": "anthropic",
            "model": "claude-3-sonnet",
            "weight": 0.8,
            "max_tokens": 768
        },
        {
            "provider": "google",
            "model": "gemini-1.5-pro",
            "weight": 0.6,
            "max_tokens": 512
        }
    ]
}

manager.create_roundtable("expert", roundtable_config)
manager.activate_roundtable("expert")
```

## Managing Roundtables

### CLI Commands
```bash
# List all roundtables
python -m src.cli.onboard roundtable list

# Show specific roundtable configuration
python -m src.cli.onboard roundtable show default

# Activate a roundtable
python -m src.cli.onboard roundtable activate expert

# Create new roundtable (via setup)
python -m src.cli.onboard setup
```

### Programmatic Management
```python
from src.llm_manager import LLMManager

manager = LLMManager()

# List roundtables
roundtables = manager.list_roundtables()
print(f"Available roundtables: {roundtables}")

# Get active roundtable
active = manager.get_active_roundtable()
print(f"Active roundtable: {active}")

# Get roundtable configuration
config = manager.get_roundtable("expert")
print(f"Expert roundtable quorum: {config['quorum']}")
```

## Executing Roundtables

### Via RoundtableExecutor
```python
from src.roundtable_executor import RoundtableExecutor
from src.llm_manager import LLMManager

# Initialize executor
executor = RoundtableExecutor(router, storage)

# Execute with LLM Manager plan
result = executor.execute_with_llm_manager_plan(
    task="Analyze the ethical implications of AI decision-making",
    roundtable_name="expert"
)

print(f"Consensus: {result.consensus}")
print(f"Confidence: {result.confidence_score}")
print(f"Execution time: {result.execution_time}")
```

### Direct Execution
```python
from src.roundtable_executor import RoundtableExecutor

executor = RoundtableExecutor(router, storage)

# Execute with specific agents
result = await executor.execute_roundtable(
    task="Your task here",
    agents=["openai", "anthropic"],
    mode='consensus'
)
```

## Best Practices

### 1. Quorum Sizing
- **Small quorum (2-3)**: Fast execution, good for simple tasks
- **Medium quorum (4-6)**: Balanced speed and reliability
- **Large quorum (7+)**: High reliability, slower execution

### 2. Participant Selection
- **Diverse models**: Mix different architectures and training approaches
- **Appropriate weights**: Assign higher weights to more capable models
- **Token limits**: Balance response quality with cost/performance

### 3. Merge Strategy Selection
- **`vote_majority`**: Simple, fast, good for classification
- **`concat_summaries`**: Comprehensive, good for research
- **`confidence_weighted`**: Sophisticated, good for complex reasoning

### 4. Error Handling
```python
try:
    result = executor.execute_with_llm_manager_plan(task, "expert")
except LLMConfigError as e:
    print(f"Configuration error: {e}")
    # Fall back to single provider or default roundtable
except Exception as e:
    print(f"Execution error: {e}")
    # Handle gracefully
```

## Advanced Configuration

### Custom Merge Strategies
You can extend the merge strategies by modifying the `_apply_merge_strategy` method in `RoundtableExecutor`:

```python
def _apply_merge_strategy(self, result: RoundtableResult, strategy: str) -> RoundtableResult:
    if strategy == "custom_strategy":
        # Implement your custom logic here
        result.consensus = f"Custom merge: {result.consensus}"
    else:
        # Call parent method for standard strategies
        return super()._apply_merge_strategy(result, strategy)
    
    return result
```

### Dynamic Participant Selection
```python
# Select participants based on task requirements
def select_participants_for_task(task: str, manager: LLMManager):
    if "code" in task.lower():
        return ["openai", "anthropic"]  # Good for code generation
    elif "reasoning" in task.lower():
        return ["openai", "google"]     # Good for reasoning
    else:
        return ["openai"]               # Default fallback
```

## Monitoring and Debugging

### Execution Statistics
```python
stats = executor.get_execution_stats()
print(f"Total executions: {stats['total_executions']}")
print(f"Success rate: {stats['successful_executions'] / stats['total_executions']:.2%}")
print(f"Average execution time: {stats['avg_execution_time']:.2f}s")
```

### Response Analysis
```python
for response in result.responses:
    print(f"Provider: {response.agent_id}")
    print(f"Content: {response.content[:100]}...")
    print(f"Confidence: {response.confidence}")
    print(f"Processing time: {response.processing_time}s")
    print("---")
```

## Troubleshooting

### Common Issues

1. **"No participants configured"**
   - Ensure LLM providers are configured before creating roundtables
   - Check that provider names match exactly

2. **"Roundtable not found"**
   - Verify roundtable exists with `roundtable list`
   - Check for typos in roundtable names

3. **Quorum not met**
   - Reduce quorum size or add more participants
   - Check that all participants are accessible

4. **Merge strategy errors**
   - Verify merge strategy name is correct
   - Check that participants have required fields (confidence, etc.)

### Debug Mode
Enable detailed logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Execute roundtable with detailed logging
result = executor.execute_with_llm_manager_plan(task, "debug")
```

## Performance Considerations

### Parallel Execution
- Roundtables execute participants in parallel when possible
- Use `max_workers` parameter to control concurrency
- Monitor memory usage with large participant counts

### Caching
- Consider caching roundtable results for repeated tasks
- Implement participant response caching for expensive models

### Cost Optimization
- Use cheaper models for initial responses
- Implement fallback chains (expensive → cheaper models)
- Monitor token usage across participants

## Integration Examples

### With FastAPI
```python
from fastapi import FastAPI
from src.roundtable_executor import RoundtableExecutor

app = FastAPI()
executor = RoundtableExecutor(router, storage)

@app.post("/roundtable/execute")
async def execute_roundtable(task: str, roundtable: str = "default"):
    try:
        result = executor.execute_with_llm_manager_plan(task, roundtable)
        return {
            "consensus": result.consensus,
            "confidence": result.confidence_score,
            "execution_time": result.execution_time
        }
    except Exception as e:
        return {"error": str(e)}
```

### With Celery
```python
from celery import Celery
from src.roundtable_executor import RoundtableExecutor

celery_app = Celery('roundtable_tasks')
executor = RoundtableExecutor(router, storage)

@celery_app.task
def execute_roundtable_task(task: str, roundtable: str):
    result = executor.execute_with_llm_manager_plan(task, roundtable)
    return {
        "consensus": result.consensus,
        "confidence": result.confidence_score
    }
```

This roundtable system provides a powerful foundation for collaborative AI execution in IOA Core.
