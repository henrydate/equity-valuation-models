"""
Valuation Module: DCF, WACC, Terminal Value
============================================

Discounted cash flow valuation with full WACC build.

Core components:
- WACC calculation (cost of equity via CAPM, WACC blended)
- Free cash flow to firm (FCFF) vs free cash flow to equity (FCFE)
- Terminal value methods (perpetuity growth, exit multiple)
- Sensitivity analysis and scenario modelling
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np
from enum import Enum


class TerminalValueMethod(Enum):
    """Terminal value calculation approach."""
    PERPETUITY_GROWTH = "perpetuity"
    EXIT_MULTIPLE = "exit_multiple"


@dataclass
class WACCComponents:
    """
    WACC Build-Up
    ==============
    All components explicitly calculated from first principles.
    """
    
    # Cost of Equity (CAPM)
    risk_free_rate: float  # e.g., 10Y AUS govt yield
    market_risk_premium: float  # e.g., historical equity risk premium
    equity_beta: float  # Company-specific systematic risk
    
    # Cost of Debt
    cost_of_debt_pre_tax: float
    tax_rate: float
    
    # Capital Structure
    market_value_equity: float
    market_value_debt: float
    
    def cost_of_equity(self) -> float:
        """Calculate cost of equity via CAPM."""
        return self.risk_free_rate + self.equity_beta * self.market_risk_premium
    
    def cost_of_debt_post_tax(self) -> float:
        """After-tax cost of debt."""
        return self.cost_of_debt_pre_tax * (1 - self.tax_rate)
    
    def wacc(self) -> float:
        """Calculate WACC."""
        total_value = self.market_value_equity + self.market_value_debt
        
        if total_value == 0:
            raise ValueError("Total firm value (equity + debt) must be > 0")
        
        weight_equity = self.market_value_equity / total_value
        weight_debt = self.market_value_debt / total_value
        
        return (weight_equity * self.cost_of_equity() + 
                weight_debt * self.cost_of_debt_post_tax())
    
    def __repr__(self):
        return (
            f"WACC Build-Up:\n"
            f"  Cost of Equity (CAPM): {self.risk_free_rate:.2%} + "
            f"{self.equity_beta:.2f} × {self.market_risk_premium:.2%} = "
            f"{self.cost_of_equity():.2%}\n"
            f"  Cost of Debt (post-tax): {self.cost_of_debt_post_tax():.2%}\n"
            f"  Capital Structure: "
            f"E={self.market_value_equity:,.0f} / D={self.market_value_debt:,.0f}\n"
            f"  WACC: {self.wacc():.2%}"
        )


@dataclass
class DCFValuation:
    """
    DCF Valuation Model
    ===================
    
    Discounts free cash flows to present value.
    """
    
    company: str
    
    # Cash flow forecast (years, fcff)
    fcff_forecast: Dict[int, float]  # Year -> FCFF
    
    # Valuation parameters
    wacc: float
    terminal_growth_rate: float
    terminal_value_method: TerminalValueMethod = TerminalValueMethod.PERPETUITY_GROWTH
    terminal_exit_multiple: Optional[float] = None  # For exit multiple method
    
    # Adjustments
    net_debt: float = 0  # Net debt to deduct from enterprise value
    minority_interest: float = 0
    preferred_equity: float = 0
    
    # Shares outstanding
    shares_outstanding: float = 0
    
    # Results
    _pv_fcff: Optional[pd.DataFrame] = None
    _enterprise_value: Optional[float] = None
    _equity_value: Optional[float] = None
    _value_per_share: Optional[float] = None
    
    def _discount_factor(self, year: int, base_year: int) -> float:
        """Calculate discount factor for a given year."""
        years_from_now = year - base_year
        return 1 / ((1 + self.wacc) ** years_from_now)
    
    def calculate_terminal_value(self, final_year: int, final_fcff: float) -> float:
        """
        Calculate terminal value at end of explicit forecast period.
        
        Methods:
        1. Perpetuity growth: TV = FCFF(final) × (1 + g) / (WACC - g)
        2. Exit multiple: TV = FCFF(final) × multiple
        """
        if self.terminal_value_method == TerminalValueMethod.PERPETUITY_GROWTH:
            if self.wacc <= self.terminal_growth_rate:
                raise ValueError(
                    f"WACC ({self.wacc:.2%}) must exceed terminal growth rate "
                    f"({self.terminal_growth_rate:.2%})"
                )
            return final_fcff * (1 + self.terminal_growth_rate) / (
                self.wacc - self.terminal_growth_rate
            )
        elif self.terminal_value_method == TerminalValueMethod.EXIT_MULTIPLE:
            if self.terminal_exit_multiple is None:
                raise ValueError(
                    "terminal_exit_multiple must be set for EXIT_MULTIPLE method"
                )
            return final_fcff * self.terminal_exit_multiple
        else:
            raise ValueError(f"Unknown terminal value method: {self.terminal_value_method}")
    
    def value(self, base_year: int) -> Dict[str, float]:
        """
        Perform DCF valuation.
        
        Returns:
            Dictionary with enterprise_value, equity_value, value_per_share
        """
        
        # Sort forecast years
        years = sorted(self.fcff_forecast.keys())
        if not years:
            raise ValueError("No FCFF forecast provided")
        
        # Calculate PV of explicit forecast period
        pv_explicit = {}
        for year in years:
            fcff = self.fcff_forecast[year]
            discount_factor = self._discount_factor(year, base_year)
            pv = fcff * discount_factor
            pv_explicit[year] = pv
        
        total_pv_explicit = sum(pv_explicit.values())
        
        # Calculate terminal value at end of forecast
        final_year = years[-1]
        final_fcff = self.fcff_forecast[final_year]
        terminal_value = self.calculate_terminal_value(final_year, final_fcff)
        terminal_discount_factor = self._discount_factor(final_year, base_year)
        pv_terminal = terminal_value * terminal_discount_factor
        
        # Enterprise value
        enterprise_value = total_pv_explicit + pv_terminal
        
        # Equity value
        equity_value = (enterprise_value 
                       - self.net_debt 
                       - self.minority_interest 
                       - self.preferred_equity)
        
        # Per share
        if self.shares_outstanding <= 0:
            raise ValueError("shares_outstanding must be > 0")
        
        value_per_share = equity_value / self.shares_outstanding
        
        self._enterprise_value = enterprise_value
        self._equity_value = equity_value
        self._value_per_share = value_per_share
        
        # Store breakdown for sensitivity analysis
        self._pv_fcff = pd.DataFrame({
            'Year': years,
            'FCFF': [self.fcff_forecast[y] for y in years],
            'Discount Factor': [self._discount_factor(y, base_year) for y in years],
            'PV of FCFF': [pv_explicit[y] for y in years]
        })
        
        return {
            'enterprise_value': enterprise_value,
            'equity_value': equity_value,
            'value_per_share': value_per_share,
            'pv_explicit': total_pv_explicit,
            'pv_terminal': pv_terminal,
            'terminal_value': terminal_value,
        }
    
    def sensitivity_analysis(self, 
                           base_year: int,
                           wacc_range: Tuple[float, float] = None,
                           tg_range: Tuple[float, float] = None,
                           step: float = 0.0025) -> pd.DataFrame:
        """
        Two-way sensitivity analysis: WACC vs Terminal Growth Rate.
        
        Args:
            base_year: Base year for discounting
            wacc_range: (min_wacc, max_wacc) - defaults to ±2% around base
            tg_range: (min_tg, max_tg) - defaults to ±1% around base
            step: Increment size (default 0.25%)
        
        Returns:
            DataFrame with value per share sensitivity table
        """
        if wacc_range is None:
            wacc_range = (self.wacc - 0.02, self.wacc + 0.02)
        if tg_range is None:
            tg_range = (self.terminal_growth_rate - 0.01, 
                       self.terminal_growth_rate + 0.01)
        
        wacc_range = np.arange(wacc_range[0], wacc_range[1] + step, step)
        tg_range = np.arange(tg_range[0], tg_range[1] + step, step)
        
        sensitivity = pd.DataFrame(
            index=wacc_range.round(4),
            columns=tg_range.round(4)
        )
        
        for wacc in wacc_range:
            for tg in tg_range:
                if wacc <= tg:
                    sensitivity.loc[round(wacc, 4), round(tg, 4)] = np.nan
                    continue
                
                # Recalculate with modified parameters
                old_wacc = self.wacc
                old_tg = self.terminal_growth_rate
                
                self.wacc = wacc
                self.terminal_growth_rate = tg
                
                result = self.value(base_year)
                sensitivity.loc[round(wacc, 4), round(tg, 4)] = result['value_per_share']
                
                self.wacc = old_wacc
                self.terminal_growth_rate = old_tg
        
        return sensitivity.astype(float)
    
    def summary(self, base_year: int) -> str:
        """Return formatted valuation summary."""
        if self._value_per_share is None:
            self.value(base_year)
        
        return (
            f"DCF Valuation Summary: {self.company}\n"
            f"{'='*50}\n"
            f"Enterprise Value: A${self._enterprise_value:,.0f}m\n"
            f"Less: Net Debt: A${self.net_debt:,.0f}m\n"
            f"Equity Value: A${self._equity_value:,.0f}m\n"
            f"Shares Outstanding: {self.shares_outstanding:.1f}m\n"
            f"{'='*50}\n"
            f"Value Per Share: A${self._value_per_share:.2f}\n"
            f"\nValuation Parameters:\n"
            f"  WACC: {self.wacc:.2%}\n"
            f"  Terminal Growth Rate: {self.terminal_growth_rate:.2%}\n"
            f"  Terminal Value Method: {self.terminal_value_method.value}\n"
        )


@dataclass
class ComparableCompaniesValuation:
    """
    Trading Comparables Analysis
    =============================
    
    Peer group trading multiples to triangulate valuation.
    """
    
    company: str
    company_metrics: Dict[str, float]  # e.g., {'revenue': 1000, 'ebitda': 200}
    
    peers: Dict[str, Dict[str, float]]  # peer -> {metric -> value}
    multiples: Dict[str, float]  # metric -> multiple (e.g., 'EV/Revenue': 5.0)
    
    def implied_values(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate implied enterprise / equity values from multiples.
        
        Returns:
            Dictionary mapping multiple type to implied value
        """
        results = {}
        
        for multiple_name, multiple in self.multiples.items():
            metric_name = multiple_name.split('/')[-1]  # Extract metric from 'EV/Revenue'
            
            if metric_name not in self.company_metrics:
                continue
            
            metric_value = self.company_metrics[metric_name]
            implied_value = metric_value * multiple
            
            results[multiple_name] = {
                'metric': metric_name,
                'metric_value': metric_value,
                'multiple': multiple,
                'implied_value': implied_value
            }
        
        return results
    
    def peer_summary(self) -> pd.DataFrame:
        """Build summary table of peer metrics and multiples."""
        data = {}
        
        for peer_name, metrics in self.peers.items():
            for metric, value in metrics.items():
                if metric not in data:
                    data[metric] = {}
                data[metric][peer_name] = value
        
        return pd.DataFrame(data).T


@dataclass
class PrecedentTransactionsValuation:
    """
    Precedent Transactions Analysis
    ================================
    
    M&A transaction multiples for comparable acquisition pricing.
    """
    
    company: str
    company_metrics: Dict[str, float]
    
    transactions: Dict[str, Dict[str, float]]  # transaction -> {metric -> value, multiple -> value}
    
    def implied_values(self) -> Dict[str, float]:
        """Calculate implied values based on precedent transaction multiples."""
        results = {}
        
        # Extract median multiples from transactions
        multiples_by_type = {}
        for txn, data in self.transactions.items():
            for key, value in data.items():
                if key.startswith('EV/') or key.startswith('Price/'):
                    if key not in multiples_by_type:
                        multiples_by_type[key] = []
                    multiples_by_type[key].append(value)
        
        # Calculate medians and implied values
        for multiple_type, values in multiples_by_type.items():
            if values:
                median_multiple = np.median(values)
                metric_name = multiple_type.split('/')[-1]
                
                if metric_name in self.company_metrics:
                    implied_value = self.company_metrics[metric_name] * median_multiple
                    results[multiple_type] = implied_value
        
        return results
