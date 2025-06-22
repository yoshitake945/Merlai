#!/bin/bash

# Merlai Test Runner Script
# This script runs various types of tests for the Merlai project

set -e

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

# Function to check if virtual environment is activated
check_venv() {
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        print_error "Virtual environment is not activated. Please activate it first:"
        echo "source venv/bin/activate"
        exit 1
    fi
    print_success "Virtual environment is active: $VIRTUAL_ENV"
}

# Function to install test dependencies
install_test_deps() {
    print_status "Installing test dependencies..."
    pip install pytest pytest-cov pytest-mock pytest-asyncio click[testing] httpx
    print_success "Test dependencies installed"
}

# Function to run unit tests
run_unit_tests() {
    print_status "Running unit tests..."
    pytest tests/test_core.py -v --cov=merlai.core --cov-report=term-missing
    print_success "Unit tests completed"
}

# Function to run API tests
run_api_tests() {
    print_status "Running API tests..."
    pytest tests/test_api.py -v --cov=merlai.api --cov-report=term-missing
    print_success "API tests completed"
}

# Function to run CLI tests
run_cli_tests() {
    print_status "Running CLI tests..."
    pytest tests/test_cli.py -v --cov=merlai.cli --cov-report=term-missing
    print_success "CLI tests completed"
}

# Function to run integration tests
run_integration_tests() {
    print_status "Running integration tests..."
    pytest tests/test_integration.py -v --cov=merlai --cov-report=term-missing
    print_success "Integration tests completed"
}

# Function to run all tests
run_all_tests() {
    print_status "Running all tests..."
    pytest tests/ -v --cov=merlai --cov-report=term-missing --cov-report=html
    print_success "All tests completed"
}

# Function to run tests with specific markers
run_marked_tests() {
    local marker=$1
    print_status "Running tests with marker: $marker"
    pytest tests/ -v -m "$marker" --cov=merlai --cov-report=term-missing
    print_success "Tests with marker '$marker' completed"
}

# Function to run tests excluding slow tests
run_fast_tests() {
    print_status "Running fast tests (excluding slow tests)..."
    pytest tests/ -v -m "not slow" --cov=merlai --cov-report=term-missing
    print_success "Fast tests completed"
}

# Function to generate coverage report
generate_coverage_report() {
    print_status "Generating coverage report..."
    pytest tests/ --cov=merlai --cov-report=html --cov-report=term-missing
    print_success "Coverage report generated in htmlcov/"
}

# Function to clean up test artifacts
cleanup() {
    print_status "Cleaning up test artifacts..."
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -delete
    find . -type d -name "*.egg-info" -exec rm -rf {} +
    print_success "Cleanup completed"
}

# Function to show help
show_help() {
    echo "Merlai Test Runner"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  unit              Run unit tests only"
    echo "  api               Run API tests only"
    echo "  cli               Run CLI tests only"
    echo "  integration       Run integration tests only"
    echo "  all               Run all tests (default)"
    echo "  fast              Run fast tests (excluding slow tests)"
    echo "  coverage          Generate coverage report"
    echo "  install-deps      Install test dependencies"
    echo "  cleanup           Clean up test artifacts"
    echo "  help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                # Run all tests"
    echo "  $0 unit           # Run unit tests only"
    echo "  $0 fast           # Run fast tests only"
    echo "  $0 coverage       # Generate coverage report"
}

# Main script logic
main() {
    # Check if virtual environment is activated
    check_venv
    
    # Parse command line arguments
    case "${1:-all}" in
        "unit")
            run_unit_tests
            ;;
        "api")
            run_api_tests
            ;;
        "cli")
            run_cli_tests
            ;;
        "integration")
            run_integration_tests
            ;;
        "all")
            run_all_tests
            ;;
        "fast")
            run_fast_tests
            ;;
        "coverage")
            generate_coverage_report
            ;;
        "install-deps")
            install_test_deps
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 