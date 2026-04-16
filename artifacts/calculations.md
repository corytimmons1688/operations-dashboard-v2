# Calculation Code Catalog

Auto-extracted from `operations-dashboard-v2` — every non-rendering function
that performs data aggregation, derived metrics, classification, forecasting,
or pure data transformation.

Total files scanned: **22**
Calculation functions extracted: **292**

Functions whose name starts with `render_` / `display_` / `generate_*_html`, or
whose body is dominated by `st.*` calls / Plotly figure building / HTML emission,
are **excluded** — this catalog is only the math and data logic.

---

## Index

### `calyx-sop-dashboard-v2/app.py` (2 functions)

- [`get_mst_time`](#calyx-sop-dashboard-v2-app-py-get_mst_time) — L105–L107
- [`main`](#calyx-sop-dashboard-v2-app-py-main) — L818–L837

### `calyx-sop-dashboard-v2/src/Rev_Ops_Playground.py` (64 functions)

- [`fig_to_base64`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-fig_to_base64) — L52–L62
- [`fig_to_html_embed`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-fig_to_html_embed) — L65–L75
- [`create_monthly_revenue_chart`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-create_monthly_revenue_chart) — L78–L123
- [`create_order_type_chart`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-create_order_type_chart) — L178–L218
- [`create_pipeline_chart`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-create_pipeline_chart) — L221–L271
- [`clean_numeric`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-clean_numeric) — L3427–L3435
- [`load_qbr_data`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-load_qbr_data) — L3438–L4027
- [`get_rep_list`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_rep_list) — L4032–L4046
- [`get_customers_for_rep`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_customers_for_rep) — L4049–L4078
- [`get_customer_deals`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_customer_deals) — L4081–L4100
- [`extract_die_tool`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-extract_die_tool) — L4669–L4711
- [`categorize_product`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-categorize_product) — L4714–L4987
- [`apply_product_categories`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-apply_product_categories) — L4990–L5169
- [`rollup_dml_lids`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-rollup_dml_lids) — L5172–L5238
- [`create_unified_product_view`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-create_unified_product_view) — L5241–L5331
- [`map_to_forecast_category`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-map_to_forecast_category) — L6291–L6335
- [`map_to_forecast_pipeline`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-map_to_forecast_pipeline) — L6338–L6356
- [`map_order_type_to_forecast_category`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-map_order_type_to_forecast_category) — L6359–L6383
- [`map_deal_type_to_forecast_category`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-map_deal_type_to_forecast_category) — L6386–L6433
- [`parse_forecast_sheet`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-parse_forecast_sheet) — L6440–L6505
- [`load_forecast_data`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-load_forecast_data) — L6509–L6516
- [`load_annual_tracker_data`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-load_annual_tracker_data) — L6520–L7040
- [`calculate_ytd_actuals`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_ytd_actuals) — L7047–L7097
- [`calculate_ytd_actuals_total`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_ytd_actuals_total) — L7100–L7129
- [`calculate_monthly_actuals`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_monthly_actuals) — L7132–L7183
- [`get_ytd_plan`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_ytd_plan) — L7186–L7196
- [`get_period_plan`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_period_plan) — L7199–L7241
- [`calculate_variance`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_variance) — L7244–L7264
- [`get_deals_for_export`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_deals_for_export) — L7271–L7337
- [`calculate_close_rate_metrics`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_close_rate_metrics) — L7340–L7451
- [`calculate_close_rate_by_category`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_close_rate_by_category) — L7454–L7498
- [`calculate_close_rate_by_pipeline`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_close_rate_by_pipeline) — L7501–L7551
- [`calculate_days_to_close_by_amount_bucket`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_days_to_close_by_amount_bucket) — L7554–L7616
- [`calculate_avg_deal_size_by_pipeline`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_avg_deal_size_by_pipeline) — L7623–L7668
- [`calculate_pipeline_expected_revenue`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_pipeline_expected_revenue) — L7671–L7761
- [`calculate_revenue_gap_analysis`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_revenue_gap_analysis) — L7764–L7804
- [`calculate_monthly_deals_needed`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_monthly_deals_needed) — L7807–L7822
- [`create_attainment_gauge`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-create_attainment_gauge) — L7829–L7866
- [`embed_chart`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-embed_chart) — L304–L321
- [`get_customer_friendly_status`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_customer_friendly_status) — L767–L774
- [`get_customer_friendly_status`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_customer_friendly_status) — L4554–L4561
- [`categorize_row`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-categorize_row) — L5077–L5134
- [`get_unified_category`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_unified_category) — L5267–L5306
- [`get_parent_category`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_parent_category) — L5312–L5327
- [`get_amount_bucket`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_amount_bucket) — L7586–L7596
- [`get_expected_value`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_expected_value) — L7707–L7723
- [`aging_bucket`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-aging_bucket) — L2012–L2017
- [`aging_bucket`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-aging_bucket) — L4199–L4209
- [`categorize_frequency`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-categorize_frequency) — L5740–L5748
- [`pattern_indicator`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-pattern_indicator) — L5823–L5830
- [`get_best_category_dli`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_best_category_dli) — L6932–L6940
- [`is_closed_won`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-is_closed_won) — L6946–L6955
- [`is_closed_lost`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-is_closed_lost) — L6960–L6962
- [`get_best_category`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_best_category) — L7019–L7027
- [`extract_customer_from_ticket`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-extract_customer_from_ticket) — L3714–L3742
- [`extract_ncr_number_from_ticket`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-extract_ncr_number_from_ticket) — L3744–L3754
- [`match_customer`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-match_customer) — L3756–L3861
- [`categorize_hubspot_ncr`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-categorize_hubspot_ncr) — L3877–L3944
- [`get_qty_and_product_type`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_qty_and_product_type) — L3971–L3983
- [`assign_so_manually_built_pipeline`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-assign_so_manually_built_pipeline) — L6634–L6650
- [`has_standard_reorder_date`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-has_standard_reorder_date) — L6846–L6851
- [`normalize_for_matching`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-normalize_for_matching) — L3761–L3772
- [`extract_base_company`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-extract_base_company) — L3774–L3804
- [`try_match`](#calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-try_match) — L3806–L3827

### `calyx-sop-dashboard-v2/src/aging_analysis.py` (2 functions)

- [`categorize_age`](#calyx-sop-dashboard-v2-src-aging_analysis-py-categorize_age) — L325–L344
- [`calculate_aging_metrics`](#calyx-sop-dashboard-v2-src-aging_analysis-py-calculate_aging_metrics) — L347–L370

### `calyx-sop-dashboard-v2/src/cost_analysis.py` (1 functions)

- [`aggregate_by_period`](#calyx-sop-dashboard-v2-src-cost_analysis-py-aggregate_by_period) — L459–L509

### `calyx-sop-dashboard-v2/src/data_loader.py` (9 functions)

- [`get_spreadsheet_id`](#calyx-sop-dashboard-v2-src-data_loader-py-get_spreadsheet_id) — L58–L60
- [`load_nc_data`](#calyx-sop-dashboard-v2-src-data_loader-py-load_nc_data) — L68–L132
- [`standardize_nc_columns`](#calyx-sop-dashboard-v2-src-data_loader-py-standardize_nc_columns) — L135–L173
- [`convert_nc_data_types`](#calyx-sop-dashboard-v2-src-data_loader-py-convert_nc_data_types) — L176–L215
- [`load_sample_data`](#calyx-sop-dashboard-v2-src-data_loader-py-load_sample_data) — L218–L274
- [`refresh_data`](#calyx-sop-dashboard-v2-src-data_loader-py-refresh_data) — L281–L284
- [`get_data_summary`](#calyx-sop-dashboard-v2-src-data_loader-py-get_data_summary) — L287–L319
- [`filter_nc_data`](#calyx-sop-dashboard-v2-src-data_loader-py-filter_nc_data) — L326–L366
- [`get_unique_values`](#calyx-sop-dashboard-v2-src-data_loader-py-get_unique_values) — L369–L375

### `calyx-sop-dashboard-v2/src/deliveries_tracking.py` (8 functions)

- [`prepare_shipment_data`](#calyx-sop-dashboard-v2-src-deliveries_tracking-py-prepare_shipment_data) — L136–L170
- [`categorize_shipment_status`](#calyx-sop-dashboard-v2-src-deliveries_tracking-py-categorize_shipment_status) — L173–L189
- [`calculate_expected_delivery`](#calyx-sop-dashboard-v2-src-deliveries_tracking-py-calculate_expected_delivery) — L192–L209
- [`check_if_delayed`](#calyx-sop-dashboard-v2-src-deliveries_tracking-py-check_if_delayed) — L212–L228
- [`check_for_exceptions`](#calyx-sop-dashboard-v2-src-deliveries_tracking-py-check_for_exceptions) — L231–L242
- [`generate_tracking_number`](#calyx-sop-dashboard-v2-src-deliveries_tracking-py-generate_tracking_number) — L245–L251
- [`assign_carrier`](#calyx-sop-dashboard-v2-src-deliveries_tracking-py-assign_carrier) — L254–L260
- [`apply_delivery_filters`](#calyx-sop-dashboard-v2-src-deliveries_tracking-py-apply_delivery_filters) — L263–L286

### `calyx-sop-dashboard-v2/src/forecasting_models.py` (13 functions)

- [`detect_seasonality`](#calyx-sop-dashboard-v2-src-forecasting_models-py-detect_seasonality) — L66–L101
- [`prepare_time_series`](#calyx-sop-dashboard-v2-src-forecasting_models-py-prepare_time_series) — L104–L126
- [`forecast_exponential_smoothing`](#calyx-sop-dashboard-v2-src-forecasting_models-py-forecast_exponential_smoothing) — L133–L253
- [`auto_arima_params`](#calyx-sop-dashboard-v2-src-forecasting_models-py-auto_arima_params) — L260–L317
- [`forecast_arima`](#calyx-sop-dashboard-v2-src-forecasting_models-py-forecast_arima) — L320–L407
- [`create_ml_features`](#calyx-sop-dashboard-v2-src-forecasting_models-py-create_ml_features) — L414–L456
- [`forecast_ml`](#calyx-sop-dashboard-v2-src-forecasting_models-py-forecast_ml) — L459–L620
- [`blend_forecasts`](#calyx-sop-dashboard-v2-src-forecasting_models-py-blend_forecasts) — L627–L676
- [`allocate_topdown_forecast`](#calyx-sop-dashboard-v2-src-forecasting_models-py-allocate_topdown_forecast) — L679–L710
- [`calculate_forecast_accuracy`](#calyx-sop-dashboard-v2-src-forecasting_models-py-calculate_forecast_accuracy) — L713–L756
- [`generate_forecast`](#calyx-sop-dashboard-v2-src-forecasting_models-py-generate_forecast) — L759–L786
- [`__init__`](#calyx-sop-dashboard-v2-src-forecasting_models-py-__init__) — L35–L49
- [`to_dataframe`](#calyx-sop-dashboard-v2-src-forecasting_models-py-to_dataframe) — L51–L63

### `calyx-sop-dashboard-v2/src/operations_view.py` (11 functions)

- [`get_category_items_map`](#calyx-sop-dashboard-v2-src-operations_view-py-get_category_items_map) — L33–L51
- [`compute_demand_history_cached`](#calyx-sop-dashboard-v2-src-operations_view-py-compute_demand_history_cached) — L55–L81
- [`compute_pipeline_data_cached`](#calyx-sop-dashboard-v2-src-operations_view-py-compute_pipeline_data_cached) — L85–L234
- [`clean_dataframe`](#calyx-sop-dashboard-v2-src-operations_view-py-clean_dataframe) — L258–L264
- [`get_column_as_series`](#calyx-sop-dashboard-v2-src-operations_view-py-get_column_as_series) — L267–L274
- [`find_column`](#calyx-sop-dashboard-v2-src-operations_view-py-find_column) — L277–L287
- [`get_df_hash`](#calyx-sop-dashboard-v2-src-operations_view-py-get_df_hash) — L290–L294
- [`align_forecast_periods`](#calyx-sop-dashboard-v2-src-operations_view-py-align_forecast_periods) — L539–L562
- [`generate_forecast`](#calyx-sop-dashboard-v2-src-operations_view-py-generate_forecast) — L565–L607
- [`get_forecast_pivot_data`](#calyx-sop-dashboard-v2-src-operations_view-py-get_forecast_pivot_data) — L677–L708
- [`to_quarter`](#calyx-sop-dashboard-v2-src-operations_view-py-to_quarter) — L546–L554

### `calyx-sop-dashboard-v2/src/pareto_chart.py` (2 functions)

- [`calculate_pareto_data`](#calyx-sop-dashboard-v2-src-pareto_chart-py-calculate_pareto_data) — L304–L339
- [`get_pareto_insights`](#calyx-sop-dashboard-v2-src-pareto_chart-py-get_pareto_insights) — L437–L466

### `calyx-sop-dashboard-v2/src/po_forecast.py` (5 functions)

- [`safe_int`](#calyx-sop-dashboard-v2-src-po_forecast-py-safe_int) — L28–L42
- [`safe_float`](#calyx-sop-dashboard-v2-src-po_forecast-py-safe_float) — L45–L58
- [`safe_str`](#calyx-sop-dashboard-v2-src-po_forecast-py-safe_str) — L61–L65
- [`get_column_as_series`](#calyx-sop-dashboard-v2-src-po_forecast-py-get_column_as_series) — L68–L75
- [`find_column`](#calyx-sop-dashboard-v2-src-po_forecast-py-find_column) — L78–L88

### `calyx-sop-dashboard-v2/src/q1_revenue_snapshot.py` (6 functions)

- [`get_spreadsheet_id`](#calyx-sop-dashboard-v2-src-q1_revenue_snapshot-py-get_spreadsheet_id) — L27–L31
- [`clean_numeric`](#calyx-sop-dashboard-v2-src-q1_revenue_snapshot-py-clean_numeric) — L114–L122
- [`load_all_data`](#calyx-sop-dashboard-v2-src-q1_revenue_snapshot-py-load_all_data) — L124–L141
- [`process_invoices`](#calyx-sop-dashboard-v2-src-q1_revenue_snapshot-py-process_invoices) — L143–L225
- [`process_dashboard_info`](#calyx-sop-dashboard-v2-src-q1_revenue_snapshot-py-process_dashboard_info) — L227–L252
- [`get_medal`](#calyx-sop-dashboard-v2-src-q1_revenue_snapshot-py-get_medal) — L353–L357

### `calyx-sop-dashboard-v2/src/q2_revenue_snapshot.py` (41 functions)

- [`calculate_business_days_remaining`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-calculate_business_days_remaining) — L55–L79
- [`get_mst_time`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_mst_time) — L81–L86
- [`get_spillover_column`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_spillover_column) — L825–L837
- [`get_spillover_value`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_spillover_value) — L839–L846
- [`is_q2_deal`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-is_q2_deal) — L848–L870
- [`apply_q2_fulfillment_logic`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-apply_q2_fulfillment_logic) — L872–L939
- [`detect_changes`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-detect_changes) — L1558–L1621
- [`calculate_team_metrics`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-calculate_team_metrics) — L3483–L3532
- [`calculate_rep_metrics`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-calculate_rep_metrics) — L3713–L3899
- [`create_sexy_gauge`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-create_sexy_gauge) — L3903–L3939
- [`get_col_by_index`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_col_by_index) — L4165–L4169
- [`create_status_breakdown_chart`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-create_status_breakdown_chart) — L4258–L4308
- [`create_pipeline_breakdown_chart`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-create_pipeline_breakdown_chart) — L4310–L4382
- [`create_deals_timeline`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-create_deals_timeline) — L4384–L4467
- [`create_invoice_status_chart`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-create_invoice_status_chart) — L4469–L4504
- [`get_business_days_before`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_business_days_before) — L897–L908
- [`get_planning_status`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_planning_status) — L2159–L2171
- [`get_planning_notes`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_planning_notes) — L2173–L2181
- [`get_amount_override`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_amount_override) — L2211–L2215
- [`set_amount_override`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-set_amount_override) — L2217–L2220
- [`get_prod_sched`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_prod_sched) — L2236–L2241
- [`get_amie_update`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_amie_update) — L2253–L2257
- [`get_col_by_index`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_col_by_index) — L2262–L2265
- [`format_ns_view`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-format_ns_view) — L2378–L2457
- [`safe_sum`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-safe_sum) — L3019–L3032
- [`get_amount`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_amount) — L3679–L3686
- [`get_quarter`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_quarter) — L4407–L4415
- [`get_so_metrics`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_so_metrics) — L5553–L5629
- [`get_hs_metrics`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_hs_metrics) — L5632–L5686
- [`style_face_value`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-style_face_value) — L5890–L5918
- [`clean_numeric`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-clean_numeric) — L1114–L1121
- [`clean_numeric_so`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-clean_numeric_so) — L1452–L1460
- [`calculate_so_metrics`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-calculate_so_metrics) — L1698–L1736
- [`format_hs_view`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-format_hs_view) — L2499–L2526
- [`calculate_biz_days`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-calculate_biz_days) — L3147–L3157
- [`clean_numeric`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-clean_numeric) — L1173–L1180
- [`clean_numeric`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-clean_numeric) — L1252–L1259
- [`business_days_between`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-business_days_between) — L1510–L1514
- [`get_expect_amount`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_expect_amount) — L1866–L1878
- [`get_best_case_amount`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_best_case_amount) — L1887–L1899
- [`get_opportunity_amount`](#calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_opportunity_amount) — L1911–L1923

### `calyx-sop-dashboard-v2/src/q4_revenue_snapshot.py` (6 functions)

- [`get_spreadsheet_id`](#calyx-sop-dashboard-v2-src-q4_revenue_snapshot-py-get_spreadsheet_id) — L26–L30
- [`clean_numeric`](#calyx-sop-dashboard-v2-src-q4_revenue_snapshot-py-clean_numeric) — L100–L108
- [`load_all_data`](#calyx-sop-dashboard-v2-src-q4_revenue_snapshot-py-load_all_data) — L110–L127
- [`process_invoices`](#calyx-sop-dashboard-v2-src-q4_revenue_snapshot-py-process_invoices) — L129–L212
- [`process_dashboard_info`](#calyx-sop-dashboard-v2-src-q4_revenue_snapshot-py-process_dashboard_info) — L214–L240
- [`get_medal`](#calyx-sop-dashboard-v2-src-q4_revenue_snapshot-py-get_medal) — L340–L344

### `calyx-sop-dashboard-v2/src/sales_rep_view.py` (3 functions)

- [`clean_dataframe`](#calyx-sop-dashboard-v2-src-sales_rep_view-py-clean_dataframe) — L20–L26
- [`get_column_as_series`](#calyx-sop-dashboard-v2-src-sales_rep_view-py-get_column_as_series) — L29–L36
- [`find_column`](#calyx-sop-dashboard-v2-src-sales_rep_view-py-find_column) — L39–L49

### `calyx-sop-dashboard-v2/src/scenario_planning.py` (3 functions)

- [`generate_scenario_forecast`](#calyx-sop-dashboard-v2-src-scenario_planning-py-generate_scenario_forecast) — L330–L400
- [`create_pipeline_forecast`](#calyx-sop-dashboard-v2-src-scenario_planning-py-create_pipeline_forecast) — L403–L441
- [`load_scenario_forecast`](#calyx-sop-dashboard-v2-src-scenario_planning-py-load_scenario_forecast) — L576–L599

### `calyx-sop-dashboard-v2/src/sop_data_loader.py` (32 functions)

- [`get_spreadsheet_id`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-get_spreadsheet_id) — L71–L73
- [`load_sheet_to_dataframe`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-load_sheet_to_dataframe) — L80–L144
- [`load_invoice_lines`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-load_invoice_lines) — L152–L189
- [`load_sales_orders`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-load_sales_orders) — L193–L226
- [`load_items`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-load_items) — L230–L275
- [`load_stock_items`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-load_stock_items) — L279–L301
- [`load_customers`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-load_customers) — L305–L325
- [`load_deals`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-load_deals) — L329–L396
- [`load_inventory`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-load_inventory) — L400–L407
- [`load_vendors`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-load_vendors) — L411–L418
- [`load_invoices`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-load_invoices) — L422–L429
- [`load_so_lines`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-load_so_lines) — L433–L440
- [`load_all_sop_data`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-load_all_sop_data) — L448–L458
- [`get_unique_sales_reps`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-get_unique_sales_reps) — L465–L493
- [`get_customers_for_rep`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-get_customers_for_rep) — L496–L533
- [`get_skus_for_customer`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-get_skus_for_customer) — L536–L573
- [`get_unique_product_types`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-get_unique_product_types) — L576–L608
- [`get_unique_skus`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-get_unique_skus) — L611–L639
- [`prepare_demand_history`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-prepare_demand_history) — L642–L702
- [`prepare_revenue_history`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-prepare_revenue_history) — L705–L777
- [`get_all_worksheet_names`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-get_all_worksheet_names) — L784–L800
- [`parse_revenue_forecast`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-parse_revenue_forecast) — L857–L881
- [`parse_revenue_forecast_long_format`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-parse_revenue_forecast_long_format) — L884–L997
- [`parse_revenue_forecast_wide_format`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-parse_revenue_forecast_wide_format) — L1000–L1076
- [`calculate_item_asp_rolling12`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-calculate_item_asp_rolling12) — L1428–L1532
- [`allocate_topdown_forecast`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-allocate_topdown_forecast) — L1535–L1666
- [`get_revenue_forecast_by_period`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-get_revenue_forecast_by_period) — L1722–L1798
- [`get_pipeline_by_period`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-get_pipeline_by_period) — L1801–L1900
- [`calculate_lead_times`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-calculate_lead_times) — L1903–L1988
- [`safe_get_series`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-safe_get_series) — L1214–L1220
- [`safe_get_series`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-safe_get_series) — L1352–L1358
- [`safe_get_series`](#calyx-sop-dashboard-v2-src-sop_data_loader-py-safe_get_series) — L1472–L1478

### `calyx-sop-dashboard-v2/src/utils.py` (18 functions)

- [`setup_logging`](#calyx-sop-dashboard-v2-src-utils-py-setup_logging) — L17–L44
- [`export_dataframe`](#calyx-sop-dashboard-v2-src-utils-py-export_dataframe) — L47–L58
- [`export_to_excel`](#calyx-sop-dashboard-v2-src-utils-py-export_to_excel) — L61–L74
- [`format_currency`](#calyx-sop-dashboard-v2-src-utils-py-format_currency) — L77–L89
- [`format_number`](#calyx-sop-dashboard-v2-src-utils-py-format_number) — L92–L107
- [`format_percentage`](#calyx-sop-dashboard-v2-src-utils-py-format_percentage) — L110–L123
- [`safe_divide`](#calyx-sop-dashboard-v2-src-utils-py-safe_divide) — L126–L143
- [`get_date_range_string`](#calyx-sop-dashboard-v2-src-utils-py-get_date_range_string) — L146–L157
- [`create_metric_card_html`](#calyx-sop-dashboard-v2-src-utils-py-create_metric_card_html) — L160–L196
- [`validate_dataframe`](#calyx-sop-dashboard-v2-src-utils-py-validate_dataframe) — L199–L214
- [`clean_string_column`](#calyx-sop-dashboard-v2-src-utils-py-clean_string_column) — L217–L227
- [`calculate_growth_rate`](#calyx-sop-dashboard-v2-src-utils-py-calculate_growth_rate) — L230–L243
- [`get_color_scale`](#calyx-sop-dashboard-v2-src-utils-py-get_color_scale) — L246–L274
- [`truncate_string`](#calyx-sop-dashboard-v2-src-utils-py-truncate_string) — L277–L291
- [`__init__`](#calyx-sop-dashboard-v2-src-utils-py-__init__) — L297–L300
- [`__enter__`](#calyx-sop-dashboard-v2-src-utils-py-__enter__) — L302–L304
- [`__exit__`](#calyx-sop-dashboard-v2-src-utils-py-__exit__) — L306–L309
- [`elapsed`](#calyx-sop-dashboard-v2-src-utils-py-elapsed) — L312–L315

### `calyx-sop-dashboard-v2/src/yearly_planning_2026.py` (66 functions)

- [`fig_to_base64`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-fig_to_base64) — L51–L61
- [`fig_to_html_embed`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-fig_to_html_embed) — L64–L74
- [`create_monthly_revenue_chart`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-create_monthly_revenue_chart) — L77–L122
- [`create_order_type_chart`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-create_order_type_chart) — L177–L217
- [`create_pipeline_chart`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-create_pipeline_chart) — L220–L270
- [`clean_numeric`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-clean_numeric) — L3622–L3630
- [`load_sku_display_names`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-load_sku_display_names) — L3634–L3663
- [`load_raw_inventory`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-load_raw_inventory) — L3667–L3694
- [`get_inventory_for_skus`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-get_inventory_for_skus) — L3697–L3742
- [`load_qbr_data`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-load_qbr_data) — L3745–L4334
- [`get_rep_list`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-get_rep_list) — L4339–L4353
- [`get_customers_for_rep`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-get_customers_for_rep) — L4356–L4385
- [`get_customer_deals`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-get_customer_deals) — L4388–L4407
- [`_crm_extract_parent`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-_crm_extract_parent) — L4422–L4444
- [`_match_mso_parent`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-_match_mso_parent) — L4481–L4508
- [`_crm_normalize`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-_crm_normalize) — L4511–L4518
- [`build_parent_child_map`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-build_parent_child_map) — L4521–L4572
- [`resolve_account_customers`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-resolve_account_customers) — L4575–L4591
- [`build_rep_account_roster`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-build_rep_account_roster) — L4594–L4726
- [`build_child_breakdown`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-build_child_breakdown) — L4729–L4811
- [`extract_die_tool`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-extract_die_tool) — L5380–L5422
- [`categorize_product`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-categorize_product) — L5425–L5698
- [`apply_product_categories`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-apply_product_categories) — L5701–L5735
- [`rollup_dml_lids`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-rollup_dml_lids) — L5738–L5804
- [`create_unified_product_view`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-create_unified_product_view) — L5807–L5897
- [`compute_period_bounds`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-compute_period_bounds) — L7107–L7134
- [`compute_comparison_bounds`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-compute_comparison_bounds) — L7137–L7157
- [`_filter_df_by_date`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-_filter_df_by_date) — L7160–L7170
- [`compute_account_kpis`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-compute_account_kpis) — L7173–L7246
- [`build_customers_export_tuples`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-build_customers_export_tuples) — L7249–L7299
- [`_fmt_money`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-_fmt_money) — L7302–L7311
- [`_fmt_delta`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-_fmt_delta) — L7314–L7325
- [`_kpi_tile`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-_kpi_tile) — L7328–L7338
- [`generate_sku_order_history_xlsx`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-generate_sku_order_history_xlsx) — L8440–L8651
- [`generate_sku_order_history_text`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-generate_sku_order_history_text) — L9112–L9168
- [`process_deals_line_items`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-process_deals_line_items) — L10359–L10402
- [`categorize_sku_for_pipeline`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-categorize_sku_for_pipeline) — L10405–L10413
- [`filter_calyx_cure_skus`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-filter_calyx_cure_skus) — L11533–L11558
- [`identify_calyx_cure_sku`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-identify_calyx_cure_sku) — L11561–L11572
- [`calculate_cure_pipeline_metrics`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-calculate_cure_pipeline_metrics) — L11575–L11640
- [`calculate_cure_order_metrics`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-calculate_cure_order_metrics) — L11643–L11701
- [`calculate_cure_historical_demand`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-calculate_cure_historical_demand) — L11704–L11753
- [`parse_period_selection`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-parse_period_selection) — L13254–L13282
- [`calculate_period_metrics`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-calculate_period_metrics) — L13285–L13333
- [`embed_chart`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-embed_chart) — L303–L320
- [`get_customer_friendly_status`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-get_customer_friendly_status) — L958–L965
- [`get_customer_friendly_status`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-get_customer_friendly_status) — L5265–L5272
- [`get_unified_category`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-get_unified_category) — L5833–L5872
- [`get_parent_category`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-get_parent_category) — L5878–L5893
- [`status_indicator`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-status_indicator) — L6648–L6658
- [`_d`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-_d) — L7603–L7604
- [`filter_by_date`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-filter_by_date) — L9754–L9769
- [`apply_dml_pairing_for_forecast`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-apply_dml_pairing_for_forecast) — L13695–L13752
- [`filter_concentrate_bases_only`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-filter_concentrate_bases_only) — L13762–L13779
- [`aging_bucket`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-aging_bucket) — L2205–L2210
- [`aging_bucket`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-aging_bucket) — L4910–L4920
- [`categorize_frequency`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-categorize_frequency) — L6306–L6314
- [`pattern_indicator`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-pattern_indicator) — L6389–L6396
- [`extract_customer_from_ticket`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-extract_customer_from_ticket) — L4021–L4049
- [`extract_ncr_number_from_ticket`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-extract_ncr_number_from_ticket) — L4051–L4061
- [`match_customer`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-match_customer) — L4063–L4168
- [`categorize_hubspot_ncr`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-categorize_hubspot_ncr) — L4184–L4251
- [`get_qty_and_product_type`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-get_qty_and_product_type) — L4278–L4290
- [`normalize_for_matching`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-normalize_for_matching) — L4068–L4079
- [`extract_base_company`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-extract_base_company) — L4081–L4111
- [`try_match`](#calyx-sop-dashboard-v2-src-yearly_planning_2026-py-try_match) — L4113–L4134

---

## Functions

## calyx-sop-dashboard-v2/app.py

### <a id="calyx-sop-dashboard-v2-app-py-get_mst_time"></a> `get_mst_time` — L105–L107

```python
def get_mst_time():
    """Get current time in Mountain Standard Time"""
    return datetime.now(ZoneInfo("America/Denver"))
```

### <a id="calyx-sop-dashboard-v2-app-py-main"></a> `main` — L818–L837

```python
def main():
    """Main application entry point."""
    inject_custom_css()
    section = render_sidebar()
    
    # Map the navigation options
    if section == "📈 Q2 Revenue Snapshot":
        render_q2_revenue_section()
    elif section == "🎯 Q1 2026 Review":
        render_q1_revenue_section()
    elif section == "📊 S&OP Planning":
        render_sop_section()
    elif section == "🛡️ Quality Management":
        render_quality_section_wrapper()
    elif section == "📉 Q4 Revenue Snapshot":
        render_q4_revenue_section()
    elif section == "📅 2026 Yearly Planning":
        render_2026_yearly_planning_section()
    elif section == "🎮 Revenue Operations Playground":
        render_rev_ops_playground_section()
```

## calyx-sop-dashboard-v2/src/Rev_Ops_Playground.py

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-fig_to_base64"></a> `fig_to_base64` — L52–L62

```python
def fig_to_base64(fig, width=700, height=350):
    """Convert a plotly figure to base64 PNG for embedding in HTML"""
    if not KALEIDO_AVAILABLE:
        return None
    try:
        img_bytes = fig.to_image(format="png", width=width, height=height, scale=2)
        return base64.b64encode(img_bytes).decode()
    except Exception as e:
        # Log the error for debugging
        print(f"Chart export error: {e}")
        return None
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-fig_to_html_embed"></a> `fig_to_html_embed` — L65–L75

```python
def fig_to_html_embed(fig, height=400):
    """Convert a plotly figure to embedded HTML (fallback when kaleido unavailable)"""
    try:
        return fig.to_html(
            include_plotlyjs='cdn',
            full_html=False,
            config={'displayModeBar': False, 'staticPlot': True},
            default_height=height
        )
    except Exception as e:
        return None
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-create_monthly_revenue_chart"></a> `create_monthly_revenue_chart` — L78–L123

```python
def create_monthly_revenue_chart(customer_invoices):
    """Create monthly revenue bar chart for PDF export"""
    if customer_invoices.empty or 'Date' not in customer_invoices.columns:
        return None
    
    invoices = customer_invoices.copy()
    invoices['Year'] = invoices['Date'].dt.year
    current_year = datetime.now().year
    recent = invoices[invoices['Year'] >= current_year - 1].copy()
    
    if recent.empty or len(recent) < 2:
        return None
    
    recent['Month'] = recent['Date'].dt.to_period('M').astype(str)
    monthly = recent.groupby('Month')['Amount'].sum().reset_index()
    
    fig = go.Figure(data=[
        go.Bar(
            x=monthly['Month'],
            y=monthly['Amount'],
            marker=dict(color='#3b82f6'),
            text=[f'${x:,.0f}' for x in monthly['Amount']],
            textposition='outside',
            textfont=dict(size=10),
            cliponaxis=False
        )
    ])
    
    # Calculate y-axis max to give room for labels
    max_val = monthly['Amount'].max()
    y_max = max_val * 1.15  # Add 15% headroom
    
    fig.update_layout(
        title=dict(text='Monthly Purchase Trend', font=dict(size=16, color='#1e293b')),
        xaxis_title='',
        yaxis_title='Purchases',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#1e293b', size=11),
        xaxis=dict(tickangle=-45, gridcolor='#e2e8f0'),
        yaxis=dict(gridcolor='#e2e8f0', tickformat='$,.0f', range=[0, y_max]),
        margin=dict(t=60, b=80, l=80, r=40),
        showlegend=False
    )
    
    return fig
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-create_order_type_chart"></a> `create_order_type_chart` — L178–L218

```python
def create_order_type_chart(customer_orders):
    """Create order type mix pie chart for PDF export"""
    if customer_orders.empty or 'Order Type' not in customer_orders.columns:
        return None
    
    valid = customer_orders[
        (customer_orders['Order Type'].notna()) &
        (customer_orders['Order Type'] != '') &
        (customer_orders['Order Type'] != 'nan')
    ]
    
    if valid.empty:
        return None
    
    type_mix = valid.groupby('Order Type')['Amount'].sum().reset_index()
    type_mix = type_mix.sort_values('Amount', ascending=False)
    
    colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4', '#ec4899', '#84cc16']
    
    fig = go.Figure(data=[go.Pie(
        labels=type_mix['Order Type'],
        values=type_mix['Amount'],
        hole=0.4,
        marker=dict(colors=colors[:len(type_mix)]),
        textposition='inside',
        textinfo='percent+label',
        textfont=dict(size=10, color='white'),
        hovertemplate='<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title=dict(text='Product Mix', font=dict(size=16, color='#1e293b')),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#1e293b'),
        showlegend=True,
        legend=dict(orientation='h', yanchor='top', y=-0.1, xanchor='center', x=0.5, font=dict(size=10)),
        margin=dict(t=50, b=80, l=20, r=20)
    )
    
    return fig
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-create_pipeline_chart"></a> `create_pipeline_chart` — L221–L271

```python
def create_pipeline_chart(customer_deals):
    """Create pipeline breakdown chart for PDF export"""
    if customer_deals.empty:
        return None
    
    open_statuses = ['Expect', 'Commit', 'Best Case', 'Opportunity']
    open_deals = customer_deals[customer_deals['Close Status'].isin(open_statuses)]
    
    if open_deals.empty:
        return None
    
    status_data = open_deals.groupby('Close Status')['Amount'].sum().reset_index()
    
    # Order by pipeline stage
    status_order = {'Commit': 0, 'Expect': 1, 'Best Case': 2, 'Opportunity': 3}
    status_data['Order'] = status_data['Close Status'].map(status_order).fillna(4)
    status_data = status_data.sort_values('Order')
    
    colors = {'Commit': '#10b981', 'Expect': '#3b82f6', 'Best Case': '#f59e0b', 'Opportunity': '#8b5cf6'}
    bar_colors = [colors.get(s, '#64748b') for s in status_data['Close Status']]
    
    fig = go.Figure(data=[
        go.Bar(
            x=status_data['Close Status'],
            y=status_data['Amount'],
            marker=dict(color=bar_colors),
            text=[f'${x:,.0f}' for x in status_data['Amount']],
            textposition='outside',
            textfont=dict(size=11),
            cliponaxis=False
        )
    ])
    
    # Calculate y-axis max to give room for labels
    max_val = status_data['Amount'].max()
    y_max = max_val * 1.15  # Add 15% headroom
    
    fig.update_layout(
        title=dict(text='Upcoming Orders by Status', font=dict(size=16, color='#1e293b')),
        xaxis_title='',
        yaxis_title='Value',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#1e293b', size=11),
        xaxis=dict(gridcolor='#e2e8f0'),
        yaxis=dict(gridcolor='#e2e8f0', tickformat='$,.0f', range=[0, y_max]),
        margin=dict(t=60, b=50, l=80, r=40),
        showlegend=False
    )
    
    return fig
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-clean_numeric"></a> `clean_numeric` — L3427–L3435

```python
def clean_numeric(value):
    """Clean and convert a value to numeric"""
    if pd.isna(value) or str(value).strip() == '':
        return 0
    cleaned = str(value).replace(',', '').replace('$', '').replace(' ', '').strip()
    try:
        return float(cleaned)
    except:
        return 0
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-load_qbr_data"></a> `load_qbr_data` — L3438–L4027

```python
def load_qbr_data():
    """Load all data needed for QBR generation"""
    
    # Load Sales Orders (A:AG to include all columns through Updated Status)
    sales_orders_df = load_google_sheets_data("_NS_SalesOrders_Data", "A:AG", version=CACHE_VERSION)
    
    # Load Invoices (A:U to include Rep Master)
    invoices_df = load_google_sheets_data("_NS_Invoices_Data", "A:U", version=CACHE_VERSION)
    
    # Load HubSpot Deals - load wider range to ensure we get Company Name
    deals_df = load_google_sheets_data("All Reps All Pipelines", "A:Z", version=CACHE_VERSION)
    
    # =========================================================================
    # PROCESS SALES ORDERS - use column names directly from sheet
    # =========================================================================
    if not sales_orders_df.empty:
        # Remove duplicate columns
        if sales_orders_df.columns.duplicated().any():
            sales_orders_df = sales_orders_df.loc[:, ~sales_orders_df.columns.duplicated()]
        
        # Handle Amount column - could be 'Amount' or 'Amount (Transaction Total)'
        if 'Amount (Transaction Total)' in sales_orders_df.columns and 'Amount' not in sales_orders_df.columns:
            sales_orders_df = sales_orders_df.rename(columns={'Amount (Transaction Total)': 'Amount'})
        
        # Clean numeric data
        if 'Amount' in sales_orders_df.columns:
            sales_orders_df['Amount'] = sales_orders_df['Amount'].apply(clean_numeric)
        
        # Clean date data
        if 'Order Start Date' in sales_orders_df.columns:
            sales_orders_df['Order Start Date'] = pd.to_datetime(sales_orders_df['Order Start Date'], errors='coerce')
        if 'Actual Ship Date' in sales_orders_df.columns:
            sales_orders_df['Actual Ship Date'] = pd.to_datetime(sales_orders_df['Actual Ship Date'], errors='coerce')
        if 'Customer Promise Date' in sales_orders_df.columns:
            sales_orders_df['Customer Promise Date'] = pd.to_datetime(sales_orders_df['Customer Promise Date'], errors='coerce')
        # Also handle alternate column name
        if 'Customer Promise Last Date to Ship' in sales_orders_df.columns:
            sales_orders_df['Customer Promise Date'] = pd.to_datetime(sales_orders_df['Customer Promise Last Date to Ship'], errors='coerce')
        
        # Clean text fields
        for col in ['Corrected Customer Name', 'Rep Master', 'Updated Status', 'Order Type', 'Status']:
            if col in sales_orders_df.columns:
                sales_orders_df[col] = sales_orders_df[col].astype(str).str.strip()
    
    # =========================================================================
    # PROCESS INVOICES - use column names directly from sheet
    # =========================================================================
    if not invoices_df.empty:
        # Remove duplicate columns
        if invoices_df.columns.duplicated().any():
            invoices_df = invoices_df.loc[:, ~invoices_df.columns.duplicated()]
        
        # Handle Amount column - could be 'Amount' or 'Amount (Transaction Total)'
        if 'Amount (Transaction Total)' in invoices_df.columns and 'Amount' not in invoices_df.columns:
            invoices_df = invoices_df.rename(columns={'Amount (Transaction Total)': 'Amount'})
        
        # Clean numeric data
        if 'Amount' in invoices_df.columns:
            invoices_df['Amount'] = invoices_df['Amount'].apply(clean_numeric)
        if 'Amount Remaining' in invoices_df.columns:
            invoices_df['Amount Remaining'] = invoices_df['Amount Remaining'].apply(clean_numeric)
        
        # Clean date data
        if 'Date' in invoices_df.columns:
            invoices_df['Date'] = pd.to_datetime(invoices_df['Date'], errors='coerce')
        if 'Due Date' in invoices_df.columns:
            invoices_df['Due Date'] = pd.to_datetime(invoices_df['Due Date'], errors='coerce')
        
        # Clean text fields
        for col in ['Corrected Customer', 'Rep Master', 'Status']:
            if col in invoices_df.columns:
                invoices_df[col] = invoices_df[col].astype(str).str.strip()
        
        # Extract SO Number from Created From
        if 'Created From' in invoices_df.columns:
            invoices_df['SO Number'] = invoices_df['Created From'].astype(str).str.replace('Sales Order #', '', regex=False).str.strip()
    
    # =========================================================================
    # PROCESS HUBSPOT DEALS
    # Use actual column names from header row, not positional indices
    # =========================================================================
    if not deals_df.empty:
        # Create a mapping of potential column name variations to standard names
        column_mapping = {
            # Standard name variations
            'Record ID': 'Record ID',
            'Deal Name': 'Deal Name',
            'Deal Stage': 'Deal Stage',
            'Close Date': 'Close Date',
            'Deal Owner First Name': 'Deal Owner First Name',
            'Deal Owner Last Name': 'Deal Owner Last Name',
            'Deal Owner First Name Deal Owner Last Name': 'Deal Owner Combined',
            'Amount': 'Amount',
            'Close Status': 'Close Status',
            'Pipeline': 'Pipeline',
            'Create Date': 'Create Date',
            'Deal Type': 'Deal Type',
            'Netsuite SO#': 'Netsuite SO#',
            'Netsuite SO Link': 'Netsuite SO Link',
            'New Design SKU': 'New Design SKU',
            'SKU': 'SKU',
            'Netsuite Sales Order Number': 'Netsuite Sales Order Number',
            'Primary Associated Company': 'Primary Associated Company',
            'Average Leadtime': 'Average Leadtime',
            'Pending Approval Date': 'Pending Approval Date',
            'Quarter': 'Quarter',
            'Deal Stage & Close Status': 'Deal Stage & Close Status',
            'Probability': 'Probability',
            'Probability Rev': 'Probability Rev',
            'Company Name': 'Company Name',
        }
        
        # Apply any mapping if column names match
        rename_dict = {}
        for col in deals_df.columns:
            col_stripped = str(col).strip()
            if col_stripped in column_mapping:
                rename_dict[col] = column_mapping[col_stripped]
        
        if rename_dict:
            deals_df = deals_df.rename(columns=rename_dict)
        
        # Remove duplicate columns
        if deals_df.columns.duplicated().any():
            deals_df = deals_df.loc[:, ~deals_df.columns.duplicated()]
        
        # Create Deal Owner by combining First Name + Last Name if separate columns exist
        if 'Deal Owner First Name' in deals_df.columns and 'Deal Owner Last Name' in deals_df.columns:
            deals_df['Deal Owner'] = (
                deals_df['Deal Owner First Name'].fillna('').astype(str).str.strip() + ' ' + 
                deals_df['Deal Owner Last Name'].fillna('').astype(str).str.strip()
            ).str.strip()
        elif 'Deal Owner Combined' in deals_df.columns:
            deals_df['Deal Owner'] = deals_df['Deal Owner Combined'].astype(str).str.strip()
        
        # Clean numeric data
        if 'Amount' in deals_df.columns:
            deals_df['Amount'] = deals_df['Amount'].apply(clean_numeric)
        if 'Probability Rev' in deals_df.columns:
            deals_df['Probability Rev'] = deals_df['Probability Rev'].apply(clean_numeric)
        else:
            deals_df['Probability Rev'] = deals_df.get('Amount', 0)
        
        # Clean date data
        if 'Close Date' in deals_df.columns:
            deals_df['Close Date'] = pd.to_datetime(deals_df['Close Date'], errors='coerce')
        if 'Pending Approval Date' in deals_df.columns:
            deals_df['Pending Approval Date'] = pd.to_datetime(deals_df['Pending Approval Date'], errors='coerce')
        
        # Clean text fields - strip whitespace AND newlines
        for col in ['Deal Owner', 'Deal Name', 'Close Status', 'Company Name', 'Primary Associated Company']:
            if col in deals_df.columns:
                deals_df[col] = deals_df[col].astype(str).str.strip().str.replace('\n', '', regex=False).str.replace('\r', '', regex=False)
        
        # FALLBACK: If Company Name doesn't exist, try to use Primary Associated Company
        if 'Company Name' not in deals_df.columns and 'Primary Associated Company' in deals_df.columns:
            deals_df['Company Name'] = deals_df['Primary Associated Company']
    
    # =========================================================================
    # LOAD AND PROCESS INVOICE LINE ITEMS
    # This is the drill-down layer explaining realized revenue composition
    # =========================================================================
    invoice_line_items_df = load_google_sheets_data("Invoice Line Item", "A:Z", version=CACHE_VERSION, silent=True)
    
    if not invoice_line_items_df.empty:
        # Remove duplicate columns
        if invoice_line_items_df.columns.duplicated().any():
            invoice_line_items_df = invoice_line_items_df.loc[:, ~invoice_line_items_df.columns.duplicated()]
        
        # Clean numeric data - Amount is line-level revenue
        if 'Amount' in invoice_line_items_df.columns:
            invoice_line_items_df['Amount'] = invoice_line_items_df['Amount'].apply(clean_numeric)
        
        # Quantity is unit-level volume
        if 'Quantity' in invoice_line_items_df.columns:
            invoice_line_items_df['Quantity'] = invoice_line_items_df['Quantity'].apply(clean_numeric)
        
        # Clean date data
        if 'Date' in invoice_line_items_df.columns:
            invoice_line_items_df['Date'] = pd.to_datetime(invoice_line_items_df['Date'], errors='coerce')
        if 'Due Date' in invoice_line_items_df.columns:
            invoice_line_items_df['Due Date'] = pd.to_datetime(invoice_line_items_df['Due Date'], errors='coerce')
        
        # Clean text fields - use Correct Customer and Rep Master as authoritative
        for col in ['Correct Customer', 'Rep Master', 'Status', 'Item', 'Item Description', 
                    'Calyx | Item Type', 'Calyx || Product Type']:
            if col in invoice_line_items_df.columns:
                invoice_line_items_df[col] = invoice_line_items_df[col].astype(str).str.strip()
                # Replace 'nan' strings with empty
                invoice_line_items_df[col] = invoice_line_items_df[col].replace('nan', '')
    
    # =========================================================================
    # LOAD AND PROCESS NCR (NON-CONFORMANCE) DATA
    # Used to track quality issues by customer
    # NetSuite NCR = source of truth from November 2024 onwards
    # HubSpot NCR = historical data before November 2024
    # =========================================================================
    
    # --- NetSuite NCR Data (Nov 2024+) ---
    ncr_df = pd.DataFrame()  # Initialize as empty
    ncr_raw = load_google_sheets_data("Non-Conformance Details", "A:W", version=CACHE_VERSION, silent=True)
    
    if not ncr_raw.empty:
        ncr_df = ncr_raw.copy()
        # Remove duplicate columns
        if ncr_df.columns.duplicated().any():
            ncr_df = ncr_df.loc[:, ~ncr_df.columns.duplicated()]
        
        # Clean text fields
        # Column mappings based on user spec:
        # F = Sales Order, I = Issue Type, P = Total Quantity Affected, V = Corrected Customer Name
        for col in ['Sales Order', 'Issue Type', 'Corrected Customer Name', 'Status', 
                    'Defect Summary', 'Priority', 'External Or Internal', 'NC Number']:
            if col in ncr_df.columns:
                ncr_df[col] = ncr_df[col].astype(str).str.strip()
                ncr_df[col] = ncr_df[col].replace('nan', '')
        
        # Clean numeric data - Total Quantity Affected
        if 'Total Quantity Affected' in ncr_df.columns:
            ncr_df['Total Quantity Affected'] = ncr_df['Total Quantity Affected'].apply(clean_numeric)
        
        # Clean Cost fields if present
        if 'Cost of Rework' in ncr_df.columns:
            ncr_df['Cost of Rework'] = ncr_df['Cost of Rework'].apply(clean_numeric)
        if 'Cost Avoided' in ncr_df.columns:
            ncr_df['Cost Avoided'] = ncr_df['Cost Avoided'].apply(clean_numeric)
        
        # Clean date data
        if 'Date Submitted' in ncr_df.columns:
            ncr_df['Date Submitted'] = pd.to_datetime(ncr_df['Date Submitted'], errors='coerce')
        if 'On Time Ship Date' in ncr_df.columns:
            ncr_df['On Time Ship Date'] = pd.to_datetime(ncr_df['On Time Ship Date'], errors='coerce')
        
        # Add source indicator
        ncr_df['NCR Source'] = 'NetSuite'
        
        # Standardize column for matching
        ncr_df['Matched Customer'] = ncr_df.get('Corrected Customer Name', '')
    
    # --- HubSpot NCR Data (Historical, pre-Nov 2024) ---
    hb_ncr_df = pd.DataFrame()  # Initialize as empty
    hb_ncr_raw = load_google_sheets_data("HB NCR", "A2:O", version=CACHE_VERSION, silent=True)
    
    if not hb_ncr_raw.empty:
        hb_ncr_df = hb_ncr_raw.copy()
        # Remove duplicate columns
        if hb_ncr_df.columns.duplicated().any():
            hb_ncr_df = hb_ncr_df.loc[:, ~hb_ncr_df.columns.duplicated()]
        
        # Filter to Customer NCR Pipeline only
        if 'Pipeline' in hb_ncr_df.columns:
            hb_ncr_df = hb_ncr_df[hb_ncr_df['Pipeline'].str.strip() == 'Customer NCR Pipeline'].copy()
        
        if not hb_ncr_df.empty:
            # Clean text fields
            for col in ['Ticket ID', 'Ticket name', 'Ticket status', 'Pipeline', 
                        'Ticket description', 'Company Name', 'Company Name 2']:
                if col in hb_ncr_df.columns:
                    hb_ncr_df[col] = hb_ncr_df[col].astype(str).str.strip()
                    hb_ncr_df[col] = hb_ncr_df[col].replace('nan', '')
            
            # Clean date data
            if 'Create date' in hb_ncr_df.columns:
                hb_ncr_df['Create date'] = pd.to_datetime(hb_ncr_df['Create date'], errors='coerce')
            if 'Close date' in hb_ncr_df.columns:
                hb_ncr_df['Close date'] = pd.to_datetime(hb_ncr_df['Close date'], errors='coerce')
            
            # Calculate resolution time (days to close)
            if 'Create date' in hb_ncr_df.columns and 'Close date' in hb_ncr_df.columns:
                hb_ncr_df['Resolution Days'] = (hb_ncr_df['Close date'] - hb_ncr_df['Create date']).dt.days
            
            # --- Customer Matching Logic ---
            # Priority 1: Company Name 2 (exact match, same naming convention)
            # Priority 2: Company Name (fuzzy match)
            # Priority 3: Extract from Ticket name (format "NCR600 - Customer Name")
            
            def extract_customer_from_ticket(ticket_name):
                """Extract customer name from ticket formats:
                - 'NCR ### - Customer Name' (with dash)
                - 'NCR ### Customer Name' (no dash)
                - Also extracts NCR number for reference
                """
                import re
                if not ticket_name or ticket_name == '' or pd.isna(ticket_name):
                    return ''
                
                ticket_str = str(ticket_name).strip()
                
                # Pattern 1: "NCR ### - Customer Name" (with dash)
                if ' - ' in ticket_str:
                    parts = ticket_str.split(' - ', 1)
                    if len(parts) > 1:
                        customer_part = parts[1].strip()
                        # Remove any trailing issue description (after another dash or parenthetical)
                        # e.g., "Acreage (OH) Smearing" -> "Acreage (OH)"
                        return customer_part
                
                # Pattern 2: "NCR ### Customer Name" (no dash)
                # Match NCR followed by number, then capture everything after
                ncr_match = re.match(r'NCR\s*(\d+)\s+(.+)', ticket_str, re.IGNORECASE)
                if ncr_match:
                    customer_part = ncr_match.group(2).strip()
                    return customer_part
                
                return ''
            
            def extract_ncr_number_from_ticket(ticket_name):
                """Extract NCR number from ticket name"""
                import re
                if not ticket_name or ticket_name == '' or pd.isna(ticket_name):
                    return None
                
                ticket_str = str(ticket_name).strip()
                ncr_match = re.search(r'NCR\s*(\d+)', ticket_str, re.IGNORECASE)
                if ncr_match:
                    return ncr_match.group(1)
                return None
            
            def match_customer(row, valid_customers):
                """Match customer using priority logic with fuzzy matching"""
                from difflib import get_close_matches
                import re
                
                def normalize_for_matching(name):
                    """Normalize customer name for better matching"""
                    if not name:
                        return ''
                    name = str(name).strip()
                    # Remove common state abbreviations at the end (NY, MA, OH, NJ, PA, IL, etc.)
                    name = re.sub(r'\s+(NY|MA|OH|NJ|PA|IL|CA|CO|FL|TX|WA|OR|AZ|NV|MI|NC|SC|GA|VA|MD|CT|RI|NH|VT|ME|DE|WV|KY|TN|AL|MS|LA|AR|MO|IA|MN|WI|IN|OK|KS|NE|SD|ND|MT|WY|ID|UT|NM|HI|AK|DC)$', '', name, flags=re.IGNORECASE)
                    # Remove parenthetical state codes like (OH), (NY)
                    name = re.sub(r'\s*\([A-Z]{2}\)\s*', ' ', name)
                    # Remove trailing description words
                    name = re.sub(r'\s+(Smearing|Defect|Issue|Problem|Damage|Error).*$', '', name, flags=re.IGNORECASE)
                    return name.strip()
                
                def extract_base_company(company_name):
                    """Extract base company name from various formats:
                    - 'Parent : Child' format -> 'Parent'
                    - 'Acreage Holdings:  New York (NY)' -> 'Acreage Holdings'
                    - 'Acreage Holdings - Massachusetts (MA)' -> 'Acreage Holdings'
                    """
                    if not company_name or pd.isna(company_name):
                        return ''
                    name = str(company_name).strip()
                    
                    # Pattern 1: 'Parent : Child' - take the first part (HubSpot Company Name 2 format)
                    if ' : ' in name:
                        return name.split(' : ')[0].strip()
                    
                    # Pattern 2: 'Company:  Location (STATE)' - take before first colon
                    if ':' in name:
                        base = name.split(':')[0].strip()
                        # Only use if it looks like a company name (not a URL)
                        if '.' not in base and len(base) > 3:
                            return base
                    
                    # Pattern 3: 'Company - Location (STATE)' - take before dash if state follows
                    if ' - ' in name:
                        parts = name.split(' - ')
                        if len(parts) >= 2:
                            # Check if second part looks like a state/location
                            second = parts[1].strip()
                            if re.search(r'(Massachusetts|New York|Ohio|Pennsylvania|Illinois|New Jersey|Connecticut|Michigan|Florida|California|Colorado|Texas|Washington|Oregon|Arizona|Nevada|North Carolina|South Carolina|Georgia|Virginia|Maryland|NY|MA|OH|PA|IL|NJ|CT|MI|FL|CA|CO|TX|WA|OR|AZ|NV|NC|SC|GA|VA|MD)', second, re.IGNORECASE):
                                return parts[0].strip()
                    
                    return name
                
                def try_match(name, customers, cutoff=0.7):
                    """Try to match a name against valid customers"""
                    if not name:
                        return None
                    # Exact match first
                    if name in customers:
                        return name
                    # Normalized exact match
                    normalized = normalize_for_matching(name)
                    for cust in customers:
                        if normalize_for_matching(cust) == normalized:
                            return cust
                    # Fuzzy match
                    matches = get_close_matches(name, customers, n=1, cutoff=cutoff)
                    if matches:
                        return matches[0]
                    # Fuzzy match on normalized
                    if normalized != name:
                        matches = get_close_matches(normalized, customers, n=1, cutoff=cutoff)
                        if matches:
                            return matches[0]
                    return None
                
                # Priority 1: Company Name 2 - extract base and match
                company_name_2 = row.get('Company Name 2', '')
                if company_name_2 and company_name_2 != '' and not pd.isna(company_name_2):
                    # Extract base company name (before " : " if present)
                    base_name = extract_base_company(company_name_2)
                    if base_name:
                        match = try_match(base_name, valid_customers, cutoff=0.8)
                        if match:
                            return match
                
                # Priority 2: Company Name (try exact first, then fuzzy)
                company_name = row.get('Company Name', '')
                if company_name and company_name != '' and not pd.isna(company_name):
                    # Also extract base company from Company Name if it has " : " format
                    base_name = extract_base_company(company_name)
                    match = try_match(base_name if base_name else company_name, valid_customers, cutoff=0.7)
                    if match:
                        return match
                    # Try the raw company name with state stripped
                    normalized = normalize_for_matching(company_name)
                    match = try_match(normalized, valid_customers, cutoff=0.6)
                    if match:
                        return match
                
                # Priority 3: Extract from Ticket name and fuzzy match
                ticket_name = row.get('Ticket name', '')
                extracted = extract_customer_from_ticket(ticket_name)
                if extracted:
                    match = try_match(extracted, valid_customers, cutoff=0.5)
                    if match:
                        return match
                
                return ''  # No match found
            
            # Get list of valid customers for fuzzy matching
            valid_customers = set()
            if not sales_orders_df.empty and 'Corrected Customer Name' in sales_orders_df.columns:
                valid_customers.update(sales_orders_df['Corrected Customer Name'].dropna().unique())
            if not invoices_df.empty and 'Corrected Customer' in invoices_df.columns:
                valid_customers.update(invoices_df['Corrected Customer'].dropna().unique())
            valid_customers = [c for c in valid_customers if c and c not in ['', 'nan', 'None', '#N/A']]
            
            # Apply customer matching
            hb_ncr_df['Matched Customer'] = hb_ncr_df.apply(
                lambda row: match_customer(row, valid_customers), axis=1
            )
            
            # --- Categorize HubSpot NCRs based on description ---
            def categorize_hubspot_ncr(description):
                """Categorize HubSpot NCR based on ticket description to match NetSuite Issue Types"""
                if not description or description == '' or pd.isna(description):
                    return 'Defective Product'
                
                desc_lower = str(description).lower()
                
                # Damaged in Transit - carrier damage, broken in shipping
                if any(kw in desc_lower for kw in ['damaged', 'broken', 'crushed', 'fedex damaged', 
                                                    'ups damaged', 'transit', 'carrier', 'pallet.*damage']):
                    return 'Damaged in Transit'
                
                # Shipped to Wrong Address - misshipments, swapped orders
                if any(kw in desc_lower for kw in ['wrong address', 'misshipped', 'swapped', 
                                                    'wrong location', 'delivered to wrong']):
                    return 'Shipped to Wrong Address'
                
                # Missing Labels Wrong Qty - shortages
                if any(kw in desc_lower for kw in ['short', 'missing', 'shorted', 'only received',
                                                    'ran short', 'labels short']):
                    return 'Missing Labels Wrong Qty'
                
                # Order Entry Error - system/data entry issues, customer ordered wrong
                if any(kw in desc_lower for kw in ['hubspot', 'netsuite', 'set up incorrectly', 
                                                    'entered into', 'system switched',
                                                    'customer ordered wrong', 'mistakenly ordered',
                                                    'accidentally placed', 'customer error',
                                                    'deal & so was reflective of the wrong',
                                                    'proofing queue']):
                    return 'Order Entry Error'
                
                # Wrong Material - wrong product shipped (includes wrong color/size)
                if any(kw in desc_lower for kw in ['wrong color', 'wrong size', 'wrong finish',
                                                    'received white instead', 'received black instead', 
                                                    'instead of', '25d instead', '15d instead', 
                                                    '7ml instead', '45d instead', '4ml instead',
                                                    'wrong sku', 'wrong product', 'mislabeled box',
                                                    'shipped black instead', 'shipped white instead',
                                                    'wrong core', 'not the artwork']):
                    return 'Wrong Material'
                
                # Incorrect Color - specifically color-related manufacturing issues
                if any(kw in desc_lower for kw in ['grey caps', 'marbling', 'translucent',
                                                    'color.*mixed', 'pigment']):
                    return 'Incorrect Color'
                
                # Artwork/Print/Label defects
                if any(kw in desc_lower for kw in ['print', 'artwork', 'off center', 'embossing',
                                                    'cut off', 'varnish', 'laminate', 'tactile',
                                                    'telescoping', 'backing.*rip', 'paper backing',
                                                    'poor print', 'skipout']):
                    return 'Artwork Error'
                
                # Defective Product - manufacturing defects, contamination, fit issues
                if any(kw in desc_lower for kw in ['warped', 'warping', 'defect', 'grease', 
                                                    'debris', 'contaminated', 'filth', 'insect', 
                                                    'hair', 'doesn\'t fit', 'not sealing', 'leaking',
                                                    'cracked', 'irregular', 'lid.*fit', 'snapping',
                                                    'boxes not forming', 'not in.*bag']):
                    return 'Defective Product'
                
                # Customer Returns (not defect-related)
                if any(kw in desc_lower for kw in ['customer return', 'return', 'exchange',
                                                    'would like to replace', 'swap out']):
                    return 'Order Entry Error'
                
                # Default fallback
                return 'Defective Product'
            
            # Map HubSpot columns to standardized NCR columns
            # Extract NCR number from ticket name (e.g., "NCR 988 Acreage NY" → "NCR-988")
            if 'Ticket name' in hb_ncr_df.columns:
                hb_ncr_df['NC Number'] = hb_ncr_df['Ticket name'].apply(
                    lambda x: f"NCR-{extract_ncr_number_from_ticket(x)}" if extract_ncr_number_from_ticket(x) else str(x)[:30]
                )
            else:
                hb_ncr_df['NC Number'] = hb_ncr_df.get('Ticket ID', '').apply(lambda x: f"HB-{x}" if x else '')
            hb_ncr_df['Date Submitted'] = hb_ncr_df.get('Create date', pd.NaT)
            hb_ncr_df['Status'] = hb_ncr_df.get('Ticket status', '')
            hb_ncr_df['Defect Summary'] = hb_ncr_df.get('Ticket description', '')
            
            # Categorize based on description - matching NetSuite Issue Types
            hb_ncr_df['Issue Type'] = hb_ncr_df['Defect Summary'].apply(categorize_hubspot_ncr)
            
            # Calculate Total Quantity Affected from QTY columns and determine Product Type
            # Priority order: Boxes → Containers → Flexpack → Labels → General QTY
            qty_columns = [
                ('QTY of boxes effected', 'Boxes'),
                ('QTY of containers effected', 'Containers'),
                ('Flexpack QTY Effected', 'Flexpack'),
                ('QTY of labels effected', 'Labels'),
                ('QTY Effected', 'General')
            ]
            
            def get_qty_and_product_type(row):
                """Get quantity affected and product type from first non-empty QTY column"""
                for col_name, product_type in qty_columns:
                    if col_name in row.index:
                        val = row[col_name]
                        if pd.notna(val) and str(val).strip() not in ['', 'nan', '0']:
                            try:
                                qty = float(str(val).replace(',', '').strip())
                                if qty > 0:
                                    return qty, product_type
                            except (ValueError, TypeError):
                                continue
                return 0, 'Unknown'
            
            # Apply to get both quantity and product type
            qty_product = hb_ncr_df.apply(get_qty_and_product_type, axis=1)
            hb_ncr_df['Total Quantity Affected'] = qty_product.apply(lambda x: x[0])
            hb_ncr_df['Product Type Affected'] = qty_product.apply(lambda x: x[1])
            hb_ncr_df['NCR Source'] = 'HubSpot'
            hb_ncr_df['Close Date'] = hb_ncr_df.get('Close date', pd.NaT)
    
    # --- Combine NCR Data ---
    # Columns to keep for combined dataframe
    ncr_columns = ['NC Number', 'Date Submitted', 'Status', 'Issue Type', 'Defect Summary',
                   'Total Quantity Affected', 'Matched Customer', 'NCR Source', 'Sales Order']
    
    combined_ncr_df = pd.DataFrame()
    
    if not ncr_df.empty:
        # Ensure Sales Order column exists
        if 'Sales Order' not in ncr_df.columns:
            ncr_df['Sales Order'] = ''
        # Select columns that exist
        ns_cols = [c for c in ncr_columns if c in ncr_df.columns]
        combined_ncr_df = ncr_df[ns_cols].copy()
    
    if not hb_ncr_df.empty:
        # Add Sales Order placeholder if not exists
        if 'Sales Order' not in hb_ncr_df.columns:
            hb_ncr_df['Sales Order'] = ''
        # Add Close Date, Resolution Days, and Product Type Affected to combined
        hb_cols = [c for c in ncr_columns if c in hb_ncr_df.columns]
        if 'Close Date' in hb_ncr_df.columns:
            hb_cols.append('Close Date')
        if 'Resolution Days' in hb_ncr_df.columns:
            hb_cols.append('Resolution Days')
        if 'Product Type Affected' in hb_ncr_df.columns:
            hb_cols.append('Product Type Affected')
        
        hb_subset = hb_ncr_df[hb_cols].copy()
        
        if combined_ncr_df.empty:
            combined_ncr_df = hb_subset
        else:
            combined_ncr_df = pd.concat([combined_ncr_df, hb_subset], ignore_index=True)
    
    return sales_orders_df, invoices_df, deals_df, invoice_line_items_df, combined_ncr_df
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_rep_list"></a> `get_rep_list` — L4032–L4046

```python
def get_rep_list(sales_orders_df, invoices_df):
    """Get unique list of sales reps from both data sources"""
    reps = set()
    
    if not sales_orders_df.empty and 'Rep Master' in sales_orders_df.columns:
        valid_reps = sales_orders_df['Rep Master'].dropna()
        valid_reps = valid_reps[~valid_reps.isin(['', 'nan', 'None', '#N/A'])]
        reps.update(valid_reps.unique())
    
    if not invoices_df.empty and 'Rep Master' in invoices_df.columns:
        valid_reps = invoices_df['Rep Master'].dropna()
        valid_reps = valid_reps[~valid_reps.isin(['', 'nan', 'None', '#N/A'])]
        reps.update(valid_reps.unique())
    
    return sorted([r for r in reps if r])
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_customers_for_rep"></a> `get_customers_for_rep` — L4049–L4078

```python
def get_customers_for_rep(rep_name, sales_orders_df, invoices_df):
    """Get unique customers for a specific rep (or all reps if 'All Reps' selected)"""
    customers = set()
    
    # Handle "All Reps" case - return all customers
    all_reps = (rep_name == "All Reps")
    
    if not sales_orders_df.empty and 'Corrected Customer Name' in sales_orders_df.columns:
        if all_reps:
            valid_customers = sales_orders_df['Corrected Customer Name'].dropna()
        elif 'Rep Master' in sales_orders_df.columns:
            rep_orders = sales_orders_df[sales_orders_df['Rep Master'] == rep_name]
            valid_customers = rep_orders['Corrected Customer Name'].dropna()
        else:
            valid_customers = pd.Series(dtype=str)
        valid_customers = valid_customers[~valid_customers.isin(['', 'nan', 'None', '#N/A'])]
        customers.update(valid_customers.unique())
    
    if not invoices_df.empty and 'Corrected Customer' in invoices_df.columns:
        if all_reps:
            valid_customers = invoices_df['Corrected Customer'].dropna()
        elif 'Rep Master' in invoices_df.columns:
            rep_invoices = invoices_df[invoices_df['Rep Master'] == rep_name]
            valid_customers = rep_invoices['Corrected Customer'].dropna()
        else:
            valid_customers = pd.Series(dtype=str)
        valid_customers = valid_customers[~valid_customers.isin(['', 'nan', 'None', '#N/A'])]
        customers.update(valid_customers.unique())
    
    return sorted([c for c in customers if c])
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_customer_deals"></a> `get_customer_deals` — L4081–L4100

```python
def get_customer_deals(customer_name, rep_name, deals_df):
    """
    Get HubSpot deals for a specific customer using direct match on Company Name
    """
    if deals_df.empty or 'Company Name' not in deals_df.columns:
        return pd.DataFrame()
    
    # Handle "All Reps" case - don't filter by Deal Owner
    if rep_name == "All Reps":
        matches = deals_df[
            deals_df['Company Name'] == customer_name
        ].copy()
    else:
        # Direct match on Company Name and Deal Owner
        matches = deals_df[
            (deals_df['Company Name'] == customer_name) &
            (deals_df['Deal Owner'] == rep_name)
        ].copy()
    
    return matches
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-extract_die_tool"></a> `extract_die_tool` — L4669–L4711

```python
def extract_die_tool(item_name):
    """
    Extract the die tool code from a SKU.
    Format: CUST-ST-DIETOOL-PRODUCT or CUST-ST-X-DIETOOL-PRODUCT
    Returns (die_tool, is_alphanumeric)
    
    Examples:
    - APOC-MI-H-25L-BB1-1 → die_tool='25L', is_alphanumeric=True (Dram lid label)
    - APOC-MI-1188-APGQ → die_tool='1188', is_alphanumeric=False (Flexpack/Label)
    - 989E-MI-H-4C-EX1-2 → die_tool='4C', is_alphanumeric=True (Concentrate label)
    """
    if pd.isna(item_name):
        return None, False
    
    name = str(item_name).upper().strip()
    
    # Pattern 1: XXXX-ST-X-DIETOOL-... (with single letter indicator like H, M, R)
    # The die tool is the component after the single letter: 25L, 45B, 4C, 7L, 116P, etc.
    match = re.search(r'^[A-Z]{3,4}-[A-Z]{2}-[A-Z]-(\d{1,3}[LBPCH])-', name)
    if match:
        return match.group(1), True
    
    # Pattern 2: XXXX-ST-X-DIETOOL (concentrate patterns like 4C, 7L, 7C)
    match = re.search(r'^[A-Z]{3,4}-[A-Z]{2}-[A-Z]-([47][CLH])-', name)
    if match:
        return match.group(1), True
    
    # Pattern 3: XXXX-ST-NUMERIC-... (purely numeric die tool for Flexpack/Labels)
    match = re.search(r'^[A-Z]{3,4}-[A-Z]{2}-(\d{4})-', name)
    if match:
        return match.group(1), False
    
    # Pattern 4: Direct patterns like -25L-, -45B-, -116P- anywhere in name
    match = re.search(r'-(\d{1,3}[LBPCH])-', name)
    if match:
        return match.group(1), True
    
    # Pattern 5: Concentrate patterns -4C-, -7L-, -7C- etc.
    match = re.search(r'-([47][CLH])-', name)
    if match:
        return match.group(1), True
    
    return None, False
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-categorize_product"></a> `categorize_product` — L4714–L4987

```python
def categorize_product(item_name, item_description="", calyx_product_type=""):
    """
    Categorize a product based on Item name, description, and Calyx || Product Type.
    Returns (category, sub_category, component_type) tuple.
    
    component_type: 'base', 'lid', 'label', 'band', 'accessory', 'complete', or None
    """
    if pd.isna(item_name):
        item_name = ""
    if pd.isna(item_description):
        item_description = ""
    if pd.isna(calyx_product_type):
        calyx_product_type = ""
    
    name = str(item_name).upper().strip()
    desc = str(item_description).upper().strip()
    product_type = str(calyx_product_type).upper().strip()
    all_text = f"{name} {desc}"
    
    # Extract die tool info
    die_tool, is_alphanumeric = extract_die_tool(item_name)
    
    # =========================================================================
    # 1. SHIPPING/TAXES/FEES - Break out into specific types
    # =========================================================================
    # Taxes
    if re.search(r'\bTAX\b|GST|HST|CANADIAN\s*(BUSINESS|GOODS)', all_text):
        return ('Fees & Adjustments', 'Taxes', None)
    
    # Shipping
    if re.search(r'^SHIPPING|SHIPPING\s*FEE|FREIGHT', all_text):
        return ('Fees & Adjustments', 'Shipping', None)
    
    # Expedite Fees
    if re.search(r'EXPEDITE\s*FEE|RUSH\s*FEE', all_text):
        return ('Fees & Adjustments', 'Expedite Fee', None)
    
    # Convenience Fees
    if re.search(r'CONVENIENCE\s*FEE', all_text):
        return ('Fees & Adjustments', 'Convenience Fee', None)
    
    # Discounts/Promos
    if re.search(r'^\$\d+OFF|DISCOUNT|PROMO|%\s*OFF', all_text):
        return ('Fees & Adjustments', 'Discount', None)
    
    # Accounting adjustments
    if re.search(r'^ACCOUNTING|OVERPAYMENT|BAD\s*DEBT|REPLACEMENT\s*ORDER', all_text):
        return ('Fees & Adjustments', 'Accounting Adjustment', None)
    
    # Sample/Creative charges
    if re.search(r'DIE\s*CUT\s*SAMPLE|SAMPLE\s*CHARGE|CREATIVE$|TESTIMONIAL', all_text):
        return ('Fees & Adjustments', 'Sample/Creative', None)
    
    # Tooling fees (check BEFORE label categorization - "Tooling Fee - Labels" is a fee, not a label)
    if re.search(r'TOOLING\s*FEE|TOOL\s*FEE|DIE\s*FEE|PLATE\s*FEE|SETUP\s*FEE', all_text):
        return ('Fees & Adjustments', 'Tooling Fee', None)
    
    # Other fees (catch-all for fee-like items)
    if re.search(r'MODULAR.*SERIAL', all_text):
        return ('Fees & Adjustments', 'Other Fee', None)
    
    # =========================================================================
    # 2. CALYX CURE
    # =========================================================================
    if name.startswith('CC-') or 'CALYX CURE' in all_text:
        return ('Calyx Cure', 'Calyx Cure', 'complete')
    
    # =========================================================================
    # 3. CALYX JAR (8TH Glass)
    # =========================================================================
    if 'GB-8TH' in name or name.startswith('CJ-') or 'CALYX JAR' in all_text:
        return ('Calyx Jar', 'Glass Base', 'base')
    if re.search(r'-JB-', name):
        return ('Calyx Jar', 'Jar Base', 'base')
    if re.search(r'-JL-', name):
        return ('Calyx Jar', 'Jar Lid', 'lid')
    if 'SB-8TH' in name:
        return ('Calyx Jar', 'Shrink Band', 'band')
    
    # =========================================================================
    # 4. CONCENTRATES (4mL/7mL Glass Bases and specific lids)
    # =========================================================================
    # Glass bases
    if re.search(r'GB-4ML|4ML.*GLASS|4\s*ML.*BASE', name):
        return ('Concentrates', '4mL Glass Base', 'base')
    if re.search(r'GB-7ML|7ML.*GLASS|7\s*ML.*BASE', name):
        return ('Concentrates', '7mL Glass Base', 'base')
    
    # Concentrate-specific lids (4C, 7C, 4L, 7L, 4H, 7H patterns)
    if re.search(r'-4[CLH]-|-4[CLH]$', name) and not re.search(r'BOX|TUCK|AUTO|DISPLAY', all_text):
        return ('Concentrates', '4mL Lid', 'lid')
    if re.search(r'-7[CLH]-|-7[CLH]$', name) and not re.search(r'BOX|TUCK|AUTO|DISPLAY', all_text):
        return ('Concentrates', '7mL Lid', 'lid')
    
    # Concentrate labels (alphanumeric die tool with 4C, 7C, 7L patterns)
    if die_tool and is_alphanumeric:
        if re.match(r'^[47][CLH]', die_tool):
            component = 'Lid Label' if 'L' in die_tool else 'Jar Label'
            size = '4mL' if die_tool.startswith('4') else '7mL'
            return ('Concentrates', f'{size} {component}', 'label')
    
    # =========================================================================
    # 5. DRAMS (15D, 25D, 45D, 145D) - Bases, Lids, Labels
    # =========================================================================
    dram_sizes = ['145', '45', '25', '15']  # Check larger first to avoid partial matches
    
    # FIRST: Check for customer label SKUs with alphanumeric die tools
    # These are LABELS, not physical products
    if die_tool and is_alphanumeric:
        for size in dram_sizes:
            size_d = f'{size}D'
            if re.match(rf'^{size}[LBPH]', die_tool):
                if 'L' in die_tool:
                    return ('Drams', f'{size_d} Lid Label', 'label')
                elif 'B' in die_tool or 'P' in die_tool:
                    return ('Drams', f'{size_d} Base Label', 'label')
                else:
                    return ('Drams', f'{size_d} Label', 'label')
    
    # THEN: Check for physical dram products (bases, lids)
    for size in dram_sizes:
        size_d = f'{size}D'
        
        # Polypropylene Bases: PB-XXD or -XXB- patterns
        if re.search(rf'PB-{size}D|{size}D.*BASE|-{size}B-', name):
            return ('Drams', f'{size_d} Base', 'base')
        
        # Polypropylene Lids: PL-XXD patterns (but NOT customer labels like XXXX-MI-H-25L-)
        # Only match if it starts with PL- or CL- (standard product codes)
        if size != '15':  # Skip 15 here, handle DML separately
            if re.search(rf'^PL-{size}D|^CL-{size}D', name):
                return ('Drams', f'{size_d} Lid', 'lid')
        
        # Direct size mentions in description (for standard products only)
        if f'{size}D LID' in all_text and not re.search(r'^[A-Z]{3,4}-[A-Z]{2}-', name):
            return ('Drams', f'{size_d} Lid', 'lid')
        if f'{size}D BASE' in all_text and not re.search(r'^[A-Z]{3,4}-[A-Z]{2}-', name):
            return ('Drams', f'{size_d} Base', 'base')
    
    # =========================================================================
    # 6. DML LIDS (Universal 4mL/7mL/15D - needs pairing to categorize)
    # -F suffix indicates it's specifically for 4mL/7mL concentrates
    # =========================================================================
    if 'DML' in name or re.search(r'PL-DML|CL-DML', name):
        # Check for -F suffix which indicates concentrate lid (4mL or 7mL)
        if name.endswith('-F') or re.search(r'-\d+-F$', name):
            return ('Concentrates', 'Universal Lid (4mL/7mL)', 'lid')
        # Otherwise mark for invoice-based pairing (could be 15D or concentrate)
        return ('DML (Universal)', 'Universal Lid', 'lid')
    
    # 15L patterns that aren't clearly dram-specific
    if re.search(r'-15L-|^15L-', name) and 'DML' not in name:
        # Check if it's clearly a dram label
        if die_tool and is_alphanumeric and die_tool.startswith('15'):
            return ('Drams', '15D Lid Label', 'label')
        # Otherwise it's likely a DML universal lid
        return ('DML (Universal)', 'Universal Lid', 'lid')
    
    # =========================================================================
    # 7. DRAM ACCESSORIES (Tray Frames, Tray Inserts, Shrink Bands)
    # =========================================================================
    if name.startswith('TF-') or 'TRAY FRAME' in all_text:
        return ('Dram Accessories', 'Tray Frame', 'accessory')
    
    if re.search(r'^TI-\d+D|TRAY INSERT', name):
        # Extract size from TI-XXD
        size_match = re.search(r'TI-(\d+)D', name)
        if size_match:
            return ('Dram Accessories', f'{size_match.group(1)}D Tray Insert', 'accessory')
        return ('Dram Accessories', 'Tray Insert', 'accessory')
    
    # Shrink bands for drams
    if re.search(r'SB-15D|SB-25D|SB-45D|SB-145D', name):
        size_match = re.search(r'SB-(\d+)D', name)
        if size_match:
            return ('Dram Accessories', f'{size_match.group(1)}D Shrink Band', 'band')
        return ('Dram Accessories', 'Shrink Band', 'band')
    
    # FEP Liners
    if 'FEP' in name and 'LINER' in all_text:
        return ('Dram Accessories', 'FEP Liner', 'accessory')
    
    # Stick & Grip
    if re.search(r'SG-|STICK.*GRIP', all_text):
        return ('Dram Accessories', 'Stick & Grip', 'accessory')
    
    # =========================================================================
    # 8. TUBES (116mm, 90mm, 84mm)
    # =========================================================================
    if re.search(r'JT-116|116\s*MM|116T|-116-|116P', name) and 'BOX' not in all_text:
        if 'LABEL' in all_text or (die_tool and '116' in die_tool):
            return ('Tubes', '116mm Label', 'label')
        return ('Tubes', '116mm Tube', 'complete')
    
    if re.search(r'JT-90|90\s*MM|90T|-90-|90M', name) and 'BOX' not in all_text and 'WAVEPACK' not in all_text:
        if 'LABEL' in all_text or (die_tool and '90' in die_tool):
            return ('Tubes', '90mm Label', 'label')
        return ('Tubes', '90mm Tube', 'complete')
    
    if re.search(r'JT-84|84\s*MM|84T|-84-', name) and 'TUBE' in all_text:
        if 'LABEL' in all_text:
            return ('Tubes', '84mm Label', 'label')
        return ('Tubes', '84mm Tube', 'complete')
    
    # =========================================================================
    # 9. BOXES
    # =========================================================================
    box_keywords = ['CORE AUTO', 'AUTOBOTTOM', 'AUTO BOTTOM', 'CORE TUCK', 
                    'REVERSE TUCK', 'ELEVATED TUCK', 'ELEVATED AUTO']
    if any(kw in all_text for kw in box_keywords) and 'BAG' not in all_text:
        if 'AUTO' in all_text:
            return ('Boxes', 'Core Auto', 'complete')
        if 'TUCK' in all_text:
            return ('Boxes', 'Core Tuck', 'complete')
        return ('Boxes', 'Box', 'complete')
    
    if re.search(r'-CNCA-|-CNC-', all_text) or 'SHIPPER BOX' in all_text:
        return ('Boxes', 'Shipper Box', 'complete')
    if 'BOX' in all_text and 'SBS' in all_text and 'BAG' not in all_text:
        return ('Boxes', 'Box', 'complete')
    if 'DISPLAY' in all_text and ('TEARAWAY' in all_text or 'ELEVATED' in all_text) and 'BAG' not in all_text:
        return ('Boxes', 'Display Box', 'complete')
    
    # =========================================================================
    # 10. FLEXPACK / WAVEPACK (check Calyx || Product Type first!)
    # =========================================================================
    # Use Calyx || Product Type if available
    if 'FLEXPACK' in product_type or 'WAVEPACK' in product_type or 'FLEX' in product_type:
        return ('Flexpack', 'Wavepack', 'complete')
    
    if name.startswith('BAM-') and 'LABEL' not in all_text:
        return ('Flexpack', 'Wavepack', 'complete')
    if re.search(r'WAVEPACK|FLEXPACK', all_text):
        return ('Flexpack', 'Wavepack', 'complete')
    if re.search(r'\bBAGS?\b|\bPOUCH\b', desc):
        return ('Flexpack', 'Bag/Pouch', 'complete')
    
    # Numeric die tool - could be Flexpack or Non-Core Label
    if die_tool and not is_alphanumeric and die_tool in FLEXPACK_CODES:
        return ('Flexpack', 'Wavepack', 'complete')
    
    # =========================================================================
    # 11. NON-CORE LABELS (customer-specific labels)
    # =========================================================================
    # Use Calyx || Product Type if available
    if 'LABEL' in product_type:
        return ('Non-Core Labels', 'Custom Label', 'label')
    
    if re.search(r'\bLABEL\b|\bLBL\b|\bBOPP\b', all_text):
        return ('Non-Core Labels', 'Custom Label', 'label')
    
    # Numeric die tool that's not a known Flexpack code
    if die_tool and not is_alphanumeric:
        return ('Non-Core Labels', 'Custom Label', 'label')
    
    # Customer SKU pattern without clear product identification
    if re.search(r'^[A-Z]{3,4}-[A-Z]{2}-', name):
        return ('Non-Core Labels', 'Custom Label', 'label')
    
    # =========================================================================
    # 12. APPLICATION FEES (categorize by what they're for)
    # =========================================================================
    if re.search(r'APPL\s*FEE|APPLICATION\s*FEE', all_text):
        # Try to determine what product the fee is for
        if re.search(r'15D|25D|45D|145D', all_text):
            return ('Drams', 'Application Fee', 'fee')
        if re.search(r'116|90', all_text) and 'TUBE' in all_text:
            return ('Tubes', 'Application Fee', 'fee')
        return ('Fees & Adjustments', 'Application Fee', 'fee')
    
    # =========================================================================
    # 13. UNCATEGORIZED
    # =========================================================================
    return ('Other', 'Uncategorized', None)
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-apply_product_categories"></a> `apply_product_categories` — L4990–L5169

```python
def apply_product_categories(df):
    """
    Apply categorization to a dataframe using Calyx || Product Type and Calyx | Item Type columns.
    
    PRIMARY: Uses 'Calyx || Product Type' (Column X) to map to Forecast Category
    FALLBACK: For blanks, checks 'Calyx | Item Type' (Column W) for Shipping/Tax
    
    Mapping from Calyx || Product Type to Forecast Category:
        Plastic Lids → Drams
        Plastic Bases → Drams
        Application → Application
        Labels → Labels
        Flex Pack → Flexpack
        Tray Inserts → Other
        Calyx Cure → Cure
        Shrink Bands → Other
        Glass Bases → Glass
        Tubes → Other
        Boxes → Other
        Fee → Other
        Design → Other
        Container → Glass
        Tray Frames → Other
        Accessories → Other
        Service → Other
    
    Mapping from Calyx | Item Type (for blanks):
        Shipping → Shipping
        Tax Item → Other (excluded from revenue)
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Mapping from Calyx || Product Type to Forecast Category
    PRODUCT_TYPE_TO_CATEGORY = {
        'plastic lids': 'Drams',
        'plastic bases': 'Drams',
        'application': 'Application',
        'labels': 'Labels',
        'flex pack': 'Flexpack',
        'tray inserts': 'Other',
        'calyx cure': 'Cure',
        'shrink bands': 'Other',
        'glass bases': 'Glass',
        'tubes': 'Other',
        'boxes': 'Other',
        'fee': 'Other',
        'design': 'Other',
        'container': 'Glass',
        'tray frames': 'Other',
        'accessories': 'Other',
        'service': 'Other',
    }
    
    # Mapping from Calyx | Item Type (fallback for blanks)
    ITEM_TYPE_TO_CATEGORY = {
        'shipping': 'Shipping',
        'shipitem': 'Shipping',
        'tax item': 'Other',
        'inventory item': 'Other',
        'non-inventory item': 'Other',
        'service': 'Other',
    }
    
    # Find Calyx columns (flexible matching - handles whitespace and case differences)
    product_type_col = None
    item_type_col = None
    item_col = None
    item_desc_col = None
    
    for col in df.columns:
        col_lower = str(col).lower().strip()
        # Look for "calyx || product type" or similar
        if 'product type' in col_lower and 'calyx' in col_lower:
            product_type_col = col
        # Look for "calyx | item type" or similar  
        elif 'item type' in col_lower and 'calyx' in col_lower:
            item_type_col = col
        # Look for Item column
        elif col_lower == 'item':
            item_col = col
        # Look for Item Description column
        elif col_lower == 'item description':
            item_desc_col = col
    
    def categorize_row(row):
        """Categorize a single row based on Calyx columns"""
        # Get column values
        product_type_raw = ''
        item_type_raw = ''
        item_name = ''
        item_desc = ''
        
        if product_type_col and product_type_col in row.index:
            val = row[product_type_col]
            if pd.notna(val):
                product_type_raw = str(val).strip()
        
        if item_type_col and item_type_col in row.index:
            val = row[item_type_col]
            if pd.notna(val):
                item_type_raw = str(val).strip()
        
        if item_col and item_col in row.index:
            val = row[item_col]
            if pd.notna(val):
                item_name = str(val).strip()
        
        if item_desc_col and item_desc_col in row.index:
            val = row[item_desc_col]
            if pd.notna(val):
                item_desc = str(val).strip()
        
        product_type = product_type_raw.lower()
        item_type = item_type_raw.lower()
        item_name_lower = item_name.lower()
        item_desc_lower = item_desc.lower()
        
        # OVERRIDE 1: Check for Tooling Fee in item name - always categorize as Other
        # This catches "Tooling Fee - Labels" which shouldn't be in Labels
        if 'tooling fee' in item_name_lower or 'tooling fee' in item_desc_lower:
            return ('Other', 'Tooling Fee', None)
        
        # OVERRIDE 2: Check Calyx | Item Type for "ShipItem" - this is shipping
        if item_type == 'shipitem' or item_type == 'shipping':
            return ('Shipping', 'Shipping', None)
        
        # PRIMARY: Check Calyx || Product Type
        if product_type and product_type in PRODUCT_TYPE_TO_CATEGORY:
            category = PRODUCT_TYPE_TO_CATEGORY[product_type]
            return (category, product_type_raw, None)
        
        # FALLBACK: Check Calyx | Item Type for other types
        if item_type and item_type in ITEM_TYPE_TO_CATEGORY:
            category = ITEM_TYPE_TO_CATEGORY[item_type]
            return (category, item_type_raw, None)
        
        # If we have a product type that's not in our mapping, categorize as Other
        if product_type_raw:
            return ('Other', product_type_raw, None)
        
        # Default fallback
        return ('Other', 'Uncategorized', None)
    
    # If we found at least one Calyx column, use the new logic
    if product_type_col or item_type_col:
        # Apply new Calyx-based categorization
        categories = df.apply(categorize_row, axis=1)
        
        df['Product Category'] = categories.apply(lambda x: x[0])
        df['Product Sub-Category'] = categories.apply(lambda x: x[1])
        df['Component Type'] = categories.apply(lambda x: x[2])
        return df
    
    # NO Calyx columns found - fall back to old SKU-based categorization
    # This is for backward compatibility with data sources that don't have Calyx columns
    item_col = 'Item' if 'Item' in df.columns else None
    desc_col = 'Item Description' if 'Item Description' in df.columns else None
    
    if item_col is None and desc_col is None:
        df['Product Category'] = 'Other'
        df['Product Sub-Category'] = 'Uncategorized'
        df['Component Type'] = None
        return df
    
    # Apply old categorization for backward compatibility
    categories = df.apply(
        lambda row: categorize_product(
            row.get(item_col, '') if item_col else '',
            row.get(desc_col, '') if desc_col else '',
            ''
        ), axis=1
    )
    
    df['Product Category'] = categories.apply(lambda x: x[0])
    df['Product Sub-Category'] = categories.apply(lambda x: x[1])
    df['Component Type'] = categories.apply(lambda x: x[2])
    return df
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-rollup_dml_lids"></a> `rollup_dml_lids` — L5172–L5238

```python
def rollup_dml_lids(df):
    """
    Roll up DML (Universal) lids into their parent category based on 
    what other components are on the same invoice.
    
    Logic:
    - If invoice has GB-4ML or GB-7ML → DML lid becomes Concentrates
    - If invoice has PB-15D (15D base) → DML lid becomes Drams (15D)
    - Otherwise → stays as DML (Universal) or defaults to Concentrates
    """
    if df.empty or 'Product Category' not in df.columns:
        return df
    
    df = df.copy()
    
    # Find invoices with DML lids
    dml_mask = df['Product Category'] == 'DML (Universal)'
    if not dml_mask.any():
        return df
    
    # Get document numbers with DML lids
    doc_col = 'Document Number' if 'Document Number' in df.columns else None
    if doc_col is None:
        # Can't pair without document number - default DML to Concentrates
        df.loc[dml_mask, 'Product Category'] = 'Concentrates'
        df.loc[dml_mask, 'Product Sub-Category'] = 'Universal Lid (4mL/7mL/15D)'
        return df
    
    # Process each invoice with DML lids
    dml_docs = df.loc[dml_mask, doc_col].unique()
    
    for doc in dml_docs:
        doc_mask = df[doc_col] == doc
        doc_items = df.loc[doc_mask]
        
        # Check what else is on this invoice
        has_concentrate_base = doc_items['Product Sub-Category'].str.contains(
            r'4mL Glass Base|7mL Glass Base', case=False, na=False
        ).any()
        
        has_15d_base = doc_items['Product Sub-Category'].str.contains(
            r'15D Base', case=False, na=False
        ).any()
        
        # Also check Item column for patterns
        if 'Item' in doc_items.columns:
            items_str = ' '.join(doc_items['Item'].fillna('').astype(str))
            if re.search(r'GB-4ML|GB-7ML|4ML.*GLASS|7ML.*GLASS', items_str.upper()):
                has_concentrate_base = True
            if re.search(r'PB-15D|15D.*BASE|-15B-', items_str.upper()):
                has_15d_base = True
        
        # Assign DML lids based on pairing
        dml_in_doc = doc_mask & dml_mask
        
        if has_concentrate_base:
            df.loc[dml_in_doc, 'Product Category'] = 'Concentrates'
            df.loc[dml_in_doc, 'Product Sub-Category'] = 'Universal Lid'
        elif has_15d_base:
            df.loc[dml_in_doc, 'Product Category'] = 'Drams'
            df.loc[dml_in_doc, 'Product Sub-Category'] = '15D Lid'
        else:
            # Default to Concentrates if no clear pairing
            df.loc[dml_in_doc, 'Product Category'] = 'Concentrates'
            df.loc[dml_in_doc, 'Product Sub-Category'] = 'Universal Lid'
    
    return df
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-create_unified_product_view"></a> `create_unified_product_view` — L5241–L5331

```python
def create_unified_product_view(df):
    """
    Create a unified product view that rolls up components into complete products.
    
    For example, instead of showing:
    - 4mL Glass Base: $300
    - Universal Lid: $200
    
    Show:
    - 4mL Concentrate Jar (complete): $500
    
    This is for customer-facing summaries.
    
    Creates two new columns:
    - 'Unified Category': Size-specific (e.g., "Drams (25D)", "Concentrates (4mL)")
    - 'Parent Category': Rolled up (e.g., "Drams", "Concentrates")
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # First apply DML rollup
    df = rollup_dml_lids(df)
    
    # Create unified category for display
    def get_unified_category(row):
        cat = row.get('Product Category', 'Other')
        subcat = row.get('Product Sub-Category', '')
        component = row.get('Component Type', '')
        
        # For categories that are already complete products
        if cat in ['Tubes', 'Boxes', 'Flexpack', 'Calyx Cure', 'Fees & Adjustments', 'Other']:
            return cat
        
        # For Drams - unify base + lid + labels
        if cat == 'Drams':
            # Extract size (15D, 25D, 45D, 145D)
            size_match = re.search(r'(\d+D)', str(subcat))
            if size_match:
                return f"Drams ({size_match.group(1)})"
            return 'Drams'
        
        # For Concentrates - unify jar + lid
        if cat == 'Concentrates':
            size_match = re.search(r'(4mL|7mL)', str(subcat))
            if size_match:
                return f"Concentrates ({size_match.group(1)})"
            # Universal lids without clear size match
            if 'lid' in str(subcat).lower() or 'universal' in str(subcat).lower():
                return 'Concentrate Lids'
            return 'Concentrates'
        
        # For Calyx Jar
        if cat == 'Calyx Jar':
            return 'Calyx Jar'
        
        # For accessories - keep unified as Dram Accessories (shows in sub-breakdown)
        if cat == 'Dram Accessories':
            return 'Dram Accessories'
        
        # For labels
        if cat == 'Non-Core Labels':
            return 'Non-Core Labels'
        
        return cat
    
    df['Unified Category'] = df.apply(get_unified_category, axis=1)
    
    # Create Parent Category (rolled up - for summary views)
    # This groups all Drams together, all Concentrates together, etc.
    def get_parent_category(unified_cat):
        if pd.isna(unified_cat):
            return 'Other'
        
        unified = str(unified_cat)
        
        # Roll up Drams (25D, 45D, 15D, 145D) and Dram Accessories → Drams
        if unified.startswith('Drams') or unified == 'Dram Accessories':
            return 'Drams'
        
        # Roll up Concentrates (4mL, 7mL) and Concentrate Lids → Concentrates
        if unified.startswith('Concentrates') or unified == 'Concentrate Lids':
            return 'Concentrates'
        
        # Everything else stays as-is
        return unified
    
    df['Parent Category'] = df['Unified Category'].apply(get_parent_category)
    
    return df
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-map_to_forecast_category"></a> `map_to_forecast_category` — L6291–L6335

```python
def map_to_forecast_category(product_category, sub_category=None):
    """
    Map product category to forecast category.
    
    Since apply_product_categories now outputs Forecast Categories directly
    (Drams, Flexpack, Cure, Glass, Labels, Application, Shipping, Other),
    this function mainly passes them through or handles legacy categories.
    
    Forecast Categories:
        - Drams
        - Flexpack
        - Cure
        - Glass
        - Labels
        - Application
        - Shipping
        - Other
    """
    if pd.isna(product_category):
        return 'Other'
    
    cat = str(product_category).strip()
    
    # Direct pass-through for new Calyx-based categories
    valid_forecast_categories = ['Drams', 'Flexpack', 'Cure', 'Glass', 'Labels', 'Application', 'Shipping', 'Other']
    if cat in valid_forecast_categories:
        return cat
    
    # Handle legacy category names (backward compatibility)
    legacy_mappings = {
        'Dram Accessories': 'Drams',
        'DML (Universal)': 'Drams',
        'Calyx Cure': 'Cure',
        'Concentrates': 'Glass',
        'Calyx Jar': 'Glass',
        'Non-Core Labels': 'Labels',
        'Fees & Adjustments': 'Other',
        'Boxes': 'Other',
        'Tubes': 'Other',
    }
    
    if cat in legacy_mappings:
        return legacy_mappings[cat]
    
    return 'Other'
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-map_to_forecast_pipeline"></a> `map_to_forecast_pipeline` — L6338–L6356

```python
def map_to_forecast_pipeline(pipeline_value):
    """Map HubSpot pipeline values to forecast pipeline categories"""
    if pd.isna(pipeline_value):
        return None
    
    pipeline = str(pipeline_value).upper().strip()
    
    if 'RETENTION' in pipeline:
        return 'Retention'
    if 'GROWTH' in pipeline:
        return 'Growth'
    if 'ACQUISITION' in pipeline or 'NEW' in pipeline:
        return 'Acquisition'
    if 'DISTRIBUT' in pipeline or 'DISTRIBUTION' in pipeline:
        return 'Distributors'
    if 'ECOM' in pipeline or 'E-COM' in pipeline or 'E COM' in pipeline:
        return 'Ecom'
    
    return None
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-map_order_type_to_forecast_category"></a> `map_order_type_to_forecast_category` — L6359–L6383

```python
def map_order_type_to_forecast_category(order_type):
    """Map Order Type from Sales Orders to Forecast Category"""
    if pd.isna(order_type):
        return 'Other'
    
    ot = str(order_type).upper().strip()
    
    if 'DRAM' in ot or re.search(r'15D|25D|45D|145D', ot):
        return 'Drams'
    if 'FLEX' in ot or 'WAVE' in ot or 'BAG' in ot:
        return 'Flexpack'
    if 'CURE' in ot:
        return 'Cure'
    if 'CUBE' in ot:
        return 'Cube'
    if 'GLASS' in ot or 'CONCENTRATE' in ot or re.search(r'4ML|7ML', ot):
        return 'Glass'
    if 'LABEL' in ot:
        return 'Labels'
    if 'APPL' in ot or 'APPLICATION' in ot:
        return 'Application'
    if 'SHIP' in ot or 'FREIGHT' in ot:
        return 'Shipping'
    
    return 'Other'
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-map_deal_type_to_forecast_category"></a> `map_deal_type_to_forecast_category` — L6386–L6433

```python
def map_deal_type_to_forecast_category(deal_type):
    """Map Deal Type from HubSpot to Forecast Category"""
    if pd.isna(deal_type):
        return 'Other'
    
    dt = str(deal_type).upper().strip()
    
    # Drams - check first since "LABELED" appears in multiple categories
    if 'NON-LABELED' in dt or 'NON LABELED' in dt:
        return 'Drams'
    if 'DRAM' in dt:
        return 'Drams'
    if 'LABELED' in dt and 'LABELS ONLY' not in dt:
        return 'Drams'
    
    # Flexpack
    if 'FLEXPACK' in dt or 'FLEX' in dt or 'WAVE' in dt or 'BAG' in dt:
        return 'Flexpack'
    
    # Cure
    if 'CURE' in dt or 'CALYX CURE' in dt:
        return 'Cure'
    
    # Cube
    if 'CUBE' in dt:
        return 'Cube'
    
    # Glass (concentrates, jars)
    if 'GLASS' in dt or 'CONCENTRATE' in dt or 'JAR' in dt or '4ML' in dt or '7ML' in dt or '8TH' in dt:
        return 'Glass'
    
    # Labels
    if 'LABELS ONLY' in dt or 'LABEL' in dt:
        return 'Labels'
    
    # Application
    if 'APPLICATION' in dt or 'APPL' in dt:
        return 'Application'
    
    # Shipping
    if 'SHIP' in dt or 'FREIGHT' in dt:
        return 'Shipping'
    
    # Boxes go to Other
    if 'OUTER BOX' in dt or 'BOX' in dt:
        return 'Other'
    
    return 'Other'
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-parse_forecast_sheet"></a> `parse_forecast_sheet` — L6440–L6505

```python
def parse_forecast_sheet(raw_df):
    """Parse the 2026 Forecast sheet structure"""
    if raw_df.empty:
        return pd.DataFrame()
    
    all_data = []
    
    month_cols = {
        'January': 2, 'February': 3, 'March': 4,
        'April': 6, 'May': 7, 'June': 8,
        'July': 10, 'August': 11, 'September': 12,
        'October': 14, 'November': 15, 'December': 16
    }
    
    quarter_cols = {'Q1': 5, 'Q2': 9, 'Q3': 13, 'Q4': 17}
    yearly_col = 18
    
    current_pipeline = None
    valid_pipelines = ['Retention', 'Growth', 'Acquisition', 'Distributors', 'Ecom', 'Total']
    categories = ['Drams', 'Flexpack', 'Cure', 'Cube', 'Glass', 'Labels', 'Application', 'Shipping', 'Other', 'Total']
    
    for idx, row in raw_df.iterrows():
        if len(row) < 3:
            continue
        
        first_col = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
        second_col = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ''
        
        if first_col in valid_pipelines:
            current_pipeline = first_col
        
        if second_col == 'Category':
            continue
        
        if second_col == '' or second_col == 'nan':
            continue
        
        if current_pipeline and second_col in categories:
            row_data = {
                'Pipeline': current_pipeline,
                'Category': second_col
            }
            
            for month, col_idx in month_cols.items():
                if col_idx < len(row):
                    row_data[month] = clean_numeric(row.iloc[col_idx])
                else:
                    row_data[month] = 0.0
            
            for quarter, col_idx in quarter_cols.items():
                if col_idx < len(row):
                    row_data[quarter] = clean_numeric(row.iloc[col_idx])
                else:
                    row_data[quarter] = 0.0
            
            if yearly_col < len(row):
                row_data['Annual_Total'] = clean_numeric(row.iloc[yearly_col])
            else:
                row_data['Annual_Total'] = 0.0
            
            all_data.append(row_data)
    
    if not all_data:
        return pd.DataFrame()
    
    return pd.DataFrame(all_data)
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-load_forecast_data"></a> `load_forecast_data` — L6509–L6516

```python
def load_forecast_data():
    """Load and parse the 2026 Forecast data"""
    raw_df = load_google_sheets_data("2026 Forecast", "A1:S80", version=CACHE_VERSION, silent=True)
    
    if raw_df.empty:
        return pd.DataFrame()
    
    return parse_forecast_sheet(raw_df)
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-load_annual_tracker_data"></a> `load_annual_tracker_data` — L6520–L7040

```python
def load_annual_tracker_data():
    """Load all data needed for the Annual Goal Tracker"""
    
    line_items_df = load_google_sheets_data("Invoice Line Item", "A:Z", version=CACHE_VERSION)
    invoices_df = load_google_sheets_data("_NS_Invoices_Data", "A:U", version=CACHE_VERSION)
    sales_orders_df = load_google_sheets_data("_NS_SalesOrders_Data", "A:AG", version=CACHE_VERSION)
    deals_df = load_google_sheets_data("All Reps All Pipelines", "A:Z", version=CACHE_VERSION)
    forecast_df = load_forecast_data()
    
    # Load Sales Order Line Item for proper categorization (same structure as Invoice Line Item)
    sales_order_line_items_df = load_google_sheets_data("Sales Order Line Item", "A:W", version=CACHE_VERSION, silent=True)
    
    # Load Copy of Deals Line Item for Close Rate Analysis
    # Note: Column headers are in row 2 of the sheet
    # Range extended to AB to include Effective unit price column
    deals_line_items_df = load_google_sheets_data("Copy of Deals Line Item", "A2:AB", version=CACHE_VERSION, silent=True)
    
    # Load Deals Line Item for Pipeline Section (Plan vs Full Pipeline)
    # Note: Column headers are in row 2 of the sheet
    # This is the active pipeline view - no standard reorder/Gonzalez filtering
    # Extended to Column V to include "Pending Approval Date"
    pipeline_deals_df = load_google_sheets_data("Deals Line Item", "A2:V", version=CACHE_VERSION, silent=True)
    
    # Standard Reorder Date columns - if ANY of these have a value, exclude the deal
    # These are columns R through Y in the Copy of Deals Line Item sheet
    STANDARD_REORDER_DATE_COLS = [
        'Date entered "Standard Reorder - Confirmed by Customer (Acquisition (New Customer))"',
        'Date entered "Standard Reorder - Confirmed by Customer (Calyx Distribution)"',
        'Date entered "Standard Reorder - Confirmed by Customer (Growth Pipeline (Upsell/Cross-sell))"',
        'Date entered "Standard Reorder - Confirmed by Customer- (Retention (Existing Product))"',
        'Date entered "Standard Reorder - Pending Customer Confirmation (Acquisition (New Customer))"',
        'Date entered "Standard Reorder - Pending Customer Confirmation (Calyx Distribution)"',
        'Date entered "Standard Reorder - Pending Customer Confirmation (Growth Pipeline (Upsell/Cross-sell))"',
        'Date entered "Standard Reorder - Pending Customer Confirmation (Retention (Existing Product))"',
    ]
    
    # Process Invoice Line Items
    if not line_items_df.empty:
        if line_items_df.columns.duplicated().any():
            line_items_df = line_items_df.loc[:, ~line_items_df.columns.duplicated()]
        
        if 'Amount' in line_items_df.columns:
            line_items_df['Amount'] = line_items_df['Amount'].apply(clean_numeric)
        if 'Quantity' in line_items_df.columns:
            line_items_df['Quantity'] = line_items_df['Quantity'].apply(clean_numeric)
        if 'Date' in line_items_df.columns:
            line_items_df['Date'] = pd.to_datetime(line_items_df['Date'], errors='coerce')
        
        line_items_df = apply_product_categories(line_items_df)
        
        line_items_df['Forecast Category'] = line_items_df.apply(
            lambda row: map_to_forecast_category(row.get('Product Category'), row.get('Product Sub-Category')),
            axis=1
        )
    
    # =======================================================================
    # CREATE SKU → CATEGORY LOOKUP FROM INVOICE LINE ITEMS
    # This will be used to categorize HubSpot deals by their SKU
    # =======================================================================
    sku_category_lookup = {}
    if not line_items_df.empty and 'Item' in line_items_df.columns and 'Product Category' in line_items_df.columns:
        # Build lookup: SKU → Product Category (use the most common category for each SKU)
        sku_categories = line_items_df.groupby('Item')['Product Category'].agg(lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Other')
        sku_category_lookup = sku_categories.to_dict()
    
    # Process Invoices (for pipeline lookup)
    pipeline_lookup = {}
    raw_pipeline_lookup = {}
    if not invoices_df.empty:
        if invoices_df.columns.duplicated().any():
            invoices_df = invoices_df.loc[:, ~invoices_df.columns.duplicated()]
        
        if 'Document Number' in invoices_df.columns:
            invoices_df['Document Number'] = invoices_df['Document Number'].astype(str).str.strip()
        
        pipeline_col = None
        for col in invoices_df.columns:
            if 'hubspot' in col.lower() and 'pipeline' in col.lower():
                pipeline_col = col
                break
        
        if pipeline_col is None and 'HubSpot Pipeline' in invoices_df.columns:
            pipeline_col = 'HubSpot Pipeline'
        
        if pipeline_col and 'Document Number' in invoices_df.columns:
            # Keep both raw pipeline and mapped pipeline for SO Manually Built handling
            invoices_df['Raw_Pipeline'] = invoices_df[pipeline_col].astype(str).str.strip()
            invoices_df['Forecast Pipeline'] = invoices_df[pipeline_col].apply(map_to_forecast_pipeline)
            
            # Create lookups for both
            pipeline_lookup = invoices_df.set_index('Document Number')['Forecast Pipeline'].to_dict()
            raw_pipeline_lookup = invoices_df.set_index('Document Number')['Raw_Pipeline'].to_dict()
    
    # Join pipeline to line items
    if not line_items_df.empty:
        if 'Document Number' in line_items_df.columns:
            line_items_df['Document Number'] = line_items_df['Document Number'].astype(str).str.strip()
            
            if pipeline_lookup:
                line_items_df['Forecast Pipeline'] = line_items_df['Document Number'].map(pipeline_lookup)
            else:
                line_items_df['Forecast Pipeline'] = None
                
            if raw_pipeline_lookup:
                line_items_df['Raw_Pipeline'] = line_items_df['Document Number'].map(raw_pipeline_lookup)
            else:
                line_items_df['Raw_Pipeline'] = None
            
            # Handle "SO Manually Built" based on Rep Master
            # Brad Sherman, Lance Mitton → Acquisition
            # Alex Gonzalez, Jake Lynch, Dave Borkowski → Retention
            acquisition_reps = ['Brad Sherman', 'Lance Mitton']
            retention_reps = ['Alex Gonzalez', 'Jake Lynch', 'Dave Borkowski']
            
            def assign_so_manually_built_pipeline(row):
                # If already mapped, keep it
                if pd.notna(row.get('Forecast Pipeline')) and row.get('Forecast Pipeline') != 'Unmapped':
                    return row['Forecast Pipeline']
                
                # Check if this is SO Manually Built
                raw_pipeline = str(row.get('Raw_Pipeline', '')).strip()
                if 'SO Manually Built' in raw_pipeline or 'Manually Built' in raw_pipeline:
                    rep = str(row.get('Rep Master', '')).strip()
                    
                    if rep in acquisition_reps:
                        return 'Acquisition'
                    elif rep in retention_reps:
                        return 'Retention'
                
                # Return original (could be None/NaN)
                return row.get('Forecast Pipeline')
            
            line_items_df['Forecast Pipeline'] = line_items_df.apply(assign_so_manually_built_pipeline, axis=1)
    
    # Process Sales Orders (header level - kept for backward compatibility)
    if not sales_orders_df.empty:
        if sales_orders_df.columns.duplicated().any():
            sales_orders_df = sales_orders_df.loc[:, ~sales_orders_df.columns.duplicated()]
        
        if 'Amount (Transaction Total)' in sales_orders_df.columns and 'Amount' not in sales_orders_df.columns:
            sales_orders_df = sales_orders_df.rename(columns={'Amount (Transaction Total)': 'Amount'})
        
        if 'Amount' in sales_orders_df.columns:
            sales_orders_df['Amount'] = sales_orders_df['Amount'].apply(clean_numeric)
        if 'Order Start Date' in sales_orders_df.columns:
            sales_orders_df['Order Start Date'] = pd.to_datetime(sales_orders_df['Order Start Date'], errors='coerce')
        
        # Parse date columns for pending orders filtering
        if 'Customer Promise Last Date to Ship' in sales_orders_df.columns:
            sales_orders_df['Customer Promise Last Date to Ship'] = pd.to_datetime(sales_orders_df['Customer Promise Last Date to Ship'], errors='coerce')
        if 'Projected Date' in sales_orders_df.columns:
            sales_orders_df['Projected Date'] = pd.to_datetime(sales_orders_df['Projected Date'], errors='coerce')
        if 'Pending Approval Date' in sales_orders_df.columns:
            sales_orders_df['Pending Approval Date'] = pd.to_datetime(sales_orders_df['Pending Approval Date'], errors='coerce')
        
        pipeline_col = None
        for col in sales_orders_df.columns:
            if 'hubspot' in col.lower() and 'pipeline' in col.lower():
                pipeline_col = col
                break
        
        if pipeline_col:
            sales_orders_df['Forecast Pipeline'] = sales_orders_df[pipeline_col].apply(map_to_forecast_pipeline)
        
        if 'Order Type' in sales_orders_df.columns:
            sales_orders_df['Forecast Category'] = sales_orders_df['Order Type'].apply(map_order_type_to_forecast_category)
    
    # =======================================================================
    # PROCESS SALES ORDER LINE ITEMS (for proper categorization)
    # Uses same Calyx || Product Type logic as Invoice Line Items
    # =======================================================================
    if not sales_order_line_items_df.empty:
        if sales_order_line_items_df.columns.duplicated().any():
            sales_order_line_items_df = sales_order_line_items_df.loc[:, ~sales_order_line_items_df.columns.duplicated()]
        
        # Clean numeric columns
        if 'Amount' in sales_order_line_items_df.columns:
            sales_order_line_items_df['Amount'] = sales_order_line_items_df['Amount'].apply(clean_numeric)
        if 'Quantity Ordered' in sales_order_line_items_df.columns:
            sales_order_line_items_df['Quantity'] = sales_order_line_items_df['Quantity Ordered'].apply(clean_numeric)
        
        # Parse dates
        if 'Date Created' in sales_order_line_items_df.columns:
            sales_order_line_items_df['Date Created'] = pd.to_datetime(sales_order_line_items_df['Date Created'], errors='coerce')
        if 'Pending Fulfillment Date' in sales_order_line_items_df.columns:
            sales_order_line_items_df['Pending Fulfillment Date'] = pd.to_datetime(sales_order_line_items_df['Pending Fulfillment Date'], errors='coerce')
        
        # Apply same Calyx-based categorization as Invoice Line Items
        sales_order_line_items_df = apply_product_categories(sales_order_line_items_df)
        
        # Map to forecast categories
        sales_order_line_items_df['Forecast Category'] = sales_order_line_items_df.apply(
            lambda row: map_to_forecast_category(row.get('Product Category'), row.get('Product Sub-Category')),
            axis=1
        )
        
        # Map HubSpot Pipeline
        if 'HubSpot Pipeline' in sales_order_line_items_df.columns:
            sales_order_line_items_df['Forecast Pipeline'] = sales_order_line_items_df['HubSpot Pipeline'].apply(map_to_forecast_pipeline)
        
        # =======================================================================
        # JOIN SALES ORDER LINE ITEMS WITH HEADER DATA FOR ACCURATE STATUS/DATES
        # Look up Updated Status (Column AG) and date columns from _NS_SalesOrders_Data
        # =======================================================================
        if not sales_orders_df.empty and 'Document Number' in sales_order_line_items_df.columns:
            # Ensure Document Number is string for joining
            sales_order_line_items_df['Document Number'] = sales_order_line_items_df['Document Number'].astype(str).str.strip()
            
            # Find the document number column in sales_orders_df
            # It might be "Document Number", "SO Number", "SO #", "Sales Order Number", etc.
            so_doc_col = None
            possible_doc_cols = ['SO Number', 'Document Number', 'SO #', 'Sales Order Number', 'Order Number']
            for col in possible_doc_cols:
                if col in sales_orders_df.columns:
                    so_doc_col = col
                    break
            
            # If we found a matching column, proceed with the join
            if so_doc_col:
                # Create lookup from sales_orders_df
                so_lookup_cols = [so_doc_col]
                if 'Updated Status' in sales_orders_df.columns:
                    so_lookup_cols.append('Updated Status')
                if 'Customer Promise Last Date to Ship' in sales_orders_df.columns:
                    so_lookup_cols.append('Customer Promise Last Date to Ship')
                if 'Projected Date' in sales_orders_df.columns:
                    so_lookup_cols.append('Projected Date')
                if 'Pending Approval Date' in sales_orders_df.columns:
                    so_lookup_cols.append('Pending Approval Date')
                
                if len(so_lookup_cols) > 1:
                    so_header_lookup = sales_orders_df[so_lookup_cols].copy()
                    # Rename to Document Number for the join
                    so_header_lookup = so_header_lookup.rename(columns={so_doc_col: 'Document Number'})
                    so_header_lookup['Document Number'] = so_header_lookup['Document Number'].astype(str).str.strip()
                    so_header_lookup = so_header_lookup.drop_duplicates(subset=['Document Number'])
                    
                    # Join to line items
                    sales_order_line_items_df = sales_order_line_items_df.merge(
                        so_header_lookup, 
                        on='Document Number', 
                        how='left',
                        suffixes=('', '_header')
                    )
                    
                    # Create a computed Expected Date based on Updated Status
                    # Status values are like: "PF with Date (Int)", "PA with Date", "PF No Date (Ext)", etc.
                    # PF = Pending Fulfillment, PA = Pending Approval
                    # Use vectorized operations for better performance and reliability
                    
                    # Initialize Expected Ship Date as NaT
                    sales_order_line_items_df['Expected Ship Date'] = pd.NaT
                    
                    # Check for date columns (might have _header suffix if originals existed)
                    cpld_col = 'Customer Promise Last Date to Ship'
                    if cpld_col not in sales_order_line_items_df.columns and f'{cpld_col}_header' in sales_order_line_items_df.columns:
                        cpld_col = f'{cpld_col}_header'
                    
                    proj_col = 'Projected Date'
                    if proj_col not in sales_order_line_items_df.columns and f'{proj_col}_header' in sales_order_line_items_df.columns:
                        proj_col = f'{proj_col}_header'
                    
                    pa_date_col = 'Pending Approval Date'
                    if pa_date_col not in sales_order_line_items_df.columns and f'{pa_date_col}_header' in sales_order_line_items_df.columns:
                        pa_date_col = f'{pa_date_col}_header'
                    
                    status_col = 'Updated Status'
                    if status_col not in sales_order_line_items_df.columns and f'{status_col}_header' in sales_order_line_items_df.columns:
                        status_col = f'{status_col}_header'
                    
                    # Get the Updated Status as uppercase for matching
                    if status_col in sales_order_line_items_df.columns:
                        status_upper = sales_order_line_items_df[status_col].fillna('').astype(str).str.upper()
                        
                        # PF (Pending Fulfillment): Use Customer Promise Last Date to Ship, then Projected Date
                        pf_mask = status_upper.str.startswith('PF')
                        if cpld_col in sales_order_line_items_df.columns:
                            # Ensure dates are datetime
                            sales_order_line_items_df[cpld_col] = pd.to_datetime(sales_order_line_items_df[cpld_col], errors='coerce')
                            sales_order_line_items_df.loc[pf_mask, 'Expected Ship Date'] = sales_order_line_items_df.loc[pf_mask, cpld_col]
                        
                        # Fill any remaining PF rows with Projected Date
                        if proj_col in sales_order_line_items_df.columns:
                            sales_order_line_items_df[proj_col] = pd.to_datetime(sales_order_line_items_df[proj_col], errors='coerce')
                            pf_no_date = pf_mask & sales_order_line_items_df['Expected Ship Date'].isna()
                            sales_order_line_items_df.loc[pf_no_date, 'Expected Ship Date'] = sales_order_line_items_df.loc[pf_no_date, proj_col]
                        
                        # PA (Pending Approval): Use Pending Approval Date
                        pa_mask = status_upper.str.startswith('PA')
                        if pa_date_col in sales_order_line_items_df.columns:
                            sales_order_line_items_df[pa_date_col] = pd.to_datetime(sales_order_line_items_df[pa_date_col], errors='coerce')
                            sales_order_line_items_df.loc[pa_mask, 'Expected Ship Date'] = sales_order_line_items_df.loc[pa_mask, pa_date_col]
    
    # Process HubSpot Deals
    if not deals_df.empty:
        if deals_df.columns.duplicated().any():
            deals_df = deals_df.loc[:, ~deals_df.columns.duplicated()]
        
        if 'Amount' in deals_df.columns:
            deals_df['Amount'] = deals_df['Amount'].apply(clean_numeric)
        if 'Close Date' in deals_df.columns:
            deals_df['Close Date'] = pd.to_datetime(deals_df['Close Date'], errors='coerce')
        
        if 'Pipeline' in deals_df.columns:
            deals_df['Forecast Pipeline'] = deals_df['Pipeline'].apply(map_to_forecast_pipeline)
        
        if 'Deal Type' in deals_df.columns:
            deals_df['Forecast Category'] = deals_df['Deal Type'].apply(map_deal_type_to_forecast_category)
    
    # Process Deals Line Items for Close Rate Analysis
    if not deals_line_items_df.empty:
        if deals_line_items_df.columns.duplicated().any():
            deals_line_items_df = deals_line_items_df.loc[:, ~deals_line_items_df.columns.duplicated()]
        
        # =======================================================================
        # FILTER OUT STANDARD REORDER DEALS
        # If any of the "Date entered Standard Reorder..." columns have a value,
        # the deal was at some point a standard reorder and should be excluded
        # =======================================================================
        
        # Find which standard reorder columns are actually present in the dataframe
        present_reorder_cols = [col for col in deals_line_items_df.columns 
                                if 'Standard Reorder' in str(col)]
        
        if present_reorder_cols:
            # Create a flag: True if ANY of the standard reorder date columns have a value
            def has_standard_reorder_date(row):
                for col in present_reorder_cols:
                    val = row.get(col, None)
                    if pd.notna(val) and str(val).strip() != '':
                        return True
                return False
            
            deals_line_items_df['Is_Standard_Reorder'] = deals_line_items_df.apply(has_standard_reorder_date, axis=1)
            
            # Count how many we're filtering out (store for display later)
            reorder_line_items = deals_line_items_df['Is_Standard_Reorder'].sum()
            total_before = len(deals_line_items_df)
            
            # Count unique deals being filtered
            if 'Deal ID' in deals_line_items_df.columns:
                reorder_deals = deals_line_items_df[deals_line_items_df['Is_Standard_Reorder'] == True]['Deal ID'].nunique()
                total_deals_before = deals_line_items_df['Deal ID'].nunique()
            else:
                reorder_deals = reorder_line_items
                total_deals_before = total_before
            
            # Filter out standard reorder deals
            deals_line_items_df = deals_line_items_df[deals_line_items_df['Is_Standard_Reorder'] == False].copy()
            
            # Store the filtering stats as attributes on the dataframe
            deals_line_items_df.attrs['reorder_filtered_line_items'] = reorder_line_items
            deals_line_items_df.attrs['reorder_filtered_deals'] = reorder_deals
            deals_line_items_df.attrs['total_deals_before_filter'] = total_deals_before
        
        # =======================================================================
        # FILTER OUT DEALS BY DEAL OWNER LAST NAME (Gonzalez)
        # =======================================================================
        if 'Deal Owner Last Name' in deals_line_items_df.columns:
            # Count deals being filtered
            gonzalez_mask = deals_line_items_df['Deal Owner Last Name'].str.strip().str.lower() == 'gonzalez'
            gonzalez_line_items = gonzalez_mask.sum()
            
            if 'Deal ID' in deals_line_items_df.columns:
                gonzalez_deals = deals_line_items_df[gonzalez_mask]['Deal ID'].nunique()
            else:
                gonzalez_deals = gonzalez_line_items
            
            # Filter out Gonzalez deals
            deals_line_items_df = deals_line_items_df[~gonzalez_mask].copy()
            
            # Store the filtering stats
            deals_line_items_df.attrs['gonzalez_filtered_deals'] = gonzalez_deals
        
        # Clean numeric columns - use Effective Unit Price × Quantity for Amount
        if 'Effective unit price' in deals_line_items_df.columns:
            deals_line_items_df['Effective unit price'] = deals_line_items_df['Effective unit price'].apply(clean_numeric)
        if 'Quantity' in deals_line_items_df.columns:
            deals_line_items_df['Quantity'] = deals_line_items_df['Quantity'].apply(clean_numeric)
        
        # Calculate Amount as Effective Unit Price × Quantity
        if 'Effective unit price' in deals_line_items_df.columns and 'Quantity' in deals_line_items_df.columns:
            deals_line_items_df['Amount'] = deals_line_items_df['Effective unit price'] * deals_line_items_df['Quantity']
        elif 'Amount' in deals_line_items_df.columns:
            deals_line_items_df['Amount'] = deals_line_items_df['Amount'].apply(clean_numeric)
        
        # Parse dates
        if 'Create Date' in deals_line_items_df.columns:
            deals_line_items_df['Create Date'] = pd.to_datetime(deals_line_items_df['Create Date'], errors='coerce')
        if 'Close Date' in deals_line_items_df.columns:
            deals_line_items_df['Close Date'] = pd.to_datetime(deals_line_items_df['Close Date'], errors='coerce')
        
        # Apply SKU-based categorization using lookup from Invoice Line Items
        # WITH FALLBACK to Deal Type when SKU is null or maps to 'Other'
        if 'SKU' in deals_line_items_df.columns and sku_category_lookup:
            deals_line_items_df['SKU_Category'] = deals_line_items_df['SKU'].map(sku_category_lookup)
        else:
            deals_line_items_df['SKU_Category'] = None
            # Fallback: Map SKU column to Item for old categorization
            if 'SKU' in deals_line_items_df.columns:
                deals_line_items_df['Item'] = deals_line_items_df['SKU']
            if 'SKU Description' in deals_line_items_df.columns:
                deals_line_items_df['Item Description'] = deals_line_items_df['SKU Description']
            deals_line_items_df = apply_product_categories(deals_line_items_df)
        
        # Get Deal Type based category as fallback (Column G = "Deal Type")
        if 'Deal Type' in deals_line_items_df.columns:
            deals_line_items_df['DealType_Category'] = deals_line_items_df['Deal Type'].apply(map_deal_type_to_forecast_category)
        else:
            deals_line_items_df['DealType_Category'] = 'Other'
        
        # Use SKU category if available and not 'Other', otherwise use Deal Type category
        def get_best_category_dli(row):
            sku_cat = row.get('SKU_Category')
            deal_cat = row.get('DealType_Category', 'Other')
            
            # If SKU lookup succeeded and isn't 'Other', use it
            if pd.notna(sku_cat) and sku_cat != 'Other':
                return map_to_forecast_category(sku_cat, None)
            # Otherwise fall back to Deal Type
            return deal_cat
        
        deals_line_items_df['Forecast Category'] = deals_line_items_df.apply(get_best_category_dli, axis=1)
        
        # Create unified closed won flag
        # Closed Won if: Is Closed Won = TRUE, or Deal Stage in ['Sales Order Created in NS', 'NCR']
        def is_closed_won(row):
            # Check Is Closed Won column
            is_won = str(row.get('Is Closed Won', '')).strip().upper()
            if is_won in ['TRUE', 'YES', '1']:
                return True
            # Check Deal Stage for Sales Order Created in NS or NCR
            deal_stage = str(row.get('Deal Stage', '')).strip()
            if deal_stage in ['Sales Order Created in NS', 'NCR']:
                return True
            return False
        
        deals_line_items_df['Is_Won'] = deals_line_items_df.apply(is_closed_won, axis=1)
        
        # Create closed lost flag
        def is_closed_lost(row):
            is_lost = str(row.get('Is closed lost', '')).strip().upper()
            return is_lost in ['TRUE', 'YES', '1']
        
        deals_line_items_df['Is_Lost'] = deals_line_items_df.apply(is_closed_lost, axis=1)
        
        # Calculate days to close
        if 'Create Date' in deals_line_items_df.columns and 'Close Date' in deals_line_items_df.columns:
            deals_line_items_df['Days_To_Close'] = (
                deals_line_items_df['Close Date'] - deals_line_items_df['Create Date']
            ).dt.days
    
    # =======================================================================
    # PROCESS PIPELINE DEALS (Deals Line Item) FOR PIPELINE SECTION
    # No filtering - show all active pipeline deals
    # =======================================================================
    if not pipeline_deals_df.empty:
        if pipeline_deals_df.columns.duplicated().any():
            pipeline_deals_df = pipeline_deals_df.loc[:, ~pipeline_deals_df.columns.duplicated()]
        
        # Clean numeric columns - use Effective Unit Price × Quantity for Amount
        if 'Effective unit price' in pipeline_deals_df.columns:
            pipeline_deals_df['Effective unit price'] = pipeline_deals_df['Effective unit price'].apply(clean_numeric)
        if 'Quantity' in pipeline_deals_df.columns:
            pipeline_deals_df['Quantity'] = pipeline_deals_df['Quantity'].apply(clean_numeric)
        
        # Calculate Amount as Effective Unit Price × Quantity
        if 'Effective unit price' in pipeline_deals_df.columns and 'Quantity' in pipeline_deals_df.columns:
            pipeline_deals_df['Amount'] = pipeline_deals_df['Effective unit price'] * pipeline_deals_df['Quantity']
        elif 'Amount' in pipeline_deals_df.columns:
            pipeline_deals_df['Amount'] = pipeline_deals_df['Amount'].apply(clean_numeric)
        
        # Parse dates
        if 'Close Date' in pipeline_deals_df.columns:
            pipeline_deals_df['Close Date'] = pd.to_datetime(pipeline_deals_df['Close Date'], errors='coerce')
        if 'Create Date' in pipeline_deals_df.columns:
            pipeline_deals_df['Create Date'] = pd.to_datetime(pipeline_deals_df['Create Date'], errors='coerce')
        # Parse Pending Approval Date (Column V) - this is the date to use for filtering deals
        if 'Pending Approval Date' in pipeline_deals_df.columns:
            pipeline_deals_df['Pending Approval Date'] = pd.to_datetime(pipeline_deals_df['Pending Approval Date'], errors='coerce')
        
        # Map Pipeline to Forecast Pipeline
        if 'Pipeline' in pipeline_deals_df.columns:
            pipeline_deals_df['Forecast Pipeline'] = pipeline_deals_df['Pipeline'].apply(map_to_forecast_pipeline)
        
        # Apply SKU-based categorization using lookup from Invoice Line Items
        # WITH FALLBACK to Deal Type when SKU is null or maps to 'Other'
        if 'SKU' in pipeline_deals_df.columns and sku_category_lookup:
            pipeline_deals_df['SKU_Category'] = pipeline_deals_df['SKU'].map(sku_category_lookup)
        else:
            pipeline_deals_df['SKU_Category'] = None
        
        # Get Deal Type based category as fallback (Column G = "Deal Type")
        if 'Deal Type' in pipeline_deals_df.columns:
            pipeline_deals_df['DealType_Category'] = pipeline_deals_df['Deal Type'].apply(map_deal_type_to_forecast_category)
        else:
            pipeline_deals_df['DealType_Category'] = 'Other'
        
        # Use SKU category if available and not 'Other', otherwise use Deal Type category
        def get_best_category(row):
            sku_cat = row.get('SKU_Category')
            deal_cat = row.get('DealType_Category', 'Other')
            
            # If SKU lookup succeeded and isn't 'Other', use it
            if pd.notna(sku_cat) and sku_cat != 'Other':
                return map_to_forecast_category(sku_cat, None)
            # Otherwise fall back to Deal Type
            return deal_cat
        
        pipeline_deals_df['Forecast Category'] = pipeline_deals_df.apply(get_best_category, axis=1)
    
    return {
        'forecast': forecast_df,
        'line_items': line_items_df,
        'invoices': invoices_df,
        'sales_orders': sales_orders_df,
        'sales_order_line_items': sales_order_line_items_df,
        'deals': deals_df,
        'deals_line_items': deals_line_items_df,
        'pipeline_deals': pipeline_deals_df
    }
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_ytd_actuals"></a> `calculate_ytd_actuals` — L7047–L7097

```python
def calculate_ytd_actuals(line_items_df, year=2026):
    """Calculate YTD actuals by Pipeline and Category, including Total rows"""
    if line_items_df.empty:
        return pd.DataFrame()
    
    df = line_items_df.copy()
    if 'Date' in df.columns:
        df = df[df['Date'].dt.year == year]
    
    if df.empty:
        return pd.DataFrame()
    
    # Fill missing pipeline with 'Unmapped' so we don't lose revenue
    if 'Forecast Pipeline' in df.columns:
        df['Forecast Pipeline'] = df['Forecast Pipeline'].fillna('Unmapped')
    else:
        df['Forecast Pipeline'] = 'Unmapped'
    
    # Fill missing category with 'Other'
    if 'Forecast Category' in df.columns:
        df['Forecast Category'] = df['Forecast Category'].fillna('Other')
    else:
        df['Forecast Category'] = 'Other'
    
    # Base grouping: Pipeline x Category
    grouped = df.groupby(['Forecast Pipeline', 'Forecast Category']).agg({
        'Amount': 'sum'
    }).reset_index()
    grouped.columns = ['Pipeline', 'Category', 'Actual']
    
    # Create Category='Total' rows for each Pipeline
    pipeline_totals = df.groupby('Forecast Pipeline')['Amount'].sum().reset_index()
    pipeline_totals.columns = ['Pipeline', 'Actual']
    pipeline_totals['Category'] = 'Total'
    
    # Create Pipeline='Total' rows for each Category
    category_totals = df.groupby('Forecast Category')['Amount'].sum().reset_index()
    category_totals.columns = ['Category', 'Actual']
    category_totals['Pipeline'] = 'Total'
    
    # Create grand total row
    grand_total = pd.DataFrame([{
        'Pipeline': 'Total',
        'Category': 'Total',
        'Actual': df['Amount'].sum()
    }])
    
    # Combine all
    result = pd.concat([grouped, pipeline_totals, category_totals, grand_total], ignore_index=True)
    
    return result
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_ytd_actuals_total"></a> `calculate_ytd_actuals_total` — L7100–L7129

```python
def calculate_ytd_actuals_total(line_items_df, year=2026):
    """Calculate total YTD actuals (ignoring pipeline, just by category)"""
    if line_items_df.empty:
        return pd.DataFrame()
    
    df = line_items_df.copy()
    if 'Date' in df.columns:
        df = df[df['Date'].dt.year == year]
    
    if df.empty:
        return pd.DataFrame()
    
    # Fill missing category with 'Other'
    if 'Forecast Category' in df.columns:
        df['Forecast Category'] = df['Forecast Category'].fillna('Other')
    else:
        df['Forecast Category'] = 'Other'
    
    grouped = df.groupby('Forecast Category').agg({
        'Amount': 'sum'
    }).reset_index()
    
    grouped.columns = ['Category', 'Actual']
    
    # Add a 'Total' row
    total_actual = grouped['Actual'].sum()
    total_row = pd.DataFrame([{'Category': 'Total', 'Actual': total_actual}])
    grouped = pd.concat([grouped, total_row], ignore_index=True)
    
    return grouped
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_monthly_actuals"></a> `calculate_monthly_actuals` — L7132–L7183

```python
def calculate_monthly_actuals(line_items_df, year=2026):
    """Calculate monthly actuals by Pipeline and Category, including Total rows"""
    if line_items_df.empty:
        return pd.DataFrame()
    
    df = line_items_df.copy()
    if 'Date' in df.columns:
        df = df[df['Date'].dt.year == year]
        df['Month'] = df['Date'].dt.month
        df['Month_Name'] = df['Date'].dt.strftime('%B')
    
    if df.empty:
        return pd.DataFrame()
    
    # Fill missing pipeline with 'Unmapped'
    if 'Forecast Pipeline' in df.columns:
        df['Forecast Pipeline'] = df['Forecast Pipeline'].fillna('Unmapped')
    else:
        df['Forecast Pipeline'] = 'Unmapped'
    
    # Fill missing category with 'Other'
    if 'Forecast Category' in df.columns:
        df['Forecast Category'] = df['Forecast Category'].fillna('Other')
    else:
        df['Forecast Category'] = 'Other'
    
    # Base grouping
    grouped = df.groupby(['Forecast Pipeline', 'Forecast Category', 'Month', 'Month_Name']).agg({
        'Amount': 'sum'
    }).reset_index()
    grouped.columns = ['Pipeline', 'Category', 'Month_Num', 'Month', 'Actual']
    
    # Pipeline totals (Category='Total')
    pipeline_monthly = df.groupby(['Forecast Pipeline', 'Month', 'Month_Name'])['Amount'].sum().reset_index()
    pipeline_monthly.columns = ['Pipeline', 'Month_Num', 'Month', 'Actual']
    pipeline_monthly['Category'] = 'Total'
    
    # Category totals (Pipeline='Total')
    category_monthly = df.groupby(['Forecast Category', 'Month', 'Month_Name'])['Amount'].sum().reset_index()
    category_monthly.columns = ['Category', 'Month_Num', 'Month', 'Actual']
    category_monthly['Pipeline'] = 'Total'
    
    # Grand totals by month
    grand_monthly = df.groupby(['Month', 'Month_Name'])['Amount'].sum().reset_index()
    grand_monthly.columns = ['Month_Num', 'Month', 'Actual']
    grand_monthly['Pipeline'] = 'Total'
    grand_monthly['Category'] = 'Total'
    
    # Combine all
    result = pd.concat([grouped, pipeline_monthly, category_monthly, grand_monthly], ignore_index=True)
    
    return result
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_ytd_plan"></a> `get_ytd_plan` — L7186–L7196

```python
def get_ytd_plan(forecast_df, through_month):
    """Calculate YTD plan from forecast"""
    if forecast_df.empty:
        return pd.DataFrame()
    
    months_to_sum = MONTH_NAMES[:through_month]
    
    df = forecast_df.copy()
    df['YTD_Plan'] = df[months_to_sum].sum(axis=1)
    
    return df[['Pipeline', 'Category', 'YTD_Plan', 'Annual_Total']]
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_period_plan"></a> `get_period_plan` — L7199–L7241

```python
def get_period_plan(forecast_df, period_type, month=None, quarter=None):
    """
    Calculate plan for a specific time period (Month or Quarter).
    
    Args:
        forecast_df: Forecast dataframe with monthly columns
        period_type: 'Month' or 'Quarter'
        month: Month number (1-12) for Month period type
        quarter: Quarter number (1-4) for Quarter period type
    
    Returns:
        DataFrame with Pipeline, Category, and Period_Plan columns
    """
    if forecast_df.empty:
        return pd.DataFrame()
    
    df = forecast_df.copy()
    
    if period_type == 'Month' and month:
        # Get plan for a single month
        month_name = MONTH_NAMES[month - 1]  # 0-indexed
        if month_name in df.columns:
            df['Period_Plan'] = df[month_name]
        else:
            df['Period_Plan'] = 0
    elif period_type == 'Quarter' and quarter:
        # Get plan for a quarter (sum of 3 months)
        quarter_months = {
            1: ['January', 'February', 'March'],
            2: ['April', 'May', 'June'],
            3: ['July', 'August', 'September'],
            4: ['October', 'November', 'December']
        }
        months_to_sum = quarter_months.get(quarter, [])
        available_months = [m for m in months_to_sum if m in df.columns]
        if available_months:
            df['Period_Plan'] = df[available_months].sum(axis=1)
        else:
            df['Period_Plan'] = 0
    else:
        df['Period_Plan'] = 0
    
    return df[['Pipeline', 'Category', 'Period_Plan', 'Annual_Total']]
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_variance"></a> `calculate_variance` — L7244–L7264

```python
def calculate_variance(actuals_df, plan_df):
    """Calculate variance between actuals and plan"""
    if actuals_df.empty and plan_df.empty:
        return pd.DataFrame()
    
    merged = plan_df.merge(actuals_df, on=['Pipeline', 'Category'], how='left')
    
    merged['Actual'] = merged['Actual'].fillna(0)
    merged['Variance'] = merged['Actual'] - merged['YTD_Plan']
    merged['Variance_Pct'] = np.where(
        merged['YTD_Plan'] > 0,
        (merged['Actual'] / merged['YTD_Plan'] - 1) * 100,
        0
    )
    merged['Attainment_Pct'] = np.where(
        merged['YTD_Plan'] > 0,
        (merged['Actual'] / merged['YTD_Plan']) * 100,
        0
    )
    
    return merged
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_deals_for_export"></a> `get_deals_for_export` — L7271–L7337

```python
def get_deals_for_export(deals_line_items_df, filter_type=None, filter_value=None):
    """
    Get deals data formatted for export/download.
    
    Args:
        deals_line_items_df: The deals line items dataframe
        filter_type: 'pipeline', 'category', 'close_status', or None for all
        filter_value: The value to filter by (e.g., 'Retention', 'Labels', 'Commit')
    
    Returns:
        DataFrame with unique deals ready for export
    """
    if deals_line_items_df.empty:
        return pd.DataFrame()
    
    df = deals_line_items_df.copy()
    
    # Get unique deals (deduplicate by Deal ID)
    deal_id_col = 'Deal ID' if 'Deal ID' in df.columns else None
    
    # Columns to include in export
    export_cols = [
        'Deal ID', 'Deal Name', 'Company Name', 'Primary Associated Company',
        'Deal Owner First Name', 'Deal Owner Last Name', 'Pipeline', 
        'Deal Stage', 'Close Status', 'Deal Type', 'Amount',
        'Create Date', 'Close Date', 'Days_To_Close',
        'Is_Won', 'Is_Lost', 'Forecast Category', 'Product Category'
    ]
    
    # Build aggregation dict dynamically based on available columns
    agg_dict = {}
    for col in export_cols:
        if col in df.columns and col != deal_id_col:
            agg_dict[col] = 'first'
    
    if deal_id_col:
        unique_deals = df.groupby(deal_id_col).agg(agg_dict).reset_index()
    else:
        deal_name_col = 'Deal Name' if 'Deal Name' in df.columns else None
        if deal_name_col and 'Deal Name' in agg_dict:
            del agg_dict['Deal Name']
        if deal_name_col:
            unique_deals = df.groupby(deal_name_col).agg(agg_dict).reset_index()
        else:
            unique_deals = df.copy()
    
    # Filter to closed deals only
    unique_deals = unique_deals[(unique_deals['Is_Won'] == True) | (unique_deals['Is_Lost'] == True)]
    
    # Apply filter if specified
    if filter_type and filter_value:
        if filter_type == 'pipeline' and 'Pipeline' in unique_deals.columns:
            unique_deals = unique_deals[unique_deals['Pipeline'] == filter_value]
        elif filter_type == 'category' and 'Forecast Category' in unique_deals.columns:
            unique_deals = unique_deals[unique_deals['Forecast Category'] == filter_value]
        elif filter_type == 'close_status' and 'Close Status' in unique_deals.columns:
            unique_deals = unique_deals[unique_deals['Close Status'] == filter_value]
    
    # Clean up for export - keep only available columns
    available_cols = [c for c in export_cols if c in unique_deals.columns]
    export_df = unique_deals[available_cols].copy()
    
    # Add a win/loss status column for clarity
    if 'Is_Won' in export_df.columns:
        export_df['Status'] = export_df['Is_Won'].apply(lambda x: 'Won' if x else 'Lost')
    
    return export_df
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_close_rate_metrics"></a> `calculate_close_rate_metrics` — L7340–L7451

```python
def calculate_close_rate_metrics(deals_line_items_df):
    """
    Calculate close rate metrics from deals line items.
    Returns dict with overall stats and breakdowns.
    
    Key insight: Amount is repeated for each line item in a deal, so we need to 
    deduplicate by Deal ID when calculating deal-level amounts.
    """
    if deals_line_items_df.empty:
        return None
    
    df = deals_line_items_df.copy()
    
    # Get unique deals for accurate deal-level metrics
    # Amount is the same for all line items in a deal, so we take the first occurrence
    deal_id_col = 'Deal ID' if 'Deal ID' in df.columns else None
    
    # Build aggregation dict dynamically based on available columns
    agg_dict = {}
    potential_cols = [
        'Amount', 'Is_Won', 'Is_Lost', 'Close Status', 'Deal Stage', 'Pipeline',
        'Deal Type', 'Create Date', 'Close Date', 'Days_To_Close', 'Deal Name',
        'Deal Owner First Name', 'Deal Owner Last Name', 'Company Name', 'Primary Associated Company'
    ]
    for col in potential_cols:
        if col in df.columns:
            agg_dict[col] = 'first'
    
    if deal_id_col:
        # Deduplicate to get unique deals with their amounts
        unique_deals = df.groupby(deal_id_col).agg(agg_dict).reset_index()
    else:
        # Fallback if no Deal ID - use Deal Name as identifier
        deal_name_col = 'Deal Name' if 'Deal Name' in df.columns else None
        if deal_name_col:
            # Remove Deal Name from agg dict if it's the groupby column
            if 'Deal Name' in agg_dict:
                del agg_dict['Deal Name']
            unique_deals = df.groupby(deal_name_col).agg(agg_dict).reset_index()
        else:
            unique_deals = df.copy()
    
    # Filter to only closed deals (won or lost)
    closed_deals = unique_deals[(unique_deals['Is_Won'] == True) | (unique_deals['Is_Lost'] == True)]
    
    # Overall close rate metrics
    total_closed = len(closed_deals)
    total_won = len(closed_deals[closed_deals['Is_Won'] == True])
    total_lost = len(closed_deals[closed_deals['Is_Lost'] == True])
    
    overall_close_rate = (total_won / total_closed * 100) if total_closed > 0 else 0
    
    total_won_amount = closed_deals[closed_deals['Is_Won'] == True]['Amount'].sum()
    total_lost_amount = closed_deals[closed_deals['Is_Lost'] == True]['Amount'].sum()
    total_closed_amount = total_won_amount + total_lost_amount
    
    amount_close_rate = (total_won_amount / total_closed_amount * 100) if total_closed_amount > 0 else 0
    
    # Close rate by Close Status (probability scores)
    close_status_rates = {}
    if 'Close Status' in closed_deals.columns:
        for status in ['Expect', 'Commit', 'Best Case', 'Opportunity']:
            status_deals = closed_deals[closed_deals['Close Status'] == status]
            status_total = len(status_deals)
            status_won = len(status_deals[status_deals['Is_Won'] == True])
            status_rate = (status_won / status_total * 100) if status_total > 0 else 0
            
            status_amount_total = status_deals['Amount'].sum()
            status_amount_won = status_deals[status_deals['Is_Won'] == True]['Amount'].sum()
            status_amount_rate = (status_amount_won / status_amount_total * 100) if status_amount_total > 0 else 0
            
            close_status_rates[status] = {
                'total_deals': status_total,
                'won_deals': status_won,
                'lost_deals': status_total - status_won,
                'close_rate_count': status_rate,
                'total_amount': status_amount_total,
                'won_amount': status_amount_won,
                'close_rate_amount': status_amount_rate
            }
    
    # Days to close statistics
    won_deals = closed_deals[closed_deals['Is_Won'] == True]
    days_to_close_stats = {}
    if 'Days_To_Close' in won_deals.columns:
        valid_days = won_deals['Days_To_Close'].dropna()
        if len(valid_days) > 0:
            days_to_close_stats = {
                'mean': valid_days.mean(),
                'median': valid_days.median(),
                'min': valid_days.min(),
                'max': valid_days.max(),
                'std': valid_days.std() if len(valid_days) > 1 else 0,
                'count': len(valid_days)
            }
    
    return {
        'unique_deals': unique_deals,
        'closed_deals': closed_deals,
        'overall': {
            'total_closed': total_closed,
            'total_won': total_won,
            'total_lost': total_lost,
            'close_rate_count': overall_close_rate,
            'total_closed_amount': total_closed_amount,
            'total_won_amount': total_won_amount,
            'total_lost_amount': total_lost_amount,
            'close_rate_amount': amount_close_rate
        },
        'by_close_status': close_status_rates,
        'days_to_close': days_to_close_stats
    }
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_close_rate_by_category"></a> `calculate_close_rate_by_category` — L7454–L7498

```python
def calculate_close_rate_by_category(deals_line_items_df):
    """
    Calculate close rate by product category using SKU categorization.
    This uses line-item level data since categories are SKU-specific.
    """
    if deals_line_items_df.empty or 'Product Category' not in deals_line_items_df.columns:
        return pd.DataFrame()
    
    df = deals_line_items_df.copy()
    
    # Filter to closed deals only
    df = df[(df['Is_Won'] == True) | (df['Is_Lost'] == True)]
    
    if df.empty:
        return pd.DataFrame()
    
    # Group by category and calculate metrics
    category_metrics = []
    
    for category in df['Product Category'].dropna().unique():
        cat_df = df[df['Product Category'] == category]
        
        total_qty = cat_df['Quantity'].sum() if 'Quantity' in cat_df.columns else len(cat_df)
        won_qty = cat_df[cat_df['Is_Won'] == True]['Quantity'].sum() if 'Quantity' in cat_df.columns else len(cat_df[cat_df['Is_Won'] == True])
        
        # Also track by unique deals in this category
        if 'Deal ID' in cat_df.columns:
            unique_deals = cat_df.groupby('Deal ID')['Is_Won'].first()
            deal_count = len(unique_deals)
            deal_won_count = unique_deals.sum()
        else:
            deal_count = len(cat_df.drop_duplicates(subset=['Deal Name'])) if 'Deal Name' in cat_df.columns else len(cat_df)
            deal_won_count = len(cat_df[cat_df['Is_Won'] == True].drop_duplicates(subset=['Deal Name'])) if 'Deal Name' in cat_df.columns else len(cat_df[cat_df['Is_Won'] == True])
        
        category_metrics.append({
            'Category': category,
            'Total Deals': deal_count,
            'Won Deals': deal_won_count,
            'Lost Deals': deal_count - deal_won_count,
            'Close Rate': (deal_won_count / deal_count * 100) if deal_count > 0 else 0,
            'Total Qty': total_qty,
            'Won Qty': won_qty
        })
    
    return pd.DataFrame(category_metrics).sort_values('Total Deals', ascending=False)
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_close_rate_by_pipeline"></a> `calculate_close_rate_by_pipeline` — L7501–L7551

```python
def calculate_close_rate_by_pipeline(deals_line_items_df):
    """
    Calculate close rate by pipeline.
    """
    if deals_line_items_df.empty or 'Pipeline' not in deals_line_items_df.columns:
        return pd.DataFrame()
    
    df = deals_line_items_df.copy()
    
    # Get unique deals
    deal_id_col = 'Deal ID' if 'Deal ID' in df.columns else 'Deal Name'
    
    if deal_id_col not in df.columns:
        return pd.DataFrame()
    
    unique_deals = df.groupby(deal_id_col).agg({
        'Amount': 'first',
        'Is_Won': 'first',
        'Is_Lost': 'first',
        'Pipeline': 'first'
    }).reset_index()
    
    # Filter to closed deals
    closed_deals = unique_deals[(unique_deals['Is_Won'] == True) | (unique_deals['Is_Lost'] == True)]
    
    if closed_deals.empty:
        return pd.DataFrame()
    
    # Group by pipeline
    pipeline_metrics = []
    
    for pipeline in closed_deals['Pipeline'].dropna().unique():
        pipe_df = closed_deals[closed_deals['Pipeline'] == pipeline]
        
        total_deals = len(pipe_df)
        won_deals = len(pipe_df[pipe_df['Is_Won'] == True])
        won_amount = pipe_df[pipe_df['Is_Won'] == True]['Amount'].sum()
        total_amount = pipe_df['Amount'].sum()
        
        pipeline_metrics.append({
            'Pipeline': pipeline,
            'Total Deals': total_deals,
            'Won Deals': won_deals,
            'Lost Deals': total_deals - won_deals,
            'Close Rate (Count)': (won_deals / total_deals * 100) if total_deals > 0 else 0,
            'Won Amount': won_amount,
            'Total Amount': total_amount,
            'Close Rate (Amount)': (won_amount / total_amount * 100) if total_amount > 0 else 0
        })
    
    return pd.DataFrame(pipeline_metrics).sort_values('Total Deals', ascending=False)
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_days_to_close_by_amount_bucket"></a> `calculate_days_to_close_by_amount_bucket` — L7554–L7616

```python
def calculate_days_to_close_by_amount_bucket(deals_line_items_df):
    """
    Calculate average days to close by deal amount buckets.
    """
    if deals_line_items_df.empty:
        return pd.DataFrame()
    
    df = deals_line_items_df.copy()
    
    # Get unique deals
    deal_id_col = 'Deal ID' if 'Deal ID' in df.columns else 'Deal Name'
    
    if deal_id_col not in df.columns:
        return pd.DataFrame()
    
    unique_deals = df.groupby(deal_id_col).agg({
        'Amount': 'first',
        'Is_Won': 'first',
        'Days_To_Close': 'first'
    }).reset_index()
    
    # Filter to won deals with valid days
    won_deals = unique_deals[
        (unique_deals['Is_Won'] == True) & 
        (unique_deals['Days_To_Close'].notna()) &
        (unique_deals['Days_To_Close'] >= 0)
    ]
    
    if won_deals.empty:
        return pd.DataFrame()
    
    # Create amount buckets
    def get_amount_bucket(amount):
        if amount < 5000:
            return '$0 - $5K'
        elif amount < 15000:
            return '$5K - $15K'
        elif amount < 50000:
            return '$15K - $50K'
        elif amount < 100000:
            return '$50K - $100K'
        else:
            return '$100K+'
    
    won_deals['Amount Bucket'] = won_deals['Amount'].apply(get_amount_bucket)
    
    # Order buckets correctly
    bucket_order = ['$0 - $5K', '$5K - $15K', '$15K - $50K', '$50K - $100K', '$100K+']
    
    bucket_metrics = []
    for bucket in bucket_order:
        bucket_df = won_deals[won_deals['Amount Bucket'] == bucket]
        if len(bucket_df) > 0:
            bucket_metrics.append({
                'Amount Bucket': bucket,
                'Deal Count': len(bucket_df),
                'Avg Days to Close': bucket_df['Days_To_Close'].mean(),
                'Median Days': bucket_df['Days_To_Close'].median(),
                'Min Days': bucket_df['Days_To_Close'].min(),
                'Max Days': bucket_df['Days_To_Close'].max()
            })
    
    return pd.DataFrame(bucket_metrics)
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_avg_deal_size_by_pipeline"></a> `calculate_avg_deal_size_by_pipeline` — L7623–L7668

```python
def calculate_avg_deal_size_by_pipeline(deals_line_items_df):
    """
    Calculate average deal size for WON deals by pipeline.
    Uses unique deals to avoid double-counting from line items.
    """
    if deals_line_items_df.empty:
        return {}
    
    df = deals_line_items_df.copy()
    
    # Get unique deals
    deal_id_col = 'Deal ID' if 'Deal ID' in df.columns else 'Deal Name'
    if deal_id_col not in df.columns:
        return {}
    
    # Only won deals
    won_deals = df[df['Is_Won'] == True].copy()
    if won_deals.empty:
        return {}
    
    unique_won = won_deals.groupby(deal_id_col).agg({
        'Amount': 'first',
        'Pipeline': 'first'
    }).reset_index()
    
    # Calculate by pipeline
    avg_by_pipeline = {}
    for pipeline in unique_won['Pipeline'].dropna().unique():
        pipe_deals = unique_won[unique_won['Pipeline'] == pipeline]
        if len(pipe_deals) > 0:
            avg_by_pipeline[pipeline] = {
                'avg_deal_size': pipe_deals['Amount'].mean(),
                'median_deal_size': pipe_deals['Amount'].median(),
                'total_deals': len(pipe_deals),
                'total_revenue': pipe_deals['Amount'].sum()
            }
    
    # Overall average
    avg_by_pipeline['Overall'] = {
        'avg_deal_size': unique_won['Amount'].mean(),
        'median_deal_size': unique_won['Amount'].median(),
        'total_deals': len(unique_won),
        'total_revenue': unique_won['Amount'].sum()
    }
    
    return avg_by_pipeline
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_pipeline_expected_revenue"></a> `calculate_pipeline_expected_revenue` — L7671–L7761

```python
def calculate_pipeline_expected_revenue(open_deals_df, close_rates_by_status, close_rates_by_pipeline):
    """
    Calculate expected revenue from open pipeline deals.
    
    Uses historical close rates to weight each deal:
    - If Close Status available: use status-specific rate
    - Fallback to pipeline-specific rate
    - Fallback to overall rate
    
    Returns dict with expected revenue calculations.
    """
    if open_deals_df.empty:
        return {
            'total_pipeline_value': 0,
            'expected_revenue': 0,
            'by_status': {},
            'by_pipeline': {},
            'deal_count': 0
        }
    
    df = open_deals_df.copy()
    
    # Get overall fallback rate
    overall_rate = 50.0  # Default assumption
    if 'Overall' in close_rates_by_pipeline:
        # Use weighted average across pipelines
        total_deals = sum(p.get('total_deals', 0) for p in close_rates_by_pipeline.values() if isinstance(p, dict))
        if total_deals > 0:
            weighted_sum = sum(
                p.get('close_rate', 50) * p.get('total_deals', 0) 
                for p in close_rates_by_pipeline.values() 
                if isinstance(p, dict)
            )
            overall_rate = weighted_sum / total_deals
    
    # Calculate expected value for each deal
    def get_expected_value(row):
        amount = row.get('Amount', 0) or 0
        close_status = row.get('Close Status', '')
        pipeline = row.get('Pipeline', '')
        
        # Priority 1: Close Status specific rate
        if close_status and close_status in close_rates_by_status:
            rate = close_rates_by_status[close_status].get('close_rate_count', overall_rate)
            return amount * (rate / 100), rate, 'status'
        
        # Priority 2: Pipeline specific rate
        if pipeline and pipeline in close_rates_by_pipeline:
            rate = close_rates_by_pipeline[pipeline].get('close_rate', overall_rate)
            return amount * (rate / 100), rate, 'pipeline'
        
        # Fallback to overall
        return amount * (overall_rate / 100), overall_rate, 'overall'
    
    df['Expected_Value'], df['Applied_Rate'], df['Rate_Source'] = zip(*df.apply(get_expected_value, axis=1))
    
    total_pipeline_value = df['Amount'].sum()
    expected_revenue = df['Expected_Value'].sum()
    
    # Breakdown by Close Status
    by_status = {}
    if 'Close Status' in df.columns:
        for status in df['Close Status'].dropna().unique():
            status_df = df[df['Close Status'] == status]
            by_status[status] = {
                'deal_count': len(status_df),
                'pipeline_value': status_df['Amount'].sum(),
                'expected_revenue': status_df['Expected_Value'].sum(),
                'applied_rate': status_df['Applied_Rate'].mean()
            }
    
    # Breakdown by Pipeline
    by_pipeline = {}
    if 'Pipeline' in df.columns:
        for pipeline in df['Pipeline'].dropna().unique():
            pipe_df = df[df['Pipeline'] == pipeline]
            by_pipeline[pipeline] = {
                'deal_count': len(pipe_df),
                'pipeline_value': pipe_df['Amount'].sum(),
                'expected_revenue': pipe_df['Expected_Value'].sum(),
                'applied_rate': pipe_df['Applied_Rate'].mean()
            }
    
    return {
        'total_pipeline_value': total_pipeline_value,
        'expected_revenue': expected_revenue,
        'by_status': by_status,
        'by_pipeline': by_pipeline,
        'deal_count': len(df),
        'details': df
    }
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_revenue_gap_analysis"></a> `calculate_revenue_gap_analysis` — L7764–L7804

```python
def calculate_revenue_gap_analysis(revenue_target, current_actuals, expected_pipeline, 
                                    avg_deal_size, close_rate):
    """
    Calculate gap to revenue target and deals/opportunities needed.
    
    Formulas:
    - Revenue Gap = Target - (Actuals + Expected Pipeline)
    - Deals Needed = Gap / Avg Deal Size
    - Opportunities Needed = Gap / (Close Rate × Avg Deal Size)
    """
    # What we expect to have
    projected_total = current_actuals + expected_pipeline
    
    # Gap to target
    revenue_gap = revenue_target - projected_total
    
    # Deals needed to close gap (assuming we win them all)
    deals_needed = revenue_gap / avg_deal_size if avg_deal_size > 0 else 0
    
    # Opportunities needed (accounting for close rate)
    close_rate_decimal = close_rate / 100 if close_rate > 1 else close_rate
    opportunities_needed = revenue_gap / (close_rate_decimal * avg_deal_size) if (close_rate_decimal * avg_deal_size) > 0 else 0
    
    # Attainment projections
    projected_attainment = (projected_total / revenue_target * 100) if revenue_target > 0 else 0
    current_attainment = (current_actuals / revenue_target * 100) if revenue_target > 0 else 0
    
    return {
        'revenue_target': revenue_target,
        'current_actuals': current_actuals,
        'expected_pipeline': expected_pipeline,
        'projected_total': projected_total,
        'revenue_gap': revenue_gap,
        'deals_needed': max(0, deals_needed),  # Can't need negative deals
        'opportunities_needed': max(0, opportunities_needed),
        'projected_attainment': projected_attainment,
        'current_attainment': current_attainment,
        'avg_deal_size': avg_deal_size,
        'close_rate': close_rate,
        'on_track': revenue_gap <= 0
    }
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-calculate_monthly_deals_needed"></a> `calculate_monthly_deals_needed` — L7807–L7822

```python
def calculate_monthly_deals_needed(gap_analysis, months_remaining):
    """
    Calculate deals/opportunities needed per month to close the gap.
    """
    if months_remaining <= 0:
        return {
            'deals_per_month': 0,
            'opportunities_per_month': 0,
            'revenue_per_month': 0
        }
    
    return {
        'deals_per_month': gap_analysis['deals_needed'] / months_remaining,
        'opportunities_per_month': gap_analysis['opportunities_needed'] / months_remaining,
        'revenue_per_month': gap_analysis['revenue_gap'] / months_remaining
    }
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-create_attainment_gauge"></a> `create_attainment_gauge` — L7829–L7866

```python
def create_attainment_gauge(value, max_value, title, color='#3b82f6'):
    """Create a progress gauge"""
    pct = (value / max_value * 100) if max_value > 0 else 0
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=pct,
        number={'suffix': '%', 'font': {'size': 36, 'color': '#f1f5f9'}},
        delta={'reference': 100, 'relative': False, 'position': 'bottom',
               'increasing': {'color': '#10b981'}, 'decreasing': {'color': '#ef4444'}},
        title={'text': title, 'font': {'size': 14, 'color': '#94a3b8'}},
        gauge={
            'axis': {'range': [0, 120], 'tickcolor': '#475569', 'tickfont': {'color': '#64748b'}},
            'bar': {'color': color},
            'bgcolor': '#1e293b',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 80], 'color': '#1e293b'},
                {'range': [80, 100], 'color': '#1e293b'},
                {'range': [100, 120], 'color': '#1e293b'}
            ],
            'threshold': {
                'line': {'color': '#10b981', 'width': 3},
                'thickness': 0.8,
                'value': 100
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': '#f1f5f9'},
        height=200,
        margin=dict(t=80, b=20, l=30, r=30)
    )
    
    return fig
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-embed_chart"></a> `embed_chart` — L304–L321

```python
def embed_chart(fig, chart_key):
        """Try to embed chart as image, fall back to interactive HTML"""
        nonlocal charts_generated
        if fig is None:
            return
        
        # First try static image (best for PDF)
        img_b64 = fig_to_base64(fig)
        if img_b64:
            charts_html[chart_key] = f'<div class="chart-container"><img src="data:image/png;base64,{img_b64}"></div>'
            charts_generated += 1
            return
        
        # Fall back to interactive HTML embed
        html_embed = fig_to_html_embed(fig)
        if html_embed:
            charts_html[chart_key] = f'<div class="chart-container">{html_embed}</div>'
            charts_generated += 1
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_customer_friendly_status"></a> `get_customer_friendly_status` — L767–L774

```python
def get_customer_friendly_status(status):
        status_map = {
            'Commit': 'Confirmed',      # Basically a done deal
            'Expect': 'Likely',         # High confidence
            'Best Case': 'Tentative',   # Medium confidence, still being finalized
            'Opportunity': 'In Discussion'  # Early stage conversations
        }
        return status_map.get(status, status)
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_customer_friendly_status"></a> `get_customer_friendly_status` — L4554–L4561

```python
def get_customer_friendly_status(status):
        status_map = {
            'Commit': 'Confirmed',
            'Expect': 'Likely',
            'Best Case': 'Tentative',
            'Opportunity': 'In Discussion'
        }
        return status_map.get(status, status)
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-categorize_row"></a> `categorize_row` — L5077–L5134

```python
def categorize_row(row):
        """Categorize a single row based on Calyx columns"""
        # Get column values
        product_type_raw = ''
        item_type_raw = ''
        item_name = ''
        item_desc = ''
        
        if product_type_col and product_type_col in row.index:
            val = row[product_type_col]
            if pd.notna(val):
                product_type_raw = str(val).strip()
        
        if item_type_col and item_type_col in row.index:
            val = row[item_type_col]
            if pd.notna(val):
                item_type_raw = str(val).strip()
        
        if item_col and item_col in row.index:
            val = row[item_col]
            if pd.notna(val):
                item_name = str(val).strip()
        
        if item_desc_col and item_desc_col in row.index:
            val = row[item_desc_col]
            if pd.notna(val):
                item_desc = str(val).strip()
        
        product_type = product_type_raw.lower()
        item_type = item_type_raw.lower()
        item_name_lower = item_name.lower()
        item_desc_lower = item_desc.lower()
        
        # OVERRIDE 1: Check for Tooling Fee in item name - always categorize as Other
        # This catches "Tooling Fee - Labels" which shouldn't be in Labels
        if 'tooling fee' in item_name_lower or 'tooling fee' in item_desc_lower:
            return ('Other', 'Tooling Fee', None)
        
        # OVERRIDE 2: Check Calyx | Item Type for "ShipItem" - this is shipping
        if item_type == 'shipitem' or item_type == 'shipping':
            return ('Shipping', 'Shipping', None)
        
        # PRIMARY: Check Calyx || Product Type
        if product_type and product_type in PRODUCT_TYPE_TO_CATEGORY:
            category = PRODUCT_TYPE_TO_CATEGORY[product_type]
            return (category, product_type_raw, None)
        
        # FALLBACK: Check Calyx | Item Type for other types
        if item_type and item_type in ITEM_TYPE_TO_CATEGORY:
            category = ITEM_TYPE_TO_CATEGORY[item_type]
            return (category, item_type_raw, None)
        
        # If we have a product type that's not in our mapping, categorize as Other
        if product_type_raw:
            return ('Other', product_type_raw, None)
        
        # Default fallback
        return ('Other', 'Uncategorized', None)
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_unified_category"></a> `get_unified_category` — L5267–L5306

```python
def get_unified_category(row):
        cat = row.get('Product Category', 'Other')
        subcat = row.get('Product Sub-Category', '')
        component = row.get('Component Type', '')
        
        # For categories that are already complete products
        if cat in ['Tubes', 'Boxes', 'Flexpack', 'Calyx Cure', 'Fees & Adjustments', 'Other']:
            return cat
        
        # For Drams - unify base + lid + labels
        if cat == 'Drams':
            # Extract size (15D, 25D, 45D, 145D)
            size_match = re.search(r'(\d+D)', str(subcat))
            if size_match:
                return f"Drams ({size_match.group(1)})"
            return 'Drams'
        
        # For Concentrates - unify jar + lid
        if cat == 'Concentrates':
            size_match = re.search(r'(4mL|7mL)', str(subcat))
            if size_match:
                return f"Concentrates ({size_match.group(1)})"
            # Universal lids without clear size match
            if 'lid' in str(subcat).lower() or 'universal' in str(subcat).lower():
                return 'Concentrate Lids'
            return 'Concentrates'
        
        # For Calyx Jar
        if cat == 'Calyx Jar':
            return 'Calyx Jar'
        
        # For accessories - keep unified as Dram Accessories (shows in sub-breakdown)
        if cat == 'Dram Accessories':
            return 'Dram Accessories'
        
        # For labels
        if cat == 'Non-Core Labels':
            return 'Non-Core Labels'
        
        return cat
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_parent_category"></a> `get_parent_category` — L5312–L5327

```python
def get_parent_category(unified_cat):
        if pd.isna(unified_cat):
            return 'Other'
        
        unified = str(unified_cat)
        
        # Roll up Drams (25D, 45D, 15D, 145D) and Dram Accessories → Drams
        if unified.startswith('Drams') or unified == 'Dram Accessories':
            return 'Drams'
        
        # Roll up Concentrates (4mL, 7mL) and Concentrate Lids → Concentrates
        if unified.startswith('Concentrates') or unified == 'Concentrate Lids':
            return 'Concentrates'
        
        # Everything else stays as-is
        return unified
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_amount_bucket"></a> `get_amount_bucket` — L7586–L7596

```python
def get_amount_bucket(amount):
        if amount < 5000:
            return '$0 - $5K'
        elif amount < 15000:
            return '$5K - $15K'
        elif amount < 50000:
            return '$15K - $50K'
        elif amount < 100000:
            return '$50K - $100K'
        else:
            return '$100K+'
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_expected_value"></a> `get_expected_value` — L7707–L7723

```python
def get_expected_value(row):
        amount = row.get('Amount', 0) or 0
        close_status = row.get('Close Status', '')
        pipeline = row.get('Pipeline', '')
        
        # Priority 1: Close Status specific rate
        if close_status and close_status in close_rates_by_status:
            rate = close_rates_by_status[close_status].get('close_rate_count', overall_rate)
            return amount * (rate / 100), rate, 'status'
        
        # Priority 2: Pipeline specific rate
        if pipeline and pipeline in close_rates_by_pipeline:
            rate = close_rates_by_pipeline[pipeline].get('close_rate', overall_rate)
            return amount * (rate / 100), rate, 'pipeline'
        
        # Fallback to overall
        return amount * (overall_rate / 100), overall_rate, 'overall'
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-aging_bucket"></a> `aging_bucket` — L2012–L2017

```python
def aging_bucket(days):
            if days <= 0: return 'Current'
            elif days <= 30: return '1-30 Days'
            elif days <= 60: return '31-60 Days'
            elif days <= 90: return '61-90 Days'
            else: return '90+ Days'
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-aging_bucket"></a> `aging_bucket` — L4199–L4209

```python
def aging_bucket(days):
            if days <= 0:
                return "Current"
            elif days <= 30:
                return "1-30 Days"
            elif days <= 60:
                return "31-60 Days"
            elif days <= 90:
                return "61-90 Days"
            else:
                return "90+ Days"
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-categorize_frequency"></a> `categorize_frequency` — L5740–L5748

```python
def categorize_frequency(occasions):
            if occasions >= 10:
                return "Core Product"
            elif occasions >= 5:
                return "Regular Product"
            elif occasions >= 2:
                return "Repeat Product"
            else:
                return "One-Time Product"
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-pattern_indicator"></a> `pattern_indicator` — L5823–L5830

```python
def pattern_indicator(pattern):
            indicators = {
                'Core Product': '🟢',
                'Regular Product': '🔵',
                'Repeat Product': '🟠',
                'One-Time Product': '⚪'
            }
            return indicators.get(pattern, '⚪')
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_best_category_dli"></a> `get_best_category_dli` — L6932–L6940

```python
def get_best_category_dli(row):
            sku_cat = row.get('SKU_Category')
            deal_cat = row.get('DealType_Category', 'Other')
            
            # If SKU lookup succeeded and isn't 'Other', use it
            if pd.notna(sku_cat) and sku_cat != 'Other':
                return map_to_forecast_category(sku_cat, None)
            # Otherwise fall back to Deal Type
            return deal_cat
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-is_closed_won"></a> `is_closed_won` — L6946–L6955

```python
def is_closed_won(row):
            # Check Is Closed Won column
            is_won = str(row.get('Is Closed Won', '')).strip().upper()
            if is_won in ['TRUE', 'YES', '1']:
                return True
            # Check Deal Stage for Sales Order Created in NS or NCR
            deal_stage = str(row.get('Deal Stage', '')).strip()
            if deal_stage in ['Sales Order Created in NS', 'NCR']:
                return True
            return False
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-is_closed_lost"></a> `is_closed_lost` — L6960–L6962

```python
def is_closed_lost(row):
            is_lost = str(row.get('Is closed lost', '')).strip().upper()
            return is_lost in ['TRUE', 'YES', '1']
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_best_category"></a> `get_best_category` — L7019–L7027

```python
def get_best_category(row):
            sku_cat = row.get('SKU_Category')
            deal_cat = row.get('DealType_Category', 'Other')
            
            # If SKU lookup succeeded and isn't 'Other', use it
            if pd.notna(sku_cat) and sku_cat != 'Other':
                return map_to_forecast_category(sku_cat, None)
            # Otherwise fall back to Deal Type
            return deal_cat
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-extract_customer_from_ticket"></a> `extract_customer_from_ticket` — L3714–L3742

```python
def extract_customer_from_ticket(ticket_name):
                """Extract customer name from ticket formats:
                - 'NCR ### - Customer Name' (with dash)
                - 'NCR ### Customer Name' (no dash)
                - Also extracts NCR number for reference
                """
                import re
                if not ticket_name or ticket_name == '' or pd.isna(ticket_name):
                    return ''
                
                ticket_str = str(ticket_name).strip()
                
                # Pattern 1: "NCR ### - Customer Name" (with dash)
                if ' - ' in ticket_str:
                    parts = ticket_str.split(' - ', 1)
                    if len(parts) > 1:
                        customer_part = parts[1].strip()
                        # Remove any trailing issue description (after another dash or parenthetical)
                        # e.g., "Acreage (OH) Smearing" -> "Acreage (OH)"
                        return customer_part
                
                # Pattern 2: "NCR ### Customer Name" (no dash)
                # Match NCR followed by number, then capture everything after
                ncr_match = re.match(r'NCR\s*(\d+)\s+(.+)', ticket_str, re.IGNORECASE)
                if ncr_match:
                    customer_part = ncr_match.group(2).strip()
                    return customer_part
                
                return ''
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-extract_ncr_number_from_ticket"></a> `extract_ncr_number_from_ticket` — L3744–L3754

```python
def extract_ncr_number_from_ticket(ticket_name):
                """Extract NCR number from ticket name"""
                import re
                if not ticket_name or ticket_name == '' or pd.isna(ticket_name):
                    return None
                
                ticket_str = str(ticket_name).strip()
                ncr_match = re.search(r'NCR\s*(\d+)', ticket_str, re.IGNORECASE)
                if ncr_match:
                    return ncr_match.group(1)
                return None
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-match_customer"></a> `match_customer` — L3756–L3861

```python
def match_customer(row, valid_customers):
                """Match customer using priority logic with fuzzy matching"""
                from difflib import get_close_matches
                import re
                
                def normalize_for_matching(name):
                    """Normalize customer name for better matching"""
                    if not name:
                        return ''
                    name = str(name).strip()
                    # Remove common state abbreviations at the end (NY, MA, OH, NJ, PA, IL, etc.)
                    name = re.sub(r'\s+(NY|MA|OH|NJ|PA|IL|CA|CO|FL|TX|WA|OR|AZ|NV|MI|NC|SC|GA|VA|MD|CT|RI|NH|VT|ME|DE|WV|KY|TN|AL|MS|LA|AR|MO|IA|MN|WI|IN|OK|KS|NE|SD|ND|MT|WY|ID|UT|NM|HI|AK|DC)$', '', name, flags=re.IGNORECASE)
                    # Remove parenthetical state codes like (OH), (NY)
                    name = re.sub(r'\s*\([A-Z]{2}\)\s*', ' ', name)
                    # Remove trailing description words
                    name = re.sub(r'\s+(Smearing|Defect|Issue|Problem|Damage|Error).*$', '', name, flags=re.IGNORECASE)
                    return name.strip()
                
                def extract_base_company(company_name):
                    """Extract base company name from various formats:
                    - 'Parent : Child' format -> 'Parent'
                    - 'Acreage Holdings:  New York (NY)' -> 'Acreage Holdings'
                    - 'Acreage Holdings - Massachusetts (MA)' -> 'Acreage Holdings'
                    """
                    if not company_name or pd.isna(company_name):
                        return ''
                    name = str(company_name).strip()
                    
                    # Pattern 1: 'Parent : Child' - take the first part (HubSpot Company Name 2 format)
                    if ' : ' in name:
                        return name.split(' : ')[0].strip()
                    
                    # Pattern 2: 'Company:  Location (STATE)' - take before first colon
                    if ':' in name:
                        base = name.split(':')[0].strip()
                        # Only use if it looks like a company name (not a URL)
                        if '.' not in base and len(base) > 3:
                            return base
                    
                    # Pattern 3: 'Company - Location (STATE)' - take before dash if state follows
                    if ' - ' in name:
                        parts = name.split(' - ')
                        if len(parts) >= 2:
                            # Check if second part looks like a state/location
                            second = parts[1].strip()
                            if re.search(r'(Massachusetts|New York|Ohio|Pennsylvania|Illinois|New Jersey|Connecticut|Michigan|Florida|California|Colorado|Texas|Washington|Oregon|Arizona|Nevada|North Carolina|South Carolina|Georgia|Virginia|Maryland|NY|MA|OH|PA|IL|NJ|CT|MI|FL|CA|CO|TX|WA|OR|AZ|NV|NC|SC|GA|VA|MD)', second, re.IGNORECASE):
                                return parts[0].strip()
                    
                    return name
                
                def try_match(name, customers, cutoff=0.7):
                    """Try to match a name against valid customers"""
                    if not name:
                        return None
                    # Exact match first
                    if name in customers:
                        return name
                    # Normalized exact match
                    normalized = normalize_for_matching(name)
                    for cust in customers:
                        if normalize_for_matching(cust) == normalized:
                            return cust
                    # Fuzzy match
                    matches = get_close_matches(name, customers, n=1, cutoff=cutoff)
                    if matches:
                        return matches[0]
                    # Fuzzy match on normalized
                    if normalized != name:
                        matches = get_close_matches(normalized, customers, n=1, cutoff=cutoff)
                        if matches:
                            return matches[0]
                    return None
                
                # Priority 1: Company Name 2 - extract base and match
                company_name_2 = row.get('Company Name 2', '')
                if company_name_2 and company_name_2 != '' and not pd.isna(company_name_2):
                    # Extract base company name (before " : " if present)
                    base_name = extract_base_company(company_name_2)
                    if base_name:
                        match = try_match(base_name, valid_customers, cutoff=0.8)
                        if match:
                            return match
                
                # Priority 2: Company Name (try exact first, then fuzzy)
                company_name = row.get('Company Name', '')
                if company_name and company_name != '' and not pd.isna(company_name):
                    # Also extract base company from Company Name if it has " : " format
                    base_name = extract_base_company(company_name)
                    match = try_match(base_name if base_name else company_name, valid_customers, cutoff=0.7)
                    if match:
                        return match
                    # Try the raw company name with state stripped
                    normalized = normalize_for_matching(company_name)
                    match = try_match(normalized, valid_customers, cutoff=0.6)
                    if match:
                        return match
                
                # Priority 3: Extract from Ticket name and fuzzy match
                ticket_name = row.get('Ticket name', '')
                extracted = extract_customer_from_ticket(ticket_name)
                if extracted:
                    match = try_match(extracted, valid_customers, cutoff=0.5)
                    if match:
                        return match
                
                return ''
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-categorize_hubspot_ncr"></a> `categorize_hubspot_ncr` — L3877–L3944

```python
def categorize_hubspot_ncr(description):
                """Categorize HubSpot NCR based on ticket description to match NetSuite Issue Types"""
                if not description or description == '' or pd.isna(description):
                    return 'Defective Product'
                
                desc_lower = str(description).lower()
                
                # Damaged in Transit - carrier damage, broken in shipping
                if any(kw in desc_lower for kw in ['damaged', 'broken', 'crushed', 'fedex damaged', 
                                                    'ups damaged', 'transit', 'carrier', 'pallet.*damage']):
                    return 'Damaged in Transit'
                
                # Shipped to Wrong Address - misshipments, swapped orders
                if any(kw in desc_lower for kw in ['wrong address', 'misshipped', 'swapped', 
                                                    'wrong location', 'delivered to wrong']):
                    return 'Shipped to Wrong Address'
                
                # Missing Labels Wrong Qty - shortages
                if any(kw in desc_lower for kw in ['short', 'missing', 'shorted', 'only received',
                                                    'ran short', 'labels short']):
                    return 'Missing Labels Wrong Qty'
                
                # Order Entry Error - system/data entry issues, customer ordered wrong
                if any(kw in desc_lower for kw in ['hubspot', 'netsuite', 'set up incorrectly', 
                                                    'entered into', 'system switched',
                                                    'customer ordered wrong', 'mistakenly ordered',
                                                    'accidentally placed', 'customer error',
                                                    'deal & so was reflective of the wrong',
                                                    'proofing queue']):
                    return 'Order Entry Error'
                
                # Wrong Material - wrong product shipped (includes wrong color/size)
                if any(kw in desc_lower for kw in ['wrong color', 'wrong size', 'wrong finish',
                                                    'received white instead', 'received black instead', 
                                                    'instead of', '25d instead', '15d instead', 
                                                    '7ml instead', '45d instead', '4ml instead',
                                                    'wrong sku', 'wrong product', 'mislabeled box',
                                                    'shipped black instead', 'shipped white instead',
                                                    'wrong core', 'not the artwork']):
                    return 'Wrong Material'
                
                # Incorrect Color - specifically color-related manufacturing issues
                if any(kw in desc_lower for kw in ['grey caps', 'marbling', 'translucent',
                                                    'color.*mixed', 'pigment']):
                    return 'Incorrect Color'
                
                # Artwork/Print/Label defects
                if any(kw in desc_lower for kw in ['print', 'artwork', 'off center', 'embossing',
                                                    'cut off', 'varnish', 'laminate', 'tactile',
                                                    'telescoping', 'backing.*rip', 'paper backing',
                                                    'poor print', 'skipout']):
                    return 'Artwork Error'
                
                # Defective Product - manufacturing defects, contamination, fit issues
                if any(kw in desc_lower for kw in ['warped', 'warping', 'defect', 'grease', 
                                                    'debris', 'contaminated', 'filth', 'insect', 
                                                    'hair', 'doesn\'t fit', 'not sealing', 'leaking',
                                                    'cracked', 'irregular', 'lid.*fit', 'snapping',
                                                    'boxes not forming', 'not in.*bag']):
                    return 'Defective Product'
                
                # Customer Returns (not defect-related)
                if any(kw in desc_lower for kw in ['customer return', 'return', 'exchange',
                                                    'would like to replace', 'swap out']):
                    return 'Order Entry Error'
                
                # Default fallback
                return 'Defective Product'
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-get_qty_and_product_type"></a> `get_qty_and_product_type` — L3971–L3983

```python
def get_qty_and_product_type(row):
                """Get quantity affected and product type from first non-empty QTY column"""
                for col_name, product_type in qty_columns:
                    if col_name in row.index:
                        val = row[col_name]
                        if pd.notna(val) and str(val).strip() not in ['', 'nan', '0']:
                            try:
                                qty = float(str(val).replace(',', '').strip())
                                if qty > 0:
                                    return qty, product_type
                            except (ValueError, TypeError):
                                continue
                return 0, 'Unknown'
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-assign_so_manually_built_pipeline"></a> `assign_so_manually_built_pipeline` — L6634–L6650

```python
def assign_so_manually_built_pipeline(row):
                # If already mapped, keep it
                if pd.notna(row.get('Forecast Pipeline')) and row.get('Forecast Pipeline') != 'Unmapped':
                    return row['Forecast Pipeline']
                
                # Check if this is SO Manually Built
                raw_pipeline = str(row.get('Raw_Pipeline', '')).strip()
                if 'SO Manually Built' in raw_pipeline or 'Manually Built' in raw_pipeline:
                    rep = str(row.get('Rep Master', '')).strip()
                    
                    if rep in acquisition_reps:
                        return 'Acquisition'
                    elif rep in retention_reps:
                        return 'Retention'
                
                # Return original (could be None/NaN)
                return row.get('Forecast Pipeline')
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-has_standard_reorder_date"></a> `has_standard_reorder_date` — L6846–L6851

```python
def has_standard_reorder_date(row):
                for col in present_reorder_cols:
                    val = row.get(col, None)
                    if pd.notna(val) and str(val).strip() != '':
                        return True
                return False
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-normalize_for_matching"></a> `normalize_for_matching` — L3761–L3772

```python
def normalize_for_matching(name):
                    """Normalize customer name for better matching"""
                    if not name:
                        return ''
                    name = str(name).strip()
                    # Remove common state abbreviations at the end (NY, MA, OH, NJ, PA, IL, etc.)
                    name = re.sub(r'\s+(NY|MA|OH|NJ|PA|IL|CA|CO|FL|TX|WA|OR|AZ|NV|MI|NC|SC|GA|VA|MD|CT|RI|NH|VT|ME|DE|WV|KY|TN|AL|MS|LA|AR|MO|IA|MN|WI|IN|OK|KS|NE|SD|ND|MT|WY|ID|UT|NM|HI|AK|DC)$', '', name, flags=re.IGNORECASE)
                    # Remove parenthetical state codes like (OH), (NY)
                    name = re.sub(r'\s*\([A-Z]{2}\)\s*', ' ', name)
                    # Remove trailing description words
                    name = re.sub(r'\s+(Smearing|Defect|Issue|Problem|Damage|Error).*$', '', name, flags=re.IGNORECASE)
                    return name.strip()
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-extract_base_company"></a> `extract_base_company` — L3774–L3804

```python
def extract_base_company(company_name):
                    """Extract base company name from various formats:
                    - 'Parent : Child' format -> 'Parent'
                    - 'Acreage Holdings:  New York (NY)' -> 'Acreage Holdings'
                    - 'Acreage Holdings - Massachusetts (MA)' -> 'Acreage Holdings'
                    """
                    if not company_name or pd.isna(company_name):
                        return ''
                    name = str(company_name).strip()
                    
                    # Pattern 1: 'Parent : Child' - take the first part (HubSpot Company Name 2 format)
                    if ' : ' in name:
                        return name.split(' : ')[0].strip()
                    
                    # Pattern 2: 'Company:  Location (STATE)' - take before first colon
                    if ':' in name:
                        base = name.split(':')[0].strip()
                        # Only use if it looks like a company name (not a URL)
                        if '.' not in base and len(base) > 3:
                            return base
                    
                    # Pattern 3: 'Company - Location (STATE)' - take before dash if state follows
                    if ' - ' in name:
                        parts = name.split(' - ')
                        if len(parts) >= 2:
                            # Check if second part looks like a state/location
                            second = parts[1].strip()
                            if re.search(r'(Massachusetts|New York|Ohio|Pennsylvania|Illinois|New Jersey|Connecticut|Michigan|Florida|California|Colorado|Texas|Washington|Oregon|Arizona|Nevada|North Carolina|South Carolina|Georgia|Virginia|Maryland|NY|MA|OH|PA|IL|NJ|CT|MI|FL|CA|CO|TX|WA|OR|AZ|NV|NC|SC|GA|VA|MD)', second, re.IGNORECASE):
                                return parts[0].strip()
                    
                    return name
```

### <a id="calyx-sop-dashboard-v2-src-Rev_Ops_Playground-py-try_match"></a> `try_match` — L3806–L3827

```python
def try_match(name, customers, cutoff=0.7):
                    """Try to match a name against valid customers"""
                    if not name:
                        return None
                    # Exact match first
                    if name in customers:
                        return name
                    # Normalized exact match
                    normalized = normalize_for_matching(name)
                    for cust in customers:
                        if normalize_for_matching(cust) == normalized:
                            return cust
                    # Fuzzy match
                    matches = get_close_matches(name, customers, n=1, cutoff=cutoff)
                    if matches:
                        return matches[0]
                    # Fuzzy match on normalized
                    if normalized != name:
                        matches = get_close_matches(normalized, customers, n=1, cutoff=cutoff)
                        if matches:
                            return matches[0]
                    return None
```

## calyx-sop-dashboard-v2/src/aging_analysis.py

### <a id="calyx-sop-dashboard-v2-src-aging_analysis-py-categorize_age"></a> `categorize_age` — L325–L344

```python
def categorize_age(days: int) -> str:
    """
    Categorize age in days into aging buckets.
    
    Args:
        days: Number of days since submission
        
    Returns:
        Aging bucket category string
    """
    if pd.isna(days) or days < 0:
        return "Unknown"
    elif days <= 30:
        return "0-30 days"
    elif days <= 60:
        return "31-60 days"
    elif days <= 90:
        return "61-90 days"
    else:
        return "90+ days"
```

### <a id="calyx-sop-dashboard-v2-src-aging_analysis-py-calculate_aging_metrics"></a> `calculate_aging_metrics` — L347–L370

```python
def calculate_aging_metrics(df: pd.DataFrame) -> dict:
    """
    Calculate comprehensive aging metrics.
    
    Args:
        df: NC DataFrame with Age_Days column
        
    Returns:
        Dictionary with aging metrics
    """
    if df.empty or 'Age_Days' not in df.columns:
        return {}
    
    return {
        'mean': df['Age_Days'].mean(),
        'median': df['Age_Days'].median(),
        'std': df['Age_Days'].std(),
        'min': df['Age_Days'].min(),
        'max': df['Age_Days'].max(),
        'count_0_30': len(df[df['Age_Days'] <= 30]),
        'count_31_60': len(df[(df['Age_Days'] > 30) & (df['Age_Days'] <= 60)]),
        'count_61_90': len(df[(df['Age_Days'] > 60) & (df['Age_Days'] <= 90)]),
        'count_90_plus': len(df[df['Age_Days'] > 90])
    }
```

## calyx-sop-dashboard-v2/src/cost_analysis.py

### <a id="calyx-sop-dashboard-v2-src-cost_analysis-py-aggregate_by_period"></a> `aggregate_by_period` — L459–L509

```python
def aggregate_by_period(
    df: pd.DataFrame, 
    cost_column: str, 
    period: str
) -> pd.DataFrame:
    """
    Aggregate cost data by the specified time period.
    
    Args:
        df: NC DataFrame
        cost_column: Name of cost column
        period: Aggregation period (Daily, Weekly, Monthly, Quarterly, Yearly)
        
    Returns:
        Aggregated DataFrame with Period and Total columns
    """
    df = df.copy()
    df['Date Submitted'] = pd.to_datetime(df['Date Submitted'])
    
    # Set the date as index for resampling
    df_indexed = df.set_index('Date Submitted')
    
    # Define resampling frequency
    freq_map = {
        'Daily': 'D',
        'Weekly': 'W',
        'Monthly': 'ME',
        'Quarterly': 'QE',
        'Yearly': 'YE'
    }
    
    freq = freq_map.get(period, 'ME')
    
    # Resample and aggregate
    aggregated = df_indexed.resample(freq)[cost_column].agg(['sum', 'count', 'mean'])
    aggregated = aggregated.reset_index()
    aggregated.columns = ['Period', 'Total', 'Count', 'Average']
    
    # Format period based on frequency
    if period == 'Daily':
        aggregated['Period'] = aggregated['Period'].dt.strftime('%Y-%m-%d')
    elif period == 'Weekly':
        aggregated['Period'] = aggregated['Period'].dt.strftime('%Y-W%U')
    elif period == 'Monthly':
        aggregated['Period'] = aggregated['Period'].dt.strftime('%Y-%m')
    elif period == 'Quarterly':
        aggregated['Period'] = aggregated['Period'].dt.to_period('Q').astype(str)
    elif period == 'Yearly':
        aggregated['Period'] = aggregated['Period'].dt.strftime('%Y')
    
    return aggregated
```

## calyx-sop-dashboard-v2/src/data_loader.py

### <a id="calyx-sop-dashboard-v2-src-data_loader-py-get_spreadsheet_id"></a> `get_spreadsheet_id` — L58–L60

```python
def get_spreadsheet_id():
    """Get spreadsheet ID from secrets."""
    return st.secrets.get('SPREADSHEET_ID', st.secrets.get('spreadsheet_id', ''))
```

### <a id="calyx-sop-dashboard-v2-src-data_loader-py-load_nc_data"></a> `load_nc_data` — L68–L132

```python
def load_nc_data() -> Optional[pd.DataFrame]:
    """
    Load Non-Conformance data from Google Sheets.
    
    Returns:
        DataFrame with NC data or None if loading fails
    """
    try:
        client = get_google_sheets_client()
        if client is None:
            logger.warning("Google Sheets client not available, using sample data")
            return load_sample_data()
        
        spreadsheet_id = get_spreadsheet_id()
        if not spreadsheet_id:
            logger.warning("No spreadsheet ID configured, using sample data")
            return load_sample_data()
        
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # Try different sheet names for NC data
        sheet_names = ['Non-Conformance Details', 'NC Details', 'NC_Details', 'NCs', 'Non-Conformance']
        worksheet = None
        
        for name in sheet_names:
            try:
                worksheet = spreadsheet.worksheet(name)
                break
            except gspread.exceptions.WorksheetNotFound:
                continue
        
        if worksheet is None:
            logger.warning("NC sheet not found, using sample data")
            return load_sample_data()
        
        data = worksheet.get_all_values()
        
        if not data:
            return load_sample_data()
        
        # Handle duplicate column names
        headers = data[0]
        seen = {}
        new_headers = []
        for h in headers:
            if h in seen:
                seen[h] += 1
                new_headers.append(f"{h}_{seen[h]}")
            else:
                seen[h] = 0
                new_headers.append(h)
        
        df = pd.DataFrame(data[1:], columns=new_headers)
        
        # Standardize column names
        df = standardize_nc_columns(df)
        
        # Convert data types
        df = convert_nc_data_types(df)
        
        return df
        
    except Exception as e:
        logger.error(f"Error loading NC data: {e}")
        return load_sample_data()
```

### <a id="calyx-sop-dashboard-v2-src-data_loader-py-standardize_nc_columns"></a> `standardize_nc_columns` — L135–L173

```python
def standardize_nc_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize NC column names."""
    col_mapping = {}
    
    for col in df.columns:
        col_lower = col.lower().strip()
        
        if 'nc' in col_lower and ('number' in col_lower or 'num' in col_lower or '#' in col_lower):
            col_mapping[col] = 'NC Number'
        elif col_lower in ['status', 'nc status']:
            col_mapping[col] = 'Status'
        elif 'priority' in col_lower:
            col_mapping[col] = 'Priority'
        elif 'customer' in col_lower:
            col_mapping[col] = 'Customer'
        elif 'date' in col_lower and ('created' in col_lower or 'open' in col_lower):
            col_mapping[col] = 'Date Created'
        elif 'date' in col_lower and 'close' in col_lower:
            col_mapping[col] = 'Date Closed'
        elif 'type' in col_lower and ('issue' in col_lower or 'nc' in col_lower):
            col_mapping[col] = 'Issue Type'
        elif 'root' in col_lower and 'cause' in col_lower:
            col_mapping[col] = 'Root Cause'
        elif 'cost' in col_lower or 'amount' in col_lower:
            col_mapping[col] = 'Cost'
        elif 'owner' in col_lower or 'assigned' in col_lower:
            col_mapping[col] = 'Owner'
        elif 'department' in col_lower or 'dept' in col_lower:
            col_mapping[col] = 'Department'
        elif 'product' in col_lower:
            col_mapping[col] = 'Product'
        elif 'description' in col_lower:
            col_mapping[col] = 'Description'
        elif 'external' in col_lower or 'internal' in col_lower:
            col_mapping[col] = 'External/Internal'
    
    df = df.rename(columns=col_mapping)
    
    return df
```

### <a id="calyx-sop-dashboard-v2-src-data_loader-py-convert_nc_data_types"></a> `convert_nc_data_types` — L176–L215

```python
def convert_nc_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """Convert NC data types."""
    df = df.copy()
    
    # Date columns
    date_cols = ['Date Created', 'Date Closed']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Numeric columns
    if 'Cost' in df.columns:
        df['Cost'] = pd.to_numeric(df['Cost'].replace(r'[\$,]', '', regex=True), errors='coerce').fillna(0)
    
    # Calculate days open
    if 'Date Created' in df.columns:
        today = pd.Timestamp.now()
        if 'Date Closed' in df.columns:
            df['Days Open'] = df.apply(
                lambda row: (row['Date Closed'] - row['Date Created']).days 
                if pd.notna(row['Date Closed']) 
                else (today - row['Date Created']).days 
                if pd.notna(row['Date Created']) 
                else 0,
                axis=1
            )
        else:
            df['Days Open'] = df['Date Created'].apply(
                lambda x: (today - x).days if pd.notna(x) else 0
            )
    
    # Fill missing values
    if 'Status' in df.columns:
        df['Status'] = df['Status'].fillna('Unknown').replace('', 'Unknown')
    if 'Priority' in df.columns:
        df['Priority'] = df['Priority'].fillna('Medium').replace('', 'Medium')
    if 'Issue Type' in df.columns:
        df['Issue Type'] = df['Issue Type'].fillna('Unknown').replace('', 'Unknown')
    
    return df
```

### <a id="calyx-sop-dashboard-v2-src-data_loader-py-load_sample_data"></a> `load_sample_data` — L218–L274

```python
def load_sample_data() -> pd.DataFrame:
    """Generate sample NC data for testing/demo purposes."""
    np.random.seed(42)
    n_records = 100
    
    statuses = ['Open', 'In Progress', 'Pending Review', 'Closed', 'On Hold']
    priorities = ['High', 'Medium', 'Low']
    issue_types = ['Quality Defect', 'Packaging Error', 'Labeling Issue', 'Shipping Damage', 
                   'Documentation Error', 'Customer Complaint', 'Process Deviation']
    customers = ['Acme Corp', 'Beta Industries', 'Gamma LLC', 'Delta Co', 'Epsilon Inc',
                 'Zeta Manufacturing', 'Eta Products', 'Theta Systems']
    departments = ['Production', 'QA', 'Shipping', 'Receiving', 'Packaging']
    owners = ['John Smith', 'Jane Doe', 'Bob Wilson', 'Alice Brown', 'Charlie Davis']
    products = ['Concentrate Jars', 'Flower Jars', 'Pre-Roll Tubes', 'Custom Packaging', 'Tray Inserts']
    
    # Generate dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    date_range = (end_date - start_date).days
    
    created_dates = [start_date + timedelta(days=np.random.randint(0, date_range)) for _ in range(n_records)]
    
    # Generate data
    data = {
        'NC Number': [f'NC-{2024000 + i}' for i in range(n_records)],
        'Status': np.random.choice(statuses, n_records, p=[0.25, 0.20, 0.15, 0.30, 0.10]),
        'Priority': np.random.choice(priorities, n_records, p=[0.2, 0.5, 0.3]),
        'Issue Type': np.random.choice(issue_types, n_records),
        'Customer': np.random.choice(customers, n_records),
        'Department': np.random.choice(departments, n_records),
        'Owner': np.random.choice(owners, n_records),
        'Product': np.random.choice(products, n_records),
        'Date Created': created_dates,
        'Cost': np.random.exponential(500, n_records).round(2),
        'External/Internal': np.random.choice(['External', 'Internal'], n_records, p=[0.4, 0.6]),
        'Description': [f'Sample NC description for record {i}' for i in range(n_records)]
    }
    
    df = pd.DataFrame(data)
    
    # Add closed dates for closed items
    df['Date Closed'] = df.apply(
        lambda row: row['Date Created'] + timedelta(days=np.random.randint(1, 30))
        if row['Status'] == 'Closed' else pd.NaT,
        axis=1
    )
    
    # Calculate days open
    today = pd.Timestamp.now()
    df['Days Open'] = df.apply(
        lambda row: (row['Date Closed'] - row['Date Created']).days 
        if pd.notna(row['Date Closed']) 
        else (today - row['Date Created']).days,
        axis=1
    )
    
    return df
```

### <a id="calyx-sop-dashboard-v2-src-data_loader-py-refresh_data"></a> `refresh_data` — L281–L284

```python
def refresh_data() -> Optional[pd.DataFrame]:
    """Force refresh of NC data by clearing cache."""
    st.cache_data.clear()
    return load_nc_data()
```

### <a id="calyx-sop-dashboard-v2-src-data_loader-py-get_data_summary"></a> `get_data_summary` — L287–L319

```python
def get_data_summary(df: pd.DataFrame = None) -> Dict:
    """
    Get summary statistics for NC data.
    
    Args:
        df: NC DataFrame (loads if not provided)
    
    Returns:
        Dictionary with summary statistics
    """
    if df is None:
        df = load_nc_data()
    
    if df is None or df.empty:
        return {
            'total_records': 0,
            'open_count': 0,
            'closed_count': 0,
            'high_priority': 0,
            'avg_days_open': 0,
            'total_cost': 0
        }
    
    summary = {
        'total_records': len(df),
        'open_count': len(df[df['Status'].isin(['Open', 'In Progress', 'Pending Review', 'On Hold'])]) if 'Status' in df.columns else 0,
        'closed_count': len(df[df['Status'] == 'Closed']) if 'Status' in df.columns else 0,
        'high_priority': len(df[df['Priority'] == 'High']) if 'Priority' in df.columns else 0,
        'avg_days_open': df['Days Open'].mean() if 'Days Open' in df.columns else 0,
        'total_cost': df['Cost'].sum() if 'Cost' in df.columns else 0
    }
    
    return summary
```

### <a id="calyx-sop-dashboard-v2-src-data_loader-py-filter_nc_data"></a> `filter_nc_data` — L326–L366

```python
def filter_nc_data(df: pd.DataFrame, 
                   status: str = None,
                   priority: str = None,
                   customer: str = None,
                   date_from: datetime = None,
                   date_to: datetime = None) -> pd.DataFrame:
    """
    Filter NC data based on criteria.
    
    Args:
        df: NC DataFrame
        status: Filter by status
        priority: Filter by priority
        customer: Filter by customer
        date_from: Start date
        date_to: End date
    
    Returns:
        Filtered DataFrame
    """
    if df is None or df.empty:
        return df
    
    filtered = df.copy()
    
    if status and status != 'All' and 'Status' in filtered.columns:
        filtered = filtered[filtered['Status'] == status]
    
    if priority and priority != 'All' and 'Priority' in filtered.columns:
        filtered = filtered[filtered['Priority'] == priority]
    
    if customer and customer != 'All' and 'Customer' in filtered.columns:
        filtered = filtered[filtered['Customer'] == customer]
    
    if date_from and 'Date Created' in filtered.columns:
        filtered = filtered[filtered['Date Created'] >= pd.Timestamp(date_from)]
    
    if date_to and 'Date Created' in filtered.columns:
        filtered = filtered[filtered['Date Created'] <= pd.Timestamp(date_to)]
    
    return filtered
```

### <a id="calyx-sop-dashboard-v2-src-data_loader-py-get_unique_values"></a> `get_unique_values` — L369–L375

```python
def get_unique_values(df: pd.DataFrame, column: str) -> List[str]:
    """Get unique values from a column."""
    if df is None or df.empty or column not in df.columns:
        return []
    
    values = df[column].dropna().unique().tolist()
    return sorted([str(v) for v in values if v])
```

## calyx-sop-dashboard-v2/src/deliveries_tracking.py

### <a id="calyx-sop-dashboard-v2-src-deliveries_tracking-py-prepare_shipment_data"></a> `prepare_shipment_data` — L136–L170

```python
def prepare_shipment_data(sales_orders: pd.DataFrame, so_lines: pd.DataFrame) -> pd.DataFrame:
    """Prepare shipment data from sales orders."""
    
    df = sales_orders.copy()
    
    # Convert date columns
    date_cols = ['Order Start Date', 'Pending Fulfillment Date', 'Actual Ship Date', 
                 'Projected Date', 'Customer Promise Last Date to Ship']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Determine shipment status
    df['Status_Category'] = df.apply(categorize_shipment_status, axis=1)
    
    # Calculate expected delivery
    df['Expected_Delivery'] = df.apply(calculate_expected_delivery, axis=1)
    
    # Calculate days until delivery
    today = pd.Timestamp(datetime.now().date())
    df['Days_Until_Delivery'] = (df['Expected_Delivery'] - today).dt.days
    
    # Flag delays
    df['Is_Delayed'] = df.apply(check_if_delayed, axis=1)
    
    # Flag exceptions
    df['Has_Exception'] = df.apply(check_for_exceptions, axis=1)
    
    # Generate tracking numbers
    df['Tracking_Number'] = df.apply(generate_tracking_number, axis=1)
    
    # Assign carrier
    df['Carrier'] = df.apply(assign_carrier, axis=1)
    
    return df
```

### <a id="calyx-sop-dashboard-v2-src-deliveries_tracking-py-categorize_shipment_status"></a> `categorize_shipment_status` — L173–L189

```python
def categorize_shipment_status(row) -> str:
    """Categorize shipment status based on order data."""
    
    status = str(row.get('Status', '')).lower()
    
    if 'closed' in status or 'billed' in status:
        return 'Delivered'
    elif 'fulfilled' in status:
        return 'In Transit'
    elif 'pending fulfillment' in status:
        return 'Processing'
    elif 'pending approval' in status:
        return 'Pending Pickup'
    elif 'partially' in status:
        return 'In Transit'
    else:
        return 'Processing'
```

### <a id="calyx-sop-dashboard-v2-src-deliveries_tracking-py-calculate_expected_delivery"></a> `calculate_expected_delivery` — L192–L209

```python
def calculate_expected_delivery(row) -> pd.Timestamp:
    """Calculate expected delivery date."""
    
    actual_ship = row.get('Actual Ship Date')
    projected = row.get('Projected Date')
    promise = row.get('Customer Promise Last Date to Ship')
    pending = row.get('Pending Fulfillment Date')
    
    if pd.notna(actual_ship):
        return actual_ship + pd.DateOffset(days=5)
    if pd.notna(projected):
        return projected
    if pd.notna(promise):
        return promise
    if pd.notna(pending):
        return pending + pd.DateOffset(days=7)
    
    return pd.Timestamp(datetime.now()) + pd.DateOffset(days=14)
```

### <a id="calyx-sop-dashboard-v2-src-deliveries_tracking-py-check_if_delayed"></a> `check_if_delayed` — L212–L228

```python
def check_if_delayed(row) -> bool:
    """Check if shipment is delayed."""
    
    today = pd.Timestamp(datetime.now().date())
    expected = row.get('Expected_Delivery')
    status = row.get('Status_Category', '')
    
    if status == 'Delivered':
        return False
    if pd.notna(expected) and expected < today:
        return True
    
    promise = row.get('Customer Promise Last Date to Ship')
    if pd.notna(promise) and promise < today and status != 'Delivered':
        return True
    
    return False
```

### <a id="calyx-sop-dashboard-v2-src-deliveries_tracking-py-check_for_exceptions"></a> `check_for_exceptions` — L231–L242

```python
def check_for_exceptions(row) -> bool:
    """Check for shipment exceptions."""
    
    is_delayed = row.get('Is_Delayed', False)
    if is_delayed:
        return True
    
    days_until = row.get('Days_Until_Delivery', 0)
    if days_until < -7:
        return True
    
    return False
```

### <a id="calyx-sop-dashboard-v2-src-deliveries_tracking-py-generate_tracking_number"></a> `generate_tracking_number` — L245–L251

```python
def generate_tracking_number(row) -> str:
    """Generate a tracking number."""
    
    so_number = row.get('SO Number', row.get('Internal ID', ''))
    if pd.notna(so_number):
        return f"TRK{str(so_number)[-8:].zfill(8)}"
    return "N/A"
```

### <a id="calyx-sop-dashboard-v2-src-deliveries_tracking-py-assign_carrier"></a> `assign_carrier` — L254–L260

```python
def assign_carrier(row) -> str:
    """Assign carrier."""
    
    carriers = ['FedEx', 'UPS', 'USPS', 'DHL', 'Freight']
    so_number = str(row.get('SO Number', row.get('Internal ID', 0)))
    idx = hash(so_number) % len(carriers)
    return carriers[idx]
```

### <a id="calyx-sop-dashboard-v2-src-deliveries_tracking-py-apply_delivery_filters"></a> `apply_delivery_filters` — L263–L286

```python
def apply_delivery_filters(shipments: pd.DataFrame, statuses: List[str], 
                           date_range: str, customer: str) -> pd.DataFrame:
    """Apply filters to shipment data."""
    
    df = shipments.copy()
    
    if statuses:
        df = df[df['Status_Category'].isin(statuses)]
    
    today = pd.Timestamp(datetime.now().date())
    
    if date_range == 'Next 7 Days':
        df = df[df['Expected_Delivery'] <= today + pd.DateOffset(days=7)]
    elif date_range == 'Next 14 Days':
        df = df[df['Expected_Delivery'] <= today + pd.DateOffset(days=14)]
    elif date_range == 'Next 30 Days':
        df = df[df['Expected_Delivery'] <= today + pd.DateOffset(days=30)]
    elif date_range == 'Overdue':
        df = df[df['Expected_Delivery'] < today]
    
    if customer != 'All' and 'Customer' in df.columns:
        df = df[df['Customer'] == customer]
    
    return df
```

## calyx-sop-dashboard-v2/src/forecasting_models.py

### <a id="calyx-sop-dashboard-v2-src-forecasting_models-py-detect_seasonality"></a> `detect_seasonality` — L66–L101

```python
def detect_seasonality(series: pd.Series, freq: str = 'M') -> Tuple[bool, int]:
    """
    Detect if a time series has seasonality and determine the period.
    
    Args:
        series: Time series data
        freq: Frequency of data ('D', 'W', 'M', 'Q')
        
    Returns:
        Tuple of (has_seasonality, seasonal_period)
    """
    if len(series) < 24:  # Need at least 2 years of monthly data
        return False, 1
    
    # Default periods by frequency
    default_periods = {'D': 7, 'W': 52, 'M': 12, 'Q': 4}
    period = default_periods.get(freq, 12)
    
    try:
        # Perform seasonal decomposition
        decomposition = seasonal_decompose(series, model='additive', period=period)
        seasonal = decomposition.seasonal
        
        # Check if seasonal component is significant
        seasonal_var = seasonal.var()
        total_var = series.var()
        
        if total_var > 0:
            seasonal_ratio = seasonal_var / total_var
            has_seasonality = seasonal_ratio > 0.1  # 10% threshold
            return has_seasonality, period
        
    except Exception as e:
        logger.warning(f"Seasonality detection failed: {e}")
    
    return False, 1
```

### <a id="calyx-sop-dashboard-v2-src-forecasting_models-py-prepare_time_series"></a> `prepare_time_series` — L104–L126

```python
def prepare_time_series(df: pd.DataFrame, 
                        date_col: str = 'Period',
                        value_col: str = 'Demand') -> pd.Series:
    """
    Prepare a DataFrame for time series modeling.
    
    Args:
        df: DataFrame with date and value columns
        date_col: Name of date column
        value_col: Name of value column
        
    Returns:
        Series with DatetimeIndex
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(date_col)
    df = df.set_index(date_col)
    
    # Fill any gaps with 0 (no demand)
    series = df[value_col].asfreq('MS', fill_value=0)
    
    return series
```

### <a id="calyx-sop-dashboard-v2-src-forecasting_models-py-forecast_exponential_smoothing"></a> `forecast_exponential_smoothing` — L133–L253

```python
def forecast_exponential_smoothing(
    series: pd.Series,
    horizon: int = 12,
    seasonal: bool = None,
    seasonal_periods: int = 12,
    trend: str = 'add',
    damped_trend: bool = True,
    alpha: float = None,
    beta: float = None,
    gamma: float = None,
    confidence_level: float = 0.95
) -> ForecastResult:
    """
    Generate forecast using Exponential Smoothing (Holt-Winters).
    
    Args:
        series: Historical time series
        horizon: Number of periods to forecast
        seasonal: Whether to include seasonality (auto-detect if None)
        seasonal_periods: Number of periods in a season
        trend: Type of trend ('add', 'mul', None)
        damped_trend: Whether to dampen the trend
        alpha: Smoothing parameter for level (auto if None)
        beta: Smoothing parameter for trend (auto if None)
        gamma: Smoothing parameter for seasonality (auto if None)
        confidence_level: Confidence level for intervals
        
    Returns:
        ForecastResult object
    """
    try:
        # Auto-detect seasonality if not specified
        if seasonal is None:
            has_seasonal, detected_period = detect_seasonality(series)
            seasonal = 'add' if has_seasonal else None
            if has_seasonal:
                seasonal_periods = detected_period
        elif seasonal:
            seasonal = 'add'
        else:
            seasonal = None
        
        # Handle short series
        if len(series) < 2 * seasonal_periods and seasonal:
            seasonal = None
            logger.warning("Series too short for seasonality, disabling")
        
        # Build model
        model = ExponentialSmoothing(
            series,
            trend=trend,
            seasonal=seasonal,
            seasonal_periods=seasonal_periods if seasonal else None,
            damped_trend=damped_trend if trend else False,
            initialization_method='estimated'
        )
        
        # Fit with custom parameters or auto
        fit_kwargs = {}
        if alpha is not None:
            fit_kwargs['smoothing_level'] = alpha
        if beta is not None and trend:
            fit_kwargs['smoothing_trend'] = beta
        if gamma is not None and seasonal:
            fit_kwargs['smoothing_seasonal'] = gamma
        
        fitted = model.fit(**fit_kwargs) if fit_kwargs else model.fit()
        
        # Generate forecast
        forecast = fitted.forecast(horizon)
        
        # Calculate confidence intervals using residual standard error
        residuals = fitted.resid
        std_error = np.std(residuals)
        z_score = stats.norm.ppf((1 + confidence_level) / 2)
        
        # Widen intervals for longer horizons
        horizon_multiplier = np.sqrt(np.arange(1, horizon + 1))
        margin = z_score * std_error * horizon_multiplier
        
        lower = forecast - margin
        upper = forecast + margin
        
        # Ensure non-negative forecasts
        forecast = forecast.clip(lower=0)
        lower = lower.clip(lower=0)
        
        # Calculate fit metrics
        fitted_values = fitted.fittedvalues
        mape = np.mean(np.abs((series - fitted_values) / series.replace(0, np.nan))) * 100
        rmse = np.sqrt(np.mean((series - fitted_values) ** 2))
        
        metrics = {
            'MAPE': mape,
            'RMSE': rmse,
            'AIC': fitted.aic if hasattr(fitted, 'aic') else None,
            'BIC': fitted.bic if hasattr(fitted, 'bic') else None
        }
        
        parameters = {
            'alpha': fitted.params.get('smoothing_level', alpha),
            'beta': fitted.params.get('smoothing_trend', beta),
            'gamma': fitted.params.get('smoothing_seasonal', gamma),
            'trend': trend,
            'seasonal': seasonal,
            'seasonal_periods': seasonal_periods,
            'damped_trend': damped_trend
        }
        
        return ForecastResult(
            forecast=forecast,
            model_name='Exponential Smoothing',
            confidence_lower=pd.Series(lower, index=forecast.index),
            confidence_upper=pd.Series(upper, index=forecast.index),
            metrics=metrics,
            parameters=parameters
        )
        
    except Exception as e:
        logger.error(f"Exponential Smoothing failed: {e}")
        raise
```

### <a id="calyx-sop-dashboard-v2-src-forecasting_models-py-auto_arima_params"></a> `auto_arima_params` — L260–L317

```python
def auto_arima_params(series: pd.Series, 
                      seasonal: bool = True,
                      seasonal_period: int = 12,
                      max_p: int = 3,
                      max_q: int = 3,
                      max_d: int = 2) -> Dict[str, Tuple]:
    """
    Auto-select ARIMA parameters using AIC minimization.
    
    Args:
        series: Time series data
        seasonal: Whether to fit seasonal model
        seasonal_period: Seasonal period
        max_p, max_q, max_d: Maximum values to search
        
    Returns:
        Dictionary with optimal parameters
    """
    best_aic = np.inf
    best_params = (1, 1, 1)
    best_seasonal_params = (0, 0, 0, seasonal_period) if seasonal else (0, 0, 0, 0)
    
    # Grid search (simplified for performance)
    for p in range(max_p + 1):
        for d in range(max_d + 1):
            for q in range(max_q + 1):
                try:
                    if seasonal and len(series) >= 2 * seasonal_period:
                        model = SARIMAX(
                            series,
                            order=(p, d, q),
                            seasonal_order=(1, 1, 1, seasonal_period),
                            enforce_stationarity=False,
                            enforce_invertibility=False
                        )
                    else:
                        model = SARIMAX(
                            series,
                            order=(p, d, q),
                            enforce_stationarity=False,
                            enforce_invertibility=False
                        )
                    
                    fitted = model.fit(disp=False, maxiter=100)
                    
                    if fitted.aic < best_aic:
                        best_aic = fitted.aic
                        best_params = (p, d, q)
                        if seasonal and len(series) >= 2 * seasonal_period:
                            best_seasonal_params = (1, 1, 1, seasonal_period)
                            
                except Exception:
                    continue
    
    return {
        'order': best_params,
        'seasonal_order': best_seasonal_params
    }
```

### <a id="calyx-sop-dashboard-v2-src-forecasting_models-py-forecast_arima"></a> `forecast_arima` — L320–L407

```python
def forecast_arima(
    series: pd.Series,
    horizon: int = 12,
    order: Tuple[int, int, int] = None,
    seasonal_order: Tuple[int, int, int, int] = None,
    auto_params: bool = True,
    confidence_level: float = 0.95
) -> ForecastResult:
    """
    Generate forecast using ARIMA/SARIMA.
    
    Args:
        series: Historical time series
        horizon: Number of periods to forecast
        order: ARIMA order (p, d, q) - auto if None
        seasonal_order: Seasonal order (P, D, Q, s) - auto if None
        auto_params: Whether to auto-select parameters
        confidence_level: Confidence level for intervals
        
    Returns:
        ForecastResult object
    """
    try:
        # Auto-select parameters if needed
        if auto_params or order is None:
            has_seasonal, seasonal_period = detect_seasonality(series)
            params = auto_arima_params(
                series, 
                seasonal=has_seasonal,
                seasonal_period=seasonal_period
            )
            order = params['order']
            seasonal_order = params['seasonal_order']
        
        # Handle no seasonality
        if seasonal_order is None or seasonal_order[3] == 0:
            seasonal_order = (0, 0, 0, 0)
        
        # Build and fit model
        model = SARIMAX(
            series,
            order=order,
            seasonal_order=seasonal_order if seasonal_order[3] > 0 else None,
            enforce_stationarity=False,
            enforce_invertibility=False
        )
        
        fitted = model.fit(disp=False, maxiter=200)
        
        # Generate forecast with confidence intervals
        forecast_obj = fitted.get_forecast(horizon)
        forecast = forecast_obj.predicted_mean
        conf_int = forecast_obj.conf_int(alpha=1 - confidence_level)
        
        # Ensure non-negative
        forecast = forecast.clip(lower=0)
        lower = conf_int.iloc[:, 0].clip(lower=0)
        upper = conf_int.iloc[:, 1].clip(lower=0)
        
        # Calculate metrics
        fitted_values = fitted.fittedvalues
        mape = np.mean(np.abs((series - fitted_values) / series.replace(0, np.nan))) * 100
        rmse = np.sqrt(np.mean((series - fitted_values) ** 2))
        
        metrics = {
            'MAPE': mape,
            'RMSE': rmse,
            'AIC': fitted.aic,
            'BIC': fitted.bic
        }
        
        parameters = {
            'order': order,
            'seasonal_order': seasonal_order
        }
        
        return ForecastResult(
            forecast=forecast,
            model_name='ARIMA/SARIMA',
            confidence_lower=lower,
            confidence_upper=upper,
            metrics=metrics,
            parameters=parameters
        )
        
    except Exception as e:
        logger.error(f"ARIMA failed: {e}")
        raise
```

### <a id="calyx-sop-dashboard-v2-src-forecasting_models-py-create_ml_features"></a> `create_ml_features` — L414–L456

```python
def create_ml_features(series: pd.Series, 
                       lags: List[int] = [1, 2, 3, 6, 12],
                       rolling_windows: List[int] = [3, 6, 12]) -> pd.DataFrame:
    """
    Create features for ML forecasting.
    
    Args:
        series: Historical time series
        lags: Lag periods to include
        rolling_windows: Rolling average windows
        
    Returns:
        DataFrame with features
    """
    df = pd.DataFrame({'value': series})
    
    # Lag features
    for lag in lags:
        df[f'lag_{lag}'] = df['value'].shift(lag)
    
    # Rolling statistics
    for window in rolling_windows:
        df[f'rolling_mean_{window}'] = df['value'].shift(1).rolling(window=window).mean()
        df[f'rolling_std_{window}'] = df['value'].shift(1).rolling(window=window).std()
        df[f'rolling_min_{window}'] = df['value'].shift(1).rolling(window=window).min()
        df[f'rolling_max_{window}'] = df['value'].shift(1).rolling(window=window).max()
    
    # Date features (if datetime index)
    if isinstance(series.index, pd.DatetimeIndex):
        df['month'] = series.index.month
        df['quarter'] = series.index.quarter
        df['year'] = series.index.year
        df['month_sin'] = np.sin(2 * np.pi * series.index.month / 12)
        df['month_cos'] = np.cos(2 * np.pi * series.index.month / 12)
    
    # Trend feature
    df['trend'] = np.arange(len(df))
    
    # Year-over-year change
    if len(series) > 12:
        df['yoy_change'] = df['value'].pct_change(12)
    
    return df
```

### <a id="calyx-sop-dashboard-v2-src-forecasting_models-py-forecast_ml"></a> `forecast_ml` — L459–L620

```python
def forecast_ml(
    series: pd.Series,
    horizon: int = 12,
    model_type: str = 'random_forest',
    n_estimators: int = 100,
    max_depth: int = 10,
    confidence_level: float = 0.95,
    lags: List[int] = [1, 2, 3, 6, 12],
    rolling_windows: List[int] = [3, 6, 12]
) -> ForecastResult:
    """
    Generate forecast using Machine Learning (Random Forest or Gradient Boosting).
    
    Args:
        series: Historical time series
        horizon: Number of periods to forecast
        model_type: 'random_forest' or 'gradient_boosting'
        n_estimators: Number of trees
        max_depth: Maximum tree depth
        confidence_level: Confidence level for intervals
        lags: Lag periods for features
        rolling_windows: Rolling window sizes
        
    Returns:
        ForecastResult object
    """
    try:
        # Create features
        df = create_ml_features(series, lags=lags, rolling_windows=rolling_windows)
        
        # Drop rows with NaN (from lag/rolling features)
        df = df.dropna()
        
        if len(df) < 20:
            raise ValueError("Insufficient data for ML model (need at least 20 observations after feature creation)")
        
        # Prepare X and y
        feature_cols = [c for c in df.columns if c != 'value']
        X = df[feature_cols]
        y = df['value']
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Initialize model
        if model_type == 'gradient_boosting':
            model = GradientBoostingRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=42,
                learning_rate=0.1
            )
        else:
            model = RandomForestRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=42,
                n_jobs=-1
            )
        
        # Fit model
        model.fit(X_scaled, y)
        
        # Calculate in-sample metrics
        y_pred = model.predict(X_scaled)
        mape = np.mean(np.abs((y.values - y_pred) / y.replace(0, np.nan).values)) * 100
        rmse = np.sqrt(np.mean((y.values - y_pred) ** 2))
        
        # Feature importance
        importance_df = pd.DataFrame({
            'Feature': feature_cols,
            'Importance': model.feature_importances_
        }).sort_values('Importance', ascending=False)
        
        # Generate future forecasts
        last_date = series.index[-1]
        future_dates = pd.date_range(
            start=last_date + pd.DateOffset(months=1),
            periods=horizon,
            freq='MS'
        )
        
        # Iteratively predict future values
        forecast_values = []
        current_series = series.copy()
        
        for i in range(horizon):
            # Create features for next period
            temp_df = create_ml_features(current_series, lags=lags, rolling_windows=rolling_windows)
            last_features = temp_df[feature_cols].iloc[-1:].values
            
            # Handle any remaining NaN
            last_features = np.nan_to_num(last_features, nan=0)
            
            # Scale and predict
            last_features_scaled = scaler.transform(last_features)
            pred = model.predict(last_features_scaled)[0]
            pred = max(0, pred)  # Ensure non-negative
            
            forecast_values.append(pred)
            
            # Add prediction to series for next iteration
            current_series = pd.concat([
                current_series,
                pd.Series([pred], index=[future_dates[i]])
            ])
        
        forecast = pd.Series(forecast_values, index=future_dates)
        
        # Estimate confidence intervals using prediction variance
        # Use cross-validation residuals to estimate uncertainty
        tscv = TimeSeriesSplit(n_splits=min(5, len(y) // 10))
        cv_residuals = []
        
        for train_idx, test_idx in tscv.split(X_scaled):
            if len(train_idx) < 10:
                continue
            model_cv = model.__class__(**model.get_params())
            model_cv.fit(X_scaled[train_idx], y.iloc[train_idx])
            preds = model_cv.predict(X_scaled[test_idx])
            cv_residuals.extend(y.iloc[test_idx].values - preds)
        
        if cv_residuals:
            std_error = np.std(cv_residuals)
        else:
            std_error = np.std(y.values - y_pred)
        
        z_score = stats.norm.ppf((1 + confidence_level) / 2)
        horizon_multiplier = np.sqrt(np.arange(1, horizon + 1))
        margin = z_score * std_error * horizon_multiplier
        
        lower = (forecast - margin).clip(lower=0)
        upper = forecast + margin
        
        metrics = {
            'MAPE': mape,
            'RMSE': rmse,
            'R2': model.score(X_scaled, y)
        }
        
        parameters = {
            'model_type': model_type,
            'n_estimators': n_estimators,
            'max_depth': max_depth,
            'lags': lags,
            'rolling_windows': rolling_windows
        }
        
        return ForecastResult(
            forecast=forecast,
            model_name=f'ML ({model_type.replace("_", " ").title()})',
            confidence_lower=lower,
            confidence_upper=upper,
            metrics=metrics,
            feature_importance=importance_df,
            parameters=parameters
        )
        
    except Exception as e:
        logger.error(f"ML Forecast failed: {e}")
        raise
```

### <a id="calyx-sop-dashboard-v2-src-forecasting_models-py-blend_forecasts"></a> `blend_forecasts` — L627–L676

```python
def blend_forecasts(forecasts: List[ForecastResult], 
                    weights: List[float] = None) -> ForecastResult:
    """
    Blend multiple forecasts with specified weights.
    
    Args:
        forecasts: List of ForecastResult objects
        weights: Weights for each forecast (equal if None)
        
    Returns:
        Blended ForecastResult
    """
    if not forecasts:
        raise ValueError("No forecasts to blend")
    
    if weights is None:
        weights = [1.0 / len(forecasts)] * len(forecasts)
    else:
        # Normalize weights
        total = sum(weights)
        weights = [w / total for w in weights]
    
    # Blend forecasts
    blended = sum(f.forecast * w for f, w in zip(forecasts, weights))
    
    # Blend confidence intervals if available
    lower = None
    upper = None
    if all(f.confidence_lower is not None for f in forecasts):
        lower = sum(f.confidence_lower * w for f, w in zip(forecasts, weights))
    if all(f.confidence_upper is not None for f in forecasts):
        upper = sum(f.confidence_upper * w for f, w in zip(forecasts, weights))
    
    # Average metrics
    metrics = {}
    for key in ['MAPE', 'RMSE']:
        values = [f.metrics.get(key) for f in forecasts if f.metrics.get(key) is not None]
        if values:
            metrics[key] = np.mean(values)
    
    model_names = [f.model_name for f in forecasts]
    
    return ForecastResult(
        forecast=blended,
        model_name=f"Blended ({', '.join(model_names)})",
        confidence_lower=lower,
        confidence_upper=upper,
        metrics=metrics,
        parameters={'weights': dict(zip(model_names, weights))}
    )
```

### <a id="calyx-sop-dashboard-v2-src-forecasting_models-py-allocate_topdown_forecast"></a> `allocate_topdown_forecast` — L679–L710

```python
def allocate_topdown_forecast(
    total_forecast: pd.Series,
    historical_proportions: pd.DataFrame,
    allocation_col: str = 'Item'
) -> pd.DataFrame:
    """
    Allocate a top-down forecast to SKU level based on historical proportions.
    
    Args:
        total_forecast: Aggregate forecast
        historical_proportions: DataFrame with historical proportions by allocation_col
        allocation_col: Column to allocate by
        
    Returns:
        DataFrame with allocated forecasts
    """
    # Calculate proportions from historical data
    total_historical = historical_proportions.groupby(allocation_col)['value'].sum()
    proportions = total_historical / total_historical.sum()
    
    # Allocate forecast
    allocated = []
    for item, prop in proportions.items():
        item_forecast = total_forecast * prop
        for date, value in item_forecast.items():
            allocated.append({
                allocation_col: item,
                'Period': date,
                'Allocated_Forecast': value
            })
    
    return pd.DataFrame(allocated)
```

### <a id="calyx-sop-dashboard-v2-src-forecasting_models-py-calculate_forecast_accuracy"></a> `calculate_forecast_accuracy` — L713–L756

```python
def calculate_forecast_accuracy(
    actual: pd.Series,
    forecast: pd.Series
) -> Dict[str, float]:
    """
    Calculate various forecast accuracy metrics.
    
    Args:
        actual: Actual values
        forecast: Forecast values
        
    Returns:
        Dictionary of accuracy metrics
    """
    # Align series
    common_idx = actual.index.intersection(forecast.index)
    actual = actual[common_idx]
    forecast = forecast[common_idx]
    
    # Handle zeros in actual
    non_zero_mask = actual != 0
    
    metrics = {}
    
    # MAPE (only where actual != 0)
    if non_zero_mask.any():
        metrics['MAPE'] = np.mean(np.abs((actual[non_zero_mask] - forecast[non_zero_mask]) / actual[non_zero_mask])) * 100
    
    # RMSE
    metrics['RMSE'] = np.sqrt(np.mean((actual - forecast) ** 2))
    
    # MAE
    metrics['MAE'] = np.mean(np.abs(actual - forecast))
    
    # Bias
    metrics['Bias'] = np.mean(forecast - actual)
    
    # Tracking Signal (cumulative bias / MAD)
    cumulative_error = (forecast - actual).cumsum()
    mad = np.mean(np.abs(actual - forecast))
    if mad > 0:
        metrics['Tracking_Signal'] = cumulative_error.iloc[-1] / mad
    
    return metrics
```

### <a id="calyx-sop-dashboard-v2-src-forecasting_models-py-generate_forecast"></a> `generate_forecast` — L759–L786

```python
def generate_forecast(
    series: pd.Series,
    model: str = 'exponential_smoothing',
    horizon: int = 12,
    **kwargs
) -> ForecastResult:
    """
    Unified forecast generation function.
    
    Args:
        series: Historical time series
        model: Model type ('exponential_smoothing', 'arima', 'ml_random_forest', 'ml_gradient_boosting')
        horizon: Forecast horizon
        **kwargs: Model-specific parameters
        
    Returns:
        ForecastResult object
    """
    if model == 'exponential_smoothing':
        return forecast_exponential_smoothing(series, horizon=horizon, **kwargs)
    elif model == 'arima':
        return forecast_arima(series, horizon=horizon, **kwargs)
    elif model == 'ml_random_forest':
        return forecast_ml(series, horizon=horizon, model_type='random_forest', **kwargs)
    elif model == 'ml_gradient_boosting':
        return forecast_ml(series, horizon=horizon, model_type='gradient_boosting', **kwargs)
    else:
        raise ValueError(f"Unknown model type: {model}")
```

### <a id="calyx-sop-dashboard-v2-src-forecasting_models-py-__init__"></a> `__init__` — L35–L49

```python
def __init__(self, 
                 forecast: pd.Series,
                 model_name: str,
                 confidence_lower: pd.Series = None,
                 confidence_upper: pd.Series = None,
                 metrics: Dict[str, float] = None,
                 feature_importance: pd.DataFrame = None,
                 parameters: Dict[str, Any] = None):
        self.forecast = forecast
        self.model_name = model_name
        self.confidence_lower = confidence_lower
        self.confidence_upper = confidence_upper
        self.metrics = metrics or {}
        self.feature_importance = feature_importance
        self.parameters = parameters or {}
```

### <a id="calyx-sop-dashboard-v2-src-forecasting_models-py-to_dataframe"></a> `to_dataframe` — L51–L63

```python
def to_dataframe(self) -> pd.DataFrame:
        """Convert forecast to DataFrame with confidence intervals."""
        df = pd.DataFrame({
            'Period': self.forecast.index,
            'Forecast': self.forecast.values
        })
        
        if self.confidence_lower is not None:
            df['Lower_CI'] = self.confidence_lower.values
        if self.confidence_upper is not None:
            df['Upper_CI'] = self.confidence_upper.values
        
        return df
```

## calyx-sop-dashboard-v2/src/operations_view.py

### <a id="calyx-sop-dashboard-v2-src-operations_view-py-get_category_items_map"></a> `get_category_items_map` — L33–L51

```python
def get_category_items_map(_invoice_lines_hash, invoice_lines, item_col, product_type_col):
    """Cache the mapping of categories to their items."""
    if invoice_lines is None or item_col is None or product_type_col is None:
        return {}
    
    result = {}
    try:
        cat_series = get_column_as_series(invoice_lines, product_type_col)
        item_series = get_column_as_series(invoice_lines, item_col)
        
        if cat_series is not None and item_series is not None:
            df = pd.DataFrame({'Category': cat_series, 'Item': item_series})
            for cat in df['Category'].dropna().unique():
                items = df[df['Category'] == cat]['Item'].dropna().unique().tolist()
                result[str(cat).strip()] = sorted([str(i) for i in items])[:200]
    except:
        pass
    
    return result
```

### <a id="calyx-sop-dashboard-v2-src-operations_view-py-compute_demand_history_cached"></a> `compute_demand_history_cached` — L55–L81

```python
def compute_demand_history_cached(data_hash, filtered_data, date_col, amount_col, freq):
    """Cache demand history computation."""
    if filtered_data is None or filtered_data.empty:
        return pd.DataFrame()
    
    try:
        date_series = get_column_as_series(filtered_data, date_col)
        amt_series = get_column_as_series(filtered_data, amount_col)
        
        if date_series is None or amt_series is None:
            return pd.DataFrame()
        
        temp_df = pd.DataFrame({
            'Date': pd.to_datetime(date_series, errors='coerce'),
            'Amount': pd.to_numeric(amt_series, errors='coerce').fillna(0)
        })
        temp_df = temp_df.dropna(subset=['Date'])
        
        if freq == 'Q':
            temp_df['Period'] = temp_df['Date'].apply(lambda x: f"{x.year}-Q{(x.month-1)//3 + 1}")
        else:
            temp_df['Period'] = temp_df['Date'].dt.to_period(freq).astype(str)
        
        demand_history = temp_df.groupby('Period')['Amount'].sum().reset_index()
        return demand_history.sort_values('Period')
    except:
        return pd.DataFrame()
```

### <a id="calyx-sop-dashboard-v2-src-operations_view-py-compute_pipeline_data_cached"></a> `compute_pipeline_data_cached` — L85–L234

```python
def compute_pipeline_data_cached(deals_hash, deals, freq, items_hash, items, category_filter):
    """
    Cache pipeline data computation.
    
    Uses:
    - SKU column (or Column O as fallback) for SKU
    - Close Date / Expected Date column (or Column D as fallback) for date
    - Amount column for dollars
    - Maps SKU to category via Raw_Items
    
    Excludes rows where SKU or date is blank.
    """
    if deals is None or deals.empty:
        return pd.DataFrame()
    
    try:
        # Get column names from deals DataFrame
        cols = deals.columns.tolist()
        
        sku_col = None
        date_col = None
        amount_col = None
        
        # FIRST: Search by column name (preferred)
        for col in cols:
            col_lower = str(col).lower().strip()
            
            # SKU column
            if sku_col is None:
                if col_lower == 'sku' or col_lower == 'item' or col_lower == 'product':
                    sku_col = col
            
            # Date column - look for close date, expected date, etc.
            if date_col is None:
                if 'close' in col_lower and 'date' in col_lower:
                    date_col = col
                elif 'expected' in col_lower and 'date' in col_lower:
                    date_col = col
                elif col_lower == 'close date' or col_lower == 'closedate':
                    date_col = col
            
            # Amount column
            if amount_col is None:
                if col_lower == 'amount':
                    amount_col = col
                elif 'amount' in col_lower or 'value' in col_lower or 'revenue' in col_lower:
                    amount_col = col
        
        # FALLBACK: Use column index if name search failed
        # Column O is index 14 (0-based), Column D is index 3
        if sku_col is None and len(cols) > 14:
            sku_col = cols[14]  # Column O
        
        if date_col is None and len(cols) > 3:
            date_col = cols[3]  # Column D
        
        if date_col is None or amount_col is None:
            return pd.DataFrame()
        
        # Build SKU -> Category mapping from Raw_Items
        sku_to_category = {}
        if items is not None and not items.empty:
            # Look for SKU column - exact match first
            items_sku_col = None
            items_cat_col = None
            
            for col in items.columns:
                col_str = str(col).strip()
                if col_str == 'SKU' or col_str == 'Item':
                    items_sku_col = col
                    break
            
            if items_sku_col is None:
                items_sku_col = find_column(items, ['sku', 'item'])
            
            # Look for category column
            for col in items.columns:
                col_str = str(col).strip()
                if 'Calyx Product Type' in col_str or 'Calyx || Product Type' in col_str:
                    items_cat_col = col
                    break
            
            if items_cat_col is None:
                items_cat_col = find_column(items, ['calyx product type', 'product type', 'category'])
            
            if items_sku_col and items_cat_col:
                for _, row in items.iterrows():
                    sku_val = row.get(items_sku_col)
                    cat_val = row.get(items_cat_col)
                    if pd.notna(sku_val) and pd.notna(cat_val):
                        sku_to_category[str(sku_val).strip()] = str(cat_val).strip()
        
        # Extract data
        date_series = get_column_as_series(deals, date_col)
        amt_series = get_column_as_series(deals, amount_col)
        sku_series = get_column_as_series(deals, sku_col) if sku_col else None
        
        temp_df = pd.DataFrame({
            'Date': pd.to_datetime(date_series, errors='coerce'),
            'Amount': pd.to_numeric(amt_series, errors='coerce').fillna(0)
        })
        
        if sku_series is not None:
            temp_df['SKU'] = sku_series.astype(str).str.strip()
            # Map SKU to Category
            temp_df['Category'] = temp_df['SKU'].map(sku_to_category).fillna('Unknown')
        else:
            temp_df['SKU'] = ''
            temp_df['Category'] = 'Unknown'
        
        # EXCLUDE rows where SKU or Date is blank/null
        temp_df = temp_df.dropna(subset=['Date'])
        temp_df = temp_df[temp_df['SKU'].str.len() > 0]  # Exclude blank SKUs
        temp_df = temp_df[temp_df['SKU'] != 'nan']  # Exclude 'nan' strings
        temp_df = temp_df[temp_df['SKU'].str.lower() != 'none']  # Exclude 'none' strings
        
        if temp_df.empty:
            return pd.DataFrame()
        
        # Filter by category if specified
        if category_filter and category_filter != 'All':
            # Try exact match first
            filtered = temp_df[temp_df['Category'] == category_filter]
            
            # If no match, try case-insensitive
            if filtered.empty:
                filtered = temp_df[temp_df['Category'].str.lower().str.strip() == category_filter.lower().strip()]
            
            # If still empty, try partial match
            if filtered.empty:
                filtered = temp_df[temp_df['Category'].str.lower().str.contains(category_filter.lower().strip(), na=False)]
            
            if not filtered.empty:
                temp_df = filtered
        
        # Create period column
        if freq == 'Q':
            temp_df['Period'] = temp_df['Date'].apply(lambda x: f"{x.year}-Q{(x.month-1)//3 + 1}")
        else:
            temp_df['Period'] = temp_df['Date'].dt.to_period(freq).astype(str)
        
        # Aggregate by period
        pipeline_by_period = temp_df.groupby('Period')['Amount'].sum().reset_index()
        pipeline_by_period.columns = ['Period', 'Pipeline Value']
        
        return pipeline_by_period.sort_values('Period')
        
    except Exception as e:
        logger.error(f"Error in compute_pipeline_data_cached: {e}")
        return pd.DataFrame()
```

### <a id="calyx-sop-dashboard-v2-src-operations_view-py-clean_dataframe"></a> `clean_dataframe` — L258–L264

```python
def clean_dataframe(df):
    """Remove duplicate columns from DataFrame."""
    if df is None:
        return None
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]
    return df
```

### <a id="calyx-sop-dashboard-v2-src-operations_view-py-get_column_as_series"></a> `get_column_as_series` — L267–L274

```python
def get_column_as_series(df, col_name):
    """Safely get a column as a Series."""
    if df is None or col_name not in df.columns:
        return None
    result = df.loc[:, col_name]
    if isinstance(result, pd.DataFrame):
        return result.iloc[:, 0]
    return result
```

### <a id="calyx-sop-dashboard-v2-src-operations_view-py-find_column"></a> `find_column` — L277–L287

```python
def find_column(df, keywords, exclude=None):
    """Find first column matching any keyword."""
    if df is None:
        return None
    exclude = exclude or []
    for col in df.columns:
        col_lower = str(col).lower()
        if any(kw in col_lower for kw in keywords):
            if not any(ex in col_lower for ex in exclude):
                return col
    return None
```

### <a id="calyx-sop-dashboard-v2-src-operations_view-py-get_df_hash"></a> `get_df_hash` — L290–L294

```python
def get_df_hash(df):
    """Get a simple hash for a dataframe for caching."""
    if df is None:
        return "none"
    return f"{len(df)}_{df.columns.tolist()[:3]}"
```

### <a id="calyx-sop-dashboard-v2-src-operations_view-py-align_forecast_periods"></a> `align_forecast_periods` — L539–L562

```python
def align_forecast_periods(forecast_df):
    """Convert monthly periods to quarterly."""
    if forecast_df.empty or 'Period' not in forecast_df.columns:
        return forecast_df
    
    df = forecast_df.copy()
    
    def to_quarter(period_str):
        try:
            parts = str(period_str).split('-')
            if len(parts) == 2:
                year, month = int(parts[0]), int(parts[1])
                return f"{year}-Q{(month - 1) // 3 + 1}"
            return period_str
        except:
            return period_str
    
    df['Period'] = df['Period'].apply(to_quarter)
    
    agg_cols = {'Forecast_Revenue': 'sum'}
    if 'Forecast_Units' in df.columns:
        agg_cols['Forecast_Units'] = 'sum'
    
    return df.groupby('Period').agg(agg_cols).reset_index()
```

### <a id="calyx-sop-dashboard-v2-src-operations_view-py-generate_forecast"></a> `generate_forecast` — L565–L607

```python
def generate_forecast(history_df, horizon, freq):
    """Generate demand forecast using weighted moving average."""
    if history_df.empty:
        return pd.DataFrame()
    
    try:
        recent = history_df.tail(6)
        values = recent['Amount'].values
        
        if len(values) < 2:
            avg_value = values.mean() if len(values) > 0 else 0
            growth_rate = 0.02
        else:
            weights = np.arange(1, len(values) + 1)
            weighted_avg = np.average(values, weights=weights)
            growth_rate = np.clip((values[-1] / values[0]) ** (1/len(values)) - 1, -0.10, 0.15) if values[0] > 0 else 0.02
            avg_value = weighted_avg
        
        try:
            last_date = pd.to_datetime(history_df['Period'].iloc[-1])
        except:
            last_date = datetime.now()
        
        forecast_data = []
        for i in range(1, horizon + 1):
            if freq == 'Q':
                future_date = last_date + pd.DateOffset(months=i*3)
                period_label = f"{future_date.year}-Q{(future_date.month-1)//3 + 1}"
            else:
                future_date = last_date + pd.DateOffset(months=i)
                period_label = future_date.strftime('%Y-%m')
            
            forecast_value = avg_value * (1 + growth_rate) ** i
            forecast_data.append({
                'Period': period_label,
                'Forecast': forecast_value,
                'Lower': forecast_value * 0.85,
                'Upper': forecast_value * 1.15
            })
        
        return pd.DataFrame(forecast_data)
    except:
        return pd.DataFrame()
```

### <a id="calyx-sop-dashboard-v2-src-operations_view-py-get_forecast_pivot_data"></a> `get_forecast_pivot_data` — L677–L708

```python
def get_forecast_pivot_data(category):
    """Cache the forecast pivot table computation."""
    try:
        from .sop_data_loader import get_topdown_item_forecast
        item_forecast = get_topdown_item_forecast()
        
        if item_forecast.empty:
            return None, None
        
        if category and category != 'All':
            item_forecast = item_forecast[
                item_forecast['Category'].str.lower().str.strip() == category.lower().strip()
            ]
        
        if item_forecast.empty:
            return None, None
        
        # Units pivot
        pivot_units = item_forecast.pivot_table(
            index=['Item', 'Category'], columns='Period',
            values='Forecast_Units', aggfunc='sum', fill_value=0
        ).reset_index()
        
        # Revenue pivot
        pivot_revenue = item_forecast.pivot_table(
            index=['Item', 'Category'], columns='Period',
            values='Forecast_Revenue', aggfunc='sum', fill_value=0
        ).reset_index()
        
        return pivot_units, pivot_revenue
    except:
        return None, None
```

### <a id="calyx-sop-dashboard-v2-src-operations_view-py-to_quarter"></a> `to_quarter` — L546–L554

```python
def to_quarter(period_str):
        try:
            parts = str(period_str).split('-')
            if len(parts) == 2:
                year, month = int(parts[0]), int(parts[1])
                return f"{year}-Q{(month - 1) // 3 + 1}"
            return period_str
        except:
            return period_str
```

## calyx-sop-dashboard-v2/src/pareto_chart.py

### <a id="calyx-sop-dashboard-v2-src-pareto_chart-py-calculate_pareto_data"></a> `calculate_pareto_data` — L304–L339

```python
def calculate_pareto_data(df: pd.DataFrame, min_count: int = 0) -> pd.DataFrame:
    """
    Calculate Pareto analysis data for issue types.
    
    Args:
        df: NC DataFrame
        min_count: Minimum count threshold for inclusion
        
    Returns:
        DataFrame with Issue Type, Count, Percentage, and Cumulative Percentage
    """
    # Count by issue type
    issue_counts = df['Issue Type'].value_counts()
    
    # Apply minimum count filter
    issue_counts = issue_counts[issue_counts >= min_count]
    
    if issue_counts.empty:
        return pd.DataFrame()
    
    # Calculate percentages
    total = issue_counts.sum()
    percentages = (issue_counts / total) * 100
    
    # Calculate cumulative percentage
    cumulative_pct = percentages.cumsum()
    
    # Create DataFrame
    pareto_df = pd.DataFrame({
        'Issue Type': issue_counts.index,
        'Count': issue_counts.values,
        'Percentage': percentages.values,
        'Cumulative_Pct': cumulative_pct.values
    })
    
    return pareto_df
```

### <a id="calyx-sop-dashboard-v2-src-pareto_chart-py-get_pareto_insights"></a> `get_pareto_insights` — L437–L466

```python
def get_pareto_insights(pareto_data: pd.DataFrame) -> dict:
    """
    Generate insights from Pareto analysis.
    
    Args:
        pareto_data: DataFrame with Pareto analysis data
        
    Returns:
        Dictionary with Pareto insights
    """
    if pareto_data.empty:
        return {}
    
    # Find number of issues for 80%
    issues_for_80 = len(pareto_data[pareto_data['Cumulative_Pct'] <= 80]) + 1
    
    # Top 3 issues
    top_3 = pareto_data.head(3)['Issue Type'].tolist()
    top_3_pct = pareto_data.head(3)['Cumulative_Pct'].iloc[-1] if len(pareto_data) >= 3 else 0
    
    return {
        'total_issue_types': len(pareto_data),
        'total_ncs': pareto_data['Count'].sum(),
        'issues_for_80_pct': issues_for_80,
        'top_issue': pareto_data.iloc[0]['Issue Type'],
        'top_issue_count': pareto_data.iloc[0]['Count'],
        'top_issue_pct': pareto_data.iloc[0]['Percentage'],
        'top_3_issues': top_3,
        'top_3_cumulative_pct': top_3_pct
    }
```

## calyx-sop-dashboard-v2/src/po_forecast.py

### <a id="calyx-sop-dashboard-v2-src-po_forecast-py-safe_int"></a> `safe_int` — L28–L42

```python
def safe_int(value, default=0):
    """Safely convert a value to integer."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return default
    if pd.isna(value):
        return default
    try:
        # Handle string numbers
        if isinstance(value, str):
            value = value.replace(',', '').replace('$', '').strip()
            if value == '' or value.lower() in ['nan', 'none', 'null']:
                return default
        return int(float(value))
    except (ValueError, TypeError):
        return default
```

### <a id="calyx-sop-dashboard-v2-src-po_forecast-py-safe_float"></a> `safe_float` — L45–L58

```python
def safe_float(value, default=0.0):
    """Safely convert a value to float."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return default
    if pd.isna(value):
        return default
    try:
        if isinstance(value, str):
            value = value.replace('$', '').replace(',', '').strip()
            if value == '' or value.lower() in ['nan', 'none', 'null']:
                return default
        return float(value)
    except (ValueError, TypeError):
        return default
```

### <a id="calyx-sop-dashboard-v2-src-po_forecast-py-safe_str"></a> `safe_str` — L61–L65

```python
def safe_str(value, default=''):
    """Safely convert a value to string."""
    if value is None or pd.isna(value):
        return default
    return str(value).strip()
```

### <a id="calyx-sop-dashboard-v2-src-po_forecast-py-get_column_as_series"></a> `get_column_as_series` — L68–L75

```python
def get_column_as_series(df, col_name):
    """Safely get a column as a Series."""
    if df is None or col_name not in df.columns:
        return None
    result = df.loc[:, col_name]
    if isinstance(result, pd.DataFrame):
        return result.iloc[:, 0]
    return result
```

### <a id="calyx-sop-dashboard-v2-src-po_forecast-py-find_column"></a> `find_column` — L78–L88

```python
def find_column(df, keywords, exclude=None):
    """Find first column matching any keyword."""
    if df is None:
        return None
    exclude = exclude or []
    for col in df.columns:
        col_lower = str(col).lower()
        if any(kw in col_lower for kw in keywords):
            if not any(ex in col_lower for ex in exclude):
                return col
    return None
```

## calyx-sop-dashboard-v2/src/q1_revenue_snapshot.py

### <a id="calyx-sop-dashboard-v2-src-q1_revenue_snapshot-py-get_spreadsheet_id"></a> `get_spreadsheet_id` — L27–L31

```python
def get_spreadsheet_id():
    try:
        return st.secrets.get("spreadsheet_id", "15JhBZ_7aHHZA1W1qsoC2163borL6RYjk0xTDWPmWPfA")
    except:
        return "15JhBZ_7aHHZA1W1qsoC2163borL6RYjk0xTDWPmWPfA"
```

### <a id="calyx-sop-dashboard-v2-src-q1_revenue_snapshot-py-clean_numeric"></a> `clean_numeric` — L114–L122

```python
def clean_numeric(value):
    """Convert value to numeric, handling currency formatting"""
    if pd.isna(value) or str(value).strip() == '':
        return 0
    cleaned = str(value).replace(',', '').replace('$', '').replace(' ', '').strip()
    try:
        return float(cleaned)
    except:
        return 0
```

### <a id="calyx-sop-dashboard-v2-src-q1_revenue_snapshot-py-load_all_data"></a> `load_all_data` — L124–L141

```python
def load_all_data():
    """Load all required data for Q1 2026 review"""

    # Load invoice data - extended to column Y for Product Type
    invoices_df = load_google_sheets_data("_NS_Invoices_Data", "A:Y", version=CACHE_VERSION)

    # Load dashboard info (rep quotas)
    dashboard_df = load_google_sheets_data("Dashboard Info", "A:C", version=CACHE_VERSION)

    # Process invoices
    if not invoices_df.empty:
        invoices_df = process_invoices(invoices_df)

    # Process dashboard info
    if not dashboard_df.empty:
        dashboard_df = process_dashboard_info(dashboard_df)

    return invoices_df, dashboard_df
```

### <a id="calyx-sop-dashboard-v2-src-q1_revenue_snapshot-py-process_invoices"></a> `process_invoices` — L143–L225

```python
def process_invoices(df):
    """Process invoice data for Q1 2026 analysis"""
    if df.empty:
        return df

    col_mapping = {}
    col_names = df.columns.tolist()

    # Map columns by name
    for i, col in enumerate(col_names):
        col_lower = str(col).lower().strip()
        if 'document' in col_lower and 'number' in col_lower:
            col_mapping[col] = 'Invoice Number'
        elif col_lower == 'status':
            col_mapping[col] = 'Status'
        elif col_lower == 'date' and 'due' not in col_lower and 'closed' not in col_lower:
            col_mapping[col] = 'Date'
        elif col_lower == 'customer':
            col_mapping[col] = 'Customer'
        elif 'amount' in col_lower and 'transaction total' in col_lower:
            col_mapping[col] = 'Amount'
        elif 'amount' in col_lower and 'remaining' in col_lower:
            col_mapping[col] = 'Amount Remaining'
        elif col_lower == 'sales rep':
            col_mapping[col] = 'Sales Rep'
        elif 'hubspot' in col_lower and 'pipeline' in col_lower:
            col_mapping[col] = 'Pipeline'
        elif col_lower == 'department':
            col_mapping[col] = 'Department'
        elif col_lower == 'period':
            col_mapping[col] = 'Period'
        elif 'corrected' in col_lower and 'customer' in col_lower:
            col_mapping[col] = 'Corrected Customer'
        elif col_lower == 'rep master':
            col_mapping[col] = 'Rep Master'
        elif 'product' in col_lower and 'type' in col_lower:
            col_mapping[col] = 'Product Type'

    df = df.rename(columns=col_mapping)

    # CRITICAL: Use column U (index 20) as Rep Master for accurate rep attribution
    if len(col_names) >= 21:
        col_u_name = col_names[20]
        df['Rep Master'] = df[col_u_name].astype(str).str.strip()

    # Use column Y (index 24) for Product Type
    if len(col_names) >= 25:
        col_y_name = col_names[24]
        df['Product Type'] = df[col_y_name].astype(str).str.strip()

    # Use Rep Master as the Sales Rep (source of truth)
    if 'Rep Master' in df.columns:
        invalid_values = ['', 'nan', 'None', '#N/A', '#REF!', '#VALUE!', '#ERROR!']
        df = df[~df['Rep Master'].isin(invalid_values)]
        df['Sales Rep'] = df['Rep Master']

    # Use Corrected Customer if available
    if 'Corrected Customer' in df.columns and 'Customer' in df.columns:
        df['Corrected Customer'] = df['Corrected Customer'].astype(str).str.strip()
        invalid_values = ['', 'nan', 'None', '#N/A', '#REF!', '#VALUE!', '#ERROR!']
        mask = ~df['Corrected Customer'].isin(invalid_values)
        df.loc[mask, 'Customer'] = df.loc[mask, 'Corrected Customer']

    # Clean amount
    if 'Amount' in df.columns:
        df['Amount'] = df['Amount'].apply(clean_numeric)
    else:
        df['Amount'] = 0

    # Parse date and filter for Q1 2026
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df[(df['Date'] >= Q1_START) & (df['Date'] <= Q1_END)]
        df['Month'] = df['Date'].dt.strftime('%B %Y')
        df['Month_Num'] = df['Date'].dt.month

    # Clean Sales Rep
    if 'Sales Rep' in df.columns:
        df['Sales Rep'] = df['Sales Rep'].astype(str).str.strip()
        invalid_reps = ['', 'nan', 'None', '#N/A', '#REF!']
        df = df[~df['Sales Rep'].isin(invalid_reps)]

    return df
```

### <a id="calyx-sop-dashboard-v2-src-q1_revenue_snapshot-py-process_dashboard_info"></a> `process_dashboard_info` — L227–L252

```python
def process_dashboard_info(df):
    """Process dashboard info for quota data"""
    if df.empty:
        return df

    col_names = df.columns.tolist()
    rename_map = {}

    for col in col_names:
        col_lower = str(col).lower().strip()
        if 'rep' in col_lower and 'name' in col_lower:
            rename_map[col] = 'Rep Name'
        elif 'quota' in col_lower:
            rename_map[col] = 'Quota'
        elif 'netsuite' in col_lower and 'order' in col_lower:
            rename_map[col] = 'NetSuite Orders'

    df = df.rename(columns=rename_map)

    if 'Quota' not in df.columns:
        st.sidebar.warning(f"⚠️ Dashboard Info columns: {df.columns.tolist()}")

    if 'Quota' in df.columns:
        df['Quota'] = df['Quota'].apply(clean_numeric)

    return df
```

### <a id="calyx-sop-dashboard-v2-src-q1_revenue_snapshot-py-get_medal"></a> `get_medal` — L353–L357

```python
def get_medal(idx):
            if idx == 0: return "🥇"
            elif idx == 1: return "🥈"
            elif idx == 2: return "🥉"
            else: return f"#{idx + 1}"
```

## calyx-sop-dashboard-v2/src/q2_revenue_snapshot.py

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-calculate_business_days_remaining"></a> `calculate_business_days_remaining` — L55–L79

```python
def calculate_business_days_remaining():
    """
    Calculate business days from today through end of Q2 2026 (Jun 30)
    Excludes weekends and major holidays
    """
    from datetime import date, timedelta
    
    today = date.today()
    q2_end = date(2026, 6, 30)
    
    # Define holidays to exclude
    holidays = [
        date(2026, 5, 25),  # Memorial Day
    ]
    
    business_days = 0
    current_date = today
    
    while current_date <= q2_end:
        # Check if it's a weekday (Monday=0, Sunday=6)
        if current_date.weekday() < 5 and current_date not in holidays:
            business_days += 1
        current_date += timedelta(days=1)
    
    return business_days
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_mst_time"></a> `get_mst_time` — L81–L86

```python
def get_mst_time():
    """
    Get current time in Mountain Standard Time (MST/MDT)
    Returns timezone-aware datetime in America/Denver timezone
    """
    return datetime.now(ZoneInfo("America/Denver"))
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_spillover_column"></a> `get_spillover_column` — L825–L837

```python
def get_spillover_column(df):
    """
    Get the spillover column name - handles both old and new column names.
    Returns the column name if found, None otherwise.
    Checks for 'Q3 2026 Spillover' first, falls back to 'Q2 2026 Spillover'.
    """
    if df is None or df.empty:
        return None
    if 'Q3 2026 Spillover' in df.columns:
        return 'Q3 2026 Spillover'
    elif 'Q2 2026 Spillover' in df.columns:
        return 'Q2 2026 Spillover'
    return None
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_spillover_value"></a> `get_spillover_value` — L839–L846

```python
def get_spillover_value(df, spillover_col):
    """
    Get spillover column values, handling the case where column doesn't exist.
    Returns a Series of the column values or a Series of empty strings if column doesn't exist.
    """
    if spillover_col and spillover_col in df.columns:
        return df[spillover_col]
    return pd.Series([''] * len(df), index=df.index)
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-is_q2_deal"></a> `is_q2_deal` — L848–L870

```python
def is_q2_deal(df, spillover_col):
    """
    Determine if deals are Q2 2026 deals (primary quarter).
    Q2 deals are NOT marked as Q3 2026 spillover AND NOT marked as Q1 2026 spillover.
    Handles various Quarter column value formats: 'Q3 2026', 'Q3', 'Q1 2026', 'Q1', etc.
    """
    if df is None or df.empty:
        return pd.Series([], dtype=bool)
    if spillover_col is None:
        return pd.Series([True] * len(df), index=df.index)
    
    spillover_vals = get_spillover_value(df, spillover_col).astype(str).str.strip().str.upper()
    
    if spillover_col == 'Q3 2026 Spillover':
        # Exclude Q2 spillover (various formats) and Q4 spillover (various formats)
        # Q2 values: 'Q2 2026', 'Q2', 'Q2 26', etc.
        # Q4 values: 'Q4 2025', 'Q4', 'Q4 25', etc.
        is_q3 = spillover_vals.str.contains('Q3', na=False)
        is_q1 = spillover_vals.str.contains('Q1', na=False)
        return ~is_q3 & ~is_q1
    else:
        # Old column 'Q2 2026 Spillover': for Q2 dashboard, all deals are primary quarter
        return pd.Series([True] * len(df), index=df.index)
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-apply_q2_fulfillment_logic"></a> `apply_q2_fulfillment_logic` — L872–L939

```python
def apply_q2_fulfillment_logic(deals_df):
    """
    Apply lead time logic to filter out deals that close late in Q2 2026
    but won't ship until Q3 based on product type
    """
    # Lead time mapping based on your image
    lead_time_map = {
        'Labeled - Labels In Stock': 10,
        'Outer Boxes': 20,
        'Non-Labeled - 1 Week Lead Time': 5,
        'Non-Labeled - 2 Week Lead Time': 10,
        'Labeled - Print & Apply': 20,
        'Non-Labeled - Custom Lead Time': 30,
        'Labeled with FEP - Print & Apply': 35,
        'Labeled - Custom Lead Time': 40,
        'Flexpack': 25,
        'Labels Only - Direct to Customer': 15,
        'Labels Only - For Inventory': 15,
        'Labeled with FEP - Labels In Stock': 25,
        'Labels Only (deprecated)': 15
    }
    
    # Calculate cutoff date for each product type
    q2_end = pd.Timestamp('2026-06-30')
    
    def get_business_days_before(end_date, business_days):
        """Calculate date that is N business days before end_date"""
        current = end_date
        days_counted = 0
        
        while days_counted < business_days:
            current -= timedelta(days=1)
            # Skip weekends (Monday=0, Sunday=6)
            if current.weekday() < 5:
                days_counted += 1
        
        return current
    
    # Add a column to track if deal counts for Q2
    deals_df['Counts_In_Q2'] = True
    deals_df['Q3_Spillover_Amount'] = 0
    
    # Check if we have a Product Type column
    if 'Product Type' in deals_df.columns:
        for product_type, lead_days in lead_time_map.items():
            cutoff_date = get_business_days_before(q2_end, lead_days)
            
            # Mark deals closing after cutoff as Q2
            mask = (
                (deals_df['Product Type'] == product_type) & 
                (deals_df['Close Date'] > cutoff_date) &
                (deals_df['Close Date'].notna())
            )
            deals_df.loc[mask, 'Counts_In_Q2'] = False
            deals_df.loc[mask, 'Q3_Spillover_Amount'] = deals_df.loc[mask, 'Amount']
            
        # Log how many deals were excluded
        excluded_count = (~deals_df['Counts_In_Q2']).sum()
        excluded_value = deals_df[~deals_df['Counts_In_Q2']]['Amount'].sum()
        
        if excluded_count > 0:
            pass  # Debug info removed
            #st.sidebar.info(f"📊 {excluded_count} deals (${excluded_value:,.0f}) deferred to Q3 2026 due to lead times")
    else:
        pass  # Debug info removed
        #st.sidebar.warning("⚠️ No 'Product Type' column found - lead time logic not applied")
    
    return deals_df
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-detect_changes"></a> `detect_changes` — L1558–L1621

```python
def detect_changes(current, previous):
    """
    Detect changes between current and previous snapshots
    Returns a dictionary of changes
    """
    changes = {
        'new_invoices': [],
        'new_sales_orders': [],
        'updated_deals': [],
        'rep_changes': {}
    }
    
    if previous is None:
        return changes
    
    try:
        # Detect new invoices
        if not current['invoices'].empty and not previous['invoices'].empty:
            if 'Document Number' in current['invoices'].columns:
                current_invoices = set(current['invoices']['Document Number'].dropna())
                previous_invoices = set(previous['invoices']['Document Number'].dropna())
                new_invoices = current_invoices - previous_invoices
                changes['new_invoices'] = list(new_invoices)
        
        # Detect new sales orders
        if not current['sales_orders'].empty and not previous['sales_orders'].empty:
            if 'Document Number' in current['sales_orders'].columns:
                current_orders = set(current['sales_orders']['Document Number'].dropna())
                previous_orders = set(previous['sales_orders']['Document Number'].dropna())
                new_orders = current_orders - previous_orders
                changes['new_sales_orders'] = list(new_orders)
        
        # Detect rep-level changes in forecasts
        if not current['dashboard'].empty and not previous['dashboard'].empty:
            if 'Rep Name' in current['dashboard'].columns:
                for rep in current['dashboard']['Rep Name'].unique():
                    current_rep = current['dashboard'][current['dashboard']['Rep Name'] == rep]
                    previous_rep = previous['dashboard'][previous['dashboard']['Rep Name'] == rep]
                    
                    if not previous_rep.empty:
                        rep_change = {}
                        
                        # Check for changes in key metrics
                        if 'Quota' in current_rep.columns:
                            current_val = pd.to_numeric(current_rep['Quota'].iloc[0], errors='coerce')
                            previous_val = pd.to_numeric(previous_rep['Quota'].iloc[0], errors='coerce')
                            if not pd.isna(current_val) and not pd.isna(previous_val):
                                if current_val != previous_val:
                                    rep_change['goal_change'] = current_val - previous_val
                        
                        if 'NetSuite Orders' in current_rep.columns:
                            current_val = pd.to_numeric(current_rep['NetSuite Orders'].iloc[0], errors='coerce')
                            previous_val = pd.to_numeric(previous_rep['NetSuite Orders'].iloc[0], errors='coerce')
                            if not pd.isna(current_val) and not pd.isna(previous_val):
                                if current_val != previous_val:
                                    rep_change['actual_change'] = current_val - previous_val
                        
                        if rep_change:
                            changes['rep_changes'][rep] = rep_change
    
    except Exception as e:
        st.error(f"Error detecting changes: {str(e)}")
    
    return changes
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-calculate_team_metrics"></a> `calculate_team_metrics` — L3483–L3532

```python
def calculate_team_metrics(deals_df, dashboard_df):
    """Calculate overall team metrics"""
    
    # Handle empty dashboard_df
    if dashboard_df.empty or 'Quota' not in dashboard_df.columns:
        total_quota = 0
        total_orders = 0
    else:
        total_quota = dashboard_df['Quota'].sum()
        total_orders = dashboard_df['NetSuite Orders'].sum() if 'NetSuite Orders' in dashboard_df.columns else 0
    
    # Get spillover column (handles both old and new column names)
    spillover_col = get_spillover_column(deals_df)
    
    # Filter for Q2 2026 fulfillment only
    if not deals_df.empty and spillover_col:
        q2_mask = is_q2_deal(deals_df, spillover_col)
        deals_q2 = deals_df[q2_mask]
    else:
        # No spillover column or empty - use all deals
        deals_q2 = deals_df
    
    # Calculate Expect/Commit forecast (Q2 only)
    if not deals_q2.empty and 'Status' in deals_q2.columns and 'Amount' in deals_q2.columns:
        expect_commit = deals_q2[deals_q2['Status'].isin(['Expect', 'Commit'])]['Amount'].sum()
        best_opp = deals_q2[deals_q2['Status'].isin(['Best Case', 'Opportunity'])]['Amount'].sum()
    else:
        expect_commit = 0
        best_opp = 0
    
    # Calculate gap
    gap = total_quota - expect_commit - total_orders
    
    # Calculate attainment percentage
    current_forecast = expect_commit + total_orders
    attainment_pct = (current_forecast / total_quota * 100) if total_quota > 0 else 0
    
    # Potential attainment (if all deals close)
    potential_attainment = ((expect_commit + best_opp + total_orders) / total_quota * 100) if total_quota > 0 else 0
    
    return {
        'total_quota': total_quota,
        'total_orders': total_orders,
        'expect_commit': expect_commit,
        'best_opp': best_opp,
        'gap': gap,
        'attainment_pct': attainment_pct,
        'potential_attainment': potential_attainment,
        'current_forecast': current_forecast
    }
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-calculate_rep_metrics"></a> `calculate_rep_metrics` — L3713–L3899

```python
def calculate_rep_metrics(rep_name, deals_df, dashboard_df, sales_orders_df=None):
    """Calculate metrics for a specific rep with detailed order lists for drill-down"""
    
    # Get rep's quota and orders
    rep_info = dashboard_df[dashboard_df['Rep Name'] == rep_name]
    
    if rep_info.empty:
        return None
    
    quota = rep_info['Quota'].iloc[0]
    
    # Determine which orders column to use based on shipping toggle
    include_shipping = st.session_state.get('q2_include_shipping', True)
    if include_shipping:
        orders = rep_info['NetSuite Orders'].iloc[0]
    else:
        # Use Net column if available, otherwise fall back to regular
        if 'NetSuite Orders Net' in rep_info.columns:
            orders = rep_info['NetSuite Orders Net'].iloc[0]
        else:
            orders = rep_info['NetSuite Orders'].iloc[0]
    
    # Filter deals for this rep - ALL Q2 2026 deals (regardless of spillover)
    # Handle empty deals_df gracefully (e.g., when Google Sheets returns 503)
    if deals_df.empty or 'Deal Owner' not in deals_df.columns:
        rep_deals = pd.DataFrame()
    else:
        rep_deals = deals_df[deals_df['Deal Owner'] == rep_name].copy()
    
    # Check for spillover column (handles both old and new column names)
    spillover_col = get_spillover_column(rep_deals)
    
    if spillover_col == 'Q3 2026 Spillover':
        # New column: Separate deals by shipping timeline
        rep_deals['Ships_In_Q2'] = (rep_deals[spillover_col] != 'Q3 2026') & (rep_deals[spillover_col] != 'Q1 2026')
        rep_deals['Ships_In_Q3'] = rep_deals[spillover_col] == 'Q3 2026'
        rep_deals['Ships_In_Q1'] = rep_deals[spillover_col] == 'Q1 2026'
        
        # Deals that ship in Q2 2026 (primary quarter)
        rep_deals_ship_q2 = rep_deals[rep_deals['Ships_In_Q2'] == True].copy()
        
        # Deals that ship in Q2 2026 (forward spillover)
        rep_deals_ship_q3 = rep_deals[rep_deals['Ships_In_Q3'] == True].copy()
        
        # Deals that ship in Q4 2025 (backward spillover - carryover)
        rep_deals_ship_q1 = rep_deals[rep_deals['Ships_In_Q1'] == True].copy()
    else:
        # Old column name or no column - treat all as Q2 (primary quarter)
        rep_deals_ship_q2 = rep_deals.copy()
        rep_deals_ship_q3 = pd.DataFrame()
        rep_deals_ship_q1 = pd.DataFrame()
    
    # Calculate metrics for DEALS SHIPPING IN Q2 (this counts toward quota)
    if not rep_deals_ship_q2.empty and 'Status' in rep_deals_ship_q2.columns:
        expect_commit_q2_deals = rep_deals_ship_q2[rep_deals_ship_q2['Status'].isin(['Expect', 'Commit'])].copy()
        if expect_commit_q2_deals.columns.duplicated().any():
            expect_commit_q2_deals = expect_commit_q2_deals.loc[:, ~expect_commit_q2_deals.columns.duplicated()]
        expect_commit_q2 = expect_commit_q2_deals['Amount'].sum() if not expect_commit_q2_deals.empty else 0
        
        best_opp_q2_deals = rep_deals_ship_q2[rep_deals_ship_q2['Status'].isin(['Best Case', 'Opportunity'])].copy()
        if best_opp_q2_deals.columns.duplicated().any():
            best_opp_q2_deals = best_opp_q2_deals.loc[:, ~best_opp_q2_deals.columns.duplicated()]
        best_opp_q2 = best_opp_q2_deals['Amount'].sum() if not best_opp_q2_deals.empty else 0
    else:
        expect_commit_q2_deals = pd.DataFrame()
        expect_commit_q2 = 0
        best_opp_q2_deals = pd.DataFrame()
        best_opp_q2 = 0
    
    # Calculate metrics for Q3 SPILLOVER DEALS (closing in Q1 but shipping in Q2)
    if not rep_deals_ship_q3.empty and 'Status' in rep_deals_ship_q3.columns:
        expect_commit_q3_deals = rep_deals_ship_q3[rep_deals_ship_q3['Status'].isin(['Expect', 'Commit'])].copy()
        if expect_commit_q3_deals.columns.duplicated().any():
            expect_commit_q3_deals = expect_commit_q3_deals.loc[:, ~expect_commit_q3_deals.columns.duplicated()]
        expect_commit_q3_spillover = expect_commit_q3_deals['Amount'].sum() if not expect_commit_q3_deals.empty else 0
        
        best_opp_q3_deals = rep_deals_ship_q3[rep_deals_ship_q3['Status'].isin(['Best Case', 'Opportunity'])].copy()
        if best_opp_q3_deals.columns.duplicated().any():
            best_opp_q3_deals = best_opp_q3_deals.loc[:, ~best_opp_q3_deals.columns.duplicated()]
        best_opp_q3_spillover = best_opp_q3_deals['Amount'].sum() if not best_opp_q3_deals.empty else 0
    else:
        expect_commit_q3_deals = pd.DataFrame()
        expect_commit_q3_spillover = 0
        best_opp_q3_deals = pd.DataFrame()
        best_opp_q3_spillover = 0
    
    # Calculate metrics for Q1 2026 SPILLOVER DEALS (carryover from Q4)
    if not rep_deals_ship_q1.empty and 'Status' in rep_deals_ship_q1.columns:
        expect_commit_q1_deals = rep_deals_ship_q1[rep_deals_ship_q1['Status'].isin(['Expect', 'Commit'])].copy()
        if expect_commit_q1_deals.columns.duplicated().any():
            expect_commit_q1_deals = expect_commit_q1_deals.loc[:, ~expect_commit_q1_deals.columns.duplicated()]
        expect_commit_q1_spillover = expect_commit_q1_deals['Amount'].sum() if not expect_commit_q1_deals.empty else 0
        
        best_opp_q1_deals = rep_deals_ship_q1[rep_deals_ship_q1['Status'].isin(['Best Case', 'Opportunity'])].copy()
        if best_opp_q1_deals.columns.duplicated().any():
            best_opp_q1_deals = best_opp_q1_deals.loc[:, ~best_opp_q1_deals.columns.duplicated()]
        best_opp_q1_spillover = best_opp_q1_deals['Amount'].sum() if not best_opp_q1_deals.empty else 0
    else:
        expect_commit_q1_deals = pd.DataFrame()
        expect_commit_q1_spillover = 0
        best_opp_q1_deals = pd.DataFrame()
        best_opp_q1_spillover = 0
    
    # Total spillovers
    q3_spillover_total = expect_commit_q3_spillover + best_opp_q3_spillover
    q1_spillover_total = expect_commit_q1_spillover + best_opp_q1_spillover
    
    # === USE CENTRALIZED CATEGORIZATION FUNCTION ===
    so_categories = categorize_sales_orders(sales_orders_df, rep_name)
    
    # Extract amounts
    pending_fulfillment = so_categories['pf_date_ext_amount'] + so_categories['pf_date_int_amount']
    pending_fulfillment_no_date = so_categories['pf_nodate_ext_amount'] + so_categories['pf_nodate_int_amount']
    pending_approval = so_categories['pa_date_amount']
    pending_approval_no_date = so_categories['pa_nodate_amount']
    pending_approval_old = so_categories['pa_old_amount']
    
    # Extract detail dataframes
    pending_approval_details = so_categories['pa_date']
    pending_approval_no_date_details = so_categories['pa_nodate']
    pending_approval_old_details = so_categories['pa_old']
    pending_fulfillment_details = pd.concat([so_categories['pf_date_ext'], so_categories['pf_date_int']])
    pending_fulfillment_no_date_details = pd.concat([so_categories['pf_nodate_ext'], so_categories['pf_nodate_int']])
    
    # Total calculations - ONLY Q2 SHIPPING DEALS COUNT TOWARD QUOTA
    total_pending_fulfillment = pending_fulfillment + pending_fulfillment_no_date
    total_progress = orders + expect_commit_q2 + pending_approval + pending_fulfillment
    gap = quota - total_progress
    attainment_pct = (total_progress / quota * 100) if quota > 0 else 0
    potential_attainment = ((total_progress + best_opp_q2) / quota * 100) if quota > 0 else 0
    
    return {
        'quota': quota,
        'orders': orders,
        'expect_commit': expect_commit_q2,  # Only Q2 shipping deals
        'best_opp': best_opp_q2,  # Only Q2 shipping deals
        'gap': gap,
        'attainment_pct': attainment_pct,
        'potential_attainment': potential_attainment,
        'total_progress': total_progress,
        'pending_approval': pending_approval,
        'pending_approval_no_date': pending_approval_no_date,
        'pending_approval_old': pending_approval_old,
        'pending_fulfillment': pending_fulfillment,
        'pending_fulfillment_no_date': pending_fulfillment_no_date,
        'total_pending_fulfillment': total_pending_fulfillment,
        
        # Q3 2026 Spillover metrics (forward)
        'q3_spillover_expect_commit': expect_commit_q3_spillover,
        'q3_spillover_best_opp': best_opp_q3_spillover,
        'q3_spillover_total': q3_spillover_total,
        
        # Q2 2026 Spillover metrics (backward carryover)
        'q1_spillover_expect_commit': expect_commit_q1_spillover,
        'q1_spillover_best_opp': best_opp_q1_spillover,
        'q1_spillover_total': q1_spillover_total,
        
        # Keep q1_spillover keys for backward compatibility (mapped to q2)
        'q2_spillover_expect_commit': expect_commit_q3_spillover,
        'q2_spillover_best_opp': best_opp_q3_spillover,
        'q2_spillover_total': q3_spillover_total,
        
        # ALL Q2 2026 closing deals (for reference)
        'total_q2_closing_deals': len(rep_deals),
        'total_q2_closing_amount': rep_deals['Amount'].sum() if not rep_deals.empty else 0,
        
        'deals': rep_deals_ship_q2,  # Deals shipping in Q2
        
        # Add detail dataframes for drill-down
        'pending_approval_details': pending_approval_details,
        'pending_approval_no_date_details': pending_approval_no_date_details,
        'pending_approval_old_details': pending_approval_old_details,
        'pending_fulfillment_details': pending_fulfillment_details,
        'pending_fulfillment_no_date_details': pending_fulfillment_no_date_details,
        'expect_commit_deals': expect_commit_q2_deals,
        'best_opp_deals': best_opp_q2_deals,
        
        # Q2 Spillover deal details
        'expect_commit_q3_spillover_deals': expect_commit_q3_deals,
        'best_opp_q3_spillover_deals': best_opp_q3_deals,
        'all_q3_spillover_deals': rep_deals_ship_q3,
        
        # Keep old key names for backward compatibility
        'expect_commit_q2_spillover_deals': expect_commit_q3_deals,
        'best_opp_q2_spillover_deals': best_opp_q3_deals,
        'all_q2_spillover_deals': rep_deals_ship_q3
    }
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-create_sexy_gauge"></a> `create_sexy_gauge` — L3903–L3939

```python
def create_sexy_gauge(current_val, target_val, title="Progress to Quota"):
    """Enhanced cyber-style gauge"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = current_val,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title.upper(), 'font': {'size': 12, 'color': '#94a3b8'}},
        delta = {
            'reference': target_val, 
            'increasing': {'color': "#10b981"},
            'decreasing': {'color': "#ef4444"},
            'font': {'size': 14}
        },
        number = {'font': {'size': 40, 'color': 'white', 'family': 'Inter'}, 'prefix': "$"},
        gauge = {
            'axis': {'range': [None, max(target_val * 1.1, current_val * 1.1)], 'visible': False},
            'bar': {'color': "#3b82f6", 'thickness': 1},
            'bgcolor': "rgba(255,255,255,0.05)",
            'borderwidth': 0,
            'steps': [
                 {'range': [0, target_val], 'color': "rgba(30, 41, 59, 0.5)"}
            ],
            'threshold': {
                'line': {'color': "#10b981", 'width': 4},
                'thickness': 1,
                'value': target_val
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white', 'family': 'Inter'},
        height=250,
        margin=dict(l=30, r=30, t=40, b=10)
    )
    return fig
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_col_by_index"></a> `get_col_by_index` — L4165–L4169

```python
def get_col_by_index(df, index):
    """Safely grab a column by index with fallback"""
    if df is not None and not df.empty and len(df.columns) > index:
        return df.iloc[:, index]
    return pd.Series(dtype=object)
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-create_status_breakdown_chart"></a> `create_status_breakdown_chart` — L4258–L4308

```python
def create_status_breakdown_chart(deals_df, rep_name=None):
    """Create a pie chart showing deal distribution by status"""
    
    if deals_df.empty:
        return None
    
    if rep_name and 'Deal Owner' in deals_df.columns:
        deals_df = deals_df[deals_df['Deal Owner'] == rep_name]
    
    # Only show Q2 deals (filter out Q2 and Q4 spillover)
    spillover_col = get_spillover_column(deals_df)
    if spillover_col:
        q2_mask = is_q2_deal(deals_df, spillover_col)
        deals_df = deals_df[q2_mask]
    
    if deals_df.empty:
        return None
    
    status_summary = deals_df.groupby('Status')['Amount'].sum().reset_index()
    
    color_map = {
        'Expect': '#3b82f6',
        'Commit': '#10b981',
        'Best Case': '#f59e0b',
        'Opportunity': '#8b5cf6'
    }
    
    fig = px.pie(
        status_summary,
        values='Amount',
        names='Status',
        title='Deal Amount by Forecast Category (Q2 Only)',
        color='Status',
        color_discrete_map=color_map,
        hole=0.4
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#f8fafc", family="Inter"),
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(color="#94a3b8")
        )
    )
    
    return fig
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-create_pipeline_breakdown_chart"></a> `create_pipeline_breakdown_chart` — L4310–L4382

```python
def create_pipeline_breakdown_chart(deals_df, rep_name=None):
    """Create a stacked bar chart showing pipeline breakdown"""
    
    if deals_df.empty:
        return None
    
    if rep_name and 'Deal Owner' in deals_df.columns:
        deals_df = deals_df[deals_df['Deal Owner'] == rep_name]
    
    # Only show Q2 deals (filter out Q2 and Q4 spillover)
    spillover_col = get_spillover_column(deals_df)
    if spillover_col:
        q2_mask = is_q2_deal(deals_df, spillover_col)
        deals_df = deals_df[q2_mask]
    
    if deals_df.empty:
        return None
    
    # Group by pipeline and status
    pipeline_summary = deals_df.groupby(['Pipeline', 'Status'])['Amount'].sum().reset_index()
    
    color_map = {
        'Expect': '#3b82f6',
        'Commit': '#10b981',
        'Best Case': '#f59e0b',
        'Opportunity': '#8b5cf6'
    }
    
    fig = px.bar(
        pipeline_summary,
        x='Pipeline',
        y='Amount',
        color='Status',
        title='Pipeline Breakdown by Forecast Category (Q2 Only)',
        color_discrete_map=color_map,
        text_auto='.2s',
        barmode='stack'
    )

    fig.update_traces(textfont_size=14, textposition='auto')

    fig.update_layout(
        height=450,
        yaxis_title="Amount ($)",
        xaxis_title="Pipeline",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#f8fafc", family="Inter"),
        xaxis=dict(
            automargin=True,
            tickangle=-45,
            showgrid=False,
            tickfont=dict(color='#94a3b8')
        ),
        yaxis=dict(
            automargin=True,
            showgrid=True,
            gridcolor='rgba(255,255,255,0.05)',
            tickfont=dict(color='#94a3b8')
        ),
        margin=dict(l=50, r=50, t=80, b=100),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#94a3b8")
        )
    )
    
    return fig
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-create_deals_timeline"></a> `create_deals_timeline` — L4384–L4467

```python
def create_deals_timeline(deals_df, rep_name=None):
    """Create a timeline showing when deals are expected to close"""
    
    if deals_df.empty:
        return None
    
    if rep_name and 'Deal Owner' in deals_df.columns:
        deals_df = deals_df[deals_df['Deal Owner'] == rep_name]
    
    # Filter out deals without close dates
    if 'Close Date' not in deals_df.columns:
        return None
    timeline_df = deals_df[deals_df['Close Date'].notna()].copy()
    
    if timeline_df.empty:
        return None
    
    # Sort by close date
    timeline_df = timeline_df.sort_values('Close Date')
    
    # Add Q1/Q4/Q2 indicator to color map
    spillover_col = get_spillover_column(timeline_df)
    
    def get_quarter(row):
        if spillover_col and spillover_col in row.index:
            spillover_val = row.get(spillover_col, '')
            if spillover_col == 'Q3 2026 Spillover':
                if spillover_val == 'Q1 2026':
                    return 'Q1 2026 Spillover'
                elif spillover_val == 'Q3 2026':
                    return 'Q3 2026 Spillover'
        return 'Q2 2026'
    
    timeline_df['Quarter'] = timeline_df.apply(get_quarter, axis=1)
    
    color_map = {
        'Expect': '#3b82f6',
        'Commit': '#10b981',
        'Best Case': '#f59e0b',
        'Opportunity': '#8b5cf6'
    }
    
    fig = px.scatter(
        timeline_df,
        x='Close Date',
        y='Amount',
        color='Status',
        size='Amount',
        hover_data=['Deal Name', 'Amount', 'Pipeline', 'Quarter'],
        title='Deal Close Date Timeline',
        color_discrete_map=color_map
    )
    
    # Fixed: Use datetime object for the vertical line
    from datetime import datetime
    q4_boundary = datetime(2026, 3, 31)
    
    try:
        fig.add_vline(
            x=q4_boundary, 
            line_dash="dash", 
            line_color="#ef4444",
            annotation_text="Q1/Q2 Boundary"
        )
    except:
        pass
    
    fig.update_layout(
        height=400,
        yaxis_title="Deal Amount ($)",
        xaxis_title="Expected Close Date",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#f8fafc", family="Inter"),
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(color="#94a3b8")
        ),
        xaxis=dict(showgrid=False, tickfont=dict(color='#94a3b8')),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#94a3b8'))
    )
    
    return fig
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-create_invoice_status_chart"></a> `create_invoice_status_chart` — L4469–L4504

```python
def create_invoice_status_chart(invoices_df, rep_name=None):
    """Create a chart showing invoice breakdown by status"""
    
    if invoices_df.empty:
        return None
    
    if rep_name:
        invoices_df = invoices_df[invoices_df['Sales Rep'] == rep_name]
    
    if invoices_df.empty:
        return None
    
    status_summary = invoices_df.groupby('Status')['Amount'].sum().reset_index()
    
    fig = px.pie(
        status_summary,
        values='Amount',
        names='Status',
        title='Invoice Amount by Status',
        hole=0.4
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#f8fafc", family="Inter"),
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(color="#94a3b8")
        )
    )
    
    return fig
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_business_days_before"></a> `get_business_days_before` — L897–L908

```python
def get_business_days_before(end_date, business_days):
        """Calculate date that is N business days before end_date"""
        current = end_date
        days_counted = 0
        
        while days_counted < business_days:
            current -= timedelta(days=1)
            # Skip weekends (Monday=0, Sunday=6)
            if current.weekday() < 5:
                days_counted += 1
        
        return current
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_planning_status"></a> `get_planning_status` — L2159–L2171

```python
def get_planning_status(id_value):
        """Get planning status (IN/OUT/MAYBE) for a given SO# or Deal ID"""
        if not id_value or pd.isna(id_value):
            return None
        id_str = str(id_value).strip()
        item_data = st.session_state[planning_key].get(id_str)
        if item_data:
            # Handle both old format (string) and new format (dict)
            if isinstance(item_data, dict):
                return item_data.get('status')
            else:
                return item_data  # Backward compatibility
        return None
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_planning_notes"></a> `get_planning_notes` — L2173–L2181

```python
def get_planning_notes(id_value):
        """Get planning notes for a given SO# or Deal ID"""
        if not id_value or pd.isna(id_value):
            return ''
        id_str = str(id_value).strip()
        item_data = st.session_state[planning_key].get(id_str)
        if item_data and isinstance(item_data, dict):
            return item_data.get('notes', '')
        return ''
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_amount_override"></a> `get_amount_override` — L2211–L2215

```python
def get_amount_override(so_num):
        """Get user-edited amount for a given SO#, or None if not overridden"""
        if not so_num or pd.isna(so_num):
            return None
        return st.session_state[amount_override_key].get(str(so_num).strip())
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-set_amount_override"></a> `set_amount_override` — L2217–L2220

```python
def set_amount_override(so_num, amount):
        """Store a user-edited amount override for a given SO#"""
        if so_num and not pd.isna(so_num):
            st.session_state[amount_override_key][str(so_num).strip()] = amount
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_prod_sched"></a> `get_prod_sched` — L2236–L2241

```python
def get_prod_sched(so_num):
        """Look up Production Schedule info for a given SO#"""
        if not so_num or pd.isna(so_num):
            return {'on_schedule': 'No', 'prod_ship_date': '', 'prod_start': '', 'prod_end': '', 'prod_notes': ''}
        return prod_sched_lookup.get(str(so_num).strip(),
               {'on_schedule': 'No', 'prod_ship_date': '', 'prod_start': '', 'prod_end': '', 'prod_notes': ''})
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_amie_update"></a> `get_amie_update` — L2253–L2257

```python
def get_amie_update(so_num):
        """Look up Amie Update info for a given SO#"""
        if not so_num or pd.isna(so_num):
            return {'amie_pf_date': ''}
        return amie_lookup.get(str(so_num).strip(), {'amie_pf_date': ''})
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_col_by_index"></a> `get_col_by_index` — L2262–L2265

```python
def get_col_by_index(df, index):
        if df is not None and len(df.columns) > index:
            return df.iloc[:, index]
        return pd.Series()
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-format_ns_view"></a> `format_ns_view` — L2378–L2457

```python
def format_ns_view(df, date_col_name):
        if df.empty: 
            return df
        d = df.copy()
        
        # Create Amount_Numeric based on shipping toggle
        if ns_amount_col in d.columns:
            d['Amount_Numeric'] = pd.to_numeric(d[ns_amount_col], errors='coerce').fillna(0)
        elif 'Amount' in d.columns:
            d['Amount_Numeric'] = pd.to_numeric(d['Amount'], errors='coerce').fillna(0)
        else:
            d['Amount_Numeric'] = 0
        
        # CRITICAL: Ensure Sales Rep column is preserved
        # Sales Rep should already exist from Rep Master (Column AF)
        if 'Sales Rep' not in d.columns and 'Rep Master' in d.columns:
            d['Sales Rep'] = d['Rep Master']
        
        # Add display columns
        if 'Internal ID' in d.columns:
            d['Link'] = d['Internal ID'].apply(lambda x: f"https://7086864.app.netsuite.com/app/accounting/transactions/salesord.nl?id={x}" if pd.notna(x) else "")
        
        # Add SO# column (from Display_SO_Num)
        if 'Display_SO_Num' in d.columns:
            d['SO #'] = d['Display_SO_Num']
        
        # Add Order Type column (from Display_Type)
        if 'Display_Type' in d.columns:
            d['Type'] = d['Display_Type']
        
        # Add Ship Date based on category
        # date_col_name indicates which date field was used to classify this SO
        if date_col_name == 'Promise':
            # For PF with date: use Customer Promise Date OR Projected Date (whichever exists)
            d['Ship Date'] = ''
            
            # Try Customer Promise Date first
            if 'Display_Promise_Date' in d.columns:
                promise_dates = pd.to_datetime(d['Display_Promise_Date'], errors='coerce')
                d.loc[promise_dates.notna(), 'Ship Date'] = promise_dates.dt.strftime('%Y-%m-%d')
            
            # Fill in with Projected Date where Promise Date is missing
            if 'Display_Projected_Date' in d.columns:
                projected_dates = pd.to_datetime(d['Display_Projected_Date'], errors='coerce')
                mask = (d['Ship Date'] == '') & projected_dates.notna()
                if mask.any():
                    d.loc[mask, 'Ship Date'] = projected_dates.loc[mask].dt.strftime('%Y-%m-%d')
                    
        elif date_col_name == 'PA_Date':
            # For PA with date: use Pending Approval Date
            if 'Display_PA_Date' in d.columns:
                pa_dates = pd.to_datetime(d['Display_PA_Date'], errors='coerce')
                d['Ship Date'] = pa_dates.dt.strftime('%Y-%m-%d').fillna('')
            else:
                d['Ship Date'] = ''
        else:
            # For PF/PA no date or other: show blank
            d['Ship Date'] = ''

        # --- ENRICH WITH PRODUCTION SCHEDULE ---
        if 'SO #' in d.columns:
            d['Prod Sched'] = d['SO #'].apply(lambda so: get_prod_sched(so)['on_schedule'])
            d['Prod Ship'] = d['SO #'].apply(lambda so: get_prod_sched(so)['prod_ship_date'])
            d['Prod Start'] = d['SO #'].apply(lambda so: get_prod_sched(so)['prod_start'])
            d['Prod End'] = d['SO #'].apply(lambda so: get_prod_sched(so)['prod_end'])
            d['Prod Notes'] = d['SO #'].apply(lambda so: get_prod_sched(so)['prod_notes'])

        # --- ENRICH WITH AMIE UPDATE ---
        if 'SO #' in d.columns:
            d['Amie PF Date'] = d['SO #'].apply(lambda so: get_amie_update(so)['amie_pf_date'])

        # --- APPLY AMOUNT OVERRIDES ---
        if 'SO #' in d.columns:
            for idx in d.index:
                so_num = str(d.at[idx, 'SO #']).strip()
                override = get_amount_override(so_num)
                if override is not None:
                    d.at[idx, 'Amount_Numeric'] = override

        return d.sort_values('Amount_Numeric', ascending=False) if 'Amount_Numeric' in d.columns else d
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-safe_sum"></a> `safe_sum` — L3019–L3032

```python
def safe_sum(df, is_hubspot=False):
        if df.empty:
            return 0
        if is_hubspot and use_probability_for_calc:
            if 'Prob_Amount_Numeric' in df.columns:
                return df['Prob_Amount_Numeric'].sum()
            elif 'Amount_Numeric' in df.columns:
                return df['Amount_Numeric'].sum()
        else:
            if 'Amount_Numeric' in df.columns:
                return df['Amount_Numeric'].sum()
            elif 'Amount' in df.columns:
                return df['Amount'].sum()
        return 0
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_amount"></a> `get_amount` — L3679–L3686

```python
def get_amount(df):
        # Try the preferred column first, fall back to Amount if not available
        if not df.empty:
            if amount_col in df.columns:
                return df[amount_col].sum()
            elif 'Amount' in df.columns:
                return df['Amount'].sum()
        return 0
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_quarter"></a> `get_quarter` — L4407–L4415

```python
def get_quarter(row):
        if spillover_col and spillover_col in row.index:
            spillover_val = row.get(spillover_col, '')
            if spillover_col == 'Q3 2026 Spillover':
                if spillover_val == 'Q1 2026':
                    return 'Q1 2026 Spillover'
                elif spillover_val == 'Q3 2026':
                    return 'Q3 2026 Spillover'
        return 'Q2 2026'
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_so_metrics"></a> `get_so_metrics` — L5553–L5629

```python
def get_so_metrics(rep_name):
        metrics = {'pf_with_date': 0, 'pf_no_date': 0, 'pa_with_date': 0, 'pa_no_date': 0, 'pa_old': 0, 'pf_spillover': 0, 'pa_spillover': 0}
        
        if sales_orders_df.empty:
            return metrics
        
        if 'Sales Rep' not in sales_orders_df.columns:
            return metrics
        
        rep_orders = sales_orders_df[sales_orders_df['Sales Rep'] == rep_name].copy()
        if rep_orders.empty:
            return metrics
        
        amount_col = 'Amount' if include_shipping else 'Net_Amount'
        if amount_col not in rep_orders.columns:
            amount_col = 'Amount'
        if amount_col not in rep_orders.columns:
            return metrics
        
        rep_orders['Amount_Calc'] = pd.to_numeric(rep_orders[amount_col], errors='coerce').fillna(0)
        
        # Find Updated Status column
        status_col = None
        for col in ['Updated Status', 'Updated_Status', 'UpdatedStatus']:
            if col in rep_orders.columns:
                status_col = col
                break
        
        if not status_col:
            return metrics
        
        # Parse date columns for spillover detection (matching Apps Script V5)
        q2_end = pd.Timestamp('2026-06-30')
        
        # Customer Promise Date (Col L) and Projected Date (Col M)
        promise_col = 'Customer Promise Date' if 'Customer Promise Date' in rep_orders.columns else None
        projected_col = 'Projected Date' if 'Projected Date' in rep_orders.columns else None
        pa_date_col = 'Pending Approval Date' if 'Pending Approval Date' in rep_orders.columns else None
        
        if promise_col:
            rep_orders['_promise'] = pd.to_datetime(rep_orders[promise_col], errors='coerce')
        if projected_col:
            rep_orders['_projected'] = pd.to_datetime(rep_orders[projected_col], errors='coerce')
        if pa_date_col:
            rep_orders['_pa_date'] = pd.to_datetime(rep_orders[pa_date_col], errors='coerce')
        
        for _, row in rep_orders.iterrows():
            status = str(row.get(status_col, '')).strip()
            amount = row['Amount_Calc']
            
            if 'PF with Date' in status or 'PF w/ Date' in status:
                # Check for PF spillover: min(promise, projected) > Q2 end
                promise_dt = row.get('_promise', pd.NaT) if promise_col else pd.NaT
                projected_dt = row.get('_projected', pd.NaT) if projected_col else pd.NaT
                dates = [d for d in [promise_dt, projected_dt] if pd.notna(d)]
                ship_date = min(dates) if dates else None
                
                if ship_date and ship_date > q2_end:
                    metrics['pf_spillover'] += amount
                else:
                    metrics['pf_with_date'] += amount
            elif 'PF No Date' in status or 'PF no Date' in status:
                metrics['pf_no_date'] += amount
            elif 'PA with Date' in status or 'PA w/ Date' in status:
                # Check for PA spillover: pending approval date > Q2 end
                pa_dt = row.get('_pa_date', pd.NaT) if pa_date_col else pd.NaT
                
                if pd.notna(pa_dt) and pa_dt > q2_end:
                    metrics['pa_spillover'] += amount
                else:
                    metrics['pa_with_date'] += amount
            elif 'PA No Date' in status or 'PA no Date' in status:
                metrics['pa_no_date'] += amount
            elif 'PA Old' in status or '>2 Week' in status:
                metrics['pa_old'] += amount
        
        return metrics
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_hs_metrics"></a> `get_hs_metrics` — L5632–L5686

```python
def get_hs_metrics(rep_name):
        metrics = {
            'expect': 0, 'expect_prob': 0,
            'commit': 0, 'commit_prob': 0,
            'best_case': 0, 'best_case_prob': 0,
            'opportunity': 0, 'opportunity_prob': 0,
            'q2_spillover': 0, 'q2_spillover_prob': 0
        }
        
        if deals_df.empty or 'Deal Owner' not in deals_df.columns:
            return metrics
        
        rep_deals = deals_df[deals_df['Deal Owner'] == rep_name].copy()
        if rep_deals.empty:
            return metrics
        
        # Find spillover column
        spillover_col = None
        for col in rep_deals.columns:
            col_lower = str(col).lower()
            if 'spillover' in col_lower or ('q2' in col_lower and '2026' in col_lower):
                spillover_col = col
                break
        
        for _, row in rep_deals.iterrows():
            status = str(row.get('Status', '')).strip()
            amount = pd.to_numeric(row.get('Amount', 0), errors='coerce') or 0
            prob_amount = pd.to_numeric(row.get('Probability Rev', amount), errors='coerce') or amount
            
            # Check if Q2 spillover
            is_q2 = False
            if spillover_col and spillover_col in row.index:
                spillover_val = str(row.get(spillover_col, '')).upper()
                if 'Q2' in spillover_val:
                    is_q2 = True
                elif 'Q4' in spillover_val:
                    continue
            
            if is_q2:
                metrics['q2_spillover'] += amount
                metrics['q2_spillover_prob'] += prob_amount
            elif status == 'Expect':
                metrics['expect'] += amount
                metrics['expect_prob'] += prob_amount
            elif status == 'Commit':
                metrics['commit'] += amount
                metrics['commit_prob'] += prob_amount
            elif status == 'Best Case':
                metrics['best_case'] += amount
                metrics['best_case_prob'] += prob_amount
            elif status == 'Opportunity':
                metrics['opportunity'] += amount
                metrics['opportunity_prob'] += prob_amount
        
        return metrics
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-style_face_value"></a> `style_face_value` — L5890–L5918

```python
def style_face_value(df):
        # Create a style dataframe
        styles = pd.DataFrame('', index=df.index, columns=df.columns)
        
        # Highlight Total and All Q2 columns
        styles['Total'] = 'background-color: rgba(59, 130, 246, 0.2)'
        styles['All Q2'] = 'background-color: rgba(59, 130, 246, 0.2)'
        
        # Highlight Forecast column
        styles['Forecast'] = 'background-color: rgba(139, 92, 246, 0.3); color: #a78bfa; font-weight: bold'
        
        # Highlight Q2, PF Spill, PA Spill and Full Pipe
        styles['PF Spill'] = 'color: #f472b6'
        styles['PA Spill'] = 'color: #f472b6'
        styles['Q3 Spill'] = 'color: #f472b6'
        styles['Full Pipe'] = 'background-color: rgba(244, 114, 182, 0.2); color: #f472b6'
        
        # Color % column based on value
        for i, row in df.iterrows():
            if row['%'] >= 0:
                styles.loc[i, '%'] = 'color: #4ade80; font-weight: bold'
            else:
                styles.loc[i, '%'] = 'color: #f87171; font-weight: bold'
        
        # Bold the totals row
        if len(df) > 0:
            styles.iloc[-1] = styles.iloc[-1].apply(lambda x: x + '; font-weight: bold; background-color: rgba(59, 130, 246, 0.3)')
        
        return styles
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-clean_numeric"></a> `clean_numeric` — L1114–L1121

```python
def clean_numeric(value):
            if pd.isna(value) or str(value).strip() == '':
                return 0
            cleaned = str(value).replace(',', '').replace('$', '').replace(' ', '').strip()
            try:
                return float(cleaned)
            except:
                return 0
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-clean_numeric_so"></a> `clean_numeric_so` — L1452–L1460

```python
def clean_numeric_so(value):
            value_str = str(value).strip()
            if value_str == '' or value_str == 'nan' or value_str == 'None':
                return 0
            cleaned = value_str.replace(',', '').replace('$', '').replace(' ', '')
            try:
                return float(cleaned)
            except:
                return 0
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-calculate_so_metrics"></a> `calculate_so_metrics` — L1698–L1736

```python
def calculate_so_metrics(so_df):
            metrics = {
                'pending_fulfillment': 0,
                'pending_fulfillment_no_date': 0,
                'pending_approval': 0,
                'pending_approval_no_date': 0,
                'pending_approval_old': 0
            }
            
            if so_df.empty:
                return metrics
            
            so_df = so_df.copy()
            so_df['Amount_Numeric'] = pd.to_numeric(so_df.get('Amount', 0), errors='coerce')
            
            # Use Updated Status column if available
            if 'Updated Status' in so_df.columns:
                so_df['Updated_Status_Clean'] = so_df['Updated Status'].astype(str).str.strip()
                
                # Pending Fulfillment with date (Ext + Int)
                pf_date_ext = so_df[so_df['Updated_Status_Clean'] == 'PF with Date (Ext)']['Amount_Numeric'].sum()
                pf_date_int = so_df[so_df['Updated_Status_Clean'] == 'PF with Date (Int)']['Amount_Numeric'].sum()
                metrics['pending_fulfillment'] = pf_date_ext + pf_date_int
                
                # Pending Fulfillment no date (Ext + Int)
                pf_nodate_ext = so_df[so_df['Updated_Status_Clean'] == 'PF No Date (Ext)']['Amount_Numeric'].sum()
                pf_nodate_int = so_df[so_df['Updated_Status_Clean'] == 'PF No Date (Int)']['Amount_Numeric'].sum()
                metrics['pending_fulfillment_no_date'] = pf_nodate_ext + pf_nodate_int
                
                # Pending Approval with date
                metrics['pending_approval'] = so_df[so_df['Updated_Status_Clean'] == 'PA with Date']['Amount_Numeric'].sum()
                
                # Pending Approval no date
                metrics['pending_approval_no_date'] = so_df[so_df['Updated_Status_Clean'] == 'PA No Date']['Amount_Numeric'].sum()
                
                # Pending Approval old (>2 weeks)
                metrics['pending_approval_old'] = so_df[so_df['Updated_Status_Clean'] == 'PA Old (>2 Weeks)']['Amount_Numeric'].sum()
            
            return metrics
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-format_hs_view"></a> `format_hs_view` — L2499–L2526

```python
def format_hs_view(df):
            if df.empty: return df
            d = df.copy()
            
            # CRITICAL: Ensure Deal Owner column is preserved
            # Deal Owner should already exist from column mapping
            if 'Deal Owner' not in d.columns:
                if 'Deal Owner First Name' in d.columns and 'Deal Owner Last Name' in d.columns:
                    d['Deal Owner'] = d['Deal Owner First Name'].fillna('') + ' ' + d['Deal Owner Last Name'].fillna('')
                    d['Deal Owner'] = d['Deal Owner'].str.strip()
            
            # Add Deal ID column (from Record ID)
            if 'Record ID' in d.columns:
                d['Deal ID'] = d['Record ID']
            
            d['Type'] = d['Display_Type']
            d['Close'] = pd.to_datetime(d['Close Date'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
            
            # Change to Pending Approval Date
            if 'Display_PA_Date' in d.columns:
                pa_dates = pd.to_datetime(d['Display_PA_Date'], errors='coerce')
                d['PA Date'] = pa_dates.dt.strftime('%Y-%m-%d').fillna('')
            else:
                d['PA Date'] = ''
            
            if 'Record ID' in d.columns:
                d['Link'] = d['Record ID'].apply(lambda x: f"https://app.hubspot.com/contacts/6712259/record/0-3/{x}/" if pd.notna(x) else "")
            return d.sort_values(['Type', 'Amount_Numeric'], ascending=[True, False])
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-calculate_biz_days"></a> `calculate_biz_days` — L3147–L3157

```python
def calculate_biz_days():
             from datetime import date, timedelta
             today = date.today()
             q4_end = date(2025, 12, 31)
             holidays = [date(2025, 11, 27), date(2025, 11, 28), date(2025, 12, 25), date(2025, 12, 26)]
             days = 0
             current = today
             while current <= q4_end:
                 if current.weekday() < 5 and current not in holidays: days += 1
                 current += timedelta(days=1)
             return days
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-clean_numeric"></a> `clean_numeric` — L1173–L1180

```python
def clean_numeric(value):
                if pd.isna(value) or str(value).strip() == '':
                    return 0
                cleaned = str(value).replace(',', '').replace('$', '').replace(' ', '').strip()
                try:
                    return float(cleaned)
                except:
                    return 0
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-clean_numeric"></a> `clean_numeric` — L1252–L1259

```python
def clean_numeric(value):
                if pd.isna(value) or str(value).strip() == '':
                    return 0
                cleaned = str(value).replace(',', '').replace('$', '').replace(' ', '').strip()
                try:
                    return float(cleaned)
                except:
                    return 0
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-business_days_between"></a> `business_days_between` — L1510–L1514

```python
def business_days_between(start_date, end_date):
                if pd.isna(start_date):
                    return 0
                days = pd.bdate_range(start=start_date, end=end_date).size - 1
                return max(0, days)
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_expect_amount"></a> `get_expect_amount` — L1866–L1878

```python
def get_expect_amount(df):
                if df.empty or 'Status' not in df.columns:
                    return 0
                df = df.copy()
                df['Amount_Numeric'] = pd.to_numeric(df.get('Amount', 0), errors='coerce')
                # Use spillover column - handles both old and new column names
                spillover_col = get_spillover_column(df)
                if spillover_col:
                    q2_mask = is_q2_deal(df, spillover_col)
                    q1_deals = df[q2_mask]
                else:
                    q1_deals = df
                return q1_deals[q1_deals['Status'] == 'Expect']['Amount_Numeric'].sum()
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_best_case_amount"></a> `get_best_case_amount` — L1887–L1899

```python
def get_best_case_amount(df):
                if df.empty or 'Status' not in df.columns:
                    return 0
                df = df.copy()
                df['Amount_Numeric'] = pd.to_numeric(df.get('Amount', 0), errors='coerce')
                # Use spillover column - handles both old and new column names
                spillover_col = get_spillover_column(df)
                if spillover_col:
                    q2_mask = is_q2_deal(df, spillover_col)
                    q1_deals = df[q2_mask]
                else:
                    q1_deals = df
                return q1_deals[q1_deals['Status'] == 'Best Case']['Amount_Numeric'].sum()
```

### <a id="calyx-sop-dashboard-v2-src-q2_revenue_snapshot-py-get_opportunity_amount"></a> `get_opportunity_amount` — L1911–L1923

```python
def get_opportunity_amount(df):
                if df.empty or 'Status' not in df.columns:
                    return 0
                df = df.copy()
                df['Amount_Numeric'] = pd.to_numeric(df.get('Amount', 0), errors='coerce')
                # Use spillover column - handles both old and new column names
                spillover_col = get_spillover_column(df)
                if spillover_col:
                    q2_mask = is_q2_deal(df, spillover_col)
                    q1_deals = df[q2_mask]
                else:
                    q1_deals = df
                return q1_deals[q1_deals['Status'] == 'Opportunity']['Amount_Numeric'].sum()
```

## calyx-sop-dashboard-v2/src/q4_revenue_snapshot.py

### <a id="calyx-sop-dashboard-v2-src-q4_revenue_snapshot-py-get_spreadsheet_id"></a> `get_spreadsheet_id` — L26–L30

```python
def get_spreadsheet_id():
    try:
        return st.secrets.get("spreadsheet_id", "15JhBZ_7aHHZA1W1qsoC2163borL6RYjk0xTDWPmWPfA")
    except:
        return "15JhBZ_7aHHZA1W1qsoC2163borL6RYjk0xTDWPmWPfA"
```

### <a id="calyx-sop-dashboard-v2-src-q4_revenue_snapshot-py-clean_numeric"></a> `clean_numeric` — L100–L108

```python
def clean_numeric(value):
    """Convert value to numeric, handling currency formatting"""
    if pd.isna(value) or str(value).strip() == '':
        return 0
    cleaned = str(value).replace(',', '').replace('$', '').replace(' ', '').strip()
    try:
        return float(cleaned)
    except:
        return 0
```

### <a id="calyx-sop-dashboard-v2-src-q4_revenue_snapshot-py-load_all_data"></a> `load_all_data` — L110–L127

```python
def load_all_data():
    """Load all required data for Q4 review"""
    
    # Load invoice data - extended to column Y for Product Type
    invoices_df = load_google_sheets_data("_NS_Invoices_Data", "A:Y", version=CACHE_VERSION)
    
    # Load dashboard info (rep quotas)
    dashboard_df = load_google_sheets_data("Dashboard Info", "A:C", version=CACHE_VERSION)
    
    # Process invoices
    if not invoices_df.empty:
        invoices_df = process_invoices(invoices_df)
    
    # Process dashboard info
    if not dashboard_df.empty:
        dashboard_df = process_dashboard_info(dashboard_df)
    
    return invoices_df, dashboard_df
```

### <a id="calyx-sop-dashboard-v2-src-q4_revenue_snapshot-py-process_invoices"></a> `process_invoices` — L129–L212

```python
def process_invoices(df):
    """Process invoice data for Q4 analysis"""
    if df.empty:
        return df
    
    col_mapping = {}
    col_names = df.columns.tolist()
    
    # Map columns by name
    for i, col in enumerate(col_names):
        col_lower = str(col).lower().strip()
        if 'document' in col_lower and 'number' in col_lower:
            col_mapping[col] = 'Invoice Number'
        elif col_lower == 'status':
            col_mapping[col] = 'Status'
        elif col_lower == 'date' and 'due' not in col_lower and 'closed' not in col_lower:
            col_mapping[col] = 'Date'
        elif col_lower == 'customer':
            col_mapping[col] = 'Customer'
        elif 'amount' in col_lower and 'transaction total' in col_lower:
            col_mapping[col] = 'Amount'
        elif 'amount' in col_lower and 'remaining' in col_lower:
            col_mapping[col] = 'Amount Remaining'
        elif col_lower == 'sales rep':
            col_mapping[col] = 'Sales Rep'
        elif 'hubspot' in col_lower and 'pipeline' in col_lower:
            col_mapping[col] = 'Pipeline'
        elif col_lower == 'department':
            col_mapping[col] = 'Department'
        elif col_lower == 'period':
            col_mapping[col] = 'Period'
        elif 'corrected' in col_lower and 'customer' in col_lower:
            col_mapping[col] = 'Corrected Customer'
        elif col_lower == 'rep master':
            col_mapping[col] = 'Rep Master'
        elif 'product' in col_lower and 'type' in col_lower:
            col_mapping[col] = 'Product Type'
    
    df = df.rename(columns=col_mapping)
    
    # CRITICAL: Use column U (index 20) as Rep Master for accurate rep attribution
    # This is the authoritative source for which rep gets credit
    if len(col_names) >= 21:  # Column U exists (index 20)
        col_u_name = col_names[20]
        df['Rep Master'] = df[col_u_name].astype(str).str.strip()
    
    # Use column Y (index 24) for Product Type
    if len(col_names) >= 25:  # Column Y exists (index 24)
        col_y_name = col_names[24]
        df['Product Type'] = df[col_y_name].astype(str).str.strip()
    
    # Use Rep Master as the Sales Rep (source of truth)
    if 'Rep Master' in df.columns:
        invalid_values = ['', 'nan', 'None', '#N/A', '#REF!', '#VALUE!', '#ERROR!']
        df = df[~df['Rep Master'].isin(invalid_values)]
        df['Sales Rep'] = df['Rep Master']
    
    # Use Corrected Customer if available
    if 'Corrected Customer' in df.columns and 'Customer' in df.columns:
        df['Corrected Customer'] = df['Corrected Customer'].astype(str).str.strip()
        invalid_values = ['', 'nan', 'None', '#N/A', '#REF!', '#VALUE!', '#ERROR!']
        mask = ~df['Corrected Customer'].isin(invalid_values)
        df.loc[mask, 'Customer'] = df.loc[mask, 'Corrected Customer']
    
    # Clean amount
    if 'Amount' in df.columns:
        df['Amount'] = df['Amount'].apply(clean_numeric)
    else:
        df['Amount'] = 0
    
    # Parse date and filter for Q4 2025
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df[(df['Date'] >= Q4_START) & (df['Date'] <= Q4_END)]
        df['Month'] = df['Date'].dt.strftime('%B %Y')
        df['Month_Num'] = df['Date'].dt.month
    
    # Clean Sales Rep
    if 'Sales Rep' in df.columns:
        df['Sales Rep'] = df['Sales Rep'].astype(str).str.strip()
        invalid_reps = ['', 'nan', 'None', '#N/A', '#REF!']
        df = df[~df['Sales Rep'].isin(invalid_reps)]
    
    return df
```

### <a id="calyx-sop-dashboard-v2-src-q4_revenue_snapshot-py-process_dashboard_info"></a> `process_dashboard_info` — L214–L240

```python
def process_dashboard_info(df):
    """Process dashboard info for quota data"""
    if df.empty:
        return df
    
    col_names = df.columns.tolist()
    rename_map = {}
    
    for col in col_names:
        col_lower = str(col).lower().strip()
        if 'rep' in col_lower and 'name' in col_lower:
            rename_map[col] = 'Rep Name'
        elif 'quota' in col_lower:  # More flexible matching
            rename_map[col] = 'Quota'
        elif 'netsuite' in col_lower and 'order' in col_lower:
            rename_map[col] = 'NetSuite Orders'
    
    df = df.rename(columns=rename_map)
    
    # Debug: show what we found
    if 'Quota' not in df.columns:
        st.sidebar.warning(f"⚠️ Dashboard Info columns: {df.columns.tolist()}")
    
    if 'Quota' in df.columns:
        df['Quota'] = df['Quota'].apply(clean_numeric)
    
    return df
```

### <a id="calyx-sop-dashboard-v2-src-q4_revenue_snapshot-py-get_medal"></a> `get_medal` — L340–L344

```python
def get_medal(idx):
            if idx == 0: return "🥇"
            elif idx == 1: return "🥈"
            elif idx == 2: return "🥉"
            else: return f"#{idx + 1}"
```

## calyx-sop-dashboard-v2/src/sales_rep_view.py

### <a id="calyx-sop-dashboard-v2-src-sales_rep_view-py-clean_dataframe"></a> `clean_dataframe` — L20–L26

```python
def clean_dataframe(df):
    """Remove duplicate columns from DataFrame."""
    if df is None:
        return None
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]
    return df
```

### <a id="calyx-sop-dashboard-v2-src-sales_rep_view-py-get_column_as_series"></a> `get_column_as_series` — L29–L36

```python
def get_column_as_series(df, col_name):
    """Safely get a column as a Series, handling duplicates."""
    if col_name not in df.columns:
        return None
    result = df.loc[:, col_name]
    if isinstance(result, pd.DataFrame):
        return result.iloc[:, 0]
    return result
```

### <a id="calyx-sop-dashboard-v2-src-sales_rep_view-py-find_column"></a> `find_column` — L39–L49

```python
def find_column(df, keywords, exclude=None):
    """Find first column matching any keyword."""
    if df is None:
        return None
    exclude = exclude or []
    for col in df.columns:
        col_lower = str(col).lower()
        if any(kw in col_lower for kw in keywords):
            if not any(ex in col_lower for ex in exclude):
                return col
    return None
```

## calyx-sop-dashboard-v2/src/scenario_planning.py

### <a id="calyx-sop-dashboard-v2-src-scenario_planning-py-generate_scenario_forecast"></a> `generate_scenario_forecast` — L330–L400

```python
def generate_scenario_forecast(
    monthly_demand: pd.Series,
    monthly_revenue: pd.Series,
    deals: pd.DataFrame,
    horizon: int,
    model: str,
    growth_rate: float,
    demand_weight: float,
    seasonality_factor: float,
    quarterly_adjustments: Dict[str, float]
) -> ForecastResult:
    """Generate a scenario forecast with all adjustments applied."""
    
    # Generate base demand forecast
    base_forecast = generate_forecast(monthly_demand, model=model, horizon=horizon)
    
    # Apply adjustments
    adjusted_values = base_forecast.forecast.copy()
    
    # 1. Apply growth rate (compound monthly)
    if growth_rate != 0:
        monthly_growth = (1 + growth_rate / 100) ** (1/12) - 1
        for i in range(len(adjusted_values)):
            adjusted_values.iloc[i] *= (1 + monthly_growth) ** (i + 1)
    
    # 2. Apply seasonality factor
    if seasonality_factor != 1.0:
        # Calculate historical seasonality pattern
        seasonal_pattern = monthly_demand.groupby(monthly_demand.index.month).mean()
        overall_mean = seasonal_pattern.mean()
        seasonal_indices = seasonal_pattern / overall_mean
        
        for i, (date, value) in enumerate(adjusted_values.items()):
            month = date.month
            seasonal_idx = seasonal_indices.get(month, 1.0)
            # Adjust towards or away from 1.0 based on factor
            new_idx = 1 + (seasonal_idx - 1) * seasonality_factor
            adjusted_values.iloc[i] = value * new_idx / seasonal_idx
    
    # 3. Apply quarterly adjustments
    for i, (date, value) in enumerate(adjusted_values.items()):
        quarter = f"Q{(date.month - 1) // 3 + 1}"
        q_adj = quarterly_adjustments.get(quarter, 0) / 100
        adjusted_values.iloc[i] *= (1 + q_adj)
    
    # 4. Blend with pipeline if available
    if demand_weight < 1.0 and deals is not None and not deals.empty:
        # Create a simple pipeline-based forecast
        pipeline_forecast = create_pipeline_forecast(deals, horizon, adjusted_values.index)
        if pipeline_forecast is not None:
            adjusted_values = (adjusted_values * demand_weight + 
                             pipeline_forecast * (1 - demand_weight))
    
    # Ensure non-negative
    adjusted_values = adjusted_values.clip(lower=0)
    
    # Create new result with adjusted forecast
    return ForecastResult(
        forecast=adjusted_values,
        model_name=f"Scenario ({model})",
        confidence_lower=base_forecast.confidence_lower * (adjusted_values / base_forecast.forecast).mean() if base_forecast.confidence_lower is not None else None,
        confidence_upper=base_forecast.confidence_upper * (adjusted_values / base_forecast.forecast).mean() if base_forecast.confidence_upper is not None else None,
        metrics=base_forecast.metrics,
        parameters={
            'base_model': model,
            'growth_rate': growth_rate,
            'demand_weight': demand_weight,
            'seasonality_factor': seasonality_factor,
            'quarterly_adjustments': quarterly_adjustments
        }
    )
```

### <a id="calyx-sop-dashboard-v2-src-scenario_planning-py-create_pipeline_forecast"></a> `create_pipeline_forecast` — L403–L441

```python
def create_pipeline_forecast(
    deals: pd.DataFrame,
    horizon: int,
    forecast_index: pd.DatetimeIndex
) -> Optional[pd.Series]:
    """Create a forecast based on pipeline data."""
    
    if deals is None or deals.empty:
        return None
    
    # Check if required columns exist
    if 'Close Date' not in deals.columns or 'Amount' not in deals.columns:
        return None
    
    df = deals.copy()
    df['Close Date'] = pd.to_datetime(df['Close Date'], errors='coerce')
    df = df.dropna(subset=['Close Date', 'Amount'])
    
    if df.empty:
        return None
    
    # Group by month
    df['Month'] = df['Close Date'].dt.to_period('M').dt.to_timestamp()
    monthly_pipeline = df.groupby('Month')['Amount'].sum()
    
    # Map to forecast periods
    pipeline_values = []
    for period in forecast_index:
        if period in monthly_pipeline.index:
            pipeline_values.append(monthly_pipeline[period])
        else:
            # Use average pipeline as proxy
            pipeline_values.append(monthly_pipeline.mean() if len(monthly_pipeline) > 0 else 0)
    
    # Convert to quantity estimate (rough conversion)
    avg_order_value = monthly_pipeline.mean() if len(monthly_pipeline) > 0 else 1
    pipeline_qty = pd.Series(pipeline_values, index=forecast_index)
    
    return pipeline_qty
```

### <a id="calyx-sop-dashboard-v2-src-scenario_planning-py-load_scenario_forecast"></a> `load_scenario_forecast` — L576–L599

```python
def load_scenario_forecast(scenario: Dict) -> ForecastResult:
    """Load a ForecastResult from saved scenario data."""
    fc_data = scenario.get('forecast_data', {})
    
    forecast = pd.Series(fc_data.get('values', {}))
    forecast.index = pd.to_datetime(forecast.index)
    
    lower = None
    upper = None
    if 'lower' in fc_data:
        lower = pd.Series(fc_data['lower'])
        lower.index = pd.to_datetime(lower.index)
    if 'upper' in fc_data:
        upper = pd.Series(fc_data['upper'])
        upper.index = pd.to_datetime(upper.index)
    
    return ForecastResult(
        forecast=forecast,
        model_name=fc_data.get('model_name', 'Scenario'),
        confidence_lower=lower,
        confidence_upper=upper,
        metrics=fc_data.get('metrics', {}),
        parameters=fc_data.get('parameters', {})
    )
```

## calyx-sop-dashboard-v2/src/sop_data_loader.py

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-get_spreadsheet_id"></a> `get_spreadsheet_id` — L71–L73

```python
def get_spreadsheet_id():
    """Get spreadsheet ID from secrets."""
    return st.secrets.get('SPREADSHEET_ID', st.secrets.get('spreadsheet_id', ''))
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-load_sheet_to_dataframe"></a> `load_sheet_to_dataframe` — L80–L144

```python
def load_sheet_to_dataframe(sheet_name: str, handle_duplicates: bool = True) -> Optional[pd.DataFrame]:
    """
    Load a Google Sheet into a pandas DataFrame.
    
    Args:
        sheet_name: Name of the sheet to load
        handle_duplicates: Whether to handle duplicate column names
    
    Returns:
        DataFrame or None if loading fails
    """
    try:
        client = get_google_sheets_client()
        if client is None:
            logger.error(f"No Google Sheets client available for sheet '{sheet_name}'")
            return None
        
        spreadsheet_id = get_spreadsheet_id()
        if not spreadsheet_id:
            logger.error("No spreadsheet ID configured")
            return None
        
        logger.info(f"Opening spreadsheet {spreadsheet_id} for sheet '{sheet_name}'")
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        data = worksheet.get_all_values()
        
        if not data:
            logger.info(f"Sheet '{sheet_name}' has no data")
            return pd.DataFrame()
        
        logger.info(f"Sheet '{sheet_name}' has {len(data)} rows")
        
        # Handle duplicate column names
        headers = data[0]
        if handle_duplicates:
            seen = {}
            new_headers = []
            for h in headers:
                if h in seen:
                    seen[h] += 1
                    new_headers.append(f"{h}_{seen[h]}")
                else:
                    seen[h] = 0
                    new_headers.append(h)
            headers = new_headers
        
        df = pd.DataFrame(data[1:], columns=headers)
        
        # Convert numeric columns
        for col in df.columns:
            # Try to convert to numeric
            try:
                numeric_vals = pd.to_numeric(df[col], errors='coerce')
                if numeric_vals.notna().sum() > len(df) * 0.5:  # More than 50% numeric
                    df[col] = numeric_vals
            except:
                pass
        
        logger.info(f"Successfully created DataFrame with {len(df)} rows and {len(df.columns)} columns")
        return df
        
    except Exception as e:
        logger.error(f"Error loading sheet '{sheet_name}': {e}")
        return None
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-load_invoice_lines"></a> `load_invoice_lines` — L152–L189

```python
def load_invoice_lines() -> Optional[pd.DataFrame]:
    """Load Invoice Line Item data."""
    df = load_sheet_to_dataframe('Invoice Line Item')
    
    if df is None or df.empty:
        return None
    
    # Standardize column names
    col_mapping = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'customer' in col_lower and 'correct' in col_lower:
            col_mapping[col] = 'Customer'
        elif col_lower == 'customer' or 'customer name' in col_lower:
            if 'Customer' not in col_mapping.values():
                col_mapping[col] = 'Customer'
        elif 'item' in col_lower and 'name' not in col_lower:
            col_mapping[col] = 'Item'
        elif 'amount' in col_lower or 'line amount' in col_lower:
            col_mapping[col] = 'Amount'
        elif 'qty' in col_lower or 'quantity' in col_lower:
            col_mapping[col] = 'Quantity'
        elif 'date' in col_lower and ('invoice' in col_lower or 'tran' in col_lower):
            col_mapping[col] = 'Date'
        elif 'rep' in col_lower and 'master' in col_lower:
            col_mapping[col] = 'Rep'
        elif 'calyx' in col_lower and 'product type' in col_lower:
            col_mapping[col] = 'Product Type'
        elif 'product type' in col_lower and 'Product Type' not in col_mapping.values():
            col_mapping[col] = 'Product Type'
    
    df = df.rename(columns=col_mapping)
    
    # Clean Product Type
    if 'Product Type' in df.columns:
        df['Product Type'] = df['Product Type'].fillna('Unknown').replace('', 'Unknown')
    
    return df
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-load_sales_orders"></a> `load_sales_orders` — L193–L226

```python
def load_sales_orders() -> Optional[pd.DataFrame]:
    """Load Sales Orders Main data."""
    df = load_sheet_to_dataframe('_NS_SalesOrders_Data')
    
    if df is None or df.empty:
        # Try alternate name
        df = load_sheet_to_dataframe('Sales Order Line Item')
    
    if df is None or df.empty:
        return None
    
    # Standardize column names
    col_mapping = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'customer' in col_lower:
            if 'Customer' not in col_mapping.values():
                col_mapping[col] = 'Customer'
        elif 'rep' in col_lower:
            if 'Rep' not in col_mapping.values():
                col_mapping[col] = 'Rep'
        elif 'item' in col_lower:
            if 'Item' not in col_mapping.values():
                col_mapping[col] = 'Item'
        elif 'amount' in col_lower:
            if 'Amount' not in col_mapping.values():
                col_mapping[col] = 'Amount'
        elif 'status' in col_lower:
            if 'Status' not in col_mapping.values():
                col_mapping[col] = 'Status'
    
    df = df.rename(columns=col_mapping)
    
    return df
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-load_items"></a> `load_items` — L230–L275

```python
def load_items() -> Optional[pd.DataFrame]:
    """
    Load Raw_Items data with 'Calyx || Product Type' column.
    """
    df = load_sheet_to_dataframe('Raw_Items')
    
    if df is None or df.empty:
        return None
    
    # Find and standardize the Calyx Product Type column
    product_type_col = None
    for col in df.columns:
        col_lower = col.lower()
        if 'calyx' in col_lower and 'product type' in col_lower:
            product_type_col = col
            break
    
    if product_type_col:
        df['Calyx Product Type'] = df[product_type_col].fillna('Unknown').replace('', 'Unknown')
    
    # Find Stock Item column
    stock_item_col = None
    for col in df.columns:
        col_lower = col.lower().strip()
        if col_lower == 'stock item' or col_lower == 'stockitem' or col_lower == 'stock_item':
            stock_item_col = col
            break
    
    if stock_item_col:
        df['Stock Item'] = df[stock_item_col].fillna('').astype(str).str.strip()
    else:
        df['Stock Item'] = ''  # Default to blank if column not found
    
    # Also keep original column mapping
    col_mapping = {}
    for col in df.columns:
        col_lower = col.lower()
        if col_lower in ['item', 'item name', 'name', 'sku']:
            col_mapping[col] = 'Item'
        elif 'description' in col_lower:
            if 'Description' not in col_mapping.values():
                col_mapping[col] = 'Description'
    
    df = df.rename(columns=col_mapping)
    
    return df
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-load_stock_items"></a> `load_stock_items` — L279–L301

```python
def load_stock_items() -> Optional[pd.DataFrame]:
    """
    Load Raw_Items data filtered to only include Stock Items.
    Excludes items where Stock Item = 'No' or blank.
    
    Returns only items where Stock Item = 'Yes'
    """
    df = load_items()
    
    if df is None or df.empty:
        return df
    
    # Filter to only stock items (Yes)
    if 'Stock Item' in df.columns:
        # Keep only rows where Stock Item is 'Yes' (case insensitive)
        stock_item_series = df['Stock Item'].astype(str).str.strip().str.lower()
        df_filtered = df[stock_item_series == 'yes'].copy()
        
        logger.info(f"Filtered items: {len(df)} total -> {len(df_filtered)} stock items")
        return df_filtered
    
    # If no Stock Item column, return all items
    return df
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-load_customers"></a> `load_customers` — L305–L325

```python
def load_customers() -> Optional[pd.DataFrame]:
    """Load Customer List data."""
    df = load_sheet_to_dataframe('_NS_Customer_List')
    
    if df is None or df.empty:
        return None
    
    # Standardize column names
    col_mapping = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'company' in col_lower or 'customer' in col_lower:
            if 'Customer' not in col_mapping.values():
                col_mapping[col] = 'Customer'
        elif 'rep' in col_lower or 'salesperson' in col_lower:
            if 'Rep' not in col_mapping.values():
                col_mapping[col] = 'Rep'
    
    df = df.rename(columns=col_mapping)
    
    return df
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-load_deals"></a> `load_deals` — L329–L396

```python
def load_deals() -> Optional[pd.DataFrame]:
    """
    Load HubSpot Deals/Pipeline data.
    
    Handles case where first row is a title/info row like "HubSpot Import..."
    and actual headers are in row 2.
    """
    df = load_sheet_to_dataframe('Deals')
    
    if df is None or df.empty:
        # Try alternate names
        for sheet_name in ['All Reps All Pipelines', 'HubSpot Deals', 'Pipeline']:
            df = load_sheet_to_dataframe(sheet_name)
            if df is not None and not df.empty:
                break
    
    if df is None or df.empty:
        return None
    
    # Check if first column header looks like a title row (HubSpot Import, etc.)
    first_col = str(df.columns[0]).lower() if len(df.columns) > 0 else ''
    if 'hubspot' in first_col or 'import' in first_col or 'last updated' in first_col:
        # First row is a title - the actual headers are in the first data row
        # Use the first row as new headers
        if len(df) > 0:
            new_headers = df.iloc[0].astype(str).tolist()
            df = df.iloc[1:].reset_index(drop=True)
            df.columns = new_headers
            logger.info(f"Deals: Detected title row, using row 2 as headers: {new_headers[:5]}...")
    
    # Also check if columns are generic like '_1', '_2', etc.
    generic_cols = [c for c in df.columns if str(c).startswith('_') and str(c)[1:].isdigit()]
    if len(generic_cols) > len(df.columns) / 2:
        # More than half are generic - first row is likely actual headers
        if len(df) > 0:
            new_headers = df.iloc[0].astype(str).tolist()
            df = df.iloc[1:].reset_index(drop=True)
            df.columns = new_headers
            logger.info(f"Deals: Detected generic columns, using row 1 as headers: {new_headers[:5]}...")
    
    # Standardize column names
    col_mapping = {}
    for col in df.columns:
        col_lower = str(col).lower()
        if 'deal' in col_lower and 'name' in col_lower:
            col_mapping[col] = 'Deal Name'
        elif 'company' in col_lower or 'customer' in col_lower:
            if 'Company' not in col_mapping.values():
                col_mapping[col] = 'Company'
        elif col_lower == 'amount' or (('amount' in col_lower or 'value' in col_lower) and 'Amount' not in col_mapping.values()):
            col_mapping[col] = 'Amount'
        elif 'stage' in col_lower:
            if 'Stage' not in col_mapping.values():
                col_mapping[col] = 'Stage'
        elif 'close' in col_lower and 'date' in col_lower:
            col_mapping[col] = 'Close Date'
        elif 'product' in col_lower:
            if 'Product' not in col_mapping.values():
                col_mapping[col] = 'Product'
        elif col_lower == 'sku' or col_lower == 'item':
            col_mapping[col] = 'SKU'
    
    df = df.rename(columns=col_mapping)
    
    # Log the actual column names for debugging
    logger.info(f"Deals columns after processing: {list(df.columns)[:10]}...")
    
    return df
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-load_inventory"></a> `load_inventory` — L400–L407

```python
def load_inventory() -> Optional[pd.DataFrame]:
    """Load Raw_Inventory data."""
    df = load_sheet_to_dataframe('Raw_Inventory')
    
    if df is None or df.empty:
        return None
    
    return df
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-load_vendors"></a> `load_vendors` — L411–L418

```python
def load_vendors() -> Optional[pd.DataFrame]:
    """Load Raw_Vendors data."""
    df = load_sheet_to_dataframe('Raw_Vendors')
    
    if df is None or df.empty:
        return None
    
    return df
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-load_invoices"></a> `load_invoices` — L422–L429

```python
def load_invoices() -> Optional[pd.DataFrame]:
    """Load Invoices Main data."""
    df = load_sheet_to_dataframe('_NS_Invoices_Data')
    
    if df is None or df.empty:
        return None
    
    return df
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-load_so_lines"></a> `load_so_lines` — L433–L440

```python
def load_so_lines() -> Optional[pd.DataFrame]:
    """Load Sales Order Line Items."""
    df = load_sheet_to_dataframe('Sales Order Line Item')
    
    if df is None or df.empty:
        return None
    
    return df
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-load_all_sop_data"></a> `load_all_sop_data` — L448–L458

```python
def load_all_sop_data() -> Dict[str, pd.DataFrame]:
    """Load all S&OP data at once."""
    return {
        'invoice_lines': load_invoice_lines(),
        'sales_orders': load_sales_orders(),
        'items': load_items(),
        'customers': load_customers(),
        'deals': load_deals(),
        'inventory': load_inventory(),
        'vendors': load_vendors()
    }
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-get_unique_sales_reps"></a> `get_unique_sales_reps` — L465–L493

```python
def get_unique_sales_reps(sales_orders: pd.DataFrame = None, customers: pd.DataFrame = None) -> List[str]:
    """Get list of unique sales reps."""
    reps = set()
    
    if sales_orders is None:
        sales_orders = load_sales_orders()
    if customers is None:
        customers = load_customers()
    
    for df in [sales_orders, customers]:
        if df is not None and not df.empty:
            # Handle duplicate columns
            if df.columns.duplicated().any():
                df = df.loc[:, ~df.columns.duplicated()]
            
            # Find rep column
            rep_col = None
            for col in df.columns:
                if 'rep' in col.lower():
                    rep_col = col
                    break
            
            if rep_col:
                series = df.loc[:, rep_col]
                if isinstance(series, pd.DataFrame):
                    series = series.iloc[:, 0]
                reps.update(series.dropna().unique())
    
    return sorted([str(r).strip() for r in reps if r and str(r).strip()])
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-get_customers_for_rep"></a> `get_customers_for_rep` — L496–L533

```python
def get_customers_for_rep(rep: str = None) -> List[str]:
    """Get customers for a specific rep (or all if rep is None)."""
    sales_orders = load_sales_orders()
    
    if sales_orders is None or sales_orders.empty:
        return []
    
    # Handle duplicate columns
    if sales_orders.columns.duplicated().any():
        sales_orders = sales_orders.loc[:, ~sales_orders.columns.duplicated()]
    
    # Find rep and customer columns
    rep_col = None
    cust_col = None
    for col in sales_orders.columns:
        col_lower = col.lower()
        if rep_col is None and 'rep' in col_lower:
            rep_col = col
        if cust_col is None and 'customer' in col_lower:
            cust_col = col
    
    if cust_col is None:
        return []
    
    if rep and rep != "All" and rep_col:
        rep_series = sales_orders.loc[:, rep_col]
        if isinstance(rep_series, pd.DataFrame):
            rep_series = rep_series.iloc[:, 0]
        filtered = sales_orders[rep_series == rep]
    else:
        filtered = sales_orders
    
    cust_series = filtered.loc[:, cust_col]
    if isinstance(cust_series, pd.DataFrame):
        cust_series = cust_series.iloc[:, 0]
    
    customers = cust_series.dropna().unique()
    return sorted([str(c).strip() for c in customers if c and str(c).strip()])
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-get_skus_for_customer"></a> `get_skus_for_customer` — L536–L573

```python
def get_skus_for_customer(customer: str = None) -> List[str]:
    """Get SKUs/Items for a specific customer (or all if customer is None)."""
    invoice_lines = load_invoice_lines()
    
    if invoice_lines is None or invoice_lines.empty:
        return []
    
    # Handle duplicate columns
    if invoice_lines.columns.duplicated().any():
        invoice_lines = invoice_lines.loc[:, ~invoice_lines.columns.duplicated()]
    
    # Find customer and item columns
    cust_col = None
    item_col = None
    for col in invoice_lines.columns:
        col_lower = col.lower()
        if cust_col is None and 'customer' in col_lower:
            cust_col = col
        if item_col is None and col_lower in ['item', 'sku']:
            item_col = col
    
    if item_col is None:
        return []
    
    if customer and customer != "All" and cust_col:
        cust_series = invoice_lines.loc[:, cust_col]
        if isinstance(cust_series, pd.DataFrame):
            cust_series = cust_series.iloc[:, 0]
        filtered = invoice_lines[cust_series == customer]
    else:
        filtered = invoice_lines
    
    item_series = filtered.loc[:, item_col]
    if isinstance(item_series, pd.DataFrame):
        item_series = item_series.iloc[:, 0]
    
    items = item_series.dropna().unique()
    return sorted([str(i).strip() for i in items if i and str(i).strip()])
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-get_unique_product_types"></a> `get_unique_product_types` — L576–L608

```python
def get_unique_product_types(items: pd.DataFrame = None) -> List[str]:
    """Get unique product types from items."""
    if items is None:
        items = load_items()
    
    if items is None or items.empty:
        return []
    
    # Handle duplicate columns
    if items.columns.duplicated().any():
        items = items.loc[:, ~items.columns.duplicated()]
    
    if 'Calyx Product Type' in items.columns:
        col = 'Calyx Product Type'
    elif 'Product Type' in items.columns:
        col = 'Product Type'
    else:
        # Find any column with 'product type' in name
        col = None
        for c in items.columns:
            if 'product type' in c.lower():
                col = c
                break
        if col is None:
            return []
    
    # Get as series safely
    series = items.loc[:, col]
    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]
    
    types = series.dropna().unique().tolist()
    return sorted([str(t).strip() for t in types if t and str(t).strip() and str(t) != 'Unknown'])
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-get_unique_skus"></a> `get_unique_skus` — L611–L639

```python
def get_unique_skus(items: pd.DataFrame = None) -> List[str]:
    """Get unique SKUs/Items."""
    if items is None:
        items = load_items()
    
    if items is None or items.empty:
        return []
    
    # Handle duplicate columns
    if items.columns.duplicated().any():
        items = items.loc[:, ~items.columns.duplicated()]
    
    # Find item column
    item_col = None
    for col in items.columns:
        if col.lower() in ['item', 'sku', 'item name', 'name']:
            item_col = col
            break
    
    if item_col is None:
        return []
    
    # Get as series safely
    series = items.loc[:, item_col]
    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]
    
    skus = series.dropna().unique().tolist()
    return sorted([str(s).strip() for s in skus if s and str(s).strip()])
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-prepare_demand_history"></a> `prepare_demand_history` — L642–L702

```python
def prepare_demand_history(invoice_lines: pd.DataFrame = None, 
                           period: str = 'M',
                           freq: str = None) -> pd.DataFrame:
    """Prepare historical demand data aggregated by period."""
    # Handle freq as alias for period
    if freq is not None:
        period = freq
    
    # Map common frequency strings to pandas period strings
    freq_map = {
        'MS': 'M', 'ME': 'M', 'QS': 'Q', 'QE': 'Q', 
        'YS': 'Y', 'YE': 'Y', 'W': 'W', 'D': 'D',
        'M': 'M', 'Q': 'Q', 'Y': 'Y',
    }
    period = freq_map.get(period, 'M')
        
    if invoice_lines is None:
        invoice_lines = load_invoice_lines()
    
    if invoice_lines is None or invoice_lines.empty:
        return pd.DataFrame()
    
    df = invoice_lines.copy()
    
    # Handle duplicate columns
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]
    
    # Find date column
    date_col = None
    for col in df.columns:
        if 'date' in col.lower():
            date_col = col
            break
    
    if date_col is None:
        return pd.DataFrame()
    
    # Get date series safely
    date_series = df.loc[:, date_col]
    if isinstance(date_series, pd.DataFrame):
        date_series = date_series.iloc[:, 0]
    
    df['Date'] = pd.to_datetime(date_series, errors='coerce')
    df = df.dropna(subset=['Date'])
    df['Period'] = df['Date'].dt.to_period(period)
    
    # Aggregate
    agg_cols = {}
    if 'Amount' in df.columns:
        agg_cols['Revenue'] = ('Amount', 'sum')
    if 'Quantity' in df.columns:
        agg_cols['Units'] = ('Quantity', 'sum')
    
    if not agg_cols:
        return pd.DataFrame()
    
    grouped = df.groupby('Period').agg(**agg_cols).reset_index()
    grouped['Period'] = grouped['Period'].astype(str)
    
    return grouped
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-prepare_revenue_history"></a> `prepare_revenue_history` — L705–L777

```python
def prepare_revenue_history(invoice_lines: pd.DataFrame = None,
                            group_by: str = None,
                            freq: str = None,
                            period: str = 'M') -> pd.DataFrame:
    """Prepare revenue history, optionally grouped."""
    # Handle freq as alias for period
    if freq is not None:
        period = freq
    
    # Map common frequency strings to pandas period strings
    freq_map = {
        'MS': 'M', 'ME': 'M', 'QS': 'Q', 'QE': 'Q', 
        'YS': 'Y', 'YE': 'Y', 'W': 'W', 'D': 'D',
        'M': 'M', 'Q': 'Q', 'Y': 'Y',
    }
    period = freq_map.get(period, 'M')
        
    if invoice_lines is None:
        invoice_lines = load_invoice_lines()
    
    if invoice_lines is None or invoice_lines.empty:
        return pd.DataFrame()
    
    df = invoice_lines.copy()
    
    # Handle duplicate columns
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]
    
    # Find date column
    date_col = None
    for col in df.columns:
        if 'date' in col.lower():
            date_col = col
            break
    
    if date_col is None:
        return pd.DataFrame()
    
    # Get date series safely
    date_series = df.loc[:, date_col]
    if isinstance(date_series, pd.DataFrame):
        date_series = date_series.iloc[:, 0]
    
    df['Date'] = pd.to_datetime(date_series, errors='coerce')
    df = df.dropna(subset=['Date'])
    df['Month'] = df['Date'].dt.to_period(period)
    
    # Find amount column
    amt_col = None
    for col in df.columns:
        if 'amount' in col.lower():
            amt_col = col
            break
    
    if amt_col is None:
        return pd.DataFrame()
    
    # Get amount series safely
    amt_series = df.loc[:, amt_col]
    if isinstance(amt_series, pd.DataFrame):
        amt_series = amt_series.iloc[:, 0]
    df['Amount'] = pd.to_numeric(amt_series, errors='coerce')
    
    # Group by
    group_cols = ['Month']
    if group_by and group_by in df.columns:
        group_cols.append(group_by)
    
    grouped = df.groupby(group_cols)['Amount'].sum().reset_index()
    grouped.columns = group_cols + ['Revenue']
    grouped['Month'] = grouped['Month'].astype(str)
    return grouped
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-get_all_worksheet_names"></a> `get_all_worksheet_names` — L784–L800

```python
def get_all_worksheet_names() -> list:
    """Get all worksheet names from the spreadsheet for debugging."""
    try:
        client = get_google_sheets_client()
        if client is None:
            return []
        
        spreadsheet_id = get_spreadsheet_id()
        if not spreadsheet_id:
            return []
        
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheets = spreadsheet.worksheets()
        return [ws.title for ws in worksheets]
    except Exception as e:
        logger.error(f"Error getting worksheet names: {e}")
        return []
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-parse_revenue_forecast"></a> `parse_revenue_forecast` — L857–L881

```python
def parse_revenue_forecast(revenue_forecast_df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse the Revenue Forecast sheet to long format (Category, Period, Forecast_Revenue).
    
    Supports two formats:
    1. Wide format: Category + monthly columns (January, February, etc.)
    2. Long format with Month/Year columns: Category, Month, Year, Amount
    """
    if revenue_forecast_df is None or revenue_forecast_df.empty:
        return pd.DataFrame()
    
    df = revenue_forecast_df.copy()
    
    # Handle duplicate columns
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]
    
    # Check if this is the new long format with Month and Year columns
    has_month_col = any('month' in str(col).lower() for col in df.columns)
    has_year_col = any('year' in str(col).lower() for col in df.columns)
    
    if has_month_col and has_year_col:
        return parse_revenue_forecast_long_format(df)
    else:
        return parse_revenue_forecast_wide_format(df)
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-parse_revenue_forecast_long_format"></a> `parse_revenue_forecast_long_format` — L884–L997

```python
def parse_revenue_forecast_long_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse Revenue Forecast in long format with Month and Year columns.
    Expected columns: Category, Month, Year, Amount/Revenue
    """
    # Find columns
    cat_col = None
    month_col = None
    year_col = None
    amount_col = None
    
    for col in df.columns:
        col_lower = str(col).lower().strip()
        
        if cat_col is None and ('category' in col_lower or 'product' in col_lower or col_lower == 'type'):
            cat_col = col
        if month_col is None and col_lower == 'month':
            month_col = col
        if year_col is None and col_lower == 'year':
            year_col = col
        if amount_col is None and ('amount' in col_lower or 'revenue' in col_lower or 'forecast' in col_lower):
            amount_col = col
    
    # If no category column found, use first column
    if cat_col is None:
        cat_col = df.columns[0]
    
    # If no amount column found, try to find any numeric column
    if amount_col is None:
        for col in df.columns:
            if col not in [cat_col, month_col, year_col]:
                # Check if column has numeric data
                try:
                    sample = df[col].iloc[0] if len(df) > 0 else None
                    if sample is not None:
                        if isinstance(sample, (int, float)):
                            amount_col = col
                            break
                        elif isinstance(sample, str) and sample.replace('$', '').replace(',', '').replace('.', '').isdigit():
                            amount_col = col
                            break
                except:
                    pass
    
    if month_col is None or year_col is None:
        return pd.DataFrame()
    
    # Month name to number mapping
    month_to_num = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12,
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
        'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9,
        'oct': 10, 'nov': 11, 'dec': 12
    }
    
    result_rows = []
    
    for _, row in df.iterrows():
        category = row[cat_col]
        if pd.isna(category) or str(category).strip() == '':
            continue
        
        # Get month
        month_val = row[month_col]
        if pd.isna(month_val):
            continue
        
        # Convert month to number
        if isinstance(month_val, str):
            month_num = month_to_num.get(month_val.lower().strip())
            if month_num is None:
                # Try to parse as number
                try:
                    month_num = int(month_val)
                except:
                    continue
        else:
            try:
                month_num = int(month_val)
            except:
                continue
        
        # Get year
        year_val = row[year_col]
        if pd.isna(year_val):
            continue
        try:
            year = int(year_val)
        except:
            continue
        
        # Get amount
        if amount_col:
            value = row[amount_col]
            if isinstance(value, str):
                value = value.replace('$', '').replace(',', '').strip()
            try:
                forecast_revenue = float(value)
            except:
                forecast_revenue = 0
        else:
            forecast_revenue = 0
        
        if forecast_revenue > 0:
            period = f"{year}-{month_num:02d}"
            result_rows.append({
                'Category': str(category).strip(),
                'Period': period,
                'Forecast_Revenue': forecast_revenue
            })
    
    return pd.DataFrame(result_rows)
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-parse_revenue_forecast_wide_format"></a> `parse_revenue_forecast_wide_format` — L1000–L1076

```python
def parse_revenue_forecast_wide_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse Revenue Forecast in wide format (Category + monthly columns).
    Handles columns like "January", "January 2026", "Jan 2026", etc.
    """
    import re
    
    # Find the category column
    cat_col = None
    for col in df.columns:
        col_lower = str(col).lower()
        if 'category' in col_lower or 'product' in col_lower or col_lower == 'type':
            cat_col = col
            break
    
    if cat_col is None:
        cat_col = df.columns[0]
    
    # Month name mapping
    month_names = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12,
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
        'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9,
        'oct': 10, 'nov': 11, 'dec': 12
    }
    
    # Default forecast year
    current_date = datetime.now()
    default_year = current_date.year + 1 if current_date.month >= 6 else current_date.year
    
    result_rows = []
    
    for _, row in df.iterrows():
        category = row[cat_col]
        if pd.isna(category) or str(category).strip() == '':
            continue
        
        for col in df.columns:
            if col == cat_col:
                continue
            
            col_str = str(col).lower().strip()
            
            # Try to find month name within column string
            month_num = None
            for month_name, month_val in month_names.items():
                if month_name in col_str:
                    month_num = month_val
                    break
            
            if month_num is None:
                continue  # Not a month column
            
            # Try to extract year from column (e.g., "January 2026")
            year_match = re.search(r'20\d{2}', str(col))
            year = int(year_match.group()) if year_match else default_year
            
            value = row[col]
            if isinstance(value, str):
                value = value.replace('$', '').replace(',', '').strip()
            
            try:
                forecast_revenue = float(value)
            except:
                forecast_revenue = 0
            
            if forecast_revenue > 0:
                period = f"{year}-{month_num:02d}"
                result_rows.append({
                    'Category': str(category).strip(),
                    'Period': period,
                    'Forecast_Revenue': forecast_revenue
                })
    
    return pd.DataFrame(result_rows)
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-calculate_item_asp_rolling12"></a> `calculate_item_asp_rolling12` — L1428–L1532

```python
def calculate_item_asp_rolling12(invoice_lines: pd.DataFrame = None) -> pd.DataFrame:
    """
    Calculate historical Average Selling Price (ASP) by item.
    Uses Invoice Lines data for actual sales prices.
    Rolling 12 months only.
    
    EXCLUDES lines with $0 amounts to avoid skewing ASP calculations.
    
    Returns DataFrame with columns: Item, ASP, Total_Units, Total_Revenue
    """
    if invoice_lines is None:
        invoice_lines = load_invoice_lines()
    
    if invoice_lines is None or invoice_lines.empty:
        return pd.DataFrame()
    
    df = invoice_lines.copy()
    
    # Handle duplicate columns
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]
    
    # Find required columns
    item_col = None
    amount_col = None
    qty_col = None
    date_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        
        if item_col is None and col_lower in ['item', 'sku', 'item name']:
            item_col = col
        if amount_col is None and 'amount' in col_lower:
            amount_col = col
        if qty_col is None and ('qty' in col_lower or 'quantity' in col_lower):
            qty_col = col
        if date_col is None and 'date' in col_lower:
            date_col = col
    
    if item_col is None or amount_col is None:
        return pd.DataFrame()
    
    # Get series safely
    def safe_get_series(dataframe, column):
        if column not in dataframe.columns:
            return None
        result = dataframe.loc[:, column]
        if isinstance(result, pd.DataFrame):
            return result.iloc[:, 0]
        return result
    
    item_series = safe_get_series(df, item_col)
    amt_series = safe_get_series(df, amount_col)
    qty_series = safe_get_series(df, qty_col) if qty_col else None
    date_series = safe_get_series(df, date_col) if date_col else None
    
    if item_series is None or amt_series is None:
        return pd.DataFrame()
    
    temp_df = pd.DataFrame({
        'Item': item_series,
        'Amount': pd.to_numeric(amt_series, errors='coerce').fillna(0)
    })
    
    if qty_series is not None:
        temp_df['Quantity'] = pd.to_numeric(qty_series, errors='coerce').fillna(0)
    else:
        temp_df['Quantity'] = 1
    
    # Filter to rolling 12 months
    if date_series is not None:
        temp_df['Date'] = pd.to_datetime(date_series, errors='coerce')
        cutoff_date = datetime.now() - timedelta(days=365)
        temp_df = temp_df[temp_df['Date'] >= cutoff_date]
    
    if temp_df.empty:
        return pd.DataFrame()
    
    # CRITICAL: Exclude $0 lines from ASP calculation
    # These are often samples, returns, or adjustments that would skew ASP
    temp_df = temp_df[temp_df['Amount'] > 0]
    
    # Also exclude lines with 0 quantity
    temp_df = temp_df[temp_df['Quantity'] > 0]
    
    if temp_df.empty:
        return pd.DataFrame()
    
    # Aggregate by item
    by_item = temp_df.groupby('Item').agg({
        'Amount': 'sum',
        'Quantity': 'sum'
    }).reset_index()
    
    by_item.columns = ['Item', 'Total_Revenue', 'Total_Units']
    
    # Calculate ASP (avoid division by zero)
    by_item['ASP'] = np.where(
        by_item['Total_Units'] > 0,
        by_item['Total_Revenue'] / by_item['Total_Units'],
        0
    )
    
    return by_item
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-allocate_topdown_forecast"></a> `allocate_topdown_forecast` — L1535–L1666

```python
def allocate_topdown_forecast(revenue_forecast: pd.DataFrame = None,
                              item_mix: pd.DataFrame = None,
                              item_asp: pd.DataFrame = None) -> pd.DataFrame:
    """
    Top-down allocation of category-level revenue forecast to item level.
    
    Logic:
    1. Take category revenue forecast
    2. Apply item unit mix % to get item's share of category units
    3. But we need revenue first - so: Category Revenue × Item Mix % = Item Revenue
    4. Item Revenue ÷ Item ASP = Item Units
    
    Returns DataFrame with: Item, Category, Period, Forecast_Revenue, Forecast_Units, Mix_Pct, ASP
    """
    if revenue_forecast is None or revenue_forecast.empty:
        return pd.DataFrame()
    if item_mix is None or item_mix.empty:
        return pd.DataFrame()
    
    result_rows = []
    
    # Get available categories in item_mix for matching
    available_categories = item_mix['Category'].unique().tolist() if 'Category' in item_mix.columns else []
    
    for _, forecast_row in revenue_forecast.iterrows():
        try:
            category = str(forecast_row.get('Category', '')).strip()
            period = str(forecast_row.get('Period', ''))
            
            # SAFE: Convert revenue to float
            cat_forecast_revenue_raw = forecast_row.get('Forecast_Revenue', 0)
            try:
                if pd.isna(cat_forecast_revenue_raw):
                    cat_forecast_revenue = 0.0
                elif isinstance(cat_forecast_revenue_raw, str):
                    cat_forecast_revenue = float(cat_forecast_revenue_raw.replace('$', '').replace(',', '').strip() or 0)
                else:
                    cat_forecast_revenue = float(cat_forecast_revenue_raw)
            except (ValueError, TypeError):
                cat_forecast_revenue = 0.0
            
            if cat_forecast_revenue <= 0:
                continue
            
            # Try to find matching category in item_mix
            cat_items = item_mix[item_mix['Category'] == category].copy()
            
            # If no exact match, try case-insensitive
            if cat_items.empty:
                category_lower = category.lower()
                for avail_cat in available_categories:
                    if str(avail_cat).lower() == category_lower:
                        cat_items = item_mix[item_mix['Category'] == avail_cat].copy()
                        break
            
            # If still no match, try partial match
            if cat_items.empty:
                for avail_cat in available_categories:
                    if category_lower in str(avail_cat).lower() or str(avail_cat).lower() in category_lower:
                        cat_items = item_mix[item_mix['Category'] == avail_cat].copy()
                        break
            
            if cat_items.empty:
                # No historical data - keep at category level
                result_rows.append({
                    'Item': f'{category} (Unallocated)',
                    'Category': category,
                    'Period': period,
                    'Forecast_Revenue': float(cat_forecast_revenue),
                    'Forecast_Units': 0.0,
                    'Mix_Pct': 100.0,
                    'ASP': 0.0
                })
                continue
            
            # Normalize mix percentages to sum to 100%
            # SAFE: Ensure Mix_Pct is numeric
            cat_items['Mix_Pct'] = pd.to_numeric(cat_items['Mix_Pct'], errors='coerce').fillna(0)
            total_mix = cat_items['Mix_Pct'].sum()
            if total_mix > 0:
                cat_items['Mix_Pct_Normalized'] = cat_items['Mix_Pct'] / total_mix * 100
            else:
                cat_items['Mix_Pct_Normalized'] = 100 / len(cat_items)
            
            # Allocate to each item
            for _, item_row in cat_items.iterrows():
                try:
                    item_name = str(item_row.get('Item', '')).strip()
                    
                    # SAFE: Get mix percentage as float
                    mix_pct_raw = item_row.get('Mix_Pct_Normalized', 0)
                    try:
                        mix_pct = float(mix_pct_raw) / 100.0 if pd.notna(mix_pct_raw) else 0
                    except (ValueError, TypeError):
                        mix_pct = 0
                    
                    # Item's share of category revenue (all floats)
                    item_forecast_revenue = float(cat_forecast_revenue) * float(mix_pct)
                    
                    # Get ASP for this item
                    asp = 0.0
                    forecast_units = 0.0
                    
                    if item_asp is not None and not item_asp.empty:
                        item_asp_row = item_asp[item_asp['Item'] == item_name]
                        if not item_asp_row.empty:
                            asp_raw = item_asp_row['ASP'].iloc[0]
                            try:
                                asp = float(asp_raw) if pd.notna(asp_raw) else 0.0
                            except (ValueError, TypeError):
                                asp = 0.0
                            if asp > 0:
                                forecast_units = float(item_forecast_revenue) / float(asp)
                    
                    result_rows.append({
                        'Item': item_name,
                        'Category': category,
                        'Period': period,
                        'Forecast_Revenue': round(float(item_forecast_revenue), 2),
                        'Forecast_Units': round(float(forecast_units), 0),
                        'Mix_Pct': round(float(mix_pct_raw) if pd.notna(mix_pct_raw) else 0, 2),
                        'ASP': round(float(asp), 2)
                    })
                except Exception as e:
                    logger.warning(f"Error allocating item {item_row.get('Item', 'unknown')}: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Error processing forecast row: {e}")
            continue
    
    return pd.DataFrame(result_rows)
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-get_revenue_forecast_by_period"></a> `get_revenue_forecast_by_period` — L1722–L1798

```python
def get_revenue_forecast_by_period(category: str = None) -> pd.DataFrame:
    """
    Get Revenue Forecast aggregated by period for charting.
    Optionally filter by category.
    
    Falls back to category-level data if item-level allocation fails.
    
    Returns DataFrame with Period and Forecast_Revenue columns.
    """
    # First try to get item-level forecast
    item_forecast = get_topdown_item_forecast()
    
    # If item forecast is empty, fall back to parsed category-level forecast
    if item_forecast.empty:
        # Load and parse the raw forecast
        revenue_forecast_raw = load_revenue_forecast()
        if revenue_forecast_raw is None or revenue_forecast_raw.empty:
            return pd.DataFrame()
        
        parsed_forecast = parse_revenue_forecast(revenue_forecast_raw)
        if parsed_forecast.empty:
            return pd.DataFrame()
        
        # Filter by category if specified
        if category and category != 'All':
            # Try exact match first
            filtered = parsed_forecast[parsed_forecast['Category'] == category]
            
            # If no exact match, try case-insensitive
            if filtered.empty:
                category_lower = category.lower().strip()
                filtered = parsed_forecast[parsed_forecast['Category'].str.lower().str.strip() == category_lower]
            
            # If still no match, try contains
            if filtered.empty:
                filtered = parsed_forecast[parsed_forecast['Category'].str.lower().str.contains(category_lower, na=False)]
            
            parsed_forecast = filtered
        
        if parsed_forecast.empty:
            return pd.DataFrame()
        
        # Aggregate by period
        by_period = parsed_forecast.groupby('Period')['Forecast_Revenue'].sum().reset_index()
        by_period = by_period.sort_values('Period')
        
        return by_period
    
    # If we have item-level forecast, use it
    # Filter by category if specified (with fuzzy matching)
    if category and category != 'All':
        # Try exact match first
        filtered = item_forecast[item_forecast['Category'] == category]
        
        # If no exact match, try case-insensitive
        if filtered.empty:
            category_lower = category.lower().strip()
            filtered = item_forecast[item_forecast['Category'].str.lower().str.strip() == category_lower]
        
        # If still no match, try contains
        if filtered.empty:
            filtered = item_forecast[item_forecast['Category'].str.lower().str.contains(category_lower, na=False)]
        
        item_forecast = filtered
    
    if item_forecast.empty:
        return pd.DataFrame()
    
    # Aggregate by period
    by_period = item_forecast.groupby('Period').agg({
        'Forecast_Revenue': 'sum',
        'Forecast_Units': 'sum'
    }).reset_index()
    
    by_period = by_period.sort_values('Period')
    
    return by_period
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-get_pipeline_by_period"></a> `get_pipeline_by_period` — L1801–L1900

```python
def get_pipeline_by_period(deals: pd.DataFrame = None,
                           period: str = 'M',
                           freq: str = None) -> pd.DataFrame:
    """
    Get pipeline/deals aggregated by expected close period.
    
    Args:
        deals: Deals DataFrame (optional, will load if not provided)
        period: Period frequency ('M' for monthly, 'Q' for quarterly, etc.)
        freq: Alias for period (for backwards compatibility)
    """
    # Handle freq as alias for period
    if freq is not None:
        period = freq
    
    # Map common frequency strings to pandas period strings
    freq_map = {
        'MS': 'M',   # Month Start -> Month
        'ME': 'M',   # Month End -> Month
        'QS': 'Q',   # Quarter Start -> Quarter
        'QE': 'Q',   # Quarter End -> Quarter
        'YS': 'Y',   # Year Start -> Year
        'YE': 'Y',   # Year End -> Year
        'W': 'W',
        'D': 'D',
        'M': 'M',
        'Q': 'Q',
        'Y': 'Y',
    }
    period = freq_map.get(period, 'M')  # Default to 'M' if not found
    
    if deals is None:
        deals = load_deals()
    
    if deals is None or deals.empty:
        return pd.DataFrame()
    
    df = deals.copy()
    
    # Handle duplicate columns
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]
    
    # Find close date column
    close_date_col = None
    for col in df.columns:
        col_lower = col.lower()
        if 'close' in col_lower and 'date' in col_lower:
            close_date_col = col
            break
        elif col_lower == 'close date':
            close_date_col = col
            break
    
    if close_date_col is None:
        # Try any date column
        for col in df.columns:
            if 'date' in col.lower():
                close_date_col = col
                break
    
    if close_date_col is None:
        return pd.DataFrame()
    
    # Get date series safely
    date_series = df.loc[:, close_date_col]
    if isinstance(date_series, pd.DataFrame):
        date_series = date_series.iloc[:, 0]
    
    df['Close Date'] = pd.to_datetime(date_series, errors='coerce')
    df = df.dropna(subset=['Close Date'])
    
    if df.empty:
        return pd.DataFrame()
    
    df['Period'] = df['Close Date'].dt.to_period(period)
    
    # Find amount column
    amt_col = None
    for col in df.columns:
        col_lower = col.lower()
        if 'amount' in col_lower or 'value' in col_lower:
            amt_col = col
            break
    
    if amt_col is None:
        return pd.DataFrame()
    
    # Get amount series safely
    amt_series = df.loc[:, amt_col]
    if isinstance(amt_series, pd.DataFrame):
        amt_series = amt_series.iloc[:, 0]
    
    df['Amount'] = pd.to_numeric(amt_series, errors='coerce')
    
    grouped = df.groupby('Period')['Amount'].sum().reset_index()
    grouped.columns = ['Period', 'Pipeline Value']
    grouped['Period'] = grouped['Period'].astype(str)
    
    return grouped
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-calculate_lead_times"></a> `calculate_lead_times` — L1903–L1988

```python
def calculate_lead_times(items: pd.DataFrame = None, 
                         vendors: pd.DataFrame = None) -> pd.DataFrame:
    """
    Calculate lead times for items based on vendor data.
    
    Args:
        items: Items dataframe
        vendors: Vendors dataframe
    
    Returns:
        DataFrame with item lead time information
    """
    if items is None:
        items = load_items()
    if vendors is None:
        vendors = load_vendors()
    
    if items is None or items.empty:
        return pd.DataFrame()
    
    df = items.copy()
    
    # Look for lead time column in items
    lead_time_col = None
    for col in df.columns:
        col_lower = col.lower()
        if 'lead' in col_lower and 'time' in col_lower:
            lead_time_col = col
            break
        elif 'leadtime' in col_lower:
            lead_time_col = col
            break
    
    # If no lead time column, try to get from vendors
    if lead_time_col is None and vendors is not None and not vendors.empty:
        # Find vendor column in items
        vendor_col = None
        for col in df.columns:
            col_lower = col.lower()
            if 'vendor' in col_lower or 'supplier' in col_lower:
                vendor_col = col
                break
        
        if vendor_col:
            # Find lead time in vendors
            vendor_lead_col = None
            for col in vendors.columns:
                col_lower = col.lower()
                if 'lead' in col_lower and 'time' in col_lower:
                    vendor_lead_col = col
                    break
            
            if vendor_lead_col:
                # Find vendor name column
                vendor_name_col = None
                for col in vendors.columns:
                    col_lower = col.lower()
                    if col_lower in ['vendor', 'name', 'vendor name', 'supplier']:
                        vendor_name_col = col
                        break
                
                if vendor_name_col:
                    vendor_lead_times = vendors.set_index(vendor_name_col)[vendor_lead_col].to_dict()
                    df['Lead Time'] = df[vendor_col].map(vendor_lead_times)
    
    # If we found a lead time column, standardize it
    if lead_time_col:
        df['Lead Time'] = pd.to_numeric(df[lead_time_col], errors='coerce').fillna(0)
    elif 'Lead Time' not in df.columns:
        # Default lead time
        df['Lead Time'] = 30  # Default 30 days
    
    # Create summary
    result_cols = ['Item'] if 'Item' in df.columns else [df.columns[0]]
    if 'Calyx Product Type' in df.columns:
        result_cols.append('Calyx Product Type')
    elif 'Product Type' in df.columns:
        result_cols.append('Product Type')
    result_cols.append('Lead Time')
    
    # Add vendor if available
    vendor_col = next((c for c in df.columns if 'vendor' in c.lower()), None)
    if vendor_col:
        result_cols.insert(-1, vendor_col)
    
    return df[[c for c in result_cols if c in df.columns]]
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-safe_get_series"></a> `safe_get_series` — L1214–L1220

```python
def safe_get_series(dataframe, column):
        if column not in dataframe.columns:
            return None
        result = dataframe.loc[:, column]
        if isinstance(result, pd.DataFrame):
            return result.iloc[:, 0]
        return result
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-safe_get_series"></a> `safe_get_series` — L1352–L1358

```python
def safe_get_series(dataframe, column):
        if column not in dataframe.columns:
            return None
        result = dataframe.loc[:, column]
        if isinstance(result, pd.DataFrame):
            return result.iloc[:, 0]
        return result
```

### <a id="calyx-sop-dashboard-v2-src-sop_data_loader-py-safe_get_series"></a> `safe_get_series` — L1472–L1478

```python
def safe_get_series(dataframe, column):
        if column not in dataframe.columns:
            return None
        result = dataframe.loc[:, column]
        if isinstance(result, pd.DataFrame):
            return result.iloc[:, 0]
        return result
```

## calyx-sop-dashboard-v2/src/utils.py

### <a id="calyx-sop-dashboard-v2-src-utils-py-setup_logging"></a> `setup_logging` — L17–L44

```python
def setup_logging(log_level: int = logging.INFO) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (default: INFO)
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
```

### <a id="calyx-sop-dashboard-v2-src-utils-py-export_dataframe"></a> `export_dataframe` — L47–L58

```python
def export_dataframe(df: pd.DataFrame, filename: Optional[str] = None) -> str:
    """
    Export DataFrame to CSV string.
    
    Args:
        df: DataFrame to export
        filename: Optional filename (not used in return, for reference)
        
    Returns:
        CSV string
    """
    return df.to_csv(index=False)
```

### <a id="calyx-sop-dashboard-v2-src-utils-py-export_to_excel"></a> `export_to_excel` — L61–L74

```python
def export_to_excel(df: pd.DataFrame) -> bytes:
    """
    Export DataFrame to Excel bytes.
    
    Args:
        df: DataFrame to export
        
    Returns:
        Excel file as bytes
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='NC Data')
    return output.getvalue()
```

### <a id="calyx-sop-dashboard-v2-src-utils-py-format_currency"></a> `format_currency` — L77–L89

```python
def format_currency(value: float) -> str:
    """
    Format a number as currency.
    
    Args:
        value: Numeric value
        
    Returns:
        Formatted currency string
    """
    if pd.isna(value):
        return "$0.00"
    return f"${value:,.2f}"
```

### <a id="calyx-sop-dashboard-v2-src-utils-py-format_number"></a> `format_number` — L92–L107

```python
def format_number(value: float, decimals: int = 0) -> str:
    """
    Format a number with thousands separator.
    
    Args:
        value: Numeric value
        decimals: Number of decimal places
        
    Returns:
        Formatted number string
    """
    if pd.isna(value):
        return "0"
    if decimals == 0:
        return f"{value:,.0f}"
    return f"{value:,.{decimals}f}"
```

### <a id="calyx-sop-dashboard-v2-src-utils-py-format_percentage"></a> `format_percentage` — L110–L123

```python
def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format a number as percentage.
    
    Args:
        value: Numeric value (as decimal, e.g., 0.15 for 15%)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    if pd.isna(value):
        return "0%"
    return f"{value * 100:.{decimals}f}%"
```

### <a id="calyx-sop-dashboard-v2-src-utils-py-safe_divide"></a> `safe_divide` — L126–L143

```python
def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero.
    
    Args:
        numerator: Top number
        denominator: Bottom number
        default: Value to return if division fails
        
    Returns:
        Division result or default
    """
    try:
        if denominator == 0 or pd.isna(denominator):
            return default
        return numerator / denominator
    except:
        return default
```

### <a id="calyx-sop-dashboard-v2-src-utils-py-get_date_range_string"></a> `get_date_range_string` — L146–L157

```python
def get_date_range_string(start_date: datetime, end_date: datetime) -> str:
    """
    Create a formatted date range string.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        Formatted date range string
    """
    return f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"
```

### <a id="calyx-sop-dashboard-v2-src-utils-py-create_metric_card_html"></a> `create_metric_card_html` — L160–L196

```python
def create_metric_card_html(
    title: str,
    value: str,
    subtitle: Optional[str] = None,
    color: str = "#3498db",
    icon: Optional[str] = None
) -> str:
    """
    Create HTML for a styled metric card.
    
    Args:
        title: Card title
        value: Main value to display
        subtitle: Optional subtitle
        color: Accent color
        icon: Optional emoji icon
        
    Returns:
        HTML string for the card
    """
    icon_html = f'<span style="font-size: 2rem;">{icon}</span>' if icon else ''
    subtitle_html = f'<p style="margin: 0; color: #888; font-size: 0.8rem;">{subtitle}</p>' if subtitle else ''
    
    return f"""
    <div style="
        background: linear-gradient(135deg, {color}11, {color}22);
        border-radius: 10px;
        padding: 1.5rem;
        border-left: 4px solid {color};
        text-align: center;
    ">
        {icon_html}
        <h2 style="margin: 0.5rem 0; color: #333;">{value}</h2>
        <p style="margin: 0; color: #666; font-weight: 500;">{title}</p>
        {subtitle_html}
    </div>
    """
```

### <a id="calyx-sop-dashboard-v2-src-utils-py-validate_dataframe"></a> `validate_dataframe` — L199–L214

```python
def validate_dataframe(df: pd.DataFrame, required_columns: list) -> tuple:
    """
    Validate that a DataFrame has required columns.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        
    Returns:
        Tuple of (is_valid, missing_columns)
    """
    if df is None or df.empty:
        return False, required_columns
    
    missing = [col for col in required_columns if col not in df.columns]
    return len(missing) == 0, missing
```

### <a id="calyx-sop-dashboard-v2-src-utils-py-clean_string_column"></a> `clean_string_column` — L217–L227

```python
def clean_string_column(series: pd.Series) -> pd.Series:
    """
    Clean a string column by stripping whitespace and handling nulls.
    
    Args:
        series: Pandas Series to clean
        
    Returns:
        Cleaned Series
    """
    return series.astype(str).str.strip().replace(['nan', 'None', ''], pd.NA)
```

### <a id="calyx-sop-dashboard-v2-src-utils-py-calculate_growth_rate"></a> `calculate_growth_rate` — L230–L243

```python
def calculate_growth_rate(current: float, previous: float) -> Optional[float]:
    """
    Calculate growth rate between two values.
    
    Args:
        current: Current period value
        previous: Previous period value
        
    Returns:
        Growth rate as decimal or None if calculation fails
    """
    if previous == 0 or pd.isna(previous) or pd.isna(current):
        return None
    return (current - previous) / previous
```

### <a id="calyx-sop-dashboard-v2-src-utils-py-get_color_scale"></a> `get_color_scale` — L246–L274

```python
def get_color_scale(value: float, min_val: float = 0, max_val: float = 100) -> str:
    """
    Get a color from a red-yellow-green scale based on value.
    
    Args:
        value: Value to map to color
        min_val: Minimum value (maps to red)
        max_val: Maximum value (maps to green)
        
    Returns:
        Hex color string
    """
    # Normalize value to 0-1 range
    normalized = (value - min_val) / (max_val - min_val) if max_val > min_val else 0.5
    normalized = max(0, min(1, normalized))  # Clamp to [0, 1]
    
    # Interpolate color
    if normalized < 0.5:
        # Red to Yellow
        r = 255
        g = int(255 * normalized * 2)
        b = 0
    else:
        # Yellow to Green
        r = int(255 * (1 - (normalized - 0.5) * 2))
        g = 255
        b = 0
    
    return f"#{r:02x}{g:02x}{b:02x}"
```

### <a id="calyx-sop-dashboard-v2-src-utils-py-truncate_string"></a> `truncate_string` — L277–L291

```python
def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.
    
    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
```

### <a id="calyx-sop-dashboard-v2-src-utils-py-__init__"></a> `__init__` — L297–L300

```python
def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
```

### <a id="calyx-sop-dashboard-v2-src-utils-py-__enter__"></a> `__enter__` — L302–L304

```python
def __enter__(self):
        self.start_time = datetime.now()
        return self
```

### <a id="calyx-sop-dashboard-v2-src-utils-py-__exit__"></a> `__exit__` — L306–L309

```python
def __exit__(self, *args):
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        logging.info(f"{self.name} completed in {duration:.2f} seconds")
```

### <a id="calyx-sop-dashboard-v2-src-utils-py-elapsed"></a> `elapsed` — L312–L315

```python
def elapsed(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
```

## calyx-sop-dashboard-v2/src/yearly_planning_2026.py

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-fig_to_base64"></a> `fig_to_base64` — L51–L61

```python
def fig_to_base64(fig, width=700, height=350):
    """Convert a plotly figure to base64 PNG for embedding in HTML"""
    if not KALEIDO_AVAILABLE:
        return None
    try:
        img_bytes = fig.to_image(format="png", width=width, height=height, scale=2)
        return base64.b64encode(img_bytes).decode()
    except Exception as e:
        # Log the error for debugging
        print(f"Chart export error: {e}")
        return None
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-fig_to_html_embed"></a> `fig_to_html_embed` — L64–L74

```python
def fig_to_html_embed(fig, height=400):
    """Convert a plotly figure to embedded HTML (fallback when kaleido unavailable)"""
    try:
        return fig.to_html(
            include_plotlyjs='cdn',
            full_html=False,
            config={'displayModeBar': False, 'staticPlot': True},
            default_height=height
        )
    except Exception as e:
        return None
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-create_monthly_revenue_chart"></a> `create_monthly_revenue_chart` — L77–L122

```python
def create_monthly_revenue_chart(customer_invoices):
    """Create monthly revenue bar chart for PDF export"""
    if customer_invoices.empty or 'Date' not in customer_invoices.columns:
        return None
    
    invoices = customer_invoices.copy()
    invoices['Year'] = invoices['Date'].dt.year
    current_year = datetime.now().year
    recent = invoices[invoices['Year'] >= current_year - 1].copy()
    
    if recent.empty or len(recent) < 2:
        return None
    
    recent['Month'] = recent['Date'].dt.to_period('M').astype(str)
    monthly = recent.groupby('Month')['Amount'].sum().reset_index()
    
    fig = go.Figure(data=[
        go.Bar(
            x=monthly['Month'],
            y=monthly['Amount'],
            marker=dict(color='#3b82f6'),
            text=[f'${x:,.0f}' for x in monthly['Amount']],
            textposition='outside',
            textfont=dict(size=10),
            cliponaxis=False
        )
    ])
    
    # Calculate y-axis max to give room for labels
    max_val = monthly['Amount'].max()
    y_max = max_val * 1.15  # Add 15% headroom
    
    fig.update_layout(
        title=dict(text='Monthly Purchase Trend', font=dict(size=16, color='#1e293b')),
        xaxis_title='',
        yaxis_title='Purchases',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#1e293b', size=11),
        xaxis=dict(tickangle=-45, gridcolor='#e2e8f0'),
        yaxis=dict(gridcolor='#e2e8f0', tickformat='$,.0f', range=[0, y_max]),
        margin=dict(t=60, b=80, l=80, r=40),
        showlegend=False
    )
    
    return fig
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-create_order_type_chart"></a> `create_order_type_chart` — L177–L217

```python
def create_order_type_chart(customer_orders):
    """Create order type mix pie chart for PDF export"""
    if customer_orders.empty or 'Order Type' not in customer_orders.columns:
        return None
    
    valid = customer_orders[
        (customer_orders['Order Type'].notna()) &
        (customer_orders['Order Type'] != '') &
        (customer_orders['Order Type'] != 'nan')
    ]
    
    if valid.empty:
        return None
    
    type_mix = valid.groupby('Order Type')['Amount'].sum().reset_index()
    type_mix = type_mix.sort_values('Amount', ascending=False)
    
    colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4', '#ec4899', '#84cc16']
    
    fig = go.Figure(data=[go.Pie(
        labels=type_mix['Order Type'],
        values=type_mix['Amount'],
        hole=0.4,
        marker=dict(colors=colors[:len(type_mix)]),
        textposition='inside',
        textinfo='percent+label',
        textfont=dict(size=10, color='white'),
        hovertemplate='<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title=dict(text='Product Mix', font=dict(size=16, color='#1e293b')),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#1e293b'),
        showlegend=True,
        legend=dict(orientation='h', yanchor='top', y=-0.1, xanchor='center', x=0.5, font=dict(size=10)),
        margin=dict(t=50, b=80, l=20, r=20)
    )
    
    return fig
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-create_pipeline_chart"></a> `create_pipeline_chart` — L220–L270

```python
def create_pipeline_chart(customer_deals):
    """Create pipeline breakdown chart for PDF export"""
    if customer_deals.empty:
        return None
    
    open_statuses = ['Expect', 'Commit', 'Best Case', 'Opportunity']
    open_deals = customer_deals[customer_deals['Close Status'].isin(open_statuses)]
    
    if open_deals.empty:
        return None
    
    status_data = open_deals.groupby('Close Status')['Amount'].sum().reset_index()
    
    # Order by pipeline stage
    status_order = {'Commit': 0, 'Expect': 1, 'Best Case': 2, 'Opportunity': 3}
    status_data['Order'] = status_data['Close Status'].map(status_order).fillna(4)
    status_data = status_data.sort_values('Order')
    
    colors = {'Commit': '#10b981', 'Expect': '#3b82f6', 'Best Case': '#f59e0b', 'Opportunity': '#8b5cf6'}
    bar_colors = [colors.get(s, '#64748b') for s in status_data['Close Status']]
    
    fig = go.Figure(data=[
        go.Bar(
            x=status_data['Close Status'],
            y=status_data['Amount'],
            marker=dict(color=bar_colors),
            text=[f'${x:,.0f}' for x in status_data['Amount']],
            textposition='outside',
            textfont=dict(size=11),
            cliponaxis=False
        )
    ])
    
    # Calculate y-axis max to give room for labels
    max_val = status_data['Amount'].max()
    y_max = max_val * 1.15  # Add 15% headroom
    
    fig.update_layout(
        title=dict(text='Upcoming Orders by Status', font=dict(size=16, color='#1e293b')),
        xaxis_title='',
        yaxis_title='Value',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#1e293b', size=11),
        xaxis=dict(gridcolor='#e2e8f0'),
        yaxis=dict(gridcolor='#e2e8f0', tickformat='$,.0f', range=[0, y_max]),
        margin=dict(t=60, b=50, l=80, r=40),
        showlegend=False
    )
    
    return fig
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-clean_numeric"></a> `clean_numeric` — L3622–L3630

```python
def clean_numeric(value):
    """Clean and convert a value to numeric"""
    if pd.isna(value) or str(value).strip() == '':
        return 0
    cleaned = str(value).replace(',', '').replace('$', '').replace(' ', '').strip()
    try:
        return float(cleaned)
    except:
        return 0
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-load_sku_display_names"></a> `load_sku_display_names` — L3634–L3663

```python
def load_sku_display_names(version=CACHE_VERSION):
    """
    Load SKU → Description mapping from Raw_Items sheet.
    Used for enriching SKU data with human-readable descriptions.
    Priority: Column C "Description", fallback to Column B "Display Name"
    """
    raw_items_df = load_google_sheets_data("Raw_Items", "A:C", version=version, silent=True)
    
    sku_lookup = {}
    if not raw_items_df.empty:
        # Expected columns: A=SKU, B=Display Name, C=Description
        sku_col = 'SKU' if 'SKU' in raw_items_df.columns else None
        desc_col = 'Description' if 'Description' in raw_items_df.columns else None
        name_col = 'Display Name' if 'Display Name' in raw_items_df.columns else None
        
        if sku_col and (desc_col or name_col):
            for _, row in raw_items_df.iterrows():
                sku = str(row[sku_col]).strip() if pd.notna(row[sku_col]) else ''
                
                # Prefer Description (Column C), fallback to Display Name (Column B)
                description = ''
                if desc_col and pd.notna(row[desc_col]):
                    description = str(row[desc_col]).strip()
                if (not description or description.lower() == 'nan') and name_col and pd.notna(row[name_col]):
                    description = str(row[name_col]).strip()
                
                if sku and description and description.lower() != 'nan':
                    sku_lookup[sku] = description
    
    return sku_lookup
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-load_raw_inventory"></a> `load_raw_inventory` — L3667–L3694

```python
def load_raw_inventory(version=CACHE_VERSION):
    """
    Load inventory data from Raw_Inventory sheet.
    Returns a DataFrame with SKU-level inventory quantities.
    Expected columns: Item (SKU), Location, Quantity Available, etc.
    """
    raw_inventory_df = load_google_sheets_data("Raw_Inventory", "A:Z", version=version, silent=True)
    
    if raw_inventory_df.empty:
        return pd.DataFrame()
    
    # Clean numeric columns
    numeric_cols = ['Quantity Available', 'Quantity On Hand', 'Quantity Committed', 'Quantity On Order']
    for col in numeric_cols:
        if col in raw_inventory_df.columns:
            raw_inventory_df[col] = raw_inventory_df[col].apply(clean_numeric)
    
    # Normalize Item/SKU column
    item_col = None
    for col in ['Item', 'SKU', 'Item Name']:
        if col in raw_inventory_df.columns:
            item_col = col
            break
    
    if item_col and item_col != 'SKU':
        raw_inventory_df['SKU'] = raw_inventory_df[item_col]
    
    return raw_inventory_df
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-get_inventory_for_skus"></a> `get_inventory_for_skus` — L3697–L3742

```python
def get_inventory_for_skus(inventory_df, target_skus):
    """
    Get inventory quantities for a list of SKUs.
    Returns dict: SKU -> {'available': qty, 'on_hand': qty, 'on_order': qty, 'location': location}
    """
    inventory_by_sku = {}
    
    if inventory_df.empty or 'SKU' not in inventory_df.columns:
        return inventory_by_sku
    
    # Normalize target SKUs for matching
    target_skus_upper = [sku.upper() for sku in target_skus]
    
    for sku in target_skus:
        sku_upper = sku.upper()
        # Find matching rows (could be multiple locations)
        matches = inventory_df[inventory_df['SKU'].astype(str).str.upper().str.strip() == sku_upper]
        
        if not matches.empty:
            # Sum across all locations
            available = matches['Quantity Available'].sum() if 'Quantity Available' in matches.columns else 0
            on_hand = matches['Quantity On Hand'].sum() if 'Quantity On Hand' in matches.columns else 0
            on_order = matches['Quantity On Order'].sum() if 'Quantity On Order' in matches.columns else 0
            
            # Get locations as list
            locations = []
            if 'Location' in matches.columns:
                locations = matches['Location'].dropna().unique().tolist()
            
            inventory_by_sku[sku] = {
                'available': available,
                'on_hand': on_hand,
                'on_order': on_order,
                'locations': locations,
                'total_qty': available + on_order
            }
        else:
            inventory_by_sku[sku] = {
                'available': 0,
                'on_hand': 0,
                'on_order': 0,
                'locations': [],
                'total_qty': 0
            }
    
    return inventory_by_sku
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-load_qbr_data"></a> `load_qbr_data` — L3745–L4334

```python
def load_qbr_data():
    """Load all data needed for QBR generation"""
    
    # Load Sales Orders (A:AG to include all columns through Updated Status)
    sales_orders_df = load_google_sheets_data("_NS_SalesOrders_Data", "A:AG", version=CACHE_VERSION)
    
    # Load Invoices (A:U to include Rep Master)
    invoices_df = load_google_sheets_data("_NS_Invoices_Data", "A:U", version=CACHE_VERSION)
    
    # Load HubSpot Deals - load wider range to ensure we get Company Name
    deals_df = load_google_sheets_data("All Reps All Pipelines", "A:Z", version=CACHE_VERSION)
    
    # =========================================================================
    # PROCESS SALES ORDERS - use column names directly from sheet
    # =========================================================================
    if not sales_orders_df.empty:
        # Remove duplicate columns
        if sales_orders_df.columns.duplicated().any():
            sales_orders_df = sales_orders_df.loc[:, ~sales_orders_df.columns.duplicated()]
        
        # Handle Amount column - could be 'Amount' or 'Amount (Transaction Total)'
        if 'Amount (Transaction Total)' in sales_orders_df.columns and 'Amount' not in sales_orders_df.columns:
            sales_orders_df = sales_orders_df.rename(columns={'Amount (Transaction Total)': 'Amount'})
        
        # Clean numeric data
        if 'Amount' in sales_orders_df.columns:
            sales_orders_df['Amount'] = sales_orders_df['Amount'].apply(clean_numeric)
        
        # Clean date data
        if 'Order Start Date' in sales_orders_df.columns:
            sales_orders_df['Order Start Date'] = pd.to_datetime(sales_orders_df['Order Start Date'], errors='coerce')
        if 'Actual Ship Date' in sales_orders_df.columns:
            sales_orders_df['Actual Ship Date'] = pd.to_datetime(sales_orders_df['Actual Ship Date'], errors='coerce')
        if 'Customer Promise Date' in sales_orders_df.columns:
            sales_orders_df['Customer Promise Date'] = pd.to_datetime(sales_orders_df['Customer Promise Date'], errors='coerce')
        # Also handle alternate column name
        if 'Customer Promise Last Date to Ship' in sales_orders_df.columns:
            sales_orders_df['Customer Promise Date'] = pd.to_datetime(sales_orders_df['Customer Promise Last Date to Ship'], errors='coerce')
        
        # Clean text fields
        for col in ['Corrected Customer Name', 'Rep Master', 'Updated Status', 'Order Type', 'Status']:
            if col in sales_orders_df.columns:
                sales_orders_df[col] = sales_orders_df[col].astype(str).str.strip()
    
    # =========================================================================
    # PROCESS INVOICES - use column names directly from sheet
    # =========================================================================
    if not invoices_df.empty:
        # Remove duplicate columns
        if invoices_df.columns.duplicated().any():
            invoices_df = invoices_df.loc[:, ~invoices_df.columns.duplicated()]
        
        # Handle Amount column - could be 'Amount' or 'Amount (Transaction Total)'
        if 'Amount (Transaction Total)' in invoices_df.columns and 'Amount' not in invoices_df.columns:
            invoices_df = invoices_df.rename(columns={'Amount (Transaction Total)': 'Amount'})
        
        # Clean numeric data
        if 'Amount' in invoices_df.columns:
            invoices_df['Amount'] = invoices_df['Amount'].apply(clean_numeric)
        if 'Amount Remaining' in invoices_df.columns:
            invoices_df['Amount Remaining'] = invoices_df['Amount Remaining'].apply(clean_numeric)
        
        # Clean date data
        if 'Date' in invoices_df.columns:
            invoices_df['Date'] = pd.to_datetime(invoices_df['Date'], errors='coerce')
        if 'Due Date' in invoices_df.columns:
            invoices_df['Due Date'] = pd.to_datetime(invoices_df['Due Date'], errors='coerce')
        
        # Clean text fields
        for col in ['Corrected Customer', 'Rep Master', 'Status']:
            if col in invoices_df.columns:
                invoices_df[col] = invoices_df[col].astype(str).str.strip()
        
        # Extract SO Number from Created From
        if 'Created From' in invoices_df.columns:
            invoices_df['SO Number'] = invoices_df['Created From'].astype(str).str.replace('Sales Order #', '', regex=False).str.strip()
    
    # =========================================================================
    # PROCESS HUBSPOT DEALS
    # Use actual column names from header row, not positional indices
    # =========================================================================
    if not deals_df.empty:
        # Create a mapping of potential column name variations to standard names
        column_mapping = {
            # Standard name variations
            'Record ID': 'Record ID',
            'Deal Name': 'Deal Name',
            'Deal Stage': 'Deal Stage',
            'Close Date': 'Close Date',
            'Deal Owner First Name': 'Deal Owner First Name',
            'Deal Owner Last Name': 'Deal Owner Last Name',
            'Deal Owner First Name Deal Owner Last Name': 'Deal Owner Combined',
            'Amount': 'Amount',
            'Close Status': 'Close Status',
            'Pipeline': 'Pipeline',
            'Create Date': 'Create Date',
            'Deal Type': 'Deal Type',
            'Netsuite SO#': 'Netsuite SO#',
            'Netsuite SO Link': 'Netsuite SO Link',
            'New Design SKU': 'New Design SKU',
            'SKU': 'SKU',
            'Netsuite Sales Order Number': 'Netsuite Sales Order Number',
            'Primary Associated Company': 'Primary Associated Company',
            'Average Leadtime': 'Average Leadtime',
            'Pending Approval Date': 'Pending Approval Date',
            'Quarter': 'Quarter',
            'Deal Stage & Close Status': 'Deal Stage & Close Status',
            'Probability': 'Probability',
            'Probability Rev': 'Probability Rev',
            'Company Name': 'Company Name',
        }
        
        # Apply any mapping if column names match
        rename_dict = {}
        for col in deals_df.columns:
            col_stripped = str(col).strip()
            if col_stripped in column_mapping:
                rename_dict[col] = column_mapping[col_stripped]
        
        if rename_dict:
            deals_df = deals_df.rename(columns=rename_dict)
        
        # Remove duplicate columns
        if deals_df.columns.duplicated().any():
            deals_df = deals_df.loc[:, ~deals_df.columns.duplicated()]
        
        # Create Deal Owner by combining First Name + Last Name if separate columns exist
        if 'Deal Owner First Name' in deals_df.columns and 'Deal Owner Last Name' in deals_df.columns:
            deals_df['Deal Owner'] = (
                deals_df['Deal Owner First Name'].fillna('').astype(str).str.strip() + ' ' + 
                deals_df['Deal Owner Last Name'].fillna('').astype(str).str.strip()
            ).str.strip()
        elif 'Deal Owner Combined' in deals_df.columns:
            deals_df['Deal Owner'] = deals_df['Deal Owner Combined'].astype(str).str.strip()
        
        # Clean numeric data
        if 'Amount' in deals_df.columns:
            deals_df['Amount'] = deals_df['Amount'].apply(clean_numeric)
        if 'Probability Rev' in deals_df.columns:
            deals_df['Probability Rev'] = deals_df['Probability Rev'].apply(clean_numeric)
        else:
            deals_df['Probability Rev'] = deals_df.get('Amount', 0)
        
        # Clean date data
        if 'Close Date' in deals_df.columns:
            deals_df['Close Date'] = pd.to_datetime(deals_df['Close Date'], errors='coerce')
        if 'Pending Approval Date' in deals_df.columns:
            deals_df['Pending Approval Date'] = pd.to_datetime(deals_df['Pending Approval Date'], errors='coerce')
        
        # Clean text fields - strip whitespace AND newlines
        for col in ['Deal Owner', 'Deal Name', 'Close Status', 'Company Name', 'Primary Associated Company']:
            if col in deals_df.columns:
                deals_df[col] = deals_df[col].astype(str).str.strip().str.replace('\n', '', regex=False).str.replace('\r', '', regex=False)
        
        # FALLBACK: If Company Name doesn't exist, try to use Primary Associated Company
        if 'Company Name' not in deals_df.columns and 'Primary Associated Company' in deals_df.columns:
            deals_df['Company Name'] = deals_df['Primary Associated Company']
    
    # =========================================================================
    # LOAD AND PROCESS INVOICE LINE ITEMS
    # This is the drill-down layer explaining realized revenue composition
    # =========================================================================
    invoice_line_items_df = load_google_sheets_data("Invoice Line Item", "A:Z", version=CACHE_VERSION, silent=True)
    
    if not invoice_line_items_df.empty:
        # Remove duplicate columns
        if invoice_line_items_df.columns.duplicated().any():
            invoice_line_items_df = invoice_line_items_df.loc[:, ~invoice_line_items_df.columns.duplicated()]
        
        # Clean numeric data - Amount is line-level revenue
        if 'Amount' in invoice_line_items_df.columns:
            invoice_line_items_df['Amount'] = invoice_line_items_df['Amount'].apply(clean_numeric)
        
        # Quantity is unit-level volume
        if 'Quantity' in invoice_line_items_df.columns:
            invoice_line_items_df['Quantity'] = invoice_line_items_df['Quantity'].apply(clean_numeric)
        
        # Clean date data
        if 'Date' in invoice_line_items_df.columns:
            invoice_line_items_df['Date'] = pd.to_datetime(invoice_line_items_df['Date'], errors='coerce')
        if 'Due Date' in invoice_line_items_df.columns:
            invoice_line_items_df['Due Date'] = pd.to_datetime(invoice_line_items_df['Due Date'], errors='coerce')
        
        # Clean text fields - use Correct Customer and Rep Master as authoritative
        for col in ['Correct Customer', 'Rep Master', 'Status', 'Item', 'Item Description', 
                    'Calyx | Item Type', 'Calyx || Product Type']:
            if col in invoice_line_items_df.columns:
                invoice_line_items_df[col] = invoice_line_items_df[col].astype(str).str.strip()
                # Replace 'nan' strings with empty
                invoice_line_items_df[col] = invoice_line_items_df[col].replace('nan', '')
    
    # =========================================================================
    # LOAD AND PROCESS NCR (NON-CONFORMANCE) DATA
    # Used to track quality issues by customer
    # NetSuite NCR = source of truth from November 2024 onwards
    # HubSpot NCR = historical data before November 2024
    # =========================================================================
    
    # --- NetSuite NCR Data (Nov 2024+) ---
    ncr_df = pd.DataFrame()  # Initialize as empty
    ncr_raw = load_google_sheets_data("Non-Conformance Details", "A:W", version=CACHE_VERSION, silent=True)
    
    if not ncr_raw.empty:
        ncr_df = ncr_raw.copy()
        # Remove duplicate columns
        if ncr_df.columns.duplicated().any():
            ncr_df = ncr_df.loc[:, ~ncr_df.columns.duplicated()]
        
        # Clean text fields
        # Column mappings based on user spec:
        # F = Sales Order, I = Issue Type, P = Total Quantity Affected, V = Corrected Customer Name
        for col in ['Sales Order', 'Issue Type', 'Corrected Customer Name', 'Status', 
                    'Defect Summary', 'Priority', 'External Or Internal', 'NC Number']:
            if col in ncr_df.columns:
                ncr_df[col] = ncr_df[col].astype(str).str.strip()
                ncr_df[col] = ncr_df[col].replace('nan', '')
        
        # Clean numeric data - Total Quantity Affected
        if 'Total Quantity Affected' in ncr_df.columns:
            ncr_df['Total Quantity Affected'] = ncr_df['Total Quantity Affected'].apply(clean_numeric)
        
        # Clean Cost fields if present
        if 'Cost of Rework' in ncr_df.columns:
            ncr_df['Cost of Rework'] = ncr_df['Cost of Rework'].apply(clean_numeric)
        if 'Cost Avoided' in ncr_df.columns:
            ncr_df['Cost Avoided'] = ncr_df['Cost Avoided'].apply(clean_numeric)
        
        # Clean date data
        if 'Date Submitted' in ncr_df.columns:
            ncr_df['Date Submitted'] = pd.to_datetime(ncr_df['Date Submitted'], errors='coerce')
        if 'On Time Ship Date' in ncr_df.columns:
            ncr_df['On Time Ship Date'] = pd.to_datetime(ncr_df['On Time Ship Date'], errors='coerce')
        
        # Add source indicator
        ncr_df['NCR Source'] = 'NetSuite'
        
        # Standardize column for matching
        ncr_df['Matched Customer'] = ncr_df.get('Corrected Customer Name', '')
    
    # --- HubSpot NCR Data (Historical, pre-Nov 2024) ---
    hb_ncr_df = pd.DataFrame()  # Initialize as empty
    hb_ncr_raw = load_google_sheets_data("HB NCR", "A2:O", version=CACHE_VERSION, silent=True)
    
    if not hb_ncr_raw.empty:
        hb_ncr_df = hb_ncr_raw.copy()
        # Remove duplicate columns
        if hb_ncr_df.columns.duplicated().any():
            hb_ncr_df = hb_ncr_df.loc[:, ~hb_ncr_df.columns.duplicated()]
        
        # Filter to Customer NCR Pipeline only
        if 'Pipeline' in hb_ncr_df.columns:
            hb_ncr_df = hb_ncr_df[hb_ncr_df['Pipeline'].str.strip() == 'Customer NCR Pipeline'].copy()
        
        if not hb_ncr_df.empty:
            # Clean text fields
            for col in ['Ticket ID', 'Ticket name', 'Ticket status', 'Pipeline', 
                        'Ticket description', 'Company Name', 'Company Name 2']:
                if col in hb_ncr_df.columns:
                    hb_ncr_df[col] = hb_ncr_df[col].astype(str).str.strip()
                    hb_ncr_df[col] = hb_ncr_df[col].replace('nan', '')
            
            # Clean date data
            if 'Create date' in hb_ncr_df.columns:
                hb_ncr_df['Create date'] = pd.to_datetime(hb_ncr_df['Create date'], errors='coerce')
            if 'Close date' in hb_ncr_df.columns:
                hb_ncr_df['Close date'] = pd.to_datetime(hb_ncr_df['Close date'], errors='coerce')
            
            # Calculate resolution time (days to close)
            if 'Create date' in hb_ncr_df.columns and 'Close date' in hb_ncr_df.columns:
                hb_ncr_df['Resolution Days'] = (hb_ncr_df['Close date'] - hb_ncr_df['Create date']).dt.days
            
            # --- Customer Matching Logic ---
            # Priority 1: Company Name 2 (exact match, same naming convention)
            # Priority 2: Company Name (fuzzy match)
            # Priority 3: Extract from Ticket name (format "NCR600 - Customer Name")
            
            def extract_customer_from_ticket(ticket_name):
                """Extract customer name from ticket formats:
                - 'NCR ### - Customer Name' (with dash)
                - 'NCR ### Customer Name' (no dash)
                - Also extracts NCR number for reference
                """
                import re
                if not ticket_name or ticket_name == '' or pd.isna(ticket_name):
                    return ''
                
                ticket_str = str(ticket_name).strip()
                
                # Pattern 1: "NCR ### - Customer Name" (with dash)
                if ' - ' in ticket_str:
                    parts = ticket_str.split(' - ', 1)
                    if len(parts) > 1:
                        customer_part = parts[1].strip()
                        # Remove any trailing issue description (after another dash or parenthetical)
                        # e.g., "Acreage (OH) Smearing" -> "Acreage (OH)"
                        return customer_part
                
                # Pattern 2: "NCR ### Customer Name" (no dash)
                # Match NCR followed by number, then capture everything after
                ncr_match = re.match(r'NCR\s*(\d+)\s+(.+)', ticket_str, re.IGNORECASE)
                if ncr_match:
                    customer_part = ncr_match.group(2).strip()
                    return customer_part
                
                return ''
            
            def extract_ncr_number_from_ticket(ticket_name):
                """Extract NCR number from ticket name"""
                import re
                if not ticket_name or ticket_name == '' or pd.isna(ticket_name):
                    return None
                
                ticket_str = str(ticket_name).strip()
                ncr_match = re.search(r'NCR\s*(\d+)', ticket_str, re.IGNORECASE)
                if ncr_match:
                    return ncr_match.group(1)
                return None
            
            def match_customer(row, valid_customers):
                """Match customer using priority logic with fuzzy matching"""
                from difflib import get_close_matches
                import re
                
                def normalize_for_matching(name):
                    """Normalize customer name for better matching"""
                    if not name:
                        return ''
                    name = str(name).strip()
                    # Remove common state abbreviations at the end (NY, MA, OH, NJ, PA, IL, etc.)
                    name = re.sub(r'\s+(NY|MA|OH|NJ|PA|IL|CA|CO|FL|TX|WA|OR|AZ|NV|MI|NC|SC|GA|VA|MD|CT|RI|NH|VT|ME|DE|WV|KY|TN|AL|MS|LA|AR|MO|IA|MN|WI|IN|OK|KS|NE|SD|ND|MT|WY|ID|UT|NM|HI|AK|DC)$', '', name, flags=re.IGNORECASE)
                    # Remove parenthetical state codes like (OH), (NY)
                    name = re.sub(r'\s*\([A-Z]{2}\)\s*', ' ', name)
                    # Remove trailing description words
                    name = re.sub(r'\s+(Smearing|Defect|Issue|Problem|Damage|Error).*$', '', name, flags=re.IGNORECASE)
                    return name.strip()
                
                def extract_base_company(company_name):
                    """Extract base company name from various formats:
                    - 'Parent : Child' format -> 'Parent'
                    - 'Acreage Holdings:  New York (NY)' -> 'Acreage Holdings'
                    - 'Acreage Holdings - Massachusetts (MA)' -> 'Acreage Holdings'
                    """
                    if not company_name or pd.isna(company_name):
                        return ''
                    name = str(company_name).strip()
                    
                    # Pattern 1: 'Parent : Child' - take the first part (HubSpot Company Name 2 format)
                    if ' : ' in name:
                        return name.split(' : ')[0].strip()
                    
                    # Pattern 2: 'Company:  Location (STATE)' - take before first colon
                    if ':' in name:
                        base = name.split(':')[0].strip()
                        # Only use if it looks like a company name (not a URL)
                        if '.' not in base and len(base) > 3:
                            return base
                    
                    # Pattern 3: 'Company - Location (STATE)' - take before dash if state follows
                    if ' - ' in name:
                        parts = name.split(' - ')
                        if len(parts) >= 2:
                            # Check if second part looks like a state/location
                            second = parts[1].strip()
                            if re.search(r'(Massachusetts|New York|Ohio|Pennsylvania|Illinois|New Jersey|Connecticut|Michigan|Florida|California|Colorado|Texas|Washington|Oregon|Arizona|Nevada|North Carolina|South Carolina|Georgia|Virginia|Maryland|NY|MA|OH|PA|IL|NJ|CT|MI|FL|CA|CO|TX|WA|OR|AZ|NV|NC|SC|GA|VA|MD)', second, re.IGNORECASE):
                                return parts[0].strip()
                    
                    return name
                
                def try_match(name, customers, cutoff=0.7):
                    """Try to match a name against valid customers"""
                    if not name:
                        return None
                    # Exact match first
                    if name in customers:
                        return name
                    # Normalized exact match
                    normalized = normalize_for_matching(name)
                    for cust in customers:
                        if normalize_for_matching(cust) == normalized:
                            return cust
                    # Fuzzy match
                    matches = get_close_matches(name, customers, n=1, cutoff=cutoff)
                    if matches:
                        return matches[0]
                    # Fuzzy match on normalized
                    if normalized != name:
                        matches = get_close_matches(normalized, customers, n=1, cutoff=cutoff)
                        if matches:
                            return matches[0]
                    return None
                
                # Priority 1: Company Name 2 - extract base and match
                company_name_2 = row.get('Company Name 2', '')
                if company_name_2 and company_name_2 != '' and not pd.isna(company_name_2):
                    # Extract base company name (before " : " if present)
                    base_name = extract_base_company(company_name_2)
                    if base_name:
                        match = try_match(base_name, valid_customers, cutoff=0.8)
                        if match:
                            return match
                
                # Priority 2: Company Name (try exact first, then fuzzy)
                company_name = row.get('Company Name', '')
                if company_name and company_name != '' and not pd.isna(company_name):
                    # Also extract base company from Company Name if it has " : " format
                    base_name = extract_base_company(company_name)
                    match = try_match(base_name if base_name else company_name, valid_customers, cutoff=0.7)
                    if match:
                        return match
                    # Try the raw company name with state stripped
                    normalized = normalize_for_matching(company_name)
                    match = try_match(normalized, valid_customers, cutoff=0.6)
                    if match:
                        return match
                
                # Priority 3: Extract from Ticket name and fuzzy match
                ticket_name = row.get('Ticket name', '')
                extracted = extract_customer_from_ticket(ticket_name)
                if extracted:
                    match = try_match(extracted, valid_customers, cutoff=0.5)
                    if match:
                        return match
                
                return ''  # No match found
            
            # Get list of valid customers for fuzzy matching
            valid_customers = set()
            if not sales_orders_df.empty and 'Corrected Customer Name' in sales_orders_df.columns:
                valid_customers.update(sales_orders_df['Corrected Customer Name'].dropna().unique())
            if not invoices_df.empty and 'Corrected Customer' in invoices_df.columns:
                valid_customers.update(invoices_df['Corrected Customer'].dropna().unique())
            valid_customers = [c for c in valid_customers if c and c not in ['', 'nan', 'None', '#N/A']]
            
            # Apply customer matching
            hb_ncr_df['Matched Customer'] = hb_ncr_df.apply(
                lambda row: match_customer(row, valid_customers), axis=1
            )
            
            # --- Categorize HubSpot NCRs based on description ---
            def categorize_hubspot_ncr(description):
                """Categorize HubSpot NCR based on ticket description to match NetSuite Issue Types"""
                if not description or description == '' or pd.isna(description):
                    return 'Defective Product'
                
                desc_lower = str(description).lower()
                
                # Damaged in Transit - carrier damage, broken in shipping
                if any(kw in desc_lower for kw in ['damaged', 'broken', 'crushed', 'fedex damaged', 
                                                    'ups damaged', 'transit', 'carrier', 'pallet.*damage']):
                    return 'Damaged in Transit'
                
                # Shipped to Wrong Address - misshipments, swapped orders
                if any(kw in desc_lower for kw in ['wrong address', 'misshipped', 'swapped', 
                                                    'wrong location', 'delivered to wrong']):
                    return 'Shipped to Wrong Address'
                
                # Missing Labels Wrong Qty - shortages
                if any(kw in desc_lower for kw in ['short', 'missing', 'shorted', 'only received',
                                                    'ran short', 'labels short']):
                    return 'Missing Labels Wrong Qty'
                
                # Order Entry Error - system/data entry issues, customer ordered wrong
                if any(kw in desc_lower for kw in ['hubspot', 'netsuite', 'set up incorrectly', 
                                                    'entered into', 'system switched',
                                                    'customer ordered wrong', 'mistakenly ordered',
                                                    'accidentally placed', 'customer error',
                                                    'deal & so was reflective of the wrong',
                                                    'proofing queue']):
                    return 'Order Entry Error'
                
                # Wrong Material - wrong product shipped (includes wrong color/size)
                if any(kw in desc_lower for kw in ['wrong color', 'wrong size', 'wrong finish',
                                                    'received white instead', 'received black instead', 
                                                    'instead of', '25d instead', '15d instead', 
                                                    '7ml instead', '45d instead', '4ml instead',
                                                    'wrong sku', 'wrong product', 'mislabeled box',
                                                    'shipped black instead', 'shipped white instead',
                                                    'wrong core', 'not the artwork']):
                    return 'Wrong Material'
                
                # Incorrect Color - specifically color-related manufacturing issues
                if any(kw in desc_lower for kw in ['grey caps', 'marbling', 'translucent',
                                                    'color.*mixed', 'pigment']):
                    return 'Incorrect Color'
                
                # Artwork/Print/Label defects
                if any(kw in desc_lower for kw in ['print', 'artwork', 'off center', 'embossing',
                                                    'cut off', 'varnish', 'laminate', 'tactile',
                                                    'telescoping', 'backing.*rip', 'paper backing',
                                                    'poor print', 'skipout']):
                    return 'Artwork Error'
                
                # Defective Product - manufacturing defects, contamination, fit issues
                if any(kw in desc_lower for kw in ['warped', 'warping', 'defect', 'grease', 
                                                    'debris', 'contaminated', 'filth', 'insect', 
                                                    'hair', 'doesn\'t fit', 'not sealing', 'leaking',
                                                    'cracked', 'irregular', 'lid.*fit', 'snapping',
                                                    'boxes not forming', 'not in.*bag']):
                    return 'Defective Product'
                
                # Customer Returns (not defect-related)
                if any(kw in desc_lower for kw in ['customer return', 'return', 'exchange',
                                                    'would like to replace', 'swap out']):
                    return 'Order Entry Error'
                
                # Default fallback
                return 'Defective Product'
            
            # Map HubSpot columns to standardized NCR columns
            # Extract NCR number from ticket name (e.g., "NCR 988 Acreage NY" → "NCR-988")
            if 'Ticket name' in hb_ncr_df.columns:
                hb_ncr_df['NC Number'] = hb_ncr_df['Ticket name'].apply(
                    lambda x: f"NCR-{extract_ncr_number_from_ticket(x)}" if extract_ncr_number_from_ticket(x) else str(x)[:30]
                )
            else:
                hb_ncr_df['NC Number'] = hb_ncr_df.get('Ticket ID', '').apply(lambda x: f"HB-{x}" if x else '')
            hb_ncr_df['Date Submitted'] = hb_ncr_df.get('Create date', pd.NaT)
            hb_ncr_df['Status'] = hb_ncr_df.get('Ticket status', '')
            hb_ncr_df['Defect Summary'] = hb_ncr_df.get('Ticket description', '')
            
            # Categorize based on description - matching NetSuite Issue Types
            hb_ncr_df['Issue Type'] = hb_ncr_df['Defect Summary'].apply(categorize_hubspot_ncr)
            
            # Calculate Total Quantity Affected from QTY columns and determine Product Type
            # Priority order: Boxes → Containers → Flexpack → Labels → General QTY
            qty_columns = [
                ('QTY of boxes effected', 'Boxes'),
                ('QTY of containers effected', 'Containers'),
                ('Flexpack QTY Effected', 'Flexpack'),
                ('QTY of labels effected', 'Labels'),
                ('QTY Effected', 'General')
            ]
            
            def get_qty_and_product_type(row):
                """Get quantity affected and product type from first non-empty QTY column"""
                for col_name, product_type in qty_columns:
                    if col_name in row.index:
                        val = row[col_name]
                        if pd.notna(val) and str(val).strip() not in ['', 'nan', '0']:
                            try:
                                qty = float(str(val).replace(',', '').strip())
                                if qty > 0:
                                    return qty, product_type
                            except (ValueError, TypeError):
                                continue
                return 0, 'Unknown'
            
            # Apply to get both quantity and product type
            qty_product = hb_ncr_df.apply(get_qty_and_product_type, axis=1)
            hb_ncr_df['Total Quantity Affected'] = qty_product.apply(lambda x: x[0])
            hb_ncr_df['Product Type Affected'] = qty_product.apply(lambda x: x[1])
            hb_ncr_df['NCR Source'] = 'HubSpot'
            hb_ncr_df['Close Date'] = hb_ncr_df.get('Close date', pd.NaT)
    
    # --- Combine NCR Data ---
    # Columns to keep for combined dataframe
    ncr_columns = ['NC Number', 'Date Submitted', 'Status', 'Issue Type', 'Defect Summary',
                   'Total Quantity Affected', 'Matched Customer', 'NCR Source', 'Sales Order']
    
    combined_ncr_df = pd.DataFrame()
    
    if not ncr_df.empty:
        # Ensure Sales Order column exists
        if 'Sales Order' not in ncr_df.columns:
            ncr_df['Sales Order'] = ''
        # Select columns that exist
        ns_cols = [c for c in ncr_columns if c in ncr_df.columns]
        combined_ncr_df = ncr_df[ns_cols].copy()
    
    if not hb_ncr_df.empty:
        # Add Sales Order placeholder if not exists
        if 'Sales Order' not in hb_ncr_df.columns:
            hb_ncr_df['Sales Order'] = ''
        # Add Close Date, Resolution Days, and Product Type Affected to combined
        hb_cols = [c for c in ncr_columns if c in hb_ncr_df.columns]
        if 'Close Date' in hb_ncr_df.columns:
            hb_cols.append('Close Date')
        if 'Resolution Days' in hb_ncr_df.columns:
            hb_cols.append('Resolution Days')
        if 'Product Type Affected' in hb_ncr_df.columns:
            hb_cols.append('Product Type Affected')
        
        hb_subset = hb_ncr_df[hb_cols].copy()
        
        if combined_ncr_df.empty:
            combined_ncr_df = hb_subset
        else:
            combined_ncr_df = pd.concat([combined_ncr_df, hb_subset], ignore_index=True)
    
    return sales_orders_df, invoices_df, deals_df, invoice_line_items_df, combined_ncr_df
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-get_rep_list"></a> `get_rep_list` — L4339–L4353

```python
def get_rep_list(sales_orders_df, invoices_df):
    """Get unique list of sales reps from both data sources"""
    reps = set()
    
    if not sales_orders_df.empty and 'Rep Master' in sales_orders_df.columns:
        valid_reps = sales_orders_df['Rep Master'].dropna()
        valid_reps = valid_reps[~valid_reps.isin(['', 'nan', 'None', '#N/A'])]
        reps.update(valid_reps.unique())
    
    if not invoices_df.empty and 'Rep Master' in invoices_df.columns:
        valid_reps = invoices_df['Rep Master'].dropna()
        valid_reps = valid_reps[~valid_reps.isin(['', 'nan', 'None', '#N/A'])]
        reps.update(valid_reps.unique())
    
    return sorted([r for r in reps if r])
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-get_customers_for_rep"></a> `get_customers_for_rep` — L4356–L4385

```python
def get_customers_for_rep(rep_name, sales_orders_df, invoices_df):
    """Get unique customers for a specific rep (or all reps if 'All Reps' selected)"""
    customers = set()
    
    # Handle "All Reps" case - return all customers
    all_reps = (rep_name == "All Reps")
    
    if not sales_orders_df.empty and 'Corrected Customer Name' in sales_orders_df.columns:
        if all_reps:
            valid_customers = sales_orders_df['Corrected Customer Name'].dropna()
        elif 'Rep Master' in sales_orders_df.columns:
            rep_orders = sales_orders_df[sales_orders_df['Rep Master'] == rep_name]
            valid_customers = rep_orders['Corrected Customer Name'].dropna()
        else:
            valid_customers = pd.Series(dtype=str)
        valid_customers = valid_customers[~valid_customers.isin(['', 'nan', 'None', '#N/A'])]
        customers.update(valid_customers.unique())
    
    if not invoices_df.empty and 'Corrected Customer' in invoices_df.columns:
        if all_reps:
            valid_customers = invoices_df['Corrected Customer'].dropna()
        elif 'Rep Master' in invoices_df.columns:
            rep_invoices = invoices_df[invoices_df['Rep Master'] == rep_name]
            valid_customers = rep_invoices['Corrected Customer'].dropna()
        else:
            valid_customers = pd.Series(dtype=str)
        valid_customers = valid_customers[~valid_customers.isin(['', 'nan', 'None', '#N/A'])]
        customers.update(valid_customers.unique())
    
    return sorted([c for c in customers if c])
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-get_customer_deals"></a> `get_customer_deals` — L4388–L4407

```python
def get_customer_deals(customer_name, rep_name, deals_df):
    """
    Get HubSpot deals for a specific customer using direct match on Company Name
    """
    if deals_df.empty or 'Company Name' not in deals_df.columns:
        return pd.DataFrame()
    
    # Handle "All Reps" case - don't filter by Deal Owner
    if rep_name == "All Reps":
        matches = deals_df[
            deals_df['Company Name'] == customer_name
        ].copy()
    else:
        # Direct match on Company Name and Deal Owner
        matches = deals_df[
            (deals_df['Company Name'] == customer_name) &
            (deals_df['Deal Owner'] == rep_name)
        ].copy()
    
    return matches
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-_crm_extract_parent"></a> `_crm_extract_parent` — L4422–L4444

```python
def _crm_extract_parent(customer_name):
    """Return the parent portion of a customer name, or None if it's a standalone.

    Two strategies, in order:
    1. Literal ``Parent : Child`` delimiter (HubSpot / NetSuite convention for
       groups like "AYR Wellness, Inc. : Ayr Wellness (OH)").
    2. Known MSO-parent prefix match for groups that appear in NetSuite as
       flat names like "Curaleaf NJ", "TerrAscend PA", "Trulieve - Tampa" —
       see ``_KNOWN_MSO_PARENTS``.

    Returns None for standalone customers (no colon, no known-MSO match).
    """
    if not customer_name or pd.isna(customer_name):
        return None
    name = str(customer_name).strip()
    if ' : ' in name:
        parent = name.split(' : ')[0].strip()
        if parent:
            return parent
    mso = _match_mso_parent(name)
    if mso:
        return mso
    return None
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-_match_mso_parent"></a> `_match_mso_parent` — L4481–L4508

```python
def _match_mso_parent(customer_name):
    """Return the canonical MSO parent for a flat customer name, or None.

    The name is classified as a child when, after lowercasing and collapsing
    whitespace, it STARTS WITH any alias followed by a separator (space, dash,
    colon, comma, paren, slash) — or is ``<alias> <state-code>``.
    An exact equality with the alias is treated as the parent itself, not a
    child (so the parent doesn't get listed as a child of itself).
    """
    if not customer_name or pd.isna(customer_name):
        return None
    raw = str(customer_name).strip()
    if not raw:
        return None
    name_lower = re.sub(r'\s+', ' ', raw.lower())
    separators = (' ', '-', ':', ',', '(', '/', '.')
    for canonical, aliases in _KNOWN_MSO_PARENTS.items():
        for alias in aliases:
            a_lower = alias.lower()
            # Exact match → this IS the parent, not a child
            if name_lower == a_lower:
                return None
            # Prefix match followed by a separator → this is a child location
            if name_lower.startswith(a_lower):
                rest = name_lower[len(a_lower):]
                if rest and rest[0] in separators:
                    return canonical
    return None
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-_crm_normalize"></a> `_crm_normalize` — L4511–L4518

```python
def _crm_normalize(name):
    """Lightweight normalization used for reconciling names across systems."""
    if not name or pd.isna(name):
        return ''
    n = str(name).lower().strip()
    n = re.sub(r'[^a-z0-9 ]+', ' ', n)
    n = re.sub(r'\s+', ' ', n)
    return n
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-build_parent_child_map"></a> `build_parent_child_map` — L4521–L4572

```python
def build_parent_child_map(sales_orders_df, invoices_df, deals_df):
    """Scan all three data sources and build parent<->child lookups.

    Returns a dict with three keys:
      - parent_to_children: {parent_name: [child_name, ...]}
      - child_to_parent:    {child_name: parent_name}
      - normalized_child_to_parent: {normalized_child: parent_name}
    Children are taken from any 'Parent : Child' value found in:
      - sales_orders_df['Corrected Customer Name']
      - invoices_df['Corrected Customer']
      - deals_df['Company Name 2']
    """
    names = set()

    if sales_orders_df is not None and not sales_orders_df.empty \
            and 'Corrected Customer Name' in sales_orders_df.columns:
        names.update(sales_orders_df['Corrected Customer Name'].dropna().unique())

    if invoices_df is not None and not invoices_df.empty \
            and 'Corrected Customer' in invoices_df.columns:
        names.update(invoices_df['Corrected Customer'].dropna().unique())

    if deals_df is not None and not deals_df.empty \
            and 'Company Name 2' in deals_df.columns:
        names.update(deals_df['Company Name 2'].dropna().unique())

    parent_to_children = {}
    child_to_parent = {}
    normalized_child_to_parent = {}

    for name in names:
        if not name or str(name).strip() in ('', 'nan', 'None', '#N/A'):
            continue
        parent = _crm_extract_parent(name)
        if not parent:
            continue
        child = str(name).strip()
        child_to_parent[child] = parent
        normalized_child_to_parent[_crm_normalize(child)] = parent
        parent_to_children.setdefault(parent, [])
        if child not in parent_to_children[parent]:
            parent_to_children[parent].append(child)

    # Sort children within each parent for stable UI
    for parent in parent_to_children:
        parent_to_children[parent].sort()

    return {
        'parent_to_children': parent_to_children,
        'child_to_parent': child_to_parent,
        'normalized_child_to_parent': normalized_child_to_parent,
    }
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-resolve_account_customers"></a> `resolve_account_customers` — L4575–L4591

```python
def resolve_account_customers(account, scope_mode, child, parent_map):
    """Expand an account selection into the list of underlying customer names.

    - If ``account`` is a parent in the map:
        * ``scope_mode == 'parent'`` -> all children
        * ``scope_mode == 'child'``  -> [child] when provided, else all children
    - Otherwise (standalone customer) -> [account]
    """
    if not account:
        return []
    parent_to_children = parent_map.get('parent_to_children', {})
    if account in parent_to_children:
        children = parent_to_children[account]
        if scope_mode == 'child' and child and child in children:
            return [child]
        return list(children)
    return [account]
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-build_rep_account_roster"></a> `build_rep_account_roster` — L4594–L4726

```python
def build_rep_account_roster(rep_name, sales_orders_df, invoices_df, deals_df,
                             parent_map, group_by_parent=True, today=None):
    """Build the card-grid roster for a rep, optionally rolled up by parent.

    Returns a list of dicts, one per account (parent or standalone), each with:
        account, is_parent, child_count, children,
        last_order_date, most_recent_child, days_since_last_order,
        ytd_revenue, current_quarter_rev, open_ar,
        pipeline_value, deal_count, status
    """
    if today is None:
        try:
            today = datetime.now(ZoneInfo('America/New_York')).replace(tzinfo=None)
        except Exception:
            today = datetime.now()

    year_start = datetime(today.year, 1, 1)
    quarter_idx = (today.month - 1) // 3
    quarter_start = datetime(today.year, quarter_idx * 3 + 1, 1)

    # Customers this rep touches (before parent grouping)
    customers = get_customers_for_rep(rep_name, sales_orders_df, invoices_df)
    if not customers:
        return []

    child_to_parent = parent_map.get('child_to_parent', {})

    # Group customers into accounts
    accounts = {}  # account_name -> {'is_parent': bool, 'children': [customer_name, ...]}
    for customer in customers:
        parent = child_to_parent.get(customer) if group_by_parent else None
        if parent:
            acct = accounts.setdefault(parent, {'is_parent': True, 'children': []})
            if customer not in acct['children']:
                acct['children'].append(customer)
        else:
            # Standalone (or grouping disabled)
            acct = accounts.setdefault(customer, {'is_parent': False, 'children': [customer]})

    # Precompute per-customer metrics once
    so = sales_orders_df if sales_orders_df is not None else pd.DataFrame()
    inv = invoices_df if invoices_df is not None else pd.DataFrame()
    deals = deals_df if deals_df is not None else pd.DataFrame()

    # Open deals: Close Status empty / 'Open' (anything not Won/Lost)
    open_deals = pd.DataFrame()
    if not deals.empty and 'Close Status' in deals.columns:
        cs = deals['Close Status'].fillna('').astype(str).str.strip().str.lower()
        open_deals = deals[~cs.isin(['won', 'lost', 'closed won', 'closed lost'])].copy()

    roster = []
    for account_name, data in accounts.items():
        child_list = data['children']
        is_parent = data['is_parent'] and len(child_list) > 1

        # Last order date across children (using Order Start Date)
        last_order_date = pd.NaT
        most_recent_child = None
        if not so.empty and 'Corrected Customer Name' in so.columns and 'Order Start Date' in so.columns:
            mask = so['Corrected Customer Name'].isin(child_list)
            rows = so[mask]
            if not rows.empty:
                rows = rows.dropna(subset=['Order Start Date'])
                if not rows.empty:
                    idx = rows['Order Start Date'].idxmax()
                    last_order_date = rows.loc[idx, 'Order Start Date']
                    most_recent_child = rows.loc[idx, 'Corrected Customer Name']

        days_since_last_order = None
        if pd.notna(last_order_date):
            try:
                days_since_last_order = (today - pd.Timestamp(last_order_date).to_pydatetime()).days
            except Exception:
                days_since_last_order = None

        # Invoice-driven metrics
        ytd_revenue = 0.0
        current_quarter_rev = 0.0
        open_ar = 0.0
        if not inv.empty and 'Corrected Customer' in inv.columns:
            inv_rows = inv[inv['Corrected Customer'].isin(child_list)]
            if not inv_rows.empty:
                if 'Date' in inv_rows.columns and 'Amount' in inv_rows.columns:
                    ytd_rows = inv_rows[inv_rows['Date'] >= year_start]
                    ytd_revenue = float(ytd_rows['Amount'].sum() or 0)
                    q_rows = inv_rows[inv_rows['Date'] >= quarter_start]
                    current_quarter_rev = float(q_rows['Amount'].sum() or 0)
                if 'Status' in inv_rows.columns and 'Amount Remaining' in inv_rows.columns:
                    open_rows = inv_rows[inv_rows['Status'].str.strip().str.lower() == 'open']
                    open_ar = float(open_rows['Amount Remaining'].sum() or 0)

        # Pipeline (open deals) — match deals by Company Name OR Company Name 2
        pipeline_value = 0.0
        deal_count = 0
        if not open_deals.empty:
            match = pd.Series(False, index=open_deals.index)
            if 'Company Name' in open_deals.columns:
                match = match | open_deals['Company Name'].isin(child_list)
            if 'Company Name 2' in open_deals.columns:
                match = match | open_deals['Company Name 2'].isin(child_list)
            matched = open_deals[match]
            if not matched.empty:
                if 'Amount' in matched.columns:
                    pipeline_value = float(matched['Amount'].sum() or 0)
                deal_count = len(matched)

        # Status based on days since last order
        if days_since_last_order is None:
            status = 'never'
        elif days_since_last_order <= 30:
            status = 'active'
        elif days_since_last_order <= 90:
            status = 'at_risk'
        else:
            status = 'dormant'

        roster.append({
            'account': account_name,
            'is_parent': is_parent,
            'child_count': len(child_list) if is_parent else 0,
            'children': list(child_list),
            'last_order_date': last_order_date if pd.notna(last_order_date) else None,
            'most_recent_child': most_recent_child,
            'days_since_last_order': days_since_last_order,
            'ytd_revenue': ytd_revenue,
            'current_quarter_rev': current_quarter_rev,
            'open_ar': open_ar,
            'pipeline_value': pipeline_value,
            'deal_count': deal_count,
            'status': status,
        })

    return roster
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-build_child_breakdown"></a> `build_child_breakdown` — L4729–L4811

```python
def build_child_breakdown(parent_name, sales_orders_df, invoices_df, deals_df,
                          parent_map, today=None):
    """One row per child of a parent account, for the detail-page table."""
    children = parent_map.get('parent_to_children', {}).get(parent_name, [])
    if not children:
        return []

    if today is None:
        try:
            today = datetime.now(ZoneInfo('America/New_York')).replace(tzinfo=None)
        except Exception:
            today = datetime.now()
    year_start = datetime(today.year, 1, 1)

    so = sales_orders_df if sales_orders_df is not None else pd.DataFrame()
    inv = invoices_df if invoices_df is not None else pd.DataFrame()
    deals = deals_df if deals_df is not None else pd.DataFrame()

    open_deals = pd.DataFrame()
    if not deals.empty and 'Close Status' in deals.columns:
        cs = deals['Close Status'].fillna('').astype(str).str.strip().str.lower()
        open_deals = deals[~cs.isin(['won', 'lost', 'closed won', 'closed lost'])].copy()

    rows = []
    for child in children:
        last_order = None
        days_since = None
        if not so.empty and 'Corrected Customer Name' in so.columns and 'Order Start Date' in so.columns:
            c_rows = so[so['Corrected Customer Name'] == child].dropna(subset=['Order Start Date'])
            if not c_rows.empty:
                last_order = c_rows['Order Start Date'].max()
                try:
                    days_since = (today - pd.Timestamp(last_order).to_pydatetime()).days
                except Exception:
                    days_since = None

        ytd_rev = 0.0
        open_ar = 0.0
        if not inv.empty and 'Corrected Customer' in inv.columns:
            inv_rows = inv[inv['Corrected Customer'] == child]
            if not inv_rows.empty:
                if 'Date' in inv_rows.columns and 'Amount' in inv_rows.columns:
                    ytd_rows = inv_rows[inv_rows['Date'] >= year_start]
                    ytd_rev = float(ytd_rows['Amount'].sum() or 0)
                if 'Status' in inv_rows.columns and 'Amount Remaining' in inv_rows.columns:
                    open_rows = inv_rows[inv_rows['Status'].str.strip().str.lower() == 'open']
                    open_ar = float(open_rows['Amount Remaining'].sum() or 0)

        pipeline = 0.0
        deal_count = 0
        if not open_deals.empty:
            match = pd.Series(False, index=open_deals.index)
            if 'Company Name' in open_deals.columns:
                match = match | (open_deals['Company Name'] == child)
            if 'Company Name 2' in open_deals.columns:
                match = match | (open_deals['Company Name 2'] == child)
            matched = open_deals[match]
            if not matched.empty:
                if 'Amount' in matched.columns:
                    pipeline = float(matched['Amount'].sum() or 0)
                deal_count = len(matched)

        if days_since is None:
            status = 'never'
        elif days_since <= 30:
            status = 'active'
        elif days_since <= 90:
            status = 'at_risk'
        else:
            status = 'dormant'

        rows.append({
            'child': child,
            'last_order_date': last_order if pd.notna(last_order) else None,
            'days_since_last_order': days_since,
            'ytd_revenue': ytd_rev,
            'open_ar': open_ar,
            'pipeline_value': pipeline,
            'deal_count': deal_count,
            'status': status,
        })

    return rows
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-extract_die_tool"></a> `extract_die_tool` — L5380–L5422

```python
def extract_die_tool(item_name):
    """
    Extract the die tool code from a SKU.
    Format: CUST-ST-DIETOOL-PRODUCT or CUST-ST-X-DIETOOL-PRODUCT
    Returns (die_tool, is_alphanumeric)
    
    Examples:
    - APOC-MI-H-25L-BB1-1 → die_tool='25L', is_alphanumeric=True (Dram lid label)
    - APOC-MI-1188-APGQ → die_tool='1188', is_alphanumeric=False (Flexpack/Label)
    - 989E-MI-H-4C-EX1-2 → die_tool='4C', is_alphanumeric=True (Concentrate label)
    """
    if pd.isna(item_name):
        return None, False
    
    name = str(item_name).upper().strip()
    
    # Pattern 1: XXXX-ST-X-DIETOOL-... (with single letter indicator like H, M, R)
    # The die tool is the component after the single letter: 25L, 45B, 4C, 7L, 116P, etc.
    match = re.search(r'^[A-Z]{3,4}-[A-Z]{2}-[A-Z]-(\d{1,3}[LBPCH])-', name)
    if match:
        return match.group(1), True
    
    # Pattern 2: XXXX-ST-X-DIETOOL (concentrate patterns like 4C, 7L, 7C)
    match = re.search(r'^[A-Z]{3,4}-[A-Z]{2}-[A-Z]-([47][CLH])-', name)
    if match:
        return match.group(1), True
    
    # Pattern 3: XXXX-ST-NUMERIC-... (purely numeric die tool for Flexpack/Labels)
    match = re.search(r'^[A-Z]{3,4}-[A-Z]{2}-(\d{4})-', name)
    if match:
        return match.group(1), False
    
    # Pattern 4: Direct patterns like -25L-, -45B-, -116P- anywhere in name
    match = re.search(r'-(\d{1,3}[LBPCH])-', name)
    if match:
        return match.group(1), True
    
    # Pattern 5: Concentrate patterns -4C-, -7L-, -7C- etc.
    match = re.search(r'-([47][CLH])-', name)
    if match:
        return match.group(1), True
    
    return None, False
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-categorize_product"></a> `categorize_product` — L5425–L5698

```python
def categorize_product(item_name, item_description="", calyx_product_type=""):
    """
    Categorize a product based on Item name, description, and Calyx || Product Type.
    Returns (category, sub_category, component_type) tuple.
    
    component_type: 'base', 'lid', 'label', 'band', 'accessory', 'complete', or None
    """
    if pd.isna(item_name):
        item_name = ""
    if pd.isna(item_description):
        item_description = ""
    if pd.isna(calyx_product_type):
        calyx_product_type = ""
    
    name = str(item_name).upper().strip()
    desc = str(item_description).upper().strip()
    product_type = str(calyx_product_type).upper().strip()
    all_text = f"{name} {desc}"
    
    # Extract die tool info
    die_tool, is_alphanumeric = extract_die_tool(item_name)
    
    # =========================================================================
    # 1. SHIPPING/TAXES/FEES - Break out into specific types
    # =========================================================================
    # Taxes
    if re.search(r'\bTAX\b|GST|HST|CANADIAN\s*(BUSINESS|GOODS)', all_text):
        return ('Fees & Adjustments', 'Taxes', None)
    
    # Shipping
    if re.search(r'^SHIPPING|SHIPPING\s*FEE|FREIGHT', all_text):
        return ('Fees & Adjustments', 'Shipping', None)
    
    # Expedite Fees
    if re.search(r'EXPEDITE\s*FEE|RUSH\s*FEE', all_text):
        return ('Fees & Adjustments', 'Expedite Fee', None)
    
    # Convenience Fees
    if re.search(r'CONVENIENCE\s*FEE', all_text):
        return ('Fees & Adjustments', 'Convenience Fee', None)
    
    # Discounts/Promos
    if re.search(r'^\$\d+OFF|DISCOUNT|PROMO|%\s*OFF', all_text):
        return ('Fees & Adjustments', 'Discount', None)
    
    # Accounting adjustments
    if re.search(r'^ACCOUNTING|OVERPAYMENT|BAD\s*DEBT|REPLACEMENT\s*ORDER', all_text):
        return ('Fees & Adjustments', 'Accounting Adjustment', None)
    
    # Sample/Creative charges
    if re.search(r'DIE\s*CUT\s*SAMPLE|SAMPLE\s*CHARGE|CREATIVE$|TESTIMONIAL', all_text):
        return ('Fees & Adjustments', 'Sample/Creative', None)
    
    # Tooling fees (check BEFORE label categorization - "Tooling Fee - Labels" is a fee, not a label)
    if re.search(r'TOOLING\s*FEE|TOOL\s*FEE|DIE\s*FEE|PLATE\s*FEE|SETUP\s*FEE', all_text):
        return ('Fees & Adjustments', 'Tooling Fee', None)
    
    # Other fees (catch-all for fee-like items)
    if re.search(r'MODULAR.*SERIAL', all_text):
        return ('Fees & Adjustments', 'Other Fee', None)
    
    # =========================================================================
    # 2. CALYX CURE
    # =========================================================================
    if name.startswith('CC-') or 'CALYX CURE' in all_text:
        return ('Calyx Cure', 'Calyx Cure', 'complete')
    
    # =========================================================================
    # 3. CALYX JAR (8TH Glass)
    # =========================================================================
    if 'GB-8TH' in name or name.startswith('CJ-') or 'CALYX JAR' in all_text:
        return ('Calyx Jar', 'Glass Base', 'base')
    if re.search(r'-JB-', name):
        return ('Calyx Jar', 'Jar Base', 'base')
    if re.search(r'-JL-', name):
        return ('Calyx Jar', 'Jar Lid', 'lid')
    if 'SB-8TH' in name:
        return ('Calyx Jar', 'Shrink Band', 'band')
    
    # =========================================================================
    # 4. CONCENTRATES (4mL/7mL Glass Bases and specific lids)
    # =========================================================================
    # Glass bases
    if re.search(r'GB-4ML|4ML.*GLASS|4\s*ML.*BASE', name):
        return ('Concentrates', '4mL Glass Base', 'base')
    if re.search(r'GB-7ML|7ML.*GLASS|7\s*ML.*BASE', name):
        return ('Concentrates', '7mL Glass Base', 'base')
    
    # Concentrate-specific lids (4C, 7C, 4L, 7L, 4H, 7H patterns)
    if re.search(r'-4[CLH]-|-4[CLH]$', name) and not re.search(r'BOX|TUCK|AUTO|DISPLAY', all_text):
        return ('Concentrates', '4mL Lid', 'lid')
    if re.search(r'-7[CLH]-|-7[CLH]$', name) and not re.search(r'BOX|TUCK|AUTO|DISPLAY', all_text):
        return ('Concentrates', '7mL Lid', 'lid')
    
    # Concentrate labels (alphanumeric die tool with 4C, 7C, 7L patterns)
    if die_tool and is_alphanumeric:
        if re.match(r'^[47][CLH]', die_tool):
            component = 'Lid Label' if 'L' in die_tool else 'Jar Label'
            size = '4mL' if die_tool.startswith('4') else '7mL'
            return ('Concentrates', f'{size} {component}', 'label')
    
    # =========================================================================
    # 5. DRAMS (15D, 25D, 45D, 145D) - Bases, Lids, Labels
    # =========================================================================
    dram_sizes = ['145', '45', '25', '15']  # Check larger first to avoid partial matches
    
    # FIRST: Check for customer label SKUs with alphanumeric die tools
    # These are LABELS, not physical products
    if die_tool and is_alphanumeric:
        for size in dram_sizes:
            size_d = f'{size}D'
            if re.match(rf'^{size}[LBPH]', die_tool):
                if 'L' in die_tool:
                    return ('Drams', f'{size_d} Lid Label', 'label')
                elif 'B' in die_tool or 'P' in die_tool:
                    return ('Drams', f'{size_d} Base Label', 'label')
                else:
                    return ('Drams', f'{size_d} Label', 'label')
    
    # THEN: Check for physical dram products (bases, lids)
    for size in dram_sizes:
        size_d = f'{size}D'
        
        # Polypropylene Bases: PB-XXD or -XXB- patterns
        if re.search(rf'PB-{size}D|{size}D.*BASE|-{size}B-', name):
            return ('Drams', f'{size_d} Base', 'base')
        
        # Polypropylene Lids: PL-XXD patterns (but NOT customer labels like XXXX-MI-H-25L-)
        # Only match if it starts with PL- or CL- (standard product codes)
        if size != '15':  # Skip 15 here, handle DML separately
            if re.search(rf'^PL-{size}D|^CL-{size}D', name):
                return ('Drams', f'{size_d} Lid', 'lid')
        
        # Direct size mentions in description (for standard products only)
        if f'{size}D LID' in all_text and not re.search(r'^[A-Z]{3,4}-[A-Z]{2}-', name):
            return ('Drams', f'{size_d} Lid', 'lid')
        if f'{size}D BASE' in all_text and not re.search(r'^[A-Z]{3,4}-[A-Z]{2}-', name):
            return ('Drams', f'{size_d} Base', 'base')
    
    # =========================================================================
    # 6. DML LIDS (Universal 4mL/7mL/15D - needs pairing to categorize)
    # -F suffix indicates it's specifically for 4mL/7mL concentrates
    # =========================================================================
    if 'DML' in name or re.search(r'PL-DML|CL-DML', name):
        # Check for -F suffix which indicates concentrate lid (4mL or 7mL)
        if name.endswith('-F') or re.search(r'-\d+-F$', name):
            return ('Concentrates', 'Universal Lid (4mL/7mL)', 'lid')
        # Otherwise mark for invoice-based pairing (could be 15D or concentrate)
        return ('DML (Universal)', 'Universal Lid', 'lid')
    
    # 15L patterns that aren't clearly dram-specific
    if re.search(r'-15L-|^15L-', name) and 'DML' not in name:
        # Check if it's clearly a dram label
        if die_tool and is_alphanumeric and die_tool.startswith('15'):
            return ('Drams', '15D Lid Label', 'label')
        # Otherwise it's likely a DML universal lid
        return ('DML (Universal)', 'Universal Lid', 'lid')
    
    # =========================================================================
    # 7. DRAM ACCESSORIES (Tray Frames, Tray Inserts, Shrink Bands)
    # =========================================================================
    if name.startswith('TF-') or 'TRAY FRAME' in all_text:
        return ('Dram Accessories', 'Tray Frame', 'accessory')
    
    if re.search(r'^TI-\d+D|TRAY INSERT', name):
        # Extract size from TI-XXD
        size_match = re.search(r'TI-(\d+)D', name)
        if size_match:
            return ('Dram Accessories', f'{size_match.group(1)}D Tray Insert', 'accessory')
        return ('Dram Accessories', 'Tray Insert', 'accessory')
    
    # Shrink bands for drams
    if re.search(r'SB-15D|SB-25D|SB-45D|SB-145D', name):
        size_match = re.search(r'SB-(\d+)D', name)
        if size_match:
            return ('Dram Accessories', f'{size_match.group(1)}D Shrink Band', 'band')
        return ('Dram Accessories', 'Shrink Band', 'band')
    
    # FEP Liners
    if 'FEP' in name and 'LINER' in all_text:
        return ('Dram Accessories', 'FEP Liner', 'accessory')
    
    # Stick & Grip
    if re.search(r'SG-|STICK.*GRIP', all_text):
        return ('Dram Accessories', 'Stick & Grip', 'accessory')
    
    # =========================================================================
    # 8. TUBES (116mm, 90mm, 84mm)
    # =========================================================================
    if re.search(r'JT-116|116\s*MM|116T|-116-|116P', name) and 'BOX' not in all_text:
        if 'LABEL' in all_text or (die_tool and '116' in die_tool):
            return ('Tubes', '116mm Label', 'label')
        return ('Tubes', '116mm Tube', 'complete')
    
    if re.search(r'JT-90|90\s*MM|90T|-90-|90M', name) and 'BOX' not in all_text and 'WAVEPACK' not in all_text:
        if 'LABEL' in all_text or (die_tool and '90' in die_tool):
            return ('Tubes', '90mm Label', 'label')
        return ('Tubes', '90mm Tube', 'complete')
    
    if re.search(r'JT-84|84\s*MM|84T|-84-', name) and 'TUBE' in all_text:
        if 'LABEL' in all_text:
            return ('Tubes', '84mm Label', 'label')
        return ('Tubes', '84mm Tube', 'complete')
    
    # =========================================================================
    # 9. BOXES
    # =========================================================================
    box_keywords = ['CORE AUTO', 'AUTOBOTTOM', 'AUTO BOTTOM', 'CORE TUCK', 
                    'REVERSE TUCK', 'ELEVATED TUCK', 'ELEVATED AUTO']
    if any(kw in all_text for kw in box_keywords) and 'BAG' not in all_text:
        if 'AUTO' in all_text:
            return ('Boxes', 'Core Auto', 'complete')
        if 'TUCK' in all_text:
            return ('Boxes', 'Core Tuck', 'complete')
        return ('Boxes', 'Box', 'complete')
    
    if re.search(r'-CNCA-|-CNC-', all_text) or 'SHIPPER BOX' in all_text:
        return ('Boxes', 'Shipper Box', 'complete')
    if 'BOX' in all_text and 'SBS' in all_text and 'BAG' not in all_text:
        return ('Boxes', 'Box', 'complete')
    if 'DISPLAY' in all_text and ('TEARAWAY' in all_text or 'ELEVATED' in all_text) and 'BAG' not in all_text:
        return ('Boxes', 'Display Box', 'complete')
    
    # =========================================================================
    # 10. FLEXPACK / WAVEPACK (check Calyx || Product Type first!)
    # =========================================================================
    # Use Calyx || Product Type if available
    if 'FLEXPACK' in product_type or 'WAVEPACK' in product_type or 'FLEX' in product_type:
        return ('Flexpack', 'Wavepack', 'complete')
    
    if name.startswith('BAM-') and 'LABEL' not in all_text:
        return ('Flexpack', 'Wavepack', 'complete')
    if re.search(r'WAVEPACK|FLEXPACK', all_text):
        return ('Flexpack', 'Wavepack', 'complete')
    if re.search(r'\bBAGS?\b|\bPOUCH\b', desc):
        return ('Flexpack', 'Bag/Pouch', 'complete')
    
    # Numeric die tool - could be Flexpack or Non-Core Label
    if die_tool and not is_alphanumeric and die_tool in FLEXPACK_CODES:
        return ('Flexpack', 'Wavepack', 'complete')
    
    # =========================================================================
    # 11. NON-CORE LABELS (customer-specific labels)
    # =========================================================================
    # Use Calyx || Product Type if available
    if 'LABEL' in product_type:
        return ('Non-Core Labels', 'Custom Label', 'label')
    
    if re.search(r'\bLABEL\b|\bLBL\b|\bBOPP\b', all_text):
        return ('Non-Core Labels', 'Custom Label', 'label')
    
    # Numeric die tool that's not a known Flexpack code
    if die_tool and not is_alphanumeric:
        return ('Non-Core Labels', 'Custom Label', 'label')
    
    # Customer SKU pattern without clear product identification
    if re.search(r'^[A-Z]{3,4}-[A-Z]{2}-', name):
        return ('Non-Core Labels', 'Custom Label', 'label')
    
    # =========================================================================
    # 12. APPLICATION FEES (categorize by what they're for)
    # =========================================================================
    if re.search(r'APPL\s*FEE|APPLICATION\s*FEE', all_text):
        # Try to determine what product the fee is for
        if re.search(r'15D|25D|45D|145D', all_text):
            return ('Drams', 'Application Fee', 'fee')
        if re.search(r'116|90', all_text) and 'TUBE' in all_text:
            return ('Tubes', 'Application Fee', 'fee')
        return ('Fees & Adjustments', 'Application Fee', 'fee')
    
    # =========================================================================
    # 13. UNCATEGORIZED
    # =========================================================================
    return ('Other', 'Uncategorized', None)
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-apply_product_categories"></a> `apply_product_categories` — L5701–L5735

```python
def apply_product_categories(df):
    """
    Apply categorization to a dataframe with Item and Item Description columns.
    Adds 'Product Category', 'Product Sub-Category', and 'Component Type' columns.
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Determine which columns to use
    item_col = 'Item' if 'Item' in df.columns else None
    desc_col = 'Item Description' if 'Item Description' in df.columns else None
    product_type_col = 'Calyx || Product Type' if 'Calyx || Product Type' in df.columns else None
    
    if item_col is None and desc_col is None:
        df['Product Category'] = 'Other'
        df['Product Sub-Category'] = 'Uncategorized'
        df['Component Type'] = None
        return df
    
    # Apply categorization
    categories = df.apply(
        lambda row: categorize_product(
            row.get(item_col, '') if item_col else '',
            row.get(desc_col, '') if desc_col else '',
            row.get(product_type_col, '') if product_type_col else ''
        ), axis=1
    )
    
    df['Product Category'] = categories.apply(lambda x: x[0])
    df['Product Sub-Category'] = categories.apply(lambda x: x[1])
    df['Component Type'] = categories.apply(lambda x: x[2])
    
    return df
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-rollup_dml_lids"></a> `rollup_dml_lids` — L5738–L5804

```python
def rollup_dml_lids(df):
    """
    Roll up DML (Universal) lids into their parent category based on 
    what other components are on the same invoice.
    
    Logic:
    - If invoice has GB-4ML or GB-7ML → DML lid becomes Concentrates
    - If invoice has PB-15D (15D base) → DML lid becomes Drams (15D)
    - Otherwise → stays as DML (Universal) or defaults to Concentrates
    """
    if df.empty or 'Product Category' not in df.columns:
        return df
    
    df = df.copy()
    
    # Find invoices with DML lids
    dml_mask = df['Product Category'] == 'DML (Universal)'
    if not dml_mask.any():
        return df
    
    # Get document numbers with DML lids
    doc_col = 'Document Number' if 'Document Number' in df.columns else None
    if doc_col is None:
        # Can't pair without document number - default DML to Concentrates
        df.loc[dml_mask, 'Product Category'] = 'Concentrates'
        df.loc[dml_mask, 'Product Sub-Category'] = 'Universal Lid (4mL/7mL/15D)'
        return df
    
    # Process each invoice with DML lids
    dml_docs = df.loc[dml_mask, doc_col].unique()
    
    for doc in dml_docs:
        doc_mask = df[doc_col] == doc
        doc_items = df.loc[doc_mask]
        
        # Check what else is on this invoice
        has_concentrate_base = doc_items['Product Sub-Category'].str.contains(
            r'4mL Glass Base|7mL Glass Base', case=False, na=False
        ).any()
        
        has_15d_base = doc_items['Product Sub-Category'].str.contains(
            r'15D Base', case=False, na=False
        ).any()
        
        # Also check Item column for patterns
        if 'Item' in doc_items.columns:
            items_str = ' '.join(doc_items['Item'].fillna('').astype(str))
            if re.search(r'GB-4ML|GB-7ML|4ML.*GLASS|7ML.*GLASS', items_str.upper()):
                has_concentrate_base = True
            if re.search(r'PB-15D|15D.*BASE|-15B-', items_str.upper()):
                has_15d_base = True
        
        # Assign DML lids based on pairing
        dml_in_doc = doc_mask & dml_mask
        
        if has_concentrate_base:
            df.loc[dml_in_doc, 'Product Category'] = 'Concentrates'
            df.loc[dml_in_doc, 'Product Sub-Category'] = 'Universal Lid'
        elif has_15d_base:
            df.loc[dml_in_doc, 'Product Category'] = 'Drams'
            df.loc[dml_in_doc, 'Product Sub-Category'] = '15D Lid'
        else:
            # Default to Concentrates if no clear pairing
            df.loc[dml_in_doc, 'Product Category'] = 'Concentrates'
            df.loc[dml_in_doc, 'Product Sub-Category'] = 'Universal Lid'
    
    return df
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-create_unified_product_view"></a> `create_unified_product_view` — L5807–L5897

```python
def create_unified_product_view(df):
    """
    Create a unified product view that rolls up components into complete products.
    
    For example, instead of showing:
    - 4mL Glass Base: $300
    - Universal Lid: $200
    
    Show:
    - 4mL Concentrate Jar (complete): $500
    
    This is for customer-facing summaries.
    
    Creates two new columns:
    - 'Unified Category': Size-specific (e.g., "Drams (25D)", "Concentrates (4mL)")
    - 'Parent Category': Rolled up (e.g., "Drams", "Concentrates")
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # First apply DML rollup
    df = rollup_dml_lids(df)
    
    # Create unified category for display
    def get_unified_category(row):
        cat = row.get('Product Category', 'Other')
        subcat = row.get('Product Sub-Category', '')
        component = row.get('Component Type', '')
        
        # For categories that are already complete products
        if cat in ['Tubes', 'Boxes', 'Flexpack', 'Calyx Cure', 'Fees & Adjustments', 'Other']:
            return cat
        
        # For Drams - unify base + lid + labels
        if cat == 'Drams':
            # Extract size (15D, 25D, 45D, 145D)
            size_match = re.search(r'(\d+D)', str(subcat))
            if size_match:
                return f"Drams ({size_match.group(1)})"
            return 'Drams'
        
        # For Concentrates - unify jar + lid
        if cat == 'Concentrates':
            size_match = re.search(r'(4mL|7mL)', str(subcat))
            if size_match:
                return f"Concentrates ({size_match.group(1)})"
            # Universal lids without clear size match
            if 'lid' in str(subcat).lower() or 'universal' in str(subcat).lower():
                return 'Concentrate Lids'
            return 'Concentrates'
        
        # For Calyx Jar
        if cat == 'Calyx Jar':
            return 'Calyx Jar'
        
        # For accessories - keep unified as Dram Accessories (shows in sub-breakdown)
        if cat == 'Dram Accessories':
            return 'Dram Accessories'
        
        # For labels
        if cat == 'Non-Core Labels':
            return 'Non-Core Labels'
        
        return cat
    
    df['Unified Category'] = df.apply(get_unified_category, axis=1)
    
    # Create Parent Category (rolled up - for summary views)
    # This groups all Drams together, all Concentrates together, etc.
    def get_parent_category(unified_cat):
        if pd.isna(unified_cat):
            return 'Other'
        
        unified = str(unified_cat)
        
        # Roll up Drams (25D, 45D, 15D, 145D) and Dram Accessories → Drams
        if unified.startswith('Drams') or unified == 'Dram Accessories':
            return 'Drams'
        
        # Roll up Concentrates (4mL, 7mL) and Concentrate Lids → Concentrates
        if unified.startswith('Concentrates') or unified == 'Concentrate Lids':
            return 'Concentrates'
        
        # Everything else stays as-is
        return unified
    
    df['Parent Category'] = df['Unified Category'].apply(get_parent_category)
    
    return df
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-compute_period_bounds"></a> `compute_period_bounds` — L7107–L7134

```python
def compute_period_bounds(period_label, custom_start=None, custom_end=None, today=None):
    """Return (start_date, end_date, label). ``start`` may be None to mean open-ended."""
    if today is None:
        try:
            today = datetime.now(ZoneInfo("America/New_York")).replace(tzinfo=None)
        except Exception:
            today = datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)

    if period_label == "All Time":
        return None, None, "All Time"
    if period_label == "YTD":
        return datetime(today.year, 1, 1), today, f"YTD {today.year}"
    if period_label == "This Quarter":
        q_idx = (today.month - 1) // 3
        start = datetime(today.year, q_idx * 3 + 1, 1)
        return start, today, f"Q{q_idx + 1} {today.year}"
    if period_label == "Last Year":
        return datetime(today.year - 1, 1, 1), datetime(today.year - 1, 12, 31), f"FY {today.year - 1}"
    if period_label == "Last 90 Days":
        return today - timedelta(days=90), today, "Last 90 Days"
    if period_label == "Custom Range":
        if custom_start is None or custom_end is None:
            return None, None, "Custom Range"
        s = datetime.combine(custom_start, datetime.min.time()) if hasattr(custom_start, "year") else custom_start
        e = datetime.combine(custom_end, datetime.min.time()) if hasattr(custom_end, "year") else custom_end
        return s, e, f"{s.strftime('%b %d, %Y')} – {e.strftime('%b %d, %Y')}"
    return None, None, period_label
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-compute_comparison_bounds"></a> `compute_comparison_bounds` — L7137–L7157

```python
def compute_comparison_bounds(bounds, compare_mode):
    """Given a (start, end, label) tuple and 'off'/'prior'/'yoy', return the comparison window."""
    start, end, _ = bounds
    if compare_mode == "off" or compare_mode is None:
        return None
    if start is None or end is None:
        return None  # Can't compare against "All Time"
    span_days = (end - start).days
    if compare_mode == "prior":
        c_end = start - timedelta(days=1)
        c_start = c_end - timedelta(days=span_days)
        return c_start, c_end, f"Prior {span_days + 1}d"
    if compare_mode == "yoy":
        try:
            c_start = start.replace(year=start.year - 1)
            c_end = end.replace(year=end.year - 1)
        except ValueError:  # Feb 29 edge case
            c_start = start - timedelta(days=365)
            c_end = end - timedelta(days=365)
        return c_start, c_end, f"{c_start.year}"
    return None
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-_filter_df_by_date"></a> `_filter_df_by_date` — L7160–L7170

```python
def _filter_df_by_date(df, date_col, bounds):
    """Return df filtered to the bounds window; no-op if bounds start/end are None."""
    if df is None or df.empty or date_col not in df.columns:
        return df if df is not None else pd.DataFrame()
    start, end, _ = bounds if bounds else (None, None, "")
    out = df
    if start is not None:
        out = out[out[date_col] >= start]
    if end is not None:
        out = out[out[date_col] <= end]
    return out
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-compute_account_kpis"></a> `compute_account_kpis` — L7173–L7246

```python
def compute_account_kpis(customers, bounds, sales_orders_df, invoices_df, deals_df):
    """Return a dict of KPI metrics for a list of customer names within the period bounds."""
    result = {
        "revenue": 0.0,
        "pipeline": 0.0,
        "open_ar": 0.0,
        "last_order_date": None,
        "most_recent_child": None,
        "days_since_last_order": None,
        "avg_order_value": 0.0,
        "order_count": 0,
        "deals_won_amt": 0.0,
        "deals_won_count": 0,
    }
    if not customers:
        return result

    # Revenue + avg order value from invoices within bounds
    if invoices_df is not None and not invoices_df.empty and "Corrected Customer" in invoices_df.columns:
        inv = invoices_df[invoices_df["Corrected Customer"].isin(customers)]
        if not inv.empty:
            inv_p = _filter_df_by_date(inv, "Date", bounds)
            if not inv_p.empty and "Amount" in inv_p.columns:
                result["revenue"] = float(inv_p["Amount"].sum() or 0)
                if "SO Number" in inv_p.columns:
                    unique_so = inv_p["SO Number"].dropna().nunique()
                    result["order_count"] = int(unique_so)
                    result["avg_order_value"] = (
                        result["revenue"] / unique_so if unique_so else 0.0
                    )
            # Open AR is NOT period-filtered (balance as-of now)
            if "Status" in inv.columns and "Amount Remaining" in inv.columns:
                open_inv = inv[inv["Status"].str.strip().str.lower() == "open"]
                result["open_ar"] = float(open_inv["Amount Remaining"].sum() or 0)

    # Last order date — period-filtered
    if sales_orders_df is not None and not sales_orders_df.empty \
            and "Corrected Customer Name" in sales_orders_df.columns \
            and "Order Start Date" in sales_orders_df.columns:
        so = sales_orders_df[sales_orders_df["Corrected Customer Name"].isin(customers)]
        so_p = _filter_df_by_date(so, "Order Start Date", bounds).dropna(subset=["Order Start Date"])
        if not so_p.empty:
            idx = so_p["Order Start Date"].idxmax()
            result["last_order_date"] = so_p.loc[idx, "Order Start Date"]
            result["most_recent_child"] = so_p.loc[idx, "Corrected Customer Name"]
            try:
                today = datetime.now()
                result["days_since_last_order"] = (
                    today - pd.Timestamp(result["last_order_date"]).to_pydatetime()
                ).days
            except Exception:
                pass

    # Pipeline (open deals, not period-filtered) + Deals Won (period-filtered on Close Date)
    if deals_df is not None and not deals_df.empty:
        match = pd.Series(False, index=deals_df.index)
        if "Company Name" in deals_df.columns:
            match = match | deals_df["Company Name"].isin(customers)
        if "Company Name 2" in deals_df.columns:
            match = match | deals_df["Company Name 2"].isin(customers)
        matched = deals_df[match]
        if not matched.empty and "Close Status" in matched.columns:
            cs = matched["Close Status"].fillna("").astype(str).str.strip().str.lower()
            open_deals = matched[~cs.isin(["won", "lost", "closed won", "closed lost"])]
            if not open_deals.empty and "Amount" in open_deals.columns:
                result["pipeline"] = float(open_deals["Amount"].sum() or 0)
            won = matched[cs.isin(["won", "closed won"])]
            if not won.empty:
                won_p = _filter_df_by_date(won, "Close Date", bounds) if "Close Date" in won.columns else won
                if "Amount" in won_p.columns:
                    result["deals_won_amt"] = float(won_p["Amount"].sum() or 0)
                result["deals_won_count"] = int(len(won_p))

    return result
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-build_customers_export_tuples"></a> `build_customers_export_tuples` — L7249–L7299

```python
def build_customers_export_tuples(customers, sales_orders_df, invoices_df, deals_df, bounds,
                                  invoice_line_items_df=None, ncr_df=None):
    """Build the 6-tuple list expected by generate_qbr_html / generate_combined_qbr_html /
    generate_combined_summary_html.

    Each tuple: (customer_name, orders, invoices, deals, line_items, ncrs) — matches the
    legacy QBR Generator's ``all_customers_data`` format exactly.
    """
    tuples = []
    start, end, _ = bounds if bounds else (None, None, "")
    for c in customers:
        c_orders = pd.DataFrame()
        c_invoices = pd.DataFrame()
        c_deals = pd.DataFrame()
        c_line_items = pd.DataFrame()
        c_ncrs = pd.DataFrame()

        if sales_orders_df is not None and not sales_orders_df.empty \
                and "Corrected Customer Name" in sales_orders_df.columns:
            c_orders = sales_orders_df[sales_orders_df["Corrected Customer Name"] == c].copy()
            if start is not None and "Order Start Date" in c_orders.columns:
                c_orders = c_orders[(c_orders["Order Start Date"] >= start) & (c_orders["Order Start Date"] <= end)]

        if invoices_df is not None and not invoices_df.empty \
                and "Corrected Customer" in invoices_df.columns:
            c_invoices = invoices_df[invoices_df["Corrected Customer"] == c].copy()
            if start is not None and "Date" in c_invoices.columns:
                c_invoices = c_invoices[(c_invoices["Date"] >= start) & (c_invoices["Date"] <= end)]

        if deals_df is not None and not deals_df.empty:
            m = pd.Series(False, index=deals_df.index)
            if "Company Name" in deals_df.columns:
                m = m | (deals_df["Company Name"] == c)
            if "Company Name 2" in deals_df.columns:
                m = m | (deals_df["Company Name 2"] == c)
            c_deals = deals_df[m].copy()

        if invoice_line_items_df is not None and not invoice_line_items_df.empty \
                and "Correct Customer" in invoice_line_items_df.columns:
            c_line_items = invoice_line_items_df[invoice_line_items_df["Correct Customer"] == c].copy()
            if start is not None and "Date" in c_line_items.columns:
                c_line_items = c_line_items[(c_line_items["Date"] >= start) & (c_line_items["Date"] <= end)]

        if ncr_df is not None and not ncr_df.empty:
            if "Matched Customer" in ncr_df.columns:
                c_ncrs = ncr_df[ncr_df["Matched Customer"] == c].copy()
            if c_ncrs.empty and "Corrected Customer Name" in ncr_df.columns:
                c_ncrs = ncr_df[ncr_df["Corrected Customer Name"] == c].copy()

        tuples.append((c, c_orders, c_invoices, c_deals, c_line_items, c_ncrs))
    return tuples
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-_fmt_money"></a> `_fmt_money` — L7302–L7311

```python
def _fmt_money(v, compact=False):
    if v is None or pd.isna(v):
        return "—"
    v = float(v)
    if compact:
        if abs(v) >= 1_000_000:
            return f"${v / 1_000_000:.1f}M"
        if abs(v) >= 1_000:
            return f"${v / 1_000:.0f}K"
    return f"${v:,.0f}"
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-_fmt_delta"></a> `_fmt_delta` — L7314–L7325

```python
def _fmt_delta(current, compare):
    if compare is None or compare == 0:
        return ""
    delta = current - compare
    pct = (delta / abs(compare)) * 100 if compare else 0
    sign = "+" if delta >= 0 else ""
    color = "#10b981" if delta >= 0 else "#ef4444"
    arrow = "▲" if delta >= 0 else "▼"
    return (
        f"<div style='margin-top:6px;font-size:0.78rem;color:{color};font-weight:600;'>"
        f"{arrow} {sign}{_fmt_money(delta, compact=True)} ({sign}{pct:.1f}%)</div>"
    )
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-_kpi_tile"></a> `_kpi_tile` — L7328–L7338

```python
def _kpi_tile(label, value_html, delta_html=""):
    return f"""
    <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                border: 1px solid #334155; border-radius: 12px; padding: 18px 20px;
                min-height: 120px;">
      <div style="color:#94a3b8;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;
                  font-weight:600;margin-bottom:8px;">{label}</div>
      <div style="color:#f8fafc;font-size:1.6rem;font-weight:700;line-height:1.1;">{value_html}</div>
      {delta_html}
    </div>
    """
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-generate_sku_order_history_xlsx"></a> `generate_sku_order_history_xlsx` — L8440–L8651

```python
def generate_sku_order_history_xlsx(customer_name, sku_histories, date_label):
    """
    Generate Excel file with SKU order history in wide format.
    Format: SKU | Description | First Order Date | Quantity | Second Order Date | Quantity | ...
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from io import BytesIO
    
    wb = Workbook()
    ws = wb.active
    ws.title = "SKU Order History"
    
    # Styles
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill("solid", fgColor="1e40af")
    data_font = Font(size=10)
    date_font = Font(size=10, color="1e40af")
    qty_font = Font(size=10, bold=True)
    border = Border(
        left=Side(style='thin', color='e2e8f0'),
        right=Side(style='thin', color='e2e8f0'),
        top=Side(style='thin', color='e2e8f0'),
        bottom=Side(style='thin', color='e2e8f0')
    )
    center_align = Alignment(horizontal='center', vertical='center')
    left_align = Alignment(horizontal='left', vertical='center')
    
    # Find max number of orders across all SKUs
    max_orders = max(len(s['orders']) for s in sku_histories) if sku_histories else 1
    
    # Title row
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=5 + max_orders * 2)
    title_cell = ws.cell(row=1, column=1, value=f"SKU Order History - {customer_name}")
    title_cell.font = Font(bold=True, size=14, color="1e40af")
    title_cell.alignment = Alignment(horizontal='left', vertical='center')
    ws.row_dimensions[1].height = 25
    
    # Subtitle row
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=5 + max_orders * 2)
    subtitle_cell = ws.cell(row=2, column=1, value=f"Period: {date_label} | Generated: {datetime.now().strftime('%B %d, %Y')}")
    subtitle_cell.font = Font(size=10, color="64748b")
    subtitle_cell.alignment = Alignment(horizontal='left', vertical='center')
    ws.row_dimensions[2].height = 20
    
    # Header row
    header_row = 4
    headers = ['SKU', 'Description', 'Invoices', 'Total Orders', 'Total Qty']
    
    # Add order columns dynamically
    ordinal_names = ['First', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth', 'Seventh', 'Eighth', 'Ninth', 'Tenth']
    for i in range(max_orders):
        ordinal = ordinal_names[i] if i < len(ordinal_names) else f"Order {i+1}"
        headers.append(f"{ordinal} Order Date")
        headers.append("Quantity")
    
    # Add prediction columns
    headers.extend(['Avg Days Between', 'Predicted Next', 'Status'])
    
    # Write headers
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = border
    
    ws.row_dimensions[header_row].height = 22
    
    # Write data rows
    for row_idx, sku_data in enumerate(sku_histories, start=header_row + 1):
        col = 1
        
        # SKU
        cell = ws.cell(row=row_idx, column=col, value=sku_data['sku'])
        cell.font = Font(size=10, bold=True, name='Consolas')
        cell.alignment = left_align
        cell.border = border
        col += 1
        
        # Description
        cell = ws.cell(row=row_idx, column=col, value=sku_data['display_name'] or '')
        cell.font = data_font
        cell.alignment = left_align
        cell.border = border
        col += 1
        
        # Invoices (comma-separated list)
        invoices_str = ', '.join(sku_data.get('invoices', []))
        cell = ws.cell(row=row_idx, column=col, value=invoices_str)
        cell.font = Font(size=9, color="64748b")
        cell.alignment = left_align
        cell.border = border
        col += 1
        
        # Total Orders
        cell = ws.cell(row=row_idx, column=col, value=sku_data['num_orders'])
        cell.font = data_font
        cell.alignment = center_align
        cell.border = border
        col += 1
        
        # Total Qty
        cell = ws.cell(row=row_idx, column=col, value=sku_data['total_qty'])
        cell.font = qty_font
        cell.number_format = '#,##0'
        cell.alignment = center_align
        cell.border = border
        col += 1
        
        # Order dates and quantities
        for i in range(max_orders):
            if i < len(sku_data['orders']):
                order = sku_data['orders'][i]
                # Date
                cell = ws.cell(row=row_idx, column=col, value=order['date'])
                cell.font = date_font
                cell.number_format = 'YYYY-MM-DD'
                cell.alignment = center_align
                cell.border = border
                col += 1
                
                # Quantity
                cell = ws.cell(row=row_idx, column=col, value=order['qty'])
                cell.font = qty_font
                cell.number_format = '#,##0'
                cell.alignment = center_align
                cell.border = border
                col += 1
            else:
                # Empty cells for orders that don't exist
                for _ in range(2):
                    cell = ws.cell(row=row_idx, column=col, value='')
                    cell.border = border
                    col += 1
        
        # Avg Days Between
        cell = ws.cell(row=row_idx, column=col, value=round(sku_data['avg_days']) if sku_data['avg_days'] else '')
        cell.font = data_font
        cell.alignment = center_align
        cell.border = border
        col += 1
        
        # Predicted Next
        if sku_data['predicted_next']:
            cell = ws.cell(row=row_idx, column=col, value=sku_data['predicted_next'])
            cell.number_format = 'YYYY-MM-DD'
        else:
            cell = ws.cell(row=row_idx, column=col, value='')
        cell.font = data_font
        cell.alignment = center_align
        cell.border = border
        col += 1
        
        # Status
        days_until = sku_data['days_until']
        if days_until is not None:
            if days_until < -14:
                status = f"Overdue ({abs(days_until)}d)"
            elif days_until < 0:
                status = f"Past ({abs(days_until)}d)"
            elif days_until <= 30:
                status = f"Due Soon ({days_until}d)"
            else:
                status = f"Upcoming ({days_until}d)"
        else:
            status = "N/A"
        
        cell = ws.cell(row=row_idx, column=col, value=status)
        cell.font = data_font
        cell.alignment = center_align
        cell.border = border
        
        # Color code status
        if days_until is not None:
            if days_until < -14:
                cell.font = Font(size=10, bold=True, color="dc2626")
            elif days_until < 0:
                cell.font = Font(size=10, bold=True, color="d97706")
            elif days_until <= 30:
                cell.font = Font(size=10, bold=True, color="059669")
            else:
                cell.font = Font(size=10, color="2563eb")
    
    # Auto-adjust column widths
    ws.column_dimensions['A'].width = 22  # SKU
    ws.column_dimensions['B'].width = 45  # Description
    ws.column_dimensions['C'].width = 35  # Invoices
    ws.column_dimensions['D'].width = 12  # Total Orders
    ws.column_dimensions['E'].width = 12  # Total Qty
    
    # Order columns start at F (index 6)
    col_idx = 6
    for i in range(max_orders):
        ws.column_dimensions[get_column_letter(col_idx)].width = 14  # Date
        ws.column_dimensions[get_column_letter(col_idx + 1)].width = 12  # Qty
        col_idx += 2
    
    # Prediction columns
    ws.column_dimensions[get_column_letter(col_idx)].width = 14  # Avg Days
    ws.column_dimensions[get_column_letter(col_idx + 1)].width = 14  # Predicted
    ws.column_dimensions[get_column_letter(col_idx + 2)].width = 16  # Status
    
    # Freeze header row
    ws.freeze_panes = 'A5'
    
    # Save to bytes
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-generate_sku_order_history_text"></a> `generate_sku_order_history_text` — L9112–L9168

```python
def generate_sku_order_history_text(customer_name, sku_histories):
    """Generate a plain text summary for easy copy/paste"""
    
    lines = []
    lines.append(f"SKU ORDER HISTORY REPORT")
    lines.append(f"Customer: {customer_name}")
    lines.append(f"Generated: {datetime.now().strftime('%B %d, %Y')}")
    lines.append("=" * 60)
    lines.append("")
    
    ordinal_map = {1: "First", 2: "Second", 3: "Third", 4: "Fourth", 5: "Fifth", 
                   6: "Sixth", 7: "Seventh", 8: "Eighth", 9: "Ninth", 10: "Tenth"}
    
    for sku_data in sku_histories:
        sku = sku_data['sku']
        display_name = sku_data['display_name']
        orders = sku_data['orders']
        avg_days = sku_data['avg_days']
        predicted_next = sku_data['predicted_next']
        days_until = sku_data['days_until']
        
        # Build narrative
        sku_label = f"{sku}" + (f" ({display_name})" if display_name else "")
        
        order_parts = []
        for i, order in enumerate(orders):
            ordinal = ordinal_map.get(i + 1, f"Order #{i + 1}")
            date_str = order['date'].strftime('%m/%d/%y')
            qty_str = f"{order['qty']:,.0f}" if order['qty'] else "N/A"
            order_parts.append(f"{ordinal} order on {date_str} for {qty_str}")
        
        order_narrative = ". ".join(order_parts) + "."
        
        # Status
        if days_until is not None and days_until < 0:
            status = f"OVERDUE by {abs(days_until)} days"
        elif days_until is not None and days_until <= 30:
            status = f"Due in {days_until} days"
        elif predicted_next:
            status = f"Next predicted: {predicted_next.strftime('%m/%d/%y')}"
        else:
            status = ""
        
        cadence = f"Avg cadence: {avg_days:.0f} days." if avg_days else ""
        
        lines.append(f"{sku_label}")
        lines.append(f"  {order_narrative}")
        if cadence:
            lines.append(f"  {cadence}")
        if status:
            lines.append(f"  → {status}")
        lines.append("")
    
    lines.append("=" * 60)
    lines.append("Prepared by Calyx Containers")
    
    return "\n".join(lines)
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-process_deals_line_items"></a> `process_deals_line_items` — L10359–L10402

```python
def process_deals_line_items(df):
    """Process and clean Deals Line Item data"""
    if df.empty:
        return df
    
    # Remove duplicate columns
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]
    
    # Clean numeric data
    if 'Amount' in df.columns:
        df['Amount'] = df['Amount'].apply(clean_numeric)
    if 'Quantity' in df.columns:
        df['Quantity'] = df['Quantity'].apply(clean_numeric)
    
    # Clean date data
    if 'Create Date' in df.columns:
        df['Create Date'] = pd.to_datetime(df['Create Date'], errors='coerce')
    if 'Close Date' in df.columns:
        df['Close Date'] = pd.to_datetime(df['Close Date'], errors='coerce')
    
    # Create Deal Owner by combining First Name + Last Name
    if 'Deal Owner First Name' in df.columns and 'Deal Owner Last Name' in df.columns:
        df['Deal Owner'] = (
            df['Deal Owner First Name'].fillna('').astype(str).str.strip() + ' ' + 
            df['Deal Owner Last Name'].fillna('').astype(str).str.strip()
        ).str.strip()
    
    # Clean text fields
    for col in ['SKU', 'SKU Description', 'Deal Name', 'Deal Stage', 'Pipeline', 
                'Deal Type', 'Close Status', 'Deal Close Status', 'Company Name', 
                'Primary Associated Company']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace('nan', '')
            df[col] = df[col].str.replace('\n', '', regex=False).str.replace('\r', '', regex=False)
    
    # Parse boolean fields
    if 'Is Closed Won' in df.columns:
        df['Is Closed Won'] = df['Is Closed Won'].astype(str).str.lower().isin(['true', 'yes', '1'])
    if 'Is closed lost' in df.columns:
        df['Is closed lost'] = df['Is closed lost'].astype(str).str.lower().isin(['true', 'yes', '1'])
    
    return df
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-categorize_sku_for_pipeline"></a> `categorize_sku_for_pipeline` — L10405–L10413

```python
def categorize_sku_for_pipeline(sku, description):
    """
    Categorize SKU for pipeline data using the same logic as QBR.
    Uses the existing categorize_product function with SKU as item_name and description as item_description.
    Returns (category, sub_category) tuple.
    """
    # Use the existing categorize_product function
    category, sub_category, _ = categorize_product(sku, description, "")
    return category, sub_category
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-filter_calyx_cure_skus"></a> `filter_calyx_cure_skus` — L11533–L11558

```python
def filter_calyx_cure_skus(df, sku_column='SKU'):
    """Filter dataframe to only include Calyx Cure SKUs."""
    if df.empty or sku_column not in df.columns:
        return pd.DataFrame()
    
    df = df.copy()
    df['_sku_normalized'] = df[sku_column].astype(str).str.upper().str.strip()
    
    # Check for exact matches first
    exact_matches = df[df['_sku_normalized'].isin(CALYX_CURE_CONFIG['TARGET_SKUS'])]
    
    if not exact_matches.empty:
        return exact_matches.drop(columns=['_sku_normalized'])
    
    # Try partial matches
    partial_matches = []
    for sku in CALYX_CURE_CONFIG['TARGET_SKUS']:
        matches = df[df['_sku_normalized'].str.contains(sku, na=False)]
        if not matches.empty:
            partial_matches.append(matches)
    
    if partial_matches:
        result = pd.concat(partial_matches, ignore_index=True).drop_duplicates()
        return result.drop(columns=['_sku_normalized'])
    
    return pd.DataFrame()
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-identify_calyx_cure_sku"></a> `identify_calyx_cure_sku` — L11561–L11572

```python
def identify_calyx_cure_sku(item_value):
    """Identify which Calyx Cure SKU an item belongs to."""
    if pd.isna(item_value):
        return None
    
    item_str = str(item_value).upper().strip()
    
    for sku in CALYX_CURE_CONFIG['TARGET_SKUS']:
        if sku in item_str or item_str == sku:
            return sku
    
    return None
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-calculate_cure_pipeline_metrics"></a> `calculate_cure_pipeline_metrics` — L11575–L11640

```python
def calculate_cure_pipeline_metrics(deals_line_items_df):
    """Calculate pipeline metrics from Deals Line Item data for Calyx Cure."""
    metrics = {}
    
    # Initialize metrics for all target SKUs
    for sku in CALYX_CURE_CONFIG['TARGET_SKUS']:
        metrics[sku] = {
            'opportunity': {'qty': 0, 'deals': []},
            'best_case': {'qty': 0, 'deals': []},
            'expect': {'qty': 0, 'deals': []},
            'commit': {'qty': 0, 'deals': []},
            'total': 0
        }
    
    if deals_line_items_df.empty:
        return metrics
    
    # Filter to Calyx Cure SKUs
    sku_col = 'SKU' if 'SKU' in deals_line_items_df.columns else 'Item'
    cure_deals = filter_calyx_cure_skus(deals_line_items_df, sku_col)
    
    if cure_deals.empty:
        return metrics
    
    # Add matched SKU column
    cure_deals = cure_deals.copy()
    cure_deals['Matched SKU'] = cure_deals[sku_col].apply(identify_calyx_cure_sku)
    cure_deals = cure_deals[cure_deals['Matched SKU'].notna()]
    
    # Filter by date and close status
    if 'Close Date' in cure_deals.columns:
        cure_deals['Close Date'] = pd.to_datetime(cure_deals['Close Date'], errors='coerce')
        cure_deals = cure_deals[cure_deals['Close Date'] >= CALYX_CURE_CONFIG['MIN_CLOSE_DATE']]
    
    if 'Close Status' in cure_deals.columns:
        cure_deals = cure_deals[cure_deals['Close Status'].isin(CALYX_CURE_CONFIG['VALID_CLOSE_STATUSES'])]
    
    # Ensure Quantity column exists
    qty_col = 'Quantity' if 'Quantity' in cure_deals.columns else 'Qty'
    if qty_col not in cure_deals.columns:
        return metrics
    
    # Calculate metrics per SKU
    for _, row in cure_deals.iterrows():
        sku = row['Matched SKU']
        if sku not in metrics:
            continue
        
        qty = float(row.get(qty_col, 0) or 0)
        status = str(row.get('Close Status', '')).lower().replace(' ', '_')
        
        deal_info = {
            'deal_name': row.get('Deal Name', ''),
            'company': row.get('Company Name', ''),
            'quantity': qty,
            'close_date': row.get('Close Date'),
            'deal_owner': row.get('Deal Owner', '')
        }
        
        if status in metrics[sku]:
            metrics[sku][status]['qty'] += qty
            metrics[sku][status]['deals'].append(deal_info)
        
        metrics[sku]['total'] += qty
    
    return metrics
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-calculate_cure_order_metrics"></a> `calculate_cure_order_metrics` — L11643–L11701

```python
def calculate_cure_order_metrics(sales_order_line_items_df):
    """Calculate active order metrics from Sales Order Line Items for Calyx Cure."""
    metrics = {}
    
    # Initialize metrics for all target SKUs
    for sku in CALYX_CURE_CONFIG['TARGET_SKUS']:
        metrics[sku] = {
            'pending_approval': {'qty': 0, 'amount': 0},
            'pending_fulfillment': {'qty': 0, 'amount': 0},
            'total_qty': 0,
            'total_amount': 0
        }
    
    if sales_order_line_items_df.empty:
        return metrics
    
    # Filter to Calyx Cure SKUs
    item_col = 'Item' if 'Item' in sales_order_line_items_df.columns else 'SKU'
    cure_orders = filter_calyx_cure_skus(sales_order_line_items_df, item_col)
    
    if cure_orders.empty:
        return metrics
    
    # Filter by status
    if 'Status' in cure_orders.columns:
        cure_orders = cure_orders[cure_orders['Status'].isin(CALYX_CURE_CONFIG['VALID_ORDER_STATUSES'])]
    
    # Add matched SKU column
    cure_orders = cure_orders.copy()
    cure_orders['Matched SKU'] = cure_orders[item_col].apply(identify_calyx_cure_sku)
    cure_orders = cure_orders[cure_orders['Matched SKU'].notna()]
    
    # Calculate Qty Remaining
    if 'Qty Remaining' not in cure_orders.columns:
        qty_ordered = cure_orders.get('Quantity Ordered', cure_orders.get('Quantity', 0))
        qty_fulfilled = cure_orders.get('Quantity Fulfilled', 0)
        cure_orders['Qty Remaining'] = pd.to_numeric(qty_ordered, errors='coerce').fillna(0) - pd.to_numeric(qty_fulfilled, errors='coerce').fillna(0)
    
    # Calculate metrics per SKU
    for _, row in cure_orders.iterrows():
        sku = row['Matched SKU']
        if sku not in metrics:
            continue
        
        qty = float(row.get('Qty Remaining', 0) or 0)
        amount = float(row.get('Amount', 0) or 0)
        status = str(row.get('Status', '')).lower().replace(' ', '_')
        
        if status == 'pending_approval':
            metrics[sku]['pending_approval']['qty'] += qty
            metrics[sku]['pending_approval']['amount'] += amount
        elif status == 'pending_fulfillment':
            metrics[sku]['pending_fulfillment']['qty'] += qty
            metrics[sku]['pending_fulfillment']['amount'] += amount
        
        metrics[sku]['total_qty'] += qty
        metrics[sku]['total_amount'] += amount
    
    return metrics
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-calculate_cure_historical_demand"></a> `calculate_cure_historical_demand` — L11704–L11753

```python
def calculate_cure_historical_demand(invoice_line_items_df, months=12):
    """Calculate historical demand metrics from Invoice Line Items for Calyx Cure."""
    metrics = {}
    
    # Initialize metrics for all target SKUs
    for sku in CALYX_CURE_CONFIG['TARGET_SKUS']:
        metrics[sku] = {
            'total_qty': 0,
            'total_revenue': 0,
            'monthly_avg': 0,
            'order_count': 0
        }
    
    if invoice_line_items_df.empty or 'Date' not in invoice_line_items_df.columns:
        return metrics
    
    # Filter to Calyx Cure SKUs
    item_col = 'Item' if 'Item' in invoice_line_items_df.columns else 'SKU'
    cure_invoices = filter_calyx_cure_skus(invoice_line_items_df, item_col)
    
    if cure_invoices.empty:
        return metrics
    
    # Filter to last N months
    cure_invoices = cure_invoices.copy()
    cure_invoices['Date'] = pd.to_datetime(cure_invoices['Date'], errors='coerce')
    cutoff_date = datetime.now() - timedelta(days=months * 30)
    cure_invoices = cure_invoices[cure_invoices['Date'] >= cutoff_date]
    
    # Add matched SKU column
    cure_invoices['Matched SKU'] = cure_invoices[item_col].apply(identify_calyx_cure_sku)
    cure_invoices = cure_invoices[cure_invoices['Matched SKU'].notna()]
    
    # Calculate metrics per SKU
    for sku in CALYX_CURE_CONFIG['TARGET_SKUS']:
        sku_data = cure_invoices[cure_invoices['Matched SKU'] == sku]
        
        if not sku_data.empty:
            total_qty = sku_data['Quantity'].sum() if 'Quantity' in sku_data.columns else 0
            total_revenue = sku_data['Amount'].sum() if 'Amount' in sku_data.columns else 0
            order_count = len(sku_data)
            
            metrics[sku] = {
                'total_qty': total_qty,
                'total_revenue': total_revenue,
                'monthly_avg': total_qty / months,
                'order_count': order_count
            }
    
    return metrics
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-parse_period_selection"></a> `parse_period_selection` — L13254–L13282

```python
def parse_period_selection(period_type):
    """Parse period selection string into start date, end date, and label"""
    today = datetime.now()
    
    if period_type == "Q1 2026 YTD":
        return datetime(2026, 1, 1), today, "Q1 2026 YTD"
    elif period_type == "Q1 2025":
        return datetime(2025, 1, 1), datetime(2025, 3, 31), "Q1 2025"
    elif period_type == "Q2 2025":
        return datetime(2025, 4, 1), datetime(2025, 6, 30), "Q2 2025"
    elif period_type == "Q3 2025":
        return datetime(2025, 7, 1), datetime(2025, 9, 30), "Q3 2025"
    elif period_type == "Q4 2025":
        return datetime(2025, 10, 1), datetime(2025, 12, 31), "Q4 2025"
    elif period_type == "Q1 2024":
        return datetime(2024, 1, 1), datetime(2024, 3, 31), "Q1 2024"
    elif period_type == "Q2 2024":
        return datetime(2024, 4, 1), datetime(2024, 6, 30), "Q2 2024"
    elif period_type == "Q3 2024":
        return datetime(2024, 7, 1), datetime(2024, 9, 30), "Q3 2024"
    elif period_type == "Q4 2024":
        return datetime(2024, 10, 1), datetime(2024, 12, 31), "Q4 2024"
    elif period_type == "Full Year 2024":
        return datetime(2024, 1, 1), datetime(2024, 12, 31), "Full Year 2024"
    elif period_type == "Full Year 2025":
        return datetime(2025, 1, 1), datetime(2025, 12, 31), "Full Year 2025"
    else:
        # Default to Q1 2025
        return datetime(2025, 1, 1), datetime(2025, 3, 31), "Q1 2025"
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-calculate_period_metrics"></a> `calculate_period_metrics` — L13285–L13333

```python
def calculate_period_metrics(df, customer_col):
    """Calculate all metrics for a period from invoice line items"""
    
    if df.empty:
        return {
            'total_revenue': 0,
            'order_count': 0,
            'customer_count': 0,
            'category_breakdown': {},
            'customer_revenue': {},
            'product_revenue': {}
        }
    
    # Total revenue
    total_revenue = df['Amount'].sum() if 'Amount' in df.columns else 0
    
    # Order count (unique document numbers)
    order_count = df['Document Number'].nunique() if 'Document Number' in df.columns else 0
    
    # Customer count
    customer_count = df[customer_col].nunique() if customer_col in df.columns else 0
    
    # Category breakdown (using Parent Category for rollup)
    category_col = 'Parent Category' if 'Parent Category' in df.columns else 'Product Category'
    category_breakdown = {}
    if category_col in df.columns and 'Amount' in df.columns:
        cat_df = df.groupby(category_col)['Amount'].sum()
        category_breakdown = cat_df.to_dict()
    
    # Customer revenue
    customer_revenue = {}
    if customer_col in df.columns and 'Amount' in df.columns:
        cust_df = df.groupby(customer_col)['Amount'].sum()
        customer_revenue = cust_df.to_dict()
    
    # Product revenue (by SKU)
    product_revenue = {}
    if 'Item' in df.columns and 'Amount' in df.columns:
        prod_df = df.groupby('Item')['Amount'].sum()
        product_revenue = prod_df.to_dict()
    
    return {
        'total_revenue': total_revenue,
        'order_count': order_count,
        'customer_count': customer_count,
        'category_breakdown': category_breakdown,
        'customer_revenue': customer_revenue,
        'product_revenue': product_revenue
    }
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-embed_chart"></a> `embed_chart` — L303–L320

```python
def embed_chart(fig, chart_key):
        """Try to embed chart as image, fall back to interactive HTML"""
        nonlocal charts_generated
        if fig is None:
            return
        
        # First try static image (best for PDF)
        img_b64 = fig_to_base64(fig)
        if img_b64:
            charts_html[chart_key] = f'<div class="chart-container"><img src="data:image/png;base64,{img_b64}"></div>'
            charts_generated += 1
            return
        
        # Fall back to interactive HTML embed
        html_embed = fig_to_html_embed(fig)
        if html_embed:
            charts_html[chart_key] = f'<div class="chart-container">{html_embed}</div>'
            charts_generated += 1
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-get_customer_friendly_status"></a> `get_customer_friendly_status` — L958–L965

```python
def get_customer_friendly_status(status):
        status_map = {
            'Commit': 'Confirmed',      # Basically a done deal
            'Expect': 'Likely',         # High confidence
            'Best Case': 'Tentative',   # Medium confidence, still being finalized
            'Opportunity': 'In Discussion'  # Early stage conversations
        }
        return status_map.get(status, status)
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-get_customer_friendly_status"></a> `get_customer_friendly_status` — L5265–L5272

```python
def get_customer_friendly_status(status):
        status_map = {
            'Commit': 'Confirmed',
            'Expect': 'Likely',
            'Best Case': 'Tentative',
            'Opportunity': 'In Discussion'
        }
        return status_map.get(status, status)
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-get_unified_category"></a> `get_unified_category` — L5833–L5872

```python
def get_unified_category(row):
        cat = row.get('Product Category', 'Other')
        subcat = row.get('Product Sub-Category', '')
        component = row.get('Component Type', '')
        
        # For categories that are already complete products
        if cat in ['Tubes', 'Boxes', 'Flexpack', 'Calyx Cure', 'Fees & Adjustments', 'Other']:
            return cat
        
        # For Drams - unify base + lid + labels
        if cat == 'Drams':
            # Extract size (15D, 25D, 45D, 145D)
            size_match = re.search(r'(\d+D)', str(subcat))
            if size_match:
                return f"Drams ({size_match.group(1)})"
            return 'Drams'
        
        # For Concentrates - unify jar + lid
        if cat == 'Concentrates':
            size_match = re.search(r'(4mL|7mL)', str(subcat))
            if size_match:
                return f"Concentrates ({size_match.group(1)})"
            # Universal lids without clear size match
            if 'lid' in str(subcat).lower() or 'universal' in str(subcat).lower():
                return 'Concentrate Lids'
            return 'Concentrates'
        
        # For Calyx Jar
        if cat == 'Calyx Jar':
            return 'Calyx Jar'
        
        # For accessories - keep unified as Dram Accessories (shows in sub-breakdown)
        if cat == 'Dram Accessories':
            return 'Dram Accessories'
        
        # For labels
        if cat == 'Non-Core Labels':
            return 'Non-Core Labels'
        
        return cat
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-get_parent_category"></a> `get_parent_category` — L5878–L5893

```python
def get_parent_category(unified_cat):
        if pd.isna(unified_cat):
            return 'Other'
        
        unified = str(unified_cat)
        
        # Roll up Drams (25D, 45D, 15D, 145D) and Dram Accessories → Drams
        if unified.startswith('Drams') or unified == 'Dram Accessories':
            return 'Drams'
        
        # Roll up Concentrates (4mL, 7mL) and Concentrate Lids → Concentrates
        if unified.startswith('Concentrates') or unified == 'Concentrate Lids':
            return 'Concentrates'
        
        # Everything else stays as-is
        return unified
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-status_indicator"></a> `status_indicator` — L6648–L6658

```python
def status_indicator(days):
        if pd.isna(days):
            return "⚪ Insufficient Data"
        elif days < -14:
            return f"🔴 Overdue ({abs(int(days))} days)"
        elif days < 0:
            return f"🟠 Slightly Past ({abs(int(days))} days)"
        elif days <= 30:
            return f"🟢 Due Soon ({int(days)} days)"
        else:
            return f"🔵 Upcoming ({int(days)} days)"
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-_d"></a> `_d` — L7603–L7604

```python
def _d(key):
        return _fmt_delta(metrics_cur[key], metrics_cmp[key]) if metrics_cmp else ""
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-filter_by_date"></a> `filter_by_date` — L9754–L9769

```python
def filter_by_date(df, date_col, start, end):
        """Filter dataframe by date column"""
        if df.empty or date_col not in df.columns:
            return df
        if start is None and end is None:
            return df
        
        df_filtered = df.copy()
        df_filtered[date_col] = pd.to_datetime(df_filtered[date_col], errors='coerce')
        
        if start is not None:
            df_filtered = df_filtered[df_filtered[date_col] >= pd.Timestamp(start)]
        if end is not None:
            df_filtered = df_filtered[df_filtered[date_col] <= pd.Timestamp(end)]
        
        return df_filtered
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-apply_dml_pairing_for_forecast"></a> `apply_dml_pairing_for_forecast` — L13695–L13752

```python
def apply_dml_pairing_for_forecast(df):
        """
        Apply DML lid pairing logic for concentrate forecasting.
        
        Logic:
        - 4mL + 7mL Glass Bases define total concentrate units
        - Universal Lid (4mL/7mL) covers some of those bases
        - DML Universal fills the deficit
        - Final concentrate qty = total bases (4mL + 7mL)
        
        Returns a modified summary with proper concentrate rollup.
        """
        if df.empty:
            return df, {}
        
        # Calculate raw quantities by subcategory
        subcat_qtys = df.groupby(['Product Category', 'Product Subcategory'])['Quantity'].sum().reset_index()
        
        # Get concentrate components
        conc_4ml_base = subcat_qtys[
            (subcat_qtys['Product Category'] == 'Concentrates') & 
            (subcat_qtys['Product Subcategory'].str.contains('4mL.*Base', case=False, regex=True))
        ]['Quantity'].sum()
        
        conc_7ml_base = subcat_qtys[
            (subcat_qtys['Product Category'] == 'Concentrates') & 
            (subcat_qtys['Product Subcategory'].str.contains('7mL.*Base', case=False, regex=True))
        ]['Quantity'].sum()
        
        conc_dedicated_lids = subcat_qtys[
            (subcat_qtys['Product Category'] == 'Concentrates') & 
            (subcat_qtys['Product Subcategory'].str.contains('Lid|Universal', case=False, regex=True))
        ]['Quantity'].sum()
        
        # Get DML Universal quantity
        dml_universal_qty = subcat_qtys[
            subcat_qtys['Product Category'] == 'DML (Universal)'
        ]['Quantity'].sum()
        
        # Calculate concentrate totals
        total_conc_bases = conc_4ml_base + conc_7ml_base
        lid_deficit = max(0, total_conc_bases - conc_dedicated_lids)
        dml_used_for_conc = min(lid_deficit, dml_universal_qty)
        dml_remaining = dml_universal_qty - dml_used_for_conc
        
        # Build pairing info dict
        pairing_info = {
            '4mL_bases': conc_4ml_base,
            '7mL_bases': conc_7ml_base,
            'total_conc_bases': total_conc_bases,
            'dedicated_lids': conc_dedicated_lids,
            'lid_deficit': lid_deficit,
            'dml_total': dml_universal_qty,
            'dml_used_for_conc': dml_used_for_conc,
            'dml_remaining': dml_remaining
        }
        
        return df, pairing_info
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-filter_concentrate_bases_only"></a> `filter_concentrate_bases_only` — L13762–L13779

```python
def filter_concentrate_bases_only(df):
        """
        For Concentrates category, only keep base SKUs (4mL/7mL Glass Base).
        This gives accurate unit counts without double-counting components.
        """
        if df.empty or 'Product Category' not in df.columns:
            return df
        
        df = df.copy()
        
        # Identify concentrate rows that are NOT bases (lids, labels, etc.)
        is_concentrate = df['Product Category'] == 'Concentrates'
        is_base = df['Product Subcategory'].str.contains('Base', case=False, na=False)
        
        # Keep: all non-concentrates + concentrate bases only
        filtered = df[~is_concentrate | (is_concentrate & is_base)]
        
        return filtered
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-aging_bucket"></a> `aging_bucket` — L2205–L2210

```python
def aging_bucket(days):
            if days <= 0: return 'Current'
            elif days <= 30: return '1-30 Days'
            elif days <= 60: return '31-60 Days'
            elif days <= 90: return '61-90 Days'
            else: return '90+ Days'
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-aging_bucket"></a> `aging_bucket` — L4910–L4920

```python
def aging_bucket(days):
            if days <= 0:
                return "Current"
            elif days <= 30:
                return "1-30 Days"
            elif days <= 60:
                return "31-60 Days"
            elif days <= 90:
                return "61-90 Days"
            else:
                return "90+ Days"
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-categorize_frequency"></a> `categorize_frequency` — L6306–L6314

```python
def categorize_frequency(occasions):
            if occasions >= 10:
                return "Core Product"
            elif occasions >= 5:
                return "Regular Product"
            elif occasions >= 2:
                return "Repeat Product"
            else:
                return "One-Time Product"
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-pattern_indicator"></a> `pattern_indicator` — L6389–L6396

```python
def pattern_indicator(pattern):
            indicators = {
                'Core Product': '🟢',
                'Regular Product': '🔵',
                'Repeat Product': '🟠',
                'One-Time Product': '⚪'
            }
            return indicators.get(pattern, '⚪')
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-extract_customer_from_ticket"></a> `extract_customer_from_ticket` — L4021–L4049

```python
def extract_customer_from_ticket(ticket_name):
                """Extract customer name from ticket formats:
                - 'NCR ### - Customer Name' (with dash)
                - 'NCR ### Customer Name' (no dash)
                - Also extracts NCR number for reference
                """
                import re
                if not ticket_name or ticket_name == '' or pd.isna(ticket_name):
                    return ''
                
                ticket_str = str(ticket_name).strip()
                
                # Pattern 1: "NCR ### - Customer Name" (with dash)
                if ' - ' in ticket_str:
                    parts = ticket_str.split(' - ', 1)
                    if len(parts) > 1:
                        customer_part = parts[1].strip()
                        # Remove any trailing issue description (after another dash or parenthetical)
                        # e.g., "Acreage (OH) Smearing" -> "Acreage (OH)"
                        return customer_part
                
                # Pattern 2: "NCR ### Customer Name" (no dash)
                # Match NCR followed by number, then capture everything after
                ncr_match = re.match(r'NCR\s*(\d+)\s+(.+)', ticket_str, re.IGNORECASE)
                if ncr_match:
                    customer_part = ncr_match.group(2).strip()
                    return customer_part
                
                return ''
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-extract_ncr_number_from_ticket"></a> `extract_ncr_number_from_ticket` — L4051–L4061

```python
def extract_ncr_number_from_ticket(ticket_name):
                """Extract NCR number from ticket name"""
                import re
                if not ticket_name or ticket_name == '' or pd.isna(ticket_name):
                    return None
                
                ticket_str = str(ticket_name).strip()
                ncr_match = re.search(r'NCR\s*(\d+)', ticket_str, re.IGNORECASE)
                if ncr_match:
                    return ncr_match.group(1)
                return None
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-match_customer"></a> `match_customer` — L4063–L4168

```python
def match_customer(row, valid_customers):
                """Match customer using priority logic with fuzzy matching"""
                from difflib import get_close_matches
                import re
                
                def normalize_for_matching(name):
                    """Normalize customer name for better matching"""
                    if not name:
                        return ''
                    name = str(name).strip()
                    # Remove common state abbreviations at the end (NY, MA, OH, NJ, PA, IL, etc.)
                    name = re.sub(r'\s+(NY|MA|OH|NJ|PA|IL|CA|CO|FL|TX|WA|OR|AZ|NV|MI|NC|SC|GA|VA|MD|CT|RI|NH|VT|ME|DE|WV|KY|TN|AL|MS|LA|AR|MO|IA|MN|WI|IN|OK|KS|NE|SD|ND|MT|WY|ID|UT|NM|HI|AK|DC)$', '', name, flags=re.IGNORECASE)
                    # Remove parenthetical state codes like (OH), (NY)
                    name = re.sub(r'\s*\([A-Z]{2}\)\s*', ' ', name)
                    # Remove trailing description words
                    name = re.sub(r'\s+(Smearing|Defect|Issue|Problem|Damage|Error).*$', '', name, flags=re.IGNORECASE)
                    return name.strip()
                
                def extract_base_company(company_name):
                    """Extract base company name from various formats:
                    - 'Parent : Child' format -> 'Parent'
                    - 'Acreage Holdings:  New York (NY)' -> 'Acreage Holdings'
                    - 'Acreage Holdings - Massachusetts (MA)' -> 'Acreage Holdings'
                    """
                    if not company_name or pd.isna(company_name):
                        return ''
                    name = str(company_name).strip()
                    
                    # Pattern 1: 'Parent : Child' - take the first part (HubSpot Company Name 2 format)
                    if ' : ' in name:
                        return name.split(' : ')[0].strip()
                    
                    # Pattern 2: 'Company:  Location (STATE)' - take before first colon
                    if ':' in name:
                        base = name.split(':')[0].strip()
                        # Only use if it looks like a company name (not a URL)
                        if '.' not in base and len(base) > 3:
                            return base
                    
                    # Pattern 3: 'Company - Location (STATE)' - take before dash if state follows
                    if ' - ' in name:
                        parts = name.split(' - ')
                        if len(parts) >= 2:
                            # Check if second part looks like a state/location
                            second = parts[1].strip()
                            if re.search(r'(Massachusetts|New York|Ohio|Pennsylvania|Illinois|New Jersey|Connecticut|Michigan|Florida|California|Colorado|Texas|Washington|Oregon|Arizona|Nevada|North Carolina|South Carolina|Georgia|Virginia|Maryland|NY|MA|OH|PA|IL|NJ|CT|MI|FL|CA|CO|TX|WA|OR|AZ|NV|NC|SC|GA|VA|MD)', second, re.IGNORECASE):
                                return parts[0].strip()
                    
                    return name
                
                def try_match(name, customers, cutoff=0.7):
                    """Try to match a name against valid customers"""
                    if not name:
                        return None
                    # Exact match first
                    if name in customers:
                        return name
                    # Normalized exact match
                    normalized = normalize_for_matching(name)
                    for cust in customers:
                        if normalize_for_matching(cust) == normalized:
                            return cust
                    # Fuzzy match
                    matches = get_close_matches(name, customers, n=1, cutoff=cutoff)
                    if matches:
                        return matches[0]
                    # Fuzzy match on normalized
                    if normalized != name:
                        matches = get_close_matches(normalized, customers, n=1, cutoff=cutoff)
                        if matches:
                            return matches[0]
                    return None
                
                # Priority 1: Company Name 2 - extract base and match
                company_name_2 = row.get('Company Name 2', '')
                if company_name_2 and company_name_2 != '' and not pd.isna(company_name_2):
                    # Extract base company name (before " : " if present)
                    base_name = extract_base_company(company_name_2)
                    if base_name:
                        match = try_match(base_name, valid_customers, cutoff=0.8)
                        if match:
                            return match
                
                # Priority 2: Company Name (try exact first, then fuzzy)
                company_name = row.get('Company Name', '')
                if company_name and company_name != '' and not pd.isna(company_name):
                    # Also extract base company from Company Name if it has " : " format
                    base_name = extract_base_company(company_name)
                    match = try_match(base_name if base_name else company_name, valid_customers, cutoff=0.7)
                    if match:
                        return match
                    # Try the raw company name with state stripped
                    normalized = normalize_for_matching(company_name)
                    match = try_match(normalized, valid_customers, cutoff=0.6)
                    if match:
                        return match
                
                # Priority 3: Extract from Ticket name and fuzzy match
                ticket_name = row.get('Ticket name', '')
                extracted = extract_customer_from_ticket(ticket_name)
                if extracted:
                    match = try_match(extracted, valid_customers, cutoff=0.5)
                    if match:
                        return match
                
                return ''
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-categorize_hubspot_ncr"></a> `categorize_hubspot_ncr` — L4184–L4251

```python
def categorize_hubspot_ncr(description):
                """Categorize HubSpot NCR based on ticket description to match NetSuite Issue Types"""
                if not description or description == '' or pd.isna(description):
                    return 'Defective Product'
                
                desc_lower = str(description).lower()
                
                # Damaged in Transit - carrier damage, broken in shipping
                if any(kw in desc_lower for kw in ['damaged', 'broken', 'crushed', 'fedex damaged', 
                                                    'ups damaged', 'transit', 'carrier', 'pallet.*damage']):
                    return 'Damaged in Transit'
                
                # Shipped to Wrong Address - misshipments, swapped orders
                if any(kw in desc_lower for kw in ['wrong address', 'misshipped', 'swapped', 
                                                    'wrong location', 'delivered to wrong']):
                    return 'Shipped to Wrong Address'
                
                # Missing Labels Wrong Qty - shortages
                if any(kw in desc_lower for kw in ['short', 'missing', 'shorted', 'only received',
                                                    'ran short', 'labels short']):
                    return 'Missing Labels Wrong Qty'
                
                # Order Entry Error - system/data entry issues, customer ordered wrong
                if any(kw in desc_lower for kw in ['hubspot', 'netsuite', 'set up incorrectly', 
                                                    'entered into', 'system switched',
                                                    'customer ordered wrong', 'mistakenly ordered',
                                                    'accidentally placed', 'customer error',
                                                    'deal & so was reflective of the wrong',
                                                    'proofing queue']):
                    return 'Order Entry Error'
                
                # Wrong Material - wrong product shipped (includes wrong color/size)
                if any(kw in desc_lower for kw in ['wrong color', 'wrong size', 'wrong finish',
                                                    'received white instead', 'received black instead', 
                                                    'instead of', '25d instead', '15d instead', 
                                                    '7ml instead', '45d instead', '4ml instead',
                                                    'wrong sku', 'wrong product', 'mislabeled box',
                                                    'shipped black instead', 'shipped white instead',
                                                    'wrong core', 'not the artwork']):
                    return 'Wrong Material'
                
                # Incorrect Color - specifically color-related manufacturing issues
                if any(kw in desc_lower for kw in ['grey caps', 'marbling', 'translucent',
                                                    'color.*mixed', 'pigment']):
                    return 'Incorrect Color'
                
                # Artwork/Print/Label defects
                if any(kw in desc_lower for kw in ['print', 'artwork', 'off center', 'embossing',
                                                    'cut off', 'varnish', 'laminate', 'tactile',
                                                    'telescoping', 'backing.*rip', 'paper backing',
                                                    'poor print', 'skipout']):
                    return 'Artwork Error'
                
                # Defective Product - manufacturing defects, contamination, fit issues
                if any(kw in desc_lower for kw in ['warped', 'warping', 'defect', 'grease', 
                                                    'debris', 'contaminated', 'filth', 'insect', 
                                                    'hair', 'doesn\'t fit', 'not sealing', 'leaking',
                                                    'cracked', 'irregular', 'lid.*fit', 'snapping',
                                                    'boxes not forming', 'not in.*bag']):
                    return 'Defective Product'
                
                # Customer Returns (not defect-related)
                if any(kw in desc_lower for kw in ['customer return', 'return', 'exchange',
                                                    'would like to replace', 'swap out']):
                    return 'Order Entry Error'
                
                # Default fallback
                return 'Defective Product'
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-get_qty_and_product_type"></a> `get_qty_and_product_type` — L4278–L4290

```python
def get_qty_and_product_type(row):
                """Get quantity affected and product type from first non-empty QTY column"""
                for col_name, product_type in qty_columns:
                    if col_name in row.index:
                        val = row[col_name]
                        if pd.notna(val) and str(val).strip() not in ['', 'nan', '0']:
                            try:
                                qty = float(str(val).replace(',', '').strip())
                                if qty > 0:
                                    return qty, product_type
                            except (ValueError, TypeError):
                                continue
                return 0, 'Unknown'
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-normalize_for_matching"></a> `normalize_for_matching` — L4068–L4079

```python
def normalize_for_matching(name):
                    """Normalize customer name for better matching"""
                    if not name:
                        return ''
                    name = str(name).strip()
                    # Remove common state abbreviations at the end (NY, MA, OH, NJ, PA, IL, etc.)
                    name = re.sub(r'\s+(NY|MA|OH|NJ|PA|IL|CA|CO|FL|TX|WA|OR|AZ|NV|MI|NC|SC|GA|VA|MD|CT|RI|NH|VT|ME|DE|WV|KY|TN|AL|MS|LA|AR|MO|IA|MN|WI|IN|OK|KS|NE|SD|ND|MT|WY|ID|UT|NM|HI|AK|DC)$', '', name, flags=re.IGNORECASE)
                    # Remove parenthetical state codes like (OH), (NY)
                    name = re.sub(r'\s*\([A-Z]{2}\)\s*', ' ', name)
                    # Remove trailing description words
                    name = re.sub(r'\s+(Smearing|Defect|Issue|Problem|Damage|Error).*$', '', name, flags=re.IGNORECASE)
                    return name.strip()
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-extract_base_company"></a> `extract_base_company` — L4081–L4111

```python
def extract_base_company(company_name):
                    """Extract base company name from various formats:
                    - 'Parent : Child' format -> 'Parent'
                    - 'Acreage Holdings:  New York (NY)' -> 'Acreage Holdings'
                    - 'Acreage Holdings - Massachusetts (MA)' -> 'Acreage Holdings'
                    """
                    if not company_name or pd.isna(company_name):
                        return ''
                    name = str(company_name).strip()
                    
                    # Pattern 1: 'Parent : Child' - take the first part (HubSpot Company Name 2 format)
                    if ' : ' in name:
                        return name.split(' : ')[0].strip()
                    
                    # Pattern 2: 'Company:  Location (STATE)' - take before first colon
                    if ':' in name:
                        base = name.split(':')[0].strip()
                        # Only use if it looks like a company name (not a URL)
                        if '.' not in base and len(base) > 3:
                            return base
                    
                    # Pattern 3: 'Company - Location (STATE)' - take before dash if state follows
                    if ' - ' in name:
                        parts = name.split(' - ')
                        if len(parts) >= 2:
                            # Check if second part looks like a state/location
                            second = parts[1].strip()
                            if re.search(r'(Massachusetts|New York|Ohio|Pennsylvania|Illinois|New Jersey|Connecticut|Michigan|Florida|California|Colorado|Texas|Washington|Oregon|Arizona|Nevada|North Carolina|South Carolina|Georgia|Virginia|Maryland|NY|MA|OH|PA|IL|NJ|CT|MI|FL|CA|CO|TX|WA|OR|AZ|NV|NC|SC|GA|VA|MD)', second, re.IGNORECASE):
                                return parts[0].strip()
                    
                    return name
```

### <a id="calyx-sop-dashboard-v2-src-yearly_planning_2026-py-try_match"></a> `try_match` — L4113–L4134

```python
def try_match(name, customers, cutoff=0.7):
                    """Try to match a name against valid customers"""
                    if not name:
                        return None
                    # Exact match first
                    if name in customers:
                        return name
                    # Normalized exact match
                    normalized = normalize_for_matching(name)
                    for cust in customers:
                        if normalize_for_matching(cust) == normalized:
                            return cust
                    # Fuzzy match
                    matches = get_close_matches(name, customers, n=1, cutoff=cutoff)
                    if matches:
                        return matches[0]
                    # Fuzzy match on normalized
                    if normalized != name:
                        matches = get_close_matches(normalized, customers, n=1, cutoff=cutoff)
                        if matches:
                            return matches[0]
                    return None
```
