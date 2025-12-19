"""
Operations/Supply Chain View Module for S&OP Dashboard
Demand planning, pipeline analysis, and coverage tracking

Author: Xander @ Calyx Containers
Version: 4.0.0
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

# =============================================================================
# SETTINGS STORAGE (Session State)
# =============================================================================

def init_settings():
    """Initialize settings in session state if not present."""
    if 'ops_case_quantities' not in st.session_state:
        # Default case quantities by category
        st.session_state.ops_case_quantities = {
            'Calyx Cure': 1,
            'Plastic Lids': 1000,
            'Plastic Bases': 1000,
            'Glass Bases': 100,
            'Shrink Bands': 5000,
            'Tray Inserts': 100,
            'Tray Frames': 50,
            'Tubes': 500,
        }
    
    if 'ops_item_consolidation' not in st.session_state:
        # Item consolidation mapping: {child_sku: parent_sku}
        st.session_state.ops_item_consolidation = {}


def get_case_quantity(category):
    """Get case quantity for a category."""
    init_settings()
    return st.session_state.ops_case_quantities.get(category, 1)


def get_consolidated_sku(sku):
    """Get the parent SKU if this SKU is consolidated, otherwise return itself."""
    init_settings()
    return st.session_state.ops_item_consolidation.get(sku, sku)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def clean_dataframe(df):
    """Remove duplicate columns from DataFrame."""
    if df is None:
        return None
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]
    return df


def get_column_as_series(df, col_name):
    """Safely get a column as a Series, handling duplicates."""
    if df is None or col_name not in df.columns:
        return None
    result = df.loc[:, col_name]
    if isinstance(result, pd.DataFrame):
        return result.iloc[:, 0]
    return result


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


def get_items_for_category(invoice_lines, item_col, product_type_col, category):
    """Get list of items that belong to a specific category."""
    if invoice_lines is None or item_col is None or product_type_col is None:
        return []
    
    if category == "All":
        item_series = get_column_as_series(invoice_lines, item_col)
        if item_series is not None:
            return sorted(item_series.dropna().astype(str).unique().tolist())[:200]
        return []
    
    cat_series = get_column_as_series(invoice_lines, product_type_col)
    item_series = get_column_as_series(invoice_lines, item_col)
    
    if cat_series is None or item_series is None:
        return []
    
    mask = cat_series.astype(str).str.strip() == category
    items = item_series[mask].dropna().astype(str).unique().tolist()
    return sorted(items)[:200]


# =============================================================================
# MAIN RENDER FUNCTION
# =============================================================================

def render_operations_view():
    """Main render function for Operations/Supply Chain View."""
    
    init_settings()
    
    st.markdown("## 📦 Operations & Supply Chain View")
    st.markdown("Demand planning, pipeline analysis, and coverage tracking")
    
    # Load data
    try:
        from .sop_data_loader import (
            load_invoice_lines, load_sales_orders, load_items,
            load_inventory, load_deals, prepare_demand_history,
            get_pipeline_by_period
        )
        
        invoice_lines = clean_dataframe(load_invoice_lines())
        sales_orders = clean_dataframe(load_sales_orders())
        items = clean_dataframe(load_items())
        inventory = clean_dataframe(load_inventory())
        deals = clean_dataframe(load_deals())
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return
    
    if invoice_lines is None or invoice_lines.empty:
        st.error("Unable to load invoice data. Please check your data connection.")
        return
    
    # ==========================================================================
    # IDENTIFY KEY COLUMNS
    # ==========================================================================
    
    product_type_col = find_column(invoice_lines, ['product type', 'calyx'])
    item_col = find_column(invoice_lines, ['item', 'sku'], exclude=['description'])
    date_col = find_column(invoice_lines, ['date'])
    amount_col = find_column(invoice_lines, ['amount'])
    qty_col = find_column(invoice_lines, ['qty', 'quantity'])
    
    # ==========================================================================
    # BUILD FILTER OPTIONS - Category first
    # ==========================================================================
    
    category_options = ["All"]
    if product_type_col:
        cat_series = get_column_as_series(invoice_lines, product_type_col)
        if cat_series is not None:
            cats = cat_series.dropna().astype(str).unique().tolist()
            category_options.extend(sorted([c for c in cats if c.strip() and c != 'Unknown']))
    
    # ==========================================================================
    # FILTER UI
    # ==========================================================================
    
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        selected_category = st.selectbox("Product Category", category_options, key="opsv_category")
    
    # Dynamic Item/SKU filter based on selected category
    with col2:
        item_options = ["All"] + get_items_for_category(invoice_lines, item_col, product_type_col, selected_category)
        selected_item = st.selectbox("Item/SKU", item_options, key="opsv_item")
    
    with col3:
        time_period = st.selectbox(
            "Time Period", 
            ["Monthly", "Quarterly", "Weekly"],
            key="opsv_time_period"
        )
    with col4:
        forecast_horizon = st.selectbox(
            "Forecast Horizon",
            ["3 Months", "6 Months", "12 Months"],
            key="opsv_horizon"
        )
    
    # Convert selections to parameters
    freq_map = {"Monthly": "M", "Quarterly": "Q", "Weekly": "W"}
    freq = freq_map.get(time_period, "M")
    
    horizon_map = {"3 Months": 3, "6 Months": 6, "12 Months": 12}
    horizon = horizon_map.get(forecast_horizon, 6)
    
    # ==========================================================================
    # APPLY FILTERS
    # ==========================================================================
    
    filtered = invoice_lines.copy()
    
    if selected_category != "All" and product_type_col:
        cat_series = get_column_as_series(filtered, product_type_col)
        if cat_series is not None:
            filtered = filtered[cat_series.astype(str).str.strip() == selected_category].copy()
    
    if selected_item != "All" and item_col:
        item_series = get_column_as_series(filtered, item_col)
        if item_series is not None:
            filtered = filtered[item_series == selected_item].copy()
    
    # Convert numeric columns
    if amount_col:
        amt_series = get_column_as_series(filtered, amount_col)
        if amt_series is not None:
            filtered.loc[:, amount_col] = pd.to_numeric(amt_series, errors='coerce').fillna(0)
    
    if qty_col:
        qty_series = get_column_as_series(filtered, qty_col)
        if qty_series is not None:
            filtered.loc[:, qty_col] = pd.to_numeric(qty_series, errors='coerce').fillna(0)
    
    # ==========================================================================
    # TABS
    # ==========================================================================
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Demand vs Pipeline",
        "📊 Coverage Analysis",
        "📦 Inventory Status",
        "🔍 SKU Deep Dive",
        "📋 Top-Down Forecast",
        "⚙️ Settings"
    ])
    
    with tab1:
        render_demand_pipeline_tab(filtered, deals, date_col, amount_col, qty_col, freq, horizon, selected_category, item_col, product_type_col)
    
    with tab2:
        render_coverage_tab(filtered, deals, sales_orders, date_col, amount_col, product_type_col)
    
    with tab3:
        render_inventory_tab(inventory, items, item_col, product_type_col, selected_category, selected_item)
    
    with tab4:
        render_sku_deep_dive(filtered, item_col, amount_col, qty_col, date_col, product_type_col)
    
    with tab5:
        render_topdown_forecast_tab(selected_category, freq)
    
    with tab6:
        render_settings_tab()
    
    # ==========================================================================
    # DEBUG INFO AT BOTTOM
    # ==========================================================================
    
    st.markdown("---")
    with st.expander("🔧 Data Debug Info"):
        st.write(f"**Data Loaded:**")
        st.write(f"- Invoice Lines: {len(invoice_lines) if invoice_lines is not None else 'None'} rows")
        st.write(f"- Sales Orders: {len(sales_orders) if sales_orders is not None else 'None'} rows")
        st.write(f"- Items: {len(items) if items is not None else 'None'} rows")
        st.write(f"- Inventory: {len(inventory) if inventory is not None else 'None'} rows")
        st.write(f"- Deals: {len(deals) if deals is not None else 'None'} rows")
        st.write(f"- Filtered: {len(filtered)} rows")
        
        st.write(f"**Column Mappings:**")
        st.write(f"- Product Type: {product_type_col}")
        st.write(f"- Item: {item_col}")
        st.write(f"- Date: {date_col}")
        st.write(f"- Amount: {amount_col}")
        st.write(f"- Quantity: {qty_col}")
        
        # Revenue Forecast debug
        if 'forecast_debug' in st.session_state:
            st.write("---")
            st.write("**Revenue Forecast Debug:**")
            for key, value in st.session_state.forecast_debug.items():
                st.write(f"- {key}: {value}")
        
        if 'item_mix_debug' in st.session_state:
            st.write("---")
            st.write("**Item Mix Debug:**")
            for key, value in st.session_state.item_mix_debug.items():
                st.write(f"- {key}: {value}")


# =============================================================================
# DEMAND VS PIPELINE TAB
# =============================================================================

def render_demand_pipeline_tab(filtered, deals, date_col, amount_col, qty_col, freq, horizon, category, item_col, product_type_col):
    """Render Demand vs Pipeline overlay chart with 4 lines."""
    
    st.markdown("### 📈 Demand Forecast vs Pipeline Overlay")
    st.markdown("Compare historical demand, demand forecast, deals pipeline, and revenue forecast plan")
    
    if filtered.empty:
        st.warning("No data available for the selected filters.")
        return
    
    # Load Top-Down Revenue Forecast from Google Sheet
    revenue_forecast_raw = None
    revenue_forecast_by_period = pd.DataFrame()
    item_forecast = pd.DataFrame()
    
    try:
        from .sop_data_loader import (
            get_topdown_item_forecast, get_revenue_forecast_by_period, 
            load_revenue_forecast
        )
        
        revenue_forecast_raw = load_revenue_forecast()
        revenue_forecast_by_period = get_revenue_forecast_by_period(category=category)
        item_forecast = get_topdown_item_forecast()
        
    except Exception as e:
        st.warning(f"Could not load Revenue Forecast: {e}")
    
    # Prepare historical demand by period
    if date_col and amount_col:
        try:
            date_series = get_column_as_series(filtered, date_col)
            amt_series = get_column_as_series(filtered, amount_col)
            
            if date_series is not None and amt_series is not None:
                temp_df = pd.DataFrame({
                    'Date': pd.to_datetime(date_series, errors='coerce'),
                    'Amount': pd.to_numeric(amt_series, errors='coerce').fillna(0)
                })
                temp_df = temp_df.dropna(subset=['Date'])
                temp_df['Period'] = temp_df['Date'].dt.to_period(freq)
                
                demand_history = temp_df.groupby('Period')['Amount'].sum().reset_index()
                demand_history['Period'] = demand_history['Period'].astype(str)
                demand_history = demand_history.sort_values('Period')
                
                # Generate demand forecast (statistical/ML based)
                demand_forecast_df = generate_advanced_forecast(demand_history, horizon, freq)
                
                # Get pipeline/deals data with SKU and Close Date
                pipeline_df = get_pipeline_data(deals, freq, category, item_col, product_type_col)
                
                # Align revenue forecast periods to match chart format
                if not revenue_forecast_by_period.empty:
                    revenue_forecast_by_period = align_forecast_periods(revenue_forecast_by_period, freq)
                
                # Create overlay chart with 4 lines
                fig = create_four_line_chart(
                    demand_history, 
                    demand_forecast_df, 
                    pipeline_df, 
                    revenue_forecast_by_period,
                    category,
                    freq
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                total_historical = demand_history['Amount'].sum()
                total_demand_forecast = demand_forecast_df['Forecast'].sum() if not demand_forecast_df.empty else 0
                total_pipeline = pipeline_df['Pipeline Value'].sum() if not pipeline_df.empty and 'Pipeline Value' in pipeline_df.columns else 0
                total_revenue_forecast = revenue_forecast_by_period['Forecast_Revenue'].sum() if not revenue_forecast_by_period.empty else 0
                
                with col1:
                    st.metric("Historical Demand", f"${total_historical:,.0f}")
                with col2:
                    st.metric("Demand Forecast", f"${total_demand_forecast:,.0f}")
                with col3:
                    st.metric("Pipeline/Deals", f"${total_pipeline:,.0f}")
                with col4:
                    st.metric("Revenue Forecast", f"${total_revenue_forecast:,.0f}")
                
        except Exception as e:
            st.error(f"Error creating demand chart: {e}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.warning("Required columns (Date, Amount) not found.")


def get_pipeline_data(deals, freq, category, item_col, product_type_col):
    """Get pipeline data from Deals using SKU column and Close Date."""
    if deals is None or deals.empty:
        return pd.DataFrame()
    
    df = deals.copy()
    
    # Find SKU column
    sku_col = find_column(df, ['sku'])
    
    # Find Close Date column
    close_date_col = find_column(df, ['close date', 'closedate', 'close_date'])
    if close_date_col is None:
        close_date_col = find_column(df, ['date'])
    
    # Find Amount column
    amount_col = find_column(df, ['amount', 'value', 'revenue'])
    
    if close_date_col is None or amount_col is None:
        return pd.DataFrame()
    
    try:
        date_series = get_column_as_series(df, close_date_col)
        amt_series = get_column_as_series(df, amount_col)
        
        temp_df = pd.DataFrame({
            'Date': pd.to_datetime(date_series, errors='coerce'),
            'Amount': pd.to_numeric(amt_series, errors='coerce').fillna(0)
        })
        
        # Add SKU if available
        if sku_col:
            sku_series = get_column_as_series(df, sku_col)
            temp_df['SKU'] = sku_series
        
        temp_df = temp_df.dropna(subset=['Date'])
        temp_df['Period'] = temp_df['Date'].dt.to_period(freq).astype(str)
        
        # Format period for quarterly
        if freq == 'Q':
            temp_df['Period'] = temp_df['Date'].apply(lambda x: f"{x.year}-Q{(x.month-1)//3 + 1}")
        
        pipeline_by_period = temp_df.groupby('Period')['Amount'].sum().reset_index()
        pipeline_by_period.columns = ['Period', 'Pipeline Value']
        
        return pipeline_by_period
        
    except Exception as e:
        logger.error(f"Error getting pipeline data: {e}")
        return pd.DataFrame()


def align_forecast_periods(forecast_df, freq):
    """Align forecast periods to match chart format."""
    if forecast_df.empty or 'Period' not in forecast_df.columns:
        return forecast_df
    
    df = forecast_df.copy()
    
    if freq == 'Q':
        # Convert YYYY-MM to YYYY-QN format
        def to_quarter(period_str):
            try:
                parts = str(period_str).split('-')
                if len(parts) == 2:
                    year = int(parts[0])
                    month = int(parts[1])
                    quarter = (month - 1) // 3 + 1
                    return f"{year}-Q{quarter}"
                return period_str
            except:
                return period_str
        
        df['Period'] = df['Period'].apply(to_quarter)
        # Aggregate by quarter in case multiple months map to same quarter
        df = df.groupby('Period').agg({
            'Forecast_Revenue': 'sum',
            'Forecast_Units': 'sum' if 'Forecast_Units' in df.columns else 'first'
        }).reset_index()
    
    return df


def generate_advanced_forecast(history_df, horizon, freq):
    """Generate demand forecast using moving average with trend."""
    if history_df.empty:
        return pd.DataFrame()
    
    try:
        # Use weighted moving average of last 6 periods
        recent = history_df.tail(6)
        
        if len(recent) < 2:
            avg_value = recent['Amount'].mean() if not recent.empty else 0
            growth_rate = 0.02
        else:
            values = recent['Amount'].values
            weights = np.array([1, 2, 3, 4, 5, 6])[:len(values)]
            weights = weights / weights.sum()
            
            weighted_avg = np.sum(values * weights)
            
            if len(values) >= 2 and values[0] > 0:
                growth_rate = (values[-1] / values[0]) ** (1/len(values)) - 1
                growth_rate = max(min(growth_rate, 0.15), -0.10)
            else:
                growth_rate = 0.02
            
            avg_value = weighted_avg
        
        # Get last period and generate future periods
        last_period_str = history_df['Period'].iloc[-1]
        
        try:
            last_date = pd.to_datetime(last_period_str)
        except:
            last_date = datetime.now()
        
        # Generate future periods
        forecast_data = []
        for i in range(1, horizon + 1):
            if freq == 'M':
                future_date = last_date + pd.DateOffset(months=i)
                period_label = future_date.strftime('%Y-%m')
            elif freq == 'Q':
                future_date = last_date + pd.DateOffset(months=i*3)
                period_label = f"{future_date.year}-Q{(future_date.month-1)//3 + 1}"
            elif freq == 'W':
                future_date = last_date + pd.DateOffset(weeks=i)
                period_label = future_date.strftime('%Y-%W')
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
        
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        return pd.DataFrame()


def create_four_line_chart(demand_df, demand_forecast_df, pipeline_df, revenue_forecast_df, category, freq):
    """Create overlay chart with Historical, Demand Forecast, Pipeline, and Revenue Forecast."""
    
    fig = go.Figure()
    
    title_suffix = f" - {category}" if category != "All" else " - All Categories"
    
    # 1. Historical demand (blue bars)
    if not demand_df.empty:
        fig.add_trace(go.Bar(
            x=demand_df['Period'],
            y=demand_df['Amount'],
            name='Historical Demand',
            marker_color='#0033A1',
            opacity=0.7,
            hovertemplate='<b>Historical Demand</b><br>Period: %{x}<br>Revenue: $%{y:,.0f}<extra></extra>'
        ))
    
    # 2. Demand Forecast (green dashed line)
    if not demand_forecast_df.empty:
        fig.add_trace(go.Scatter(
            x=demand_forecast_df['Period'],
            y=demand_forecast_df['Forecast'],
            mode='lines+markers',
            name='Demand Forecast',
            line=dict(color='#22C55E', width=3, dash='dash'),
            marker=dict(size=8, symbol='circle'),
            hovertemplate='<b>Demand Forecast</b><br>Period: %{x}<br>Forecast: $%{y:,.0f}<extra></extra>'
        ))
        
        # Confidence interval
        fig.add_trace(go.Scatter(
            x=demand_forecast_df['Period'].tolist() + demand_forecast_df['Period'].tolist()[::-1],
            y=demand_forecast_df['Upper'].tolist() + demand_forecast_df['Lower'].tolist()[::-1],
            fill='toself',
            fillcolor='rgba(34, 197, 94, 0.15)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Forecast CI (85%)',
            showlegend=True,
            hoverinfo='skip'
        ))
    
    # 3. Pipeline/Deals (orange line)
    if pipeline_df is not None and not pipeline_df.empty and 'Pipeline Value' in pipeline_df.columns:
        fig.add_trace(go.Scatter(
            x=pipeline_df['Period'],
            y=pipeline_df['Pipeline Value'],
            mode='lines+markers',
            name='Deals Pipeline',
            line=dict(color='#F59E0B', width=3),
            marker=dict(size=8, symbol='diamond'),
            hovertemplate='<b>Deals Pipeline</b><br>Period: %{x}<br>Value: $%{y:,.0f}<extra></extra>'
        ))
    
    # 4. Revenue Forecast (purple line)
    if revenue_forecast_df is not None and not revenue_forecast_df.empty and 'Forecast_Revenue' in revenue_forecast_df.columns:
        fig.add_trace(go.Scatter(
            x=revenue_forecast_df['Period'],
            y=revenue_forecast_df['Forecast_Revenue'],
            mode='lines+markers',
            name='Revenue Plan (Top-Down)',
            line=dict(color='#8B5CF6', width=3),
            marker=dict(size=10, symbol='star'),
            hovertemplate='<b>Revenue Plan (Top-Down)</b><br>Period: %{x}<br>Forecast: $%{y:,.0f}<extra></extra>'
        ))
    
    fig.update_layout(
        title=f'Demand & Pipeline Overlay{title_suffix}',
        xaxis_title='Period',
        yaxis_title='Revenue ($)',
        hovermode='x unified',
        legend=dict(
            orientation='h', 
            yanchor='bottom', 
            y=1.02, 
            xanchor='right', 
            x=1
        ),
        height=550,
        barmode='group'
    )
    
    fig.update_yaxes(tickformat='$,.0f')
    
    return fig


# =============================================================================
# TOP-DOWN FORECAST TAB
# =============================================================================

def render_topdown_forecast_tab(category, freq):
    """Render Top-Down Forecast tab with SKU-level monthly breakdown."""
    
    st.markdown("### 📋 Top-Down Item Forecast Allocation")
    st.markdown("SKU-level forecast breakdown by period based on historical mix and ASP")
    
    try:
        from .sop_data_loader import get_topdown_item_forecast, load_revenue_forecast
        
        item_forecast = get_topdown_item_forecast()
        revenue_forecast_raw = load_revenue_forecast()
        
        if item_forecast.empty:
            st.warning("No item-level forecast data available.")
            if revenue_forecast_raw is not None and not revenue_forecast_raw.empty:
                st.info("Revenue Forecast sheet loaded but item allocation failed. Check that Items table has Product Type mapping.")
            return
        
        # Filter by category if selected
        if category and category != 'All':
            item_forecast = item_forecast[item_forecast['Category'].str.lower().str.strip() == category.lower().strip()]
        
        if item_forecast.empty:
            st.warning(f"No forecast data for category: {category}")
            return
        
        # Create pivot table: SKU x Period with Units
        st.markdown("#### Forecasted Units by SKU and Period")
        
        pivot_units = item_forecast.pivot_table(
            index=['Item', 'Category'],
            columns='Period',
            values='Forecast_Units',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # Sort columns (periods) chronologically
        period_cols = [c for c in pivot_units.columns if c not in ['Item', 'Category']]
        period_cols_sorted = sorted(period_cols)
        
        display_cols = ['Item', 'Category'] + period_cols_sorted
        pivot_units = pivot_units[display_cols]
        
        # Format numbers
        for col in period_cols_sorted:
            pivot_units[col] = pivot_units[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "0")
        
        st.dataframe(pivot_units, use_container_width=True, hide_index=True, height=400)
        
        # Also show revenue breakdown
        st.markdown("#### Forecasted Revenue by SKU and Period")
        
        pivot_revenue = item_forecast.pivot_table(
            index=['Item', 'Category'],
            columns='Period',
            values='Forecast_Revenue',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        pivot_revenue = pivot_revenue[display_cols]
        
        for col in period_cols_sorted:
            pivot_revenue[col] = pivot_revenue[col].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")
        
        st.dataframe(pivot_revenue, use_container_width=True, hide_index=True, height=400)
        
        # Summary stats
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        total_units = item_forecast['Forecast_Units'].sum()
        total_revenue = item_forecast['Forecast_Revenue'].sum()
        unique_skus = item_forecast['Item'].nunique()
        
        with col1:
            st.metric("Total Forecast Units", f"{total_units:,.0f}")
        with col2:
            st.metric("Total Forecast Revenue", f"${total_revenue:,.0f}")
        with col3:
            st.metric("Unique SKUs", f"{unique_skus}")
        
    except Exception as e:
        st.error(f"Error loading forecast data: {e}")
        import traceback
        st.code(traceback.format_exc())


# =============================================================================
# SETTINGS TAB
# =============================================================================

def render_settings_tab():
    """Render Settings tab with case quantities and item consolidation."""
    
    st.markdown("### ⚙️ Operations Settings")
    
    # Case Quantities Section
    st.markdown("#### 📦 Case Quantities by Category")
    st.markdown("Set the number of units per case for each category to align forecast with packout expectations.")
    
    init_settings()
    
    # Create editable table for case quantities
    categories = [
        'Calyx Cure', 'Plastic Lids', 'Plastic Bases', 'Glass Bases',
        'Shrink Bands', 'Tray Inserts', 'Tray Frames', 'Tubes'
    ]
    
    case_data = []
    for cat in categories:
        case_data.append({
            'Category': cat,
            'Units per Case': st.session_state.ops_case_quantities.get(cat, 1)
        })
    
    case_df = pd.DataFrame(case_data)
    
    edited_case_df = st.data_editor(
        case_df,
        column_config={
            "Category": st.column_config.TextColumn("Category", disabled=True),
            "Units per Case": st.column_config.NumberColumn("Units per Case", min_value=1, max_value=100000, step=1)
        },
        hide_index=True,
        use_container_width=True,
        key="case_qty_editor"
    )
    
    if st.button("💾 Save Case Quantities", key="save_case_qty"):
        for _, row in edited_case_df.iterrows():
            st.session_state.ops_case_quantities[row['Category']] = int(row['Units per Case'])
        st.success("Case quantities saved!")
    
    st.markdown("---")
    
    # Item Consolidation Section
    st.markdown("#### 🔗 Item Consolidation")
    st.markdown("Combine demand from one SKU into another. For example, consolidate 'PB-25D-001-00-EZ' into 'PB-25D-001-00'.")
    
    # Show current consolidations
    consolidations = st.session_state.ops_item_consolidation
    
    if consolidations:
        st.write("**Current Consolidations:**")
        consol_df = pd.DataFrame([
            {'Child SKU': k, 'Parent SKU': v} 
            for k, v in consolidations.items()
        ])
        st.dataframe(consol_df, hide_index=True, use_container_width=True)
    
    # Add new consolidation
    st.markdown("**Add New Consolidation:**")
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        child_sku = st.text_input("Child SKU (to be consolidated)", key="child_sku_input")
    with col2:
        parent_sku = st.text_input("Parent SKU (consolidate into)", key="parent_sku_input")
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Add", key="add_consolidation"):
            if child_sku and parent_sku:
                st.session_state.ops_item_consolidation[child_sku.strip()] = parent_sku.strip()
                st.success(f"Added: {child_sku} → {parent_sku}")
                st.rerun()
            else:
                st.warning("Please enter both SKUs")
    
    # Remove consolidation
    if consolidations:
        st.markdown("**Remove Consolidation:**")
        sku_to_remove = st.selectbox(
            "Select child SKU to remove",
            options=list(consolidations.keys()),
            key="remove_consolidation_select"
        )
        if st.button("🗑️ Remove Selected", key="remove_consolidation"):
            if sku_to_remove in st.session_state.ops_item_consolidation:
                del st.session_state.ops_item_consolidation[sku_to_remove]
                st.success(f"Removed consolidation for: {sku_to_remove}")
                st.rerun()


# =============================================================================
# COVERAGE ANALYSIS TAB
# =============================================================================

def render_coverage_tab(filtered, deals, sales_orders, date_col, amount_col, product_type_col):
    """Render Coverage Analysis tab."""
    
    st.markdown("### 📊 Pipeline Coverage Analysis")
    st.markdown("Analyze pipeline coverage by product category")
    
    if filtered.empty:
        st.warning("No data available for coverage analysis.")
        return
    
    if product_type_col is None:
        st.warning("Product type column not found.")
        return
    
    try:
        # Calculate demand by category
        cat_series = get_column_as_series(filtered, product_type_col)
        amt_series = get_column_as_series(filtered, amount_col)
        
        if cat_series is None or amt_series is None:
            st.warning("Could not extract category or amount data.")
            return
        
        temp_df = pd.DataFrame({
            'Category': cat_series,
            'Amount': pd.to_numeric(amt_series, errors='coerce').fillna(0)
        })
        
        by_category = temp_df.groupby('Category')['Amount'].sum().reset_index()
        by_category.columns = ['Category', 'Historical Revenue']
        by_category = by_category.sort_values('Historical Revenue', ascending=False)
        
        # Create chart
        fig = px.bar(
            by_category.head(15),
            x='Category',
            y='Historical Revenue',
            title='Revenue by Product Category'
        )
        fig.update_layout(height=400)
        fig.update_yaxes(tickformat='$,.0f')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show table
        display_df = by_category.copy()
        display_df['Historical Revenue'] = display_df['Historical Revenue'].apply(lambda x: f"${x:,.0f}")
        st.dataframe(display_df, hide_index=True, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error in coverage analysis: {e}")


# =============================================================================
# INVENTORY STATUS TAB
# =============================================================================

def render_inventory_tab(inventory, items, item_col, product_type_col, selected_category, selected_item):
    """Render Inventory Status tab with category/item filtering."""
    
    st.markdown("### 📦 Inventory Status")
    st.markdown("Current inventory levels filtered by selected category and item")
    
    if inventory is None or inventory.empty:
        st.info("No inventory data available.")
        return
    
    df = inventory.copy()
    
    # Find columns in inventory
    inv_item_col = find_column(df, ['item', 'sku', 'name'])
    inv_qty_col = find_column(df, ['qty', 'quantity', 'on hand', 'available'])
    
    if inv_item_col is None:
        st.warning("Item column not found in inventory data.")
        return
    
    # Try to filter by category if we have items table with product type
    if items is not None and not items.empty and selected_category != "All":
        # Build item -> category mapping from items table
        items_item_col = find_column(items, ['item', 'sku', 'name'])
        items_cat_col = find_column(items, ['product type', 'calyx', 'category'])
        
        if items_item_col and items_cat_col:
            item_cat_map = {}
            for _, row in items.iterrows():
                item_val = row[items_item_col]
                cat_val = row[items_cat_col]
                if pd.notna(item_val) and pd.notna(cat_val):
                    item_cat_map[str(item_val).strip()] = str(cat_val).strip()
            
            # Filter inventory to items in selected category
            inv_items = get_column_as_series(df, inv_item_col)
            if inv_items is not None:
                df['_category'] = inv_items.astype(str).str.strip().map(item_cat_map)
                df = df[df['_category'] == selected_category]
                df = df.drop(columns=['_category'])
    
    # Filter by specific item if selected
    if selected_item != "All" and inv_item_col:
        inv_items = get_column_as_series(df, inv_item_col)
        if inv_items is not None:
            df = df[inv_items.astype(str).str.strip() == selected_item]
    
    if df.empty:
        st.info(f"No inventory data for the selected filters.")
        return
    
    # Display inventory table
    st.dataframe(df, use_container_width=True, hide_index=True, height=400)
    
    # Summary metrics
    if inv_qty_col:
        qty_series = get_column_as_series(df, inv_qty_col)
        if qty_series is not None:
            total_qty = pd.to_numeric(qty_series, errors='coerce').fillna(0).sum()
            unique_items = df[inv_item_col].nunique() if inv_item_col else 0
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Units in Stock", f"{total_qty:,.0f}")
            with col2:
                st.metric("Unique Items", f"{unique_items}")


# =============================================================================
# SKU DEEP DIVE TAB
# =============================================================================

def render_sku_deep_dive(filtered, item_col, amount_col, qty_col, date_col, product_type_col):
    """Render SKU Deep Dive tab."""
    
    st.markdown("### 🔍 SKU Deep Dive")
    st.markdown("Detailed analysis of top performing SKUs")
    
    if filtered.empty or item_col is None or amount_col is None:
        st.warning("Insufficient data for SKU analysis.")
        return
    
    try:
        item_series = get_column_as_series(filtered, item_col)
        amt_series = get_column_as_series(filtered, amount_col)
        
        if item_series is None or amt_series is None:
            st.warning("Could not extract item or amount data.")
            return
        
        temp_df = pd.DataFrame({
            'Item': item_series,
            'Amount': pd.to_numeric(amt_series, errors='coerce').fillna(0)
        })
        
        if qty_col:
            qty_series = get_column_as_series(filtered, qty_col)
            if qty_series is not None:
                temp_df['Quantity'] = pd.to_numeric(qty_series, errors='coerce').fillna(0)
        
        # Aggregate by item
        by_item = temp_df.groupby('Item').agg({
            'Amount': 'sum',
            'Quantity': 'sum' if 'Quantity' in temp_df.columns else 'count'
        }).reset_index()
        
        by_item.columns = ['Item', 'Revenue', 'Units']
        by_item = by_item.sort_values('Revenue', ascending=False)
        
        # Top 25 SKUs
        top_skus = by_item.head(25)
        
        # Chart
        fig = px.bar(
            top_skus.head(10),
            x='Item',
            y='Revenue',
            title='Top 10 SKUs by Revenue'
        )
        fig.update_layout(height=400)
        fig.update_yaxes(tickformat='$,.0f')
        fig.update_xaxes(tickangle=45)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Table
        display_df = top_skus.copy()
        display_df['Revenue'] = display_df['Revenue'].apply(lambda x: f"${x:,.0f}")
        display_df['Units'] = display_df['Units'].apply(lambda x: f"{x:,.0f}")
        
        st.dataframe(display_df, hide_index=True, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error in SKU analysis: {e}")
