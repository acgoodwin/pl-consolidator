from typing import List, Tuple, Optional
from decimal import Decimal


class ValidationService:
    """Validate extracted financial data."""

    def __init__(self):
        pass

    def validate_balance_sheet(self, accounts: List[dict]) -> Tuple[bool, Optional[float], List[str]]:
        """
        Validate balance sheet equation: Assets = Liabilities + Equity.

        Args:
            accounts: List of accounts with amounts

        Returns:
            (is_valid, variance, warnings)
            is_valid: True if balance ≤ 0.01 EUR
            variance: Assets - (Liabilities + Equity)
            warnings: List of warning messages
        """
        warnings = []

        # Calculate totals by account type
        total_assets = Decimal(0)
        total_liabilities = Decimal(0)
        total_equity = Decimal(0)

        asset_accounts = []
        liability_accounts = []
        equity_accounts = []

        for account in accounts:
            account_type = account.get("account_type", "ITEM")
            cy_amount = account.get("amount_current_year")

            if cy_amount is None:
                continue

            cy_decimal = Decimal(str(cy_amount))

            if account_type == "ASSET":
                total_assets += cy_decimal
                asset_accounts.append(account)
            elif account_type == "LIABILITY":
                total_liabilities += cy_decimal
                liability_accounts.append(account)
            elif account_type == "EQUITY":
                total_equity += cy_decimal
                equity_accounts.append(account)

        # Check balance equation
        variance = total_assets - (total_liabilities + total_equity)
        is_valid = abs(variance) <= Decimal("0.01")

        if not is_valid:
            variance_float = float(variance)
            warnings.append(
                f"Balance sheet does not balance: Assets (€{float(total_assets):,.2f}) - "
                f"(Liabilities (€{float(total_liabilities):,.2f}) + Equity (€{float(total_equity):,.2f})) = "
                f"€{variance_float:,.2f} (variance)"
            )

        # Validate individual sections
        cy_asset_warnings = self._validate_asset_section(asset_accounts)
        cy_liability_warnings = self._validate_liability_section(liability_accounts)
        cy_equity_warnings = self._validate_equity_section(equity_accounts)

        warnings.extend(cy_asset_warnings)
        warnings.extend(cy_liability_warnings)
        warnings.extend(cy_equity_warnings)

        # Prior year validation (if available)
        py_total_assets = Decimal(0)
        py_total_liabilities = Decimal(0)
        py_total_equity = Decimal(0)

        for account in accounts:
            account_type = account.get("account_type", "ITEM")
            py_amount = account.get("amount_prior_year")

            if py_amount is None:
                continue

            py_decimal = Decimal(str(py_amount))

            if account_type == "ASSET":
                py_total_assets += py_decimal
            elif account_type == "LIABILITY":
                py_total_liabilities += py_decimal
            elif account_type == "EQUITY":
                py_total_equity += py_decimal

        py_variance = py_total_assets - (py_total_liabilities + py_total_equity)
        if abs(py_variance) > Decimal("0.01"):
            warnings.append(
                f"Prior year balance sheet does not balance: variance = "
                f"€{float(py_variance):,.2f}"
            )

        return is_valid, float(variance), warnings

    def _validate_asset_section(self, accounts: List[dict]) -> List[str]:
        """Validate asset section."""
        warnings = []

        # Check for negative assets (unusual)
        negative_assets = [acc for acc in accounts if acc.get("amount_current_year", 0) < 0]
        if negative_assets:
            asset_names = ", ".join([acc["name"] for acc in negative_assets])
            warnings.append(f"Negative asset values found: {asset_names}")

        return warnings

    def _validate_liability_section(self, accounts: List[dict]) -> List[str]:
        """Validate liability section."""
        warnings = []

        # Check for negative liabilities (unusual)
        negative_liabilities = [acc for acc in accounts if acc.get("amount_current_year", 0) < 0]
        if negative_liabilities:
            liability_names = ", ".join([acc["name"] for acc in negative_liabilities])
            warnings.append(f"Negative liability values found: {liability_names}")

        return warnings

    def _validate_equity_section(self, accounts: List[dict]) -> List[str]:
        """Validate equity section."""
        warnings = []

        # Check for negative equity (indicates loss)
        total_equity = sum(Decimal(str(acc.get("amount_current_year", 0))) for acc in accounts)
        if total_equity < 0:
            warnings.append(f"Negative equity: €{float(total_equity):,.2f} - Company may be technically insolvent")

        return warnings

    def validate_extraction(self, accounts: List[dict]) -> Tuple[bool, List[str]]:
        """
        Validate that extraction is complete and reasonable.

        Args:
            accounts: List of extracted accounts

        Returns:
            (is_valid, warnings)
        """
        warnings = []

        if not accounts:
            return False, ["No accounts extracted"]

        # Check for minimum number of accounts
        if len(accounts) < 5:
            warnings.append(f"Only {len(accounts)} accounts extracted - may be incomplete")

        # Check for accounts without amounts
        accounts_no_cy = [acc for acc in accounts if acc.get("amount_current_year") is None]
        if accounts_no_cy:
            pct = len(accounts_no_cy) / len(accounts) * 100
            if pct > 20:
                warnings.append(
                    f"{pct:.1f}% of accounts missing current year amounts - may indicate extraction issues"
                )

        # Check for duplicate codes
        codes = [acc["code"] for acc in accounts]
        duplicates = [code for code in set(codes) if codes.count(code) > 1]
        if duplicates:
            warnings.append(f"Duplicate account codes found: {', '.join(duplicates)}")

        is_valid = len(warnings) == 0 or (
            len(warnings) == 1 and "accounts extracted" not in warnings[0]
        )

        return is_valid, warnings
