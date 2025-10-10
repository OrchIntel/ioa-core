**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Hello World Tutorial

Welcome to IOA Core! This tutorial will guide you through creating and running your first AI agent workflow.

## Prerequisites

Before starting this tutorial, ensure you have:

- [IOA Core installed](../getting-started/installation.md)
- [Basic configuration set up](../getting-started/quickstart.md)
- Python 3.9+ and pip available

## Quick Start (5 minutes)

### Step 1: Create a New Project

> **Note**: Some commands below are examples for future functionality.

```bash
# Create a new IOA project
# Example (not currently implemented): ioa boot --project-name hello-world --template basic

# Navigate to the project directory
cd hello-world.ioa
```

### Step 2: Create a Simple Workflow

Create a file called `workflow.yaml` in your project directory:

```yaml
name: Hello World
description: My first IOA Core workflow

steps:
  - name: greet
    task: "Say hello to the world and introduce yourself"
    timeout: 30
    output_format: "text"
```

### Step 3: Run the Workflow

> **Note**: Some commands below are examples for future functionality.

```bash
# Run the workflow
# Example (not currently implemented): ioa workflows run --file workflow.yaml

# Check the status
# Example (not currently implemented): ioa workflows status
```

That's it! You've created and run your first IOA Core workflow. 🎉

## Detailed Tutorial

### Understanding the Components

Let's break down what we just created:

#### 1. **Workflow Definition** (`workflow.yaml`)
- **name**: Human-readable identifier
- **description**: What the workflow does
- **steps**: List of tasks to execute

#### 2. **Step Configuration**
- **name**: Unique identifier for the step
- **agent**: Which AI agent to use
- **task**: What the agent should do
- **timeout**: Maximum execution time (seconds)
- **output_format**: Expected response format

#### 3. **Agent Types**
IOA Core provides several built-in agent types:
- `hello_agent`: Simple greeting and introduction
- `analysis_agent`: Data analysis and insights
- `summary_agent`: Text summarization
- `code_agent`: Code generation and review

### Creating More Complex Workflows

Let's expand our workflow to include multiple steps:

```yaml
name: Enhanced Hello World
description: A workflow with multiple steps and dependencies

steps:
  - name: introduction
    task: "Introduce yourself and explain what you can do"
    timeout: 30
    output_format: "text"

  - name: analysis
    task: "Analyze the introduction and provide insights"
    depends_on: [introduction]
    timeout: 45
    output_format: "json"

  - name: summary
    task: "Create a concise summary of the analysis"
    depends_on: [analysis]
    timeout: 30
    output_format: "text"
```

#### Key Concepts:

1. **Dependencies**: The `depends_on` field ensures steps run in order
2. **Output Formats**: Different agents can return different data types
3. **Timeouts**: Each step has its own execution limit

### Running and Monitoring

#### Execute the Workflow

> **Note**: Some commands below are examples for future functionality.

```bash
# Run with verbose output
# Example (not currently implemented): ioa workflows run --file workflow.yaml --verbose

# Run in dry-run mode (validate without execution)
# Example (not currently implemented): ioa workflows run --file workflow.yaml --dry-run
```

#### Monitor Progress

> **Note**: Some commands below are examples for future functionality.

```bash
# Check workflow status
# Example (not currently implemented): ioa workflows status

# View real-time logs
# Example (not currently implemented): ioa workflows logs --follow

# Get execution results
# Example (not currently implemented): ioa workflows results
```

#### Example Output

```
✅ Workflow 'Enhanced Hello World' completed successfully

- Introduction: ✅ Completed (2.3s)
- Analysis: ✅ Completed (4.1s)  

⏱️ Total Time: 8.2 seconds
```

### Customizing Agents

You can customize agent behavior by adding parameters:

```yaml
steps:
  - name: personalized_greeting
    task: "Greet the user and ask about their interests"
    timeout: 30
    parameters:
      tone: "friendly"
      language: "en"
      include_questions: true
    output_format: "text"
```

### Error Handling

Workflows can handle failures gracefully:

```yaml
steps:
  - name: robust_step
    task: "Perform a task that might fail"
    timeout: 30
    max_retries: 3
    retry_delay: 5
    on_failure: "continue"  # Options: continue, fail, retry
```

### Testing Your Workflow

#### Validate Before Running

> **Note**: Some commands below are examples for future functionality.

```bash
# Check workflow syntax
# Example (not currently implemented): ioa workflows validate workflow.yaml

# Validate with schema
# Example (not currently implemented): ioa workflows validate workflow.yaml --schema
```

#### Test Individual Steps

> **Note**: Some commands below are examples for future functionality.

```bash
# Test a specific agent
# Example (not currently implemented): ioa agents test hello_agent --task "Say hello"

# Test with custom parameters
# Example (not currently implemented): ioa agents test hello_agent --task "Greet in Spanish" --parameters '{"language": "es"}'
```

## Next Steps

Now that you've mastered the basics, explore:

1. **[Governance & Audit Tutorial](governance-audit.md)** - Learn about security and compliance
2. **[PKI Onboarding Tutorial](pki-onboarding.md)** - Secure agent verification
3. **[Domain Schema Tutorial](domain-schema.md)** - Custom data validation
4. **[CLI Reference](../user-guide/cli-reference.md)** - Complete command reference
5. **[Configuration Guide](../user-guide/configuration.md)** - Advanced settings

## Troubleshooting

### Common Issues

#### "Agent not found" Error
> **Note**: Some commands below are examples for future functionality.

```bash
# Check available agents
# Example (not currently implemented): ioa agents list

# Verify agent configuration
# Example (not currently implemented): ioa agents show hello_agent
```

#### Workflow Validation Errors
> **Note**: Some commands below are examples for future functionality.

```bash
# Check YAML syntax
# yamllint workflow.yaml

# Validate against schema
# Example (not currently implemented): ioa workflows validate workflow.yaml --schema
```

#### Timeout Issues
> **Note**: Some commands below are examples for future functionality.

```bash
# Increase timeout for slow steps
# timeout: 60  # 60 seconds instead of 30

# Check system resources
# Example (not currently implemented): ioa health --detailed
```

### Getting Help

> **Note**: Some commands below are examples for future functionality.

```bash
# Workflow help
# Example (not currently implemented): ioa workflows --help

# Agent help
# Example (not currently implemented): ioa agents --help

# General help
# Example (not currently implemented): ioa --help
```

## Advanced Features

### Environment Variables

You can use environment variables in your workflows:

```yaml
steps:
  - name: configurable_greeting
    task: "Greet ${USER_NAME} in ${LANGUAGE}"
    timeout: 30
```

### Conditional Execution

```yaml
steps:
  - name: conditional_step
    task: "Perform conditional task"
    when: "${ENVIRONMENT} == 'production'"
    timeout: 30
```

### Parallel Execution

```yaml
steps:
  - name: parallel_task_1
    task: "Task 1"
    timeout: 30

  - name: parallel_task_2
    task: "Task 2"
    timeout: 30
    # No dependencies = runs in parallel with task_1
```

## Summary

In this tutorial, you learned:

✅ How to create a basic IOA Core workflow  
✅ How to configure steps and agents  
✅ How to run and monitor workflows  
✅ How to handle dependencies and errors  
✅ How to customize and extend workflows  

You're now ready to build more complex AI agent systems with IOA Core! 🚀

---

*Need help? Check the [FAQ](../user-guide/FAQ_IOA_CORE.md) or [Community Support](https://github.com/orchintel/ioa-core/discussions)*
