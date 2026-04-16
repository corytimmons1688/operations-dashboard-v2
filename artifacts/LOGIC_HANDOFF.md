# Logic Handoff — Operations Dashboard → Next.js / Vercel Port

> ## ⚠️ VERIFICATION STATUS — READ FIRST
>
> **This document is WIP and has NOT been fully code-verified.**
>
> Much of it was synthesized from (a) exploratory agent summaries and (b) session memory while the author was actively editing `yearly_planning_2026.py` — which means some `file:line` anchors have drifted and some claims are one-step removed from a direct read of the source.
>
> **Before trusting any specific claim:**
> 1. Treat the **narrative explanations** as a starting map, not ground truth.
> 2. Treat the **column names, sheet tabs, status enums, and hardcoded lists** (MSO parents, quotas, rep allowlist, pending statuses, NCR categories, SKU exclusions) as more reliable — they come from structured extraction.
> 3. Cross-check any `file:line` anchor against the current source before quoting it back. Line numbers shift whenever `yearly_planning_2026.py` is edited.
> 4. The companion file **`artifacts/calculations.md`** is AST-extracted (fully verified) and contains the actual source bodies of all 292 calculation functions. Prefer it when you need the exact implementation.
>
> A follow-up pass will either (a) replace this prose with a structured YAML/JSON schema of facts plus a thin file-level index, or (b) re-verify every citation in place. See the session discussion for which route was chosen.

---

**Purpose**: This is the playbook for how our Streamlit operations dashboard parses, aggregates, and presents data. If you're the Claude Code thread building the new Vercel dashboard, read this before you write any queries. It's organized by **what the rep is looking at**, not by module — because that's how the business thinks about the data.

For every section below you'll find:
- **What it answers** — the business question
- **Where the data lives** — sheet tabs and columns
- **How we filter and aggregate** — the rules
- **Parsing rules & gotchas** — cleaning, joins, edge cases that will bite you
- **Code anchors** — `file:line` in the current Streamlit repo if you want the canonical implementation

The companion file `artifacts/calculations.md` contains the full source code of every calculation function extracted via AST (292 functions, ~11.7k lines). Use this doc for the **why**, that one for the **exact how**.

---

## 0. Data sources — the 30-second primer

All data lives in a single Google Sheets workbook. Six tabs matter for everything in this document:

| Tab name | What it is | Range loaded | Column variant gotcha |
|---|---|---|---|
| `All Reps All Pipelines` | HubSpot deals (header-level) | `A:Z` | `Company Name` may be blank → fall back to `Primary Associated Company` |
| `Deals Line Item` | HubSpot deal line items (SKU level) | **`A2:V`** (headers start at row 2) | `Amount` is NOT stored — compute as `Effective unit price × Quantity` |
| `_NS_Invoices_Data` | NetSuite invoice headers | `A:U` | Customer column is `Corrected Customer` |
| `Invoice Line Item` | NetSuite invoice line items | `A:Z` | Customer column is `Correct Customer` (no "-ed" — this is real) |
| `_NS_SalesOrders_Data` | NetSuite sales order headers | `A:AG` (need full width for `Updated Status`) | Customer column is `Corrected Customer Name` |
| `Sales Order Line Item` | NetSuite SO line items | `A:W` | Quantity field is `Quantity Ordered`, aliased to `Quantity` at load |

**The three customer-column spellings will trip you.** Any unified query needs to normalize these before joining:

| Tab | Customer column spelling |
|---|---|
| Sales Order header | `Corrected Customer Name` |
| Invoice header | `Corrected Customer` |
| Invoice Line Item | `Correct Customer` |
| HubSpot Deals | `Company Name` (with `Primary Associated Company` fallback) |
| HubSpot Deal Line Items | inherits from deal via Deal ID |

**Amount column aliasing.** On both invoices and sales orders the sheet may carry the column as `Amount` OR `Amount (Transaction Total)`. The loader renames to `Amount`. On deal line items there is no Amount — you compute it.

**Standard cleaner** applied to every numeric field:
```python
# yearly_planning_2026.py:3622
def clean_numeric(value):
    if pd.isna(value) or str(value).strip() == '':
        return 0
    cleaned = str(value).replace(',', '').replace('$', '').replace(' ', '').strip()
    try:    return float(cleaned)
    except: return 0
```
Strips `$` and commas, coerces to float, returns `0` (not `NaN`) on parse failure. This matters — downstream math assumes numbers, not nullables.

**Standard date cleaner**: `pd.to_datetime(col, errors='coerce')` — bad dates become `NaT`, not a crash.

**Deal Owner is synthesized.** HubSpot gives you two columns (`Deal Owner First Name`, `Deal Owner Last Name`). At load time the dashboard concatenates them with a space, strips `\n`/`\r` chars, and stores as `Deal Owner`.

---

## 1. Parent/child account aggregation — READ THIS FIRST

This is the single most important piece of tribal knowledge in the repo. **Do not build any customer view without implementing it.**

### The problem
Corporate parents (MSOs like Curaleaf, AYR Wellness, TerrAscend, Acreage, Trulieve) operate many state-level locations. Each location is a separate row in NetSuite and HubSpot. Without aggregation, reps see twelve Curaleaf locations as twelve customers instead of one account with twelve children.

### How parents are detected — two strategies, applied in order

**Strategy 1 — The `Parent : Child` delimiter.** Some customer names are already hierarchical:
```
AYR Wellness, Inc. : Ayr Wellness (OH)
AYR Wellness, Inc. : AYR Canntech LLC (PA)
AYR Wellness, Inc. : AYR Liberty Health Sciences (FL)
Acreage Holdings : New York
Acreage Holdings : Massachusetts
```
Split on ` : ` (literal, with the spaces) and take the left side. That's the parent.

**Strategy 2 — Curated MSO prefix list.** Most MSOs DON'T use the colon format in NetSuite. They appear as flat names:
```
Curaleaf NJ
Curaleaf MA
Curaleaf - Florida
TerrAscend PA
TerrAscend New Jersey
Trulieve - Tampa
GTI Chicago
Cresco Labs OH
```
These need a curated list. The canonical table lives in `calyx-sop-dashboard-v2/src/yearly_planning_2026.py:4454` as `_KNOWN_MSO_PARENTS`:

```python
_KNOWN_MSO_PARENTS = {
    "Curaleaf": ["Curaleaf"],
    "TerrAscend": ["TerrAscend", "Terrascend", "Terra Ascend"],
    "Trulieve": ["Trulieve"],
    "Verano": ["Verano"],
    "Green Thumb Industries": ["Green Thumb Industries", "Green Thumb", "GTI"],
    "Cresco Labs": ["Cresco Labs", "Cresco"],
    "Columbia Care / Cannabist": ["Columbia Care", "Cannabist"],
    "Jushi Holdings": ["Jushi Holdings", "Jushi"],
    "Ascend Wellness Holdings": ["Ascend Wellness Holdings", "Ascend Wellness", "AWH"],
    "AYR Wellness, Inc.": ["AYR Wellness, Inc.", "AYR Wellness", "Ayr Wellness", "AYR"],
    "Acreage Holdings": ["Acreage Holdings", "Acreage"],
    "Glass House Brands": ["Glass House Brands", "Glass House"],
    "4Front Ventures": ["4Front Ventures", "4Front"],
    "Planet 13": ["Planet 13"],
    "MedMen": ["MedMen"],
    "Schwazze": ["Schwazze"],
    "Harvest Health & Recreation": ["Harvest Health", "Harvest HOC"],
    "StateHouse Holdings": ["StateHouse Holdings", "StateHouse"],
    "Holistic Industries": ["Holistic Industries"],
    "Revolutionary Clinics": ["Revolutionary Clinics"],
    "Parallel": ["Parallel Cannabis", "Surterra"],
    "The Cannabist Company": ["The Cannabist Company"],
    "Goodness Growth Holdings": ["Goodness Growth", "Vireo Health", "Vireo"],
    "Lowell Farms": ["Lowell Farms", "Lowell Herb Co"],
}
```

### The matching rule — do not over-match

A customer name is classified as a child of parent P when, **after lowercasing and collapsing whitespace**:
1. The name starts with one of P's aliases, AND
2. The next character is a separator — space, dash, colon, comma, paren, slash, or dot.

An **exact equality** with the alias is treated as "this IS the parent, not a child of itself" and returns `None` (so the parent doesn't get listed as a child of itself). Example outcomes:

| Input | Parent |
|---|---|
| `Curaleaf NJ` | `Curaleaf` |
| `Curaleaf - Florida` | `Curaleaf` |
| `Curaleaf (MA)` | `Curaleaf` |
| `Curaleaf` (exact) | `None` (this IS the parent) |
| `TerrAscend New Jersey` | `TerrAscend` |
| `Terrascend MA` (misspelled) | `TerrAscend` |
| `GTI Chicago` | `Green Thumb Industries` |
| `Generic Shop Inc` | `None` (not in MSO list → standalone) |

### Build the map once, reference everywhere

Scan the union of unique customer names across all three sources (SO header + invoice header + HubSpot deals' `Company Name 2`) and produce three dicts:

```
{
  "parent_to_children":  { "Curaleaf": ["Curaleaf NJ", "Curaleaf MA", ...], ... },
  "child_to_parent":     { "Curaleaf NJ": "Curaleaf", ... },
  "normalized_child_to_parent": { "curaleaf nj": "Curaleaf", ... }  // for fuzzy rematch
}
```

Anchor: `build_parent_child_map` at `yearly_planning_2026.py:4553`.

### Scope resolution — the one place parent → children expansion happens

When a user picks an account, expand it:
- If `account ∈ parent_to_children` AND scope is "rolled up" → return all children
- If scope is "single location" → return `[child]`
- Otherwise standalone → return `[account]`

Anchor: `resolve_account_customers` at `yearly_planning_2026.py:4615`.

**Critical**: EVERY metric query, EVERY filter, EVERY export must pull its customer list from this function. Drift here = double-counting or missing locations.

### When to extend the MSO list

If a customer that should aggregate is showing as standalone, add the canonical parent + its name aliases to `_KNOWN_MSO_PARENTS`. The matcher is case-insensitive so capitalization variants are covered automatically. Misspellings (like `Terrascend` vs `TerrAscend`) need an explicit alias.

---

## 2. Customer naming conventions & fuzzy matching

Beyond the parent/child aggregation above, there's another customer-matching layer used for **linking HubSpot NCR tickets to NetSuite customers**. Worth knowing because the patterns are reused elsewhere.

### The normalizer
Purpose: make "Acreage Holdings NY" and "Acreage Holdings (NY)" and "Acreage Holdings Smearing Defect" all collapse to "Acreage Holdings".

```python
# yearly_planning_2026.py:4068
def normalize_for_matching(name):
    name = str(name).strip()
    # Drop state abbreviations at end: NY, MA, OH, NJ, PA, IL, CA, CO, FL, TX, ...
    name = re.sub(r'\s+(NY|MA|OH|NJ|PA|IL|CA|...)\s*$', '', name, flags=re.IGNORECASE)
    # Drop parenthetical state codes: (OH), (NY)
    name = re.sub(r'\s*\([A-Z]{2}\)\s*', ' ', name)
    # Drop trailing descriptors
    name = re.sub(r'\s+(Smearing|Defect|Issue|Problem|Damage|Error).*$', '', name, flags=re.IGNORECASE)
    return name.strip()
```

### The base-company extractor
Handles three hierarchical name formats:

```python
# yearly_planning_2026.py:4081
def extract_base_company(company_name):
    # Format 1: "Parent : Child" (HubSpot Company Name 2)
    if ' : ' in name: return name.split(' : ')[0].strip()
    # Format 2: "Company: Location (STATE)"
    if ':' in name:
        base = name.split(':')[0].strip()
        if '.' not in base and len(base) > 3: return base
    # Format 3: "Company - Location (STATE)" — only when second part looks like a state
    if ' - ' in name:
        parts = name.split(' - ')
        second = parts[1].strip() if len(parts) > 1 else ''
        if re.search(r'(Massachusetts|New York|Ohio|...)', second, re.IGNORECASE):
            return parts[0].strip()
    return name
```

### The fuzzy matcher — three tiers of cutoff

Uses Python's `difflib.get_close_matches`. Tiered cutoffs because name quality varies by source:

| Source | Cutoff | Why |
|---|---|---|
| HubSpot `Company Name 2` | `0.8` | Most structured — stricter pass |
| HubSpot `Company Name` | `0.7` then `0.6` | Less structured — progressive relaxation |
| HubSpot `Ticket name` extraction | `0.5` | Fallback, permissive |

```python
# yearly_planning_2026.py:4113
def try_match(name, customers, cutoff=0.7):
    if name in customers: return name
    # Try normalized exact match
    normalized = normalize_for_matching(name)
    for cust in customers:
        if normalize_for_matching(cust) == normalized: return cust
    # Fuzzy
    matches = get_close_matches(name, customers, n=1, cutoff=cutoff)
    return matches[0] if matches else None
```

**The valid-customers pool** for matching is the union of `Corrected Customer Name` (SO) + `Corrected Customer` (invoices), filtered to drop `''`, `'nan'`, `'None'`, `'#N/A'`.

---

## 3. Current-quarter forecast & attainment

**What it answers**: "How much will each rep close this quarter, and how close are they to quota?"

### Where to look
- Per-quarter file: `calyx-sop-dashboard-v2/src/q2_revenue_snapshot.py` (Q2 2026) — each quarter gets its own file (`q1_revenue_snapshot.py`, `q4_revenue_snapshot.py`, ...). Don't factor them — they're hardcoded on purpose so historical numbers never change.

### The rule: ship date wins over close date

Every deal is bucketed into a quarter by **when we expect it to SHIP**, not when the HubSpot close date says. This is the single most important rule in the forecast. The dashboard reads a column called `Q3 2026 Spillover` (or equivalent for the current quarter) on each deal row that says "this closes in Q2 but actually ships in Q3" — if that column has a value, we push the deal to the target quarter.

```python
# q2_revenue_snapshot.py:3747
rep_deals['Ships_In_Q2'] = (rep_deals[spillover_col] != 'Q3 2026') & \
                            (rep_deals[spillover_col] != 'Q1 2026')
rep_deals_ship_q2 = rep_deals[rep_deals['Ships_In_Q2'] == True]
```

This is why a deal closing in Q1 can count toward Q2 forecast (and vice-versa).

### Quota configuration — hardcoded, per rep, per quarter

Quotas live inline at the top of each quarter file. No lookup table, no external config. They're frozen so historical dashboards don't drift.

```python
# q2_revenue_snapshot.py:706
REP_QUOTAS = {
    "Jake Lynch":      2_739_194,
    "Dave Borkowski":  1_013_647,
    "Brad Sherman":      566_039,
    "Lance Mitton":      241_753,
    "Alex Gonzalez":           0,
    "Owen Labombard":          0,
    "Shopify ECommerce":       0,
}
TEAM_QUOTA = sum(REP_QUOTAS.values())  # 4_560_633
```

Reps can have a `0` quota (new hires, non-quota-carrying channels like Shopify). Treat `quota == 0` as "don't compute attainment %; show absolute progress only."

### Quarter date boundaries — also hardcoded

```python
# q2_revenue_snapshot.py:700
QUARTER_LABEL = "Q2 2026"
QUARTER_START = "2026-04-01"
QUARTER_END   = "2026-06-30"
```

To advance the dashboard to a new quarter, someone has to create a new `q3_revenue_snapshot.py`. This is intentional — each quarter's snapshot is a frozen artifact.

### Forecast composition — four buckets summed

Total forecast = **A + B + C + D**, each from a different data source:

| Bucket | Source | Filter | Column |
|---|---|---|---|
| **A. Invoiced revenue** | Dashboard Info sheet (or `_NS_Invoices_Data` filtered by date) | Already shipped in Q2 | `NetSuite Orders` (or `NetSuite Orders Net` when the "exclude shipping" toggle is on) |
| **B. Expect + Commit pipeline** | HubSpot deals | `Status ∈ {"Expect", "Commit"}` AND ships in Q2 | Raw `Amount` (NOT probability-weighted) |
| **C. Pending Approval** | NetSuite SO | `Updated Status` starts with `PA` | `pa_date_amount` + `pa_no_date_amount` |
| **D. Pending Fulfillment** | NetSuite SO | `Updated Status` starts with `PF` | `pf_date_ext_amount` + `pf_date_int_amount` |

```python
# q2_revenue_snapshot.py:3839
total_progress = orders + expect_commit_q2 + pending_approval + pending_fulfillment
attainment_pct = (total_progress / quota * 100) if quota > 0 else 0
```

### Best Case upside — separate bucket, not in base forecast

Deals with `Status ∈ {"Best Case", "Opportunity"}` are tracked separately as "potential upside" and shown as a secondary projection, never rolled into `total_progress`. The `potential_attainment` metric is:

```python
potential_attainment = ((total_progress + best_opp_q2) / quota * 100) if quota > 0 else 0
```

### Status taxonomy (HubSpot `Close Status` / `Status`)

| Value | Forecast bucket |
|---|---|
| `Expect` | ✅ Base forecast (Bucket B) |
| `Commit` | ✅ Base forecast (Bucket B) |
| `Best Case` | ⚠️ Potential upside only |
| `Opportunity` | ⚠️ Potential upside only |
| `Closed Won` | Already in Invoiced Revenue (Bucket A) — not in deals view |
| `Closed Lost` | ❌ Excluded |
| `Cancelled`, `Checkout Abandoned` | ❌ Excluded (q2_revenue_snapshot.py:721) |

### Attainment vs pacing

The dashboard shows **absolute attainment %** — no time-of-quarter normalization. There's no "you're 50% through Q2 so you should be at 50% of quota" pacing metric. The gap is just `quota - total_progress` in absolute dollars.

If you want pacing in the new dashboard, it's a net-new feature — just be explicit that it's new so nobody thinks the old numbers were wrong.

### Shipping toggle — watch out

There's a UI toggle to exclude shipping charges from forecast amounts. When ON, the dashboard swaps:
- `NetSuite Orders` → `NetSuite Orders Net`
- `Amount` → `Net_Amount` (SO columns)

The toggle affects every bucket. The underlying columns are pre-computed upstream (in Sheets / Apps Script) — the Python just switches which column it reads.

### Code anchors for rebuild

| What | Anchor |
|---|---|
| Quota dictionary | `q2_revenue_snapshot.py:706` |
| Quarter boundaries | `q2_revenue_snapshot.py:700` |
| Spillover / ships-in-quarter filter | `q2_revenue_snapshot.py:3747-3770` |
| Forecast summation | `q2_revenue_snapshot.py:3839-3842` |
| SO category splits (PA/PF) | `q2_revenue_snapshot.py:3600-3625, 3824-3826` |
| Closed-status exclusion list | `q2_revenue_snapshot.py:721-729` |

---

## 4. Rep pipeline & quota view

**What it answers**: "For a single rep — how's their pipeline distributed, how much can slip, and what's their runway?"

### Data shape
Rep is always selected from this hard-allowed list (same in every tool):
```python
ALLOWED_REPS = [
    "Jake Lynch", "Brad Sherman", "Lance Mitton", "Owen Labombard",
    "Alex Gonzalez", "Dave Borkowski", "Kyle Bissell",
]
```
Anchor: `yearly_planning_2026.py:8508`.

Also add `"All Reps"` as option 0 for leadership views.

Per-rep filtering uses the `Rep Master` column on SO and invoice headers, and `Deal Owner` on HubSpot deals. `Rep Master` is authoritative — `Deal Owner` sometimes doesn't match (e.g., after a rep switch) so don't cross-reference them for conflict detection unless you want a rabbit hole.

### The rep-level computation

1. **Pull rep's customers**: union of unique `Corrected Customer Name` (from SO where `Rep Master == rep`) + `Corrected Customer` (from invoices where `Rep Master == rep`). Filter out `'', 'nan', 'None', '#N/A'`. Anchor: `get_customers_for_rep` at `yearly_planning_2026.py:4688`.
2. **Group into accounts**: run the parent/child map (Section 1) over the customer list. Parents get rolled up; standalones stay individual.
3. **Per-account metrics**: last order date, YTD revenue, open AR, pipeline value, deal count, health status.
4. **Per-rep aggregates**: sum the account metrics to get the rep's book-of-business numbers.

### Health-status thresholds (rolled up — "best child wins")

| Label | Rule |
|---|---|
| `active` | any child ordered within last 30 days |
| `at_risk` | most recent order across children 30–90 days ago |
| `dormant` | most recent order 90+ days ago |
| `never` | no orders on record for any child |

Anchor: `build_rep_account_roster` at `yearly_planning_2026.py:4785`.

### Special rep handling

- `Alex Gonzalez` — `Deal Owner Last Name == 'Gonzalez'` rows on **Deals Line Item** are **filtered out** of the pipeline forecast in `Rev_Ops_Playground.py:6878`. This is a deliberate business rule (retention pipeline is handled differently). Don't carry it into the new dashboard without confirming it's still correct.
- `Shopify ECommerce` — has $0 quota; shows up in the roster but treat attainment as N/A.

---

## 5. Customer Account Overview (QBR) — the core screen

**What it answers**: "Give me the one-page story on this account — what have they ordered, what's open, what's at risk, and what's pipelining?"

This is the screen we unified this session. It's the canonical rep-facing view.

### The control surface (top of page)

1. **Rep selector** → filters account list
2. **Account selector** → parent names (rolled up) and standalone customers
3. **Scope toggle** (only when a parent is selected) → `Rolled up` vs `Single location`
4. **Period chips** (radio, horizontal): `All Time · YTD · This Quarter · Last Year · Last 90 Days · Custom Range`
5. **Comparison toggle**: `Off · Prior Period · Same Period Last Year`
6. **Export options** (see Section 13)

### Period semantics — exactly what each preset means

The resolver returns `(start_date, end_date, label)`. Where `start` or `end` is `None`, that side is open-ended.

```python
# yearly_planning_2026.py:7034  compute_period_bounds()
```

| Preset | Start | End | Label format |
|---|---|---|---|
| `All Time` | `None` | `None` | `"All Time"` |
| `YTD` | Jan 1 of current year | today | `"YTD 2026"` |
| `This Quarter` | First day of current quarter | today | `"Q2 2026"` |
| `Last Year` | Jan 1 of prior year | Dec 31 of prior year | `"FY 2025"` |
| `Last 90 Days` | today - 90 days | today | `"Last 90 Days"` |
| `Custom Range` | user-picked | user-picked | `"Apr 01, 2026 – Jun 30, 2026"` |

**Timezone**: uses `America/New_York` when available (`datetime.now(ZoneInfo("America/New_York"))`), with a naive fallback. The dashboard never shows hours/minutes — everything is date-floored.

### Comparison window math

```python
# yearly_planning_2026.py:7069  compute_comparison_bounds()
```

| Mode | How it's computed |
|---|---|
| `off` | no comparison |
| `prior` | span = `end - start` days; comparison window = `[start - span, start - 1 day]` |
| `yoy` | shift both `start` and `end` back one year (Feb 29 → `start - 365 days`) |

If the current period is `All Time`, comparison is impossible → return `None`.

### Which metrics are period-filtered and which aren't

This trips every re-implementation. Be careful:

| Metric | Period-filtered? | Reason |
|---|---|---|
| Revenue (period) | ✅ YES | that's the whole point |
| Avg Order Value | ✅ YES | `revenue_in_period / distinct_SOs_in_period` |
| Deals Won $ / count | ✅ YES | filtered on `Close Date` |
| Monthly revenue trend | ✅ YES | grouped by `Date.dt.to_period("M")` |
| **Pipeline value** | ❌ NO | "Pipeline" is a current-state number — always as-of-now |
| **Open AR** | ❌ NO | "Open AR" is a current balance — always as-of-now |
| **Last Order Date** | ✅ YES | within the selected window (if no orders in window, shows "—") |

Anchor: `compute_account_kpis` at `yearly_planning_2026.py:7100`.

### Scope expansion — single source of truth

Any metric pulled on this screen goes through `resolve_account_customers()` first. If parent → all children. If single-location → `[child]`. If standalone → `[account]`. This is the only place expansion happens. Don't do it inline elsewhere or numbers drift.

### The 6-tile KPI hero

| Tile | Value | Delta (if comparison on) |
|---|---|---|
| Revenue | `sum(invoices.Amount)` for period | vs comparison period |
| Pipeline | `sum(open_deals.Amount)` current | n/a |
| Open AR | `sum(invoices[Status=='Open'].Amount Remaining)` | n/a |
| Last Order | most recent `Order Start Date` within period + days-ago + which child | n/a |
| Avg Order Value | `revenue / distinct_SOs` | vs comparison |
| Deals Won | count + $ of `Close Status ∈ {won, closed won}` within period | vs comparison |

### Child accounts breakdown (parent roll-up only)

Below the hero, when a parent is selected in rolled-up mode, show a table with one row per child:

| Col | Source |
|---|---|
| Location (health dot) | child name + colored dot based on last-order recency |
| Last Order | max `Order Start Date` for child |
| YTD Revenue | sum invoices Amount for child YTD |
| Open AR | sum invoices `Amount Remaining` where `Status == 'Open'` for child |
| Pipeline | sum open-deals Amount for child |

Clicking a row re-scopes the whole page to that single child. Anchor: `build_child_breakdown` at `yearly_planning_2026.py:4880`.

---

## 6. Pending Orders

**What it answers**: "What's in the queue — approvals outstanding, fulfillment pending, and what's aging?"

### Source & filter

Single source: **`_NS_SalesOrders_Data`**. Filter on the `Updated Status` column — a pre-computed string column in the sheet that encodes the SO's pipeline stage. Loaded from column range `A:AG` (need the full width or you lose this column).

### The full taxonomy

```python
# yearly_planning_2026.py:4825
pending_statuses = [
    'PA with Date',
    'PA No Date',
    'PA Old (>2 Weeks)',
    'PF with Date (Ext)',
    'PF with Date (Int)',
    'PF No Date (Ext)',
    'PF No Date (Int)',
]
```

| Status | Meaning | Aging signal |
|---|---|---|
| `PA with Date` | Pending Approval; customer has committed a date | use `Pending Approval Date` for aging |
| `PA No Date` | Pending Approval; no date | no aging bucket |
| `PA Old (>2 Weeks)` | PA + date is >14 days old | already an aging marker |
| `PF with Date (Ext)` | Pending Fulfillment; external delay (carrier, customer) | use `Customer Promise Last Date to Ship` or `Projected Date` |
| `PF with Date (Int)` | Pending Fulfillment; internal delay (production) | ditto |
| `PF No Date (Ext)` | PF external, no confirmed ship date | unknown aging |
| `PF No Date (Int)` | PF internal, no confirmed ship date | unknown aging |

### Metrics to render per account/rep

```python
# Sum of Amount across pending rows
total_pending_value = pending_rows['Amount'].sum()

# Split by prefix
pa_value = pending_rows[pending_rows['Updated Status'].str.startswith('PA')]['Amount'].sum()
pf_value = pending_rows[pending_rows['Updated Status'].str.startswith('PF')]['Amount'].sum()
```

The breakdown table is grouped by `Updated Status`. Anchor: `render_pending_orders_section` at `yearly_planning_2026.py:4812`.

### Expected Ship Date — a computed field on SO line items

Line-item-level ship-date prediction, used when you need to roll pending orders up by delivery month:

```python
# Rev_Ops_Playground.py:6765
# For PF (Pending Fulfillment) status
#   → Customer Promise Last Date to Ship (fallback: Projected Date)
# For PA (Pending Approval) status
#   → Pending Approval Date
```

### The `Updated Status` column is upstream-computed

The dashboard does **not** calculate whether an SO is "PA with Date" vs "PA No Date" — that classification happens in a Google Apps Script / Sheets formula layer, and Python just reads the result. If you port to a DB-backed system, you need to replicate that classification logic before this section works. A rough translation:

- If `Status == 'Pending Approval'` and `Pending Approval Date` is set → `PA with Date`
- If `Status == 'Pending Approval'` and `Pending Approval Date` is empty → `PA No Date`
- If `PA with Date` and date > 14 days ago → `PA Old (>2 Weeks)`
- If `Status == 'Pending Fulfillment'` → `PF` + with/without-date + Ext/Int flag based on another source field

Verify with whoever owns the Sheets formulas before you re-implement.

---

## 7. Open Invoices & AR Aging

**What it answers**: "Who owes us money, how much, and how overdue?"

### Open = `Status == 'Open'`, balance = `Amount Remaining`

```python
# yearly_planning_2026.py:826
open_invoices = customer_invoices[customer_invoices['Status'] == 'Open']
open_invoice_count = len(open_invoices)
open_invoice_value = open_invoices['Amount Remaining'].sum()
```

Three non-obvious rules:

1. **Never period-filter AR.** Open AR is always as-of-now regardless of what period chip is selected. The rep wants the current balance, not "AR from Q1 only."
2. **`Amount Remaining`, not `Amount`.** `Amount` is the original invoice total; `Amount Remaining` is what's still owed. Partial payments land in the former but not the latter.
3. **`Status` is case- and whitespace-sensitive.** Already stripped at load time, but when matching use exact `'Open'` (capitalized).

### Aging buckets

```python
# yearly_planning_2026.py:2205
def aging_bucket(days):
    if days <= 0:  return 'Current'
    elif days <= 30:  return '1-30 Days'
    elif days <= 60:  return '31-60 Days'
    elif days <= 90:  return '61-90 Days'
    else:              return '90+ Days'

open_inv['Days Overdue'] = (today - open_inv['Due Date']).dt.days
open_inv['Aging']        = open_inv['Days Overdue'].apply(aging_bucket)
```

- `Days Overdue = today - Due Date`. Negative = not yet due → "Current".
- `today` is a date, not a datetime (all the math is in days).
- If `Due Date` is `NaT`, the aging bucket is whatever `NaN.days` evaluates to — filter those out or handle explicitly.

### Aging summary

```python
aging_summary = open_inv.groupby('Aging')['Amount Remaining'].sum()
```

Render in the fixed order `Current → 1-30 → 31-60 → 61-90 → 90+`, not alphabetical. The ordering is semantic.

---

## 8. Product Mix / Top SKUs

**What it answers**: "What categories and specific products drive this account's revenue?"

### Source & aggregation

Always use **`Invoice Line Item`** for realized mix — it's the drill-down layer under the invoice header and carries `Item`, `Item Description`, `Amount`, `Quantity`, and the `Calyx || Product Type` categorization.

```python
# Pattern used in QBR rendering
category_summary = product_df.groupby(parent_col).agg({'Amount': 'sum'}).reset_index()
category_summary.columns = ['Category', 'Revenue']
category_summary = category_summary.sort_values('Revenue', ascending=False)
category_summary['% of Revenue'] = (category_summary['Revenue'] / product_revenue * 100).round(1)
```

**Sort order is always Revenue descending.** Unit count is misleading because components (base, lid, label) aren't the same as finished products.

### Two-level hierarchy

1. **Parent Category** — rolled up: `Drams`, `Concentrates`, `Boxes`, `Flexpack`, etc.
2. **Unified Category** — size-specific: `Drams (15D)`, `Drams (25D)`, `Concentrates (4mL)`, `Concentrates (7mL)`, etc.

Use Parent for executive/summary views; Unified for rep-facing QBRs where the size detail matters.

### The fees-and-adjustments filter

Revenue Mix excludes non-product lines (shipping, taxes, discount adjustments, tooling fees). Anchor: the `Fees & Adjustments` branch of `categorize_product` handles classification; the display layer filters that category out before computing `product_revenue` and the percentages.

---

## 9. Product categorization — the `categorize_product` taxonomy

This is the canonical SKU-to-category logic. The new dashboard needs a faithful port — it drives product mix, SKU reorder, aging by product, and the whole "what do they buy" narrative.

Anchor: `yearly_planning_2026.py:5425`.

### Signature

```python
def categorize_product(item_name, item_description="", calyx_product_type=""):
    """Returns (category, sub_category, component_type)."""
```

- `category` — top-level group (Drams, Concentrates, Boxes, ...)
- `sub_category` — size-specific (15D Base, 4mL Lid, ...)
- `component_type` — physical role: `'base'`, `'lid'`, `'label'`, `'band'`, `'accessory'`, `'complete'`, or `None`

### Input priority

Check the three inputs in this order (each can override the previous):
1. `Calyx || Product Type` (when populated, this is the canonical ERP classification)
2. Regex patterns on `Item` (SKU code)
3. Keyword match on `Item Description`

### Category table — the full taxonomy

| Parent Category | Sub-Categories | Pattern hint | Component |
|---|---|---|---|
| **Fees & Adjustments** | Taxes, Shipping, Expedite Fee, Convenience Fee, Discount, Tooling Fee, Sample/Creative, Accounting Adjustment | `TAX`, `SHIPPING`, `CONVENIENCE FEE`, `TOOLING FEE` | — |
| **Calyx Cure** | Calyx Cure | `CC-*` or `CALYX CURE` | complete |
| **Calyx Jar** | Glass Base, Jar Base, Jar Lid, Shrink Band | `GB-8TH`, `CJ-*`, `-JB-`, `-JL-`, `SB-8TH` | base / base / lid / band |
| **Concentrates** | 4mL Base, 7mL Base, 4mL Lid, 7mL Lid, 4mL Label, 7mL Label, Universal Lid | `GB-4ML`, `GB-7ML`, `-4[CLH]-`, `-7[CLH]-`, die-tool `^[47][CLH]` | base / lid / label / lid |
| **Drams** | 15D/25D/45D/145D Base, Lid, Lid Label, Base Label | `PB-XXD`, `PL-XXD`, `CL-XXD`, die-tool `^XX[LBPH]` | base / lid / label |
| **Dram Accessories** | Tray Frame, Tray Insert, Shrink Band, FEP Liner, Stick & Grip | `TF-*`, `TI-XXD`, `SB-XXD`, `FEP`, `SG-*` | accessory / band |
| **Tubes** | 116mm, 90mm, 84mm Tubes + Labels | `JT-116`, `JT-90`, `JT-84` | complete / label |
| **Boxes** | Core Auto, Core Tuck, Shipper, Display | `-CNCA-`, `CORE AUTO`, `DISPLAY` | complete |
| **Flexpack** | Wavepack, Bag/Pouch | `BAM-*`, `WAVEPACK`, `FLEXPACK`, or `Calyx \|\| Product Type` | complete |
| **DML (Universal)** | Universal Lid — 4mL/7mL/15D | `PL-DML`, `CL-DML` | lid (resolves later, see below) |
| **Non-Core Labels** | Custom Label | `LABEL`, numeric die-tool, customer SKU like `^[A-Z]{3,4}-[A-Z]{2}-` | label |
| **Other** | Uncategorized | (no match) | — |

### The three edge cases that matter

**1. Die-tool extraction for customer-specific labels.** Customers ordering branded labels have SKUs like `ACME-MI-H-25L-0001`. The alphanumeric "die tool" is extracted from the fourth segment (`25L`) and parsed as `<size><type>`:
- `4`, `7`, `15`, `25`, `45`, `145` → concentrate or dram size
- `C` = cap, `L` = label, `H` = heat-seal, `B` = base, `P` = plain

So `25L` → Drams (25D Lid Label). Anchor: `yearly_planning_2026.py:5520`.

**2. DML lid resolution — must pair with a base on the same invoice.** `PL-DML` is a universal lid. Whether it's a concentrate lid or a dram lid depends on what base it ships alongside:

```python
# yearly_planning_2026.py:5738  rollup_dml_lids()
# If the invoice has:
#   GB-4ML (4mL base)      → DML lid becomes Concentrates (4mL Lid)
#   GB-7ML (7mL base)      → DML lid becomes Concentrates (7mL Lid)
#   PB-15D (15D base)      → DML lid becomes Drams (15D Lid)
#   nothing determinative  → stays "DML (Universal)"
```

This step runs **after** the initial categorization pass. The new dashboard needs both passes.

**3. "Tooling Fee" must be classified as a fee BEFORE label matching.** The string `TOOLING FEE - Labels` matches the `LABEL` keyword but it's actually a fee. The fee regex (`TOOLING\s*FEE`) is checked first.

### Applying it to a dataframe

```python
# yearly_planning_2026.py:5701  apply_product_categories()
categories = df.apply(lambda r: categorize_product(
    r.get('Item', ''),
    r.get('Item Description', ''),
    r.get('Calyx || Product Type', ''),
), axis=1)

df['Product Category']     = categories.apply(lambda x: x[0])
df['Product Sub-Category'] = categories.apply(lambda x: x[1])
df['Component Type']       = categories.apply(lambda x: x[2])
```

Then run `rollup_dml_lids()` if you want DML resolution.

### Unified category column for customer-facing reports

For QBR product mix the dashboard collapses Parent + Sub into a single readable label:

```python
# yearly_planning_2026.py:5807  create_unified_product_view()
# Drams + 15D → "Drams (15D)"
# Concentrates + 4mL Lid → "Concentrates (4mL)"
# Parent category stays for executive roll-ups
```

This drives the "Unified Category" and "Parent Category" columns seen in the QBR product mix table.

---

## 10. SKU Order History — reorder cadence

**What it answers**: "How often does this customer reorder each SKU, and when do we expect the next order?"

### One order = one unique date per SKU

Important: multiple line items on the same invoice date count as ONE order. Use `Date.dt.date` (strip the time), deduplicate, sort ascending:

```python
# yearly_planning_2026.py:6536  (inside render_sku_reorder_analysis_section)
order_dates = sku_orders['Date'].dt.date.unique()
order_dates = sorted(order_dates)
num_orders = len(order_dates)
```

### Average interval and predicted next order

```python
if num_orders >= 2:
    intervals = []
    for i in range(1, len(order_dates)):
        interval = (order_dates[i] - order_dates[i-1]).days
        if interval > 0:
            intervals.append(interval)

    if intervals:
        avg_days_between = sum(intervals) / len(intervals)
        last_order_dt = pd.Timestamp(last_order)
        predicted_next = last_order_dt + timedelta(days=avg_days_between)
        days_until_next = (predicted_next - today).days
```

- Skip zero and negative intervals (same-day dupes that escaped the unique-date collapse).
- If `num_orders < 2`, no prediction (shows `"—"`).

### Status buckets for the "days until next" column

| Value | Label |
|---|---|
| `< -14` | `🔴 Overdue` |
| `-14 … 0` | `🟠 Past` |
| `0 … 30` | `🟢 Due Soon` |
| `> 30` | `🔵 Upcoming` |

### Exclusions — never include these SKUs in cadence calc

```python
EXCLUDED_SKUS = [
    'AVATAX', 'UPS GROUND', 'UPS NEXT DAY SAVER', 'Estes Express',
    'Convenience Fee 3.5%', 'Tooling Fee - Labels', 'Expedite Fee',
    'Ecommerce Shipping', 'Ecommerce shipping',
]
EXCLUDED_PATTERNS = [
    'fee', 'shipping', 'freight', 'ups ', 'fedex', 'estes', 'avatax',
    'tax', 'tooling', 'expedite', 'convenience', 'surcharge', 'handling',
]
```

Applied before computing intervals. Fees don't have reorder cadence.

### SKU display names — load once, lookup always

Canonical product descriptions live in a separate sheet called `Raw_Items`:

```python
# yearly_planning_2026.py:3634  load_sku_display_names()
# Range: A:C (SKU, Display Name, Description)
# Lookup: {raw_sku: display_description}
# Priority: Column C "Description" → fallback to Column B "Display Name"
```

Use this when rendering card titles, tooltips, or export labels — the raw SKUs are ugly codes like `PB-25D-BK`, the Raw_Items sheet gives human-readable descriptions.

---
