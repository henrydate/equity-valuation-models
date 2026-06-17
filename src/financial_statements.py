"""
Three-Statement Financial Model Framework
==========================================

Core module for constructing integrated income statement, balance sheet, 
and cash flow statement models from first principles.

Principles:
- All line items explicitly modelled with transparent assumptions
- Cross-statement integrity checks (e.g., net income → retained earnings, 
  capex → PPE movements)
- Provenance tracking for each assumption (source, date, basis)
- Formula-first approach: no hard-coded values in calculations
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import pandas as pd
import numpy as np
from datetime import datetime


class SourceOfTruth(Enum):
    """Hierarchy for data provenance and credibility."""
    MANAGEMENT_GUIDANCE = 1
    COMPANY_FILING = 2
    BROKER_CONSENSUS = 3
    ANALYST_ESTIMATE = 4
    EXTERNAL_DATA = 5
    ASSUMPTION = 6


@dataclass
class Assumption:
    """Provenance-tagged assumption for model transparency."""
    name: str
    value: float
    unit: str
    source: SourceOfTruth
    basis: str  # e.g., "Historical 3yr avg", "Management guidance FY25"
    date: datetime
    notes: Optional[str] = None
    
    def __repr__(self):
        return (f"{self.name}: {self.value} {self.unit} "
                f"({self.source.name} - {self.basis})")


@dataclass
class IncomeStatement:
    """
    Income Statement Model
    =====================
    P&L forecast built from revenue drivers and cost structure.
    """
    
    # Metadata
    company: str
    forecast_years: int
    base_year: int
    
    # Revenue drivers (primary assumptions)
    revenue_drivers: Dict[str, Assumption] = field(default_factory=dict)
    
    # Cost structure (% of revenue or absolute)
    cogs_pct_revenue: Assumption = None
    opex_fixed: Dict[int, Assumption] = field(default_factory=dict)  # Year -> assumption
    opex_variable_pct: Assumption = None
    
    # Other P&L items
    depreciation: Dict[int, Assumption] = field(default_factory=dict)
    amortization: Dict[int, Assumption] = field(default_factory=dict)
    interest_expense: Dict[int, Assumption] = field(default_factory=dict)
    tax_rate: Assumption = None
    
    # Working capital items
    change_in_nwc: Dict[int, float] = field(default_factory=dict)
    
    # Output dataframe
    _forecast: Optional[pd.DataFrame] = None
    
    def calculate_revenue(self, year: int) -> float:
        """
        Calculate revenue for given year.
        Override this method for company-specific revenue logic.
        """
        raise NotImplementedError(
            "Subclass must implement calculate_revenue() with specific logic"
        )
    
    def forecast(self) -> pd.DataFrame:
        """
        Build full P&L forecast.
        
        Returns:
            DataFrame with rows = P&L line items, cols = forecast years
        """
        years = list(range(self.base_year + 1, self.base_year + self.forecast_years + 1))
        
        # Initialize output
        pl = pd.DataFrame(index=[
            'Revenue',
            'COGS',
            'Gross Profit',
            'Gross Margin %',
            'OPEX',
            'EBITDA',
            'Depreciation',
            'Amortization',
            'EBIT',
            'Interest Expense',
            'EBT',
            'Tax (at statutory rate)',
            'NPAT',
        ], columns=years)
        
        for year in years:
            revenue = self.calculate_revenue(year)
            cogs = revenue * self.cogs_pct_revenue.value
            gross_profit = revenue - cogs
            
            opex = self.opex_fixed.get(year, Assumption(
                name=f'OPEX {year}', 
                value=0, 
                unit='$m',
                source=SourceOfTruth.ASSUMPTION,
                basis='Not specified',
                date=datetime.now()
            )).value
            
            if self.opex_variable_pct:
                opex += revenue * self.opex_variable_pct.value
            
            ebitda = gross_profit - opex
            
            depreciation = self.depreciation.get(year, Assumption(
                name=f'D&A {year}',
                value=0,
                unit='$m',
                source=SourceOfTruth.ASSUMPTION,
                basis='Not specified',
                date=datetime.now()
            )).value
            
            amortization = self.amortization.get(year, Assumption(
                name=f'Amortization {year}',
                value=0,
                unit='$m',
                source=SourceOfTruth.ASSUMPTION,
                basis='Not specified',
                date=datetime.now()
            )).value
            
            ebit = ebitda - depreciation - amortization
            
            interest = self.interest_expense.get(year, Assumption(
                name=f'Interest {year}',
                value=0,
                unit='$m',
                source=SourceOfTruth.ASSUMPTION,
                basis='Not specified',
                date=datetime.now()
            )).value
            
            ebt = ebit - interest
            tax = ebt * self.tax_rate.value
            npat = ebt - tax
            
            pl.loc['Revenue', year] = revenue
            pl.loc['COGS', year] = cogs
            pl.loc['Gross Profit', year] = gross_profit
            pl.loc['Gross Margin %', year] = gross_profit / revenue if revenue > 0 else 0
            pl.loc['OPEX', year] = opex
            pl.loc['EBITDA', year] = ebitda
            pl.loc['Depreciation', year] = depreciation
            pl.loc['Amortization', year] = amortization
            pl.loc['EBIT', year] = ebit
            pl.loc['Interest Expense', year] = interest
            pl.loc['EBT', year] = ebt
            pl.loc['Tax (at statutory rate)', year] = tax
            pl.loc['NPAT', year] = npat
        
        self._forecast = pl
        return pl


@dataclass
class BalanceSheet:
    """
    Balance Sheet Model
    ===================
    Assets, liabilities and equity.
    
    Integrated with P&L via retained earnings bridge.
    """
    
    company: str
    forecast_years: int
    base_year: int
    
    # Asset drivers
    ppe_gross: Dict[int, Assumption] = field(default_factory=dict)
    capex: Dict[int, Assumption] = field(default_factory=dict)
    depreciation_schedule: Dict[int, float] = field(default_factory=dict)
    
    # Working capital
    receivables_days: Assumption = None
    inventory_days: Assumption = None
    payables_days: Assumption = None
    
    # Financing
    debt_schedule: Dict[int, Assumption] = field(default_factory=dict)
    equity_issuance: Dict[int, Assumption] = field(default_factory=dict)
    
    # Link to P&L
    pl_forecast: Optional[pd.DataFrame] = None
    
    _balance_sheet: Optional[pd.DataFrame] = None
    
    def calculate_nwc(self, year: int, revenue: float, cogs: float) -> Tuple[float, float, float]:
        """
        Calculate net working capital components.
        
        Returns:
            (receivables, inventory, payables)
        """
        receivables = revenue * (self.receivables_days.value / 365)
        inventory = cogs * (self.inventory_days.value / 365)
        payables = cogs * (self.payables_days.value / 365)
        
        return receivables, inventory, payables
    
    def forecast(self, pl_forecast: pd.DataFrame) -> pd.DataFrame:
        """Deprecated. Use three_statement.ThreeStatementModel.

        The original stub faked a balance (equity = assets) and never rolled
        retained earnings. The articulated model that genuinely foots lives in
        three_statement.ThreeStatementModel.
        """
        raise NotImplementedError(
            "BalanceSheet.forecast was a non-articulating stub. Use "
            "three_statement.ThreeStatementModel for a balance sheet that foots."
        )


@dataclass
class CashFlowStatement:
    """
    Cash Flow Statement Model
    =========================
    
    Derived from P&L and balance sheet changes.
    Structure: Operating CF + Investing CF + Financing CF = Change in cash
    """
    
    pl_forecast: Optional[pd.DataFrame] = None
    bs_forecast: Optional[pd.DataFrame] = None
    
    capex_forecast: Dict[int, float] = field(default_factory=dict)
    
    _cash_flow: Optional[pd.DataFrame] = None
    
    def forecast(self,
                 pl_forecast: pd.DataFrame,
                 bs_forecast: pd.DataFrame) -> pd.DataFrame:
        """Deprecated. Use three_statement.ThreeStatementModel.

        The original stub omitted financing flows and the cash roll-forward.
        ThreeStatementModel produces a cash-flow statement that reconciles to
        the change in balance-sheet cash.
        """
        raise NotImplementedError(
            "CashFlowStatement.forecast was an incomplete stub. Use "
            "three_statement.ThreeStatementModel for a reconciling cash flow."
        )


# The articulated, footing implementation lives in three_statement.py;
# re-exported here so existing imports keep working.
from .three_statement import validate_three_statement_integrity  # noqa: E402,F401
