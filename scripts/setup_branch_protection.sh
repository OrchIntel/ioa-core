# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

#!/bin/bash


set -e

# Configuration
REPO_OWNER="OrchIntel"
REPO_NAME="ioa"
BRANCH="main"

# Required status checks
REQUIRED_CHECKS=(
    "Python Tests (Zero-Warning)"
    "Docs (MkDocs)"
    "Enhanced Python Tests Workflow"
    "Enhanced Docs Workflow"
)

echo "🔒 Setting up branch protection for $REPO_OWNER/$REPO_NAME:$BRANCH"

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed"
    exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub CLI"
    echo "Run: gh auth login"
    exit 1
fi

# Create branch protection configuration
cat > branch_protection.json << EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": []
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "required_approving_review_count": 1
  },
  "allow_force_pushes": false,
  "allow_deletions": false,
  "restrictions": null
}
EOF

# Apply branch protection
echo "📋 Applying branch protection rules..."
gh api -X PUT \
  -H "Accept: application/vnd.github+json" \
  "/repos/$REPO_OWNER/$REPO_NAME/branches/$BRANCH/protection" \
  --input branch_protection.json

# Add required status checks
echo "✅ Adding required status checks..."
STATUS_CHECKS_JSON=$(printf '{"strict": true, "contexts": ["%s"]}' "$(IFS='","'; echo "${REQUIRED_CHECKS[*]}")")

gh api -X PATCH \
  -H "Accept: application/vnd.github+json" \
  "/repos/$REPO_OWNER/$REPO_NAME/branches/$BRANCH/protection/required_status_checks" \
  -f strict=true \
  $(printf -- '-f contexts[]="%s"' "${REQUIRED_CHECKS[@]}")

# Enable vulnerability alerts
echo "🔍 Enabling vulnerability alerts..."
gh api -X PUT "/repos/$REPO_OWNER/$REPO_NAME/vulnerability-alerts"

# Enable automated security fixes
echo "🤖 Enabling automated security fixes..."
gh api -X PUT "/repos/$REPO_OWNER/$REPO_NAME/automated-security-fixes"

# Cleanup
rm -f branch_protection.json

echo "✅ Branch protection setup complete!"
echo "📋 Protected branch: $BRANCH"
echo "🔒 Required checks: ${REQUIRED_CHECKS[*]}"
echo "👥 Admin enforcement: enabled"
echo "🔍 Vulnerability alerts: enabled"
echo "🤖 Security fixes: automated"
