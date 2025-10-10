# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

#!/usr/bin/env bash
#
# Quick Test Status Checker
# Usage: ./quick_status.sh [COMMAND_ID]
#
set -euo pipefail

: "${AWS_PROFILE:=default}"
: "${AWS_REGION:=us-east-1}"
: "${INSTANCE_ID:=i-07866e3efe79fbe88}"

# Get command ID from argument or use latest
if [ $# -eq 0 ]; then
    echo "Getting latest command ID..."
    COMMAND_ID=$(aws ssm list-commands --region "$AWS_REGION" --max-items 1 --query 'Commands[0].CommandId' --output text)
    echo "Latest Command ID: $COMMAND_ID"
else
    COMMAND_ID="$1"
fi

echo "🔍 Test Status Check"
echo "===================="
echo "Command ID: $COMMAND_ID"
echo

# Get status
STATUS=$(aws ssm get-command-invocation \
    --command-id "$COMMAND_ID" \
    --instance-id "$INSTANCE_ID" \
    --region "$AWS_REGION" \
    --query 'Status' \
    --output text 2>/dev/null || echo "UNKNOWN")

echo "Status: $STATUS"
echo

if [ "$STATUS" = "InProgress" ] || [ "$STATUS" = "Pending" ]; then
    echo "✅ TEST IS RUNNING"
    echo
    echo "Check active processes:"
    aws ssm send-command \
        --instance-ids "$INSTANCE_ID" \
        --document-name "AWS-RunShellScript" \
        --parameters 'commands=["ps aux | grep pytest | grep -v grep || echo \"No pytest running\""]' \
        --region "$AWS_REGION" \
        --query 'Command.CommandId' \
        --output text > /tmp/status_cmd.txt
    
    sleep 3
    STATUS_CMD=$(cat /tmp/status_cmd.txt)
    aws ssm get-command-invocation \
        --command-id "$STATUS_CMD" \
        --instance-id "$INSTANCE_ID" \
        --region "$AWS_REGION" \
        --query 'StandardOutputContent' \
        --output text 2>/dev/null || true
    
elif [ "$STATUS" = "Success" ]; then
    echo "✅ TEST COMPLETED"
    echo
    echo "Check results with:"
    echo "  aws s3 ls s3://ioa-perf-results-us-east-1-238836619152/ --recursive | tail -20"
    
elif [ "$STATUS" = "Failed" ]; then
    echo "❌ TEST FAILED"
    echo
    echo "Get error details:"
    aws ssm get-command-invocation \
        --command-id "$COMMAND_ID" \
        --instance-id "$INSTANCE_ID" \
        --region "$AWS_REGION" \
        --query '[StandardOutputContent,StandardErrorContent]' \
        --output text 2>/dev/null | tail -50 || true
fi

echo
echo "===================="


