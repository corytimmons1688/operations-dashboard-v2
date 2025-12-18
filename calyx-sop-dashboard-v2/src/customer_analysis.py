"""
Customer Analysis Module for NC Dashboard
Analyzes NC distribution by customer with drill-down capabilities

Author: Xander @ Calyx Containers
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


def render_customer_analysis(df: pd.DataFrame) -> None:
    """
    Render the Customer Analysis dashboard section.
    
    Displays:
    - NC count by customer (bar chart, descending order)
    - Interactive drill-down capability
    - Customer summary statistics
    - Detailed customer breakdown table
    
    Args:
        df: Filtered NC DataFrame
    """
    st.markdown("## 👥 Customer Analysis")
    st.markdown("Analyze non-conformance distribution by customer")
    
    if df.empty:
        st.warning("No data available for the selected filters.")
        return
    
    # Filter controls
    st.markdown("### 🎯 Analysis Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Number of customers to display
        top_n = st.slider(
            "Number of Customers to Show",
            min_value=5,
            max_value=50,
            value=15,
            step=5,
            key="customer_top_n"
        )
    
    with col2:
        # Metric to sort by
        sort_metric = st.selectbox(
            "Sort By",
            options=["NC Count", "Total Rework Cost", "Total Cost Avoided", "Total Quantity Affected"],
            key="customer_sort_metric"
        )
    
    with col3:
        # Include/exclude option
        exclude_empty = st.checkbox(
            "Exclude Unknown Customers",
            value=True,
            key="customer_exclude_empty"
        )
    
    # Prepare data
    df_analysis = df.copy()
    
    if exclude_empty:
        df_analysis = df_analysis[
            (df_analysis['Customer'].notna()) & 
            (df_analysis['Customer'] != '') &
            (df_analysis['Customer'] != 'nan')
        ]
    
    if df_analysis.empty:
        st.warning("No customer data available after filtering.")
        return
    
    st.markdown("---")
    
    # Row 1: Summary Metrics
    st.markdown("### 📊 Customer Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    unique_customers = df_analysis['Customer'].nunique()
    total_ncs = len(df_analysis)
    avg_nc_per_customer = total_ncs / unique_customers if unique_customers > 0 else 0
    
    # Find top customer
    customer_counts = df_analysis['Customer'].value_counts()
    top_customer = customer_counts.index[0] if len(customer_counts) > 0 else "N/A"
    top_customer_count = customer_counts.iloc[0] if len(customer_counts) > 0 else 0
    
    with col1:
        st.metric("Unique Customers", f"{unique_customers:,}")
    
    with col2:
        st.metric("Total NCs", f"{total_ncs:,}")
    
    with col3:
        st.metric("Avg NCs per Customer", f"{avg_nc_per_customer:.1f}")
    
    with col4:
        st.metric("Top Customer", f"{top_customer[:20]}...", delta=f"{top_customer_count} NCs")
    
    st.markdown("---")
    
    # Row 2: Main Bar Chart
    st.markdown("### 📊 NC Count by Customer")
    
    # Aggregate by selected metric
    if sort_metric == "NC Count":
        customer_data = df_analysis['Customer'].value_counts().head(top_n)
        y_label = "Number of NCs"
    elif sort_metric == "Total Rework Cost":
        customer_data = df_analysis.groupby('Customer')['Cost of Rework'].sum().nlargest(top_n)
        y_label = "Total Rework Cost ($)"
    elif sort_metric == "Total Cost Avoided":
        customer_data = df_analysis.groupby('Customer')['Cost Avoided'].sum().nlargest(top_n)
        y_label = "Total Cost Avoided ($)"
    else:  # Total Quantity Affected
        customer_data = df_analysis.groupby('Customer')['Total Quantity Affected'].sum().nlargest(top_n)
        y_label = "Total Quantity Affected"
    
    # Create bar chart (left to right, descending)
    fig_bar = px.bar(
        x=customer_data.index,
        y=customer_data.values,
        title=f"Top {top_n} Customers by {sort_metric}",
        color=customer_data.values,
        color_continuous_scale='Blues'
    )
    
    fig_bar.update_layout(
        height=500,
        xaxis_title="Customer",
        yaxis_title=y_label,
        xaxis_tickangle=-45,
        showlegend=False,
        coloraxis_showscale=False
    )
    
    # Add value labels on bars
    fig_bar.update_traces(
        texttemplate='%{y:,.0f}',
        textposition='outside'
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("---")
    
    # Row 3: Drill-down Section
    st.markdown("### 🔍 Customer Drill-Down")
    
    # Customer selector for drill-down
    all_customers = sorted(df_analysis['Customer'].unique())
    selected_customer = st.selectbox(
        "Select Customer for Detailed Analysis",
        options=["-- Select a Customer --"] + list(all_customers),
        key="customer_drilldown"
    )
    
    if selected_customer != "-- Select a Customer --":
        render_customer_drilldown(df_analysis, selected_customer)
    
    st.markdown("---")
    
    # Row 4: Customer Comparison Table
    st.markdown("### 📋 Customer Comparison Table")
    
    # Build comprehensive customer summary
    customer_summary = df_analysis.groupby('Customer').agg({
        'NC Number': 'count',
        'Cost of Rework': 'sum',
        'Cost Avoided': 'sum',
        'Total Quantity Affected': 'sum'
    }).reset_index()
    
    customer_summary.columns = ['Customer', 'NC Count', 'Total Rework Cost', 
                                'Total Cost Avoided', 'Total Qty Affected']
    
    # Sort by selected metric
    sort_col_map = {
        "NC Count": "NC Count",
        "Total Rework Cost": "Total Rework Cost",
        "Total Cost Avoided": "Total Cost Avoided",
        "Total Quantity Affected": "Total Qty Affected"
    }
    customer_summary = customer_summary.sort_values(
        sort_col_map[sort_metric], 
        ascending=False
    ).head(top_n)
    
    # Format currency columns
    customer_summary['Total Rework Cost'] = customer_summary['Total Rework Cost'].apply(
        lambda x: f"${x:,.2f}"
    )
    customer_summary['Total Cost Avoided'] = customer_summary['Total Cost Avoided'].apply(
        lambda x: f"${x:,.2f}"
    )
    customer_summary['Total Qty Affected'] = customer_summary['Total Qty Affected'].apply(
        lambda x: f"{x:,.0f}"
    )
    
    st.dataframe(
        customer_summary,
        use_container_width=True,
        hide_index=True
    )
    
    # Row 5: Customer Distribution Analysis
    st.markdown("---")
    st.markdown("### 📈 Distribution Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pareto-style cumulative distribution
        customer_counts_sorted = df_analysis['Customer'].value_counts()
        cumulative_pct = (customer_counts_sorted.cumsum() / customer_counts_sorted.sum() * 100)
        
        fig_pareto = go.Figure()
        
        fig_pareto.add_trace(go.Bar(
            x=list(range(1, len(customer_counts_sorted) + 1)),
            y=customer_counts_sorted.values,
            name='NC Count',
            marker_color='#3498db'
        ))
        
        fig_pareto.add_trace(go.Scatter(
            x=list(range(1, len(cumulative_pct) + 1)),
            y=cumulative_pct.values,
            name='Cumulative %',
            yaxis='y2',
            line=dict(color='#e74c3c', width=2)
        ))
        
        fig_pareto.update_layout(
            title="Customer Concentration Analysis",
            height=400,
            xaxis_title="Customer Rank",
            yaxis_title="NC Count",
            yaxis2=dict(
                title="Cumulative %",
                overlaying='y',
                side='right',
                range=[0, 105]
            ),
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        
        # Add 80% threshold line
        fig_pareto.add_hline(
            y=80, 
            line_dash="dash", 
            line_color="gray",
            annotation_text="80%",
            yref='y2'
        )
        
        st.plotly_chart(fig_pareto, use_container_width=True)
    
    with col2:
        # Customer NC frequency histogram
        nc_per_customer = df_analysis['Customer'].value_counts()
        
        fig_hist = px.histogram(
            nc_per_customer,
            nbins=20,
            title="Distribution of NCs per Customer",
            color_discrete_sequence=['#9b59b6']
        )
        fig_hist.update_layout(
            height=400,
            xaxis_title="Number of NCs",
            yaxis_title="Number of Customers"
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    # Export option
    st.markdown("---")
    with st.expander("📥 Export Customer Data"):
        export_df = df_analysis.groupby('Customer').agg({
            'NC Number': 'count',
            'Cost of Rework': 'sum',
            'Cost Avoided': 'sum',
            'Total Quantity Affected': 'sum',
            'Issue Type': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'N/A'
        }).reset_index()
        export_df.columns = ['Customer', 'NC Count', 'Total Rework Cost', 
                            'Total Cost Avoided', 'Total Qty Affected', 'Most Common Issue']
        
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="Download Customer Report (CSV)",
            data=csv,
            file_name="nc_customer_report.csv",
            mime="text/csv"
        )


def render_customer_drilldown(df: pd.DataFrame, customer: str) -> None:
    """
    Render detailed drill-down view for a specific customer.
    
    Args:
        df: NC DataFrame
        customer: Selected customer name
    """
    customer_df = df[df['Customer'] == customer]
    
    if customer_df.empty:
        st.warning(f"No data found for customer: {customer}")
        return
    
    st.markdown(f"#### 📋 Details for: **{customer}**")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total NCs", len(customer_df))
    
    with col2:
        total_rework = customer_df['Cost of Rework'].sum()
        st.metric("Total Rework Cost", f"${total_rework:,.2f}")
    
    with col3:
        total_avoided = customer_df['Cost Avoided'].sum()
        st.metric("Total Cost Avoided", f"${total_avoided:,.2f}")
    
    with col4:
        closed_statuses = ['closed', 'complete', 'resolved', 'done']
        open_count = customer_df[~customer_df['Status'].str.lower().isin(closed_statuses)].shape[0]
        st.metric("Open NCs", open_count)
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        # Issue type breakdown
        issue_counts = customer_df['Issue Type'].value_counts()
        fig_issues = px.pie(
            values=issue_counts.values,
            names=issue_counts.index,
            title="Issues by Type",
            hole=0.3
        )
        fig_issues.update_layout(height=300)
        st.plotly_chart(fig_issues, use_container_width=True)
    
    with col2:
        # Status breakdown
        status_counts = customer_df['Status'].value_counts()
        fig_status = px.bar(
            x=status_counts.index,
            y=status_counts.values,
            title="NCs by Status",
            color=status_counts.index
        )
        fig_status.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig_status, use_container_width=True)
    
    # Recent NCs table
    st.markdown("##### Recent NCs")
    recent_ncs = customer_df.nlargest(10, 'Date Submitted')[
        ['NC Number', 'Issue Type', 'Status', 'Priority', 'Date Submitted', 'Cost of Rework']
    ].copy()
    
    recent_ncs['Date Submitted'] = pd.to_datetime(recent_ncs['Date Submitted']).dt.strftime('%Y-%m-%d')
    recent_ncs['Cost of Rework'] = recent_ncs['Cost of Rework'].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(recent_ncs, use_container_width=True, hide_index=True)
