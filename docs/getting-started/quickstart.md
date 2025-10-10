**Version:** v2.5.0  
Last-Updated: 2025-10-09

<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2025 OrchIntel Systems Ltd.
<!-- https://orchintel.com | https://ioa.systems
<!--
<!-- Part of IOA Core (Open Source Edition). See LICENSE at repo root.
-->

# Quickstart Guide

Get up and running with IOA Core in under 10 minutes! This guide will walk you through the essential steps to create and run your first AI agent workflow.

## Prerequisites

- ✅ [IOA Core installed](installation.md)
- ✅ Python 3.9+ and pip available
- ✅ Basic command line knowledge

## Step 1: Verify Installation (1 minute)

First, let's make sure everything is working:

> **Note**: Some commands below are examples for future functionality.

```bash
# Check IOA Core version
# Example (not currently implemented): ioa --version

# Verify system health
# Example (not currently implemented): ioa health

# Expected output:
# IOA Core v2.5.0
# ✅ System health check passed
```

## Step 2: Initialize Configuration (2 minutes)

Set up your basic configuration:

> **Note**: Some commands below are examples for future functionality.

```bash
# Initialize configuration
# Example (not currently implemented): ioa config init

# Show current settings
# Example (not currently implemented): ioa config show

# Set basic preferences
# Example (not currently implemented): ioa config set environment development
# Example (not currently implemented): ioa config set log_level INFO
```

## Step 3: Create Your First Project (2 minutes)

Create a new IOA project:

> **Note**: Some commands below are examples for future functionality.

```bash
# Create project with basic template
# Example (not currently implemented): ioa boot --project-name my-first-project --template basic

# Navigate to project directory
cd my-first-project.ioa

# Check project structure
ls -la
```

You should see a directory structure like:
```
my-first-project.ioa/
├── config/
│   ├── agents.json
│   ├── workflows.yaml
│   └── governance.json
├── schemas/
│   └── message_schema.json
├── agents/
│   └── README.md
└── README.md
```

## Step 4: Create a Simple Workflow (2 minutes)

Create your first workflow file:

> **Note**: Some commands below are examples for future functionality.

```bash
# Create workflow file
cat > workflow.yaml << 'EOF'
# name: My First Workflow
# description: A simple workflow to test IOA Core

# steps:
#   - name: introduction
#     task: "Introduce yourself and explain what you can do"
#     timeout: 30
#     output_format: "text"

#   - name: analysis
#     task: "Analyze the introduction and provide insights"
#     depends_on: [introduction]
#     timeout: 45
#     output_format: "json"
# EOF
```

## Step 5: Run Your Workflow (2 minutes)

Execute your first workflow:

> **Note**: Some commands below are examples for future functionality.

```bash
# Validate the workflow
# Example (not currently implemented): ioa workflows validate workflow.yaml

# Run the workflow
# Example (not currently implemented): ioa workflows run --file workflow.yaml --verbose

# Check status
# Example (not currently implemented): ioa workflows status
```

## Step 6: View Results (1 minute)

Explore what your workflow produced:

> **Note**: Some commands below are examples for future functionality.

```bash
# View workflow results
# Example (not currently implemented): ioa workflows results

# Check memory for stored data
# Example (not currently implemented): ioa memory status

# List memory entries
# Example (not currently implemented): ioa memory list --type all --limit 10
```

## What Just Happened?

Let's break down what we accomplished:

### 1. **Project Creation**
- Created a new IOA project with basic configuration
- Set up directory structure for agents, workflows, and schemas
- Initialized governance and audit settings

### 2. **Workflow Definition**
- Defined a two-step workflow using YAML DSL
- First step: Introduction using `hello_agent`
- Second step: Analysis using `analysis_agent`
- Established dependencies between steps

### 3. **Execution**
- IOA Core orchestrated the workflow execution
- Managed agent communication and data flow
- Stored results in the memory engine
- Applied governance policies and audit logging

### 4. **Results**
- Generated structured output from each step
- Stored data in hot/cold memory storage
- Created audit trail of all operations
- Provided execution metrics and timing

## Understanding the Components

### **Agents**
- `hello_agent`: Simple greeting and introduction
- `analysis_agent`: Data analysis and insights
- `summary_agent`: Text summarization
- `code_agent`: Code generation and review

### **Workflow DSL**
- **YAML-based** configuration
- **Step dependencies** for execution order
- **Timeout controls** for resource management
- **Output formats** for structured data

### **Memory Engine**
- **Hot storage**: Fast access, limited size
- **Cold storage**: Persistent, larger capacity
- **Automatic pruning** for resource management
- **Audit logging** for compliance

## Next Steps

Now that you've completed the quickstart, explore:

### **Immediate Next Steps**
1. **Modify the workflow** - Add more steps or change tasks
2. **Test different agents** - Try `summary_agent` or `code_agent`
3. **Add dependencies** - Create more complex workflow chains

### **Advanced Features**
1. **[Governance Tutorial](../tutorials/governance-audit.md)** - Security and compliance
2. **[PKI Tutorial](../tutorials/pki-onboarding.md)** - Agent verification
3. **[CLI Reference](../user-guide/cli-reference.md)** - All available commands
4. **[Configuration Guide](configuration.md)** - Advanced settings

### **Examples to Try**

#### **Multi-Step Analysis**
```yaml
name: Data Analysis Pipeline
description: Analyze and summarize data

steps:
  - name: data_collection
    task: "Collect sample data"
    timeout: 30

  - name: data_analysis
    task: "Analyze the collected data"
    depends_on: [data_collection]
    timeout: 45

  - name: generate_report
    task: "Create a summary report"
    depends_on: [data_analysis]
    timeout: 30
```

#### **Parallel Execution**
```yaml
name: Parallel Processing
description: Execute tasks in parallel

steps:
  - name: task_a
    task: "Process task A"
    timeout: 30

  - name: task_b
    task: "Process task B"
    timeout: 30
    # No dependencies = runs in parallel with task_a
```

## Troubleshooting

### **Common Issues**

#### **"Agent not found" Error**
> **Note**: Some commands below are examples for future functionality.

```bash
# Check available agents
# Example (not currently implemented): ioa agents list

# Verify agent configuration
# Example (not currently implemented): ioa agents show hello_agent
```

#### **Workflow Validation Errors**
> **Note**: Some commands below are examples for future functionality.

```bash
# Check YAML syntax
# yamllint workflow.yaml

# Validate against schema
# Example (not currently implemented): ioa workflows validate workflow.yaml --schema
```

#### **Permission Issues**
```bash
# Check file permissions
ls -la workflow.yaml

# Fix permissions if needed
chmod 644 workflow.yaml
```

### **Getting Help**

> **Note**: Some commands below are examples for future functionality.

```bash
# Command help
# Example (not currently implemented): ioa workflows --help

# Agent help
# Example (not currently implemented): ioa agents --help

# General help
# Example (not currently implemented): ioa --help
```

## Performance Tips

### **Optimize Your Workflows**

1. **Set appropriate timeouts** - Don't set unnecessarily long timeouts
2. **Use dependencies wisely** - Only add dependencies when necessary
3. **Choose the right agents** - Use specialized agents for specific tasks
4. **Monitor resource usage** - Check memory and CPU usage

### **Development Best Practices**

1. **Start simple** - Begin with basic workflows and add complexity
2. **Test incrementally** - Test each step before adding the next
3. **Use dry-run mode** - Validate workflows without execution
4. **Monitor logs** - Check execution logs for debugging

## Summary

In this quickstart, you:

✅ **Installed and configured** IOA Core  
✅ **Created your first project** with proper structure  
✅ **Built a multi-step workflow** using YAML DSL  
✅ **Executed and monitored** workflow execution  
✅ **Explored results** and memory storage  
✅ **Learned basic concepts** of agents and workflows  

You're now ready to build more sophisticated AI agent systems! 🚀

---

*Need help? Check the [FAQ](../user-guide/FAQ_IOA_CORE.md) or [Community Support](https://github.com/orchintel/ioa-core/discussions)*
