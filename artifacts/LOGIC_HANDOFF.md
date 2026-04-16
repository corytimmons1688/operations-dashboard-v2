# Logic Handoff — Operations Dashboard → Next.js / Vercel Port

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
