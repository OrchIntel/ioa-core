# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

#!/bin/bash

set -e

# Configuration
export IOA_PERF_TUNE=1
export IOA_SHARDS=8
export IOA_STAGE_SIZE=20000
export IOA_COMMIT_EVERY=500
export IOA_PRECOMPILE_SCHEMA=1
export IOA_4D_CACHE_SIZE=2048
export IOA_PROGRESS_T=10
export IOA_TEST_RECORDS=500000

# AWS Configuration
export AWS_REGION=${AWS_REGION:-us-east-1}
export S3_BUCKET=${S3_BUCKET:-ioa-perf-results-us-east-1-238836619152}
export TS=$(date +%Y%m%d_%H%M%S)
export S3_PREFIX=${S3_PREFIX:-benchmark_500k_SHARDED/$TS/}

# Create progress directory
mkdir -p /tmp/perf
: > /tmp/perf/progress.log

echo "=== IOA MemoryFabric 500k Sharded Test ==="
echo "Shards: $IOA_SHARDS"
echo "Stage Size: $IOA_STAGE_SIZE"
echo "Records: $IOA_TEST_RECORDS"
echo "S3 Prefix: $S3_PREFIX"
echo "Started: $(date)"

# Start background progress monitor
(
    while true; do
        echo "$(date -Is) heartbeat marker=heavy records=$IOA_TEST_RECORDS shards=$IOA_SHARDS" >> /tmp/perf/progress.log
        aws s3 cp /tmp/perf/progress.log s3://$S3_BUCKET/$S3_PREFIX --region $AWS_REGION >/dev/null 2>&1 || true
        sleep 60
    done
) &
HB_PID=$!

# Function to cleanup on exit
cleanup() {
    echo "Cleaning up..."
    kill $HB_PID 2>/dev/null || true
    wait $HB_PID 2>/dev/null || true
    
    # Upload final results
    echo "Uploading results to S3..."
    aws s3 cp /tmp/perf/progress.log s3://$S3_BUCKET/$S3_PREFIX/progress.log --region $AWS_REGION || true
    
    # Upload any generated databases for analysis
    find . -name "mf_shard_*.db" -exec aws s3 cp {} s3://$S3_BUCKET/$S3_PREFIX/ --region $AWS_REGION \; || true
    
    echo "Cleanup completed"
}

trap cleanup EXIT

# Run the 500k test with timeout
echo "Starting 500k sharded test..."
timeout --signal=INT 5h python3 -c "
import os
import sys
import json
import time
import asyncio
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, 'src')

from ioa_core.memory_fabric.fabric import MemoryFabric

async def run_500k_test():
    print('Initializing MemoryFabric with sharding...')
    mf = MemoryFabric(
        backend='sqlite',
        config={'data_dir': './artifacts/memory/'}
    )
    
    print(f'Shards: {mf.shards}')
    print(f'Stage Size: {mf.stage_size}')
    print(f'Progress Telemetry: {mf.progress_telemetry}s')
    
    # Generate 500k test records
    print('Generating 500k test records...')
    records = []
    for i in range($IOA_TEST_RECORDS):
        records.append({
            'content': f'Test document {i} with some content for sharding test',
            'metadata': {
                'jurisdiction': 'EU' if i % 2 == 0 else 'US',
                'risk_level': 'high' if i % 10 == 0 else 'medium',
                'content_length': len(f'Test document {i}'),
                'batch_id': i // 1000
            },
            'tags': [f'test_{i % 100}', 'sharding', 'performance'],
            'memory_type': 'conversation',
            'storage_tier': 'hot'
        })
    
    print(f'Generated {len(records)} records')
    
    # Store with sharding
    print('Starting sharded batch storage...')
    start_time = time.time()
    
    record_ids = await mf.store_batch(records)
    
    end_time = time.time()
    duration = end_time - start_time
    rate = len(records) / duration if duration > 0 else 0
    
    print(f'Storage completed: {len(record_ids)} records in {duration:.2f}s ({rate:.0f} records/sec)')
    
    # Verify integrity using verification script
    print('Verifying data integrity...')
    import subprocess
    try:
        result = subprocess.run(['python3', 'scripts/verify_shard_integrity.py', './artifacts/memory/'], 
                              capture_output=True, text=True, timeout=60)
        print('Integrity verification output:')
        print(result.stdout)
        if result.stderr:
            print('Errors:')
            print(result.stderr)
        
        # Parse verification results
        try:
            with open('shard_integrity_report.json', 'r') as f:
                integrity_report = json.load(f)
            total_stored = integrity_report['total_records']
            unique_stored = integrity_report['unique_records']
            integrity_status = integrity_report['integrity_status']
            max_deviation = integrity_report['max_deviation']
        except Exception as e:
            print(f'Failed to parse integrity report: {e}')
            total_stored = 0
            unique_stored = 0
            integrity_status = 'UNKNOWN'
            max_deviation = 100.0
    except Exception as e:
        print(f'Integrity verification failed: {e}')
        total_stored = 0
        unique_stored = 0
        integrity_status = 'ERROR'
        max_deviation = 100.0
    
    # Performance summary with integrity details
    integrity_passed = (integrity_status == 'PASS' and 
                       total_stored == len(records) and 
                       unique_stored == len(records) and 
                       max_deviation <= 5.0)
    
    summary = {
        'test_type': '500k_sharded',
        'records_processed': len(records),
        'records_stored': total_stored,
        'unique_records': unique_stored,
        'duration_seconds': round(duration, 2),
        'rate_per_second': round(rate, 0),
        'shards': mf.shards,
        'stage_size': mf.stage_size,
        'integrity_status': integrity_status,
        'max_deviation_percent': round(max_deviation, 2),
        'integrity_check': 'PASS' if integrity_passed else 'FAIL',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    print(json.dumps(summary, indent=2))
    
    # Write summary to file
    with open('performance_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Close connections
    mf.close()
    
    return summary

# Run the test
if __name__ == '__main__':
    try:
        summary = asyncio.run(run_500k_test())
        print('Test completed successfully')
        exit(0)
    except Exception as e:
        print(f'Test failed: {e}')
        import traceback
        traceback.print_exc()
        exit(1)
" 2>&1 | tee /var/log/mf_500k_sharded.out

# Capture exit code
EXIT_CODE=$?

# Upload logs and results
echo "Uploading logs and results..."
aws s3 cp /var/log/mf_500k_sharded.out s3://$S3_BUCKET/$S3_PREFIX/ --region $AWS_REGION || true
aws s3 cp performance_summary.json s3://$S3_BUCKET/$S3_PREFIX/ --region $AWS_REGION || true

# Write final status
if [ $EXIT_CODE -eq 0 ]; then
    echo "SUCCESS" > RUN_STATUS.txt
    echo "500k sharded test completed successfully"
else
    echo "FAILED" > RUN_STATUS.txt
    echo "500k sharded test failed with exit code $EXIT_CODE"
fi

aws s3 cp RUN_STATUS.txt s3://$S3_BUCKET/$S3_PREFIX/ --region $AWS_REGION || true

echo "Test completed at $(date)"
exit $EXIT_CODE
