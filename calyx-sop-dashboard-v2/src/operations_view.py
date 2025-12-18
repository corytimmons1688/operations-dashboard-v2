"""
Operations/Supply Chain View Module for S&OP Dashboard
Tab 2: Supply chain focused view with demand vs pipeline analysis

Features:
- Filter by Product Category, SKU
- Overlay chart: Historical demand, Forecasted demand, HubSpot pipeline, Revenue forecast
- Gap analysis: Forecast vs Pipeline coverage
- Inventory coverage analysis

Author: Xander @ Calyx Containers
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
import logging

from .sop_data_loader import (
    load_invoice_lines, load_sales_orders, load_items, load_inventory,
    load_deals, prepare_demand_history, prepare_revenue_history,
    get_pipeline_by_period, get_unique_product_types, get_unique_skus
)
from .forecasting_models import generate_forecast, blend_forecasts, allocate_topdown_forecast

logger = logging.getLogger(__name__)


def render_operations_view():
    """Main render function for Operations/Supply Chain View tab."""
    
    st.markdown("## 📦 Operations & Supply Chain View")
    st.markdown("Demand planning, pipeline analysis, and coverage tracking")
    
    # Load data
    with st.spinner("Loading operations data..."):
        invoice_lines = load_invoice_lines()
        sales_orders = load_sales_orders()
        items = load_items()
        inventory = load_inventory()
        deals = load_deals()
    
    if invoice_lines is None:
        st.error("Unable to load invoice data. Please check your data connection.")
        return
    
    # Sidebar filters
    st.sidebar.markdown("### 🔍 Operations Filters")
    
    # Product Category filter
    if items is not None and 'Calyx || Product Type' in items.columns:
        product_types = get_unique_product_types(items)
        selected_category = st.sidebar.selectbox(
            "Product Category",
            options=["All"] + product_types,
            key="ops_category_filter"
        )
    else:
        selected_category = "All"
    
    # SKU filter (restricted by category)
    if items is not None:
        if selected_category != "All" and 'Calyx || Product Type' in items.columns:
            filtered_items = items[items['Calyx || Product Type'] == selected_category]
            available_skus = filtered_items['SKU'].dropna().unique().tolist() if 'SKU' in filtered_items.columns else []
        else:
            available_skus = get_unique_skus(items)
    else:
        available_skus = []
    
    selected_sku = st.sidebar.selectbox(
        "Select SKU",
        options=["All"] + available_skus,
        key="ops_sku_filter"
    )
    
    # Forecast settings
    st.sidebar.markdown("### 📊 Forecast Settings")
    
    forecast_horizon = st.sidebar.selectbox(
        "Forecast Horizon",
        options=[3, 6, 9, 12, 18, 24],
        index=3,
        format_func=lambda x: f"{x} months",
        key="ops_forecast_horizon"
    )
    
    forecast_model = st.sidebar.selectbox(
        "Primary Forecast Model",
        options=['exponential_smoothing', 'arima', 'ml_random_forest'],
        format_func=lambda x: {
            'exponential_smoothing': 'Exponential Smoothing',
            'arima': 'ARIMA/SARIMA',
            'ml_random_forest': 'Machine Learning (RF)'
        }.get(x, x),
        key="ops_forecast_model"
    )
    
    st.sidebar.markdown("---")
    
    # Filter data
    filtered_invoices = filter_by_category_sku(
        invoice_lines, items, selected_category, selected_sku
    )
    
    if filtered_invoices.empty:
        st.warning("No data found for the selected filters.")
        return
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Demand vs Pipeline",
        "📊 Coverage Analysis",
        "📦 Inventory Status",
        "🔍 SKU Deep Dive"
    ])
    
    with tab1:
        render_demand_pipeline_overlay(
            filtered_invoices, deals, forecast_horizon, forecast_model, selected_category
        )
    
    with tab2:
        render_coverage_analysis(
            filtered_invoices, deals, sales_orders, forecast_horizon, forecast_model
        )
    
    with tab3:
        render_inventory_status(inventory, items, filtered_invoices, selected_category)
    
    with tab4:
        render_sku_deep_dive(filtered_invoices, items, forecast_horizon, forecast_model, selected_sku)


def filter_by_category_sku(
    invoice_lines: pd.DataFrame,
    items: pd.DataFrame,
    category: str,
    sku: str
) -> pd.DataFrame:
    """Filter invoice lines by product category and/or SKU."""
    df = invoice_lines.copy()
    
    # Filter by category via items lookup
    if category != "All" and items is not None:
        if 'Calyx || Product Type' in items.columns and 'SKU' in items.columns:
            category_skus = items[items['Calyx || Product Type'] == category]['SKU'].tolist()
            if 'Item' in df.columns:
                df = df[df['Item'].isin(category_skus)]
    
    # Filter by specific SKU
    if sku != "All" and 'Item' in df.columns:
        df = df[df['Item'] == sku]
    
    return df


def render_demand_pipeline_overlay(
    invoice_lines: pd.DataFrame,
    deals: pd.DataFrame,
    horizon: int,
    model: str,
    category: str
):
    """Render the main demand vs pipeline overlay chart."""
    
    st.markdown("### 📈 Demand Forecast vs Pipeline Overlay")
    st.markdown("Compare historical demand, forecasted demand, and sales pipeline")
    
    # Prepare historical demand
    date_col = 'Date'
    qty_col = 'Quantity'
    amount_col = 'Amount'
    
    df = invoice_lines.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])
    
    # Monthly aggregation
    df['Period'] = df[date_col].dt.to_period('M').dt.to_timestamp()
    
    # Demand (quantity)
    monthly_demand = df.groupby('Period')[qty_col].sum()
    
    # Revenue
    monthly_revenue = df.groupby('Period')[amount_col].sum() if amount_col in df.columns else None
    
    # Pipeline data
    pipeline_data = None
    if deals is not None and not deals.empty:
        pipeline_data = get_pipeline_by_period(deals, freq='MS')
    
    # Generate forecasts
    demand_forecast = None
    revenue_forecast = None
    
    if len(monthly_demand) >= 6:
        try:
            demand_forecast = generate_forecast(monthly_demand, model=model, horizon=horizon)
        except Exception as e:
            st.warning(f"Demand forecast failed: {str(e)}")
    
    if monthly_revenue is not None and len(monthly_revenue) >= 6:
        try:
            revenue_forecast = generate_forecast(monthly_revenue, model=model, horizon=horizon)
        except Exception as e:
            st.warning(f"Revenue forecast failed: {str(e)}")
    
    # Create overlay chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Historical Demand (bars)
    fig.add_trace(
        go.Bar(
            x=monthly_demand.index,
            y=monthly_demand.values,
            name='Historical Demand',
            marker_color='#3498db',
            opacity=0.7
        ),
        secondary_y=False
    )
    
    # Demand Forecast (line)
    if demand_forecast is not None:
        fig.add_trace(
            go.Scatter(
                x=demand_forecast.forecast.index,
                y=demand_forecast.forecast.values,
                mode='lines+markers',
                name='Demand Forecast',
                line=dict(color='#2ecc71', width=3, dash='dash'),
                marker=dict(size=8)
            ),
            secondary_y=False
        )
        
        # Confidence interval
        if demand_forecast.confidence_lower is not None:
            fig.add_trace(
                go.Scatter(
                    x=list(demand_forecast.forecast.index) + list(demand_forecast.forecast.index[::-1]),
                    y=list(demand_forecast.confidence_upper.values) + list(demand_forecast.confidence_lower.values[::-1]),
                    fill='toself',
                    fillcolor='rgba(46, 204, 113, 0.15)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name='Forecast CI (95%)',
                    showlegend=True
                ),
                secondary_y=False
            )
    
    # Pipeline (line on secondary axis)
    if pipeline_data is not None and not pipeline_data.empty:
        fig.add_trace(
            go.Scatter(
                x=pipeline_data['Period'],
                y=pipeline_data['Pipeline_Amount'],
                mode='lines+markers',
                name='Pipeline ($)',
                line=dict(color='#9b59b6', width=2),
                marker=dict(size=6)
            ),
            secondary_y=True
        )
    
    # Revenue Forecast (line on secondary axis)
    if revenue_forecast is not None:
        fig.add_trace(
            go.Scatter(
                x=revenue_forecast.forecast.index,
                y=revenue_forecast.forecast.values,
                mode='lines+markers',
                name='Revenue Forecast ($)',
                line=dict(color='#e74c3c', width=2, dash='dot'),
                marker=dict(size=6)
            ),
            secondary_y=True
        )
    
    # Layout
    fig.update_layout(
        title=f"Demand & Pipeline Overlay - {category if category != 'All' else 'All Categories'}",
        height=550,
        hovermode='x unified',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5
        ),
        barmode='overlay'
    )
    
    fig.update_xaxes(title_text="Period")
    fig.update_yaxes(title_text="Quantity", secondary_y=False)
    fig.update_yaxes(title_text="Revenue / Pipeline ($)", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary metrics
    st.markdown("---")
    st.markdown("#### Summary Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        last_3m_demand = monthly_demand.tail(3).sum()
        st.metric("Last 3M Demand", f"{last_3m_demand:,.0f}")
    
    with col2:
        if demand_forecast is not None:
            next_3m_forecast = demand_forecast.forecast.head(3).sum()
            pct_change = ((next_3m_forecast - last_3m_demand) / last_3m_demand * 100) if last_3m_demand > 0 else 0
            st.metric("Next 3M Forecast", f"{next_3m_forecast:,.0f}", delta=f"{pct_change:+.1f}%")
        else:
            st.metric("Next 3M Forecast", "N/A")
    
    with col3:
        if pipeline_data is not None and not pipeline_data.empty:
            total_pipeline = pipeline_data['Pipeline_Amount'].sum()
            st.metric("Total Pipeline", f"${total_pipeline:,.0f}")
        else:
            st.metric("Total Pipeline", "N/A")
    
    with col4:
        if demand_forecast is not None:
            st.metric("Forecast MAPE", f"{demand_forecast.metrics.get('MAPE', 0):.1f}%")
        else:
            st.metric("Forecast MAPE", "N/A")
    
    with col5:
        st.metric("Model Used", model.replace('_', ' ').title())
    
    # Gap analysis table
    if demand_forecast is not None and pipeline_data is not None and not pipeline_data.empty:
        st.markdown("---")
        st.markdown("#### Forecast vs Pipeline Gap Analysis")
        
        gap_analysis = create_gap_analysis(demand_forecast, pipeline_data, monthly_revenue)
        
        st.dataframe(gap_analysis, use_container_width=True, hide_index=True)


def create_gap_analysis(
    demand_forecast,
    pipeline_data: pd.DataFrame,
    monthly_revenue: pd.Series = None
) -> pd.DataFrame:
    """Create gap analysis between forecast and pipeline."""
    
    # Align periods
    forecast_periods = demand_forecast.forecast.index
    
    gap_data = []
    
    for period in forecast_periods[:6]:  # Next 6 months
        period_str = period.strftime('%Y-%m')
        
        # Forecast demand
        demand = demand_forecast.forecast.get(period, 0)
        
        # Pipeline for period
        pipeline = pipeline_data[pipeline_data['Period'] == period]['Pipeline_Amount'].sum()
        
        # Estimate revenue from demand (if we have historical revenue per unit)
        if monthly_revenue is not None and len(monthly_revenue) > 0:
            avg_rev_per_unit = monthly_revenue.sum() / max(1, monthly_revenue.index.size)
            estimated_revenue = demand * (avg_rev_per_unit / monthly_revenue.mean() if monthly_revenue.mean() > 0 else 0)
        else:
            estimated_revenue = 0
        
        # Gap
        gap = pipeline - estimated_revenue if estimated_revenue > 0 else 0
        coverage = (pipeline / estimated_revenue * 100) if estimated_revenue > 0 else 0
        
        gap_data.append({
            'Period': period_str,
            'Forecast Demand': f"{demand:,.0f}",
            'Pipeline $': f"${pipeline:,.0f}",
            'Gap $': f"${gap:,.0f}",
            'Coverage %': f"{coverage:.1f}%",
            'Status': '✅ Covered' if coverage >= 80 else '⚠️ At Risk' if coverage >= 50 else '🔴 Gap'
        })
    
    return pd.DataFrame(gap_data)


def render_coverage_analysis(
    invoice_lines: pd.DataFrame,
    deals: pd.DataFrame,
    sales_orders: pd.DataFrame,
    horizon: int,
    model: str
):
    """Render coverage analysis section."""
    
    st.markdown("### 📊 Coverage Analysis")
    st.markdown("Analyze forecast coverage by pipeline and pending orders")
    
    # Calculate historical metrics
    df = invoice_lines.copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # Monthly demand
    df['Period'] = df['Date'].dt.to_period('M').dt.to_timestamp()
    monthly_demand = df.groupby('Period')['Quantity'].sum()
    
    if len(monthly_demand) < 6:
        st.warning("Insufficient historical data for coverage analysis.")
        return
    
    # Generate forecast
    try:
        forecast_result = generate_forecast(monthly_demand, model=model, horizon=horizon)
    except Exception as e:
        st.error(f"Forecast failed: {str(e)}")
        return
    
    # Pending orders coverage
    pending_orders_qty = 0
    if sales_orders is not None and 'Status' in sales_orders.columns:
        pending_statuses = ['Pending Fulfillment', 'Pending Approval', 'Partially Fulfilled']
        pending = sales_orders[sales_orders['Status'].str.contains('|'.join(pending_statuses), case=False, na=False)]
        if 'Amount (Transaction Total)' in pending.columns:
            pending_value = pending['Amount (Transaction Total)'].sum()
        else:
            pending_value = 0
    else:
        pending_value = 0
    
    # Pipeline coverage
    pipeline_value = 0
    if deals is not None and 'Amount' in deals.columns:
        pipeline_value = deals['Amount'].sum()
    
    # Coverage metrics
    total_forecast = forecast_result.forecast.sum()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Forecast (Units)",
            f"{total_forecast:,.0f}",
            help=f"Next {horizon} months"
        )
    
    with col2:
        st.metric(
            "Pending Orders ($)",
            f"${pending_value:,.0f}",
            help="Orders awaiting fulfillment"
        )
    
    with col3:
        st.metric(
            "Pipeline ($)",
            f"${pipeline_value:,.0f}",
            help="Total HubSpot pipeline"
        )
    
    with col4:
        combined_coverage = pending_value + pipeline_value
        st.metric(
            "Total Coverage ($)",
            f"${combined_coverage:,.0f}",
            help="Pending + Pipeline"
        )
    
    st.markdown("---")
    
    # Coverage breakdown chart
    col1, col2 = st.columns(2)
    
    with col1:
        # Waterfall chart for coverage sources
        fig_waterfall = go.Figure(go.Waterfall(
            name="Coverage",
            orientation="v",
            x=["Forecast Gap", "Pending Orders", "Pipeline", "Remaining Gap"],
            y=[total_forecast * 100, -pending_value, -pipeline_value, 
               max(0, total_forecast * 100 - pending_value - pipeline_value)],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            increasing={"marker": {"color": "#e74c3c"}},
            decreasing={"marker": {"color": "#2ecc71"}},
            totals={"marker": {"color": "#3498db"}}
        ))
        
        fig_waterfall.update_layout(
            title="Coverage Sources (Estimated $)",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig_waterfall, use_container_width=True)
    
    with col2:
        # Coverage by month
        coverage_by_month = []
        
        for i, (period, forecast_val) in enumerate(forecast_result.forecast.items()):
            if i >= 6:
                break
            
            # Estimate monthly coverage (distribute evenly for simplicity)
            monthly_pending = pending_value / max(1, len(forecast_result.forecast))
            monthly_pipeline = pipeline_value / max(1, len(forecast_result.forecast))
            
            coverage_by_month.append({
                'Period': period.strftime('%b %Y'),
                'Forecast': forecast_val,
                'Covered': min(forecast_val, (monthly_pending + monthly_pipeline) / 100)
            })
        
        coverage_df = pd.DataFrame(coverage_by_month)
        
        fig_coverage = go.Figure()
        
        fig_coverage.add_trace(go.Bar(
            x=coverage_df['Period'],
            y=coverage_df['Forecast'],
            name='Forecast',
            marker_color='#3498db'
        ))
        
        fig_coverage.add_trace(go.Bar(
            x=coverage_df['Period'],
            y=coverage_df['Covered'],
            name='Covered',
            marker_color='#2ecc71'
        ))
        
        fig_coverage.update_layout(
            title="Monthly Coverage Status",
            height=400,
            barmode='overlay',
            legend=dict(orientation='h', y=1.1)
        )
        
        st.plotly_chart(fig_coverage, use_container_width=True)
    
    # Risk assessment
    st.markdown("---")
    st.markdown("#### Risk Assessment")
    
    if combined_coverage > 0:
        coverage_ratio = (combined_coverage / (total_forecast * 100)) * 100 if total_forecast > 0 else 0
        
        if coverage_ratio >= 80:
            st.success(f"✅ **Healthy Coverage**: {coverage_ratio:.1f}% of forecast is covered by pending orders and pipeline")
        elif coverage_ratio >= 50:
            st.warning(f"⚠️ **Moderate Risk**: {coverage_ratio:.1f}% coverage - consider increasing pipeline activity")
        else:
            st.error(f"🔴 **High Risk**: Only {coverage_ratio:.1f}% coverage - significant gap exists")


def render_inventory_status(
    inventory: pd.DataFrame,
    items: pd.DataFrame,
    invoice_lines: pd.DataFrame,
    category: str
):
    """Render inventory status section."""
    
    st.markdown("### 📦 Inventory Status")
    
    if inventory is None or inventory.empty:
        st.info("No inventory data available.")
        return
    
    # Filter by category if applicable
    if category != "All" and items is not None and 'Calyx || Product Type' in items.columns:
        category_items = items[items['Calyx || Product Type'] == category]
        if 'Name' in inventory.columns and 'Name' in category_items.columns:
            inventory = inventory[inventory['Name'].isin(category_items['Name'])]
    
    if inventory.empty:
        st.info(f"No inventory data for category: {category}")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_on_hand = inventory['On Hand'].sum() if 'On Hand' in inventory.columns else 0
        st.metric("Total On Hand", f"{total_on_hand:,.0f}")
    
    with col2:
        total_value = (inventory['On Hand'] * inventory['Average Cost']).sum() if 'On Hand' in inventory.columns and 'Average Cost' in inventory.columns else 0
        st.metric("Inventory Value", f"${total_value:,.2f}")
    
    with col3:
        sku_count = inventory['Name'].nunique() if 'Name' in inventory.columns else len(inventory)
        st.metric("Active SKUs", f"{sku_count:,}")
    
    with col4:
        # Calculate average days of supply
        if invoice_lines is not None and not invoice_lines.empty:
            # Get last 90 days demand
            df = invoice_lines.copy()
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            cutoff = datetime.now() - timedelta(days=90)
            recent_demand = df[df['Date'] >= cutoff]['Quantity'].sum()
            daily_demand = recent_demand / 90 if recent_demand > 0 else 1
            days_supply = total_on_hand / daily_demand
            st.metric("Days of Supply", f"{days_supply:.0f}")
        else:
            st.metric("Days of Supply", "N/A")
    
    st.markdown("---")
    
    # Inventory breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        # Top items by quantity
        if 'Name' in inventory.columns and 'On Hand' in inventory.columns:
            top_items = inventory.nlargest(10, 'On Hand')[['Name', 'On Hand', 'Average Cost']]
            top_items['Value'] = top_items['On Hand'] * top_items['Average Cost']
            
            fig_top = px.bar(
                top_items,
                x='Name',
                y='On Hand',
                color='Value',
                color_continuous_scale='Blues',
                title="Top 10 Items by Quantity"
            )
            fig_top.update_layout(height=400)
            fig_top.update_xaxes(tickangle=-45)
            
            st.plotly_chart(fig_top, use_container_width=True)
    
    with col2:
        # Low stock items
        if 'On Hand' in inventory.columns:
            low_stock = inventory[inventory['On Hand'] < 100].nsmallest(10, 'On Hand')
            
            if not low_stock.empty:
                fig_low = px.bar(
                    low_stock,
                    x='Name' if 'Name' in low_stock.columns else low_stock.index,
                    y='On Hand',
                    title="Low Stock Items (< 100 units)",
                    color_discrete_sequence=['#e74c3c']
                )
                fig_low.update_layout(height=400)
                fig_low.update_xaxes(tickangle=-45)
                
                st.plotly_chart(fig_low, use_container_width=True)
            else:
                st.info("No items with low stock (< 100 units)")
    
    # Full inventory table
    with st.expander("📋 Full Inventory Table"):
        display_cols = ['Name', 'Display Name', 'On Hand', 'Average Cost']
        display_cols = [c for c in display_cols if c in inventory.columns]
        
        display_df = inventory[display_cols].copy()
        if 'On Hand' in display_df.columns and 'Average Cost' in display_df.columns:
            display_df['Total Value'] = display_df['On Hand'] * display_df['Average Cost']
            display_df['Total Value'] = display_df['Total Value'].apply(lambda x: f"${x:,.2f}")
        if 'Average Cost' in display_df.columns:
            display_df['Average Cost'] = display_df['Average Cost'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "N/A")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_sku_deep_dive(
    invoice_lines: pd.DataFrame,
    items: pd.DataFrame,
    horizon: int,
    model: str,
    selected_sku: str
):
    """Render SKU-level deep dive analysis."""
    
    st.markdown("### 🔍 SKU Deep Dive")
    
    if selected_sku == "All":
        st.info("Select a specific SKU from the sidebar to view detailed analysis.")
        
        # Show top SKUs summary
        if 'Item' in invoice_lines.columns:
            st.markdown("#### Top SKUs by Volume")
            
            sku_summary = invoice_lines.groupby('Item').agg({
                'Quantity': 'sum',
                'Amount': 'sum',
                'Document Number': 'nunique'
            }).reset_index()
            sku_summary.columns = ['SKU', 'Total Quantity', 'Total Revenue', 'Order Count']
            sku_summary = sku_summary.sort_values('Total Quantity', ascending=False).head(20)
            
            # Format columns
            sku_summary['Total Revenue'] = sku_summary['Total Revenue'].apply(lambda x: f"${x:,.2f}")
            sku_summary['Total Quantity'] = sku_summary['Total Quantity'].apply(lambda x: f"{x:,.0f}")
            
            st.dataframe(sku_summary, use_container_width=True, hide_index=True)
        return
    
    # Single SKU analysis
    df = invoice_lines[invoice_lines['Item'] == selected_sku].copy() if 'Item' in invoice_lines.columns else invoice_lines.copy()
    
    if df.empty:
        st.warning(f"No data found for SKU: {selected_sku}")
        return
    
    # SKU details from items master
    sku_details = None
    if items is not None and 'SKU' in items.columns:
        sku_info = items[items['SKU'] == selected_sku]
        if not sku_info.empty:
            sku_details = sku_info.iloc[0]
    
    # Header info
    st.markdown(f"#### SKU: {selected_sku}")
    
    if sku_details is not None:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Description:** {sku_details.get('Description', 'N/A')}")
        with col2:
            st.markdown(f"**Product Type:** {sku_details.get('Calyx || Product Type', 'N/A')}")
        with col3:
            lead_time = sku_details.get('Purchase Lead Time', 'N/A')
            st.markdown(f"**Lead Time:** {lead_time} days" if lead_time != 'N/A' else "**Lead Time:** N/A")
    
    st.markdown("---")
    
    # Prepare time series
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    df['Period'] = df['Date'].dt.to_period('M').dt.to_timestamp()
    
    monthly_demand = df.groupby('Period')['Quantity'].sum()
    monthly_revenue = df.groupby('Period')['Amount'].sum() if 'Amount' in df.columns else None
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_qty = df['Quantity'].sum()
        st.metric("Total Quantity Sold", f"{total_qty:,.0f}")
    
    with col2:
        total_rev = df['Amount'].sum() if 'Amount' in df.columns else 0
        st.metric("Total Revenue", f"${total_rev:,.2f}")
    
    with col3:
        avg_price = total_rev / total_qty if total_qty > 0 else 0
        st.metric("Avg Price/Unit", f"${avg_price:,.2f}")
    
    with col4:
        order_count = df['Document Number'].nunique() if 'Document Number' in df.columns else 0
        st.metric("Order Count", f"{order_count:,}")
    
    st.markdown("---")
    
    # Forecast
    if len(monthly_demand) >= 6:
        try:
            forecast_result = generate_forecast(monthly_demand, model=model, horizon=horizon)
            
            # Chart
            fig = go.Figure()
            
            # Historical
            fig.add_trace(go.Scatter(
                x=monthly_demand.index,
                y=monthly_demand.values,
                mode='lines+markers',
                name='Historical',
                line=dict(color='#3498db', width=2)
            ))
            
            # Forecast
            fig.add_trace(go.Scatter(
                x=forecast_result.forecast.index,
                y=forecast_result.forecast.values,
                mode='lines+markers',
                name='Forecast',
                line=dict(color='#e74c3c', width=2, dash='dash')
            ))
            
            # Confidence interval
            if forecast_result.confidence_lower is not None:
                fig.add_trace(go.Scatter(
                    x=list(forecast_result.forecast.index) + list(forecast_result.forecast.index[::-1]),
                    y=list(forecast_result.confidence_upper.values) + list(forecast_result.confidence_lower.values[::-1]),
                    fill='toself',
                    fillcolor='rgba(231, 76, 60, 0.2)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name='95% CI'
                ))
            
            fig.update_layout(
                title=f"Demand Forecast: {selected_sku}",
                xaxis_title="Period",
                yaxis_title="Quantity",
                height=450,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Forecast table
            forecast_df = forecast_result.to_dataframe()
            forecast_df['Forecast'] = forecast_df['Forecast'].round(0)
            if 'Lower_CI' in forecast_df.columns:
                forecast_df['Lower_CI'] = forecast_df['Lower_CI'].round(0)
            if 'Upper_CI' in forecast_df.columns:
                forecast_df['Upper_CI'] = forecast_df['Upper_CI'].round(0)
            
            with st.expander("📋 Forecast Details"):
                st.dataframe(forecast_df, use_container_width=True, hide_index=True)
            
        except Exception as e:
            st.error(f"Forecast failed: {str(e)}")
    else:
        st.warning("Insufficient history for forecasting (need at least 6 months)")
    
    # Customer breakdown for this SKU
    if 'Correct Customer' in df.columns or 'Customer' in df.columns:
        st.markdown("---")
        st.markdown("#### Customer Breakdown")
        
        customer_col = 'Correct Customer' if 'Correct Customer' in df.columns else 'Customer'
        customer_summary = df.groupby(customer_col).agg({
            'Quantity': 'sum',
            'Amount': 'sum'
        }).reset_index()
        customer_summary = customer_summary.sort_values('Quantity', ascending=False).head(10)
        
        fig_cust = px.bar(
            customer_summary,
            x=customer_col,
            y='Quantity',
            color='Amount',
            color_continuous_scale='Greens',
            title=f"Top 10 Customers for {selected_sku}"
        )
        fig_cust.update_layout(height=350)
        fig_cust.update_xaxes(tickangle=-45)
        
        st.plotly_chart(fig_cust, use_container_width=True)
