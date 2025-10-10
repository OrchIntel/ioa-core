# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

# IOA Core Environment Configuration Template
# Copy this file to .env and configure with your actual values

# =============================================================================
# LLM API Configuration
# =============================================================================

# OpenAI API Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4
OPENAI_BASE_URL=https://api.openai.com/v1

# Alternative LLM Providers (uncomment as needed)
# ANTHROPIC_API_KEY=your-anthropic-key-here
# GOOGLE_API_KEY=your-google-ai-key-here
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_OPENAI_API_KEY=your-azure-key-here

# =============================================================================
# IOA Core Configuration
# =============================================================================

# Project Configuration
IOA_PROJECT_PATH=./projects/my_project.ioa
IOA_LOG_LEVEL=INFO
IOA_DEBUG_MODE=false

# Memory Engine Configuration
MEMORY_STORAGE_TYPE=json  # Options: json, memory, mongodb (enterprise)
MEMORY_MAX_ENTRIES=10000
MEMORY_AUTO_CLEANUP=true

# Agent Router Configuration
AGENT_TIMEOUT_SECONDS=30
AGENT_MAX_CONCURRENT=5
AGENT_RETRY_ATTEMPTS=3

# Pattern Weaver Configuration
PATTERN_WEAVER_ENABLED=true
PATTERN_BATCH_SIZE=50
PATTERN_SIMILARITY_THRESHOLD=0.7

# =============================================================================
# Security Configuration (Development Only)
# =============================================================================

# WARNING: These are development-only settings
# DO NOT use in production - implement proper PKI/HSM
TRUST_REGISTRY_PATH=./config/agent_trust_registry.json
SIGNATURE_VERIFICATION_ENABLED=false
DEVELOPMENT_MODE=true

# =============================================================================
# Storage Configuration
# =============================================================================

# Local Storage Paths
DATA_DIRECTORY=./data
LOG_DIRECTORY=./logs
ARCHIVE_DIRECTORY=./archive

# Cold Storage (Enterprise Feature)
# COLD_STORAGE_ENABLED=false
# COLD_STORAGE_PATH=./cold_archive
# COLD_STORAGE_COMPRESSION=false

# =============================================================================
# Monitoring and Observability
# =============================================================================

# Logging Configuration
LOG_FORMAT=json
LOG_ROTATION_SIZE=10MB
LOG_RETENTION_DAYS=30

# Metrics Collection
METRICS_ENABLED=true
METRICS_EXPORT_INTERVAL=60
METRICS_ENDPOINT=http://localhost:9090/metrics

# Health Check Configuration
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_PORT=8080
HEALTH_CHECK_PATH=/health

# =============================================================================
# Development and Testing
# =============================================================================

# Test Configuration
TEST_DATA_PATH=./tests/fixtures
TEST_MOCK_APIS=true
TEST_PARALLEL_EXECUTION=false

# Development Features
DEV_RELOAD_PATTERNS=true
DEV_VERBOSE_LOGGING=true
DEV_SKIP_VALIDATION=false

# =============================================================================
# Performance Tuning
# =============================================================================

# Resource Limits
MAX_MEMORY_MB=1024
MAX_CPU_CORES=4
MAX_CONCURRENT_REQUESTS=100

# Caching Configuration
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600
CACHE_MAX_SIZE=1000

# =============================================================================
# Integration Configuration
# =============================================================================

# External Service Integration
# SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
# DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK
# ZAPIER_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/YOUR/WEBHOOK

# Database Configuration (Enterprise)
# DATABASE_URL=postgresql://user:pass@localhost:5432/ioa_db
# REDIS_URL=redis://localhost:6379/0
# MONGODB_URI=mongodb://localhost:27017/ioa_core

# =============================================================================
# Security Notes
# =============================================================================

# IMPORTANT SECURITY REMINDERS:
# 1. Never commit .env files to version control
# 2. Use secure key management in production (not environment variables)
# 3. Rotate API keys regularly
# 4. Enable signature verification in production
# 5. Use HTTPS/TLS for all external communications
# 6. Implement proper authentication and authorization
# 7. Regular security audits and updates

# For enterprise security features, contact: enterprise@orchintel.com
