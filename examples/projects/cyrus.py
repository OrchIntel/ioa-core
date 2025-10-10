""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

# IOA Module v2.4.8 | IOA Contributors | Last updated: 2025-08-05
# Description: Module cyrus
# License: Apache-2.0 – IOA Project
# © 2025 IOA Project. All rights reserved.


from src.cli_interface import IOACLI
import os
if __name__ == '__main__':
    project_path = os.path.dirname(os.path.abspath(__file__))
    IOACLI(project_path=project_path).cmdloop()