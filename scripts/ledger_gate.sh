# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

#!/usr/bin/env bash
set -euo pipefail


LEDGER_MD="docs/ops/qa/ledger/master-execution-ledger.md"
LEDGER_JSON="docs/ops/qa/ledger/dispatch_ledger.json"
LEDGER_SUM="docs/ops/qa/ledger/CHECKSUMS.sha256"
DISPATCHES_DIR="docs/ops/qa/dispatches"

echo "[ledger-gate] 🚪 Starting IOA Ledger Gate..."

# Check if we're in CI mode
if [[ "${CI:-}" == "true" ]]; then
    echo "[ledger-gate] CI mode detected"
    CI_MODE=true
else
    CI_MODE=false
fi

# Validate required directories exist
if [[ ! -d "$DISPATCHES_DIR" ]]; then
    echo "[ledger-gate] ❌ Dispatches directory not found: $DISPATCHES_DIR"
    exit 1
fi

if [[ ! -d "docs/ops/qa/ledger" ]]; then
    echo "[ledger-gate] ❌ Ledger directory not found"
    exit 1
fi

echo "[ledger-gate] 📁 Updating master ledger..."

# Run the Python ledger update script
if [[ -f "scripts/tools/update_ledger.py" ]]; then
    python3 scripts/tools/update_ledger.py
else
    echo "[ledger-gate] ⚠️  update_ledger.py not found, skipping automated update"
fi

echo "[ledger-gate] 🔍 Rebuilding checksums..."

# Rebuild checksums for ledger directory
(
    cd docs/ops/qa/ledger
    find . -type f \( -name "*.md" -o -name "*.json" -o -name "*.log" \) \
        | sort | xargs sha256sum > CHECKSUMS.sha256
)

echo "[ledger-gate] ✅ Checksums regenerated"

# Stage ledger files
git add "$LEDGER_MD" "$LEDGER_JSON" "$LEDGER_SUM"

# Check if there are staged changes
if ! git diff --cached --quiet; then
    echo "[ledger-gate] 📝 Ledger updated and staged for commit"
    
    # Show what changed
    echo "[ledger-gate] Changes staged:"
    git diff --cached --name-only | grep -E "(ledger|CHECKSUMS)" || true
else
    echo "[ledger-gate] ℹ️  No ledger changes detected"
fi

# Public guard - fail if internal docs would be exposed
echo "[ledger-gate] 🛡️  Checking for public doc leaks..."

if [[ -d "docs/public" ]]; then
    if grep -R "docs/ops/qa/dispatches" -n docs/public 2>/dev/null; then
        echo "[ledger-gate] ❌ Public docs leak detected!"
        echo "[ledger-gate] Internal dispatch paths found in public documentation"
        exit 42
    fi
    
    if grep -R "docs/ops/qa/ledger" -n docs/public 2>/dev/null; then
        echo "[ledger-gate] ❌ Public docs leak detected!"
        echo "[ledger-gate] Internal ledger paths found in public documentation"
        exit 42
    fi
fi

# Validate ledger freshness
echo "[ledger-gate] 🔍 Validating ledger freshness..."

# Check if current dispatch is represented in ledger
CURRENT_DISPATCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
if [[ "$CURRENT_DISPATCH" != "unknown" ]]; then
    if grep -q "$CURRENT_DISPATCH" "$LEDGER_MD" 2>/dev/null; then
        echo "[ledger-gate] ✅ Current dispatch found in ledger"
    else
        echo "[ledger-gate] ⚠️  Current dispatch not found in ledger (may be new)"
    fi
fi

# Final validation
echo "[ledger-gate] 🎯 Final validation..."

# Check ledger files exist and are readable
for file in "$LEDGER_MD" "$LEDGER_JSON" "$LEDGER_SUM"; do
    if [[ -f "$file" && -r "$file" ]]; then
        echo "[ledger-gate] ✅ $file validated"
    else
        echo "[ledger-gate] ❌ $file validation failed"
        exit 1
    fi
done

# Check checksums file is not empty
if [[ ! -s "$LEDGER_SUM" ]]; then
    echo "[ledger-gate] ❌ Checksums file is empty"
    exit 1
fi

echo "[ledger-gate] 🎉 Ledger Gate passed successfully!"
echo "[ledger-gate] 📋 Next: Commit with ledger files included"

if [[ "$CI_MODE" == "true" ]]; then
    echo "[ledger-gate] 🚀 CI mode: Ledger validation complete"
else
    echo "[ledger-gate] 💡 Local mode: Run 'git commit' to include ledger updates"
fi

exit 0
