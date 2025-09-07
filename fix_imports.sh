#!/bin/bash
set -e

# Fix Import Issues Script
# This script fixes common import issues and missing dependencies

echo "🔧 Fixing AI Agent Import Issues"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[FIX]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment exists
if [ -d "venv" ]; then
    print_status "Activating virtual environment..."
    source venv/bin/activate
else
    print_warning "Virtual environment not found. Please run ./build.sh first."
    
    # Try to install dependencies globally as fallback
    print_status "Installing missing dependencies globally..."
fi

# Determine Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_error "Python not found. Please install Python 3.12"
    exit 1
fi

# Install missing pydantic-settings
print_status "Installing pydantic-settings..."
$PYTHON_CMD -m pip install pydantic-settings>=2.0.0 --user

# Test imports
print_status "Testing imports..."
$PYTHON_CMD test_imports.py

if [ $? -eq 0 ]; then
    print_status "✅ All imports working correctly!"
    echo
    echo "You can now run:"
    echo "  ./run.sh interactive"
    echo "  ./run.sh demo"
    echo "  ./run.sh search 'test query'"
else
    print_error "❌ Import issues still exist. Please check error messages above."
    exit 1
fi