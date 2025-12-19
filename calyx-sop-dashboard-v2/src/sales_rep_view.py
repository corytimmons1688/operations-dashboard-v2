"""
Sales Rep View Module for S&OP Dashboard
Customer-focused demand analysis and forecasting

Author: Xander @ Calyx Containers
Version: 3.3.0
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
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
    if col_name not in df.columns:
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


def render_sales_rep_view():
    """Main render function for Sales Rep View."""
    
    st.markdown("### 👤 Sales Rep View")
    st.markdown("Customer-focused demand analysis and forecasting")
    
    # Load data
    try:
        from .sop_data_loader import (
            load_invoice_lines, load_sales_orders, load_items,
            load_customers, load_deals
        )
        
        invoice_lines = clean_dataframe(load_invoice_lines())
        sales_orders = clean_dataframe(load_sales_orders())
        items = clean_dataframe(load_items())
        customers_df = clean_dataframe(load_customers())
        deals = clean_dataframe(load_deals())
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return
    
    # Debug info (collapsible)
    with st.expander("🔧 Data Debug Info"):
        st.write(f"Invoice Lines: {len(invoice_lines) if invoice_lines is not None else 'None'} rows")
        st.write(f"Sales Orders: {len(sales_orders) if sales_orders is not None else 'None'} rows")
        st.write(f"Items: {len(items) if items is not None else 'None'} rows")
        st.write(f"Customers: {len(customers_df) if customers_df is not None else 'None'} rows")
        st.write(f"Deals: {len(deals) if deals is not None else 'None'} rows")
        if invoice_lines is not None:
            st.write("Columns:", list(invoice_lines.columns)[:15])
    
    if invoice_lines is None or invoice_lines.empty:
        st.error("No invoice data available.")
        return
    
    # ==========================================================================
    # IDENTIFY KEY COLUMNS
    # ==========================================================================
    
    customer_col = find_column(invoice_lines, ['customer'])
    item_col = find_column(invoice_lines, ['item', 'sku'], exclude=['description'])
    date_col = find_column(invoice_lines, ['date'])
    amount_col = find_column(invoice_lines, ['amount'])
    qty_col = find_column(invoice_lines, ['qty', 'quantity'])
    product_type_col = find_column(invoice_lines, ['product type', 'calyx'])
    rep_col = find_column(invoice_lines, ['rep'])
    
    # ==========================================================================
    # BUILD FILTER OPTIONS
    # ==========================================================================
    
    # Sales Reps
    rep_options = ["All"]
    if rep_col:
        rep_series = get_column_as_series(invoice_lines, rep_col)
        if rep_series is not None:
            reps = rep_series.dropna().astype(str).unique().tolist()
            rep_options.extend(sorted([r for r in reps if r.strip()]))
    
    # Customers
    customer_options = ["All"]
    if customer_col:
        cust_series = get_column_as_series(invoice_lines, customer_col)
        if cust_series is not None:
            custs = cust_series.dropna().astype(str).unique().tolist()
            customer_options.extend(sorted([c for c in custs if c.strip()][:200]))
    
    # Items
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
        selected_rep = st.selectbox("Sales Rep", rep_options, key="srv_rep")
    with col2:
        selected_customer = st.selectbox("Customer", customer_options, key="srv_cust")
    with col3:
        selected_item = st.selectbox("Item/SKU", item_options, key="srv_item")
    with col4:
        date_range = st.selectbox(
            "Date Range", 
            ["Last 12 Months", "Last 6 Months", "Last 3 Months", "YTD", "All Time"],
            key="srv_date"
        )
    
    st.markdown("---")
    
    # ==========================================================================
    # APPLY FILTERS
    # ==========================================================================
    
    filtered = invoice_lines.copy()
    
    # Rep filter
    if selected_rep != "All" and rep_col:
        rep_series = get_column_as_series(filtered, rep_col)
        if rep_series is not None:
            filtered = filtered[rep_series == selected_rep].copy()
    
    # Customer filter
    if selected_customer != "All" and customer_col:
        cust_series = get_column_as_series(filtered, customer_col)
        if cust_series is not None:
            filtered = filtered[cust_series == selected_customer].copy()
    
    # Item filter
    if selected_item != "All" and item_col:
        item_series = get_column_as_series(filtered, item_col)
        if item_series is not None:
            filtered = filtered[item_series == selected_item].copy()
    
    # Date filter
    if date_col and date_range != "All Time":
        try:
            date_series = get_column_as_series(filtered, date_col)
            if date_series is not None:
                date_series = pd.to_datetime(date_series, errors='coerce')
                today = datetime.now()
                
                if date_range == "Last 12 Months":
                    start = today - timedelta(days=365)
                elif date_range == "Last 6 Months":
                    start = today - timedelta(days=180)
                elif date_range == "Last 3 Months":
                    start = today - timedelta(days=90)
                elif date_range == "YTD":
                    start = datetime(today.year, 1, 1)
                else:
                    start = None
                
                if start:
                    filtered = filtered[date_series >= start].copy()
        except Exception as e:
            st.warning(f"Date filter error: {e}")
    
    # Convert numeric columns
    if amount_col:
        amt_series = get_column_as_series(filtered, amount_col)
        if amt_series is not None:
            filtered.loc[:, amount_col] = pd.to_numeric(amt_series, errors='coerce')
    
    if qty_col:
        qty_series = get_column_as_series(filtered, qty_col)
        if qty_series is not None:
            filtered.loc[:, qty_col] = pd.to_numeric(qty_series, errors='coerce')
    
    # ==========================================================================
    # KPI METRICS
    # ==========================================================================
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    total_revenue = filtered[amount_col].sum() if amount_col else 0
    total_units = filtered[qty_col].sum() if qty_col else 0
    total_orders = len(filtered)
    avg_order = total_revenue / total_orders if total_orders > 0 else 0
    
    with kpi1:
        st.metric("Total Revenue", f"${total_revenue:,.0f}")
    with kpi2:
        st.metric("Total Units", f"{total_units:,.0f}")
    with kpi3:
        st.metric("Line Items", f"{total_orders:,}")
    with kpi4:
        st.metric("Avg Line Value", f"${avg_order:,.2f}")
    
    # ==========================================================================
    # DEMAND BY PRODUCT TYPE
    # ==========================================================================
    
    st.markdown("### 📊 Demand by Product Type")
    
    if product_type_col and amount_col:
        try:
            type_series = get_column_as_series(filtered, product_type_col)
            amt_series = get_column_as_series(filtered, amount_col)
            
            if type_series is not None and amt_series is not None:
                temp_df = pd.DataFrame({
                    'Product Type': type_series,
                    'Amount': amt_series
                })
                by_type = temp_df.groupby('Product Type')['Amount'].sum().sort_values(ascending=False)
                by_type = by_type[by_type > 0].head(15)
                
                if not by_type.empty:
                    chart_df = pd.DataFrame({
                        'Product Type': by_type.index,
                        'Revenue': by_type.values
                    })
                    
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        fig = px.bar(chart_df, x='Product Type', y='Revenue', 
                                     color='Revenue', color_continuous_scale='Blues')
                        fig.update_layout(height=400, showlegend=False, coloraxis_showscale=False)
                        st.plotly_chart(fig, use_container_width=True)
                    with col2:
                        st.dataframe(chart_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No product type data available.")
        except Exception as e:
            st.warning(f"Chart error: {e}")
    else:
        st.info("Product Type column not found in data.")
    
    # ==========================================================================
    # FORECAST PLANNING SECTION
    # ==========================================================================
    
    st.markdown("---")
    st.markdown("### 📈 Forecast Planning")
    
    if selected_customer == "All":
        st.info("👆 Select a specific customer above to view forecast planning details.")
    else:
        st.markdown(f"#### Forecast for: {selected_customer}")
        
        # Item demand summary
        if item_col and amount_col:
            try:
                item_series = get_column_as_series(filtered, item_col)
                amt_series = get_column_as_series(filtered, amount_col)
                
                if item_series is not None and amt_series is not None:
                    temp_df = pd.DataFrame({
                        'Item': item_series,
                        'Revenue': amt_series
                    })
                    
                    # Add product type if available
                    if product_type_col:
                        type_series = get_column_as_series(filtered, product_type_col)
                        if type_series is not None:
                            temp_df['Product Type'] = type_series
                    
                    # Aggregate
                    if 'Product Type' in temp_df.columns:
                        demand = temp_df.groupby(['Item', 'Product Type'])['Revenue'].sum().reset_index()
                        demand = demand.sort_values(['Product Type', 'Revenue'], ascending=[True, False])
                    else:
                        demand = temp_df.groupby('Item')['Revenue'].sum().reset_index()
                        demand = demand.sort_values('Revenue', ascending=False)
                    
                    demand = demand.head(25)
                    
                    # Add projections
                    demand['Projected Revenue'] = (demand['Revenue'] * 1.10).round(2)
                    
                    st.markdown("##### 📋 Item Demand & Projections")
                    st.dataframe(demand, use_container_width=True, hide_index=True)
                    
                    # Growth rate slider
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        growth = st.slider("Adjust Growth Rate %", -50, 100, 10, 5)
                    with col2:
                        projected_total = demand['Revenue'].sum() * (1 + growth/100)
                        st.metric("Total Projected Revenue", f"${projected_total:,.2f}")
                    
            except Exception as e:
                st.warning(f"Demand table error: {e}")
        
        # ==========================================================================
        # PIPELINE / DEALS
        # ==========================================================================
        
        st.markdown("##### 🎯 Pipeline & Deals")
        
        if deals is not None and not deals.empty:
            deal_cust_col = find_column(deals, ['company', 'customer', 'account'])
            
            if deal_cust_col:
                try:
                    deal_cust_series = get_column_as_series(deals, deal_cust_col)
                    if deal_cust_series is not None:
                        mask = deal_cust_series.str.contains(selected_customer, case=False, na=False)
                        customer_deals = deals[mask].copy()
                        
                        if not customer_deals.empty:
                            st.write(f"Found {len(customer_deals)} deals")
                            st.dataframe(customer_deals.head(10), use_container_width=True, hide_index=True)
                            
                            # Sum deal amounts if column exists
                            deal_amt_col = find_column(customer_deals, ['amount', 'value'])
                            if deal_amt_col:
                                deal_amt = get_column_as_series(customer_deals, deal_amt_col)
                                if deal_amt is not None:
                                    deal_total = pd.to_numeric(deal_amt, errors='coerce').sum()
                                    st.metric("Total Pipeline Value", f"${deal_total:,.2f}")
                        else:
                            st.info("No deals found for this customer.")
                except Exception as e:
                    st.warning(f"Deals error: {e}")
            else:
                st.info("Could not find customer column in deals data.")
        else:
            st.info("No deals data available.")
        
        # ==========================================================================
        # SUBMIT FORECAST
        # ==========================================================================
        
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("📤 Submit Forecast", type="primary", use_container_width=True):
                st.success(f"✅ Forecast submitted for {selected_customer}!")
                st.balloons()
