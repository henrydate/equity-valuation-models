"""
Sum-of-Parts (SOTP) Valuation
=============================

The right way to value a diversified miner: value each asset on its own
economics, sum to a division, sum divisions to an enterprise value, then bridge
to equity (less net debt, minorities, and the present value of unallocated
corporate costs) and divide by shares.

Asset after-tax free cash flow (transparent, deliberately simple):

    revenue   = production x realised price
    EBITDA    = revenue - (production x unit cash cost) - royalties
    tax       = tax_rate x max(EBITDA - sustaining capex, 0)   # sus-capex as a depreciation proxy
    FCF        = (EBITDA - tax - sustaining capex - growth capex) x ownership stake

discounted at the group WACC (from the Stage 1 ledger). The depreciation proxy
is a documented simplification; a deeper build would carry an explicit
depletion schedule. Commodity price decks are discretionary ledger inputs and
flow in here as the per-year ``price`` map.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional

import pandas as pd


@dataclass
class AssetValuation:
    """DCF of a single producing asset (commodity-agnostic)."""

    name: str
    commodity: str
    production: Dict[int, float]                 # units per year
    price: Dict[int, float]                      # realised price per unit (from the commodity deck)
    unit_cash_cost: Dict[int, float]             # C1 / AISC per unit
    sustaining_capex: Dict[int, float] = field(default_factory=dict)
    growth_capex: Dict[int, float] = field(default_factory=dict)
    royalty_rate: float = 0.0                    # fraction of revenue
    tax_rate: float = 0.30
    closure_cost: float = 0.0                    # undiscounted cash outflow at end of life
    stake: float = 1.0                           # ownership fraction

    def fcf_schedule(self) -> Dict[int, float]:
        out: Dict[int, float] = {}
        for y in sorted(self.production):
            prod = self.production[y]
            revenue = prod * self.price.get(y, 0.0)
            opex = prod * self.unit_cash_cost.get(y, 0.0)
            royalty = revenue * self.royalty_rate
            ebitda = revenue - opex - royalty
            sus = self.sustaining_capex.get(y, 0.0)
            grow = self.growth_capex.get(y, 0.0)
            tax = self.tax_rate * max(ebitda - sus, 0.0)
            out[y] = (ebitda - tax - sus - grow) * self.stake
        return out

    def npv(self, discount_rate: float, base_year: int) -> float:
        years = sorted(self.production)
        if not years:
            return 0.0
        fcf = self.fcf_schedule()
        npv = sum(fcf[y] / (1 + discount_rate) ** (y - base_year) for y in years)
        if self.closure_cost:
            last = years[-1]
            npv -= self.stake * self.closure_cost / (1 + discount_rate) ** (last - base_year)
        return npv


@dataclass
class Division:
    """A reporting division: a group of assets plus any division-level overhead."""

    name: str
    assets: List[AssetValuation]
    overhead_pv: float = 0.0       # PV of division overhead (a drag, subtracted)

    def npv(self, discount_rate: float, base_year: int) -> float:
        return sum(a.npv(discount_rate, base_year) for a in self.assets) - self.overhead_pv


@dataclass
class SumOfParts:
    """Group sum-of-parts: divisions -> enterprise value -> equity -> per share."""

    company: str
    base_year: int
    discount_rate: float                         # group WACC
    divisions: List[Division]
    other_assets: float = 0.0                    # investments, JVs carried at value
    corporate_pv: float = 0.0                    # PV of unallocated corporate costs (drag)
    net_debt: float = 0.0
    minorities: float = 0.0
    shares_outstanding: float = 1.0

    def division_values(self) -> Dict[str, float]:
        return {d.name: d.npv(self.discount_rate, self.base_year) for d in self.divisions}

    def enterprise_value(self) -> float:
        return sum(self.division_values().values()) + self.other_assets - self.corporate_pv

    def equity_value(self) -> float:
        return self.enterprise_value() - self.net_debt - self.minorities

    def value_per_share(self) -> float:
        if self.shares_outstanding <= 0:
            raise ValueError("shares_outstanding must be > 0")
        return self.equity_value() / self.shares_outstanding

    def revalue(self, discount_rate: Optional[float] = None, price_factor: float = 1.0) -> float:
        """Per-share value under an alternative discount rate and a uniform price
        shift. Used for sensitivity / scenario tables; does not mutate the original."""
        rate = self.discount_rate if discount_rate is None else discount_rate
        divisions = []
        for d in self.divisions:
            assets = [replace(a, price={y: p * price_factor for y, p in a.price.items()})
                      for a in d.assets]
            divisions.append(replace(d, assets=assets))
        return replace(self, discount_rate=rate, divisions=divisions).value_per_share()

    def summary_table(self) -> pd.DataFrame:
        ev = self.enterprise_value()
        rows: List[tuple] = []
        for name, val in self.division_values().items():
            rows.append((name, val, val / ev if ev else float("nan")))
        if self.other_assets:
            rows.append(("Other assets", self.other_assets, self.other_assets / ev if ev else float("nan")))
        if self.corporate_pv:
            rows.append(("Less: Corporate (PV)", -self.corporate_pv, -self.corporate_pv / ev if ev else float("nan")))
        rows.append(("Enterprise value", ev, 1.0))
        rows.append(("Less: Net debt", -self.net_debt, float("nan")))
        if self.minorities:
            rows.append(("Less: Minorities", -self.minorities, float("nan")))
        rows.append(("Equity value", self.equity_value(), float("nan")))
        rows.append(("Shares (m)", self.shares_outstanding, float("nan")))
        rows.append(("Value per share", self.value_per_share(), float("nan")))
        return pd.DataFrame(rows, columns=["Component", "Value", "% of EV"]).set_index("Component")
