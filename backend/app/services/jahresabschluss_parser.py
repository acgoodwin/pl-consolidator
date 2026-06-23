"""
Parser for German Jahresabschluss (annual statement) PDFs with text-based layouts.

Handles columnar text extraction without structured tables.
"""

import re
from typing import List, Dict, Optional, Tuple
from app.utils.german_locale import parse_german_decimal


class JahresabschlussParser:
    """Parse Jahresabschluss balance sheets from text extraction."""

    def __init__(self, text: str):
        self.text = text
        self.lines = [line.strip() for line in text.split('\n') if line.strip()]

    def parse(self) -> Dict:
        """
        Parse the balance sheet text.

        Returns:
            Dictionary with accounts list, each account having:
            - code: "A", "A.I", "A.I.1", etc.
            - name: Description
            - amount_current_year: Current year amount (EUR)
            - amount_prior_year: Prior year amount (EUR)
            - is_subtotal: True if "Summe" line
            - is_header: True if section header (A, B, C)
        """
        accounts = []
        current_section = None
        pending_name = None
        pending_amounts = None

        for line_idx, line in enumerate(self.lines):
            # Skip headers and metadata
            if any(x in line.lower() for x in ['blatt', 'handelsbilanz', 'geschäfts', 'vorjahr']):
                continue
            if 'handelsrecht' in line.lower():
                continue
            if line in ['AKTIVA', 'PASSIVA', 'EUR']:
                continue

            # Try to extract account code and amounts
            account = self._parse_line(line, pending_name, pending_amounts)

            if account:
                accounts.append(account)
                pending_name = None
                pending_amounts = None
            else:
                # This line might be a continuation of the previous account name
                # Store it for the next line that has amounts
                if pending_name:
                    pending_name += " " + line
                else:
                    pending_name = line

        return {"accounts": accounts}

    def _parse_line(self, line: str, prev_name: Optional[str], prev_amounts: Optional[Tuple]) -> Optional[Dict]:
        """
        Parse a single line to extract account information.

        Patterns:
        - "A. Anlagevermögen" (section header)
        - "I. Sachanlagen 131.265,00 94.134,00" (subsection with amounts)
        - "1. andere Anlagen..." (item, may span multiple lines)
        - "Summe Anlagevermögen 131.265,00 94.134,00" (subtotal)
        """

        # Pattern 1: Section header (A., B., C.)
        section_match = re.match(r'^([A-C])\.?\s+(.+)$', line)
        if section_match and not self._has_amounts(line):
            return {
                "code": section_match.group(1),
                "name": section_match.group(2),
                "amount_current_year": None,
                "amount_prior_year": None,
                "is_header": True,
                "is_subtotal": False
            }

        # Pattern 2: Subsection or item with Roman numerals or numbers
        # Examples: "I. Sachanlagen 131.265,00 94.134,00"
        #          "1. andere Anlagen... 131.265,00 94.134,00"

        # Extract amounts from the line
        amounts = self._extract_amounts(line)

        if amounts:
            current_year, prior_year = amounts

            # Check for subtotal
            is_subtotal = "Summe" in line or "Gesamt" in line or "Übertrag" in line

            # Extract code and name
            code = self._extract_code(line)
            name = self._extract_name(line, code)

            if code:
                return {
                    "code": code,
                    "name": name,
                    "amount_current_year": current_year,
                    "amount_prior_year": prior_year,
                    "is_header": False,
                    "is_subtotal": is_subtotal
                }

        return None

    def _has_amounts(self, line: str) -> bool:
        """Check if line has numeric amounts."""
        amount_pattern = r'\d+[\.,]\d{2}'
        return bool(re.search(amount_pattern, line))

    def _extract_amounts(self, line: str) -> Optional[Tuple[float, float]]:
        """
        Extract current year and prior year amounts from a line.

        German format: "131.265,00 94.134,00"
        Returns: (131265.00, 94134.00) or None if not found
        """
        # Pattern: German decimal numbers at end of line
        # Match: number, space, number (ignoring trailing dashes or other chars)
        pattern = r'(\d+[\.,]\d{2})\s+(\d+[\.,]\d{2})'

        matches = list(re.finditer(pattern, line))

        if len(matches) >= 1:
            # Use the last two amounts found (should be current and prior year)
            last_match = matches[-1]
            current = parse_german_decimal(last_match.group(1))
            prior = parse_german_decimal(last_match.group(2))
            return (current, prior)

        return None

    def _extract_code(self, line: str) -> Optional[str]:
        """
        Extract account code from line.

        Patterns:
        - "A.", "B.", "C." (section)
        - "I.", "II.", "III.", etc. (subsection)
        - "1.", "2.", "3." (item)
        """
        # Try section code first
        match = re.match(r'^([A-C])\.\s', line)
        if match:
            return match.group(1)

        # Try roman numeral
        match = re.match(r'^([IVX]+)\.\s', line)
        if match:
            return self._roman_to_code(match.group(1))

        # Try numeric
        match = re.match(r'^(\d+)\.\s', line)
        if match:
            return match.group(1)

        return None

    def _extract_name(self, line: str, code: Optional[str]) -> str:
        """
        Extract account name by removing code and amounts.
        """
        # Remove leading code
        name = line
        if code:
            # Remove code pattern from start
            name = re.sub(r'^([A-C]|[IVX]+|\d+)\.\s*', '', name)

        # Remove trailing amounts (last two EUR values)
        name = re.sub(r'\s+(\d+[\.,]\d{2})\s+(\d+[\.,]\d{2})\s*$', '', name)

        # Remove trailing dash
        name = name.rstrip('-').strip()

        return name

    def _roman_to_code(self, roman: str) -> str:
        """Convert Roman numeral to code (I -> A.I, II -> A.II)."""
        # For now, just return the roman numeral
        # In a real scenario, we'd track the current section
        return roman
