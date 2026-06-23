"""
Parse columnar German financial statements using character positioning.

Reconstructs the two-column layout (AKTIVA left, PASSIVA right) from pdfplumber chars.
"""

import re
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from app.utils.german_locale import parse_german_decimal


class ColumnarBalanceSheetParser:
    """Parse balance sheets with two-column layout using char positioning."""

    def __init__(self, page):
        """
        Args:
            page: pdfplumber page object
        """
        self.page = page
        self.chars = page.chars
        self.width = page.width
        self.midpoint = page.width / 2

    def parse(self) -> List[Dict]:
        """
        Parse the balance sheet.

        Returns:
            List of accounts with code, name, amounts
        """
        # Reconstruct lines using character positions
        lines_left = self._extract_column_lines(left=True)
        lines_right = self._extract_column_lines(left=False)

        # Parse each column independently
        accounts_left = self._parse_column_lines(lines_left, side="AKTIVA")
        accounts_right = self._parse_column_lines(lines_right, side="PASSIVA")

        # Combine both sides
        accounts = accounts_left + accounts_right

        return accounts

    def _extract_column_lines(self, left: bool = True) -> List[str]:
        """
        Extract text lines from one column, preserving line breaks.

        Args:
            left: If True, extract left column (AKTIVA), else right (PASSIVA)

        Returns:
            List of text lines
        """
        # Filter chars to one column
        chars = [c for c in self.chars if (c['x0'] < self.midpoint) == left]

        if not chars:
            return []

        # Group characters into lines by y-position
        # Chars with similar y0 values are on the same line
        lines_dict = defaultdict(list)
        y_threshold = 3  # Characters within 3 points are on same line

        for char in sorted(chars, key=lambda c: (round(c['y0'] / y_threshold) * y_threshold, c['x0'])):
            y_key = round(char['y0'] / y_threshold) * y_threshold
            lines_dict[y_key].append(char)

        # Convert character lists to strings
        lines = []
        for y_key in sorted(lines_dict.keys()):
            # Sort chars left-to-right
            chars_on_line = sorted(lines_dict[y_key], key=lambda c: c['x0'])
            # Reconstruct text (preserve spacing roughly)
            text_parts = []
            last_x = None

            for char in chars_on_line:
                if last_x and char['x0'] - last_x > 5:
                    text_parts.append(" ")  # Add space for gap
                text_parts.append(char['text'])
                last_x = char['x1']

            line_text = "".join(text_parts).strip()
            if line_text:
                lines.append(line_text)

        return lines

    def _parse_column_lines(self, lines: List[str], side: str = "AKTIVA") -> List[Dict]:
        """
        Parse lines from one column into accounts.

        Args:
            lines: List of text lines from column
            side: "AKTIVA" or "PASSIVA" (for classification)

        Returns:
            List of account dictionaries
        """
        accounts = []
        current_section = None
        section_count = {}

        for line in lines:
            # Skip headers and formatting
            if not line or line.lower() in ['aktiva', 'passiva', 'eur', 'geschäftsjahr', 'vorjahr']:
                continue

            # Parse the line
            account = self._parse_line(line, side)
            if account:
                accounts.append(account)

        return accounts

    def _parse_line(self, line: str, side: str) -> Optional[Dict]:
        """
        Parse a single line to extract account data.

        Returns:
            Account dict or None
        """
        # Skip meta lines
        if any(x in line.lower() for x in ['blatt', 'handelsbilanz', 'handelsrecht']):
            return None

        # Extract amounts (last two EUR numbers on the line)
        amounts = self._extract_amounts_from_line(line)
        if not amounts:
            return None

        current_year, prior_year = amounts

        # Extract account code
        code = self._extract_code(line)
        if not code:
            return None

        # Extract name
        name = self._extract_name(line, code)

        return {
            "code": code,
            "name": name,
            "amount_current_year": current_year,
            "amount_prior_year": prior_year,
            "side": side,
            "is_header": self._is_header(line),
            "is_subtotal": self._is_subtotal(line)
        }

    def _extract_amounts_from_line(self, line: str) -> Optional[Tuple[float, float]]:
        """Extract the two amount columns from a line."""
        # Pattern: two German decimal numbers
        pattern = r'(\d+[\.,]\d{2})\s+(\d+[\.,]\d{2})'
        matches = list(re.finditer(pattern, line))

        if not matches:
            return None

        # Use last match (should be the actual amounts, not footnotes)
        last = matches[-1]
        try:
            current = parse_german_decimal(last.group(1))
            prior = parse_german_decimal(last.group(2))
            return (current, prior)
        except:
            return None

    def _extract_code(self, line: str) -> Optional[str]:
        """Extract account code (A, A.I, A.I.1, etc.)"""
        # Match section: "A.", "B.", "C."
        match = re.match(r'^([A-C])\.\s+', line)
        if match:
            return match.group(1)

        # Match subsection: "I.", "II.", "III.", etc.
        match = re.match(r'^([IVX]+)\.\s+', line)
        if match:
            return match.group(1)

        # Match item: "1.", "2.", "3.", etc.
        match = re.match(r'^(\d+)\.\s+', line)
        if match:
            return match.group(1)

        return None

    def _extract_name(self, line: str, code: str) -> str:
        """Extract account name by removing code and amounts."""
        # Remove code from start
        name = re.sub(r'^([A-C]|[IVX]+|\d+)\.\s*', '', line)

        # Remove amounts from end
        name = re.sub(r'\s+\d+[\.,]\d{2}\s+\d+[\.,]\d{2}\s*$', '', name)

        # Remove trailing dash
        name = name.rstrip('- ').strip()

        return name

    def _is_header(self, line: str) -> bool:
        """Check if this is a section header line."""
        return bool(re.match(r'^[A-C]\.\s+', line))

    def _is_subtotal(self, line: str) -> bool:
        """Check if this is a subtotal/sum line."""
        keywords = ['summe', 'gesamt', 'übertrag', 'total']
        return any(kw in line.lower() for kw in keywords)
