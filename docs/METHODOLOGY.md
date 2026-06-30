# Methodology: Equity Valuation Framework

## Philosophy

This framework is built on a single principle: **valuation is not a target to be achieved, but a mathematical outcome of assumptions**.

If you start with a desired price and work backwards to find assumptions that support it, you've built a sales pitch, not an analysis.

Instead:

1. **Define assumptions from first principles** (sourced, defensible)
2. **Build a financial model** (three statements with integrity checks)
3. **Calculate valuation** (DCF, comps, precedent transactions)
4. **Compare across methods** (if they disagree, assumptions are wrong)
5. **Accept whatever answer the math gives you** (even if you don't like it)

---

## Core Principles

### 1. Provenance Over Convenience

Every assumption must be traceable to a source:

```
Management Guidance (e.g., "FY26 Revenue target: $1bn, FY25 result")
  ↓
Company Filing (e.g., FY25 annual report, page 45)
  ↓
Broker Consensus (e.g., Bloomberg consensus of 12 brokers)
  ↓
Analyst Estimate (e.g., Ord Minnett's cost of equity estimate)
  ↓
External Data (e.g., RBA cash rate, ABS migration data)
  ↓
Assumption (e.g., "Assume 3% terminal growth")
```

If you can't source an assumption, it belongs in the sensitivity table, not the base case.

### 2. Sector Methodology Must Match the Asset

A generic DCF template applied indiscriminately fails:

| Sector | Drivers | Valuation Method |
|--------|---------|------------------|
| **Mining** | Commodity prices, mine grade/recovery, capex phasing | NAV / sum-of-parts (value each mine, deduct corporate debt) |
| **SaaS** | ARR growth, net revenue retention, unit economics | ARR-based DCF + EV/ARR cross-check |
| **REITs** | NOI (net operating income), occupancy, lease growth | Cap rate / FFO / NTA bridge |
| **Banking** | NIM (net interest margin), CTI (cost-to-income), ROE | ROE frameworks + deposit/loan growth models |

Using mining revenue assumptions for a SaaS company, or SaaS retention logic for a bank, creates undetectable errors.

### 3. Three-Statement Integrity Is Non-Negotiable

A financially consistent model requires:

- **P&L → Equity**: NPAT flows to retained earnings in the balance sheet
- **Balance Sheet Balance**: Assets = Liabilities + Equity (exactly)
- **Cash Flow Reconciliation**: Operating CF + Investing CF + Financing CF = Change in cash
- **Working Capital**: Receivables, inventory, payables are modeled explicitly and consistent across statements

If your three statements don't reconcile, your valuation is built on sand.

### 4. Valuation Must Bridge

The target price is **the mathematical outcome** of your model, not an input:

```
DCF Valuation:
  PV of FCFF (Years 1-10):        $500m
  + PV of Terminal Value:          $800m
  = Enterprise Value:              $1,300m
  - Net Debt:                      ($200m)
  = Equity Value:                  $1,100m
  ÷ Shares Outstanding:            100m
  = Value per Share:               $11.00
```

If you calculated a $11.00 valuation but "really think it's worth $15," the error is in your assumptions, not the math. Fix the model; don't fix the output.

### 5. Cross-Check Everything

Run three valuations in parallel:

1. **DCF**: Discount free cash flows (base case)
2. **Trading Comparables**: EV/EBITDA, P/E, EV/Revenue multiples of peers
3. **Precedent Transactions**: M&A multiples from similar deals

If DCF says $11 but comps say $8 and M&A precedents say $10, something in your assumptions is wrong. Find it. Don't publish a valuation range of $8-$11 and call it analysis.

---

## Validation & Data Quality

### How the copper EBITDA error was caught

Building the BHP real valuation from the FY25 annual report exposed a common
analyst failure mode: **segment line vs. total line confusion**.

**The initial misread:**
The AR25 p.21 segment table lists copper contributors as sub-rows under a
"Copper" heading. The first sub-row is Escondida (BHP's largest copper asset) at
US$8,593m. This was pulled as the segment total.

**The actual number (AR25 p.21 — Total Copper from Group production):**

| Sub-segment | EBITDA US$m |
|---|---|
| Escondida | 8,593 |
| Pampa Norte | 1,270 |
| Copper South Australia | 1,936 |
| Antamina | 1,002 |
| Other | (100) |
| **Total Copper from Group production** | **12,701** |

**Quantified impact of the misread:**

Using 8,593 instead of 12,701 understates copper EBITDA by 48%. At the 8.0×
peer EV/EBITDA multiple, the error flows directly into valuation:

- SOTP: copper EV understated by US$32,864m → SOTP per share falls by ~A$9/share
  (correct A$49 vs misstated ~A$40)
- DCF: group EBITDA understated → normalized FCF falls → DCF per share falls by
  ~A$14/share (correct A$58 vs misstated ~A$44)
- Blended: correct A$54 vs misstated ~A$42 — a ~A$12/share swing

This is a material error on a reportable valuation.

**How the citation requirement caught it:**

Every hard fact in the ledger requires a page citation before it can be recorded
as VERIFIED. The entry for copper EBITDA requires:

```
Fact     | Copper underlying EBITDA
Value    | 8,593   ← initial entry
Source   | AR25
Page     | 21
Note     | Segment performance table
```

Returning to AR25 p.21 to fill in the *exact reference* field made the error
visible: the filled-in line was the Escondida sub-row, not the "Total Copper from
Group production" row three lines below. The value was updated to 12,701 and the
exact reference updated to `"Total Copper from Group production row — NOT the
Escondida sub-line (8593)"` — which now serves as a permanent warning in the
citation ledger.

**The lesson:**

Citations are not documentation overhead. The act of writing down a page number
and exact reference forces re-verification. Silent errors — **right document, wrong
line** — are exactly what a citation requirement catches, because you have to name
the line, not just the page. The data quality benefit is the point.

This design is reflected throughout the repo:
- `data/ledger/bhp_sources.csv` carries every hard fact with page, note, and
  exact reference fields
- `src/validate_citations.py` checks that each cited value actually appears on
  the cited page in the source PDF
- The ledger's `HARD_FACT` tier enforces that `citation` and `as_of` are present
  before a fact is accepted as VERIFIED

---

## The Valuation Workflow

### Step 1: Define the Revenue Model

Start with the revenue driver, not arbitrary growth rates.

**Bad approach**:
> "Revenue grows 5% per year"

**Good approach**:
> Revenue = Unit Volume × Avg Price
> - Unit Volume: Historical data shows 1,000 units sold in FY25. Management guidance (Aug 2024) targets 10% annual volume growth through market share gains in the industrial segment. Broker consensus (12 brokers, median) is 8% growth. Model base case at 8%.
> - Avg Price: FY25 was $100/unit. Management commentary indicates 2-3% annual price increases in line with inflation. Model $103/unit in FY26, $105 in FY27, etc.

Every line item has a **basis** (why this number makes sense) and a **source** (where did I get it).

### Step 2: Build Cost Structure

Model costs as either:

1. **Fixed costs** (e.g., head office salaries, annual software licenses)
2. **Variable costs** (e.g., COGS as % of revenue)
3. **Scale-dependent costs** (e.g., depreciation tied to capex; interest tied to debt levels)

Document why each cost grows or shrinks with revenue.

**Example — COGS as % of Revenue**:

```
FY25 COGS = $400m, Revenue = $1,000m → 40% of revenue
Historical range: 38-42% (per 10-year financial summaries)
Management commentary (FY25 result call, page 4): "COGS improved to 40% from 42% as we optimized supply chain"
Model assumption: COGS stays at 40%, with potential upside to 38% if supply-chain savings accelerate
```

### Step 3: Model Capital Expenditure

Capex is not a single line item; it's typically:

1. **Growth Capex** (capex needed to grow revenue): Tie to revenue growth assumptions
2. **Sustaining Capex** (capex to maintain current production): Often tied to depreciation or historical averages
3. **Cyclical/One-Off Capex** (major assets, expansions): Explicitly modeled with timing and payoff period

**Example — Mining Company**:

```
Year 1-2:  Sustaining capex $50m (maintain existing mine)
Year 3:    Growth capex $400m (develop new mine)
Year 4-10: Sustaining capex $50m on each mine
```

### Step 4: Calculate Free Cash Flow

Free cash flow to firm (FCFF):

```
FCFF = EBIT × (1 - tax rate) + Depreciation - Capex - Change in NWC
```

Or from P&L perspective:

```
FCFF = NPAT + Interest × (1 - tax rate) + D&A - Capex - Δ NWC
```

Ensure consistency across both methods.

### Step 5: Build WACC

Cost of equity via CAPM:

```
Cost of Equity = Risk-Free Rate + Beta × Market Risk Premium
```

Example for Australian ASX stock:

```
Risk-Free Rate:        4.0%  (10Y AUS govt yield, current)
Beta:                  1.2   (Company more volatile than market)
Market Risk Premium:   6.0%  (historical equity risk premium, Australia)
Cost of Equity:        4.0% + 1.2 × 6.0% = 11.2%
```

Cost of debt (after-tax):

```
Cost of Debt (pre-tax):  5.0%  (current weighted avg interest rate on debt)
Tax Rate:               30%
Cost of Debt (post-tax): 5.0% × (1 - 0.30) = 3.5%
```

WACC (weighted by market values):

```
Market Value of Equity:   $5bn
Market Value of Debt:     $1bn
Total Value:              $6bn

WACC = (5/6) × 11.2% + (1/6) × 3.5% = 9.6%
```

### Step 6: Calculate Terminal Value

At the end of your explicit forecast period (10 years), the company has a value based on:

**Perpetuity Growth Method** (most common):

```
Terminal Value = FCFF(Year 10) × (1 + g) / (WACC - g)

Example:
FCFF Year 10:  $100m
Terminal Growth: 2.5% (in line with long-term GDP growth)
WACC:          9.6%

TV = $100m × 1.025 / (0.096 - 0.025) = $100m × 1.025 / 0.071 = $1,441m
```

**Exit Multiple Method** (alternative):

```
Terminal Value = FCFF(Year 10) × Exit EV/EBITDA Multiple

Example:
FCFF Year 10:        $100m (assume = EBITDA for simplicity)
Peer average EV/EBITDA: 12x

TV = $100m × 12 = $1,200m
```

### Step 7: Discount to Present Value

```
PV = FCFF / (1 + WACC)^year

For Terminal Value:
PV(TV) = TV / (1 + WACC)^10
```

### Step 8: Calculate Valuation

```
Enterprise Value = PV of explicit FCFF (Years 1-10) + PV of Terminal Value
Equity Value = Enterprise Value - Net Debt
Value per Share = Equity Value / Shares Outstanding
```

---

## Worked Example: Simple Company

**Company**: RegularCorp
**FY25 Financials**: Revenue $1,000m, EBITDA $300m, NPAT $100m

### Build Revenue Model

```
FY25 Base:        $1,000m
Management target (FY26-27): 10% growth per year  [Source: Aug 2024 guidance]
Consensus estimate (FY28+): 5% growth per year   [Source: 10 brokers, median]

FY26: $1,000m × 1.10 = $1,100m
FY27: $1,100m × 1.10 = $1,210m
FY28: $1,210m × 1.05 = $1,271m
FY29-FY35: 5% per year
```

### Model EBITDA

```
FY25 EBITDA Margin: 30% ($300m / $1,000m)
Assume improves to 32% by FY28 as scale benefits kick in, then stable

FY26: $1,100m × 30% = $330m
FY27: $1,210m × 31% = $375m
FY28: $1,271m × 32% = $407m
FY29+: 32% (stable)
```

### Model D&A and Capex

```
Depreciation:  $50m historically (tied to PPE)
Assume stable.

Capex:
FY26-27: $80m (growth capex for expansion)
FY28+: $60m (sustaining capex)
```

### Calculate FCFF

```
FY26 EBITDA:           $330m
Less: D&A             ($50m)
= EBIT                $280m
Less: Tax @ 30%       ($84m)
= NOPAT               $196m
Add: D&A              $50m
Less: Capex           ($80m)
Less: Δ NWC           ($20m)
= FCFF                $146m

[Repeat for FY27-FY35]
```

### Build WACC

```
Risk-Free Rate (10Y AUS yield):    4.0%
Beta (RegularCorp):                1.0  (market beta)
Market Risk Premium:               6.0%
Cost of Equity:  4.0% + 1.0 × 6.0% = 10.0%

Cost of Debt (pre-tax):            5.0%
Tax Rate:                          30%
Cost of Debt (post-tax):           5.0% × 0.70 = 3.5%

Market Value Equity:               $2,000m  (share price × shares)
Market Value Debt:                 $500m
Total:                             $2,500m

WACC = (2,000/2,500) × 10.0% + (500/2,500) × 3.5%
     = 8.0% + 0.7% = 8.7%
```

### Calculate Terminal Value

```
FCFF(FY35):         $250m (after 10 years of modeled growth)
Terminal Growth:    2.5%

TV = $250m × (1.025) / (0.087 - 0.025) = $250m × 1.025 / 0.062 = $4,133m
```

### Discount to PV

```
PV of FCFF (Years 1-10):  [Sum of discounted annual FCFF]  = $1,500m
PV of TV (at Year 10):    $4,133m / (1.087^10) = $1,800m

Enterprise Value:         $1,500m + $1,800m = $3,300m
Less: Net Debt:           $400m
Equity Value:             $2,900m
Shares Outstanding:       100m
Value per Share:          $29.00
```

### Cross-Check vs. Comps

```
Peer 1 (SimilarCorp):    EV/EBITDA = 11x
Peer 2 (ComparaCorp):    EV/EBITDA = 10x
Peer 3 (MatchCorp):      EV/EBITDA = 11x
Median Peer Multiple:    11x

RegularCorp FY26E EBITDA: $330m
Implied EV:               $330m × 11x = $3,630m
Less: Net Debt:           $400m
Implied Equity Value:     $3,230m
Implied Value/Share:      $32.30

DCF: $29.00 | Comps: $32.30
Variance: +11% (acceptable, suggests DCF assumptions are slightly conservative)
```

---

## Key Judgments & Sensitivities

Every model has critical judgment calls:

1. **Revenue growth**: Is management guidance credible? Is market saturation a risk?
2. **Margin trajectory**: Can the company sustain / improve margins, or does competition force pressure?
3. **Capex phasing**: Is the capex plan realistic, and will it actually drive the projected revenue growth?
4. **WACC**: Is the cost of equity reasonable given the company's systematic risk? Does the cost of debt reflect current market rates?
5. **Terminal growth**: Is 2.5% realistic, or should it be lower (1.5%) given long-term GDP growth constraints?

Always run a **two-way sensitivity table** (WACC vs. Terminal Growth) to show:

```
                    Terminal Growth Rate
WACC      1.5%      2.0%      2.5%      3.0%
8.0%      $32.50    $35.40    $38.75    $43.20
8.5%      $30.10    $32.50    $35.40    $38.75
9.0%      $28.10    $30.10    $32.50    $35.40
9.5%      $26.40    $28.10    $30.10    $32.50
```

This shows that a 50bp change in WACC (8% to 8.5%) results in a ~7% swing in value per share, making WACC assumptions critical.

---

## Avoiding Common Pitfalls

| Pitfall | Example | How to Avoid |
|---------|---------|-------------|
| **Assume constant margins** | SaaS company with scale but no margin expansion | Model margin improvement explicitly with drivers (R&D leverage, SG&A leverage) |
| **Ignore working capital** | Growing company with increasing receivables/inventory | Track days of receivables, inventory, payables; model NWC build |
| **Capex doesn't drive growth** | Model $500m capex but no corresponding revenue uplift | Explicitly link capex to revenue assumptions (capex for what?) |
| **Terminal value too high** | Terminal value = 80% of enterprise value | Check reasonableness: is terminal value 40-60% of EV? If >70%, assumptions may be stretched |
| **No cross-check** | DCF gives $10, comps give $15, call it "range" | Resolve divergence. If they disagree >20%, something is wrong. |
| **Magic growth rates** | "Revenue grows 20% forever" | Growth must decelerate toward long-term GDP growth (2-3% for developed markets) |
| **WACC too low** | Cost of equity 8%, but company is high-beta | Check WACC reasonableness: should typically be 7-12% for mature companies, 10-15% for early-stage |

---

## Sensitivity & Scenario Analysis

Beyond base-case DCF, always model:

### 1. Two-Way Sensitivity Tables

Show how valuation changes with two key assumptions:

```
Rows: WACC (8.0% to 10.0% in 50bp increments)
Columns: Terminal Growth Rate (1.5% to 3.5% in 0.5% increments)
Cells: Value per share
```

### 2. Scenario Analysis

Build explicit scenarios with coherent assumptions:

**Bull Case** (e.g., 25th percentile):
- Revenue growth at management guidance (higher)
- Margins expand faster (competition weaker)
- WACC lower (lower risk profile)
- Terminal growth at high end (2.5%)
- Result: $35 target

**Base Case** (median):
- Revenue growth at consensus
- Margins as modeled
- WACC as built
- Terminal growth at 2.5%
- Result: $29 target

**Bear Case** (e.g., 75th percentile):
- Revenue growth below consensus
- Margin pressure (intense competition)
- WACC higher (higher risk)
- Terminal growth at low end (1.5%)
- Result: $22 target

### 3. Stress Testing

What breaks the model? Test:

- Commodity prices down 20% (mining)
- Customer churn up 500bps (SaaS)
- Interest rates up 200bps (banks, REITs)
- Capex overrun 30% (infrastructure)

---

## Documentation Standards

Every model should have:

1. **Cover Sheet**: Company, analyst, date, key assumptions (WACC, terminal growth, margin), valuation summary
2. **Assumptions Sheet**: Every input with source, basis, date
3. **Financial Statements**: P&L, balance sheet, cash flow (10 years)
4. **DCF Schedule**: FCFF calculation, discount factors, PV, terminal value
5. **Sensitivity Table**: Two-way (WACC vs. TG), scenario summary
6. **Comps Analysis**: Peer multiples, implied valuation
7. **Model Audit**: Reconciliation checks, integrity validation

---

## Final Checkpoints

Before publishing:

- [ ] Does revenue growth have an explicit driver (units × price, ARR growth, m³ × commodity price)?
- [ ] Are all assumptions sourced (management guidance, filings, consensus, analyst estimates)?
- [ ] Do three financial statements reconcile (P&L → equity, balance sheet balance, cash flow)?
- [ ] Does valuation bridge (PV of FCFF + PV of TV = target price)?
- [ ] Have you cross-checked DCF vs. comps vs. precedent transactions?
- [ ] Does WACC seem reasonable (7-12% for mature; 10-15% for early-stage)?
- [ ] Have you run two-way sensitivity and stress scenarios?
- [ ] Can you defend every assumption if challenged?

If any answer is "no," go back and fix it.
