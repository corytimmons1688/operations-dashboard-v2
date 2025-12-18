"""
Sales Rep View Module for S&OP Dashboard
Customer-focused demand analysis and forecasting

Features:
- Fixed dropdown filters (Customer, Item, Date Range)
- Item category linked to "Calyx || Product Type" from Raw_Items
- Forecast Planning section with interactive pipeline/deals
- Historical and forecasted revenue charts
- Submit Forecast functionality

Author: Xander @ Calyx Containers
Version: 3.1.0
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# DATA LOADING FUNCTIONS
# =============================================================================

@st.cache_data(ttl=300)
def load_sales_data():
    """Load all required sales data with caching."""
    try:
        from .sop_data_loader import (
            load_invoice_lines, load_sales_orders, load_items,
            load_customers, load_deals
        )
        
        invoice_lines = load_invoice_lines()
        sales_orders = load_sales_orders()
        items = load_items()
        customers = load_customers()
        deals = load_deals()
        
        return {
            'invoice_lines': invoice_lines,
            'sales_orders': sales_orders,
            'items': items,
            'customers': customers,
            'deals': deals
        }
    except Exception as e:
        logger.error(f"Error loading sales data: {e}")
        return None


def get_product_type_mapping(items_df: pd.DataFrame) -> Dict[str, str]:
    """
    Create mapping of Item to Product Type from Raw_Items.
    Links to 'Calyx || Product Type' column.
    """
    if items_df is None or items_df.empty:
        return {}
    
    # Find the product type column
    product_type_col = None
    for col in items_df.columns:
        col_lower = col.lower()
        if 'calyx' in col_lower and 'product type' in col_lower:
            product_type_col = col
            break
        elif 'product type' in col_lower or 'product_type' in col_lower:
            product_type_col = col
            break
    
    if product_type_col is None:
        logger.warning("Could not find 'Calyx || Product Type' column in items data")
        return {}
    
    # Find the item name/ID column
    item_col = None
    for col in items_df.columns:
        col_lower = col.lower()
        if col_lower in ['item', 'item name', 'item_name', 'sku', 'name']:
            item_col = col
            break
    
    if item_col is None:
        # Try first column as item identifier
        item_col = items_df.columns[0]
    
    # Create mapping
    mapping = {}
    for _, row in items_df.iterrows():
        item = str(row.get(item_col, '')).strip()
        product_type = str(row.get(product_type_col, 'Unknown')).strip()
        if item and product_type:
            mapping[item] = product_type if product_type else 'Unknown'
    
    return mapping


def enrich_with_product_type(df: pd.DataFrame, product_type_map: Dict[str, str]) -> pd.DataFrame:
    """Add/update Product Type column using the item mapping."""
    if df is None or df.empty:
        return df
    
    df = df.copy()
    
    # Find item column
    item_col = None
    for col in df.columns:
        col_lower = col.lower()
        if col_lower in ['item', 'item name', 'item_name', 'sku']:
            item_col = col
            break
    
    if item_col and product_type_map:
        df['Product Type'] = df[item_col].map(product_type_map).fillna('Unknown')
    elif 'Product Type' not in df.columns:
        # Check for existing product type column with different name
        for col in df.columns:
            if 'product type' in col.lower():
                df['Product Type'] = df[col]
                break
        else:
            df['Product Type'] = 'Unknown'
    
    return df


# =============================================================================
# FILTER FUNCTIONS
# =============================================================================

def get_unique_sales_reps(sales_orders: pd.DataFrame, customers: pd.DataFrame) -> List[str]:
    """Get unique sales reps from data."""
    reps = set()
    
    # Check sales orders for rep column
    if sales_orders is not None and not sales_orders.empty:
        for col in sales_orders.columns:
            col_lower = col.lower()
            if 'rep' in col_lower or 'salesperson' in col_lower or 'sales rep' in col_lower:
                reps.update(sales_orders[col].dropna().unique())
                break
    
    # Check customers for rep column
    if customers is not None and not customers.empty:
        for col in customers.columns:
            col_lower = col.lower()
            if 'rep' in col_lower or 'salesperson' in col_lower:
                reps.update(customers[col].dropna().unique())
                break
    
    # Clean and sort
    reps = [str(r).strip() for r in reps if r and str(r).strip()]
    return sorted(list(set(reps)))


def get_customers_for_rep(sales_orders: pd.DataFrame, invoice_lines: pd.DataFrame, 
                          rep: str = None) -> List[str]:
    """Get unique customers, optionally filtered by rep."""
    customers = set()
    
    # Get customer column name
    customer_cols = ['Customer', 'Correct Customer', 'Customer Name', 'customer', 'Customer Companyname']
    
    for df in [sales_orders, invoice_lines]:
        if df is not None and not df.empty:
            for col in customer_cols:
                if col in df.columns:
                    if rep and rep != "All":
                        # Find rep column and filter
                        rep_col = None
                        for rc in df.columns:
                            if 'rep' in rc.lower():
                                rep_col = rc
                                break
                        if rep_col:
                            filtered = df[df[rep_col] == rep]
                            customers.update(filtered[col].dropna().unique())
                        else:
                            customers.update(df[col].dropna().unique())
                    else:
                        customers.update(df[col].dropna().unique())
                    break
    
    # Clean and sort
    customers = [str(c).strip() for c in customers if c and str(c).strip() and str(c).lower() != 'nan']
    return sorted(list(set(customers)))


def get_items_for_customer(invoice_lines: pd.DataFrame, sales_orders: pd.DataFrame,
                           customer: str = None) -> List[str]:
    """Get unique items/SKUs, optionally filtered by customer."""
    items = set()
    
    item_cols = ['Item', 'SKU', 'Item Name', 'item', 'Product']
    customer_cols = ['Customer', 'Correct Customer', 'Customer Name', 'customer']
    
    for df in [invoice_lines, sales_orders]:
        if df is not None and not df.empty:
            # Find item column
            item_col = None
            for col in item_cols:
                if col in df.columns:
                    item_col = col
                    break
            
            if item_col is None:
                continue
            
            # Find customer column
            cust_col = None
            for col in customer_cols:
                if col in df.columns:
                    cust_col = col
                    break
            
            if customer and customer != "All" and cust_col:
                filtered = df[df[cust_col] == customer]
                items.update(filtered[item_col].dropna().unique())
            else:
                items.update(df[item_col].dropna().unique())
    
    # Clean and sort
    items = [str(i).strip() for i in items if i and str(i).strip() and str(i).lower() != 'nan']
    return sorted(list(set(items)))


def filter_data_by_date_range(df: pd.DataFrame, date_range: str, date_col: str = None) -> pd.DataFrame:
    """Filter dataframe by date range selection."""
    if df is None or df.empty:
        return df
    
    df = df.copy()
    
    # Find date column
    if date_col is None:
        date_cols = ['Date', 'date', 'Invoice Date', 'Order Date', 'Tran Date', 'Transaction Date']
        for col in date_cols:
            if col in df.columns:
                date_col = col
                break
    
    if date_col is None or date_col not in df.columns:
        return df
    
    # Convert to datetime
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    today = datetime.now()
    
    if date_range == "Last 3 Months":
        start_date = today - timedelta(days=90)
    elif date_range == "Last 6 Months":
        start_date = today - timedelta(days=180)
    elif date_range == "Last 12 Months":
        start_date = today - timedelta(days=365)
    elif date_range == "YTD":
        start_date = datetime(today.year, 1, 1)
    elif date_range == "All Time":
        return df
    else:
        # Default to last 12 months
        start_date = today - timedelta(days=365)
    
    return df[df[date_col] >= start_date]


# =============================================================================
# FORECAST PLANNING FUNCTIONS
# =============================================================================

def calculate_customer_demand(invoice_lines: pd.DataFrame, customer: str, 
                              date_range: str, product_type_map: Dict) -> pd.DataFrame:
    """Calculate demand by item for a customer within date range."""
    if invoice_lines is None or invoice_lines.empty:
        return pd.DataFrame()
    
    df = invoice_lines.copy()
    
    # Find customer column
    customer_cols = ['Customer', 'Correct Customer', 'Customer Name']
    cust_col = None
    for col in customer_cols:
        if col in df.columns:
            cust_col = col
            break
    
    if cust_col is None or customer == "All":
        filtered = df
    else:
        filtered = df[df[cust_col] == customer]
    
    # Apply date filter
    filtered = filter_data_by_date_range(filtered, date_range)
    
    if filtered.empty:
        return pd.DataFrame()
    
    # Enrich with product type
    filtered = enrich_with_product_type(filtered, product_type_map)
    
    # Find quantity and amount columns
    qty_col = None
    amt_col = None
    item_col = None
    
    for col in filtered.columns:
        col_lower = col.lower()
        if 'qty' in col_lower or 'quantity' in col_lower:
            qty_col = col
        elif 'amount' in col_lower or 'total' in col_lower or 'revenue' in col_lower:
            amt_col = col
        elif col_lower in ['item', 'sku', 'item name']:
            item_col = col
    
    if item_col is None:
        return pd.DataFrame()
    
    # Aggregate by item
    agg_dict = {}
    if qty_col:
        agg_dict['Units'] = (qty_col, 'sum')
    if amt_col:
        agg_dict['Revenue'] = (amt_col, 'sum')
    agg_dict['Orders'] = (item_col, 'count')
    
    if not agg_dict:
        return pd.DataFrame()
    
    # Group and aggregate
    grouped = filtered.groupby([item_col, 'Product Type']).agg(**agg_dict).reset_index()
    grouped.columns = ['Item', 'Product Type'] + list(agg_dict.keys())
    
    # Calculate projections (simple growth assumption)
    if 'Units' in grouped.columns:
        grouped['Projected Units'] = (grouped['Units'] * 1.1).round(0).astype(int)
    if 'Revenue' in grouped.columns:
        grouped['Projected Revenue'] = (grouped['Revenue'] * 1.1).round(2)
    
    # Sort by Product Type then Revenue
    sort_cols = ['Product Type']
    if 'Revenue' in grouped.columns:
        sort_cols.append('Revenue')
        grouped = grouped.sort_values(sort_cols, ascending=[True, False])
    else:
        grouped = grouped.sort_values(sort_cols)
    
    return grouped


def get_deals_for_customer(deals_df: pd.DataFrame, customer: str) -> pd.DataFrame:
    """Get pipeline/deals for a specific customer."""
    if deals_df is None or deals_df.empty:
        return pd.DataFrame()
    
    df = deals_df.copy()
    
    # Find customer/company column in deals
    cust_cols = ['Company', 'Customer', 'Account', 'company_name', 'Associated Company']
    cust_col = None
    for col in cust_cols:
        if col in df.columns:
            cust_col = col
            break
    
    if cust_col is None or customer == "All":
        return df
    
    return df[df[cust_col].str.contains(customer, case=False, na=False)]


def calculate_historical_revenue(invoice_lines: pd.DataFrame, customer: str) -> pd.DataFrame:
    """Calculate monthly historical revenue for a customer."""
    if invoice_lines is None or invoice_lines.empty:
        return pd.DataFrame()
    
    df = invoice_lines.copy()
    
    # Find columns
    customer_cols = ['Customer', 'Correct Customer', 'Customer Name']
    date_cols = ['Date', 'Invoice Date', 'Tran Date']
    amt_cols = ['Amount', 'Total', 'Revenue', 'Line Amount']
    
    cust_col = next((c for c in customer_cols if c in df.columns), None)
    date_col = next((c for c in date_cols if c in df.columns), None)
    amt_col = next((c for c in amt_cols if c in df.columns), None)
    
    if date_col is None or amt_col is None:
        return pd.DataFrame()
    
    # Filter by customer
    if cust_col and customer != "All":
        df = df[df[cust_col] == customer]
    
    # Convert date and aggregate monthly
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])
    df['Month'] = df[date_col].dt.to_period('M')
    
    monthly = df.groupby('Month')[amt_col].sum().reset_index()
    monthly.columns = ['Month', 'Revenue']
    monthly['Month'] = monthly['Month'].astype(str)
    
    return monthly


def generate_revenue_forecast(historical: pd.DataFrame, periods: int = 6) -> pd.DataFrame:
    """Generate simple revenue forecast based on historical data."""
    if historical.empty:
        return pd.DataFrame()
    
    # Simple moving average forecast
    recent_avg = historical['Revenue'].tail(3).mean()
    growth_rate = 0.05  # 5% monthly growth assumption
    
    last_month = pd.to_datetime(historical['Month'].iloc[-1])
    
    forecast_data = []
    for i in range(1, periods + 1):
        next_month = last_month + pd.DateOffset(months=i)
        forecast_value = recent_avg * (1 + growth_rate) ** i
        forecast_data.append({
            'Month': next_month.strftime('%Y-%m'),
            'Revenue': forecast_value,
            'Type': 'Forecast'
        })
    
    return pd.DataFrame(forecast_data)


def save_forecast_to_sheet(forecast_data: pd.DataFrame, customer: str) -> bool:
    """Save forecast data to Google Sheets (placeholder for actual implementation)."""
    try:
        # This would connect to your Google Sheets API and save the forecast
        # For now, this is a placeholder that returns success
        logger.info(f"Forecast saved for customer: {customer}")
        return True
    except Exception as e:
        logger.error(f"Error saving forecast: {e}")
        return False


# =============================================================================
# VISUALIZATION FUNCTIONS
# =============================================================================

def create_revenue_chart(historical: pd.DataFrame, forecast: pd.DataFrame, 
                         deals_revenue: float = 0) -> go.Figure:
    """Create combined historical and forecast revenue chart."""
    fig = go.Figure()
    
    # Historical revenue
    if not historical.empty:
        fig.add_trace(go.Scatter(
            x=historical['Month'],
            y=historical['Revenue'],
            mode='lines+markers',
            name='Historical Revenue',
            line=dict(color='#0033A1', width=2),
            marker=dict(size=8)
        ))
    
    # Forecast revenue
    if not forecast.empty:
        fig.add_trace(go.Scatter(
            x=forecast['Month'],
            y=forecast['Revenue'],
            mode='lines+markers',
            name='Forecasted Revenue',
            line=dict(color='#004FFF', width=2, dash='dash'),
            marker=dict(size=8, symbol='diamond')
        ))
    
    # Add deals/pipeline as potential upside
    if deals_revenue > 0 and not forecast.empty:
        forecast_with_deals = forecast.copy()
        forecast_with_deals['Revenue'] = forecast_with_deals['Revenue'] + (deals_revenue / len(forecast_with_deals))
        
        fig.add_trace(go.Scatter(
            x=forecast_with_deals['Month'],
            y=forecast_with_deals['Revenue'],
            mode='lines',
            name='With Pipeline',
            line=dict(color='#22C55E', width=2, dash='dot'),
            fill='tonexty',
            fillcolor='rgba(34, 197, 94, 0.1)'
        ))
    
    fig.update_layout(
        title='Customer Revenue: Historical & Forecast',
        xaxis_title='Month',
        yaxis_title='Revenue ($)',
        hovermode='x unified',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        height=400
    )
    
    return fig


def create_demand_by_category_chart(demand_df: pd.DataFrame) -> go.Figure:
    """Create demand breakdown by product category chart."""
    if demand_df.empty:
        return go.Figure()
    
    # Aggregate by product type
    if 'Revenue' in demand_df.columns:
        by_type = demand_df.groupby('Product Type')['Revenue'].sum().sort_values(ascending=True)
    elif 'Units' in demand_df.columns:
        by_type = demand_df.groupby('Product Type')['Units'].sum().sort_values(ascending=True)
    else:
        return go.Figure()
    
    fig = go.Figure(go.Bar(
        x=by_type.values,
        y=by_type.index,
        orientation='h',
        marker_color='#0033A1'
    ))
    
    fig.update_layout(
        title='Demand by Product Category',
        xaxis_title='Revenue ($)' if 'Revenue' in demand_df.columns else 'Units',
        yaxis_title='Product Type',
        height=300
    )
    
    return fig


# =============================================================================
# MAIN RENDER FUNCTION
# =============================================================================

def render_sales_rep_view():
    """Main render function for Sales Rep View."""
    
    st.markdown("### 👤 Sales Rep View")
    st.markdown("Customer-focused demand analysis and forecasting")
    
    # Load data
    with st.spinner("Loading sales data..."):
        data = load_sales_data()
    
    if data is None:
        st.error("Unable to load sales data. Please check your data connection.")
        return
    
    invoice_lines = data.get('invoice_lines')
    sales_orders = data.get('sales_orders')
    items = data.get('items')
    customers_df = data.get('customers')
    deals = data.get('deals')
    
    # Create product type mapping from Raw_Items
    product_type_map = get_product_type_mapping(items)
    
    # Enrich data with product types
    if invoice_lines is not None:
        invoice_lines = enrich_with_product_type(invoice_lines, product_type_map)
    if sales_orders is not None:
        sales_orders = enrich_with_product_type(sales_orders, product_type_map)
    
    # ==========================================================================
    # FILTERS - Now populated dynamically
    # ==========================================================================
    
    # Get filter options from data
    rep_options = ["All"] + get_unique_sales_reps(sales_orders, customers_df)
    
    # Get selected rep from session state or use first option
    if 'sr_selected_rep' not in st.session_state:
        st.session_state.sr_selected_rep = "All"
    
    # Update customer options based on selected rep
    customer_options = ["All"] + get_customers_for_rep(
        sales_orders, invoice_lines, 
        st.session_state.get('sr_selected_rep', 'All')
    )
    
    if 'sr_selected_customer' not in st.session_state:
        st.session_state.sr_selected_customer = "All"
    
    # Update item options based on selected customer
    item_options = ["All"] + get_items_for_customer(
        invoice_lines, sales_orders,
        st.session_state.get('sr_selected_customer', 'All')
    )
    
    # Filter bar
    st.markdown("---")
    filter_cols = st.columns([2, 2, 2, 2])
    
    with filter_cols[0]:
        selected_rep = st.selectbox(
            "Sales Rep",
            options=rep_options,
            index=rep_options.index(st.session_state.sr_selected_rep) if st.session_state.sr_selected_rep in rep_options else 0,
            key="filter_sr_rep"
        )
        if selected_rep != st.session_state.sr_selected_rep:
            st.session_state.sr_selected_rep = selected_rep
            st.session_state.sr_selected_customer = "All"  # Reset customer on rep change
            st.rerun()
    
    with filter_cols[1]:
        selected_customer = st.selectbox(
            "Customer",
            options=customer_options,
            index=customer_options.index(st.session_state.sr_selected_customer) if st.session_state.sr_selected_customer in customer_options else 0,
            key="filter_sr_customer"
        )
        if selected_customer != st.session_state.sr_selected_customer:
            st.session_state.sr_selected_customer = selected_customer
            st.rerun()
    
    with filter_cols[2]:
        selected_item = st.selectbox(
            "Item/SKU",
            options=item_options,
            key="filter_sr_item"
        )
    
    with filter_cols[3]:
        date_range = st.selectbox(
            "Date Range",
            options=["Last 12 Months", "Last 6 Months", "Last 3 Months", "YTD", "All Time"],
            key="filter_sr_date"
        )
    
    st.markdown("---")
    
    # ==========================================================================
    # APPLY FILTERS TO DATA
    # ==========================================================================
    
    filtered_invoices = invoice_lines.copy() if invoice_lines is not None else pd.DataFrame()
    
    # Apply rep filter
    if selected_rep != "All" and not filtered_invoices.empty:
        rep_col = next((c for c in filtered_invoices.columns if 'rep' in c.lower()), None)
        if rep_col:
            filtered_invoices = filtered_invoices[filtered_invoices[rep_col] == selected_rep]
    
    # Apply customer filter
    if selected_customer != "All" and not filtered_invoices.empty:
        cust_col = next((c for c in ['Customer', 'Correct Customer', 'Customer Name'] if c in filtered_invoices.columns), None)
        if cust_col:
            filtered_invoices = filtered_invoices[filtered_invoices[cust_col] == selected_customer]
    
    # Apply item filter
    if selected_item != "All" and not filtered_invoices.empty:
        item_col = next((c for c in ['Item', 'SKU', 'Item Name'] if c in filtered_invoices.columns), None)
        if item_col:
            filtered_invoices = filtered_invoices[filtered_invoices[item_col] == selected_item]
    
    # Apply date filter
    filtered_invoices = filter_data_by_date_range(filtered_invoices, date_range)
    
    # ==========================================================================
    # KPI METRICS
    # ==========================================================================
    
    kpi_cols = st.columns(4)
    
    # Calculate KPIs
    total_revenue = 0
    total_units = 0
    total_orders = 0
    avg_order_value = 0
    
    if not filtered_invoices.empty:
        amt_col = next((c for c in ['Amount', 'Total', 'Revenue', 'Line Amount'] if c in filtered_invoices.columns), None)
        qty_col = next((c for c in ['Quantity', 'Qty', 'Units'] if c in filtered_invoices.columns), None)
        
        if amt_col:
            total_revenue = filtered_invoices[amt_col].sum()
        if qty_col:
            total_units = filtered_invoices[qty_col].sum()
        total_orders = len(filtered_invoices)
        if total_orders > 0 and total_revenue > 0:
            avg_order_value = total_revenue / total_orders
    
    with kpi_cols[0]:
        st.metric("Total Revenue", f"${total_revenue:,.0f}")
    with kpi_cols[1]:
        st.metric("Total Units", f"{total_units:,.0f}")
    with kpi_cols[2]:
        st.metric("Total Orders", f"{total_orders:,}")
    with kpi_cols[3]:
        st.metric("Avg Order Value", f"${avg_order_value:,.2f}")
    
    # ==========================================================================
    # DEMAND BY PRODUCT CATEGORY
    # ==========================================================================
    
    st.markdown("### 📊 Demand by Product Category")
    
    if not filtered_invoices.empty and 'Product Type' in filtered_invoices.columns:
        amt_col = next((c for c in ['Amount', 'Total', 'Revenue'] if c in filtered_invoices.columns), None)
        
        if amt_col:
            by_category = filtered_invoices.groupby('Product Type')[amt_col].sum().sort_values(ascending=False)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig = px.bar(
                    x=by_category.index,
                    y=by_category.values,
                    labels={'x': 'Product Type', 'y': 'Revenue ($)'},
                    color=by_category.values,
                    color_continuous_scale='Blues'
                )
                fig.update_layout(
                    showlegend=False,
                    coloraxis_showscale=False,
                    height=350
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.dataframe(
                    by_category.reset_index().rename(columns={amt_col: 'Revenue', 'index': 'Product Type'}),
                    use_container_width=True,
                    hide_index=True
                )
    else:
        st.info("No data available for the selected filters.")
    
    # ==========================================================================
    # FORECAST PLANNING SECTION (NEW)
    # ==========================================================================
    
    st.markdown("---")
    st.markdown("### 📈 Forecast Planning")
    
    if selected_customer == "All":
        st.info("👆 Select a specific customer above to view their forecast planning details.")
    else:
        # Get customer demand data
        demand_df = calculate_customer_demand(
            invoice_lines, selected_customer, date_range, product_type_map
        )
        
        # Get deals/pipeline for customer
        customer_deals = get_deals_for_customer(deals, selected_customer)
        
        # Calculate historical revenue
        historical_revenue = calculate_historical_revenue(invoice_lines, selected_customer)
        
        # Generate forecast
        forecast_revenue = generate_revenue_forecast(historical_revenue)
        
        # ==========================================================================
        # FORECAST TABLE
        # ==========================================================================
        
        st.markdown("#### 📋 Item Demand & Projections")
        st.markdown(f"*Items ordered by **{selected_customer}**, sorted by Product Type*")
        
        if not demand_df.empty:
            # Display editable table
            edited_df = st.data_editor(
                demand_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Item': st.column_config.TextColumn('Item', disabled=True),
                    'Product Type': st.column_config.TextColumn('Category', disabled=True),
                    'Units': st.column_config.NumberColumn('Historical Units', disabled=True, format="%d"),
                    'Revenue': st.column_config.NumberColumn('Historical Revenue', disabled=True, format="$%.2f"),
                    'Orders': st.column_config.NumberColumn('Order Count', disabled=True),
                    'Projected Units': st.column_config.NumberColumn('Projected Units', format="%d"),
                    'Projected Revenue': st.column_config.NumberColumn('Projected Revenue', format="$%.2f")
                },
                key="forecast_table"
            )
            
            # Summary row
            if 'Projected Revenue' in edited_df.columns:
                total_projected = edited_df['Projected Revenue'].sum()
                st.markdown(f"**Total Projected Revenue: ${total_projected:,.2f}**")
        else:
            st.warning("No historical demand data found for this customer.")
        
        # ==========================================================================
        # PIPELINE/DEALS SECTION
        # ==========================================================================
        
        st.markdown("#### 🎯 Pipeline & Deals")
        
        if not customer_deals.empty:
            st.markdown("*Select deals to include in revenue projection:*")
            
            # Initialize session state for deal selections
            if 'selected_deals' not in st.session_state:
                st.session_state.selected_deals = {}
            
            # Find amount column in deals
            deal_amt_col = next((c for c in ['Amount', 'Deal Value', 'Value', 'Revenue'] if c in customer_deals.columns), None)
            deal_name_col = next((c for c in ['Deal Name', 'Name', 'Opportunity', 'Deal'] if c in customer_deals.columns), None)
            deal_stage_col = next((c for c in ['Stage', 'Deal Stage', 'Status'] if c in customer_deals.columns), None)
            
            selected_deals_total = 0
            
            # Create checkboxes for each deal
            for idx, row in customer_deals.iterrows():
                deal_name = row.get(deal_name_col, f'Deal {idx}') if deal_name_col else f'Deal {idx}'
                deal_amount = row.get(deal_amt_col, 0) if deal_amt_col else 0
                deal_stage = row.get(deal_stage_col, 'Unknown') if deal_stage_col else 'Unknown'
                
                col1, col2, col3 = st.columns([1, 3, 2])
                
                with col1:
                    is_selected = st.checkbox(
                        "",
                        key=f"deal_{idx}",
                        value=st.session_state.selected_deals.get(idx, False)
                    )
                    st.session_state.selected_deals[idx] = is_selected
                
                with col2:
                    st.markdown(f"**{deal_name}** - {deal_stage}")
                
                with col3:
                    st.markdown(f"${deal_amount:,.2f}")
                
                if is_selected:
                    selected_deals_total += deal_amount
            
            st.markdown(f"**Selected Pipeline Total: ${selected_deals_total:,.2f}**")
        else:
            st.info("No pipeline/deals found for this customer.")
            selected_deals_total = 0
        
        # ==========================================================================
        # REVENUE CHART
        # ==========================================================================
        
        st.markdown("#### 📊 Revenue Chart: Historical & Forecast")
        
        fig = create_revenue_chart(historical_revenue, forecast_revenue, selected_deals_total)
        st.plotly_chart(fig, use_container_width=True)
        
        # ==========================================================================
        # SUBMIT FORECAST BUTTON
        # ==========================================================================
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            if st.button("📤 Submit Forecast", type="primary", use_container_width=True):
                # Prepare forecast data
                forecast_data = {
                    'customer': selected_customer,
                    'date_submitted': datetime.now().isoformat(),
                    'date_range': date_range,
                    'demand_items': edited_df.to_dict() if not demand_df.empty else {},
                    'selected_deals_total': selected_deals_total,
                    'historical_revenue': historical_revenue.to_dict() if not historical_revenue.empty else {},
                    'forecast_revenue': forecast_revenue.to_dict() if not forecast_revenue.empty else {}
                }
                
                # Save forecast
                success = save_forecast_to_sheet(pd.DataFrame([forecast_data]), selected_customer)
                
                if success:
                    st.success(f"✅ Forecast submitted successfully for {selected_customer}!")
                    st.balloons()
                else:
                    st.error("❌ Error submitting forecast. Please try again.")
        
        # Export option
        with col3:
            if not demand_df.empty:
                csv = demand_df.to_csv(index=False)
                st.download_button(
                    label="📥 Export Forecast",
                    data=csv,
                    file_name=f"forecast_{selected_customer}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

