import pytest
from app.services.account_parser import AccountParser


class TestAccountCodeDetection:
    """Test account code detection."""

    def test_valid_account_codes(self):
        """Test valid account code patterns"""
        parser = AccountParser()

        valid_codes = ["A", "A.I", "A.I.1", "A.II", "B.III.2", "C", "D.IV.5"]
        for code in valid_codes:
            assert parser._is_account_code(code), f"Code {code} should be valid"

    def test_invalid_account_codes(self):
        """Test invalid account code patterns"""
        parser = AccountParser()

        invalid_codes = ["AA", "1.A", "A.1.I", "X.Y.Z", ""]
        for code in invalid_codes:
            assert not parser._is_account_code(code), f"Code {code} should be invalid"


class TestAccountHierarchy:
    """Test account hierarchy parsing."""

    def test_determine_level(self):
        """Test account level determination"""
        parser = AccountParser()

        assert parser._determine_level("A") == 1
        assert parser._determine_level("A.I") == 2
        assert parser._determine_level("A.I.1") == 3
        assert parser._determine_level("B.II.2") == 3

    def test_parent_code_extraction(self):
        """Test parent code extraction"""
        parser = AccountParser()

        assert parser._get_parent_code("A.I.1") == "A.I"
        assert parser._get_parent_code("A.I") == "A"
        assert parser._get_parent_code("A") is None

    def test_account_type_determination(self):
        """Test account type classification"""
        parser = AccountParser()

        # Assets
        assert parser._determine_account_type("A", "Sachanlagen") == "ASSET"
        assert parser._determine_account_type("B", "Forderungen") == "ASSET"

        # Liabilities
        assert parser._determine_account_type("C", "Verbindlichkeiten") == "LIABILITY"
        assert parser._determine_account_type("D", "Rückstellungen") == "LIABILITY"

        # Equity
        assert parser._determine_account_type("E", "Eigenkapital") == "EQUITY"

    def test_subtotal_identification(self):
        """Test subtotal row identification"""
        parser = AccountParser()

        assert parser._is_subtotal("Summe Aktiva") is True
        assert parser._is_subtotal("Gesamt Vermögen") is True
        assert parser._is_subtotal("Übertrag") is True
        assert parser._is_subtotal("Forderungen aus L+L") is False

    def test_roman_numeral_conversion(self):
        """Test Roman numeral to integer conversion"""
        parser = AccountParser()

        assert parser._roman_to_int("I") == 1
        assert parser._roman_to_int("II") == 2
        assert parser._roman_to_int("III") == 3
        assert parser._roman_to_int("IV") == 4
        assert parser._roman_to_int("V") == 5
        assert parser._roman_to_int("IX") == 9


class TestVarianceCalculation:
    """Test variance calculation."""

    def test_positive_variance(self):
        """Test positive variance calculation"""
        parser = AccountParser()
        accounts = [{
            "code": "A.I.1",
            "name": "Test Account",
            "level": 3,
            "account_type": "ASSET",
            "is_subtotal": False,
            "is_header": False,
            "amount_current_year": 150000.00,
            "amount_prior_year": 100000.00,
            "order_seq": 1,
            "parent_code": "A.I",
            "variance_amount": None,
            "variance_pct": None,
            "variance_status": None,
        }]

        parser.calculate_variances(accounts)
        account = accounts[0]

        assert account["variance_amount"] == 50000.00
        assert abs(account["variance_pct"] - 50.0) < 0.01

    def test_negative_variance(self):
        """Test negative variance calculation"""
        parser = AccountParser()
        accounts = [{
            "code": "A.I.1",
            "name": "Test Account",
            "level": 3,
            "account_type": "ASSET",
            "is_subtotal": False,
            "is_header": False,
            "amount_current_year": 75000.00,
            "amount_prior_year": 100000.00,
            "order_seq": 1,
            "parent_code": "A.I",
            "variance_amount": None,
            "variance_pct": None,
            "variance_status": None,
        }]

        parser.calculate_variances(accounts)
        account = accounts[0]

        assert account["variance_amount"] == -25000.00
        assert abs(account["variance_pct"] - (-25.0)) < 0.01

    def test_zero_prior_year(self):
        """Test variance when prior year is zero"""
        parser = AccountParser()
        accounts = [{
            "code": "A.I.1",
            "name": "Test Account",
            "level": 3,
            "account_type": "ASSET",
            "is_subtotal": False,
            "is_header": False,
            "amount_current_year": 50000.00,
            "amount_prior_year": 0.00,
            "order_seq": 1,
            "parent_code": "A.I",
            "variance_amount": None,
            "variance_pct": None,
            "variance_status": None,
        }]

        parser.calculate_variances(accounts)
        account = accounts[0]

        assert account["variance_amount"] == 50000.00
        assert account["variance_pct"] is None  # Can't calculate percentage
