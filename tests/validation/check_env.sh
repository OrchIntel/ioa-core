#!/bin/bash
# Quick check of LLM provider environment variables

echo "============================================"
echo "LLM Provider Environment Variables Check"
echo "============================================"
echo ""

check_var() {
    local var_name=$1
    local var_value="${!var_name}"
    
    if [ -n "$var_value" ]; then
        local length=${#var_value}
        echo "✅ $var_name: SET ($length chars)"
    else
        echo "❌ $var_name: NOT SET"
    fi
}

check_var "OPENAI_API_KEY"
check_var "ANTHROPIC_API_KEY"
check_var "GOOGLE_API_KEY"
check_var "GEMINI_API_KEY"
check_var "XAI_API_KEY"
check_var "DEEPSEEK_API_KEY"
check_var "OLLAMA_HOST"

echo ""
echo "============================================"

# Count how many are set
set_count=0
for var in OPENAI_API_KEY ANTHROPIC_API_KEY GOOGLE_API_KEY XAI_API_KEY DEEPSEEK_API_KEY; do
    if [ -n "${!var}" ]; then
        ((set_count++))
    fi
done

echo "Configured Providers: $set_count/5 (+ Ollama)"
echo ""

if [ $set_count -eq 0 ]; then
    echo "⚠️  No API keys found. Run:"
    echo ""
    echo "export OPENAI_API_KEY='sk-proj-...'"
    echo "export ANTHROPIC_API_KEY='sk-ant-...'"
    echo "export GOOGLE_API_KEY='AIzaSy...'"
    echo "export XAI_API_KEY='xai-...'"
    echo "export DEEPSEEK_API_KEY='sk-...'"
    echo ""
elif [ $set_count -ge 2 ]; then
    echo "✅ Ready for round-table orchestration!"
    echo ""
    echo "Run the validator:"
    echo "  python3 tests/validation/llm_validator.py"
else
    echo "⚠️  Only $set_count provider configured."
    echo "Add at least 2 providers for round-table."
fi

echo "============================================"

