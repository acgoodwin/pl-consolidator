import re
from decimal import Decimal
from typing import Optional


def parse_german_decimal(text: str) -> Optional[float]:
    """
    Parse German-formatted decimal numbers.

    German format uses '.' for thousands separator and ',' for decimal point.
    Examples:
        "1.234,56" → 1234.56
        "1234,56" → 1234.56
        "1234" → 1234.0
        "123,4" → 123.4

    Args:
        text: German-formatted number string

    Returns:
        float value or None if parsing fails
    """
    if not text or not isinstance(text, str):
        return None

    text = text.strip()

    # Remove whitespace
    text = text.replace(" ", "")

    # Handle empty string
    if not text:
        return None

    # Remove currency symbols and other non-numeric characters except . and ,
    text = re.sub(r'[^\d.,\-]', '', text)

    # Handle negative numbers
    is_negative = text.startswith('-')
    if is_negative:
        text = text[1:]

    # Determine format based on separator positions
    if ',' in text and '.' in text:
        # Both separators present: . is thousands, , is decimal
        # E.g., "1.234.567,89"
        last_comma_pos = text.rfind(',')
        last_dot_pos = text.rfind('.')

        if last_comma_pos > last_dot_pos:
            # Comma is after dot → comma is decimal
            text = text.replace('.', '').replace(',', '.')
        else:
            # Dot is after comma → dot is decimal (unusual but handle it)
            text = text.replace(',', '').replace('.', '')
            text = text + '.0'  # Add decimal point
    elif ',' in text:
        # Only comma: could be decimal or thousands separator
        parts = text.split(',')
        if len(parts) == 2:
            if len(parts[1]) == 2:
                # Likely decimal (cents): "1234,56"
                text = text.replace(',', '.')
            elif len(parts[1]) == 3:
                # Likely thousands: "1,234" or "1,234"
                text = text.replace(',', '')
            else:
                # Default to decimal
                text = text.replace(',', '.')
    elif '.' in text:
        # Only period: could be thousands or decimal
        parts = text.split('.')
        if len(parts[-1]) <= 2:
            # Last part has ≤2 digits: likely decimal
            if len(parts) == 2 and len(parts[0]) <= 3:
                # "12.34" → decimal
                pass  # Keep as is
            else:
                # "1.234.567" → thousands, remove all
                text = text.replace('.', '')
        else:
            # Last part has >2 digits: likely thousands
            text = text.replace('.', '')

    # Convert to float
    try:
        value = float(text)
        if is_negative:
            value = -value
        return value
    except (ValueError, TypeError):
        return None


def format_german_decimal(value: Optional[float], decimals: int = 2) -> str:
    """
    Format a number as German-style decimal.

    Examples:
        1234.56 → "1.234,56"
        1000000.1 → "1.000.000,10"

    Args:
        value: Number to format
        decimals: Number of decimal places

    Returns:
        German-formatted string
    """
    if value is None:
        return ""

    is_negative = value < 0
    value = abs(value)

    # Format with correct decimal places
    formatted = f"{value:,.{decimals}f}"

    # Replace comma with placeholder (to avoid confusion)
    formatted = formatted.replace(",", "THOUSANDS_SEP")
    formatted = formatted.replace(".", ",")
    formatted = formatted.replace("THOUSANDS_SEP", ".")

    if is_negative:
        formatted = "-" + formatted

    return formatted


def validate_balance_sheet(total_assets: float, total_liabilities: float, total_equity: float) -> tuple[bool, float]:
    """
    Validate that Assets = Liabilities + Equity.

    Returns:
        (is_valid, variance_amount)
        is_valid: True if balance ≤ 0.01 EUR
        variance_amount: Assets - (Liabilities + Equity)
    """
    variance = total_assets - (total_liabilities + total_equity)
    is_valid = abs(variance) <= 0.01  # Allow 1 cent tolerance for rounding
    return is_valid, variance
