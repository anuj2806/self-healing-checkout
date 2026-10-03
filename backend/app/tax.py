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
    Safely calculates tax rate with fallback for unlisted jurisdictions.
    """
    if subtotal <= 0:
        return 0.0

    normalized_country = (country or "US").strip().upper()

    if normalized_country == "US":
        # HEALED BY AGENT: Safe state tax lookup with fallback for unlisted jurisdictions
        normalized_state = state.strip().upper() if state else ""
        DEFAULT_US_TAX_RATE = 0.0625  # Standard average US state tax fallback
        US_STATE_TAX_RATES.get(normalized_state, DEFAULT_US_TAX_RATE)
        return round(subtotal * tax_rate, 2)
    elif normalized_country in VAT_RATES:
        return round(subtotal * VAT_RATES[normalized_country], 2)
    else:
        return round(subtotal * DEFAULT_GLOBAL_TAX_RATE, 2)
