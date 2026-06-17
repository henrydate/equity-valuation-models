"""
Synthetic Example: Mining NAV Mechanics (FICTIONAL company)
===========================================================

A runnable demonstration of the NAV (net asset value) / sum-of-parts mechanics
on an INVENTED company. The numbers are made up to exercise the code paths --
this is NOT a real valuation. The real worked example (BHP) is the Stage 2
deliverable; see the README roadmap.

Company: "MultiMine Ltd" (fictional)
Assets: Three mines at various stages
Valuation: NAV per share with discount to NTA

This example demonstrates:
1. Mine-by-mine economics (MineEconomics)
2. Sum-of-parts (NAVValuation)
3. Sensitivity to commodity prices and cap rates
"""

import os
import sys

import pandas as pd

# Allow running directly (`python examples/mining_nav_example.py`) from any cwd.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sector_models import MineEconomics, NAVValuation


def example_multimine_nav():
    """
    Build and value a diversified mining company.
    """
    
    print("=" * 80)
    print("MultiMine Ltd: NAV Valuation Example")
    print("=" * 80)
    
    # ========================================================================
    # ASSET 1: Golden Goose Mine (Producing)
    # ========================================================================
    
    print("\n1. GOLDEN GOOSE MINE (Producing)")
    print("-" * 80)
    
    golden_goose = MineEconomics(
        mine_name="Golden Goose",
        production_schedule={
            1: 1000,  # Year 1: 1,000 tonnes ore
            2: 1200,  # Year 2: 1,200 tonnes
            3: 1100,  # Year 3: 1,100 tonnes
            4: 1000,  # Year 4: declining as ore body depletes
            5: 900,
            6: 800,
            7: 700,
            8: 600,
            9: 500,
            10: 400,
        },
        ore_grade={
            1: 5.0,   # % metal in ore
            2: 5.2,
            3: 5.0,
            4: 4.8,
            5: 4.6,
            6: 4.4,
            7: 4.2,
            8: 4.0,
            9: 3.8,
            10: 3.5,
        },
        recovery_rate=0.85,  # 85% of metal recoverable
        commodity_price={
            1: 1500,  # $/tonne metal content
            2: 1400,
            3: 1300,
            4: 1250,
            5: 1200,
            6: 1200,
            7: 1200,
            8: 1200,
            9: 1200,
            10: 1200,
        },
        processing_cost_per_tonne={
            i: 50 for i in range(1, 11)  # $50/tonne ore
        },
        transport_cost_per_tonne={
            i: 10 for i in range(1, 11)  # $10/tonne ore
        },
        smelting_treatment_charge={
            i: 100 for i in range(1, 11)  # $100/tonne metal
        },
        initial_capex=500,  # $500m development capex already spent
        sustaining_capex={
            i: 20 for i in range(1, 11)  # $20m annual sustaining capex
        },
        mine_life_years=10,
        discount_rate=0.10,  # 10% WACC
    )
    
    gg_npv, gg_forecast = golden_goose.mine_life_npv()
    print(f"Golden Goose NPV (10% discount): A${gg_npv:.0f}m\n")
    print("Year 1-3 Economics:")
    print(gg_forecast.loc[['Metal Production (t)', 'Revenues', 'Operating Costs', 'EBITDA', 'Free Cash Flow']].iloc[:, :3])
    
    # ========================================================================
    # ASSET 2: Silver Stream (Development)
    # ========================================================================
    
    print("\n2. SILVER STREAM (Development Stage)")
    print("-" * 80)
    
    silver_stream = MineEconomics(
        mine_name="Silver Stream",
        production_schedule={
            1: 0,  # Year 1: still in development
            2: 0,
            3: 500,  # Year 3: first production
            4: 800,
            5: 1000,
            6: 1000,
            7: 1000,
            8: 900,
            9: 800,
            10: 700,
        },
        ore_grade={i: 3.0 for i in range(1, 11)},  # 3% grade
        recovery_rate=0.80,
        commodity_price={i: 800 for i in range(1, 11)},  # $/tonne
        processing_cost_per_tonne={i: 40 for i in range(1, 11)},
        transport_cost_per_tonne={i: 8 for i in range(1, 11)},
        smelting_treatment_charge={i: 80 for i in range(1, 11)},
        initial_capex=800,  # $800m dev capex
        sustaining_capex={i: 15 for i in range(1, 11)},
        mine_life_years=10,
        discount_rate=0.10,
    )
    
    ss_npv, ss_forecast = silver_stream.mine_life_npv()
    print(f"Silver Stream NPV (10% discount): A${ss_npv:.0f}m")
    print(f"(Note: negative NPV in development stage is common if capex heavy)")
    
    # ========================================================================
    # ASSET 3: Copper Prospect (Pre-Development, Probabilistic)
    # ========================================================================
    
    print("\n3. COPPER PROSPECT (Pre-Dev, Risk-Adjusted)")
    print("-" * 80)
    
    # Pre-dev asset: uncertain valuation
    # Typical approach: PFS feasibility study + probability of success
    gross_copper_value = 300  # $300m if developed
    probability_of_success = 0.60  # 60% chance of development
    risk_adjusted_copper = gross_copper_value * probability_of_success
    
    print(f"Gross Copper PFS value: A${gross_copper_value:.0f}m")
    print(f"Probability of development: {probability_of_success:.0%}")
    print(f"Risk-adjusted value: A${risk_adjusted_copper:.0f}m")
    
    # ========================================================================
    # SUM OF PARTS (NAV)
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("NET ASSET VALUE (NAV) CALCULATION")
    print("=" * 80)
    
    nav = NAVValuation(
        company="MultiMine Ltd",
        assets={
            "Golden Goose Mine": gg_npv,
            "Silver Stream": ss_npv,
            "Copper Prospect": risk_adjusted_copper,
        },
        net_debt=500,  # $500m net debt
        corporate_deduction=30,  # $30m annual head office costs (capitalized as $30m deduction)
        shares_outstanding=250,  # 250m shares outstanding
    )
    
    print(f"\nAsset Values:")
    for asset, value in nav.assets.items():
        print(f"  {asset:.<40} A${value:>8,.0f}m")
    print(f"  {'Gross NAV':.<40} A${nav.nav():>8,.0f}m")
    print(f"\nDeductions:")
    print(f"  {'Net Debt':.<40} A${nav.net_debt:>8,.0f}m")
    print(f"  {'Corporate Deduction':.<40} A${nav.corporate_deduction:>8,.0f}m")
    print(f"  {'Adjusted NAV':.<40} A${nav.adjusted_nav():>8,.0f}m")
    print(f"\nPer Share:")
    print(f"  {'Shares Outstanding':.<40} {nav.shares_outstanding:>8,.0f}m")
    print(f"  {'NAV per Share':.<40} A${nav.nav_per_share():>8.2f}")
    
    # ========================================================================
    # DISCOUNT TO NAV SENSITIVITY
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("NAV PER SHARE: Sensitivity to Discount")
    print("=" * 80)
    
    discounts = [0, 0.10, 0.20, 0.30, 0.40]
    print("\nDiscount %     NAV/Share")
    print("-" * 30)
    for d in discounts:
        nav.nav_discount = d
        value_ps = nav.nav_per_share(discount_applied=True)
        print(f"{d:>6.0%}         A${value_ps:>6.2f}")
    
    # Reset
    nav.nav_discount = 0
    
    # ========================================================================
    # COMMODITY PRICE SENSITIVITY
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("VALUATION SENSITIVITY: Commodity Prices")
    print("=" * 80)
    
    base_price_gg = 1500
    price_multipliers = [0.8, 0.9, 1.0, 1.1, 1.2]
    
    print("\nGolden Goose NPV sensitivity to commodity prices:")
    print("Price Multiple     NPV      NAV/Share")
    print("-" * 40)
    
    for mult in price_multipliers:
        # Re-run mine with adjusted prices
        test_mine = MineEconomics(
            mine_name="Golden Goose",
            production_schedule=golden_goose.production_schedule,
            ore_grade=golden_goose.ore_grade,
            recovery_rate=golden_goose.recovery_rate,
            commodity_price={i: base_price_gg * mult for i in range(1, 11)},
            processing_cost_per_tonne=golden_goose.processing_cost_per_tonne,
            transport_cost_per_tonne=golden_goose.transport_cost_per_tonne,
            smelting_treatment_charge=golden_goose.smelting_treatment_charge,
            initial_capex=golden_goose.initial_capex,
            sustaining_capex=golden_goose.sustaining_capex,
            mine_life_years=10,
            discount_rate=0.10,
        )
        
        test_npv, _ = test_mine.mine_life_npv()
        
        # Recalculate NAV with new mine value
        nav_test = NAVValuation(
            company="MultiMine Ltd",
            assets={
                "Golden Goose Mine": test_npv,
                "Silver Stream": ss_npv,
                "Copper Prospect": risk_adjusted_copper,
            },
            net_debt=500,
            corporate_deduction=30,
            shares_outstanding=250,
        )
        
        nav_ps = nav_test.nav_per_share()
        print(f"{mult:>6.0%}x           A${test_npv:>6,.0f}m   A${nav_ps:>6.2f}")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("VALUATION SUMMARY")
    print("=" * 80)
    print(f"\nBase Case NAV per Share: A${nav.nav_per_share():.2f}")
    print(f"  (Assumes base commodity prices, no discount to NAV)")
    print(f"\nValuation Range (with discount):")
    print(f"  Bull case (no discount):     A${nav.nav_per_share():.2f}")
    print(f"  Base case (20% discount):    A${nav.nav_per_share(discount_applied=True):.2f}")
    print(f"  Bear case (30% discount):    A${nav.nav_per_share()*(1-0.30):.2f}")
    
    return nav, golden_goose, silver_stream


if __name__ == "__main__":
    nav, gg, ss = example_multimine_nav()
