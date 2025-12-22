"""
Operations/Supply Chain View Module for S&OP Dashboard
Demand planning, pipeline analysis, and coverage tracking

Author: Xander @ Calyx Containers
Version: 4.1.0 - Performance Optimized
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# PERFORMANCE: Cache expensive computations
# =============================================================================

@st.cache_data(ttl=300)
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


@st.cache_data(ttl=300)
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


@st.cache_data(ttl=300)
def compute_pipeline_data_cached(deals_hash, deals, freq):
    """Cache pipeline data computation."""
    if deals is None or deals.empty:
        return pd.DataFrame()
    
    try:
        # Find columns
        close_date_col = find_column(deals, ['close date', 'closedate', 'close_date'])
        if close_date_col is None:
            close_date_col = find_column(deals, ['date'])
        
        amount_col = find_column(deals, ['amount', 'value', 'revenue'])
        sku_col = find_column(deals, ['sku'])
        
        if close_date_col is None or amount_col is None:
            return pd.DataFrame()
        
        date_series = get_column_as_series(deals, close_date_col)
        amt_series = get_column_as_series(deals, amount_col)
        
        temp_df = pd.DataFrame({
            'Date': pd.to_datetime(date_series, errors='coerce'),
            'Amount': pd.to_numeric(amt_series, errors='coerce').fillna(0)
        })
        
        if sku_col:
            temp_df['SKU'] = get_column_as_series(deals, sku_col)
        
        temp_df = temp_df.dropna(subset=['Date'])
        
        if freq == 'Q':
            temp_df['Period'] = temp_df['Date'].apply(lambda x: f"{x.year}-Q{(x.month-1)//3 + 1}")
        else:
            temp_df['Period'] = temp_df['Date'].dt.to_period(freq).astype(str)
        
        pipeline_by_period = temp_df.groupby('Period')['Amount'].sum().reset_index()
        pipeline_by_period.columns = ['Period', 'Pipeline Value']
        return pipeline_by_period
    except:
        return pd.DataFrame()


# =============================================================================
# SETTINGS STORAGE
# =============================================================================

def init_settings():
    """Initialize settings in session state if not present."""
    if 'ops_case_quantities' not in st.session_state:
        st.session_state.ops_case_quantities = {
            'Calyx Cure': 1, 'Plastic Lids': 1000, 'Plastic Bases': 1000,
            'Glass Bases': 100, 'Shrink Bands': 5000, 'Tray Inserts': 100,
            'Tray Frames': 50, 'Tubes': 500,
        }
    
    if 'ops_item_consolidation' not in st.session_state:
        st.session_state.ops_item_consolidation = {}


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
    """Safely get a column as a Series."""
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


def get_df_hash(df):
    """Get a simple hash for a dataframe for caching."""
    if df is None:
        return "none"
    return f"{len(df)}_{df.columns.tolist()[:3]}"


# =============================================================================
# MAIN RENDER FUNCTION - OPTIMIZED
# =============================================================================

def render_operations_view():
    """Main render function for Operations/Supply Chain View - Optimized."""
    
    init_settings()
    
    st.markdown("## 📦 Operations & Supply Chain View")
    st.markdown("Demand planning, pipeline analysis, and coverage tracking")
    
    # ==========================================================================
    # LOAD ALL DATA ONCE (cached in sop_data_loader)
    # ==========================================================================
    
    try:
        from .sop_data_loader import (
            load_invoice_lines, load_sales_orders, load_items,
            load_inventory, load_deals
        )
        
        # These are all cached - only load once
        invoice_lines = clean_dataframe(load_invoice_lines())
        sales_orders = clean_dataframe(load_sales_orders())
        items = clean_dataframe(load_items())
        inventory = clean_dataframe(load_inventory())
        deals = clean_dataframe(load_deals())
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return
    
    if invoice_lines is None or invoice_lines.empty:
        st.error("Unable to load invoice data. Please check your data connection.")
        return
    
    # ==========================================================================
    # IDENTIFY KEY COLUMNS (do once)
    # ==========================================================================
    
    product_type_col = find_column(invoice_lines, ['product type', 'calyx'])
    item_col = find_column(invoice_lines, ['item', 'sku'], exclude=['description'])
    date_col = find_column(invoice_lines, ['date'])
    amount_col = find_column(invoice_lines, ['amount'])
    qty_col = find_column(invoice_lines, ['qty', 'quantity'])
    
    # ==========================================================================
    # BUILD FILTER OPTIONS (cached)
    # ==========================================================================
    
    category_options = ["All"]
    if product_type_col:
        cat_series = get_column_as_series(invoice_lines, product_type_col)
        if cat_series is not None:
            cats = cat_series.dropna().astype(str).unique().tolist()
            category_options.extend(sorted([c for c in cats if c.strip() and c != 'Unknown']))
    
    # Get cached category-items map
    invoice_hash = get_df_hash(invoice_lines)
    category_items_map = get_category_items_map(invoice_hash, invoice_lines, item_col, product_type_col)
    
    # ==========================================================================
    # FILTER UI
    # ==========================================================================
    
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        selected_category = st.selectbox("Product Category", category_options, key="opsv_category")
    
    # Dynamic item options based on category
    with col2:
        if selected_category == "All":
            item_options = ["All"] + sorted(list(set(
                item for items in category_items_map.values() for item in items
            )))[:200]
        else:
            item_options = ["All"] + category_items_map.get(selected_category, [])
        selected_item = st.selectbox("Item/SKU", item_options, key="opsv_item")
    
    with col3:
        time_period = st.selectbox("Time Period", ["Monthly", "Quarterly", "Weekly"], key="opsv_time_period")
    
    with col4:
        forecast_horizon = st.selectbox("Forecast Horizon", ["3 Months", "6 Months", "12 Months"], key="opsv_horizon")
    
    freq_map = {"Monthly": "M", "Quarterly": "Q", "Weekly": "W"}
    freq = freq_map.get(time_period, "M")
    horizon = {"3 Months": 3, "6 Months": 6, "12 Months": 12}.get(forecast_horizon, 6)
    
    # ==========================================================================
    # APPLY FILTERS (vectorized operations)
    # ==========================================================================
    
    # Create filter mask instead of copying dataframe multiple times
    mask = pd.Series([True] * len(invoice_lines), index=invoice_lines.index)
    
    if selected_category != "All" and product_type_col:
        cat_series = get_column_as_series(invoice_lines, product_type_col)
        if cat_series is not None:
            mask &= (cat_series.astype(str).str.strip() == selected_category)
    
    if selected_item != "All" and item_col:
        item_series = get_column_as_series(invoice_lines, item_col)
        if item_series is not None:
            mask &= (item_series == selected_item)
    
    filtered = invoice_lines[mask].copy()
    
    # Convert numeric columns once
    if amount_col:
        amt_series = get_column_as_series(filtered, amount_col)
        if amt_series is not None:
            filtered[amount_col] = pd.to_numeric(amt_series, errors='coerce').fillna(0)
    
    if qty_col:
        qty_series = get_column_as_series(filtered, qty_col)
        if qty_series is not None:
            filtered[qty_col] = pd.to_numeric(qty_series, errors='coerce').fillna(0)
    
    # ==========================================================================
    # TABS - Each tab only computes what it needs
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
        render_demand_pipeline_tab(filtered, deals, date_col, amount_col, qty_col, freq, horizon, selected_category)
    
    with tab2:
        render_coverage_tab(filtered, amount_col, product_type_col)
    
    with tab3:
        render_inventory_tab(inventory, items, selected_category, selected_item)
    
    with tab4:
        render_sku_deep_dive(filtered, item_col, amount_col, qty_col)
    
    with tab5:
        render_topdown_forecast_tab(selected_category)
    
    with tab6:
        render_settings_tab()
    
    # Debug info at bottom
    with st.expander("🔧 Data Debug Info", expanded=False):
        st.write(f"Invoice Lines: {len(invoice_lines):,} | Filtered: {len(filtered):,}")
        st.write(f"Sales Orders: {len(sales_orders) if sales_orders is not None else 0:,}")
        st.write(f"Items: {len(items) if items is not None else 0:,}")
        st.write(f"Inventory: {len(inventory) if inventory is not None else 0:,}")
        st.write(f"Deals: {len(deals) if deals is not None else 0:,}")


# =============================================================================
# DEMAND VS PIPELINE TAB
# =============================================================================

def render_demand_pipeline_tab(filtered, deals, date_col, amount_col, qty_col, freq, horizon, category):
    """Render Demand vs Pipeline overlay chart."""
    
    st.markdown("### 📈 Demand Forecast vs Pipeline Overlay")
    
    if filtered.empty:
        st.warning("No data available for the selected filters.")
        return
    
    # Load revenue forecast (cached)
    try:
        from .sop_data_loader import get_revenue_forecast_by_period
        revenue_forecast_by_period = get_revenue_forecast_by_period(category=category)
        
        # Align to quarterly if needed
        if freq == 'Q' and not revenue_forecast_by_period.empty:
            revenue_forecast_by_period = align_forecast_periods(revenue_forecast_by_period)
    except:
        revenue_forecast_by_period = pd.DataFrame()
    
    # Compute demand history (cached based on filtered data hash)
    filtered_hash = f"{len(filtered)}_{category}_{freq}"
    demand_history = compute_demand_history_cached(filtered_hash, filtered, date_col, amount_col, freq)
    
    if demand_history.empty:
        st.warning("Could not compute demand history.")
        return
    
    # Generate forecast
    demand_forecast_df = generate_forecast(demand_history, horizon, freq)
    
    # Get pipeline data (cached)
    deals_hash = get_df_hash(deals)
    pipeline_df = compute_pipeline_data_cached(deals_hash, deals, freq)
    
    # Create chart
    fig = create_overlay_chart(demand_history, demand_forecast_df, pipeline_df, revenue_forecast_by_period, category)
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Historical Demand", f"${demand_history['Amount'].sum():,.0f}")
    with col2:
        st.metric("Demand Forecast", f"${demand_forecast_df['Forecast'].sum() if not demand_forecast_df.empty else 0:,.0f}")
    with col3:
        st.metric("Pipeline/Deals", f"${pipeline_df['Pipeline Value'].sum() if not pipeline_df.empty else 0:,.0f}")
    with col4:
        st.metric("Revenue Forecast", f"${revenue_forecast_by_period['Forecast_Revenue'].sum() if not revenue_forecast_by_period.empty else 0:,.0f}")


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


def create_overlay_chart(demand_df, forecast_df, pipeline_df, revenue_forecast_df, category):
    """Create overlay chart with 4 lines."""
    
    fig = go.Figure()
    title_suffix = f" - {category}" if category != "All" else ""
    
    # Historical demand
    if not demand_df.empty:
        fig.add_trace(go.Bar(
            x=demand_df['Period'], y=demand_df['Amount'],
            name='Historical Demand', marker_color='#0033A1', opacity=0.7,
            hovertemplate='<b>Historical Demand</b><br>Period: %{x}<br>Revenue: $%{y:,.0f}<extra></extra>'
        ))
    
    # Demand Forecast
    if not forecast_df.empty:
        fig.add_trace(go.Scatter(
            x=forecast_df['Period'], y=forecast_df['Forecast'],
            mode='lines+markers', name='Demand Forecast',
            line=dict(color='#22C55E', width=3, dash='dash'),
            hovertemplate='<b>Demand Forecast</b><br>Period: %{x}<br>Forecast: $%{y:,.0f}<extra></extra>'
        ))
        
        # Confidence interval
        fig.add_trace(go.Scatter(
            x=forecast_df['Period'].tolist() + forecast_df['Period'].tolist()[::-1],
            y=forecast_df['Upper'].tolist() + forecast_df['Lower'].tolist()[::-1],
            fill='toself', fillcolor='rgba(34, 197, 94, 0.15)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Forecast CI (85%)', showlegend=True, hoverinfo='skip'
        ))
    
    # Pipeline
    if pipeline_df is not None and not pipeline_df.empty and 'Pipeline Value' in pipeline_df.columns:
        fig.add_trace(go.Scatter(
            x=pipeline_df['Period'], y=pipeline_df['Pipeline Value'],
            mode='lines+markers', name='Deals Pipeline',
            line=dict(color='#F59E0B', width=3), marker=dict(symbol='diamond', size=8),
            hovertemplate='<b>Deals Pipeline</b><br>Period: %{x}<br>Value: $%{y:,.0f}<extra></extra>'
        ))
    
    # Revenue Forecast
    if revenue_forecast_df is not None and not revenue_forecast_df.empty and 'Forecast_Revenue' in revenue_forecast_df.columns:
        fig.add_trace(go.Scatter(
            x=revenue_forecast_df['Period'], y=revenue_forecast_df['Forecast_Revenue'],
            mode='lines+markers', name='Revenue Plan (Top-Down)',
            line=dict(color='#8B5CF6', width=3), marker=dict(symbol='star', size=10),
            hovertemplate='<b>Revenue Plan (Top-Down)</b><br>Period: %{x}<br>Forecast: $%{y:,.0f}<extra></extra>'
        ))
    
    fig.update_layout(
        title=f'Demand & Pipeline Overlay{title_suffix}',
        xaxis_title='Period', yaxis_title='Revenue ($)',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=500
    )
    fig.update_yaxes(tickformat='$,.0f')
    
    return fig


# =============================================================================
# TOP-DOWN FORECAST TAB
# =============================================================================

@st.cache_data(ttl=300)
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


def render_topdown_forecast_tab(category):
    """Render Top-Down Forecast tab."""
    
    st.markdown("### 📋 Top-Down Item Forecast Allocation")
    
    pivot_units, pivot_revenue = get_forecast_pivot_data(category)
    
    if pivot_units is None:
        st.warning("No item-level forecast data available.")
        return
    
    # Sort period columns
    period_cols = sorted([c for c in pivot_units.columns if c not in ['Item', 'Category']])
    display_cols = ['Item', 'Category'] + period_cols
    
    st.markdown("#### Forecasted Units by SKU and Period")
    units_display = pivot_units[display_cols].copy()
    for col in period_cols:
        units_display[col] = units_display[col].apply(lambda x: f"{x:,.0f}")
    st.dataframe(units_display, use_container_width=True, hide_index=True, height=350)
    
    st.markdown("#### Forecasted Revenue by SKU and Period")
    rev_display = pivot_revenue[display_cols].copy()
    for col in period_cols:
        rev_display[col] = rev_display[col].apply(lambda x: f"${x:,.0f}")
    st.dataframe(rev_display, use_container_width=True, hide_index=True, height=350)


# =============================================================================
# SETTINGS TAB
# =============================================================================

def render_settings_tab():
    """Render Settings tab."""
    
    st.markdown("### ⚙️ Operations Settings")
    
    # Case Quantities
    st.markdown("#### 📦 Case Quantities by Category")
    
    categories = ['Calyx Cure', 'Plastic Lids', 'Plastic Bases', 'Glass Bases',
                  'Shrink Bands', 'Tray Inserts', 'Tray Frames', 'Tubes']
    
    case_df = pd.DataFrame([
        {'Category': cat, 'Units per Case': st.session_state.ops_case_quantities.get(cat, 1)}
        for cat in categories
    ])
    
    edited_case_df = st.data_editor(
        case_df,
        column_config={
            "Category": st.column_config.TextColumn("Category", disabled=True),
            "Units per Case": st.column_config.NumberColumn("Units per Case", min_value=1, max_value=100000)
        },
        hide_index=True, use_container_width=True, key="case_qty_editor"
    )
    
    if st.button("💾 Save Case Quantities"):
        for _, row in edited_case_df.iterrows():
            st.session_state.ops_case_quantities[row['Category']] = int(row['Units per Case'])
        st.success("Saved!")
        st.cache_data.clear()
    
    st.markdown("---")
    
    # Item Consolidation
    st.markdown("#### 🔗 Item Consolidation")
    
    consolidations = st.session_state.ops_item_consolidation
    if consolidations:
        st.dataframe(pd.DataFrame([{'Child SKU': k, 'Parent SKU': v} for k, v in consolidations.items()]),
                     hide_index=True, use_container_width=True)
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        child_sku = st.text_input("Child SKU", key="child_sku_input")
    with col2:
        parent_sku = st.text_input("Parent SKU", key="parent_sku_input")
    with col3:
        st.write("")
        if st.button("➕ Add"):
            if child_sku and parent_sku:
                st.session_state.ops_item_consolidation[child_sku.strip()] = parent_sku.strip()
                st.success(f"Added: {child_sku} → {parent_sku}")
                st.cache_data.clear()
                st.rerun()
    
    if consolidations:
        to_remove = st.selectbox("Remove consolidation:", list(consolidations.keys()), key="remove_select")
        if st.button("🗑️ Remove"):
            del st.session_state.ops_item_consolidation[to_remove]
            st.cache_data.clear()
            st.rerun()


# =============================================================================
# COVERAGE ANALYSIS TAB
# =============================================================================

def render_coverage_tab(filtered, amount_col, product_type_col):
    """Render Coverage Analysis tab."""
    
    st.markdown("### 📊 Pipeline Coverage Analysis")
    
    if filtered.empty or product_type_col is None:
        st.warning("No data available.")
        return
    
    cat_series = get_column_as_series(filtered, product_type_col)
    amt_series = get_column_as_series(filtered, amount_col)
    
    if cat_series is None or amt_series is None:
        return
    
    by_category = pd.DataFrame({
        'Category': cat_series,
        'Amount': pd.to_numeric(amt_series, errors='coerce').fillna(0)
    }).groupby('Category')['Amount'].sum().reset_index()
    
    by_category = by_category.sort_values('Amount', ascending=False)
    
    fig = go.Figure(go.Bar(
        x=by_category['Category'].head(15),
        y=by_category['Amount'].head(15),
        marker_color='#0033A1'
    ))
    fig.update_layout(title='Revenue by Product Category', height=400)
    fig.update_yaxes(tickformat='$,.0f')
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# INVENTORY STATUS TAB
# =============================================================================

def render_inventory_tab(inventory, items, selected_category, selected_item):
    """Render Inventory Status tab with filtering."""
    
    st.markdown("### 📦 Inventory Status")
    
    if inventory is None or inventory.empty:
        st.info("No inventory data available.")
        return
    
    df = inventory.copy()
    inv_item_col = find_column(df, ['item', 'sku', 'name'])
    
    if inv_item_col is None:
        st.warning("Item column not found.")
        return
    
    # Filter by category using items table
    if selected_category != "All" and items is not None and not items.empty:
        items_item_col = find_column(items, ['item', 'sku', 'name'])
        items_cat_col = find_column(items, ['product type', 'calyx', 'category'])
        
        if items_item_col and items_cat_col:
            item_cat_map = dict(zip(
                items[items_item_col].astype(str).str.strip(),
                items[items_cat_col].astype(str).str.strip()
            ))
            inv_items = get_column_as_series(df, inv_item_col)
            if inv_items is not None:
                df = df[inv_items.astype(str).str.strip().map(item_cat_map) == selected_category]
    
    # Filter by specific item
    if selected_item != "All":
        inv_items = get_column_as_series(df, inv_item_col)
        if inv_items is not None:
            df = df[inv_items.astype(str).str.strip() == selected_item]
    
    if df.empty:
        st.info("No inventory data for selected filters.")
        return
    
    st.dataframe(df, use_container_width=True, hide_index=True, height=400)


# =============================================================================
# SKU DEEP DIVE TAB
# =============================================================================

def render_sku_deep_dive(filtered, item_col, amount_col, qty_col):
    """Render SKU Deep Dive tab."""
    
    st.markdown("### 🔍 SKU Deep Dive")
    
    if filtered.empty or item_col is None:
        st.warning("Insufficient data.")
        return
    
    item_series = get_column_as_series(filtered, item_col)
    amt_series = get_column_as_series(filtered, amount_col)
    
    if item_series is None or amt_series is None:
        return
    
    temp_df = pd.DataFrame({
        'Item': item_series,
        'Amount': pd.to_numeric(amt_series, errors='coerce').fillna(0)
    })
    
    if qty_col:
        qty_series = get_column_as_series(filtered, qty_col)
        if qty_series is not None:
            temp_df['Quantity'] = pd.to_numeric(qty_series, errors='coerce').fillna(0)
    
    by_item = temp_df.groupby('Item').agg({
        'Amount': 'sum',
        'Quantity': 'sum' if 'Quantity' in temp_df.columns else 'count'
    }).reset_index()
    by_item.columns = ['Item', 'Revenue', 'Units']
    by_item = by_item.sort_values('Revenue', ascending=False).head(25)
    
    fig = go.Figure(go.Bar(x=by_item['Item'].head(10), y=by_item['Revenue'].head(10), marker_color='#0033A1'))
    fig.update_layout(title='Top 10 SKUs by Revenue', height=400)
    fig.update_yaxes(tickformat='$,.0f')
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)
    
    display_df = by_item.copy()
    display_df['Revenue'] = display_df['Revenue'].apply(lambda x: f"${x:,.0f}")
    display_df['Units'] = display_df['Units'].apply(lambda x: f"{x:,.0f}")
    st.dataframe(display_df, hide_index=True, use_container_width=True)
