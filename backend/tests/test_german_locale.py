import pytest
from app.utils.german_locale import parse_german_decimal, format_german_decimal, validate_balance_sheet


class TestGermanDecimalParsing:
    """Test German decimal number parsing."""

    def test_parse_german_format(self):
        """Test parsing German format: 1.234.567,89"""
        result = parse_german_decimal("1.234.567,89")
        assert result == 1234567.89

    def test_parse_german_thousands_only(self):
        """Test parsing with thousands separator only: 1.234,00"""
        result = parse_german_decimal("1.234,00")
        assert result == 1234.0

    def test_parse_german_decimal_only(self):
        """Test parsing with decimal only: 1234,56"""
        result = parse_german_decimal("1234,56")
        assert result == 1234.56

    def test_parse_integer(self):
        """Test parsing integer: 1234"""
        result = parse_german_decimal("1234")
        assert result == 1234.0

    def test_parse_with_whitespace(self):
        """Test parsing with whitespace"""
        result = parse_german_decimal("  1.234,56  ")
        assert result == 1234.56

    def test_parse_negative(self):
        """Test parsing negative number"""
        result = parse_german_decimal("-1.234,56")
        assert result == -1234.56

    def test_parse_invalid(self):
        """Test parsing invalid input returns None"""
        result = parse_german_decimal("abc")
        assert result is None

    def test_parse_empty_string(self):
        """Test parsing empty string returns None"""
        result = parse_german_decimal("")
        assert result is None


class TestGermanDecimalFormatting:
    """Test German decimal number formatting."""

    def test_format_german_standard(self):
        """Test formatting to German standard"""
        result = format_german_decimal(1234.56)
        assert result == "1.234,56"

    def test_format_german_large(self):
        """Test formatting large number"""
        result = format_german_decimal(1234567.89)
        assert result == "1.234.567,89"

    def test_format_german_integer(self):
        """Test formatting integer"""
        result = format_german_decimal(1000)
        assert result == "1.000,00"

    def test_format_german_decimal_places(self):
        """Test formatting with custom decimal places"""
        result = format_german_decimal(1234.5, decimals=1)
        assert result == "1.234,5"

    def test_format_german_negative(self):
        """Test formatting negative number"""
        result = format_german_decimal(-1234.56)
        assert result == "-1.234,56"

    def test_format_german_none(self):
        """Test formatting None returns empty string"""
        result = format_german_decimal(None)
        assert result == ""


class TestBalanceSheetValidation:
    """Test balance sheet validation."""

    def test_balanced_sheet(self):
        """Test balanced balance sheet"""
        total_assets = 100000.00
        total_liabilities = 60000.00
        total_equity = 40000.00

        is_valid, variance = validate_balance_sheet(
            total_assets, total_liabilities, total_equity
        )

        assert is_valid is True
        assert variance == 0.0

    def test_unbalanced_sheet(self):
        """Test unbalanced balance sheet"""
        total_assets = 100000.00
        total_liabilities = 60000.00
        total_equity = 39000.00  # Off by 1000

        is_valid, variance = validate_balance_sheet(
            total_assets, total_liabilities, total_equity
        )

        assert is_valid is False
        assert variance == 1000.0

    def test_tolerance(self):
        """Test tolerance of 1 cent"""
        total_assets = 100000.00
        total_liabilities = 60000.00
        total_equity = 40000.005  # Off by 0.5 cents (should be valid)

        is_valid, variance = validate_balance_sheet(
            total_assets, total_liabilities, total_equity
        )

        assert is_valid is True
