"""
EV/EBITDA sum-of-parts + a normalized-FCF DCF cross-check
=========================================================

A second valuation path, complementary to the bottom-up production DCF in
:mod:`src.sotp`. Where ``sotp`` builds value from per-asset tonnes x price, this
module values each *segment* off its reported Underlying EBITDA x a peer
EV/EBITDA multiple, and triangulates with a group normalized-FCF perpetuity.

This is the right approach when you have audited segment EBITDA (a results
release) but not a clean multi-decade, per-asset operating model: it leans on
disclosed, verifiable figures and isolates the judgement to (a) the multiples
and (b) the DCF's discount rate / long-run growth -- each recorded in the ledger
as a discretionary input.

All inputs are in the reporting currency (US$m for BHP); the final per-share
figure is converted to the listing currency with an explicit FX rate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd


@dataclass
class Segment:
    """One reporting segment valued on an EV/EBITDA multiple."""

    name: str
    ebitda: float              # reporting-currency m, underlying
    multiple: float            # EV/EBITDA (x)
    note: str = ""

    @property
    def ev(self) -> float:
        return self.ebitda * self.multiple


@dataclass
class ComparablesValuation:
    """EV/EBITDA sum-of-parts -> equity bridge -> per share (converted to AUD)."""

    segments: List[Segment]
    other_assets: float = 0.0          # e.g. Jansen at invested capital (pre-production)
    corporate_drag_ebitda: float = 0.0  # recurring unallocated cost (negative)
    corporate_multiple: float = 6.0
    net_debt: float = 0.0
    nci: float = 0.0
    shares_m: float = 1.0              # shares outstanding, millions
    usd_per_aud: float = 0.65          # FX: USD per 1 AUD (AUD/USD spot)

    def segment_values(self) -> Dict[str, float]:
        return {s.name: s.ev for s in self.segments}

    def corporate_value(self) -> float:
        return self.corporate_drag_ebitda * self.corporate_multiple

    def enterprise_value(self) -> float:
        return sum(self.segment_values().values()) + self.other_assets + self.corporate_value()

    def equity_value_usd(self) -> float:
        return self.enterprise_value() - self.net_debt - self.nci

    def value_per_share_usd(self) -> float:
        return self.equity_value_usd() / self.shares_m

    def value_per_share(self) -> float:
        """Per share in the LISTING currency (AUD) -- what you compare to the market."""
        return self.value_per_share_usd() / self.usd_per_aud

    def summary_table(self) -> pd.DataFrame:
        """Bridge table in the LISTING currency (AUD); shape matches src.sotp.SumOfParts
        so note.py renders it unchanged. Source figures are US$m (see the ledger); each
        line is converted at the FX rate so the column reads in AUDm consistently."""
        f = 1.0 / self.usd_per_aud   # US$m -> A$m
        ev = self.enterprise_value()

        def pct(v):
            return v / ev if ev else float("nan")

        rows: List[tuple] = []
        for name, val in self.segment_values().items():
            rows.append((name, val * f, pct(val)))
        if self.other_assets:
            rows.append(("Potash / other (invested capital)", self.other_assets * f, pct(self.other_assets)))
        if self.corporate_drag_ebitda:
            rows.append(("Less: corporate (capitalised)", self.corporate_value() * f, pct(self.corporate_value())))
        rows.append(("Enterprise value", ev * f, 1.0))
        rows.append(("Less: net debt", -self.net_debt * f, float("nan")))
        rows.append(("Less: non-controlling interests", -self.nci * f, float("nan")))
        rows.append(("Equity value", self.equity_value_usd() * f, float("nan")))
        rows.append(("Shares (m)", self.shares_m, float("nan")))
        rows.append(("Value per share", self.value_per_share(), float("nan")))
        return pd.DataFrame(rows, columns=["Component", "Value", "% of EV"]).set_index("Component")


@dataclass
class NormalizedDCF:
    """Group normalized-FCF perpetuity -- a discount-rate cross-check on the comps.

    FCF = NOPAT + D&A - sustaining capex, where NOPAT = (EBITDA - D&A) x (1 - tax).
    EV = FCF x (1 + g) / (WACC - g)  [Gordon growth on a steady, sustaining-only state].
    Suited to a diversified major that reinvests sustaining capex to hold output;
    the perpetuity is a documented simplification of finite reserve lives.
    """

    ebitda: float
    da: float
    tax_rate: float
    sustaining_capex: float
    wacc: float
    growth: float
    net_debt: float
    nci: float
    shares_m: float
    usd_per_aud: float = 0.65
    affiliates: float = 0.0   # equity-accounted investments carried outside EBITDA, if any

    def fcf(self) -> float:
        ebit = self.ebitda - self.da
        nopat = ebit * (1 - self.tax_rate)
        return nopat + self.da - self.sustaining_capex

    def enterprise_value(self) -> float:
        if self.wacc <= self.growth:
            raise ValueError("WACC must exceed the perpetuity growth rate")
        return self.fcf() * (1 + self.growth) / (self.wacc - self.growth) + self.affiliates

    def equity_value_usd(self) -> float:
        return self.enterprise_value() - self.net_debt - self.nci

    def value_per_share_usd(self) -> float:
        return self.equity_value_usd() / self.shares_m

    def value_per_share(self) -> float:
        return self.value_per_share_usd() / self.usd_per_aud

    def sensitivity(self, wacc_deltas: List[float], growth_levels: List[float]) -> pd.DataFrame:
        """Per-share (A$) over a WACC band x long-run growth grid."""
        from dataclasses import replace
        data = {}
        for g in growth_levels:
            col = f"g={g:.1%}"
            data[col] = [round(replace(self, wacc=self.wacc + d, growth=g).value_per_share(), 2)
                         for d in wacc_deltas]
        idx = [f"{self.wacc + d:.2%}" for d in wacc_deltas]
        df = pd.DataFrame(data, index=idx)
        df.index.name = "WACC \\ growth"
        return df
