"""
Sector-Specific Valuation Models
=================================

Industry-specific frameworks that layer sector dynamics onto the generic 
three-statement and DCF foundations.

Implementations:
- Mining & Resources (NAV/sum-of-parts, mine economics)
- SaaS (ARR, retention, NRR)
- Real Estate / REITs (FFO, NAV, cap rates)
- Banking (NIM, CTI, ROE)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod

from .financial_statements import IncomeStatement, BalanceSheet


# ============================================================================
# MINING & RESOURCES
# ============================================================================

@dataclass
class MineEconomics:
    """
    Single Mine Valuation
    ======================
    
    Production, grade, recovery, processing costs, capex, and mine life.
    """
    
    mine_name: str
    
    # Production profile
    production_schedule: Dict[int, float]  # Year -> ore tonnes produced
    ore_grade: Dict[int, float]  # Year -> % metal in ore
    recovery_rate: float  # % of metal in ore successfully recovered
    
    # Commodity prices
    commodity_price: Dict[int, float]  # Year -> commodity price $/tonne
    
    # Cost structure
    processing_cost_per_tonne: Dict[int, float]  # $/tonne ore
    transport_cost_per_tonne: Dict[int, float]
    smelting_treatment_charge: Dict[int, float]  # $/tonne contained metal
    
    # Capex
    initial_capex: float  # Development capex
    sustaining_capex: Dict[int, float]  # Annual sustaining capex
    
    # Mine life
    mine_life_years: int
    residual_value: float = 0  # Salvage value
    
    # Tax & discount
    tax_rate: float = 0.30
    discount_rate: float = 0.10
    
    def metal_production(self, year: int) -> float:
        """Calculate contained metal production (tonnes)."""
        ore_tonnes = self.production_schedule.get(year, 0)
        grade = self.ore_grade.get(year, 0)
        recovery = self.recovery_rate
        
        return ore_tonnes * (grade / 100) * recovery
    
    def calculate_revenues(self, year: int) -> float:
        """Calculate revenue from metal sales."""
        metal_tonnes = self.metal_production(year)
        commodity_price = self.commodity_price.get(year, 0)
        return metal_tonnes * commodity_price
    
    def calculate_opex(self, year: int) -> float:
        """Calculate site operating costs."""
        ore_tonnes = self.production_schedule.get(year, 0)
        metal_tonnes = self.metal_production(year)
        
        processing = ore_tonnes * self.processing_cost_per_tonne.get(year, 0)
        transport = ore_tonnes * self.transport_cost_per_tonne.get(year, 0)
        smelting = metal_tonnes * self.smelting_treatment_charge.get(year, 0)
        
        return processing + transport + smelting
    
    def mine_life_npv(self) -> Tuple[float, pd.DataFrame]:
        """
        Calculate mine NPV over life of mine.
        
        Returns:
            (npv, forecast_dataframe)
        """
        years = list(range(1, self.mine_life_years + 1))
        forecast = pd.DataFrame(index=[
            'Metal Production (t)',
            'Commodity Price ($/t)',
            'Revenues',
            'Operating Costs',
            'EBITDA',
            'Sustaining Capex',
            'Free Cash Flow',
            'Discount Factor',
            'Present Value',
        ], columns=years)
        
        npv = -self.initial_capex  # Initial development capex
        
        for i, year in enumerate(years):
            metal_prod = self.metal_production(year)
            commodity_price = self.commodity_price.get(year, 0)
            revenue = metal_prod * commodity_price
            opex = self.calculate_opex(year)
            ebitda = revenue - opex
            capex = self.sustaining_capex.get(year, 0)
            fcf = ebitda - capex
            
            discount_factor = 1 / ((1 + self.discount_rate) ** i)
            pv = fcf * discount_factor
            
            npv += pv
            
            forecast.loc['Metal Production (t)', year] = metal_prod
            forecast.loc['Commodity Price ($/t)', year] = commodity_price
            forecast.loc['Revenues', year] = revenue
            forecast.loc['Operating Costs', year] = opex
            forecast.loc['EBITDA', year] = ebitda
            forecast.loc['Sustaining Capex', year] = capex
            forecast.loc['Free Cash Flow', year] = fcf
            forecast.loc['Discount Factor', year] = discount_factor
            forecast.loc['Present Value', year] = pv
        
        # Add terminal/residual value
        npv += self.residual_value / ((1 + self.discount_rate) ** self.mine_life_years)
        
        return npv, forecast


@dataclass
class NAVValuation:
    """
    Net Asset Value (NAV) Valuation
    ===============================
    
    Sum-of-parts approach: value each asset separately, add corporate 
    overhead deduction.
    
    Typical for diversified miners, asset-heavy companies.
    """
    
    company: str
    
    # Assets (project, mine, or segment)
    assets: Dict[str, float]  # Asset name -> Value ($m)
    
    # Liabilities & deductions
    net_debt: float
    shares_outstanding: float  # required -- must precede defaulted fields
    minority_interest: float = 0
    preferred_equity: float = 0
    
    # Corporate deduction (head office costs not allocated to assets)
    corporate_deduction: float = 0
    
    # Discount to NAV (if any)
    nav_discount: float = 0  # e.g., 0.20 = 20% discount
    
    def nav(self) -> float:
        """Calculate gross NAV (sum of all assets)."""
        return sum(self.assets.values())
    
    def adjusted_nav(self) -> float:
        """Calculate adjusted NAV (NAV less net debt, minority, corporate deductions)."""
        gross_nav = self.nav()
        return (gross_nav 
                - self.net_debt 
                - self.minority_interest
                - self.corporate_deduction)
    
    def nav_per_share(self, discount_applied: bool = False) -> float:
        """
        Calculate NAV per share.
        
        Args:
            discount_applied: If True, apply nav_discount to gross NAV
        """
        gross_nav = self.nav()
        
        if discount_applied:
            gross_nav = gross_nav * (1 - self.nav_discount)
        
        adjusted = (gross_nav 
                   - self.net_debt 
                   - self.minority_interest
                   - self.corporate_deduction)
        
        return adjusted / self.shares_outstanding
    
    def sensitivity_to_nav_discount(self) -> pd.Series:
        """Sensitivity analysis: NAV per share vs discount %."""
        discounts = np.arange(0, 0.5, 0.05)
        sensitivities = {}
        
        for d in discounts:
            self.nav_discount = d
            sensitivities[f'{d:.0%}'] = self.nav_per_share(discount_applied=True)
        
        return pd.Series(sensitivities)


# ============================================================================
# SaaS / TECHNOLOGY
# ============================================================================

@dataclass
class SaaSMetrics:
    """
    SaaS Key Metrics
    ================
    
    ARR, MRR, net revenue retention, CAC, churn, LTV.
    """
    
    company: str
    
    # Revenue metrics
    arr: Dict[int, float]  # Annual recurring revenue by year
    mrr: Dict[int, float]  # Monthly recurring revenue (optional)
    
    # Growth & retention
    net_revenue_retention: Dict[int, float]  # Year-over-year NRR (can exceed 100%)
    logo_churn: Dict[int, float]  # % of customers lost
    dollar_churn: Dict[int, float]  # % of revenue lost
    
    # Unit economics
    cac: Dict[int, float]  # Customer acquisition cost ($)
    cac_payback: Dict[int, float]  # Months to payback
    ltv: Dict[int, float]  # Lifetime value ($)
    
    # Forecast horizon
    forecast_years: int = 10
    
    def arr_forecast(self, base_arr: float) -> Dict[int, float]:
        """
        Build ARR forecast from NRR.
        
        Example:
        Year 1 ARR: $100m
        Year 2 NRR: 120% → Year 2 ARR = $100m × 1.20 = $120m
        """
        forecast = {0: base_arr}
        
        for year in range(1, self.forecast_years):
            prev_arr = forecast[year - 1]
            nrr = self.net_revenue_retention.get(year, 1.0)
            forecast[year] = prev_arr * nrr
        
        return forecast
    
    def magic_number(self, year: int) -> float:
        """
        Magic Number = Incremental ARR / Sales & Marketing Spend
        
        Rule of thumb: >0.75 is good, >1.0 is excellent.
        """
        raise NotImplementedError("Requires sales & marketing spend data")
    
    def rule_of_40(self, growth_rate: float, operating_margin: float) -> float:
        """
        Rule of 40: Growth Rate + Operating Margin should exceed 40%.
        
        Heuristic for SaaS company health.
        """
        return growth_rate + operating_margin


@dataclass
class SaaSIncomeStatement(IncomeStatement):
    """
    SaaS P&L Model
    ===============
    
    Specialized income statement for SaaS:
    - Subscription revenue (recurring)
    - Professional services / other revenue (one-time)
    - Low COGS (mostly S&M, R&D, G&A)
    """
    
    # SaaS-specific
    arr: Dict[int, float] = field(default_factory=dict)  # Annual recurring revenue driver
    ps_revenue_pct: float = 0  # Prof services as % of ARR
    
    def calculate_revenue(self, year: int) -> float:
        """Revenue = ARR + professional services."""
        if year not in self.arr:
            return 0
        
        subscription_revenue = self.arr[year]
        ps_revenue = subscription_revenue * self.ps_revenue_pct
        
        return subscription_revenue + ps_revenue


# ============================================================================
# REAL ESTATE / REITs
# ============================================================================

@dataclass
class REITProperty:
    """
    Individual Property Valuation
    ==============================
    
    Cap rate / yield approach for real estate assets.
    """
    
    property_name: str
    
    # Income generating
    noi: float  # Net operating income (annual)
    noi_growth: float  # Expected annual growth %
    
    # Valuation
    cap_rate: float  # Discount rate / cap rate
    
    # Assumptions
    forecast_years: int = 10
    terminal_growth: float = 0.025  # Long-term growth
    
    def property_valuation(self) -> float:
        """
        DCF valuation of property using NOI.
        
        Simplified: PV of annuity + terminal value.
        """
        pv = 0
        current_noi = self.noi
        
        # Explicit period
        for year in range(1, self.forecast_years + 1):
            year_noi = current_noi * ((1 + self.noi_growth) ** (year - 1))
            discount_factor = 1 / ((1 + self.cap_rate) ** year)
            pv += year_noi * discount_factor
            
            if year == self.forecast_years:
                final_year_noi = year_noi
        
        # Terminal value
        terminal_noi = final_year_noi * (1 + self.terminal_growth)
        terminal_value = terminal_noi / (self.cap_rate - self.terminal_growth)
        terminal_discount_factor = 1 / ((1 + self.cap_rate) ** self.forecast_years)
        pv += terminal_value * terminal_discount_factor
        
        return pv
    
    def implied_cap_rate(self, valuation: float) -> float:
        """Back-solve implied cap rate from valuation."""
        return self.noi / valuation


@dataclass
class REITValuation:
    """
    REIT Valuation
    ===============
    
    Funds from operations (FFO), net tangible assets (NTA), cap rates.
    """
    
    company: str
    
    # Properties
    properties: List[REITProperty]
    
    # Capital structure
    total_debt: float
    cash: float
    shares_outstanding: float  # required -- must precede defaulted fields
    minority_interest: float = 0
    
    def gross_property_value(self) -> float:
        """Sum valuation of all properties."""
        return sum(p.property_valuation() for p in self.properties)
    
    def net_tangible_assets(self) -> float:
        """NTA = Property valuations - net debt."""
        return self.gross_property_value() - (self.total_debt - self.cash)
    
    def nta_per_share(self) -> float:
        """NTA per share."""
        return self.net_tangible_assets() / self.shares_outstanding
    
    def discount_to_nta(self, current_share_price: float) -> float:
        """Calculate discount/premium to NTA."""
        nta_ps = self.nta_per_share()
        return (current_share_price - nta_ps) / nta_ps


# ============================================================================
# BANKING
# ============================================================================

@dataclass
class BankingValuation:
    """
    Bank Valuation Framework
    =========================
    
    Net interest margin (NIM), cost-to-income (CTI), return on equity (ROE).
    """
    
    company: str
    
    # Balance sheet
    total_assets: float
    net_loans: float
    deposits: float
    shareholders_equity: float
    
    # Income statement
    net_interest_income: float
    total_revenue: float
    total_costs: float
    npat: float
    
    # Metrics
    nim: float  # Net interest margin (%)
    cost_to_income: float  # Costs / Revenue (%)
    roe: float  # NPAT / Equity (%)
    
    # Valuation multiples
    target_roe: float = 0.12  # 12% target ROE
    
    def calculate_nim(self) -> float:
        """NIM = Net interest income / Average earning assets."""
        return self.net_interest_income / self.net_loans if self.net_loans > 0 else 0
    
    def calculate_cti(self) -> float:
        """Cost-to-income = Total costs / Total revenue."""
        return self.total_costs / self.total_revenue if self.total_revenue > 0 else 0
    
    def calculate_roe(self) -> float:
        """ROE = NPAT / Average shareholders equity."""
        return self.npat / self.shareholders_equity if self.shareholders_equity > 0 else 0
    
    def implied_npat_at_target_roe(self) -> float:
        """NPAT implied by target ROE."""
        return self.shareholders_equity * self.target_roe
    
    def payout_ratio_from_roe(self, target_payout: float = 0.5) -> float:
        """Implied dividend payout ratio if ROE improves to target."""
        improved_npat = self.implied_npat_at_target_roe()
        return target_payout * improved_npat
