# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

#!/bin/bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
WORKFLOW_FILE=""
JOB_NAME=""
USE_ACT=false
CI_GATES_MODE="monitor"
PYTHON_VERSION="3.11"

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if act is available
check_act() {
    if command -v act &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to setup local environment
setup_local_env() {
    print_status $YELLOW "Setting up local environment..."
    
    # Ensure we're in the repo root
    if [[ ! -f "pyproject.toml" ]]; then
        print_status $RED "Error: Not in repository root. Please run from the repo root directory."
        exit 1
    fi
    
    # Create artifacts directories
    mkdir -p artifacts/lens artifacts/logs artifacts/snapshots
    
    # Set up Python environment
    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
        print_status $YELLOW "No virtual environment detected. Using system Python."
        PYTHON_CMD="python3"
    else
        PYTHON_CMD="python"
    fi
    
    # Install dependencies
    print_status $YELLOW "Installing dependencies..."
    $PYTHON_CMD -m pip install -e .[dev] --quiet
    
    # Set environment variables
    export CI_GATES_MODE="$CI_GATES_MODE"
    export PYTHONWARNINGS="error"
    export PYTHON_CMD="$PYTHON_CMD"
    
    print_status $GREEN "Local environment ready"
}

# Function to run with act
run_with_act() {
    local workflow_file=$1
    local job_name=$2
    
    print_status $YELLOW "Running with act (GitHub Actions local runner)..."
    
    # Check if act is available
    if ! check_act; then
        print_status $RED "act not found. Please install act: https://github.com/nektos/act"
        print_status $YELLOW "Falling back to shell simulation..."
        run_shell_simulation "$workflow_file" "$job_name"
        return
    fi
    
    # Create a minimal .secrets file for act
    cat > .secrets << EOF
# Minimal secrets for local testing
GITHUB_TOKEN=dummy_token
EOF
    
    # Run act
    act -W "$workflow_file" -j "$job_name" --secret-file .secrets --env CI_GATES_MODE="$CI_GATES_MODE" --env PYTHON_CMD="$PYTHON_CMD"
    
    # Cleanup
    rm -f .secrets
}

# Function to run shell simulation
run_shell_simulation() {
    local workflow_file=$1
    local job_name=$2
    
    print_status $YELLOW "Running shell simulation (closest match)..."
    
    # Parse the workflow file to extract job steps
    if [[ ! -f "$workflow_file" ]]; then
        print_status $RED "Error: Workflow file '$workflow_file' not found"
        exit 1
    fi
    
    # Extract job steps using yq or python
    if command -v yq &> /dev/null; then
        steps=$(yq eval ".jobs.$job_name.steps[]" "$workflow_file" 2>/dev/null || echo "")
    else
        # Fallback to python
        steps=$(python3 -c "
import yaml
import sys
try:
    with open('$workflow_file', 'r') as f:
        workflow = yaml.safe_load(f)
    job = workflow.get('jobs', {}).get('$job_name', {})
    steps = job.get('steps', [])
    for step in steps:
        print(f\"{step.get('name', 'unnamed')}: {step.get('run', step.get('uses', 'no command'))}\")
except Exception as e:
    print(f'Error parsing workflow: {e}', file=sys.stderr)
    sys.exit(1)
")
    fi
    
    if [[ -z "$steps" ]]; then
        print_status $RED "Error: Could not extract steps for job '$job_name'"
        exit 1
    fi
    
    print_status $GREEN "Simulating job: $job_name"
    echo "Steps to execute:"
    echo "$steps"
    echo ""
    
    # Execute common patterns
    print_status $YELLOW "Executing common CI patterns..."
    
    # Python setup
    print_status $YELLOW "Setting up Python $PYTHON_VERSION..."
    $PYTHON_CMD --version
    
    # Install dependencies
    print_status $YELLOW "Installing dependencies..."
    $PYTHON_CMD -m pip install -e .[dev] --quiet
    
    # Run tests if they exist
    if [[ -d "tests" ]]; then
        print_status $YELLOW "Running tests..."
        $PYTHON_CMD -m pytest tests/ -q --tb=short
    fi
    
    # Run linting
    print_status $YELLOW "Running linting..."
    $PYTHON_CMD -m ruff check src/ tests/ --quiet || true
    $PYTHON_CMD -m black --check src/ tests/ --quiet || true
    
    # Run type checking
    print_status $YELLOW "Running type checking..."
    $PYTHON_CMD -m mypy src/ --ignore-missing-imports --quiet || true
    
    print_status $GREEN "Shell simulation complete"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS] WORKFLOW_FILE [JOB_NAME]"
    echo ""
    echo "Options:"
    echo "  -a, --act          Use act (GitHub Actions local runner) if available"
    echo "  -m, --mode MODE    Set CI_GATES_MODE (default: monitor)"
    echo "  -p, --python VER   Set Python version (default: 3.11)"
    echo "  -h, --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 .github/workflows/ci-gates.yml"
    echo "  $0 .github/workflows/python-tests.yml test"
    echo "  $0 -a .github/workflows/docs.yml build"
    echo ""
    echo "If act is not available, falls back to shell simulation."
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--act)
            USE_ACT=true
            shift
            ;;
        -m|--mode)
            CI_GATES_MODE="$2"
            shift 2
            ;;
        -p|--python)
            PYTHON_VERSION="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        -*)
            print_status $RED "Unknown option: $1"
            show_usage
            exit 1
            ;;
        *)
            if [[ -z "$WORKFLOW_FILE" ]]; then
                WORKFLOW_FILE="$1"
            elif [[ -z "$JOB_NAME" ]]; then
                JOB_NAME="$1"
            else
                print_status $RED "Too many arguments"
                show_usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate arguments
if [[ -z "$WORKFLOW_FILE" ]]; then
    print_status $RED "Error: WORKFLOW_FILE is required"
    show_usage
    exit 1
fi

# Set default job name if not provided
if [[ -z "$JOB_NAME" ]]; then
    # Try to extract the first job name from the workflow
    if command -v yq &> /dev/null; then
        JOB_NAME=$(yq eval '.jobs | keys | .[0]' "$WORKFLOW_FILE" 2>/dev/null || echo "default")
    else
        JOB_NAME="default"
    fi
fi

# Main execution
print_status $GREEN "IOA GHA Reproduction Tool"
print_status $GREEN "========================="
echo "Workflow: $WORKFLOW_FILE"
echo "Job: $JOB_NAME"
echo "Mode: $CI_GATES_MODE"
echo "Python: $PYTHON_VERSION"
echo "Use act: $USE_ACT"
echo ""

# Setup local environment
setup_local_env

# Run the workflow
if [[ "$USE_ACT" == "true" ]]; then
    run_with_act "$WORKFLOW_FILE" "$JOB_NAME"
else
    run_shell_simulation "$WORKFLOW_FILE" "$JOB_NAME"
fi

print_status $GREEN "Reproduction complete!"
