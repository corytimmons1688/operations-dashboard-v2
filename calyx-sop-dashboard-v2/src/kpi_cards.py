"""
KPI Cards Module for NC Dashboard
Renders the Open NC Status Tracker with various visualizations

Author: Xander @ Calyx Containers
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def render_open_nc_status_tracker(df: pd.DataFrame) -> None:
    """
    Render the Open NCs Status Tracker dashboard section.
    
    Displays:
    - KPI metric cards for each status
    - Status distribution bar chart
    - Status gauge charts
    - Priority breakdown within open NCs
    
    Args:
        df: Filtered NC DataFrame
    """
    st.markdown("## 📋 Current Open NCs Status Tracker")
    st.markdown("Real-time view of all non-conformance tickets by status")
    
    if df.empty:
        st.warning("No data available for the selected filters.")
        return
    
    # Get status counts
    status_counts = df['Status'].value_counts()
    total_ncs = len(df)
    
    # Define status colors
    status_colors = {
        'Open': '#FF6B6B',
        'In Progress': '#4ECDC4',
        'Pending Review': '#FFE66D',
        'Closed': '#95E1D3',
        'On Hold': '#DDA0DD'
    }
    
    # Row 1: KPI Metric Cards
    st.markdown("### Status Overview")
    
    # Create columns for metrics
    cols = st.columns(len(status_counts) if len(status_counts) <= 5 else 5)
    
    for idx, (status, count) in enumerate(status_counts.items()):
        if idx < 5:  # Show top 5 statuses
            with cols[idx]:
                percentage = (count / total_ncs) * 100
                color = status_colors.get(status, '#888888')
                
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, {color}22, {color}44);
                    border-left: 4px solid {color};
                    border-radius: 8px;
                    padding: 1rem;
                    text-align: center;
                ">
                    <h3 style="margin: 0; color: #333;">{count}</h3>
                    <p style="margin: 0; color: #666; font-size: 0.9rem;">{status}</p>
                    <p style="margin: 0; color: {color}; font-weight: bold;">{percentage:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Row 2: Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Status Distribution")
        
        # Bar chart
        fig_bar = px.bar(
            x=status_counts.index,
            y=status_counts.values,
            color=status_counts.index,
            color_discrete_map=status_colors,
            labels={'x': 'Status', 'y': 'Count'},
            title=""
        )
        fig_bar.update_layout(
            showlegend=False,
            xaxis_title="Status",
            yaxis_title="Number of NCs",
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        fig_bar.update_traces(
            texttemplate='%{y}',
            textposition='outside'
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        st.markdown("### Status Breakdown")
        
        # Pie/Donut chart
        fig_pie = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            hole=0.4,
            color=status_counts.index,
            color_discrete_map=status_colors
        )
        fig_pie.update_layout(
            height=400,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2)
        )
        fig_pie.update_traces(
            textposition='inside',
            textinfo='percent+label'
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    st.markdown("---")
    
    # Row 3: Open NCs Deep Dive
    st.markdown("### 🔍 Open NCs Deep Dive")
    
    # Filter for open (non-closed) NCs - exclude only "Closed" status
    # This captures all statuses that are not explicitly "Closed"
    closed_statuses = ['Closed', 'Complete', 'Resolved', 'Done']
    open_ncs = df[~df['Status'].str.lower().isin([s.lower() for s in closed_statuses])]
    
    if not open_ncs.empty:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Priority breakdown for open NCs
            priority_counts = open_ncs['Priority'].value_counts()
            
            priority_colors = {
                'High': '#FF4444',
                'Medium': '#FFAA00',
                'Low': '#44AA44'
            }
            
            fig_priority = px.bar(
                x=priority_counts.index,
                y=priority_counts.values,
                color=priority_counts.index,
                color_discrete_map=priority_colors,
                title="Open NCs by Priority"
            )
            fig_priority.update_layout(
                showlegend=False,
                height=300,
                xaxis_title="Priority",
                yaxis_title="Count"
            )
            st.plotly_chart(fig_priority, use_container_width=True)
        
        with col2:
            # External vs Internal breakdown
            ext_int_counts = open_ncs['External Or Internal'].value_counts()
            
            fig_ext_int = px.pie(
                values=ext_int_counts.values,
                names=ext_int_counts.index,
                title="External vs Internal",
                color_discrete_sequence=['#667eea', '#f093fb']
            )
            fig_ext_int.update_layout(height=300)
            st.plotly_chart(fig_ext_int, use_container_width=True)
        
        with col3:
            # Gauge for open NC percentage
            open_percentage = (len(open_ncs) / total_ncs) * 100
            
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=open_percentage,
                title={'text': "Open NC Rate"},
                delta={'reference': 50},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#FF6B6B"},
                    'steps': [
                        {'range': [0, 30], 'color': '#95E1D3'},
                        {'range': [30, 60], 'color': '#FFE66D'},
                        {'range': [60, 100], 'color': '#FF6B6B'}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 75
                    }
                }
            ))
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        # NEW: Full Detail Table with Status Filter
        st.markdown("---")
        st.markdown("### 📋 Open NCs - Full Detail Table")
        st.markdown("View all source data columns, filtered by status")
        
        # Status filter for the detail table
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Get unique statuses from open NCs
            available_statuses = ["All Open"] + sorted(open_ncs['Status'].dropna().unique().tolist())
            selected_status = st.selectbox(
                "Filter by Status",
                options=available_statuses,
                index=0,
                key="open_nc_status_filter"
            )
        
        with col2:
            # Priority filter
            available_priorities = ["All"] + sorted(open_ncs['Priority'].dropna().unique().tolist())
            selected_priority = st.selectbox(
                "Filter by Priority",
                options=available_priorities,
                index=0,
                key="open_nc_priority_filter"
            )
        
        with col3:
            # External/Internal filter
            available_ext_int = ["All"] + sorted(open_ncs['External Or Internal'].dropna().unique().tolist())
            selected_ext_int = st.selectbox(
                "External/Internal",
                options=available_ext_int,
                index=0,
                key="open_nc_ext_int_filter"
            )
        
        with col4:
            # Customer filter
            available_customers = ["All"] + sorted(open_ncs['Customer'].dropna().unique().tolist())
            selected_customer = st.selectbox(
                "Filter by Customer",
                options=available_customers,
                index=0,
                key="open_nc_customer_filter"
            )
        
        # Apply filters
        filtered_open_ncs = open_ncs.copy()
        
        if selected_status != "All Open":
            filtered_open_ncs = filtered_open_ncs[filtered_open_ncs['Status'] == selected_status]
        
        if selected_priority != "All":
            filtered_open_ncs = filtered_open_ncs[filtered_open_ncs['Priority'] == selected_priority]
        
        if selected_ext_int != "All":
            filtered_open_ncs = filtered_open_ncs[filtered_open_ncs['External Or Internal'] == selected_ext_int]
        
        if selected_customer != "All":
            filtered_open_ncs = filtered_open_ncs[filtered_open_ncs['Customer'] == selected_customer]
        
        # Search box
        search_term = st.text_input(
            "🔎 Search across all columns",
            "",
            key="open_nc_search"
        )
        
        if search_term:
            search_mask = filtered_open_ncs.astype(str).apply(
                lambda row: row.str.contains(search_term, case=False, na=False).any(),
                axis=1
            )
            filtered_open_ncs = filtered_open_ncs[search_mask]
        
        # Display record count
        st.markdown(f"**Showing {len(filtered_open_ncs)} of {len(open_ncs)} open NCs** | {len(filtered_open_ncs.columns)} columns available")
        
        # Show column list
        with st.expander("📑 View All Column Names"):
            st.markdown(", ".join(filtered_open_ncs.columns.tolist()))
        
        # Prepare display dataframe with ALL columns
        display_df = filtered_open_ncs.copy()
        
        # Format date columns for display
        for col in display_df.columns:
            if display_df[col].dtype == 'datetime64[ns]':
                display_df[col] = display_df[col].dt.strftime('%Y-%m-%d')
        
        # Display the FULL dataframe with ALL columns
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=500
        )
        
        # Export filtered data
        col1, col2 = st.columns(2)
        
        with col1:
            csv_data = filtered_open_ncs.to_csv(index=False)
            st.download_button(
                label="📥 Download Filtered Open NCs (CSV)",
                data=csv_data,
                file_name="open_ncs_filtered.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            csv_all = open_ncs.to_csv(index=False)
            st.download_button(
                label="📥 Download All Open NCs (CSV)",
                data=csv_all,
                file_name="open_ncs_all.csv",
                mime="text/csv",
                use_container_width=True
            )
    else:
        st.success("🎉 No open NCs! All non-conformances have been resolved.")
    
    # Export option
    st.markdown("---")
    with st.expander("📥 Export Status Data"):
        export_df = df[['NC Number', 'Status', 'Priority', 'Customer', 
                       'Issue Type', 'Date Submitted', 'Cost of Rework']].copy()
        
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="Download Status Report (CSV)",
            data=csv,
            file_name="nc_status_report.csv",
            mime="text/csv"
        )
    
    # Row 5: Current Week Detailed View - ALL COLUMNS
    st.markdown("---")
    render_current_week_detail_view(df)


def render_current_week_detail_view(df: pd.DataFrame) -> None:
    """
    Render a detailed table view of current week's NCs showing ALL columns.
    
    Args:
        df: NC DataFrame
    """
    from datetime import datetime, timedelta
    
    st.markdown("## 📅 Current Week - Full Detail View")
    st.markdown("Complete data table with **all columns** from the source data")
    
    if df.empty:
        st.warning("No data available.")
        return
    
    # Ensure Date Submitted is datetime
    df = df.copy()
    df['Date Submitted'] = pd.to_datetime(df['Date Submitted'], errors='coerce')
    
    # Calculate current week boundaries
    today = datetime.now()
    current_week_start = today - timedelta(days=today.weekday())  # Monday of current week
    current_week_start = current_week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Week selection
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        week_options = [
            "Current Week",
            "Last Week", 
            "Last 2 Weeks",
            "Last 4 Weeks",
            "All Data"
        ]
        selected_period = st.selectbox(
            "📆 Select Time Period",
            options=week_options,
            index=0,
            key="week_detail_period"
        )
    
    # Calculate date range based on selection
    if selected_period == "Current Week":
        start_date = current_week_start
        end_date = today
    elif selected_period == "Last Week":
        start_date = current_week_start - timedelta(days=7)
        end_date = current_week_start - timedelta(seconds=1)
    elif selected_period == "Last 2 Weeks":
        start_date = current_week_start - timedelta(days=14)
        end_date = today
    elif selected_period == "Last 4 Weeks":
        start_date = current_week_start - timedelta(days=28)
        end_date = today
    else:  # All Data
        start_date = df['Date Submitted'].min()
        end_date = today
    
    with col2:
        st.markdown(f"**From:** {start_date.strftime('%b %d, %Y') if pd.notna(start_date) else 'N/A'}")
    with col3:
        st.markdown(f"**To:** {end_date.strftime('%b %d, %Y') if pd.notna(end_date) else 'N/A'}")
    
    # Filter data for selected period
    df_valid = df.dropna(subset=['Date Submitted'])
    
    if selected_period != "All Data":
        mask = (df_valid['Date Submitted'] >= start_date) & (df_valid['Date Submitted'] <= end_date)
        filtered_df = df_valid[mask].copy()
    else:
        filtered_df = df_valid.copy()
    
    if filtered_df.empty:
        st.info(f"No NCs found for {selected_period.lower()}.")
        return
    
    # Quick summary
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total Records", len(filtered_df))
    with col2:
        closed_statuses_lower = ['closed', 'complete', 'resolved', 'done']
        open_count = len(filtered_df[~filtered_df['Status'].str.lower().isin(closed_statuses_lower)])
        st.metric("🔴 Open NCs", open_count)
    with col3:
        if 'Cost of Rework' in filtered_df.columns:
            st.metric("💰 Rework Cost", f"${filtered_df['Cost of Rework'].sum():,.2f}")
    with col4:
        if 'Cost Avoided' in filtered_df.columns:
            st.metric("✅ Cost Avoided", f"${filtered_df['Cost Avoided'].sum():,.2f}")
    
    st.markdown("---")
    
    # Show all available columns
    st.markdown("### 📋 Complete Data Table (All Columns)")
    st.markdown(f"**{len(filtered_df.columns)} columns available** | Scroll horizontally to see all data")
    
    # List all columns for reference
    with st.expander("📑 View Column List"):
        col_list = ", ".join(filtered_df.columns.tolist())
        st.markdown(f"**Columns:** {col_list}")
    
    # Prepare the display dataframe with ALL columns
    display_df = filtered_df.copy()
    
    # Format date columns for better readability
    for col in display_df.columns:
        if display_df[col].dtype == 'datetime64[ns]':
            display_df[col] = display_df[col].dt.strftime('%Y-%m-%d')
    
    # Display the FULL dataframe with ALL columns
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=600
    )
    
    # Export options
    st.markdown("---")
    st.markdown("### 📥 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            label="⬇️ Download Full Data (CSV)",
            data=csv_data,
            file_name=f"nc_full_data_{selected_period.lower().replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Show record count in download button area
        st.markdown(f"**{len(filtered_df)} records** with **{len(filtered_df.columns)} columns**")


def render_status_kpi_card(
    status: str, 
    count: int, 
    total: int, 
    color: str
) -> None:
    """
    Render a single status KPI card.
    
    Args:
        status: Status name
        count: Number of NCs with this status
        total: Total number of NCs
        color: Color for the card
    """
    percentage = (count / total) * 100 if total > 0 else 0
    
    st.markdown(f"""
    <div class="metric-card" style="border-left: 4px solid {color};">
        <h2 style="margin: 0; color: {color};">{count}</h2>
        <p style="margin: 0.5rem 0 0 0; font-size: 1rem;">{status}</p>
        <p style="margin: 0; color: #888; font-size: 0.8rem;">{percentage:.1f}% of total</p>
    </div>
    """, unsafe_allow_html=True)
