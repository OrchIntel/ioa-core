# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

#!/bin/bash

set -euo pipefail

# Configuration
EXPORT_DIR="ioa-core-public"
DRY_RUN=${1:-false}

log_info() {
    echo "[INFO] $1"
}

log_warning() {
    echo "[WARNING] $1"
}

log_error() {
    echo "[ERROR] $1"
}

check_prerequisites() {
    if ! command -v git &> /dev/null; then
        log_error "git is required but not installed"
        exit 1
    fi
}

create_export_directory() {
    if [ -d "$EXPORT_DIR" ]; then
        log_warning "Export directory $EXPORT_DIR already exists"
        read -p "Remove existing directory? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$EXPORT_DIR"
        else
            log_error "Export cancelled"
            exit 1
        fi
    fi
    
    mkdir -p "$EXPORT_DIR"
}

create_public_readme() {
    log_info "Creating public README..."
    cat > "$EXPORT_DIR/README.md" << 'EOF'
# IOA Core

Open-source core components of the IOA (Intelligent Operations Automation) system.

## Features

- Agent management and routing
- Memory engine and pattern governance
- Ethics filtering and validation
- Workflow execution engine
- Audit logging and compliance

## Installation

```bash
pip install ioa-core
```

## License

Apache-2.0
EOF
}

filter_and_copy_files() {
    log_info "Filtering and copying core files..."
    
    # Copy core source files
    if [ -d "src" ]; then
        cp -r src "$EXPORT_DIR/"
    fi
    
    # Copy core packages
    if [ -d "packages/core" ]; then
        cp -r packages/core "$EXPORT_DIR/"
    fi
    
    # Copy documentation (excluding enterprise/qa)
    if [ -d "docs" ]; then
        mkdir -p "$EXPORT_DIR/docs"
        cp -r docs/* "$EXPORT_DIR/docs/" 2>/dev/null || true
        # Remove enterprise and qa directories
        rm -rf "$EXPORT_DIR/docs/ops/enterprise" 2>/dev/null || true
        rm -rf "$EXPORT_DIR/docs/ops/qa" 2>/dev/null || true
    fi
    
    # Copy configuration files
    cp pyproject.toml "$EXPORT_DIR/" 2>/dev/null || true
    cp LICENSE "$EXPORT_DIR/" 2>/dev/null || true
    cp CHANGELOG.md "$EXPORT_DIR/" 2>/dev/null || true
    
    # Remove enterprise/SaaS specific content
    rm -rf "$EXPORT_DIR/packages/enterprise" 2>/dev/null || true
    rm -rf "$EXPORT_DIR/packages/saas" 2>/dev/null || true
    rm -rf "$EXPORT_DIR/.github" 2>/dev/null || true
    rm -rf "$EXPORT_DIR/reports" 2>/dev/null || true
    rm -rf "$EXPORT_DIR/TEMP" 2>/dev/null || true
    rm -rf "$EXPORT_DIR/qa_archive" 2>/dev/null || true
    rm -f "$EXPORT_DIR/.secrets.baseline" 2>/dev/null || true
}

update_public_config() {
    log_info "Updating configuration for public release..."
    
    # Update pyproject.toml
    if [ -f "$EXPORT_DIR/pyproject.toml" ]; then
        # Remove enterprise and SaaS dependencies
        sed -i.bak '/enterprise = \[/,/\]/d' "$EXPORT_DIR/pyproject.toml" 2>/dev/null || true
        sed -i.bak '/saas = \[/,/\]/d' "$EXPORT_DIR/pyproject.toml" 2>/dev/null || true
        # Remove enterprise and SaaS from package discovery
        sed -i.bak 's/, "packages"//' "$EXPORT_DIR/pyproject.toml" 2>/dev/null || true
        rm -f "$EXPORT_DIR/pyproject.toml.bak" 2>/dev/null || true
    fi
}

main() {
    log_info "Starting IOA Core public export..."
    
    check_prerequisites
    create_export_directory
    
    if [ "$DRY_RUN" = "--dry-run" ]; then
        log_info "DRY RUN: Would perform the following operations:"
        log_info "1. Create export directory: $EXPORT_DIR"
        log_info "2. Copy core source files (src/, packages/core/)"
        log_info "3. Copy documentation (excluding enterprise/qa)"
        log_info "4. Copy configuration files"
        log_info "5. Remove enterprise/SaaS specific content"
        log_info "6. Update configuration for public release"
        log_info "7. Create public README"
        exit 0
    fi
    
    filter_and_copy_files
    create_public_readme
    update_public_config
    
    log_info "Public export completed successfully in $EXPORT_DIR"
    log_info "Next steps:"
    log_info "1. Review exported content in $EXPORT_DIR"
    log_info "2. Initialize git repository in $EXPORT_DIR"
    log_info "3. Push to public repository"
    log_info "4. Create GitHub release"
}

main "$@"
