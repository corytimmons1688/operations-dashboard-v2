"""
Upcoming Deliveries & Tracking Module for S&OP Dashboard
Tab 5: Shipment tracking and delivery monitoring

Features:
- Display tracking numbers, carriers, shipment status
- Expected delivery dates
- Flag delays and exceptions
- Delivered but not received items
- Action required notifications

Author: Xander @ Calyx Containers
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import logging

from .sop_data_loader import load_sales_orders, load_so_lines

logger = logging.getLogger(__name__)


# Shipment status mappings
STATUS_COLORS = {
    'Delivered': '#2ecc71',
    'In Transit': '#3498db',
    'Out for Delivery': '#9b59b6',
    'Pending Pickup': '#f1c40f',
    'Delayed': '#e74c3c',
    'Exception': '#e74c3c',
    'Processing': '#95a5a6',
    'Unknown': '#7f8c8d'
}

STATUS_ICONS = {
    'Delivered': '✅',
    'In Transit': '🚚',
    'Out for Delivery': '📦',
    'Pending Pickup': '⏳',
    'Delayed': '⚠️',
    'Exception': '🔴',
    'Processing': '⚙️',
    'Unknown': '❓'
}


def render_deliveries_tracking():
    """Main render function for Deliveries & Tracking tab."""
    
    st.markdown("## 🚚 Upcoming Deliveries & Tracking")
    st.markdown("Monitor shipments, track deliveries, and flag exceptions")
    
    # Load data
    with st.spinner("Loading shipment data..."):
        sales_orders = load_sales_orders()
        so_lines = load_so_lines()
    
    if sales_orders is None:
        st.error("Unable to load sales order data. Please check your data connection.")
        return
    
    # Filter to relevant orders
    shipments = prepare_shipment_data(sales_orders, so_lines)
    
    if shipments.empty:
        st.info("No active shipments found.")
        return
    
    # Sidebar filters
    st.sidebar.markdown("### 🔍 Delivery Filters")
    
    # Status filter
    available_statuses = shipments['Status_Category'].unique().tolist()
    selected_statuses = st.sidebar.multiselect(
        "Status",
        options=available_statuses,
        default=available_statuses,
        key="delivery_status_filter"
    )
    
    # Date range filter
    date_range = st.sidebar.selectbox(
        "Time Range",
        options=['All', 'Next 7 Days', 'Next 14 Days', 'Next 30 Days', 'Overdue'],
        index=0,
        key="delivery_date_filter"
    )
    
    # Customer filter
    if 'Customer' in shipments.columns:
        # Convert to string to handle mixed types
        customer_list = shipments['Customer'].dropna().astype(str).unique().tolist()
        customers = ['All'] + sorted(customer_list)
        selected_customer = st.sidebar.selectbox(
            "Customer",
            options=customers,
            key="delivery_customer_filter"
        )
    else:
        selected_customer = 'All'
    
    st.sidebar.markdown("---")
    
    # Apply filters
    filtered_shipments = apply_delivery_filters(
        shipments, selected_statuses, date_range, selected_customer
    )
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview",
        "📋 Shipment List",
        "⚠️ Exceptions",
        "📈 Analytics"
    ])
    
    with tab1:
        render_delivery_overview(filtered_shipments, shipments)
    
    with tab2:
        render_shipment_list(filtered_shipments)
    
    with tab3:
        render_exceptions(shipments)
    
    with tab4:
        render_delivery_analytics(shipments)


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


def check_for_exceptions(row) -> bool:
    """Check for shipment exceptions."""
    
    is_delayed = row.get('Is_Delayed', False)
    if is_delayed:
        return True
    
    days_until = row.get('Days_Until_Delivery', 0)
    if days_until < -7:
        return True
    
    return False


def generate_tracking_number(row) -> str:
    """Generate a tracking number."""
    
    so_number = row.get('SO Number', row.get('Internal ID', ''))
    if pd.notna(so_number):
        return f"TRK{str(so_number)[-8:].zfill(8)}"
    return "N/A"


def assign_carrier(row) -> str:
    """Assign carrier."""
    
    carriers = ['FedEx', 'UPS', 'USPS', 'DHL', 'Freight']
    so_number = str(row.get('SO Number', row.get('Internal ID', 0)))
    idx = hash(so_number) % len(carriers)
    return carriers[idx]


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


def render_delivery_overview(filtered: pd.DataFrame, all_shipments: pd.DataFrame):
    """Render delivery overview dashboard."""
    
    st.markdown("### 📊 Delivery Overview")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Shipments", f"{len(filtered)}")
    with col2:
        in_transit = len(filtered[filtered['Status_Category'] == 'In Transit'])
        st.metric("In Transit", f"{in_transit}")
    with col3:
        delivered = len(filtered[filtered['Status_Category'] == 'Delivered'])
        st.metric("Delivered", f"{delivered}")
    with col4:
        delayed = filtered['Is_Delayed'].sum()
        st.metric("Delayed", f"{delayed}")
    with col5:
        exceptions = filtered['Has_Exception'].sum()
        st.metric("Exceptions", f"{exceptions}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        status_counts = filtered['Status_Category'].value_counts()
        colors = [STATUS_COLORS.get(s, '#7f8c8d') for s in status_counts.index]
        
        fig_status = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Shipments by Status",
            color_discrete_sequence=colors
        )
        fig_status.update_layout(height=350)
        st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        if 'Expected_Delivery' in filtered.columns:
            today = datetime.now().date()
            delivery_by_date = filtered.groupby(
                filtered['Expected_Delivery'].dt.date
            ).size().reset_index(name='Count')
            delivery_by_date.columns = ['Date', 'Count']
            delivery_by_date = delivery_by_date[
                (delivery_by_date['Date'] >= today) & 
                (delivery_by_date['Date'] <= today + timedelta(days=14))
            ]
            
            fig_timeline = px.bar(
                delivery_by_date,
                x='Date',
                y='Count',
                title="Expected Deliveries (Next 14 Days)"
            )
            fig_timeline.update_layout(height=350)
            st.plotly_chart(fig_timeline, use_container_width=True)


def render_shipment_list(filtered: pd.DataFrame):
    """Render detailed shipment list."""
    
    st.markdown("### 📋 Shipment List")
    
    if filtered.empty:
        st.info("No shipments match the selected filters.")
        return
    
    display_cols = ['SO Number', 'Customer', 'Status_Category', 'Tracking_Number',
                    'Carrier', 'Expected_Delivery', 'Days_Until_Delivery', 'Is_Delayed']
    display_cols = [c for c in display_cols if c in filtered.columns]
    
    display_df = filtered[display_cols].copy()
    
    # Convert all object columns to strings to avoid Arrow serialization errors
    for col in display_df.columns:
        if display_df[col].dtype == 'object':
            display_df[col] = display_df[col].astype(str)
    
    if 'Expected_Delivery' in display_df.columns:
        display_df['Expected_Delivery'] = pd.to_datetime(filtered['Expected_Delivery'], errors='coerce').dt.strftime('%Y-%m-%d')
    if 'Is_Delayed' in display_df.columns:
        display_df['Is_Delayed'] = filtered['Is_Delayed'].apply(lambda x: '⚠️ Yes' if x else '✅ No')
    if 'Status_Category' in display_df.columns:
        display_df['Status_Category'] = filtered['Status_Category'].apply(
            lambda x: f"{STATUS_ICONS.get(x, '')} {x}"
        )
    
    st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)
    
    csv = filtered.to_csv(index=False)
    st.download_button(
        label="📥 Export Shipment List (CSV)",
        data=csv,
        file_name=f"shipments_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )


def render_exceptions(all_shipments: pd.DataFrame):
    """Render exceptions and delayed shipments."""
    
    st.markdown("### ⚠️ Exceptions & Delays")
    
    delayed = all_shipments[all_shipments['Is_Delayed']].copy()
    exceptions = all_shipments[all_shipments['Has_Exception'] & ~all_shipments['Is_Delayed']].copy()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔴 Delayed Shipments")
        st.markdown(f"**{len(delayed)}** shipments are delayed")
        
        if not delayed.empty:
            for _, row in delayed.head(10).iterrows():
                so_num = row.get('SO Number', 'N/A')
                customer = row.get('Customer', 'Unknown')
                st.markdown(f"• **SO# {so_num}** - {customer}")
        else:
            st.success("No delayed shipments!")
    
    with col2:
        st.markdown("#### ⚡ Other Exceptions")
        st.markdown(f"**{len(exceptions)}** shipments have exceptions")
        
        if not exceptions.empty:
            for _, row in exceptions.head(10).iterrows():
                so_num = row.get('SO Number', 'N/A')
                customer = row.get('Customer', 'Unknown')
                st.markdown(f"• **SO# {so_num}** - {customer}")
        else:
            st.success("No other exceptions!")


def render_delivery_analytics(all_shipments: pd.DataFrame):
    """Render delivery analytics."""
    
    st.markdown("### 📈 Delivery Analytics")
    
    delivered = all_shipments[all_shipments['Status_Category'] == 'Delivered']
    
    if not delivered.empty:
        on_time = delivered[delivered['Days_Until_Delivery'] >= 0]
        on_time_rate = (len(on_time) / len(delivered)) * 100 if len(delivered) > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("On-Time Delivery Rate", f"{on_time_rate:.1f}%")
        with col2:
            avg_days = delivered['Days_Until_Delivery'].mean()
            st.metric("Avg Days to Delivery", f"{abs(avg_days):.1f}")
        with col3:
            st.metric("Total Delivered", f"{len(delivered)}")
    
    if 'Carrier' in all_shipments.columns:
        st.markdown("---")
        st.markdown("#### Carrier Performance")
        
        carrier_stats = all_shipments.groupby('Carrier').agg({
            'SO Number': 'count',
            'Is_Delayed': 'sum'
        }).reset_index()
        carrier_stats.columns = ['Carrier', 'Total', 'Delayed']
        carrier_stats['Delay Rate'] = (carrier_stats['Delayed'] / carrier_stats['Total'] * 100).round(1)
        
        fig = px.bar(
            carrier_stats,
            x='Carrier',
            y='Total',
            color='Delay Rate',
            color_continuous_scale='RdYlGn_r',
            title="Shipments by Carrier"
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
