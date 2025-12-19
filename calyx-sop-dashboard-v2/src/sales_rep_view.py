"""
Sales Rep View Module - Minimal Version
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


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
        
        invoice_lines = load_invoice_lines()
        sales_orders = load_sales_orders()
        items = load_items()
        customers_df = load_customers()
        deals = load_deals()
        
    except Exception as e:
        st.error(f"Error importing/loading data: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return
    
    # Debug info
    st.write("**Data Loaded:**")
    st.write(f"- Invoice Lines: {len(invoice_lines) if invoice_lines is not None else 'None'} rows")
    st.write(f"- Sales Orders: {len(sales_orders) if sales_orders is not None else 'None'} rows")
    st.write(f"- Items: {len(items) if items is not None else 'None'} rows")
    st.write(f"- Customers: {len(customers_df) if customers_df is not None else 'None'} rows")
    st.write(f"- Deals: {len(deals) if deals is not None else 'None'} rows")
    
    if invoice_lines is None:
        st.error("No invoice data available.")
        return
    
    st.markdown("---")
    
    # Simple filters - no fancy features
    st.write("**Filters:**")
    
    # Get customer list simply
    customer_list = ["All"]
    try:
        for col in invoice_lines.columns:
            if 'customer' in col.lower():
                vals = invoice_lines[col].dropna().astype(str).unique().tolist()
                customer_list = ["All"] + sorted([v for v in vals if v.strip()][:50])
                break
    except Exception as e:
        st.warning(f"Error getting customers: {e}")
    
    selected_customer = st.selectbox("Select Customer", customer_list)
    
    st.markdown("---")
    
    # Filter data - use .copy() to avoid SettingWithCopyWarning
    filtered = invoice_lines.copy()
    
    # Check for duplicate columns
    if filtered.columns.duplicated().any():
        st.warning("Warning: Duplicate column names detected. Using first occurrence.")
        filtered = filtered.loc[:, ~filtered.columns.duplicated()]
    
    if selected_customer != "All":
        for col in filtered.columns:
            if 'customer' in col.lower():
                filtered = filtered[filtered[col] == selected_customer].copy()
                break
    
    # Show basic stats
    st.write(f"**Filtered rows:** {len(filtered)}")
    
    # Find amount column - be explicit about getting first match only
    amount_col = None
    for col in filtered.columns:
        col_lower = str(col).lower()
        if 'amount' in col_lower and amount_col is None:
            amount_col = col
            break
    
    if amount_col is not None:
        try:
            # Get the column as a Series explicitly using .iloc or .loc
            amount_data = filtered.loc[:, amount_col].copy()
            
            # Convert to numeric
            amount_numeric = pd.to_numeric(amount_data, errors='coerce')
            filtered.loc[:, amount_col] = amount_numeric
            
            total = amount_numeric.sum()
            if pd.notna(total):
                st.metric("Total Revenue", f"${total:,.0f}")
            else:
                st.metric("Total Revenue", "$0")
        except Exception as e:
            st.warning(f"Could not process amount column '{amount_col}': {e}")
            import traceback
            st.code(traceback.format_exc())
    
    # Show sample data
    st.write("**Sample Data (first 10 rows):**")
    st.dataframe(filtered.head(10))
    
    st.markdown("---")
    st.success("✅ Sales Rep View loaded successfully!")
