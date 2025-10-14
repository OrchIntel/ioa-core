"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# PATCH: Cursor-2025-01-27 Initial implementation for governance consolidation

class LedgerUpdater:
    """Updates IOA master execution ledger from dispatch sources."""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent.parent
        self.dispatches_dir = self.repo_root / "docs" / "ops" / "qa" / "dispatches"
        self.ledger_dir = self.repo_root / "docs" / "ops" / "qa" / "ledger"
        self.ledger_md = self.ledger_dir / "master-execution-ledger.md"
        self.ledger_json = self.ledger_dir / "dispatch_ledger.json"
        
    def parse_dispatch_headers(self) -> List[Dict]:
        """Parse all dispatch headers to extract metadata."""
        dispatches = []
        
        if not self.dispatches_dir.exists():
            print(f"⚠️  Dispatches directory not found: {self.dispatches_dir}")
            return dispatches
            
        # Process EXEC dispatches
        exec_dir = self.dispatches_dir / "EXEC"
        if exec_dir.exists():
            for dispatch_dir in exec_dir.iterdir():
                if dispatch_dir.is_dir():
                    dispatch_info = self._parse_dispatch_dir(dispatch_dir, "EXEC")
                    if dispatch_info:
                        dispatches.append(dispatch_info)
        
        # Process GOV dispatches
        gov_dir = self.dispatches_dir / "GOV"
        if gov_dir.exists():
            for item in gov_dir.iterdir():
                if item.is_dir():
                    dispatch_info = self._parse_dispatch_dir(item, "GOV")
                    if dispatch_info:
                        dispatches.append(dispatch_info)
                elif item.is_file() and item.suffix == ".md":
                    # Handle governance dispatch files directly
                    dispatch_info = self._parse_summary_file(item, "GOV")
                    if dispatch_info:
                        dispatches.append(dispatch_info)
        
        return dispatches
    
    def _parse_dispatch_dir(self, dispatch_dir: Path, category: str) -> Optional[Dict]:
        """Parse a single dispatch directory for metadata."""
        # Look for summary or completion files
        summary_files = list(dispatch_dir.glob("*SUMMARY*.md")) + list(dispatch_dir.glob("*COMPLETION*.md"))
        
        if not summary_files:
            # Try to infer from directory name
            return self._infer_dispatch_info(dispatch_dir, category)
        
        # Parse the first summary file found
        summary_file = summary_files[0]
        return self._parse_summary_file(summary_file, category)
    
    def _parse_summary_file(self, summary_file: Path, category: str) -> Optional[Dict]:
        """Parse a summary file for dispatch metadata."""
        try:
            content = summary_file.read_text(encoding='utf-8')
            
            # Extract dispatch code
            code_match = re.search(r'DISPATCH[-\w]+', content, re.IGNORECASE)
            dispatch_code = code_match.group(0) if code_match else summary_file.parent.name
            
            # Extract status
            if "✅" in content or "Completed" in content:
                status = "✅"
            elif "🔄" in content or "Active" in content:
                status = "🔄"
            elif "⚠️" in content or "Partial" in content:
                status = "⚠️"
            elif "❌" in content or "Failed" in content:
                status = "❌"
            else:
                status = "❓"
            
            # Extract date
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', content)
            date = date_match.group(1) if date_match else "Unknown"
            
            return {
                "code": dispatch_code,
                "path": str(summary_file.relative_to(self.repo_root)),
                "date": date,
                "status": status,
                "category": category,
                "summary": f"Dispatch {dispatch_code} ({category})",
                "log_refs": f"docs/ops/qa/dispatches/{category}/{summary_file.parent.name}/"
            }
            
        except Exception as e:
            print(f"⚠️  Error parsing {summary_file}: {e}")
            return None
    
    def _infer_dispatch_info(self, dispatch_dir: Path, category: str) -> Optional[Dict]:
        """Infer dispatch info from directory structure when no summary file exists."""
        dir_name = dispatch_dir.name
        
        # Try to extract dispatch code from directory name
        if dir_name.startswith("dispatch-"):
            dispatch_code = dir_name
        else:
            dispatch_code = f"UNKNOWN-{dir_name}"
        
        return {
            "code": dispatch_code,
            "path": str(dispatch_dir.relative_to(self.repo_root)),
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "status": "❓",
            "category": category,
            "summary": f"Inferred dispatch {dispatch_code} ({category})",
            "log_refs": f"docs/ops/qa/dispatches/{category}/{dir_name}/"
        }
    
    def update_master_ledger(self, dispatches: List[Dict]) -> None:
        """Update the master execution ledger markdown file.

        Idempotency: Cleans any previously injected "Normalized Structure" blocks
        between section B and C, then inserts exactly one fresh block wrapped in
        BEGIN/END markers so repeated runs are a no-op except for the date/content.
        """
        if not self.ledger_md.exists():
            print(f"⚠️  Master ledger not found: {self.ledger_md}")
            return
        
        # Read existing content
        content = self.ledger_md.read_text(encoding='utf-8')
        
        # Update the structure section
        new_structure = self._generate_structure_section(dispatches)
        
        # Ensure we operate only between Section B and Section C
        start_match = re.search(r"## B\. HISTORY \(MERGED FROM DISPATCH LEDGER\)", content)
        end_match = re.search(r"## C\. ACTIVE NOW", content)

        if start_match and end_match and start_match.start() < end_match.start():
            before = content[: start_match.end()]
            middle = content[start_match.end() : end_match.start()]
            after = content[end_match.start() :]

            # Remove any existing normalized structure blocks in the middle slice:
            # 1) Our explicit markers if present
            middle = re.sub(
                r"\n?<!-- BEGIN_NORMALIZED_STRUCTURE -->[\s\S]*?<!-- END_NORMALIZED_STRUCTURE -->\n?",
                "\n",
                middle,
                flags=re.DOTALL,
            )
            # 2) Legacy blocks that begin with the heading and include a fenced code block
            middle = re.sub(
                r"\n?\*\*Normalized Structure \(Updated: .*?\)\*\*[\s\S]*?```\n\n?",
                "\n",
                middle,
                flags=re.DOTALL,
            )

            # Compose the new single normalized block with explicit markers
            normalized_block = (
                f"\n<!-- BEGIN_NORMALIZED_STRUCTURE -->\n"
                f"**Normalized Structure (Updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')})**\n"
                f"{new_structure}\n"
                f"<!-- END_NORMALIZED_STRUCTURE -->\n\n"
            )

            content = before + normalized_block + after
        
        # Write updated content
        self.ledger_md.write_text(content, encoding='utf-8')
        print(f"✅ Updated master ledger: {self.ledger_md}")
    
    def _generate_structure_section(self, dispatches: List[Dict]) -> str:
        """Generate the normalized structure section for the ledger."""
        exec_dispatches = [d for d in dispatches if d["category"] == "EXEC"]
        gov_dispatches = [d for d in dispatches if d["category"] == "GOV"]
        
        structure = "```\ndocs/ops/qa/\n├── dispatches/\n"
        
        if exec_dispatches:
            structure += "│   ├── EXEC/          # Execution dispatches (affect completion %)\n"
            for dispatch in exec_dispatches[:5]:  # Show first 5
                structure += f"│   │   ├── {dispatch['code']}/\n"
            if len(exec_dispatches) > 5:
                structure += f"│   │   └── ... ({len(exec_dispatches)} total)\n"
            else:
                structure += "│   │\n"
        else:
            structure += "│   ├── EXEC/          # No execution dispatches found\n"
        
        if gov_dispatches:
            structure += "│   └── GOV/           # Governance dispatches (tracked, no completion %)\n"
            for dispatch in gov_dispatches:
                structure += f"│       └── {dispatch['code']}/\n"
        else:
            structure += "│   └── GOV/           # No governance dispatches found\n"
        
        structure += "└── ledger/            # Master ledgers\n"
        structure += "    ├── master-execution-ledger.md\n"
        structure += "    ├── dispatch_ledger.json\n"
        structure += "    └── CHECKSUMS.sha256\n```"
        
        return structure
    
    def update_json_ledger(self, dispatches: List[Dict]) -> None:
        """Update the JSON dispatch ledger."""
        ledger_data = {
            "metadata": {
                "generated": datetime.now(timezone.utc).isoformat(),
                "total_dispatches": len(dispatches),
                "exec_count": len([d for d in dispatches if d["category"] == "EXEC"]),
                "gov_count": len([d for d in dispatches if d["category"] == "GOV"]),
                "structure_version": "2.5.0-normalized"
            },
            "dispatches": dispatches
        }
        
        # Write JSON ledger
        with open(self.ledger_json, 'w', encoding='utf-8') as f:
            json.dump(ledger_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Updated JSON ledger: {self.ledger_json}")
    
    def validate_required_fields(self, dispatches: List[Dict]) -> bool:
        """Validate that all dispatches have required fields."""
        required_fields = ["code", "path", "date", "status", "category"]
        
        for dispatch in dispatches:
            for field in required_fields:
                if field not in dispatch or not dispatch[field]:
                    print(f"❌ Missing required field '{field}' in dispatch: {dispatch.get('code', 'unknown')}")
                    return False
        
        print(f"✅ All {len(dispatches)} dispatches have required fields")
        return True
    
    def run(self) -> None:
        """Main execution method."""
        print("🔄 Starting IOA Ledger Update...")
        
        # Parse all dispatch headers
        dispatches = self.parse_dispatch_headers()
        print(f"📁 Found {len(dispatches)} dispatches")
        
        if not dispatches:
            print("⚠️  No dispatches found to process")
            return
        
        # Validate required fields
        if not self.validate_required_fields(dispatches):
            print("❌ Validation failed")
            sys.exit(1)
        
        # Update ledger files
        self.update_master_ledger(dispatches)
        self.update_json_ledger(dispatches)
        
        print("🎉 Ledger update completed successfully!")
        print(f"   - EXEC: {len([d for d in dispatches if d['category'] == 'EXEC'])}")
        print(f"   - GOV: {len([d for d in dispatches if d['category'] == 'GOV'])}")


def main():
    """Main entry point."""
    updater = LedgerUpdater()
    try:
        updater.run()
    except Exception as e:
        print(f"❌ Error during ledger update: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
