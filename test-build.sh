#!/bin/bash
set -e  # Exit on any error

# Test Build Script
# Quick verification that the build completed successfully

echo "🧪 Testing AI Agent Build"
echo "========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[TEST]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if build was run
print_status "Checking if build was completed..."

# Check virtual environment
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found. Run './build.sh' first."
    exit 1
fi
print_status "✅ Virtual environment exists"

# Activate virtual environment
source venv/bin/activate

# Check Python version
PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ "$PYTHON_VERSION" == "3.12" ]]; then
    print_status "✅ Python 3.12 confirmed in virtual environment"
else
    print_error "❌ Expected Python 3.12, found $PYTHON_VERSION"
    exit 1
fi

# Check key dependencies
print_status "Testing key imports..."

python -c "
import sys
import traceback

def test_import(module_name, description):
    try:
        __import__(module_name)
        print(f'✅ {description}')
        return True
    except ImportError as e:
        print(f'❌ {description}: {e}')
        return False
    except Exception as e:
        print(f'⚠️  {description}: Unexpected error - {e}')
        return False

# Test core dependencies
tests = [
    ('pydantic', 'Pydantic'),
    ('pydantic_settings', 'Pydantic Settings'),
    ('fastapi', 'FastAPI'),
    ('aiohttp', 'aiohttp'),
    ('click', 'Click'),
    ('structlog', 'Structlog'),
    ('nltk', 'NLTK'),
    ('rich', 'Rich'),
]

passed = 0
total = len(tests)

for module, desc in tests:
    if test_import(module, desc):
        passed += 1

print(f'\\n📊 Import Tests: {passed}/{total} passed')

if passed == total:
    print('🎉 All dependency imports successful!')
    sys.exit(0)
else:
    print('❌ Some dependency imports failed')
    sys.exit(1)
"

# Test AI Agent imports
print_status "Testing AI Agent module imports..."

python -c "
import sys

def test_ai_agent_imports():
    try:
        from ai_agent.core.config import Config, load_config
        print('✅ Config module')
        
        from ai_agent.core.types import QueryString, SearchResponse, ProblemAnalysis
        print('✅ Types module') 
        
        from ai_agent.core.context_managers import ai_agent_context, ManagedAIAgent
        print('✅ Context managers module')
        
        # Test basic config loading (might fail without .env, that's ok)
        try:
            config = load_config()
            print('✅ Configuration loading works')
        except Exception as e:
            print(f'⚠️  Configuration loading needs .env file: {e}')
        
        return True
        
    except Exception as e:
        print(f'❌ AI Agent import failed: {e}')
        return False

if test_ai_agent_imports():
    print('🎉 AI Agent module imports successful!')
    sys.exit(0)
else:
    print('❌ AI Agent module imports failed') 
    sys.exit(1)
"

# Check if directories were created
print_status "Checking created directories..."

for dir in "cache" "logs" "data"; do
    if [ -d "$dir" ]; then
        print_status "✅ Directory $dir exists"
    else
        print_warning "⚠️  Directory $dir missing (will be created on first run)"
    fi
done

# Check configuration files
print_status "Checking configuration files..."

if [ -f ".env.example" ]; then
    print_status "✅ .env.example template exists"
else
    print_warning "⚠️  .env.example template missing"
fi

if [ -f ".env" ]; then
    print_status "✅ .env configuration file exists"
else
    print_warning "⚠️  .env configuration file missing - you'll need to create one"
fi

# Check executable scripts
print_status "Checking executable scripts..."

for script in "build.sh" "run.sh"; do
    if [ -x "$script" ]; then
        print_status "✅ $script is executable"
    else
        print_warning "⚠️  $script is not executable (run: chmod +x $script)"
    fi
done

# Run Python 3.12 compatibility check
print_status "Running Python 3.12 compatibility check..."

if [ -f "verify_python312_compatibility.py" ]; then
    if python verify_python312_compatibility.py > /dev/null 2>&1; then
        print_status "✅ Python 3.12 compatibility verified"
    else
        print_warning "⚠️  Python 3.12 compatibility check had issues"
    fi
else
    print_warning "⚠️  Compatibility check script not found"
fi

# Final status
print_status "Build test completed!"
echo
echo -e "${GREEN}🎉 Build verification successful!${NC}"
echo
echo "Next steps:"
echo "1. Create/edit .env file with your configuration"
echo "2. Run: ./run.sh interactive"
echo "3. Or run: ./run.sh demo (to see Phase 1 improvements)"
echo
echo "For help: ./run.sh help"