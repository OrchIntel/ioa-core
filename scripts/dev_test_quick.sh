# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

#!/bin/bash

# IOA Core Quick Test Runner
# This script runs a subset of tests for quick development feedback

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]]; then
    print_error "This script must be run from the IOA Core root directory"
    exit 1
fi

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    print_warning "Virtual environment not activated. Attempting to activate..."
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
        print_success "Virtual environment activated"
    else
        print_error "Virtual environment not found. Run ./scripts/dev_local_setup.sh first"
        exit 1
    fi
fi

# Function to run tests with timing
run_tests() {
    local test_path="$1"
    local test_name="$2"
    local start_time=$(date +%s)
    
    print_status "Running $test_name tests..."
    
    if pytest "$test_path" -v --tb=short --maxfail=3; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        print_success "$test_name tests completed in ${duration}s"
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        print_error "$test_name tests failed after ${duration}s"
        return 1
    fi
}

# Function to check test results
check_test_results() {
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    local skipped_tests=0
    
    # Parse pytest output for summary
    while IFS= read -r line; do
        if [[ $line =~ ([0-9]+)\ passed ]]; then
            passed_tests=${BASH_REMATCH[1]}
        elif [[ $line =~ ([0-9]+)\ failed ]]; then
            failed_tests=${BASH_REMATCH[1]}
        elif [[ $line =~ ([0-9]+)\ skipped ]]; then
            skipped_tests=${BASH_REMATCH[1]}
        fi
    done < <(pytest --collect-only 2>/dev/null | tail -5)
    
    total_tests=$((passed_tests + failed_tests + skipped_tests))
    
    echo ""
    echo "  Total: $total_tests"
    echo "  Passed: $passed_tests"
    echo "  Failed: $failed_tests"
    echo "  Skipped: $skipped_tests"
    
    if [[ $failed_tests -gt 0 ]]; then
        return 1
    else
        return 0
    fi
}

# Main execution
echo "🧪 IOA Core Quick Test Runner"
echo "=============================="
echo ""

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    print_error "pytest not found. Please install development dependencies first"
    exit 1
fi

# Check if tests directory exists
if [[ ! -d "tests" ]]; then
    print_error "Tests directory not found"
    exit 1
fi

# Run test collection first
print_status "Collecting test information..."
if pytest --collect-only > /dev/null 2>&1; then
    print_success "Test collection successful"
else
    print_warning "Test collection had issues"
fi

echo ""
print_status "Starting quick test suite..."

# Track overall success
overall_success=true

# 1. Unit tests (fastest)
if [[ -d "tests/unit" ]]; then
    if run_tests "tests/unit" "Unit"; then
        print_success "✅ Unit tests passed"
    else
        print_error "❌ Unit tests failed"
        overall_success=false
    fi
else
    print_warning "Unit tests directory not found, skipping"
fi

echo ""

# 2. Smoke tests (no external dependencies)
if [[ -d "tests/smoke" ]]; then
    if run_tests "tests/smoke" "Smoke"; then
        print_success "✅ Smoke tests passed"
    else
        print_error "❌ Smoke tests failed"
        overall_success=false
    fi
else
    print_warning "Smoke tests directory not found, skipping"
fi

echo ""

# 3. Basic integration tests (if they exist and are fast)
if [[ -d "tests/integration" ]]; then
    # Only run fast integration tests
    if run_tests "tests/integration" "Integration (fast)"; then
        print_success "✅ Integration tests passed"
    else
        print_error "❌ Integration tests failed"
        overall_success=false
    fi
else
    print_warning "Integration tests directory not found, skipping"
fi

echo ""

# 4. Schema validation tests
if [[ -d "tests" ]] && find tests -name "*schema*" -type f | grep -q .; then
    print_status "Running schema validation tests..."
    if pytest tests/ -k "schema" -v --tb=short --maxfail=3; then
        print_success "✅ Schema validation tests passed"
    else
        print_error "❌ Schema validation tests failed"
        overall_success=false
    fi
else
    print_warning "Schema validation tests not found, skipping"
fi

echo ""

# Final summary
echo "=============================="
if check_test_results; then
    print_success "🎉 Quick test suite completed successfully!"
else
    print_warning "⚠️  Some tests failed. Check the output above for details."
fi

echo ""
echo "Next steps:"
echo "  • Run full test suite: ./dev.sh test"
echo "  • Run specific tests: pytest tests/path/to/test.py -v"
echo "  • Check test coverage: pytest --cov=src tests/"
echo "  • Run linting: ./dev.sh lint"
echo ""

# Exit with appropriate code
if [[ "$overall_success" == true ]]; then
    exit 0
else
    exit 1
fi
