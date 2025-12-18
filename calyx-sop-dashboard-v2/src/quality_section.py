"""
Quality Section Module for S&OP Dashboard
Tab 6: Wrapper for existing NC Dashboard functionality

This module organizes the existing NC Dashboard components into
sub-tabs within the S&OP structure.

Author: Xander @ Calyx Containers
"""

import streamlit as st
import pandas as pd
from typing import Optional
import logging

# Import existing NC Dashboard modules
from .data_loader import load_nc_data
from .kpi_cards import render_open_nc_status_tracker
from .aging_analysis import render_aging_dashboard
from .cost_analysis import render_cost_of_rework, render_cost_avoided
from .customer_analysis import render_customer_analysis
from .pareto_chart import render_issue_type_pareto

logger = logging.getLogger(__name__)


def render_quality_section():
    """Main render function for Quality Section (NC Dashboard)."""
    
    st.markdown("## 🔍 Quality Management")
    st.markdown("Non-Conformance tracking, analysis, and reporting")
    
    # Load NC data
    with st.spinner("Loading quality data..."):
        nc_data = load_nc_data()
    
    if nc_data is None or nc_data.empty:
        st.error("Unable to load Non-Conformance data. Please check your data connection.")
        st.info("Ensure the 'Non-Conformance Details' sheet exists and is accessible.")
        return
    
    # Display data summary
    st.sidebar.markdown("### 📊 NC Data Summary")
    st.sidebar.markdown(f"**Total Records:** {len(nc_data):,}")
    
    if 'Status' in nc_data.columns:
        closed_statuses = ['closed', 'complete', 'resolved', 'done']
        open_count = len(nc_data[~nc_data['Status'].str.lower().isin(closed_statuses)])
        st.sidebar.markdown(f"**Open NCs:** {open_count:,}")
    
    if 'Date Submitted' in nc_data.columns:
        nc_data['Date Submitted'] = pd.to_datetime(nc_data['Date Submitted'], errors='coerce')
        latest = nc_data['Date Submitted'].max()
        if pd.notna(latest):
            st.sidebar.markdown(f"**Latest NC:** {latest.strftime('%Y-%m-%d')}")
    
    st.sidebar.markdown("---")
    
    # Create sub-tabs for NC Dashboard sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Status Tracker",
        "⏱️ Aging Analysis",
        "💰 Cost Analysis",
        "👥 Customer Analysis",
        "📊 Pareto Analysis",
        "📋 Raw Data"
    ])
    
    with tab1:
        render_status_tracker_tab(nc_data)
    
    with tab2:
        render_aging_tab(nc_data)
    
    with tab3:
        render_cost_tab(nc_data)
    
    with tab4:
        render_customer_tab(nc_data)
    
    with tab5:
        render_pareto_tab(nc_data)
    
    with tab6:
        render_raw_data_tab(nc_data)


def render_status_tracker_tab(nc_data: pd.DataFrame):
    """Render the NC Status Tracker sub-tab."""
    
    st.markdown("### 📈 Open NC Status Tracker")
    st.markdown("Monitor open non-conformances and their status")
    
    try:
        render_open_nc_status_tracker(nc_data)
    except Exception as e:
        st.error(f"Error rendering status tracker: {str(e)}")
        logger.error(f"Status tracker error: {e}")


def render_aging_tab(nc_data: pd.DataFrame):
    """Render the NC Aging Analysis sub-tab."""
    
    st.markdown("### ⏱️ NC Aging Analysis")
    st.markdown("Analyze how long non-conformances have been open")
    
    try:
        render_aging_dashboard(nc_data)
    except Exception as e:
        st.error(f"Error rendering aging analysis: {str(e)}")
        logger.error(f"Aging analysis error: {e}")


def render_cost_tab(nc_data: pd.DataFrame):
    """Render the Cost Analysis sub-tab."""
    
    st.markdown("### 💰 Cost of Quality Analysis")
    st.markdown("Track rework costs and cost avoidance")
    
    try:
        # Show both cost of rework and cost avoided
        st.markdown("#### Cost of Rework")
        render_cost_of_rework(nc_data)
        
        st.markdown("---")
        
        st.markdown("#### Cost Avoided")
        render_cost_avoided(nc_data)
        
    except Exception as e:
        st.error(f"Error rendering cost analysis: {str(e)}")
        logger.error(f"Cost analysis error: {e}")


def render_customer_tab(nc_data: pd.DataFrame):
    """Render the Customer Analysis sub-tab."""
    
    st.markdown("### 👥 Customer Impact Analysis")
    st.markdown("Analyze non-conformances by customer")
    
    try:
        render_customer_analysis(nc_data)
    except Exception as e:
        st.error(f"Error rendering customer analysis: {str(e)}")
        logger.error(f"Customer analysis error: {e}")


def render_pareto_tab(nc_data: pd.DataFrame):
    """Render the Pareto Analysis sub-tab."""
    
    st.markdown("### 📊 Pareto Analysis")
    st.markdown("Identify the vital few causes of non-conformances")
    
    try:
        render_issue_type_pareto(nc_data)
    except Exception as e:
        st.error(f"Error rendering pareto analysis: {str(e)}")
        logger.error(f"Pareto analysis error: {e}")


def render_raw_data_tab(nc_data: pd.DataFrame):
    """Render the Raw Data sub-tab with full data access."""
    
    st.markdown("### 📋 NC Data Explorer")
    st.markdown("View and export all non-conformance data")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'Status' in nc_data.columns:
            statuses = ['All'] + sorted(nc_data['Status'].dropna().unique().tolist())
            selected_status = st.selectbox(
                "Filter by Status",
                options=statuses,
                key="raw_nc_status_filter"
            )
        else:
            selected_status = 'All'
    
    with col2:
        if 'Customer' in nc_data.columns:
            customers = ['All'] + sorted(nc_data['Customer'].dropna().unique().tolist())
            selected_customer = st.selectbox(
                "Filter by Customer",
                options=customers,
                key="raw_nc_customer_filter"
            )
        else:
            selected_customer = 'All'
    
    with col3:
        if 'Issue Type' in nc_data.columns:
            issue_types = ['All'] + sorted(nc_data['Issue Type'].dropna().unique().tolist())
            selected_issue = st.selectbox(
                "Filter by Issue Type",
                options=issue_types,
                key="raw_nc_issue_filter"
            )
        else:
            selected_issue = 'All'
    
    # Apply filters
    filtered_data = nc_data.copy()
    
    if selected_status != 'All':
        filtered_data = filtered_data[filtered_data['Status'] == selected_status]
    
    if selected_customer != 'All':
        filtered_data = filtered_data[filtered_data['Customer'] == selected_customer]
    
    if selected_issue != 'All':
        filtered_data = filtered_data[filtered_data['Issue Type'] == selected_issue]
    
    # Search
    search_term = st.text_input(
        "🔎 Search across all columns",
        "",
        key="raw_nc_search"
    )
    
    if search_term:
        mask = filtered_data.astype(str).apply(
            lambda row: row.str.contains(search_term, case=False, na=False).any(),
            axis=1
        )
        filtered_data = filtered_data[mask]
    
    # Display count
    st.markdown(f"**Showing {len(filtered_data):,} of {len(nc_data):,} records** | {len(filtered_data.columns)} columns")
    
    # Column selector
    with st.expander("📑 Select Columns to Display"):
        all_cols = filtered_data.columns.tolist()
        default_cols = ['NC Number', 'Status', 'Customer', 'Issue Type', 'Date Submitted', 
                       'Priority', 'Cost of Rework', 'Total Quantity Affected']
        default_cols = [c for c in default_cols if c in all_cols]
        
        selected_cols = st.multiselect(
            "Choose columns",
            options=all_cols,
            default=default_cols if default_cols else all_cols[:8],
            key="raw_nc_columns"
        )
    
    if not selected_cols:
        selected_cols = all_cols
    
    # Prepare display data
    display_data = filtered_data[selected_cols].copy()
    
    # Format date columns
    for col in display_data.columns:
        if display_data[col].dtype == 'datetime64[ns]':
            display_data[col] = display_data[col].dt.strftime('%Y-%m-%d')
    
    # Display table
    st.dataframe(
        display_data,
        use_container_width=True,
        hide_index=True,
        height=500
    )
    
    # Export options
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        csv_filtered = filtered_data.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data (CSV)",
            data=csv_filtered,
            file_name="nc_data_filtered.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        csv_all = nc_data.to_csv(index=False)
        st.download_button(
            label="📥 Download All NC Data (CSV)",
            data=csv_all,
            file_name="nc_data_complete.csv",
            mime="text/csv",
            use_container_width=True
        )
