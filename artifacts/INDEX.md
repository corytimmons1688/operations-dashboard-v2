# Vercel-Port Handoff — Artifact Index

Three artifacts are shipped alongside this index. Trust them in this order:

| Artifact | Trust level | Size | Use when |
|---|---|---|---|
| `facts.yaml` | **Highest** — auto-extracted from source via AST/regex. Zero paraphrase. | 8 KB | You need a column name, a sheet tab, a function line number, a constant value, or an enum. |
| `calculations.md` | **High** — full source of every non-UI function, AST-extracted. | 565 KB | You need the exact math for an aggregation, cadence calc, or categorization. |
| `LOGIC_HANDOFF.md` | **Medium** — narrative playbook explaining WHY, written from agent summaries. Some line numbers may be stale. | ~60 KB | You need to understand intent and business rules, not cite specifics. |

## Where to look, by question

| Question | Go to |
|---|---|
| Which sheet tab holds X? | `facts.yaml → sheets[]` |
| What's the exact column name on Y? | `facts.yaml → sheets[]`, then read the loader function in `calculations.md` |
| What are the pending-order statuses? | `facts.yaml → enums.pending_order_statuses` |
| What rep quotas are set for the current quarter? | `facts.yaml → constants.REP_QUOTAS` |
| Which corporate parents do we aggregate? | `facts.yaml → constants._KNOWN_MSO_PARENTS` |
| How is a customer name classified as a child of a parent? | `calculations.md → _match_mso_parent` and `_crm_extract_parent` |
| How is the parent/child map built from all three data sources? | `calculations.md → build_parent_child_map` |
| What period does "YTD" / "This Quarter" / "Last Year" resolve to? | `calculations.md → compute_period_bounds` |
| How are comparison-period bounds (Prior / YoY) computed? | `calculations.md → compute_comparison_bounds` |
| How is the 6-tile KPI hero's data calculated? | `calculations.md → compute_account_kpis` |
| How are SKUs categorized into product types? | `calculations.md → categorize_product` (plus `rollup_dml_lids` for universal-lid resolution) |
| How is reorder cadence predicted? | `calculations.md → render_sku_reorder_analysis_section` (interval-average of unique order dates) |
| How are HubSpot NCR tickets classified? | `calculations.md → categorize_hubspot_ncr` |
| How do NCRs get matched to NetSuite customers? | `calculations.md → match_customer` + `normalize_for_matching` + `extract_base_company` + `try_match` |
| How do the three HTML exports differ (aggregated / state-by-state / individual)? | `calculations.md → generate_qbr_html`, `generate_combined_qbr_html`, `generate_combined_summary_html` |
| Why is "Correct Customer" spelled without the -ed? | That's real. Invoice line items use `Correct Customer`; invoice headers use `Corrected Customer`; SO headers use `Corrected Customer Name`. See `LOGIC_HANDOFF.md §0`. |
| What's the ship-date spillover rule for forecast bucketing? | `LOGIC_HANDOFF.md §3` (narrative) + `calculations.md → calculate_rep_metrics` in `q2_revenue_snapshot.py` (authoritative) |
| Why does the deal line items tab use range `A2:V`? | Headers are in row 2, not row 1. See `facts.yaml → sheets[]`. |

## Canonical file map

| What lives where | File |
|---|---|
| Unified account overview + parent/child helpers + exports | `calyx-sop-dashboard-v2/src/yearly_planning_2026.py` (14.7k lines) |
| Current-quarter forecast, rep quotas, attainment, spillover | `calyx-sop-dashboard-v2/src/q2_revenue_snapshot.py` (6.3k lines) |
| Prior-quarter frozen snapshots | `calyx-sop-dashboard-v2/src/q1_revenue_snapshot.py`, `q4_revenue_snapshot.py` |
| Rev-Ops analytics layer (has some overlapping logic) | `calyx-sop-dashboard-v2/src/Rev_Ops_Playground.py` (11.3k lines) |
| Google Sheets client + caching | `calyx-sop-dashboard-v2/src/data_loader.py` |
| Routing, global CSS, rep selector | `calyx-sop-dashboard-v2/app.py` |

## Build-order suggestion for the Vercel port

1. **Data layer first.** Implement the 6 sheet loaders with the exact column-name contracts in `facts.yaml → sheets[]`. Write a normalization layer that collapses the three customer-column spellings to a single canonical `customer` field.
2. **Parent/child map.** Port `build_parent_child_map` + `_match_mso_parent` + `_crm_extract_parent` + the `_KNOWN_MSO_PARENTS` table. Unit-test with the 18 cases documented in `LOGIC_HANDOFF.md §1`.
3. **Period resolver.** Port `compute_period_bounds` + `compute_comparison_bounds`. Small, pure functions, easy to translate.
4. **KPI computation.** Port `compute_account_kpis`. Confirm which metrics are period-filtered vs current-state (`LOGIC_HANDOFF.md §5` has the table).
5. **Then the UI.** Hero + trend chart + child-breakdown table + section accordion. By this point the data layer is trusted.
6. **Exports later.** The three HTML generators are the most Python-specific; consider whether the Vercel port needs HTML export at all, or if browser print-to-PDF of the live page is enough.

## What's NOT in this handoff

- The Streamlit widget/session-state layer — not portable, re-architect for Next.js.
- The legacy QBR Generator's PDF-config toggles — consider whether the new dashboard needs them at all.
- Per-sheet Apps Script / formula logic upstream of the Python (e.g., what computes `Updated Status`). That lives in Google Sheets, not in the repo. Ask whoever owns the Sheets.

