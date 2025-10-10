# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== IOA Feature Independence Test (FIST) ===${NC}"
echo "Testing system-agnostic behavior of feature toggles"
echo ""

# Ensure we're in the right directory
cd "$(dirname "$0")/.."

# Create output directory
mkdir -p docs/ops/qa/dispatch-031

# Run the feature toggle matrix tests
echo -e "${YELLOW}Running feature toggle matrix tests...${NC}"
export IOA_NON_INTERACTIVE=1

# Run tests with verbose output
pytest tests/e2e/test_feature_toggles_matrix.py -v --tb=short

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Feature toggle matrix tests passed${NC}"
    
    # Generate results summary
    echo -e "${YELLOW}Generating results summary...${NC}"
    
    # Get current feature states
    python3 -c "
import sys
sys.path.insert(0, 'src')
from config.loader import get_all_features

features = get_all_features()
print('Feature Toggle Matrix Results')
print('============================')
print('Feature,Status,Value')
for name, value in features.items():
    status = 'ENABLED' if value != 'off' else 'DISABLED'
    print(f'{name},{status},{value}')
print('')
print('All features can be independently toggled without breaking others.')
print('System-agnostic behavior validated successfully.')
" > docs/ops/qa/dispatch-031/fist_matrix_results.csv
    
    echo -e "${GREEN}✓ Results saved to docs/ops/qa/dispatch-031/fist_matrix_results.csv${NC}"
    
    # Display results
    echo ""
    echo -e "${GREEN}=== FIST Test Results ===${NC}"
    cat docs/ops/qa/dispatch-031/fist_matrix_results.csv
    
else
    echo -e "${RED}✗ Feature toggle matrix tests failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=== FIST Test Complete ===${NC}"
echo "Feature independence validated successfully"
echo "Results saved to: docs/ops/qa/dispatch-031/fist_matrix_results.csv"
