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
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REMOTE_NAME="origin-private"
REMOTE_URL="https://github.com/ioa-org/ioa-core-private.git"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_git_installed() {
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed. Please install git first."
        exit 1
    fi
    log_success "Git is available: $(git --version)"
}

init_git_repo() {
    cd "$REPO_ROOT"
    
    if [ -d ".git" ]; then
        log_info "Git repository already exists"
        return 0
    fi
    
    log_info "Initializing git repository..."
    git init
    log_success "Git repository initialized"
}

setup_remote() {
    cd "$REPO_ROOT"
    
    if git remote get-url "$REMOTE_NAME" &> /dev/null; then
        log_info "Remote '$REMOTE_NAME' already exists"
        return 0
    fi
    
    log_info "Adding remote '$REMOTE_NAME'..."
    git remote add "$REMOTE_NAME" "$REMOTE_URL"
    log_success "Remote '$REMOTE_NAME' added"
}

setup_git_config() {
    cd "$REPO_ROOT"
    
    # Set user config if not already set
    if [ -z "$(git config user.name)" ]; then
        log_warning "Git user.name not set. Please configure with:"
        log_warning "  git config user.name 'Your Name'"
        log_warning "  git config user.email 'your.email@example.com'"
    fi
    
    # Set default branch name
    git config init.defaultBranch main
    
    # Set core.autocrlf to false for cross-platform compatibility
    git config core.autocrlf false
    
    # Set core.eol to lf for consistent line endings
    git config core.eol lf
    
    log_success "Git configuration updated"
}

install_pre_commit() {
    if ! command -v pre-commit &> /dev/null; then
        log_warning "pre-commit not installed. Installing..."
        pip3 install pre-commit
    fi
    
    if [ -f ".pre-commit-config.yaml" ]; then
        log_info "Installing pre-commit hooks..."
        pre-commit install
        pre-commit install --hook-type commit-msg
        log_success "Pre-commit hooks installed"
    else
        log_warning "No .pre-commit-config.yaml found"
    fi
}

setup_detect_secrets() {
    if ! command -v detect-secrets &> /dev/null; then
        log_warning "detect-secrets not installed. Installing..."
        pip3 install detect-secrets
    fi
    
    if [ ! -f ".secrets.baseline" ]; then
        log_info "Creating detect-secrets baseline..."
        detect-secrets scan --baseline .secrets.baseline
        log_success "Detect-secrets baseline created"
    else
        log_info "Detect-secrets baseline already exists"
    fi
}

create_initial_commit() {
    cd "$REPO_ROOT"
    
    if git rev-parse HEAD &> /dev/null; then
        log_info "Repository already has commits"
        return 0
    fi
    
    log_info "Creating initial commit..."
    git add .
    git commit -m "feat: initial commit - IOA Core v2.5.0 repository setup"
    log_success "Initial commit created"
}

main() {
    log_info "Starting IOA Core VCS bootstrap..."
    log_info "Repository root: $REPO_ROOT"
    
    check_git_installed
    init_git_repo
    setup_remote
    setup_git_config
    install_pre_commit
    setup_detect_secrets
    create_initial_commit
    
    log_success "VCS bootstrap completed successfully!"
    log_info "Next steps:"
    log_info "1. Configure git user: git config user.name 'Your Name'"
    log_info "2. Configure git email: git config user.email 'your.email@example.com'"
    log_info "3. Push to remote: git push -u $REMOTE_NAME main"
}

# Run main function
main "$@"
