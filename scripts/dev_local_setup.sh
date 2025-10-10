# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 OrchIntel Systems Ltd.
# https://orchintel.com | https://ioa.systems
#
# Part of IOA Core (Open Source Edition). See LICENSE at repo root.

#!/bin/bash

# IOA Core Development Setup Script
# This script sets up a local development environment for IOA Core

set -e

echo "🚀 Setting up IOA Core development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]]; then
    print_error "This script must be run from the IOA Core root directory"
    exit 1
fi

# Check Python version
print_status "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.9"

if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
    print_error "Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

# Create virtual environment
print_status "Creating virtual environment..."
if [[ ! -d "venv" ]]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip
print_success "Pip upgraded"

# Install dependencies
print_status "Installing development dependencies..."
pip install -e ".[dev]"
print_success "Development dependencies installed"

# Install pre-commit hooks
print_status "Installing pre-commit hooks..."
if command -v pre-commit &> /dev/null; then
    pre-commit install
    print_success "Pre-commit hooks installed"
else
    print_warning "pre-commit not found, skipping hook installation"
fi

# Create configuration directory
print_status "Creating configuration directory..."
mkdir -p ~/.ioa/config
print_success "Configuration directory created"

# Create .env.sample if it doesn't exist
if [[ ! -f ".env.sample" ]]; then
    print_status "Creating .env.sample file..."
    cat > .env.sample << 'EOF'
# IOA Core Environment Configuration
# Copy this file to .env and fill in your actual values

# LLM Provider API Keys
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key
GOOGLE_API_KEY=your-google-api-key
DEEPSEEK_API_KEY=your-deepseek-api-key
XAI_API_KEY=your-xai-api-key
GROK_API_KEY=your-grok-api-key

# Ollama Configuration (Local)
OLLAMA_HOST=http://localhost:11434

# IOA Configuration
IOA_ENV=development
IOA_OFFLINE=false
IOA_REGISTRY_PATH=./config/agent_trust_registry.json

# Development Settings
IOA_DEBUG=true
IOA_LOG_LEVEL=INFO
EOF
    print_success ".env.sample file created"
fi

# Run basic tests to verify installation
print_status "Running basic tests to verify installation..."
if pytest --collect-only > /dev/null 2>&1; then
    print_success "Test collection successful"
else
    print_warning "Test collection had issues - this may be normal for a fresh install"
fi

# Create development shortcuts
print_status "Creating development shortcuts..."
cat > dev.sh << 'EOF'
#!/bin/bash

# IOA Core Development Helper Script

case "$1" in
    "test")
        echo "🧪 Running tests..."
        pytest "${@:2}"
        ;;
    "test-quick")
        echo "⚡ Running quick tests..."
        pytest tests/unit/ tests/smoke/ -v
        ;;
    "test-integration")
        echo "🔗 Running integration tests..."
        pytest tests/integration/ -v
        ;;
    "test-performance")
        echo "⚡ Running performance tests..."
        pytest tests/performance/ -v
        ;;
    "lint")
        echo "🔍 Running linters..."
        black src/ tests/
        isort src/ tests/
        flake8 src/ tests/
        mypy src/
        ;;
    "format")
        echo "✨ Formatting code..."
        black src/ tests/
        isort src/ tests/
        ;;
    "clean")
        echo "🧹 Cleaning up..."
        find . -type d -name "__pycache__" -exec rm -rf {} +
        find . -type f -name "*.pyc" -delete
        find . -type f -name "*.pyo" -delete
        find . -type f -name "*.pyd" -delete
        find . -type d -name "*.egg-info" -exec rm -rf {} +
        find . -type d -name ".pytest_cache" -exec rm -rf {} +
        find . -type d -name ".coverage" -delete
        ;;
    "docs")
        echo "📚 Building documentation..."
        mkdocs build
        ;;
    "serve-docs")
        echo "🌐 Serving documentation..."
        mkdocs serve
        ;;
    "help"|"--help"|"-h"|"")
        echo "IOA Core Development Helper"
        echo ""
        echo "Usage: ./dev.sh <command> [options]"
        echo ""
        echo "Commands:"
        echo "  test              Run all tests"
        echo "  test-quick        Run quick tests (unit + smoke)"
        echo "  test-integration  Run integration tests"
        echo "  test-performance  Run performance tests"
        echo "  lint              Run all linters"
        echo "  format            Format code with black/isort"
        echo "  clean             Clean up cache files"
        echo "  docs              Build documentation"
        echo "  serve-docs        Serve documentation locally"
        echo "  help              Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./dev.sh test-quick"
        echo "  ./dev.sh test tests/unit/test_agent_router.py"
        echo "  ./dev.sh lint"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Run './dev.sh help' for usage information"
        exit 1
        ;;
esac
EOF

chmod +x dev.sh
print_success "Development shortcuts created (use ./dev.sh help)"

# Final setup instructions
echo ""
echo "🎉 IOA Core development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Copy .env.sample to .env and configure your API keys"
echo "3. Run tests: ./dev.sh test-quick"
echo "4. Check the documentation: ./dev.sh serve-docs"
echo ""
echo "Useful commands:"
echo "  ./dev.sh help          - Show all available commands"
echo "  ./dev.sh test-quick    - Run quick tests"
echo "  ./dev.sh lint          - Run code quality checks"
echo "  ./dev.sh format        - Format your code"
echo ""
echo "Happy coding! 🚀"
