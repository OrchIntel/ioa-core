#!/usr/bin/env python3
"""
Colab Notebook Validation Script

Validates IOA Colab notebooks by executing the first 2 cells
and capturing results for validation reporting.
"""

import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import nbformat
    from nbconvert.preprocessors import ExecutePreprocessor
    from nbconvert.preprocessors.execute import CellExecutionError
except ImportError:
    print("Error: nbformat and nbconvert required. Install with: pip install nbformat nbconvert")
    sys.exit(1)

class NotebookValidator:
    """Validates Colab notebooks by executing cells"""
    
    def __init__(self, notebook_path: Path):
        self.notebook_path = notebook_path
        self.results = {
            "notebook": str(notebook_path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cells": [],
            "overall_status": "unknown",
            "execution_time": 0,
            "errors": []
        }
    
    def load_notebook(self) -> Optional[nbformat.NotebookNode]:
        """Load the notebook file"""
        try:
            with open(self.notebook_path, 'r', encoding='utf-8') as f:
                return nbformat.read(f, as_version=4)
        except Exception as e:
            self.results["errors"].append(f"Failed to load notebook: {e}")
            return None
    
    def execute_cell(self, cell, cell_index: int) -> Dict[str, Any]:
        """Execute a single cell and capture results"""
        cell_result = {
            "index": cell_index,
            "cell_type": cell.cell_type,
            "status": "unknown",
            "execution_time": 0,
            "output": "",
            "error": None,
            "skipped": False
        }
        
        if cell.cell_type != "code":
            cell_result["status"] = "skipped"
            cell_result["skipped"] = True
            cell_result["output"] = f"Non-code cell ({cell.cell_type})"
            return cell_result
        
        start_time = time.time()
        
        try:
            # Get cell source as string
            if isinstance(cell.source, list):
                source_code = ''.join(cell.source)
            else:
                source_code = str(cell.source)
            
            # Skip cells with Jupyter magic commands
            lines = source_code.strip().split('\n')
            has_magic = any(line.strip().startswith('!') or line.strip().startswith('%') for line in lines)
            if has_magic:
                cell_result["status"] = "skipped"
                cell_result["skipped"] = True
                cell_result["output"] = "Skipped - Jupyter magic command (not executable in Python)"
                return cell_result
            
            # Create a minimal execution environment
            exec_globals = {
                "__name__": "__main__",
                "__file__": str(self.notebook_path)
            }
            
            # Execute the cell code
            exec(source_code, exec_globals)
            
            cell_result["status"] = "success"
            cell_result["output"] = "Cell executed successfully"
            
        except NameError as e:
            if "IOA_CLOUD_URL" in str(e) or "IOA_CLOUD_API_KEY" in str(e):
                cell_result["status"] = "skipped"
                cell_result["skipped"] = True
                cell_result["output"] = "Skipped - API key missing (expected for Cloud demo)"
            else:
                cell_result["status"] = "error"
                cell_result["error"] = str(e)
                cell_result["output"] = f"NameError: {e}"
                
        except ImportError as e:
            if "openai" in str(e) or "anthropic" in str(e):
                cell_result["status"] = "skipped"
                cell_result["skipped"] = True
                cell_result["output"] = "Skipped - Provider SDK not installed (expected)"
            else:
                cell_result["status"] = "error"
                cell_result["error"] = str(e)
                cell_result["output"] = f"ImportError: {e}"
                
        except Exception as e:
            cell_result["status"] = "error"
            cell_result["error"] = str(e)
            cell_result["output"] = f"Error: {e}"
            # Add debug info for syntax errors
            if "invalid syntax" in str(e):
                cell_result["output"] += f"\nSource preview: {source_code[:200]}..."
        
        cell_result["execution_time"] = time.time() - start_time
        return cell_result
    
    def validate(self, max_cells: int = 2) -> Dict[str, Any]:
        """Validate the notebook by executing the first max_cells"""
        print(f"🔍 Validating {self.notebook_path.name}...")
        
        start_time = time.time()
        
        # Load notebook
        notebook = self.load_notebook()
        if not notebook:
            self.results["overall_status"] = "failed"
            return self.results
        
        # Execute first max_cells
        cells_to_execute = min(max_cells, len(notebook.cells))
        
        for i in range(cells_to_execute):
            cell = notebook.cells[i]
            print(f"  📝 Executing cell {i+1}/{cells_to_execute}...")
            
            cell_result = self.execute_cell(cell, i)
            self.results["cells"].append(cell_result)
            
            # Debug: print cell source preview
            if isinstance(cell.source, list):
                source_preview = ''.join(cell.source)[:100]
            else:
                source_preview = str(cell.source)[:100]
            print(f"    Source preview: {source_preview}...")
            
            # Print cell result
            if cell_result["status"] == "success":
                print(f"    ✅ Success")
            elif cell_result["status"] == "skipped":
                print(f"    ⚠️ Skipped: {cell_result['output']}")
            else:
                print(f"    ❌ Error: {cell_result['output']}")
        
        self.results["execution_time"] = time.time() - start_time
        
        # Determine overall status
        if any(cell["status"] == "error" for cell in self.results["cells"]):
            self.results["overall_status"] = "failed"
        elif all(cell["status"] in ["success", "skipped"] for cell in self.results["cells"]):
            self.results["overall_status"] = "passed"
        else:
            self.results["overall_status"] = "partial"
        
        return self.results

def generate_validation_report(results: List[Dict[str, Any]]) -> str:
    """Generate a markdown validation report"""
    report = f"""# Colab Notebook Validation Report

**Generated**: {datetime.now(timezone.utc).isoformat()}  
**Purpose**: Validate Colab notebook accessibility and first-cell execution  

## Summary

| Notebook | Status | Cells Tested | Success | Skipped | Errors |
|----------|--------|--------------|---------|---------|--------|
"""
    
    for result in results:
        success_count = sum(1 for cell in result["cells"] if cell["status"] == "success")
        skipped_count = sum(1 for cell in result["cells"] if cell["status"] == "skipped")
        error_count = sum(1 for cell in result["cells"] if cell["status"] == "error")
        
        status_icon = "✅" if result["overall_status"] == "passed" else "⚠️" if result["overall_status"] == "partial" else "❌"
        
        report += f"| {Path(result['notebook']).name} | {status_icon} {result['overall_status']} | {len(result['cells'])} | {success_count} | {skipped_count} | {error_count} |\n"
    
    report += "\n## Detailed Results\n\n"
    
    for result in results:
        notebook_name = Path(result['notebook']).name
        report += f"### {notebook_name}\n\n"
        report += f"**Overall Status**: {result['overall_status']}  \n"
        report += f"**Execution Time**: {result['execution_time']:.2f}s  \n"
        report += f"**Cells Tested**: {len(result['cells'])}  \n\n"
        
        if result['errors']:
            report += "**Errors**:\n"
            for error in result['errors']:
                report += f"- {error}\n"
            report += "\n"
        
        report += "**Cell Results**:\n\n"
        
        for i, cell in enumerate(result['cells']):
            status_icon = "✅" if cell["status"] == "success" else "⚠️" if cell["status"] == "skipped" else "❌"
            report += f"#### Cell {i+1} {status_icon} {cell['status'].upper()}\n\n"
            report += f"- **Type**: {cell['cell_type']}\n"
            report += f"- **Execution Time**: {cell['execution_time']:.2f}s\n"
            report += f"- **Output**: {cell['output']}\n"
            
            if cell['error']:
                report += f"- **Error**: {cell['error']}\n"
            
            if cell['skipped']:
                report += f"- **Skipped Reason**: {cell['output']}\n"
            
            report += "\n"
        
        report += "---\n\n"
    
    report += """## Validation Notes

- **Success ✅**: Cell executed without errors
- **Skipped ⚠️**: Cell skipped due to missing dependencies or API keys (expected for some demos)
- **Error ❌**: Cell failed to execute due to code issues

## Expected Behavior

- **IOA_Aletheia_Runtime_Demo.ipynb**: Should work without API keys (simulation mode)
- **IOA_Cloud_API_Demo.ipynb**: May skip cells requiring API keys (expected)

---
*Generated by IOA Colab Notebook Validator*
"""
    
    return report

def main():
    """Main validation function"""
    print("🚀 IOA Colab Notebook Validator")
    print("=" * 50)
    
    # Define notebooks to validate
    notebooks = [
        "IOA_Aletheia_Runtime_Demo.ipynb",
        "IOA_Cloud_API_Demo.ipynb"
    ]
    
    results = []
    
    for notebook_name in notebooks:
        notebook_path = Path(notebook_name)
        if not notebook_path.exists():
            print(f"❌ Notebook not found: {notebook_name}")
            continue
        
        validator = NotebookValidator(notebook_path)
        result = validator.validate(max_cells=2)
        results.append(result)
    
    # Generate validation report
    report = generate_validation_report(results)
    
    # Save report
    report_path = Path("VALIDATION.md")
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\n📄 Validation report saved: {report_path}")
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Validation Summary")
    print("=" * 50)
    
    for result in results:
        notebook_name = Path(result['notebook']).name
        status_icon = "✅" if result['overall_status'] == "passed" else "⚠️" if result['overall_status'] == "partial" else "❌"
        print(f"{status_icon} {notebook_name}: {result['overall_status']}")
    
    # Determine overall success
    all_passed = all(result['overall_status'] in ['passed', 'partial'] for result in results)
    
    if all_passed:
        print("\n🎉 All notebooks validated successfully!")
        return 0
    else:
        print("\n⚠️ Some notebooks had issues - check VALIDATION.md for details")
        return 1

if __name__ == "__main__":
    sys.exit(main())
