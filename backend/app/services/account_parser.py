import re
from typing import List, Optional, Tuple
from decimal import Decimal


class AccountParser:
    """Parse and organize account hierarchy from extracted PDF data."""

    def __init__(self):
        self.accounts = []

    def parse_accounts(self, raw_accounts: List[dict]) -> List[dict]:
        """
        Parse raw account data into hierarchical structure.

        Args:
            raw_accounts: List of raw account dictionaries from PDF extraction

        Returns:
            List of parsed account dictionaries with hierarchy information
        """
        parsed = []

        # Sort by code to maintain hierarchical order
        sorted_accounts = sorted(raw_accounts, key=lambda x: self._code_sort_key(x["code"]))

        for idx, account in enumerate(sorted_accounts):
            parsed_account = self._parse_single_account(account, idx)
            if parsed_account:
                parsed.append(parsed_account)

        # Post-process: identify subtotals and add parent codes
        self._identify_subtotals(parsed)
        self._assign_parent_codes(parsed)

        return parsed

    def _parse_single_account(self, raw_account: dict, order_seq: int) -> Optional[dict]:
        """Parse a single raw account into processed format."""
        code = raw_account.get("code", "").strip()
        name = raw_account.get("name", "").strip()

        if not code:
            return None

        # Determine account level (A=1, A.I=2, A.I.1=3, etc.)
        level = self._determine_level(code)

        # Determine account type (ASSET, LIABILITY, EQUITY, ITEM)
        account_type = self._determine_account_type(code, name)

        # Check if subtotal
        is_subtotal = self._is_subtotal(name)

        return {
            "code": code,
            "name": name,
            "level": level,
            "account_type": account_type,
            "is_subtotal": is_subtotal,
            "is_header": self._is_header(code, name),
            "amount_current_year": raw_account.get("amount_current_year"),
            "amount_prior_year": raw_account.get("amount_prior_year"),
            "order_seq": order_seq,
            "parent_code": None,  # Will be filled in post-processing
            "variance_amount": None,  # Will be calculated
            "variance_pct": None,
            "variance_status": None,
        }

    def _determine_level(self, code: str) -> int:
        """
        Determine hierarchical level of account code.

        Examples:
            A → 1
            A.I → 2
            A.I.1 → 3
            A.II → 2
        """
        parts = code.split('.')
        return len(parts)

    def _determine_account_type(self, code: str, name: str) -> str:
        """Determine account type based on code and name."""
        code_upper = code.upper()
        name_upper = name.upper()

        # German HGB structure:
        # A - Anlage (Assets)
        # B - Umlaufvermögen (Current Assets)
        # C, D, E - Liabilities

        if code_upper.startswith('A'):
            return "ASSET"
        elif code_upper.startswith('B'):
            return "ASSET"  # Current assets are still assets
        elif code_upper.startswith('C'):
            return "LIABILITY"
        elif code_upper.startswith('D'):
            return "LIABILITY"
        elif code_upper.startswith('E'):
            return "EQUITY"

        # Check name for keywords
        if any(word in name_upper for word in ['EIGENKAPITAL', 'KAPITAL', 'GEWINN', 'VERLUST']):
            return "EQUITY"
        elif any(word in name_upper for word in ['VERBINDLICHKEITEN', 'RÜCKSTELLUNG', 'SCHULD']):
            return "LIABILITY"

        return "ITEM"

    def _is_subtotal(self, name: str) -> bool:
        """Check if account is a subtotal row."""
        name_upper = name.upper()
        subtotal_keywords = [
            "SUMME",
            "GESAMT",
            "ÜBERTRAG",
            "TOTAL",
            "TOTAL ASSETS",
            "TOTAL LIABILITIES",
        ]
        return any(keyword in name_upper for keyword in subtotal_keywords)

    def _is_header(self, code: str, name: str) -> bool:
        """Check if account is a section header (AKTIVA, PASSIVA, etc.)."""
        name_upper = name.upper()
        headers = ["AKTIVA", "PASSIVA", "EIGENKAPITAL"]
        return name_upper in headers or code in ["A", "B", "C", "D", "E"]

    def _code_sort_key(self, code: str) -> Tuple:
        """
        Generate sort key for account code.

        This ensures proper hierarchical ordering:
        A → A.I → A.I.1 → A.I.2 → A.II → A.II.1 → B → ...

        Returns:
            Tuple for sorting
        """
        parts = code.split('.')
        sort_key = []

        for part in parts:
            # Convert roman numerals to numbers for sorting
            if part in ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX']:
                sort_key.append((0, self._roman_to_int(part)))
            elif part.isdigit():
                sort_key.append((1, int(part)))
            else:
                sort_key.append((2, part))

        return tuple(sort_key)

    def _roman_to_int(self, roman: str) -> int:
        """Convert roman numeral to integer."""
        values = {
            'I': 1, 'V': 5, 'X': 10, 'L': 50,
            'C': 100, 'D': 500, 'M': 1000
        }
        total = 0
        prev_value = 0

        for char in reversed(roman):
            value = values[char]
            if value < prev_value:
                total -= value
            else:
                total += value
            prev_value = value

        return total

    def _identify_subtotals(self, accounts: List[dict]) -> None:
        """Identify subtotal rows (already mostly done, but add heuristics)."""
        for idx, account in enumerate(accounts):
            if account["is_subtotal"]:
                continue

            # Check if this is a parent and might have a subtotal
            code = account["code"]
            level = account["level"]

            # Look ahead for same-level accounts (if none found, might be subtotal)
            # This is already handled by _is_subtotal, so skip for now

    def _assign_parent_codes(self, accounts: List[dict]) -> None:
        """Assign parent codes to all accounts."""
        code_index = {acc["code"]: acc for acc in accounts}

        for account in accounts:
            parent_code = self._get_parent_code(account["code"])
            if parent_code and parent_code in code_index:
                account["parent_code"] = parent_code

    def _get_parent_code(self, code: str) -> Optional[str]:
        """
        Get parent code for a given code.

        Examples:
            A.I.1 → A.I
            A.I → A
            A → None
        """
        parts = code.split('.')

        if len(parts) <= 1:
            return None

        return '.'.join(parts[:-1])

    def calculate_variances(self, accounts: List[dict]) -> List[dict]:
        """
        Calculate variance amounts and percentages for all accounts.

        Args:
            accounts: List of accounts with current and prior year amounts

        Returns:
            Updated accounts list with variance calculated
        """
        for account in accounts:
            cy = account.get("amount_current_year")
            py = account.get("amount_prior_year")

            if cy is None or py is None:
                continue

            # Convert to Decimal for precision
            cy = Decimal(str(cy)) if cy else Decimal(0)
            py = Decimal(str(py)) if py else Decimal(0)

            # Absolute variance
            variance_amount = float(cy - py)
            account["variance_amount"] = variance_amount

            # Percentage variance
            if py != 0:
                variance_pct = float((cy - py) / abs(py) * 100)
                account["variance_pct"] = variance_pct
            else:
                account["variance_pct"] = None

            # Status
            account["variance_status"] = self._get_variance_status(variance_amount, account["account_type"])

        return accounts

    def _get_variance_status(self, variance_amount: float, account_type: str) -> str:
        """Determine variance status based on amount and type."""
        abs_variance = abs(variance_amount)

        if abs_variance < 0.01:
            return "STABLE"
        elif variance_amount > 0:
            if account_type == "ASSET":
                return "IMPROVED"  # More assets = better
            else:
                return "DECLINED"  # More liabilities/equity reduction = worse
        else:
            if account_type == "ASSET":
                return "DECLINED"  # Fewer assets = worse
            else:
                return "IMPROVED"  # Fewer liabilities = better

        return "STABLE"
