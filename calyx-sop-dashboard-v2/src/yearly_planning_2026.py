"""
QBR (Quarterly Business Review) Generator
Generates customer-specific QBR reports for sales rep meetings

Data Sources:
- _NS_SalesOrders_Data: Pending orders, order cadence, OT%, order type mix
- _NS_Invoices_Data: Revenue history, open invoices, aging
- All Reps All Pipelines: Active HubSpot pipeline deals
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from google.oauth2 import service_account
from googleapiclient.discovery import build
import base64
import io
import re

# ========== CONFIGURATION ==========
DEFAULT_SPREADSHEET_ID = "15JhBZ_7aHHZA1W1qsoC2163borL6RYjk0xTDWPmWPfA"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
CACHE_VERSION = "v1_qbr_generator"


# ========== PDF/HTML GENERATION HELPERS ==========

# Note: Chart export to static images requires kaleido package
# Install with: pip install -U kaleido
# If kaleido isn't available, charts will be embedded as interactive Plotly HTML
KALEIDO_AVAILABLE = True
KALEIDO_ERROR = None
try:
    import kaleido
    # Test that it actually works
    test_fig = go.Figure()
    test_fig.add_trace(go.Scatter(x=[1], y=[1]))
    test_bytes = test_fig.to_image(format="png", width=100, height=100)
    if not test_bytes:
        KALEIDO_AVAILABLE = False
        KALEIDO_ERROR = "to_image returned empty"
except Exception as e:
    KALEIDO_AVAILABLE = False
    KALEIDO_ERROR = str(e)


def fig_to_base64(fig, width=700, height=350):
    """Convert a plotly figure to base64 PNG for embedding in HTML"""
    if not KALEIDO_AVAILABLE:
        return None
    try:
        img_bytes = fig.to_image(format="png", width=width, height=height, scale=2)
        return base64.b64encode(img_bytes).decode()
    except Exception as e:
        # Log the error for debugging
        print(f"Chart export error: {e}")
        return None


def fig_to_html_embed(fig, height=400):
    """Convert a plotly figure to embedded HTML (fallback when kaleido unavailable)"""
    try:
        return fig.to_html(
            include_plotlyjs='cdn',
            full_html=False,
            config={'displayModeBar': False, 'staticPlot': True},
            default_height=height
        )
    except Exception as e:
        return None


def create_monthly_revenue_chart(customer_invoices):
    """Create monthly revenue bar chart for PDF export"""
    if customer_invoices.empty or 'Date' not in customer_invoices.columns:
        return None
    
    invoices = customer_invoices.copy()
    invoices['Year'] = invoices['Date'].dt.year
    current_year = datetime.now().year
    recent = invoices[invoices['Year'] >= current_year - 1].copy()
    
    if recent.empty or len(recent) < 2:
        return None
    
    recent['Month'] = recent['Date'].dt.to_period('M').astype(str)
    monthly = recent.groupby('Month')['Amount'].sum().reset_index()
    
    fig = go.Figure(data=[
        go.Bar(
            x=monthly['Month'],
            y=monthly['Amount'],
            marker=dict(color='#3b82f6'),
            text=[f'${x:,.0f}' for x in monthly['Amount']],
            textposition='outside',
            textfont=dict(size=10),
            cliponaxis=False
        )
    ])
    
    # Calculate y-axis max to give room for labels
    max_val = monthly['Amount'].max()
    y_max = max_val * 1.15  # Add 15% headroom
    
    fig.update_layout(
        title=dict(text='Monthly Purchase Trend', font=dict(size=16, color='#1e293b')),
        xaxis_title='',
        yaxis_title='Purchases',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#1e293b', size=11),
        xaxis=dict(tickangle=-45, gridcolor='#e2e8f0'),
        yaxis=dict(gridcolor='#e2e8f0', tickformat='$,.0f', range=[0, y_max]),
        margin=dict(t=60, b=80, l=80, r=40),
        showlegend=False
    )
    
    return fig


def create_ontime_chart(customer_orders):
    """Create on-time performance chart for PDF export"""
    if customer_orders.empty:
        return None
    
    promise_col = 'Customer Promise Date' if 'Customer Promise Date' in customer_orders.columns else 'Customer Promise Last Date to Ship'
    if promise_col not in customer_orders.columns:
        return None
    
    completed = customer_orders[
        (customer_orders['Status'].isin(['Billed', 'Closed'])) &
        (customer_orders['Actual Ship Date'].notna()) &
        (customer_orders[promise_col].notna())
    ].copy()
    
    if completed.empty or len(completed) < 3:
        return None
    
    completed['Variance'] = (completed['Actual Ship Date'] - completed[promise_col]).dt.days
    
    # Create colored histogram
    early = completed[completed['Variance'] < 0]['Variance']
    on_time = completed[completed['Variance'] == 0]['Variance']
    late = completed[completed['Variance'] > 0]['Variance']
    
    fig = go.Figure()
    if len(early) > 0:
        fig.add_trace(go.Histogram(x=early, name='Early', marker_color='#10b981', opacity=0.8))
    if len(on_time) > 0:
        fig.add_trace(go.Histogram(x=on_time, name='On Time', marker_color='#3b82f6', opacity=0.8))
    if len(late) > 0:
        fig.add_trace(go.Histogram(x=late, name='Late', marker_color='#ef4444', opacity=0.8))
    
    fig.add_vline(x=0, line_dash="dash", line_color="#22c55e", line_width=2)
    
    fig.update_layout(
        title=dict(text='Delivery Timing Distribution', font=dict(size=16, color='#1e293b')),
        xaxis_title='Days (Negative = Early, Positive = Late)',
        yaxis_title='Orders',
        barmode='stack',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#1e293b', size=11),
        xaxis=dict(gridcolor='#e2e8f0'),
        yaxis=dict(gridcolor='#e2e8f0'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        margin=dict(t=70, b=50, l=60, r=40)
    )
    
    return fig


def create_order_type_chart(customer_orders):
    """Create order type mix pie chart for PDF export"""
    if customer_orders.empty or 'Order Type' not in customer_orders.columns:
        return None
    
    valid = customer_orders[
        (customer_orders['Order Type'].notna()) &
        (customer_orders['Order Type'] != '') &
        (customer_orders['Order Type'] != 'nan')
    ]
    
    if valid.empty:
        return None
    
    type_mix = valid.groupby('Order Type')['Amount'].sum().reset_index()
    type_mix = type_mix.sort_values('Amount', ascending=False)
    
    colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4', '#ec4899', '#84cc16']
    
    fig = go.Figure(data=[go.Pie(
        labels=type_mix['Order Type'],
        values=type_mix['Amount'],
        hole=0.4,
        marker=dict(colors=colors[:len(type_mix)]),
        textposition='inside',
        textinfo='percent+label',
        textfont=dict(size=10, color='white'),
        hovertemplate='<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title=dict(text='Product Mix', font=dict(size=16, color='#1e293b')),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#1e293b'),
        showlegend=True,
        legend=dict(orientation='h', yanchor='top', y=-0.1, xanchor='center', x=0.5, font=dict(size=10)),
        margin=dict(t=50, b=80, l=20, r=20)
    )
    
    return fig


def create_pipeline_chart(customer_deals):
    """Create pipeline breakdown chart for PDF export"""
    if customer_deals.empty:
        return None
    
    open_statuses = ['Expect', 'Commit', 'Best Case', 'Opportunity']
    open_deals = customer_deals[customer_deals['Close Status'].isin(open_statuses)]
    
    if open_deals.empty:
        return None
    
    status_data = open_deals.groupby('Close Status')['Amount'].sum().reset_index()
    
    # Order by pipeline stage
    status_order = {'Commit': 0, 'Expect': 1, 'Best Case': 2, 'Opportunity': 3}
    status_data['Order'] = status_data['Close Status'].map(status_order).fillna(4)
    status_data = status_data.sort_values('Order')
    
    colors = {'Commit': '#10b981', 'Expect': '#3b82f6', 'Best Case': '#f59e0b', 'Opportunity': '#8b5cf6'}
    bar_colors = [colors.get(s, '#64748b') for s in status_data['Close Status']]
    
    fig = go.Figure(data=[
        go.Bar(
            x=status_data['Close Status'],
            y=status_data['Amount'],
            marker=dict(color=bar_colors),
            text=[f'${x:,.0f}' for x in status_data['Amount']],
            textposition='outside',
            textfont=dict(size=11),
            cliponaxis=False
        )
    ])
    
    # Calculate y-axis max to give room for labels
    max_val = status_data['Amount'].max()
    y_max = max_val * 1.15  # Add 15% headroom
    
    fig.update_layout(
        title=dict(text='Upcoming Orders by Status', font=dict(size=16, color='#1e293b')),
        xaxis_title='',
        yaxis_title='Value',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#1e293b', size=11),
        xaxis=dict(gridcolor='#e2e8f0'),
        yaxis=dict(gridcolor='#e2e8f0', tickformat='$,.0f', range=[0, y_max]),
        margin=dict(t=60, b=50, l=80, r=40),
        showlegend=False
    )
    
    return fig


def generate_qbr_html(customer_name, rep_name, customer_orders, customer_invoices, customer_deals):
    """Generate a clean HTML report for PDF export with charts"""
    
    generated_date = datetime.now().strftime('%B %d, %Y')
    
    # ===== Generate Charts =====
    charts_html = {}
    charts_generated = 0
    
    def embed_chart(fig, chart_key):
        """Try to embed chart as image, fall back to interactive HTML"""
        nonlocal charts_generated
        if fig is None:
            return
        
        # First try static image (best for PDF)
        img_b64 = fig_to_base64(fig)
        if img_b64:
            charts_html[chart_key] = f'<div class="chart-container"><img src="data:image/png;base64,{img_b64}"></div>'
            charts_generated += 1
            return
        
        # Fall back to interactive HTML embed
        html_embed = fig_to_html_embed(fig)
        if html_embed:
            charts_html[chart_key] = f'<div class="chart-container">{html_embed}</div>'
            charts_generated += 1
    
    # Monthly Revenue Chart
    revenue_fig = create_monthly_revenue_chart(customer_invoices)
    embed_chart(revenue_fig, 'revenue')
    
    # On-Time Performance Chart
    ontime_fig = create_ontime_chart(customer_orders)
    embed_chart(ontime_fig, 'ontime')
    
    # Order Type Mix Chart
    ordertype_fig = create_order_type_chart(customer_orders)
    embed_chart(ordertype_fig, 'ordertype')
    
    # Pipeline Chart
    pipeline_fig = create_pipeline_chart(customer_deals)
    embed_chart(pipeline_fig, 'pipeline')
    
    # ===== Calculate all metrics =====
    
    # Pending Orders
    pending_statuses = ['Pending Approval', 'Pending Fulfillment', 'PA', 'PF']
    pending_orders = pd.DataFrame()
    if not customer_orders.empty:
        try:
            if 'Updated Status' in customer_orders.columns:
                pending_orders = customer_orders[
                    customer_orders['Updated Status'].isin(pending_statuses) | 
                    customer_orders['Status'].isin(['Pending Approval', 'Pending Fulfillment'])
                ]
            elif 'Status' in customer_orders.columns:
                pending_orders = customer_orders[
                    customer_orders['Status'].isin(['Pending Approval', 'Pending Fulfillment'])
                ]
        except Exception:
            pending_orders = pd.DataFrame()
    
    pending_count = len(pending_orders)
    pending_value = pending_orders['Amount'].sum() if not pending_orders.empty else 0
    
    # Pending Orders Detail Table
    pending_orders_html = ""
    if not pending_orders.empty:
        # Group by status first
        status_col = 'Updated Status' if 'Updated Status' in pending_orders.columns else 'Status'
        status_summary = pending_orders.groupby(status_col).agg({
            'Amount': ['sum', 'count']
        }).round(0)
        status_summary.columns = ['Value', 'Count']
        status_summary = status_summary.sort_values('Value', ascending=False)
        
        status_rows = ""
        for status, row in status_summary.iterrows():
            status_rows += f"<tr><td>{status}</td><td>${row['Value']:,.0f}</td><td>{int(row['Count'])}</td></tr>"
        
        pending_status_html = f"""
        <h4 style="color: #475569; margin: 20px 0 10px 0;">By Status</h4>
        <table class="data-table">
            <thead><tr><th>Status</th><th>Value</th><th>Orders</th></tr></thead>
            <tbody>{status_rows}</tbody>
        </table>
        """
        
        # Individual order details
        order_rows = ""
        for _, order in pending_orders.sort_values('Amount', ascending=False).iterrows():
            so_num = order.get('SO Number', 'N/A')
            order_type = order.get('Order Type', 'N/A')
            amount = order.get('Amount', 0)
            order_date = order.get('Order Start Date')
            if pd.notna(order_date):
                order_date = order_date.strftime('%Y-%m-%d')
            else:
                order_date = 'N/A'
            status = order.get(status_col, 'N/A')
            order_rows += f"<tr><td>{so_num}</td><td>{order_type}</td><td>${amount:,.0f}</td><td>{order_date}</td><td>{status}</td></tr>"
        
        pending_detail_html = f"""
        <h4 style="color: #475569; margin: 20px 0 10px 0;">Order Details</h4>
        <table class="data-table">
            <thead><tr><th>SO #</th><th>Order Type</th><th>Amount</th><th>Order Date</th><th>Status</th></tr></thead>
            <tbody>{order_rows}</tbody>
        </table>
        """
        
        pending_orders_html = pending_status_html + pending_detail_html
    
    # Open Invoices
    open_invoices = customer_invoices[customer_invoices['Status'] == 'Open'] if not customer_invoices.empty else pd.DataFrame()
    open_invoice_count = len(open_invoices)
    open_invoice_value = open_invoices['Amount Remaining'].sum() if not open_invoices.empty and 'Amount Remaining' in open_invoices.columns else 0
    
    # Open Invoices Detail Table with Aging
    open_invoices_html = ""
    if not open_invoices.empty and 'Due Date' in open_invoices.columns:
        today = pd.Timestamp.now()
        open_inv = open_invoices.copy()
        open_inv['Days Overdue'] = (today - open_inv['Due Date']).dt.days
        
        # Aging buckets
        def aging_bucket(days):
            if days <= 0: return 'Current'
            elif days <= 30: return '1-30 Days'
            elif days <= 60: return '31-60 Days'
            elif days <= 90: return '61-90 Days'
            else: return '90+ Days'
        
        open_inv['Aging'] = open_inv['Days Overdue'].apply(aging_bucket)
        
        # Aging summary
        aging_summary = open_inv.groupby('Aging')['Amount Remaining'].sum()
        bucket_order = ['Current', '1-30 Days', '31-60 Days', '61-90 Days', '90+ Days']
        
        aging_rows = ""
        for bucket in bucket_order:
            if bucket in aging_summary.index:
                amt = aging_summary[bucket]
                style = 'color: #ef4444; font-weight: 600;' if bucket == '90+ Days' else ''
                aging_rows += f"<tr><td>{bucket}</td><td style='{style}'>${amt:,.0f}</td></tr>"
        
        aging_html = f"""
        <h4 style="color: #475569; margin: 20px 0 10px 0;">Aging Summary</h4>
        <table class="data-table">
            <thead><tr><th>Aging Bucket</th><th>Amount</th></tr></thead>
            <tbody>{aging_rows}</tbody>
        </table>
        """
        
        # Individual invoice details
        invoice_rows = ""
        for _, inv in open_inv.sort_values('Days Overdue', ascending=False).iterrows():
            doc_num = inv.get('Document Number', 'N/A')
            amount = inv.get('Amount Remaining', 0)
            due_date = inv.get('Due Date')
            if pd.notna(due_date):
                due_date = due_date.strftime('%Y-%m-%d')
            else:
                due_date = 'N/A'
            days_over = inv.get('Days Overdue', 0)
            aging = inv.get('Aging', 'N/A')
            style = 'color: #ef4444;' if days_over > 90 else 'color: #f59e0b;' if days_over > 30 else ''
            invoice_rows += f"<tr><td>{doc_num}</td><td>${amount:,.0f}</td><td>{due_date}</td><td style='{style}'>{days_over:.0f}</td><td>{aging}</td></tr>"
        
        invoice_detail_html = f"""
        <h4 style="color: #475569; margin: 20px 0 10px 0;">Invoice Details</h4>
        <table class="data-table">
            <thead><tr><th>Invoice #</th><th>Amount</th><th>Due Date</th><th>Days Overdue</th><th>Aging</th></tr></thead>
            <tbody>{invoice_rows}</tbody>
        </table>
        """
        
        open_invoices_html = aging_html + invoice_detail_html
    
    # Revenue
    total_revenue = customer_invoices['Amount'].sum() if not customer_invoices.empty else 0
    total_invoices = len(customer_invoices)
    avg_invoice = total_revenue / total_invoices if total_invoices > 0 else 0
    
    # Year breakdown
    yearly_html = ""
    if not customer_invoices.empty and 'Date' in customer_invoices.columns:
        invoices_copy = customer_invoices.copy()
        invoices_copy['Year'] = invoices_copy['Date'].dt.year
        yearly_data = invoices_copy.groupby('Year').agg({'Amount': 'sum', 'Document Number': 'count'}).reset_index()
        yearly_data.columns = ['Year', 'Revenue', 'Invoices']
        yearly_data = yearly_data.sort_values('Year', ascending=False)
        
        yearly_rows = ""
        for _, row in yearly_data.iterrows():
            yearly_rows += f"<tr><td>{int(row['Year'])}</td><td>${row['Revenue']:,.0f}</td><td>{int(row['Invoices'])}</td></tr>"
        
        yearly_html = f"""
        <table class="data-table">
            <thead><tr><th>Year</th><th>Purchases</th><th>Orders</th></tr></thead>
            <tbody>{yearly_rows}</tbody>
        </table>
        """
    
    # On-Time Performance
    promise_col = 'Customer Promise Date' if 'Customer Promise Date' in customer_orders.columns else 'Customer Promise Last Date to Ship'
    if promise_col in customer_orders.columns:
        completed = customer_orders[
            (customer_orders['Status'].isin(['Billed', 'Closed'])) &
            (customer_orders['Actual Ship Date'].notna()) &
            (customer_orders[promise_col].notna())
        ].copy()
        if not completed.empty:
            completed['Variance'] = (completed['Actual Ship Date'] - completed[promise_col]).dt.days
            ot_count = (completed['Variance'] <= 0).sum()
            ot_rate = (ot_count / len(completed) * 100) if len(completed) > 0 else 0
            avg_variance = completed['Variance'].mean()
        else:
            ot_rate, avg_variance = 0, 0
    else:
        ot_rate, avg_variance = 0, 0
    
    # Order Cadence
    if not customer_orders.empty and 'Order Start Date' in customer_orders.columns:
        orders_dated = customer_orders[customer_orders['Order Start Date'].notna()].sort_values('Order Start Date')
        if len(orders_dated) > 1:
            orders_dated['Days Between'] = orders_dated['Order Start Date'].diff().dt.days
            avg_cadence = orders_dated['Days Between'].mean()
            last_order = orders_dated['Order Start Date'].max().strftime('%Y-%m-%d')
        else:
            avg_cadence = 0
            last_order = orders_dated['Order Start Date'].max().strftime('%Y-%m-%d') if len(orders_dated) == 1 else 'N/A'
    else:
        avg_cadence = 0
        last_order = 'N/A'
    
    # Order Type Mix
    order_type_html = ""
    if not customer_orders.empty and 'Order Type' in customer_orders.columns:
        valid_orders = customer_orders[
            (customer_orders['Order Type'].notna()) & 
            (customer_orders['Order Type'] != '') & 
            (customer_orders['Order Type'] != 'nan')
        ]
        if not valid_orders.empty:
            type_mix = valid_orders.groupby('Order Type').agg({'Amount': ['sum', 'count']}).round(0)
            type_mix.columns = ['Value', 'Count']
            type_mix = type_mix.sort_values('Value', ascending=False)
            total_val = type_mix['Value'].sum()
            
            type_rows = ""
            for order_type, row in type_mix.iterrows():
                pct = (row['Value'] / total_val * 100) if total_val > 0 else 0
                type_rows += f"<tr><td>{order_type}</td><td>${row['Value']:,.0f}</td><td>{int(row['Count'])}</td><td>{pct:.1f}%</td></tr>"
            
            order_type_html = f"""
            <table class="data-table">
                <thead><tr><th>Product Category</th><th>Value</th><th>Orders</th><th>% of Total</th></tr></thead>
                <tbody>{type_rows}</tbody>
            </table>
            """
    
    # Pipeline
    pipeline_html = ""
    if not customer_deals.empty:
        open_statuses = ['Expect', 'Commit', 'Best Case', 'Opportunity']
        open_deals = customer_deals[customer_deals['Close Status'].isin(open_statuses)]
        if not open_deals.empty:
            pipeline_value = open_deals['Amount'].sum()
            pipeline_count = len(open_deals)
            
            deal_rows = ""
            for _, deal in open_deals.iterrows():
                close_date = deal['Close Date'].strftime('%Y-%m-%d') if pd.notna(deal['Close Date']) else 'TBD'
                deal_rows += f"<tr><td>{deal['Deal Name']}</td><td>${deal['Amount']:,.0f}</td><td>{deal['Close Status']}</td><td>{close_date}</td></tr>"
            
            pipeline_html = f"""
            <div class="metric-row">
                <div class="metric-card">
                    <div class="metric-label">Upcoming Order Value</div>
                    <div class="metric-value">${pipeline_value:,.0f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Planned Orders</div>
                    <div class="metric-value">{pipeline_count}</div>
                </div>
            </div>
            <table class="data-table">
                <thead><tr><th>Order Description</th><th>Amount</th><th>Status</th><th>Expected Date</th></tr></thead>
                <tbody>{deal_rows}</tbody>
            </table>
            """
    
    # ===== Generate HTML =====
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Account Summary - {customer_name}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                background: #ffffff;
                color: #1e293b;
                line-height: 1.6;
                padding: 40px;
            }}
            
            .header {{
                background: linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #0891b2 100%);
                color: white;
                padding: 40px;
                border-radius: 16px;
                margin-bottom: 40px;
            }}
            
            .header h1 {{
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 8px;
            }}
            
            .header .subtitle {{
                font-size: 1rem;
                opacity: 0.9;
            }}
            
            .section {{
                margin-bottom: 40px;
                page-break-inside: avoid;
            }}
            
            .section-title {{
                font-size: 1.4rem;
                font-weight: 600;
                color: #1e40af;
                border-bottom: 3px solid #3b82f6;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            
            .metric-row {{
                display: flex;
                gap: 20px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }}
            
            .metric-card {{
                background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 20px 30px;
                min-width: 180px;
                flex: 1;
            }}
            
            .metric-label {{
                font-size: 0.85rem;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 5px;
            }}
            
            .metric-value {{
                font-size: 1.8rem;
                font-weight: 700;
                color: #1e293b;
            }}
            
            .metric-value.success {{
                color: #059669;
            }}
            
            .metric-value.warning {{
                color: #d97706;
            }}
            
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
                font-size: 0.9rem;
            }}
            
            .data-table th {{
                background: #1e40af;
                color: white;
                padding: 12px 16px;
                text-align: left;
                font-weight: 600;
            }}
            
            .data-table td {{
                padding: 12px 16px;
                border-bottom: 1px solid #e2e8f0;
            }}
            
            .data-table tr:nth-child(even) {{
                background: #f8fafc;
            }}
            
            .data-table tr:hover {{
                background: #eff6ff;
            }}
            
            .highlight-box {{
                background: #eff6ff;
                border-left: 4px solid #3b82f6;
                padding: 15px 20px;
                border-radius: 0 8px 8px 0;
                margin: 15px 0;
            }}
            
            .footer {{
                margin-top: 60px;
                padding-top: 20px;
                border-top: 1px solid #e2e8f0;
                text-align: center;
                color: #64748b;
                font-size: 0.85rem;
            }}
            
            .chart-container {{
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 15px;
                margin: 20px 0;
                text-align: center;
            }}
            
            .chart-container img {{
                max-width: 100%;
                height: auto;
                border-radius: 8px;
            }}
            
            @media print {{
                body {{
                    padding: 20px;
                }}
                .header {{
                    -webkit-print-color-adjust: exact;
                    print-color-adjust: exact;
                }}
                .section {{
                    page-break-inside: avoid;
                }}
                .chart-container {{
                    page-break-inside: avoid;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📋 Account Summary</h1>
            <div class="subtitle">{customer_name} &nbsp;|&nbsp; Account Manager: {rep_name} &nbsp;|&nbsp; {generated_date}</div>
        </div>
        
        <div class="section">
            <div class="section-title">📦 Orders in Progress</div>
            <div class="metric-row">
                <div class="metric-card">
                    <div class="metric-label">Active Orders</div>
                    <div class="metric-value">{pending_count}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Order Value</div>
                    <div class="metric-value">${pending_value:,.0f}</div>
                </div>
            </div>
            {pending_orders_html}
        </div>
        
        <div class="section">
            <div class="section-title">💳 Account Balance</div>
            <div class="metric-row">
                <div class="metric-card">
                    <div class="metric-label">Open Invoices</div>
                    <div class="metric-value">{open_invoice_count}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Balance Due</div>
                    <div class="metric-value {'warning' if open_invoice_value > 0 else ''}">${open_invoice_value:,.0f}</div>
                </div>
            </div>
            {open_invoices_html}
        </div>
        
        <div class="section">
            <div class="section-title">💰 Purchase History</div>
            <div class="metric-row">
                <div class="metric-card">
                    <div class="metric-label">Lifetime Purchases</div>
                    <div class="metric-value success">${total_revenue:,.0f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total Orders</div>
                    <div class="metric-value">{total_invoices}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Avg Order Value</div>
                    <div class="metric-value">${avg_invoice:,.0f}</div>
                </div>
            </div>
            {yearly_html}
            {charts_html.get('revenue', '')}
        </div>
        
        <div class="section">
            <div class="section-title">⏱️ Delivery Performance</div>
            <div class="metric-row">
                <div class="metric-card">
                    <div class="metric-label">On-Time Delivery Rate</div>
                    <div class="metric-value {'success' if ot_rate >= 90 else 'warning' if ot_rate >= 70 else ''}">{ot_rate:.1f}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Avg Delivery Timing</div>
                    <div class="metric-value">{avg_variance:.1f} days</div>
                </div>
            </div>
            {charts_html.get('ontime', '')}
        </div>
        
        <div class="section">
            <div class="section-title">📅 Ordering Frequency</div>
            <div class="metric-row">
                <div class="metric-card">
                    <div class="metric-label">Avg Days Between Orders</div>
                    <div class="metric-value">{avg_cadence:.0f} days</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Most Recent Order</div>
                    <div class="metric-value" style="font-size: 1.2rem;">{last_order}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">📊 Product Mix</div>
            {charts_html.get('ordertype', '')}
            {order_type_html if order_type_html else '<p style="color: #64748b;">No product data available.</p>'}
        </div>
        
        <div class="section">
            <div class="section-title">🎯 Upcoming Orders</div>
            {charts_html.get('pipeline', '')}
            {pipeline_html if pipeline_html else '<p style="color: #64748b;">No upcoming orders scheduled.</p>'}
        </div>
        
        <div class="footer">
            <p>Prepared by Calyx Containers &nbsp;|&nbsp; {generated_date}</p>
            <p style="margin-top: 5px;">Thank you for your partnership!</p>
        </div>
    </body>
    </html>
    """
    
    return html


def generate_combined_qbr_html(customers_data, rep_name):
    """
    Generate a combined HTML report for multiple customers.
    customers_data is a list of tuples: (customer_name, customer_orders, customer_invoices, customer_deals)
    """
    generated_date = datetime.now().strftime('%B %d, %Y')
    
    # Start with the common HTML header and styles
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Account Summaries - {rep_name}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                background: #ffffff;
                color: #1e293b;
                line-height: 1.6;
                padding: 40px;
            }}
            
            .header {{
                background: linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #0891b2 100%);
                color: white;
                padding: 40px;
                border-radius: 16px;
                margin-bottom: 40px;
            }}
            
            .header h1 {{
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 8px;
            }}
            
            .header .subtitle {{
                font-size: 1rem;
                opacity: 0.9;
            }}
            
            .section {{
                margin-bottom: 40px;
                page-break-inside: avoid;
            }}
            
            .section-title {{
                font-size: 1.4rem;
                font-weight: 600;
                color: #1e40af;
                border-bottom: 3px solid #3b82f6;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            
            .metric-row {{
                display: flex;
                gap: 20px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }}
            
            .metric-card {{
                background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 20px 30px;
                min-width: 180px;
                flex: 1;
            }}
            
            .metric-label {{
                font-size: 0.85rem;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 5px;
            }}
            
            .metric-value {{
                font-size: 1.8rem;
                font-weight: 700;
                color: #1e293b;
            }}
            
            .metric-value.success {{
                color: #059669;
            }}
            
            .metric-value.warning {{
                color: #d97706;
            }}
            
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
                font-size: 0.9rem;
            }}
            
            .data-table th {{
                background: #1e40af;
                color: white;
                padding: 12px 16px;
                text-align: left;
                font-weight: 600;
            }}
            
            .data-table td {{
                padding: 12px 16px;
                border-bottom: 1px solid #e2e8f0;
            }}
            
            .data-table tr:nth-child(even) {{
                background: #f8fafc;
            }}
            
            .data-table tr:hover {{
                background: #eff6ff;
            }}
            
            .chart-container {{
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 15px;
                margin: 20px 0;
                text-align: center;
            }}
            
            .chart-container img {{
                max-width: 100%;
                height: auto;
                border-radius: 8px;
            }}
            
            .customer-divider {{
                page-break-before: always;
                margin-top: 60px;
                padding-top: 40px;
            }}
            
            .footer {{
                margin-top: 60px;
                padding-top: 20px;
                border-top: 1px solid #e2e8f0;
                text-align: center;
                color: #64748b;
                font-size: 0.85rem;
            }}
            
            @media print {{
                body {{
                    padding: 20px;
                }}
                .header {{
                    -webkit-print-color-adjust: exact;
                    print-color-adjust: exact;
                }}
                .section {{
                    page-break-inside: avoid;
                }}
                .chart-container {{
                    page-break-inside: avoid;
                }}
                .customer-divider {{
                    page-break-before: always;
                }}
            }}
        </style>
    </head>
    <body>
    """
    
    # Generate content for each customer
    for idx, (customer_name, customer_orders, customer_invoices, customer_deals, *_) in enumerate(customers_data):
        # Add page break divider for customers after the first
        if idx > 0:
            html += '<div class="customer-divider"></div>'
        
        # Generate this customer's content by calling the single-customer function
        single_html = generate_qbr_html(customer_name, rep_name, customer_orders, customer_invoices, customer_deals)
        
        # Extract just the body content (between <body> and </body>)
        body_match = re.search(r'<body>(.*?)</body>', single_html, re.DOTALL)
        if body_match:
            body_content = body_match.group(1)
            # Remove the footer from individual reports (we'll add one at the end)
            body_content = re.sub(r'<div class="footer">.*?</div>', '', body_content, flags=re.DOTALL)
            html += body_content
    
    # Add combined footer
    customer_names = ", ".join([c[0] for c in customers_data])
    html += f"""
        <div class="footer">
            <p>Prepared by Calyx Containers &nbsp;|&nbsp; {generated_date}</p>
            <p style="margin-top: 5px;">Accounts: {customer_names}</p>
            <p style="margin-top: 5px;">Thank you for your partnership!</p>
        </div>
    </body>
    </html>
    """
    
    return html


def generate_combined_summary_html(customers_data, rep_name):
    """
    Generate a combined summary HTML report that uses the same format as individual reports.
    Just aggregates the data from all selected customers.
    """
    customer_names = [c[0] for c in customers_data]
    num_customers = len(customers_data)
    
    # Aggregate all data
    all_orders = pd.concat([data[1] for data in customers_data if not data[1].empty], ignore_index=True) if any(not data[1].empty for data in customers_data) else pd.DataFrame()
    all_invoices = pd.concat([data[2] for data in customers_data if not data[2].empty], ignore_index=True) if any(not data[2].empty for data in customers_data) else pd.DataFrame()
    all_deals = pd.concat([data[3] for data in customers_data if not data[3].empty], ignore_index=True) if any(not data[3].empty for data in customers_data) else pd.DataFrame()
    
    # Use the same report generator with a combined customer name
    combined_name = f"Combined Summary ({num_customers} Customers)"
    
    # Generate report using same format as individual reports
    html = generate_qbr_html(combined_name, rep_name, all_orders, all_invoices, all_deals)
    
    # Add a customer list section after the header
    customer_list_html = f"""
        <div style="
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 8px;
            padding: 15px 20px;
            margin-bottom: 30px;
        ">
            <div style="font-weight: 600; color: #059669; margin-bottom: 8px;">Included Accounts ({num_customers}):</div>
            <div style="color: #1e293b;">{', '.join(customer_names)}</div>
        </div>
    """
    
    # Insert customer list after the header div
    html = html.replace('</div>\n        \n        <div class="section">', 
                        f'</div>\n        \n        {customer_list_html}\n        <div class="section">', 1)
    
    return html


# ========== DATA LOADING ==========
@st.cache_data
def load_google_sheets_data(sheet_name, range_name, version=CACHE_VERSION, silent=False):
    """Load data from Google Sheets with caching"""
    try:
        spreadsheet_id = st.secrets.get("SPREADSHEET_ID", DEFAULT_SPREADSHEET_ID)
        
        if "service_account" not in st.secrets:
            if not silent:
                st.error("❌ Missing Google Cloud credentials in Streamlit secrets")
            return pd.DataFrame()
        
        creds_dict = dict(st.secrets["service_account"])
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=SCOPES
        )
        
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!{range_name}"
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            if not silent:
                st.warning(f"⚠️ No data found in {sheet_name}!{range_name}")
            return pd.DataFrame()
        
        # Handle mismatched column counts
        if len(values) > 1:
            max_cols = max(len(row) for row in values)
            for row in values:
                while len(row) < max_cols:
                    row.append('')
        
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
        
    except Exception as e:
        if not silent:
            st.error(f"❌ Error loading data from {sheet_name}: {str(e)}")
        return pd.DataFrame()


def clean_numeric(value):
    """Clean and convert a value to numeric"""
    if pd.isna(value) or str(value).strip() == '':
        return 0
    cleaned = str(value).replace(',', '').replace('$', '').replace(' ', '').strip()
    try:
        return float(cleaned)
    except:
        return 0


def load_qbr_data():
    """Load all data needed for QBR generation"""
    
    # Load Sales Orders (A:AF to include all columns through Updated Status)
    sales_orders_df = load_google_sheets_data("_NS_SalesOrders_Data", "A:AF", version=CACHE_VERSION)
    
    # Load Invoices (A:U to include Rep Master)
    invoices_df = load_google_sheets_data("_NS_Invoices_Data", "A:U", version=CACHE_VERSION)
    
    # Load HubSpot Deals - load wider range to ensure we get Company Name
    deals_df = load_google_sheets_data("All Reps All Pipelines", "A:Z", version=CACHE_VERSION)
    
    # =========================================================================
    # PROCESS SALES ORDERS - use column names directly from sheet
    # =========================================================================
    if not sales_orders_df.empty:
        # Remove duplicate columns
        if sales_orders_df.columns.duplicated().any():
            sales_orders_df = sales_orders_df.loc[:, ~sales_orders_df.columns.duplicated()]
        
        # Handle Amount column - could be 'Amount' or 'Amount (Transaction Total)'
        if 'Amount (Transaction Total)' in sales_orders_df.columns and 'Amount' not in sales_orders_df.columns:
            sales_orders_df = sales_orders_df.rename(columns={'Amount (Transaction Total)': 'Amount'})
        
        # Clean numeric data
        if 'Amount' in sales_orders_df.columns:
            sales_orders_df['Amount'] = sales_orders_df['Amount'].apply(clean_numeric)
        
        # Clean date data
        if 'Order Start Date' in sales_orders_df.columns:
            sales_orders_df['Order Start Date'] = pd.to_datetime(sales_orders_df['Order Start Date'], errors='coerce')
        if 'Actual Ship Date' in sales_orders_df.columns:
            sales_orders_df['Actual Ship Date'] = pd.to_datetime(sales_orders_df['Actual Ship Date'], errors='coerce')
        if 'Customer Promise Date' in sales_orders_df.columns:
            sales_orders_df['Customer Promise Date'] = pd.to_datetime(sales_orders_df['Customer Promise Date'], errors='coerce')
        # Also handle alternate column name
        if 'Customer Promise Last Date to Ship' in sales_orders_df.columns:
            sales_orders_df['Customer Promise Date'] = pd.to_datetime(sales_orders_df['Customer Promise Last Date to Ship'], errors='coerce')
        
        # Clean text fields
        for col in ['Corrected Customer Name', 'Rep Master', 'Updated Status', 'Order Type', 'Status']:
            if col in sales_orders_df.columns:
                sales_orders_df[col] = sales_orders_df[col].astype(str).str.strip()
    
    # =========================================================================
    # PROCESS INVOICES - use column names directly from sheet
    # =========================================================================
    if not invoices_df.empty:
        # Remove duplicate columns
        if invoices_df.columns.duplicated().any():
            invoices_df = invoices_df.loc[:, ~invoices_df.columns.duplicated()]
        
        # Handle Amount column - could be 'Amount' or 'Amount (Transaction Total)'
        if 'Amount (Transaction Total)' in invoices_df.columns and 'Amount' not in invoices_df.columns:
            invoices_df = invoices_df.rename(columns={'Amount (Transaction Total)': 'Amount'})
        
        # Clean numeric data
        if 'Amount' in invoices_df.columns:
            invoices_df['Amount'] = invoices_df['Amount'].apply(clean_numeric)
        if 'Amount Remaining' in invoices_df.columns:
            invoices_df['Amount Remaining'] = invoices_df['Amount Remaining'].apply(clean_numeric)
        
        # Clean date data
        if 'Date' in invoices_df.columns:
            invoices_df['Date'] = pd.to_datetime(invoices_df['Date'], errors='coerce')
        if 'Due Date' in invoices_df.columns:
            invoices_df['Due Date'] = pd.to_datetime(invoices_df['Due Date'], errors='coerce')
        
        # Clean text fields
        for col in ['Corrected Customer', 'Rep Master', 'Status']:
            if col in invoices_df.columns:
                invoices_df[col] = invoices_df[col].astype(str).str.strip()
        
        # Extract SO Number from Created From
        if 'Created From' in invoices_df.columns:
            invoices_df['SO Number'] = invoices_df['Created From'].astype(str).str.replace('Sales Order #', '', regex=False).str.strip()
    
    # =========================================================================
    # PROCESS HUBSPOT DEALS
    # Use actual column names from header row, not positional indices
    # =========================================================================
    if not deals_df.empty:
        # Create a mapping of potential column name variations to standard names
        column_mapping = {
            # Standard name variations
            'Record ID': 'Record ID',
            'Deal Name': 'Deal Name',
            'Deal Stage': 'Deal Stage',
            'Close Date': 'Close Date',
            'Deal Owner First Name': 'Deal Owner First Name',
            'Deal Owner Last Name': 'Deal Owner Last Name',
            'Deal Owner First Name Deal Owner Last Name': 'Deal Owner Combined',
            'Amount': 'Amount',
            'Close Status': 'Close Status',
            'Pipeline': 'Pipeline',
            'Create Date': 'Create Date',
            'Deal Type': 'Deal Type',
            'Netsuite SO#': 'Netsuite SO#',
            'Netsuite SO Link': 'Netsuite SO Link',
            'New Design SKU': 'New Design SKU',
            'SKU': 'SKU',
            'Netsuite Sales Order Number': 'Netsuite Sales Order Number',
            'Primary Associated Company': 'Primary Associated Company',
            'Average Leadtime': 'Average Leadtime',
            'Pending Approval Date': 'Pending Approval Date',
            'Quarter': 'Quarter',
            'Deal Stage & Close Status': 'Deal Stage & Close Status',
            'Probability': 'Probability',
            'Probability Rev': 'Probability Rev',
            'Company Name': 'Company Name',
        }
        
        # Apply any mapping if column names match
        rename_dict = {}
        for col in deals_df.columns:
            col_stripped = str(col).strip()
            if col_stripped in column_mapping:
                rename_dict[col] = column_mapping[col_stripped]
        
        if rename_dict:
            deals_df = deals_df.rename(columns=rename_dict)
        
        # Remove duplicate columns
        if deals_df.columns.duplicated().any():
            deals_df = deals_df.loc[:, ~deals_df.columns.duplicated()]
        
        # Create Deal Owner by combining First Name + Last Name if separate columns exist
        if 'Deal Owner First Name' in deals_df.columns and 'Deal Owner Last Name' in deals_df.columns:
            deals_df['Deal Owner'] = (
                deals_df['Deal Owner First Name'].fillna('').astype(str).str.strip() + ' ' + 
                deals_df['Deal Owner Last Name'].fillna('').astype(str).str.strip()
            ).str.strip()
        elif 'Deal Owner Combined' in deals_df.columns:
            deals_df['Deal Owner'] = deals_df['Deal Owner Combined'].astype(str).str.strip()
        
        # Clean numeric data
        if 'Amount' in deals_df.columns:
            deals_df['Amount'] = deals_df['Amount'].apply(clean_numeric)
        if 'Probability Rev' in deals_df.columns:
            deals_df['Probability Rev'] = deals_df['Probability Rev'].apply(clean_numeric)
        else:
            deals_df['Probability Rev'] = deals_df.get('Amount', 0)
        
        # Clean date data
        if 'Close Date' in deals_df.columns:
            deals_df['Close Date'] = pd.to_datetime(deals_df['Close Date'], errors='coerce')
        if 'Pending Approval Date' in deals_df.columns:
            deals_df['Pending Approval Date'] = pd.to_datetime(deals_df['Pending Approval Date'], errors='coerce')
        
        # Clean text fields - strip whitespace AND newlines
        for col in ['Deal Owner', 'Deal Name', 'Close Status', 'Company Name', 'Primary Associated Company']:
            if col in deals_df.columns:
                deals_df[col] = deals_df[col].astype(str).str.strip().str.replace('\n', '', regex=False).str.replace('\r', '', regex=False)
        
        # FALLBACK: If Company Name doesn't exist, try to use Primary Associated Company
        if 'Company Name' not in deals_df.columns and 'Primary Associated Company' in deals_df.columns:
            deals_df['Company Name'] = deals_df['Primary Associated Company']
    
    # =========================================================================
    # LOAD AND PROCESS INVOICE LINE ITEMS
    # This is the drill-down layer explaining realized revenue composition
    # =========================================================================
    invoice_line_items_df = load_google_sheets_data("Invoice Line Item", "A:Z", version=CACHE_VERSION, silent=True)
    
    if not invoice_line_items_df.empty:
        # Remove duplicate columns
        if invoice_line_items_df.columns.duplicated().any():
            invoice_line_items_df = invoice_line_items_df.loc[:, ~invoice_line_items_df.columns.duplicated()]
        
        # Clean numeric data - Amount is line-level revenue
        if 'Amount' in invoice_line_items_df.columns:
            invoice_line_items_df['Amount'] = invoice_line_items_df['Amount'].apply(clean_numeric)
        
        # Quantity is unit-level volume
        if 'Quantity' in invoice_line_items_df.columns:
            invoice_line_items_df['Quantity'] = invoice_line_items_df['Quantity'].apply(clean_numeric)
        
        # Clean date data
        if 'Date' in invoice_line_items_df.columns:
            invoice_line_items_df['Date'] = pd.to_datetime(invoice_line_items_df['Date'], errors='coerce')
        if 'Due Date' in invoice_line_items_df.columns:
            invoice_line_items_df['Due Date'] = pd.to_datetime(invoice_line_items_df['Due Date'], errors='coerce')
        
        # Clean text fields - use Correct Customer and Rep Master as authoritative
        for col in ['Correct Customer', 'Rep Master', 'Status', 'Item', 'Item Description', 
                    'Calyx | Item Type', 'Calyx || Product Type']:
            if col in invoice_line_items_df.columns:
                invoice_line_items_df[col] = invoice_line_items_df[col].astype(str).str.strip()
                # Replace 'nan' strings with empty
                invoice_line_items_df[col] = invoice_line_items_df[col].replace('nan', '')
    
    return sales_orders_df, invoices_df, deals_df, invoice_line_items_df


# ========== HELPER FUNCTIONS ==========

def get_rep_list(sales_orders_df, invoices_df):
    """Get unique list of sales reps from both data sources"""
    reps = set()
    
    if not sales_orders_df.empty and 'Rep Master' in sales_orders_df.columns:
        valid_reps = sales_orders_df['Rep Master'].dropna()
        valid_reps = valid_reps[~valid_reps.isin(['', 'nan', 'None', '#N/A'])]
        reps.update(valid_reps.unique())
    
    if not invoices_df.empty and 'Rep Master' in invoices_df.columns:
        valid_reps = invoices_df['Rep Master'].dropna()
        valid_reps = valid_reps[~valid_reps.isin(['', 'nan', 'None', '#N/A'])]
        reps.update(valid_reps.unique())
    
    return sorted([r for r in reps if r])


def get_customers_for_rep(rep_name, sales_orders_df, invoices_df):
    """Get unique customers for a specific rep"""
    customers = set()
    
    if not sales_orders_df.empty and 'Rep Master' in sales_orders_df.columns and 'Corrected Customer Name' in sales_orders_df.columns:
        rep_orders = sales_orders_df[sales_orders_df['Rep Master'] == rep_name]
        valid_customers = rep_orders['Corrected Customer Name'].dropna()
        valid_customers = valid_customers[~valid_customers.isin(['', 'nan', 'None', '#N/A'])]
        customers.update(valid_customers.unique())
    
    if not invoices_df.empty and 'Rep Master' in invoices_df.columns and 'Corrected Customer' in invoices_df.columns:
        rep_invoices = invoices_df[invoices_df['Rep Master'] == rep_name]
        valid_customers = rep_invoices['Corrected Customer'].dropna()
        valid_customers = valid_customers[~valid_customers.isin(['', 'nan', 'None', '#N/A'])]
        customers.update(valid_customers.unique())
    
    return sorted([c for c in customers if c])


def get_customer_deals(customer_name, rep_name, deals_df):
    """
    Get HubSpot deals for a specific customer using direct match on Company Name
    """
    if deals_df.empty or 'Company Name' not in deals_df.columns:
        return pd.DataFrame()
    
    # Direct match on Company Name and Deal Owner
    matches = deals_df[
        (deals_df['Company Name'] == customer_name) &
        (deals_df['Deal Owner'] == rep_name)
    ].copy()
    
    return matches


# ========== QBR SECTION FUNCTIONS ==========

def render_pending_orders_section(customer_orders):
    """Section 1: Current Pending Orders"""
    st.markdown("### 📦 Current Pending Orders")
    
    if customer_orders.empty:
        st.info("No pending orders found for this customer.")
        return
    
    # Filter to pending orders only using Updated Status
    pending_statuses = ['PA with Date', 'PA No Date', 'PA Old (>2 Weeks)', 
                        'PF with Date (Ext)', 'PF with Date (Int)', 
                        'PF No Date (Ext)', 'PF No Date (Int)']
    
    pending_orders = customer_orders[customer_orders['Updated Status'].isin(pending_statuses)].copy()
    
    if pending_orders.empty:
        st.success("✅ No pending orders - all orders have been fulfilled!")
        return
    
    # Summary metrics
    total_pending = pending_orders['Amount'].sum()
    pending_count = len(pending_orders)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Pending Value", f"${total_pending:,.0f}")
    with col2:
        st.metric("Pending Orders", pending_count)
    with col3:
        # Breakdown by PA vs PF
        pa_amount = pending_orders[pending_orders['Updated Status'].str.startswith('PA')]['Amount'].sum()
        pf_amount = pending_orders[pending_orders['Updated Status'].str.startswith('PF')]['Amount'].sum()
        st.metric("PA / PF Split", f"${pa_amount:,.0f} / ${pf_amount:,.0f}")
    
    # Breakdown by Updated Status
    st.markdown("**Breakdown by Status:**")
    status_summary = pending_orders.groupby('Updated Status').agg({
        'Amount': ['sum', 'count']
    }).round(0)
    status_summary.columns = ['Total Value', 'Count']
    status_summary = status_summary.sort_values('Total Value', ascending=False)
    status_summary['Total Value'] = status_summary['Total Value'].apply(lambda x: f"${x:,.0f}")
    st.dataframe(status_summary, use_container_width=True)
    
    # Order details table
    with st.expander("📋 View Order Details", expanded=False):
        display_cols = ['SO Number', 'Order Type', 'Amount', 'Order Start Date', 'Updated Status']
        display_cols = [c for c in display_cols if c in pending_orders.columns]
        display_df = pending_orders[display_cols].copy()
        display_df['Amount'] = display_df['Amount'].apply(lambda x: f"${x:,.0f}")
        if 'Order Start Date' in display_df.columns:
            display_df['Order Start Date'] = pd.to_datetime(display_df['Order Start Date'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
        st.dataframe(display_df, use_container_width=True)


def render_open_invoices_section(customer_invoices):
    """Section 2: Open Invoices"""
    st.markdown("### 💳 Open Invoices")
    
    if customer_invoices.empty:
        st.info("No invoice data found for this customer.")
        return
    
    # Filter to open invoices
    open_invoices = customer_invoices[customer_invoices['Status'] == 'Open'].copy()
    
    if open_invoices.empty:
        st.success("✅ No open invoices - all invoices paid in full!")
        return
    
    # Summary metrics
    total_outstanding = open_invoices['Amount Remaining'].sum()
    invoice_count = len(open_invoices)
    
    # Calculate aging
    today = pd.Timestamp.now()
    open_invoices['Days Overdue'] = (today - open_invoices['Due Date']).dt.days
    overdue_invoices = open_invoices[open_invoices['Days Overdue'] > 0]
    overdue_amount = overdue_invoices['Amount Remaining'].sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Outstanding", f"${total_outstanding:,.0f}")
    with col2:
        st.metric("Open Invoices", invoice_count)
    with col3:
        st.metric("Overdue Amount", f"${overdue_amount:,.0f}", 
                  delta=f"{len(overdue_invoices)} overdue" if len(overdue_invoices) > 0 else None,
                  delta_color="inverse")
    
    # Aging breakdown
    if not open_invoices.empty:
        st.markdown("**Aging Summary:**")
        
        def aging_bucket(days):
            if days <= 0:
                return "Current"
            elif days <= 30:
                return "1-30 Days"
            elif days <= 60:
                return "31-60 Days"
            elif days <= 90:
                return "61-90 Days"
            else:
                return "90+ Days"
        
        open_invoices['Aging Bucket'] = open_invoices['Days Overdue'].apply(aging_bucket)
        aging_summary = open_invoices.groupby('Aging Bucket')['Amount Remaining'].sum()
        
        # Order buckets properly
        bucket_order = ["Current", "1-30 Days", "31-60 Days", "61-90 Days", "90+ Days"]
        aging_summary = aging_summary.reindex([b for b in bucket_order if b in aging_summary.index])
        
        aging_df = pd.DataFrame({
            'Aging Bucket': aging_summary.index,
            'Amount': aging_summary.values
        })
        aging_df['Amount'] = aging_df['Amount'].apply(lambda x: f"${x:,.0f}")
        st.dataframe(aging_df, use_container_width=True, hide_index=True)
    
    # Invoice details
    with st.expander("📋 View Invoice Details"):
        display_cols = ['Document Number', 'Date', 'Due Date', 'Amount', 'Amount Remaining', 'Days Overdue']
        display_cols = [c for c in display_cols if c in open_invoices.columns]
        display_df = open_invoices[display_cols].copy()
        display_df['Amount'] = display_df['Amount'].apply(lambda x: f"${x:,.0f}")
        display_df['Amount Remaining'] = display_df['Amount Remaining'].apply(lambda x: f"${x:,.0f}")
        if 'Date' in display_df.columns:
            display_df['Date'] = pd.to_datetime(display_df['Date'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
        if 'Due Date' in display_df.columns:
            display_df['Due Date'] = pd.to_datetime(display_df['Due Date'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
        st.dataframe(display_df.sort_values('Days Overdue', ascending=False), use_container_width=True)


def render_revenue_section(customer_invoices):
    """Section 3: Historical Revenue"""
    st.markdown("### 💰 Historical Revenue")
    
    if customer_invoices.empty:
        st.info("No invoice data found for this customer.")
        return
    
    # Just use all invoices - simple!
    total_revenue = customer_invoices['Amount'].sum()
    total_invoice_count = len(customer_invoices)
    avg_invoice = total_revenue / total_invoice_count if total_invoice_count > 0 else 0
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Lifetime Revenue", f"${total_revenue:,.0f}")
    with col2:
        st.metric("Total Invoices", total_invoice_count)
    with col3:
        st.metric("Avg Invoice Size", f"${avg_invoice:,.0f}")
    
    # Year breakdown
    if 'Date' in customer_invoices.columns and customer_invoices['Date'].notna().any():
        customer_invoices = customer_invoices.copy()
        customer_invoices['Year'] = customer_invoices['Date'].dt.year
        
        yearly_revenue = customer_invoices.groupby('Year').agg({
            'Amount': 'sum',
            'Document Number': 'count'
        }).reset_index()
        yearly_revenue.columns = ['Year', 'Revenue', 'Invoice Count']
        yearly_revenue = yearly_revenue.sort_values('Year', ascending=False)
        
        st.markdown("**Revenue by Year:**")
        display_yearly = yearly_revenue.copy()
        display_yearly['Revenue'] = display_yearly['Revenue'].apply(lambda x: f"${x:,.0f}")
        st.dataframe(display_yearly, use_container_width=True, hide_index=True)
        
        # Monthly chart
        current_year = datetime.now().year
        recent_invoices = customer_invoices[customer_invoices['Year'] >= current_year - 1].copy()
        if not recent_invoices.empty and len(recent_invoices) > 1:
            recent_invoices['Month'] = recent_invoices['Date'].dt.to_period('M').astype(str)
            monthly_revenue = recent_invoices.groupby('Month')['Amount'].sum().reset_index()
            
            fig = go.Figure(data=[
                go.Bar(
                    x=monthly_revenue['Month'],
                    y=monthly_revenue['Amount'],
                    marker=dict(
                        color=monthly_revenue['Amount'],
                        colorscale=[[0, '#1e40af'], [0.5, '#3b82f6'], [1, '#60a5fa']],
                        line=dict(width=0)
                    ),
                    hovertemplate='<b>%{x}</b><br>Revenue: $%{y:,.0f}<extra></extra>'
                )
            ])
            
            fig.update_layout(
                title=dict(text='Monthly Revenue Trend', font=dict(size=16, color='#f1f5f9')),
                xaxis_title='',
                yaxis_title='Revenue',
                plot_bgcolor='rgba(15, 23, 42, 0.5)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8', size=12),
                xaxis=dict(
                    gridcolor='#334155',
                    tickangle=-45,
                    tickfont=dict(size=10)
                ),
                yaxis=dict(
                    gridcolor='#334155',
                    tickformat='$,.0f'
                ),
                margin=dict(t=40, b=60)
            )
            st.plotly_chart(fig, use_container_width=True)


def render_on_time_section(customer_orders):
    """Section 4: On-Time Shipment Performance"""
    st.markdown("### ⏱️ On-Time Shipment Performance")
    
    if customer_orders.empty:
        st.info("No order data found for this customer.")
        return
    
    # Determine which column name is used for customer promise date
    promise_col = None
    if 'Customer Promise Date' in customer_orders.columns:
        promise_col = 'Customer Promise Date'
    elif 'Customer Promise Last Date to Ship' in customer_orders.columns:
        promise_col = 'Customer Promise Last Date to Ship'
    
    if promise_col is None:
        st.info("No customer promise date data available.")
        return
    
    # Filter to completed orders (Billed or Closed) with valid dates
    completed_orders = customer_orders[
        (customer_orders['Status'].isin(['Billed', 'Closed'])) &
        (customer_orders['Actual Ship Date'].notna()) &
        (customer_orders[promise_col].notna())
    ].copy()
    
    if completed_orders.empty:
        st.info("No completed orders with ship date data available.")
        return
    
    # Calculate on-time status
    completed_orders['Days Variance'] = (completed_orders['Actual Ship Date'] - completed_orders[promise_col]).dt.days
    completed_orders['On Time'] = completed_orders['Days Variance'] <= 0
    
    # Metrics
    total_orders = len(completed_orders)
    on_time_orders = completed_orders['On Time'].sum()
    ot_rate = (on_time_orders / total_orders * 100) if total_orders > 0 else 0
    avg_variance = completed_orders['Days Variance'].mean()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        delta_color = "normal" if ot_rate >= 90 else "inverse"
        st.metric("On-Time Rate", f"{ot_rate:.1f}%", 
                  delta=f"{on_time_orders}/{total_orders} orders",
                  delta_color=delta_color)
    with col2:
        st.metric("Avg Days Variance", f"{avg_variance:.1f} days",
                  delta="Early" if avg_variance < 0 else "Late" if avg_variance > 0 else "On Time",
                  delta_color="normal" if avg_variance <= 0 else "inverse")
    with col3:
        early_orders = (completed_orders['Days Variance'] < 0).sum()
        late_orders = (completed_orders['Days Variance'] > 0).sum()
        st.metric("Early / Late", f"{early_orders} / {late_orders}")
    
    # Distribution chart
    if len(completed_orders) > 5:
        # Create a more visually appealing histogram
        fig = go.Figure()
        
        # Separate early, on-time, and late
        early_data = completed_orders[completed_orders['Days Variance'] < 0]['Days Variance']
        on_time_data = completed_orders[completed_orders['Days Variance'] == 0]['Days Variance']
        late_data = completed_orders[completed_orders['Days Variance'] > 0]['Days Variance']
        
        # Add traces with different colors
        if len(early_data) > 0:
            fig.add_trace(go.Histogram(x=early_data, name='Early', marker_color='#10b981', opacity=0.8))
        if len(on_time_data) > 0:
            fig.add_trace(go.Histogram(x=on_time_data, name='On Time', marker_color='#3b82f6', opacity=0.8))
        if len(late_data) > 0:
            fig.add_trace(go.Histogram(x=late_data, name='Late', marker_color='#ef4444', opacity=0.8))
        
        fig.add_vline(x=0, line_dash="dash", line_color="#22c55e", line_width=2,
                      annotation_text="On Time", annotation_font_color="#22c55e")
        
        fig.update_layout(
            title=dict(text='Ship Date Variance', font=dict(size=16, color='#f1f5f9')),
            xaxis_title='Days (Negative = Early, Positive = Late)',
            yaxis_title='Orders',
            barmode='stack',
            plot_bgcolor='rgba(15, 23, 42, 0.5)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94a3b8', size=12),
            xaxis=dict(gridcolor='#334155', zerolinecolor='#334155'),
            yaxis=dict(gridcolor='#334155'),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='center',
                x=0.5,
                font=dict(color='#f1f5f9')
            ),
            margin=dict(t=60, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)


def render_order_cadence_section(customer_orders):
    """Section 5: Order Cadence Analysis"""
    st.markdown("### 📅 Order Cadence")
    
    if customer_orders.empty:
        st.info("No order data found for this customer.")
        return
    
    # Filter to orders with valid dates
    orders_with_dates = customer_orders[customer_orders['Order Start Date'].notna()].copy()
    
    if orders_with_dates.empty:
        st.info("No order date data available.")
        return
    
    # Sort by date
    orders_with_dates = orders_with_dates.sort_values('Order Start Date')
    
    # Calculate days between orders
    orders_with_dates['Days Since Last Order'] = orders_with_dates['Order Start Date'].diff().dt.days
    
    # Overall cadence
    avg_days_between = orders_with_dates['Days Since Last Order'].mean()
    last_order_date = orders_with_dates['Order Start Date'].max()
    days_since_last = (pd.Timestamp.now() - last_order_date).days if pd.notna(last_order_date) else None
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Avg Days Between Orders", f"{avg_days_between:.0f}" if pd.notna(avg_days_between) else "N/A")
    with col2:
        st.metric("Last Order", last_order_date.strftime('%Y-%m-%d') if pd.notna(last_order_date) else "N/A")
    with col3:
        if days_since_last is not None:
            delta_color = "inverse" if days_since_last > avg_days_between * 1.5 else "normal"
            st.metric("Days Since Last Order", f"{days_since_last:.0f}",
                      delta="Overdue" if days_since_last > avg_days_between * 1.5 else "On Track",
                      delta_color=delta_color)
    
    # Cadence by Order Type
    if 'Order Type' in orders_with_dates.columns:
        st.markdown("**Cadence by Order Type:**")
        
        type_cadence = orders_with_dates.groupby('Order Type').agg({
            'Days Since Last Order': 'mean',
            'Amount': ['sum', 'count']
        }).round(0)
        type_cadence.columns = ['Avg Days Between', 'Total Revenue', 'Order Count']
        type_cadence = type_cadence.sort_values('Total Revenue', ascending=False)
        type_cadence['Avg Days Between'] = type_cadence['Avg Days Between'].apply(lambda x: f"{x:.0f} days" if pd.notna(x) else "N/A")
        type_cadence['Total Revenue'] = type_cadence['Total Revenue'].apply(lambda x: f"${x:,.0f}")
        st.dataframe(type_cadence, use_container_width=True)


def render_order_type_mix_section(customer_orders):
    """Section 6: Order Type Mix"""
    st.markdown("### 📊 Order Type Mix (All Time)")
    
    if customer_orders.empty:
        st.info("No order data found for this customer.")
        return
    
    # Filter to valid order types
    valid_orders = customer_orders[
        (customer_orders['Order Type'].notna()) &
        (customer_orders['Order Type'] != '') &
        (customer_orders['Order Type'] != 'nan')
    ].copy()
    
    if valid_orders.empty:
        st.info("No order type data available.")
        return
    
    # Group by Order Type
    type_mix = valid_orders.groupby('Order Type').agg({
        'Amount': ['sum', 'count']
    }).round(0)
    type_mix.columns = ['Total Value', 'Order Count']
    type_mix = type_mix.sort_values('Total Value', ascending=False)
    
    # Calculate percentages
    total_value = type_mix['Total Value'].sum()
    type_mix['% of Total'] = (type_mix['Total Value'] / total_value * 100).round(1)
    
    # Display metrics
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart with better colors and legend
        colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4', '#ec4899', '#84cc16']
        
        fig = go.Figure(data=[go.Pie(
            labels=type_mix.reset_index()['Order Type'],
            values=type_mix['Total Value'],
            hole=0.4,  # Donut chart
            marker=dict(colors=colors[:len(type_mix)]),
            textposition='inside',
            textinfo='percent',
            textfont=dict(size=14, color='white'),
            hovertemplate='<b>%{label}</b><br>Revenue: $%{value:,.0f}<br>%{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title=dict(text='Revenue by Order Type', font=dict(size=16, color='#f1f5f9')),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94a3b8'),
            legend=dict(
                orientation='h',
                yanchor='top',
                y=-0.1,
                xanchor='center',
                x=0.5,
                font=dict(size=11, color='#f1f5f9'),
                bgcolor='rgba(0,0,0,0)'
            ),
            margin=dict(t=40, b=80, l=20, r=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Table
        display_df = type_mix.copy()
        display_df['Total Value'] = display_df['Total Value'].apply(lambda x: f"${x:,.0f}")
        display_df['% of Total'] = display_df['% of Total'].apply(lambda x: f"{x:.1f}%")
        st.dataframe(display_df, use_container_width=True)


def render_pipeline_section(customer_deals, customer_name):
    """Section 7: Active HubSpot Pipeline"""
    st.markdown("### 🎯 Active Pipeline")
    
    if customer_deals.empty:
        st.info(f"No HubSpot deals found for '{customer_name}'.")
        return
    
    # Filter to open deals
    open_statuses = ['Expect', 'Commit', 'Best Case', 'Opportunity']
    open_deals = customer_deals[customer_deals['Close Status'].isin(open_statuses)].copy()
    
    if open_deals.empty:
        st.info("No open pipeline deals found for this customer.")
        return
    
    # Toggle for Raw vs Probability-Adjusted
    # Use customer name to create unique key for multi-select support
    safe_customer_key = customer_name.replace(' ', '_').replace('.', '_')[:30]
    amount_mode = st.radio(
        "Amount Display:",
        ["Raw Forecast", "Probability-Adjusted"],
        horizontal=True,
        key=f"pipeline_amount_mode_{safe_customer_key}"
    )
    
    use_probability = amount_mode == "Probability-Adjusted"
    amount_col = 'Probability Rev' if use_probability else 'Amount'
    
    # Summary metrics
    total_pipeline = open_deals[amount_col].sum()
    deal_count = len(open_deals)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"Total Pipeline ({amount_mode})", f"${total_pipeline:,.0f}")
    with col2:
        st.metric("Open Deals", deal_count)
    with col3:
        if use_probability:
            raw_total = open_deals['Amount'].sum()
            st.metric("Raw Total (Reference)", f"${raw_total:,.0f}")
        else:
            prob_total = open_deals['Probability Rev'].sum()
            st.metric("Prob-Adjusted (Reference)", f"${prob_total:,.0f}")
    
    # Breakdown by Close Status
    status_summary = open_deals.groupby('Close Status').agg({
        amount_col: 'sum',
        'Record ID': 'count'
    }).round(0)
    status_summary.columns = ['Value', 'Count']
    
    # Order by pipeline stage
    stage_order = ['Expect', 'Commit', 'Best Case', 'Opportunity']
    status_summary = status_summary.reindex([s for s in stage_order if s in status_summary.index])
    
    status_summary['Value'] = status_summary['Value'].apply(lambda x: f"${x:,.0f}")
    st.dataframe(status_summary, use_container_width=True)
    
    # Deal details
    with st.expander("📋 View Deal Details"):
        display_cols = ['Deal Name', 'Close Status', 'Deal Type', 'Amount', 'Probability Rev', 'Close Date', 'Pending Approval Date']
        display_cols = [c for c in display_cols if c in open_deals.columns]
        display_df = open_deals[display_cols].copy()
        
        # Remove duplicate columns if any
        if display_df.columns.duplicated().any():
            display_df = display_df.loc[:, ~display_df.columns.duplicated()]
        
        if 'Amount' in display_df.columns:
            display_df['Amount'] = display_df['Amount'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")
        if 'Probability Rev' in display_df.columns:
            display_df['Probability Rev'] = display_df['Probability Rev'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")
        
        # Rename Pending Approval Date to Projected Ship Date
        if 'Pending Approval Date' in display_df.columns:
            display_df = display_df.rename(columns={'Pending Approval Date': 'Projected Ship Date'})
            display_df['Projected Ship Date'] = pd.to_datetime(display_df['Projected Ship Date'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
        if 'Close Date' in display_df.columns:
            display_df['Close Date'] = pd.to_datetime(display_df['Close Date'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
        
        st.dataframe(display_df, use_container_width=True)


# =============================================================================
# PRODUCT CATEGORIZATION FUNCTIONS
# Based on Calyx Containers Product Master Categorization Rules
# =============================================================================

def categorize_product(item_name, item_description=""):
    """
    Categorize a product based on Item name and description.
    Returns (category, sub_category) tuple.
    
    Categories: Drams, Concentrates, Tubes, Boxes, Flexpack, Calyx Jar, 
                Calyx Cure, Labels, Shipping/Fees
    """
    if pd.isna(item_name):
        item_name = ""
    if pd.isna(item_description):
        item_description = ""
    
    name = str(item_name).upper()
    desc = str(item_description).upper()
    combined = name + " " + desc
    
    # =========================================================================
    # 1. SHIPPING/TAXES/FEES (exclude from product analysis)
    # =========================================================================
    if any(x in combined for x in ['DISCOUNT', 'PROMO', '%OFF', 'TAX', 'GST', 'HST', 
                                    'SHIPPING', 'EXPEDITE FEE', 'CONVENIENCE FEE',
                                    'APPL FEE', 'APPLICATION FEE', 'ACCOUNTING']):
        if '$' in name and 'OFF' in name:
            return ('Shipping/Fees', 'Discount')
        if 'TAX' in combined or 'GST' in combined or 'HST' in combined:
            return ('Shipping/Fees', 'Tax')
        if 'SHIPPING' in combined or 'EXPEDITE' in combined:
            return ('Shipping/Fees', 'Shipping')
        if 'APPL' in combined and 'FEE' in combined:
            return ('Shipping/Fees', 'Application Fee')
        return ('Shipping/Fees', 'Other Fee')
    
    # =========================================================================
    # 2. CALYX CURE
    # =========================================================================
    if name.startswith('CC-') or 'CALYX CURE' in combined:
        return ('Calyx Cure', 'Calyx Cure')
    
    # =========================================================================
    # 3. CALYX JAR
    # =========================================================================
    if '-JB-' in name or '-JL-' in name or name.startswith('GB-8TH-') or 'CALYX JAR' in combined:
        if '-JB-' in name or 'BASE' in combined:
            return ('Calyx Jar', 'Jar Base')
        if '-JL-' in name or 'LID' in combined:
            return ('Calyx Jar', 'Jar Lid')
        return ('Calyx Jar', 'Calyx Jar')
    
    # =========================================================================
    # 4. DRAMS (15D, 25D, 45D, 145D) - Check BEFORE concentrates
    # =========================================================================
    dram_patterns = {
        '15D': ['-15L-', '-15B-', '-15P-', '-15H-', '-15LTE-', '15D'],
        '25D': ['-25L-', '-25B-', '-25P-', '-25H-', '-25LTE-', '25D'],
        '45D': ['-45L-', '-45B-', '-45P-', '-45H-', '-45LTE-', '45D'],
        '145D': ['-145L-', '-145B-', '-145P-', '-145H-', '-145LTE-', '145D']
    }
    
    for dram_size, patterns in dram_patterns.items():
        for pattern in patterns:
            if pattern in name:
                # Determine if it's a lid, base, or printed
                if any(x in name for x in ['-15L-', '-25L-', '-45L-', '-145L-', 'LID']):
                    return ('Drams', f'{dram_size} Lid')
                elif any(x in name for x in ['-15B-', '-25B-', '-45B-', '-145B-', 'BASE']):
                    return ('Drams', f'{dram_size} Base')
                elif any(x in name for x in ['-15P-', '-25P-', '-45P-', '-145P-']):
                    return ('Drams', f'{dram_size} Printed')
                else:
                    return ('Drams', dram_size)
    
    # =========================================================================
    # 5. CONCENTRATES (4mL/7mL)
    # =========================================================================
    concentrate_patterns = {
        '4mL': ['-4C-', '-4L-', '-4H-'],
        '7mL': ['-7C-', '-7L-', '-7H-']
    }
    
    for size, patterns in concentrate_patterns.items():
        for pattern in patterns:
            if pattern in name:
                if 'BOX' not in name and 'TUCK' not in name and 'AUTO' not in name:
                    if 'L-' in pattern or 'LID' in combined:
                        return ('Concentrates', f'{size} Lid')
                    elif 'C-' in pattern or 'BASE' in combined or 'JAR' in combined:
                        return ('Concentrates', f'{size} Jar')
                    else:
                        return ('Concentrates', size)
    
    if 'CONCENTRATE' in combined and 'BOX' not in name:
        return ('Concentrates', 'Concentrate')
    
    # =========================================================================
    # 6. TUBES (116mm, 90mm, 84mm)
    # =========================================================================
    if 'BOX' not in name:
        if any(x in name for x in ['116MM', '116T', '-116-', '116P']):
            return ('Tubes', '116mm')
        if any(x in name for x in ['90MM', '90T', '-90-', '90M']):
            return ('Tubes', '90mm')
        if any(x in name for x in ['84MM', '84T', '-84-']):
            return ('Tubes', '84mm')
    
    # =========================================================================
    # 7. BOXES
    # =========================================================================
    if any(x in combined for x in ['CORE AUTO', 'AUTOBOTTOM', 'AUTO BOTTOM', '-CNCA-', '-CNC-']):
        return ('Boxes', 'Core Auto')
    if any(x in combined for x in ['CORE TUCK', 'REVERSE TUCK']):
        return ('Boxes', 'Core Tuck')
    if any(x in combined for x in ['ELEVATED TUCK', 'ELEVATED AUTO', 'ELEVATED DISPLAY']):
        return ('Boxes', 'Elevated')
    if 'SHIPPER BOX' in combined:
        return ('Boxes', 'Shipper Box')
    if 'BOX' in combined and 'SBS' in combined and 'BAG' not in combined:
        return ('Boxes', 'Box')
    if 'TEARAWAY' in combined:
        return ('Boxes', 'Tearaway Display')
    
    # =========================================================================
    # 8. FLEXPACK / WAVEPACK
    # =========================================================================
    flexpack_codes = ['1148', '1164', '1169', '1179', '1180', '1182', '1183', '1188', 
                      '1190', '1192', '1247', '1259', '1283', '1304', '1325', '1340', 
                      '1345', '1354', '1367', '1373', '1375', '1393', '1492', '1519', 
                      '1608', '1635', '1666', '1670', '1673', '1678', '1696', '1703', 
                      '1711', '1758', '1768', '1771', '1776', '1780', '1787', '1808', 
                      '1849', '1867', '1875', '1883', '1890', '1896', '1901', '1904', 
                      '1906', '1909', '1915']
    
    if name.startswith('BAM-'):
        return ('Flexpack', 'B&M Flexpack')
    if 'WAVEPACK' in combined:
        return ('Flexpack', 'Wavepack')
    if 'FLEXPACK' in combined:
        return ('Flexpack', 'Flexpack')
    if any(x in combined for x in ['BAG', 'BAGS', 'POUCH']):
        return ('Flexpack', 'Bag/Pouch')
    
    # Check for flexpack codes
    code_match = re.search(r'-(\d{4})-', name)
    if code_match and code_match.group(1) in flexpack_codes:
        return ('Flexpack', 'Flexpack')
    
    # =========================================================================
    # 9. LABELS (catch-all for remaining label products)
    # =========================================================================
    if any(x in combined for x in ['LABEL', 'LBL', 'BOPP']):
        return ('Labels', 'Label')
    
    # =========================================================================
    # 10. UNCATEGORIZED
    # =========================================================================
    return ('Other', 'Other')


def apply_product_categories(df):
    """
    Apply categorization to a dataframe with Item and Item Description columns.
    Adds 'Product Category' and 'Product Sub-Category' columns.
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Determine which column to use
    item_col = 'Item' if 'Item' in df.columns else None
    desc_col = 'Item Description' if 'Item Description' in df.columns else None
    
    if item_col is None and desc_col is None:
        return df
    
    # Apply categorization
    categories = df.apply(
        lambda row: categorize_product(
            row.get(item_col, '') if item_col else '',
            row.get(desc_col, '') if desc_col else ''
        ), axis=1
    )
    
    df['Product Category'] = categories.apply(lambda x: x[0])
    df['Product Sub-Category'] = categories.apply(lambda x: x[1])
    
    return df


# =============================================================================
# INVOICE LINE ITEM ANALYSIS SECTION
# Purpose: Drill-down layer explaining realized revenue composition
# This does NOT recalculate totals - it explains what revenue consists of
# =============================================================================

def render_line_item_analysis_section(line_items_df, customer_name):
    """
    Render Invoice Line Item Analysis Section
    
    Purpose: Explain what realized revenue consists of at the product/SKU level
    
    Key principles:
    - Group by Correct Customer and Rep Master (authoritative attribution)
    - Use Amount as line-level revenue, Quantity as unit-level volume
    - Do NOT recompute transaction totals
    - Use probabilistic language for container-related behavior
    """
    st.markdown("### 📦 Product & SKU Analysis")
    st.caption("Drill-down analysis of invoice line items — explains what revenue consists of")
    
    if line_items_df is None or line_items_df.empty:
        st.info(f"No invoice line item data available for {customer_name}.")
        return
    
    # Apply product categorization
    line_items_df = apply_product_categories(line_items_df)
    
    # Exclude Shipping/Fees from product analysis
    product_df = line_items_df[line_items_df['Product Category'] != 'Shipping/Fees'].copy()
    
    if product_df.empty:
        st.info("No product line items found (only fees/shipping).")
        return
    
    # Calculate totals for context (not recomputing - just line item sum)
    total_line_revenue = product_df['Amount'].sum() if 'Amount' in product_df.columns else 0
    total_quantity = product_df['Quantity'].sum() if 'Quantity' in product_df.columns else 0
    line_count = len(product_df)
    unique_categories = product_df['Product Category'].nunique() if 'Product Category' in product_df.columns else 0
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Product Revenue", f"${total_line_revenue:,.0f}")
    with col2:
        st.metric("Total Units", f"{total_quantity:,.0f}")
    with col3:
        st.metric("Line Items", f"{line_count:,}")
    with col4:
        st.metric("Product Categories", f"{unique_categories}")
    
    # Create tabs for different analysis views
    analysis_tabs = st.tabs(["📊 Product Categories", "🔍 Category Breakdown", "📈 Purchase Patterns"])
    
    # =========================================================================
    # TAB 1: Product Categories Overview (Customer-Friendly)
    # =========================================================================
    with analysis_tabs[0]:
        st.markdown("#### Product Categories")
        st.caption("Your purchases organized by product type")
        
        # Group by Product Category
        category_summary = product_df.groupby('Product Category').agg({
            'Amount': 'sum',
            'Quantity': 'sum',
            'Document Number': 'nunique'
        }).reset_index()
        category_summary.columns = ['Category', 'Revenue', 'Units', 'Orders']
        category_summary = category_summary.sort_values('Revenue', ascending=False)
        
        # Calculate percentages
        category_summary['% of Revenue'] = (category_summary['Revenue'] / total_line_revenue * 100).round(1)
        
        if len(category_summary) > 0:
            # Two columns: chart and summary
            chart_col, summary_col = st.columns([1, 1])
            
            with chart_col:
                # Donut chart
                fig = go.Figure(data=[go.Pie(
                    labels=category_summary['Category'],
                    values=category_summary['Revenue'],
                    hole=0.45,
                    textinfo='label+percent',
                    textposition='outside',
                    marker=dict(colors=['#3b82f6', '#10b981', '#f59e0b', '#ef4444', 
                                       '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'])
                )])
                fig.update_layout(
                    title="Revenue by Product Category",
                    showlegend=False,
                    height=400,
                    margin=dict(t=50, b=20, l=20, r=20)
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with summary_col:
                # Category cards
                st.markdown("**Revenue Breakdown**")
                for _, row in category_summary.iterrows():
                    revenue_str = f"${row['Revenue']:,.0f}"
                    units_str = f"{row['Units']:,.0f} units"
                    pct_str = f"{row['% of Revenue']:.1f}%"
                    st.markdown(f"""
                        <div style="
                            background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%);
                            padding: 12px 16px;
                            border-radius: 8px;
                            margin-bottom: 8px;
                            border-left: 4px solid #3b82f6;
                        ">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="color: #f1f5f9; font-weight: 600;">{row['Category']}</span>
                                <span style="color: #10b981; font-weight: 700;">{revenue_str}</span>
                            </div>
                            <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 4px;">
                                {units_str} • {pct_str} of total • {int(row['Orders'])} orders
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            
            # Detailed table
            with st.expander("📋 View Category Details Table"):
                display_df = category_summary.copy()
                display_df['Revenue'] = display_df['Revenue'].apply(lambda x: f"${x:,.0f}")
                display_df['Units'] = display_df['Units'].apply(lambda x: f"{x:,.0f}")
                display_df['% of Revenue'] = display_df['% of Revenue'].apply(lambda x: f"{x:.1f}%")
                st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # =========================================================================
    # TAB 2: Category Breakdown (Drill-down into each category)
    # =========================================================================
    with analysis_tabs[1]:
        st.markdown("#### Category Breakdown")
        st.caption("Drill down into each product category to see specific sizes/types")
        
        # Get categories ordered by revenue
        categories_ordered = category_summary['Category'].tolist()
        
        for category in categories_ordered:
            cat_df = product_df[product_df['Product Category'] == category]
            cat_revenue = cat_df['Amount'].sum()
            cat_units = cat_df['Quantity'].sum()
            
            # Get sub-category breakdown
            subcat_summary = cat_df.groupby('Product Sub-Category').agg({
                'Amount': 'sum',
                'Quantity': 'sum',
                'Document Number': 'nunique'
            }).reset_index()
            subcat_summary.columns = ['Type', 'Revenue', 'Units', 'Orders']
            subcat_summary = subcat_summary.sort_values('Revenue', ascending=False)
            subcat_summary['% of Category'] = (subcat_summary['Revenue'] / cat_revenue * 100).round(1)
            
            # Category header with summary
            with st.expander(f"**{category}** — ${cat_revenue:,.0f} ({cat_units:,.0f} units)", expanded=(category == categories_ordered[0])):
                
                if len(subcat_summary) > 1:
                    # Show breakdown chart
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        fig = go.Figure(data=[go.Bar(
                            x=subcat_summary['Type'],
                            y=subcat_summary['Revenue'],
                            marker_color='#3b82f6',
                            text=subcat_summary['Revenue'].apply(lambda x: f"${x/1000:.1f}K" if x >= 1000 else f"${x:.0f}"),
                            textposition='outside'
                        )])
                        fig.update_layout(
                            title=f"{category} Breakdown",
                            xaxis_title="",
                            yaxis_title="Revenue ($)",
                            height=300,
                            margin=dict(t=50, b=50),
                            xaxis_tickangle=-30
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Summary table
                        display_subcat = subcat_summary.copy()
                        display_subcat['Revenue'] = display_subcat['Revenue'].apply(lambda x: f"${x:,.0f}")
                        display_subcat['Units'] = display_subcat['Units'].apply(lambda x: f"{x:,.0f}")
                        display_subcat['% of Category'] = display_subcat['% of Category'].apply(lambda x: f"{x:.1f}%")
                        st.dataframe(display_subcat, use_container_width=True, hide_index=True)
                else:
                    # Single sub-category, just show the value
                    st.markdown(f"**{subcat_summary.iloc[0]['Type']}**: ${subcat_summary.iloc[0]['Revenue']:,.0f} ({subcat_summary.iloc[0]['Units']:,.0f} units)")
                
                # Show top items in this category
                st.markdown("---")
                st.markdown("**Top Items in this Category:**")
                
                # Use Item Description for readability
                item_col = 'Item Description' if 'Item Description' in cat_df.columns else 'Item'
                top_items = cat_df.groupby(item_col).agg({
                    'Amount': 'sum',
                    'Quantity': 'sum'
                }).reset_index().sort_values('Amount', ascending=False).head(5)
                
                top_items.columns = ['Item', 'Revenue', 'Units']
                top_items['Revenue'] = top_items['Revenue'].apply(lambda x: f"${x:,.0f}")
                top_items['Units'] = top_items['Units'].apply(lambda x: f"{x:,.0f}")
                st.dataframe(top_items, use_container_width=True, hide_index=True)
    
    # =========================================================================
    # TAB 3: Purchase Patterns
    # =========================================================================
    with analysis_tabs[2]:
        st.markdown("#### Purchase Patterns by Category")
        st.caption("Which product categories are consistently purchased vs. one-time")
        
        # Analyze purchase frequency by category
        category_frequency = product_df.groupby('Product Category').agg({
            'Document Number': 'nunique',
            'Amount': 'sum',
            'Quantity': 'sum'
        }).reset_index()
        category_frequency.columns = ['Category', 'Purchase Occasions', 'Total Revenue', 'Total Units']
        category_frequency = category_frequency.sort_values('Purchase Occasions', ascending=False)
        
        # Categorize
        def categorize_frequency(occasions):
            if occasions >= 10:
                return "Core Product"
            elif occasions >= 5:
                return "Regular Product"
            elif occasions >= 2:
                return "Repeat Product"
            else:
                return "One-Time Product"
        
        category_frequency['Pattern'] = category_frequency['Purchase Occasions'].apply(categorize_frequency)
        
        # Color mapping for patterns
        pattern_colors = {
            'Core Product': '#10b981',
            'Regular Product': '#3b82f6', 
            'Repeat Product': '#f59e0b',
            'One-Time Product': '#94a3b8'
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Categories by Purchase Frequency**")
            
            # Stacked bar or grouped display
            fig = go.Figure(data=[go.Bar(
                x=category_frequency['Category'],
                y=category_frequency['Purchase Occasions'],
                marker_color=[pattern_colors.get(p, '#94a3b8') for p in category_frequency['Pattern']],
                text=category_frequency['Purchase Occasions'],
                textposition='outside'
            )])
            fig.update_layout(
                title="Orders per Category",
                xaxis_title="",
                yaxis_title="Number of Orders",
                height=350,
                margin=dict(b=100),
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("**Revenue by Purchase Pattern**")
            
            pattern_summary = category_frequency.groupby('Pattern').agg({
                'Category': 'count',
                'Total Revenue': 'sum'
            }).reset_index()
            pattern_summary.columns = ['Pattern', 'Categories', 'Revenue']
            
            # Order patterns
            pattern_order = ['Core Product', 'Regular Product', 'Repeat Product', 'One-Time Product']
            pattern_summary['Sort'] = pattern_summary['Pattern'].apply(lambda x: pattern_order.index(x) if x in pattern_order else 99)
            pattern_summary = pattern_summary.sort_values('Sort').drop('Sort', axis=1)
            
            fig = go.Figure(data=[go.Bar(
                x=pattern_summary['Pattern'],
                y=pattern_summary['Revenue'],
                marker_color=[pattern_colors.get(p, '#94a3b8') for p in pattern_summary['Pattern']],
                text=pattern_summary['Revenue'].apply(lambda x: f"${x/1000:.1f}K" if x >= 1000 else f"${x:.0f}"),
                textposition='outside'
            )])
            fig.update_layout(
                title="Revenue by Pattern",
                xaxis_title="",
                yaxis_title="Revenue ($)",
                height=350,
                margin=dict(b=50)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed breakdown
        st.markdown("---")
        st.markdown("**Category Purchase Details**")
        
        # Show each category with its pattern
        display_freq = category_frequency.copy()
        display_freq['Total Revenue'] = display_freq['Total Revenue'].apply(lambda x: f"${x:,.0f}")
        display_freq['Total Units'] = display_freq['Total Units'].apply(lambda x: f"{x:,.0f}")
        
        # Add color indicators
        def pattern_indicator(pattern):
            indicators = {
                'Core Product': '🟢',
                'Regular Product': '🔵',
                'Repeat Product': '🟠',
                'One-Time Product': '⚪'
            }
            return indicators.get(pattern, '⚪')
        
        display_freq[''] = display_freq['Pattern'].apply(pattern_indicator)
        display_freq = display_freq[['', 'Category', 'Pattern', 'Purchase Occasions', 'Total Revenue', 'Total Units']]
        
        st.dataframe(display_freq, use_container_width=True, hide_index=True)
        
        # Legend
        st.markdown("""
            <div style="display: flex; gap: 20px; margin-top: 10px; color: #94a3b8; font-size: 0.85rem;">
                <span>🟢 Core (10+ orders)</span>
                <span>🔵 Regular (5-9 orders)</span>
                <span>🟠 Repeat (2-4 orders)</span>
                <span>⚪ One-Time (1 order)</span>
            </div>
        """, unsafe_allow_html=True)


# ========== MAIN RENDER FUNCTION ==========

def render_yearly_planning_2026():
    """Main entry point for QBR Generator"""
    
    st.title("📋 QBR Generator")
    st.caption("Generate Quarterly Business Review reports for customer meetings")
    
    # Load data
    with st.spinner("Loading data..."):
        sales_orders_df, invoices_df, deals_df, invoice_line_items_df = load_qbr_data()
    
    # Check if data loaded
    if sales_orders_df.empty and invoices_df.empty:
        st.error("❌ Unable to load data. Please check your Google Sheets connection.")
        return
    
    # Custom CSS for sleek dark theme
    st.markdown("""
        <style>
        /* ===== DROPDOWNS / SELECTBOX ===== */
        div[data-baseweb="select"] > div {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
            border: 2px solid #3b82f6 !important;
            border-radius: 10px !important;
            color: #f1f5f9 !important;
            padding: 2px 8px !important;
            min-height: 50px !important;
        }
        div[data-baseweb="select"] > div:hover {
            border-color: #60a5fa !important;
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.4) !important;
            transform: translateY(-1px);
        }
        div[data-baseweb="select"] span {
            color: #f1f5f9 !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
        }
        /* Dropdown arrow */
        div[data-baseweb="select"] svg {
            fill: #3b82f6 !important;
        }
        /* Dropdown menu */
        div[data-baseweb="popover"] {
            background: #1e293b !important;
            border: 2px solid #3b82f6 !important;
            border-radius: 10px !important;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5) !important;
        }
        div[data-baseweb="popover"] ul {
            background: #1e293b !important;
            max-height: 400px !important;
        }
        div[data-baseweb="popover"] li {
            color: #f1f5f9 !important;
            background: transparent !important;
            padding: 12px 16px !important;
            font-size: 0.95rem !important;
            border-bottom: 1px solid #334155 !important;
        }
        div[data-baseweb="popover"] li:hover {
            background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%) !important;
            color: #ffffff !important;
        }
        div[data-baseweb="popover"] li[aria-selected="true"] {
            background: #1e40af !important;
            color: #ffffff !important;
        }
        /* Input labels */
        .stSelectbox label, .stMultiSelect label {
            color: #94a3b8 !important;
            font-weight: 700 !important;
            font-size: 0.85rem !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
            margin-bottom: 8px !important;
        }
        
        /* ===== MULTISELECT ===== */
        .stMultiSelect > div > div {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
            border: 2px solid #3b82f6 !important;
            border-radius: 10px !important;
        }
        .stMultiSelect span[data-baseweb="tag"] {
            background: #3b82f6 !important;
            border-radius: 6px !important;
        }
        .stMultiSelect span[data-baseweb="tag"] span {
            color: white !important;
        }
        
        /* ===== METRICS ===== */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
            border: 1px solid #334155 !important;
            border-radius: 12px !important;
            padding: 1rem !important;
        }
        div[data-testid="stMetric"] label {
            color: #94a3b8 !important;
        }
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            color: #f1f5f9 !important;
        }
        
        /* ===== BUTTONS ===== */
        .stButton > button {
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 12px 24px !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            transition: all 0.3s ease !important;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #1d4ed8 0%, #60a5fa 100%) !important;
            box-shadow: 0 5px 20px rgba(59, 130, 246, 0.4) !important;
            transform: translateY(-2px) !important;
        }
        
        /* ===== DOWNLOAD BUTTON ===== */
        .stDownloadButton > button {
            background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 12px 24px !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
        }
        .stDownloadButton > button:hover {
            background: linear-gradient(135deg, #047857 0%, #34d399 100%) !important;
            box-shadow: 0 5px 20px rgba(16, 185, 129, 0.4) !important;
            transform: translateY(-2px) !important;
        }
        
        /* ===== DATAFRAMES ===== */
        .stDataFrame {
            border-radius: 8px !important;
            overflow: hidden !important;
        }
        
        /* ===== SECTION HEADERS ===== */
        h3 {
            color: #f1f5f9 !important;
            border-bottom: 2px solid #3b82f6 !important;
            padding-bottom: 0.5rem !important;
        }
        
        /* ===== RADIO BUTTONS ===== */
        .stRadio > div {
            background: transparent !important;
        }
        .stRadio label {
            color: #f1f5f9 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # =========================================================================
    # REP AND CUSTOMER SELECTION - ON MAIN DASHBOARD
    # =========================================================================
    st.markdown("""
        <div style="
            background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
            padding: 1rem 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #3b82f6;
            margin: 1rem 0;
        ">
            <h3 style="color: #f1f5f9; margin: 0; font-size: 1.3rem;">🔍 Select Customer(s) for QBR</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # Allowed sales reps
    ALLOWED_REPS = [
        'Jake Lynch', 
        'Brad Sherman', 
        'Lance Mitton', 
        'Owen Labombard', 
        'Alex Gonzalez', 
        'Dave Borkowski', 
        'Kyle Bissell'
    ]
    
    # Rep selector - filtered to allowed reps only
    rep_list = get_rep_list(sales_orders_df, invoices_df)
    rep_list = [r for r in rep_list if r in ALLOWED_REPS]
    
    if not rep_list:
        st.error("No sales reps found in data.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_rep = st.selectbox(
            "SALES REP", 
            rep_list, 
            key="qbr_rep_selector"
        )
    
    # Customer selector (filtered by rep) - MULTI-SELECT with NO default
    customer_list = get_customers_for_rep(selected_rep, sales_orders_df, invoices_df)
    
    with col2:
        if not customer_list:
            st.warning(f"No customers found for {selected_rep}")
            return
        
        selected_customers = st.multiselect(
            f"CUSTOMERS ({len(customer_list)} accounts)", 
            customer_list,
            placeholder="Select customers...",
            key="qbr_customer_selector"
        )
    
    # Empty state - show helpful message
    if not selected_customers:
        st.markdown("---")
        st.markdown("""
            <div style="
                text-align: center;
                padding: 3rem;
                color: #64748b;
            ">
                <h3 style="color: #94a3b8; margin-bottom: 1rem;">👆 Select one or more customers above</h3>
                <p>Choose customers from the dropdown to view their QBR data and generate reports.</p>
                <p style="margin-top: 0.5rem; font-size: 0.9rem;">You can select multiple customers to compare or generate a combined report.</p>
            </div>
        """, unsafe_allow_html=True)
        return
    
    # =========================================================================
    # DATE FILTER SECTION
    # =========================================================================
    st.markdown("""
        <div style="
            background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
            padding: 0.75rem 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #f59e0b;
            margin: 1rem 0;
        ">
            <h3 style="color: #f1f5f9; margin: 0; font-size: 1.1rem;">📅 Date Range Filter</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # Date filter controls
    col_period, col_range = st.columns([1, 2])
    
    with col_period:
        period_type = st.selectbox(
            "TIME PERIOD",
            ["All Time", "This Month", "This Quarter", "This Year", "Last Month", "Last Quarter", "Last Year", "Custom Range"],
            key="qbr_period_type"
        )
    
    # Calculate date range based on selection
    today = datetime.now()
    
    if period_type == "All Time":
        start_date = None
        end_date = None
        date_label = "All Time"
    elif period_type == "This Month":
        start_date = today.replace(day=1)
        end_date = today
        date_label = today.strftime("%B %Y")
    elif period_type == "Last Month":
        first_of_month = today.replace(day=1)
        last_month_end = first_of_month - timedelta(days=1)
        start_date = last_month_end.replace(day=1)
        end_date = last_month_end
        date_label = start_date.strftime("%B %Y")
    elif period_type == "This Quarter":
        quarter = (today.month - 1) // 3
        start_date = datetime(today.year, quarter * 3 + 1, 1)
        end_date = today
        date_label = f"Q{quarter + 1} {today.year}"
    elif period_type == "Last Quarter":
        quarter = (today.month - 1) // 3
        if quarter == 0:
            start_date = datetime(today.year - 1, 10, 1)
            end_date = datetime(today.year - 1, 12, 31)
            date_label = f"Q4 {today.year - 1}"
        else:
            start_date = datetime(today.year, (quarter - 1) * 3 + 1, 1)
            end_month = quarter * 3
            if end_month == 3:
                end_date = datetime(today.year, 3, 31)
            elif end_month == 6:
                end_date = datetime(today.year, 6, 30)
            else:
                end_date = datetime(today.year, 9, 30)
            date_label = f"Q{quarter} {today.year}"
    elif period_type == "This Year":
        start_date = datetime(today.year, 1, 1)
        end_date = today
        date_label = str(today.year)
    elif period_type == "Last Year":
        start_date = datetime(today.year - 1, 1, 1)
        end_date = datetime(today.year - 1, 12, 31)
        date_label = str(today.year - 1)
    else:  # Custom Range
        start_date = None
        end_date = None
        date_label = "Custom"
    
    with col_range:
        if period_type == "Custom Range":
            # Show date range picker for custom
            date_col1, date_col2 = st.columns(2)
            with date_col1:
                custom_start = st.date_input(
                    "START DATE",
                    value=today - timedelta(days=365),
                    key="qbr_custom_start"
                )
            with date_col2:
                custom_end = st.date_input(
                    "END DATE",
                    value=today,
                    key="qbr_custom_end"
                )
            start_date = datetime.combine(custom_start, datetime.min.time())
            end_date = datetime.combine(custom_end, datetime.max.time())
            date_label = f"{custom_start.strftime('%b %d, %Y')} - {custom_end.strftime('%b %d, %Y')}"
        else:
            # Show the calculated date range
            if start_date and end_date:
                st.markdown(f"""
                    <div style="
                        background: #1e293b;
                        padding: 0.75rem 1rem;
                        border-radius: 8px;
                        margin-top: 1.5rem;
                        color: #94a3b8;
                    ">
                        <span style="color: #f59e0b; font-weight: 600;">📆 {date_label}</span><br>
                        <span style="font-size: 0.85rem;">{start_date.strftime('%b %d, %Y')} → {end_date.strftime('%b %d, %Y')}</span>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style="
                        background: #1e293b;
                        padding: 0.75rem 1rem;
                        border-radius: 8px;
                        margin-top: 1.5rem;
                        color: #94a3b8;
                    ">
                        <span style="color: #f59e0b; font-weight: 600;">📆 All Time</span><br>
                        <span style="font-size: 0.85rem;">No date filter applied</span>
                    </div>
                """, unsafe_allow_html=True)
    
    # Apply date filter to dataframes
    def filter_by_date(df, date_col, start, end):
        """Filter dataframe by date column"""
        if df.empty or date_col not in df.columns:
            return df
        if start is None and end is None:
            return df
        
        df_filtered = df.copy()
        df_filtered[date_col] = pd.to_datetime(df_filtered[date_col], errors='coerce')
        
        if start is not None:
            df_filtered = df_filtered[df_filtered[date_col] >= pd.Timestamp(start)]
        if end is not None:
            df_filtered = df_filtered[df_filtered[date_col] <= pd.Timestamp(end)]
        
        return df_filtered
    
    # Filter each dataframe
    # Sales Orders - filter by Order Start Date
    filtered_orders_df = filter_by_date(sales_orders_df, 'Order Start Date', start_date, end_date)
    
    # Invoices - filter by Date
    filtered_invoices_df = filter_by_date(invoices_df, 'Date', start_date, end_date)
    
    # Deals - filter by Close Date
    filtered_deals_df = filter_by_date(deals_df, 'Close Date', start_date, end_date)
    
    # Invoice Line Items - filter by Date
    filtered_line_items_df = filter_by_date(invoice_line_items_df, 'Date', start_date, end_date)
    
    st.markdown("---")
    
    # Prepare data for all selected customers (using filtered dataframes)
    all_customers_data = []
    for customer_name in selected_customers:
        customer_orders = filtered_orders_df[
            (filtered_orders_df['Corrected Customer Name'] == customer_name) &
            (filtered_orders_df['Rep Master'] == selected_rep)
        ].copy() if not filtered_orders_df.empty and 'Corrected Customer Name' in filtered_orders_df.columns else pd.DataFrame()
        
        customer_invoices = filtered_invoices_df[
            (filtered_invoices_df['Corrected Customer'] == customer_name) &
            (filtered_invoices_df['Rep Master'] == selected_rep)
        ].copy() if not filtered_invoices_df.empty and 'Corrected Customer' in filtered_invoices_df.columns else pd.DataFrame()
        
        customer_deals = get_customer_deals(customer_name, selected_rep, filtered_deals_df)
        
        # Invoice Line Items - group by Correct Customer and Rep Master (authoritative attribution)
        customer_line_items = filtered_line_items_df[
            (filtered_line_items_df['Correct Customer'] == customer_name) &
            (filtered_line_items_df['Rep Master'] == selected_rep)
        ].copy() if not filtered_line_items_df.empty and 'Correct Customer' in filtered_line_items_df.columns else pd.DataFrame()
        
        all_customers_data.append((customer_name, customer_orders, customer_invoices, customer_deals, customer_line_items))
    
    # Download buttons section
    date_info = f" | 📅 {date_label}" if date_label != "All Time" else ""
    st.markdown(f"""
        <div style="
            background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
            padding: 1rem 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #10b981;
            margin-bottom: 1rem;
        ">
            <h3 style="color: #f1f5f9; margin: 0; font-size: 1.1rem;">📥 Download Reports{date_info}</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # Create download buttons
    if len(selected_customers) == 1:
        # Single customer - just one download button
        customer_name, customer_orders, customer_invoices, customer_deals, customer_line_items = all_customers_data[0]
        html_report = generate_qbr_html(customer_name, selected_rep, customer_orders, customer_invoices, customer_deals)
        
        col_spacer1, col_btn, col_spacer2 = st.columns([2, 1, 2])
        with col_btn:
            st.download_button(
                label=f"📄 Download {customer_name}",
                data=html_report,
                file_name=f"Account_Summary_{customer_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.html",
                mime="text/html",
                use_container_width=True,
                key="download_single"
            )
    else:
        # Multiple customers - show combined summary + all reports + individual buttons
        num_customers = len(selected_customers)
        
        # Generate reports
        combined_summary_html = generate_combined_summary_html(all_customers_data, selected_rep)
        all_reports_html = generate_combined_qbr_html(all_customers_data, selected_rep)
        
        # Two main download buttons side by side
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label=f"📊 Combined Summary ({num_customers} customers)",
                data=combined_summary_html,
                file_name=f"Combined_Summary_{selected_rep.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.html",
                mime="text/html",
                use_container_width=True,
                key="download_combined_summary"
            )
            st.caption("Aggregated metrics & breakdown table")
        
        with col2:
            st.download_button(
                label=f"📑 All Individual Reports ({num_customers})",
                data=all_reports_html,
                file_name=f"All_Reports_{selected_rep.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.html",
                mime="text/html",
                use_container_width=True,
                key="download_all_reports"
            )
            st.caption("Each customer's full report, separated")
        
        # Individual download buttons in expandable section
        with st.expander(f"📄 Download Individual Customer Reports"):
            cols = st.columns(min(3, num_customers))
            for idx, (customer_name, customer_orders, customer_invoices, customer_deals, _) in enumerate(all_customers_data):
                html_report = generate_qbr_html(customer_name, selected_rep, customer_orders, customer_invoices, customer_deals)
                with cols[idx % 3]:
                    st.download_button(
                        label=f"📄 {customer_name[:20]}{'...' if len(customer_name) > 20 else ''}",
                        data=html_report,
                        file_name=f"Account_Summary_{customer_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.html",
                        mime="text/html",
                        use_container_width=True,
                        key=f"download_individual_{idx}"
                    )
    
    # Chart status
    if not KALEIDO_AVAILABLE:
        st.caption(f"📊 Charts: Interactive mode")
    else:
        st.caption("📊 Charts: Static images")
    
    st.markdown("---")
    
    # Date filter label for headers
    date_filter_text = f" &nbsp;|&nbsp; 📅 {date_label}" if date_label != "All Time" else ""
    
    # Display customer QBR sections
    if len(all_customers_data) == 1:
        # Single customer - display directly
        selected_customer, customer_orders, customer_invoices, customer_deals, customer_line_items = all_customers_data[0]
        
        st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #06b6d4 100%);
                padding: 1.5rem 2rem;
                border-radius: 12px;
                margin-bottom: 1rem;
            ">
                <h1 style="color: white; margin: 0; font-size: 2rem;">📋 {selected_customer}</h1>
                <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 0.9rem;">
                    Sales Rep: {selected_rep}{date_filter_text} &nbsp;|&nbsp; Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        render_pending_orders_section(customer_orders)
        st.markdown("---")
        render_open_invoices_section(customer_invoices)
        st.markdown("---")
        render_revenue_section(customer_invoices)
        st.markdown("---")
        render_on_time_section(customer_orders)
        st.markdown("---")
        render_order_cadence_section(customer_orders)
        st.markdown("---")
        render_order_type_mix_section(customer_orders)
        st.markdown("---")
        render_pipeline_section(customer_deals, selected_customer)
        
        # =========================================================================
        # INVOICE LINE ITEM ANALYSIS - Drill-down layer for realized revenue
        # =========================================================================
        st.markdown("---")
        render_line_item_analysis_section(customer_line_items, selected_customer)
        
    else:
        # Multiple customers - use tabs with Combined view first
        tab_names = ["📊 Combined View"] + [name[:25] + "..." if len(name) > 25 else name for name, *_ in all_customers_data]
        tabs = st.tabs(tab_names)
        
        # Combined View Tab
        with tabs[0]:
            st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #059669 0%, #10b981 50%, #34d399 100%);
                    padding: 1.5rem 2rem;
                    border-radius: 12px;
                    margin-bottom: 1rem;
                ">
                    <h1 style="color: white; margin: 0; font-size: 2rem;">📊 Combined View - {len(all_customers_data)} Customers</h1>
                    <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 0.9rem;">
                        Sales Rep: {selected_rep}{date_filter_text} &nbsp;|&nbsp; Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            # Aggregate all data
            all_orders = pd.concat([data[1] for data in all_customers_data if not data[1].empty], ignore_index=True) if any(not data[1].empty for data in all_customers_data) else pd.DataFrame()
            all_invoices = pd.concat([data[2] for data in all_customers_data if not data[2].empty], ignore_index=True) if any(not data[2].empty for data in all_customers_data) else pd.DataFrame()
            all_deals = pd.concat([data[3] for data in all_customers_data if not data[3].empty], ignore_index=True) if any(not data[3].empty for data in all_customers_data) else pd.DataFrame()
            all_line_items = pd.concat([data[4] for data in all_customers_data if not data[4].empty], ignore_index=True) if any(not data[4].empty for data in all_customers_data) else pd.DataFrame()
            
            # Combined Summary Metrics
            st.markdown("### 📈 Combined Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            # Pending Orders
            pending_statuses = ['PA with Date', 'PA No Date', 'PA Old (>2 Weeks)', 
                                'PF with Date (Ext)', 'PF with Date (Int)', 
                                'PF No Date (Ext)', 'PF No Date (Int)']
            if not all_orders.empty and 'Updated Status' in all_orders.columns:
                pending_orders = all_orders[all_orders['Updated Status'].isin(pending_statuses)]
                total_pending = pending_orders['Amount'].sum() if not pending_orders.empty else 0
                pending_count = len(pending_orders)
            else:
                total_pending = 0
                pending_count = 0
            
            with col1:
                st.metric("Total Pending Orders", f"${total_pending:,.0f}", f"{pending_count} orders")
            
            # Open Invoices
            if not all_invoices.empty and 'Status' in all_invoices.columns:
                open_inv = all_invoices[all_invoices['Status'] == 'Open']
                total_outstanding = open_inv['Amount Remaining'].sum() if not open_inv.empty and 'Amount Remaining' in open_inv.columns else 0
                open_count = len(open_inv)
            else:
                total_outstanding = 0
                open_count = 0
            
            with col2:
                st.metric("Total Outstanding", f"${total_outstanding:,.0f}", f"{open_count} invoices")
            
            # Total Revenue
            total_revenue = all_invoices['Amount'].sum() if not all_invoices.empty and 'Amount' in all_invoices.columns else 0
            invoice_count = len(all_invoices)
            
            with col3:
                st.metric("Total Revenue", f"${total_revenue:,.0f}", f"{invoice_count} invoices")
            
            # Pipeline
            if not all_deals.empty and 'Close Status' in all_deals.columns:
                open_statuses = ['Expect', 'Commit', 'Best Case', 'Opportunity']
                open_deals = all_deals[all_deals['Close Status'].isin(open_statuses)]
                total_pipeline = open_deals['Amount'].sum() if not open_deals.empty else 0
                deal_count = len(open_deals)
            else:
                total_pipeline = 0
                deal_count = 0
            
            with col4:
                st.metric("Total Pipeline", f"${total_pipeline:,.0f}", f"{deal_count} deals")
            
            st.markdown("---")
            
            # Customer Breakdown Table
            st.markdown("### 👥 Customer Breakdown")
            
            breakdown_data = []
            for customer_name, customer_orders, customer_invoices, customer_deals, _ in all_customers_data:
                # Calculate metrics for each customer
                if not customer_orders.empty and 'Updated Status' in customer_orders.columns:
                    cust_pending = customer_orders[customer_orders['Updated Status'].isin(pending_statuses)]
                    cust_pending_val = cust_pending['Amount'].sum() if not cust_pending.empty else 0
                else:
                    cust_pending_val = 0
                
                if not customer_invoices.empty and 'Status' in customer_invoices.columns:
                    cust_open = customer_invoices[customer_invoices['Status'] == 'Open']
                    cust_outstanding = cust_open['Amount Remaining'].sum() if not cust_open.empty and 'Amount Remaining' in cust_open.columns else 0
                else:
                    cust_outstanding = 0
                
                cust_revenue = customer_invoices['Amount'].sum() if not customer_invoices.empty and 'Amount' in customer_invoices.columns else 0
                
                if not customer_deals.empty and 'Close Status' in customer_deals.columns:
                    cust_open_deals = customer_deals[customer_deals['Close Status'].isin(['Expect', 'Commit', 'Best Case', 'Opportunity'])]
                    cust_pipeline = cust_open_deals['Amount'].sum() if not cust_open_deals.empty else 0
                else:
                    cust_pipeline = 0
                
                breakdown_data.append({
                    'Customer': customer_name,
                    'Pending Orders': f"${cust_pending_val:,.0f}",
                    'Outstanding': f"${cust_outstanding:,.0f}",
                    'Total Revenue': f"${cust_revenue:,.0f}",
                    'Pipeline': f"${cust_pipeline:,.0f}"
                })
            
            breakdown_df = pd.DataFrame(breakdown_data)
            st.dataframe(breakdown_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # Combined sections with aggregated data
            st.markdown("### 📦 Combined Pending Orders")
            render_pending_orders_section(all_orders)
            
            st.markdown("---")
            st.markdown("### 💳 Combined Open Invoices")
            render_open_invoices_section(all_invoices)
            
            st.markdown("---")
            st.markdown("### 💰 Combined Revenue")
            render_revenue_section(all_invoices)
            
            st.markdown("---")
            st.markdown("### 🎯 Combined Pipeline")
            render_pipeline_section(all_deals, "All Selected Customers")
            
            # Combined Line Item Analysis
            st.markdown("---")
            st.markdown("### 📦 Combined Product Analysis")
            render_line_item_analysis_section(all_line_items, "All Selected Customers")
        
        # Individual customer tabs
        for idx, (tab, (selected_customer, customer_orders, customer_invoices, customer_deals, customer_line_items)) in enumerate(zip(tabs[1:], all_customers_data)):
            with tab:
                st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #06b6d4 100%);
                        padding: 1.5rem 2rem;
                        border-radius: 12px;
                        margin-bottom: 1rem;
                    ">
                        <h1 style="color: white; margin: 0; font-size: 2rem;">📋 {selected_customer}</h1>
                        <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 0.9rem;">
                            Sales Rep: {selected_rep}{date_filter_text} &nbsp;|&nbsp; Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                
                render_pending_orders_section(customer_orders)
                st.markdown("---")
                render_open_invoices_section(customer_invoices)
                st.markdown("---")
                render_revenue_section(customer_invoices)
                st.markdown("---")
                render_on_time_section(customer_orders)
                st.markdown("---")
                render_order_cadence_section(customer_orders)
                st.markdown("---")
                render_order_type_mix_section(customer_orders)
                st.markdown("---")
                render_pipeline_section(customer_deals, selected_customer)
                
                # Line Item Analysis
                st.markdown("---")
                render_line_item_analysis_section(customer_line_items, selected_customer)


# ========== ENTRY POINT ==========
if __name__ == "__main__":
    st.set_page_config(
        page_title="QBR Generator",
        page_icon="📋",
        layout="wide"
    )
    render_yearly_planning_2026()
