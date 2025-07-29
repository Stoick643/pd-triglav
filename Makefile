# PD Triglav Test Runner Makefile
# Makes it easy to run different test suites

SHELL := /bin/bash
.PHONY: help test-fast test-all test-security test-api test-models test-auth test-slow test-integration clean

# Default target
help:
	@echo "PD Triglav Test Runner"
	@echo "====================="
	@echo ""
	@echo "Available commands:"
	@echo "  make test-fast      - Run fast tests (~40 seconds) - for development"
	@echo "  make test-fast-parallel - Run fast tests in parallel (~20 seconds)"
	@echo "  make test-security  - Run security tests only"
	@echo "  make test-api       - Run API tests only" 
	@echo "  make test-models    - Run model tests only"
	@echo "  make test-auth      - Run authentication tests only"
	@echo "  make test-slow      - Run slow tests only (external services)"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-all       - Run all tests (~8+ minutes)"
	@echo "  make test-all-parallel - Run all tests in parallel (~3-4 minutes)"
	@echo "  make test-coverage  - Run tests with coverage report"
	@echo "  make clean          - Clean test artifacts"
	@echo ""
	@echo "Usage examples:"
	@echo "  make test-fast      # Daily development"
	@echo "  make test-all       # Before commit"

# Fast development tests (1-2 minutes)
test-fast:
	@echo "🚀 Running fast tests (development subset)..."
	source venv/bin/activate && pytest -m "fast" -v --tb=short

# Fast development tests with parallel execution 
test-fast-parallel:
	@echo "🚀 Running fast tests in parallel..."
	source venv/bin/activate && pytest -m "fast" -n auto -v --tb=short

# Run all tests (8+ minutes)
test-all:
	@echo "🧪 Running all tests (full suite)..."
	source venv/bin/activate && pytest -v --tb=short

# Run all tests in parallel (3-4 minutes)
test-all-parallel:
	@echo "🧪 Running all tests in parallel (full suite)..."
	source venv/bin/activate && pytest -n auto -v --tb=short

# Security tests only
test-security:
	@echo "🔒 Running security tests..."
	source venv/bin/activate && pytest -m "security" -v --tb=short

# API tests only  
test-api:
	@echo "🌐 Running API tests..."
	source venv/bin/activate && pytest -m "api" -v --tb=short

# Model tests only
test-models:
	@echo "📊 Running model tests..."
	source venv/bin/activate && pytest -m "models" -v --tb=short

# Authentication tests only
test-auth:
	@echo "🔐 Running authentication tests..."
	source venv/bin/activate && pytest -m "auth" -v --tb=short

# Slow tests only (external services)
test-slow:
	@echo "🐌 Running slow tests (external services)..."
	source venv/bin/activate && pytest -m "slow" -v --tb=short

# Integration tests only
test-integration:
	@echo "🔗 Running integration tests..."
	source venv/bin/activate && pytest -m "integration" -v --tb=short

# Tests with coverage
test-coverage:
	@echo "📈 Running tests with coverage..."
	source venv/bin/activate && pytest -m "fast" --cov=. --cov-report=html --cov-report=term-missing

# Clean test artifacts
clean:
	@echo "🧹 Cleaning test artifacts..."
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Development workflow shortcuts
dev: test-fast
pre-commit: test-fast test-security
ci: test-all test-coverage