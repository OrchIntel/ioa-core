# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

#!/bin/bash

# Start instances during business hours
aws ec2 start-instances --instance-ids i-1234567890abcdef0

# Stop instances after hours
aws ec2 stop-instances --instance-ids i-1234567890abcdef0
