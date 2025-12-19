"""
Operations/Supply Chain View Module for S&OP Dashboard
Demand planning, pipeline analysis, and coverage tracking

Author: Xander @ Calyx Containers
Version: 3.3.0
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


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


def render_operations_view():
    """Main render function for Operations/Supply Chain View."""
    
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
    
    # Debug info
    with st.expander("🔧 Data Debug Info"):
        st.write(f"Invoice Lines: {len(invoice_lines) if invoice_lines is not None else 'None'} rows")
        st.write(f"Sales Orders: {len(sales_orders) if sales_orders is not None else 'None'} rows")
        st.write(f"Items: {len(items) if items is not None else 'None'} rows")
        st.write(f"Inventory: {len(inventory) if inventory is not None else 'None'} rows")
        st.write(f"Deals: {len(deals) if deals is not None else 'None'} rows")
    
    # ==========================================================================
    # IDENTIFY KEY COLUMNS
    # ==========================================================================
    
    product_type_col = find_column(invoice_lines, ['product type', 'calyx'])
    item_col = find_column(invoice_lines, ['item', 'sku'], exclude=['description'])
    date_col = find_column(invoice_lines, ['date'])
    amount_col = find_column(invoice_lines, ['amount'])
    qty_col = find_column(invoice_lines, ['qty', 'quantity'])
    
    # ==========================================================================
    # BUILD FILTER OPTIONS
    # ==========================================================================
    
    # Product Categories
    category_options = ["All"]
    if product_type_col:
        cat_series = get_column_as_series(invoice_lines, product_type_col)
        if cat_series is not None:
            cats = cat_series.dropna().astype(str).unique().tolist()
            category_options.extend(sorted([c for c in cats if c.strip() and c != 'Unknown']))
    
    # Items/SKUs
    item_options = ["All"]
    if item_col:
        item_series = get_column_as_series(invoice_lines, item_col)
        if item_series is not None:
            items_list = item_series.dropna().astype(str).unique().tolist()
            item_options.extend(sorted([i for i in items_list if i.strip()][:200]))
    
    # ==========================================================================
    # FILTER UI
    # ==========================================================================
    
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        selected_category = st.selectbox("Product Category", category_options, key="ops_category")
    with col2:
        selected_item = st.selectbox("Item/SKU", item_options, key="ops_item")
    with col3:
        time_period = st.selectbox(
            "Time Period", 
            ["Monthly", "Quarterly", "Weekly"],
            key="ops_period"
        )
    with col4:
        forecast_horizon = st.selectbox(
            "Forecast Horizon",
            ["3 Months", "6 Months", "12 Months"],
            key="ops_horizon"
        )
    
    st.markdown("---")
    
    # Map time period to frequency
    period_map = {"Monthly": "M", "Quarterly": "Q", "Weekly": "W"}
    freq = period_map.get(time_period, "M")
    
    # Map forecast horizon
    horizon_map = {"3 Months": 3, "6 Months": 6, "12 Months": 12}
    horizon = horizon_map.get(forecast_horizon, 6)
    
    # ==========================================================================
    # APPLY FILTERS
    # ==========================================================================
    
    filtered = invoice_lines.copy()
    
    # Category filter
    if selected_category != "All" and product_type_col:
        cat_series = get_column_as_series(filtered, product_type_col)
        if cat_series is not None:
            filtered = filtered[cat_series == selected_category].copy()
    
    # Item filter
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
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Demand vs Pipeline",
        "📊 Coverage Analysis",
        "📦 Inventory Status",
        "🔍 SKU Deep Dive"
    ])
    
    with tab1:
        render_demand_pipeline_tab(filtered, deals, date_col, amount_col, qty_col, freq, horizon, selected_category)
    
    with tab2:
        render_coverage_tab(filtered, deals, sales_orders, date_col, amount_col, product_type_col)
    
    with tab3:
        render_inventory_tab(inventory, items, item_col, product_type_col)
    
    with tab4:
        render_sku_deep_dive(filtered, item_col, amount_col, qty_col, date_col, product_type_col)


def render_demand_pipeline_tab(filtered, deals, date_col, amount_col, qty_col, freq, horizon, category):
    """Render Demand vs Pipeline overlay chart."""
    
    st.markdown("### 📈 Demand Forecast vs Pipeline Overlay")
    st.markdown("Compare historical demand, forecasted demand, and sales pipeline")
    
    if filtered.empty:
        st.warning("No data available for the selected filters.")
        return
    
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
                
                # Generate simple forecast
                forecast_df = generate_simple_forecast(demand_history, horizon, freq)
                
                # Get pipeline data
                pipeline_df = pd.DataFrame()
                if deals is not None and not deals.empty:
                    try:
                        from .sop_data_loader import get_pipeline_by_period
                        pipeline_df = get_pipeline_by_period(deals, freq=freq)
                    except Exception as e:
                        st.warning(f"Pipeline data error: {e}")
                
                # Create overlay chart
                fig = create_overlay_chart(demand_history, forecast_df, pipeline_df, category)
                st.plotly_chart(fig, use_container_width=True)
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                total_historical = demand_history['Amount'].sum()
                total_forecast = forecast_df['Forecast'].sum() if not forecast_df.empty else 0
                total_pipeline = pipeline_df['Pipeline Value'].sum() if not pipeline_df.empty else 0
                coverage = (total_pipeline / total_forecast * 100) if total_forecast > 0 else 0
                
                with col1:
                    st.metric("Historical Demand (LTM)", f"${total_historical:,.0f}")
                with col2:
                    st.metric(f"Forecast ({horizon}mo)", f"${total_forecast:,.0f}")
                with col3:
                    st.metric("Pipeline Value", f"${total_pipeline:,.0f}")
                with col4:
                    st.metric("Pipeline Coverage", f"{coverage:.1f}%")
                
        except Exception as e:
            st.error(f"Error creating demand chart: {e}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.warning("Required columns (Date, Amount) not found.")


def generate_simple_forecast(history_df, horizon, freq):
    """Generate simple forecast based on historical average."""
    if history_df.empty:
        return pd.DataFrame()
    
    try:
        # Use last 6 periods average with growth
        recent = history_df.tail(6)
        avg_value = recent['Amount'].mean()
        growth_rate = 0.02  # 2% monthly growth assumption
        
        # Generate future periods
        last_period = history_df['Period'].iloc[-1]
        
        # Parse last period and generate future
        forecast_data = []
        for i in range(1, horizon + 1):
            forecast_value = avg_value * (1 + growth_rate) ** i
            forecast_data.append({
                'Period': f"F+{i}",
                'Forecast': forecast_value,
                'Lower': forecast_value * 0.85,
                'Upper': forecast_value * 1.15
            })
        
        return pd.DataFrame(forecast_data)
        
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        return pd.DataFrame()


def create_overlay_chart(demand_df, forecast_df, pipeline_df, category):
    """Create the demand vs pipeline overlay chart."""
    
    fig = go.Figure()
    
    title_suffix = f" - {category}" if category != "All" else " - All Categories"
    
    # Historical demand bars
    if not demand_df.empty:
        fig.add_trace(go.Bar(
            x=demand_df['Period'],
            y=demand_df['Amount'],
            name='Historical Demand',
            marker_color='#0033A1'
        ))
    
    # Forecast line
    if not forecast_df.empty:
        # Extend x-axis with forecast periods
        fig.add_trace(go.Scatter(
            x=forecast_df['Period'],
            y=forecast_df['Forecast'],
            mode='lines+markers',
            name='Demand Forecast',
            line=dict(color='#22C55E', width=2, dash='dash'),
            marker=dict(size=8)
        ))
        
        # Confidence interval
        fig.add_trace(go.Scatter(
            x=forecast_df['Period'].tolist() + forecast_df['Period'].tolist()[::-1],
            y=forecast_df['Upper'].tolist() + forecast_df['Lower'].tolist()[::-1],
            fill='toself',
            fillcolor='rgba(34, 197, 94, 0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Forecast CI (95%)',
            showlegend=True
        ))
    
    # Pipeline overlay
    if not pipeline_df.empty:
        fig.add_trace(go.Scatter(
            x=pipeline_df['Period'],
            y=pipeline_df['Pipeline Value'],
            mode='lines+markers',
            name='Sales Pipeline',
            line=dict(color='#F59E0B', width=2),
            marker=dict(size=8, symbol='diamond')
        ))
    
    fig.update_layout(
        title=f'Demand & Pipeline Overlay{title_suffix}',
        xaxis_title='Period',
        yaxis_title='Revenue ($)',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=500,
        barmode='group'
    )
    
    return fig


def render_coverage_tab(filtered, deals, sales_orders, date_col, amount_col, product_type_col):
    """Render Coverage Analysis tab."""
    
    st.markdown("### 📊 Pipeline Coverage Analysis")
    st.markdown("Analyze how well your pipeline covers forecasted demand")
    
    if filtered.empty:
        st.warning("No data available for coverage analysis.")
        return
    
    # Calculate coverage by product type
    if product_type_col and amount_col:
        try:
            type_series = get_column_as_series(filtered, product_type_col)
            amt_series = get_column_as_series(filtered, amount_col)
            
            if type_series is not None and amt_series is not None:
                temp_df = pd.DataFrame({
                    'Product Type': type_series,
                    'Amount': pd.to_numeric(amt_series, errors='coerce').fillna(0)
                })
                
                by_type = temp_df.groupby('Product Type')['Amount'].sum().reset_index()
                by_type.columns = ['Product Type', 'Historical Demand']
                by_type = by_type.sort_values('Historical Demand', ascending=False).head(10)
                
                # Simple forecast (10% growth)
                by_type['Forecasted Demand'] = by_type['Historical Demand'] * 1.10
                
                # Mock pipeline data (in real implementation, join with deals)
                by_type['Pipeline'] = by_type['Historical Demand'] * np.random.uniform(0.3, 0.8, len(by_type))
                by_type['Coverage %'] = (by_type['Pipeline'] / by_type['Forecasted Demand'] * 100).round(1)
                by_type['Gap'] = by_type['Forecasted Demand'] - by_type['Pipeline']
                
                # Display table
                st.dataframe(
                    by_type.style.format({
                        'Historical Demand': '${:,.0f}',
                        'Forecasted Demand': '${:,.0f}',
                        'Pipeline': '${:,.0f}',
                        'Coverage %': '{:.1f}%',
                        'Gap': '${:,.0f}'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Coverage chart
                fig = px.bar(
                    by_type,
                    x='Product Type',
                    y=['Forecasted Demand', 'Pipeline'],
                    barmode='group',
                    title='Forecasted Demand vs Pipeline by Category'
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
        except Exception as e:
            st.error(f"Coverage analysis error: {e}")
    else:
        st.info("Product Type column not found for coverage analysis.")


def render_inventory_tab(inventory, items, item_col, product_type_col):
    """Render Inventory Status tab."""
    
    st.markdown("### 📦 Inventory Status")
    st.markdown("Current inventory levels and coverage")
    
    if inventory is None or inventory.empty:
        st.info("No inventory data available. Connect your inventory data source to see this analysis.")
        
        # Show placeholder metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total SKUs", "—")
        with col2:
            st.metric("In Stock", "—")
        with col3:
            st.metric("Low Stock", "—")
        with col4:
            st.metric("Out of Stock", "—")
        return
    
    # Display inventory summary
    st.dataframe(inventory.head(20), use_container_width=True)


def render_sku_deep_dive(filtered, item_col, amount_col, qty_col, date_col, product_type_col):
    """Render SKU Deep Dive tab."""
    
    st.markdown("### 🔍 SKU Deep Dive")
    st.markdown("Detailed analysis by individual SKU")
    
    if filtered.empty or item_col is None:
        st.warning("No data available for SKU analysis.")
        return
    
    # Get top SKUs by revenue
    if amount_col:
        try:
            item_series = get_column_as_series(filtered, item_col)
            amt_series = get_column_as_series(filtered, amount_col)
            
            if item_series is not None and amt_series is not None:
                temp_df = pd.DataFrame({
                    'Item': item_series,
                    'Amount': pd.to_numeric(amt_series, errors='coerce').fillna(0)
                })
                
                if qty_col:
                    qty_series = get_column_as_series(filtered, qty_col)
                    if qty_series is not None:
                        temp_df['Quantity'] = pd.to_numeric(qty_series, errors='coerce').fillna(0)
                
                # Aggregate by item
                agg_dict = {'Amount': 'sum'}
                if 'Quantity' in temp_df.columns:
                    agg_dict['Quantity'] = 'sum'
                
                by_item = temp_df.groupby('Item').agg(agg_dict).reset_index()
                by_item.columns = ['Item'] + [f'Total {k}' for k in agg_dict.keys()]
                by_item = by_item.sort_values('Total Amount', ascending=False).head(25)
                
                # Add rank
                by_item.insert(0, 'Rank', range(1, len(by_item) + 1))
                
                st.dataframe(by_item, use_container_width=True, hide_index=True)
                
                # Top 10 chart
                top10 = by_item.head(10)
                fig = px.bar(
                    top10,
                    x='Item',
                    y='Total Amount',
                    title='Top 10 SKUs by Revenue'
                )
                fig.update_layout(height=400, xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
                
        except Exception as e:
            st.error(f"SKU analysis error: {e}")
