# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

#!/usr/bin/env bash
#
# Quick Test Status Checker
# Shows if test is running and approximate progress
#
set -euo pipefail

: "${AWS_PROFILE:=default}"
: "${AWS_REGION:=us-east-1}"
: "${INSTANCE_ID:=i-07866e3efe79fbe88}"
: "${COMMAND_ID:?COMMAND_ID required - pass as first argument}"

echo "🔍 IOA Performance Test Status Check"
echo "====================================="
echo "Command ID: $COMMAND_ID"
echo

# Check SSM command status
echo "SSM Command Status:"
STATUS=$(aws ssm get-command-invocation \
  --command-id "$COMMAND_ID" \
  --instance-id "$INSTANCE_ID" \
  --region "$AWS_REGION" \
  --query 'Status' \
  --output text 2>/dev/null || echo "UNKNOWN")

echo "  Status: $STATUS"

if [ "$STATUS" = "InProgress" ] || [ "$STATUS" = "Pending" ]; then
    echo "  ✅ TEST IS RUNNING"
    echo
    
    # Try to get recent logs
    echo "Checking for progress indicators..."
    aws ssm send-command \
      --instance-ids "$INSTANCE_ID" \
      --document-name "AWS-RunShellScript" \
      --parameters 'commands=["echo \"=== ACTIVE PYTEST PROCESS ===\"","ps aux | grep pytest | grep -v grep || echo \"No pytest process found\"","echo","echo \"=== LATEST LOG ENTRIES (last 10 lines) ===\"","tail -10 /tmp/perf_*.log 2>/dev/null | tail -10 || echo \"No logs yet\"","echo","echo \"=== MEMORY/DISK STATUS ===\"","free -h | grep Mem","df -h / | tail -1"]' \
      --region "$AWS_REGION" \
      --query 'Command.CommandId' \
      --output text > /tmp/status_check_cmd.txt
    
    STATUS_CMD=$(cat /tmp/status_check_cmd.txt)
    sleep 3
    
    echo
    aws ssm get-command-invocation \
      --command-id "$STATUS_CMD" \
      --instance-id "$INSTANCE_ID" \
      --region "$AWS_REGION" \
      --query 'StandardOutputContent' \
      --output text 2>/dev/null || echo "Could not fetch detailed status"
    
elif [ "$STATUS" = "Success" ]; then
    echo "  ✅ TEST COMPLETED SUCCESSFULLY"
    echo
    echo "Fetch results with:"
    echo "  aws s3 ls s3://ioa-perf-results-us-east-1-238836619152/ --recursive | grep -E \"(PERF|PERFORMANCE|summary)\""
    
elif [ "$STATUS" = "Failed" ]; then
    echo "  ❌ TEST FAILED"
    echo
    echo "Check error with:"
    echo "  aws ssm get-command-invocation --command-id $COMMAND_ID --instance-id $INSTANCE_ID --query 'StandardErrorContent' --output text"
    
else
    echo "  ⚠️  STATUS UNKNOWN: $STATUS"
fi

echo
echo "====================================="
echo "Check complete"



