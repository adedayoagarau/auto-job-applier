# AutoJobApplier Tests

This directory contains unit and integration tests for the AutoJobApplier application.

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=src --cov=web_app --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_auth.py
```

### Run specific test
```bash
pytest tests/test_auth.py::test_password_hashing
```

### Run tests by marker
```bash
# Run only auth tests
pytest -m auth

# Run only API tests
pytest -m api

# Skip slow tests
pytest -m "not slow"
```

## Test Structure

```
tests/
├── __init__.py           # Test package initialization
├── test_auth.py          # Authentication tests
├── test_api.py           # API endpoint tests
└── README.md             # This file
```

## Writing Tests

### Basic test structure
```python
def test_feature_name():
    """Test description"""
    # Arrange
    input_data = ...

    # Act
    result = function_to_test(input_data)

    # Assert
    assert result == expected_value
```

### Using fixtures
```python
@pytest.fixture
def sample_data():
    """Create sample data for tests"""
    return {"key": "value"}

def test_with_fixture(sample_data):
    """Test using fixture"""
    assert sample_data["key"] == "value"
```

### Async tests
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async function"""
    result = await async_function()
    assert result is not None
```

### Testing exceptions
```python
import pytest

def test_exception():
    """Test that exception is raised"""
    with pytest.raises(ValueError, match="error message"):
        function_that_raises()
```

## Test Coverage

To generate a coverage report:

```bash
# Install coverage
pip install pytest-cov

# Run tests with coverage
pytest --cov=src --cov=web_app --cov-report=term-missing

# Generate HTML report
pytest --cov=src --cov=web_app --cov-report=html

# Open report
open htmlcov/index.html
```

## Markers

Tests can be marked for categorization:

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.slow`: Slow running tests
- `@pytest.mark.auth`: Authentication-related tests
- `@pytest.mark.api`: API endpoint tests

## Fixtures

Common fixtures available:

- `client`: FastAPI test client
- `auth_token`: Authentication token for API tests
- `auth_headers`: Authorization headers for API requests

## Best Practices

1. **Test naming**: Use descriptive names starting with `test_`
2. **One assertion per test**: Focus on one thing per test
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Use fixtures**: Reuse setup code with fixtures
5. **Mock external dependencies**: Don't rely on external services
6. **Test edge cases**: Include boundary conditions and error cases
7. **Keep tests fast**: Use mocks to avoid slow operations

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=src --cov=web_app
```

## Current Test Coverage

- ✅ Authentication (password hashing, tokens, user management)
- ✅ API endpoints (protected routes, validation)
- ⏳ Job scraping (TODO)
- ⏳ Form filling (TODO)
- ⏳ Application tracking (TODO)
- ⏳ Resume parsing (TODO)

## Adding New Tests

When adding new features:

1. Write tests first (TDD approach)
2. Test happy path and edge cases
3. Test error handling
4. Update this README if adding new test categories
5. Maintain test coverage above 80%

## Troubleshooting

**Issue**: Tests fail due to missing dependencies
- Solution: `pip install -r requirements.txt`

**Issue**: Database errors in tests
- Solution: Tests should use in-memory SQLite or mocks

**Issue**: Async test warnings
- Solution: Ensure `pytest-asyncio` is installed

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
