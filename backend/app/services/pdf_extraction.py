import pdfplumber
from typing import Optional, Tuple, List
from app.utils.german_locale import parse_german_decimal
import re


class PdfExtractionService:
    """Service for extracting text and tables from PDF documents."""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf = None
        self.pages = []

    def open(self):
        """Open the PDF document."""
        try:
            self.pdf = pdfplumber.open(self.pdf_path)
            self.pages = self.pdf.pages
            return True
        except Exception as e:
            raise Exception(f"Failed to open PDF: {str(e)}")

    def close(self):
        """Close the PDF document."""
        if self.pdf:
            self.pdf.close()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def extract_text(self, page_num: int = 0) -> str:
        """
        Extract all text from a page.

        Args:
            page_num: Page index (0-based)

        Returns:
            Extracted text
        """
        if not self.pages or page_num >= len(self.pages):
            return ""

        return self.pages[page_num].extract_text()

    def detect_document_type(self) -> Optional[str]:
        """
        Detect the type of financial document.

        Returns:
            'BILANZ' (Balance Sheet), 'P_AND_L' (Income Statement), or None
        """
        text = self.extract_text(0)  # Check first page
        text_upper = text.upper()

        if "HANDELSBILANZEN" in text_upper or "BILANZ" in text_upper:
            return "BILANZ"
        elif "ENTWICKLUNGSÜBERSICHT" in text_upper or "ERFOLGSRECHNUNG" in text_upper:
            return "P_AND_L"
        elif "JAHRESÜBERSICHT" in text_upper:
            return "SUSA"  # Monthly ledger

        return None

    def extract_balance_sheet_data(self) -> dict:
        """
        Extract balance sheet (Bilanz) data from the PDF.

        Returns:
            Dictionary with extracted account data and metadata
        """
        result = {
            "company_name": None,
            "fiscal_year": None,
            "accounts": [],
            "warnings": []
        }

        # Extract company info from first page
        first_page_text = self.extract_text(0)
        result["company_name"] = self._extract_company_name(first_page_text)
        result["fiscal_year"] = self._extract_fiscal_year(first_page_text)

        # Extract tables from all pages
        all_accounts = []
        for page_num, page in enumerate(self.pages):
            tables = page.extract_tables()
            for table in tables or []:
                accounts = self._parse_balance_sheet_table(table, page_num)
                all_accounts.extend(accounts)

        # Merge and deduplicate accounts
        result["accounts"] = self._merge_accounts(all_accounts)

        return result

    def _extract_company_name(self, text: str) -> Optional[str]:
        """Extract company name from text."""
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            # Look for GmbH, AG, KG patterns
            if any(suffix in line for suffix in ['GmbH', 'AG', 'KG', 'Ltd']):
                return line
        return None

    def _extract_fiscal_year(self, text: str) -> Optional[int]:
        """Extract fiscal year from text."""
        # Look for "zum 31. Dezember XXXX" or "31.12.XXXX"
        match = re.search(r'(?:zum\s+)?31\.?\s*(?:Dezember|12\.?)\s+(\d{4})', text, re.IGNORECASE)
        if match:
            return int(match.group(1))

        # Fallback: look for any 4-digit year
        match = re.search(r'20\d{2}', text)
        if match:
            return int(match.group(0))

        return None

    def _parse_balance_sheet_table(self, table: List[List[str]], page_num: int) -> List[dict]:
        """
        Parse a single table from balance sheet PDF.

        Args:
            table: 2D list representing table cells
            page_num: Page number where table was found

        Returns:
            List of account dictionaries
        """
        accounts = []

        # Skip header rows (typically contain column names like "EUR", "Geschäftsjahr", "Vorjahr")
        for row_idx, row in enumerate(table):
            if row_idx < 2:  # Skip first few rows (likely headers)
                continue

            account = self._parse_balance_sheet_row(row, row_idx, page_num)
            if account:
                accounts.append(account)

        return accounts

    def _parse_balance_sheet_row(self, row: List[str], row_idx: int, page_num: int) -> Optional[dict]:
        """
        Parse a single row from balance sheet table.

        Expected columns (varies by layout):
        - Code (A.I.1, A.II, etc.)
        - Name/Description
        - Amount Current Year (EUR)
        - Amount Prior Year (EUR)

        Returns:
            Account dictionary or None if row is empty/invalid
        """
        if not row or all(not cell or not str(cell).strip() for cell in row):
            return None

        # Clean up cells
        cells = [str(cell).strip() if cell else "" for cell in row]

        # Try to identify columns
        # Look for account code pattern (A.I.1, A.II, etc.)
        code = None
        code_idx = -1

        for idx, cell in enumerate(cells):
            if self._is_account_code(cell):
                code = cell
                code_idx = idx
                break

        if not code:
            return None  # Skip rows without account codes

        # Name is typically after code or in the next non-empty cell
        name = ""
        name_idx = -1
        if code_idx + 1 < len(cells):
            name = cells[code_idx + 1]
            name_idx = code_idx + 1

        # Find amount columns (typically EUR values after code/name)
        amounts_start_idx = max(code_idx, name_idx) + 1

        # Extract amounts (current year and prior year)
        amounts = []
        for idx in range(amounts_start_idx, len(cells)):
            cell = cells[idx]
            if cell and self._is_numeric_value(cell):
                amounts.append(cell)

        # Need at least 2 amounts (current year and prior year) for balance sheet
        if len(amounts) < 2:
            # Single amount - might be subtotal, try to extract anyway
            if amounts:
                amount_current_year = self._parse_amount(amounts[0])
            else:
                return None
            amount_prior_year = None
        else:
            amount_current_year = self._parse_amount(amounts[0])
            amount_prior_year = self._parse_amount(amounts[1])

        return {
            "code": code,
            "name": name,
            "amount_current_year": amount_current_year,
            "amount_prior_year": amount_prior_year,
            "page_num": page_num,
            "raw_row": cells
        }

    def _is_account_code(self, text: str) -> bool:
        """Check if text matches account code pattern (A.I.1, A.II, etc.)."""
        # German HGB chart of accounts uses letters and roman numerals
        pattern = r'^[A-C](?:\.(?:I{1,3}|V|IX|IV|VI|VII|VIII))*(?:\.\d+)?$'
        return bool(re.match(pattern, text.strip()))

    def _is_numeric_value(self, text: str) -> bool:
        """Check if text is a numeric value (possibly German formatted)."""
        # German format: 1.234.567,89 or variations
        cleaned = text.replace('.', '').replace(',', '').replace('-', '').strip()
        return cleaned.isdigit()

    def _parse_amount(self, text: str) -> Optional[float]:
        """Parse amount from text (German or English format)."""
        if not text:
            return None
        return parse_german_decimal(text)

    def _merge_accounts(self, accounts: List[dict]) -> List[dict]:
        """
        Merge accounts from multiple pages, deduplicating by code.

        If an account appears multiple times (e.g., across pages),
        keep the version with complete data.
        """
        merged = {}

        for account in accounts:
            code = account["code"]
            if code not in merged:
                merged[code] = account
            else:
                # Keep the one with more data
                existing = merged[code]
                if (account.get("amount_prior_year") and
                    not existing.get("amount_prior_year")):
                    existing["amount_prior_year"] = account["amount_prior_year"]

        return list(merged.values())
