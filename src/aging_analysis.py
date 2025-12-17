"""
Aging Analysis Module for NC Dashboard
Calculates and visualizes NC aging based on Date Submitted

Author: Xander @ Calyx Containers
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Tuple, List
import logging

logger = logging.getLogger(__name__)

# Aging bucket definitions
AGING_BUCKETS = [
    ("0-30 days", 0, 30, "#4CAF50"),      # Green
    ("31-60 days", 31, 60, "#FFC107"),    # Yellow
    ("61-90 days", 61, 90, "#FF9800"),    # Orange
    ("90+ days", 91, float('inf'), "#F44336")  # Red
]


def render_aging_dashboard(df: pd.DataFrame) -> None:
    """
    Render the Aging Analysis dashboard section.
    
    Displays:
    - Aging bucket distribution
    - Average age metrics
    - Aging trend over time
    - Detailed aging breakdown table
    
    Args:
        df: Filtered NC DataFrame
    """
    st.markdown("## ⏱️ Aging Analysis Dashboard")
    st.markdown("Track how long non-conformances have been open")
    
    if df.empty:
        st.warning("No data available for the selected filters.")
        return
    
    # Ensure Date Submitted is datetime
    df = df.copy()
    df['Date Submitted'] = pd.to_datetime(df['Date Submitted'], errors='coerce')
    
    # Filter out rows with invalid dates
    df_valid = df.dropna(subset=['Date Submitted'])
    
    if df_valid.empty:
        st.warning("No valid date data available for aging analysis.")
        return
    
    # Calculate age in days
    today = datetime.now()
    df_valid['Age_Days'] = (today - df_valid['Date Submitted']).dt.days
    
    # Filter controls
    st.markdown("### 📅 Date Range Filter")
    col1, col2 = st.columns(2)
    
    with col1:
        min_date = df_valid['Date Submitted'].min().date()
        max_date = df_valid['Date Submitted'].max().date()
        
        start_date = st.date_input(
            "From Date",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            key="aging_start_date"
        )
    
    with col2:
        end_date = st.date_input(
            "To Date",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            key="aging_end_date"
        )
    
    # Apply date filter
    mask = (
        (df_valid['Date Submitted'].dt.date >= start_date) &
        (df_valid['Date Submitted'].dt.date <= end_date)
    )
    df_filtered = df_valid[mask]
    
    if df_filtered.empty:
        st.warning("No data found for the selected date range.")
        return
    
    st.markdown("---")
    
    # Row 1: Summary Metrics
    st.markdown("### 📊 Aging Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    avg_age = df_filtered['Age_Days'].mean()
    median_age = df_filtered['Age_Days'].median()
    max_age = df_filtered['Age_Days'].max()
    
    # Filter for open NCs only
    # Filter for open NCs only (exclude closed statuses)
    closed_statuses = ['closed', 'complete', 'resolved', 'done']
    open_ncs = df_filtered[~df_filtered['Status'].str.lower().isin(closed_statuses)]
    open_avg_age = open_ncs['Age_Days'].mean() if not open_ncs.empty else 0
    
    with col1:
        st.metric(
            "Average Age (All)",
            f"{avg_age:.1f} days",
            delta=None
        )
    
    with col2:
        st.metric(
            "Average Age (Open)",
            f"{open_avg_age:.1f} days",
            delta=f"{open_avg_age - avg_age:.1f}" if open_avg_age > avg_age else None,
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            "Median Age",
            f"{median_age:.1f} days"
        )
    
    with col4:
        st.metric(
            "Oldest NC",
            f"{max_age:.0f} days"
        )
    
    st.markdown("---")
    
    # Row 2: Aging Bucket Distribution
    st.markdown("### 📈 Aging Bucket Distribution")
    
    # Categorize into buckets
    df_filtered['Aging_Bucket'] = df_filtered['Age_Days'].apply(categorize_age)
    bucket_counts = df_filtered['Aging_Bucket'].value_counts()
    
    # Ensure all buckets are represented
    bucket_order = ["0-30 days", "31-60 days", "61-90 days", "90+ days"]
    bucket_colors = ["#4CAF50", "#FFC107", "#FF9800", "#F44336"]
    
    bucket_data = []
    for bucket, color in zip(bucket_order, bucket_colors):
        count = bucket_counts.get(bucket, 0)
        bucket_data.append({
            'Bucket': bucket,
            'Count': count,
            'Color': color,
            'Percentage': (count / len(df_filtered)) * 100 if len(df_filtered) > 0 else 0
        })
    
    bucket_df = pd.DataFrame(bucket_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Horizontal bar chart
        fig_bar = px.bar(
            bucket_df,
            x='Count',
            y='Bucket',
            orientation='h',
            color='Bucket',
            color_discrete_map={b['Bucket']: b['Color'] for b in bucket_data},
            title="NCs by Aging Bucket"
        )
        fig_bar.update_layout(
            showlegend=False,
            height=350,
            yaxis={'categoryorder': 'array', 'categoryarray': bucket_order[::-1]},
            xaxis_title="Number of NCs",
            yaxis_title=""
        )
        fig_bar.update_traces(
            texttemplate='%{x}',
            textposition='outside'
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        # Donut chart with percentages
        fig_pie = go.Figure(data=[go.Pie(
            labels=bucket_df['Bucket'],
            values=bucket_df['Count'],
            hole=0.5,
            marker_colors=bucket_df['Color'],
            textinfo='percent+label',
            textposition='outside'
        )])
        fig_pie.update_layout(
            title="Aging Distribution",
            height=350,
            showlegend=False,
            annotations=[{
                'text': f"{len(df_filtered)}<br>Total",
                'x': 0.5, 'y': 0.5,
                'font_size': 16,
                'showarrow': False
            }]
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Bucket summary cards
    cols = st.columns(4)
    for idx, bucket in enumerate(bucket_data):
        with cols[idx]:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {bucket['Color']}22, {bucket['Color']}44);
                border-radius: 8px;
                padding: 1rem;
                text-align: center;
                border-left: 4px solid {bucket['Color']};
            ">
                <h3 style="margin: 0; color: #333;">{bucket['Count']}</h3>
                <p style="margin: 0; color: #666;">{bucket['Bucket']}</p>
                <p style="margin: 0; color: {bucket['Color']}; font-weight: bold;">{bucket['Percentage']:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Row 3: Aging by Status
    st.markdown("### 📊 Aging by Status")
    
    # Box plot of age by status
    fig_box = px.box(
        df_filtered,
        x='Status',
        y='Age_Days',
        color='Status',
        title="Age Distribution by Status"
    )
    fig_box.update_layout(
        height=400,
        showlegend=False,
        xaxis_title="Status",
        yaxis_title="Age (Days)"
    )
    st.plotly_chart(fig_box, use_container_width=True)
    
    st.markdown("---")
    
    # Row 4: Aging Trend Over Time
    st.markdown("### 📈 Aging Trend Over Time")
    
    # Group by submission date and calculate average age at time of snapshot
    daily_submitted = df_filtered.groupby(
        df_filtered['Date Submitted'].dt.date
    ).size().reset_index(name='Count')
    daily_submitted.columns = ['Date', 'Count']
    
    # Calculate cumulative aging (NCs submitted over time)
    fig_trend = px.area(
        daily_submitted,
        x='Date',
        y='Count',
        title="NCs Submitted Over Time"
    )
    fig_trend.update_layout(
        height=350,
        xaxis_title="Date Submitted",
        yaxis_title="Number of NCs"
    )
    st.plotly_chart(fig_trend, use_container_width=True)
    
    st.markdown("---")
    
    # Row 5: Critical Aging Table
    st.markdown("### 🚨 Critical Aging NCs (90+ Days)")
    
    critical_ncs = df_filtered[df_filtered['Age_Days'] >= 90].copy()
    
    if not critical_ncs.empty:
        critical_ncs = critical_ncs.sort_values('Age_Days', ascending=False)
        
        display_cols = ['NC Number', 'Customer', 'Issue Type', 'Status', 
                       'Priority', 'Date Submitted', 'Age_Days', 'Cost of Rework']
        
        critical_display = critical_ncs[display_cols].head(20).copy()
        critical_display['Date Submitted'] = critical_display['Date Submitted'].dt.strftime('%Y-%m-%d')
        critical_display['Cost of Rework'] = critical_display['Cost of Rework'].apply(lambda x: f"${x:,.2f}")
        critical_display.columns = ['NC #', 'Customer', 'Issue Type', 'Status', 
                                   'Priority', 'Submitted', 'Age (Days)', 'Rework Cost']
        
        st.dataframe(
            critical_display,
            use_container_width=True,
            hide_index=True
        )
        
        st.info(f"Showing top 20 of {len(critical_ncs)} critical aging NCs")
    else:
        st.success("✅ No NCs over 90 days old!")
    
    # Export option
    st.markdown("---")
    with st.expander("📥 Export Aging Data"):
        export_df = df_filtered[['NC Number', 'Customer', 'Issue Type', 'Status',
                                'Date Submitted', 'Age_Days', 'Aging_Bucket']].copy()
        export_df['Date Submitted'] = export_df['Date Submitted'].dt.strftime('%Y-%m-%d')
        
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="Download Aging Report (CSV)",
            data=csv,
            file_name="nc_aging_report.csv",
            mime="text/csv"
        )


def categorize_age(days: int) -> str:
    """
    Categorize age in days into aging buckets.
    
    Args:
        days: Number of days since submission
        
    Returns:
        Aging bucket category string
    """
    if pd.isna(days) or days < 0:
        return "Unknown"
    elif days <= 30:
        return "0-30 days"
    elif days <= 60:
        return "31-60 days"
    elif days <= 90:
        return "61-90 days"
    else:
        return "90+ days"


def calculate_aging_metrics(df: pd.DataFrame) -> dict:
    """
    Calculate comprehensive aging metrics.
    
    Args:
        df: NC DataFrame with Age_Days column
        
    Returns:
        Dictionary with aging metrics
    """
    if df.empty or 'Age_Days' not in df.columns:
        return {}
    
    return {
        'mean': df['Age_Days'].mean(),
        'median': df['Age_Days'].median(),
        'std': df['Age_Days'].std(),
        'min': df['Age_Days'].min(),
        'max': df['Age_Days'].max(),
        'count_0_30': len(df[df['Age_Days'] <= 30]),
        'count_31_60': len(df[(df['Age_Days'] > 30) & (df['Age_Days'] <= 60)]),
        'count_61_90': len(df[(df['Age_Days'] > 60) & (df['Age_Days'] <= 90)]),
        'count_90_plus': len(df[df['Age_Days'] > 90])
    }
