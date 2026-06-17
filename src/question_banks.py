"""
Question banks
==============

Data-driven definitions of the elicitation flows. A *bank* is an ordered list
of input specs; each spec declares the question, the benchmark anchor shown to
the analyst, the default source type, the guardrails to run, and -- where
methods genuinely compete -- a method registry with per-method sub-questions
and guardrails (the hybrid model: a house default, switchable first-class).

This module is the WACC bank, the template every other input bank copies.
Anchors are illustrative mid-2026 levels; they orient the analyst, they are not
the answer. See ``docs/elicitation_design.md``.
"""

from __future__ import annotations

from typing import Dict, List

from .ledger import InputKind
from .financial_statements import SourceOfTruth

# Soft sanity bands reused across similar inputs
_ERP_BAND = {"check": "within_range", "params": {"range": [0.035, 0.075]}}
_BETA_BAND = {"check": "within_range", "params": {"range": [0.7, 1.3]}}

CURRENCY_BASIS = {
    "key": "wacc.currency_basis",
    "label": "WACC currency basis",
    "unit": "ccy",
    "kind": InputKind.DISCRETIONARY,
    "default_source_type": SourceOfTruth.ASSUMPTION,
    "prompt": "Which currency are the cash flows in -- USD (functional) or AUD?",
    "anchor": "BHP reports USD; commodities priced USD. House default: USD, convert final $/share to AUD at spot.",
    "guardrails": [],
}

RISK_FREE = {
    "key": "wacc.risk_free",
    "label": "Risk-free rate",
    "unit": "%",
    "kind": InputKind.DISCRETIONARY,
    "default_source_type": SourceOfTruth.EXTERNAL_DATA,
    "prompt": "10Y government bond yield in the cash-flow currency?",
    "anchor": "US 10Y ~4.2% (FRED) | AU 10Y ~4.3% (RBA), as of the valuation date.",
    "guardrails": [{"check": "within_range", "params": {"range": [0.01, 0.08]}}],
}

ERP = {
    "key": "wacc.erp",
    "label": "Equity risk premium",
    "unit": "%",
    "kind": InputKind.DISCRETIONARY,
    "default_source_type": SourceOfTruth.ANALYST_ESTIMATE,
    "prompt": "Equity risk premium (expected market return over the risk-free)?",
    "anchor": "Historical developed-mkt ~6% | Damodaran implied ~4.8%.",
    "default_method": "implied",
    "methods": {
        "historical": {"label": "Historical average", "asks": ["market", "window"], "guardrails": [_ERP_BAND]},
        "implied": {"label": "Damodaran implied (forward)", "asks": ["vintage"], "guardrails": [_ERP_BAND]},
    },
    "guardrails": [],
}

BETA = {
    "key": "wacc.equity_beta",
    "label": "Equity beta",
    "unit": "x",
    "kind": InputKind.DISCRETIONARY,
    "default_source_type": SourceOfTruth.ANALYST_ESTIMATE,
    "prompt": "Equity beta? (the scaffold holds the raw yfinance beta to sanity-check against)",
    "anchor": "Diversified-miner peers (RIO/VALE/Anglo) unlevered ~0.8-1.0; Damodaran sector ~0.9.",
    "default_method": "bottom_up",
    "methods": {
        "bottom_up": {
            "label": "Bottom-up (unlever peers, re-lever to target gearing)",
            "asks": ["peer_set", "relever_gearing"],
            "guardrails": [_BETA_BAND, "relever_gearing_matches_weights"],
        },
        "regression": {
            "label": "Own regression vs index",
            "asks": ["window", "index", "blume_adjusted"],
            "guardrails": [_BETA_BAND],
        },
        "comparable": {
            "label": "Damodaran sector beta",
            "asks": ["vintage"],
            "guardrails": [_BETA_BAND],
        },
    },
    "guardrails": [],
}

COST_OF_DEBT = {
    "key": "wacc.cost_of_debt",
    "label": "Pre-tax cost of debt",
    "unit": "%",
    "kind": InputKind.DISCRETIONARY,
    "default_source_type": SourceOfTruth.COMPANY_FILING,
    "prompt": "Pre-tax cost of debt?",
    "anchor": "BHP ~A/A3 -> spread ~1.0-1.5% over rf -> ~5.3%.",
    "default_method": "rating_implied",
    "methods": {
        "actual": {"label": "Weighted average from the debt note", "asks": ["citation"], "guardrails": []},
        "rating_implied": {"label": "Rating-implied (rf + credit spread)", "asks": ["rating", "spread"], "guardrails": []},
    },
    "guardrails": [],
}

TAX_RATE = {
    "key": "wacc.tax_rate",
    "label": "Tax rate (for the discount)",
    "unit": "%",
    "kind": InputKind.DISCRETIONARY,
    "default_source_type": SourceOfTruth.EXTERNAL_DATA,
    "prompt": "Marginal tax rate? (royalties are opex, not tax -- don't double-count)",
    "anchor": "AUS statutory 30%; BHP effective ~33% with the global mix.",
    "guardrails": [{"check": "within_range", "params": {"range": [0.0, 0.5]}}],
}

MV_EQUITY = {
    "key": "wacc.mv_equity",
    "label": "Market value of equity",
    "unit": "m",
    "kind": InputKind.HARD_FACT,
    "default_source_type": SourceOfTruth.EXTERNAL_DATA,
    "prompt": "Market value of equity (share price x shares outstanding)?",
    "anchor": "Cross-check against the scaffold market cap.",
    "guardrails": [{"check": "vs_scaffold_within", "params": {"tol_pct": 0.05}}],
}

MV_DEBT = {
    "key": "wacc.mv_debt",
    "label": "Market value of net debt",
    "unit": "m",
    # NOTE: capital-structure method switching (current market vs target
    # through-cycle gearing) is the 4th multi-method input -- a documented
    # roadmap item; v1 captures net debt as a single figure.
    "kind": InputKind.HARD_FACT,
    "default_source_type": SourceOfTruth.COMPANY_FILING,
    "prompt": "Market value of net debt?",
    "anchor": "BHP net debt ~US$10bn (FY25); low gearing ~12-15%.",
    "guardrails": [],
}

WACC_BANK: List[dict] = [
    CURRENCY_BASIS, RISK_FREE, ERP, BETA, COST_OF_DEBT, TAX_RATE, MV_EQUITY, MV_DEBT,
]


# --- Mining: commodity price decks (the highest-judgement valuation drivers) ---
# A deck's value is a per-year map plus a "long_run" level; the long_run_vs_spot
# guardrail flags a deck that sits far from spot (spot supplied in context).
def _price_deck(key: str, label: str, unit: str, anchor: str) -> dict:
    return {
        "key": key, "label": label, "unit": unit, "kind": InputKind.DISCRETIONARY,
        "default_source_type": SourceOfTruth.ANALYST_ESTIMATE,
        "prompt": f"{label} price deck (per-year levels + a long_run)?",
        "anchor": anchor,
        "guardrails": [{"check": "long_run_vs_spot", "params": {"threshold": 0.30}}],
    }


IRON_ORE_DECK = _price_deck("ironore.price_deck", "Iron ore 62% Fe CFR China", "USD/t",
                            "Spot ~US$105/t; consensus front years; long-run ~US$75-80 (cost support).")
COPPER_DECK = _price_deck("copper.price_deck", "Copper (LME)", "USD/t",
                          "Spot ~US$9,500/t; long-run ~US$9,000-10,000 (incentive price).")
MET_COAL_DECK = _price_deck("metcoal.price_deck", "Met (coking) coal", "USD/t",
                            "Spot ~US$200/t; long-run ~US$160-180.")
POTASH_DECK = _price_deck("potash.price_deck", "Potash (MOP)", "USD/t",
                          "Spot ~US$300/t; long-run ~US$300-350 (Jansen ramp).")

MINING_BANK: List[dict] = [IRON_ORE_DECK, COPPER_DECK, MET_COAL_DECK, POTASH_DECK]

BANKS: Dict[str, List[dict]] = {"wacc": WACC_BANK, "mining": MINING_BANK}


def get_bank(name: str) -> List[dict]:
    return BANKS[name]
