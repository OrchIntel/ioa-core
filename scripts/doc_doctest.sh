# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

#!/bin/bash


set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCS_DIR="docs"
PYTHON_FILES=()
PYTEST_ARGS=""
VERBOSE=false
FAIL_FAST=false

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Run doctests for documentation code blocks referenced by mkdocs.

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    -f, --fail-fast         Stop on first failure
    -d, --docs-dir DIR      Documentation directory (default: docs)
    --pytest-args ARGS      Additional pytest arguments

EXAMPLES:
    $0                           # Run with default settings
    $0 -v                       # Verbose output
    $0 --fail-fast             # Stop on first failure
    $0 --pytest-args "-xvs"    # Pass custom pytest arguments

EOF
}

# Function to parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -f|--fail-fast)
                FAIL_FAST=true
                shift
                ;;
            -d|--docs-dir)
                DOCS_DIR="$2"
                shift 2
                ;;
            --pytest-args)
                PYTEST_ARGS="$2"
                shift 2
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Function to find Python files in documentation
find_python_files() {
    print_status "Scanning documentation directory: $DOCS_DIR"
    
    if [[ ! -d "$DOCS_DIR" ]]; then
        print_error "Documentation directory not found: $DOCS_DIR"
        exit 1
    fi
    
    # Find all Python files in docs directory
    PYTHON_FILES=($(find "$DOCS_DIR" -name "*.py" -type f))
    
    if [[ ${#PYTHON_FILES[@]} -eq 0 ]]; then
        print_warning "No Python files found in documentation directory"
        return
    fi
    
    print_status "Found ${#PYTHON_FILES[@]} Python files:"
    for file in "${PYTHON_FILES[@]}"; do
        echo "  - $file"
    done
}

# Function to check if file has doctests
has_doctests() {
    local file="$1"
    if grep -q ">>>" "$file" || grep -q "\.\.\." "$file"; then
        return 0
    else
        return 1
    fi
}

# Function to run doctests for a file
run_doctests() {
    local file="$1"
    local relative_path="${file#$DOCS_DIR/}"
    
    print_status "Running doctests for: $relative_path"
    
    if ! has_doctests "$file"; then
        print_warning "No doctests found in: $relative_path"
        return 0
    fi
    
    # Run doctest using pytest
    local pytest_cmd="python -m pytest --doctest-modules"
    
    if [[ "$VERBOSE" == true ]]; then
        pytest_cmd="$pytest_cmd -v"
    fi
    
    if [[ "$FAIL_FAST" == true ]]; then
        pytest_cmd="$pytest_cmd -x"
    fi
    
    if [[ -n "$PYTEST_ARGS" ]]; then
        pytest_cmd="$pytest_cmd $PYTEST_ARGS"
    fi
    
    pytest_cmd="$pytest_cmd \"$file\""
    
    if [[ "$VERBOSE" == true ]]; then
        echo "Command: $pytest_cmd"
    fi
    
    if eval "$pytest_cmd"; then
        print_success "Doctests passed for: $relative_path"
        return 0
    else
        print_error "Doctests failed for: $relative_path"
        return 1
    fi
}

# Function to run all doctests
run_all_doctests() {
    local failed_files=()
    local total_files=0
    local passed_files=0
    
    print_status "Starting doctest execution..."
    
    for file in "${PYTHON_FILES[@]}"; do
        total_files=$((total_files + 1))
        
        if run_doctests "$file"; then
            passed_files=$((passed_files + 1))
        else
            failed_files+=("$file")
            if [[ "$FAIL_FAST" == true ]]; then
                break
            fi
        fi
    done
    
    # Summary
    echo
    echo "  Total files: $total_files"
    echo "  Passed: $passed_files"
    echo "  Failed: ${#failed_files[@]}"
    
    if [[ ${#failed_files[@]} -gt 0 ]]; then
        echo
        print_error "Failed files:"
        for file in "${failed_files[@]}"; do
            echo "  - ${file#$DOCS_DIR/}"
        done
        return 1
    else
        print_success "All doctests passed!"
        return 0
    fi
}

# Function to check dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v python &> /dev/null; then
        print_error "Python is not installed or not in PATH"
        exit 1
    fi
    
    if ! python -c "import pytest" &> /dev/null; then
        print_error "pytest is not installed. Install with: pip install pytest"
        exit 1
    fi
    
    print_success "Dependencies check passed"
}

# Main function
main() {
    print_status "IOA Documentation Doctest Runner"
    echo "Date: $(date)"
    echo
    
    # Parse arguments
    parse_args "$@"
    
    # Check dependencies
    check_dependencies
    
    # Find Python files
    find_python_files
    
    if [[ ${#PYTHON_FILES[@]} -eq 0 ]]; then
        print_warning "No Python files to test"
        exit 0
    fi
    
    # Run doctests
    if run_all_doctests; then
        print_success "All documentation doctests completed successfully"
        exit 0
    else
        print_error "Some documentation doctests failed"
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
