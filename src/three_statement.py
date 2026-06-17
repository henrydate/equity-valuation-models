"""
Articulated Three-Statement Model
=================================

A transparent, fully-articulated income statement / balance sheet / cash-flow
model that **genuinely foots**. The earlier `BalanceSheet` stub faked a balance
by setting equity = assets; this one is driven by explicit flows so the
accounting identities hold *by construction*:

- Retained earnings roll forward:  RE_t = RE_{t-1} + NPAT_t - dividends_t
- Non-current assets roll forward: NCA_t = NCA_{t-1} + capex_t - D&A_t
- Cash rolls from the cash-flow statement: Cash_t = Cash_{t-1} + net change
- Therefore Assets = Liabilities + Equity every year (proof: the change in
  cash from the CF statement is exactly the residual the balance sheet needs).

Inputs are plain floats (provenance now lives in the ledger, not here).
:func:`validate_three_statement_integrity` checks the three identities to the
cent and is re-exported from ``financial_statements`` for backwards
compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pandas as pd

PL_ROWS = [
    "Revenue", "COGS", "Gross Profit", "Operating Expenses", "EBITDA",
    "D&A", "EBIT", "Interest", "Pre-tax Profit", "Tax", "NPAT", "Dividends",
]
BS_ROWS = [
    "Cash", "Receivables", "Inventory", "Non-current Assets", "Total Assets",
    "Payables", "Debt", "Total Liabilities",
    "Share Capital", "Retained Earnings", "Total Equity",
    "Total Liabilities & Equity",
]
CF_ROWS = [
    "NPAT", "Add: D&A", "Less: Change in Receivables", "Less: Change in Inventory",
    "Add: Change in Payables", "Operating Cash Flow", "Capex", "Investing Cash Flow",
    "Debt Drawdown / (Repayment)", "Equity Issuance", "Dividends Paid",
    "Financing Cash Flow", "Net Change in Cash", "Opening Cash", "Closing Cash",
]


@dataclass
class ThreeStatementModel:
    """Build three articulated statements from explicit per-year drivers."""

    company: str
    base_year: int
    years: List[int]                       # forecast years, e.g. [2027, 2028, 2029]
    opening: Dict[str, float]              # balances at base_year (see _OPENING_KEYS)
    revenue: Dict[int, float]
    cogs: Dict[int, float]

    opex: Dict[int, float] = field(default_factory=dict)
    da: Dict[int, float] = field(default_factory=dict)          # depreciation + amortisation
    interest: Dict[int, float] = field(default_factory=dict)
    tax_rate: float = 0.30
    capex: Dict[int, float] = field(default_factory=dict)
    debt: Dict[int, float] = field(default_factory=dict)        # ending balance; carries prior if absent
    equity_issuance: Dict[int, float] = field(default_factory=dict)
    dividends: Dict[int, float] = field(default_factory=dict)
    receivables_days: Optional[float] = None                    # if None, NWC line carries opening
    inventory_days: Optional[float] = None
    payables_days: Optional[float] = None

    def _o(self, key: str) -> float:
        return float(self.opening.get(key, 0.0))

    @staticmethod
    def _totals(bs: pd.DataFrame, col) -> None:
        ta = bs.loc["Cash", col] + bs.loc["Receivables", col] + bs.loc["Inventory", col] + bs.loc["Non-current Assets", col]
        tl = bs.loc["Payables", col] + bs.loc["Debt", col]
        te = bs.loc["Share Capital", col] + bs.loc["Retained Earnings", col]
        bs.loc["Total Assets", col] = ta
        bs.loc["Total Liabilities", col] = tl
        bs.loc["Total Equity", col] = te
        bs.loc["Total Liabilities & Equity", col] = tl + te

    def build(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        years = list(self.years)
        pl = pd.DataFrame(index=PL_ROWS, columns=years, dtype=float)
        cf = pd.DataFrame(index=CF_ROWS, columns=years, dtype=float)
        bs = pd.DataFrame(index=BS_ROWS, columns=[self.base_year] + years, dtype=float)

        # opening balance sheet (base_year column)
        b = self.base_year
        for line, key in [("Cash", "cash"), ("Receivables", "receivables"),
                          ("Inventory", "inventory"), ("Non-current Assets", "non_current_assets"),
                          ("Payables", "payables"), ("Debt", "debt"),
                          ("Share Capital", "share_capital"), ("Retained Earnings", "retained_earnings")]:
            bs.loc[line, b] = self._o(key)
        self._totals(bs, b)

        prev = b
        for y in years:
            rev = float(self.revenue[y])
            cogs = float(self.cogs[y])
            opex = float(self.opex.get(y, 0.0))
            da = float(self.da.get(y, 0.0))
            interest = float(self.interest.get(y, 0.0))
            capex = float(self.capex.get(y, 0.0))
            div = float(self.dividends.get(y, 0.0))
            eq_iss = float(self.equity_issuance.get(y, 0.0))

            gross = rev - cogs
            ebitda = gross - opex
            ebit = ebitda - da
            pretax = ebit - interest
            tax = pretax * self.tax_rate if pretax > 0 else 0.0
            npat = pretax - tax

            # working capital (days drive the level; else carry prior)
            ar = rev * self.receivables_days / 365 if self.receivables_days is not None else bs.loc["Receivables", prev]
            inv = cogs * self.inventory_days / 365 if self.inventory_days is not None else bs.loc["Inventory", prev]
            ap = cogs * self.payables_days / 365 if self.payables_days is not None else bs.loc["Payables", prev]
            d_ar = ar - bs.loc["Receivables", prev]
            d_inv = inv - bs.loc["Inventory", prev]
            d_ap = ap - bs.loc["Payables", prev]

            nca = bs.loc["Non-current Assets", prev] + capex - da
            debt = float(self.debt.get(y, bs.loc["Debt", prev]))
            d_debt = debt - bs.loc["Debt", prev]
            sc = bs.loc["Share Capital", prev] + eq_iss
            re = bs.loc["Retained Earnings", prev] + npat - div

            ocf = npat + da - d_ar - d_inv + d_ap
            icf = -capex
            fcf = d_debt + eq_iss - div
            net = ocf + icf + fcf
            opening_cash = bs.loc["Cash", prev]
            closing_cash = opening_cash + net

            # P&L
            pl.loc["Revenue", y] = rev
            pl.loc["COGS", y] = cogs
            pl.loc["Gross Profit", y] = gross
            pl.loc["Operating Expenses", y] = opex
            pl.loc["EBITDA", y] = ebitda
            pl.loc["D&A", y] = da
            pl.loc["EBIT", y] = ebit
            pl.loc["Interest", y] = interest
            pl.loc["Pre-tax Profit", y] = pretax
            pl.loc["Tax", y] = tax
            pl.loc["NPAT", y] = npat
            pl.loc["Dividends", y] = div

            # Balance sheet
            bs.loc["Cash", y] = closing_cash
            bs.loc["Receivables", y] = ar
            bs.loc["Inventory", y] = inv
            bs.loc["Non-current Assets", y] = nca
            bs.loc["Payables", y] = ap
            bs.loc["Debt", y] = debt
            bs.loc["Share Capital", y] = sc
            bs.loc["Retained Earnings", y] = re
            self._totals(bs, y)

            # Cash flow
            cf.loc["NPAT", y] = npat
            cf.loc["Add: D&A", y] = da
            cf.loc["Less: Change in Receivables", y] = -d_ar
            cf.loc["Less: Change in Inventory", y] = -d_inv
            cf.loc["Add: Change in Payables", y] = d_ap
            cf.loc["Operating Cash Flow", y] = ocf
            cf.loc["Capex", y] = -capex
            cf.loc["Investing Cash Flow", y] = icf
            cf.loc["Debt Drawdown / (Repayment)", y] = d_debt
            cf.loc["Equity Issuance", y] = eq_iss
            cf.loc["Dividends Paid", y] = -div
            cf.loc["Financing Cash Flow", y] = fcf
            cf.loc["Net Change in Cash", y] = net
            cf.loc["Opening Cash", y] = opening_cash
            cf.loc["Closing Cash", y] = closing_cash

            prev = y

        return pl, bs, cf

    def validate(self) -> Dict[str, List[str]]:
        pl, bs, cf = self.build()
        return validate_three_statement_integrity(pl, bs, cf)


def validate_three_statement_integrity(
    pl: pd.DataFrame,
    bs: pd.DataFrame,
    cf: pd.DataFrame,
    tol: float = 0.01,
) -> Dict[str, List[str]]:
    """Check the three articulation identities to within ``tol``.

    1. Balance sheet balances:        Total Assets == Total Liabilities & Equity
    2. Retained earnings bridge:      d(Retained Earnings) == NPAT - Dividends
    3. Cash flow reconciles:          Net change == OCF + ICF + FCF, and
                                      Closing - Opening == Net change, and
                                      Closing Cash == balance-sheet Cash
    """
    errors: List[str] = []
    warnings: List[str] = []

    def has(df: pd.DataFrame, row: str) -> bool:
        return row in df.index

    years = list(pl.columns)
    bs_cols = list(bs.columns)

    # 1. Balance
    if has(bs, "Total Assets") and has(bs, "Total Liabilities & Equity"):
        for y in bs_cols:
            a = bs.loc["Total Assets", y]
            le = bs.loc["Total Liabilities & Equity", y]
            if abs(a - le) > tol:
                errors.append(f"{y}: balance sheet does not balance (assets {a:.2f} != L+E {le:.2f})")
    else:
        warnings.append("balance check skipped: missing Total Assets / Total Liabilities & Equity")

    # 2. Retained-earnings bridge
    if has(bs, "Retained Earnings") and has(pl, "NPAT"):
        for y in years:
            if y not in bs_cols:
                warnings.append(f"{y}: RE bridge skipped (no balance-sheet column)")
                continue
            i = bs_cols.index(y)
            if i == 0:
                warnings.append(f"{y}: RE bridge skipped (no opening column)")
                continue
            prev = bs_cols[i - 1]
            d_re = bs.loc["Retained Earnings", y] - bs.loc["Retained Earnings", prev]
            div = pl.loc["Dividends", y] if has(pl, "Dividends") else 0.0
            expected = pl.loc["NPAT", y] - div
            if abs(d_re - expected) > tol:
                errors.append(f"{y}: RE bridge fails (d_RE {d_re:.2f} != NPAT-div {expected:.2f})")
    else:
        warnings.append("RE bridge skipped: missing Retained Earnings / NPAT")

    # 3. Cash-flow reconciliation
    if has(cf, "Net Change in Cash"):
        for y in years:
            net = cf.loc["Net Change in Cash", y]
            if all(has(cf, r) for r in ("Operating Cash Flow", "Investing Cash Flow", "Financing Cash Flow")):
                s = cf.loc["Operating Cash Flow", y] + cf.loc["Investing Cash Flow", y] + cf.loc["Financing Cash Flow", y]
                if abs(net - s) > tol:
                    errors.append(f"{y}: net change {net:.2f} != OCF+ICF+FCF {s:.2f}")
            if has(cf, "Opening Cash") and has(cf, "Closing Cash"):
                if abs((cf.loc["Closing Cash", y] - cf.loc["Opening Cash", y]) - net) > tol:
                    errors.append(f"{y}: closing - opening cash != net change")
                if has(bs, "Cash") and y in bs_cols and abs(cf.loc["Closing Cash", y] - bs.loc["Cash", y]) > tol:
                    errors.append(f"{y}: CF closing cash != balance-sheet cash")
    else:
        warnings.append("cash reconciliation skipped: missing Net Change in Cash")

    return {"errors": errors, "warnings": warnings, "status": "PASS" if not errors else "FAIL"}
