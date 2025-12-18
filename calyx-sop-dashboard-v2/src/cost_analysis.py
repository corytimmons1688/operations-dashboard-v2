"""
Cost Analysis Module for NC Dashboard
Analyzes Cost of Rework and Cost Avoided with time-based aggregations

Author: Xander @ Calyx Containers
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def render_cost_of_rework(df: pd.DataFrame) -> None:
    """
    Render the Cost of Rework analysis dashboard section.
    
    Displays:
    - Time period filters (daily, weekly, monthly, yearly)
    - Cost trends with line charts
    - Aggregation buckets
    - Summary statistics
    
    Args:
        df: Filtered NC DataFrame
    """
    st.markdown("## 💰 Cost of Rework Analysis")
    st.markdown("Track and analyze rework costs over time")
    
    render_cost_analysis(
        df=df,
        cost_column='Cost of Rework',
        title_prefix='Rework',
        color_scheme='Reds',
        primary_color='#E74C3C'
    )


def render_cost_avoided(df: pd.DataFrame) -> None:
    """
    Render the Cost Avoided analysis dashboard section.
    
    Displays:
    - Time period filters (daily, weekly, monthly, yearly)
    - Cost trends with line charts
    - Aggregation buckets
    - Summary statistics
    - Comparative analysis
    
    Args:
        df: Filtered NC DataFrame
    """
    st.markdown("## ✅ Cost Avoided Analysis")
    st.markdown("Track savings from quality interventions")
    
    render_cost_analysis(
        df=df,
        cost_column='Cost Avoided',
        title_prefix='Avoided',
        color_scheme='Greens',
        primary_color='#27AE60'
    )
    
    # Additional comparative analysis section
    st.markdown("---")
    st.markdown("### 📊 Comparative Analysis: Rework vs Avoided")
    
    render_comparative_analysis(df)


def render_cost_analysis(
    df: pd.DataFrame,
    cost_column: str,
    title_prefix: str,
    color_scheme: str,
    primary_color: str
) -> None:
    """
    Render a generic cost analysis dashboard.
    
    Args:
        df: NC DataFrame
        cost_column: Name of the cost column to analyze
        title_prefix: Prefix for titles (e.g., 'Rework' or 'Avoided')
        color_scheme: Plotly color scheme name
        primary_color: Primary color for highlights
    """
    if df.empty:
        st.warning("No data available for the selected filters.")
        return
    
    # Ensure proper data types
    df = df.copy()
    df['Date Submitted'] = pd.to_datetime(df['Date Submitted'], errors='coerce')
    df[cost_column] = pd.to_numeric(df[cost_column], errors='coerce').fillna(0)
    
    # Filter out invalid dates
    df_valid = df.dropna(subset=['Date Submitted'])
    
    if df_valid.empty:
        st.warning("No valid date data available for cost analysis.")
        return
    
    # Filter controls
    st.markdown("### 📅 Time Period Selection")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        aggregation = st.selectbox(
            "Aggregation Period",
            options=["Daily", "Weekly", "Monthly", "Quarterly", "Yearly"],
            index=2,
            key=f"{cost_column}_agg"
        )
    
    with col2:
        min_date = df_valid['Date Submitted'].min().date()
        max_date = df_valid['Date Submitted'].max().date()
        
        date_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key=f"{cost_column}_date_range"
        )
    
    with col3:
        # Quick date range presets
        preset = st.selectbox(
            "Quick Select",
            options=["Custom", "Last 30 Days", "Last 90 Days", "Last 6 Months", 
                    "Last Year", "Year to Date", "All Time"],
            key=f"{cost_column}_preset"
        )
        
        if preset != "Custom":
            today = datetime.now().date()
            if preset == "Last 30 Days":
                date_range = (today - timedelta(days=30), today)
            elif preset == "Last 90 Days":
                date_range = (today - timedelta(days=90), today)
            elif preset == "Last 6 Months":
                date_range = (today - timedelta(days=180), today)
            elif preset == "Last Year":
                date_range = (today - timedelta(days=365), today)
            elif preset == "Year to Date":
                date_range = (datetime(today.year, 1, 1).date(), today)
            elif preset == "All Time":
                date_range = (min_date, max_date)
    
    # Apply date filter
    if len(date_range) == 2:
        mask = (
            (df_valid['Date Submitted'].dt.date >= date_range[0]) &
            (df_valid['Date Submitted'].dt.date <= date_range[1])
        )
        df_filtered = df_valid[mask]
    else:
        df_filtered = df_valid
    
    if df_filtered.empty:
        st.warning("No data found for the selected date range.")
        return
    
    st.markdown("---")
    
    # Row 1: Summary Metrics
    st.markdown(f"### 📊 {title_prefix} Cost Summary")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_cost = df_filtered[cost_column].sum()
    avg_cost = df_filtered[cost_column].mean()
    median_cost = df_filtered[cost_column].median()
    max_cost = df_filtered[cost_column].max()
    nc_with_cost = (df_filtered[cost_column] > 0).sum()
    
    with col1:
        st.metric(
            f"Total {title_prefix} Cost",
            f"${total_cost:,.2f}"
        )
    
    with col2:
        st.metric(
            "Average Cost",
            f"${avg_cost:,.2f}"
        )
    
    with col3:
        st.metric(
            "Median Cost",
            f"${median_cost:,.2f}"
        )
    
    with col4:
        st.metric(
            "Max Single Cost",
            f"${max_cost:,.2f}"
        )
    
    with col5:
        st.metric(
            "NCs with Cost",
            f"{nc_with_cost:,}"
        )
    
    st.markdown("---")
    
    # Row 2: Time Series Trend
    st.markdown(f"### 📈 {title_prefix} Cost Trend")
    
    # Aggregate data based on selected period
    agg_data = aggregate_by_period(df_filtered, cost_column, aggregation)
    
    if not agg_data.empty:
        # Line chart with trend
        fig_trend = go.Figure()
        
        # Add bar chart for cost
        fig_trend.add_trace(go.Bar(
            x=agg_data['Period'],
            y=agg_data['Total'],
            name='Total Cost',
            marker_color=primary_color,
            opacity=0.7
        ))
        
        # Add line for moving average
        if len(agg_data) >= 3:
            agg_data['MA'] = agg_data['Total'].rolling(window=3, min_periods=1).mean()
            fig_trend.add_trace(go.Scatter(
                x=agg_data['Period'],
                y=agg_data['MA'],
                name='3-Period Moving Avg',
                line=dict(color='#333', width=2, dash='dash')
            ))
        
        fig_trend.update_layout(
            height=400,
            xaxis_title="Period",
            yaxis_title="Cost ($)",
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        
        st.plotly_chart(fig_trend, use_container_width=True)
    
    # Row 3: Distribution Analysis
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### 📊 Cost Distribution")
        
        # Histogram of costs
        fig_hist = px.histogram(
            df_filtered[df_filtered[cost_column] > 0],
            x=cost_column,
            nbins=30,
            title=f"{title_prefix} Cost Distribution",
            color_discrete_sequence=[primary_color]
        )
        fig_hist.update_layout(
            height=350,
            xaxis_title="Cost ($)",
            yaxis_title="Frequency"
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        st.markdown(f"### 🏢 Top Contributors")
        
        # Top customers by cost
        top_customers = df_filtered.groupby('Customer')[cost_column].sum().nlargest(10)
        
        fig_top = px.bar(
            x=top_customers.values,
            y=top_customers.index,
            orientation='h',
            title=f"Top 10 Customers by {title_prefix} Cost",
            color=top_customers.values,
            color_continuous_scale=color_scheme
        )
        fig_top.update_layout(
            height=350,
            xaxis_title="Total Cost ($)",
            yaxis_title="",
            showlegend=False,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_top, use_container_width=True)
    
    # Row 4: Breakdown by Category
    st.markdown("---")
    st.markdown(f"### 📋 {title_prefix} Cost by Category")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # By Issue Type
        by_issue = df_filtered.groupby('Issue Type')[cost_column].sum().sort_values(ascending=False)
        
        fig_issue = px.pie(
            values=by_issue.values,
            names=by_issue.index,
            title="By Issue Type",
            hole=0.4
        )
        fig_issue.update_layout(height=350)
        st.plotly_chart(fig_issue, use_container_width=True)
    
    with col2:
        # By Priority
        by_priority = df_filtered.groupby('Priority')[cost_column].sum()
        priority_colors = {'High': '#FF4444', 'Medium': '#FFAA00', 'Low': '#44AA44'}
        
        fig_priority = px.bar(
            x=by_priority.index,
            y=by_priority.values,
            title="By Priority",
            color=by_priority.index,
            color_discrete_map=priority_colors
        )
        fig_priority.update_layout(
            height=350,
            showlegend=False,
            xaxis_title="Priority",
            yaxis_title="Total Cost ($)"
        )
        st.plotly_chart(fig_priority, use_container_width=True)
    
    # Export option
    st.markdown("---")
    with st.expander(f"📥 Export {title_prefix} Cost Data"):
        export_df = agg_data.copy()
        export_df['Total'] = export_df['Total'].apply(lambda x: f"${x:,.2f}")
        
        csv = export_df.to_csv(index=False)
        st.download_button(
            label=f"Download {title_prefix} Cost Report (CSV)",
            data=csv,
            file_name=f"nc_{title_prefix.lower()}_cost_report.csv",
            mime="text/csv"
        )


def render_comparative_analysis(df: pd.DataFrame) -> None:
    """
    Render comparative analysis between Cost of Rework and Cost Avoided.
    
    Args:
        df: NC DataFrame
    """
    if df.empty:
        return
    
    df = df.copy()
    df['Date Submitted'] = pd.to_datetime(df['Date Submitted'], errors='coerce')
    df['Cost of Rework'] = pd.to_numeric(df['Cost of Rework'], errors='coerce').fillna(0)
    df['Cost Avoided'] = pd.to_numeric(df['Cost Avoided'], errors='coerce').fillna(0)
    
    df_valid = df.dropna(subset=['Date Submitted'])
    
    if df_valid.empty:
        return
    
    col1, col2, col3 = st.columns(3)
    
    total_rework = df_valid['Cost of Rework'].sum()
    total_avoided = df_valid['Cost Avoided'].sum()
    net_impact = total_avoided - total_rework
    
    with col1:
        st.metric(
            "Total Cost of Rework",
            f"${total_rework:,.2f}",
            delta=None
        )
    
    with col2:
        st.metric(
            "Total Cost Avoided",
            f"${total_avoided:,.2f}",
            delta=None
        )
    
    with col3:
        st.metric(
            "Net Impact",
            f"${net_impact:,.2f}",
            delta=f"{'Positive' if net_impact > 0 else 'Negative'}",
            delta_color="normal" if net_impact > 0 else "inverse"
        )
    
    # Monthly comparison chart
    monthly_rework = df_valid.set_index('Date Submitted').resample('ME')['Cost of Rework'].sum()
    monthly_avoided = df_valid.set_index('Date Submitted').resample('ME')['Cost Avoided'].sum()
    
    comparison_df = pd.DataFrame({
        'Period': monthly_rework.index.strftime('%Y-%m'),
        'Cost of Rework': monthly_rework.values,
        'Cost Avoided': monthly_avoided.values
    })
    
    fig_compare = go.Figure()
    
    fig_compare.add_trace(go.Bar(
        x=comparison_df['Period'],
        y=comparison_df['Cost of Rework'],
        name='Cost of Rework',
        marker_color='#E74C3C'
    ))
    
    fig_compare.add_trace(go.Bar(
        x=comparison_df['Period'],
        y=comparison_df['Cost Avoided'],
        name='Cost Avoided',
        marker_color='#27AE60'
    ))
    
    fig_compare.update_layout(
        title="Monthly Cost Comparison",
        height=400,
        barmode='group',
        xaxis_title="Month",
        yaxis_title="Cost ($)",
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    
    st.plotly_chart(fig_compare, use_container_width=True)
    
    # ROI indicator
    if total_rework > 0:
        roi = ((total_avoided - total_rework) / total_rework) * 100
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 10px;
            padding: 1.5rem;
            text-align: center;
            color: white;
        ">
            <h3 style="margin: 0;">Quality ROI</h3>
            <h1 style="margin: 0.5rem 0; font-size: 3rem;">{roi:.1f}%</h1>
            <p style="margin: 0; opacity: 0.8;">Return on quality investment</p>
        </div>
        """, unsafe_allow_html=True)


def aggregate_by_period(
    df: pd.DataFrame, 
    cost_column: str, 
    period: str
) -> pd.DataFrame:
    """
    Aggregate cost data by the specified time period.
    
    Args:
        df: NC DataFrame
        cost_column: Name of cost column
        period: Aggregation period (Daily, Weekly, Monthly, Quarterly, Yearly)
        
    Returns:
        Aggregated DataFrame with Period and Total columns
    """
    df = df.copy()
    df['Date Submitted'] = pd.to_datetime(df['Date Submitted'])
    
    # Set the date as index for resampling
    df_indexed = df.set_index('Date Submitted')
    
    # Define resampling frequency
    freq_map = {
        'Daily': 'D',
        'Weekly': 'W',
        'Monthly': 'ME',
        'Quarterly': 'QE',
        'Yearly': 'YE'
    }
    
    freq = freq_map.get(period, 'ME')
    
    # Resample and aggregate
    aggregated = df_indexed.resample(freq)[cost_column].agg(['sum', 'count', 'mean'])
    aggregated = aggregated.reset_index()
    aggregated.columns = ['Period', 'Total', 'Count', 'Average']
    
    # Format period based on frequency
    if period == 'Daily':
        aggregated['Period'] = aggregated['Period'].dt.strftime('%Y-%m-%d')
    elif period == 'Weekly':
        aggregated['Period'] = aggregated['Period'].dt.strftime('%Y-W%U')
    elif period == 'Monthly':
        aggregated['Period'] = aggregated['Period'].dt.strftime('%Y-%m')
    elif period == 'Quarterly':
        aggregated['Period'] = aggregated['Period'].dt.to_period('Q').astype(str)
    elif period == 'Yearly':
        aggregated['Period'] = aggregated['Period'].dt.strftime('%Y')
    
    return aggregated
