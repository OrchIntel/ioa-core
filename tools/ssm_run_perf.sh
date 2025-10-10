# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

#!/usr/bin/env bash
set -euo pipefail

# IOA SSM Performance Runner
# Executes Docker container on EC2 instance via SSM to run MemoryFabric perf tests

: "${AWS_PROFILE:=default}"
: "${AWS_REGION:=us-east-1}"
: "${INSTANCE_ID:?INSTANCE_ID must be set}"
: "${S3_BUCKET:?S3_BUCKET must be set}"
: "${S3_PREFIX:?S3_PREFIX must be set}"
: "${PERF_MARKER:=smoke}"
: "${IOA_TEST_RECORDS:=10}"
: "${IOA_4D_PROFILE:=governance}"

echo "== IOA SSM Perf Runner =="
echo "Instance: $INSTANCE_ID"
echo "Marker: $PERF_MARKER"
echo "Records: $IOA_TEST_RECORDS"
echo "Profile: $IOA_4D_PROFILE"
echo "S3: s3://$S3_BUCKET/$S3_PREFIX"

# Step 1: Ensure Docker is installed on the EC2 instance
echo "Ensuring Docker is installed on EC2 instance..."
aws --profile "$AWS_PROFILE" --region "$AWS_REGION" ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters commands='[
"#!/bin/bash",
"set -e",
"if ! command -v docker &> /dev/null; then",
"  echo Installing Docker...",
"  sudo apt-get update -y",
"  sudo apt-get install -y docker.io",
"  sudo systemctl enable --now docker",
"  sudo usermod -aG docker ubuntu || true",
"  echo Docker installed successfully",
"else",
"  echo Docker already installed",
"fi",
"sudo systemctl status docker --no-pager || true",
"docker --version"
]' >/dev/null

echo "Waiting for Docker installation to complete..."
sleep 10

# Step 2: Verify repo exists on instance
echo "Verifying repo exists at /opt/ioa-run/ioa-core-internal..."
aws --profile "$AWS_PROFILE" --region "$AWS_REGION" ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters commands='[
"#!/bin/bash",
"set -e",
"if [ ! -d /opt/ioa-run/ioa-core-internal ]; then",
"  echo ERROR: Repository not found at /opt/ioa-run/ioa-core-internal",
"  echo Please ensure the repo is copied to the instance first",
"  exit 1",
"fi",
"echo Repository verified: /opt/ioa-run/ioa-core-internal",
"ls -la /opt/ioa-run/ioa-core-internal/ | head -10"
]' >/dev/null

# Step 3: Run the performance test in Docker container
echo "Starting Docker container with performance tests..."
aws --profile "$AWS_PROFILE" --region "$AWS_REGION" ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters commands="[
\"#!/bin/bash\",
\"set -e\",
\"cd /opt/ioa-run\",
\"echo Starting IOA perf test in Docker...\",
\"echo Marker: $PERF_MARKER, Records: $IOA_TEST_RECORDS, Profile: $IOA_4D_PROFILE\",
\"sudo docker run --rm \",
\"  -e AWS_REGION=$AWS_REGION \",
\"  -e S3_BUCKET=$S3_BUCKET \",
\"  -e S3_PREFIX=$S3_PREFIX \",
\"  -e PERF_MARKER=$PERF_MARKER \",
\"  -e IOA_TEST_RECORDS=$IOA_TEST_RECORDS \",
\"  -e IOA_4D_PROFILE=$IOA_4D_PROFILE \",
\"  -v /opt/ioa-run/ioa-core-internal:/work \",
\"  -w /work \",
\"  -t ioa-perf-runner:local \",
\"  /work/scripts/run_perf.sh\"
]"

echo "SSM command sent. Monitor the instance for results."
echo "Results will be uploaded to: s3://$S3_BUCKET/$S3_PREFIX"
