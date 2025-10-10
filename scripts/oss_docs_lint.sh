# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

#!/bin/bash


set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
OSS_DOCS_DIRS=(
    "docs"
    "README.md"
    "CONTRIBUTING.md"
    "docs/getting-started"
    "docs/tutorials"
    "docs/user-guide"
    "docs/api"
    "docs/core"
    "docs/governance"
    "docs/ip"
    "docs/whitepapers"
)

# Enterprise keywords that should not appear in OSS docs
ENTERPRISE_KEYWORDS=(
    "enterprise"
    "Enterprise"
    "ENTERPRISE"
    "proprietary"
    "Proprietary"
    "PROPRIETARY"
    "commercial"
    "Commercial"
    "COMMERCIAL"
    "licensed"
    "Licensed"
    "LICENSED"
    "subscription"
    "Subscription"
    "SUBSCRIPTION"
    "premium"
    "Premium"
    "PREMIUM"
    "paid"
    "Paid"
    "PAID"
)

# Allow-listed files that may contain Enterprise references (legacy/governance)
ALLOWLISTED_FILES=(
    "docs/ops/qa_archive/**"
    "docs/ops/control-center/**"
    "docs/ops/rules/**"
    "docs/ops/status_reports/**"
    "docs/ops/Execution_Tracker_Core_Launch_v4.2.md"
    "docs/ops/IOA_Core_Launch_Roadmap_v4.2.md"
    "docs/ops/IOA_MASTER_SNAPSHOT_v2_4_6.txt"
    "docs/ops/ROADMAP_IOA_CORE_v2_4_6.txt"
    "docs/ops/SECURITY_GUIDE_IOA_v2_4_6.txt"
    "docs/ops/STRATEGIC_UPDATE_MEMO_IOA_v2_4_6.txt"
    "docs/ops/INTEGRATION_STRATEGY_v2_4_6.txt"
    "docs/ops/README_IOA_v2_4_6.txt"
    "docs/ops/ROUNDTABLE.md"
    "docs/ops/WORKFLOWS.md"
    "docs/ops/SIMULATION.md"
    "docs/ops/PERFORMANCE.md"
    "docs/ops/MEMORY_ENGINE.md"
    "docs/ops/SENTINEL_INTEGRATION.md"
    "docs/ops/BIAS_MITIGATION.md"
    "docs/ops/COMPLIANCE_CHECKLIST.md"
    "docs/ops/COMPARISON.md"
    "docs/ops/DISCLAIMER.md"
    "docs/ops/TERMS_OF_USE.md"
    "docs/ops/TRADEMARK.md"
    "docs/ops/TRADEMARK_NOTICE.md"
    "docs/ops/GLOSSARY.md"
    "docs/ops/ONBOARDING.md"
    "docs/ops/Multi-Agent Validation Academic Paper.md"
    "docs/ops/feature-matrix.md"
    "docs/ops/integration_summary_doc.md"
    "docs/ops/eth_gov_005_completion.md"
)

# Function to check if a file is allow-listed
is_allowlisted() {
    local file="$1"
    for pattern in "${ALLOWLISTED_FILES[@]}"; do
        if [[ "$file" == $pattern ]]; then
            return 0
        fi
    done
    return 1
}

# Function to check a single file for Enterprise references
check_file() {
    local file="$1"
    local issues_found=0
    
    # Skip allow-listed files
    if is_allowlisted "$file"; then
        echo -e "${YELLOW}⚠️  Skipping allow-listed file: $file${NC}"
        return 0
    fi
    
    # Check for Enterprise keywords
    for keyword in "${ENTERPRISE_KEYWORDS[@]}"; do
        if grep -q "$keyword" "$file" 2>/dev/null; then
            echo -e "${RED}❌ Enterprise reference found in $file: '$keyword'${NC}"
            grep -n "$keyword" "$file" | head -3 | sed 's/^/    /'
            issues_found=$((issues_found + 1))
        fi
    done
    
    if [ $issues_found -eq 0 ]; then
        echo -e "${GREEN}✅ $file${NC}"
    fi
    
    return $issues_found
}

# Function to check directories recursively
check_directory() {
    local dir="$1"
    local total_issues=0
    
    echo "🔍 Checking directory: $dir"
    
    if [ ! -d "$dir" ]; then
        echo -e "${YELLOW}⚠️  Directory not found: $dir${NC}"
        return 0
    fi
    
    # Find all markdown, text, and Python files
    while IFS= read -r -d '' file; do
        if [[ "$file" == *.md ]] || [[ "$file" == *.txt ]] || [[ "$file" == *.py ]]; then
            if check_file "$file"; then
                # File passed checks
                :
            else
                total_issues=$((total_issues + 1))
            fi
        fi
    done < <(find "$dir" -type f \( -name "*.md" -o -name "*.txt" -o -name "*.py" \) -print0 2>/dev/null)
    
    return $total_issues
}

# Function to check individual files
check_individual_files() {
    local total_issues=0
    
    for file in "README.md" "CONTRIBUTING.md"; do
        if [ -f "$file" ]; then
            if check_file "$file"; then
                # File passed checks
                :
            else
                total_issues=$((total_issues + 1))
            fi
        fi
    done
    
    return $total_issues
}

# Main execution
main() {
    echo "🔒 IOA OSS Documentation Linter"
    echo "================================="
    echo "Checking for Enterprise references in OSS documentation..."
    echo ""
    
    local total_issues=0
    
    # Check individual files
    echo "📄 Checking individual files..."
    if check_individual_files; then
        # Individual files passed
        :
    else
        total_issues=$((total_issues + $?))
    fi
    
    echo ""
    
    # Check directories
    for dir in "${OSS_DOCS_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            if check_directory "$dir"; then
                # Directory passed checks
                :
            else
                total_issues=$((total_issues + $?))
            fi
        fi
        echo ""
    done
    
    # Summary
    echo "================================="
    if [ $total_issues -eq 0 ]; then
        echo -e "${GREEN}✅ All OSS documentation passed Enterprise reference checks!${NC}"
        echo "✅ No Enterprise references found in OSS documentation"
        exit 0
    else
        echo -e "${RED}❌ Found $total_issues Enterprise reference(s) in OSS documentation${NC}"
        echo "❌ OSS documentation must not contain Enterprise references"
        echo "❌ Please review and remove Enterprise references from the files listed above"
        exit 1
    fi
}

# Run main function
main "$@"
