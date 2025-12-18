"""
Purchase Order Forecast Module for S&OP Dashboard
Tab 4: PO planning, timing, and cash flow impact

Features:
- Generate planned PO dates based on demand forecast and lead times
- Expected arrival dates
- PO quantity and cost calculations
- Vendor assignment
- Payment timing
- Cash flow impact timeline
- Export-ready structure for Finance

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
    load_invoice_lines, load_items, load_vendors, load_inventory,
    load_sales_orders, calculate_lead_times, prepare_demand_history
)
from .forecasting_models import generate_forecast
from .scenario_planning import APPROVED_SCENARIO_KEY, SCENARIOS_KEY, load_scenario_forecast

logger = logging.getLogger(__name__)


# Default assumptions
DEFAULT_LEAD_TIME_DAYS = 30
DEFAULT_SAFETY_STOCK_DAYS = 14
DEFAULT_REORDER_POINT_DAYS = 45
DEFAULT_PAYMENT_TERMS_DAYS = 30


def render_po_forecast():
    """Main render function for Purchase Order Forecast tab."""
    
    st.markdown("## 📦 Purchase Order Forecast")
    st.markdown("Plan purchase orders based on demand forecast and inventory requirements")
    
    # Load data
    with st.spinner("Loading data..."):
        invoice_lines = load_invoice_lines()
        items = load_items()
        vendors = load_vendors()
        inventory = load_inventory()
        sales_orders = load_sales_orders()
    
    if invoice_lines is None:
        st.error("Unable to load data. Please check your data connection.")
        return
    
    # Sidebar settings
    st.sidebar.markdown("### ⚙️ PO Planning Settings")
    
    planning_horizon = st.sidebar.selectbox(
        "Planning Horizon",
        options=[3, 6, 9, 12],
        index=1,
        format_func=lambda x: f"{x} months",
        key="po_planning_horizon"
    )
    
    safety_stock_days = st.sidebar.slider(
        "Safety Stock (Days)",
        min_value=0,
        max_value=60,
        value=DEFAULT_SAFETY_STOCK_DAYS,
        key="safety_stock_days"
    )
    
    reorder_point_days = st.sidebar.slider(
        "Reorder Point (Days of Supply)",
        min_value=14,
        max_value=90,
        value=DEFAULT_REORDER_POINT_DAYS,
        key="reorder_point_days"
    )
    
    default_payment_terms = st.sidebar.selectbox(
        "Default Payment Terms",
        options=[0, 15, 30, 45, 60, 90],
        index=2,
        format_func=lambda x: f"Net {x}" if x > 0 else "Due on Receipt",
        key="default_payment_terms"
    )
    
    st.sidebar.markdown("---")
    
    # Check for approved scenario
    approved_scenario = st.session_state.get(APPROVED_SCENARIO_KEY)
    scenarios = st.session_state.get(SCENARIOS_KEY, {})
    
    use_approved = False
    if approved_scenario and approved_scenario in scenarios:
        use_approved = st.sidebar.checkbox(
            f"Use Approved Scenario: {approved_scenario}",
            value=True,
            key="use_approved_scenario"
        )
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 PO Schedule",
        "💰 Cash Flow Impact",
        "📊 SKU Analysis",
        "📥 Export"
    ])
    
    with tab1:
        render_po_schedule(
            invoice_lines, items, inventory, vendors,
            planning_horizon, safety_stock_days, reorder_point_days,
            default_payment_terms, use_approved, approved_scenario, scenarios
        )
    
    with tab2:
        render_cash_flow_impact(
            invoice_lines, items, inventory,
            planning_horizon, safety_stock_days, reorder_point_days,
            default_payment_terms, use_approved, approved_scenario, scenarios
        )
    
    with tab3:
        render_sku_po_analysis(
            invoice_lines, items, inventory,
            planning_horizon, use_approved, approved_scenario, scenarios
        )
    
    with tab4:
        render_po_export(
            invoice_lines, items, inventory, vendors,
            planning_horizon, safety_stock_days, reorder_point_days,
            default_payment_terms, use_approved, approved_scenario, scenarios
        )


def calculate_demand_forecast(
    invoice_lines: pd.DataFrame,
    horizon: int,
    use_approved: bool,
    approved_scenario: str,
    scenarios: Dict
) -> Tuple[pd.Series, pd.Series]:
    """Calculate or retrieve demand forecast."""
    
    # Prepare historical demand
    df = invoice_lines.copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    df['Period'] = df['Date'].dt.to_period('M').dt.to_timestamp()
    
    monthly_demand = df.groupby('Period')['Quantity'].sum()
    
    # Use approved scenario if available
    if use_approved and approved_scenario and approved_scenario in scenarios:
        scenario = scenarios[approved_scenario]
        forecast_result = load_scenario_forecast(scenario)
        return monthly_demand, forecast_result.forecast
    
    # Generate fresh forecast
    if len(monthly_demand) >= 6:
        try:
            result = generate_forecast(monthly_demand, model='exponential_smoothing', horizon=horizon)
            return monthly_demand, result.forecast
        except Exception as e:
            logger.error(f"Forecast failed: {e}")
    
    # Fallback: use average of last 6 months
    avg_demand = monthly_demand.tail(6).mean()
    future_dates = pd.date_range(
        start=monthly_demand.index[-1] + pd.DateOffset(months=1),
        periods=horizon,
        freq='MS'
    )
    fallback_forecast = pd.Series([avg_demand] * horizon, index=future_dates)
    
    return monthly_demand, fallback_forecast


def generate_po_schedule(
    forecast: pd.Series,
    items: pd.DataFrame,
    inventory: pd.DataFrame,
    safety_stock_days: int,
    reorder_point_days: int,
    default_payment_terms: int
) -> pd.DataFrame:
    """Generate a purchase order schedule based on forecast and inventory."""
    
    po_records = []
    
    # Get item details
    if items is not None and not items.empty:
        item_details = items.set_index('SKU').to_dict('index') if 'SKU' in items.columns else {}
    else:
        item_details = {}
    
    # Get current inventory
    if inventory is not None and not inventory.empty and 'Name' in inventory.columns:
        current_inv = inventory.set_index('Name')['On Hand'].to_dict() if 'On Hand' in inventory.columns else {}
        avg_cost = inventory.set_index('Name')['Average Cost'].to_dict() if 'Average Cost' in inventory.columns else {}
    else:
        current_inv = {}
        avg_cost = {}
    
    # Calculate daily demand rate from forecast
    total_forecast = forecast.sum()
    forecast_days = len(forecast) * 30  # Approximate days
    daily_demand = total_forecast / forecast_days if forecast_days > 0 else 0
    
    # Generate POs for aggregate level (simplified)
    running_inventory = sum(current_inv.values()) if current_inv else 0
    safety_stock = daily_demand * safety_stock_days
    reorder_point = daily_demand * reorder_point_days
    
    current_date = datetime.now()
    
    for period, demand in forecast.items():
        period_start = period
        period_end = period + pd.DateOffset(months=1) - pd.DateOffset(days=1)
        
        # Check if we need to order
        projected_inv = running_inventory - demand
        
        if projected_inv < reorder_point:
            # Calculate order quantity (EOQ simplified)
            order_qty = max(demand * 2, reorder_point + safety_stock - projected_inv)
            
            # Determine lead time (use average)
            lead_time = DEFAULT_LEAD_TIME_DAYS
            
            # Calculate dates
            arrival_needed = period_start - pd.DateOffset(days=safety_stock_days)
            po_date = arrival_needed - pd.DateOffset(days=lead_time)
            
            # Don't create POs in the past
            if po_date < pd.Timestamp(current_date):
                po_date = pd.Timestamp(current_date) + pd.DateOffset(days=3)
                arrival_needed = po_date + pd.DateOffset(days=lead_time)
            
            # Calculate cost
            avg_unit_cost = np.mean(list(avg_cost.values())) if avg_cost else 10.0
            total_cost = order_qty * avg_unit_cost
            
            # Payment due date
            payment_date = po_date + pd.DateOffset(days=default_payment_terms)
            
            po_records.append({
                'PO_Date': po_date,
                'Arrival_Date': arrival_needed,
                'For_Period': period.strftime('%Y-%m'),
                'Quantity': order_qty,
                'Unit_Cost': avg_unit_cost,
                'Total_Cost': total_cost,
                'Payment_Terms': f"Net {default_payment_terms}",
                'Payment_Due': payment_date,
                'Lead_Time_Days': lead_time,
                'Status': 'Planned'
            })
            
            # Update running inventory
            running_inventory = projected_inv + order_qty
        else:
            running_inventory = projected_inv
    
    return pd.DataFrame(po_records)


def render_po_schedule(
    invoice_lines: pd.DataFrame,
    items: pd.DataFrame,
    inventory: pd.DataFrame,
    vendors: pd.DataFrame,
    horizon: int,
    safety_stock_days: int,
    reorder_point_days: int,
    payment_terms: int,
    use_approved: bool,
    approved_scenario: str,
    scenarios: Dict
):
    """Render the PO schedule view."""
    
    st.markdown("### 📋 Planned Purchase Order Schedule")
    
    # Get forecast
    historical, forecast = calculate_demand_forecast(
        invoice_lines, horizon, use_approved, approved_scenario, scenarios
    )
    
    if use_approved and approved_scenario:
        st.info(f"📊 Using approved scenario: **{approved_scenario}**")
    
    # Generate PO schedule
    po_schedule = generate_po_schedule(
        forecast, items, inventory,
        safety_stock_days, reorder_point_days, payment_terms
    )
    
    if po_schedule.empty:
        st.success("No purchase orders needed for the planning horizon based on current inventory and forecast.")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_pos = len(po_schedule)
        st.metric("Planned POs", f"{total_pos}")
    
    with col2:
        total_qty = po_schedule['Quantity'].sum()
        st.metric("Total Quantity", f"{total_qty:,.0f}")
    
    with col3:
        total_cost = po_schedule['Total_Cost'].sum()
        st.metric("Total Cost", f"${total_cost:,.2f}")
    
    with col4:
        avg_lead = po_schedule['Lead_Time_Days'].mean()
        st.metric("Avg Lead Time", f"{avg_lead:.0f} days")
    
    st.markdown("---")
    
    # Timeline visualization
    st.markdown("#### PO Timeline")
    
    fig = go.Figure()
    
    # Add PO markers
    for _, row in po_schedule.iterrows():
        # PO Date
        fig.add_trace(go.Scatter(
            x=[row['PO_Date']],
            y=[1],
            mode='markers+text',
            marker=dict(size=15, color='#3498db', symbol='circle'),
            text=[f"PO: {row['Quantity']:,.0f}"],
            textposition='top center',
            name='PO Date',
            showlegend=False
        ))
        
        # Arrival Date
        fig.add_trace(go.Scatter(
            x=[row['Arrival_Date']],
            y=[1],
            mode='markers+text',
            marker=dict(size=15, color='#2ecc71', symbol='diamond'),
            text=[f"Arrive"],
            textposition='top center',
            name='Arrival',
            showlegend=False
        ))
        
        # Payment Date
        fig.add_trace(go.Scatter(
            x=[row['Payment_Due']],
            y=[1],
            mode='markers+text',
            marker=dict(size=15, color='#e74c3c', symbol='square'),
            text=[f"Pay: ${row['Total_Cost']:,.0f}"],
            textposition='top center',
            name='Payment',
            showlegend=False
        ))
        
        # Connect with lines
        fig.add_trace(go.Scatter(
            x=[row['PO_Date'], row['Arrival_Date'], row['Payment_Due']],
            y=[1, 1, 1],
            mode='lines',
            line=dict(color='#bdc3c7', width=1),
            showlegend=False
        ))
    
    fig.update_layout(
        title="Purchase Order Timeline",
        height=250,
        showlegend=False,
        yaxis=dict(visible=False),
        xaxis_title="Date"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # PO Schedule Table
    st.markdown("#### Detailed PO Schedule")
    
    display_df = po_schedule.copy()
    display_df['PO_Date'] = display_df['PO_Date'].dt.strftime('%Y-%m-%d')
    display_df['Arrival_Date'] = display_df['Arrival_Date'].dt.strftime('%Y-%m-%d')
    display_df['Payment_Due'] = display_df['Payment_Due'].dt.strftime('%Y-%m-%d')
    display_df['Quantity'] = display_df['Quantity'].apply(lambda x: f"{x:,.0f}")
    display_df['Unit_Cost'] = display_df['Unit_Cost'].apply(lambda x: f"${x:,.2f}")
    display_df['Total_Cost'] = display_df['Total_Cost'].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_cash_flow_impact(
    invoice_lines: pd.DataFrame,
    items: pd.DataFrame,
    inventory: pd.DataFrame,
    horizon: int,
    safety_stock_days: int,
    reorder_point_days: int,
    payment_terms: int,
    use_approved: bool,
    approved_scenario: str,
    scenarios: Dict
):
    """Render cash flow impact analysis."""
    
    st.markdown("### 💰 Cash Flow Impact")
    
    # Get forecast and PO schedule
    historical, forecast = calculate_demand_forecast(
        invoice_lines, horizon, use_approved, approved_scenario, scenarios
    )
    
    po_schedule = generate_po_schedule(
        forecast, items, inventory,
        safety_stock_days, reorder_point_days, payment_terms
    )
    
    if po_schedule.empty:
        st.info("No POs planned - no cash flow impact to display.")
        return
    
    # Group payments by month
    po_schedule['Payment_Month'] = pd.to_datetime(po_schedule['Payment_Due']).dt.to_period('M').astype(str)
    
    monthly_payments = po_schedule.groupby('Payment_Month')['Total_Cost'].sum().reset_index()
    monthly_payments.columns = ['Month', 'Payment_Amount']
    monthly_payments = monthly_payments.sort_values('Month')
    
    # Calculate cumulative
    monthly_payments['Cumulative'] = monthly_payments['Payment_Amount'].cumsum()
    
    # Chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(
            x=monthly_payments['Month'],
            y=monthly_payments['Payment_Amount'],
            name='Monthly Payments',
            marker_color='#e74c3c'
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(
            x=monthly_payments['Month'],
            y=monthly_payments['Cumulative'],
            mode='lines+markers',
            name='Cumulative',
            line=dict(color='#3498db', width=2)
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        title="PO Payment Cash Flow",
        height=400,
        hovermode='x unified',
        legend=dict(orientation='h', y=1.1)
    )
    fig.update_xaxes(title_text="Month")
    fig.update_yaxes(title_text="Monthly Payment ($)", secondary_y=False)
    fig.update_yaxes(title_text="Cumulative ($)", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary table
    st.markdown("#### Monthly Cash Requirements")
    
    display_df = monthly_payments.copy()
    display_df['Payment_Amount'] = display_df['Payment_Amount'].apply(lambda x: f"${x:,.2f}")
    display_df['Cumulative'] = display_df['Cumulative'].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Key insights
    st.markdown("---")
    st.markdown("#### 💡 Key Insights")
    
    total_cash_needed = po_schedule['Total_Cost'].sum()
    peak_month = monthly_payments.loc[monthly_payments['Payment_Amount'].idxmax()]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Total Cash Required:** ${total_cash_needed:,.2f}")
        st.markdown(f"**Peak Payment Month:** {peak_month['Month']}")
    
    with col2:
        avg_monthly = total_cash_needed / len(monthly_payments)
        st.markdown(f"**Average Monthly:** ${avg_monthly:,.2f}")
        st.markdown(f"**Payment Terms:** Net {payment_terms}")


def render_sku_po_analysis(
    invoice_lines: pd.DataFrame,
    items: pd.DataFrame,
    inventory: pd.DataFrame,
    horizon: int,
    use_approved: bool,
    approved_scenario: str,
    scenarios: Dict
):
    """Render SKU-level PO analysis."""
    
    st.markdown("### 📊 SKU-Level Analysis")
    
    if 'Item' not in invoice_lines.columns:
        st.warning("Item column not found in data.")
        return
    
    df = invoice_lines.copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # Calculate metrics by SKU
    last_90_days = datetime.now() - timedelta(days=90)
    recent_df = df[df['Date'] >= last_90_days]
    
    sku_analysis = recent_df.groupby('Item').agg({
        'Quantity': 'sum',
        'Amount': 'sum',
        'Document Number': 'nunique'
    }).reset_index()
    sku_analysis.columns = ['SKU', 'Qty_90d', 'Revenue_90d', 'Orders_90d']
    
    # Add inventory info
    if inventory is not None and 'Name' in inventory.columns and 'On Hand' in inventory.columns:
        inv_dict = inventory.set_index('Name')['On Hand'].to_dict()
        sku_analysis['On_Hand'] = sku_analysis['SKU'].map(inv_dict).fillna(0)
    else:
        sku_analysis['On_Hand'] = 0
    
    # Calculate days of supply
    sku_analysis['Daily_Demand'] = sku_analysis['Qty_90d'] / 90
    sku_analysis['Days_of_Supply'] = np.where(
        sku_analysis['Daily_Demand'] > 0,
        sku_analysis['On_Hand'] / sku_analysis['Daily_Demand'],
        999
    )
    
    # Flag items needing reorder
    sku_analysis['Needs_Reorder'] = sku_analysis['Days_of_Supply'] < 30
    
    # Sort by days of supply
    sku_analysis = sku_analysis.sort_values('Days_of_Supply')
    
    # Summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        needs_reorder = sku_analysis['Needs_Reorder'].sum()
        st.metric("SKUs Need Reorder", f"{needs_reorder}")
    
    with col2:
        low_stock = (sku_analysis['Days_of_Supply'] < 14).sum()
        st.metric("Critical (< 14 days)", f"{low_stock}")
    
    with col3:
        total_skus = len(sku_analysis)
        st.metric("Total Active SKUs", f"{total_skus}")
    
    st.markdown("---")
    
    # Chart: Days of Supply by SKU
    top_20 = sku_analysis.head(20)
    
    fig = px.bar(
        top_20,
        x='SKU',
        y='Days_of_Supply',
        color='Needs_Reorder',
        color_discrete_map={True: '#e74c3c', False: '#2ecc71'},
        title="Days of Supply by SKU (Top 20 Lowest)"
    )
    fig.add_hline(y=30, line_dash="dash", line_color="orange", annotation_text="30 Day Threshold")
    fig.update_layout(height=400)
    fig.update_xaxes(tickangle=-45)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed table
    st.markdown("#### SKU Inventory Status")
    
    display_df = sku_analysis[['SKU', 'On_Hand', 'Qty_90d', 'Daily_Demand', 'Days_of_Supply', 'Needs_Reorder']].copy()
    display_df['On_Hand'] = display_df['On_Hand'].apply(lambda x: f"{x:,.0f}")
    display_df['Qty_90d'] = display_df['Qty_90d'].apply(lambda x: f"{x:,.0f}")
    display_df['Daily_Demand'] = display_df['Daily_Demand'].apply(lambda x: f"{x:,.1f}")
    display_df['Days_of_Supply'] = display_df['Days_of_Supply'].apply(lambda x: f"{x:,.0f}" if x < 999 else "∞")
    display_df['Needs_Reorder'] = display_df['Needs_Reorder'].apply(lambda x: "🔴 Yes" if x else "✅ No")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_po_export(
    invoice_lines: pd.DataFrame,
    items: pd.DataFrame,
    inventory: pd.DataFrame,
    vendors: pd.DataFrame,
    horizon: int,
    safety_stock_days: int,
    reorder_point_days: int,
    payment_terms: int,
    use_approved: bool,
    approved_scenario: str,
    scenarios: Dict
):
    """Render PO export functionality."""
    
    st.markdown("### 📥 Export PO Forecast")
    
    # Get forecast and PO schedule
    historical, forecast = calculate_demand_forecast(
        invoice_lines, horizon, use_approved, approved_scenario, scenarios
    )
    
    po_schedule = generate_po_schedule(
        forecast, items, inventory,
        safety_stock_days, reorder_point_days, payment_terms
    )
    
    if po_schedule.empty:
        st.info("No POs to export.")
        return
    
    st.markdown("#### Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**PO Schedule Export**")
        st.markdown("Complete purchase order schedule with dates, quantities, and costs")
        
        export_df = po_schedule.copy()
        export_df['PO_Date'] = export_df['PO_Date'].dt.strftime('%Y-%m-%d')
        export_df['Arrival_Date'] = export_df['Arrival_Date'].dt.strftime('%Y-%m-%d')
        export_df['Payment_Due'] = export_df['Payment_Due'].dt.strftime('%Y-%m-%d')
        
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="📥 Download PO Schedule (CSV)",
            data=csv,
            file_name=f"po_schedule_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        st.markdown("**Cash Flow Export**")
        st.markdown("Monthly cash requirements for Finance planning")
        
        po_schedule['Payment_Month'] = pd.to_datetime(po_schedule['Payment_Due']).dt.to_period('M').astype(str)
        monthly_payments = po_schedule.groupby('Payment_Month')['Total_Cost'].sum().reset_index()
        monthly_payments.columns = ['Month', 'Payment_Amount']
        monthly_payments['Cumulative'] = monthly_payments['Payment_Amount'].cumsum()
        
        csv_cf = monthly_payments.to_csv(index=False)
        st.download_button(
            label="📥 Download Cash Flow (CSV)",
            data=csv_cf,
            file_name=f"po_cash_flow_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    # Preview
    st.markdown("---")
    st.markdown("#### Export Preview")
    
    with st.expander("PO Schedule Preview"):
        st.dataframe(export_df, use_container_width=True, hide_index=True)
    
    with st.expander("Cash Flow Preview"):
        st.dataframe(monthly_payments, use_container_width=True, hide_index=True)
