"""
Data scaffold
=============

Pulls the fast-moving, objective market data from yfinance to *pre-fill* the
ledger as UNVERIFIED scaffold entries (source = external_data). The analyst
then verifies or overrides each against a primary source -- the scaffold is a
starting point and an error-check (see the ``vs_scaffold_within`` guardrail),
never the final word.

Reported fundamentals are deliberately NOT trusted from here: for a deep
single-name valuation they are entered from the filings. yfinance gives us the
live market wrapper (price, shares, market cap, a raw beta to sanity-check
against), not the asset-level detail a sum-of-parts needs.

The yfinance import is lazy so the rest of the package (and the test suite)
never needs the network.
"""

from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional, Tuple

from .ledger import InputKind, LedgerEntry, VerificationStatus
from .financial_statements import SourceOfTruth

# (ledger key, label, unit, yfinance info field, scale_to_millions)
_MARKET_FIELDS: List[Tuple[str, str, str, str, bool]] = [
    ("group.share_price", "Share price (last close)", "__px__", "currentPrice", False),
    ("group.shares_outstanding", "Shares outstanding", "m shares", "sharesOutstanding", True),
    ("group.market_cap", "Market capitalisation", "__cur_m__", "marketCap", True),
    ("wacc.equity_beta_raw", "Raw equity beta (yfinance)", "x", "beta", False),
]


def fetch_info(ticker: str) -> dict:
    """Lazy yfinance fetch of the ticker ``info`` dict (requires network)."""
    import yfinance as yf  # lazy import -- keeps the package importable offline
    return yf.Ticker(ticker).info


def scaffold_entries(info: dict, ticker: str, as_of: Optional[str] = None,
                     price_currency: str = "AUD", live: bool = True) -> Dict[str, LedgerEntry]:
    """Build UNVERIFIED scaffold ledger entries from a yfinance-style info dict.

    Pure function: pass any dict (real yfinance ``info`` or a test fixture).
    ``live=False`` marks the entries as an illustrative placeholder rather than a
    real pull, so an offline demo never presents a frozen number as live data.
    Market-cap units carry the price currency (e.g. ``"AUD m"``) so the AUD
    listing is never silently mixed with the USD valuation basis.
    """
    as_of = as_of or date.today().isoformat()
    out: Dict[str, LedgerEntry] = {}
    for key, label, unit, field_name, to_millions in _MARKET_FIELDS:
        raw = info.get(field_name)
        if raw is None:
            continue
        value = raw
        if to_millions and isinstance(raw, (int, float)):
            value = round(raw / 1_000_000, 2)
        if unit == "__px__":
            resolved_unit = price_currency
        elif unit == "__cur_m__":
            resolved_unit = f"{price_currency} m"
        else:
            resolved_unit = unit
        citation = (f"yfinance {ticker} (field: {field_name})" if live
                    else f"ILLUSTRATIVE placeholder -- {ticker} {field_name}; not a live pull")
        out[key] = LedgerEntry(
            key=key,
            label=label,
            value=value,
            unit=resolved_unit,
            kind=InputKind.HARD_FACT,
            source_type=SourceOfTruth.EXTERNAL_DATA,
            citation=citation,
            as_of=as_of,
            verification=VerificationStatus.UNVERIFIED,
            provenance_method="auto_pull" if live else "manual",
            entered_by="system",
            scaffold_value=value,
        )
    return out


def load_scaffold(ledger, ticker: str, as_of: Optional[str] = None,
                  price_currency: Optional[str] = None) -> Dict[str, LedgerEntry]:
    """Fetch live data and add scaffold entries straight onto a ledger."""
    price_currency = price_currency or ledger.presentation_currency
    entries = scaffold_entries(fetch_info(ticker), ticker, as_of, price_currency)
    for entry in entries.values():
        ledger.add(entry)
    return entries
