"""
Financial utility functions for Pythia.
"""
from decimal import Decimal
from typing import Optional


def get_yahoo_symbol(symbol: str, exchange: Optional[str] = None) -> str:
    """Convert symbol to Yahoo Finance format (.BK for Thai stocks)."""
    if exchange and exchange.upper() in ("SET", "MAI"):
        if not symbol.endswith(".BK"):
            return f"{symbol}.BK"
    return symbol


def format_currency(value: Decimal, currency: str = "THB") -> str:
    """Format currency value with symbol."""
    symbols = {"THB": "฿", "USD": "$", "EUR": "€"}
    sym = symbols.get(currency, currency)
    return f"{sym}{value:,.2f}"


def safe_decimal(value: float, precision: int = 6) -> Decimal:
    """Safely convert float to Decimal."""
    return Decimal(str(round(value, precision)))
