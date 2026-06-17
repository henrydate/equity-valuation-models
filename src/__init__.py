"""
Equity Valuation Models Package
================================

Institutional-quality equity research framework: DCF, comparables, 
sector-specific models (mining/NAV, SaaS/ARR, REITs/cap rates, banking/ROE).
"""

from .financial_statements import (
    Assumption,
    SourceOfTruth,
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
    validate_three_statement_integrity,
)

from .valuation import (
    WACCComponents,
    DCFValuation,
    ComparableCompaniesValuation,
    PrecedentTransactionsValuation,
    TerminalValueMethod,
)

from .sector_models import (
    MineEconomics,
    NAVValuation,
    SaaSMetrics,
    SaaSIncomeStatement,
    REITProperty,
    REITValuation,
    BankingValuation,
)

from .ledger import Ledger, LedgerEntry, InputKind, VerificationStatus
from .guardrails import run_checks, CheckStatus, GuardrailResult
from .wizard import build_entry, compute_wacc, run_bank
from .data_scaffold import scaffold_entries, fetch_info
from .question_banks import get_bank, WACC_BANK
from .three_statement import ThreeStatementModel
from .sotp import AssetValuation, Division, SumOfParts
from .note import render_note, write_note
from .excel_model import build_workbook, write_workbook
from .template_loader import load_template, build_from_template, collect_missing, run_template

__all__ = [
    # Financial statements
    'Assumption',
    'SourceOfTruth',
    'IncomeStatement',
    'BalanceSheet',
    'CashFlowStatement',
    'validate_three_statement_integrity',
    
    # Valuation
    'WACCComponents',
    'DCFValuation',
    'ComparableCompaniesValuation',
    'PrecedentTransactionsValuation',
    'TerminalValueMethod',
    
    # Sector models
    'MineEconomics',
    'NAVValuation',
    'SaaSMetrics',
    'SaaSIncomeStatement',
    'REITProperty',
    'REITValuation',
    'BankingValuation',

    # Ledger & elicitation engine
    'Ledger', 'LedgerEntry', 'InputKind', 'VerificationStatus',
    'run_checks', 'CheckStatus', 'GuardrailResult',
    'build_entry', 'compute_wacc', 'run_bank',
    'scaffold_entries', 'fetch_info',
    'get_bank', 'WACC_BANK',
    'ThreeStatementModel',
    'AssetValuation', 'Division', 'SumOfParts',
    'render_note', 'write_note',
    'build_workbook', 'write_workbook',
    'load_template', 'build_from_template', 'collect_missing', 'run_template',
]
