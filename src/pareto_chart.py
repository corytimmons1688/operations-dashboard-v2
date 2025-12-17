"""
Pareto Chart Module for NC Dashboard
Creates Pareto analysis for Issue Types with cumulative percentage

Author: Xander @ Calyx Containers
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def render_issue_type_pareto(df: pd.DataFrame, default_ext_int: str = "All") -> None:
    """
    Render the Issue Type Pareto analysis dashboard section.
    
    Displays:
    - Pareto chart with bars and cumulative percentage line
    - Date range filter
    - External/Internal filter
    - Issue type breakdown statistics
    
    Args:
        df: NC DataFrame (raw, unfiltered for this tab's own filters)
        default_ext_int: Default External/Internal filter value from sidebar
    """
    st.markdown("## 📊 Issue Type Pareto Analysis")
    st.markdown("Identify the vital few issue types causing the most non-conformances")
    
    if df.empty:
        st.warning("No data available.")
        return
    
    # Ensure proper data types
    df = df.copy()
    df['Date Submitted'] = pd.to_datetime(df['Date Submitted'], errors='coerce')
    
    # Filter controls specific to this tab
    st.markdown("### 🎯 Pareto Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Date range filter
        df_valid = df.dropna(subset=['Date Submitted'])
        
        if not df_valid.empty:
            min_date = df_valid['Date Submitted'].min().date()
            max_date = df_valid['Date Submitted'].max().date()
            
            date_range = st.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="pareto_date_range"
            )
        else:
            date_range = None
            st.warning("No valid date data available")
    
    with col2:
        # External/Internal filter
        ext_int_options = ["All", "External", "Internal"]
        
        # Set default based on sidebar selection
        default_index = ext_int_options.index(default_ext_int) if default_ext_int in ext_int_options else 0
        
        ext_int_filter = st.selectbox(
            "External or Internal",
            options=ext_int_options,
            index=default_index,
            key="pareto_ext_int"
        )
    
    with col3:
        # Minimum count threshold
        min_count = st.number_input(
            "Minimum NC Count",
            min_value=0,
            max_value=100,
            value=0,
            step=1,
            help="Only show issue types with at least this many NCs",
            key="pareto_min_count"
        )
    
    # Apply filters
    df_filtered = df.copy()
    
    # Apply date filter
    if date_range and len(date_range) == 2:
        df_filtered = df_filtered.dropna(subset=['Date Submitted'])
        mask = (
            (df_filtered['Date Submitted'].dt.date >= date_range[0]) &
            (df_filtered['Date Submitted'].dt.date <= date_range[1])
        )
        df_filtered = df_filtered[mask]
    
    # Apply External/Internal filter
    if ext_int_filter != "All":
        df_filtered = df_filtered[df_filtered['External Or Internal'] == ext_int_filter]
    
    if df_filtered.empty:
        st.warning("No data found for the selected filters.")
        return
    
    # Filter out empty/unknown issue types
    df_filtered = df_filtered[
        (df_filtered['Issue Type'].notna()) & 
        (df_filtered['Issue Type'] != '') &
        (df_filtered['Issue Type'] != 'nan')
    ]
    
    if df_filtered.empty:
        st.warning("No issue type data available after filtering.")
        return
    
    st.markdown("---")
    
    # Calculate Pareto data
    pareto_data = calculate_pareto_data(df_filtered, min_count)
    
    if pareto_data.empty:
        st.warning(f"No issue types found with at least {min_count} occurrences.")
        return
    
    # Row 1: Summary Metrics
    st.markdown("### 📈 Pareto Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    unique_issues = len(pareto_data)
    total_ncs = pareto_data['Count'].sum()
    
    # Find 80% threshold
    issues_for_80 = len(pareto_data[pareto_data['Cumulative_Pct'] <= 80]) + 1
    pct_issues_for_80 = (issues_for_80 / unique_issues) * 100 if unique_issues > 0 else 0
    
    with col1:
        st.metric("Unique Issue Types", f"{unique_issues:,}")
    
    with col2:
        st.metric("Total NCs", f"{total_ncs:,}")
    
    with col3:
        st.metric(
            "Issues for 80% of NCs",
            f"{issues_for_80}",
            delta=f"{pct_issues_for_80:.1f}% of types"
        )
    
    with col4:
        top_issue = pareto_data.iloc[0]['Issue Type'] if len(pareto_data) > 0 else "N/A"
        top_count = pareto_data.iloc[0]['Count'] if len(pareto_data) > 0 else 0
        st.metric("Top Issue Type", f"{top_issue[:25]}...", delta=f"{top_count} NCs")
    
    st.markdown("---")
    
    # Row 2: Pareto Chart
    st.markdown("### 📊 Pareto Chart")
    
    fig = create_pareto_chart(pareto_data)
    st.plotly_chart(fig, use_container_width=True)
    
    # 80/20 Rule Analysis
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea22, #764ba222);
        border-radius: 10px;
        padding: 1rem;
        border-left: 4px solid #667eea;
    ">
        <h4 style="margin: 0 0 0.5rem 0;">📌 80/20 Principle Analysis</h4>
        <p style="margin: 0;">
            <strong>{}</strong> issue types ({:.1f}%) account for approximately 80% of all non-conformances.
            Focus improvement efforts on these vital few categories for maximum impact.
        </p>
    </div>
    """.format(issues_for_80, pct_issues_for_80), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Row 3: Detailed Breakdown
    st.markdown("### 📋 Issue Type Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart of top issues
        top_5 = pareto_data.head(5)
        other_count = pareto_data.iloc[5:]['Count'].sum() if len(pareto_data) > 5 else 0
        
        if other_count > 0:
            pie_data = pd.concat([
                top_5[['Issue Type', 'Count']],
                pd.DataFrame({'Issue Type': ['Other'], 'Count': [other_count]})
            ])
        else:
            pie_data = top_5[['Issue Type', 'Count']]
        
        fig_pie = px.pie(
            pie_data,
            values='Count',
            names='Issue Type',
            title="Top 5 Issue Types + Other",
            hole=0.4
        )
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Issue type by External/Internal
        if ext_int_filter == "All":
            ext_int_breakdown = df_filtered.groupby(['Issue Type', 'External Or Internal']).size().unstack(fill_value=0)
            
            if not ext_int_breakdown.empty:
                ext_int_breakdown = ext_int_breakdown.reindex(pareto_data['Issue Type'].head(10))
                
                fig_stacked = go.Figure()
                
                for col in ext_int_breakdown.columns:
                    fig_stacked.add_trace(go.Bar(
                        x=ext_int_breakdown.index,
                        y=ext_int_breakdown[col],
                        name=col
                    ))
                
                fig_stacked.update_layout(
                    title="Top 10 Issues: External vs Internal",
                    barmode='stack',
                    height=400,
                    xaxis_tickangle=-45,
                    xaxis_title="Issue Type",
                    yaxis_title="Count",
                    legend=dict(orientation='h', yanchor='bottom', y=1.02)
                )
                st.plotly_chart(fig_stacked, use_container_width=True)
        else:
            # Show cost impact instead
            cost_by_issue = df_filtered.groupby('Issue Type')['Cost of Rework'].sum().reindex(
                pareto_data['Issue Type'].head(10)
            )
            
            fig_cost = px.bar(
                x=cost_by_issue.index,
                y=cost_by_issue.values,
                title="Top 10 Issues: Rework Cost Impact",
                color=cost_by_issue.values,
                color_continuous_scale='Reds'
            )
            fig_cost.update_layout(
                height=400,
                xaxis_tickangle=-45,
                showlegend=False,
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_cost, use_container_width=True)
    
    st.markdown("---")
    
    # Row 4: Detailed Table
    st.markdown("### 📊 Complete Issue Type Table")
    
    # Add cost data to pareto table
    cost_by_issue = df_filtered.groupby('Issue Type').agg({
        'Cost of Rework': 'sum',
        'Cost Avoided': 'sum'
    }).reset_index()
    
    display_df = pareto_data.merge(cost_by_issue, on='Issue Type', how='left')
    display_df['Cost of Rework'] = display_df['Cost of Rework'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00")
    display_df['Cost Avoided'] = display_df['Cost Avoided'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00")
    display_df['Percentage'] = display_df['Percentage'].apply(lambda x: f"{x:.1f}%")
    display_df['Cumulative_Pct'] = display_df['Cumulative_Pct'].apply(lambda x: f"{x:.1f}%")
    
    display_df.columns = ['Issue Type', 'NC Count', 'Percentage', 'Cumulative %', 
                         'Total Rework Cost', 'Total Cost Avoided']
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Export option
    st.markdown("---")
    with st.expander("📥 Export Pareto Data"):
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="Download Pareto Analysis (CSV)",
            data=csv,
            file_name="nc_pareto_analysis.csv",
            mime="text/csv"
        )


def calculate_pareto_data(df: pd.DataFrame, min_count: int = 0) -> pd.DataFrame:
    """
    Calculate Pareto analysis data for issue types.
    
    Args:
        df: NC DataFrame
        min_count: Minimum count threshold for inclusion
        
    Returns:
        DataFrame with Issue Type, Count, Percentage, and Cumulative Percentage
    """
    # Count by issue type
    issue_counts = df['Issue Type'].value_counts()
    
    # Apply minimum count filter
    issue_counts = issue_counts[issue_counts >= min_count]
    
    if issue_counts.empty:
        return pd.DataFrame()
    
    # Calculate percentages
    total = issue_counts.sum()
    percentages = (issue_counts / total) * 100
    
    # Calculate cumulative percentage
    cumulative_pct = percentages.cumsum()
    
    # Create DataFrame
    pareto_df = pd.DataFrame({
        'Issue Type': issue_counts.index,
        'Count': issue_counts.values,
        'Percentage': percentages.values,
        'Cumulative_Pct': cumulative_pct.values
    })
    
    return pareto_df


def create_pareto_chart(pareto_data: pd.DataFrame) -> go.Figure:
    """
    Create a Pareto chart with bars and cumulative line.
    
    Args:
        pareto_data: DataFrame with Pareto analysis data
        
    Returns:
        Plotly Figure object
    """
    from plotly.subplots import make_subplots
    
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add bar chart for counts
    fig.add_trace(
        go.Bar(
            x=pareto_data['Issue Type'],
            y=pareto_data['Count'],
            name='NC Count',
            marker_color='#3498db',
            hovertemplate='<b>%{x}</b><br>Count: %{y}<br>Percentage: %{customdata:.1f}%<extra></extra>',
            customdata=pareto_data['Percentage']
        ),
        secondary_y=False
    )
    
    # Add line chart for cumulative percentage
    fig.add_trace(
        go.Scatter(
            x=pareto_data['Issue Type'],
            y=pareto_data['Cumulative_Pct'],
            name='Cumulative %',
            mode='lines+markers',
            line=dict(color='#e74c3c', width=3),
            marker=dict(size=8),
            hovertemplate='<b>%{x}</b><br>Cumulative: %{y:.1f}%<extra></extra>'
        ),
        secondary_y=True
    )
    
    # Add 80% threshold line
    fig.add_hline(
        y=80,
        line_dash="dash",
        line_color="gray",
        annotation_text="80% Threshold",
        annotation_position="right",
        secondary_y=True
    )
    
    # Update layout
    fig.update_layout(
        title="Issue Type Pareto Analysis",
        height=500,
        hovermode='x unified',
        bargap=0.2,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5
        )
    )
    
    # Update x-axis
    fig.update_xaxes(
        title_text="Issue Type",
        tickangle=-45,
        tickfont=dict(size=10)
    )
    
    # Update primary y-axis (bar chart)
    fig.update_yaxes(
        title_text="Number of NCs",
        title_font=dict(color='#3498db'),
        tickfont=dict(color='#3498db'),
        secondary_y=False
    )
    
    # Update secondary y-axis (line chart)
    fig.update_yaxes(
        title_text="Cumulative Percentage (%)",
        title_font=dict(color='#e74c3c'),
        tickfont=dict(color='#e74c3c'),
        range=[0, 105],
        showgrid=False,
        secondary_y=True
    )
    
    return fig


def get_pareto_insights(pareto_data: pd.DataFrame) -> dict:
    """
    Generate insights from Pareto analysis.
    
    Args:
        pareto_data: DataFrame with Pareto analysis data
        
    Returns:
        Dictionary with Pareto insights
    """
    if pareto_data.empty:
        return {}
    
    # Find number of issues for 80%
    issues_for_80 = len(pareto_data[pareto_data['Cumulative_Pct'] <= 80]) + 1
    
    # Top 3 issues
    top_3 = pareto_data.head(3)['Issue Type'].tolist()
    top_3_pct = pareto_data.head(3)['Cumulative_Pct'].iloc[-1] if len(pareto_data) >= 3 else 0
    
    return {
        'total_issue_types': len(pareto_data),
        'total_ncs': pareto_data['Count'].sum(),
        'issues_for_80_pct': issues_for_80,
        'top_issue': pareto_data.iloc[0]['Issue Type'],
        'top_issue_count': pareto_data.iloc[0]['Count'],
        'top_issue_pct': pareto_data.iloc[0]['Percentage'],
        'top_3_issues': top_3,
        'top_3_cumulative_pct': top_3_pct
    }
