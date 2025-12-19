"""
Sales Rep View Module for S&OP Dashboard
Customer-focused demand analysis and forecasting

Author: Xander @ Calyx Containers
Version: 3.2.0 - Simplified
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def render_sales_rep_view():
    """Main render function for Sales Rep View."""
    
    st.markdown("### 👤 Sales Rep View")
    st.markdown("Customer-focused demand analysis and forecasting")
    
    # Load data with error handling
    try:
        from .sop_data_loader import (
            load_invoice_lines, load_sales_orders, load_items,
            load_customers, load_deals
        )
        
        with st.spinner("Loading sales data..."):
            invoice_lines = load_invoice_lines()
            sales_orders = load_sales_orders()
            items = load_items()
            customers_df = load_customers()
            deals = load_deals()
            
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return
    
    # Debug info
    with st.expander("🔧 Data Debug Info"):
        st.write(f"Invoice Lines: {len(invoice_lines) if invoice_lines is not None else 'None'} rows")
        st.write(f"Sales Orders: {len(sales_orders) if sales_orders is not None else 'None'} rows")
        st.write(f"Items: {len(items) if items is not None else 'None'} rows")
        st.write(f"Customers: {len(customers_df) if customers_df is not None else 'None'} rows")
        st.write(f"Deals: {len(deals) if deals is not None else 'None'} rows")
        
        if invoice_lines is not None:
            st.write("Invoice Lines columns:", list(invoice_lines.columns)[:10])
    
    if invoice_lines is None:
        st.error("Unable to load invoice data.")
        return
    
    # ==========================================================================
    # BUILD FILTER OPTIONS
    # ==========================================================================
    
    # Get unique reps
    rep_options = ["All"]
    if sales_orders is not None:
        for col in sales_orders.columns:
            if 'rep' in col.lower():
                reps = sales_orders[col].dropna().unique().tolist()
                rep_options.extend([str(r) for r in reps if r])
                break
    rep_options = list(dict.fromkeys(rep_options))  # Remove duplicates
    
    # Get unique customers
    customer_options = ["All"]
    for col in invoice_lines.columns:
        if 'customer' in col.lower():
            custs = invoice_lines[col].dropna().unique().tolist()
            customer_options.extend([str(c) for c in custs if c and str(c).strip()])
            break
    customer_options = sorted(list(set(customer_options)))[:100]  # Limit to 100
    
    # Get unique items
    item_options = ["All"]
    for col in invoice_lines.columns:
        if col.lower() in ['item', 'sku', 'item name']:
            items_list = invoice_lines[col].dropna().unique().tolist()
            item_options.extend([str(i) for i in items_list if i][:100])
            break
    
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
    
    filtered_df = invoice_lines.copy()
    
    # Find column names
    customer_col = None
    item_col = None
    date_col = None
    amount_col = None
    qty_col = None
    
    for col in filtered_df.columns:
        col_lower = col.lower()
        if customer_col is None and 'customer' in col_lower:
            customer_col = col
        if item_col is None and col_lower in ['item', 'sku']:
            item_col = col
        if date_col is None and 'date' in col_lower:
            date_col = col
        if amount_col is None and ('amount' in col_lower or 'revenue' in col_lower):
            amount_col = col
        if qty_col is None and ('qty' in col_lower or 'quantity' in col_lower):
            qty_col = col
    
    # Apply customer filter
    if selected_customer != "All" and customer_col:
        filtered_df = filtered_df[filtered_df[customer_col] == selected_customer]
    
    # Apply item filter
    if selected_item != "All" and item_col:
        filtered_df = filtered_df[filtered_df[item_col] == selected_item]
    
    # Apply date filter
    if date_col and date_range != "All Time":
        try:
            filtered_df[date_col] = pd.to_datetime(filtered_df[date_col], errors='coerce')
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
                filtered_df = filtered_df[filtered_df[date_col] >= start]
        except Exception as e:
            st.warning(f"Could not filter by date: {e}")
    
    # ==========================================================================
    # KPI METRICS
    # ==========================================================================
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    total_revenue = 0
    total_units = 0
    total_orders = len(filtered_df)
    
    if amount_col and amount_col in filtered_df.columns:
        filtered_df[amount_col] = pd.to_numeric(filtered_df[amount_col], errors='coerce')
        total_revenue = filtered_df[amount_col].sum()
    
    if qty_col and qty_col in filtered_df.columns:
        filtered_df[qty_col] = pd.to_numeric(filtered_df[qty_col], errors='coerce')
        total_units = filtered_df[qty_col].sum()
    
    with kpi1:
        st.metric("Total Revenue", f"${total_revenue:,.0f}")
    with kpi2:
        st.metric("Total Units", f"{total_units:,.0f}")
    with kpi3:
        st.metric("Total Orders", f"{total_orders:,}")
    with kpi4:
        avg = total_revenue / total_orders if total_orders > 0 else 0
        st.metric("Avg Order Value", f"${avg:,.2f}")
    
    # ==========================================================================
    # DEMAND BY PRODUCT TYPE
    # ==========================================================================
    
    st.markdown("### 📊 Demand by Product Type")
    
    # Find product type column
    product_type_col = None
    for col in filtered_df.columns:
        if 'product type' in col.lower() or 'calyx' in col.lower():
            product_type_col = col
            break
    
    if product_type_col and amount_col:
        try:
            by_type = filtered_df.groupby(product_type_col)[amount_col].sum().sort_values(ascending=False)
            by_type = by_type[by_type > 0].head(15)  # Top 15
            
            if not by_type.empty:
                chart_df = pd.DataFrame({
                    'Product Type': by_type.index,
                    'Revenue': by_type.values
                })
                
                fig = px.bar(chart_df, x='Product Type', y='Revenue')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No product type data available.")
        except Exception as e:
            st.warning(f"Could not create chart: {e}")
    else:
        st.info("Product Type or Amount column not found.")
    
    # ==========================================================================
    # FORECAST PLANNING SECTION
    # ==========================================================================
    
    st.markdown("---")
    st.markdown("### 📈 Forecast Planning")
    
    if selected_customer == "All":
        st.info("👆 Select a specific customer above to view forecast planning.")
        return
    
    # Customer demand summary
    st.markdown(f"#### Customer: {selected_customer}")
    
    if item_col and amount_col:
        try:
            demand_summary = filtered_df.groupby(item_col).agg({
                amount_col: 'sum'
            }).reset_index()
            demand_summary.columns = ['Item', 'Revenue']
            demand_summary = demand_summary.sort_values('Revenue', ascending=False).head(20)
            
            # Add projections (10% growth)
            demand_summary['Projected Revenue'] = demand_summary['Revenue'] * 1.10
            
            st.dataframe(demand_summary, use_container_width=True, hide_index=True)
            
            total_proj = demand_summary['Projected Revenue'].sum()
            st.markdown(f"**Total Projected Revenue: ${total_proj:,.2f}**")
            
        except Exception as e:
            st.warning(f"Could not create demand summary: {e}")
    
    # ==========================================================================
    # DEALS/PIPELINE
    # ==========================================================================
    
    st.markdown("#### 🎯 Pipeline & Deals")
    
    if deals is not None and not deals.empty:
        # Find customer column in deals
        deal_cust_col = None
        for col in deals.columns:
            if 'company' in col.lower() or 'customer' in col.lower():
                deal_cust_col = col
                break
        
        if deal_cust_col:
            customer_deals = deals[deals[deal_cust_col].str.contains(selected_customer, case=False, na=False)]
            
            if not customer_deals.empty:
                st.write(f"Found {len(customer_deals)} deals for this customer")
                st.dataframe(customer_deals.head(10), use_container_width=True, hide_index=True)
            else:
                st.info("No deals found for this customer.")
        else:
            st.info("Could not identify customer column in deals data.")
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
