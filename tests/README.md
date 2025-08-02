# Test Suite Documentation

## Overview

The PD Triglav project has comprehensive test coverage including unit tests, integration tests, and end-to-end functionality tests.

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- **Fast**: Run quickly without external dependencies
- **Mocked**: Use mocked dependencies for isolation
- **Default**: Run automatically in CI/CD pipelines

### Integration Tests (`@pytest.mark.integration`)
- **Real APIs**: Make actual calls to LLM providers
- **Requires API Keys**: Need valid API keys configured
- **Slower**: May take several seconds per test
- **Optional**: Can be skipped if APIs are unavailable

## Running Tests

### Prerequisites
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip-sync requirements.txt
```

### Run All Unit Tests (Fast)
```bash
# Run only unit tests (mocked, fast)
pytest -m unit

# Run all tests except integration tests
pytest -m "not integration"

# Run all tests in tests/ directory (default)
pytest tests/
```

### Run Integration Tests (Real APIs)
```bash
# Run only integration tests (requires API keys)
pytest -m integration

# Run specific integration test class
pytest tests/test_llm_integration.py::TestLLMProviderIntegration

# Run specific integration test
pytest tests/test_llm_integration.py::TestLLMProviderIntegration::test_moonshot_basic_connectivity
```

### Run All Tests
```bash
# Run everything (unit + integration)
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html
```

## Testing Dependencies

The project uses several pytest plugins and tools to provide comprehensive testing capabilities:

### Core Testing Framework
- **`pytest`** - Main testing framework and test runner
  - Replaces Python's built-in `unittest` with better discovery and fixtures
  - Usage: `pytest`, `pytest -v`, `pytest tests/`

- **`pytest-flask`** - Flask-specific testing integration
  - Provides Flask app context, test client, and database fixtures automatically
  - Enables testing of routes, authentication, and database operations
  - Usage: Automatic when testing Flask applications

### Code Coverage
- **`pytest-cov`** - Code coverage plugin for pytest
  - Measures which lines of code are executed during tests
  - Generates coverage reports in multiple formats
  - Usage: `pytest --cov=.`, `pytest --cov=. --cov-report=html`

- **`coverage`** - Core coverage measurement library
  - Backend engine for pytest-cov
  - Can be used standalone: `coverage run -m pytest && coverage report`

### Performance & Parallel Execution
- **`pytest-xdist`** - Parallel test execution across multiple CPU cores
  - Significantly speeds up test execution for large test suites
  - Usage: `pytest -n 4` (run with 4 workers), `pytest -n auto` (auto-detect cores)

### Advanced Usage Examples
```bash
# Run tests with coverage and parallel execution
pytest -n 4 --cov=. --cov-report=html

# Generate detailed coverage report
pytest --cov=. --cov-report=html --cov-report=term-missing

# Run only fast tests in parallel
pytest -n auto -m "not integration"

# Run with verbose output and coverage
pytest -v --cov=. --cov-report=term
```

## Test Configuration

### API Keys Required for Integration Tests
Set these environment variables in `.env`:
```bash
MOONSHOT_API_KEY=your-moonshot-api-key
DEEPSEEK_API_KEY=your-deepseek-api-key
```

### Test Skipping Behavior
- Integration tests automatically skip if API keys are missing
- No failures, just skip with reason message
- Safe to run in CI/CD without API keys

## Test Files

### Unit Tests (Mocked)
- `test_llm_service.py` - LLM service layer with mocked providers
- `test_content_generation.py` - Content generation with mocked LLM calls
- `test_historical_events_model.py` - Database model tests
- `test_user_model.py` - User model and authentication
- `test_auth.py` - Authentication flows
- `test_trip_model.py` - Trip management

### Integration Tests (Real APIs)
- `test_llm_integration.py` - Real LLM provider connectivity and responses

### End-to-End Tests
- `test_historical_events_routes.py` - Route testing with database
- `test_app.py` - Application-level tests

## Test Examples

### Basic Connectivity Test
```python
# Manual test of API connectivity
from tests.test_llm_integration import run_basic_connectivity_tests
run_basic_connectivity_tests()
```

### Provider-Specific Tests
```bash
# Test only Moonshot provider
pytest -k "moonshot" -m integration

# Test only DeepSeek provider  
pytest -k "deepseek" -m integration

# Test provider fallback logic
pytest tests/test_llm_integration.py::TestProviderManagerIntegration::test_provider_fallback_logic
```

## CI/CD Integration

### Fast CI Pipeline (Unit Tests Only)
```bash
pytest -m "not integration" --cov=. --cov-report=xml
```

### Full CI Pipeline (With Integration)
```bash
# Set API keys in CI environment variables
export MOONSHOT_API_KEY=$MOONSHOT_API_KEY
export DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY

# Run all tests
pytest --cov=. --cov-report=xml
```

## Test Markers Reference

| Marker | Description | Speed | Dependencies |
|--------|-------------|-------|--------------|
| `unit` | Fast unit tests with mocks | Very Fast | None |
| `integration` | Real API calls | Slow | API Keys |
| `slow` | Long-running tests | Slow | Various |

## Troubleshooting

### Integration Tests Not Running
1. Check API keys are set in `.env`
2. Verify API keys are valid
3. Check internet connectivity
4. Review rate limiting (tests may be throttled)

### Unit Tests Failing
1. Check virtual environment is activated
2. Verify dependencies are installed with `pip-sync`
3. Review Flask app context setup in conftest.py

### Database Tests Failing
1. Ensure test database is clean
2. Check migration status
3. Verify database permissions

## Adding New Tests

### New Unit Test
```python
@pytest.mark.unit
class TestNewFeature:
    def test_new_functionality(self):
        # Use mocks for external dependencies
        assert True
```

### New Integration Test
```python
@pytest.mark.integration
@pytest.mark.skipif(not has_api_keys(), reason="API keys not configured")
class TestNewIntegration:
    def test_real_api_call(self):
        # Make actual API calls
        assert True
```

This test structure ensures both fast development cycles (unit tests) and reliable production validation (integration tests).