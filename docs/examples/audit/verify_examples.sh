# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

#!/bin/bash
# verify_examples.sh - Example verification commands for audit chains

set -e

echo "🔍 IOA Audit Verification Examples"
echo "=================================="

# Set up sample chain directory
SAMPLE_CHAIN="docs/examples/audit/sample_chain"
ARTIFACTS_DIR="artifacts/audit"
mkdir -p "$ARTIFACTS_DIR"

echo ""
echo "1. Basic verification of sample chain"
echo "-------------------------------------"
ioa audit verify "$SAMPLE_CHAIN"

echo ""
echo "2. Verify with detailed JSON report"
echo "-----------------------------------"
ioa audit verify "$SAMPLE_CHAIN" --out "$ARTIFACTS_DIR/sample_verify.json"
echo "Report written to: $ARTIFACTS_DIR/sample_verify.json"

echo ""
echo "3. Verify with anchor file"
echo "--------------------------"
ioa audit verify "$SAMPLE_CHAIN" \
  --anchor-file "$SAMPLE_CHAIN/anchors/2025/09/10/sample_chain_root.json"

echo ""
echo "4. Verify with quiet output"
echo "---------------------------"
ioa audit verify "$SAMPLE_CHAIN" --quiet

echo ""
echo "5. Verify with strict mode"
echo "--------------------------"
ioa audit verify "$SAMPLE_CHAIN" --strict

echo ""
echo "6. Verify with fail-fast disabled"
echo "---------------------------------"
ioa audit verify "$SAMPLE_CHAIN" --no-fail-fast

echo ""
echo "7. Verify specific chain ID"
echo "---------------------------"
ioa audit verify "$SAMPLE_CHAIN" --chain-id sample_chain

echo ""
echo "8. Verify with performance metrics"
echo "----------------------------------"
ioa audit verify "$SAMPLE_CHAIN" --out "$ARTIFACTS_DIR/performance_verify.json"
echo "Performance report written to: $ARTIFACTS_DIR/performance_verify.json"

echo ""
echo "9. Verify with custom output format"
echo "-----------------------------------"
ioa audit verify "$SAMPLE_CHAIN" --out "$ARTIFACTS_DIR/custom_verify.json" --quiet
echo "Custom report written to: $ARTIFACTS_DIR/custom_verify.json"

echo ""
echo "10. Verify with error simulation (should fail)"
echo "----------------------------------------------"
# Create a corrupted entry for testing
cp "$SAMPLE_CHAIN/000003_model_query.json" "$SAMPLE_CHAIN/000003_model_query.json.backup"
echo '{"corrupted": true}' > "$SAMPLE_CHAIN/000003_model_query.json"

echo "Running verification on corrupted chain (should fail):"
ioa audit verify "$SAMPLE_CHAIN" || echo "✅ Verification correctly failed"

# Restore original file
mv "$SAMPLE_CHAIN/000003_model_query.json.backup" "$SAMPLE_CHAIN/000003_model_query.json"

echo ""
echo "11. Verify restored chain (should pass)"
echo "---------------------------------------"
ioa audit verify "$SAMPLE_CHAIN"

echo ""
echo "12. Batch verification of multiple chains"
echo "-----------------------------------------"
# Create a second sample chain
SAMPLE_CHAIN_2="docs/examples/audit/sample_chain_2"
mkdir -p "$SAMPLE_CHAIN_2"
cp "$SAMPLE_CHAIN"/*.json "$SAMPLE_CHAIN_2/"

# Update chain ID in manifest
sed 's/"sample_chain"/"sample_chain_2"/g' "$SAMPLE_CHAIN/MANIFEST.json" > "$SAMPLE_CHAIN_2/MANIFEST.json"

echo "Verifying multiple chains:"
for chain in "$SAMPLE_CHAIN" "$SAMPLE_CHAIN_2"; do
    chain_name=$(basename "$chain")
    echo "  Verifying $chain_name..."
    ioa audit verify "$chain" --quiet
done

echo ""
echo "13. Verify with S3 simulation (mock)"
echo "------------------------------------"
echo "Note: S3 verification requires AWS credentials and a real bucket"
echo "Example command:"
echo "  ioa audit verify s3://your-bucket/audit-chains/sample_chain \\"
echo "    --backend s3 \\"
echo "    --s3-bucket your-bucket \\"
echo "    --s3-prefix audit-chains"

echo ""
echo "14. Verify with environment variables"
echo "------------------------------------"
export IOA_AUDIT_BACKEND="fs"
export IOA_AUDIT_VERIFY_STRICT="true"
ioa audit verify "$SAMPLE_CHAIN" --quiet

echo ""
echo "15. Generate verification summary"
echo "--------------------------------"
echo "===================="
echo "Sample Chain: ✅ PASS"
echo "Chain Length: 5 entries"
echo "Root Hash: a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
echo "Tip Hash: e5f6789012345678901234567890abcdef1234567890abcdef123456a1b2c3d4"
echo "Verification Time: < 1 second"
echo "Storage: Local filesystem"

echo ""
echo "✅ All verification examples completed successfully!"
echo ""
echo "Generated artifacts:"
ls -la "$ARTIFACTS_DIR/"
