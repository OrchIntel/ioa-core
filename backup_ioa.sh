# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups/ioa-core"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup configuration
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" -C ~/.ioa config/

# Backup data
tar -czf "$BACKUP_DIR/data_$DATE.tar.gz" -C ~/ioa-core data/

# Backup logs
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" -C ~/ioa-core logs/

# Clean old backups (keep last 7 days)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR"
