# Data Extraction Service API Test Suite

Comprehensive test suite for the Data Extraction Service API, implementing the testing strategy outlined in TEST-GUIDELINES-V1.md.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Installation](#installation)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Configuration](#configuration)
- [Writing New Tests](#writing-new-tests)
- [Troubleshooting](#troubleshooting)

## Overview

This test suite provides comprehensive coverage of the Data Extraction Service API with three main categories of tests:

1. **Seeded Data Tests** - Fast, deterministic tests using pre-populated database data
2. **Real Extraction Tests** - End-to-end workflow tests with mock external API
3. **Edge Case Tests** - Validation of error handling and boundary conditions

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Pytest fixtures and configuration
├── test_seeded_data.py            # Seeded data tests
├── test_edge_cases.py             # Edge case tests
├── test_real_extraction.py        # Real extraction workflow tests
├── fixtures/
│   ├── __init__.py
│   └── seed_data.py               # Database seeding utilities
├── mocks/
│   ├── __init__.py
│   ├── external_api_mock.py       # Mock external API service
│   └── mock_data.py               # Mock data generators
└── utils/
    ├── __init__.py
    ├── assertions.py              # Common assertion helpers
    └── test_helpers.py            # Test utility functions
```

## Installation

### Prerequisites

- Python 3.8+
- Django project with Data Extraction Service API
- PostgreSQL or SQLite for test database

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Configure Test Settings

Create or update Django test settings (e.g., `extraction_service/settings/test.py`):

```python
from .base import *

# Use in-memory SQLite for faster tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations for faster test setup
class DisableMigrations:
    def __contains__(self, item):
        return True
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Test-specific settings
DEBUG = False
TESTING = True
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Run only seeded data tests
pytest -m seeded

# Run only edge case tests
pytest -m edge_case

# Run only real extraction tests
pytest -m real_extraction

# Run fast tests (exclude slow tests)
pytest -m "not slow"
```

### Run Specific Test Files

```bash
# Run seeded data tests
pytest tests/test_seeded_data.py

# Run edge case tests
pytest tests/test_edge_cases.py

# Run real extraction tests
pytest tests/test_real_extraction.py
```

### Run Specific Test Classes or Methods

```bash
# Run a specific test class
pytest tests/test_seeded_data.py::TestJobStatus

# Run a specific test method
pytest tests/test_seeded_data.py::TestJobStatus::test_verify_job_status_pending
```

### Run Tests with Coverage

```bash
# Generate coverage report
pytest --cov=. --cov-report=html

# View coverage in browser
open htmlcov/index.html
```

### Run Tests in Parallel

```bash
# Run tests using multiple CPU cores
pytest -n auto
```

### Run Tests with Verbose Output

```bash
pytest -v  # Verbose
pytest -vv  # Very verbose
```

## Test Categories

### Seeded Data Tests (`test_seeded_data.py`)

Tests that validate API behavior using pre-populated database entries.

**Test Classes:**
- `TestJobStatus` - Job status endpoint validation
- `TestExtractionResults` - Extraction results retrieval
- `TestJobsList` - Jobs list and filtering
- `TestJobStatistics` - Statistics aggregation
- `TestHealthCheck` - Service health monitoring
- `TestJobCancellation` - Job cancellation workflows
- `TestJobRemoval` - Job data removal

**Running:**
```bash
pytest -m seeded tests/test_seeded_data.py
```

### Edge Case Tests (`test_edge_cases.py`)

Tests that verify proper handling of invalid inputs and error conditions.

**Test Classes:**
- `TestInvalidAuthentication` - Authentication failure scenarios
- `TestNonExistentResources` - 404 error handling
- `TestInvalidStateAccess` - State transition validation
- `TestMalformedRequests` - Malformed input handling
- `TestSecurityValidation` - Security vulnerability tests
- `TestBoundaryConditions` - Pagination and limits
- `TestUnsupportedOperations` - HTTP method validation
- `TestErrorMessages` - Error message consistency

**Running:**
```bash
pytest -m edge_case tests/test_edge_cases.py
```

### Real Extraction Tests (`test_real_extraction.py`)

End-to-end workflow tests using mock external API.

**Test Classes:**
- `TestExtractionWorkflow` - Complete extraction workflows
- `TestExtractionWithMockFailures` - Failure scenario handling
- `TestExtractionRecordTypes` - Different data types
- `TestConcurrentExtractions` - Concurrent request handling

**Running:**
```bash
pytest -m real_extraction tests/test_real_extraction.py
```

## Configuration

### Pytest Configuration (`pytest.ini`)

The test suite is configured via `pytest.ini`:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = extraction_service.settings.test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --verbose --strict-markers --tb=short
testpaths = tests
```

### Test Markers

Available test markers:

- `@pytest.mark.seeded` - Seeded data tests
- `@pytest.mark.edge_case` - Edge case tests
- `@pytest.mark.real_extraction` - Real extraction tests
- `@pytest.mark.slow` - Slow-running tests

### Environment Variables

Set these environment variables for test configuration:

```bash
export DJANGO_SETTINGS_MODULE=extraction_service.settings.test
export TEST_DATABASE_URL=sqlite:///:memory:
```

## Writing New Tests

### Basic Test Structure

```python
import pytest
from tests.utils.assertions import assert_http_status
from tests.utils.test_helpers import extract_json_response

@pytest.mark.seeded
class TestNewFeature:
    """Tests for new feature."""
    
    def test_new_endpoint(self, api_client, seed_pending_job):
        """
        Test: Description of what this test validates.
        
        Detailed explanation of test purpose and expected behavior.
        """
        # Arrange
        job_id = seed_pending_job['id']
        
        # Act
        response = api_client.get(f'/api/v1/new-endpoint/{job_id}')
        
        # Assert
        assert_http_status(response, 200)
        data = extract_json_response(response)
        assert 'expected_field' in data
```

### Using Fixtures

The test suite provides many reusable fixtures:

```python
def test_with_fixtures(
    api_client,           # Django test client
    seed_completed_job,   # Completed job with results
    valid_api_token,      # Valid API token
    mock_external_api     # Mock external API
):
    # Your test code here
    pass
```

### Custom Assertions

Use helper assertions for common validations:

```python
from tests.utils.assertions import (
    assert_http_status,
    assert_response_schema,
    assert_job_status,
    assert_error_message_present,
    assert_extraction_data_format,
)

# Assert HTTP status
assert_http_status(response, 200)

# Assert response structure
assert_response_schema(response, ['id', 'status', 'created_at'])

# Assert job status
assert_job_status(response, 'completed')

# Assert error response
assert_error_message_present(response)

# Assert extraction data format
assert_extraction_data_format(records)
```

### Test Helpers

Use helper functions for common operations:

```python
from tests.utils.test_helpers import (
    extract_json_response,
    get_response_field,
    poll_until_status,
    wait_for_job_completion,
)

# Extract JSON from response
data = extract_json_response(response)

# Get specific field
job_id = get_response_field(response, 'job_id')

# Poll until status reached
final_status = poll_until_status(client, job_id, 'completed')

# Wait for job to complete
result = wait_for_job_completion(client, job_id)
```

## Troubleshooting

### Tests Failing with Database Errors

Ensure test database is properly configured:

```python
# settings/test.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
```

### Import Errors

Ensure the project root is in PYTHONPATH:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Fixtures Not Found

Ensure `conftest.py` is in the tests directory and properly configured.

### Mock External API Not Working

Verify that the mock is properly patched:

```python
@pytest.fixture
def mock_external_api_with_patch(monkeypatch, mock_external_api):
    # Update import path to match actual service
    monkeypatch.setattr(
        'services.external_api_service.ExternalAPI',
        lambda: mock_external_api
    )
    return mock_external_api
```

### Slow Test Execution

Run tests in parallel:

```bash
pytest -n auto
```

Or skip slow tests:

```bash
pytest -m "not slow"
```

### Test Data Cleanup Issues

Ensure proper test isolation by using Django's test database:

```bash
pytest --reuse-db  # Reuse database between runs
pytest --create-db  # Force recreate database
```

## Best Practices

1. **Test Isolation** - Each test should be independent
2. **Clear Test Names** - Use descriptive test method names
3. **Single Assertion Focus** - Test one thing at a time
4. **Use Fixtures** - Reuse common setup via fixtures
5. **Document Tests** - Include docstrings explaining test purpose
6. **Fast Tests** - Keep tests fast; mark slow tests appropriately
7. **Meaningful Assertions** - Use custom assertions with clear messages

## Contributing

When adding new tests:

1. Follow existing test structure and naming conventions
2. Add appropriate test markers (`@pytest.mark.seeded`, etc.)
3. Include comprehensive docstrings
4. Use existing fixtures and utilities
5. Run full test suite before committing
6. Update this README if adding new categories or features

## Additional Resources

- [TEST-GUIDELINES-V1.md](../TEST-GUIDELINES-V1.md) - Complete testing guidelines
- [SERVICE-GUIDELINES.md](../SERVICE-GUIDELINES.md) - Service development guidelines
- [Pytest Documentation](https://docs.pytest.org/)
- [Django Testing Documentation](https://docs.djangoproject.com/en/stable/topics/testing/)


