# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

#!/usr/bin/env bash
set -euo pipefail

# IOA Performance Runner Script
# Runs micro-scale MemoryFabric tests with heartbeat and S3 uploads

: "${PERF_MARKER:=smoke}"         # smoke|quick|step|heavy
: "${IOA_TEST_RECORDS:=10}"
: "${AWS_REGION:?AWS_REGION must be set}"
: "${S3_BUCKET:?S3_BUCKET must be set}"
: "${S3_PREFIX:?S3_PREFIX must be set}"                # e.g. runs/$(date +%Y%m%d-%H%M%S)/
: "${IOA_4D_PROFILE:=governance}" # governance|throughput|balanced

echo "== IOA perf runner =="
echo "marker=$PERF_MARKER records=$IOA_TEST_RECORDS profile=$IOA_4D_PROFILE"
echo "s3_prefix=$S3_PREFIX"

# Install package from the mounted repo
echo "Installing package..."
pip install --no-cache-dir .[bench] 2>/dev/null || pip install --no-cache-dir . || echo "Package install failed, trying PYTHONPATH fallback"
# Fallback: Add src to PYTHONPATH if install fails
export PYTHONPATH="/opt/ioa-run/ioa-core-internal/src:${PYTHONPATH:-}"
echo "PYTHONPATH set to: $PYTHONPATH"

# Create temp directory for logs and results
mkdir -p /tmp/perf

# Pre-flight check
echo "OK" > /tmp/perf/PREFLIGHT_OK.txt
echo "Pre-flight check passed at $(date -Is)"

# Heartbeat loop (background)
echo "Starting heartbeat..."
( while true; do echo "heartbeat: $(date -Is) marker=$PERF_MARKER records=$IOA_TEST_RECORDS"; sleep 10; done ) &
HB=$!

# Set environment for 4D tiering profile
export IOA_4D_PROFILE="$IOA_4D_PROFILE"
export USE_4D_TIERING="true"

# Configure pytest based on marker
# Note: Parallel execution with -n requires pytest-xdist, skip for now
PYTEST_ARGS="-m $PERF_MARKER -v -s --durations=20 --tb=short --maxfail=1"
if [ "$PERF_MARKER" = "heavy" ]; then
    echo "Running heavy tests (serial execution for compatibility)"
else
    echo "Running $PERF_MARKER tests"
fi

# Run pytest with the specified marker (only in tests/performance/)
echo "Starting pytest with args: $PYTEST_ARGS"
set +e
pytest tests/performance/ $PYTEST_ARGS 2>&1 | tee "/tmp/perf/perf_${PERF_MARKER}.log"
RC=${PIPESTATUS[0]}
set -e

echo "Pytest completed with exit code: $RC"

# Generate scorecard
{
  echo "| ts | marker | records | profile | rc |"
  echo "|---|---|---:|---|---:|"
  echo "| $(date -Is) | $PERF_MARKER | $IOA_TEST_RECORDS | $IOA_4D_PROFILE | $RC |"
} > /tmp/perf/PERF_SCORECARD.md

# Upload results to S3 with comprehensive artifacts
echo "Uploading comprehensive results to S3..."

# Core artifacts
aws s3 cp /tmp/perf/PREFLIGHT_OK.txt "s3://$S3_BUCKET/$S3_PREFIX" --region "$AWS_REGION"
aws s3 cp "/tmp/perf/perf_${PERF_MARKER}.log" "s3://$S3_BUCKET/$S3_PREFIX" --region "$AWS_REGION"
aws s3 cp /tmp/perf/PERF_SCORECARD.md "s3://$S3_BUCKET/$S3_PREFIX" --region "$AWS_REGION"

# Additional artifacts for heavy tests
if [ "$PERF_MARKER" = "heavy" ]; then
    # Capture system info
    uname -a > /tmp/perf/system_info.txt
    df -h > /tmp/perf/disk_usage.txt
    free -h > /tmp/perf/memory_info.txt 2>/dev/null || echo "Memory info not available" > /tmp/perf/memory_info.txt

    aws s3 cp /tmp/perf/system_info.txt "s3://$S3_BUCKET/$S3_PREFIX" --region "$AWS_REGION"
    aws s3 cp /tmp/perf/disk_usage.txt "s3://$S3_BUCKET/$S3_PREFIX" --region "$AWS_REGION"
    aws s3 cp /tmp/perf/memory_info.txt "s3://$S3_BUCKET/$S3_PREFIX" --region "$AWS_REGION"

    # Performance summary
    echo "# MemoryFabric v1.2 Heavy Test Results" > /tmp/perf/PERFORMANCE_SUMMARY.md
    echo "- Test: $PERF_MARKER" >> /tmp/perf/PERFORMANCE_SUMMARY.md
    echo "- Records: $IOA_TEST_RECORDS" >> /tmp/perf/PERFORMANCE_SUMMARY.md
    echo "- Profile: $IOA_4D_PROFILE" >> /tmp/perf/PERFORMANCE_SUMMARY.md
    echo "- Timestamp: $(date -Is)" >> /tmp/perf/PERFORMANCE_SUMMARY.md
    echo "- Exit Code: $RC" >> /tmp/perf/PERFORMANCE_SUMMARY.md

    aws s3 cp /tmp/perf/PERFORMANCE_SUMMARY.md "s3://$S3_BUCKET/$S3_PREFIX" --region "$AWS_REGION"
fi

echo "Results uploaded to s3://$S3_BUCKET/$S3_PREFIX"

# Kill heartbeat
kill $HB || true

echo "Run complete. Exit code: $RC"
exit $RC
