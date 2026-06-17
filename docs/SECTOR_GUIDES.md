# Sector-Specific Valuation Guides

Deep-dive guides for each major sector, with worked examples and pitfalls to avoid.

---

## 1. MINING & RESOURCES

### Why Generic DCF Fails

Mining companies have:
- **Commodity price exposure** (uncontrollable by management)
- **Reserve depletion** (finite lives, declining ore quality)
- **Capex lumpy and large** (development capex, major expansions)
- **Multiple assets at different stages** (producing mines, development projects, prospects)

A generic DCF that assumes stable revenue growth and constant capex misses everything that matters.

### The Right Approach: NAV / Sum-of-Parts

Value each **asset separately**, then sum:

```
Asset 1 (Mine A - Producing):    NPV of mine life
Asset 2 (Mine B - Development):  PFS value × probability of development
Asset 3 (Exploration Project):   Risk-adjusted exploration upside
Asset 4 (Corporate / HQ):        Deduct corporate costs not allocated to assets
Less: Net Debt / Financing:      Deduct debt, add cash
= Net Asset Value (NAV)

NAV per Share = NAV / Shares Outstanding
```

### Step 1: Value Each Mine

For a producing mine:

```
1. Production Schedule (by year)
   - Historical data + management guidance
   - Ore reserves, mine plan, grade curve
   - Example: Year 1: 1,000 ore tonnes, 5% grade → 50 tonnes metal

2. Commodity Price Assumptions
   - Current spot price
   - Historical volatility
   - Consensus long-term (3-5 year) price
   - Terminal price (usually long-term average)

3. Operating Costs
   = Processing costs ($/tonne ore)
   + Transport costs ($/tonne ore)
   + Smelting treatment charges ($/tonne metal)
   + Corporate allocation ($/tonne)
   
4. Capex
   - Initial development capex (if not yet spent)
   - Annual sustaining capex (keep mine running)
   - Exploration capex
   
5. Taxes & Royalties
   - Corporate income tax
   - Mining royalties (% of revenues or NAV)
   - Special mining taxes (some jurisdictions)

6. Discount Rate
   - Typically 7-10% for operating mines (relatively certain)
   - 12-15%+ for development/exploration (higher risk)
   
7. Terminal Value / Residual Value
   - Salvage value of plant & equipment (small)
   - Or in-situ value of remaining ore (more realistic)
```

### Step 2: Build NAV Bridge

```
GROSS NAV:
  Mine A (PFS, 60% prob of dev):     A$ 300m × 60% = A$ 180m
  Mine B (Producing):                                  A$ 450m
  Exploration Property (upside):                       A$  50m
  Joint Ventures (50% share):                          A$ 100m
  Gross NAV:                                           A$ 780m

LESS: DEDUCTIONS:
  Net Debt:                                            A$ 200m
  Corporate Deduction:                                 A$  40m
  Minority Interests:                                  A$  10m
  Adjusted NAV:                                        A$ 530m

PER SHARE:
  Shares Outstanding:                                  100m
  NAV per Share (unrisked):                            A$  5.30
  
APPLY DISCOUNT:
  Typical range: 10-30% (due to company-specific risk, junior miner uncertainty)
  Conservative (20% discount):                         A$  4.24
  Base Case (15% discount):                            A$  4.51
  Optimistic (10% discount):                           A$  4.77
```

### Step 3: Sensitivity Analysis

Test to commodity price shocks (biggest driver for mining):

```
Commodity Price      NAV per Share
80% of base           A$ 3.50
90% of base           A$ 4.10
100% of base          A$ 4.51
110% of base          A$ 4.95
120% of base          A$ 5.35
```

Also test:

- **Discount rate** (±1%): Changes NPV of long-dated assets significantly
- **Development probability** (e.g., 50% vs 70% vs 90%): Big impact on pre-dev projects
- **Capex timing**: Does phasing move, what's the NPV impact?

### Key Pitfalls

| Pitfall | Fix |
|---------|-----|
| Using current spot commodity price (too volatile) | Use consensus long-term price (brokers, industry associations) |
| Ignoring reserve depletion (assumes infinite mine life) | Model declining production as ore body depletes; include mine closure costs |
| Treating all capex the same | Separate growth capex (drives production, impacts revenue) from sustaining (just keeps lights on) |
| Valuing development projects at full PFS value | Apply probability of success discount (60% for dev, 30% for early exploration) |
| Overstating corporate costs | Only deduct head office costs not allocated to mines; mine-specific costs in each asset NPV |
| Ignoring JVs and partnerships | Value your % stake; for JVs, get your proportional share of economics |

### Real Example: Diversified Miner

```
Assets:
- Copper Mine A (producing, 8yr life):     A$ 600m NPV
- Copper Mine B (development):             A$ 300m × 65% prob = A$ 195m
- Gold Project (early-stage):              A$ 100m × 40% prob = A$ 40m
- Lithium Deposit (in negotiation):        A$ 50m (option value only)

Gross NAV:                                  A$ 885m
Less: Net Debt                             (A$ 250m)
Less: Corporate costs (2yr capitalized)    (A$ 40m)
Adjusted NAV:                               A$ 595m
÷ Shares Outstanding:                       150m
= NAV per Share (unrisked):                 A$ 3.97

Applying 20% discount:                      A$ 3.17
```

---

## 2. SaaS / TECHNOLOGY

### Why SaaS Is Different

- **Recurring revenue model** (ARR is the key metric, not total revenue)
- **Expansion revenue** (net revenue retention >100% means growing revenue from existing customer base)
- **Low/negative gross margin businesses can be valuable** (if CAC payback is short and LTV is high)
- **Valuation multiples are absurd relative to traditional businesses** (15-25x EV/Revenue vs. 1-2x for industrials)

### Key Metrics

#### 1. Annual Recurring Revenue (ARR)

```
ARR (end of year) = Sum of all subscription contracts on Dec 31

Unlike GAAP revenue (which includes one-time, services, other):
ARR captures only the recurring, contracted revenue stream
```

#### 2. Net Revenue Retention (NRR)

```
NRR = (ARR_current_year - Churned_ARR + Expansion_ARR) / ARR_prior_year

Example:
Year 0 ARR:                                 $100m
Less: Customers lost (churn):               ($ 5m)
Add: Existing customers buying more:       ($ 8m)  [expansion/upsell]
Year 1 ARR:                                 $103m

NRR = ($103m / $100m) = 103%

If NRR > 100%, the company is growing from its existing customer base
without acquiring new customers (highest quality growth)
```

#### 3. Customer Acquisition Cost (CAC) & Payback

```
CAC = Total Sales & Marketing spend / New customers acquired

CAC Payback = CAC / (Gross Margin per customer / month)

Example:
Annual S&M spend:                           $50m
New customers acquired:                     100
CAC per customer:                           $500k

Annual gross margin per customer:           $80k
Monthly gross margin per customer:          $6.7k

CAC Payback = $500k / $6.7k = 75 months (6.25 years)
[Industry standard: <12 months = great, 12-24 months = acceptable]
```

#### 4. Lifetime Value (LTV)

```
LTV = Gross Margin per Customer × Expected Customer Life (months)

Or more precisely:
LTV = (ARPU × Gross Margin %) / Monthly Churn Rate

Where:
ARPU = Average Revenue per User / Customer
```

#### 5. The "Magic Number"

```
Magic Number = Incremental ARR in Year N / Sales & Marketing spend in Year N-1

Benchmark: >0.75 is healthy, >1.0 is excellent

Indicates how efficiently the company converts sales spend into recurring revenue
```

### Valuation Approach

**Method 1: ARR-based DCF**

```
Forecast ARR for 10 years:
- Use historical NRR to project ARR growth
- Model deceleration as company grows (harder to grow from larger base)
- Apply S&M and R&D leverage to model improving margins

Forecast Rule of 40:
- Growth Rate + Operating Margin should track toward 40% target
- Shows health of unit economics + profitability path

Run DCF on FCFF derived from:
- Subscription revenue (from ARR)
- Professional services / other revenue (smaller)
- Operating margins (S&M, R&D, G&A as % of revenue)
- Assume low/negative capex (software company)

Discount at 10-15% WACC (higher risk than manufacturing)
```

**Method 2: EV/ARR Multiple**

```
Peer Comps (SaaS companies):
- Company A: $10bn market cap / $100m ARR = 100x EV/ARR
- Company B: $5bn market cap / $80m ARR = 62.5x EV/ARR
- Company C: $3bn market cap / $50m ARR = 60x EV/ARR

Median peer multiple: 62x

For your SaaS company with $20m ARR:
Implied valuation = $20m ARR × 62x = $1,240m

[But be careful: growth rate and profitability path matter enormously in multiple]
```

### Modelling Assumptions

#### Revenue Growth

```
Years 1-3:   Aggressive growth (50%+ YoY) if in land-grab phase
Years 4-7:   Moderate growth (20-30% YoY) as market saturates
Years 8-10:  Mature growth (10-15% YoY)
Terminal:    Long-term growth 3-5%

Drivers:
- Existing customer expansion (NRR, typically 110-130% for healthy SaaS)
- New customer acquisition (new logos, depends on S&M efficiency)
- Price increases (usually 3-8% annually)
```

#### Operating Margins

```
Early stage (pre-profitability):
- Gross margin:    60-80% (software, minimal COGS)
- S&M margin:      -50% to -30% (spending heavily to acquire customers)
- R&D margin:      -15% (product development)
- G&A margin:      -10% (corporate overhead)
- Operating margin: Negative (improving toward breakeven)

Mature / efficient:
- Gross margin:    75%+
- S&M margin:      -20% to -10% (more efficient acquisition)
- R&D margin:      -8% (more leverage)
- G&A margin:      -5% (scale)
- Operating margin: +15-25%

[Note: Some SaaS companies maintain negative growth-adjusted margins to grow faster;
this is a choice, not a mistake]
```

### Worked Example

```
SaaSCorp: $30m ARR, growing 40% YoY

DCF Valuation:
- Years 1-3: 40% growth (ARR: $30 → $42 → $59 → $83m)
- Years 4-7: 25% growth → 20% → 15% → 10% growth (decelerating)
- Years 8-10: 8% growth (maturing)
- Terminal: 3% growth

Operating margins:
- Years 1-3: -10% (operating margin, company still scaling but approaching breakeven)
- Years 4-7: 0% to +5% (approaching profitability)
- Years 8-10: +12% (mature, profitable growth)

Discount rate (WACC): 12% (higher risk than mature company, but lower than early-stage startup)

Result: $800m enterprise value (not yet subtracting net debt; if company is debt-free, = equity value)
÷ 50m shares = $16 per share
```

### Key Pitfalls

| Pitfall | Fix |
|---------|-----|
| Model ARR growth forever at current rate | ARR growth MUST decelerate as company grows |
| Ignore churn / assume 0% monthly churn | Even "stable" SaaS has 1-5% monthly churn; impacts ARR sustainability |
| Confuse GAAP revenue with ARR | Services revenue, one-off deals, etc. don't count toward "recurring" ARR |
| Apply industrial company margins to SaaS | SaaS margins are structurally different; don't assume 30% net margin unless path is clear |
| Overestimate TAM expansion | TAM doesn't grow; company's share of TAM does. Model market share, not TAM growth |
| Ignore competition / assume sticky customers | High growth attracts competitors; model share pressure in years 5-10 |

---

## 3. REAL ESTATE / REITs

### Why Cap Rates Matter

REITs own real estate that generates **net operating income (NOI)**, not traditional earnings.

```
REIT valuation ≠ DCF on NPAT
REIT valuation = Sum of properties using cap rates + debt structure
```

### Key Metrics

#### 1. Net Operating Income (NOI)

```
NOI = Gross Rental Income - Operating Expenses

Gross Rental Income:
- Lease payments from tenants
- Usually grows with CPI / market rent growth

Operating Expenses:
- Property taxes
- Maintenance & repairs
- Insurance
- Management fees
- Usually ~20-40% of gross rental income (varies by property type)
```

#### 2. Capitalization Rate (Cap Rate)

```
Cap Rate = NOI / Property Value

Example:
Property annual NOI:    $10m
Cap Rate (market):      5%
Implied Property Value: $10m / 5% = $200m

[Cap rates vary by property type & location]
Market-implied cap rates (2024-2025):
- Grade A office (CBD):     4.0-5.0%
- Retail (good location):   5.0-6.0%
- Industrial/logistics:     4.5-5.5%
- Residential:              3.5-4.5%
```

#### 3. Net Tangible Assets (NTA)

```
NTA = Sum of property valuations - Net Debt

Ratio: NTA per Share / Current share price
- Below 1.0x = trading at discount to underlying asset value
- Above 1.0x = trading at premium
```

#### 4. Funds From Operations (FFO)

```
FFO = NPAT + Depreciation on real estate + Gains/(Losses) on property sales

[Similar to operating cash flow, but adjusted for non-cash items]
FFO Multiple = Market Cap / FFO
[How much investors pay per dollar of distributable cash]
```

### Valuation Approach

#### Method 1: Cap Rate Valuation

```
For each property:
1. Project annual NOI for next 10 years
   - Start year NOI
   - Growth rate (typically 2-3% per year, in line with inflation)
2. Apply cap rate to terminal year NOI (or use perpetuity formula)
3. Discount to present value

Example:
Property 1:
- Year 1 NOI:        $10m
- Growth:            2.5% per year
- Year 10 NOI:       $10m × (1.025^9) = $12.3m
- Terminal cap rate: 5.0%
- Terminal value:    $12.3m / 5% = $246m
- Discount (at 6%):  $246m / (1.06^10) = $137m

Property 2, 3, etc...

Sum properties, deduct debt, = Equity value
```

#### Method 2: NTA (Net Tangible Assets)

```
Total Gross Property Value (appraised):     $2,000m
Less: Debt                                  ($ 400m)
Less: Minority interests                    ($  50m)
= Net Tangible Assets:                      $1,550m

÷ Shares Outstanding:                       200m
= NTA per Share:                            $7.75

Current share price:                        $6.50
Discount to NTA:                            (16%)
```

#### Method 3: FFO Multiple

```
Total FFO (across all properties):          $150m
Peer FFO multiple (REIT sector):            15x
Implied market cap:                         $2,250m
Less: Net Debt:                             ($ 400m)
= Equity value:                             $1,850m
÷ Shares:                                   200m
= Per share:                                $9.25
```

### Sensitivity Analysis

Test:

1. **Cap Rate Changes** (±50bps)
   - If cap rates rise (investor demanded yield increases), property values fall
   - If cap rates fall (yield compression), values rise

2. **NOI Growth** (1.5% vs 2.5% vs 3.5% annual growth)
   - Properties with long-term leases have low NOI growth
   - Properties with upcoming lease renewals have higher growth potential

3. **Debt Levels** (current vs. 30% more debt vs. 30% less debt)
   - More debt = higher financial leverage, riskier equity
   - Less debt = lower returns on equity (but less financial risk)

### Key Pitfalls

| Pitfall | Fix |
|---------|-----|
| Use generic P/E multiples for REITs | Use FFO, not NPAT; apply cap rates, not P/E |
| Assume unlimited NOI growth | Property NOI growth limited by inflation / wage growth (2-3%); model realistically |
| Ignore capital recycling | REITs regularly sell mature properties and buy higher-growth properties; model turnover |
| Treat depreciation as real cost | In REIT accounting, depreciation is non-cash; FFO adds it back |
| Overpay for "trophy assets" | Blue-chip CBD office might trade at 4% cap rate, while suburban retail is 6%; understand why |

---

## 4. BANKING

### Why Standard DCF Breaks

Banks don't have "revenue" like normal companies. They have:

- **Net Interest Income (NII)**: Interest earned on loans minus interest paid on deposits
- **Fee Income**: Commissions, FX trading, advisory fees
- **Credit Losses**: Provisions for bad debts (reduce earnings, not a cash outflow initially)

A traditional DCF on NPAT misses the balance sheet dynamics that drive bank returns.

### Key Metrics

#### 1. Net Interest Margin (NIM)

```
NIM = (Interest Income - Interest Expense) / Average Interest-Earning Assets

Typical NIM for major banks: 2.0-3.5%

Factors affecting NIM:
- Central bank policy (RBA cash rate)
- Deposit mix (cost of deposits rises when rates rise)
- Loan mix (mortgages vs. business loans have different rates)
- Competition (lower rates if competition intense)
```

#### 2. Cost-to-Income (CTI)

```
CTI = Total Operating Costs / Total Revenue

Lower is better; typical range: 40-60%

Example:
Total costs:    $10bn
Total revenue:  $20bn
CTI:            50%
```

#### 3. Return on Equity (ROE)

```
ROE = Net Income / Average Shareholders' Equity

Benchmark: Most large banks target 12-15% ROE
```

#### 4. Loan-to-Deposit Ratio

```
L/D Ratio = Total Loans / Total Deposits

If >100%, bank is funding loans through wholesale markets (riskier)
If <100%, bank has stable deposit base to fund loans
```

#### 5. Capital Ratios

```
Common Equity Tier 1 (CET1) Ratio = CET1 capital / Risk-weighted assets

Regulatory minimum: ~11%
Well-capitalized: >13%

Banks above minimum have excess capital for dividends / buybacks / acquisitions
```

### Valuation Approach

#### Method 1: P/E Multiple

```
Peer P/E multiples (major banks):  15-18x
Your bank target P/E:               16x
Target ROE:                         14%

Implied growth rate (Gordon Growth):
P/E = Payout Ratio × (1 + g) / (r - g)

Where: r = cost of equity, g = growth

If bank is targeting 14% ROE and paying out 60% of earnings:
16x = 0.6 × (1 + g) / (0.10 - g)
=> Implies 3.7% long-term growth (reasonable for bank)
```

#### Method 2: P/B Multiple (Price-to-Book)

```
Price-to-Book = Market Cap / Book Value of Equity

Banks typically trade at 1.0-2.0x book depending on:
- ROE (higher ROE = higher P/B multiple)
- Capital ratios (well-capitalized = higher multiple)
- Asset quality (low impaired loans = higher multiple)
- Dividend yield (high yield = lower P/B)

Example:
Target ROE:                         15%
Cost of Equity:                     10%
Payout Ratio:                       60%

Implied P/B = ROE × Payout Ratio / (Cost of Equity - Growth)
           = 0.15 × 0.6 / (0.10 - 0.04)
           = 1.5x book value
```

#### Method 3: NIM-based Model

```
For projections:

Loan Portfolio:                     $500bn
Spread (NIM):                       2.5%
Interest Income on loans:           $12.5bn

Deposit Base:                       $600bn
Cost of deposits:                   1.5%
Interest Expense:                   $9.0bn

Net Interest Income:                $3.5bn
Fee Income:                         $1.2bn
Total Revenue:                      $4.7bn

Operating Costs (50% CTI):          $2.35bn
Operating Income:                   $2.35bn

Credit Losses / Provisions:         $0.3bn
NPAT (after tax):                   $1.6bn

ROE = $1.6bn / $20bn (equity) = 8%
[Model forward: as cost of deposits falls, NIM expands, ROE improves]
```

### Sensitivity Analysis

Test to:

1. **NIM Changes** (±50bps)
   - RBA rate changes, deposit cost changes

2. **Cost-to-Income Ratios** (48% vs. 50% vs. 52%)
   - Operating leverage, digital transformation

3. **Credit Costs** (low/normal/high)
   - Economic cycle effects

4. **Loan Growth** (2% vs. 4% vs. 6% annual)
   - Market share dynamics

### Key Pitfalls

| Pitfall | Fix |
|---------|-----|
| Model NIM as constant (it changes with rates) | Model NIM expansion/compression based on deposit re-pricing lag |
| Ignore credit cycle | Credit costs rise in downturns; test scenarios with 100-200bps higher provisions |
| Treat deposits as "free funding" | Deposits cost something (opportunity cost); model competitive deposit rates |
| Use revenue = total interest income | Use NET interest income (interest earned minus interest paid) |
| Project 20%+ ROE | Large banks have structural 12-15% ROE ceiling; higher implies market share gain or cost transformation unlikely |

---

## Summary Checklist by Sector

### Mining
- [ ] Value each mine separately (NPV of mine life)
- [ ] Model commodity prices (use consensus long-term, not spot)
- [ ] Include reserve depletion curve
- [ ] Deduct corporate overhead
- [ ] Test sensitivity to commodity prices & discount rates

### SaaS
- [ ] Model ARR growth with deceleration path
- [ ] Use net revenue retention (NRR) to project existing customer growth
- [ ] Test CAC payback & LTV
- [ ] Model margin expansion as company scales
- [ ] Use Rule of 40 as health check (growth + margin)

### REITs
- [ ] Value each property separately using cap rates
- [ ] Model NOI growth (typically 2-3%, tied to inflation)
- [ ] Calculate NTA (net asset value per share)
- [ ] Test to cap rate shocks (±50bps)
- [ ] Use FFO, not NPAT, for comparison

### Banking
- [ ] Model NIM based on deposit costs & interest-earning assets
- [ ] Calculate ROE as key metric (not revenue)
- [ ] Model cost-to-income ratio (CTI) improvements
- [ ] Test to credit cost shocks
- [ ] Use P/B (price-to-book) as primary valuation metric, not P/E

---

All frameworks should:

✓ Have transparent assumptions with sources
✓ Cross-check via 2-3 valuation methods
✓ Test sensitivities to key drivers
✓ Link back to sector fundamentals (not generic formulas)
✓ Produce a valuation that is mathematically defensible
