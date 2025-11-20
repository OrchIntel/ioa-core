# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""
Evidence Exporters

Provides various export formats for evidence bundles including JSON, HTML,
and cryptographic signatures.
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Literal
from pathlib import Path

from .evidence_bundle import EvidenceBundle, EvidenceBundleError


BundleFormat = Literal["json", "html", "sig"]


class EvidenceExporter:
    """
    Export evidence bundles in multiple formats.
    
    Supports JSON, HTML, and cryptographic signature formats for
    compliance and audit requirements.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize evidence exporter.
        
        Args:
            config: Configuration options for export behavior
        """
        self.config = config or {}
        self.version = "1.0.0"
        self.frameworks = ["IOA_7LAWS", "GDPR", "HIPAA", "SOX", "CCPA"]
    
    def export_bundle(
        self,
        bundle: EvidenceBundle,
        formats: Optional[List[BundleFormat]] = None,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export evidence bundle in requested formats.
        
        Args:
            bundle: Evidence bundle to export
            formats: List of export formats (json, html, sig)
            output_dir: Directory to save exported files
            
        Returns:
            Dictionary with export results and file paths
        """
        formats = formats or ["json", "html", "sig"]
        output_dir = Path(output_dir) if output_dir else Path(".")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {
            "bundle_id": bundle.bundle_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "formats": {},
            "files": {}
        }
        
        # Export in each requested format
        for format_type in formats:
            try:
                if format_type == "json":
                    result = self._export_json(bundle, output_dir)
                elif format_type == "html":
                    result = self._export_html(bundle, output_dir)
                elif format_type == "sig":
                    result = self._export_signature(bundle, output_dir)
                else:
                    raise EvidenceBundleError(f"Unsupported format: {format_type}")
                
                results["formats"][format_type] = result["status"]
                results["files"][format_type] = result["filepath"]
                
            except Exception as e:
                results["formats"][format_type] = f"error: {str(e)}"
                results["files"][format_type] = None
        
        return results
    
    def _export_json(self, bundle: EvidenceBundle, output_dir: Path) -> Dict[str, Any]:
        """Export bundle as JSON file."""
        filename = f"{bundle.bundle_id}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(bundle.to_json())
        
        return {
            "status": "success",
            "filepath": str(filepath),
            "size_bytes": filepath.stat().st_size
        }
    
    def _export_html(self, bundle: EvidenceBundle, output_dir: Path) -> Dict[str, Any]:
        """Export bundle as HTML report."""
        filename = f"{bundle.bundle_id}.html"
        filepath = output_dir / filename
        
        html_content = self._generate_html_report(bundle)
        
        with open(filepath, 'w') as f:
            f.write(html_content)
        
        return {
            "status": "success",
            "filepath": str(filepath),
            "size_bytes": filepath.stat().st_size
        }
    
    def _export_signature(self, bundle: EvidenceBundle, output_dir: Path) -> Dict[str, Any]:
        """Export bundle signature file."""
        filename = f"{bundle.bundle_id}.sig"
        filepath = output_dir / filename
        
        # Generate signature if not present
        if not bundle.signature:
            bundle.generate_signature()
        
        sig_data = {
            "bundle_id": bundle.bundle_id,
            "evidence_hash": bundle.evidence_hash,
            "signature": bundle.signature,
            "signed_at": datetime.now(timezone.utc).isoformat(),
            "algorithm": "SHA256",
            "version": "SIGv1"
        }
        
        with open(filepath, 'w') as f:
            json.dump(sig_data, f, indent=2)
        
        return {
            "status": "success",
            "filepath": str(filepath),
            "size_bytes": filepath.stat().st_size
        }
    
    def _generate_html_report(self, bundle: EvidenceBundle) -> str:
        """Generate HTML report for evidence bundle."""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IOA Evidence Bundle Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .header { background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .section { margin: 20px 0; }
        .validation { background: #f9f9f9; padding: 10px; margin: 10px 0; border-left: 4px solid #007cba; }
        .metadata { background: #f0f8ff; padding: 15px; border-radius: 3px; }
        .signature { background: #fff3cd; padding: 15px; border-radius: 3px; border: 1px solid #ffeaa7; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 3px; overflow-x: auto; }
        .status { font-weight: bold; }
        .success { color: #28a745; }
        .error { color: #dc3545; }
    </style>
</head>
<body>
    <div class="header">
        <h1>IOA Evidence Bundle Report</h1>
        <p><strong>Bundle ID:</strong> {bundle_id}</p>
        <p><strong>Generated:</strong> {generated_at}</p>
        <p><strong>Framework:</strong> {framework}</p>
        <p><strong>Version:</strong> {version}</p>
    </div>
    
    <div class="section">
        <h2>Bundle Information</h2>
        <div class="metadata">
            <p><strong>Validations Count:</strong> {validations_count}</p>
            <p><strong>Evidence Hash:</strong> <code>{evidence_hash}</code></p>
            <p><strong>Signature Status:</strong> <span class="status {signature_status}">{signature_status_text}</span></p>
        </div>
    </div>
    
    <div class="section">
        <h2>Validations</h2>
        {validations_html}
    </div>
    
    <div class="section">
        <h2>Metadata</h2>
        <pre>{metadata_json}</pre>
    </div>
    
    {signature_section}
    
    <div class="section">
        <h2>Raw Bundle Data</h2>
        <pre>{bundle_json}</pre>
    </div>
</body>
</html>
        """
        
        # Generate validations HTML
        validations_html = ""
        for i, validation in enumerate(bundle.validations):
            validations_html += f"""
            <div class="validation">
                <h3>Validation {i + 1}</h3>
                <p><strong>ID:</strong> {validation.get('validation_id', 'N/A')}</p>
                <p><strong>Timestamp:</strong> {validation.get('timestamp', 'N/A')}</p>
                <pre>{json.dumps(validation, indent=2)}</pre>
            </div>
            """
        
        # Generate signature section
        signature_section = ""
        if bundle.signature:
            signature_section = f"""
            <div class="section">
                <h2>Digital Signature</h2>
                <div class="signature">
                    <p><strong>Signature:</strong> <code>{bundle.signature}</code></p>
                    <p><strong>Algorithm:</strong> SHA256</p>
                    <p><strong>Status:</strong> <span class="status {'success' if bundle.verify_signature() else 'error'}">
                        {'Valid' if bundle.verify_signature() else 'Invalid'}
                    </span></p>
                </div>
            </div>
            """
        
        # Fill template
        return html_template.format(
            bundle_id=bundle.bundle_id,
            generated_at=bundle.generated_at,
            framework=bundle.framework,
            version=bundle.version,
            validations_count=bundle.validations_count,
            evidence_hash=bundle.evidence_hash,
            signature_status="success" if bundle.signature else "error",
            signature_status_text="Present" if bundle.signature else "Missing",
            validations_html=validations_html,
            metadata_json=json.dumps(bundle.metadata, indent=2),
            signature_section=signature_section,
            bundle_json=bundle.to_json()
        )
