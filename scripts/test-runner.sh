#!/bin/bash
# PD Triglav Test Runner Script
# Usage: ./scripts/test-runner.sh [command]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Activate virtual environment
source venv/bin/activate

case "$1" in
  "fast")
    echo -e "${GREEN}🚀 Running fast tests (development subset)...${NC}"
    pytest -m "fast" -v --tb=short
    ;;
  "security")
    echo -e "${RED}🔒 Running security tests...${NC}"
    pytest -m "security" -v --tb=short
    ;;
  "api")
    echo -e "${BLUE}🌐 Running API tests...${NC}"
    pytest -m "api" -v --tb=short
    ;;
  "models")
    echo -e "${YELLOW}📊 Running model tests...${NC}"
    pytest -m "models" -v --tb=short
    ;;
  "auth")
    echo -e "${BLUE}🔐 Running authentication tests...${NC}"
    pytest -m "auth" -v --tb=short
    ;;
  "slow")
    echo -e "${YELLOW}🐌 Running slow tests (external services)...${NC}"
    pytest -m "slow" -v --tb=short
    ;;
  "integration")
    echo -e "${GREEN}🔗 Running integration tests...${NC}"
    pytest -m "integration" -v --tb=short
    ;;
  "all")
    echo -e "${GREEN}🧪 Running all tests (full suite)...${NC}"
    pytest -v --tb=short
    ;;
  "coverage")
    echo -e "${GREEN}📈 Running tests with coverage...${NC}"
    pytest -m "fast" --cov=. --cov-report=html --cov-report=term-missing
    ;;
  "clean")
    echo -e "${YELLOW}🧹 Cleaning test artifacts...${NC}"
    rm -rf .pytest_cache/
    rm -rf htmlcov/
    rm -rf .coverage
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    echo -e "${GREEN}✅ Cleaned!${NC}"
    ;;
  *)
    echo -e "${BLUE}PD Triglav Test Runner${NC}"
    echo "====================="
    echo ""
    echo "Available commands:"
    echo "  ./scripts/test-runner.sh fast      - Run fast tests (~1-2 minutes)"
    echo "  ./scripts/test-runner.sh security  - Run security tests only"
    echo "  ./scripts/test-runner.sh api       - Run API tests only"
    echo "  ./scripts/test-runner.sh models    - Run model tests only"
    echo "  ./scripts/test-runner.sh auth      - Run authentication tests only"
    echo "  ./scripts/test-runner.sh slow      - Run slow tests (external services)"
    echo "  ./scripts/test-runner.sh integration - Run integration tests"
    echo "  ./scripts/test-runner.sh all       - Run all tests (~8+ minutes)"
    echo "  ./scripts/test-runner.sh coverage  - Run tests with coverage"
    echo "  ./scripts/test-runner.sh clean     - Clean test artifacts"
    echo ""
    echo "Usage examples:"
    echo "  ./scripts/test-runner.sh fast      # Daily development"
    echo "  ./scripts/test-runner.sh all       # Before commit"
    ;;
esac