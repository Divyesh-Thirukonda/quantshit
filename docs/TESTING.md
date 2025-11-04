# Testing Documentation

## Overview

This document provides comprehensive documentation for the Quantshit testing suite. The test suite follows best practices for Python testing using pytest, with a focus on clean architecture, comprehensive coverage, and maintainability.

## Table of Contents

- [Test Architecture](#test-architecture)
- [Test Categories](#test-categories)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)
- [Writing Tests](#writing-tests)
- [Fixtures and Mocks](#fixtures-and-mocks)
- [Test Organization](#test-organization)
- [Continuous Integration](#continuous-integration)
- [Troubleshooting](#troubleshooting)

---

## Test Architecture

The testing suite is organized following clean architecture principles, mirroring the application structure:

```
tests/
├── conftest.py                  # Shared fixtures and configuration
├── test_models.py               # Tests for domain models
├── test_utils.py                # Tests for utility functions
├── test_exchanges.py            # Tests for exchange clients
├── test_services.py             # Tests for business logic services
├── test_strategies.py           # Tests for trading strategies
└── test_integration.py          # End-to-end integration tests
```

### Design Principles

1. **Isolation**: Each test is independent and can run in any order
2. **Mocking**: External dependencies (APIs, databases) are mocked
3. **Fixtures**: Reusable test data and setup via pytest fixtures
4. **Markers**: Tests are categorized using pytest markers for selective execution
5. **Clear Naming**: Test names describe what they test and expected behavior

---

## Test Categories

### Unit Tests (`@pytest.mark.unit`)

Test individual components in isolation:

- **Models** (`test_models.py`): Data structures, validation, properties
- **Utils** (`test_utils.py`): Mathematical calculations, conversions, helpers
- **Services** (`test_services.py`): Matching, scoring, validation logic
- **Strategies** (`test_strategies.py`): Strategy filtering, ranking, position sizing
- **Exchanges** (`test_exchanges.py`): API client logic, parsers

```bash
# Run only unit tests
pytest -m unit
```

### Integration Tests (`@pytest.mark.integration`)

Test interactions between multiple components:

- **Full Workflow** : Complete arbitrage cycle from market fetching to execution
- **Error Handling**: System behavior under failure conditions
- **Repository Integration**: Data persistence and retrieval
- **Performance**: System behavior with large datasets

```bash
# Run only integration tests
pytest -m integration
```

### API Tests (`@pytest.mark.api`)

Test external API interactions (mocked by default):

- **Exchange Clients**: Market data fetching, order placement
- **Error Handling**: API failures, timeouts, rate limits

```bash
# Run only API tests
pytest -m api
```

### Slow Tests (`@pytest.mark.slow`)

Tests that take longer to run (performance tests, large datasets):

```bash
# Skip slow tests for quick feedback
pytest -m "not slow"
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_models.py

# Run specific test class
pytest tests/test_models.py::TestMarket

# Run specific test method
pytest tests/test_models.py::TestMarket::test_market_creation_valid

# Run tests matching pattern
pytest -k "test_market"
```

### With Markers

```bash
# Run only unit tests
pytest -m unit

# Run unit and integration tests (exclude slow tests)
pytest -m "unit or integration"

# Run everything except slow tests
pytest -m "not slow"

# Run tests with multiple markers
pytest -m "unit and not api"
```

### Coverage Reports

```bash
# Run with coverage
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html

# Terminal coverage summary
pytest --cov=src --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=src --cov-fail-under=80
```

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto

# Run with 4 workers
pytest -n 4
```

---

## Test Coverage

### Current Coverage Goals

- **Overall**: > 80%
- **Models**: > 90% (critical data structures)
- **Services**: > 85% (business logic)
- **Utils**: > 90% (mathematical functions)
- **Exchanges**: > 75% (external dependencies)
- **Strategies**: > 85% (trading logic)

### Coverage by Module

```bash
# Check coverage by module
pytest --cov=src --cov-report=term-missing

# Generate HTML report
pytest --cov=src --cov-report=html

# View report
open htmlcov/index.html
```

### Untested Code

Code that is intentionally not tested:

- External API actual requests (mocked instead)
- UI/CLI output formatting
- Development/debug utilities
- Deprecated code paths

---

## Writing Tests

### Test Structure

Follow the **Arrange-Act-Assert** pattern:

```python
def test_calculate_profit_with_fees(self):
    """Test profit calculation includes fees"""
    # Arrange: Setup test data
    buy_price = 0.40
    sell_price = 0.50
    quantity = 100
    buy_fee = 0.01
    sell_fee = 0.02

    # Act: Execute the function
    profit = calculate_profit(
        buy_price=buy_price,
        sell_price=sell_price,
        quantity=quantity,
        buy_fee_pct=buy_fee,
        sell_fee_pct=sell_fee
    )

    # Assert: Verify the result
    assert abs(profit - 8.6) < 0.001
```

### Naming Conventions

Test names should be descriptive and follow this pattern:

```
test_<component>_<scenario>_<expected_result>
```

Examples:
- `test_market_creation_valid()` - Tests valid market creation
- `test_validator_rejects_low_confidence()` - Tests validation rejection
- `test_profit_calculation_with_fees()` - Tests profit calc with fees

### Testing Edge Cases

Always test edge cases:

```python
# Valid input
def test_price_to_probability_valid(self):
    prob = price_to_probability(0.65)
    assert prob == 0.65

# Boundary values
def test_price_to_probability_zero(self):
    prob = price_to_probability(0.0)
    assert prob == 0.0

def test_price_to_probability_one(self):
    prob = price_to_probability(1.0)
    assert prob == 1.0

# Invalid input
def test_price_to_probability_invalid_negative(self):
    with pytest.raises(ValueError, match="Price must be between 0 and 1"):
        price_to_probability(-0.1)
```

### Testing Exceptions

Use `pytest.raises()` context manager:

```python
def test_market_price_validation_invalid(self):
    """Test that invalid price raises ValueError"""
    with pytest.raises(ValueError, match="YES price must be between 0 and 1"):
        Market(
            id="test",
            exchange=Exchange.KALSHI,
            title="Test",
            yes_price=1.5,  # Invalid
            no_price=0.5,
            volume=1000.0,
            liquidity=500.0,
            status=MarketStatus.OPEN
        )
```

---

## Fixtures and Mocks

### Using Fixtures

Fixtures provide reusable test data and setup. Defined in `conftest.py`:

```python
@pytest.fixture
def sample_kalshi_market():
    """Create a sample Kalshi market for testing"""
    return Market(
        id="kalshi_test_001",
        exchange=Exchange.KALSHI,
        title="Will Bitcoin reach $100k by end of 2025?",
        yes_price=0.45,
        no_price=0.55,
        volume=50000.0,
        liquidity=25000.0,
        status=MarketStatus.OPEN
    )

# Use in tests
def test_market_properties(sample_kalshi_market):
    assert sample_kalshi_market.exchange == Exchange.KALSHI
    assert sample_kalshi_market.yes_price == 0.45
```

### Available Fixtures

- `sample_kalshi_market`: Single Kalshi market
- `sample_polymarket_market`: Single Polymarket market
- `sample_kalshi_markets`: List of Kalshi markets for matching
- `sample_polymarket_markets`: List of Polymarket markets for matching
- `sample_opportunity`: Profitable arbitrage opportunity
- `sample_buy_order`: Buy order example
- `sample_sell_order`: Sell order example
- `mock_kalshi_client`: Mocked Kalshi API client
- `mock_polymarket_client`: Mocked Polymarket API client
- `in_memory_repository`: In-memory data repository
- `closed_market`: Closed market for edge cases
- `expired_opportunity`: Expired opportunity for validation testing
- `low_confidence_opportunity`: Low confidence opportunity

### Mocking External Services

Use `unittest.mock` for mocking:

```python
from unittest.mock import Mock, patch

def test_exchange_client_with_mock(self):
    """Test exchange client with mocked API"""
    mock_client = Mock()
    mock_client.get_markets.return_value = [...]

    # Use mock_client in tests
    markets = mock_client.get_markets()
    assert len(markets) > 0
```

---

## Test Organization

### File Structure

Each test file corresponds to a source module:

| Test File | Source Module | Purpose |
|-----------|---------------|---------|
| `test_models.py` | `src/models/` | Domain models |
| `test_utils.py` | `src/utils/` | Utility functions |
| `test_exchanges.py` | `src/exchanges/` | Exchange clients |
| `test_services.py` | `src/services/` | Business logic |
| `test_strategies.py` | `src/strategies/` | Trading strategies |
| `test_integration.py` | Full system | End-to-end workflows |

### Test Classes

Group related tests in classes:

```python
@pytest.mark.unit
class TestMarket:
    """Test Market model"""

    def test_market_creation_valid(self):
        # ...

    def test_market_price_validation(self):
        # ...

    def test_market_spread_property(self):
        # ...
```

---

## Continuous Integration

### GitHub Actions (Recommended)

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        pytest --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

### Pre-commit Hooks

Install pre-commit to run tests before commits:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml <<EOF
repos:
-   repo: local
    hooks:
    -   id: pytest-check
        name: pytest
        entry: pytest -m "not slow"
        language: system
        pass_filenames: false
        always_run: true
EOF

# Install hooks
pre-commit install
```

---

## Troubleshooting

### Common Issues

#### Import Errors

```bash
# Error: ModuleNotFoundError: No module named 'src'
# Solution: Run tests from project root
cd /path/to/quantshit
pytest
```

#### Fixture Not Found

```bash
# Error: fixture 'sample_kalshi_market' not found
# Solution: Ensure conftest.py is in tests/ directory
ls tests/conftest.py
```

#### Slow Tests

```bash
# Skip slow tests during development
pytest -m "not slow"

# Or run in parallel
pytest -n auto
```

#### Test Failures After Code Changes

1. Check if test expectations need updating
2. Verify fixtures still match new data structures
3. Update mocks to match new interfaces
4. Run `pytest -vv` for detailed failure info

### Debugging Tests

```bash
# Run with verbose output
pytest -vv

# Show print statements
pytest -s

# Drop into debugger on failure
pytest --pdb

# Show local variables in traceback
pytest -l
```

### Coverage Issues

```bash
# Find uncovered lines
pytest --cov=src --cov-report=term-missing

# Generate HTML report for visual inspection
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

---

## Best Practices

### Do's ✅

- Write tests for all new features
- Test edge cases and error conditions
- Use descriptive test names
- Keep tests independent and isolated
- Mock external dependencies
- Use fixtures for reusable test data
- Run tests before committing
- Maintain high coverage (>80%)

### Don'ts ❌

- Don't test implementation details
- Don't make tests dependent on each other
- Don't use sleep() for timing (use mocks)
- Don't test external APIs directly
- Don't commit failing tests
- Don't skip writing tests "for later"

---

## Test Metrics

### Running Test Metrics

```bash
# Total test count
pytest --collect-only | grep "test session starts"

# Test execution time
pytest --durations=10

# Coverage summary
pytest --cov=src --cov-report=term

# Detailed coverage
pytest --cov=src --cov-report=term-missing
```

### Current Test Statistics

```bash
# Get test stats
pytest --collect-only | tail -1

# Example output:
# 150+ tests collected
```

---

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Python Testing Best Practices](https://realpython.com/pytest-python-testing/)
- [Test-Driven Development](https://www.obeythetestinggoat.com/)
- [Clean Architecture Testing](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

## Maintenance

### Updating Tests

When updating code, follow this checklist:

1. [ ] Update unit tests for changed modules
2. [ ] Update integration tests if workflow changed
3. [ ] Update fixtures if data models changed
4. [ ] Run full test suite: `pytest`
5. [ ] Check coverage: `pytest --cov=src`
6. [ ] Update this documentation if test structure changed

### Adding New Tests

When adding new functionality:

1. [ ] Write unit tests for new functions/classes
2. [ ] Write integration tests if new workflow
3. [ ] Add fixtures if reusable test data needed
4. [ ] Update markers if new test category
5. [ ] Document new test patterns in this file

---

## Quick Reference

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific category
pytest -m unit
pytest -m integration

# Run fast tests only
pytest -m "not slow"

# Parallel execution
pytest -n auto

# Verbose output
pytest -vv

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Debug on failure
pytest --pdb
```

---

**Last Updated**: January 2025
**Maintained By**: Quantshit Development Team
