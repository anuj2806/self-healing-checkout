"""
Tax Calculation Module for Checkout.

WARNING: Contains an intentional production bug where calculating tax for US states
not explicitly defined in US_STATE_TAX_RATES causes an unhandled KeyError!
"""

from typing import Optional

US_STATE_TAX_RATES = {
    "CA": 0.0825,
    "NY": 0.0850,
    "TX": 0.0625,
    "WA": 0.0650,
    "IL": 0.0625,
}

VAT_RATES = {
    "GB": 0.20,
    "DE": 0.19,
    "FR": 0.20,
    "AU": 0.10,
    "IN": 0.18,
}

DEFAULT_GLOBAL_TAX_RATE = 0.05


def calculate_tax(subtotal: float, country: str = "US", state: Optional[str] = None) -> float:
    """
    Calculate sales or VAT tax based on country jurisdiction and state.

    NOTE: Intentional bug in v1.0.0:
    Direct dictionary lookup on US_STATE_TAX_RATES[state] without fallback
    raises KeyError if state is not in the hardcoded list (e.g., 'FL', 'OR', 'NV')
    or TypeError if state is None.
    """
    if subtotal <= 0:
        return 0.0

    normalized_country = (country or "US").strip().upper()

    if normalized_country == "US":
        # INTENTIONAL BUG:
        # Direct lookup causes KeyError when state is not in US_STATE_TAX_RATES (e.g., 'FL')
        tax_rate = US_STATE_TAX_RATES[state]
        return round(subtotal * tax_rate, 2)
    elif normalized_country in VAT_RATES:
        return round(subtotal * VAT_RATES[normalized_country], 2)
    else:
        return round(subtotal * DEFAULT_GLOBAL_TAX_RATE, 2)
