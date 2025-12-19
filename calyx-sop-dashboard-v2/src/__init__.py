"""
Calyx S&OP Dashboard Source Package
Contains all modules for S&OP Planning and Quality Management

Author: Xander @ Calyx Containers
Version: 3.1.0
"""

# NC Data Loader
from .data_loader import (
    load_nc_data,
    refresh_data,
    get_data_summary,
    load_sample_data,
    filter_nc_data,
    get_unique_values
)

# S&OP Data Loader
from .sop_data_loader import (
    load_invoices,
    load_invoice_lines,
    load_so_lines,
    load_sales_orders,
    load_customers,
    load_items,
    load_vendors,
    load_inventory,
    load_deals,
    load_all_sop_data,
    prepare_demand_history,
    prepare_revenue_history,
    get_unique_sales_reps,
    get_customers_for_rep,
    get_skus_for_customer,
    get_unique_product_types,
    get_unique_skus,
    get_pipeline_by_period,
    calculate_lead_times,
    allocate_topdown_forecast
)

from .sales_rep_view import render_sales_rep_view

# Export all
__all__ = [
    # NC Data
    'load_nc_data',
    'refresh_data',
    'get_data_summary',
    'load_sample_data',
    'filter_nc_data',
    'get_unique_values',
    # S&OP Data
    'load_invoices',
    'load_invoice_lines',
    'load_so_lines',
    'load_sales_orders',
    'load_customers',
    'load_items',
    'load_vendors',
    'load_inventory',
    'load_deals',
    'load_all_sop_data',
    'prepare_demand_history',
    'prepare_revenue_history',
    'get_unique_sales_reps',
    'get_customers_for_rep',
    'get_skus_for_customer',
    'get_unique_product_types',
    'get_unique_skus',
    'get_pipeline_by_period',
    'calculate_lead_times',
    'allocate_topdown_forecast',
    # Views
    'render_sales_rep_view',
]
