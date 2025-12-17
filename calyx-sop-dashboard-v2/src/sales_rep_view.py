"""
Sales Rep View Module for S&OP Dashboard
Tab 1: Sales representative focused view with customer/SKU forecasts

Features:
- Filter by Sales Rep, Customer (auto-restrict SKUs to customer history)
- Historical SKU ordering cadence
- Invoice payment behavior
- SKU-level demand forecast
- Quarterly recommendations (Q1-Q4)
- Customer-safe visualizations

Author: Xander @ Calyx Containers
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import logging

from .sop_data_loader import (
    load_invoice_lines, load_sales_orders, load_customers, load_items,
    get_unique_sales_reps, get_customers_for_rep, get_skus_for_customer,
    prepare_demand_history
)
from .forecasting_models import generate_forecast, ForecastResult

logger = logging.getLogger(__name__)


def render_sales_rep_view():
    """Main render function for Sales Rep View tab."""
    
    st.markdown("## 👤 Sales Rep View")
    st.markdown("Customer-focused demand analysis and forecasting")
    
    # Load data
    with st.spinner("Loading sales data..."):
        invoice_lines = load_invoice_lines()
        sales_orders = load_sales_orders()
        customers = load_customers()
        items = load_items()
    
    if invoice_lines is None or sales_orders is None:
        st.error("Unable to load sales data. Please check your data connection.")
        return
    
    # Sidebar filters
    st.sidebar.markdown("### 🔍 Sales Rep Filters")
    
    # Sales Rep filter
    sales_reps = get_unique_sales_reps(sales_orders)
    if not sales_reps:
        sales_reps = ["All"]
    
    selected_rep = st.sidebar.selectbox(
        "Select Sales Rep",
        options=["All"] + sales_reps,
        key="sales_rep_filter"
    )
    
    # Customer filter (restricted by rep)
    if selected_rep != "All":
        available_customers = get_customers_for_rep(sales_orders, selected_rep)
    else:
        available_customers = get_unique_customers_from_invoices(invoice_lines)
    
    selected_customer = st.sidebar.selectbox(
        "Select Customer",
        options=["All"] + available_customers,
        key="customer_filter"
    )
    
    # SKU filter (restricted by customer)
    if selected_customer != "All":
        available_skus = get_skus_for_customer(invoice_lines, selected_customer)
    else:
        available_skus = get_unique_items_from_invoices(invoice_lines)
    
    selected_sku = st.sidebar.selectbox(
        "Select SKU (Optional)",
        options=["All"] + available_skus,
        key="sku_filter"
    )
    
    # Forecast settings
    st.sidebar.markdown("### 📊 Forecast Settings")
    
    forecast_horizon = st.sidebar.selectbox(
        "Forecast Horizon",
        options=[3, 6, 9, 12, 18, 24],
        index=3,
        format_func=lambda x: f"{x} months",
        key="forecast_horizon"
    )
    
    forecast_model = st.sidebar.selectbox(
        "Forecast Model",
        options=['exponential_smoothing', 'arima', 'ml_random_forest'],
        format_func=lambda x: {
            'exponential_smoothing': 'Exponential Smoothing',
            'arima': 'ARIMA/SARIMA',
            'ml_random_forest': 'Machine Learning (RF)'
        }.get(x, x),
        key="forecast_model"
    )
    
    st.sidebar.markdown("---")
    
    # Filter data based on selections
    filtered_invoices = filter_invoice_data(
        invoice_lines, selected_rep, selected_customer, selected_sku, sales_orders
    )
    
    if filtered_invoices.empty:
        st.warning("No data found for the selected filters.")
        return
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Ordering Cadence",
        "💳 Payment Behavior", 
        "🔮 SKU Forecast",
        "📋 Quarterly Recommendations"
    ])
    
    with tab1:
        render_ordering_cadence(filtered_invoices, selected_customer, selected_sku)
    
    with tab2:
        render_payment_behavior(filtered_invoices, invoice_lines, selected_customer)
    
    with tab3:
        render_sku_forecast(filtered_invoices, forecast_horizon, forecast_model, selected_sku)
    
    with tab4:
        render_quarterly_recommendations(filtered_invoices, forecast_horizon, forecast_model)


def get_unique_customers_from_invoices(invoice_lines: pd.DataFrame) -> List[str]:
    """Get unique customer names from invoice lines."""
    for col in ['Correct Customer', 'Customer']:
        if col in invoice_lines.columns:
            return sorted(invoice_lines[col].dropna().unique().tolist())
    return []


def get_unique_items_from_invoices(invoice_lines: pd.DataFrame) -> List[str]:
    """Get unique items from invoice lines."""
    if 'Item' in invoice_lines.columns:
        return sorted(invoice_lines['Item'].dropna().unique().tolist())
    return []


def filter_invoice_data(
    invoice_lines: pd.DataFrame,
    rep: str,
    customer: str,
    sku: str,
    sales_orders: pd.DataFrame
) -> pd.DataFrame:
    """Filter invoice line data based on selections."""
    df = invoice_lines.copy()
    
    # Get customer column name
    customer_col = 'Correct Customer' if 'Correct Customer' in df.columns else 'Customer'
    
    # Filter by rep (via sales orders customer mapping)
    if rep != "All" and 'Rep Master' in sales_orders.columns:
        rep_customers = sales_orders[sales_orders['Rep Master'] == rep]
        for col in ['Customer', 'Corrected Customer Name', 'Customer Companyname']:
            if col in rep_customers.columns:
                valid_customers = rep_customers[col].dropna().unique().tolist()
                df = df[df[customer_col].isin(valid_customers)]
                break
    
    # Filter by customer
    if customer != "All":
        df = df[df[customer_col] == customer]
    
    # Filter by SKU
    if sku != "All" and 'Item' in df.columns:
        df = df[df['Item'] == sku]
    
    return df


def render_ordering_cadence(df: pd.DataFrame, customer: str, sku: str):
    """Render the ordering cadence analysis section."""
    
    st.markdown("### 📈 Historical Ordering Cadence")
    
    if df.empty:
        st.info("No ordering data available for the selected filters.")
        return
    
    # Ensure date column
    date_col = 'Date'
    if date_col not in df.columns:
        st.warning("Date column not found in data.")
        return
    
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])
    
    # Aggregate by month
    df['Month'] = df[date_col].dt.to_period('M').astype(str)
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_orders = df['Document Number'].nunique() if 'Document Number' in df.columns else len(df)
        st.metric("Total Orders", f"{total_orders:,}")
    
    with col2:
        total_qty = df['Quantity'].sum() if 'Quantity' in df.columns else 0
        st.metric("Total Quantity", f"{total_qty:,.0f}")
    
    with col3:
        total_revenue = df['Amount'].sum() if 'Amount' in df.columns else 0
        st.metric("Total Revenue", f"${total_revenue:,.2f}")
    
    with col4:
        # Calculate average days between orders
        if 'Document Number' in df.columns:
            order_dates = df.groupby('Document Number')[date_col].min().sort_values()
            if len(order_dates) > 1:
                days_between = order_dates.diff().dt.days.mean()
                st.metric("Avg Days Between Orders", f"{days_between:.0f}")
            else:
                st.metric("Avg Days Between Orders", "N/A")
        else:
            st.metric("Avg Days Between Orders", "N/A")
    
    st.markdown("---")
    
    # Monthly ordering trend
    monthly_data = df.groupby('Month').agg({
        'Quantity': 'sum',
        'Amount': 'sum'
    }).reset_index()
    monthly_data = monthly_data.sort_values('Month')
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(
            x=monthly_data['Month'],
            y=monthly_data['Quantity'],
            name='Quantity',
            marker_color='#3498db'
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(
            x=monthly_data['Month'],
            y=monthly_data['Amount'],
            name='Revenue',
            mode='lines+markers',
            line=dict(color='#e74c3c', width=2),
            marker=dict(size=8)
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        title="Monthly Ordering Trend",
        height=400,
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    fig.update_xaxes(title_text="Month", tickangle=-45)
    fig.update_yaxes(title_text="Quantity", secondary_y=False)
    fig.update_yaxes(title_text="Revenue ($)", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # SKU breakdown if not filtered to single SKU
    if sku == "All" and 'Item' in df.columns:
        st.markdown("### Top SKUs by Quantity")
        
        sku_summary = df.groupby('Item').agg({
            'Quantity': 'sum',
            'Amount': 'sum',
            'Document Number': 'nunique'
        }).reset_index()
        sku_summary.columns = ['SKU', 'Total Qty', 'Total Revenue', 'Order Count']
        sku_summary = sku_summary.sort_values('Total Qty', ascending=False).head(15)
        
        fig_sku = px.bar(
            sku_summary,
            x='SKU',
            y='Total Qty',
            color='Order Count',
            color_continuous_scale='Blues',
            title="Top 15 SKUs by Quantity"
        )
        fig_sku.update_layout(height=400)
        fig_sku.update_xaxes(tickangle=-45)
        
        st.plotly_chart(fig_sku, use_container_width=True)
    
    # Order frequency heatmap (day of week vs month)
    if len(df) > 10:
        st.markdown("### Order Frequency Heatmap")
        
        df['DayOfWeek'] = df[date_col].dt.day_name()
        df['MonthName'] = df[date_col].dt.month_name()
        
        heatmap_data = df.groupby(['DayOfWeek', 'MonthName']).size().reset_index(name='Orders')
        heatmap_pivot = heatmap_data.pivot(index='DayOfWeek', columns='MonthName', values='Orders').fillna(0)
        
        # Reorder days
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_pivot = heatmap_pivot.reindex([d for d in day_order if d in heatmap_pivot.index])
        
        # Reorder months
        month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        heatmap_pivot = heatmap_pivot[[m for m in month_order if m in heatmap_pivot.columns]]
        
        fig_heat = px.imshow(
            heatmap_pivot,
            color_continuous_scale='Blues',
            title="Order Frequency: Day of Week vs Month"
        )
        fig_heat.update_layout(height=350)
        
        st.plotly_chart(fig_heat, use_container_width=True)


def render_payment_behavior(filtered_df: pd.DataFrame, all_invoices: pd.DataFrame, customer: str):
    """Render the payment behavior analysis section."""
    
    st.markdown("### 💳 Invoice Payment Behavior")
    
    # Use filtered data or customer-specific data
    if customer != "All":
        customer_col = 'Correct Customer' if 'Correct Customer' in all_invoices.columns else 'Customer'
        df = all_invoices[all_invoices[customer_col] == customer].copy()
    else:
        df = filtered_df.copy()
    
    if df.empty:
        st.info("No payment data available for the selected filters.")
        return
    
    # Calculate payment metrics
    if 'Date' in df.columns and 'Date Closed' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Date Closed'] = pd.to_datetime(df['Date Closed'], errors='coerce')
        
        # Days to payment
        df['Days_to_Payment'] = (df['Date Closed'] - df['Date']).dt.days
        df = df[df['Days_to_Payment'].notna() & (df['Days_to_Payment'] >= 0)]
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'Amount (Transaction Total)' in df.columns:
            total_invoiced = df['Amount (Transaction Total)'].sum()
        elif 'Amount' in df.columns:
            total_invoiced = df['Amount'].sum()
        else:
            total_invoiced = 0
        st.metric("Total Invoiced", f"${total_invoiced:,.2f}")
    
    with col2:
        if 'Amount Remaining' in df.columns:
            outstanding = df['Amount Remaining'].sum()
            st.metric("Outstanding Balance", f"${outstanding:,.2f}")
        else:
            st.metric("Outstanding Balance", "N/A")
    
    with col3:
        if 'Days_to_Payment' in df.columns and len(df) > 0:
            avg_days = df['Days_to_Payment'].mean()
            st.metric("Avg Days to Pay", f"{avg_days:.1f}")
        else:
            st.metric("Avg Days to Pay", "N/A")
    
    with col4:
        if 'Amount Remaining' in df.columns and total_invoiced > 0:
            collection_rate = ((total_invoiced - outstanding) / total_invoiced) * 100
            st.metric("Collection Rate", f"{collection_rate:.1f}%")
        else:
            st.metric("Collection Rate", "N/A")
    
    st.markdown("---")
    
    # Payment timeline distribution
    if 'Days_to_Payment' in df.columns and len(df) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            fig_hist = px.histogram(
                df,
                x='Days_to_Payment',
                nbins=30,
                title="Payment Timeline Distribution",
                labels={'Days_to_Payment': 'Days to Payment', 'count': 'Number of Invoices'}
            )
            fig_hist.update_layout(height=350)
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            # Payment buckets
            def payment_bucket(days):
                if days <= 30:
                    return '0-30 days'
                elif days <= 60:
                    return '31-60 days'
                elif days <= 90:
                    return '61-90 days'
                else:
                    return '90+ days'
            
            df['Payment_Bucket'] = df['Days_to_Payment'].apply(payment_bucket)
            bucket_counts = df['Payment_Bucket'].value_counts()
            
            fig_pie = px.pie(
                values=bucket_counts.values,
                names=bucket_counts.index,
                title="Payment Timing Breakdown",
                color_discrete_sequence=['#2ecc71', '#f1c40f', '#e67e22', '#e74c3c']
            )
            fig_pie.update_layout(height=350)
            st.plotly_chart(fig_pie, use_container_width=True)
    
    # Monthly payment trend
    if 'Date' in df.columns and 'Amount' in df.columns:
        df['Month'] = pd.to_datetime(df['Date']).dt.to_period('M').astype(str)
        monthly_payments = df.groupby('Month')['Amount'].sum().reset_index()
        monthly_payments = monthly_payments.sort_values('Month')
        
        fig_trend = px.bar(
            monthly_payments,
            x='Month',
            y='Amount',
            title="Monthly Invoice Amounts"
        )
        fig_trend.update_layout(height=350)
        fig_trend.update_xaxes(tickangle=-45)
        
        st.plotly_chart(fig_trend, use_container_width=True)


def render_sku_forecast(df: pd.DataFrame, horizon: int, model: str, selected_sku: str):
    """Render the SKU-level forecast section."""
    
    st.markdown("### 🔮 SKU Demand Forecast")
    
    if df.empty:
        st.info("No data available for forecasting.")
        return
    
    # Prepare demand history
    date_col = 'Date'
    qty_col = 'Quantity'
    
    if date_col not in df.columns or qty_col not in df.columns:
        st.warning("Required columns (Date, Quantity) not found.")
        return
    
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col, qty_col])
    
    # Aggregate to monthly
    df['Period'] = df[date_col].dt.to_period('M').dt.to_timestamp()
    
    if selected_sku != "All" and 'Item' in df.columns:
        # Single SKU forecast
        monthly_demand = df.groupby('Period')[qty_col].sum()
        
        if len(monthly_demand) < 6:
            st.warning("Insufficient history for forecasting (need at least 6 months).")
            return
        
        # Generate forecast
        try:
            result = generate_forecast(
                monthly_demand,
                model=model,
                horizon=horizon
            )
            
            render_forecast_chart(monthly_demand, result, selected_sku)
            render_forecast_metrics(result)
            
        except Exception as e:
            st.error(f"Forecast generation failed: {str(e)}")
    
    else:
        # Multi-SKU view
        if 'Item' not in df.columns:
            st.warning("Item column not found for SKU-level analysis.")
            return
        
        # Get top SKUs by volume
        top_skus = df.groupby('Item')[qty_col].sum().nlargest(5).index.tolist()
        
        st.markdown("#### Top 5 SKUs Forecast Summary")
        
        forecast_results = {}
        
        for sku in top_skus:
            sku_data = df[df['Item'] == sku]
            monthly_demand = sku_data.groupby('Period')[qty_col].sum()
            
            if len(monthly_demand) >= 6:
                try:
                    result = generate_forecast(monthly_demand, model=model, horizon=horizon)
                    forecast_results[sku] = {
                        'history': monthly_demand,
                        'forecast': result
                    }
                except Exception:
                    continue
        
        if forecast_results:
            # Summary chart
            fig = go.Figure()
            
            for sku, data in forecast_results.items():
                # Historical
                fig.add_trace(go.Scatter(
                    x=data['history'].index,
                    y=data['history'].values,
                    mode='lines',
                    name=f'{sku} (Historical)',
                    line=dict(width=2)
                ))
                
                # Forecast
                fig.add_trace(go.Scatter(
                    x=data['forecast'].forecast.index,
                    y=data['forecast'].forecast.values,
                    mode='lines',
                    name=f'{sku} (Forecast)',
                    line=dict(dash='dash', width=2)
                ))
            
            fig.update_layout(
                title="Top SKUs: Historical vs Forecast",
                xaxis_title="Period",
                yaxis_title="Quantity",
                height=500,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Forecast summary table
            summary_data = []
            for sku, data in forecast_results.items():
                fc = data['forecast']
                summary_data.append({
                    'SKU': sku,
                    'Last 3M Avg': data['history'].tail(3).mean(),
                    'Next 3M Forecast': fc.forecast.head(3).sum(),
                    'Next 6M Forecast': fc.forecast.head(6).sum() if len(fc.forecast) >= 6 else fc.forecast.sum(),
                    'MAPE': fc.metrics.get('MAPE', 'N/A')
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df['Last 3M Avg'] = summary_df['Last 3M Avg'].apply(lambda x: f"{x:,.0f}")
            summary_df['Next 3M Forecast'] = summary_df['Next 3M Forecast'].apply(lambda x: f"{x:,.0f}")
            summary_df['Next 6M Forecast'] = summary_df['Next 6M Forecast'].apply(lambda x: f"{x:,.0f}")
            if 'MAPE' in summary_df.columns:
                summary_df['MAPE'] = summary_df['MAPE'].apply(
                    lambda x: f"{x:.1f}%" if isinstance(x, (int, float)) else x
                )
            
            st.dataframe(summary_df, use_container_width=True, hide_index=True)


def render_forecast_chart(history: pd.Series, result: ForecastResult, title_suffix: str = ""):
    """Render a forecast chart with confidence intervals."""
    
    fig = go.Figure()
    
    # Historical data
    fig.add_trace(go.Scatter(
        x=history.index,
        y=history.values,
        mode='lines+markers',
        name='Historical',
        line=dict(color='#3498db', width=2),
        marker=dict(size=6)
    ))
    
    # Forecast
    fig.add_trace(go.Scatter(
        x=result.forecast.index,
        y=result.forecast.values,
        mode='lines+markers',
        name='Forecast',
        line=dict(color='#e74c3c', width=2, dash='dash'),
        marker=dict(size=6)
    ))
    
    # Confidence interval
    if result.confidence_lower is not None and result.confidence_upper is not None:
        fig.add_trace(go.Scatter(
            x=list(result.forecast.index) + list(result.forecast.index[::-1]),
            y=list(result.confidence_upper.values) + list(result.confidence_lower.values[::-1]),
            fill='toself',
            fillcolor='rgba(231, 76, 60, 0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='95% Confidence Interval',
            showlegend=True
        ))
    
    title = f"Demand Forecast: {title_suffix}" if title_suffix else "Demand Forecast"
    
    fig.update_layout(
        title=title,
        xaxis_title="Period",
        yaxis_title="Quantity",
        height=450,
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_forecast_metrics(result: ForecastResult):
    """Render forecast accuracy metrics."""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        mape = result.metrics.get('MAPE')
        st.metric(
            "MAPE",
            f"{mape:.1f}%" if mape else "N/A",
            help="Mean Absolute Percentage Error (lower is better)"
        )
    
    with col2:
        rmse = result.metrics.get('RMSE')
        st.metric(
            "RMSE",
            f"{rmse:,.1f}" if rmse else "N/A",
            help="Root Mean Square Error"
        )
    
    with col3:
        st.metric("Model", result.model_name)
    
    with col4:
        total_forecast = result.forecast.sum()
        st.metric("Total Forecast", f"{total_forecast:,.0f}")
    
    # Feature importance for ML models
    if result.feature_importance is not None and not result.feature_importance.empty:
        with st.expander("📊 Feature Importance"):
            fig = px.bar(
                result.feature_importance.head(10),
                x='Importance',
                y='Feature',
                orientation='h',
                title="Top 10 Features"
            )
            fig.update_layout(height=300, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)


def render_quarterly_recommendations(df: pd.DataFrame, horizon: int, model: str):
    """Render quarterly recommendations section."""
    
    st.markdown("### 📋 Quarterly Recommendations")
    
    if df.empty:
        st.info("No data available for recommendations.")
        return
    
    # Ensure required columns
    date_col = 'Date'
    qty_col = 'Quantity'
    
    if date_col not in df.columns or qty_col not in df.columns:
        st.warning("Required columns not found.")
        return
    
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col, qty_col])
    
    # Aggregate to monthly
    df['Period'] = df[date_col].dt.to_period('M').dt.to_timestamp()
    monthly_demand = df.groupby('Period')[qty_col].sum()
    
    if len(monthly_demand) < 6:
        st.warning("Insufficient history for quarterly recommendations.")
        return
    
    # Generate forecast
    try:
        result = generate_forecast(monthly_demand, model=model, horizon=max(horizon, 12))
    except Exception as e:
        st.error(f"Forecast failed: {str(e)}")
        return
    
    # Group forecast by quarter
    forecast_df = result.to_dataframe()
    forecast_df['Quarter'] = pd.to_datetime(forecast_df['Period']).dt.to_period('Q').astype(str)
    
    quarterly_forecast = forecast_df.groupby('Quarter').agg({
        'Forecast': 'sum',
        'Lower_CI': 'sum' if 'Lower_CI' in forecast_df.columns else 'first',
        'Upper_CI': 'sum' if 'Upper_CI' in forecast_df.columns else 'first'
    }).reset_index()
    
    # Historical quarterly for comparison
    df['Quarter'] = df[date_col].dt.to_period('Q').astype(str)
    historical_quarterly = df.groupby('Quarter')[qty_col].sum().reset_index()
    historical_quarterly.columns = ['Quarter', 'Historical']
    
    # Get same quarters from previous year for YoY comparison
    current_year = datetime.now().year
    
    # Display quarterly cards
    st.markdown("#### Quarterly Forecast Summary")
    
    quarters = quarterly_forecast['Quarter'].head(4).tolist()
    cols = st.columns(len(quarters))
    
    for i, quarter in enumerate(quarters):
        with cols[i]:
            fc = quarterly_forecast[quarterly_forecast['Quarter'] == quarter]
            forecast_val = fc['Forecast'].values[0] if len(fc) > 0 else 0
            
            # Find same quarter last year
            quarter_num = quarter.split('Q')[1][0]
            last_year_quarter = f"{current_year - 1}Q{quarter_num}"
            last_year = historical_quarterly[historical_quarterly['Quarter'] == last_year_quarter]
            last_year_val = last_year['Historical'].values[0] if len(last_year) > 0 else None
            
            if last_year_val and last_year_val > 0:
                yoy_change = ((forecast_val - last_year_val) / last_year_val) * 100
                delta = f"{yoy_change:+.1f}% YoY"
            else:
                delta = None
            
            st.metric(
                quarter,
                f"{forecast_val:,.0f} units",
                delta=delta
            )
    
    st.markdown("---")
    
    # Recommendations based on forecast
    st.markdown("#### 📝 Recommended Actions")
    
    # Analyze trends
    if len(quarterly_forecast) >= 2:
        q1_forecast = quarterly_forecast.iloc[0]['Forecast']
        q2_forecast = quarterly_forecast.iloc[1]['Forecast']
        trend = "increasing" if q2_forecast > q1_forecast else "decreasing"
        trend_pct = abs((q2_forecast - q1_forecast) / q1_forecast * 100) if q1_forecast > 0 else 0
        
        recommendations = []
        
        if trend == "increasing" and trend_pct > 10:
            recommendations.append("📈 **Demand Growth**: Consider increasing inventory levels and reviewing supplier capacity")
        elif trend == "decreasing" and trend_pct > 10:
            recommendations.append("📉 **Demand Decline**: Monitor closely and adjust procurement accordingly")
        
        # High volume quarters
        max_quarter = quarterly_forecast.loc[quarterly_forecast['Forecast'].idxmax()]
        recommendations.append(f"🔝 **Peak Quarter**: {max_quarter['Quarter']} with {max_quarter['Forecast']:,.0f} units forecasted")
        
        # Seasonality check
        if 'Item' in df.columns:
            item_count = df['Item'].nunique()
            recommendations.append(f"📦 **SKU Diversity**: {item_count} unique SKUs in selection")
        
        for rec in recommendations:
            st.markdown(rec)
    
    # Quarterly comparison chart
    st.markdown("#### Historical vs Forecast by Quarter")
    
    # Combine historical and forecast
    historical_quarterly['Type'] = 'Historical'
    quarterly_forecast_plot = quarterly_forecast[['Quarter', 'Forecast']].copy()
    quarterly_forecast_plot.columns = ['Quarter', 'Quantity']
    quarterly_forecast_plot['Type'] = 'Forecast'
    historical_quarterly = historical_quarterly.rename(columns={'Historical': 'Quantity'})
    
    combined = pd.concat([historical_quarterly, quarterly_forecast_plot])
    combined = combined.sort_values('Quarter')
    
    fig = px.bar(
        combined,
        x='Quarter',
        y='Quantity',
        color='Type',
        barmode='group',
        title="Quarterly Demand: Historical vs Forecast",
        color_discrete_map={'Historical': '#3498db', 'Forecast': '#e74c3c'}
    )
    fig.update_layout(height=400)
    fig.update_xaxes(tickangle=-45)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Export forecast
    with st.expander("📥 Export Forecast Data"):
        export_df = quarterly_forecast.copy()
        export_df['Forecast'] = export_df['Forecast'].round(0)
        
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="Download Quarterly Forecast (CSV)",
            data=csv,
            file_name="quarterly_forecast.csv",
            mime="text/csv"
        )
