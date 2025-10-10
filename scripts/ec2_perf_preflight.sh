# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

#!/usr/bin/env bash
#
# EC2 Performance Test Pre-Flight Check
# Ensures environment is ready before running performance tests
#
set -euo pipefail

: "${MIN_DISK_GB:=2}"
: "${MIN_MEM_GB:=2}"
: "${CLEANUP_ARTIFACTS:=true}"

echo "🔍 IOA Performance Test Pre-Flight Check"
echo "========================================"
echo

# Check disk space
echo "📊 Checking disk space..."
AVAILABLE_GB=$(df / | tail -1 | awk '{print int($4/1024/1024)}')
USED_PERCENT=$(df / | tail -1 | awk '{print int($5)}' | tr -d '%')

echo "  Available: ${AVAILABLE_GB}GB"
echo "  Used: ${USED_PERCENT}%"

if [ "$AVAILABLE_GB" -lt "$MIN_DISK_GB" ]; then
    echo "  ❌ INSUFFICIENT DISK SPACE"
    echo "  Required: ${MIN_DISK_GB}GB, Available: ${AVAILABLE_GB}GB"
    
    if [ "$CLEANUP_ARTIFACTS" = "true" ]; then
        echo
        echo "🧹 Attempting automatic cleanup..."
        
        # Clean old artifacts
        rm -rf artifacts/memory/*.db* 2>/dev/null || true
        rm -rf artifacts/lens/*.db* 2>/dev/null || true
        rm -rf test_results/*.log 2>/dev/null || true
        rm -rf reports/pytest/*.xml 2>/dev/null || true
        rm -rf .pytest_cache 2>/dev/null || true
        
        # Re-check
        AVAILABLE_GB=$(df / | tail -1 | awk '{print int($4/1024/1024)}')
        echo "  After cleanup: ${AVAILABLE_GB}GB available"
        
        if [ "$AVAILABLE_GB" -lt "$MIN_DISK_GB" ]; then
            echo "  ❌ STILL INSUFFICIENT - Manual intervention required"
            exit 1
        else
            echo "  ✅ Cleanup successful"
        fi
    else
        exit 1
    fi
else
    echo "  ✅ Sufficient disk space"
fi

# Check memory
echo
echo "💾 Checking memory..."
AVAILABLE_MEM_GB=$(free -g | grep Mem | awk '{print $7}')
echo "  Available: ${AVAILABLE_MEM_GB}GB"

if [ "$AVAILABLE_MEM_GB" -lt "$MIN_MEM_GB" ]; then
    echo "  ⚠️  LOW MEMORY WARNING"
    echo "  Required: ${MIN_MEM_GB}GB, Available: ${AVAILABLE_MEM_GB}GB"
    echo "  Continuing anyway..."
else
    echo "  ✅ Sufficient memory"
fi

# Check Python environment
echo
echo "🐍 Checking Python environment..."
if ! python3 -c "import sys; sys.path.insert(0, 'src'); from ioa_core.memory_fabric.fabric import MemoryFabric; print('OK')" > /dev/null 2>&1; then
    echo "  ❌ Python environment check failed"
    exit 1
else
    echo "  ✅ Python environment OK"
fi

# Check pytest availability
echo
echo "🧪 Checking pytest..."
if ! python3 -m pytest --version > /dev/null 2>&1; then
    echo "  ❌ pytest not available"
    exit 1
else
    echo "  ✅ pytest available"
fi

# Summary
echo
echo "========================================"
echo "✅ PRE-FLIGHT CHECK PASSED"
echo
echo "Environment Ready:"
echo "  Disk: ${AVAILABLE_GB}GB available (${USED_PERCENT}% used)"
echo "  Memory: ${AVAILABLE_MEM_GB}GB available"
echo "  Python: OK"
echo "  Pytest: OK"
echo
echo "Recommended test parameters:"
if [ "$AVAILABLE_GB" -lt 5 ]; then
    echo "  ⚠️  Limited disk - recommend IOA_TEST_RECORDS=10000"
elif [ "$AVAILABLE_GB" -lt 10 ]; then
    echo "  IOA_TEST_RECORDS=50000"
else
    echo "  IOA_TEST_RECORDS=100000+"
fi
echo
echo "========================================"



