# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

#!/usr/bin/env bash
#
# Safe Performance Test Runner with Error Handling
# Wrapper around run_perf.sh with comprehensive error handling and monitoring
#
set -euo pipefail

: "${PERF_MARKER:=smoke}"
: "${IOA_TEST_RECORDS:=10}"
: "${AWS_REGION:=us-east-1}"
: "${S3_BUCKET:=}"
: "${S3_PREFIX:=}"
: "${MAX_DURATION_SECONDS:=3600}"
: "${HEARTBEAT_INTERVAL:=30}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/perf_${PERF_MARKER}_$(date +%Y%m%d_%H%M%S).log"
STATUS_FILE="/tmp/perf_status.json"

echo "🚀 IOA Safe Performance Test Runner"
echo "==================================="
echo "Marker: $PERF_MARKER"
echo "Records: $IOA_TEST_RECORDS"
echo "Log: $LOG_FILE"
echo

# Function: Log with timestamp
log() {
    echo "[$(date -Iseconds)] $*" | tee -a "$LOG_FILE"
}

# Function: Update status file
update_status() {
    local status="$1"
    local message="$2"
    cat > "$STATUS_FILE" << EOF
{
  "status": "$status",
  "message": "$message",
  "timestamp": "$(date -Iseconds)",
  "marker": "$PERF_MARKER",
  "records": $IOA_TEST_RECORDS,
  "log_file": "$LOG_FILE"
}
EOF
}

# Function: Cleanup on exit
cleanup() {
    local exit_code=$?
    log "Cleanup triggered (exit code: $exit_code)"
    
    # Kill heartbeat if running
    if [ -n "${HEARTBEAT_PID:-}" ]; then
        kill "$HEARTBEAT_PID" 2>/dev/null || true
    fi
    
    # Upload logs to S3 if configured (before cleanup)
    if [ -n "$S3_BUCKET" ] && [ -n "$S3_PREFIX" ]; then
        log "Uploading logs to S3..."
        aws s3 cp "$LOG_FILE" "s3://$S3_BUCKET/$S3_PREFIX" --region "$AWS_REGION" 2>&1 | tee -a "$LOG_FILE" || true
        aws s3 cp "$STATUS_FILE" "s3://$S3_BUCKET/$S3_PREFIX" --region "$AWS_REGION" 2>&1 | tee -a "$LOG_FILE" || true
        
        # Upload performance artifacts if they exist
        if [ -d "/tmp/perf" ]; then
            log "Uploading performance artifacts..."
            aws s3 cp /tmp/perf/ "s3://$S3_BUCKET/$S3_PREFIX" --recursive --region "$AWS_REGION" 2>&1 | tee -a "$LOG_FILE" || true
        fi
    fi
    
    # Clean up test artifacts (after S3 upload)
    log "Cleaning up test artifacts..."
    DISK_BEFORE=$(df / | tail -1 | awk '{print int($3/1024)}')
    
    # Remove SQLite databases from this test run
    rm -rf artifacts/memory/*.db* 2>/dev/null || true
    rm -rf artifacts/lens/*.db* 2>/dev/null || true
    
    # Remove test results
    rm -rf test_results/*.log 2>/dev/null || true
    rm -rf test_results/*.xml 2>/dev/null || true
    
    # Remove temporary performance files
    rm -rf /tmp/perf 2>/dev/null || true
    
    # Remove old log files (keep only last 5)
    cd /tmp && ls -t perf_*.log 2>/dev/null | tail -n +6 | xargs -r rm 2>/dev/null || true
    
    DISK_AFTER=$(df / | tail -1 | awk '{print int($3/1024)}')
    FREED=$((DISK_BEFORE - DISK_AFTER))
    
    log "Disk cleanup complete: Freed ${FREED}MB"
    log "Current disk usage: $(df -h / | tail -1 | awk '{print $5}')"
    
    log "Cleanup complete"
}

trap cleanup EXIT INT TERM

# Step 1: Pre-flight check
log "Running pre-flight check..."
update_status "preflight" "Running environment checks"

if ! bash "$SCRIPT_DIR/ec2_perf_preflight.sh" 2>&1 | tee -a "$LOG_FILE"; then
    log "❌ Pre-flight check failed"
    update_status "failed" "Pre-flight check failed - insufficient resources"
    exit 1
fi

log "✅ Pre-flight check passed"

# Step 2: Start heartbeat
log "Starting heartbeat monitor..."
update_status "running" "Test in progress"

(
    while true; do
        log "💓 Heartbeat: Test running (marker=$PERF_MARKER, records=$IOA_TEST_RECORDS)"
        
        # Check disk space during test
        AVAILABLE_MB=$(df / | tail -1 | awk '{print int($4/1024)}')
        if [ "$AVAILABLE_MB" -lt 500 ]; then
            log "⚠️  WARNING: Low disk space - ${AVAILABLE_MB}MB available"
        fi
        
        sleep "$HEARTBEAT_INTERVAL"
    done
) &
HEARTBEAT_PID=$!

# Step 3: Run test with timeout
log "Starting performance test..."
START_TIME=$(date +%s)

set +e
timeout "$MAX_DURATION_SECONDS" bash "$SCRIPT_DIR/run_perf.sh" 2>&1 | tee -a "$LOG_FILE"
TEST_EXIT_CODE=$?
set -e

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Step 4: Analyze results
log "Test completed with exit code: $TEST_EXIT_CODE"
log "Duration: ${DURATION}s"

if [ $TEST_EXIT_CODE -eq 124 ]; then
    # Timeout
    log "❌ Test timed out after ${MAX_DURATION_SECONDS}s"
    update_status "timeout" "Test exceeded maximum duration of ${MAX_DURATION_SECONDS}s"
    exit 124
elif [ $TEST_EXIT_CODE -ne 0 ]; then
    # Other error
    log "❌ Test failed with exit code: $TEST_EXIT_CODE"
    
    # Analyze common errors
    if grep -q "No space left on device" "$LOG_FILE"; then
        log "Root cause: Disk space exhausted"
        update_status "failed" "Disk space exhausted during test"
    elif grep -q "MemoryError" "$LOG_FILE"; then
        log "Root cause: Out of memory"
        update_status "failed" "Out of memory during test"
    elif grep -q "database is locked" "$LOG_FILE"; then
        log "Root cause: SQLite database lock"
        update_status "failed" "Database lock - possible concurrent access or disk I/O issue"
    else
        log "Root cause: Unknown error"
        update_status "failed" "Test failed with exit code $TEST_EXIT_CODE"
    fi
    
    exit $TEST_EXIT_CODE
else
    # Success
    log "✅ Test completed successfully"
    update_status "success" "Test completed in ${DURATION}s"
    
    # Extract key metrics if available
    if [ -f "/tmp/perf/PERF_SCORECARD.md" ]; then
        log "Performance scorecard generated"
        cat "/tmp/perf/PERF_SCORECARD.md" | tee -a "$LOG_FILE"
    fi
fi

log "==================================="
log "Test run complete"
log "Exit code: $TEST_EXIT_CODE"
log "Duration: ${DURATION}s"
log "Log file: $LOG_FILE"
log "==================================="

