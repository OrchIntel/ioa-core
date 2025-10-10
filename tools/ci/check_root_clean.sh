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

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🔍 Checking repo root hygiene..."

# Change to repo root
cd "$REPO_ROOT"

# Allowed files in root (standard project files)
ALLOWED_FILES=(
    "README.md"
    "LICENSE"
    "CHANGELOG.md"
    "CONTRIBUTING.md"
    "CODE_OF_CONDUCT.md"
    "SECURITY.md"
    "TRADEMARK.md"
    "TRADEMARK_NOTICE.md"
    "NOTICE"
    "MAINTAINERS.md"
    "pyproject.toml"
    "setup.py"
    "setup.cfg"
    "requirements.txt"
    "requirements-dev.txt"
    "pytest.ini"
    "conftest.py"
    "Makefile"
    "docker-compose.yml"
    "workflow.yaml"
    "VERSION"
    "MANIFEST.txt"
    ".gitignore"
    ".gitattributes"
    ".pre-commit-config.yaml"
    ".markdownlint.yaml"
    ".vale.ini"
    "config.yaml"
    "governance_config.json"
    "agent_trust_registry.json"
    "config_export.json"
    "ioa_cli.py"
    "debug_packages.py"
    "backup_ioa.sh"
    "dev-minimal.sh"
    "schedule_instances.sh"
    "connector_validation.md"
    "changed-md.txt"
)

# Disallowed patterns in root
DISALLOWED_PATTERNS=(
    "*.log"
    "*.json"  # Except known config files
    "*.tmp"
    "*.bak"
    "*_snapshot.json"
    "*_metrics.log"
    "*_benchmark.log"
    "*_error.log"
    "*_results.json"
    "*_report.json"
    "health_report.json"
    "provider_metrics.log"
    "ollama_*.log"
    "ollama_*.json"
    "ollama_*.txt"
    "ioa_doctor_snapshot.json"
    "smoketest_results.json"
    "shell_env.json"
)

# Function to check if file is allowed
is_allowed_file() {
    local file="$1"
    for allowed in "${ALLOWED_FILES[@]}"; do
        if [[ "$file" == "$allowed" ]]; then
            return 0
        fi
    done
    return 1
}

# Function to check if file matches disallowed pattern
matches_disallowed_pattern() {
    local file="$1"
    for pattern in "${DISALLOWED_PATTERNS[@]}"; do
        if [[ "$file" == $pattern ]]; then
            return 0
        fi
    done
    return 1
}

# Check for disallowed files
VIOLATIONS=()
FOUND_FILES=()

# Get all files in root (excluding directories and hidden files)
while IFS= read -r -d '' file; do
    # Extract just the filename
    filename=$(basename "$file")
    
    # Skip if it's a directory
    if [[ -d "$file" ]]; then
        continue
    fi
    
    # Skip if it's a hidden file (starts with .)
    if [[ "$filename" == .* ]]; then
        continue
    fi
    
    FOUND_FILES+=("$filename")
    
    # Check if it's an allowed file
    if is_allowed_file "$filename"; then
        continue
    fi
    
    # Check if it matches disallowed patterns
    if matches_disallowed_pattern "$filename"; then
        VIOLATIONS+=("$filename")
    else
        # Check if it's a JSON file that's not explicitly allowed
        if [[ "$filename" == *.json ]]; then
            VIOLATIONS+=("$filename (unexpected JSON file in root)")
        fi
    fi
done < <(find . -maxdepth 1 -type f -print0)

# Report results
if [[ ${#VIOLATIONS[@]} -eq 0 ]]; then
    echo -e "${GREEN}✅ Root hygiene check passed!${NC}"
    echo "Found ${#FOUND_FILES[@]} files in root, all are allowed."
    exit 0
else
    echo -e "${RED}❌ Root hygiene check failed!${NC}"
    echo -e "${YELLOW}Found ${#VIOLATIONS[@]} disallowed files in repo root:${NC}"
    for violation in "${VIOLATIONS[@]}"; do
        echo -e "  ${RED}•${NC} $violation"
    done
    echo ""
    echo -e "${YELLOW}These files should be moved to appropriate subdirectories:${NC}"
    echo "  • Logs → artifacts/logs/"
    echo "  • Ollama artifacts → artifacts/ollama/"
    echo "  • Snapshots → artifacts/snapshots/"
    echo "  • Smoketest results → artifacts/smoketest/"
    echo "  • Audit logs → logs/audit/"
    echo "  • Benchmarks → benchmarks/"
    echo ""
    echo -e "${YELLOW}To fix this, run:${NC}"
    echo "  tools/ci/check_root_clean.sh --fix"
    exit 1
fi
