# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

#!/bin/bash

# IOA Core Minimal Development Helper Script

case "$1" in
    "test")
        echo "🧪 Running tests..."
        pytest "${@:2}"
        ;;
    "test-quick")
        echo "⚡ Running quick tests..."
        pytest tests/unit/ tests/smoke/ -v
        ;;
    "test-integration")
        echo "🔗 Running integration tests..."
        pytest tests/integration/ -v
        ;;
    "clean")
        echo "🧹 Cleaning up..."
        find . -type d -name "__pycache__" -exec rm -rf {} +
        find . -type f -name "*.pyc" -delete
        find . -type f -name "*.pyo" -delete
        find . -type f -name "*.pyd" -delete
        find . -type d -name "*.egg-info" -exec rm -rf {} +
        find . -type d -name ".pytest_cache" -exec rm -rf {} +
        find . -type d -name ".coverage" -delete
        ;;
    "help"|"--help"|"-h"|"")
        echo "IOA Core Minimal Development Helper"
        echo ""
        echo "Usage: ./dev-minimal.sh <command> [options]"
        echo ""
        echo "Commands:"
        echo "  test              Run all tests"
        echo "  test-quick        Run quick tests (unit + smoke)"
        echo "  test-integration  Run integration tests"
        echo "  clean             Clean up cache files"
        echo "  help              Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./dev-minimal.sh test-quick"
        echo "  ./dev-minimal.sh test tests/unit/test_agent_router.py"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Run './dev-minimal.sh help' for usage information"
        exit 1
        ;;
esac
