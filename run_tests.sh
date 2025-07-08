#!/bin/bash

# BioIntel.AI Test Runner Script

echo "🧪 BioIntel.AI Test Suite Runner"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "info") echo -e "${BLUE}ℹ️  $message${NC}" ;;
        "success") echo -e "${GREEN}✅ $message${NC}" ;;
        "warning") echo -e "${YELLOW}⚠️  $message${NC}" ;;
        "error") echo -e "${RED}❌ $message${NC}" ;;
    esac
}

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    print_status "error" "pytest is not installed. Installing now..."
    pip install pytest pytest-asyncio pytest-cov
fi

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    print_status "error" "requirements.txt not found. Please run this script from the project root."
    exit 1
fi

# Install dependencies
print_status "info" "Installing dependencies..."
pip install -r requirements.txt

# Create test database directory
mkdir -p /tmp/test_db

# Set environment variables for testing
export ENVIRONMENT=testing
export DATABASE_URL=sqlite:///./test.db
export SECRET_KEY=test-secret-key
export JWT_SECRET_KEY=test-jwt-secret
export REDIS_URL=redis://localhost:6379/1

# Parse command line arguments
TEST_TYPE="all"
VERBOSE=false
COVERAGE=false
SPECIFIC_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -f|--file)
            SPECIFIC_FILE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -t, --type TYPE     Test type (all, unit, integration, api)"
            echo "  -v, --verbose       Verbose output"
            echo "  -c, --coverage      Run with coverage report"
            echo "  -f, --file FILE     Run specific test file"
            echo "  -h, --help          Show this help message"
            exit 0
            ;;
        *)
            print_status "error" "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="pytest"

if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=. --cov-report=html --cov-report=term-missing"
fi

# Run tests based on type
print_status "info" "Running tests..."

case $TEST_TYPE in
    "all")
        print_status "info" "Running all tests..."
        $PYTEST_CMD tests/
        ;;
    "unit")
        print_status "info" "Running unit tests..."
        $PYTEST_CMD tests/test_*_service.py tests/test_*_model.py
        ;;
    "api")
        print_status "info" "Running API tests..."
        $PYTEST_CMD tests/test_*_api.py
        ;;
    "integration")
        print_status "info" "Running integration tests..."
        $PYTEST_CMD tests/test_integration_*.py
        ;;
    *)
        if [ -n "$SPECIFIC_FILE" ]; then
            print_status "info" "Running specific test file: $SPECIFIC_FILE"
            $PYTEST_CMD "tests/$SPECIFIC_FILE"
        else
            print_status "error" "Unknown test type: $TEST_TYPE"
            exit 1
        fi
        ;;
esac

# Store exit code
TEST_EXIT_CODE=$?

# Generate test report
print_status "info" "Test execution completed."

if [ $TEST_EXIT_CODE -eq 0 ]; then
    print_status "success" "All tests passed!"
else
    print_status "error" "Some tests failed. Exit code: $TEST_EXIT_CODE"
fi

# Coverage report
if [ "$COVERAGE" = true ]; then
    if [ -d "htmlcov" ]; then
        print_status "success" "Coverage report generated in htmlcov/ directory"
        print_status "info" "Open htmlcov/index.html in your browser to view the report"
    fi
fi

# Cleanup
print_status "info" "Cleaning up test artifacts..."
rm -f test.db
rm -rf /tmp/test_db

# Summary
echo ""
echo "🧪 Test Summary"
echo "=============="
echo "Test Type: $TEST_TYPE"
echo "Verbose: $VERBOSE"
echo "Coverage: $COVERAGE"
echo "Exit Code: $TEST_EXIT_CODE"

if [ "$COVERAGE" = true ]; then
    echo "Coverage Report: htmlcov/index.html"
fi

echo ""
print_status "info" "Test execution completed!"

exit $TEST_EXIT_CODE