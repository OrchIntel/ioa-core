""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

#!/usr/bin/env python3
"""
IOA LLM Configuration Checker
Quick script to check and configure IOA LLM providers
"""

import os
import subprocess
import sys
from pathlib import Path

def run_ioa_command(cmd):
    """Run IOA command and return output"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "adapters.ioa_core.cli"] + cmd,
            capture_output=True,
            text=True,
            cwd="/Users/ryan/OrchIntelWorkspace/ioa-core-internal"
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def check_environment_variables():
    """Check which LLM API keys are set in environment"""
    print("🔍 Checking Environment Variables")
    print("=" * 50)
    
    env_vars = {
        "OPENAI_API_KEY": "OpenAI (GPT-4, GPT-3.5)",
        "ANTHROPIC_API_KEY": "Anthropic (Claude 3)",
        "XAI_API_KEY": "XAI (Grok)",
        "GROK_API_KEY": "Grok (Alternative to XAI)",
        "GOOGLE_API_KEY": "Google Gemini",
        "DEEPSEEK_API_KEY": "DeepSeek",
        "OLLAMA_HOST": "Ollama (Local)"
    }
    
    configured = []
    missing = []
    
    for var, description in env_vars.items():
        value = os.getenv(var)
        if value:
            # Mask the key for security
            masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            print(f"✅ {var}: {masked} ({description})")
            configured.append(var)
        else:
            print(f"❌ {var}: Not set ({description})")
            missing.append(var)
    
    return configured, missing

def check_ioa_status():
    """Check IOA Core status"""
    print("\n🔍 Checking IOA Core Status")
    print("=" * 50)
    
    # Check version
    returncode, stdout, stderr = run_ioa_command(["--version"])
    if returncode == 0:
        print(f"✅ IOA Core: {stdout.strip()}")
    else:
        print(f"❌ IOA Core: Error - {stderr}")
        return False
    
    # Check doctor
    returncode, stdout, stderr = run_ioa_command(["doctor"])
    if returncode == 0:
        print(f"✅ IOA Doctor: OK")
        print(stdout)
    else:
        print(f"❌ IOA Doctor: Error - {stderr}")
    
    return True

def test_providers():
    """Test provider connectivity"""
    print("\n🔍 Testing Provider Connectivity")
    print("=" * 50)
    
    # Test offline first (safe)
    print("Testing offline mode (safe)...")
    returncode, stdout, stderr = run_ioa_command(["smoketest", "providers", "--provider", "all"])
    if returncode == 0:
        print("✅ Offline test completed")
        print(stdout)
    else:
        print(f"❌ Offline test failed: {stderr}")
    
    # Ask if user wants to test live
    print("\n" + "=" * 50)
    response = input("Do you want to test live API connectivity? (y/N): ").strip().lower()
    if response in ['y', 'yes']:
        print("Testing live connectivity...")
        returncode, stdout, stderr = run_ioa_command(["smoketest", "providers", "--provider", "all"])
        if returncode == 0:
            print("✅ Live test completed")
            print(stdout)
        else:
            print(f"❌ Live test failed: {stderr}")

def show_setup_instructions():
    """Show setup instructions"""
    print("\n📋 Setup Instructions")
    print("=" * 50)
    
    print("To configure LLM providers, set these environment variables:")
    print()
    print("# OpenAI")
    print("export OPENAI_API_KEY='sk-your-openai-key'")
    print()
    print("# Anthropic")
    print("export ANTHROPIC_API_KEY='sk-ant-your-anthropic-key'")
    print()
    print("# XAI/Grok")
    print("export XAI_API_KEY='xai-your-xai-key'")
    print("# OR")
    print("export GROK_API_KEY='grok-your-grok-key'")
    print()
    print("# Google Gemini")
    print("export GOOGLE_API_KEY='your-google-key'")
    print()
    print("# DeepSeek")
    print("export DEEPSEEK_API_KEY='your-deepseek-key'")
    print()
    print("# Ollama (Local - no API key needed)")
    print("export OLLAMA_HOST='http://localhost:11434'")
    print()
    print("Then run this script again to verify configuration.")

def main():
    """Main function"""
    print("🧠 IOA LLM Configuration Checker")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("/Users/ryan/OrchIntelWorkspace/ioa-core-internal").exists():
        print("❌ Error: Please run this script from the ioa-core-internal directory")
        return
    
    # Check environment variables
    configured, missing = check_environment_variables()
    
    # Check IOA status
    if not check_ioa_status():
        print("❌ IOA Core is not properly installed or configured")
        return
    
    # Test providers
    test_providers()
    
    # Show setup instructions if needed
    if missing:
        show_setup_instructions()
    
    print("\n🎉 IOA LLM Configuration Check Complete!")
    print("=" * 50)

if __name__ == "__main__":
    main()
