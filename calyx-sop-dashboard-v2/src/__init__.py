"""
Calyx S&OP Dashboard Source Package
Contains all modules for S&OP Planning and Quality Management

Author: Xander @ Calyx Containers
"""

# NC Dashboard / Quality modules
from .data_loader import (
    load_nc_data,
    refresh_data,
    get_data_summary,
    load_sample_data
)

from .kpi_cards import render_open_nc_status_tracker

from .aging_analysis import (
    render_aging_dashboard,
    calculate_aging_metrics
)

from .cost_analysis import (
    render_cost_of_rework,
    render_cost_avoided
)

from .customer_analysis import render_customer_analysis

from .pareto_chart import (
    render_issue_type_pareto,
    calculate_pareto_data
)

from .utils import (
    setup_logging,
    export_dataframe,
    format_currency,
    format_number,
    format_percentage
)

# S&OP modules
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
    prepare_revenue_history
)

from .forecasting_models import (
    generate_forecast,
    forecast_exponential_smoothing,
    forecast_arima,
    forecast_ml,
    blend_forecasts,
    ForecastResult
)

from .sales_rep_view import render_sales_rep_view
from .operations_view import render_operations_view
from .scenario_planning import render_scenario_planning
from .po_forecast import render_po_forecast
from .deliveries_tracking import render_deliveries_tracking
from .quality_section import render_quality_section

__all__ = [
    # NC Dashboard
    'load_nc_data',
    'refresh_data',
    'get_data_summary',
    'load_sample_data',
    'render_open_nc_status_tracker',
    'render_aging_dashboard',
    'calculate_aging_metrics',
    'render_cost_of_rework',
    'render_cost_avoided',
    'render_customer_analysis',
    'render_issue_type_pareto',
    'calculate_pareto_data',
    'setup_logging',
    'export_dataframe',
    'format_currency',
    'format_number',
    'format_percentage',
    # S&OP Data Loading
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
    # Forecasting
    'generate_forecast',
    'forecast_exponential_smoothing',
    'forecast_arima',
    'forecast_ml',
    'blend_forecasts',
    'ForecastResult',
    # S&OP Views
    'render_sales_rep_view',
    'render_operations_view',
    'render_scenario_planning',
    'render_po_forecast',
    'render_deliveries_tracking',
    'render_quality_section'
]

__version__ = '2.0.0'
