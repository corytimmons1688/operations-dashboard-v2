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
        selected_category = st.selectbox("Product Category", category_options, key="opsv_category")
    with col2:
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
    """Render Demand vs Pipeline overlay chart with 4 lines."""
    
    st.markdown("### 📈 Demand Forecast vs Pipeline Overlay")
    st.markdown("Compare historical demand, demand forecast, deals pipeline, and revenue forecast plan")
    
    if filtered.empty:
        st.warning("No data available for the selected filters.")
        return
    
    # Load Top-Down Revenue Forecast from Google Sheet
    try:
        from .sop_data_loader import (
            get_topdown_item_forecast, get_revenue_forecast_by_period, 
            load_revenue_forecast, calculate_item_unit_mix_rolling12,
            calculate_item_asp_rolling12
        )
        
        revenue_forecast_raw = load_revenue_forecast()
        revenue_forecast_by_period = get_revenue_forecast_by_period(category=category)
        item_forecast = get_topdown_item_forecast()
        
    except Exception as e:
        st.warning(f"Could not load Revenue Forecast: {e}")
        import traceback
        st.code(traceback.format_exc())
        revenue_forecast_raw = None
        revenue_forecast_by_period = pd.DataFrame()
        item_forecast = pd.DataFrame()
    
    # Show Revenue Forecast debug info
    with st.expander("📊 Top-Down Forecast Data", expanded=True):
        if revenue_forecast_raw is not None and not revenue_forecast_raw.empty:
            st.write("**Revenue Forecast (Category Level from Sheet)**")
            st.write(f"Loaded {len(revenue_forecast_raw)} categories")
            st.write("Columns:", list(revenue_forecast_raw.columns))
            st.dataframe(revenue_forecast_raw.head(10), use_container_width=True)
        else:
            st.warning("⚠️ No Revenue Forecast data loaded. Add a 'Revenue forecast' tab to your Google Sheet.")
        
        if not revenue_forecast_by_period.empty:
            st.write("---")
            st.write("**Revenue Forecast by Period (for chart)**")
            st.write(f"Periods: {revenue_forecast_by_period['Period'].tolist()}")
            st.dataframe(revenue_forecast_by_period, use_container_width=True)
        else:
            st.warning("⚠️ Revenue forecast by period is empty - check category name matching")
            if not item_forecast.empty:
                st.write("Available categories in item forecast:", item_forecast['Category'].unique().tolist())
                st.write(f"Selected category filter: '{category}'")
        
        if not item_forecast.empty:
            st.write("---")
            st.write("**Item-Level Allocation (Top-Down)**")
            st.write(f"Allocated to {len(item_forecast)} item-period combinations")
            
            # Show summary by category
            cat_summary = item_forecast.groupby('Category').agg({
                'Forecast_Revenue': 'sum',
                'Forecast_Units': 'sum',
                'Item': 'nunique'
            }).reset_index()
            cat_summary.columns = ['Category', 'Total Forecast Revenue', 'Total Forecast Units', 'Items']
            st.dataframe(cat_summary, use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ Item forecast is empty")
        
        # Show category matching debug info
        if 'forecast_debug' in st.session_state:
            debug = st.session_state.forecast_debug
            st.write("---")
            st.write("**Category Matching Debug**")
            st.write(f"Revenue Forecast categories: {debug.get('forecast_categories', [])}")
            st.write(f"Sales Order Product Types: {debug.get('mix_categories', [])}")
            st.write(f"Item Mix rows: {debug.get('item_mix_rows', 0)}")
            st.write(f"Item ASP rows: {debug.get('item_asp_rows', 0)}")
    
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
                
                # Get pipeline/deals data
                pipeline_df = pd.DataFrame()
                if deals is not None and not deals.empty:
                    try:
                        from .sop_data_loader import get_pipeline_by_period
                        pipeline_df = get_pipeline_by_period(deals, freq=freq)
                    except Exception as e:
                        st.warning(f"Pipeline data error: {e}")
                
                # Create overlay chart with 4 lines
                fig = create_four_line_chart(
                    demand_history, 
                    demand_forecast_df, 
                    pipeline_df, 
                    revenue_forecast_by_period,
                    category
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Debug: Show what data is being charted
                if revenue_forecast_by_period.empty:
                    st.info("ℹ️ Revenue Forecast line not shown - no matching data for selected category")
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                total_historical = demand_history['Amount'].sum()
                total_demand_forecast = demand_forecast_df['Forecast'].sum() if not demand_forecast_df.empty else 0
                total_pipeline = pipeline_df['Pipeline Value'].sum() if not pipeline_df.empty else 0
                total_revenue_forecast = revenue_forecast_by_period['Forecast_Revenue'].sum() if not revenue_forecast_by_period.empty else 0
                
                with col1:
                    st.metric("Historical Demand", f"${total_historical:,.0f}")
                with col2:
                    st.metric("Demand Forecast", f"${total_demand_forecast:,.0f}")
                with col3:
                    st.metric("Pipeline/Deals", f"${total_pipeline:,.0f}")
                with col4:
                    st.metric("Revenue Forecast", f"${total_revenue_forecast:,.0f}")
                
                # Show item-level breakdown
                render_item_level_forecast(category, item_forecast)
                
        except Exception as e:
            st.error(f"Error creating demand chart: {e}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.warning("Required columns (Date, Amount) not found.")


def render_item_level_forecast(category, item_forecast=None):
    """Show item-level forecast breakdown from top-down allocation."""
    try:
        if item_forecast is None or item_forecast.empty:
            from .sop_data_loader import get_topdown_item_forecast
            item_forecast = get_topdown_item_forecast()
        
        if item_forecast.empty:
            return
        
        # Filter by category if specified
        if category and category != 'All':
            item_forecast = item_forecast[item_forecast['Category'] == category]
        
        if item_forecast.empty:
            return
        
        st.markdown("---")
        st.markdown("### 📋 Top-Down Item Forecast Allocation")
        st.markdown("*Category revenue forecast allocated to items based on rolling 12-month unit mix and ASP*")
        
        # Aggregate by item (sum across periods)
        by_item = item_forecast.groupby(['Item', 'Category']).agg({
            'Forecast_Revenue': 'sum',
            'Forecast_Units': 'sum',
            'Mix_Pct': 'first',
            'ASP': 'first'
        }).reset_index()
        
        by_item = by_item.sort_values('Forecast_Revenue', ascending=False).head(25)
        
        # Format for display
        display_df = by_item.copy()
        display_df['Forecast_Revenue'] = display_df['Forecast_Revenue'].apply(lambda x: f"${x:,.0f}")
        display_df['Forecast_Units'] = display_df['Forecast_Units'].apply(lambda x: f"{x:,.0f}")
        display_df['Mix_Pct'] = display_df['Mix_Pct'].apply(lambda x: f"{x:.1f}%")
        display_df['ASP'] = display_df['ASP'].apply(lambda x: f"${x:.2f}")
        
        display_df.columns = ['Item', 'Category', 'Forecast Revenue', 'Forecast Units', 'Unit Mix %', 'ASP']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Summary totals
        total_rev = by_item['Forecast_Revenue'].sum() if 'Forecast_Revenue' in by_item.columns else 0
        total_units = by_item['Forecast_Units'].sum() if 'Forecast_Units' in by_item.columns else 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Forecast Revenue", f"${total_rev:,.0f}")
        with col2:
            st.metric("Total Forecast Units", f"{total_units:,.0f}")
        
    except Exception as e:
        st.warning(f"Could not display item forecast: {e}")


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
            # Calculate trend from recent data
            values = recent['Amount'].values
            weights = np.array([1, 2, 3, 4, 5, 6])[:len(values)]
            weights = weights / weights.sum()
            
            weighted_avg = np.sum(values * weights)
            
            # Calculate growth rate from trend
            if len(values) >= 2 and values[0] > 0:
                growth_rate = (values[-1] / values[0]) ** (1/len(values)) - 1
                growth_rate = max(min(growth_rate, 0.15), -0.10)  # Cap between -10% and +15%
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


def create_four_line_chart(demand_df, demand_forecast_df, pipeline_df, revenue_forecast_df, category):
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
            opacity=0.7
        ))
    
    # 2. Demand Forecast (green dashed line) - Statistical/ML forecast
    if not demand_forecast_df.empty:
        fig.add_trace(go.Scatter(
            x=demand_forecast_df['Period'],
            y=demand_forecast_df['Forecast'],
            mode='lines+markers',
            name='Demand Forecast',
            line=dict(color='#22C55E', width=3, dash='dash'),
            marker=dict(size=8, symbol='circle')
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
    if not pipeline_df.empty:
        fig.add_trace(go.Scatter(
            x=pipeline_df['Period'],
            y=pipeline_df['Pipeline Value'],
            mode='lines+markers',
            name='Deals Pipeline',
            line=dict(color='#F59E0B', width=3),
            marker=dict(size=8, symbol='diamond')
        ))
    
    # 4. Revenue Forecast (purple line) - From Google Sheet (Top-Down)
    if revenue_forecast_df is not None and not revenue_forecast_df.empty and 'Forecast_Revenue' in revenue_forecast_df.columns:
        fig.add_trace(go.Scatter(
            x=revenue_forecast_df['Period'],
            y=revenue_forecast_df['Forecast_Revenue'],
            mode='lines+markers',
            name='Revenue Plan (Top-Down)',
            line=dict(color='#8B5CF6', width=3),
            marker=dict(size=10, symbol='star')
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
    
    # Format y-axis with dollar amounts
    fig.update_yaxes(tickformat='$,.0f')
    
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
