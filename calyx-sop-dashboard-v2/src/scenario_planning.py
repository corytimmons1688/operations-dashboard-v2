"""
Scenario Planning Module for S&OP Dashboard
Tab 3: Scenario creation, comparison, and approval workflow

Features:
- Growth rate adjustment (±%)
- Forecast blending (% demand vs % sales forecast)
- Save/load/compare scenarios
- Persist scenarios with assumptions and cash implications
- Scenario approval workflow

Author: Xander @ Calyx Containers
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
import logging

from .sop_data_loader import (
    load_invoice_lines, load_deals, prepare_demand_history
)
from .forecasting_models import generate_forecast, blend_forecasts, ForecastResult

logger = logging.getLogger(__name__)


# Session state keys for scenario management
SCENARIOS_KEY = 'sop_scenarios'
ACTIVE_SCENARIO_KEY = 'active_scenario'
APPROVED_SCENARIO_KEY = 'approved_scenario'


def init_scenario_state():
    """Initialize session state for scenarios."""
    if SCENARIOS_KEY not in st.session_state:
        st.session_state[SCENARIOS_KEY] = {}
    if ACTIVE_SCENARIO_KEY not in st.session_state:
        st.session_state[ACTIVE_SCENARIO_KEY] = None
    if APPROVED_SCENARIO_KEY not in st.session_state:
        st.session_state[APPROVED_SCENARIO_KEY] = None


def render_scenario_planning():
    """Main render function for Scenario Planning tab."""
    
    init_scenario_state()
    
    st.markdown("## 🎯 Scenario Planning")
    st.markdown("Create, compare, and approve demand scenarios")
    
    # Load data
    with st.spinner("Loading data for scenarios..."):
        invoice_lines = load_invoice_lines()
        deals = load_deals()
    
    if invoice_lines is None:
        st.error("Unable to load data. Please check your data connection.")
        return
    
    # Prepare base forecast
    df = invoice_lines.copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    df['Period'] = df['Date'].dt.to_period('M').dt.to_timestamp()
    
    monthly_demand = df.groupby('Period')['Quantity'].sum()
    monthly_revenue = df.groupby('Period')['Amount'].sum() if 'Amount' in df.columns else None
    
    if len(monthly_demand) < 6:
        st.warning("Insufficient historical data for scenario planning.")
        return
    
    # Main content layout
    col_main, col_sidebar = st.columns([3, 1])
    
    with col_sidebar:
        render_scenario_sidebar()
    
    with col_main:
        # Tabs for scenario workflow
        tab1, tab2, tab3, tab4 = st.tabs([
            "🔧 Create Scenario",
            "📊 Compare Scenarios",
            "✅ Approve Scenario",
            "📋 Scenario Library"
        ])
        
        with tab1:
            render_create_scenario(monthly_demand, monthly_revenue, deals)
        
        with tab2:
            render_compare_scenarios(monthly_demand)
        
        with tab3:
            render_approve_scenario()
        
        with tab4:
            render_scenario_library()


def render_scenario_sidebar():
    """Render the scenario management sidebar."""
    
    st.markdown("### 📁 Scenarios")
    
    scenarios = st.session_state.get(SCENARIOS_KEY, {})
    
    if scenarios:
        st.markdown(f"**{len(scenarios)} scenarios saved**")
        
        # List scenarios
        for name, scenario in scenarios.items():
            is_approved = st.session_state.get(APPROVED_SCENARIO_KEY) == name
            icon = "✅" if is_approved else "📄"
            st.markdown(f"{icon} {name}")
    else:
        st.info("No scenarios created yet")
    
    st.markdown("---")
    
    # Quick actions
    if st.button("🗑️ Clear All Scenarios", use_container_width=True):
        st.session_state[SCENARIOS_KEY] = {}
        st.session_state[ACTIVE_SCENARIO_KEY] = None
        st.session_state[APPROVED_SCENARIO_KEY] = None
        st.rerun()


def render_create_scenario(
    monthly_demand: pd.Series,
    monthly_revenue: pd.Series,
    deals: pd.DataFrame
):
    """Render scenario creation interface."""
    
    st.markdown("### 🔧 Create New Scenario")
    
    col1, col2 = st.columns(2)
    
    with col1:
        scenario_name = st.text_input(
            "Scenario Name",
            value=f"Scenario_{datetime.now().strftime('%Y%m%d_%H%M')}",
            key="new_scenario_name"
        )
        
        scenario_description = st.text_area(
            "Description / Assumptions",
            placeholder="Describe the assumptions behind this scenario...",
            key="scenario_description"
        )
    
    with col2:
        forecast_horizon = st.selectbox(
            "Forecast Horizon",
            options=[6, 9, 12, 18, 24],
            index=2,
            format_func=lambda x: f"{x} months",
            key="scenario_horizon"
        )
        
        base_model = st.selectbox(
            "Base Forecast Model",
            options=['exponential_smoothing', 'arima', 'ml_random_forest'],
            format_func=lambda x: {
                'exponential_smoothing': 'Exponential Smoothing',
                'arima': 'ARIMA/SARIMA',
                'ml_random_forest': 'Machine Learning (RF)'
            }.get(x, x),
            key="scenario_base_model"
        )
    
    st.markdown("---")
    st.markdown("### 📊 Scenario Adjustments")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Growth Adjustment")
        growth_rate = st.slider(
            "Annual Growth Rate (%)",
            min_value=-50,
            max_value=100,
            value=0,
            step=5,
            key="growth_rate",
            help="Apply uniform growth/decline to forecast"
        )
    
    with col2:
        st.markdown("#### Forecast Blend")
        demand_weight = st.slider(
            "Demand Forecast Weight (%)",
            min_value=0,
            max_value=100,
            value=70,
            step=10,
            key="demand_weight",
            help="Blend between demand forecast and pipeline-based forecast"
        )
        pipeline_weight = 100 - demand_weight
        st.caption(f"Pipeline Weight: {pipeline_weight}%")
    
    with col3:
        st.markdown("#### Seasonality Override")
        seasonality_factor = st.slider(
            "Seasonality Strength (%)",
            min_value=50,
            max_value=150,
            value=100,
            step=10,
            key="seasonality_factor",
            help="Amplify or dampen seasonal patterns"
        )
    
    st.markdown("---")
    st.markdown("### 🎚️ Quarterly Adjustments")
    
    col1, col2, col3, col4 = st.columns(4)
    
    q_adjustments = {}
    with col1:
        q_adjustments['Q1'] = st.number_input("Q1 Adjustment (%)", value=0, step=5, key="q1_adj")
    with col2:
        q_adjustments['Q2'] = st.number_input("Q2 Adjustment (%)", value=0, step=5, key="q2_adj")
    with col3:
        q_adjustments['Q3'] = st.number_input("Q3 Adjustment (%)", value=0, step=5, key="q3_adj")
    with col4:
        q_adjustments['Q4'] = st.number_input("Q4 Adjustment (%)", value=0, step=5, key="q4_adj")
    
    st.markdown("---")
    
    # Generate and preview scenario
    if st.button("🔄 Generate Scenario Preview", type="primary", use_container_width=True):
        with st.spinner("Generating scenario..."):
            try:
                scenario_forecast = generate_scenario_forecast(
                    monthly_demand,
                    monthly_revenue,
                    deals,
                    horizon=forecast_horizon,
                    model=base_model,
                    growth_rate=growth_rate,
                    demand_weight=demand_weight / 100,
                    seasonality_factor=seasonality_factor / 100,
                    quarterly_adjustments=q_adjustments
                )
                
                # Store in session for preview
                st.session_state['preview_scenario'] = {
                    'name': scenario_name,
                    'description': scenario_description,
                    'forecast': scenario_forecast,
                    'parameters': {
                        'horizon': forecast_horizon,
                        'model': base_model,
                        'growth_rate': growth_rate,
                        'demand_weight': demand_weight,
                        'seasonality_factor': seasonality_factor,
                        'quarterly_adjustments': q_adjustments
                    },
                    'created_at': datetime.now().isoformat(),
                    'historical_demand': monthly_demand.to_dict()
                }
                
                st.success("Scenario generated! Review below.")
                
            except Exception as e:
                st.error(f"Failed to generate scenario: {str(e)}")
    
    # Preview area
    if 'preview_scenario' in st.session_state:
        preview = st.session_state['preview_scenario']
        
        st.markdown("### 📈 Scenario Preview")
        
        # Chart
        render_scenario_chart(monthly_demand, preview['forecast'])
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_forecast = preview['forecast'].forecast.sum()
            st.metric("Total Forecast", f"{total_forecast:,.0f}")
        
        with col2:
            last_year = monthly_demand.tail(12).sum()
            yoy_change = ((total_forecast - last_year) / last_year * 100) if last_year > 0 else 0
            st.metric("vs Last 12M", f"{yoy_change:+.1f}%")
        
        with col3:
            avg_monthly = total_forecast / forecast_horizon
            st.metric("Avg Monthly", f"{avg_monthly:,.0f}")
        
        with col4:
            mape = preview['forecast'].metrics.get('MAPE', 0)
            st.metric("Base MAPE", f"{mape:.1f}%")
        
        # Cash flow implications
        st.markdown("---")
        st.markdown("#### 💰 Cash Flow Implications")
        
        render_cash_implications(preview['forecast'], monthly_revenue)
        
        # Save button
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Save Scenario", type="primary", use_container_width=True):
                save_scenario(preview)
                st.success(f"Scenario '{preview['name']}' saved!")
                del st.session_state['preview_scenario']
                st.rerun()
        
        with col2:
            if st.button("🗑️ Discard Preview", use_container_width=True):
                del st.session_state['preview_scenario']
                st.rerun()


def generate_scenario_forecast(
    monthly_demand: pd.Series,
    monthly_revenue: pd.Series,
    deals: pd.DataFrame,
    horizon: int,
    model: str,
    growth_rate: float,
    demand_weight: float,
    seasonality_factor: float,
    quarterly_adjustments: Dict[str, float]
) -> ForecastResult:
    """Generate a scenario forecast with all adjustments applied."""
    
    # Generate base demand forecast
    base_forecast = generate_forecast(monthly_demand, model=model, horizon=horizon)
    
    # Apply adjustments
    adjusted_values = base_forecast.forecast.copy()
    
    # 1. Apply growth rate (compound monthly)
    if growth_rate != 0:
        monthly_growth = (1 + growth_rate / 100) ** (1/12) - 1
        for i in range(len(adjusted_values)):
            adjusted_values.iloc[i] *= (1 + monthly_growth) ** (i + 1)
    
    # 2. Apply seasonality factor
    if seasonality_factor != 1.0:
        # Calculate historical seasonality pattern
        seasonal_pattern = monthly_demand.groupby(monthly_demand.index.month).mean()
        overall_mean = seasonal_pattern.mean()
        seasonal_indices = seasonal_pattern / overall_mean
        
        for i, (date, value) in enumerate(adjusted_values.items()):
            month = date.month
            seasonal_idx = seasonal_indices.get(month, 1.0)
            # Adjust towards or away from 1.0 based on factor
            new_idx = 1 + (seasonal_idx - 1) * seasonality_factor
            adjusted_values.iloc[i] = value * new_idx / seasonal_idx
    
    # 3. Apply quarterly adjustments
    for i, (date, value) in enumerate(adjusted_values.items()):
        quarter = f"Q{(date.month - 1) // 3 + 1}"
        q_adj = quarterly_adjustments.get(quarter, 0) / 100
        adjusted_values.iloc[i] *= (1 + q_adj)
    
    # 4. Blend with pipeline if available
    if demand_weight < 1.0 and deals is not None and not deals.empty:
        # Create a simple pipeline-based forecast
        pipeline_forecast = create_pipeline_forecast(deals, horizon, adjusted_values.index)
        if pipeline_forecast is not None:
            adjusted_values = (adjusted_values * demand_weight + 
                             pipeline_forecast * (1 - demand_weight))
    
    # Ensure non-negative
    adjusted_values = adjusted_values.clip(lower=0)
    
    # Create new result with adjusted forecast
    return ForecastResult(
        forecast=adjusted_values,
        model_name=f"Scenario ({model})",
        confidence_lower=base_forecast.confidence_lower * (adjusted_values / base_forecast.forecast).mean() if base_forecast.confidence_lower is not None else None,
        confidence_upper=base_forecast.confidence_upper * (adjusted_values / base_forecast.forecast).mean() if base_forecast.confidence_upper is not None else None,
        metrics=base_forecast.metrics,
        parameters={
            'base_model': model,
            'growth_rate': growth_rate,
            'demand_weight': demand_weight,
            'seasonality_factor': seasonality_factor,
            'quarterly_adjustments': quarterly_adjustments
        }
    )


def create_pipeline_forecast(
    deals: pd.DataFrame,
    horizon: int,
    forecast_index: pd.DatetimeIndex
) -> Optional[pd.Series]:
    """Create a forecast based on pipeline data."""
    
    if deals is None or deals.empty:
        return None
    
    df = deals.copy()
    df['Close Date'] = pd.to_datetime(df['Close Date'], errors='coerce')
    df = df.dropna(subset=['Close Date', 'Amount'])
    
    if df.empty:
        return None
    
    # Group by month
    df['Month'] = df['Close Date'].dt.to_period('M').dt.to_timestamp()
    monthly_pipeline = df.groupby('Month')['Amount'].sum()
    
    # Map to forecast periods
    pipeline_values = []
    for period in forecast_index:
        if period in monthly_pipeline.index:
            pipeline_values.append(monthly_pipeline[period])
        else:
            # Use average pipeline as proxy
            pipeline_values.append(monthly_pipeline.mean() if len(monthly_pipeline) > 0 else 0)
    
    # Convert to quantity estimate (rough conversion)
    avg_order_value = monthly_pipeline.mean() if len(monthly_pipeline) > 0 else 1
    pipeline_qty = pd.Series(pipeline_values, index=forecast_index)
    
    return pipeline_qty


def render_scenario_chart(historical: pd.Series, forecast: ForecastResult):
    """Render a scenario preview chart."""
    
    fig = go.Figure()
    
    # Historical
    fig.add_trace(go.Scatter(
        x=historical.index,
        y=historical.values,
        mode='lines+markers',
        name='Historical',
        line=dict(color='#3498db', width=2)
    ))
    
    # Scenario forecast
    fig.add_trace(go.Scatter(
        x=forecast.forecast.index,
        y=forecast.forecast.values,
        mode='lines+markers',
        name='Scenario Forecast',
        line=dict(color='#e74c3c', width=2, dash='dash')
    ))
    
    # Confidence interval
    if forecast.confidence_lower is not None:
        fig.add_trace(go.Scatter(
            x=list(forecast.forecast.index) + list(forecast.forecast.index[::-1]),
            y=list(forecast.confidence_upper.values) + list(forecast.confidence_lower.values[::-1]),
            fill='toself',
            fillcolor='rgba(231, 76, 60, 0.15)',
            line=dict(color='rgba(255,255,255,0)'),
            name='95% CI'
        ))
    
    fig.update_layout(
        title="Scenario Forecast vs Historical",
        xaxis_title="Period",
        yaxis_title="Quantity",
        height=400,
        hovermode='x unified',
        legend=dict(orientation='h', y=1.1)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_cash_implications(forecast: ForecastResult, monthly_revenue: pd.Series):
    """Render cash flow implications of scenario."""
    
    # Estimate revenue per unit from historical data
    if monthly_revenue is not None and len(monthly_revenue) > 0:
        avg_rev_per_unit = monthly_revenue.mean()
    else:
        avg_rev_per_unit = 100  # Default assumption
    
    # Calculate projected revenue
    projected_revenue = forecast.forecast * avg_rev_per_unit
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_projected = projected_revenue.sum()
        st.metric("Projected Revenue", f"${total_projected:,.0f}")
    
    with col2:
        # Assuming 30% COGS
        cogs = total_projected * 0.3
        st.metric("Est. COGS (30%)", f"${cogs:,.0f}")
    
    with col3:
        gross_profit = total_projected - cogs
        st.metric("Est. Gross Profit", f"${gross_profit:,.0f}")
    
    # Monthly cash flow chart
    monthly_cf = projected_revenue - (projected_revenue * 0.3)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=monthly_cf.index,
        y=monthly_cf.values,
        name='Monthly Gross Profit',
        marker_color='#2ecc71'
    ))
    
    # Cumulative line
    cumulative = monthly_cf.cumsum()
    fig.add_trace(go.Scatter(
        x=cumulative.index,
        y=cumulative.values,
        mode='lines+markers',
        name='Cumulative',
        yaxis='y2',
        line=dict(color='#3498db', width=2)
    ))
    
    fig.update_layout(
        title="Projected Cash Flow",
        height=350,
        yaxis=dict(title="Monthly ($)"),
        yaxis2=dict(title="Cumulative ($)", overlaying='y', side='right'),
        legend=dict(orientation='h', y=1.1),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def save_scenario(scenario: Dict):
    """Save a scenario to session state."""
    if SCENARIOS_KEY not in st.session_state:
        st.session_state[SCENARIOS_KEY] = {}
    
    # Convert forecast to serializable format
    scenario_to_save = scenario.copy()
    if 'forecast' in scenario_to_save:
        fc = scenario_to_save['forecast']
        scenario_to_save['forecast_data'] = {
            'values': fc.forecast.to_dict(),
            'model_name': fc.model_name,
            'metrics': fc.metrics,
            'parameters': fc.parameters
        }
        if fc.confidence_lower is not None:
            scenario_to_save['forecast_data']['lower'] = fc.confidence_lower.to_dict()
        if fc.confidence_upper is not None:
            scenario_to_save['forecast_data']['upper'] = fc.confidence_upper.to_dict()
        del scenario_to_save['forecast']
    
    st.session_state[SCENARIOS_KEY][scenario['name']] = scenario_to_save


def load_scenario_forecast(scenario: Dict) -> ForecastResult:
    """Load a ForecastResult from saved scenario data."""
    fc_data = scenario.get('forecast_data', {})
    
    forecast = pd.Series(fc_data.get('values', {}))
    forecast.index = pd.to_datetime(forecast.index)
    
    lower = None
    upper = None
    if 'lower' in fc_data:
        lower = pd.Series(fc_data['lower'])
        lower.index = pd.to_datetime(lower.index)
    if 'upper' in fc_data:
        upper = pd.Series(fc_data['upper'])
        upper.index = pd.to_datetime(upper.index)
    
    return ForecastResult(
        forecast=forecast,
        model_name=fc_data.get('model_name', 'Scenario'),
        confidence_lower=lower,
        confidence_upper=upper,
        metrics=fc_data.get('metrics', {}),
        parameters=fc_data.get('parameters', {})
    )


def render_compare_scenarios(monthly_demand: pd.Series):
    """Render scenario comparison view."""
    
    st.markdown("### 📊 Compare Scenarios")
    
    scenarios = st.session_state.get(SCENARIOS_KEY, {})
    
    if len(scenarios) < 2:
        st.info("Create at least 2 scenarios to compare them.")
        return
    
    # Select scenarios to compare
    scenario_names = list(scenarios.keys())
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_scenarios = st.multiselect(
            "Select Scenarios to Compare",
            options=scenario_names,
            default=scenario_names[:min(3, len(scenario_names))],
            key="compare_scenarios"
        )
    
    with col2:
        comparison_metric = st.selectbox(
            "Comparison Metric",
            options=['Total Forecast', 'Monthly Average', 'Peak Month', 'Growth Rate'],
            key="comparison_metric"
        )
    
    if len(selected_scenarios) < 2:
        st.warning("Select at least 2 scenarios to compare.")
        return
    
    # Load selected scenarios
    loaded_scenarios = {}
    for name in selected_scenarios:
        scenario = scenarios[name]
        loaded_scenarios[name] = {
            'info': scenario,
            'forecast': load_scenario_forecast(scenario)
        }
    
    # Comparison chart
    fig = go.Figure()
    
    # Add historical
    fig.add_trace(go.Scatter(
        x=monthly_demand.index,
        y=monthly_demand.values,
        mode='lines',
        name='Historical',
        line=dict(color='#7f8c8d', width=2)
    ))
    
    # Add each scenario
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#9b59b6', '#f1c40f']
    
    for i, (name, data) in enumerate(loaded_scenarios.items()):
        fc = data['forecast']
        color = colors[i % len(colors)]
        
        fig.add_trace(go.Scatter(
            x=fc.forecast.index,
            y=fc.forecast.values,
            mode='lines+markers',
            name=name,
            line=dict(color=color, width=2, dash='dash')
        ))
    
    fig.update_layout(
        title="Scenario Comparison",
        xaxis_title="Period",
        yaxis_title="Quantity",
        height=450,
        hovermode='x unified',
        legend=dict(orientation='h', y=1.1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Comparison table
    st.markdown("#### Scenario Metrics Comparison")
    
    comparison_data = []
    for name, data in loaded_scenarios.items():
        fc = data['forecast']
        info = data['info']
        
        comparison_data.append({
            'Scenario': name,
            'Total Forecast': fc.forecast.sum(),
            'Monthly Avg': fc.forecast.mean(),
            'Peak Month': fc.forecast.max(),
            'Peak Period': fc.forecast.idxmax().strftime('%b %Y'),
            'Growth Rate (%)': info.get('parameters', {}).get('growth_rate', 0),
            'Model': info.get('parameters', {}).get('model', 'N/A'),
            'Created': info.get('created_at', 'N/A')[:10]
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # Format numbers
    comparison_df['Total Forecast'] = comparison_df['Total Forecast'].apply(lambda x: f"{x:,.0f}")
    comparison_df['Monthly Avg'] = comparison_df['Monthly Avg'].apply(lambda x: f"{x:,.0f}")
    comparison_df['Peak Month'] = comparison_df['Peak Month'].apply(lambda x: f"{x:,.0f}")
    
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    # Variance analysis
    st.markdown("---")
    st.markdown("#### Variance Analysis")
    
    if len(loaded_scenarios) >= 2:
        scenario_list = list(loaded_scenarios.keys())
        base_name = scenario_list[0]
        base_fc = loaded_scenarios[base_name]['forecast'].forecast
        
        variance_data = []
        for name in scenario_list[1:]:
            comp_fc = loaded_scenarios[name]['forecast'].forecast
            
            # Align indexes
            common_idx = base_fc.index.intersection(comp_fc.index)
            base_vals = base_fc[common_idx]
            comp_vals = comp_fc[common_idx]
            
            variance = comp_vals.sum() - base_vals.sum()
            variance_pct = (variance / base_vals.sum() * 100) if base_vals.sum() > 0 else 0
            
            variance_data.append({
                'Comparison': f"{name} vs {base_name}",
                'Variance (Units)': f"{variance:+,.0f}",
                'Variance (%)': f"{variance_pct:+.1f}%"
            })
        
        variance_df = pd.DataFrame(variance_data)
        st.dataframe(variance_df, use_container_width=True, hide_index=True)


def render_approve_scenario():
    """Render scenario approval interface."""
    
    st.markdown("### ✅ Approve Scenario")
    
    scenarios = st.session_state.get(SCENARIOS_KEY, {})
    
    if not scenarios:
        st.info("No scenarios available for approval. Create a scenario first.")
        return
    
    current_approved = st.session_state.get(APPROVED_SCENARIO_KEY)
    
    if current_approved:
        st.success(f"Currently Approved: **{current_approved}**")
        
        # Display approved scenario details
        if current_approved in scenarios:
            approved = scenarios[current_approved]
            fc = load_scenario_forecast(approved)
            
            st.markdown("#### Approved Scenario Summary")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Forecast", f"{fc.forecast.sum():,.0f}")
            with col2:
                st.metric("Horizon", f"{len(fc.forecast)} months")
            with col3:
                st.metric("Model", approved.get('parameters', {}).get('model', 'N/A'))
    
    st.markdown("---")
    
    # Select scenario to approve
    scenario_options = list(scenarios.keys())
    
    selected_for_approval = st.selectbox(
        "Select Scenario for Approval",
        options=["-- Select --"] + scenario_options,
        key="approval_selection"
    )
    
    if selected_for_approval != "-- Select --":
        scenario = scenarios[selected_for_approval]
        fc = load_scenario_forecast(scenario)
        
        st.markdown(f"#### Preview: {selected_for_approval}")
        
        # Display scenario details
        st.markdown(f"**Description:** {scenario.get('description', 'No description')}")
        st.markdown(f"**Created:** {scenario.get('created_at', 'N/A')[:10]}")
        
        params = scenario.get('parameters', {})
        st.markdown(f"**Parameters:**")
        st.markdown(f"- Growth Rate: {params.get('growth_rate', 0)}%")
        st.markdown(f"- Demand Weight: {params.get('demand_weight', 100)}%")
        st.markdown(f"- Model: {params.get('model', 'N/A')}")
        
        # Simple chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=fc.forecast.index,
            y=fc.forecast.values,
            mode='lines+markers',
            fill='tozeroy',
            line=dict(color='#2ecc71')
        ))
        fig.update_layout(
            title=f"Forecast: {selected_for_approval}",
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Approval button
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Approve This Scenario", type="primary", use_container_width=True):
                st.session_state[APPROVED_SCENARIO_KEY] = selected_for_approval
                st.success(f"Scenario '{selected_for_approval}' has been approved!")
                st.rerun()
        
        with col2:
            if current_approved and st.button("❌ Revoke Current Approval", use_container_width=True):
                st.session_state[APPROVED_SCENARIO_KEY] = None
                st.info("Approval revoked.")
                st.rerun()


def render_scenario_library():
    """Render scenario library with management options."""
    
    st.markdown("### 📋 Scenario Library")
    
    scenarios = st.session_state.get(SCENARIOS_KEY, {})
    approved = st.session_state.get(APPROVED_SCENARIO_KEY)
    
    if not scenarios:
        st.info("No scenarios in library. Create your first scenario!")
        return
    
    # Display all scenarios
    for name, scenario in scenarios.items():
        is_approved = name == approved
        
        with st.expander(f"{'✅ ' if is_approved else ''}{name}", expanded=is_approved):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Description:** {scenario.get('description', 'No description')}")
                st.markdown(f"**Created:** {scenario.get('created_at', 'N/A')[:16]}")
                
                params = scenario.get('parameters', {})
                st.markdown("**Parameters:**")
                param_str = f"Growth: {params.get('growth_rate', 0)}% | "
                param_str += f"Demand Weight: {params.get('demand_weight', 100)}% | "
                param_str += f"Model: {params.get('model', 'N/A')}"
                st.caption(param_str)
                
                # Forecast summary
                fc = load_scenario_forecast(scenario)
                st.markdown(f"**Forecast Total:** {fc.forecast.sum():,.0f} units over {len(fc.forecast)} months")
            
            with col2:
                if st.button("🗑️ Delete", key=f"delete_{name}"):
                    del st.session_state[SCENARIOS_KEY][name]
                    if st.session_state.get(APPROVED_SCENARIO_KEY) == name:
                        st.session_state[APPROVED_SCENARIO_KEY] = None
                    st.rerun()
    
    # Export all scenarios
    st.markdown("---")
    
    if st.button("📥 Export All Scenarios (JSON)", use_container_width=True):
        export_data = {
            'scenarios': scenarios,
            'approved': approved,
            'exported_at': datetime.now().isoformat()
        }
        
        json_str = json.dumps(export_data, indent=2, default=str)
        
        st.download_button(
            label="Download Scenarios",
            data=json_str,
            file_name=f"scenarios_export_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
