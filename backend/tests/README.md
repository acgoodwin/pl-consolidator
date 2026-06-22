# Test Suite

This directory contains unit tests, integration tests, and test fixtures for the P&L Consolidator backend.

## Running Tests

### Install test dependencies
```bash
pip install pytest pytest-asyncio pytest-cov
```

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/test_german_locale.py -v
```

### Run with coverage report
```bash
pytest --cov=app tests/
```

## Test Structure

### `test_german_locale.py`
Tests for German decimal number parsing and formatting.

**Test Classes:**
- `TestGermanDecimalParsing`: Parse German format (1.234.567,89 → 1234567.89)
- `TestGermanDecimalFormatting`: Format to German standard
- `TestBalanceSheetValidation`: Validate Assets = Liabilities + Equity

**Example:**
```python
from app.utils.german_locale import parse_german_decimal

result = parse_german_decimal("1.234.567,89")
assert result == 1234567.89
```

### `test_account_parser.py`
Tests for account code parsing and hierarchy processing.

**Test Classes:**
- `TestAccountCodeDetection`: Valid/invalid account codes (A, A.I, A.I.1)
- `TestAccountHierarchy`: Level determination, parent codes, account types
- `TestVarianceCalculation`: Absolute variance, percentage, status

**Example:**
```python
from app.services.account_parser import AccountParser

parser = AccountParser()
assert parser._determine_level("A.I.1") == 3
assert parser._get_parent_code("A.I.1") == "A.I"
```

## Test Fixtures

### `fixtures/expected_accounts_2024.json`
Expected output from extracting sample Jahresabschluss PDF.

Contains:
- Company name, fiscal year, document type
- Sample accounts with codes, names, levels, types
- Current year and prior year amounts
- Balance sheet validation data

Use in integration tests to verify extraction accuracy:
```python
import json

with open("tests/fixtures/expected_accounts_2024.json") as f:
    expected = json.load(f)

assert extracted_data["company_name"] == expected["company_name"]
assert len(extracted_data["accounts"]) == len(expected["accounts"])
```

## Sample PDFs

To test with real PDFs, place anonymized financial statement PDFs in `fixtures/`:

- `sample_jahresabschluss_2024.pdf` - Annual balance sheet
- `sample_jahresabschluss_2023.pdf` - Prior year for comparison
- `malformed_pdf.pdf` - Invalid/corrupted PDF for error testing

## Coverage Goals

- **Unit tests:** >85% coverage on utility functions
- **Integration tests:** >70% coverage on API endpoints
- **Manual testing:** Balance sheet extraction from real PDFs

## Running Specific Tests

```bash
# Test German decimal parsing only
pytest tests/test_german_locale.py::TestGermanDecimalParsing -v

# Test account hierarchy
pytest tests/test_account_parser.py::TestAccountHierarchy -v

# Run with print output
pytest tests/ -s

# Run with verbose output
pytest tests/ -vv

# Stop on first failure
pytest tests/ -x

# Run last failed tests
pytest tests/ --lf
```

## CI/CD Integration

For GitHub Actions, use:
```yaml
- name: Run tests
  run: |
    pip install -r backend/requirements.txt
    pytest backend/tests/ --cov=app --cov-report=xml
```

## Adding New Tests

1. Create test file: `tests/test_<module>.py`
2. Use pytest conventions: `def test_<feature>()`
3. Use descriptive test names
4. Add docstrings explaining what is tested
5. Run locally: `pytest tests/test_<module>.py -v`

Example:
```python
def test_my_feature(session, test_company):
    """Test that my feature works correctly."""
    # Arrange
    obj = MyClass(company=test_company)
    
    # Act
    result = obj.do_something()
    
    # Assert
    assert result is not None
```
