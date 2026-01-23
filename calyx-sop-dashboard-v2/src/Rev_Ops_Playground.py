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
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from google.oauth2 import service_account
from googleapiclient.discovery import build
import base64
import io
import re
import uuid

# ========== CONFIGURATION ==========
DEFAULT_SPREADSHEET_ID = "15JhBZ_7aHHZA1W1qsoC2163borL6RYjk0xTDWPmWPfA"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
CACHE_VERSION = "v7_so_line_items_time_filter"


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


def generate_qbr_html(customer_name, rep_name, customer_orders, customer_invoices, customer_deals, customer_line_items=None, customer_ncrs=None, date_label="All Time", pdf_config=None):
    """Generate a professional, customer-facing HTML report for PDF export"""
    
    # Default PDF config - all sections enabled
    if pdf_config is None:
        pdf_config = {
            'exec_summary': True,
            'orders_in_progress': True,
            'open_invoices': True,
            'purchase_history': True,
            'product_mix': True,
            'upcoming_business': True,
            'quality_ncr': True
        }
    
    generated_date = datetime.now().strftime('%B %d, %Y')
    # Use date_label for period display, fallback to current quarter if All Time
    if date_label == "All Time":
        period_display = f"Q{((datetime.now().month - 1) // 3) + 1} {datetime.now().year} Review"
        purchases_label = "Lifetime Purchases"
        orders_label = "Total Orders"
    else:
        period_display = date_label
        purchases_label = f"Purchases ({date_label})"
        orders_label = f"Orders ({date_label})"
    
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
    
    # ===== Generate Line Item Analysis HTML =====
    line_item_html = ""
    if customer_line_items is not None and not customer_line_items.empty:
        # Apply categorization
        li_df = apply_product_categories(customer_line_items.copy())
        li_df = create_unified_product_view(li_df)
        
        # Separate products from fees
        product_df = li_df[li_df['Product Category'] != 'Fees & Adjustments'].copy()
        fees_df = li_df[li_df['Product Category'] == 'Fees & Adjustments'].copy()
        
        total_line_revenue = li_df['Amount'].sum() if 'Amount' in li_df.columns else 0
        product_revenue = product_df['Amount'].sum() if not product_df.empty else 0
        
        # Build category breakdown table using Parent Category with sub-category details
        # Note: We exclude unit counts as they can be misleading (components ≠ finished products)
        category_rows = ""
        parent_col = 'Parent Category' if 'Parent Category' in product_df.columns else 'Unified Category'
        unified_col = 'Unified Category' if 'Unified Category' in product_df.columns else 'Product Category'
        
        if not product_df.empty and parent_col in product_df.columns:
            category_summary = product_df.groupby(parent_col).agg({
                'Amount': 'sum'
            }).reset_index()
            category_summary.columns = ['Category', 'Revenue']
            category_summary = category_summary.sort_values('Revenue', ascending=False)
            category_summary['% of Revenue'] = (category_summary['Revenue'] / product_revenue * 100).round(1) if product_revenue > 0 else 0
            
            for idx, row in category_summary.iterrows():
                bar_width = row['% of Revenue']
                parent_cat = row['Category']
                
                # Main category row
                category_rows += f"""
                <tr>
                    <td style="font-weight: 600;">{parent_cat}</td>
                    <td style="text-align: right; font-weight: 600; color: #059669;">${row['Revenue']:,.0f}</td>
                    <td style="width: 150px;">
                        <div style="background: #e2e8f0; border-radius: 4px; height: 20px; overflow: hidden;">
                            <div style="background: linear-gradient(90deg, #3b82f6, #1d4ed8); height: 100%; width: {bar_width}%;"></div>
                        </div>
                    </td>
                    <td style="text-align: right; font-weight: 500;">{row['% of Revenue']:.1f}%</td>
                </tr>"""
                
                # Add sub-category breakdown for Drams and Concentrates
                if parent_cat in ['Drams', 'Concentrates']:
                    parent_cat_df = product_df[product_df[parent_col] == parent_cat]
                    sub_categories = parent_cat_df[unified_col].unique()
                    
                    if len(sub_categories) > 1 or (len(sub_categories) == 1 and sub_categories[0] != parent_cat):
                        subcat_breakdown = parent_cat_df.groupby(unified_col).agg({
                            'Amount': 'sum'
                        }).reset_index()
                        subcat_breakdown.columns = ['Sub-Category', 'Revenue']
                        subcat_breakdown = subcat_breakdown.sort_values('Revenue', ascending=False)
                        
                        for _, sub_row in subcat_breakdown.iterrows():
                            sub_name = sub_row['Sub-Category']
                            sub_pct = (sub_row['Revenue'] / row['Revenue'] * 100) if row['Revenue'] > 0 else 0
                            category_rows += f"""
                <tr style="background: #f8fafc;">
                    <td style="padding-left: 30px; color: #64748b; font-size: 0.85rem;">↳ {sub_name}</td>
                    <td style="text-align: right; color: #64748b;">${sub_row['Revenue']:,.0f}</td>
                    <td></td>
                    <td style="text-align: right; color: #64748b; font-size: 0.85rem;">{sub_pct:.1f}%</td>
                </tr>"""
        
        line_item_html = f"""
        <div class="section">
            <div class="section-header">
                <div class="section-icon-box blue">📦</div>
                <div>
                    <div class="section-title">Product Mix Analysis</div>
                    <div class="section-subtitle">Breakdown of your purchases by product category</div>
                </div>
            </div>
            
            <div class="stats-row">
                <div class="stat-card purple">
                    <div class="stat-value">${product_revenue:,.0f}</div>
                    <div class="stat-label">Product Purchases</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(category_summary) if category_rows else 0}</div>
                    <div class="stat-label">Categories</div>
                </div>
            </div>
            
            {f'''
            <div class="table-container">
            <table class="data-table product-table">
                <thead>
                    <tr>
                        <th style="text-align: left;">Product Category</th>
                        <th style="text-align: right;">Revenue</th>
                        <th style="text-align: center;">Distribution</th>
                        <th style="text-align: right;">Share</th>
                    </tr>
                </thead>
                <tbody>{category_rows}</tbody>
            </table>
            </div>
            ''' if category_rows else '<p class="no-data">No product category data available.</p>'}
        </div>
        """
    
    # ===== Generate NCR Analysis HTML =====
    ncr_html = ""
    total_orders = len(customer_orders) if not customer_orders.empty else 0
    
    if customer_ncrs is not None and not customer_ncrs.empty:
        ncr_count = len(customer_ncrs)
        
        # Calculate NCR rate as: Total NCRs / Total Orders (more intuitive metric)
        ncr_rate = (ncr_count / total_orders * 100) if total_orders > 0 else 0
        
        # Total Quantity Affected
        total_qty_affected = 0
        if 'Total Quantity Affected' in customer_ncrs.columns:
            total_qty_affected = customer_ncrs['Total Quantity Affected'].sum()
        
        # Source breakdown
        netsuite_count = 0
        hubspot_count = 0
        if 'NCR Source' in customer_ncrs.columns:
            netsuite_count = len(customer_ncrs[customer_ncrs['NCR Source'] == 'NetSuite'])
            hubspot_count = len(customer_ncrs[customer_ncrs['NCR Source'] == 'HubSpot'])
        
        # Resolution time metrics
        avg_resolution = None
        if 'Resolution Days' in customer_ncrs.columns:
            resolution_data = customer_ncrs['Resolution Days'].dropna()
            if len(resolution_data) > 0:
                avg_resolution = resolution_data.mean()
        
        # Issue Type breakdown
        issue_rows = ""
        if 'Issue Type' in customer_ncrs.columns:
            issue_summary = customer_ncrs.groupby('Issue Type').agg({
                'NC Number': 'count' if 'NC Number' in customer_ncrs.columns else 'size',
                'Total Quantity Affected': 'sum' if 'Total Quantity Affected' in customer_ncrs.columns else lambda x: 0
            }).reset_index()
            
            if 'NC Number' in issue_summary.columns:
                issue_summary = issue_summary.rename(columns={'NC Number': 'NCR Count'})
            else:
                issue_summary['NCR Count'] = issue_summary.iloc[:, 1]
            
            if 'Total Quantity Affected' in issue_summary.columns:
                issue_summary = issue_summary.rename(columns={'Total Quantity Affected': 'Qty Affected'})
            else:
                issue_summary['Qty Affected'] = 0
            
            issue_summary = issue_summary.sort_values('NCR Count', ascending=False)
            issue_summary['% of NCRs'] = (issue_summary['NCR Count'] / ncr_count * 100).round(1) if ncr_count > 0 else 0
            
            for _, row in issue_summary.iterrows():
                issue_rows += f"<tr><td>{row['Issue Type']}</td><td style='text-align: center;'>{row['NCR Count']}</td><td style='text-align: right;'>{row['Qty Affected']:,.0f}</td><td style='text-align: right;'>{row['% of NCRs']:.1f}%</td></tr>"
        
        # NCR rate styling - positive/accountability-focused messaging
        if ncr_rate < 2:
            rate_class = "success"
            rate_badge = "EXCELLENT"
        elif ncr_rate < 5:
            rate_class = "success"
            rate_badge = "STRONG"
        elif ncr_rate < 10:
            rate_class = "warning"
            rate_badge = "TRACKING"
        else:
            rate_class = "warning"
            rate_badge = "MONITORING"
        
        resolution_text = f"{avg_resolution:.1f} days" if avg_resolution is not None else "N/A"
        
        ncr_html = f"""
        <div class="section">
            <div class="section-header">
                <div class="section-icon-box {'green' if rate_class == 'success' else 'amber'}">📋</div>
                <div>
                    <div class="section-title">Quality Performance</div>
                    <div class="section-subtitle">Non-conformance tracking and resolution metrics</div>
                </div>
            </div>
            
            <div class="quality-grid">
                <div class="quality-score-card {rate_class}">
                    <div class="quality-badge">{rate_badge}</div>
                    <div class="quality-rate">{ncr_rate:.1f}%</div>
                    <div class="quality-label">NCR Rate</div>
                    <div class="quality-detail">{ncr_count} of {total_orders} orders</div>
                </div>
                <div class="quality-metrics-grid">
                    <div class="quality-metric-card">
                        <div class="qm-value">{ncr_count}</div>
                        <div class="qm-label">Total NCRs</div>
                    </div>
                    <div class="quality-metric-card">
                        <div class="qm-value">{total_qty_affected:,.0f}</div>
                        <div class="qm-label">Units Affected</div>
                    </div>
                    <div class="quality-metric-card">
                        <div class="qm-value">{resolution_text}</div>
                        <div class="qm-label">Avg Resolution</div>
                    </div>
                </div>
            </div>
            
            {f'''
            <h4 style="color: #475569; margin: 30px 0 15px 0; font-size: 1.1rem; font-weight: 600;">Issue Type Analysis</h4>
            <div class="table-container">
            <table class="data-table">
                <thead><tr><th style="text-align: left;">Issue Type</th><th style="text-align: center;">Count</th><th style="text-align: right;">Qty Affected</th><th style="text-align: right;">% of Total</th></tr></thead>
                <tbody>{issue_rows}</tbody>
            </table>
            </div>
            ''' if issue_rows else ''}
        </div>
        """
    else:
        # No NCRs - show positive message
        ncr_html = f"""
        <div class="section">
            <div class="section-header">
                <div class="section-icon-box green">✅</div>
                <div>
                    <div class="section-title">Quality Performance</div>
                    <div class="section-subtitle">Non-conformance tracking and resolution metrics</div>
                </div>
            </div>
            <div class="success-banner">
                <div class="success-emoji">🏆</div>
                <div class="success-content">
                    <h4>Zero Quality Issues</h4>
                    <p>{total_orders} orders delivered with no non-conformance reports</p>
                </div>
            </div>
        </div>
        """
    
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
        order_rows = ""
        for _, order in pending_orders.sort_values('Amount', ascending=False).head(10).iterrows():
            so_num = order.get('SO Number', 'N/A')
            order_type = order.get('Order Type', 'N/A')
            amount = order.get('Amount', 0)
            order_date = order.get('Order Start Date')
            if pd.notna(order_date):
                order_date = order_date.strftime('%b %d, %Y')
            else:
                order_date = 'N/A'
            status_col = 'Updated Status' if 'Updated Status' in order.index else 'Status'
            status = order.get(status_col, 'N/A')
            status_badge = "pa" if "Approval" in str(status) else "pf"
            order_rows += f"""
            <tr>
                <td><strong>{so_num}</strong></td>
                <td>{order_type}</td>
                <td style="text-align: right; font-weight: 600; color: #059669;">${amount:,.0f}</td>
                <td>{order_date}</td>
                <td><span class="status-badge {status_badge}">{status}</span></td>
            </tr>"""
        
        pending_orders_html = f"""
        <table class="data-table">
            <thead><tr><th>Order #</th><th>Type</th><th style="text-align: right;">Value</th><th>Date</th><th>Status</th></tr></thead>
            <tbody>{order_rows}</tbody>
        </table>
        """
    
    # Open Invoices
    open_invoices = customer_invoices[customer_invoices['Status'] == 'Open'] if not customer_invoices.empty else pd.DataFrame()
    open_invoice_count = len(open_invoices)
    open_invoice_value = open_invoices['Amount Remaining'].sum() if not open_invoices.empty and 'Amount Remaining' in open_invoices.columns else 0
    
    # Open Invoices Detail Table (simplified - no aging for customer-facing reports)
    open_invoices_html = ""
    if not open_invoices.empty and 'Due Date' in open_invoices.columns:
        open_inv = open_invoices.copy()
        
        # Individual invoice details
        invoice_rows = ""
        for _, inv in open_inv.sort_values('Due Date', ascending=True).head(10).iterrows():
            doc_num = inv.get('Document Number', 'N/A')
            amount = inv.get('Amount Remaining', 0)
            due_date = inv.get('Due Date')
            if pd.notna(due_date):
                due_date = due_date.strftime('%b %d, %Y')
            else:
                due_date = 'N/A'
            invoice_rows += f"""
            <tr>
                <td><strong>{doc_num}</strong></td>
                <td style="text-align: right;">${amount:,.0f}</td>
                <td>{due_date}</td>
            </tr>"""
        
        open_invoices_html = f"""
        <table class="data-table">
            <thead><tr><th>Invoice #</th><th style="text-align: right;">Amount Due</th><th>Due Date</th></tr></thead>
            <tbody>{invoice_rows}</tbody>
        </table>
        """
    
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
            yearly_rows += f"<tr><td style='font-weight: 600;'>{int(row['Year'])}</td><td style='text-align: right; color: #059669; font-weight: 600;'>${row['Revenue']:,.0f}</td><td style='text-align: center;'>{int(row['Invoices'])}</td></tr>"
        
        yearly_html = f"""
        <table class="data-table compact">
            <thead><tr><th>Year</th><th style="text-align: right;">Revenue</th><th style="text-align: center;">Orders</th></tr></thead>
            <tbody>{yearly_rows}</tbody>
        </table>
        """
    
    # On-Time Performance
    promise_col = 'Customer Promise Date' if 'Customer Promise Date' in customer_orders.columns else 'Customer Promise Last Date to Ship'
    ot_rate = 0
    avg_variance = 0
    completed_count = 0
    if promise_col in customer_orders.columns:
        completed = customer_orders[
            (customer_orders['Status'].isin(['Billed', 'Closed'])) &
            (customer_orders['Actual Ship Date'].notna()) &
            (customer_orders[promise_col].notna())
        ].copy()
        if not completed.empty:
            completed['Variance'] = (completed['Actual Ship Date'] - completed[promise_col]).dt.days
            ot_count = (completed['Variance'] <= 0).sum()
            completed_count = len(completed)
            ot_rate = (ot_count / completed_count * 100) if completed_count > 0 else 0
            avg_variance = completed['Variance'].mean()
    
    # Order Cadence
    avg_cadence = 0
    last_order = 'N/A'
    days_since_last = 0
    if not customer_orders.empty and 'Order Start Date' in customer_orders.columns:
        orders_dated = customer_orders[customer_orders['Order Start Date'].notna()].sort_values('Order Start Date')
        if len(orders_dated) > 1:
            orders_dated['Days Between'] = orders_dated['Order Start Date'].diff().dt.days
            avg_cadence = orders_dated['Days Between'].mean()
            last_order_date = orders_dated['Order Start Date'].max()
            last_order = last_order_date.strftime('%B %d, %Y')
            days_since_last = (pd.Timestamp.now() - last_order_date).days
        elif len(orders_dated) == 1:
            last_order_date = orders_dated['Order Start Date'].max()
            last_order = last_order_date.strftime('%B %d, %Y')
            days_since_last = (pd.Timestamp.now() - last_order_date).days
    
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
                type_rows += f"""
                <tr>
                    <td style="font-weight: 500;">{order_type}</td>
                    <td style="text-align: right; color: #059669; font-weight: 600;">${row['Value']:,.0f}</td>
                    <td style="text-align: center;">{int(row['Count'])}</td>
                    <td style="text-align: right;">{pct:.1f}%</td>
                </tr>"""
            
            order_type_html = f"""
            <table class="data-table">
                <thead><tr><th>Category</th><th style="text-align: right;">Value</th><th style="text-align: center;">Orders</th><th style="text-align: right;">Share</th></tr></thead>
                <tbody>{type_rows}</tbody>
            </table>
            """
    
    # Forecasted Orders (internally called Pipeline)
    pipeline_html = ""
    pipeline_value = 0
    pipeline_count = 0
    
    # Helper to convert internal status to customer-friendly
    # These terms are clearer for customers about where things stand
    def get_customer_friendly_status(status):
        status_map = {
            'Commit': 'Confirmed',      # Basically a done deal
            'Expect': 'Likely',         # High confidence
            'Best Case': 'Tentative',   # Medium confidence, still being finalized
            'Opportunity': 'In Discussion'  # Early stage conversations
        }
        return status_map.get(status, status)
    
    if not customer_deals.empty:
        open_statuses = ['Expect', 'Commit', 'Best Case', 'Opportunity']
        open_deals = customer_deals[customer_deals['Close Status'].isin(open_statuses)]
        if not open_deals.empty:
            pipeline_value = open_deals['Amount'].sum()
            pipeline_count = len(open_deals)
            
            deal_rows = ""
            for _, deal in open_deals.sort_values('Amount', ascending=False).iterrows():
                close_date = deal['Close Date'].strftime('%b %d, %Y') if pd.notna(deal['Close Date']) else 'TBD'
                status = deal['Close Status']
                friendly_status = get_customer_friendly_status(status)
                status_class = "commit" if status == "Commit" else "expect" if status == "Expect" else "opportunity"
                deal_rows += f"""
                <tr>
                    <td style="font-weight: 500;">{deal['Deal Name']}</td>
                    <td style="text-align: right; color: #059669; font-weight: 600;">${deal['Amount']:,.0f}</td>
                    <td><span class="pipeline-badge {status_class}">{friendly_status}</span></td>
                    <td>{close_date}</td>
                </tr>"""
            
            pipeline_html = f"""
            <table class="data-table">
                <thead><tr><th>Order Description</th><th style="text-align: right;">Value</th><th>Status</th><th>Expected Date</th></tr></thead>
                <tbody>{deal_rows}</tbody>
            </table>
            """
    
    # Calculate executive summary metrics
    health_score = 100
    health_factors = []
    
    # Factor 1: Payment health
    if open_invoice_value > total_revenue * 0.1:
        health_score -= 15
        health_factors.append("Outstanding balance to review")
    
    # Factor 2: Quality
    if customer_ncrs is not None and not customer_ncrs.empty:
        ncr_rate_calc = (len(customer_ncrs) / total_orders * 100) if total_orders > 0 else 0
        if ncr_rate_calc > 10:
            health_score -= 20
            health_factors.append("Quality metrics under review")
        elif ncr_rate_calc > 5:
            health_score -= 10
    
    # Factor 3: On-time delivery
    if ot_rate < 70:
        health_score -= 15
        health_factors.append("Delivery performance opportunity")
    elif ot_rate < 85:
        health_score -= 5
    
    # Factor 4: Engagement
    if days_since_last > avg_cadence * 2 and avg_cadence > 0:
        health_score -= 10
        health_factors.append("Time for a check-in")
    
    health_score = max(0, min(100, health_score))
    health_class = "excellent" if health_score >= 90 else "good" if health_score >= 75 else "attention" if health_score >= 60 else "concern"
    health_label = "Excellent" if health_score >= 90 else "Good" if health_score >= 75 else "Opportunity" if health_score >= 60 else "Review"
    
    # ===== Generate HTML =====
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Account Review - {customer_name}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
            
            :root {{
                --primary: #0ea5e9;
                --primary-dark: #0284c7;
                --secondary: #8b5cf6;
                --success: #10b981;
                --warning: #f59e0b;
                --danger: #ef4444;
                --dark: #0f172a;
                --dark-light: #1e293b;
                --gray-100: #f8fafc;
                --gray-200: #e2e8f0;
                --gray-300: #cbd5e1;
                --gray-400: #94a3b8;
                --gray-500: #64748b;
                --gray-600: #475569;
                --text: #1e293b;
                --text-light: #64748b;
            }}
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
                background: #ffffff;
                color: var(--text);
                line-height: 1.7;
                font-size: 14px;
            }}
            
            /* ═══════════════════════════════════════════════════════════════
               COVER SECTION - Premium Hero Design
               ═══════════════════════════════════════════════════════════════ */
            .cover {{
                background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 40%, #0f766e 100%);
                color: white;
                padding: 80px 60px;
                position: relative;
                overflow: hidden;
                min-height: 320px;
            }}
            
            .cover::before {{
                content: '';
                position: absolute;
                top: -100px;
                right: -100px;
                width: 500px;
                height: 500px;
                background: radial-gradient(circle, rgba(14, 165, 233, 0.15) 0%, transparent 70%);
                border-radius: 50%;
            }}
            
            .cover::after {{
                content: '';
                position: absolute;
                bottom: -150px;
                left: -100px;
                width: 400px;
                height: 400px;
                background: radial-gradient(circle, rgba(139, 92, 246, 0.1) 0%, transparent 70%);
                border-radius: 50%;
            }}
            
            .cover-content {{
                position: relative;
                z-index: 1;
            }}
            
            .brand-container {{
                display: flex;
                align-items: center;
                gap: 16px;
                margin-bottom: 50px;
            }}
            
            .brand-logo {{
                width: 50px;
                height: 50px;
                border-radius: 12px;
                object-fit: contain;
                box-shadow: 0 10px 30px rgba(14, 165, 233, 0.3);
            }}
            
            .brand-text {{
                font-size: 1.4rem;
                font-weight: 700;
                letter-spacing: 1px;
                background: linear-gradient(90deg, #fff 0%, #a5f3fc 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}
            
            .cover-title {{
                font-size: 3.5rem;
                font-weight: 800;
                margin-bottom: 8px;
                letter-spacing: -2px;
                line-height: 1.1;
            }}
            
            .cover-subtitle {{
                font-size: 2.2rem;
                font-weight: 300;
                background: linear-gradient(90deg, #67e8f9 0%, #a5f3fc 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 40px;
            }}
            
            .cover-meta {{
                display: flex;
                gap: 35px;
            }}
            
            .meta-pill {{
                display: flex;
                align-items: center;
                gap: 10px;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                padding: 12px 20px;
                border-radius: 50px;
                border: 1px solid rgba(255, 255, 255, 0.15);
            }}
            
            .meta-pill span {{
                font-size: 0.9rem;
                font-weight: 500;
            }}
            
            /* ═══════════════════════════════════════════════════════════════
               MAIN CONTENT AREA
               ═══════════════════════════════════════════════════════════════ */
            .main-content {{
                padding: 60px;
                background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100px);
            }}
            
            /* ═══════════════════════════════════════════════════════════════
               EXECUTIVE SUMMARY - Premium Cards
               ═══════════════════════════════════════════════════════════════ */
            .exec-summary {{
                background: white;
                border-radius: 24px;
                padding: 40px;
                margin-bottom: 50px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 20px 50px -15px rgba(0, 0, 0, 0.1);
                border: 1px solid var(--gray-200);
            }}
            
            .exec-header {{
                display: flex;
                align-items: center;
                gap: 15px;
                margin-bottom: 35px;
            }}
            
            .exec-icon {{
                width: 48px;
                height: 48px;
                background: linear-gradient(135deg, var(--primary) 0%, #06b6d4 100%);
                border-radius: 14px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 22px;
                box-shadow: 0 8px 20px rgba(14, 165, 233, 0.25);
            }}
            
            .exec-title {{
                font-size: 1.5rem;
                font-weight: 700;
                color: var(--dark);
            }}
            
            .exec-grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
                margin-bottom: 30px;
            }}
            
            .metric-card {{
                background: linear-gradient(135deg, var(--gray-100) 0%, white 100%);
                border-radius: 16px;
                padding: 24px;
                text-align: center;
                border: 1px solid var(--gray-200);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }}
            
            .metric-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, var(--primary) 0%, #06b6d4 100%);
                opacity: 0;
                transition: opacity 0.3s;
            }}
            
            .metric-card.highlight::before {{
                opacity: 1;
            }}
            
            .metric-card.green {{ border-color: #86efac; background: linear-gradient(135deg, #f0fdf4 0%, white 100%); }}
            .metric-card.green::before {{ background: linear-gradient(90deg, var(--success) 0%, #34d399 100%); opacity: 1; }}
            
            .metric-card.blue {{ border-color: #93c5fd; background: linear-gradient(135deg, #eff6ff 0%, white 100%); }}
            .metric-card.blue::before {{ background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%); opacity: 1; }}
            
            .metric-value {{
                font-size: 2.2rem;
                font-weight: 800;
                color: var(--dark);
                margin-bottom: 6px;
                letter-spacing: -1px;
            }}
            
            .metric-card.green .metric-value {{ color: #059669; }}
            .metric-card.blue .metric-value {{ color: #2563eb; }}
            .metric-card.amber .metric-value {{ color: #d97706; }}
            
            .metric-label {{
                font-size: 0.8rem;
                font-weight: 600;
                color: var(--gray-500);
                text-transform: uppercase;
                letter-spacing: 0.8px;
            }}
            
            /* Health Score Widget */
            .health-widget {{
                background: linear-gradient(135deg, var(--dark) 0%, var(--dark-light) 100%);
                border-radius: 20px;
                padding: 28px 35px;
                display: flex;
                align-items: center;
                gap: 25px;
                color: white;
            }}
            
            .health-ring {{
                position: relative;
                width: 90px;
                height: 90px;
            }}
            
            .health-ring-bg {{
                position: absolute;
                inset: 0;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.1);
            }}
            
            .health-ring-progress {{
                position: absolute;
                inset: 0;
                border-radius: 50%;
            }}
            
            .health-ring-progress.excellent {{ background: conic-gradient(#10b981 0deg, #10b981 324deg, transparent 324deg); }}
            .health-ring-progress.good {{ background: conic-gradient(#3b82f6 0deg, #3b82f6 270deg, transparent 270deg); }}
            .health-ring-progress.attention {{ background: conic-gradient(#f59e0b 0deg, #f59e0b 216deg, transparent 216deg); }}
            .health-ring-progress.concern {{ background: conic-gradient(#ef4444 0deg, #ef4444 144deg, transparent 144deg); }}
            
            .health-ring-inner {{
                position: absolute;
                inset: 8px;
                border-radius: 50%;
                background: var(--dark);
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            
            .health-score-value {{
                font-size: 1.6rem;
                font-weight: 800;
            }}
            
            .health-info h4 {{
                font-size: 1.15rem;
                font-weight: 700;
                margin-bottom: 6px;
            }}
            
            .health-info p {{
                font-size: 0.9rem;
                opacity: 0.75;
                line-height: 1.5;
            }}
            
            /* ═══════════════════════════════════════════════════════════════
               SECTION STYLING
               ═══════════════════════════════════════════════════════════════ */
            .section {{
                margin-bottom: 50px;
                page-break-inside: avoid;
            }}
            
            .section-header {{
                display: flex;
                align-items: center;
                gap: 18px;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 2px solid var(--gray-200);
            }}
            
            .section-icon-box {{
                width: 52px;
                height: 52px;
                background: linear-gradient(135deg, var(--gray-100) 0%, white 100%);
                border: 2px solid var(--gray-200);
                border-radius: 14px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
            }}
            
            .section-icon-box.blue {{
                background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
                border-color: #93c5fd;
            }}
            
            .section-icon-box.green {{
                background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
                border-color: #86efac;
            }}
            
            .section-icon-box.purple {{
                background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
                border-color: #c4b5fd;
            }}
            
            .section-icon-box.amber {{
                background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
                border-color: #fcd34d;
            }}
            
            .section-title {{
                font-size: 1.5rem;
                font-weight: 700;
                color: var(--dark);
            }}
            
            .section-subtitle {{
                font-size: 0.9rem;
                color: var(--gray-500);
                margin-top: 4px;
            }}
            
            /* Summary Stats Row */
            .stats-row {{
                display: flex;
                gap: 20px;
                margin-bottom: 30px;
            }}
            
            .stat-card {{
                flex: 1;
                background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
                border: 1px solid #bfdbfe;
                border-radius: 16px;
                padding: 24px 30px;
                text-align: center;
            }}
            
            .stat-card.green {{
                background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
                border-color: #86efac;
            }}
            
            .stat-card.purple {{
                background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
                border-color: #c4b5fd;
            }}
            
            .stat-value {{
                font-size: 2.5rem;
                font-weight: 800;
                color: #1e40af;
                letter-spacing: -1px;
            }}
            
            .stat-card.green .stat-value {{ color: #059669; }}
            .stat-card.purple .stat-value {{ color: #7c3aed; }}
            
            .stat-label {{
                font-size: 0.8rem;
                font-weight: 600;
                color: #3b82f6;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                margin-top: 6px;
            }}
            
            .stat-card.green .stat-label {{ color: #059669; }}
            .stat-card.purple .stat-label {{ color: #7c3aed; }}
            
            /* ═══════════════════════════════════════════════════════════════
               DATA TABLES - Premium Design
               ═══════════════════════════════════════════════════════════════ */
            .table-container {{
                background: white;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
                border: 1px solid var(--gray-200);
            }}
            
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 0.9rem;
            }}
            
            .data-table th {{
                background: linear-gradient(135deg, var(--dark) 0%, var(--dark-light) 100%);
                color: white;
                padding: 16px 20px;
                text-align: left;
                font-weight: 600;
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.8px;
            }}
            
            .data-table th:first-child {{
                border-top-left-radius: 0;
            }}
            
            .data-table th:last-child {{
                border-top-right-radius: 0;
            }}
            
            .data-table td {{
                padding: 16px 20px;
                border-bottom: 1px solid var(--gray-200);
                color: var(--gray-600);
            }}
            
            .data-table tr:last-child td {{
                border-bottom: none;
            }}
            
            .data-table tr:nth-child(even) {{
                background: var(--gray-100);
            }}
            
            .data-table tr:hover {{
                background: #f1f5f9;
            }}
            
            /* Status Badges */
            .badge {{
                display: inline-block;
                padding: 6px 14px;
                border-radius: 50px;
                font-size: 0.7rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .badge-pending {{
                background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                color: #92400e;
            }}
            
            .badge-approved {{
                background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
                color: #1e40af;
            }}
            
            .badge-confirmed {{
                background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
                color: #166534;
            }}
            
            .badge-likely {{
                background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
                color: #1e40af;
            }}
            
            .badge-tentative {{
                background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%);
                color: #7c3aed;
            }}
            
            .badge-discussion {{
                background: linear-gradient(135deg, var(--gray-200) 0%, var(--gray-300) 100%);
                color: var(--gray-600);
            }}
            
            /* ═══════════════════════════════════════════════════════════════
               QUALITY SECTION - Premium Cards
               ═══════════════════════════════════════════════════════════════ */
            .quality-grid {{
                display: grid;
                grid-template-columns: 200px 1fr;
                gap: 25px;
                margin-bottom: 30px;
            }}
            
            .quality-score-card {{
                background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
                border: 2px solid #86efac;
                border-radius: 20px;
                padding: 30px;
                text-align: center;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }}
            
            .quality-score-card.success {{
                background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
                border-color: #86efac;
            }}
            
            .quality-score-card.warning {{
                background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
                border-color: #fcd34d;
            }}
            
            .quality-badge {{
                display: inline-block;
                padding: 6px 16px;
                border-radius: 50px;
                font-size: 0.65rem;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 1px;
                background: white;
                margin-bottom: 15px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            }}
            
            .quality-score-card.success .quality-badge {{ color: #166534; }}
            .quality-score-card.warning .quality-badge {{ color: #92400e; }}
            
            .quality-rate {{
                font-size: 3rem;
                font-weight: 800;
                letter-spacing: -2px;
            }}
            
            .quality-score-card.success .quality-rate {{ color: #059669; }}
            .quality-score-card.warning .quality-rate {{ color: #d97706; }}
            
            .quality-label {{
                font-size: 0.85rem;
                color: var(--gray-500);
                font-weight: 600;
                margin-top: 8px;
            }}
            
            .quality-detail {{
                font-size: 0.8rem;
                color: var(--gray-400);
                margin-top: 10px;
            }}
            
            .quality-metrics-grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 15px;
            }}
            
            .quality-metric-card {{
                background: var(--gray-100);
                border: 1px solid var(--gray-200);
                border-radius: 14px;
                padding: 22px;
                text-align: center;
            }}
            
            .qm-value {{
                font-size: 1.8rem;
                font-weight: 800;
                color: var(--dark);
            }}
            
            .qm-label {{
                font-size: 0.7rem;
                font-weight: 600;
                color: var(--gray-500);
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-top: 6px;
            }}
            
            /* Success Banner */
            .success-banner {{
                background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
                border: 2px solid #86efac;
                border-radius: 20px;
                padding: 35px 40px;
                display: flex;
                align-items: center;
                gap: 25px;
            }}
            
            .success-emoji {{
                font-size: 3.5rem;
            }}
            
            .success-content h4 {{
                font-size: 1.4rem;
                font-weight: 700;
                color: #166534;
                margin-bottom: 6px;
            }}
            
            .success-content p {{
                font-size: 1rem;
                color: #15803d;
            }}
            
            /* ═══════════════════════════════════════════════════════════════
               CHARTS SECTION
               ═══════════════════════════════════════════════════════════════ */
            .chart-container {{
                background: var(--gray-100);
                border: 1px solid var(--gray-200);
                border-radius: 16px;
                padding: 25px;
                margin: 25px 0;
                text-align: center;
            }}
            
            .chart-container img {{
                max-width: 100%;
                height: auto;
                border-radius: 12px;
            }}
            
            /* ═══════════════════════════════════════════════════════════════
               NO DATA STATE
               ═══════════════════════════════════════════════════════════════ */
            .no-data {{
                color: var(--gray-400);
                font-style: italic;
                padding: 40px;
                text-align: center;
                background: var(--gray-100);
                border-radius: 16px;
                border: 1px dashed var(--gray-300);
            }}
            
            /* ═══════════════════════════════════════════════════════════════
               FOOTER - Premium Design
               ═══════════════════════════════════════════════════════════════ */
            .footer {{
                margin-top: 60px;
                background: linear-gradient(135deg, var(--dark) 0%, var(--dark-light) 100%);
                padding: 50px 60px;
                text-align: center;
                color: white;
                position: relative;
                overflow: hidden;
            }}
            
            .footer::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, var(--primary) 0%, #06b6d4 50%, var(--secondary) 100%);
            }}
            
            .footer-main {{
                font-size: 1.4rem;
                font-weight: 700;
                margin-bottom: 10px;
            }}
            
            .footer-sub {{
                font-size: 0.9rem;
                opacity: 0.6;
            }}
            
            .footer-brand {{
                margin-top: 25px;
                font-size: 0.8rem;
                opacity: 0.4;
                text-transform: uppercase;
                letter-spacing: 2px;
            }}
            
            /* ═══════════════════════════════════════════════════════════════
               PRINT STYLES
               ═══════════════════════════════════════════════════════════════ */
            @media print {{
                body {{
                    padding: 0;
                }}
                .cover, .footer, .section, .metric-card, .stat-card, .quality-score-card {{
                    -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important;
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
        <!-- ═══════════════════════════════════════════════════════════════
             COVER SECTION
             ═══════════════════════════════════════════════════════════════ -->
        <div class="cover">
            <div class="cover-content">
                <div class="brand-container">
                    <img src="https://raw.githubusercontent.com/corytimmons1688/operations-dashboard-v2/main/calyx-sop-dashboard-v2/calyx_logo.png" alt="Calyx" class="brand-logo">
                    <div class="brand-text">CALYX CONTAINERS</div>
                </div>
                <div class="cover-title">Account Review</div>
                <div class="cover-subtitle">{customer_name}</div>
                <div class="cover-meta">
                    <div class="meta-pill">
                        <span>📅</span>
                        <span>{generated_date}</span>
                    </div>
                    <div class="meta-pill">
                        <span>👤</span>
                        <span>{rep_name}</span>
                    </div>
                    <div class="meta-pill">
                        <span>📊</span>
                        <span>{period_display}</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="main-content">
            {f'''
            <!-- ═══════════════════════════════════════════════════════════════
                 EXECUTIVE SUMMARY
                 ═══════════════════════════════════════════════════════════════ -->
            <div class="exec-summary">
                <div class="exec-header">
                    <div class="exec-icon">📊</div>
                    <div class="exec-title">Executive Summary</div>
                </div>
                <div class="exec-grid">
                    <div class="metric-card green highlight">
                        <div class="metric-value">${total_revenue:,.0f}</div>
                        <div class="metric-label">{purchases_label}</div>
                    </div>
                    <div class="metric-card blue highlight">
                        <div class="metric-value">{total_invoices}</div>
                        <div class="metric-label">{orders_label}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${pending_value:,.0f}</div>
                        <div class="metric-label">In Progress</div>
                    </div>
                    <div class="metric-card {'green' if ot_rate >= 90 else 'amber' if ot_rate >= 70 else ''}">
                        <div class="metric-value">{ot_rate:.0f}%</div>
                        <div class="metric-label">On-Time Rate</div>
                    </div>
                </div>
                <div class="health-widget">
                    <div class="health-ring">
                        <div class="health-ring-bg"></div>
                        <div class="health-ring-progress {health_class}"></div>
                        <div class="health-ring-inner">
                            <div class="health-score-value">{health_score}</div>
                        </div>
                    </div>
                    <div class="health-info">
                        <h4>Account Health: {health_label}</h4>
                        <p>{'All metrics looking strong! Keep up the great partnership.' if not health_factors else ' · '.join(health_factors)}</p>
                    </div>
                </div>
            </div>
            ''' if pdf_config.get('exec_summary', True) else ''}
            
            {f'''
            <!-- ═══════════════════════════════════════════════════════════════
                 ORDERS IN PROGRESS
                 ═══════════════════════════════════════════════════════════════ -->
            <div class="section">
                <div class="section-header">
                    <div class="section-icon-box blue">📦</div>
                    <div>
                        <div class="section-title">Orders in Progress</div>
                        <div class="section-subtitle">Active orders currently being processed</div>
                    </div>
                </div>
                <div class="stats-row">
                    <div class="stat-card">
                        <div class="stat-value">{pending_count}</div>
                        <div class="stat-label">Active Orders</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${pending_value:,.0f}</div>
                        <div class="stat-label">Total Value</div>
                    </div>
                </div>
                {f'<div class="table-container">{pending_orders_html}</div>' if pending_orders_html else '<p class="no-data">No orders currently in progress</p>'}
            </div>
            ''' if pdf_config.get('orders_in_progress', True) else ''}
            
            {f'''
            <!-- ═══════════════════════════════════════════════════════════════
                 ACCOUNT BALANCE
                 ═══════════════════════════════════════════════════════════════ -->
            <div class="section">
                <div class="section-header">
                    <div class="section-icon-box green">💳</div>
                    <div>
                        <div class="section-title">Account Balance</div>
                        <div class="section-subtitle">Outstanding invoices and payment status</div>
                    </div>
                </div>
                <div class="stats-row">
                    <div class="stat-card">
                        <div class="stat-value">{open_invoice_count}</div>
                        <div class="stat-label">Open Invoices</div>
                    </div>
                    <div class="stat-card green">
                        <div class="stat-value">${open_invoice_value:,.0f}</div>
                        <div class="stat-label">Balance Due</div>
                    </div>
                </div>
                {f'<div class="table-container">{open_invoices_html}</div>' if open_invoices_html else '<div class="success-banner"><div class="success-emoji">✨</div><div class="success-content"><h4>Account Current</h4><p>No outstanding invoices — thank you for staying current!</p></div></div>'}
            </div>
            ''' if pdf_config.get('open_invoices', True) else ''}
            
            {f'''
            <!-- ═══════════════════════════════════════════════════════════════
                 PURCHASE HISTORY
                 ═══════════════════════════════════════════════════════════════ -->
            <div class="section">
                <div class="section-header">
                    <div class="section-icon-box purple">💰</div>
                    <div>
                        <div class="section-title">Purchase History</div>
                        <div class="section-subtitle">Historical purchasing trends and patterns</div>
                    </div>
                </div>
                <div class="stats-row">
                    <div class="stat-card purple">
                        <div class="stat-value">${total_revenue:,.0f}</div>
                        <div class="stat-label">Lifetime Value</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${avg_invoice:,.0f}</div>
                        <div class="stat-label">Avg Order</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{avg_cadence:.0f}</div>
                        <div class="stat-label">Days Between Orders</div>
                    </div>
                </div>
                {f'<div class="table-container">{yearly_html}</div>' if yearly_html else ''}
                {charts_html.get('revenue', '')}
            </div>
            
            <!-- ═══════════════════════════════════════════════════════════════
                 DELIVERY PERFORMANCE
                 ═══════════════════════════════════════════════════════════════ -->
            <div class="section">
                <div class="section-header">
                    <div class="section-icon-box amber">⏱️</div>
                    <div>
                        <div class="section-title">Delivery Performance</div>
                        <div class="section-subtitle">On-time delivery metrics and trends</div>
                    </div>
                </div>
                <div class="stats-row">
                    <div class="stat-card {'green' if ot_rate >= 90 else ''}">
                        <div class="stat-value">{ot_rate:.1f}%</div>
                        <div class="stat-label">On-Time Rate</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{avg_variance:+.1f}</div>
                        <div class="stat-label">Avg Days Variance</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{completed_count}</div>
                        <div class="stat-label">Orders Measured</div>
                    </div>
                </div>
                {charts_html.get('ontime', '')}
            </div>
            ''' if pdf_config.get('purchase_history', True) else ''}
            
            {f'''
            <!-- ═══════════════════════════════════════════════════════════════
                 UPCOMING BUSINESS
                 ═══════════════════════════════════════════════════════════════ -->
            <div class="section">
                <div class="section-header">
                    <div class="section-icon-box green">🎯</div>
                    <div>
                        <div class="section-title">Upcoming Business</div>
                        <div class="section-subtitle">Business opportunities in progress</div>
                    </div>
                </div>
                <div class="stats-row">
                    <div class="stat-card green">
                        <div class="stat-value">${pipeline_value:,.0f}</div>
                        <div class="stat-label">Projected Value</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{pipeline_count}</div>
                        <div class="stat-label">Opportunities</div>
                    </div>
                </div>
                {f'<div class="table-container">{pipeline_html}</div>' if pipeline_html else ''}
            </div>
            ''' if pdf_config.get('upcoming_business', True) and pipeline_html else ''}
            
            {line_item_html if pdf_config.get('product_mix', True) else ''}
            
            {ncr_html if pdf_config.get('quality_ncr', True) else ''}
        </div>
        
        <!-- ═══════════════════════════════════════════════════════════════
             FOOTER
             ═══════════════════════════════════════════════════════════════ -->
        <div class="footer">
            <div class="footer-main">Thank you for your partnership!</div>
            <div class="footer-sub">Questions? Reach out to {rep_name}</div>
            <div class="footer-brand">Calyx Containers · {generated_date}</div>
        </div>
    </body>
    </html>
    """
    
    return html
    
    # ===== Generate NCR Analysis HTML =====
    ncr_html = ""
    total_orders = len(customer_orders) if not customer_orders.empty else 0
    
    if customer_ncrs is not None and not customer_ncrs.empty:
        ncr_count = len(customer_ncrs)
        
        # Get unique Sales Orders with NCRs
        ncr_so_numbers = set()
        if 'Sales Order' in customer_ncrs.columns:
            ncr_so_numbers = set(customer_ncrs['Sales Order'].dropna().unique())
            ncr_so_numbers = {str(so).strip() for so in ncr_so_numbers if str(so).strip()}
        
        orders_with_ncrs = len(ncr_so_numbers)
        ncr_rate = (orders_with_ncrs / total_orders * 100) if total_orders > 0 else 0
        
        # Total Quantity Affected
        total_qty_affected = 0
        if 'Total Quantity Affected' in customer_ncrs.columns:
            total_qty_affected = customer_ncrs['Total Quantity Affected'].sum()
        
        # Source breakdown
        netsuite_count = 0
        hubspot_count = 0
        if 'NCR Source' in customer_ncrs.columns:
            netsuite_count = len(customer_ncrs[customer_ncrs['NCR Source'] == 'NetSuite'])
            hubspot_count = len(customer_ncrs[customer_ncrs['NCR Source'] == 'HubSpot'])
        
        # Resolution time metrics
        avg_resolution = None
        if 'Resolution Days' in customer_ncrs.columns:
            resolution_data = customer_ncrs['Resolution Days'].dropna()
            if len(resolution_data) > 0:
                avg_resolution = resolution_data.mean()
        
        # Issue Type breakdown
        issue_rows = ""
        if 'Issue Type' in customer_ncrs.columns:
            issue_summary = customer_ncrs.groupby('Issue Type').agg({
                'NC Number': 'count' if 'NC Number' in customer_ncrs.columns else 'size',
                'Total Quantity Affected': 'sum' if 'Total Quantity Affected' in customer_ncrs.columns else lambda x: 0
            }).reset_index()
            
            if 'NC Number' in issue_summary.columns:
                issue_summary = issue_summary.rename(columns={'NC Number': 'NCR Count'})
            else:
                issue_summary['NCR Count'] = issue_summary.iloc[:, 1]
            
            if 'Total Quantity Affected' in issue_summary.columns:
                issue_summary = issue_summary.rename(columns={'Total Quantity Affected': 'Qty Affected'})
            else:
                issue_summary['Qty Affected'] = 0
            
            issue_summary = issue_summary.sort_values('NCR Count', ascending=False)
            issue_summary['% of NCRs'] = (issue_summary['NCR Count'] / ncr_count * 100).round(1) if ncr_count > 0 else 0
            
            for _, row in issue_summary.iterrows():
                issue_rows += f"<tr><td>{row['Issue Type']}</td><td>{row['NCR Count']}</td><td>{row['Qty Affected']:,.0f}</td><td>{row['% of NCRs']:.1f}%</td></tr>"
        
        # NCR rate color
        rate_class = "success" if ncr_rate < 5 else "warning" if ncr_rate < 10 else ""
        
        # Build source breakdown HTML
        source_html = ""
        if netsuite_count > 0 or hubspot_count > 0:
            resolution_text = f"{avg_resolution:.1f} days" if avg_resolution is not None else "N/A"
            source_html = f"""
            <div style="display: flex; gap: 15px; margin: 15px 0; flex-wrap: wrap;">
                <div style="background: #f1f5f9; padding: 10px 15px; border-radius: 6px; border-left: 3px solid #3b82f6;">
                    <div style="color: #64748b; font-size: 0.75rem;">NetSuite (Nov 2024+)</div>
                    <div style="color: #1e293b; font-weight: 600;">{netsuite_count} NCRs</div>
                </div>
                <div style="background: #f1f5f9; padding: 10px 15px; border-radius: 6px; border-left: 3px solid #f59e0b;">
                    <div style="color: #64748b; font-size: 0.75rem;">HubSpot (Historical)</div>
                    <div style="color: #1e293b; font-weight: 600;">{hubspot_count} NCRs</div>
                </div>
                <div style="background: #f1f5f9; padding: 10px 15px; border-radius: 6px; border-left: 3px solid #10b981;">
                    <div style="color: #64748b; font-size: 0.75rem;">Avg Resolution</div>
                    <div style="color: #1e293b; font-weight: 600;">{resolution_text}</div>
                </div>
            </div>
            """
        
        ncr_html = f"""
        <div class="section">
            <div class="section-title">⚠️ Quality & Non-Conformance</div>
            <div class="metric-row">
                <div class="metric-card">
                    <div class="metric-label">NCR Rate</div>
                    <div class="metric-value {rate_class}">{ncr_rate:.1f}%</div>
                    <div style="color: #64748b; font-size: 0.8rem;">{orders_with_ncrs} of {total_orders} orders</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total NCRs</div>
                    <div class="metric-value">{ncr_count}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Qty Affected</div>
                    <div class="metric-value">{total_qty_affected:,.0f}</div>
                </div>
            </div>
            {source_html}
            {f'''
            <h4 style="color: #475569; margin: 20px 0 10px 0;">Issue Type Breakdown</h4>
            <table class="data-table">
                <thead><tr><th>Issue Type</th><th>NCR Count</th><th>Qty Affected</th><th>% of NCRs</th></tr></thead>
                <tbody>{issue_rows}</tbody>
            </table>
            ''' if issue_rows else ''}
        </div>
        """
    else:
        # No NCRs - show positive message
        ncr_html = f"""
        <div class="section">
            <div class="section-title">⚠️ Quality & Non-Conformance</div>
            <div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); padding: 20px; border-radius: 8px; border-left: 4px solid #10b981;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 1.5rem;">✅</span>
                    <div>
                        <div style="color: #065f46; font-weight: 700;">No Quality Issues Recorded</div>
                        <div style="color: #047857; font-size: 0.9rem;">{f'{total_orders} orders' if total_orders > 0 else 'Orders'} with zero NCRs on file</div>
                    </div>
                </div>
            </div>
        </div>
        """
    
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
                    <div class="metric-label">Projected Value</div>
                    <div class="metric-value">${pipeline_value:,.0f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Opportunities</div>
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
                    <div class="metric-label">{purchases_label}</div>
                    <div class="metric-value success">${total_revenue:,.0f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">{orders_label}</div>
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
        
        {line_item_html}
        
        {ncr_html}
        
        <div class="footer">
            <p>Prepared by Calyx Containers &nbsp;|&nbsp; {generated_date}</p>
            <p style="margin-top: 5px;">Thank you for your partnership!</p>
        </div>
    </body>
    </html>
    """
    
    return html


def generate_combined_qbr_html(customers_data, rep_name, date_label="All Time", pdf_config=None):
    """
    Generate a combined HTML report for multiple customers.
    customers_data is a list of tuples: (customer_name, customer_orders, customer_invoices, customer_deals)
    """
    # Default PDF config
    if pdf_config is None:
        pdf_config = {
            'exec_summary': True,
            'orders_in_progress': True,
            'open_invoices': True,
            'purchase_history': True,
            'product_mix': True,
            'upcoming_business': True,
            'quality_ncr': True
        }
    
    generated_date = datetime.now().strftime('%B %d, %Y')
    # Use date_label for period display and labels
    if date_label == "All Time":
        period_display = f"Q{((datetime.now().month - 1) // 3) + 1} {datetime.now().year} Review"
        revenue_label = "Portfolio Revenue"
        orders_label = "Total Orders"
    else:
        period_display = date_label
        revenue_label = f"Revenue ({date_label})"
        orders_label = f"Orders ({date_label})"
    num_customers = len(customers_data)
    customer_names = [c[0] for c in customers_data]
    
    # Start with professional header and styles
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Portfolio Review - {rep_name}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
            
            :root {{
                --primary: #0ea5e9;
                --primary-dark: #0284c7;
                --secondary: #8b5cf6;
                --success: #10b981;
                --warning: #f59e0b;
                --danger: #ef4444;
                --dark: #0f172a;
                --dark-light: #1e293b;
                --gray-100: #f8fafc;
                --gray-200: #e2e8f0;
                --gray-300: #cbd5e1;
                --gray-400: #94a3b8;
                --gray-500: #64748b;
                --gray-600: #475569;
                --text: #1e293b;
                --text-light: #64748b;
            }}
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
                background: #ffffff;
                color: var(--text);
                line-height: 1.7;
                font-size: 14px;
            }}
            
            /* Portfolio Cover - Premium Design */
            .portfolio-cover {{
                background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 40%, #0f766e 100%);
                color: white;
                padding: 80px 60px;
                position: relative;
                overflow: hidden;
                page-break-after: always;
                min-height: 500px;
            }}
            
            .portfolio-cover::before {{
                content: '';
                position: absolute;
                top: -100px;
                right: -100px;
                width: 500px;
                height: 500px;
                background: radial-gradient(circle, rgba(14, 165, 233, 0.15) 0%, transparent 70%);
                border-radius: 50%;
            }}
            
            .portfolio-cover::after {{
                content: '';
                position: absolute;
                bottom: -150px;
                left: -100px;
                width: 400px;
                height: 400px;
                background: radial-gradient(circle, rgba(139, 92, 246, 0.1) 0%, transparent 70%);
                border-radius: 50%;
            }}
            
            .portfolio-cover .brand-container {{
                display: flex;
                align-items: center;
                gap: 16px;
                margin-bottom: 50px;
                position: relative;
                z-index: 1;
            }}
            
            .portfolio-cover .brand-logo {{
                width: 50px;
                height: 50px;
                border-radius: 12px;
                object-fit: contain;
                box-shadow: 0 10px 30px rgba(14, 165, 233, 0.3);
            }}
            
            .portfolio-cover .brand-text {{
                font-size: 1.4rem;
                font-weight: 700;
                letter-spacing: 1px;
                background: linear-gradient(90deg, #fff 0%, #a5f3fc 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}
            
            .portfolio-cover h1 {{
                font-size: 3.5rem;
                font-weight: 800;
                margin-bottom: 10px;
                letter-spacing: -2px;
                position: relative;
                z-index: 1;
            }}
            
            .portfolio-cover .subtitle {{
                font-size: 2.2rem;
                font-weight: 300;
                background: linear-gradient(90deg, #67e8f9 0%, #a5f3fc 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 40px;
                position: relative;
                z-index: 1;
            }}
            
            .portfolio-meta {{
                display: flex;
                gap: 25px;
                margin-bottom: 50px;
                position: relative;
                z-index: 1;
            }}
            
            .portfolio-meta .meta-pill {{
                display: flex;
                align-items: center;
                gap: 10px;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                padding: 12px 20px;
                border-radius: 50px;
                border: 1px solid rgba(255, 255, 255, 0.15);
                font-size: 0.9rem;
            }}
            
            .portfolio-stats {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin-top: 40px;
                position: relative;
                z-index: 1;
            }}
            
            .portfolio-stat {{
                background: rgba(255,255,255,0.08);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 16px;
                padding: 30px;
                text-align: center;
            }}
            
            .portfolio-stat-value {{
                font-size: 2.8rem;
                font-weight: 800;
                background: linear-gradient(90deg, #67e8f9 0%, #a5f3fc 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}
            
            .portfolio-stat-label {{
                font-size: 0.8rem;
                opacity: 0.7;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-top: 10px;
            }}
            
            .account-list {{
                background: rgba(255,255,255,0.05);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 16px;
                padding: 25px 30px;
                margin-top: 40px;
                position: relative;
                z-index: 1;
            }}
            
            .account-list-title {{
                font-size: 0.8rem;
                text-transform: uppercase;
                letter-spacing: 1px;
                opacity: 0.6;
                margin-bottom: 15px;
            }}
            
            .account-list-items {{
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
            }}
            
            .account-tag {{
                background: rgba(103, 232, 249, 0.15);
                border: 1px solid rgba(103, 232, 249, 0.3);
                color: #a5f3fc;
                padding: 8px 16px;
                border-radius: 50px;
                font-size: 0.85rem;
                font-weight: 500;
            }}
            
            /* Customer Section Divider */
            .customer-section {{
                page-break-before: always;
            }}
            
            .customer-header {{
                background: linear-gradient(135deg, var(--dark) 0%, var(--dark-light) 100%);
                color: white;
                padding: 50px 60px;
                margin-bottom: 0;
                position: relative;
                overflow: hidden;
            }}
            
            .customer-header::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, var(--primary) 0%, #06b6d4 50%, var(--secondary) 100%);
            }}
            
            .customer-header h2 {{
                font-size: 2.2rem;
                font-weight: 800;
                margin-bottom: 10px;
                letter-spacing: -1px;
            }}
            
            .customer-header .customer-meta {{
                display: flex;
                gap: 30px;
                font-size: 0.9rem;
                opacity: 0.75;
            }}
            
            /* Executive Summary styles - Premium */
            .exec-summary {{
                background: white;
                border-radius: 24px;
                padding: 40px;
                margin-bottom: 50px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 20px 50px -15px rgba(0, 0, 0, 0.1);
                border: 1px solid var(--gray-200);
            }}
            
            .exec-header {{
                display: flex;
                align-items: center;
                gap: 15px;
                margin-bottom: 35px;
            }}
            
            .exec-icon {{
                width: 48px;
                height: 48px;
                background: linear-gradient(135deg, var(--primary) 0%, #06b6d4 100%);
                border-radius: 14px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 22px;
                box-shadow: 0 8px 20px rgba(14, 165, 233, 0.25);
            }}
            
            .exec-title {{
                font-size: 1.5rem;
                font-weight: 700;
                color: var(--dark);
            }}
            
            .exec-grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
                margin-bottom: 30px;
            }}
            
            .metric-card {{
                background: linear-gradient(135deg, var(--gray-100) 0%, white 100%);
                border-radius: 16px;
                padding: 24px;
                text-align: center;
                border: 1px solid var(--gray-200);
                position: relative;
                overflow: hidden;
            }}
            
            .metric-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, var(--primary) 0%, #06b6d4 100%);
                opacity: 0;
            }}
            
            .metric-card.highlight::before {{ opacity: 1; }}
            .metric-card.green {{ border-color: #86efac; background: linear-gradient(135deg, #f0fdf4 0%, white 100%); }}
            .metric-card.green::before {{ background: linear-gradient(90deg, var(--success) 0%, #34d399 100%); opacity: 1; }}
            .metric-card.blue {{ border-color: #93c5fd; background: linear-gradient(135deg, #eff6ff 0%, white 100%); }}
            .metric-card.blue::before {{ background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%); opacity: 1; }}
            
            .metric-value {{
                font-size: 2.2rem;
                font-weight: 800;
                color: var(--dark);
                margin-bottom: 6px;
                letter-spacing: -1px;
            }}
            
            .metric-card.green .metric-value {{ color: #059669; }}
            .metric-card.blue .metric-value {{ color: #2563eb; }}
            .metric-card.amber .metric-value {{ color: #d97706; }}
            
            .metric-label {{
                font-size: 0.8rem;
                font-weight: 600;
                color: var(--gray-500);
                text-transform: uppercase;
                letter-spacing: 0.8px;
            }}
            
            /* Health Widget - Premium */
            .health-widget {{
                background: linear-gradient(135deg, var(--dark) 0%, var(--dark-light) 100%);
                border-radius: 20px;
                padding: 28px 35px;
                display: flex;
                align-items: center;
                gap: 25px;
                color: white;
            }}
            
            .health-ring {{
                position: relative;
                width: 90px;
                height: 90px;
            }}
            
            .health-ring-bg {{
                position: absolute;
                inset: 0;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.1);
            }}
            
            .health-ring-progress {{
                position: absolute;
                inset: 0;
                border-radius: 50%;
            }}
            
            .health-ring-progress.excellent {{ background: conic-gradient(#10b981 0deg, #10b981 324deg, transparent 324deg); }}
            .health-ring-progress.good {{ background: conic-gradient(#3b82f6 0deg, #3b82f6 270deg, transparent 270deg); }}
            .health-ring-progress.attention {{ background: conic-gradient(#f59e0b 0deg, #f59e0b 216deg, transparent 216deg); }}
            .health-ring-progress.concern {{ background: conic-gradient(#ef4444 0deg, #ef4444 144deg, transparent 144deg); }}
            
            .health-ring-inner {{
                position: absolute;
                inset: 8px;
                border-radius: 50%;
                background: var(--dark);
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            
            .health-score-value {{
                font-size: 1.6rem;
                font-weight: 800;
            }}
            
            .health-info h4 {{
                font-size: 1.15rem;
                font-weight: 700;
                margin-bottom: 6px;
            }}
            
            .health-info p {{
                font-size: 0.9rem;
                opacity: 0.75;
                line-height: 1.5;
            }}
            
            /* Rest of styles - Premium */
            .main-content {{
                padding: 60px;
                background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100px);
            }}
            
            .section {{
                margin-bottom: 50px;
                page-break-inside: avoid;
            }}
            
            .section-header {{
                display: flex;
                align-items: center;
                gap: 18px;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 2px solid var(--gray-200);
            }}
            
            .section-icon-box {{
                width: 52px;
                height: 52px;
                background: linear-gradient(135deg, var(--gray-100) 0%, white 100%);
                border: 2px solid var(--gray-200);
                border-radius: 14px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
            }}
            
            .section-icon-box.blue {{ background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border-color: #93c5fd; }}
            .section-icon-box.green {{ background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border-color: #86efac; }}
            .section-icon-box.purple {{ background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%); border-color: #c4b5fd; }}
            .section-icon-box.amber {{ background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); border-color: #fcd34d; }}
            
            .section-title {{
                font-size: 1.5rem;
                font-weight: 700;
                color: var(--dark);
            }}
            
            .section-subtitle {{
                font-size: 0.9rem;
                color: var(--gray-500);
                margin-top: 4px;
            }}
            
            .stats-row {{
                display: flex;
                gap: 20px;
                margin-bottom: 30px;
            }}
            
            .stat-card {{
                flex: 1;
                background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
                border: 1px solid #bfdbfe;
                border-radius: 16px;
                padding: 24px 30px;
                text-align: center;
            }}
            
            .stat-card.green {{ background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border-color: #86efac; }}
            .stat-card.purple {{ background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%); border-color: #c4b5fd; }}
            
            .stat-value {{
                font-size: 2.5rem;
                font-weight: 800;
                color: #1e40af;
                letter-spacing: -1px;
            }}
            
            .stat-card.green .stat-value {{ color: #059669; }}
            .stat-card.purple .stat-value {{ color: #7c3aed; }}
            
            .stat-label {{
                font-size: 0.8rem;
                font-weight: 600;
                color: #3b82f6;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                margin-top: 6px;
            }}
            
            .stat-card.green .stat-label {{ color: #059669; }}
            .stat-card.purple .stat-label {{ color: #7c3aed; }}
            
            .table-container {{
                background: white;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
                border: 1px solid var(--gray-200);
            }}
            
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 0.9rem;
            }}
            
            .data-table th {{
                background: linear-gradient(135deg, var(--dark) 0%, var(--dark-light) 100%);
                color: white;
                padding: 12px 14px;
                text-align: left;
                font-weight: 600;
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .data-table td {{
                padding: 12px 14px;
                border-bottom: 1px solid #e2e8f0;
            }}
            
            .data-table tr:nth-child(even) {{
                background: #f8fafc;
            }}
            
            .chart-container {{
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 15px;
                margin: 15px 0;
                text-align: center;
            }}
            
            .chart-container img {{
                max-width: 100%;
                height: auto;
                border-radius: 8px;
            }}
            
            /* Status badges */
            .status-badge {{
                display: inline-block;
                padding: 3px 10px;
                border-radius: 15px;
                font-size: 0.7rem;
                font-weight: 600;
                text-transform: uppercase;
            }}
            
            .status-badge.pa {{
                background: #fef3c7;
                color: #92400e;
            }}
            
            .status-badge.pf {{
                background: #dbeafe;
                color: #1e40af;
            }}
            
            /* Quality styling */
            .quality-summary {{
                display: flex;
                gap: 20px;
                margin-bottom: 20px;
            }}
            
            .quality-card {{
                background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
                border: 2px solid #86efac;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                min-width: 160px;
            }}
            
            .quality-card.success {{ background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border-color: #86efac; }}
            .quality-card.warning {{ background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); border-color: #fcd34d; }}
            .quality-card.danger {{ background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%); border-color: #fca5a5; }}
            
            .quality-badge {{
                display: inline-block;
                padding: 3px 10px;
                border-radius: 15px;
                font-size: 0.65rem;
                font-weight: 700;
                text-transform: uppercase;
                background: white;
                margin-bottom: 8px;
            }}
            
            .quality-rate {{ font-size: 2rem; font-weight: 800; }}
            .quality-card.success .quality-rate {{ color: #166534; }}
            .quality-card.warning .quality-rate {{ color: #92400e; }}
            .quality-card.danger .quality-rate {{ color: #991b1b; }}
            
            .quality-label {{ font-size: 0.85rem; color: var(--gray-500); font-weight: 600; margin-top: 8px; }}
            .quality-detail {{ font-size: 0.8rem; color: var(--gray-400); margin-top: 10px; }}
            
            /* Quality Grid - Premium */
            .quality-grid {{
                display: grid;
                grid-template-columns: 200px 1fr;
                gap: 25px;
                margin-bottom: 30px;
            }}
            
            .quality-score-card {{
                background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
                border: 2px solid #86efac;
                border-radius: 20px;
                padding: 30px;
                text-align: center;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }}
            
            .quality-score-card.success {{ background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border-color: #86efac; }}
            .quality-score-card.warning {{ background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); border-color: #fcd34d; }}
            
            .quality-metrics-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }}
            .quality-metric-card {{ background: var(--gray-100); border: 1px solid var(--gray-200); border-radius: 14px; padding: 22px; text-align: center; }}
            .qm-value {{ font-size: 1.8rem; font-weight: 800; color: var(--dark); }}
            .qm-label {{ font-size: 0.7rem; font-weight: 600; color: var(--gray-500); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 6px; }}
            
            .success-banner {{
                background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
                border: 2px solid #86efac;
                border-radius: 20px;
                padding: 35px 40px;
                display: flex;
                align-items: center;
                gap: 25px;
            }}
            
            .success-emoji {{ font-size: 3.5rem; }}
            .success-content h4 {{ font-size: 1.4rem; font-weight: 700; color: #166534; margin-bottom: 6px; }}
            .success-content p {{ font-size: 1rem; color: #15803d; }}
            
            .no-data {{
                color: var(--gray-400);
                font-style: italic;
                padding: 40px;
                text-align: center;
                background: var(--gray-100);
                border-radius: 16px;
                border: 1px dashed var(--gray-300);
            }}
            
            /* Product table styling */
            .product-table td:nth-child(2) {{
                text-align: right;
                font-weight: 600;
                color: #059669;
            }}
            
            /* Footer - Premium */
            .portfolio-footer {{
                margin-top: 60px;
                background: linear-gradient(135deg, var(--dark) 0%, var(--dark-light) 100%);
                padding: 50px 60px;
                text-align: center;
                color: white;
                position: relative;
                overflow: hidden;
            }}
            
            .portfolio-footer::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, var(--primary) 0%, #06b6d4 50%, var(--secondary) 100%);
            }}
            
            .footer-main {{
                font-size: 1.4rem;
                font-weight: 700;
                margin-bottom: 10px;
            }}
            
            .footer-sub {{
                font-size: 0.9rem;
                opacity: 0.6;
            }}
            
            .footer-brand {{
                margin-top: 25px;
                font-size: 0.8rem;
                opacity: 0.4;
                text-transform: uppercase;
                letter-spacing: 2px;
            }}
            
            @media print {{
                body {{ padding: 0; }}
                .portfolio-cover, .customer-header, .metric-card, .stat-card, .quality-score-card {{
                    -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important;
                }}
                .section {{ page-break-inside: avoid; }}
                .chart-container {{ page-break-inside: avoid; }}
                .customer-section {{ page-break-before: always; }}
            }}
        </style>
    </head>
    <body>
    """
    
    # Calculate portfolio-level stats
    total_portfolio_revenue = 0
    total_portfolio_orders = 0
    total_pipeline_value = 0
    
    for customer_data in customers_data:
        customer_invoices = customer_data[2]
        customer_deals = customer_data[3]
        if not customer_invoices.empty and 'Amount' in customer_invoices.columns:
            total_portfolio_revenue += customer_invoices['Amount'].sum()
            total_portfolio_orders += len(customer_invoices)
        if not customer_deals.empty and 'Amount' in customer_deals.columns:
            open_statuses = ['Expect', 'Commit', 'Best Case', 'Opportunity']
            if 'Close Status' in customer_deals.columns:
                open_deals = customer_deals[customer_deals['Close Status'].isin(open_statuses)]
                total_pipeline_value += open_deals['Amount'].sum()
    
    # Portfolio Cover Page
    html += f"""
        <div class="portfolio-cover">
            <div class="brand-container">
                <img src="https://raw.githubusercontent.com/corytimmons1688/operations-dashboard-v2/main/calyx-sop-dashboard-v2/calyx_logo.png" alt="Calyx" class="brand-logo">
                <div class="brand-text">CALYX CONTAINERS</div>
            </div>
            <h1>Portfolio Review</h1>
            <div class="subtitle">{period_display}</div>
            
            <div class="portfolio-meta">
                <div class="meta-pill">
                    <span>📅</span>
                    <span>{generated_date}</span>
                </div>
                <div class="meta-pill">
                    <span>👤</span>
                    <span>{rep_name}</span>
                </div>
                <span>📊 {num_customers} Accounts</span>
            </div>
            
            <div class="portfolio-stats">
                <div class="portfolio-stat">
                    <div class="portfolio-stat-value">${total_portfolio_revenue:,.0f}</div>
                    <div class="portfolio-stat-label">{revenue_label}</div>
                </div>
                <div class="portfolio-stat">
                    <div class="portfolio-stat-value">{total_portfolio_orders}</div>
                    <div class="portfolio-stat-label">{orders_label}</div>
                </div>
                <div class="portfolio-stat">
                    <div class="portfolio-stat-value">${total_pipeline_value:,.0f}</div>
                    <div class="portfolio-stat-label">Upcoming Business</div>
                </div>
            </div>
            
            <div class="account-list">
                <div class="account-list-title">Included Accounts</div>
                <div class="account-list-items">
                    {''.join([f'<span class="account-tag">{name}</span>' for name in customer_names])}
                </div>
            </div>
        </div>
    """
    
    # Generate content for each customer
    for idx, customer_data in enumerate(customers_data):
        customer_name = customer_data[0]
        customer_orders = customer_data[1]
        customer_invoices = customer_data[2]
        customer_deals = customer_data[3]
        customer_line_items = customer_data[4] if len(customer_data) > 4 else None
        customer_ncrs = customer_data[5] if len(customer_data) > 5 else None
        
        # Generate this customer's individual report content
        single_html = generate_qbr_html(customer_name, rep_name, customer_orders, customer_invoices, customer_deals, customer_line_items, customer_ncrs, date_label, pdf_config)
        
        # Extract just the main-content section (between main-content div and footer)
        # Find where main-content starts
        main_start = single_html.find('<div class="main-content">')
        footer_start = single_html.find('<div class="footer">')
        
        # Label for value depends on date filter
        value_label = "Period Value" if date_label != "All Time" else "Lifetime Value"
        
        if main_start != -1 and footer_start != -1:
            # Get everything from main-content to just before footer
            main_content = single_html[main_start:footer_start]
            
            # Add customer section with header
            customer_revenue = customer_invoices['Amount'].sum() if not customer_invoices.empty and 'Amount' in customer_invoices.columns else 0
            customer_order_count = len(customer_invoices) if not customer_invoices.empty else 0
            
            html += f"""
            <div class="customer-section">
                <div class="customer-header">
                    <h2>{customer_name}</h2>
                    <div class="customer-meta">
                        <span>💰 ${customer_revenue:,.0f} {value_label}</span>
                        <span>📦 {customer_order_count} Orders</span>
                        <span>#{idx + 1} of {num_customers}</span>
                    </div>
                </div>
                {main_content}
            </div>
            """
    
    # Add combined footer
    html += f"""
        <div class="portfolio-footer">
            <div class="footer-main">Thank you for your partnership!</div>
            <div class="footer-sub">Calyx Containers • {generated_date} • Questions? Contact {rep_name}</div>
        </div>
    </body>
    </html>
    """
    
    return html


def generate_combined_summary_html(customers_data, rep_name, date_label="All Time", pdf_config=None):
    """
    Generate a combined summary HTML report that aggregates data from all selected customers
    into a single unified view.
    """
    customer_names = [c[0] for c in customers_data]
    num_customers = len(customers_data)
    
    # Aggregate all data (handle None values)
    all_orders = pd.concat([data[1] for data in customers_data if data[1] is not None and not data[1].empty], ignore_index=True) if any(data[1] is not None and not data[1].empty for data in customers_data) else pd.DataFrame()
    all_invoices = pd.concat([data[2] for data in customers_data if data[2] is not None and not data[2].empty], ignore_index=True) if any(data[2] is not None and not data[2].empty for data in customers_data) else pd.DataFrame()
    all_deals = pd.concat([data[3] for data in customers_data if data[3] is not None and not data[3].empty], ignore_index=True) if any(data[3] is not None and not data[3].empty for data in customers_data) else pd.DataFrame()
    
    # Aggregate line items and NCRs if available
    all_line_items = pd.DataFrame()
    all_ncrs = pd.DataFrame()
    if len(customers_data) > 0 and len(customers_data[0]) > 4:
        all_line_items = pd.concat([data[4] for data in customers_data if len(data) > 4 and data[4] is not None and not data[4].empty], ignore_index=True) if any(len(data) > 4 and data[4] is not None and not data[4].empty for data in customers_data) else pd.DataFrame()
    if len(customers_data) > 0 and len(customers_data[0]) > 5:
        all_ncrs = pd.concat([data[5] for data in customers_data if len(data) > 5 and data[5] is not None and not data[5].empty], ignore_index=True) if any(len(data) > 5 and data[5] is not None and not data[5].empty for data in customers_data) else pd.DataFrame()
    
    # Generate the combined report using unified data
    combined_name = f"Portfolio Summary ({num_customers} Accounts)"
    
    # Generate the base report with pdf_config
    html = generate_qbr_html(combined_name, rep_name, all_orders, all_invoices, all_deals, all_line_items, all_ncrs, date_label, pdf_config)
    
    # Build customer tags
    customer_tags = ''.join([f'<span style="background: white; border: 1px solid #bfdbfe; color: #1e40af; padding: 5px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 500;">{name}</span>' for name in customer_names])
    
    # Add a customer list banner after the cover
    customer_list_html = f"""
        <div style="
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            border: 2px solid #93c5fd;
            border-radius: 12px;
            padding: 20px 30px;
            margin: 0 50px 30px 50px;
        ">
            <div style="font-weight: 700; color: #1e40af; margin-bottom: 10px; font-size: 1rem;">
                📊 Accounts Included in This Summary ({num_customers})
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                {customer_tags}
            </div>
        </div>
    """
    
    # Insert customer list after the cover div closes
    html = html.replace('<div class="main-content">', 
                        f'{customer_list_html}\n        <div class="main-content">', 1)
    
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
    
    # Load Sales Orders (A:AG to include all columns through Updated Status)
    sales_orders_df = load_google_sheets_data("_NS_SalesOrders_Data", "A:AG", version=CACHE_VERSION)
    
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
    
    # =========================================================================
    # LOAD AND PROCESS NCR (NON-CONFORMANCE) DATA
    # Used to track quality issues by customer
    # NetSuite NCR = source of truth from November 2024 onwards
    # HubSpot NCR = historical data before November 2024
    # =========================================================================
    
    # --- NetSuite NCR Data (Nov 2024+) ---
    ncr_df = pd.DataFrame()  # Initialize as empty
    ncr_raw = load_google_sheets_data("Non-Conformance Details", "A:W", version=CACHE_VERSION, silent=True)
    
    if not ncr_raw.empty:
        ncr_df = ncr_raw.copy()
        # Remove duplicate columns
        if ncr_df.columns.duplicated().any():
            ncr_df = ncr_df.loc[:, ~ncr_df.columns.duplicated()]
        
        # Clean text fields
        # Column mappings based on user spec:
        # F = Sales Order, I = Issue Type, P = Total Quantity Affected, V = Corrected Customer Name
        for col in ['Sales Order', 'Issue Type', 'Corrected Customer Name', 'Status', 
                    'Defect Summary', 'Priority', 'External Or Internal', 'NC Number']:
            if col in ncr_df.columns:
                ncr_df[col] = ncr_df[col].astype(str).str.strip()
                ncr_df[col] = ncr_df[col].replace('nan', '')
        
        # Clean numeric data - Total Quantity Affected
        if 'Total Quantity Affected' in ncr_df.columns:
            ncr_df['Total Quantity Affected'] = ncr_df['Total Quantity Affected'].apply(clean_numeric)
        
        # Clean Cost fields if present
        if 'Cost of Rework' in ncr_df.columns:
            ncr_df['Cost of Rework'] = ncr_df['Cost of Rework'].apply(clean_numeric)
        if 'Cost Avoided' in ncr_df.columns:
            ncr_df['Cost Avoided'] = ncr_df['Cost Avoided'].apply(clean_numeric)
        
        # Clean date data
        if 'Date Submitted' in ncr_df.columns:
            ncr_df['Date Submitted'] = pd.to_datetime(ncr_df['Date Submitted'], errors='coerce')
        if 'On Time Ship Date' in ncr_df.columns:
            ncr_df['On Time Ship Date'] = pd.to_datetime(ncr_df['On Time Ship Date'], errors='coerce')
        
        # Add source indicator
        ncr_df['NCR Source'] = 'NetSuite'
        
        # Standardize column for matching
        ncr_df['Matched Customer'] = ncr_df.get('Corrected Customer Name', '')
    
    # --- HubSpot NCR Data (Historical, pre-Nov 2024) ---
    hb_ncr_df = pd.DataFrame()  # Initialize as empty
    hb_ncr_raw = load_google_sheets_data("HB NCR", "A2:O", version=CACHE_VERSION, silent=True)
    
    if not hb_ncr_raw.empty:
        hb_ncr_df = hb_ncr_raw.copy()
        # Remove duplicate columns
        if hb_ncr_df.columns.duplicated().any():
            hb_ncr_df = hb_ncr_df.loc[:, ~hb_ncr_df.columns.duplicated()]
        
        # Filter to Customer NCR Pipeline only
        if 'Pipeline' in hb_ncr_df.columns:
            hb_ncr_df = hb_ncr_df[hb_ncr_df['Pipeline'].str.strip() == 'Customer NCR Pipeline'].copy()
        
        if not hb_ncr_df.empty:
            # Clean text fields
            for col in ['Ticket ID', 'Ticket name', 'Ticket status', 'Pipeline', 
                        'Ticket description', 'Company Name', 'Company Name 2']:
                if col in hb_ncr_df.columns:
                    hb_ncr_df[col] = hb_ncr_df[col].astype(str).str.strip()
                    hb_ncr_df[col] = hb_ncr_df[col].replace('nan', '')
            
            # Clean date data
            if 'Create date' in hb_ncr_df.columns:
                hb_ncr_df['Create date'] = pd.to_datetime(hb_ncr_df['Create date'], errors='coerce')
            if 'Close date' in hb_ncr_df.columns:
                hb_ncr_df['Close date'] = pd.to_datetime(hb_ncr_df['Close date'], errors='coerce')
            
            # Calculate resolution time (days to close)
            if 'Create date' in hb_ncr_df.columns and 'Close date' in hb_ncr_df.columns:
                hb_ncr_df['Resolution Days'] = (hb_ncr_df['Close date'] - hb_ncr_df['Create date']).dt.days
            
            # --- Customer Matching Logic ---
            # Priority 1: Company Name 2 (exact match, same naming convention)
            # Priority 2: Company Name (fuzzy match)
            # Priority 3: Extract from Ticket name (format "NCR600 - Customer Name")
            
            def extract_customer_from_ticket(ticket_name):
                """Extract customer name from ticket formats:
                - 'NCR ### - Customer Name' (with dash)
                - 'NCR ### Customer Name' (no dash)
                - Also extracts NCR number for reference
                """
                import re
                if not ticket_name or ticket_name == '' or pd.isna(ticket_name):
                    return ''
                
                ticket_str = str(ticket_name).strip()
                
                # Pattern 1: "NCR ### - Customer Name" (with dash)
                if ' - ' in ticket_str:
                    parts = ticket_str.split(' - ', 1)
                    if len(parts) > 1:
                        customer_part = parts[1].strip()
                        # Remove any trailing issue description (after another dash or parenthetical)
                        # e.g., "Acreage (OH) Smearing" -> "Acreage (OH)"
                        return customer_part
                
                # Pattern 2: "NCR ### Customer Name" (no dash)
                # Match NCR followed by number, then capture everything after
                ncr_match = re.match(r'NCR\s*(\d+)\s+(.+)', ticket_str, re.IGNORECASE)
                if ncr_match:
                    customer_part = ncr_match.group(2).strip()
                    return customer_part
                
                return ''
            
            def extract_ncr_number_from_ticket(ticket_name):
                """Extract NCR number from ticket name"""
                import re
                if not ticket_name or ticket_name == '' or pd.isna(ticket_name):
                    return None
                
                ticket_str = str(ticket_name).strip()
                ncr_match = re.search(r'NCR\s*(\d+)', ticket_str, re.IGNORECASE)
                if ncr_match:
                    return ncr_match.group(1)
                return None
            
            def match_customer(row, valid_customers):
                """Match customer using priority logic with fuzzy matching"""
                from difflib import get_close_matches
                import re
                
                def normalize_for_matching(name):
                    """Normalize customer name for better matching"""
                    if not name:
                        return ''
                    name = str(name).strip()
                    # Remove common state abbreviations at the end (NY, MA, OH, NJ, PA, IL, etc.)
                    name = re.sub(r'\s+(NY|MA|OH|NJ|PA|IL|CA|CO|FL|TX|WA|OR|AZ|NV|MI|NC|SC|GA|VA|MD|CT|RI|NH|VT|ME|DE|WV|KY|TN|AL|MS|LA|AR|MO|IA|MN|WI|IN|OK|KS|NE|SD|ND|MT|WY|ID|UT|NM|HI|AK|DC)$', '', name, flags=re.IGNORECASE)
                    # Remove parenthetical state codes like (OH), (NY)
                    name = re.sub(r'\s*\([A-Z]{2}\)\s*', ' ', name)
                    # Remove trailing description words
                    name = re.sub(r'\s+(Smearing|Defect|Issue|Problem|Damage|Error).*$', '', name, flags=re.IGNORECASE)
                    return name.strip()
                
                def extract_base_company(company_name):
                    """Extract base company name from various formats:
                    - 'Parent : Child' format -> 'Parent'
                    - 'Acreage Holdings:  New York (NY)' -> 'Acreage Holdings'
                    - 'Acreage Holdings - Massachusetts (MA)' -> 'Acreage Holdings'
                    """
                    if not company_name or pd.isna(company_name):
                        return ''
                    name = str(company_name).strip()
                    
                    # Pattern 1: 'Parent : Child' - take the first part (HubSpot Company Name 2 format)
                    if ' : ' in name:
                        return name.split(' : ')[0].strip()
                    
                    # Pattern 2: 'Company:  Location (STATE)' - take before first colon
                    if ':' in name:
                        base = name.split(':')[0].strip()
                        # Only use if it looks like a company name (not a URL)
                        if '.' not in base and len(base) > 3:
                            return base
                    
                    # Pattern 3: 'Company - Location (STATE)' - take before dash if state follows
                    if ' - ' in name:
                        parts = name.split(' - ')
                        if len(parts) >= 2:
                            # Check if second part looks like a state/location
                            second = parts[1].strip()
                            if re.search(r'(Massachusetts|New York|Ohio|Pennsylvania|Illinois|New Jersey|Connecticut|Michigan|Florida|California|Colorado|Texas|Washington|Oregon|Arizona|Nevada|North Carolina|South Carolina|Georgia|Virginia|Maryland|NY|MA|OH|PA|IL|NJ|CT|MI|FL|CA|CO|TX|WA|OR|AZ|NV|NC|SC|GA|VA|MD)', second, re.IGNORECASE):
                                return parts[0].strip()
                    
                    return name
                
                def try_match(name, customers, cutoff=0.7):
                    """Try to match a name against valid customers"""
                    if not name:
                        return None
                    # Exact match first
                    if name in customers:
                        return name
                    # Normalized exact match
                    normalized = normalize_for_matching(name)
                    for cust in customers:
                        if normalize_for_matching(cust) == normalized:
                            return cust
                    # Fuzzy match
                    matches = get_close_matches(name, customers, n=1, cutoff=cutoff)
                    if matches:
                        return matches[0]
                    # Fuzzy match on normalized
                    if normalized != name:
                        matches = get_close_matches(normalized, customers, n=1, cutoff=cutoff)
                        if matches:
                            return matches[0]
                    return None
                
                # Priority 1: Company Name 2 - extract base and match
                company_name_2 = row.get('Company Name 2', '')
                if company_name_2 and company_name_2 != '' and not pd.isna(company_name_2):
                    # Extract base company name (before " : " if present)
                    base_name = extract_base_company(company_name_2)
                    if base_name:
                        match = try_match(base_name, valid_customers, cutoff=0.8)
                        if match:
                            return match
                
                # Priority 2: Company Name (try exact first, then fuzzy)
                company_name = row.get('Company Name', '')
                if company_name and company_name != '' and not pd.isna(company_name):
                    # Also extract base company from Company Name if it has " : " format
                    base_name = extract_base_company(company_name)
                    match = try_match(base_name if base_name else company_name, valid_customers, cutoff=0.7)
                    if match:
                        return match
                    # Try the raw company name with state stripped
                    normalized = normalize_for_matching(company_name)
                    match = try_match(normalized, valid_customers, cutoff=0.6)
                    if match:
                        return match
                
                # Priority 3: Extract from Ticket name and fuzzy match
                ticket_name = row.get('Ticket name', '')
                extracted = extract_customer_from_ticket(ticket_name)
                if extracted:
                    match = try_match(extracted, valid_customers, cutoff=0.5)
                    if match:
                        return match
                
                return ''  # No match found
            
            # Get list of valid customers for fuzzy matching
            valid_customers = set()
            if not sales_orders_df.empty and 'Corrected Customer Name' in sales_orders_df.columns:
                valid_customers.update(sales_orders_df['Corrected Customer Name'].dropna().unique())
            if not invoices_df.empty and 'Corrected Customer' in invoices_df.columns:
                valid_customers.update(invoices_df['Corrected Customer'].dropna().unique())
            valid_customers = [c for c in valid_customers if c and c not in ['', 'nan', 'None', '#N/A']]
            
            # Apply customer matching
            hb_ncr_df['Matched Customer'] = hb_ncr_df.apply(
                lambda row: match_customer(row, valid_customers), axis=1
            )
            
            # --- Categorize HubSpot NCRs based on description ---
            def categorize_hubspot_ncr(description):
                """Categorize HubSpot NCR based on ticket description to match NetSuite Issue Types"""
                if not description or description == '' or pd.isna(description):
                    return 'Defective Product'
                
                desc_lower = str(description).lower()
                
                # Damaged in Transit - carrier damage, broken in shipping
                if any(kw in desc_lower for kw in ['damaged', 'broken', 'crushed', 'fedex damaged', 
                                                    'ups damaged', 'transit', 'carrier', 'pallet.*damage']):
                    return 'Damaged in Transit'
                
                # Shipped to Wrong Address - misshipments, swapped orders
                if any(kw in desc_lower for kw in ['wrong address', 'misshipped', 'swapped', 
                                                    'wrong location', 'delivered to wrong']):
                    return 'Shipped to Wrong Address'
                
                # Missing Labels Wrong Qty - shortages
                if any(kw in desc_lower for kw in ['short', 'missing', 'shorted', 'only received',
                                                    'ran short', 'labels short']):
                    return 'Missing Labels Wrong Qty'
                
                # Order Entry Error - system/data entry issues, customer ordered wrong
                if any(kw in desc_lower for kw in ['hubspot', 'netsuite', 'set up incorrectly', 
                                                    'entered into', 'system switched',
                                                    'customer ordered wrong', 'mistakenly ordered',
                                                    'accidentally placed', 'customer error',
                                                    'deal & so was reflective of the wrong',
                                                    'proofing queue']):
                    return 'Order Entry Error'
                
                # Wrong Material - wrong product shipped (includes wrong color/size)
                if any(kw in desc_lower for kw in ['wrong color', 'wrong size', 'wrong finish',
                                                    'received white instead', 'received black instead', 
                                                    'instead of', '25d instead', '15d instead', 
                                                    '7ml instead', '45d instead', '4ml instead',
                                                    'wrong sku', 'wrong product', 'mislabeled box',
                                                    'shipped black instead', 'shipped white instead',
                                                    'wrong core', 'not the artwork']):
                    return 'Wrong Material'
                
                # Incorrect Color - specifically color-related manufacturing issues
                if any(kw in desc_lower for kw in ['grey caps', 'marbling', 'translucent',
                                                    'color.*mixed', 'pigment']):
                    return 'Incorrect Color'
                
                # Artwork/Print/Label defects
                if any(kw in desc_lower for kw in ['print', 'artwork', 'off center', 'embossing',
                                                    'cut off', 'varnish', 'laminate', 'tactile',
                                                    'telescoping', 'backing.*rip', 'paper backing',
                                                    'poor print', 'skipout']):
                    return 'Artwork Error'
                
                # Defective Product - manufacturing defects, contamination, fit issues
                if any(kw in desc_lower for kw in ['warped', 'warping', 'defect', 'grease', 
                                                    'debris', 'contaminated', 'filth', 'insect', 
                                                    'hair', 'doesn\'t fit', 'not sealing', 'leaking',
                                                    'cracked', 'irregular', 'lid.*fit', 'snapping',
                                                    'boxes not forming', 'not in.*bag']):
                    return 'Defective Product'
                
                # Customer Returns (not defect-related)
                if any(kw in desc_lower for kw in ['customer return', 'return', 'exchange',
                                                    'would like to replace', 'swap out']):
                    return 'Order Entry Error'
                
                # Default fallback
                return 'Defective Product'
            
            # Map HubSpot columns to standardized NCR columns
            # Extract NCR number from ticket name (e.g., "NCR 988 Acreage NY" → "NCR-988")
            if 'Ticket name' in hb_ncr_df.columns:
                hb_ncr_df['NC Number'] = hb_ncr_df['Ticket name'].apply(
                    lambda x: f"NCR-{extract_ncr_number_from_ticket(x)}" if extract_ncr_number_from_ticket(x) else str(x)[:30]
                )
            else:
                hb_ncr_df['NC Number'] = hb_ncr_df.get('Ticket ID', '').apply(lambda x: f"HB-{x}" if x else '')
            hb_ncr_df['Date Submitted'] = hb_ncr_df.get('Create date', pd.NaT)
            hb_ncr_df['Status'] = hb_ncr_df.get('Ticket status', '')
            hb_ncr_df['Defect Summary'] = hb_ncr_df.get('Ticket description', '')
            
            # Categorize based on description - matching NetSuite Issue Types
            hb_ncr_df['Issue Type'] = hb_ncr_df['Defect Summary'].apply(categorize_hubspot_ncr)
            
            # Calculate Total Quantity Affected from QTY columns and determine Product Type
            # Priority order: Boxes → Containers → Flexpack → Labels → General QTY
            qty_columns = [
                ('QTY of boxes effected', 'Boxes'),
                ('QTY of containers effected', 'Containers'),
                ('Flexpack QTY Effected', 'Flexpack'),
                ('QTY of labels effected', 'Labels'),
                ('QTY Effected', 'General')
            ]
            
            def get_qty_and_product_type(row):
                """Get quantity affected and product type from first non-empty QTY column"""
                for col_name, product_type in qty_columns:
                    if col_name in row.index:
                        val = row[col_name]
                        if pd.notna(val) and str(val).strip() not in ['', 'nan', '0']:
                            try:
                                qty = float(str(val).replace(',', '').strip())
                                if qty > 0:
                                    return qty, product_type
                            except (ValueError, TypeError):
                                continue
                return 0, 'Unknown'
            
            # Apply to get both quantity and product type
            qty_product = hb_ncr_df.apply(get_qty_and_product_type, axis=1)
            hb_ncr_df['Total Quantity Affected'] = qty_product.apply(lambda x: x[0])
            hb_ncr_df['Product Type Affected'] = qty_product.apply(lambda x: x[1])
            hb_ncr_df['NCR Source'] = 'HubSpot'
            hb_ncr_df['Close Date'] = hb_ncr_df.get('Close date', pd.NaT)
    
    # --- Combine NCR Data ---
    # Columns to keep for combined dataframe
    ncr_columns = ['NC Number', 'Date Submitted', 'Status', 'Issue Type', 'Defect Summary',
                   'Total Quantity Affected', 'Matched Customer', 'NCR Source', 'Sales Order']
    
    combined_ncr_df = pd.DataFrame()
    
    if not ncr_df.empty:
        # Ensure Sales Order column exists
        if 'Sales Order' not in ncr_df.columns:
            ncr_df['Sales Order'] = ''
        # Select columns that exist
        ns_cols = [c for c in ncr_columns if c in ncr_df.columns]
        combined_ncr_df = ncr_df[ns_cols].copy()
    
    if not hb_ncr_df.empty:
        # Add Sales Order placeholder if not exists
        if 'Sales Order' not in hb_ncr_df.columns:
            hb_ncr_df['Sales Order'] = ''
        # Add Close Date, Resolution Days, and Product Type Affected to combined
        hb_cols = [c for c in ncr_columns if c in hb_ncr_df.columns]
        if 'Close Date' in hb_ncr_df.columns:
            hb_cols.append('Close Date')
        if 'Resolution Days' in hb_ncr_df.columns:
            hb_cols.append('Resolution Days')
        if 'Product Type Affected' in hb_ncr_df.columns:
            hb_cols.append('Product Type Affected')
        
        hb_subset = hb_ncr_df[hb_cols].copy()
        
        if combined_ncr_df.empty:
            combined_ncr_df = hb_subset
        else:
            combined_ncr_df = pd.concat([combined_ncr_df, hb_subset], ignore_index=True)
    
    return sales_orders_df, invoices_df, deals_df, invoice_line_items_df, combined_ncr_df


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
    """Get unique customers for a specific rep (or all reps if 'All Reps' selected)"""
    customers = set()
    
    # Handle "All Reps" case - return all customers
    all_reps = (rep_name == "All Reps")
    
    if not sales_orders_df.empty and 'Corrected Customer Name' in sales_orders_df.columns:
        if all_reps:
            valid_customers = sales_orders_df['Corrected Customer Name'].dropna()
        elif 'Rep Master' in sales_orders_df.columns:
            rep_orders = sales_orders_df[sales_orders_df['Rep Master'] == rep_name]
            valid_customers = rep_orders['Corrected Customer Name'].dropna()
        else:
            valid_customers = pd.Series(dtype=str)
        valid_customers = valid_customers[~valid_customers.isin(['', 'nan', 'None', '#N/A'])]
        customers.update(valid_customers.unique())
    
    if not invoices_df.empty and 'Corrected Customer' in invoices_df.columns:
        if all_reps:
            valid_customers = invoices_df['Corrected Customer'].dropna()
        elif 'Rep Master' in invoices_df.columns:
            rep_invoices = invoices_df[invoices_df['Rep Master'] == rep_name]
            valid_customers = rep_invoices['Corrected Customer'].dropna()
        else:
            valid_customers = pd.Series(dtype=str)
        valid_customers = valid_customers[~valid_customers.isin(['', 'nan', 'None', '#N/A'])]
        customers.update(valid_customers.unique())
    
    return sorted([c for c in customers if c])


def get_customer_deals(customer_name, rep_name, deals_df):
    """
    Get HubSpot deals for a specific customer using direct match on Company Name
    """
    if deals_df.empty or 'Company Name' not in deals_df.columns:
        return pd.DataFrame()
    
    # Handle "All Reps" case - don't filter by Deal Owner
    if rep_name == "All Reps":
        matches = deals_df[
            deals_df['Company Name'] == customer_name
        ].copy()
    else:
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
            st.plotly_chart(fig, use_container_width=True, key=f"revenue_chart_{uuid.uuid4().hex[:8]}")


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
        st.plotly_chart(fig, use_container_width=True, key=f"ontime_chart_{uuid.uuid4().hex[:8]}")


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
        st.plotly_chart(fig, use_container_width=True, key=f"ordertype_chart_{uuid.uuid4().hex[:8]}")
    
    with col2:
        # Table
        display_df = type_mix.copy()
        display_df['Total Value'] = display_df['Total Value'].apply(lambda x: f"${x:,.0f}")
        display_df['% of Total'] = display_df['% of Total'].apply(lambda x: f"{x:.1f}%")
        st.dataframe(display_df, use_container_width=True)


def render_pipeline_section(customer_deals, customer_name):
    """Section 7: Upcoming Business (formerly Pipeline)"""
    st.markdown("### 🎯 Upcoming Business")
    
    if customer_deals.empty:
        st.info(f"No upcoming business found for '{customer_name}'.")
        return
    
    # Helper to convert internal status to customer-friendly
    def get_customer_friendly_status(status):
        status_map = {
            'Commit': 'Confirmed',
            'Expect': 'Likely',
            'Best Case': 'Tentative',
            'Opportunity': 'In Discussion'
        }
        return status_map.get(status, status)
    
    # Filter to open deals
    open_statuses = ['Expect', 'Commit', 'Best Case', 'Opportunity']
    open_deals = customer_deals[customer_deals['Close Status'].isin(open_statuses)].copy()
    
    if open_deals.empty:
        st.info("No upcoming business found for this customer.")
        return
    
    # Add customer-friendly status column
    open_deals['Status'] = open_deals['Close Status'].apply(get_customer_friendly_status)
    
    # Toggle for Raw vs Probability-Adjusted
    # Use customer name to create unique key for multi-select support
    safe_customer_key = customer_name.replace(' ', '_').replace('.', '_')[:30]
    amount_mode = st.radio(
        "Amount Display:",
        ["Raw Estimate", "Probability-Adjusted"],
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
        st.metric(f"Projected Value ({amount_mode})", f"${total_pipeline:,.0f}")
    with col2:
        st.metric("Opportunities", deal_count)
    with col3:
        if use_probability:
            raw_total = open_deals['Amount'].sum()
            st.metric("Raw Total (Reference)", f"${raw_total:,.0f}")
        else:
            prob_total = open_deals['Probability Rev'].sum()
            st.metric("Prob-Adjusted (Reference)", f"${prob_total:,.0f}")
    
    # Breakdown by Status (using friendly names)
    status_summary = open_deals.groupby('Status').agg({
        amount_col: 'sum',
        'Record ID': 'count'
    }).round(0)
    status_summary.columns = ['Value', 'Count']
    
    # Order by stage (mapping back from friendly names)
    stage_order = ['Confirmed', 'Likely', 'Tentative', 'In Discussion']
    status_summary = status_summary.reindex([s for s in stage_order if s in status_summary.index])
    
    status_summary['Value'] = status_summary['Value'].apply(lambda x: f"${x:,.0f}")
    st.dataframe(status_summary, use_container_width=True)
    
    # Deal details
    with st.expander("📋 View Order Details"):
        display_cols = ['Deal Name', 'Status', 'Deal Type', 'Amount', 'Probability Rev', 'Close Date', 'Pending Approval Date']
        display_cols = [c for c in display_cols if c in open_deals.columns]
        display_df = open_deals[display_cols].copy()
        
        # Remove duplicate columns if any
        if display_df.columns.duplicated().any():
            display_df = display_df.loc[:, ~display_df.columns.duplicated()]
        
        # Rename columns for customer-facing display
        rename_cols = {
            'Deal Name': 'Order Description',
            'Deal Type': 'Type',
            'Amount': 'Forecast Value',
            'Probability Rev': 'Adjusted Value'
        }
        display_df = display_df.rename(columns={k: v for k, v in rename_cols.items() if k in display_df.columns})
        
        if 'Forecast Value' in display_df.columns:
            display_df['Forecast Value'] = display_df['Forecast Value'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")
        if 'Adjusted Value' in display_df.columns:
            display_df['Adjusted Value'] = display_df['Adjusted Value'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")
        
        # Rename Pending Approval Date to Projected Ship Date
        if 'Pending Approval Date' in display_df.columns:
            display_df = display_df.rename(columns={'Pending Approval Date': 'Projected Ship Date'})
            display_df['Projected Ship Date'] = pd.to_datetime(display_df['Projected Ship Date'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
        if 'Close Date' in display_df.columns:
            display_df = display_df.rename(columns={'Close Date': 'Expected Date'})
            display_df['Expected Date'] = pd.to_datetime(display_df['Expected Date'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
        
        st.dataframe(display_df, use_container_width=True)


# =============================================================================
# PRODUCT CATEGORIZATION FUNCTIONS
# Based on Calyx Containers Product Master Categorization Rules
# =============================================================================

# Flexpack-specific 4-digit codes
FLEXPACK_CODES = {
    '1148', '1164', '1169', '1179', '1180', '1182', '1183', '1188', 
    '1190', '1192', '1247', '1259', '1283', '1304', '1325', '1340', 
    '1345', '1354', '1367', '1373', '1375', '1393', '1492', '1519', 
    '1608', '1635', '1666', '1670', '1673', '1678', '1696', '1703', 
    '1711', '1758', '1768', '1771', '1776', '1780', '1787', '1808', 
    '1849', '1867', '1875', '1883', '1890', '1896', '1901', '1904', 
    '1906', '1909', '1915'
}

def extract_die_tool(item_name):
    """
    Extract the die tool code from a SKU.
    Format: CUST-ST-DIETOOL-PRODUCT or CUST-ST-X-DIETOOL-PRODUCT
    Returns (die_tool, is_alphanumeric)
    
    Examples:
    - APOC-MI-H-25L-BB1-1 → die_tool='25L', is_alphanumeric=True (Dram lid label)
    - APOC-MI-1188-APGQ → die_tool='1188', is_alphanumeric=False (Flexpack/Label)
    - 989E-MI-H-4C-EX1-2 → die_tool='4C', is_alphanumeric=True (Concentrate label)
    """
    if pd.isna(item_name):
        return None, False
    
    name = str(item_name).upper().strip()
    
    # Pattern 1: XXXX-ST-X-DIETOOL-... (with single letter indicator like H, M, R)
    # The die tool is the component after the single letter: 25L, 45B, 4C, 7L, 116P, etc.
    match = re.search(r'^[A-Z]{3,4}-[A-Z]{2}-[A-Z]-(\d{1,3}[LBPCH])-', name)
    if match:
        return match.group(1), True
    
    # Pattern 2: XXXX-ST-X-DIETOOL (concentrate patterns like 4C, 7L, 7C)
    match = re.search(r'^[A-Z]{3,4}-[A-Z]{2}-[A-Z]-([47][CLH])-', name)
    if match:
        return match.group(1), True
    
    # Pattern 3: XXXX-ST-NUMERIC-... (purely numeric die tool for Flexpack/Labels)
    match = re.search(r'^[A-Z]{3,4}-[A-Z]{2}-(\d{4})-', name)
    if match:
        return match.group(1), False
    
    # Pattern 4: Direct patterns like -25L-, -45B-, -116P- anywhere in name
    match = re.search(r'-(\d{1,3}[LBPCH])-', name)
    if match:
        return match.group(1), True
    
    # Pattern 5: Concentrate patterns -4C-, -7L-, -7C- etc.
    match = re.search(r'-([47][CLH])-', name)
    if match:
        return match.group(1), True
    
    return None, False


def categorize_product(item_name, item_description="", calyx_product_type=""):
    """
    Categorize a product based on Item name, description, and Calyx || Product Type.
    Returns (category, sub_category, component_type) tuple.
    
    component_type: 'base', 'lid', 'label', 'band', 'accessory', 'complete', or None
    """
    if pd.isna(item_name):
        item_name = ""
    if pd.isna(item_description):
        item_description = ""
    if pd.isna(calyx_product_type):
        calyx_product_type = ""
    
    name = str(item_name).upper().strip()
    desc = str(item_description).upper().strip()
    product_type = str(calyx_product_type).upper().strip()
    all_text = f"{name} {desc}"
    
    # Extract die tool info
    die_tool, is_alphanumeric = extract_die_tool(item_name)
    
    # =========================================================================
    # 1. SHIPPING/TAXES/FEES - Break out into specific types
    # =========================================================================
    # Taxes
    if re.search(r'\bTAX\b|GST|HST|CANADIAN\s*(BUSINESS|GOODS)', all_text):
        return ('Fees & Adjustments', 'Taxes', None)
    
    # Shipping
    if re.search(r'^SHIPPING|SHIPPING\s*FEE|FREIGHT', all_text):
        return ('Fees & Adjustments', 'Shipping', None)
    
    # Expedite Fees
    if re.search(r'EXPEDITE\s*FEE|RUSH\s*FEE', all_text):
        return ('Fees & Adjustments', 'Expedite Fee', None)
    
    # Convenience Fees
    if re.search(r'CONVENIENCE\s*FEE', all_text):
        return ('Fees & Adjustments', 'Convenience Fee', None)
    
    # Discounts/Promos
    if re.search(r'^\$\d+OFF|DISCOUNT|PROMO|%\s*OFF', all_text):
        return ('Fees & Adjustments', 'Discount', None)
    
    # Accounting adjustments
    if re.search(r'^ACCOUNTING|OVERPAYMENT|BAD\s*DEBT|REPLACEMENT\s*ORDER', all_text):
        return ('Fees & Adjustments', 'Accounting Adjustment', None)
    
    # Sample/Creative charges
    if re.search(r'DIE\s*CUT\s*SAMPLE|SAMPLE\s*CHARGE|CREATIVE$|TESTIMONIAL', all_text):
        return ('Fees & Adjustments', 'Sample/Creative', None)
    
    # Tooling fees (check BEFORE label categorization - "Tooling Fee - Labels" is a fee, not a label)
    if re.search(r'TOOLING\s*FEE|TOOL\s*FEE|DIE\s*FEE|PLATE\s*FEE|SETUP\s*FEE', all_text):
        return ('Fees & Adjustments', 'Tooling Fee', None)
    
    # Other fees (catch-all for fee-like items)
    if re.search(r'MODULAR.*SERIAL', all_text):
        return ('Fees & Adjustments', 'Other Fee', None)
    
    # =========================================================================
    # 2. CALYX CURE
    # =========================================================================
    if name.startswith('CC-') or 'CALYX CURE' in all_text:
        return ('Calyx Cure', 'Calyx Cure', 'complete')
    
    # =========================================================================
    # 3. CALYX JAR (8TH Glass)
    # =========================================================================
    if 'GB-8TH' in name or name.startswith('CJ-') or 'CALYX JAR' in all_text:
        return ('Calyx Jar', 'Glass Base', 'base')
    if re.search(r'-JB-', name):
        return ('Calyx Jar', 'Jar Base', 'base')
    if re.search(r'-JL-', name):
        return ('Calyx Jar', 'Jar Lid', 'lid')
    if 'SB-8TH' in name:
        return ('Calyx Jar', 'Shrink Band', 'band')
    
    # =========================================================================
    # 4. CONCENTRATES (4mL/7mL Glass Bases and specific lids)
    # =========================================================================
    # Glass bases
    if re.search(r'GB-4ML|4ML.*GLASS|4\s*ML.*BASE', name):
        return ('Concentrates', '4mL Glass Base', 'base')
    if re.search(r'GB-7ML|7ML.*GLASS|7\s*ML.*BASE', name):
        return ('Concentrates', '7mL Glass Base', 'base')
    
    # Concentrate-specific lids (4C, 7C, 4L, 7L, 4H, 7H patterns)
    if re.search(r'-4[CLH]-|-4[CLH]$', name) and not re.search(r'BOX|TUCK|AUTO|DISPLAY', all_text):
        return ('Concentrates', '4mL Lid', 'lid')
    if re.search(r'-7[CLH]-|-7[CLH]$', name) and not re.search(r'BOX|TUCK|AUTO|DISPLAY', all_text):
        return ('Concentrates', '7mL Lid', 'lid')
    
    # Concentrate labels (alphanumeric die tool with 4C, 7C, 7L patterns)
    if die_tool and is_alphanumeric:
        if re.match(r'^[47][CLH]', die_tool):
            component = 'Lid Label' if 'L' in die_tool else 'Jar Label'
            size = '4mL' if die_tool.startswith('4') else '7mL'
            return ('Concentrates', f'{size} {component}', 'label')
    
    # =========================================================================
    # 5. DRAMS (15D, 25D, 45D, 145D) - Bases, Lids, Labels
    # =========================================================================
    dram_sizes = ['145', '45', '25', '15']  # Check larger first to avoid partial matches
    
    # FIRST: Check for customer label SKUs with alphanumeric die tools
    # These are LABELS, not physical products
    if die_tool and is_alphanumeric:
        for size in dram_sizes:
            size_d = f'{size}D'
            if re.match(rf'^{size}[LBPH]', die_tool):
                if 'L' in die_tool:
                    return ('Drams', f'{size_d} Lid Label', 'label')
                elif 'B' in die_tool or 'P' in die_tool:
                    return ('Drams', f'{size_d} Base Label', 'label')
                else:
                    return ('Drams', f'{size_d} Label', 'label')
    
    # THEN: Check for physical dram products (bases, lids)
    for size in dram_sizes:
        size_d = f'{size}D'
        
        # Polypropylene Bases: PB-XXD or -XXB- patterns
        if re.search(rf'PB-{size}D|{size}D.*BASE|-{size}B-', name):
            return ('Drams', f'{size_d} Base', 'base')
        
        # Polypropylene Lids: PL-XXD patterns (but NOT customer labels like XXXX-MI-H-25L-)
        # Only match if it starts with PL- or CL- (standard product codes)
        if size != '15':  # Skip 15 here, handle DML separately
            if re.search(rf'^PL-{size}D|^CL-{size}D', name):
                return ('Drams', f'{size_d} Lid', 'lid')
        
        # Direct size mentions in description (for standard products only)
        if f'{size}D LID' in all_text and not re.search(r'^[A-Z]{3,4}-[A-Z]{2}-', name):
            return ('Drams', f'{size_d} Lid', 'lid')
        if f'{size}D BASE' in all_text and not re.search(r'^[A-Z]{3,4}-[A-Z]{2}-', name):
            return ('Drams', f'{size_d} Base', 'base')
    
    # =========================================================================
    # 6. DML LIDS (Universal 4mL/7mL/15D - needs pairing to categorize)
    # -F suffix indicates it's specifically for 4mL/7mL concentrates
    # =========================================================================
    if 'DML' in name or re.search(r'PL-DML|CL-DML', name):
        # Check for -F suffix which indicates concentrate lid (4mL or 7mL)
        if name.endswith('-F') or re.search(r'-\d+-F$', name):
            return ('Concentrates', 'Universal Lid (4mL/7mL)', 'lid')
        # Otherwise mark for invoice-based pairing (could be 15D or concentrate)
        return ('DML (Universal)', 'Universal Lid', 'lid')
    
    # 15L patterns that aren't clearly dram-specific
    if re.search(r'-15L-|^15L-', name) and 'DML' not in name:
        # Check if it's clearly a dram label
        if die_tool and is_alphanumeric and die_tool.startswith('15'):
            return ('Drams', '15D Lid Label', 'label')
        # Otherwise it's likely a DML universal lid
        return ('DML (Universal)', 'Universal Lid', 'lid')
    
    # =========================================================================
    # 7. DRAM ACCESSORIES (Tray Frames, Tray Inserts, Shrink Bands)
    # =========================================================================
    if name.startswith('TF-') or 'TRAY FRAME' in all_text:
        return ('Dram Accessories', 'Tray Frame', 'accessory')
    
    if re.search(r'^TI-\d+D|TRAY INSERT', name):
        # Extract size from TI-XXD
        size_match = re.search(r'TI-(\d+)D', name)
        if size_match:
            return ('Dram Accessories', f'{size_match.group(1)}D Tray Insert', 'accessory')
        return ('Dram Accessories', 'Tray Insert', 'accessory')
    
    # Shrink bands for drams
    if re.search(r'SB-15D|SB-25D|SB-45D|SB-145D', name):
        size_match = re.search(r'SB-(\d+)D', name)
        if size_match:
            return ('Dram Accessories', f'{size_match.group(1)}D Shrink Band', 'band')
        return ('Dram Accessories', 'Shrink Band', 'band')
    
    # FEP Liners
    if 'FEP' in name and 'LINER' in all_text:
        return ('Dram Accessories', 'FEP Liner', 'accessory')
    
    # Stick & Grip
    if re.search(r'SG-|STICK.*GRIP', all_text):
        return ('Dram Accessories', 'Stick & Grip', 'accessory')
    
    # =========================================================================
    # 8. TUBES (116mm, 90mm, 84mm)
    # =========================================================================
    if re.search(r'JT-116|116\s*MM|116T|-116-|116P', name) and 'BOX' not in all_text:
        if 'LABEL' in all_text or (die_tool and '116' in die_tool):
            return ('Tubes', '116mm Label', 'label')
        return ('Tubes', '116mm Tube', 'complete')
    
    if re.search(r'JT-90|90\s*MM|90T|-90-|90M', name) and 'BOX' not in all_text and 'WAVEPACK' not in all_text:
        if 'LABEL' in all_text or (die_tool and '90' in die_tool):
            return ('Tubes', '90mm Label', 'label')
        return ('Tubes', '90mm Tube', 'complete')
    
    if re.search(r'JT-84|84\s*MM|84T|-84-', name) and 'TUBE' in all_text:
        if 'LABEL' in all_text:
            return ('Tubes', '84mm Label', 'label')
        return ('Tubes', '84mm Tube', 'complete')
    
    # =========================================================================
    # 9. BOXES
    # =========================================================================
    box_keywords = ['CORE AUTO', 'AUTOBOTTOM', 'AUTO BOTTOM', 'CORE TUCK', 
                    'REVERSE TUCK', 'ELEVATED TUCK', 'ELEVATED AUTO']
    if any(kw in all_text for kw in box_keywords) and 'BAG' not in all_text:
        if 'AUTO' in all_text:
            return ('Boxes', 'Core Auto', 'complete')
        if 'TUCK' in all_text:
            return ('Boxes', 'Core Tuck', 'complete')
        return ('Boxes', 'Box', 'complete')
    
    if re.search(r'-CNCA-|-CNC-', all_text) or 'SHIPPER BOX' in all_text:
        return ('Boxes', 'Shipper Box', 'complete')
    if 'BOX' in all_text and 'SBS' in all_text and 'BAG' not in all_text:
        return ('Boxes', 'Box', 'complete')
    if 'DISPLAY' in all_text and ('TEARAWAY' in all_text or 'ELEVATED' in all_text) and 'BAG' not in all_text:
        return ('Boxes', 'Display Box', 'complete')
    
    # =========================================================================
    # 10. FLEXPACK / WAVEPACK (check Calyx || Product Type first!)
    # =========================================================================
    # Use Calyx || Product Type if available
    if 'FLEXPACK' in product_type or 'WAVEPACK' in product_type or 'FLEX' in product_type:
        return ('Flexpack', 'Wavepack', 'complete')
    
    if name.startswith('BAM-') and 'LABEL' not in all_text:
        return ('Flexpack', 'Wavepack', 'complete')
    if re.search(r'WAVEPACK|FLEXPACK', all_text):
        return ('Flexpack', 'Wavepack', 'complete')
    if re.search(r'\bBAGS?\b|\bPOUCH\b', desc):
        return ('Flexpack', 'Bag/Pouch', 'complete')
    
    # Numeric die tool - could be Flexpack or Non-Core Label
    if die_tool and not is_alphanumeric and die_tool in FLEXPACK_CODES:
        return ('Flexpack', 'Wavepack', 'complete')
    
    # =========================================================================
    # 11. NON-CORE LABELS (customer-specific labels)
    # =========================================================================
    # Use Calyx || Product Type if available
    if 'LABEL' in product_type:
        return ('Non-Core Labels', 'Custom Label', 'label')
    
    if re.search(r'\bLABEL\b|\bLBL\b|\bBOPP\b', all_text):
        return ('Non-Core Labels', 'Custom Label', 'label')
    
    # Numeric die tool that's not a known Flexpack code
    if die_tool and not is_alphanumeric:
        return ('Non-Core Labels', 'Custom Label', 'label')
    
    # Customer SKU pattern without clear product identification
    if re.search(r'^[A-Z]{3,4}-[A-Z]{2}-', name):
        return ('Non-Core Labels', 'Custom Label', 'label')
    
    # =========================================================================
    # 12. APPLICATION FEES (categorize by what they're for)
    # =========================================================================
    if re.search(r'APPL\s*FEE|APPLICATION\s*FEE', all_text):
        # Try to determine what product the fee is for
        if re.search(r'15D|25D|45D|145D', all_text):
            return ('Drams', 'Application Fee', 'fee')
        if re.search(r'116|90', all_text) and 'TUBE' in all_text:
            return ('Tubes', 'Application Fee', 'fee')
        return ('Fees & Adjustments', 'Application Fee', 'fee')
    
    # =========================================================================
    # 13. UNCATEGORIZED
    # =========================================================================
    return ('Other', 'Uncategorized', None)


def apply_product_categories(df):
    """
    Apply categorization to a dataframe using Calyx || Product Type and Calyx | Item Type columns.
    
    PRIMARY: Uses 'Calyx || Product Type' (Column X) to map to Forecast Category
    FALLBACK: For blanks, checks 'Calyx | Item Type' (Column W) for Shipping/Tax
    
    Mapping from Calyx || Product Type to Forecast Category:
        Plastic Lids → Drams
        Plastic Bases → Drams
        Application → Application
        Labels → Labels
        Flex Pack → Flexpack
        Tray Inserts → Other
        Calyx Cure → Cure
        Shrink Bands → Other
        Glass Bases → Glass
        Tubes → Other
        Boxes → Other
        Fee → Other
        Design → Other
        Container → Glass
        Tray Frames → Other
        Accessories → Other
        Service → Other
    
    Mapping from Calyx | Item Type (for blanks):
        Shipping → Shipping
        Tax Item → Other (excluded from revenue)
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Mapping from Calyx || Product Type to Forecast Category
    PRODUCT_TYPE_TO_CATEGORY = {
        'plastic lids': 'Drams',
        'plastic bases': 'Drams',
        'application': 'Application',
        'labels': 'Labels',
        'flex pack': 'Flexpack',
        'tray inserts': 'Other',
        'calyx cure': 'Cure',
        'shrink bands': 'Other',
        'glass bases': 'Glass',
        'tubes': 'Other',
        'boxes': 'Other',
        'fee': 'Other',
        'design': 'Other',
        'container': 'Glass',
        'tray frames': 'Other',
        'accessories': 'Other',
        'service': 'Other',
    }
    
    # Mapping from Calyx | Item Type (fallback for blanks)
    ITEM_TYPE_TO_CATEGORY = {
        'shipping': 'Shipping',
        'shipitem': 'Shipping',
        'tax item': 'Other',
        'inventory item': 'Other',
        'non-inventory item': 'Other',
        'service': 'Other',
    }
    
    # Find Calyx columns (flexible matching - handles whitespace and case differences)
    product_type_col = None
    item_type_col = None
    item_col = None
    item_desc_col = None
    
    for col in df.columns:
        col_lower = str(col).lower().strip()
        # Look for "calyx || product type" or similar
        if 'product type' in col_lower and 'calyx' in col_lower:
            product_type_col = col
        # Look for "calyx | item type" or similar  
        elif 'item type' in col_lower and 'calyx' in col_lower:
            item_type_col = col
        # Look for Item column
        elif col_lower == 'item':
            item_col = col
        # Look for Item Description column
        elif col_lower == 'item description':
            item_desc_col = col
    
    def categorize_row(row):
        """Categorize a single row based on Calyx columns"""
        # Get column values
        product_type_raw = ''
        item_type_raw = ''
        item_name = ''
        item_desc = ''
        
        if product_type_col and product_type_col in row.index:
            val = row[product_type_col]
            if pd.notna(val):
                product_type_raw = str(val).strip()
        
        if item_type_col and item_type_col in row.index:
            val = row[item_type_col]
            if pd.notna(val):
                item_type_raw = str(val).strip()
        
        if item_col and item_col in row.index:
            val = row[item_col]
            if pd.notna(val):
                item_name = str(val).strip()
        
        if item_desc_col and item_desc_col in row.index:
            val = row[item_desc_col]
            if pd.notna(val):
                item_desc = str(val).strip()
        
        product_type = product_type_raw.lower()
        item_type = item_type_raw.lower()
        item_name_lower = item_name.lower()
        item_desc_lower = item_desc.lower()
        
        # OVERRIDE 1: Check for Tooling Fee in item name - always categorize as Other
        # This catches "Tooling Fee - Labels" which shouldn't be in Labels
        if 'tooling fee' in item_name_lower or 'tooling fee' in item_desc_lower:
            return ('Other', 'Tooling Fee', None)
        
        # OVERRIDE 2: Check Calyx | Item Type for "ShipItem" - this is shipping
        if item_type == 'shipitem' or item_type == 'shipping':
            return ('Shipping', 'Shipping', None)
        
        # PRIMARY: Check Calyx || Product Type
        if product_type and product_type in PRODUCT_TYPE_TO_CATEGORY:
            category = PRODUCT_TYPE_TO_CATEGORY[product_type]
            return (category, product_type_raw, None)
        
        # FALLBACK: Check Calyx | Item Type for other types
        if item_type and item_type in ITEM_TYPE_TO_CATEGORY:
            category = ITEM_TYPE_TO_CATEGORY[item_type]
            return (category, item_type_raw, None)
        
        # If we have a product type that's not in our mapping, categorize as Other
        if product_type_raw:
            return ('Other', product_type_raw, None)
        
        # Default fallback
        return ('Other', 'Uncategorized', None)
    
    # If we found at least one Calyx column, use the new logic
    if product_type_col or item_type_col:
        # Apply new Calyx-based categorization
        categories = df.apply(categorize_row, axis=1)
        
        df['Product Category'] = categories.apply(lambda x: x[0])
        df['Product Sub-Category'] = categories.apply(lambda x: x[1])
        df['Component Type'] = categories.apply(lambda x: x[2])
        return df
    
    # NO Calyx columns found - fall back to old SKU-based categorization
    # This is for backward compatibility with data sources that don't have Calyx columns
    item_col = 'Item' if 'Item' in df.columns else None
    desc_col = 'Item Description' if 'Item Description' in df.columns else None
    
    if item_col is None and desc_col is None:
        df['Product Category'] = 'Other'
        df['Product Sub-Category'] = 'Uncategorized'
        df['Component Type'] = None
        return df
    
    # Apply old categorization for backward compatibility
    categories = df.apply(
        lambda row: categorize_product(
            row.get(item_col, '') if item_col else '',
            row.get(desc_col, '') if desc_col else '',
            ''
        ), axis=1
    )
    
    df['Product Category'] = categories.apply(lambda x: x[0])
    df['Product Sub-Category'] = categories.apply(lambda x: x[1])
    df['Component Type'] = categories.apply(lambda x: x[2])
    return df


def rollup_dml_lids(df):
    """
    Roll up DML (Universal) lids into their parent category based on 
    what other components are on the same invoice.
    
    Logic:
    - If invoice has GB-4ML or GB-7ML → DML lid becomes Concentrates
    - If invoice has PB-15D (15D base) → DML lid becomes Drams (15D)
    - Otherwise → stays as DML (Universal) or defaults to Concentrates
    """
    if df.empty or 'Product Category' not in df.columns:
        return df
    
    df = df.copy()
    
    # Find invoices with DML lids
    dml_mask = df['Product Category'] == 'DML (Universal)'
    if not dml_mask.any():
        return df
    
    # Get document numbers with DML lids
    doc_col = 'Document Number' if 'Document Number' in df.columns else None
    if doc_col is None:
        # Can't pair without document number - default DML to Concentrates
        df.loc[dml_mask, 'Product Category'] = 'Concentrates'
        df.loc[dml_mask, 'Product Sub-Category'] = 'Universal Lid (4mL/7mL/15D)'
        return df
    
    # Process each invoice with DML lids
    dml_docs = df.loc[dml_mask, doc_col].unique()
    
    for doc in dml_docs:
        doc_mask = df[doc_col] == doc
        doc_items = df.loc[doc_mask]
        
        # Check what else is on this invoice
        has_concentrate_base = doc_items['Product Sub-Category'].str.contains(
            r'4mL Glass Base|7mL Glass Base', case=False, na=False
        ).any()
        
        has_15d_base = doc_items['Product Sub-Category'].str.contains(
            r'15D Base', case=False, na=False
        ).any()
        
        # Also check Item column for patterns
        if 'Item' in doc_items.columns:
            items_str = ' '.join(doc_items['Item'].fillna('').astype(str))
            if re.search(r'GB-4ML|GB-7ML|4ML.*GLASS|7ML.*GLASS', items_str.upper()):
                has_concentrate_base = True
            if re.search(r'PB-15D|15D.*BASE|-15B-', items_str.upper()):
                has_15d_base = True
        
        # Assign DML lids based on pairing
        dml_in_doc = doc_mask & dml_mask
        
        if has_concentrate_base:
            df.loc[dml_in_doc, 'Product Category'] = 'Concentrates'
            df.loc[dml_in_doc, 'Product Sub-Category'] = 'Universal Lid'
        elif has_15d_base:
            df.loc[dml_in_doc, 'Product Category'] = 'Drams'
            df.loc[dml_in_doc, 'Product Sub-Category'] = '15D Lid'
        else:
            # Default to Concentrates if no clear pairing
            df.loc[dml_in_doc, 'Product Category'] = 'Concentrates'
            df.loc[dml_in_doc, 'Product Sub-Category'] = 'Universal Lid'
    
    return df


def create_unified_product_view(df):
    """
    Create a unified product view that rolls up components into complete products.
    
    For example, instead of showing:
    - 4mL Glass Base: $300
    - Universal Lid: $200
    
    Show:
    - 4mL Concentrate Jar (complete): $500
    
    This is for customer-facing summaries.
    
    Creates two new columns:
    - 'Unified Category': Size-specific (e.g., "Drams (25D)", "Concentrates (4mL)")
    - 'Parent Category': Rolled up (e.g., "Drams", "Concentrates")
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # First apply DML rollup
    df = rollup_dml_lids(df)
    
    # Create unified category for display
    def get_unified_category(row):
        cat = row.get('Product Category', 'Other')
        subcat = row.get('Product Sub-Category', '')
        component = row.get('Component Type', '')
        
        # For categories that are already complete products
        if cat in ['Tubes', 'Boxes', 'Flexpack', 'Calyx Cure', 'Fees & Adjustments', 'Other']:
            return cat
        
        # For Drams - unify base + lid + labels
        if cat == 'Drams':
            # Extract size (15D, 25D, 45D, 145D)
            size_match = re.search(r'(\d+D)', str(subcat))
            if size_match:
                return f"Drams ({size_match.group(1)})"
            return 'Drams'
        
        # For Concentrates - unify jar + lid
        if cat == 'Concentrates':
            size_match = re.search(r'(4mL|7mL)', str(subcat))
            if size_match:
                return f"Concentrates ({size_match.group(1)})"
            # Universal lids without clear size match
            if 'lid' in str(subcat).lower() or 'universal' in str(subcat).lower():
                return 'Concentrate Lids'
            return 'Concentrates'
        
        # For Calyx Jar
        if cat == 'Calyx Jar':
            return 'Calyx Jar'
        
        # For accessories - keep unified as Dram Accessories (shows in sub-breakdown)
        if cat == 'Dram Accessories':
            return 'Dram Accessories'
        
        # For labels
        if cat == 'Non-Core Labels':
            return 'Non-Core Labels'
        
        return cat
    
    df['Unified Category'] = df.apply(get_unified_category, axis=1)
    
    # Create Parent Category (rolled up - for summary views)
    # This groups all Drams together, all Concentrates together, etc.
    def get_parent_category(unified_cat):
        if pd.isna(unified_cat):
            return 'Other'
        
        unified = str(unified_cat)
        
        # Roll up Drams (25D, 45D, 15D, 145D) and Dram Accessories → Drams
        if unified.startswith('Drams') or unified == 'Dram Accessories':
            return 'Drams'
        
        # Roll up Concentrates (4mL, 7mL) and Concentrate Lids → Concentrates
        if unified.startswith('Concentrates') or unified == 'Concentrate Lids':
            return 'Concentrates'
        
        # Everything else stays as-is
        return unified
    
    df['Parent Category'] = df['Unified Category'].apply(get_parent_category)
    
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
    
    # Create unique key prefix from customer name for chart keys
    key_prefix = f"line_items_{customer_name.replace(' ', '_').replace('.', '').replace(',', '')[:30]}"
    
    if line_items_df is None or line_items_df.empty:
        st.info(f"No invoice line item data available for {customer_name}.")
        return
    
    # Apply product categorization and create unified view
    line_items_df = apply_product_categories(line_items_df)
    line_items_df = create_unified_product_view(line_items_df)
    
    # Calculate totals for ALL line items (must match invoice main line)
    total_line_revenue = line_items_df['Amount'].sum() if 'Amount' in line_items_df.columns else 0
    total_quantity = line_items_df['Quantity'].sum() if 'Quantity' in line_items_df.columns else 0
    line_count = len(line_items_df)
    
    # Separate product items from fees for display purposes
    product_df = line_items_df[line_items_df['Product Category'] != 'Fees & Adjustments'].copy()
    fees_df = line_items_df[line_items_df['Product Category'] == 'Fees & Adjustments'].copy()
    
    product_revenue = product_df['Amount'].sum() if not product_df.empty else 0
    fees_revenue = fees_df['Amount'].sum() if not fees_df.empty else 0
    unique_categories = product_df['Unified Category'].nunique() if not product_df.empty and 'Unified Category' in product_df.columns else 0
    
    # Summary metrics - show TOTAL first (to match invoice main line)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Revenue", f"${total_line_revenue:,.0f}")
    with col2:
        st.metric("Product Revenue", f"${product_revenue:,.0f}")
    with col3:
        st.metric("Line Items", f"{line_count:,}")
    with col4:
        st.metric("Product Categories", f"{unique_categories}")
    
    # Show fees separately if they exist with detailed breakdown
    if fees_revenue != 0:
        with st.expander(f"💰 Fees & Adjustments: ${fees_revenue:,.0f} ({len(fees_df)} items)", expanded=False):
            # Break down fees by type
            fees_breakdown = fees_df.groupby('Product Sub-Category').agg({
                'Amount': 'sum',
                'Quantity': 'sum'
            }).reset_index()
            fees_breakdown.columns = ['Type', 'Amount', 'Count']
            fees_breakdown = fees_breakdown.sort_values('Amount', ascending=False)
            
            # Format for display
            for _, row in fees_breakdown.iterrows():
                amount = row['Amount']
                amount_str = f"${amount:,.0f}" if amount >= 0 else f"-${abs(amount):,.0f}"
                color = "#10b981" if amount < 0 else "#f59e0b"  # Green for credits, amber for charges
                st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; padding: 8px 12px; 
                                background: #1e293b; border-radius: 6px; margin-bottom: 6px;">
                        <span style="color: #e2e8f0;">{row['Type']}</span>
                        <span style="color: {color}; font-weight: 600;">{amount_str}</span>
                    </div>
                """, unsafe_allow_html=True)
    
    if product_df.empty:
        st.info("No product line items found (only fees/adjustments).")
        return
    
    # Create tabs for different analysis views
    analysis_tabs = st.tabs(["📊 Product Categories", "🔍 Category Breakdown", "📈 Purchase Patterns"])
    
    # =========================================================================
    # TAB 1: Product Categories Overview (Parent Categories with Expandable Sub-categories)
    # =========================================================================
    with analysis_tabs[0]:
        st.markdown("#### Product Categories")
        st.caption("Your purchases organized by product type (click to expand sub-categories)")
        
        # Group by Parent Category for rolled-up view
        parent_col = 'Parent Category' if 'Parent Category' in product_df.columns else 'Unified Category'
        unified_col = 'Unified Category' if 'Unified Category' in product_df.columns else 'Product Category'
        
        parent_summary = product_df.groupby(parent_col).agg({
            'Amount': 'sum',
            'Quantity': 'sum',
            'Document Number': 'nunique'
        }).reset_index()
        parent_summary.columns = ['Category', 'Revenue', 'Units', 'Orders']
        parent_summary = parent_summary.sort_values('Revenue', ascending=False)
        
        # Calculate percentages (of product revenue, not including fees)
        parent_summary['% of Revenue'] = (parent_summary['Revenue'] / product_revenue * 100).round(1) if product_revenue > 0 else 0
        
        if len(parent_summary) > 0:
            # Two columns: chart and summary with expandable sub-categories
            chart_col, summary_col = st.columns([1, 1])
            
            with chart_col:
                # Donut chart using Parent Categories
                fig = go.Figure(data=[go.Pie(
                    labels=parent_summary['Category'],
                    values=parent_summary['Revenue'],
                    hole=0.45,
                    textinfo='label+percent',
                    textposition='outside',
                    marker=dict(colors=['#3b82f6', '#10b981', '#f59e0b', '#ef4444', 
                                       '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'])
                )])
                fig.update_layout(
                    title="Revenue by Product Category",
                    showlegend=False,
                    height=450,
                    margin=dict(t=60, b=60, l=60, r=60)
                )
                st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_category_pie")
            
            with summary_col:
                # Parent category cards with expandable sub-categories
                st.markdown("**Revenue Breakdown** *(click to expand)*")
                
                for _, row in parent_summary.iterrows():
                    parent_cat = row['Category']
                    revenue_str = f"${row['Revenue']:,.0f}"
                    units_str = f"{row['Units']:,.0f} units"
                    pct_str = f"{row['% of Revenue']:.1f}%"
                    
                    # Check if this parent category has sub-categories
                    parent_cat_df = product_df[product_df[parent_col] == parent_cat]
                    sub_categories = parent_cat_df[unified_col].unique()
                    has_sub_cats = len(sub_categories) > 1 or (len(sub_categories) == 1 and sub_categories[0] != parent_cat)
                    
                    # Main category card
                    st.markdown(f"""
                        <div style="
                            background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%);
                            padding: 12px 16px;
                            border-radius: 8px;
                            margin-bottom: 4px;
                            border-left: 4px solid #3b82f6;
                        ">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="color: #f1f5f9; font-weight: 600;">{parent_cat}</span>
                                <span style="color: #10b981; font-weight: 700;">{revenue_str}</span>
                            </div>
                            <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 4px;">
                                {units_str} • {pct_str} of total • {int(row['Orders'])} orders
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Expandable sub-categories if they exist
                    if has_sub_cats:
                        with st.expander(f"↳ View {parent_cat} breakdown", expanded=False):
                            # Get sub-category breakdown
                            subcat_breakdown = parent_cat_df.groupby(unified_col).agg({
                                'Amount': 'sum',
                                'Quantity': 'sum',
                                'Document Number': 'nunique'
                            }).reset_index()
                            subcat_breakdown.columns = ['Sub-Category', 'Revenue', 'Units', 'Orders']
                            subcat_breakdown = subcat_breakdown.sort_values('Revenue', ascending=False)
                            subcat_breakdown['% of Parent'] = (subcat_breakdown['Revenue'] / row['Revenue'] * 100).round(1) if row['Revenue'] > 0 else 0
                            
                            for _, sub_row in subcat_breakdown.iterrows():
                                sub_name = sub_row['Sub-Category']
                                # Clean up the sub-category name (remove parent prefix for cleaner display)
                                display_name = sub_name.replace(f"{parent_cat} ", "").replace(f"{parent_cat}", sub_name)
                                if display_name == parent_cat:
                                    display_name = sub_name
                                
                                st.markdown(f"""
                                    <div style="
                                        background: #0f172a;
                                        padding: 8px 12px;
                                        border-radius: 6px;
                                        margin-bottom: 4px;
                                        margin-left: 12px;
                                        border-left: 2px solid #475569;
                                    ">
                                        <div style="display: flex; justify-content: space-between; align-items: center;">
                                            <span style="color: #cbd5e1; font-size: 0.9rem;">{display_name}</span>
                                            <span style="color: #10b981; font-weight: 600;">${sub_row['Revenue']:,.0f}</span>
                                        </div>
                                        <div style="color: #64748b; font-size: 0.8rem;">
                                            {sub_row['Units']:,.0f} units • {sub_row['% of Parent']:.1f}% of {parent_cat}
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)
            
            # Detailed table
            with st.expander("📋 View Category Details Table"):
                display_df = parent_summary.copy()
                display_df['Revenue'] = display_df['Revenue'].apply(lambda x: f"${x:,.0f}")
                display_df['Units'] = display_df['Units'].apply(lambda x: f"{x:,.0f}")
                display_df['% of Revenue'] = display_df['% of Revenue'].apply(lambda x: f"{x:.1f}%")
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Verification section - shows actual line items for each category
            with st.expander("🔍 Verify Categorization (View Raw Line Items)"):
                st.caption("Review the actual SKUs/items included in each category to verify correct classification")
                
                # Category selector
                verify_category = st.selectbox(
                    "Select category to inspect:",
                    options=parent_summary['Category'].tolist(),
                    key=f"{key_prefix}_verify_cat"
                )
                
                if verify_category:
                    # Get items in this category
                    cat_items = product_df[product_df[parent_col] == verify_category].copy()
                    
                    # Determine which columns to show
                    verify_cols = []
                    if 'Item' in cat_items.columns:
                        verify_cols.append('Item')
                    if 'Item Description' in cat_items.columns:
                        verify_cols.append('Item Description')
                    verify_cols.extend(['Product Category', 'Product Sub-Category', 'Unified Category'])
                    if 'Amount' in cat_items.columns:
                        verify_cols.append('Amount')
                    if 'Quantity' in cat_items.columns:
                        verify_cols.append('Quantity')
                    if 'Document Number' in cat_items.columns:
                        verify_cols.append('Document Number')
                    
                    # Filter to existing columns
                    verify_cols = [c for c in verify_cols if c in cat_items.columns]
                    
                    if verify_cols:
                        verify_display = cat_items[verify_cols].copy()
                        
                        # Format Amount
                        if 'Amount' in verify_display.columns:
                            verify_display['Amount'] = verify_display['Amount'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "-")
                        
                        # Format Quantity
                        if 'Quantity' in verify_display.columns:
                            verify_display['Quantity'] = verify_display['Quantity'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "-")
                        
                        # Show summary stats
                        st.markdown(f"""
                            <div style="background: #1e293b; padding: 10px 15px; border-radius: 6px; margin-bottom: 10px;">
                                <span style="color: #94a3b8;">Items in <strong style="color: #f1f5f9;">{verify_category}</strong>:</span>
                                <span style="color: #10b981; font-weight: 600; margin-left: 10px;">{len(cat_items)} line items</span>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Show the data
                        st.dataframe(
                            verify_display.sort_values('Amount' if 'Amount' in verify_display.columns else verify_cols[0], ascending=False),
                            use_container_width=True,
                            hide_index=True,
                            height=400
                        )
                        
                        # Show unique sub-categories in this parent
                        if 'Product Sub-Category' in cat_items.columns:
                            unique_subcats = cat_items['Product Sub-Category'].unique()
                            st.markdown("**Sub-categories found:**")
                            for subcat in unique_subcats:
                                subcat_count = len(cat_items[cat_items['Product Sub-Category'] == subcat])
                                subcat_revenue = cat_items[cat_items['Product Sub-Category'] == subcat]['Amount'].sum() if 'Amount' in cat_items.columns else 0
                                st.markdown(f"- `{subcat}`: {subcat_count} items, ${subcat_revenue:,.0f}")
                    else:
                        st.info("No detailed item data available for verification.")
    
    # =========================================================================
    # TAB 2: Category Breakdown (Drill-down into each category)
    # =========================================================================
    with analysis_tabs[1]:
        st.markdown("#### Category Breakdown")
        st.caption("Drill down into each product category to see components and sizes")
        
        # Get categories ordered by revenue (using Parent Category for drill-down)
        parent_col = 'Parent Category' if 'Parent Category' in product_df.columns else 'Unified Category'
        categories_ordered = parent_summary['Category'].tolist()
        
        for category in categories_ordered:
            cat_df = product_df[product_df[parent_col] == category]
            cat_revenue = cat_df['Amount'].sum()
            cat_units = cat_df['Quantity'].sum()
            
            # Get sub-category breakdown (shows components: Base, Lid, Label, etc.)
            subcat_summary = cat_df.groupby('Product Sub-Category').agg({
                'Amount': 'sum',
                'Quantity': 'sum',
                'Document Number': 'nunique'
            }).reset_index()
            subcat_summary.columns = ['Component', 'Revenue', 'Units', 'Orders']
            subcat_summary = subcat_summary.sort_values('Revenue', ascending=False)
            subcat_summary['% of Category'] = (subcat_summary['Revenue'] / cat_revenue * 100).round(1) if cat_revenue > 0 else 0
            
            # Also get component type breakdown
            if 'Component Type' in cat_df.columns:
                component_summary = cat_df.groupby('Component Type').agg({
                    'Amount': 'sum'
                }).reset_index()
                component_summary.columns = ['Type', 'Revenue']
                component_summary = component_summary.sort_values('Revenue', ascending=False)
            
            # Category header with summary
            with st.expander(f"**{category}** — ${cat_revenue:,.0f} ({cat_units:,.0f} units)", expanded=(category == categories_ordered[0])):
                
                # Show component type summary if available
                if 'Component Type' in cat_df.columns:
                    comp_types = cat_df['Component Type'].dropna().unique()
                    if len(comp_types) > 1:
                        comp_str = ", ".join([f"{t}s" for t in comp_types if t])
                        st.caption(f"Includes: {comp_str}")
                
                if len(subcat_summary) > 1:
                    # Show breakdown chart
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        fig = go.Figure(data=[go.Bar(
                            x=subcat_summary['Component'],
                            y=subcat_summary['Revenue'],
                            marker_color='#3b82f6',
                            text=subcat_summary['Revenue'].apply(lambda x: f"${x/1000:.1f}K" if x >= 1000 else f"${x:.0f}"),
                            textposition='outside'
                        )])
                        fig.update_layout(
                            title=f"{category} Components",
                            xaxis_title="",
                            yaxis_title="Revenue ($)",
                            height=350,
                            margin=dict(t=60, b=100, l=60, r=40),
                            xaxis_tickangle=-35
                        )
                        # Create unique key using category name
                        cat_key = category.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')[:20]
                        st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_cat_{cat_key}")
                    
                    with col2:
                        # Summary table
                        display_subcat = subcat_summary.copy()
                        display_subcat['Revenue'] = display_subcat['Revenue'].apply(lambda x: f"${x:,.0f}")
                        display_subcat['Units'] = display_subcat['Units'].apply(lambda x: f"{x:,.0f}")
                        display_subcat['% of Category'] = display_subcat['% of Category'].apply(lambda x: f"{x:.1f}%")
                        st.dataframe(display_subcat, use_container_width=True, hide_index=True)
                else:
                    # Single sub-category, just show the value
                    if not subcat_summary.empty:
                        st.markdown(f"**{subcat_summary.iloc[0]['Component']}**: ${subcat_summary.iloc[0]['Revenue']:,.0f} ({subcat_summary.iloc[0]['Units']:,.0f} units)")
                
                # Show top items in this category - ROLLED UP by Sub-Category
                st.markdown("---")
                st.markdown("**Top Items in this Category:**")
                
                # Group by Product Sub-Category for clean rolled-up view
                if 'Product Sub-Category' in cat_df.columns:
                    top_items = cat_df.groupby('Product Sub-Category').agg({
                        'Amount': 'sum',
                        'Quantity': 'sum'
                    }).reset_index().sort_values('Amount', ascending=False).head(5)
                    top_items.columns = ['Item', 'Revenue', 'Units']
                else:
                    # Fallback to Item Description if Sub-Category not available
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
        
        # Analyze purchase frequency by Unified Category
        category_col = 'Unified Category' if 'Unified Category' in product_df.columns else 'Product Category'
        
        category_frequency = product_df.groupby(category_col).agg({
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
                height=380,
                margin=dict(t=60, b=120, l=60, r=40),
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_orders_per_cat")
        
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
                height=380,
                margin=dict(t=60, b=80, l=60, r=40)
            )
            st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_rev_by_pattern")
        
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


def render_ncr_section(customer_ncrs, customer_orders, customer_name):
    """
    Section: Non-Conformance Report (NCR) Analysis
    Shows quality issues for the customer - how many orders had NCRs, issue types, etc.
    Combines data from both NetSuite (Nov 2024+) and HubSpot (historical)
    """
    st.markdown("### 📋 Quality Performance")
    st.caption("Non-conformance tracking and resolution metrics")
    
    # Create unique key prefix from customer name for chart keys
    key_prefix = f"ncr_{customer_name.replace(' ', '_').replace('.', '').replace(',', '')[:30]}"
    
    # Calculate total orders for this customer
    total_orders = len(customer_orders) if not customer_orders.empty else 0
    
    # If no NCR data available at all
    if customer_ncrs is None or customer_ncrs.empty:
        st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #064e3b 0%, #065f46 100%);
                padding: 1.5rem;
                border-radius: 12px;
                border-left: 4px solid #10b981;
            ">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 2rem;">✅</span>
                    <div>
                        <div style="color: #f1f5f9; font-weight: 700; font-size: 1.2rem;">No Quality Issues Recorded</div>
                        <div style="color: #a7f3d0; font-size: 0.9rem;">
                            {f'{total_orders} orders' if total_orders > 0 else 'Orders'} with zero NCRs on file
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        return
    
    # ===== NCR FILTER - MOVED TO TOP =====
    # Get list of all NCR numbers for filtering
    all_ncr_numbers = []
    if 'NC Number' in customer_ncrs.columns:
        all_ncr_numbers = customer_ncrs['NC Number'].dropna().unique().tolist()
    
    # NCR Filter expander at the top
    with st.expander("🔧 Filter NCRs (exclude specific NCRs from analysis)", expanded=False):
        if all_ncr_numbers:
            st.markdown("**Deselect NCRs to exclude them from ALL metrics and charts below:**")
            selected_ncrs = st.multiselect(
                "NCRs to include",
                options=all_ncr_numbers,
                default=all_ncr_numbers,
                key=f"{key_prefix}_ncr_filter",
                label_visibility="collapsed"
            )
            
            # Show count of excluded NCRs
            excluded_count = len(all_ncr_numbers) - len(selected_ncrs)
            if excluded_count > 0:
                st.markdown(f"""
                    <div style="
                        background: #7f1d1d;
                        padding: 8px 12px;
                        border-radius: 6px;
                        margin-top: 10px;
                        color: #fecaca;
                        font-size: 0.85rem;
                    ">
                        ⚠️ {excluded_count} NCR(s) excluded — metrics below reflect filtered data
                    </div>
                """, unsafe_allow_html=True)
        else:
            selected_ncrs = []
    
    # Apply filter to NCR data - this filtered data is used for ALL metrics below
    if all_ncr_numbers and 'NC Number' in customer_ncrs.columns:
        filtered_ncrs = customer_ncrs[customer_ncrs['NC Number'].isin(selected_ncrs)].copy()
    else:
        filtered_ncrs = customer_ncrs.copy()
    
    # Check if all NCRs were filtered out
    if filtered_ncrs.empty:
        st.info("All NCRs have been excluded by the filter above. Deselect fewer NCRs to see metrics.")
        return
    
    # Show filter status banner if filtering is active
    if all_ncr_numbers and len(selected_ncrs) < len(all_ncr_numbers):
        st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #1e3a5f 0%, #164e63 100%);
                padding: 10px 16px;
                border-radius: 8px;
                border-left: 4px solid #f59e0b;
                margin-bottom: 1rem;
            ">
                <span style="color: #fcd34d; font-weight: 600;">📊 Filtered View:</span>
                <span style="color: #e2e8f0;"> Showing {len(selected_ncrs)} of {len(all_ncr_numbers)} NCRs</span>
            </div>
        """, unsafe_allow_html=True)
    
    # ===== CALCULATE METRICS USING FILTERED DATA =====
    ncr_count = len(filtered_ncrs)
    
    # Get unique Sales Orders with NCRs
    ncr_so_numbers = set()
    if 'Sales Order' in filtered_ncrs.columns:
        ncr_so_numbers = set(filtered_ncrs['Sales Order'].dropna().unique())
        ncr_so_numbers = {str(so).strip() for so in ncr_so_numbers if str(so).strip()}
    
    # Calculate orders affected
    orders_with_ncrs = len(ncr_so_numbers)
    ncr_rate = (orders_with_ncrs / total_orders * 100) if total_orders > 0 else 0
    
    # Total Quantity Affected
    total_qty_affected = 0
    if 'Total Quantity Affected' in filtered_ncrs.columns:
        total_qty_affected = filtered_ncrs['Total Quantity Affected'].sum()
    
    # Source breakdown
    netsuite_count = 0
    hubspot_count = 0
    if 'NCR Source' in filtered_ncrs.columns:
        netsuite_count = len(filtered_ncrs[filtered_ncrs['NCR Source'] == 'NetSuite'])
        hubspot_count = len(filtered_ncrs[filtered_ncrs['NCR Source'] == 'HubSpot'])
    
    # Resolution time metrics (HubSpot data has this)
    avg_resolution = None
    if 'Resolution Days' in filtered_ncrs.columns:
        resolution_data = filtered_ncrs['Resolution Days'].dropna()
        if len(resolution_data) > 0:
            avg_resolution = resolution_data.mean()
    
    # ===== TOTAL NCR METRICS (always based on ALL NCRs, not filtered) =====
    # These are the "headline" numbers that shouldn't change with filtering
    total_ncr_count = len(customer_ncrs)
    
    # Calculate NCR rate as: Total NCRs / Total Orders (more intuitive metric)
    total_ncr_rate = (total_ncr_count / total_orders * 100) if total_orders > 0 else 0
    
    # Determine badge based on TOTAL NCR rate
    if total_ncr_rate < 2:
        rate_badge = "EXCELLENT"
        badge_color = "#10b981"
        badge_bg = "#064e3b"
    elif total_ncr_rate < 5:
        rate_badge = "STRONG"
        badge_color = "#10b981"
        badge_bg = "#064e3b"
    elif total_ncr_rate < 10:
        rate_badge = "TRACKING"
        badge_color = "#f59e0b"
        badge_bg = "#78350f"
    else:
        rate_badge = "MONITORING"
        badge_color = "#f59e0b"
        badge_bg = "#78350f"
    
    # Summary metrics row 1 - with styled badge card
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Styled NCR Rate card with badge
        st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {badge_bg} 0%, #1e293b 100%);
                padding: 16px;
                border-radius: 12px;
                border: 1px solid {badge_color}40;
                text-align: center;
            ">
                <div style="
                    background: {badge_color};
                    color: white;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 0.7rem;
                    font-weight: 700;
                    display: inline-block;
                    margin-bottom: 8px;
                ">{rate_badge}</div>
                <div style="color: {badge_color}; font-size: 2rem; font-weight: 700;">{total_ncr_rate:.1f}%</div>
                <div style="color: #94a3b8; font-size: 0.85rem;">NCR Rate</div>
                <div style="color: #64748b; font-size: 0.75rem;">{total_ncr_count} of {total_orders} orders</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.metric("Total NCRs", total_ncr_count)
    
    with col3:
        # Use filtered qty for this one (shows impact of selected NCRs)
        st.metric("Qty Affected", f"{total_qty_affected:,.0f}")
    
    with col4:
        # Get most common issue type from filtered data
        if 'Issue Type' in filtered_ncrs.columns:
            issue_counts = filtered_ncrs['Issue Type'].value_counts()
            top_issue = issue_counts.index[0] if len(issue_counts) > 0 else "N/A"
            top_count = issue_counts.iloc[0] if len(issue_counts) > 0 else 0
            st.metric("Top Issue Type", top_issue, f"{top_count} occurrences")
        else:
            st.metric("Issue Types", "N/A")
    
    # Source breakdown and resolution metrics row
    if netsuite_count > 0 or hubspot_count > 0 or avg_resolution is not None:
        st.markdown("---")
        
        source_cols = st.columns(4)
        
        with source_cols[0]:
            st.markdown(f"""
                <div style="
                    background: #1e293b;
                    padding: 12px 16px;
                    border-radius: 8px;
                    border-left: 3px solid #3b82f6;
                ">
                    <div style="color: #94a3b8; font-size: 0.8rem;">NetSuite NCRs</div>
                    <div style="color: #f1f5f9; font-size: 1.3rem; font-weight: 600;">{netsuite_count}</div>
                    <div style="color: #64748b; font-size: 0.75rem;">Nov 2024+</div>
                </div>
            """, unsafe_allow_html=True)
        
        with source_cols[1]:
            st.markdown(f"""
                <div style="
                    background: #1e293b;
                    padding: 12px 16px;
                    border-radius: 8px;
                    border-left: 3px solid #f59e0b;
                ">
                    <div style="color: #94a3b8; font-size: 0.8rem;">HubSpot NCRs</div>
                    <div style="color: #f1f5f9; font-size: 1.3rem; font-weight: 600;">{hubspot_count}</div>
                    <div style="color: #64748b; font-size: 0.75rem;">Historical</div>
                </div>
            """, unsafe_allow_html=True)
        
        with source_cols[2]:
            if avg_resolution is not None:
                resolution_color = "#10b981" if avg_resolution <= 7 else "#f59e0b" if avg_resolution <= 14 else "#ef4444"
                st.markdown(f"""
                    <div style="
                        background: #1e293b;
                        padding: 12px 16px;
                        border-radius: 8px;
                        border-left: 3px solid {resolution_color};
                    ">
                        <div style="color: #94a3b8; font-size: 0.8rem;">Avg Resolution</div>
                        <div style="color: #f1f5f9; font-size: 1.3rem; font-weight: 600;">{avg_resolution:.1f} days</div>
                        <div style="color: #64748b; font-size: 0.75rem;">Create → Close</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style="
                        background: #1e293b;
                        padding: 12px 16px;
                        border-radius: 8px;
                        border-left: 3px solid #475569;
                    ">
                        <div style="color: #94a3b8; font-size: 0.8rem;">Avg Resolution</div>
                        <div style="color: #64748b; font-size: 1.3rem; font-weight: 600;">N/A</div>
                        <div style="color: #64748b; font-size: 0.75rem;">No data</div>
                    </div>
                """, unsafe_allow_html=True)
        
        with source_cols[3]:
            # Closed vs Open
            if 'Close Date' in filtered_ncrs.columns or 'Status' in filtered_ncrs.columns:
                closed_count = 0
                if 'Close Date' in filtered_ncrs.columns:
                    closed_count = filtered_ncrs['Close Date'].notna().sum()
                elif 'Status' in filtered_ncrs.columns:
                    closed_statuses = ['Closed', 'Resolved', 'Complete', 'Done']
                    closed_count = filtered_ncrs['Status'].isin(closed_statuses).sum()
                
                open_count = ncr_count - closed_count
                st.markdown(f"""
                    <div style="
                        background: #1e293b;
                        padding: 12px 16px;
                        border-radius: 8px;
                        border-left: 3px solid {'#10b981' if open_count == 0 else '#ef4444'};
                    ">
                        <div style="color: #94a3b8; font-size: 0.8rem;">Status</div>
                        <div style="color: #f1f5f9; font-size: 1.3rem; font-weight: 600;">{closed_count} Closed</div>
                        <div style="color: {'#10b981' if open_count == 0 else '#fbbf24'}; font-size: 0.75rem;">{open_count} Open</div>
                    </div>
                """, unsafe_allow_html=True)
    
    # Issue Type Breakdown
    if 'Issue Type' in filtered_ncrs.columns:
        st.markdown("**Issue Type Breakdown:**")
        
        issue_summary = filtered_ncrs.groupby('Issue Type').agg({
            'NC Number': 'count' if 'NC Number' in filtered_ncrs.columns else 'size',
            'Total Quantity Affected': 'sum' if 'Total Quantity Affected' in filtered_ncrs.columns else lambda x: 0
        }).reset_index()
        
        # Rename columns safely
        if 'NC Number' in issue_summary.columns:
            issue_summary = issue_summary.rename(columns={'NC Number': 'NCR Count'})
        else:
            issue_summary['NCR Count'] = issue_summary.iloc[:, 1]
        
        if 'Total Quantity Affected' in issue_summary.columns:
            issue_summary = issue_summary.rename(columns={'Total Quantity Affected': 'Qty Affected'})
        else:
            issue_summary['Qty Affected'] = 0
        
        issue_summary = issue_summary.sort_values('NCR Count', ascending=False)
        
        # Calculate percentage of total NCRs
        issue_summary['% of NCRs'] = (issue_summary['NCR Count'] / ncr_count * 100).round(1)
        
        # Two columns: chart and table
        col_chart, col_table = st.columns([1, 1])
        
        with col_chart:
            if len(issue_summary) > 0:
                # Color scale - red shades for quality issues
                colors = ['#ef4444', '#f59e0b', '#f97316', '#fb923c', '#fbbf24', '#fcd34d', '#fde68a', '#fef3c7']
                
                fig = go.Figure(data=[go.Pie(
                    labels=issue_summary['Issue Type'],
                    values=issue_summary['NCR Count'],
                    hole=0.45,
                    textinfo='label+percent',
                    textposition='outside',
                    marker=dict(colors=colors[:len(issue_summary)])
                )])
                fig.update_layout(
                    title="NCRs by Issue Type",
                    showlegend=False,
                    height=350,
                    margin=dict(t=60, b=40, l=40, r=40)
                )
                st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_issue_pie")
        
        with col_table:
            display_summary = issue_summary.copy()
            display_summary['Qty Affected'] = display_summary['Qty Affected'].apply(lambda x: f"{x:,.0f}")
            display_summary['% of NCRs'] = display_summary['% of NCRs'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(
                display_summary[['Issue Type', 'NCR Count', 'Qty Affected', '% of NCRs']],
                use_container_width=True,
                hide_index=True
            )
    
    # NCR Details Expander - now just shows the filtered data (filtering is done at top)
    with st.expander("📋 View NCR Details"):
        # Select columns to display - include source, product type, and resolution info
        display_cols = []
        for col in ['NC Number', 'NCR Source', 'Product Type Affected', 'Sales Order', 'Issue Type', 'Priority', 'Status', 
                    'Defect Summary', 'Total Quantity Affected', 'Date Submitted', 'Close Date', 'Resolution Days']:
            if col in filtered_ncrs.columns:
                display_cols.append(col)
        
        if display_cols:
            display_df = filtered_ncrs[display_cols].copy()
            
            # Format quantity
            if 'Total Quantity Affected' in display_df.columns:
                display_df['Total Quantity Affected'] = display_df['Total Quantity Affected'].apply(
                    lambda x: f"{x:,.0f}" if pd.notna(x) and x > 0 else "-"
                )
            
            # Format dates
            if 'Date Submitted' in display_df.columns:
                display_df['Date Submitted'] = pd.to_datetime(
                    display_df['Date Submitted'], errors='coerce'
                ).dt.strftime('%Y-%m-%d').fillna('')
            
            if 'Close Date' in display_df.columns:
                display_df['Close Date'] = pd.to_datetime(
                    display_df['Close Date'], errors='coerce'
                ).dt.strftime('%Y-%m-%d').fillna('')
            
            # Format resolution days
            if 'Resolution Days' in display_df.columns:
                display_df['Resolution Days'] = display_df['Resolution Days'].apply(
                    lambda x: f"{x:.0f} days" if pd.notna(x) else "-"
                )
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No detailed NCR information available.")
    
    # Visual indicator based on NCR rate
    if ncr_rate > 10:
        st.warning(f"⚠️ NCR rate of {ncr_rate:.1f}% is above the 10% threshold. Consider scheduling a quality review meeting.")
    elif ncr_rate > 5:
        st.info(f"📊 NCR rate of {ncr_rate:.1f}% - moderate. Monitor for patterns in issue types.")


# ========== MAIN RENDER FUNCTION ==========


# ===================================================================================
# 2026 ANNUAL GOAL TRACKER - ADDED CONSTANTS AND FUNCTIONS
# ===================================================================================

# Forecast Categories
FORECAST_CATEGORIES = ['Drams', 'Flexpack', 'Cure', 'Cube', 'Glass', 'Labels', 'Application', 'Shipping', 'Other']

# Forecast Pipelines  
FORECAST_PIPELINES = ['Retention', 'Growth', 'Acquisition', 'Distributors', 'Ecom']

# Category colors for Annual Goal Tracker
CATEGORY_COLORS = {
    'Drams': '#3b82f6',
    'Flexpack': '#10b981',
    'Cure': '#8b5cf6',
    'Cube': '#f59e0b',
    'Glass': '#06b6d4',
    'Labels': '#ec4899',
    'Application': '#f97316',
    'Shipping': '#64748b',
    'Other': '#94a3b8',
    'Total': '#1e40af'
}

# Pipeline colors for Annual Goal Tracker
PIPELINE_COLORS = {
    'Retention': '#10b981',
    'Growth': '#3b82f6',
    'Acquisition': '#8b5cf6',
    'Distributors': '#f59e0b',
    'Ecom': '#06b6d4',
    'Total': '#1e40af'
}

# Month mapping
MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 
               'July', 'August', 'September', 'October', 'November', 'December']
MONTH_ABBREV = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


# ===================================================================================
# ANNUAL GOAL TRACKER - MAPPING FUNCTIONS
# ===================================================================================

def map_to_forecast_category(product_category, sub_category=None):
    """
    Map product category to forecast category.
    
    Since apply_product_categories now outputs Forecast Categories directly
    (Drams, Flexpack, Cure, Glass, Labels, Application, Shipping, Other),
    this function mainly passes them through or handles legacy categories.
    
    Forecast Categories:
        - Drams
        - Flexpack
        - Cure
        - Glass
        - Labels
        - Application
        - Shipping
        - Other
    """
    if pd.isna(product_category):
        return 'Other'
    
    cat = str(product_category).strip()
    
    # Direct pass-through for new Calyx-based categories
    valid_forecast_categories = ['Drams', 'Flexpack', 'Cure', 'Glass', 'Labels', 'Application', 'Shipping', 'Other']
    if cat in valid_forecast_categories:
        return cat
    
    # Handle legacy category names (backward compatibility)
    legacy_mappings = {
        'Dram Accessories': 'Drams',
        'DML (Universal)': 'Drams',
        'Calyx Cure': 'Cure',
        'Concentrates': 'Glass',
        'Calyx Jar': 'Glass',
        'Non-Core Labels': 'Labels',
        'Fees & Adjustments': 'Other',
        'Boxes': 'Other',
        'Tubes': 'Other',
    }
    
    if cat in legacy_mappings:
        return legacy_mappings[cat]
    
    return 'Other'


def map_to_forecast_pipeline(pipeline_value):
    """Map HubSpot pipeline values to forecast pipeline categories"""
    if pd.isna(pipeline_value):
        return None
    
    pipeline = str(pipeline_value).upper().strip()
    
    if 'RETENTION' in pipeline:
        return 'Retention'
    if 'GROWTH' in pipeline:
        return 'Growth'
    if 'ACQUISITION' in pipeline or 'NEW' in pipeline:
        return 'Acquisition'
    if 'DISTRIBUT' in pipeline or 'DISTRIBUTION' in pipeline:
        return 'Distributors'
    if 'ECOM' in pipeline or 'E-COM' in pipeline or 'E COM' in pipeline:
        return 'Ecom'
    
    return None


def map_order_type_to_forecast_category(order_type):
    """Map Order Type from Sales Orders to Forecast Category"""
    if pd.isna(order_type):
        return 'Other'
    
    ot = str(order_type).upper().strip()
    
    if 'DRAM' in ot or re.search(r'15D|25D|45D|145D', ot):
        return 'Drams'
    if 'FLEX' in ot or 'WAVE' in ot or 'BAG' in ot:
        return 'Flexpack'
    if 'CURE' in ot:
        return 'Cure'
    if 'CUBE' in ot:
        return 'Cube'
    if 'GLASS' in ot or 'CONCENTRATE' in ot or re.search(r'4ML|7ML', ot):
        return 'Glass'
    if 'LABEL' in ot:
        return 'Labels'
    if 'APPL' in ot or 'APPLICATION' in ot:
        return 'Application'
    if 'SHIP' in ot or 'FREIGHT' in ot:
        return 'Shipping'
    
    return 'Other'


def map_deal_type_to_forecast_category(deal_type):
    """Map Deal Type from HubSpot to Forecast Category"""
    if pd.isna(deal_type):
        return 'Other'
    
    dt = str(deal_type).upper().strip()
    
    # Drams - check first since "LABELED" appears in multiple categories
    if 'NON-LABELED' in dt or 'NON LABELED' in dt:
        return 'Drams'
    if 'DRAM' in dt:
        return 'Drams'
    if 'LABELED' in dt and 'LABELS ONLY' not in dt:
        return 'Drams'
    
    # Flexpack
    if 'FLEXPACK' in dt or 'FLEX' in dt or 'WAVE' in dt or 'BAG' in dt:
        return 'Flexpack'
    
    # Cure
    if 'CURE' in dt or 'CALYX CURE' in dt:
        return 'Cure'
    
    # Cube
    if 'CUBE' in dt:
        return 'Cube'
    
    # Glass (concentrates, jars)
    if 'GLASS' in dt or 'CONCENTRATE' in dt or 'JAR' in dt or '4ML' in dt or '7ML' in dt or '8TH' in dt:
        return 'Glass'
    
    # Labels
    if 'LABELS ONLY' in dt or 'LABEL' in dt:
        return 'Labels'
    
    # Application
    if 'APPLICATION' in dt or 'APPL' in dt:
        return 'Application'
    
    # Shipping
    if 'SHIP' in dt or 'FREIGHT' in dt:
        return 'Shipping'
    
    # Boxes go to Other
    if 'OUTER BOX' in dt or 'BOX' in dt:
        return 'Other'
    
    return 'Other'


# ===================================================================================
# ANNUAL GOAL TRACKER - DATA LOADING FUNCTIONS
# ===================================================================================

def parse_forecast_sheet(raw_df):
    """Parse the 2026 Forecast sheet structure"""
    if raw_df.empty:
        return pd.DataFrame()
    
    all_data = []
    
    month_cols = {
        'January': 2, 'February': 3, 'March': 4,
        'April': 6, 'May': 7, 'June': 8,
        'July': 10, 'August': 11, 'September': 12,
        'October': 14, 'November': 15, 'December': 16
    }
    
    quarter_cols = {'Q1': 5, 'Q2': 9, 'Q3': 13, 'Q4': 17}
    yearly_col = 18
    
    current_pipeline = None
    valid_pipelines = ['Retention', 'Growth', 'Acquisition', 'Distributors', 'Ecom', 'Total']
    categories = ['Drams', 'Flexpack', 'Cure', 'Cube', 'Glass', 'Labels', 'Application', 'Shipping', 'Other', 'Total']
    
    for idx, row in raw_df.iterrows():
        if len(row) < 3:
            continue
        
        first_col = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
        second_col = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ''
        
        if first_col in valid_pipelines:
            current_pipeline = first_col
        
        if second_col == 'Category':
            continue
        
        if second_col == '' or second_col == 'nan':
            continue
        
        if current_pipeline and second_col in categories:
            row_data = {
                'Pipeline': current_pipeline,
                'Category': second_col
            }
            
            for month, col_idx in month_cols.items():
                if col_idx < len(row):
                    row_data[month] = clean_numeric(row.iloc[col_idx])
                else:
                    row_data[month] = 0.0
            
            for quarter, col_idx in quarter_cols.items():
                if col_idx < len(row):
                    row_data[quarter] = clean_numeric(row.iloc[col_idx])
                else:
                    row_data[quarter] = 0.0
            
            if yearly_col < len(row):
                row_data['Annual_Total'] = clean_numeric(row.iloc[yearly_col])
            else:
                row_data['Annual_Total'] = 0.0
            
            all_data.append(row_data)
    
    if not all_data:
        return pd.DataFrame()
    
    return pd.DataFrame(all_data)


@st.cache_data(ttl=300)
def load_forecast_data():
    """Load and parse the 2026 Forecast data"""
    raw_df = load_google_sheets_data("2026 Forecast", "A1:S80", version=CACHE_VERSION, silent=True)
    
    if raw_df.empty:
        return pd.DataFrame()
    
    return parse_forecast_sheet(raw_df)


@st.cache_data(ttl=300)
def load_annual_tracker_data():
    """Load all data needed for the Annual Goal Tracker"""
    
    line_items_df = load_google_sheets_data("Invoice Line Item", "A:Z", version=CACHE_VERSION)
    invoices_df = load_google_sheets_data("_NS_Invoices_Data", "A:U", version=CACHE_VERSION)
    sales_orders_df = load_google_sheets_data("_NS_SalesOrders_Data", "A:AG", version=CACHE_VERSION)
    deals_df = load_google_sheets_data("All Reps All Pipelines", "A:Z", version=CACHE_VERSION)
    forecast_df = load_forecast_data()
    
    # Load Sales Order Line Item for proper categorization (same structure as Invoice Line Item)
    sales_order_line_items_df = load_google_sheets_data("Sales Order Line Item", "A:W", version=CACHE_VERSION, silent=True)
    
    # Load Copy of Deals Line Item for Close Rate Analysis
    # Note: Column headers are in row 2 of the sheet
    # Range extended to AB to include Effective unit price column
    deals_line_items_df = load_google_sheets_data("Copy of Deals Line Item", "A2:AB", version=CACHE_VERSION, silent=True)
    
    # Load Deals Line Item for Pipeline Section (Plan vs Full Pipeline)
    # Note: Column headers are in row 2 of the sheet
    # This is the active pipeline view - no standard reorder/Gonzalez filtering
    # Extended to Column V to include "Pending Approval Date"
    pipeline_deals_df = load_google_sheets_data("Deals Line Item", "A2:V", version=CACHE_VERSION, silent=True)
    
    # Standard Reorder Date columns - if ANY of these have a value, exclude the deal
    # These are columns R through Y in the Copy of Deals Line Item sheet
    STANDARD_REORDER_DATE_COLS = [
        'Date entered "Standard Reorder - Confirmed by Customer (Acquisition (New Customer))"',
        'Date entered "Standard Reorder - Confirmed by Customer (Calyx Distribution)"',
        'Date entered "Standard Reorder - Confirmed by Customer (Growth Pipeline (Upsell/Cross-sell))"',
        'Date entered "Standard Reorder - Confirmed by Customer- (Retention (Existing Product))"',
        'Date entered "Standard Reorder - Pending Customer Confirmation (Acquisition (New Customer))"',
        'Date entered "Standard Reorder - Pending Customer Confirmation (Calyx Distribution)"',
        'Date entered "Standard Reorder - Pending Customer Confirmation (Growth Pipeline (Upsell/Cross-sell))"',
        'Date entered "Standard Reorder - Pending Customer Confirmation (Retention (Existing Product))"',
    ]
    
    # Process Invoice Line Items
    if not line_items_df.empty:
        if line_items_df.columns.duplicated().any():
            line_items_df = line_items_df.loc[:, ~line_items_df.columns.duplicated()]
        
        if 'Amount' in line_items_df.columns:
            line_items_df['Amount'] = line_items_df['Amount'].apply(clean_numeric)
        if 'Quantity' in line_items_df.columns:
            line_items_df['Quantity'] = line_items_df['Quantity'].apply(clean_numeric)
        if 'Date' in line_items_df.columns:
            line_items_df['Date'] = pd.to_datetime(line_items_df['Date'], errors='coerce')
        
        line_items_df = apply_product_categories(line_items_df)
        
        line_items_df['Forecast Category'] = line_items_df.apply(
            lambda row: map_to_forecast_category(row.get('Product Category'), row.get('Product Sub-Category')),
            axis=1
        )
    
    # =======================================================================
    # CREATE SKU → CATEGORY LOOKUP FROM INVOICE LINE ITEMS
    # This will be used to categorize HubSpot deals by their SKU
    # =======================================================================
    sku_category_lookup = {}
    if not line_items_df.empty and 'Item' in line_items_df.columns and 'Product Category' in line_items_df.columns:
        # Build lookup: SKU → Product Category (use the most common category for each SKU)
        sku_categories = line_items_df.groupby('Item')['Product Category'].agg(lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Other')
        sku_category_lookup = sku_categories.to_dict()
    
    # Process Invoices (for pipeline lookup)
    pipeline_lookup = {}
    raw_pipeline_lookup = {}
    if not invoices_df.empty:
        if invoices_df.columns.duplicated().any():
            invoices_df = invoices_df.loc[:, ~invoices_df.columns.duplicated()]
        
        if 'Document Number' in invoices_df.columns:
            invoices_df['Document Number'] = invoices_df['Document Number'].astype(str).str.strip()
        
        pipeline_col = None
        for col in invoices_df.columns:
            if 'hubspot' in col.lower() and 'pipeline' in col.lower():
                pipeline_col = col
                break
        
        if pipeline_col is None and 'HubSpot Pipeline' in invoices_df.columns:
            pipeline_col = 'HubSpot Pipeline'
        
        if pipeline_col and 'Document Number' in invoices_df.columns:
            # Keep both raw pipeline and mapped pipeline for SO Manually Built handling
            invoices_df['Raw_Pipeline'] = invoices_df[pipeline_col].astype(str).str.strip()
            invoices_df['Forecast Pipeline'] = invoices_df[pipeline_col].apply(map_to_forecast_pipeline)
            
            # Create lookups for both
            pipeline_lookup = invoices_df.set_index('Document Number')['Forecast Pipeline'].to_dict()
            raw_pipeline_lookup = invoices_df.set_index('Document Number')['Raw_Pipeline'].to_dict()
    
    # Join pipeline to line items
    if not line_items_df.empty:
        if 'Document Number' in line_items_df.columns:
            line_items_df['Document Number'] = line_items_df['Document Number'].astype(str).str.strip()
            
            if pipeline_lookup:
                line_items_df['Forecast Pipeline'] = line_items_df['Document Number'].map(pipeline_lookup)
            else:
                line_items_df['Forecast Pipeline'] = None
                
            if raw_pipeline_lookup:
                line_items_df['Raw_Pipeline'] = line_items_df['Document Number'].map(raw_pipeline_lookup)
            else:
                line_items_df['Raw_Pipeline'] = None
            
            # Handle "SO Manually Built" based on Rep Master
            # Brad Sherman, Lance Mitton → Acquisition
            # Alex Gonzalez, Jake Lynch, Dave Borkowski → Retention
            acquisition_reps = ['Brad Sherman', 'Lance Mitton']
            retention_reps = ['Alex Gonzalez', 'Jake Lynch', 'Dave Borkowski']
            
            def assign_so_manually_built_pipeline(row):
                # If already mapped, keep it
                if pd.notna(row.get('Forecast Pipeline')) and row.get('Forecast Pipeline') != 'Unmapped':
                    return row['Forecast Pipeline']
                
                # Check if this is SO Manually Built
                raw_pipeline = str(row.get('Raw_Pipeline', '')).strip()
                if 'SO Manually Built' in raw_pipeline or 'Manually Built' in raw_pipeline:
                    rep = str(row.get('Rep Master', '')).strip()
                    
                    if rep in acquisition_reps:
                        return 'Acquisition'
                    elif rep in retention_reps:
                        return 'Retention'
                
                # Return original (could be None/NaN)
                return row.get('Forecast Pipeline')
            
            line_items_df['Forecast Pipeline'] = line_items_df.apply(assign_so_manually_built_pipeline, axis=1)
    
    # Process Sales Orders (header level - kept for backward compatibility)
    if not sales_orders_df.empty:
        if sales_orders_df.columns.duplicated().any():
            sales_orders_df = sales_orders_df.loc[:, ~sales_orders_df.columns.duplicated()]
        
        if 'Amount (Transaction Total)' in sales_orders_df.columns and 'Amount' not in sales_orders_df.columns:
            sales_orders_df = sales_orders_df.rename(columns={'Amount (Transaction Total)': 'Amount'})
        
        if 'Amount' in sales_orders_df.columns:
            sales_orders_df['Amount'] = sales_orders_df['Amount'].apply(clean_numeric)
        if 'Order Start Date' in sales_orders_df.columns:
            sales_orders_df['Order Start Date'] = pd.to_datetime(sales_orders_df['Order Start Date'], errors='coerce')
        
        # Parse date columns for pending orders filtering
        if 'Customer Promise Last Date to Ship' in sales_orders_df.columns:
            sales_orders_df['Customer Promise Last Date to Ship'] = pd.to_datetime(sales_orders_df['Customer Promise Last Date to Ship'], errors='coerce')
        if 'Projected Date' in sales_orders_df.columns:
            sales_orders_df['Projected Date'] = pd.to_datetime(sales_orders_df['Projected Date'], errors='coerce')
        if 'Pending Approval Date' in sales_orders_df.columns:
            sales_orders_df['Pending Approval Date'] = pd.to_datetime(sales_orders_df['Pending Approval Date'], errors='coerce')
        
        pipeline_col = None
        for col in sales_orders_df.columns:
            if 'hubspot' in col.lower() and 'pipeline' in col.lower():
                pipeline_col = col
                break
        
        if pipeline_col:
            sales_orders_df['Forecast Pipeline'] = sales_orders_df[pipeline_col].apply(map_to_forecast_pipeline)
        
        if 'Order Type' in sales_orders_df.columns:
            sales_orders_df['Forecast Category'] = sales_orders_df['Order Type'].apply(map_order_type_to_forecast_category)
    
    # =======================================================================
    # PROCESS SALES ORDER LINE ITEMS (for proper categorization)
    # Uses same Calyx || Product Type logic as Invoice Line Items
    # =======================================================================
    if not sales_order_line_items_df.empty:
        if sales_order_line_items_df.columns.duplicated().any():
            sales_order_line_items_df = sales_order_line_items_df.loc[:, ~sales_order_line_items_df.columns.duplicated()]
        
        # Clean numeric columns
        if 'Amount' in sales_order_line_items_df.columns:
            sales_order_line_items_df['Amount'] = sales_order_line_items_df['Amount'].apply(clean_numeric)
        if 'Quantity Ordered' in sales_order_line_items_df.columns:
            sales_order_line_items_df['Quantity'] = sales_order_line_items_df['Quantity Ordered'].apply(clean_numeric)
        
        # Parse dates
        if 'Date Created' in sales_order_line_items_df.columns:
            sales_order_line_items_df['Date Created'] = pd.to_datetime(sales_order_line_items_df['Date Created'], errors='coerce')
        if 'Pending Fulfillment Date' in sales_order_line_items_df.columns:
            sales_order_line_items_df['Pending Fulfillment Date'] = pd.to_datetime(sales_order_line_items_df['Pending Fulfillment Date'], errors='coerce')
        
        # Apply same Calyx-based categorization as Invoice Line Items
        sales_order_line_items_df = apply_product_categories(sales_order_line_items_df)
        
        # Map to forecast categories
        sales_order_line_items_df['Forecast Category'] = sales_order_line_items_df.apply(
            lambda row: map_to_forecast_category(row.get('Product Category'), row.get('Product Sub-Category')),
            axis=1
        )
        
        # Map HubSpot Pipeline
        if 'HubSpot Pipeline' in sales_order_line_items_df.columns:
            sales_order_line_items_df['Forecast Pipeline'] = sales_order_line_items_df['HubSpot Pipeline'].apply(map_to_forecast_pipeline)
        
        # =======================================================================
        # JOIN SALES ORDER LINE ITEMS WITH HEADER DATA FOR ACCURATE STATUS/DATES
        # Look up Updated Status (Column AG) and date columns from _NS_SalesOrders_Data
        # =======================================================================
        if not sales_orders_df.empty and 'Document Number' in sales_order_line_items_df.columns:
            # Ensure Document Number is string for joining
            sales_order_line_items_df['Document Number'] = sales_order_line_items_df['Document Number'].astype(str).str.strip()
            
            # Create lookup from sales_orders_df
            so_lookup_cols = ['Document Number']
            if 'Updated Status' in sales_orders_df.columns:
                so_lookup_cols.append('Updated Status')
            if 'Customer Promise Last Date to Ship' in sales_orders_df.columns:
                so_lookup_cols.append('Customer Promise Last Date to Ship')
            if 'Projected Date' in sales_orders_df.columns:
                so_lookup_cols.append('Projected Date')
            if 'Pending Approval Date' in sales_orders_df.columns:
                so_lookup_cols.append('Pending Approval Date')
            
            if len(so_lookup_cols) > 1:
                so_header_lookup = sales_orders_df[so_lookup_cols].copy()
                so_header_lookup['Document Number'] = so_header_lookup['Document Number'].astype(str).str.strip()
                so_header_lookup = so_header_lookup.drop_duplicates(subset=['Document Number'])
                
                # Join to line items
                sales_order_line_items_df = sales_order_line_items_df.merge(
                    so_header_lookup, 
                    on='Document Number', 
                    how='left',
                    suffixes=('', '_header')
                )
                
                # Create a computed Expected Date based on Updated Status
                def get_expected_date(row):
                    status = str(row.get('Updated Status', '')).lower() if pd.notna(row.get('Updated Status')) else ''
                    
                    if 'pending fulfillment' in status:
                        # PF: Use Customer Promise Last Date to Ship, then Projected Date
                        if pd.notna(row.get('Customer Promise Last Date to Ship')):
                            return row['Customer Promise Last Date to Ship']
                        elif pd.notna(row.get('Projected Date')):
                            return row['Projected Date']
                    elif 'pending approval' in status:
                        # PA: Use Pending Approval Date
                        if pd.notna(row.get('Pending Approval Date')):
                            return row['Pending Approval Date']
                    
                    # No date available
                    return pd.NaT
                
                sales_order_line_items_df['Expected Ship Date'] = sales_order_line_items_df.apply(get_expected_date, axis=1)
    
    # Process HubSpot Deals
    if not deals_df.empty:
        if deals_df.columns.duplicated().any():
            deals_df = deals_df.loc[:, ~deals_df.columns.duplicated()]
        
        if 'Amount' in deals_df.columns:
            deals_df['Amount'] = deals_df['Amount'].apply(clean_numeric)
        if 'Close Date' in deals_df.columns:
            deals_df['Close Date'] = pd.to_datetime(deals_df['Close Date'], errors='coerce')
        
        if 'Pipeline' in deals_df.columns:
            deals_df['Forecast Pipeline'] = deals_df['Pipeline'].apply(map_to_forecast_pipeline)
        
        if 'Deal Type' in deals_df.columns:
            deals_df['Forecast Category'] = deals_df['Deal Type'].apply(map_deal_type_to_forecast_category)
    
    # Process Deals Line Items for Close Rate Analysis
    if not deals_line_items_df.empty:
        if deals_line_items_df.columns.duplicated().any():
            deals_line_items_df = deals_line_items_df.loc[:, ~deals_line_items_df.columns.duplicated()]
        
        # =======================================================================
        # FILTER OUT STANDARD REORDER DEALS
        # If any of the "Date entered Standard Reorder..." columns have a value,
        # the deal was at some point a standard reorder and should be excluded
        # =======================================================================
        
        # Find which standard reorder columns are actually present in the dataframe
        present_reorder_cols = [col for col in deals_line_items_df.columns 
                                if 'Standard Reorder' in str(col)]
        
        if present_reorder_cols:
            # Create a flag: True if ANY of the standard reorder date columns have a value
            def has_standard_reorder_date(row):
                for col in present_reorder_cols:
                    val = row.get(col, None)
                    if pd.notna(val) and str(val).strip() != '':
                        return True
                return False
            
            deals_line_items_df['Is_Standard_Reorder'] = deals_line_items_df.apply(has_standard_reorder_date, axis=1)
            
            # Count how many we're filtering out (store for display later)
            reorder_line_items = deals_line_items_df['Is_Standard_Reorder'].sum()
            total_before = len(deals_line_items_df)
            
            # Count unique deals being filtered
            if 'Deal ID' in deals_line_items_df.columns:
                reorder_deals = deals_line_items_df[deals_line_items_df['Is_Standard_Reorder'] == True]['Deal ID'].nunique()
                total_deals_before = deals_line_items_df['Deal ID'].nunique()
            else:
                reorder_deals = reorder_line_items
                total_deals_before = total_before
            
            # Filter out standard reorder deals
            deals_line_items_df = deals_line_items_df[deals_line_items_df['Is_Standard_Reorder'] == False].copy()
            
            # Store the filtering stats as attributes on the dataframe
            deals_line_items_df.attrs['reorder_filtered_line_items'] = reorder_line_items
            deals_line_items_df.attrs['reorder_filtered_deals'] = reorder_deals
            deals_line_items_df.attrs['total_deals_before_filter'] = total_deals_before
        
        # =======================================================================
        # FILTER OUT DEALS BY DEAL OWNER LAST NAME (Gonzalez)
        # =======================================================================
        if 'Deal Owner Last Name' in deals_line_items_df.columns:
            # Count deals being filtered
            gonzalez_mask = deals_line_items_df['Deal Owner Last Name'].str.strip().str.lower() == 'gonzalez'
            gonzalez_line_items = gonzalez_mask.sum()
            
            if 'Deal ID' in deals_line_items_df.columns:
                gonzalez_deals = deals_line_items_df[gonzalez_mask]['Deal ID'].nunique()
            else:
                gonzalez_deals = gonzalez_line_items
            
            # Filter out Gonzalez deals
            deals_line_items_df = deals_line_items_df[~gonzalez_mask].copy()
            
            # Store the filtering stats
            deals_line_items_df.attrs['gonzalez_filtered_deals'] = gonzalez_deals
        
        # Clean numeric columns - use Effective Unit Price × Quantity for Amount
        if 'Effective unit price' in deals_line_items_df.columns:
            deals_line_items_df['Effective unit price'] = deals_line_items_df['Effective unit price'].apply(clean_numeric)
        if 'Quantity' in deals_line_items_df.columns:
            deals_line_items_df['Quantity'] = deals_line_items_df['Quantity'].apply(clean_numeric)
        
        # Calculate Amount as Effective Unit Price × Quantity
        if 'Effective unit price' in deals_line_items_df.columns and 'Quantity' in deals_line_items_df.columns:
            deals_line_items_df['Amount'] = deals_line_items_df['Effective unit price'] * deals_line_items_df['Quantity']
        elif 'Amount' in deals_line_items_df.columns:
            deals_line_items_df['Amount'] = deals_line_items_df['Amount'].apply(clean_numeric)
        
        # Parse dates
        if 'Create Date' in deals_line_items_df.columns:
            deals_line_items_df['Create Date'] = pd.to_datetime(deals_line_items_df['Create Date'], errors='coerce')
        if 'Close Date' in deals_line_items_df.columns:
            deals_line_items_df['Close Date'] = pd.to_datetime(deals_line_items_df['Close Date'], errors='coerce')
        
        # Apply SKU-based categorization using lookup from Invoice Line Items
        # WITH FALLBACK to Deal Type when SKU is null or maps to 'Other'
        if 'SKU' in deals_line_items_df.columns and sku_category_lookup:
            deals_line_items_df['SKU_Category'] = deals_line_items_df['SKU'].map(sku_category_lookup)
        else:
            deals_line_items_df['SKU_Category'] = None
            # Fallback: Map SKU column to Item for old categorization
            if 'SKU' in deals_line_items_df.columns:
                deals_line_items_df['Item'] = deals_line_items_df['SKU']
            if 'SKU Description' in deals_line_items_df.columns:
                deals_line_items_df['Item Description'] = deals_line_items_df['SKU Description']
            deals_line_items_df = apply_product_categories(deals_line_items_df)
        
        # Get Deal Type based category as fallback (Column G = "Deal Type")
        if 'Deal Type' in deals_line_items_df.columns:
            deals_line_items_df['DealType_Category'] = deals_line_items_df['Deal Type'].apply(map_deal_type_to_forecast_category)
        else:
            deals_line_items_df['DealType_Category'] = 'Other'
        
        # Use SKU category if available and not 'Other', otherwise use Deal Type category
        def get_best_category_dli(row):
            sku_cat = row.get('SKU_Category')
            deal_cat = row.get('DealType_Category', 'Other')
            
            # If SKU lookup succeeded and isn't 'Other', use it
            if pd.notna(sku_cat) and sku_cat != 'Other':
                return map_to_forecast_category(sku_cat, None)
            # Otherwise fall back to Deal Type
            return deal_cat
        
        deals_line_items_df['Forecast Category'] = deals_line_items_df.apply(get_best_category_dli, axis=1)
        
        # Create unified closed won flag
        # Closed Won if: Is Closed Won = TRUE, or Deal Stage in ['Sales Order Created in NS', 'NCR']
        def is_closed_won(row):
            # Check Is Closed Won column
            is_won = str(row.get('Is Closed Won', '')).strip().upper()
            if is_won in ['TRUE', 'YES', '1']:
                return True
            # Check Deal Stage for Sales Order Created in NS or NCR
            deal_stage = str(row.get('Deal Stage', '')).strip()
            if deal_stage in ['Sales Order Created in NS', 'NCR']:
                return True
            return False
        
        deals_line_items_df['Is_Won'] = deals_line_items_df.apply(is_closed_won, axis=1)
        
        # Create closed lost flag
        def is_closed_lost(row):
            is_lost = str(row.get('Is closed lost', '')).strip().upper()
            return is_lost in ['TRUE', 'YES', '1']
        
        deals_line_items_df['Is_Lost'] = deals_line_items_df.apply(is_closed_lost, axis=1)
        
        # Calculate days to close
        if 'Create Date' in deals_line_items_df.columns and 'Close Date' in deals_line_items_df.columns:
            deals_line_items_df['Days_To_Close'] = (
                deals_line_items_df['Close Date'] - deals_line_items_df['Create Date']
            ).dt.days
    
    # =======================================================================
    # PROCESS PIPELINE DEALS (Deals Line Item) FOR PIPELINE SECTION
    # No filtering - show all active pipeline deals
    # =======================================================================
    if not pipeline_deals_df.empty:
        if pipeline_deals_df.columns.duplicated().any():
            pipeline_deals_df = pipeline_deals_df.loc[:, ~pipeline_deals_df.columns.duplicated()]
        
        # Clean numeric columns - use Effective Unit Price × Quantity for Amount
        if 'Effective unit price' in pipeline_deals_df.columns:
            pipeline_deals_df['Effective unit price'] = pipeline_deals_df['Effective unit price'].apply(clean_numeric)
        if 'Quantity' in pipeline_deals_df.columns:
            pipeline_deals_df['Quantity'] = pipeline_deals_df['Quantity'].apply(clean_numeric)
        
        # Calculate Amount as Effective Unit Price × Quantity
        if 'Effective unit price' in pipeline_deals_df.columns and 'Quantity' in pipeline_deals_df.columns:
            pipeline_deals_df['Amount'] = pipeline_deals_df['Effective unit price'] * pipeline_deals_df['Quantity']
        elif 'Amount' in pipeline_deals_df.columns:
            pipeline_deals_df['Amount'] = pipeline_deals_df['Amount'].apply(clean_numeric)
        
        # Parse dates
        if 'Close Date' in pipeline_deals_df.columns:
            pipeline_deals_df['Close Date'] = pd.to_datetime(pipeline_deals_df['Close Date'], errors='coerce')
        if 'Create Date' in pipeline_deals_df.columns:
            pipeline_deals_df['Create Date'] = pd.to_datetime(pipeline_deals_df['Create Date'], errors='coerce')
        # Parse Pending Approval Date (Column V) - this is the date to use for filtering deals
        if 'Pending Approval Date' in pipeline_deals_df.columns:
            pipeline_deals_df['Pending Approval Date'] = pd.to_datetime(pipeline_deals_df['Pending Approval Date'], errors='coerce')
        
        # Map Pipeline to Forecast Pipeline
        if 'Pipeline' in pipeline_deals_df.columns:
            pipeline_deals_df['Forecast Pipeline'] = pipeline_deals_df['Pipeline'].apply(map_to_forecast_pipeline)
        
        # Apply SKU-based categorization using lookup from Invoice Line Items
        # WITH FALLBACK to Deal Type when SKU is null or maps to 'Other'
        if 'SKU' in pipeline_deals_df.columns and sku_category_lookup:
            pipeline_deals_df['SKU_Category'] = pipeline_deals_df['SKU'].map(sku_category_lookup)
        else:
            pipeline_deals_df['SKU_Category'] = None
        
        # Get Deal Type based category as fallback (Column G = "Deal Type")
        if 'Deal Type' in pipeline_deals_df.columns:
            pipeline_deals_df['DealType_Category'] = pipeline_deals_df['Deal Type'].apply(map_deal_type_to_forecast_category)
        else:
            pipeline_deals_df['DealType_Category'] = 'Other'
        
        # Use SKU category if available and not 'Other', otherwise use Deal Type category
        def get_best_category(row):
            sku_cat = row.get('SKU_Category')
            deal_cat = row.get('DealType_Category', 'Other')
            
            # If SKU lookup succeeded and isn't 'Other', use it
            if pd.notna(sku_cat) and sku_cat != 'Other':
                return map_to_forecast_category(sku_cat, None)
            # Otherwise fall back to Deal Type
            return deal_cat
        
        pipeline_deals_df['Forecast Category'] = pipeline_deals_df.apply(get_best_category, axis=1)
    
    return {
        'forecast': forecast_df,
        'line_items': line_items_df,
        'invoices': invoices_df,
        'sales_orders': sales_orders_df,
        'sales_order_line_items': sales_order_line_items_df,
        'deals': deals_df,
        'deals_line_items': deals_line_items_df,
        'pipeline_deals': pipeline_deals_df
    }


# ===================================================================================
# ANNUAL GOAL TRACKER - CALCULATION FUNCTIONS
# ===================================================================================

def calculate_ytd_actuals(line_items_df, year=2026):
    """Calculate YTD actuals by Pipeline and Category, including Total rows"""
    if line_items_df.empty:
        return pd.DataFrame()
    
    df = line_items_df.copy()
    if 'Date' in df.columns:
        df = df[df['Date'].dt.year == year]
    
    if df.empty:
        return pd.DataFrame()
    
    # Fill missing pipeline with 'Unmapped' so we don't lose revenue
    if 'Forecast Pipeline' in df.columns:
        df['Forecast Pipeline'] = df['Forecast Pipeline'].fillna('Unmapped')
    else:
        df['Forecast Pipeline'] = 'Unmapped'
    
    # Fill missing category with 'Other'
    if 'Forecast Category' in df.columns:
        df['Forecast Category'] = df['Forecast Category'].fillna('Other')
    else:
        df['Forecast Category'] = 'Other'
    
    # Base grouping: Pipeline x Category
    grouped = df.groupby(['Forecast Pipeline', 'Forecast Category']).agg({
        'Amount': 'sum'
    }).reset_index()
    grouped.columns = ['Pipeline', 'Category', 'Actual']
    
    # Create Category='Total' rows for each Pipeline
    pipeline_totals = df.groupby('Forecast Pipeline')['Amount'].sum().reset_index()
    pipeline_totals.columns = ['Pipeline', 'Actual']
    pipeline_totals['Category'] = 'Total'
    
    # Create Pipeline='Total' rows for each Category
    category_totals = df.groupby('Forecast Category')['Amount'].sum().reset_index()
    category_totals.columns = ['Category', 'Actual']
    category_totals['Pipeline'] = 'Total'
    
    # Create grand total row
    grand_total = pd.DataFrame([{
        'Pipeline': 'Total',
        'Category': 'Total',
        'Actual': df['Amount'].sum()
    }])
    
    # Combine all
    result = pd.concat([grouped, pipeline_totals, category_totals, grand_total], ignore_index=True)
    
    return result


def calculate_ytd_actuals_total(line_items_df, year=2026):
    """Calculate total YTD actuals (ignoring pipeline, just by category)"""
    if line_items_df.empty:
        return pd.DataFrame()
    
    df = line_items_df.copy()
    if 'Date' in df.columns:
        df = df[df['Date'].dt.year == year]
    
    if df.empty:
        return pd.DataFrame()
    
    # Fill missing category with 'Other'
    if 'Forecast Category' in df.columns:
        df['Forecast Category'] = df['Forecast Category'].fillna('Other')
    else:
        df['Forecast Category'] = 'Other'
    
    grouped = df.groupby('Forecast Category').agg({
        'Amount': 'sum'
    }).reset_index()
    
    grouped.columns = ['Category', 'Actual']
    
    # Add a 'Total' row
    total_actual = grouped['Actual'].sum()
    total_row = pd.DataFrame([{'Category': 'Total', 'Actual': total_actual}])
    grouped = pd.concat([grouped, total_row], ignore_index=True)
    
    return grouped


def calculate_monthly_actuals(line_items_df, year=2026):
    """Calculate monthly actuals by Pipeline and Category, including Total rows"""
    if line_items_df.empty:
        return pd.DataFrame()
    
    df = line_items_df.copy()
    if 'Date' in df.columns:
        df = df[df['Date'].dt.year == year]
        df['Month'] = df['Date'].dt.month
        df['Month_Name'] = df['Date'].dt.strftime('%B')
    
    if df.empty:
        return pd.DataFrame()
    
    # Fill missing pipeline with 'Unmapped'
    if 'Forecast Pipeline' in df.columns:
        df['Forecast Pipeline'] = df['Forecast Pipeline'].fillna('Unmapped')
    else:
        df['Forecast Pipeline'] = 'Unmapped'
    
    # Fill missing category with 'Other'
    if 'Forecast Category' in df.columns:
        df['Forecast Category'] = df['Forecast Category'].fillna('Other')
    else:
        df['Forecast Category'] = 'Other'
    
    # Base grouping
    grouped = df.groupby(['Forecast Pipeline', 'Forecast Category', 'Month', 'Month_Name']).agg({
        'Amount': 'sum'
    }).reset_index()
    grouped.columns = ['Pipeline', 'Category', 'Month_Num', 'Month', 'Actual']
    
    # Pipeline totals (Category='Total')
    pipeline_monthly = df.groupby(['Forecast Pipeline', 'Month', 'Month_Name'])['Amount'].sum().reset_index()
    pipeline_monthly.columns = ['Pipeline', 'Month_Num', 'Month', 'Actual']
    pipeline_monthly['Category'] = 'Total'
    
    # Category totals (Pipeline='Total')
    category_monthly = df.groupby(['Forecast Category', 'Month', 'Month_Name'])['Amount'].sum().reset_index()
    category_monthly.columns = ['Category', 'Month_Num', 'Month', 'Actual']
    category_monthly['Pipeline'] = 'Total'
    
    # Grand totals by month
    grand_monthly = df.groupby(['Month', 'Month_Name'])['Amount'].sum().reset_index()
    grand_monthly.columns = ['Month_Num', 'Month', 'Actual']
    grand_monthly['Pipeline'] = 'Total'
    grand_monthly['Category'] = 'Total'
    
    # Combine all
    result = pd.concat([grouped, pipeline_monthly, category_monthly, grand_monthly], ignore_index=True)
    
    return result


def get_ytd_plan(forecast_df, through_month):
    """Calculate YTD plan from forecast"""
    if forecast_df.empty:
        return pd.DataFrame()
    
    months_to_sum = MONTH_NAMES[:through_month]
    
    df = forecast_df.copy()
    df['YTD_Plan'] = df[months_to_sum].sum(axis=1)
    
    return df[['Pipeline', 'Category', 'YTD_Plan', 'Annual_Total']]


def get_period_plan(forecast_df, period_type, month=None, quarter=None):
    """
    Calculate plan for a specific time period (Month or Quarter).
    
    Args:
        forecast_df: Forecast dataframe with monthly columns
        period_type: 'Month' or 'Quarter'
        month: Month number (1-12) for Month period type
        quarter: Quarter number (1-4) for Quarter period type
    
    Returns:
        DataFrame with Pipeline, Category, and Period_Plan columns
    """
    if forecast_df.empty:
        return pd.DataFrame()
    
    df = forecast_df.copy()
    
    if period_type == 'Month' and month:
        # Get plan for a single month
        month_name = MONTH_NAMES[month - 1]  # 0-indexed
        if month_name in df.columns:
            df['Period_Plan'] = df[month_name]
        else:
            df['Period_Plan'] = 0
    elif period_type == 'Quarter' and quarter:
        # Get plan for a quarter (sum of 3 months)
        quarter_months = {
            1: ['January', 'February', 'March'],
            2: ['April', 'May', 'June'],
            3: ['July', 'August', 'September'],
            4: ['October', 'November', 'December']
        }
        months_to_sum = quarter_months.get(quarter, [])
        available_months = [m for m in months_to_sum if m in df.columns]
        if available_months:
            df['Period_Plan'] = df[available_months].sum(axis=1)
        else:
            df['Period_Plan'] = 0
    else:
        df['Period_Plan'] = 0
    
    return df[['Pipeline', 'Category', 'Period_Plan', 'Annual_Total']]


def calculate_variance(actuals_df, plan_df):
    """Calculate variance between actuals and plan"""
    if actuals_df.empty and plan_df.empty:
        return pd.DataFrame()
    
    merged = plan_df.merge(actuals_df, on=['Pipeline', 'Category'], how='left')
    
    merged['Actual'] = merged['Actual'].fillna(0)
    merged['Variance'] = merged['Actual'] - merged['YTD_Plan']
    merged['Variance_Pct'] = np.where(
        merged['YTD_Plan'] > 0,
        (merged['Actual'] / merged['YTD_Plan'] - 1) * 100,
        0
    )
    merged['Attainment_Pct'] = np.where(
        merged['YTD_Plan'] > 0,
        (merged['Actual'] / merged['YTD_Plan']) * 100,
        0
    )
    
    return merged


# ===================================================================================
# CLOSE RATE ANALYSIS - CALCULATION FUNCTIONS
# ===================================================================================

def get_deals_for_export(deals_line_items_df, filter_type=None, filter_value=None):
    """
    Get deals data formatted for export/download.
    
    Args:
        deals_line_items_df: The deals line items dataframe
        filter_type: 'pipeline', 'category', 'close_status', or None for all
        filter_value: The value to filter by (e.g., 'Retention', 'Labels', 'Commit')
    
    Returns:
        DataFrame with unique deals ready for export
    """
    if deals_line_items_df.empty:
        return pd.DataFrame()
    
    df = deals_line_items_df.copy()
    
    # Get unique deals (deduplicate by Deal ID)
    deal_id_col = 'Deal ID' if 'Deal ID' in df.columns else None
    
    # Columns to include in export
    export_cols = [
        'Deal ID', 'Deal Name', 'Company Name', 'Primary Associated Company',
        'Deal Owner First Name', 'Deal Owner Last Name', 'Pipeline', 
        'Deal Stage', 'Close Status', 'Deal Type', 'Amount',
        'Create Date', 'Close Date', 'Days_To_Close',
        'Is_Won', 'Is_Lost', 'Forecast Category', 'Product Category'
    ]
    
    # Build aggregation dict dynamically based on available columns
    agg_dict = {}
    for col in export_cols:
        if col in df.columns and col != deal_id_col:
            agg_dict[col] = 'first'
    
    if deal_id_col:
        unique_deals = df.groupby(deal_id_col).agg(agg_dict).reset_index()
    else:
        deal_name_col = 'Deal Name' if 'Deal Name' in df.columns else None
        if deal_name_col and 'Deal Name' in agg_dict:
            del agg_dict['Deal Name']
        if deal_name_col:
            unique_deals = df.groupby(deal_name_col).agg(agg_dict).reset_index()
        else:
            unique_deals = df.copy()
    
    # Filter to closed deals only
    unique_deals = unique_deals[(unique_deals['Is_Won'] == True) | (unique_deals['Is_Lost'] == True)]
    
    # Apply filter if specified
    if filter_type and filter_value:
        if filter_type == 'pipeline' and 'Pipeline' in unique_deals.columns:
            unique_deals = unique_deals[unique_deals['Pipeline'] == filter_value]
        elif filter_type == 'category' and 'Forecast Category' in unique_deals.columns:
            unique_deals = unique_deals[unique_deals['Forecast Category'] == filter_value]
        elif filter_type == 'close_status' and 'Close Status' in unique_deals.columns:
            unique_deals = unique_deals[unique_deals['Close Status'] == filter_value]
    
    # Clean up for export - keep only available columns
    available_cols = [c for c in export_cols if c in unique_deals.columns]
    export_df = unique_deals[available_cols].copy()
    
    # Add a win/loss status column for clarity
    if 'Is_Won' in export_df.columns:
        export_df['Status'] = export_df['Is_Won'].apply(lambda x: 'Won' if x else 'Lost')
    
    return export_df


def calculate_close_rate_metrics(deals_line_items_df):
    """
    Calculate close rate metrics from deals line items.
    Returns dict with overall stats and breakdowns.
    
    Key insight: Amount is repeated for each line item in a deal, so we need to 
    deduplicate by Deal ID when calculating deal-level amounts.
    """
    if deals_line_items_df.empty:
        return None
    
    df = deals_line_items_df.copy()
    
    # Get unique deals for accurate deal-level metrics
    # Amount is the same for all line items in a deal, so we take the first occurrence
    deal_id_col = 'Deal ID' if 'Deal ID' in df.columns else None
    
    # Build aggregation dict dynamically based on available columns
    agg_dict = {}
    potential_cols = [
        'Amount', 'Is_Won', 'Is_Lost', 'Close Status', 'Deal Stage', 'Pipeline',
        'Deal Type', 'Create Date', 'Close Date', 'Days_To_Close', 'Deal Name',
        'Deal Owner First Name', 'Deal Owner Last Name', 'Company Name', 'Primary Associated Company'
    ]
    for col in potential_cols:
        if col in df.columns:
            agg_dict[col] = 'first'
    
    if deal_id_col:
        # Deduplicate to get unique deals with their amounts
        unique_deals = df.groupby(deal_id_col).agg(agg_dict).reset_index()
    else:
        # Fallback if no Deal ID - use Deal Name as identifier
        deal_name_col = 'Deal Name' if 'Deal Name' in df.columns else None
        if deal_name_col:
            # Remove Deal Name from agg dict if it's the groupby column
            if 'Deal Name' in agg_dict:
                del agg_dict['Deal Name']
            unique_deals = df.groupby(deal_name_col).agg(agg_dict).reset_index()
        else:
            unique_deals = df.copy()
    
    # Filter to only closed deals (won or lost)
    closed_deals = unique_deals[(unique_deals['Is_Won'] == True) | (unique_deals['Is_Lost'] == True)]
    
    # Overall close rate metrics
    total_closed = len(closed_deals)
    total_won = len(closed_deals[closed_deals['Is_Won'] == True])
    total_lost = len(closed_deals[closed_deals['Is_Lost'] == True])
    
    overall_close_rate = (total_won / total_closed * 100) if total_closed > 0 else 0
    
    total_won_amount = closed_deals[closed_deals['Is_Won'] == True]['Amount'].sum()
    total_lost_amount = closed_deals[closed_deals['Is_Lost'] == True]['Amount'].sum()
    total_closed_amount = total_won_amount + total_lost_amount
    
    amount_close_rate = (total_won_amount / total_closed_amount * 100) if total_closed_amount > 0 else 0
    
    # Close rate by Close Status (probability scores)
    close_status_rates = {}
    if 'Close Status' in closed_deals.columns:
        for status in ['Expect', 'Commit', 'Best Case', 'Opportunity']:
            status_deals = closed_deals[closed_deals['Close Status'] == status]
            status_total = len(status_deals)
            status_won = len(status_deals[status_deals['Is_Won'] == True])
            status_rate = (status_won / status_total * 100) if status_total > 0 else 0
            
            status_amount_total = status_deals['Amount'].sum()
            status_amount_won = status_deals[status_deals['Is_Won'] == True]['Amount'].sum()
            status_amount_rate = (status_amount_won / status_amount_total * 100) if status_amount_total > 0 else 0
            
            close_status_rates[status] = {
                'total_deals': status_total,
                'won_deals': status_won,
                'lost_deals': status_total - status_won,
                'close_rate_count': status_rate,
                'total_amount': status_amount_total,
                'won_amount': status_amount_won,
                'close_rate_amount': status_amount_rate
            }
    
    # Days to close statistics
    won_deals = closed_deals[closed_deals['Is_Won'] == True]
    days_to_close_stats = {}
    if 'Days_To_Close' in won_deals.columns:
        valid_days = won_deals['Days_To_Close'].dropna()
        if len(valid_days) > 0:
            days_to_close_stats = {
                'mean': valid_days.mean(),
                'median': valid_days.median(),
                'min': valid_days.min(),
                'max': valid_days.max(),
                'std': valid_days.std() if len(valid_days) > 1 else 0,
                'count': len(valid_days)
            }
    
    return {
        'unique_deals': unique_deals,
        'closed_deals': closed_deals,
        'overall': {
            'total_closed': total_closed,
            'total_won': total_won,
            'total_lost': total_lost,
            'close_rate_count': overall_close_rate,
            'total_closed_amount': total_closed_amount,
            'total_won_amount': total_won_amount,
            'total_lost_amount': total_lost_amount,
            'close_rate_amount': amount_close_rate
        },
        'by_close_status': close_status_rates,
        'days_to_close': days_to_close_stats
    }


def calculate_close_rate_by_category(deals_line_items_df):
    """
    Calculate close rate by product category using SKU categorization.
    This uses line-item level data since categories are SKU-specific.
    """
    if deals_line_items_df.empty or 'Product Category' not in deals_line_items_df.columns:
        return pd.DataFrame()
    
    df = deals_line_items_df.copy()
    
    # Filter to closed deals only
    df = df[(df['Is_Won'] == True) | (df['Is_Lost'] == True)]
    
    if df.empty:
        return pd.DataFrame()
    
    # Group by category and calculate metrics
    category_metrics = []
    
    for category in df['Product Category'].dropna().unique():
        cat_df = df[df['Product Category'] == category]
        
        total_qty = cat_df['Quantity'].sum() if 'Quantity' in cat_df.columns else len(cat_df)
        won_qty = cat_df[cat_df['Is_Won'] == True]['Quantity'].sum() if 'Quantity' in cat_df.columns else len(cat_df[cat_df['Is_Won'] == True])
        
        # Also track by unique deals in this category
        if 'Deal ID' in cat_df.columns:
            unique_deals = cat_df.groupby('Deal ID')['Is_Won'].first()
            deal_count = len(unique_deals)
            deal_won_count = unique_deals.sum()
        else:
            deal_count = len(cat_df.drop_duplicates(subset=['Deal Name'])) if 'Deal Name' in cat_df.columns else len(cat_df)
            deal_won_count = len(cat_df[cat_df['Is_Won'] == True].drop_duplicates(subset=['Deal Name'])) if 'Deal Name' in cat_df.columns else len(cat_df[cat_df['Is_Won'] == True])
        
        category_metrics.append({
            'Category': category,
            'Total Deals': deal_count,
            'Won Deals': deal_won_count,
            'Lost Deals': deal_count - deal_won_count,
            'Close Rate': (deal_won_count / deal_count * 100) if deal_count > 0 else 0,
            'Total Qty': total_qty,
            'Won Qty': won_qty
        })
    
    return pd.DataFrame(category_metrics).sort_values('Total Deals', ascending=False)


def calculate_close_rate_by_pipeline(deals_line_items_df):
    """
    Calculate close rate by pipeline.
    """
    if deals_line_items_df.empty or 'Pipeline' not in deals_line_items_df.columns:
        return pd.DataFrame()
    
    df = deals_line_items_df.copy()
    
    # Get unique deals
    deal_id_col = 'Deal ID' if 'Deal ID' in df.columns else 'Deal Name'
    
    if deal_id_col not in df.columns:
        return pd.DataFrame()
    
    unique_deals = df.groupby(deal_id_col).agg({
        'Amount': 'first',
        'Is_Won': 'first',
        'Is_Lost': 'first',
        'Pipeline': 'first'
    }).reset_index()
    
    # Filter to closed deals
    closed_deals = unique_deals[(unique_deals['Is_Won'] == True) | (unique_deals['Is_Lost'] == True)]
    
    if closed_deals.empty:
        return pd.DataFrame()
    
    # Group by pipeline
    pipeline_metrics = []
    
    for pipeline in closed_deals['Pipeline'].dropna().unique():
        pipe_df = closed_deals[closed_deals['Pipeline'] == pipeline]
        
        total_deals = len(pipe_df)
        won_deals = len(pipe_df[pipe_df['Is_Won'] == True])
        won_amount = pipe_df[pipe_df['Is_Won'] == True]['Amount'].sum()
        total_amount = pipe_df['Amount'].sum()
        
        pipeline_metrics.append({
            'Pipeline': pipeline,
            'Total Deals': total_deals,
            'Won Deals': won_deals,
            'Lost Deals': total_deals - won_deals,
            'Close Rate (Count)': (won_deals / total_deals * 100) if total_deals > 0 else 0,
            'Won Amount': won_amount,
            'Total Amount': total_amount,
            'Close Rate (Amount)': (won_amount / total_amount * 100) if total_amount > 0 else 0
        })
    
    return pd.DataFrame(pipeline_metrics).sort_values('Total Deals', ascending=False)


def calculate_days_to_close_by_amount_bucket(deals_line_items_df):
    """
    Calculate average days to close by deal amount buckets.
    """
    if deals_line_items_df.empty:
        return pd.DataFrame()
    
    df = deals_line_items_df.copy()
    
    # Get unique deals
    deal_id_col = 'Deal ID' if 'Deal ID' in df.columns else 'Deal Name'
    
    if deal_id_col not in df.columns:
        return pd.DataFrame()
    
    unique_deals = df.groupby(deal_id_col).agg({
        'Amount': 'first',
        'Is_Won': 'first',
        'Days_To_Close': 'first'
    }).reset_index()
    
    # Filter to won deals with valid days
    won_deals = unique_deals[
        (unique_deals['Is_Won'] == True) & 
        (unique_deals['Days_To_Close'].notna()) &
        (unique_deals['Days_To_Close'] >= 0)
    ]
    
    if won_deals.empty:
        return pd.DataFrame()
    
    # Create amount buckets
    def get_amount_bucket(amount):
        if amount < 5000:
            return '$0 - $5K'
        elif amount < 15000:
            return '$5K - $15K'
        elif amount < 50000:
            return '$15K - $50K'
        elif amount < 100000:
            return '$50K - $100K'
        else:
            return '$100K+'
    
    won_deals['Amount Bucket'] = won_deals['Amount'].apply(get_amount_bucket)
    
    # Order buckets correctly
    bucket_order = ['$0 - $5K', '$5K - $15K', '$15K - $50K', '$50K - $100K', '$100K+']
    
    bucket_metrics = []
    for bucket in bucket_order:
        bucket_df = won_deals[won_deals['Amount Bucket'] == bucket]
        if len(bucket_df) > 0:
            bucket_metrics.append({
                'Amount Bucket': bucket,
                'Deal Count': len(bucket_df),
                'Avg Days to Close': bucket_df['Days_To_Close'].mean(),
                'Median Days': bucket_df['Days_To_Close'].median(),
                'Min Days': bucket_df['Days_To_Close'].min(),
                'Max Days': bucket_df['Days_To_Close'].max()
            })
    
    return pd.DataFrame(bucket_metrics)


# ===================================================================================
# REVENUE PLANNING & GAP ANALYSIS - CALCULATION FUNCTIONS
# ===================================================================================

def calculate_avg_deal_size_by_pipeline(deals_line_items_df):
    """
    Calculate average deal size for WON deals by pipeline.
    Uses unique deals to avoid double-counting from line items.
    """
    if deals_line_items_df.empty:
        return {}
    
    df = deals_line_items_df.copy()
    
    # Get unique deals
    deal_id_col = 'Deal ID' if 'Deal ID' in df.columns else 'Deal Name'
    if deal_id_col not in df.columns:
        return {}
    
    # Only won deals
    won_deals = df[df['Is_Won'] == True].copy()
    if won_deals.empty:
        return {}
    
    unique_won = won_deals.groupby(deal_id_col).agg({
        'Amount': 'first',
        'Pipeline': 'first'
    }).reset_index()
    
    # Calculate by pipeline
    avg_by_pipeline = {}
    for pipeline in unique_won['Pipeline'].dropna().unique():
        pipe_deals = unique_won[unique_won['Pipeline'] == pipeline]
        if len(pipe_deals) > 0:
            avg_by_pipeline[pipeline] = {
                'avg_deal_size': pipe_deals['Amount'].mean(),
                'median_deal_size': pipe_deals['Amount'].median(),
                'total_deals': len(pipe_deals),
                'total_revenue': pipe_deals['Amount'].sum()
            }
    
    # Overall average
    avg_by_pipeline['Overall'] = {
        'avg_deal_size': unique_won['Amount'].mean(),
        'median_deal_size': unique_won['Amount'].median(),
        'total_deals': len(unique_won),
        'total_revenue': unique_won['Amount'].sum()
    }
    
    return avg_by_pipeline


def calculate_pipeline_expected_revenue(open_deals_df, close_rates_by_status, close_rates_by_pipeline):
    """
    Calculate expected revenue from open pipeline deals.
    
    Uses historical close rates to weight each deal:
    - If Close Status available: use status-specific rate
    - Fallback to pipeline-specific rate
    - Fallback to overall rate
    
    Returns dict with expected revenue calculations.
    """
    if open_deals_df.empty:
        return {
            'total_pipeline_value': 0,
            'expected_revenue': 0,
            'by_status': {},
            'by_pipeline': {},
            'deal_count': 0
        }
    
    df = open_deals_df.copy()
    
    # Get overall fallback rate
    overall_rate = 50.0  # Default assumption
    if 'Overall' in close_rates_by_pipeline:
        # Use weighted average across pipelines
        total_deals = sum(p.get('total_deals', 0) for p in close_rates_by_pipeline.values() if isinstance(p, dict))
        if total_deals > 0:
            weighted_sum = sum(
                p.get('close_rate', 50) * p.get('total_deals', 0) 
                for p in close_rates_by_pipeline.values() 
                if isinstance(p, dict)
            )
            overall_rate = weighted_sum / total_deals
    
    # Calculate expected value for each deal
    def get_expected_value(row):
        amount = row.get('Amount', 0) or 0
        close_status = row.get('Close Status', '')
        pipeline = row.get('Pipeline', '')
        
        # Priority 1: Close Status specific rate
        if close_status and close_status in close_rates_by_status:
            rate = close_rates_by_status[close_status].get('close_rate_count', overall_rate)
            return amount * (rate / 100), rate, 'status'
        
        # Priority 2: Pipeline specific rate
        if pipeline and pipeline in close_rates_by_pipeline:
            rate = close_rates_by_pipeline[pipeline].get('close_rate', overall_rate)
            return amount * (rate / 100), rate, 'pipeline'
        
        # Fallback to overall
        return amount * (overall_rate / 100), overall_rate, 'overall'
    
    df['Expected_Value'], df['Applied_Rate'], df['Rate_Source'] = zip(*df.apply(get_expected_value, axis=1))
    
    total_pipeline_value = df['Amount'].sum()
    expected_revenue = df['Expected_Value'].sum()
    
    # Breakdown by Close Status
    by_status = {}
    if 'Close Status' in df.columns:
        for status in df['Close Status'].dropna().unique():
            status_df = df[df['Close Status'] == status]
            by_status[status] = {
                'deal_count': len(status_df),
                'pipeline_value': status_df['Amount'].sum(),
                'expected_revenue': status_df['Expected_Value'].sum(),
                'applied_rate': status_df['Applied_Rate'].mean()
            }
    
    # Breakdown by Pipeline
    by_pipeline = {}
    if 'Pipeline' in df.columns:
        for pipeline in df['Pipeline'].dropna().unique():
            pipe_df = df[df['Pipeline'] == pipeline]
            by_pipeline[pipeline] = {
                'deal_count': len(pipe_df),
                'pipeline_value': pipe_df['Amount'].sum(),
                'expected_revenue': pipe_df['Expected_Value'].sum(),
                'applied_rate': pipe_df['Applied_Rate'].mean()
            }
    
    return {
        'total_pipeline_value': total_pipeline_value,
        'expected_revenue': expected_revenue,
        'by_status': by_status,
        'by_pipeline': by_pipeline,
        'deal_count': len(df),
        'details': df
    }


def calculate_revenue_gap_analysis(revenue_target, current_actuals, expected_pipeline, 
                                    avg_deal_size, close_rate):
    """
    Calculate gap to revenue target and deals/opportunities needed.
    
    Formulas:
    - Revenue Gap = Target - (Actuals + Expected Pipeline)
    - Deals Needed = Gap / Avg Deal Size
    - Opportunities Needed = Gap / (Close Rate × Avg Deal Size)
    """
    # What we expect to have
    projected_total = current_actuals + expected_pipeline
    
    # Gap to target
    revenue_gap = revenue_target - projected_total
    
    # Deals needed to close gap (assuming we win them all)
    deals_needed = revenue_gap / avg_deal_size if avg_deal_size > 0 else 0
    
    # Opportunities needed (accounting for close rate)
    close_rate_decimal = close_rate / 100 if close_rate > 1 else close_rate
    opportunities_needed = revenue_gap / (close_rate_decimal * avg_deal_size) if (close_rate_decimal * avg_deal_size) > 0 else 0
    
    # Attainment projections
    projected_attainment = (projected_total / revenue_target * 100) if revenue_target > 0 else 0
    current_attainment = (current_actuals / revenue_target * 100) if revenue_target > 0 else 0
    
    return {
        'revenue_target': revenue_target,
        'current_actuals': current_actuals,
        'expected_pipeline': expected_pipeline,
        'projected_total': projected_total,
        'revenue_gap': revenue_gap,
        'deals_needed': max(0, deals_needed),  # Can't need negative deals
        'opportunities_needed': max(0, opportunities_needed),
        'projected_attainment': projected_attainment,
        'current_attainment': current_attainment,
        'avg_deal_size': avg_deal_size,
        'close_rate': close_rate,
        'on_track': revenue_gap <= 0
    }


def calculate_monthly_deals_needed(gap_analysis, months_remaining):
    """
    Calculate deals/opportunities needed per month to close the gap.
    """
    if months_remaining <= 0:
        return {
            'deals_per_month': 0,
            'opportunities_per_month': 0,
            'revenue_per_month': 0
        }
    
    return {
        'deals_per_month': gap_analysis['deals_needed'] / months_remaining,
        'opportunities_per_month': gap_analysis['opportunities_needed'] / months_remaining,
        'revenue_per_month': gap_analysis['revenue_gap'] / months_remaining
    }


# ===================================================================================
# ANNUAL GOAL TRACKER - VISUALIZATION FUNCTIONS
# ===================================================================================

def create_attainment_gauge(value, max_value, title, color='#3b82f6'):
    """Create a progress gauge"""
    pct = (value / max_value * 100) if max_value > 0 else 0
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=pct,
        number={'suffix': '%', 'font': {'size': 36, 'color': '#f1f5f9'}},
        delta={'reference': 100, 'relative': False, 'position': 'bottom',
               'increasing': {'color': '#10b981'}, 'decreasing': {'color': '#ef4444'}},
        title={'text': title, 'font': {'size': 14, 'color': '#94a3b8'}},
        gauge={
            'axis': {'range': [0, 120], 'tickcolor': '#475569', 'tickfont': {'color': '#64748b'}},
            'bar': {'color': color},
            'bgcolor': '#1e293b',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 80], 'color': '#1e293b'},
                {'range': [80, 100], 'color': '#1e293b'},
                {'range': [100, 120], 'color': '#1e293b'}
            ],
            'threshold': {
                'line': {'color': '#10b981', 'width': 3},
                'thickness': 0.8,
                'value': 100
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': '#f1f5f9'},
        height=200,
        margin=dict(t=80, b=20, l=30, r=30)
    )
    
    return fig


def create_pipeline_comparison_chart(data, title="Pipeline Performance"):
    """Create horizontal bar chart for pipeline comparison"""
    fig = go.Figure()
    
    # Sort by actual descending
    data = data.sort_values('Actual', ascending=True)
    
    # Custom colors for each pipeline
    pipeline_colors_ordered = [PIPELINE_COLORS.get(p, '#3b82f6') for p in data['Pipeline']]
    
    fig.add_trace(go.Bar(
        name='Plan',
        y=data['Pipeline'],
        x=data['YTD_Plan'],
        orientation='h',
        marker=dict(
            color='rgba(148, 163, 184, 0.3)',
            line=dict(color='rgba(148, 163, 184, 0.5)', width=1)
        ),
        text=[f"${x:,.0f}" for x in data['YTD_Plan']],
        textposition='inside',
        textfont=dict(color='#94a3b8', size=11),
        hovertemplate='<b>%{y}</b><br>Plan: $%{x:,.0f}<extra></extra>'
    ))
    
    fig.add_trace(go.Bar(
        name='Actual',
        y=data['Pipeline'],
        x=data['Actual'],
        orientation='h',
        marker=dict(
            color=pipeline_colors_ordered,
            line=dict(color='rgba(255,255,255,0.1)', width=1)
        ),
        text=[f"${x:,.0f}" for x in data['Actual']],
        textposition='inside',
        textfont=dict(color='#ffffff', size=12, family='Inter, sans-serif'),
        hovertemplate='<b>%{y}</b><br>Actual: $%{x:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color='#f1f5f9')) if title else None,
        barmode='overlay',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8', family='Inter, sans-serif'),
        xaxis=dict(
            gridcolor='rgba(148, 163, 184, 0.1)',
            tickformat='$,.0f',
            tickfont=dict(size=10),
            showline=False,
            zeroline=False
        ),
        yaxis=dict(
            gridcolor='rgba(148, 163, 184, 0.1)',
            tickfont=dict(size=12, color='#e2e8f0'),
            showline=False
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            font=dict(size=11),
            bgcolor='rgba(0,0,0,0)'
        ),
        height=300,
        margin=dict(t=40, b=40, l=100, r=40),
        hoverlabel=dict(
            bgcolor='#1e293b',
            font_size=12,
            font_family='Inter, sans-serif'
        )
    )
    
    return fig


def create_category_comparison_chart(data, title="Category Performance"):
    """Create bar chart for category comparison"""
    fig = go.Figure()
    
    # Sort by actual descending
    data = data.sort_values('Actual', ascending=False)
    
    # Custom colors for each category
    category_colors_ordered = [CATEGORY_COLORS.get(c, '#3b82f6') for c in data['Category']]
    
    fig.add_trace(go.Bar(
        name='Plan',
        x=data['Category'],
        y=data['YTD_Plan'],
        marker=dict(
            color='rgba(148, 163, 184, 0.2)',
            line=dict(color='rgba(148, 163, 184, 0.4)', width=1)
        ),
        text=[f"${x/1000:.0f}K" if x >= 1000 else f"${x:.0f}" for x in data['YTD_Plan']],
        textposition='outside',
        textfont=dict(color='#64748b', size=10),
        hovertemplate='<b>%{x}</b><br>Plan: $%{y:,.0f}<extra></extra>'
    ))
    
    fig.add_trace(go.Bar(
        name='Actual',
        x=data['Category'],
        y=data['Actual'],
        marker=dict(
            color=category_colors_ordered,
            line=dict(color='rgba(255,255,255,0.1)', width=1)
        ),
        text=[f"${x/1000:.0f}K" if x >= 1000 else f"${x:.0f}" for x in data['Actual']],
        textposition='outside',
        textfont=dict(color='#e2e8f0', size=10, family='Inter, sans-serif'),
        hovertemplate='<b>%{x}</b><br>Actual: $%{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color='#f1f5f9')) if title else None,
        barmode='group',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8', family='Inter, sans-serif'),
        xaxis=dict(
            gridcolor='rgba(148, 163, 184, 0.05)',
            tickangle=-45,
            tickfont=dict(size=11, color='#e2e8f0'),
            showline=False
        ),
        yaxis=dict(
            gridcolor='rgba(148, 163, 184, 0.1)',
            tickformat='$,.0f',
            tickfont=dict(size=10),
            showline=False,
            zeroline=False
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            font=dict(size=11),
            bgcolor='rgba(0,0,0,0)'
        ),
        height=400,
        margin=dict(t=60, b=100, l=80, r=40),
        bargap=0.3,
        bargroupgap=0.1,
        hoverlabel=dict(
            bgcolor='#1e293b',
            font_size=12,
            font_family='Inter, sans-serif'
        )
    )
    
    return fig


def create_monthly_trend_line_chart(monthly_actuals, forecast_df, selected_pipeline='Total', selected_category='Total'):
    """Create monthly trend line chart"""
    
    if selected_pipeline == 'Total' and selected_category == 'Total':
        plan_row = forecast_df[(forecast_df['Pipeline'] == 'Total') & (forecast_df['Category'] == 'Total')]
    elif selected_pipeline == 'Total':
        plan_row = forecast_df[(forecast_df['Pipeline'] == 'Total') & (forecast_df['Category'] == selected_category)]
    elif selected_category == 'Total':
        plan_row = forecast_df[(forecast_df['Pipeline'] == selected_pipeline) & (forecast_df['Category'] == 'Total')]
    else:
        plan_row = forecast_df[(forecast_df['Pipeline'] == selected_pipeline) & (forecast_df['Category'] == selected_category)]
    
    if plan_row.empty:
        return None
    
    plan_values = [plan_row[month].values[0] for month in MONTH_NAMES]
    
    if monthly_actuals.empty:
        actual_values = [0] * 12
    else:
        filtered = monthly_actuals.copy()
        if selected_pipeline != 'Total':
            filtered = filtered[filtered['Pipeline'] == selected_pipeline]
        if selected_category != 'Total':
            filtered = filtered[filtered['Category'] == selected_category]
        
        actual_by_month = filtered.groupby('Month_Num')['Actual'].sum().to_dict()
        actual_values = [actual_by_month.get(i, 0) for i in range(1, 13)]
    
    # Cumulative values
    plan_cumulative = np.cumsum(plan_values)
    actual_cumulative = np.cumsum(actual_values)
    
    fig = go.Figure()
    
    # Plan area
    fig.add_trace(go.Scatter(
        x=MONTH_ABBREV,
        y=plan_cumulative,
        mode='lines',
        name='Plan (Cumulative)',
        line=dict(color='rgba(148, 163, 184, 0.5)', width=2, dash='dash'),
        fill='tozeroy',
        fillcolor='rgba(148, 163, 184, 0.05)',
        hovertemplate='<b>%{x}</b><br>Plan: $%{y:,.0f}<extra></extra>'
    ))
    
    # Actual area
    fig.add_trace(go.Scatter(
        x=MONTH_ABBREV,
        y=actual_cumulative,
        mode='lines+markers',
        name='Actual (Cumulative)',
        line=dict(color='#3b82f6', width=3),
        marker=dict(size=8, color='#3b82f6', line=dict(color='#ffffff', width=2)),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.1)',
        hovertemplate='<b>%{x}</b><br>Actual: $%{y:,.0f}<extra></extra>'
    ))
    
    # Monthly bars (optional - shows monthly values)
    fig.add_trace(go.Bar(
        x=MONTH_ABBREV,
        y=actual_values,
        name='Monthly Actual',
        marker=dict(
            color='rgba(59, 130, 246, 0.3)',
            line=dict(color='rgba(59, 130, 246, 0.5)', width=1)
        ),
        hovertemplate='<b>%{x}</b><br>Monthly: $%{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8', family='Inter, sans-serif'),
        xaxis=dict(
            gridcolor='rgba(148, 163, 184, 0.1)',
            tickfont=dict(size=11, color='#e2e8f0'),
            showline=False
        ),
        yaxis=dict(
            gridcolor='rgba(148, 163, 184, 0.1)',
            tickformat='$,.0f',
            tickfont=dict(size=10),
            showline=False,
            zeroline=False
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            font=dict(size=10),
            bgcolor='rgba(0,0,0,0)'
        ),
        height=350,
        margin=dict(t=60, b=40, l=80, r=40),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='#1e293b',
            font_size=12,
            font_family='Inter, sans-serif'
        )
    )
    
    return fig


# ===================================================================================
# MAIN RENDER FUNCTION - 2026 ANNUAL GOAL TRACKER
# ===================================================================================

def render_yearly_planning_2026():
    """Main entry point for the 2026 Annual Goal Tracker"""
    
    st.markdown("""
        <style>
        /* ===== GLOBAL STYLES ===== */
        .stApp {
            background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #16213e 100%);
        }
        
        /* Hide default Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* ===== TYPOGRAPHY ===== */
        h1, h2, h3, h4 {
            color: #ffffff !important;
            font-weight: 600 !important;
            letter-spacing: -0.5px;
        }
        
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 3rem;
            font-weight: 800;
            text-align: center;
            margin-bottom: 0.5rem;
        }
        
        .sub-header {
            color: #a0aec0;
            text-align: center;
            font-size: 1.1rem;
            margin-bottom: 2rem;
        }
        
        /* ===== GLASS CARDS ===== */
        .glass-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            padding: 1.5rem;
            margin: 0.5rem 0;
            transition: all 0.3s ease;
        }
        
        .glass-card:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(255, 255, 255, 0.15);
            transform: translateY(-2px);
        }
        
        /* ===== METRIC CARDS ===== */
        .metric-card {
            background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
            border: 1px solid rgba(148, 163, 184, 0.1);
            border-radius: 16px;
            padding: 1.25rem 1.5rem;
            position: relative;
            overflow: hidden;
        }
        
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        
        .metric-card.success::before {
            background: linear-gradient(90deg, #10b981, #34d399);
        }
        
        .metric-card.warning::before {
            background: linear-gradient(90deg, #f59e0b, #fbbf24);
        }
        
        .metric-card.danger::before {
            background: linear-gradient(90deg, #ef4444, #f87171);
        }
        
        .metric-label {
            color: #94a3b8;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 0.5rem;
        }
        
        .metric-value {
            color: #f8fafc;
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.2;
            margin-bottom: 0.25rem;
        }
        
        .metric-value.large {
            font-size: 2.5rem;
        }
        
        .metric-delta {
            font-size: 0.85rem;
            font-weight: 500;
        }
        
        .metric-delta.positive { color: #34d399; }
        .metric-delta.negative { color: #f87171; }
        .metric-delta.neutral { color: #94a3b8; }
        
        /* ===== PROGRESS BAR ===== */
        .progress-container {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 1.25rem;
            margin: 0.75rem 0;
        }
        
        .progress-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }
        
        .progress-title {
            color: #e2e8f0;
            font-weight: 600;
            font-size: 1rem;
        }
        
        .progress-value {
            color: #94a3b8;
            font-size: 0.9rem;
        }
        
        .progress-bar-bg {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            height: 12px;
            overflow: hidden;
            position: relative;
        }
        
        .progress-bar-fill {
            height: 100%;
            border-radius: 8px;
            transition: width 1s ease-out;
            position: relative;
        }
        
        .progress-bar-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            animation: shimmer 2s infinite;
        }
        
        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .progress-bar-fill.excellent { background: linear-gradient(90deg, #10b981, #34d399); }
        .progress-bar-fill.good { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
        .progress-bar-fill.warning { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
        .progress-bar-fill.danger { background: linear-gradient(90deg, #ef4444, #f87171); }
        
        /* ===== PIPELINE CARDS ===== */
        .pipeline-card {
            background: linear-gradient(145deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%);
            border: 1px solid rgba(148, 163, 184, 0.1);
            border-radius: 16px;
            padding: 1.25rem;
            margin: 0.5rem 0;
            position: relative;
            overflow: hidden;
        }
        
        .pipeline-card::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
        }
        
        .pipeline-card.retention::before { background: linear-gradient(180deg, #10b981, #059669); }
        .pipeline-card.growth::before { background: linear-gradient(180deg, #3b82f6, #2563eb); }
        .pipeline-card.acquisition::before { background: linear-gradient(180deg, #8b5cf6, #7c3aed); }
        .pipeline-card.distributors::before { background: linear-gradient(180deg, #f59e0b, #d97706); }
        .pipeline-card.ecom::before { background: linear-gradient(180deg, #06b6d4, #0891b2); }
        
        .pipeline-name {
            color: #94a3b8;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 0.5rem;
        }
        
        .pipeline-actual {
            color: #f8fafc;
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }
        
        .pipeline-plan {
            color: #64748b;
            font-size: 0.85rem;
        }
        
        .pipeline-pct {
            position: absolute;
            top: 1rem;
            right: 1rem;
            font-size: 1.1rem;
            font-weight: 700;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
        }
        
        .pipeline-pct.excellent { background: rgba(16, 185, 129, 0.2); color: #34d399; }
        .pipeline-pct.good { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
        .pipeline-pct.warning { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
        .pipeline-pct.danger { background: rgba(239, 68, 68, 0.2); color: #f87171; }
        
        /* ===== SECTION HEADERS ===== */
        .section-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin: 2rem 0 1rem 0;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid rgba(148, 163, 184, 0.1);
        }
        
        .section-icon {
            font-size: 1.5rem;
        }
        
        .section-title {
            color: #f1f5f9;
            font-size: 1.25rem;
            font-weight: 600;
            margin: 0;
        }
        
        /* ===== DATA TABLE ===== */
        .styled-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            background: rgba(15, 23, 42, 0.5);
            border-radius: 12px;
            overflow: hidden;
        }
        
        .styled-table th {
            background: rgba(30, 41, 59, 0.8);
            color: #94a3b8;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 1rem;
            text-align: left;
        }
        
        .styled-table td {
            color: #e2e8f0;
            padding: 0.875rem 1rem;
            border-bottom: 1px solid rgba(148, 163, 184, 0.05);
        }
        
        .styled-table tr:hover td {
            background: rgba(255, 255, 255, 0.02);
        }
        
        /* ===== CUSTOM STREAMLIT OVERRIDES ===== */
        div[data-testid="stMetric"] {
            background: transparent !important;
        }
        
        .stSelectbox > div > div {
            background: rgba(30, 41, 59, 0.8) !important;
            border-color: rgba(148, 163, 184, 0.2) !important;
        }
        
        .stRadio > div {
            background: transparent !important;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background: rgba(30, 41, 59, 0.5) !important;
            border-radius: 12px !important;
        }
        
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <div class="main-header">🎯 2026 Annual Goal Tracker</div>
            <div class="sub-header">Real-time Progress vs. Plan by Pipeline & Category</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Load data
    with st.spinner("Loading data..."):
        data = load_annual_tracker_data()
    
    forecast_df = data.get('forecast', pd.DataFrame())
    line_items_df = data.get('line_items', pd.DataFrame())
    sales_orders_df = data.get('sales_orders', pd.DataFrame())
    sales_order_line_items_df = data.get('sales_order_line_items', pd.DataFrame())
    deals_df = data.get('deals', pd.DataFrame())
    pipeline_deals_df = data.get('pipeline_deals', pd.DataFrame())
    
    if forecast_df.empty:
        st.error("❌ Could not load 2026 Forecast data. Please check the '2026 Forecast' sheet exists.")
        return
    
    # Current period
    now = datetime.now()
    current_month = now.month
    
    # Sidebar
    st.sidebar.markdown("### 📊 Filters")
    
    # Year selector - important for comparing against prior year data
    selected_year = st.sidebar.selectbox("Actuals Year", [2026, 2025], index=0, 
                                          help="Select year for actuals data. Use 2025 to test with historical data.")
    
    period_option = st.sidebar.radio("Time Period", ["YTD (through today)", "Full Year", "Custom Month"], index=0)
    
    if period_option == "Custom Month":
        selected_month = st.sidebar.selectbox("Select Month", MONTH_NAMES, index=current_month-1)
        through_month = MONTH_NAMES.index(selected_month) + 1
    elif period_option == "Full Year":
        through_month = 12
    else:
        through_month = current_month
    
    pipeline_options = ['All Pipelines'] + FORECAST_PIPELINES
    selected_pipeline_filter = st.sidebar.selectbox("Pipeline", pipeline_options, index=0)
    
    category_options = ['All Categories'] + FORECAST_CATEGORIES
    selected_category_filter = st.sidebar.selectbox("Category", category_options, index=0)
    
    # Calculations
    ytd_plan = get_ytd_plan(forecast_df, through_month)
    ytd_actuals = calculate_ytd_actuals(line_items_df, year=selected_year)  # By Pipeline & Category
    ytd_actuals_total = calculate_ytd_actuals_total(line_items_df, year=selected_year)  # By Category only (for totals)
    monthly_actuals = calculate_monthly_actuals(line_items_df, year=selected_year)
    
    # For pipeline comparison, merge with plan
    if not ytd_actuals.empty:
        comparison = calculate_variance(ytd_actuals, ytd_plan)
    else:
        comparison = ytd_plan.copy()
        comparison['Actual'] = 0
        comparison['Variance'] = -comparison['YTD_Plan']
        comparison['Variance_Pct'] = -100
        comparison['Attainment_Pct'] = 0
    
    # For category-only comparison (used for Executive Summary totals)
    if not ytd_actuals_total.empty:
        # Get total actual from category-based calculation (includes all revenue regardless of pipeline)
        total_actual_all = ytd_actuals_total[ytd_actuals_total['Category'] == 'Total']['Actual'].values[0] if 'Total' in ytd_actuals_total['Category'].values else ytd_actuals_total['Actual'].sum()
    else:
        total_actual_all = 0
    
    # Executive Summary
    st.markdown("""
        <div class="section-header">
            <span class="section-icon">📈</span>
            <span class="section-title">Executive Summary</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Context box for leadership
    st.markdown("""
        <div style="background: rgba(59, 130, 246, 0.1); border-left: 4px solid #3b82f6; padding: 1rem; border-radius: 0 8px 8px 0; margin-bottom: 1.5rem;">
            <strong style="color: #60a5fa;">📊 What you're seeing:</strong>
            <span style="color: #94a3b8;"> Realized (invoiced) revenue vs. the 2026 Forecast plan. This is money we've already billed customers.</span>
            <br><span style="color: #64748b; font-size: 0.85rem;">Source: Invoice Line Items from NetSuite</span>
        </div>
    """, unsafe_allow_html=True)
    
    if selected_year != 2026:
        st.info(f"📅 **Note:** Showing {selected_year} actuals data for comparison. Switch to 2026 in sidebar when 2026 data is available.")
    
    # Get plan totals from forecast
    total_plan_row = ytd_plan[(ytd_plan['Pipeline'] == 'Total') & (ytd_plan['Category'] == 'Total')]
    
    if not total_plan_row.empty:
        total_plan = total_plan_row['YTD_Plan'].values[0]
        total_annual = total_plan_row['Annual_Total'].values[0]
    else:
        total_plan = ytd_plan['YTD_Plan'].sum()
        total_annual = ytd_plan['Annual_Total'].sum()
    
    # Use total_actual_all which includes ALL invoiced revenue (not just pipeline-mapped)
    total_actual = total_actual_all
    total_variance = total_actual - total_plan
    attainment = (total_actual / total_plan * 100) if total_plan > 0 else 0
    annual_attainment = (total_actual / total_annual * 100) if total_annual > 0 else 0
    
    # Determine status classes
    variance_class = "success" if total_variance >= 0 else "danger"
    attainment_class = "excellent" if attainment >= 100 else "good" if attainment >= 80 else "warning" if attainment >= 60 else "danger"
    
    # Metric Cards Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">2026 Annual Goal</div>
                <div class="metric-value large">${total_annual:,.0f}</div>
                <div class="metric-delta neutral">Full Year Target</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">YTD Plan (Jan 1 - {MONTH_NAMES[through_month-1]})</div>
                <div class="metric-value">${total_plan:,.0f}</div>
                <div class="metric-delta neutral">{through_month} month{'s' if through_month > 1 else ''} of plan</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        delta_class = "positive" if attainment >= 100 else "negative" if attainment < 80 else "neutral"
        st.markdown(f"""
            <div class="metric-card {attainment_class}">
                <div class="metric-label">YTD Actual ({selected_year})</div>
                <div class="metric-value">${total_actual:,.0f}</div>
                <div class="metric-delta {delta_class}">{attainment:.1f}% of YTD plan</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        delta_symbol = "+" if total_variance >= 0 else ""
        delta_class = "positive" if total_variance >= 0 else "negative"
        status_text = "Ahead of plan" if total_variance >= 0 else "Behind plan"
        st.markdown(f"""
            <div class="metric-card {variance_class}">
                <div class="metric-label">Variance to Plan</div>
                <div class="metric-value">{delta_symbol}${total_variance:,.0f}</div>
                <div class="metric-delta {delta_class}">{status_text}</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Big Progress Bar
    st.markdown("<br>", unsafe_allow_html=True)
    
    progress_class = "excellent" if attainment >= 100 else "good" if attainment >= 80 else "warning" if attainment >= 60 else "danger"
    progress_width = min(attainment, 120)  # Cap at 120% for display
    
    st.markdown(f"""
        <div class="progress-container">
            <div class="progress-header">
                <span class="progress-title">YTD Goal Attainment</span>
                <span class="progress-value">${total_actual:,.0f} / ${total_plan:,.0f} ({attainment:.1f}%)</span>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill {progress_class}" style="width: {progress_width}%;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Annual Progress (smaller)
    annual_progress_class = "excellent" if annual_attainment >= (through_month/12)*100 else "good" if annual_attainment >= (through_month/12)*80 else "warning"
    annual_progress_width = min(annual_attainment, 100)
    
    st.markdown(f"""
        <div class="progress-container" style="background: rgba(255,255,255,0.02);">
            <div class="progress-header">
                <span class="progress-title" style="font-size: 0.9rem;">Annual Goal Progress</span>
                <span class="progress-value">${total_actual:,.0f} / ${total_annual:,.0f} ({annual_attainment:.1f}%)</span>
            </div>
            <div class="progress-bar-bg" style="height: 8px;">
                <div class="progress-bar-fill {annual_progress_class}" style="width: {annual_progress_width}%;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Pipeline Breakdown
    st.markdown("""
        <div class="section-header">
            <span class="section-icon">🔄</span>
            <span class="section-title">Pipeline Breakdown</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Context box for leadership
    st.markdown("""
        <div style="background: rgba(139, 92, 246, 0.1); border-left: 4px solid #8b5cf6; padding: 1rem; border-radius: 0 8px 8px 0; margin-bottom: 1.5rem;">
            <strong style="color: #a78bfa;">🎯 What you're seeing:</strong>
            <span style="color: #94a3b8;"> Invoiced revenue broken down by sales motion (how we acquired/grew the customer).</span>
            <br><span style="color: #64748b; font-size: 0.85rem;">Source: Invoice Line Items joined to HubSpot Pipeline via NetSuite Invoice records</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Calculate pipeline coverage
    if not line_items_df.empty and 'Forecast Pipeline' in line_items_df.columns:
        year_filtered = line_items_df[line_items_df['Date'].dt.year == selected_year] if 'Date' in line_items_df.columns else line_items_df
        pipeline_assigned_revenue = year_filtered[year_filtered['Forecast Pipeline'].notna() & (year_filtered['Forecast Pipeline'] != 'Unmapped')]['Amount'].sum()
        total_revenue = year_filtered['Amount'].sum()
        pipeline_coverage_pct = (pipeline_assigned_revenue / total_revenue * 100) if total_revenue > 0 else 0
        
        if pipeline_coverage_pct < 100:
            st.markdown(f"""
                <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
                    <span style="color: #fbbf24;">⚠️ {pipeline_coverage_pct:.1f}% of {selected_year} revenue</span>
                    <span style="color: #94a3b8;"> (${pipeline_assigned_revenue:,.0f} / ${total_revenue:,.0f}) has HubSpot Pipeline assigned.</span>
                </div>
            """, unsafe_allow_html=True)
    
    pipeline_data = comparison[
        (comparison['Category'] == 'Total') & 
        (comparison['Pipeline'] != 'Total') &
        (comparison['Pipeline'] != 'Unmapped') &
        (comparison['Pipeline'].isin(FORECAST_PIPELINES))
    ].copy()
    
    if not pipeline_data.empty:
        # Create pipeline cards in a row
        cols = st.columns(len(FORECAST_PIPELINES))
        
        for idx, pipeline in enumerate(FORECAST_PIPELINES):
            row = pipeline_data[pipeline_data['Pipeline'] == pipeline]
            
            if not row.empty:
                actual = row['Actual'].values[0]
                plan = row['YTD_Plan'].values[0]
                att_pct = row['Attainment_Pct'].values[0]
            else:
                actual = 0
                plan_row = ytd_plan[(ytd_plan['Pipeline'] == pipeline) & (ytd_plan['Category'] == 'Total')]
                plan = plan_row['YTD_Plan'].values[0] if not plan_row.empty else 0
                att_pct = 0
            
            pct_class = "excellent" if att_pct >= 100 else "good" if att_pct >= 80 else "warning" if att_pct >= 60 else "danger"
            pipeline_class = pipeline.lower().replace(' ', '-')
            
            with cols[idx]:
                st.markdown(f"""
                    <div class="pipeline-card {pipeline_class}">
                        <div class="pipeline-pct {pct_class}">{att_pct:.0f}%</div>
                        <div class="pipeline-name">{pipeline}</div>
                        <div class="pipeline-actual">${actual:,.0f}</div>
                        <div class="pipeline-plan">Plan: ${plan:,.0f}</div>
                        <div style="margin-top: 0.75rem;">
                            <div class="progress-bar-bg" style="height: 6px;">
                                <div class="progress-bar-fill {pct_class}" style="width: {min(att_pct, 100)}%;"></div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        
        # Pipeline Chart
        st.markdown("<br>", unsafe_allow_html=True)
        pipeline_chart = create_pipeline_comparison_chart(pipeline_data, "")
        st.plotly_chart(pipeline_chart, use_container_width=True)
        
        # ===== PIPELINE VERIFICATION SECTION =====
        with st.expander("🔍 Verify Pipeline Assignment (View Raw Line Items)"):
            st.caption("Review invoices assigned to each pipeline. Includes SO Manually Built assignments based on Rep.")
            
            if not line_items_df.empty and 'Forecast Pipeline' in line_items_df.columns:
                # Filter to selected year
                year_filtered_df = line_items_df.copy()
                if 'Date' in year_filtered_df.columns:
                    year_filtered_df = year_filtered_df[year_filtered_df['Date'].dt.year == selected_year]
                
                # Get pipelines with data (including Unmapped)
                available_pipelines = year_filtered_df['Forecast Pipeline'].dropna().unique().tolist()
                # Add None/NaN option for unmapped
                if year_filtered_df['Forecast Pipeline'].isna().any():
                    available_pipelines.append('(Unmapped)')
                
                # Sort by forecast pipelines order
                sorted_pipelines = [p for p in FORECAST_PIPELINES if p in available_pipelines]
                extras = [p for p in available_pipelines if p not in FORECAST_PIPELINES and p != '(Unmapped)']
                sorted_pipelines.extend(extras)
                if '(Unmapped)' in available_pipelines:
                    sorted_pipelines.append('(Unmapped)')
                
                if sorted_pipelines:
                    st.markdown("**SELECT PIPELINE TO INSPECT**")
                    verify_pipeline = st.selectbox(
                        "Select pipeline to inspect:",
                        options=sorted_pipelines,
                        key="verify_forecast_pipeline",
                        label_visibility="collapsed"
                    )
                    
                    if verify_pipeline:
                        # Get items in this pipeline
                        if verify_pipeline == '(Unmapped)':
                            pipe_items = year_filtered_df[year_filtered_df['Forecast Pipeline'].isna()].copy()
                        else:
                            pipe_items = year_filtered_df[year_filtered_df['Forecast Pipeline'] == verify_pipeline].copy()
                        
                        # Determine which columns to show
                        verify_cols = ['Document Number']
                        if 'Correct Customer' in pipe_items.columns:
                            verify_cols.append('Correct Customer')
                        elif 'Customer' in pipe_items.columns:
                            verify_cols.append('Customer')
                        if 'Rep Master' in pipe_items.columns:
                            verify_cols.append('Rep Master')
                        if 'Raw_Pipeline' in pipe_items.columns:
                            verify_cols.append('Raw_Pipeline')
                        if 'Amount' in pipe_items.columns:
                            verify_cols.append('Amount')
                        if 'Date' in pipe_items.columns:
                            verify_cols.append('Date')
                        if 'Forecast Category' in pipe_items.columns:
                            verify_cols.append('Forecast Category')
                        
                        # Filter to existing columns
                        verify_cols = [c for c in verify_cols if c in pipe_items.columns]
                        
                        if verify_cols:
                            verify_display = pipe_items[verify_cols].copy()
                            
                            # Calculate totals before formatting
                            pipe_total_amount = pipe_items['Amount'].sum() if 'Amount' in pipe_items.columns else 0
                            unique_invoices = pipe_items['Document Number'].nunique() if 'Document Number' in pipe_items.columns else len(pipe_items)
                            
                            # Format Amount for display
                            if 'Amount' in verify_display.columns:
                                verify_display['Amount'] = verify_display['Amount'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "-")
                            
                            # Format Date for display
                            if 'Date' in verify_display.columns:
                                verify_display['Date'] = verify_display['Date'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else "-")
                            
                            # Color code for pipeline
                            pipe_color = PIPELINE_COLORS.get(verify_pipeline, '#94a3b8')
                            
                            # Show summary stats
                            st.markdown(f"""
                                <div style="background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); padding: 12px 16px; border-radius: 8px; margin-bottom: 12px;">
                                    <span style="color: #94a3b8;">Invoices in </span>
                                    <strong style="color: {pipe_color};">{verify_pipeline}</strong>
                                    <span style="color: #94a3b8;">: </span>
                                    <span style="color: #f1f5f9; font-weight: 600;">{unique_invoices:,} invoices</span>
                                    <span style="color: #475569; margin: 0 8px;">|</span>
                                    <span style="color: #94a3b8;">{len(pipe_items):,} line items</span>
                                    <span style="color: #475569; margin: 0 8px;">|</span>
                                    <span style="color: #94a3b8;">Total: </span>
                                    <span style="color: #a78bfa; font-weight: 600;">${pipe_total_amount:,.0f}</span>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Show the data (aggregated by invoice for cleaner view)
                            invoice_summary = pipe_items.groupby('Document Number').agg({
                                'Amount': 'sum',
                                'Rep Master': 'first' if 'Rep Master' in pipe_items.columns else 'count',
                                'Correct Customer': 'first' if 'Correct Customer' in pipe_items.columns else ('Customer' if 'Customer' in pipe_items.columns else 'count'),
                                'Raw_Pipeline': 'first' if 'Raw_Pipeline' in pipe_items.columns else 'count',
                                'Date': 'first' if 'Date' in pipe_items.columns else 'count'
                            }).reset_index()
                            
                            # Rename columns for display
                            invoice_summary.columns = ['Invoice #', 'Total Amount', 'Rep', 'Customer', 'Raw Pipeline', 'Date']
                            invoice_summary = invoice_summary.sort_values('Total Amount', ascending=False)
                            
                            # Format for display
                            invoice_summary['Total Amount'] = invoice_summary['Total Amount'].apply(lambda x: f"${x:,.2f}")
                            if 'Date' in invoice_summary.columns:
                                invoice_summary['Date'] = invoice_summary['Date'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else "-")
                            
                            st.dataframe(
                                invoice_summary.head(200),
                                use_container_width=True,
                                hide_index=True,
                                height=400
                            )
                            
                            if len(invoice_summary) > 200:
                                st.caption(f"Showing first 200 of {len(invoice_summary):,} invoices")
                            
                            # Show rep breakdown for this pipeline
                            if 'Rep Master' in pipe_items.columns:
                                st.markdown("**Revenue by Rep:**")
                                rep_summary = pipe_items.groupby('Rep Master')['Amount'].sum().sort_values(ascending=False)
                                for rep, amount in rep_summary.items():
                                    st.markdown(f"- `{rep}`: ${amount:,.0f}")
                        else:
                            st.info("No detailed data available for this pipeline.")
                else:
                    st.info("No pipeline data available for the selected year.")
            else:
                st.info("Line item data not available for pipeline verification.")
    else:
        st.info("📊 Pipeline breakdown will populate as invoices are linked to HubSpot deals.")
    
    # Category Breakdown
    st.markdown("""
        <div class="section-header">
            <span class="section-icon">📦</span>
            <span class="section-title">Category Breakdown</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Context box for leadership
    st.markdown("""
        <div style="background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: 1rem; border-radius: 0 8px 8px 0; margin-bottom: 1.5rem;">
            <strong style="color: #34d399;">📦 What you're seeing:</strong>
            <span style="color: #94a3b8;"> Invoiced revenue by product category. All revenue is categorized (100% coverage).</span>
            <br><span style="color: #64748b; font-size: 0.85rem;">Source: Invoice Line Items categorized by Item/SKU from NetSuite</span>
        </div>
    """, unsafe_allow_html=True)
    
    # For category breakdown, use ytd_actuals_total which includes ALL revenue
    # Merge with plan data for the 'Total' pipeline row
    category_plan = ytd_plan[
        (ytd_plan['Pipeline'] == 'Total') & 
        (ytd_plan['Category'] != 'Total') &
        (ytd_plan['Category'].isin(FORECAST_CATEGORIES))
    ][['Category', 'YTD_Plan', 'Annual_Total']].copy()
    
    if not ytd_actuals_total.empty:
        category_actuals = ytd_actuals_total[ytd_actuals_total['Category'] != 'Total'].copy()
        category_data = category_plan.merge(category_actuals, on='Category', how='left')
        category_data['Actual'] = category_data['Actual'].fillna(0)
    else:
        category_data = category_plan.copy()
        category_data['Actual'] = 0
    
    category_data['Variance'] = category_data['Actual'] - category_data['YTD_Plan']
    category_data['Attainment_Pct'] = np.where(
        category_data['YTD_Plan'] > 0,
        (category_data['Actual'] / category_data['YTD_Plan']) * 100,
        0
    )
    
    if not category_data.empty:
        category_chart = create_category_comparison_chart(category_data, "")
        st.plotly_chart(category_chart, use_container_width=True)
        
        # Use st.dataframe with column formatting instead of HTML
        with st.expander("📋 View Category Details"):
            display_df = category_data[['Category', 'YTD_Plan', 'Actual', 'Variance', 'Attainment_Pct', 'Annual_Total']].copy()
            
            # Format for display
            display_df['YTD Plan'] = display_df['YTD_Plan'].apply(lambda x: f"${x:,.0f}")
            display_df['YTD Actual'] = display_df['Actual'].apply(lambda x: f"${x:,.0f}")
            display_df['Variance'] = display_df['Variance'].apply(lambda x: f"${x:+,.0f}")
            display_df['Attainment'] = display_df['Attainment_Pct'].apply(lambda x: f"{x:.1f}%")
            display_df['Annual Goal'] = display_df['Annual_Total'].apply(lambda x: f"${x:,.0f}")
            
            # Select only display columns
            display_df = display_df[['Category', 'YTD Plan', 'YTD Actual', 'Variance', 'Attainment', 'Annual Goal']]
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Category": st.column_config.TextColumn("Category", width="medium"),
                    "YTD Plan": st.column_config.TextColumn("YTD Plan", width="small"),
                    "YTD Actual": st.column_config.TextColumn("YTD Actual", width="small"),
                    "Variance": st.column_config.TextColumn("Variance", width="small"),
                    "Attainment": st.column_config.TextColumn("Attainment", width="small"),
                    "Annual Goal": st.column_config.TextColumn("Annual Goal", width="small"),
                }
            )
        
        # ===== VERIFICATION SECTION - Drill down into raw line items =====
        with st.expander("🔍 Verify Categorization (View Raw Line Items)"):
            st.caption("Review the actual SKUs/items included in each category to verify correct classification")
            
            # Get categories that have actuals for the selector
            if not line_items_df.empty and 'Forecast Category' in line_items_df.columns:
                # Filter to selected year
                year_filtered_df = line_items_df.copy()
                if 'Date' in year_filtered_df.columns:
                    year_filtered_df = year_filtered_df[year_filtered_df['Date'].dt.year == selected_year]
                
                # Get categories with data
                available_categories = year_filtered_df['Forecast Category'].dropna().unique().tolist()
                # Sort by the order in FORECAST_CATEGORIES, then add any extras
                sorted_categories = [c for c in FORECAST_CATEGORIES if c in available_categories]
                extras = [c for c in available_categories if c not in FORECAST_CATEGORIES]
                sorted_categories.extend(extras)
                
                if sorted_categories:
                    st.markdown("**SELECT CATEGORY TO INSPECT**")
                    verify_category = st.selectbox(
                        "Select category to inspect:",
                        options=sorted_categories,
                        key="verify_forecast_category",
                        label_visibility="collapsed"
                    )
                    
                    if verify_category:
                        # Get items in this category
                        cat_items = year_filtered_df[year_filtered_df['Forecast Category'] == verify_category].copy()
                        
                        # Determine which columns to show
                        verify_cols = []
                        if 'Item' in cat_items.columns:
                            verify_cols.append('Item')
                        if 'Product Category' in cat_items.columns:
                            verify_cols.append('Product Category')
                        if 'Product Sub-Category' in cat_items.columns:
                            verify_cols.append('Product Sub-Category')
                        if 'Unified Category' in cat_items.columns:
                            verify_cols.append('Unified Category')
                        if 'Amount' in cat_items.columns:
                            verify_cols.append('Amount')
                        if 'Quantity' in cat_items.columns:
                            verify_cols.append('Quantity')
                        if 'Document Number' in cat_items.columns:
                            verify_cols.append('Document Number')
                        
                        # Filter to existing columns
                        verify_cols = [c for c in verify_cols if c in cat_items.columns]
                        
                        if verify_cols:
                            verify_display = cat_items[verify_cols].copy()
                            
                            # Calculate totals before formatting
                            cat_total_amount = cat_items['Amount'].sum() if 'Amount' in cat_items.columns else 0
                            cat_total_qty = cat_items['Quantity'].sum() if 'Quantity' in cat_items.columns else 0
                            
                            # Format Amount for display
                            if 'Amount' in verify_display.columns:
                                verify_display['Amount'] = verify_display['Amount'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "-")
                            
                            # Format Quantity for display
                            if 'Quantity' in verify_display.columns:
                                verify_display['Quantity'] = verify_display['Quantity'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "-")
                            
                            # Show summary stats
                            st.markdown(f"""
                                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); padding: 12px 16px; border-radius: 8px; margin-bottom: 12px;">
                                    <span style="color: #94a3b8;">Items in </span>
                                    <strong style="color: #34d399;">{verify_category}</strong>
                                    <span style="color: #94a3b8;">: </span>
                                    <span style="color: #f1f5f9; font-weight: 600;">{len(cat_items):,} line items</span>
                                    <span style="color: #475569; margin: 0 8px;">|</span>
                                    <span style="color: #94a3b8;">Total: </span>
                                    <span style="color: #10b981; font-weight: 600;">${cat_total_amount:,.0f}</span>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Show the data
                            st.dataframe(
                                verify_display.head(500),  # Limit to 500 rows for performance
                                use_container_width=True,
                                hide_index=True,
                                height=400
                            )
                            
                            if len(cat_items) > 500:
                                st.caption(f"Showing first 500 of {len(cat_items):,} line items")
                            
                            # Show unique sub-categories breakdown
                            if 'Product Sub-Category' in cat_items.columns:
                                st.markdown("**Sub-categories found:**")
                                
                                subcat_summary = cat_items.groupby('Product Sub-Category').agg({
                                    'Amount': 'sum',
                                    'Quantity': 'sum' if 'Quantity' in cat_items.columns else 'count'
                                }).reset_index()
                                subcat_summary = subcat_summary.sort_values('Amount', ascending=False)
                                
                                for _, subcat_row in subcat_summary.iterrows():
                                    subcat_name = subcat_row['Product Sub-Category']
                                    subcat_count = len(cat_items[cat_items['Product Sub-Category'] == subcat_name])
                                    subcat_revenue = subcat_row['Amount']
                                    st.markdown(f"- `{subcat_name}`: {subcat_count} items, ${subcat_revenue:,.0f}")
                        else:
                            st.info("No detailed item data available for verification.")
                else:
                    st.info("No category data available for the selected year.")
            else:
                st.info("Line item data not available for verification.")
    
    # Monthly Trend
    st.markdown("""
        <div class="section-header">
            <span class="section-icon">📅</span>
            <span class="section-title">Monthly Trend</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Context box
    st.markdown("""
        <div style="background: rgba(6, 182, 212, 0.1); border-left: 4px solid #06b6d4; padding: 1rem; border-radius: 0 8px 8px 0; margin-bottom: 1.5rem;">
            <strong style="color: #22d3ee;">📈 What you're seeing:</strong>
            <span style="color: #94a3b8;"> Cumulative invoiced revenue over time compared to plan. Monthly bars show individual month performance.</span>
            <br><span style="color: #64748b; font-size: 0.85rem;">Use the filters to drill down by Pipeline or Category</span>
        </div>
    """, unsafe_allow_html=True)
    
    trend_col1, trend_col2 = st.columns([4, 1])
    
    with trend_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        trend_pipeline = st.selectbox("Pipeline", ['Total'] + FORECAST_PIPELINES, key='trend_pipeline')
        trend_category = st.selectbox("Category", ['Total'] + FORECAST_CATEGORIES, key='trend_category')
    
    with trend_col1:
        trend_chart = create_monthly_trend_line_chart(monthly_actuals, forecast_df, trend_pipeline, trend_category)
        if trend_chart:
            st.plotly_chart(trend_chart, use_container_width=True)
    
    # Pipeline Health (Forward-Looking Indicators)
    st.markdown("""
        <div class="section-header">
            <span class="section-icon">💼</span>
            <span class="section-title">Forward-Looking Pipeline</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Context box explaining the difference
    st.markdown("""
        <div style="background: rgba(245, 158, 11, 0.1); border-left: 4px solid #f59e0b; padding: 1rem; border-radius: 0 8px 8px 0; margin-bottom: 1.5rem;">
            <strong style="color: #fbbf24;">🔮 What you're seeing:</strong>
            <span style="color: #94a3b8;"> Revenue that hasn't been invoiced yet but is in the pipeline. These are leading indicators of future revenue.</span>
        </div>
    """, unsafe_allow_html=True)
    
    health_col1, health_col2 = st.columns(2)
    
    with health_col1:
        if not sales_orders_df.empty:
            if 'Status' in sales_orders_df.columns:
                pending_orders = sales_orders_df[
                    sales_orders_df['Status'].str.contains('Pending|Partial', case=False, na=False)
                ]
            else:
                pending_orders = sales_orders_df
            
            pending_total = pending_orders['Amount'].sum() if 'Amount' in pending_orders.columns else 0
            pending_count = len(pending_orders)
            
            st.markdown(f"""
                <div class="glass-card">
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
                        <span style="font-size: 1.5rem;">📋</span>
                        <div>
                            <div class="metric-label">Pending Sales Orders</div>
                            <div style="color: #64748b; font-size: 0.75rem;">Booked but not yet invoiced</div>
                        </div>
                    </div>
                    <div class="metric-value">${pending_total:,.0f}</div>
                    <div class="metric-delta neutral">{pending_count:,} orders awaiting fulfillment</div>
                    <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid rgba(148,163,184,0.1);">
                        <span style="color: #64748b; font-size: 0.8rem;">⏱️ High confidence — typically converts to invoice within 2-4 weeks</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="glass-card">
                    <div class="metric-label">Pending Sales Orders</div>
                    <div class="metric-value neutral">No data available</div>
                </div>
            """, unsafe_allow_html=True)
    
    with health_col2:
        if not pipeline_deals_df.empty:
            if 'Deal Stage' in pipeline_deals_df.columns:
                open_deals = pipeline_deals_df[~pipeline_deals_df['Deal Stage'].str.contains('Closed|Won|Lost', case=False, na=False)]
            else:
                open_deals = pipeline_deals_df
            
            pipeline_total = open_deals['Amount'].sum() if 'Amount' in open_deals.columns else 0
            deal_count = open_deals['Deal ID'].nunique() if 'Deal ID' in open_deals.columns else len(open_deals)
            
            st.markdown(f"""
                <div class="glass-card">
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
                        <span style="font-size: 1.5rem;">🎯</span>
                        <div>
                            <div class="metric-label">Open HubSpot Deals</div>
                            <div style="color: #64748b; font-size: 0.75rem;">Active opportunities in pipeline</div>
                        </div>
                    </div>
                    <div class="metric-value">${pipeline_total:,.0f}</div>
                    <div class="metric-delta neutral">{deal_count:,} deals in active stages</div>
                    <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid rgba(148,163,184,0.1);">
                        <span style="color: #64748b; font-size: 0.8rem;">📊 Variable confidence — depends on deal stage and close date</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="glass-card">
                    <div class="metric-label">Open HubSpot Deals</div>
                    <div class="metric-value neutral">No data available</div>
                </div>
            """, unsafe_allow_html=True)
    
    # Add a visual showing the revenue progression
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
        <div style="background: rgba(30, 41, 59, 0.5); border-radius: 12px; padding: 1.25rem; margin-top: 1rem;">
            <div style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 1rem; text-align: center;">
                <strong>Revenue Progression Flow</strong>
            </div>
            <div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;">
                <div style="text-align: center; padding: 0.75rem;">
                    <div style="color: #64748b; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px;">HubSpot Deals</div>
                    <div style="color: #8b5cf6; font-size: 1.1rem; font-weight: 600;">Opportunity</div>
                </div>
                <div style="color: #475569;">→</div>
                <div style="text-align: center; padding: 0.75rem;">
                    <div style="color: #64748b; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px;">Sales Orders</div>
                    <div style="color: #f59e0b; font-size: 1.1rem; font-weight: 600;">Booked</div>
                </div>
                <div style="color: #475569;">→</div>
                <div style="text-align: center; padding: 0.75rem;">
                    <div style="color: #64748b; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px;">Invoices</div>
                    <div style="color: #10b981; font-size: 1.1rem; font-weight: 600;">Realized ✓</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # =========================================================================
    # COMPREHENSIVE REVENUE BREAKDOWN - Actuals + Pending + Deals
    # =========================================================================
    st.markdown("""
        <div class="section-header">
            <span class="section-icon">📊</span>
            <span class="section-title">Comprehensive Revenue Breakdown</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Context box
    st.markdown("""
        <div style="background: rgba(99, 102, 241, 0.1); border-left: 4px solid #6366f1; padding: 1rem; border-radius: 0 8px 8px 0; margin-bottom: 1.5rem;">
            <strong style="color: #a5b4fc;">📊 What you're seeing:</strong>
            <span style="color: #94a3b8;"> Combined view of Realized Revenue + Pending Orders + HubSpot Pipeline, broken down by Category and Pipeline.</span>
            <br><span style="color: #64748b; font-size: 0.85rem;">Use the filters to adjust time period and which HubSpot deal stages to include.</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Time Period and Deal Stage Filters
    filter_col1, filter_col2 = st.columns([1, 2])
    
    with filter_col1:
        st.markdown("**Time Period:**")
        time_period = st.radio(
            "View by:",
            options=["Month", "Quarter"],
            index=0,
            horizontal=True,
            key="pipeline_time_period",
            label_visibility="collapsed"
        )
        
        # Determine the date range based on selection
        # Use through_month from sidebar for consistency with Category Breakdown section
        now = datetime.now()
        if time_period == "Month":
            # Use sidebar's through_month setting for consistency
            period_start = datetime(selected_year, through_month, 1)
            if through_month == 12:
                period_end = datetime(selected_year + 1, 1, 1) - timedelta(days=1)
            else:
                period_end = datetime(selected_year, through_month + 1, 1) - timedelta(days=1)
            period_label = period_start.strftime("%B %Y")
        else:
            # Use sidebar's through_month to determine quarter
            selected_quarter = (through_month - 1) // 3 + 1
            quarter_start_month = (selected_quarter - 1) * 3 + 1
            quarter_end_month = selected_quarter * 3
            period_start = datetime(selected_year, quarter_start_month, 1)
            if quarter_end_month == 12:
                period_end = datetime(selected_year + 1, 1, 1) - timedelta(days=1)
            else:
                period_end = datetime(selected_year, quarter_end_month + 1, 1) - timedelta(days=1)
            period_label = f"Q{selected_quarter} {selected_year}"
        
        st.caption(f"Showing: **{period_label}**")
    
    with filter_col2:
        st.markdown("**HubSpot Deal Stage Filter:**")
        
        # Available stages - check what's in the data (try both column names)
        available_stages = []
        stage_column = None
        
        if not pipeline_deals_df.empty:
            if 'Close Status' in pipeline_deals_df.columns:
                stage_column = 'Close Status'
                available_stages = pipeline_deals_df['Close Status'].dropna().unique().tolist()
            elif 'Deal Stage' in pipeline_deals_df.columns:
                stage_column = 'Deal Stage'
                available_stages = pipeline_deals_df['Deal Stage'].dropna().unique().tolist()
    
    # Common stage names to look for (in priority order)
    priority_stages = ['Commit', 'Best Case', 'Expect', 'Opportunity']
    stage_options = [s for s in priority_stages if s in available_stages]
    # Add any other stages not in priority list
    other_stages = [s for s in available_stages if s not in priority_stages and 'Closed' not in str(s) and 'Won' not in str(s) and 'Lost' not in str(s)]
    stage_options.extend(other_stages)
    
    if stage_options:
        selected_stages = st.multiselect(
            "Select deal stages to include:",
            options=stage_options,
            default=[s for s in ['Commit', 'Best Case', 'Expect'] if s in stage_options],  # Default to higher confidence stages
            key="revenue_breakdown_stages",
            help="Select which HubSpot deal stages to include in the pipeline view"
        )
    else:
        selected_stages = []
        st.info("No HubSpot deal stages available")
    
    # Calculate data for each source
    # 1. Actuals (from line_items_df) - filtered by selected time period
    actuals_by_category = pd.DataFrame()
    actuals_by_pipeline = pd.DataFrame()
    
    if not line_items_df.empty:
        period_filtered = line_items_df.copy()
        if 'Date' in period_filtered.columns:
            # Filter by the selected time period (Month or Quarter)
            period_filtered = period_filtered[
                (period_filtered['Date'] >= period_start) & 
                (period_filtered['Date'] <= period_end)
            ]
        
        if 'Forecast Category' in period_filtered.columns:
            actuals_by_category = period_filtered.groupby('Forecast Category')['Amount'].sum().reset_index()
            actuals_by_category.columns = ['Category', 'Actuals']
        
        if 'Forecast Pipeline' in period_filtered.columns:
            actuals_by_pipeline = period_filtered.groupby('Forecast Pipeline')['Amount'].sum().reset_index()
            actuals_by_pipeline.columns = ['Pipeline', 'Actuals']
    
    # 2. Pending Sales Orders (from sales_order_line_items_df for proper categorization)
    # Uses Updated Status from _NS_SalesOrders_Data and the appropriate date based on status:
    # - Pending Fulfillment: Customer Promise Last Date to Ship or Projected Date
    # - Pending Approval: Pending Approval Date
    # Records without dates are excluded from projections
    pending_by_category = pd.DataFrame()
    pending_by_pipeline = pd.DataFrame()
    
    if not sales_order_line_items_df.empty:
        pending_orders = sales_order_line_items_df.copy()
        
        # Filter for pending status using Updated Status if available, otherwise fall back to Status
        status_col = 'Updated Status' if 'Updated Status' in pending_orders.columns else 'Status'
        if status_col in pending_orders.columns:
            pending_orders = pending_orders[
                pending_orders[status_col].str.contains('Pending|Partial', case=False, na=False)
            ]
        
        # Filter by Expected Ship Date within the selected time period
        # This excludes records without dates (PA No Date, PF No Date, PA Old)
        if 'Expected Ship Date' in pending_orders.columns:
            pending_orders = pending_orders[
                (pending_orders['Expected Ship Date'].notna()) &
                (pending_orders['Expected Ship Date'] >= period_start) & 
                (pending_orders['Expected Ship Date'] <= period_end)
            ]
        
        if 'Forecast Category' in pending_orders.columns:
            pending_by_category = pending_orders.groupby('Forecast Category')['Amount'].sum().reset_index()
            pending_by_category.columns = ['Category', 'Pending']
        
        if 'Forecast Pipeline' in pending_orders.columns:
            pending_by_pipeline = pending_orders.groupby('Forecast Pipeline')['Amount'].sum().reset_index()
            pending_by_pipeline.columns = ['Pipeline', 'Pending']
    elif not sales_orders_df.empty:
        # Fallback to header-level sales orders if line items not available
        pending_orders = sales_orders_df.copy()
        
        status_col = 'Updated Status' if 'Updated Status' in pending_orders.columns else 'Status'
        if status_col in pending_orders.columns:
            pending_orders = pending_orders[
                pending_orders[status_col].str.contains('Pending|Partial', case=False, na=False)
            ]
        
        if 'Forecast Category' in pending_orders.columns:
            pending_by_category = pending_orders.groupby('Forecast Category')['Amount'].sum().reset_index()
            pending_by_category.columns = ['Category', 'Pending']
        
        if 'Forecast Pipeline' in pending_orders.columns:
            pending_by_pipeline = pending_orders.groupby('Forecast Pipeline')['Amount'].sum().reset_index()
            pending_by_pipeline.columns = ['Pipeline', 'Pending']
    
    # 3. HubSpot Deals (filtered by selected stages AND Pending Approval Date within time period)
    deals_by_category = pd.DataFrame()
    deals_by_pipeline = pd.DataFrame()
    
    if not pipeline_deals_df.empty and selected_stages and stage_column:
        filtered_deals = pipeline_deals_df.copy()
        
        # Filter by selected stages using the detected column
        stage_mask = filtered_deals[stage_column].isin(selected_stages)
        filtered_deals = filtered_deals[stage_mask]
        
        # Filter by Pending Approval Date within the selected time period (preferred)
        # Fall back to Close Date if Pending Approval Date not available
        date_col_used = None
        if 'Pending Approval Date' in filtered_deals.columns:
            # Use Pending Approval Date for filtering
            date_col_used = 'Pending Approval Date'
            filtered_deals = filtered_deals[
                (filtered_deals['Pending Approval Date'] >= period_start) & 
                (filtered_deals['Pending Approval Date'] <= period_end)
            ]
        elif 'Close Date' in filtered_deals.columns:
            # Fallback to Close Date if Pending Approval Date not available
            date_col_used = 'Close Date'
            filtered_deals = filtered_deals[
                (filtered_deals['Close Date'] >= period_start) & 
                (filtered_deals['Close Date'] <= period_end)
            ]
        
        if 'Forecast Category' in filtered_deals.columns:
            deals_by_category = filtered_deals.groupby('Forecast Category')['Amount'].sum().reset_index()
            deals_by_category.columns = ['Category', 'Deals']
        
        if 'Forecast Pipeline' in filtered_deals.columns:
            deals_by_pipeline = filtered_deals.groupby('Forecast Pipeline')['Amount'].sum().reset_index()
            deals_by_pipeline.columns = ['Pipeline', 'Deals']
    
    # DEBUG: Pending Orders diagnostics
    with st.expander("🔍 DEBUG: Pending Orders (Sales Orders)"):
        st.markdown(f"**Period: {period_label}** (from {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')})")
        
        if not sales_order_line_items_df.empty:
            st.write(f"Total sales_order_line_items_df rows: {len(sales_order_line_items_df)}")
            
            # Check for key columns
            col1, col2, col3 = st.columns(3)
            with col1:
                if 'Updated Status' in sales_order_line_items_df.columns:
                    st.success("✅ Updated Status column found")
                    status_dist = sales_order_line_items_df['Updated Status'].value_counts()
                    st.write("Status distribution:")
                    st.dataframe(status_dist.head(10))
                else:
                    st.warning("⚠️ No 'Updated Status' - using 'Status'")
            
            with col2:
                if 'Expected Ship Date' in sales_order_line_items_df.columns:
                    non_null = sales_order_line_items_df['Expected Ship Date'].notna().sum()
                    st.metric("Expected Ship Date", f"{non_null} / {len(sales_order_line_items_df)}")
                else:
                    st.error("❌ No 'Expected Ship Date' computed")
            
            with col3:
                st.markdown("**Date columns available:**")
                date_cols = ['Customer Promise Last Date to Ship', 'Projected Date', 'Pending Approval Date']
                for col in date_cols:
                    if col in sales_order_line_items_df.columns:
                        count = sales_order_line_items_df[col].notna().sum()
                        st.write(f"- {col}: {count}")
            
            # Show pending orders breakdown
            st.markdown("---")
            st.markdown("**After Filtering (Pending + Has Date + In Period):**")
            if not pending_by_category.empty:
                st.dataframe(pending_by_category, hide_index=True)
                st.write(f"Total Pending: ${pending_by_category['Pending'].sum():,.0f}")
            else:
                st.warning("No pending orders passed the filters!")
        else:
            st.error("sales_order_line_items_df is empty!")
    
    # DEBUG: Deals categorization diagnostics
    with st.expander("🔍 DEBUG: HubSpot Deals Categorization"):
        st.markdown(f"**Period: {period_label}** (from {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')})")
        
        if not pipeline_deals_df.empty:
            st.write(f"Total pipeline_deals_df rows: {len(pipeline_deals_df)}")
            
            # Check date columns
            st.markdown("**Date Columns:**")
            date_col1, date_col2 = st.columns(2)
            with date_col1:
                if 'Pending Approval Date' in pipeline_deals_df.columns:
                    non_null_pa = pipeline_deals_df['Pending Approval Date'].notna().sum()
                    st.metric("Pending Approval Date", f"{non_null_pa} / {len(pipeline_deals_df)}")
                else:
                    st.warning("⚠️ No 'Pending Approval Date' column - using Close Date")
            with date_col2:
                if 'Close Date' in pipeline_deals_df.columns:
                    non_null_cd = pipeline_deals_df['Close Date'].notna().sum()
                    st.metric("Close Date", f"{non_null_cd} / {len(pipeline_deals_df)}")
            
            # Check SKU and Deal Type columns
            col1, col2 = st.columns(2)
            with col1:
                if 'SKU' in pipeline_deals_df.columns:
                    non_null_skus = pipeline_deals_df['SKU'].notna().sum()
                    st.metric("SKU Values", f"{non_null_skus} / {len(pipeline_deals_df)}")
                else:
                    st.error("❌ No 'SKU' column!")
            
            with col2:
                if 'Deal Type' in pipeline_deals_df.columns:
                    non_null_dt = pipeline_deals_df['Deal Type'].notna().sum()
                    st.metric("Deal Type Values", f"{non_null_dt} / {len(pipeline_deals_df)}")
                else:
                    st.error("❌ No 'Deal Type' column!")
            
            # Show categorization source breakdown
            if 'SKU_Category' in pipeline_deals_df.columns and 'DealType_Category' in pipeline_deals_df.columns:
                st.markdown("**Categorization Source:**")
                sku_used = pipeline_deals_df['SKU_Category'].notna() & (pipeline_deals_df['SKU_Category'] != 'Other')
                st.write(f"- Using SKU lookup: {sku_used.sum()} deals")
                st.write(f"- Using Deal Type fallback: {(~sku_used).sum()} deals")
            
            # Check Forecast Category distribution
            if 'Forecast Category' in pipeline_deals_df.columns:
                st.markdown("**All Deals - Forecast Category Distribution:**")
                all_cat_dist = pipeline_deals_df.groupby('Forecast Category')['Amount'].agg(['count', 'sum']).reset_index()
                all_cat_dist.columns = ['Category', 'Count', 'Total Amount']
                all_cat_dist['Total Amount'] = all_cat_dist['Total Amount'].apply(lambda x: f"${x:,.0f}")
                all_cat_dist = all_cat_dist.sort_values('Count', ascending=False)
                st.dataframe(all_cat_dist, hide_index=True)
                
                # Check specifically for Labels
                labels_deals = pipeline_deals_df[pipeline_deals_df['Forecast Category'] == 'Labels']
                st.info(f"**Labels deals (all time):** {len(labels_deals)} deals, ${labels_deals['Amount'].sum():,.0f}")
            else:
                st.error("❌ No 'Forecast Category' column found!")
            
            # Show what made it through the filters
            st.markdown("---")
            st.markdown("**After Stage + Date Filtering:**")
            if not deals_by_category.empty:
                st.dataframe(deals_by_category, hide_index=True)
            else:
                st.warning("No deals passed the filters!")
                
                # Debug the filtering
                if selected_stages and stage_column:
                    stage_filtered = pipeline_deals_df[pipeline_deals_df[stage_column].isin(selected_stages)]
                    st.write(f"After stage filter: {len(stage_filtered)} deals")
                    
                    # Check which date column to use
                    date_col = 'Pending Approval Date' if 'Pending Approval Date' in stage_filtered.columns else 'Close Date'
                    if date_col in stage_filtered.columns:
                        date_filtered = stage_filtered[
                            (stage_filtered[date_col] >= period_start) & 
                            (stage_filtered[date_col] <= period_end)
                        ]
                        st.write(f"After {date_col} filter: {len(date_filtered)} deals")
                        
                        if len(date_filtered) > 0 and 'Forecast Category' in date_filtered.columns:
                            st.markdown("**Filtered deals by category:**")
                            filtered_cats = date_filtered.groupby('Forecast Category')['Amount'].sum().reset_index()
                            st.dataframe(filtered_cats, hide_index=True)
        else:
            st.error("pipeline_deals_df is empty!")
    
    # ===== COMPREHENSIVE CATEGORY CHART - Plan vs Full Pipeline =====
    st.markdown(f"### 📊 Plan vs. Full Pipeline by Category ({period_label})")
    st.caption(f"Compare your {period_label} plan against realized revenue plus everything in the pipeline")
    
    # Calculate period plan based on time selection (using through_month from sidebar)
    if time_period == "Month":
        period_plan = get_period_plan(forecast_df, 'Month', month=through_month)
    else:
        selected_quarter = (through_month - 1) // 3 + 1
        period_plan = get_period_plan(forecast_df, 'Quarter', quarter=selected_quarter)
    
    # Merge all category data INCLUDING plan
    all_categories = list(set(
        FORECAST_CATEGORIES +
        list(actuals_by_category['Category'].unique() if not actuals_by_category.empty else []) +
        list(pending_by_category['Category'].unique() if not pending_by_category.empty else []) +
        list(deals_by_category['Category'].unique() if not deals_by_category.empty else [])
    ))
    
    # Filter to forecast categories for cleaner chart
    chart_categories = [c for c in FORECAST_CATEGORIES if c in all_categories]
    
    if chart_categories:
        category_combined = pd.DataFrame({'Category': chart_categories})
        
        # Add Period Plan from forecast
        plan_by_category = period_plan[
            (period_plan['Pipeline'] == 'Total') & 
            (period_plan['Category'].isin(chart_categories))
        ][['Category', 'Period_Plan']].copy()
        category_combined = category_combined.merge(plan_by_category, on='Category', how='left')
        category_combined['Period_Plan'] = category_combined['Period_Plan'].fillna(0)
        
        if not actuals_by_category.empty:
            category_combined = category_combined.merge(actuals_by_category, on='Category', how='left')
        else:
            category_combined['Actuals'] = 0
            
        if not pending_by_category.empty:
            category_combined = category_combined.merge(pending_by_category, on='Category', how='left')
        else:
            category_combined['Pending'] = 0
            
        if not deals_by_category.empty:
            category_combined = category_combined.merge(deals_by_category, on='Category', how='left')
        else:
            category_combined['Deals'] = 0
        
        category_combined = category_combined.fillna(0)
        category_combined['Total Pipeline'] = category_combined['Actuals'] + category_combined['Pending'] + category_combined['Deals']
        category_combined['Variance'] = category_combined['Total Pipeline'] - category_combined['Period_Plan']
        category_combined['Attainment'] = np.where(
            category_combined['Period_Plan'] > 0,
            (category_combined['Total Pipeline'] / category_combined['Period_Plan'] * 100),
            0
        )
        category_combined = category_combined.sort_values('Period_Plan', ascending=False)
        
        # ===== BIG BEAUTIFUL CHART =====
        fig_cat = go.Figure()
        
        # Plan bar (gray, semi-transparent background)
        fig_cat.add_trace(go.Bar(
            name=f'{period_label} Plan',
            x=category_combined['Category'],
            y=category_combined['Period_Plan'],
            marker=dict(
                color='rgba(148, 163, 184, 0.3)',
                line=dict(color='rgba(148, 163, 184, 0.6)', width=2)
            ),
            text=[f"${x/1000:.0f}K" if x >= 1000 else f"${x:.0f}" for x in category_combined['Period_Plan']],
            textposition='outside',
            textfont=dict(color='#94a3b8', size=11),
            hovertemplate='<b>%{x}</b><br>Plan: $%{y:,.0f}<extra></extra>',
            offsetgroup=0
        ))
        
        # Actuals (green - base of stack)
        fig_cat.add_trace(go.Bar(
            name='✓ Actuals (Invoiced)',
            x=category_combined['Category'],
            y=category_combined['Actuals'],
            marker=dict(
                color='#10b981',
                line=dict(color='#059669', width=1)
            ),
            text=[f"${x/1000:.0f}K" if x >= 1000 else f"${x:.0f}" for x in category_combined['Actuals']],
            textposition='inside',
            textfont=dict(color='white', size=10, family='Inter'),
            hovertemplate='<b>%{x}</b><br>Invoiced: $%{y:,.0f}<extra></extra>',
            offsetgroup=1
        ))
        
        # Pending Orders (amber - middle of stack)
        fig_cat.add_trace(go.Bar(
            name='📋 Pending Orders',
            x=category_combined['Category'],
            y=category_combined['Pending'],
            marker=dict(
                color='#f59e0b',
                line=dict(color='#d97706', width=1)
            ),
            text=[f"${x/1000:.0f}K" if x >= 1000 else "" for x in category_combined['Pending']],
            textposition='inside',
            textfont=dict(color='white', size=10, family='Inter'),
            hovertemplate='<b>%{x}</b><br>Pending: $%{y:,.0f}<extra></extra>',
            offsetgroup=1
        ))
        
        # HubSpot Deals (purple - top of stack)
        fig_cat.add_trace(go.Bar(
            name='🎯 HubSpot Deals',
            x=category_combined['Category'],
            y=category_combined['Deals'],
            marker=dict(
                color='#8b5cf6',
                line=dict(color='#7c3aed', width=1)
            ),
            text=[f"${x/1000:.0f}K" if x >= 1000 else "" for x in category_combined['Deals']],
            textposition='inside',
            textfont=dict(color='white', size=10, family='Inter'),
            hovertemplate='<b>%{x}</b><br>Deals: $%{y:,.0f}<extra></extra>',
            offsetgroup=1
        ))
        
        # Add attainment % annotations at the top
        for i, row in category_combined.iterrows():
            att = row['Attainment']
            total = row['Total Pipeline']
            color = '#10b981' if att >= 100 else '#f59e0b' if att >= 80 else '#ef4444'
            
            fig_cat.add_annotation(
                x=row['Category'],
                y=total + (category_combined['Period_Plan'].max() * 0.05),
                text=f"{att:.0f}%",
                showarrow=False,
                font=dict(color=color, size=12, family='Inter'),
                yanchor='bottom'
            )
        
        fig_cat.update_layout(
            barmode='stack',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0', family='Inter, sans-serif'),
            xaxis=dict(
                gridcolor='rgba(148, 163, 184, 0.1)',
                tickangle=-45,
                tickfont=dict(size=12, color='#e2e8f0'),
                showline=False
            ),
            yaxis=dict(
                gridcolor='rgba(148, 163, 184, 0.1)',
                tickformat='$,.0f',
                tickfont=dict(size=10, color='#94a3b8'),
                showline=False,
                zeroline=False
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='center',
                x=0.5,
                font=dict(size=11, color='#e2e8f0'),
                bgcolor='rgba(0,0,0,0)'
            ),
            height=500,
            margin=dict(t=80, b=120, l=80, r=40),
            bargap=0.3,
            bargroupgap=0.1,
            hoverlabel=dict(
                bgcolor='#1e293b',
                font_size=12,
                font_family='Inter, sans-serif'
            )
        )
        
        st.plotly_chart(fig_cat, use_container_width=True)
        
        # Summary metrics row
        st.markdown("<br>", unsafe_allow_html=True)
        
        metric_cols = st.columns(5)
        total_plan = category_combined['Period_Plan'].sum()
        total_actuals = category_combined['Actuals'].sum()
        total_pending = category_combined['Pending'].sum()
        total_deals = category_combined['Deals'].sum()
        total_pipeline = total_actuals + total_pending + total_deals
        overall_att = (total_pipeline / total_plan * 100) if total_plan > 0 else 0
        
        with metric_cols[0]:
            st.markdown(f"""
                <div style="text-align: center; padding: 0.75rem; background: rgba(148,163,184,0.1); border-radius: 8px;">
                    <div style="color: #94a3b8; font-size: 0.7rem; text-transform: uppercase;">{period_label} Plan</div>
                    <div style="color: #f1f5f9; font-size: 1.25rem; font-weight: 700;">${total_plan:,.0f}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with metric_cols[1]:
            st.markdown(f"""
                <div style="text-align: center; padding: 0.75rem; background: rgba(16,185,129,0.1); border-radius: 8px; border: 1px solid rgba(16,185,129,0.3);">
                    <div style="color: #10b981; font-size: 0.7rem; text-transform: uppercase;">✓ Invoiced</div>
                    <div style="color: #10b981; font-size: 1.25rem; font-weight: 700;">${total_actuals:,.0f}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with metric_cols[2]:
            st.markdown(f"""
                <div style="text-align: center; padding: 0.75rem; background: rgba(245,158,11,0.1); border-radius: 8px; border: 1px solid rgba(245,158,11,0.3);">
                    <div style="color: #f59e0b; font-size: 0.7rem; text-transform: uppercase;">📋 Pending</div>
                    <div style="color: #f59e0b; font-size: 1.25rem; font-weight: 700;">${total_pending:,.0f}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with metric_cols[3]:
            st.markdown(f"""
                <div style="text-align: center; padding: 0.75rem; background: rgba(139,92,246,0.1); border-radius: 8px; border: 1px solid rgba(139,92,246,0.3);">
                    <div style="color: #8b5cf6; font-size: 0.7rem; text-transform: uppercase;">🎯 Deals</div>
                    <div style="color: #8b5cf6; font-size: 1.25rem; font-weight: 700;">${total_deals:,.0f}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with metric_cols[4]:
            att_color = '#10b981' if overall_att >= 100 else '#f59e0b' if overall_att >= 80 else '#ef4444'
            st.markdown(f"""
                <div style="text-align: center; padding: 0.75rem; background: rgba(99,102,241,0.1); border-radius: 8px; border: 1px solid rgba(99,102,241,0.3);">
                    <div style="color: #6366f1; font-size: 0.7rem; text-transform: uppercase;">Pipeline Attainment</div>
                    <div style="color: {att_color}; font-size: 1.25rem; font-weight: 700;">{overall_att:.1f}%</div>
                </div>
            """, unsafe_allow_html=True)
        
        # Data table
        with st.expander("📋 View Full Category Breakdown Table"):
            display_cat = category_combined.copy()
            display_cat = display_cat.rename(columns={'Period_Plan': f'{period_label} Plan', 'Total Pipeline': 'Total (with Pipeline)'})
            display_cat[f'{period_label} Plan'] = display_cat[f'{period_label} Plan'].apply(lambda x: f"${x:,.0f}")
            display_cat['Actuals'] = display_cat['Actuals'].apply(lambda x: f"${x:,.0f}")
            display_cat['Pending'] = display_cat['Pending'].apply(lambda x: f"${x:,.0f}")
            display_cat['Deals'] = display_cat['Deals'].apply(lambda x: f"${x:,.0f}")
            display_cat['Total (with Pipeline)'] = display_cat['Total (with Pipeline)'].apply(lambda x: f"${x:,.0f}")
            display_cat['Variance'] = display_cat['Variance'].apply(lambda x: f"${x:+,.0f}")
            display_cat['Attainment'] = display_cat['Attainment'].apply(lambda x: f"{x:.1f}%")
            st.dataframe(display_cat[['Category', f'{period_label} Plan', 'Actuals', 'Pending', 'Deals', 'Total (with Pipeline)', 'Variance', 'Attainment']], 
                        use_container_width=True, hide_index=True)
        
        # DEBUG: Show what's in the forecast data
        with st.expander("🔍 DEBUG: Forecast Data Diagnostics"):
            st.markdown("**Period Plan Query Results (Pipeline='Total'):**")
            if not period_plan.empty:
                total_plan = period_plan[period_plan['Pipeline'] == 'Total'].copy()
                st.write(f"Found {len(total_plan)} rows with Pipeline='Total'")
                st.dataframe(total_plan[['Pipeline', 'Category', 'Period_Plan']], hide_index=True)
                
                # Show specific categories
                st.markdown("**Checking specific categories:**")
                for cat in ['Shipping', 'Labels', 'Application', 'Other']:
                    cat_row = total_plan[total_plan['Category'] == cat]
                    if not cat_row.empty:
                        val = cat_row['Period_Plan'].values[0]
                        st.write(f"- **{cat}**: ${val:,.0f}")
                    else:
                        st.error(f"- **{cat}**: ❌ NOT FOUND in forecast!")
            else:
                st.error("period_plan is empty!")
            
            st.markdown("---")
            st.markdown("**Full forecast_df structure:**")
            if 'forecast' in data:
                forecast_df_debug = data['forecast']
                st.write(f"Total rows: {len(forecast_df_debug)}")
                st.write(f"Unique Pipelines: {forecast_df_debug['Pipeline'].unique().tolist()}")
                st.write(f"Unique Categories: {forecast_df_debug['Category'].unique().tolist()}")
                
                # Show the Total pipeline section specifically
                st.markdown("**'Total' Pipeline rows in forecast_df:**")
                total_rows = forecast_df_debug[forecast_df_debug['Pipeline'] == 'Total']
                if not total_rows.empty:
                    cols_to_show = ['Pipeline', 'Category', 'January', 'February', 'March', 'Q1', 'Annual_Total']
                    available_cols = [c for c in cols_to_show if c in total_rows.columns]
                    st.dataframe(total_rows[available_cols], hide_index=True)
                else:
                    st.error("No 'Total' pipeline rows found!")
    else:
        st.info("No category data available")
    
    # ===== COMPREHENSIVE PIPELINE CHART - Plan vs Full Pipeline =====
    st.markdown(f"### 📊 Plan vs. Full Pipeline by Sales Motion ({period_label})")
    st.caption(f"Compare your {period_label} plan against realized revenue plus everything in the pipeline")
    
    # Filter to known pipelines and add plan data
    chart_pipelines = FORECAST_PIPELINES.copy()
    
    if chart_pipelines:
        pipeline_combined = pd.DataFrame({'Pipeline': chart_pipelines})
        
        # Add Period Plan from forecast
        plan_by_pipeline = period_plan[
            (period_plan['Category'] == 'Total') & 
            (period_plan['Pipeline'].isin(chart_pipelines))
        ][['Pipeline', 'Period_Plan']].copy()
        pipeline_combined = pipeline_combined.merge(plan_by_pipeline, on='Pipeline', how='left')
        pipeline_combined['Period_Plan'] = pipeline_combined['Period_Plan'].fillna(0)
        
        if not actuals_by_pipeline.empty:
            pipeline_combined = pipeline_combined.merge(actuals_by_pipeline, on='Pipeline', how='left')
        else:
            pipeline_combined['Actuals'] = 0
            
        if not pending_by_pipeline.empty:
            pipeline_combined = pipeline_combined.merge(pending_by_pipeline, on='Pipeline', how='left')
        else:
            pipeline_combined['Pending'] = 0
            
        if not deals_by_pipeline.empty:
            pipeline_combined = pipeline_combined.merge(deals_by_pipeline, on='Pipeline', how='left')
        else:
            pipeline_combined['Deals'] = 0
        
        pipeline_combined = pipeline_combined.fillna(0)
        pipeline_combined['Total Pipeline'] = pipeline_combined['Actuals'] + pipeline_combined['Pending'] + pipeline_combined['Deals']
        pipeline_combined['Variance'] = pipeline_combined['Total Pipeline'] - pipeline_combined['Period_Plan']
        pipeline_combined['Attainment'] = np.where(
            pipeline_combined['Period_Plan'] > 0,
            (pipeline_combined['Total Pipeline'] / pipeline_combined['Period_Plan'] * 100),
            0
        )
        pipeline_combined = pipeline_combined.sort_values('Period_Plan', ascending=True)  # For horizontal bar
        
        # Get pipeline colors
        pipe_colors = [PIPELINE_COLORS.get(p, '#3b82f6') for p in pipeline_combined['Pipeline']]
        
        # ===== BIG BEAUTIFUL HORIZONTAL CHART =====
        fig_pipe = go.Figure()
        
        # Plan bar (gray background)
        fig_pipe.add_trace(go.Bar(
            name=f'{period_label} Plan',
            y=pipeline_combined['Pipeline'],
            x=pipeline_combined['Period_Plan'],
            orientation='h',
            marker=dict(
                color='rgba(148, 163, 184, 0.25)',
                line=dict(color='rgba(148, 163, 184, 0.5)', width=2)
            ),
            text=[f"${x/1000:.0f}K" if x >= 1000 else f"${x:.0f}" for x in pipeline_combined['Period_Plan']],
            textposition='outside',
            textfont=dict(color='#94a3b8', size=11),
            hovertemplate='<b>%{y}</b><br>Plan: $%{x:,.0f}<extra></extra>',
            offsetgroup=0
        ))
        
        # Actuals (with pipeline-specific colors)
        fig_pipe.add_trace(go.Bar(
            name='✓ Actuals (Invoiced)',
            y=pipeline_combined['Pipeline'],
            x=pipeline_combined['Actuals'],
            orientation='h',
            marker=dict(
                color='#10b981',
                line=dict(color='#059669', width=1)
            ),
            text=[f"${x/1000:.0f}K" if x >= 1000 else f"${x:.0f}" for x in pipeline_combined['Actuals']],
            textposition='inside',
            textfont=dict(color='white', size=10, family='Inter'),
            hovertemplate='<b>%{y}</b><br>Invoiced: $%{x:,.0f}<extra></extra>',
            offsetgroup=1
        ))
        
        # Pending Orders
        fig_pipe.add_trace(go.Bar(
            name='📋 Pending Orders',
            y=pipeline_combined['Pipeline'],
            x=pipeline_combined['Pending'],
            orientation='h',
            marker=dict(
                color='#f59e0b',
                line=dict(color='#d97706', width=1)
            ),
            text=[f"${x/1000:.0f}K" if x >= 1000 else "" for x in pipeline_combined['Pending']],
            textposition='inside',
            textfont=dict(color='white', size=10, family='Inter'),
            hovertemplate='<b>%{y}</b><br>Pending: $%{x:,.0f}<extra></extra>',
            offsetgroup=1
        ))
        
        # HubSpot Deals
        fig_pipe.add_trace(go.Bar(
            name='🎯 HubSpot Deals',
            y=pipeline_combined['Pipeline'],
            x=pipeline_combined['Deals'],
            orientation='h',
            marker=dict(
                color='#8b5cf6',
                line=dict(color='#7c3aed', width=1)
            ),
            text=[f"${x/1000:.0f}K" if x >= 1000 else "" for x in pipeline_combined['Deals']],
            textposition='inside',
            textfont=dict(color='white', size=10, family='Inter'),
            hovertemplate='<b>%{y}</b><br>Deals: $%{x:,.0f}<extra></extra>',
            offsetgroup=1
        ))
        
        # Add attainment % annotations
        for i, row in pipeline_combined.iterrows():
            att = row['Attainment']
            total = row['Total Pipeline']
            color = '#10b981' if att >= 100 else '#f59e0b' if att >= 80 else '#ef4444'
            
            fig_pipe.add_annotation(
                y=row['Pipeline'],
                x=max(row['Period_Plan'], total) + (pipeline_combined['Period_Plan'].max() * 0.08),
                text=f"{att:.0f}%",
                showarrow=False,
                font=dict(color=color, size=12, family='Inter'),
                xanchor='left'
            )
        
        fig_pipe.update_layout(
            barmode='stack',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0', family='Inter, sans-serif'),
            xaxis=dict(
                gridcolor='rgba(148, 163, 184, 0.1)',
                tickformat='$,.0f',
                tickfont=dict(size=10, color='#94a3b8'),
                showline=False,
                zeroline=False
            ),
            yaxis=dict(
                gridcolor='rgba(148, 163, 184, 0.1)',
                tickfont=dict(size=12, color='#e2e8f0'),
                showline=False
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='center',
                x=0.5,
                font=dict(size=11, color='#e2e8f0'),
                bgcolor='rgba(0,0,0,0)'
            ),
            height=400,
            margin=dict(t=60, b=40, l=120, r=80),
            bargap=0.35,
            bargroupgap=0.15,
            hoverlabel=dict(
                bgcolor='#1e293b',
                font_size=12,
                font_family='Inter, sans-serif'
            )
        )
        
        st.plotly_chart(fig_pipe, use_container_width=True)
        
        # Data table
        with st.expander("📋 View Full Pipeline Breakdown Table"):
            display_pipe = pipeline_combined.sort_values('Period_Plan', ascending=False).copy()
            display_pipe = display_pipe.rename(columns={'Period_Plan': f'{period_label} Plan', 'Total Pipeline': 'Total (with Pipeline)'})
            display_pipe[f'{period_label} Plan'] = display_pipe[f'{period_label} Plan'].apply(lambda x: f"${x:,.0f}")
            display_pipe['Actuals'] = display_pipe['Actuals'].apply(lambda x: f"${x:,.0f}")
            display_pipe['Pending'] = display_pipe['Pending'].apply(lambda x: f"${x:,.0f}")
            display_pipe['Deals'] = display_pipe['Deals'].apply(lambda x: f"${x:,.0f}")
            display_pipe['Total (with Pipeline)'] = display_pipe['Total (with Pipeline)'].apply(lambda x: f"${x:,.0f}")
            display_pipe['Variance'] = display_pipe['Variance'].apply(lambda x: f"${x:+,.0f}")
            display_pipe['Attainment'] = display_pipe['Attainment'].apply(lambda x: f"{x:.1f}%")
            st.dataframe(display_pipe[['Pipeline', f'{period_label} Plan', 'Actuals', 'Pending', 'Deals', 'Total (with Pipeline)', 'Variance', 'Attainment']], 
                        use_container_width=True, hide_index=True)
    else:
        st.info("No pipeline data available")
    
    # Summary totals
    st.markdown("### 📈 Summary Totals")
    
    total_actuals = actuals_by_category['Actuals'].sum() if not actuals_by_category.empty else 0
    total_pending = pending_by_category['Pending'].sum() if not pending_by_category.empty else 0
    total_deals = deals_by_category['Deals'].sum() if not deals_by_category.empty else 0
    grand_total = total_actuals + total_pending + total_deals
    
    sum_col1, sum_col2, sum_col3, sum_col4 = st.columns(4)
    
    with sum_col1:
        st.markdown(f"""
            <div class="glass-card" style="border-left: 4px solid #10b981;">
                <div class="metric-label">Actuals (Invoiced)</div>
                <div class="metric-value" style="color: #10b981;">${total_actuals:,.0f}</div>
                <div class="metric-delta neutral">Realized revenue</div>
            </div>
        """, unsafe_allow_html=True)
    
    with sum_col2:
        st.markdown(f"""
            <div class="glass-card" style="border-left: 4px solid #f59e0b;">
                <div class="metric-label">Pending Orders</div>
                <div class="metric-value" style="color: #f59e0b;">${total_pending:,.0f}</div>
                <div class="metric-delta neutral">High confidence</div>
            </div>
        """, unsafe_allow_html=True)
    
    with sum_col3:
        st.markdown(f"""
            <div class="glass-card" style="border-left: 4px solid #8b5cf6;">
                <div class="metric-label">HubSpot Deals</div>
                <div class="metric-value" style="color: #8b5cf6;">${total_deals:,.0f}</div>
                <div class="metric-delta neutral">{len(selected_stages)} stage(s) selected</div>
            </div>
        """, unsafe_allow_html=True)
    
    with sum_col4:
        st.markdown(f"""
            <div class="glass-card" style="border-left: 4px solid #6366f1;">
                <div class="metric-label">Total Pipeline</div>
                <div class="metric-value" style="color: #6366f1;">${grand_total:,.0f}</div>
                <div class="metric-delta neutral">All sources combined</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Show deal stage breakdown if deals exist
    if not deals_df.empty and stage_column and selected_stages:
        with st.expander("📊 HubSpot Deals by Stage"):
            filtered_deals_for_summary = deals_df[deals_df[stage_column].isin(selected_stages)]
            if not filtered_deals_for_summary.empty:
                stage_summary = filtered_deals_for_summary.groupby(stage_column).agg({
                    'Amount': ['sum', 'count']
                }).reset_index()
                stage_summary.columns = ['Stage', 'Total Amount', 'Deal Count']
                stage_summary = stage_summary.sort_values('Total Amount', ascending=False)
                
                # Add confidence indicators
                confidence_map = {
                    'Commit': '🟢 High',
                    'Best Case': '🟡 Medium-High', 
                    'Expect': '🟠 Medium',
                    'Opportunity': '🔴 Variable'
                }
                stage_summary['Confidence'] = stage_summary['Stage'].map(confidence_map).fillna('⚪ Unknown')
                
                # Format for display
                display_stages = stage_summary.copy()
                display_stages['Total Amount'] = display_stages['Total Amount'].apply(lambda x: f"${x:,.0f}")
                display_stages['Deal Count'] = display_stages['Deal Count'].apply(lambda x: f"{int(x):,}")
                
                st.dataframe(display_stages[['Stage', 'Confidence', 'Deal Count', 'Total Amount']], 
                           use_container_width=True, hide_index=True)
    
    # ==========================================================================
    # CLOSE RATE ANALYSIS SECTION
    # ==========================================================================
    st.markdown("""
        <div class="section-header">
            <span class="section-icon">📈</span>
            <span class="section-title">Close Rate Analysis</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Context box
    st.markdown("""
        <div style="background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: 1rem; border-radius: 0 8px 8px 0; margin-bottom: 1.5rem;">
            <strong style="color: #34d399;">📊 What you're seeing:</strong>
            <span style="color: #94a3b8;"> Historical close rate analysis from HubSpot deals. Shows win/loss rates by Close Status to inform probability scoring, breakdown by product category, and time-to-close metrics.</span>
            <br><span style="color: #64748b; font-size: 0.85rem;">Source: Copy of Deals Line Item sheet (HubSpot deal line items)</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Get deals line items data
    deals_line_items_df = data.get('deals_line_items', pd.DataFrame())
    
    if deals_line_items_df.empty:
        st.warning("⚠️ No data found in 'Copy of Deals Line Item' sheet. Close Rate Analysis requires this data source.")
    else:
        # Show info about filtering if applicable
        reorder_filtered = deals_line_items_df.attrs.get('reorder_filtered_deals', 0)
        total_deals_before = deals_line_items_df.attrs.get('total_deals_before_filter', 0)
        gonzalez_filtered = deals_line_items_df.attrs.get('gonzalez_filtered_deals', 0)
        
        filter_messages = []
        if reorder_filtered > 0:
            filter_messages.append(f"**{reorder_filtered:,}** Standard Reorder deals")
        if gonzalez_filtered > 0:
            filter_messages.append(f"**{gonzalez_filtered:,}** Gonzalez deals")
        
        if filter_messages:
            total_filtered = reorder_filtered + gonzalez_filtered
            st.info(f"ℹ️ **Deals excluded from analysis:** {' and '.join(filter_messages)} filtered out to show true sales conversion rates.")
        
        # Calculate metrics
        close_rate_metrics = calculate_close_rate_metrics(deals_line_items_df)
        
        if close_rate_metrics is None:
            st.warning("⚠️ Could not calculate close rate metrics. Check data format.")
        else:
            # Overall Close Rate Summary
            overall = close_rate_metrics['overall']
            
            st.markdown("### 📊 Overall Close Rate Summary")
            
            cr_col1, cr_col2, cr_col3, cr_col4 = st.columns(4)
            
            with cr_col1:
                rate_color = "#10b981" if overall['close_rate_count'] >= 50 else "#f59e0b" if overall['close_rate_count'] >= 30 else "#ef4444"
                st.markdown(f"""
                    <div class="metric-card success">
                        <div class="metric-label">Close Rate (Count)</div>
                        <div class="metric-value" style="color: {rate_color};">{overall['close_rate_count']:.1f}%</div>
                        <div class="metric-delta neutral">{overall['total_won']:,} won / {overall['total_closed']:,} closed</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with cr_col2:
                amount_rate_color = "#10b981" if overall['close_rate_amount'] >= 50 else "#f59e0b" if overall['close_rate_amount'] >= 30 else "#ef4444"
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Close Rate (Amount)</div>
                        <div class="metric-value" style="color: {amount_rate_color};">{overall['close_rate_amount']:.1f}%</div>
                        <div class="metric-delta neutral">${overall['total_won_amount']:,.0f} won</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with cr_col3:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Total Won</div>
                        <div class="metric-value" style="color: #10b981;">{overall['total_won']:,}</div>
                        <div class="metric-delta positive">${overall['total_won_amount']:,.0f}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with cr_col4:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Total Lost</div>
                        <div class="metric-value" style="color: #ef4444;">{overall['total_lost']:,}</div>
                        <div class="metric-delta negative">${overall['total_lost_amount']:,.0f}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            # Close Rate by Close Status (Probability Scoring)
            st.markdown("### 🎯 Close Rate by Close Status (Probability Insights)")
            st.caption("Use these historical close rates to inform your probability scoring for each Close Status.")
            
            by_status = close_rate_metrics['by_close_status']
            
            if by_status:
                status_cols = st.columns(4)
                
                # Define status colors and recommended probability ranges
                status_config = {
                    'Commit': {'color': '#10b981', 'icon': '🟢', 'expected_range': '80-95%'},
                    'Expect': {'color': '#3b82f6', 'icon': '🔵', 'expected_range': '50-70%'},
                    'Best Case': {'color': '#f59e0b', 'icon': '🟡', 'expected_range': '30-50%'},
                    'Opportunity': {'color': '#ef4444', 'icon': '🔴', 'expected_range': '10-30%'}
                }
                
                for idx, status in enumerate(['Commit', 'Expect', 'Best Case', 'Opportunity']):
                    with status_cols[idx]:
                        if status in by_status:
                            data_s = by_status[status]
                            config = status_config.get(status, {'color': '#94a3b8', 'icon': '⚪', 'expected_range': 'N/A'})
                            
                            # Determine if actual rate is in expected range
                            actual_rate = data_s['close_rate_count']
                            
                            st.markdown(f"""
                                <div class="pipeline-card" style="border-left-color: {config['color']};">
                                    <div style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem;">
                                        {config['icon']} {status}
                                    </div>
                                    <div style="font-size: 2rem; font-weight: 700; color: {config['color']};">
                                        {actual_rate:.1f}%
                                    </div>
                                    <div style="color: #64748b; font-size: 0.85rem; margin-top: 0.25rem;">
                                        {data_s['won_deals']} won / {data_s['total_deals']} deals
                                    </div>
                                    <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid rgba(148, 163, 184, 0.1);">
                                        <div style="color: #64748b; font-size: 0.75rem;">
                                            💰 Amount Rate: <strong style="color: #e2e8f0;">{data_s['close_rate_amount']:.1f}%</strong>
                                        </div>
                                        <div style="color: #64748b; font-size: 0.75rem;">
                                            Won: ${data_s['won_amount']:,.0f}
                                        </div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                                <div class="pipeline-card" style="opacity: 0.5;">
                                    <div style="font-size: 0.75rem; color: #94a3b8;">
                                        {status_config.get(status, {}).get('icon', '⚪')} {status}
                                    </div>
                                    <div style="font-size: 1.5rem; color: #475569;">
                                        No Data
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                
                # Summary table
                with st.expander("📋 Detailed Close Status Breakdown"):
                    status_table_data = []
                    for status in ['Commit', 'Expect', 'Best Case', 'Opportunity']:
                        if status in by_status:
                            d = by_status[status]
                            status_table_data.append({
                                'Close Status': status,
                                'Total Deals': d['total_deals'],
                                'Won': d['won_deals'],
                                'Lost': d['lost_deals'],
                                'Close Rate (Count)': f"{d['close_rate_count']:.1f}%",
                                'Total Amount': f"${d['total_amount']:,.0f}",
                                'Won Amount': f"${d['won_amount']:,.0f}",
                                'Close Rate (Amount)': f"{d['close_rate_amount']:.1f}%"
                            })
                    
                    if status_table_data:
                        st.dataframe(pd.DataFrame(status_table_data), use_container_width=True, hide_index=True)
            
            # Days to Close Analysis
            days_stats = close_rate_metrics['days_to_close']
            if days_stats:
                st.markdown("### ⏱️ Time to Close Analysis")
                st.caption("Average time from deal creation to close for won deals.")
                
                dtc_col1, dtc_col2, dtc_col3, dtc_col4 = st.columns(4)
                
                with dtc_col1:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Average Days to Close</div>
                            <div class="metric-value">{days_stats['mean']:.0f}</div>
                            <div class="metric-delta neutral">days</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with dtc_col2:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Median Days</div>
                            <div class="metric-value">{days_stats['median']:.0f}</div>
                            <div class="metric-delta neutral">days</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with dtc_col3:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Fastest Close</div>
                            <div class="metric-value" style="color: #10b981;">{days_stats['min']:.0f}</div>
                            <div class="metric-delta neutral">days</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with dtc_col4:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Longest Close</div>
                            <div class="metric-value" style="color: #f59e0b;">{days_stats['max']:.0f}</div>
                            <div class="metric-delta neutral">days</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Days to close by amount bucket
                days_by_amount = calculate_days_to_close_by_amount_bucket(deals_line_items_df)
                if not days_by_amount.empty:
                    with st.expander("📊 Days to Close by Deal Size"):
                        st.caption("Larger deals often take longer to close. Use this to set realistic close date expectations.")
                        
                        # Create chart
                        fig_days = go.Figure()
                        
                        fig_days.add_trace(go.Bar(
                            x=days_by_amount['Amount Bucket'],
                            y=days_by_amount['Avg Days to Close'],
                            marker=dict(
                                color=['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#ef4444'][:len(days_by_amount)],
                                line=dict(color='rgba(255,255,255,0.2)', width=1)
                            ),
                            text=[f"{d:.0f} days" for d in days_by_amount['Avg Days to Close']],
                            textposition='outside',
                            textfont=dict(color='#e2e8f0', size=12)
                        ))
                        
                        fig_days.update_layout(
                            title=dict(text='Average Days to Close by Deal Size', font=dict(color='#e2e8f0', size=16)),
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#e2e8f0'),
                            xaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)', tickfont=dict(color='#94a3b8')),
                            yaxis=dict(
                                gridcolor='rgba(148, 163, 184, 0.1)', 
                                tickfont=dict(color='#94a3b8'),
                                title='Days'
                            ),
                            height=350,
                            margin=dict(t=60, b=60)
                        )
                        
                        st.plotly_chart(fig_days, use_container_width=True)
                        
                        # Show table
                        display_days = days_by_amount.copy()
                        display_days['Avg Days to Close'] = display_days['Avg Days to Close'].apply(lambda x: f"{x:.0f}")
                        display_days['Median Days'] = display_days['Median Days'].apply(lambda x: f"{x:.0f}")
                        display_days['Min Days'] = display_days['Min Days'].apply(lambda x: f"{x:.0f}")
                        display_days['Max Days'] = display_days['Max Days'].apply(lambda x: f"{x:.0f}")
                        st.dataframe(display_days, use_container_width=True, hide_index=True)
            
            # Close Rate by Product Category
            st.markdown("### 📦 Close Rate by Product Category")
            st.caption("Which product categories have the highest close rates?")
            
            category_rates = calculate_close_rate_by_category(deals_line_items_df)
            
            if not category_rates.empty:
                # Sort by close rate for chart
                chart_data = category_rates.sort_values('Close Rate', ascending=True).tail(10)  # Top 10 categories
                
                fig_cat_rate = go.Figure()
                
                # Color code by close rate
                colors = ['#ef4444' if r < 30 else '#f59e0b' if r < 50 else '#10b981' for r in chart_data['Close Rate']]
                
                fig_cat_rate.add_trace(go.Bar(
                    y=chart_data['Category'],
                    x=chart_data['Close Rate'],
                    orientation='h',
                    marker=dict(color=colors, line=dict(color='rgba(255,255,255,0.2)', width=1)),
                    text=[f"{r:.1f}% ({w}/{t})" for r, w, t in zip(chart_data['Close Rate'], chart_data['Won Deals'], chart_data['Total Deals'])],
                    textposition='outside',
                    textfont=dict(color='#e2e8f0', size=11)
                ))
                
                fig_cat_rate.update_layout(
                    title=dict(text='Close Rate by Product Category', font=dict(color='#e2e8f0', size=16)),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#e2e8f0'),
                    xaxis=dict(
                        gridcolor='rgba(148, 163, 184, 0.1)', 
                        tickfont=dict(color='#94a3b8'),
                        title='Close Rate (%)',
                        range=[0, min(100, chart_data['Close Rate'].max() * 1.2)]
                    ),
                    yaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)', tickfont=dict(color='#94a3b8')),
                    height=400,
                    margin=dict(t=60, b=40, l=150)
                )
                
                st.plotly_chart(fig_cat_rate, use_container_width=True)
                
                # Show full table
                with st.expander("📋 Full Category Breakdown"):
                    display_cat = category_rates.copy()
                    display_cat['Close Rate'] = display_cat['Close Rate'].apply(lambda x: f"{x:.1f}%")
                    display_cat['Total Qty'] = display_cat['Total Qty'].apply(lambda x: f"{x:,.0f}")
                    display_cat['Won Qty'] = display_cat['Won Qty'].apply(lambda x: f"{x:,.0f}")
                    st.dataframe(display_cat, use_container_width=True, hide_index=True)
            else:
                st.info("No category data available for close rate analysis.")
            
            # Close Rate by Pipeline - Full Section
            st.markdown("### 🔄 Close Rate by Pipeline")
            st.caption("Compare close rates across different sales pipelines to understand which motions convert best.")
            
            pipeline_rates = calculate_close_rate_by_pipeline(deals_line_items_df)
            
            if not pipeline_rates.empty:
                # Pipeline metric cards
                pipe_cols = st.columns(len(pipeline_rates))
                
                # Define pipeline colors matching the rest of the app
                pipeline_colors = {
                    'Retention (Existing Product)': '#10b981',
                    'Retention': '#10b981',
                    'Growth Pipeline (Upsell/Cross-sell)': '#3b82f6',
                    'Growth': '#3b82f6',
                    'Acquisition (New Customer)': '#8b5cf6',
                    'Acquisition': '#8b5cf6',
                    'Distributors': '#f59e0b',
                    'E-com': '#06b6d4'
                }
                
                for idx, (_, row) in enumerate(pipeline_rates.iterrows()):
                    pipeline_name = row['Pipeline']
                    close_rate = row['Close Rate (Count)']
                    won_deals = row['Won Deals']
                    total_deals = row['Total Deals']
                    won_amount = row['Won Amount']
                    amount_rate = row['Close Rate (Amount)']
                    
                    # Get color
                    color = pipeline_colors.get(pipeline_name, '#3b82f6')
                    
                    # Determine rate color based on performance
                    rate_color = '#10b981' if close_rate >= 60 else '#f59e0b' if close_rate >= 40 else '#ef4444'
                    
                    with pipe_cols[idx]:
                        st.markdown(f"""
                            <div class="pipeline-card" style="border-left-color: {color}; min-height: 180px;">
                                <div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                    {pipeline_name}
                                </div>
                                <div style="font-size: 2.5rem; font-weight: 700; color: {rate_color};">
                                    {close_rate:.1f}%
                                </div>
                                <div style="color: #64748b; font-size: 0.85rem; margin-top: 0.25rem;">
                                    {won_deals:,} won / {total_deals:,} deals
                                </div>
                                <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid rgba(148, 163, 184, 0.1);">
                                    <div style="color: #64748b; font-size: 0.75rem;">
                                        💰 Amount: <strong style="color: {rate_color};">{amount_rate:.1f}%</strong>
                                    </div>
                                    <div style="color: #10b981; font-size: 0.8rem; font-weight: 600; margin-top: 0.25rem;">
                                        ${won_amount:,.0f}
                                    </div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                
                # Pipeline Close Rate Chart
                st.markdown("<br>", unsafe_allow_html=True)
                
                fig_pipeline = go.Figure()
                
                # Sort for chart display
                chart_pipe_data = pipeline_rates.sort_values('Close Rate (Count)', ascending=True)
                
                # Get colors for each pipeline
                bar_colors = [pipeline_colors.get(p, '#3b82f6') for p in chart_pipe_data['Pipeline']]
                
                # Add won deals bar (stacked)
                fig_pipeline.add_trace(go.Bar(
                    y=chart_pipe_data['Pipeline'],
                    x=chart_pipe_data['Won Deals'],
                    name='Won Deals',
                    orientation='h',
                    marker=dict(color='#10b981', line=dict(color='#059669', width=1)),
                    text=[f"{w:,} won" for w in chart_pipe_data['Won Deals']],
                    textposition='inside',
                    textfont=dict(color='white', size=11),
                    hovertemplate='<b>%{y}</b><br>Won: %{x:,} deals<extra></extra>'
                ))
                
                # Add lost deals bar (stacked)
                fig_pipeline.add_trace(go.Bar(
                    y=chart_pipe_data['Pipeline'],
                    x=chart_pipe_data['Lost Deals'],
                    name='Lost Deals',
                    orientation='h',
                    marker=dict(color='#ef4444', line=dict(color='#dc2626', width=1)),
                    text=[f"{l:,} lost" for l in chart_pipe_data['Lost Deals']],
                    textposition='inside',
                    textfont=dict(color='white', size=11),
                    hovertemplate='<b>%{y}</b><br>Lost: %{x:,} deals<extra></extra>'
                ))
                
                # Add close rate annotation at end of each bar
                for i, row in chart_pipe_data.iterrows():
                    fig_pipeline.add_annotation(
                        y=row['Pipeline'],
                        x=row['Total Deals'] + (chart_pipe_data['Total Deals'].max() * 0.02),
                        text=f"<b>{row['Close Rate (Count)']:.1f}%</b>",
                        showarrow=False,
                        font=dict(
                            color='#10b981' if row['Close Rate (Count)'] >= 60 else '#f59e0b' if row['Close Rate (Count)'] >= 40 else '#ef4444',
                            size=14
                        ),
                        xanchor='left'
                    )
                
                fig_pipeline.update_layout(
                    title=dict(text='Won vs Lost Deals by Pipeline', font=dict(color='#e2e8f0', size=16)),
                    barmode='stack',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#e2e8f0'),
                    xaxis=dict(
                        gridcolor='rgba(148, 163, 184, 0.1)',
                        tickfont=dict(color='#94a3b8'),
                        title='Number of Deals'
                    ),
                    yaxis=dict(
                        gridcolor='rgba(148, 163, 184, 0.1)',
                        tickfont=dict(color='#e2e8f0', size=11)
                    ),
                    legend=dict(
                        orientation='h',
                        yanchor='bottom',
                        y=1.02,
                        xanchor='center',
                        x=0.5,
                        font=dict(color='#e2e8f0')
                    ),
                    height=300,
                    margin=dict(t=60, b=40, l=200, r=80)
                )
                
                st.plotly_chart(fig_pipeline, use_container_width=True)
                
                # Detailed table in expander
                with st.expander("📋 Detailed Pipeline Breakdown"):
                    display_pipe = pipeline_rates.copy()
                    display_pipe['Close Rate (Count)'] = display_pipe['Close Rate (Count)'].apply(lambda x: f"{x:.1f}%")
                    display_pipe['Close Rate (Amount)'] = display_pipe['Close Rate (Amount)'].apply(lambda x: f"{x:.1f}%")
                    display_pipe['Won Amount'] = display_pipe['Won Amount'].apply(lambda x: f"${x:,.0f}")
                    display_pipe['Total Amount'] = display_pipe['Total Amount'].apply(lambda x: f"${x:,.0f}")
                    
                    st.dataframe(display_pipe, use_container_width=True, hide_index=True)
            else:
                st.info("No pipeline data available for close rate analysis.")
            
            # ==========================================================================
            # EXPORT DEALS DATA
            # ==========================================================================
            st.markdown("### 📥 Export Deals Data")
            st.caption("Download the underlying deal data used in the Close Rate Analysis.")
            
            export_col1, export_col2 = st.columns(2)
            
            with export_col1:
                st.markdown("**Export by Filter:**")
                export_type = st.selectbox(
                    "Select export type:",
                    ["All Closed Deals", "By Pipeline", "By Category", "By Close Status"],
                    key="close_rate_export_type"
                )
                
                filter_value = None
                if export_type == "By Pipeline":
                    if not pipeline_rates.empty:
                        pipeline_options = pipeline_rates['Pipeline'].tolist()
                        filter_value = st.selectbox("Select Pipeline:", pipeline_options, key="export_pipeline_select")
                elif export_type == "By Category":
                    # category_rates might not exist if category section was skipped
                    try:
                        if not category_rates.empty:
                            category_options = category_rates['Category'].tolist()
                            filter_value = st.selectbox("Select Category:", category_options, key="export_category_select")
                    except NameError:
                        st.info("Category data not available")
                elif export_type == "By Close Status":
                    filter_value = st.selectbox("Select Close Status:", ['Commit', 'Expect', 'Best Case', 'Opportunity'], key="export_status_select")
            
            with export_col2:
                st.markdown("**Download:**")
                
                # Determine filter parameters
                if export_type == "All Closed Deals":
                    export_df = get_deals_for_export(deals_line_items_df)
                    filename = "all_closed_deals.csv"
                elif export_type == "By Pipeline" and filter_value:
                    export_df = get_deals_for_export(deals_line_items_df, 'pipeline', filter_value)
                    filename = f"deals_pipeline_{filter_value.replace(' ', '_').replace('/', '_')}.csv"
                elif export_type == "By Category" and filter_value:
                    export_df = get_deals_for_export(deals_line_items_df, 'category', filter_value)
                    filename = f"deals_category_{filter_value.replace(' ', '_')}.csv"
                elif export_type == "By Close Status" and filter_value:
                    export_df = get_deals_for_export(deals_line_items_df, 'close_status', filter_value)
                    filename = f"deals_status_{filter_value.replace(' ', '_')}.csv"
                else:
                    export_df = pd.DataFrame()
                    filename = "deals.csv"
                
                if not export_df.empty:
                    st.metric("Deals in Export", f"{len(export_df):,}")
                    
                    # Convert to CSV
                    csv_data = export_df.to_csv(index=False)
                    
                    st.download_button(
                        label=f"📥 Download {export_type}",
                        data=csv_data,
                        file_name=filename,
                        mime="text/csv",
                        key="download_close_rate_deals"
                    )
                else:
                    st.warning("No deals match the selected filter.")
            
            # Show preview of export data
            with st.expander("👀 Preview Export Data"):
                if not export_df.empty:
                    st.write(f"**{len(export_df):,} deals** will be included in the export.")
                    st.dataframe(export_df.head(20), use_container_width=True, hide_index=True)
                    if len(export_df) > 20:
                        st.caption(f"Showing first 20 of {len(export_df):,} deals. Download for full list.")
                else:
                    st.info("Select an export type to preview data.")
            
            # ==========================================================================
            # REVENUE PLANNING & GAP ANALYSIS SECTION
            # ==========================================================================
            st.markdown("### 🎯 Revenue Planning & Gap Analysis")
            st.caption("Use historical close rates to project pipeline revenue and calculate what's needed to hit targets.")
            
            # Get average deal sizes
            avg_deal_sizes = calculate_avg_deal_size_by_pipeline(deals_line_items_df)
            
            # Build close rates dict for pipeline expected revenue calculation
            close_rates_for_calc = {}
            if close_rate_metrics and 'by_close_status' in close_rate_metrics:
                for status, data in close_rate_metrics['by_close_status'].items():
                    close_rates_for_calc[status] = {
                        'close_rate_count': data.get('close_rate_count', 50),
                        'total_deals': data.get('total_deals', 0)
                    }
            
            pipeline_rates_for_calc = {}
            if not pipeline_rates.empty:
                for _, row in pipeline_rates.iterrows():
                    pipeline_rates_for_calc[row['Pipeline']] = {
                        'close_rate': row['Close Rate (Count)'],
                        'total_deals': row['Total Deals']
                    }
            
            # Get current open pipeline deals
            open_deal_statuses = ['Expect', 'Commit', 'Best Case', 'Opportunity']
            open_deals = pd.DataFrame()
            
            if not deals_df.empty:
                stage_col = 'Close Status' if 'Close Status' in deals_df.columns else 'Deal Stage'
                if stage_col in deals_df.columns:
                    open_deals = deals_df[deals_df[stage_col].isin(open_deal_statuses)].copy()
            
            # Calculate expected pipeline revenue
            pipeline_expected = calculate_pipeline_expected_revenue(
                open_deals, 
                close_rates_for_calc, 
                pipeline_rates_for_calc
            )
            
            # Show Average Deal Size metrics
            col1, col2, col3 = st.columns(3)
            
            overall_avg = avg_deal_sizes.get('Overall', {}).get('avg_deal_size', 0)
            overall_median = avg_deal_sizes.get('Overall', {}).get('median_deal_size', 0)
            overall_close_rate = close_rate_metrics['overall']['close_rate_count'] if close_rate_metrics else 50
            
            with col1:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Avg Deal Size (Won)</div>
                        <div class="metric-value">${overall_avg:,.0f}</div>
                        <div class="metric-delta neutral">Median: ${overall_median:,.0f}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Historical Close Rate</div>
                        <div class="metric-value">{overall_close_rate:.1f}%</div>
                        <div class="metric-delta neutral">Used for projections</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Open Pipeline Deals</div>
                        <div class="metric-value">{pipeline_expected['deal_count']:,}</div>
                        <div class="metric-delta neutral">${pipeline_expected['total_pipeline_value']:,.0f} total value</div>
                    </div>
                """, unsafe_allow_html=True)
            
            # Pipeline Expected Revenue Summary
            st.markdown("<br>", unsafe_allow_html=True)
            
            exp_col1, exp_col2, exp_col3 = st.columns(3)
            
            with exp_col1:
                st.markdown(f"""
                    <div class="glass-card" style="border-left: 4px solid #8b5cf6;">
                        <div class="metric-label">Raw Pipeline Value</div>
                        <div class="metric-value" style="color: #8b5cf6;">${pipeline_expected['total_pipeline_value']:,.0f}</div>
                        <div class="metric-delta neutral">If 100% closed</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with exp_col2:
                st.markdown(f"""
                    <div class="glass-card" style="border-left: 4px solid #10b981;">
                        <div class="metric-label">Expected Pipeline Revenue</div>
                        <div class="metric-value" style="color: #10b981;">${pipeline_expected['expected_revenue']:,.0f}</div>
                        <div class="metric-delta neutral">Weighted by close rates</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with exp_col3:
                conversion_pct = (pipeline_expected['expected_revenue'] / pipeline_expected['total_pipeline_value'] * 100) if pipeline_expected['total_pipeline_value'] > 0 else 0
                st.markdown(f"""
                    <div class="glass-card" style="border-left: 4px solid #f59e0b;">
                        <div class="metric-label">Effective Conversion</div>
                        <div class="metric-value" style="color: #f59e0b;">{conversion_pct:.1f}%</div>
                        <div class="metric-delta neutral">Blended pipeline rate</div>
                    </div>
                """, unsafe_allow_html=True)
            
            # Expected Revenue by Close Status breakdown
            if pipeline_expected['by_status']:
                with st.expander("📊 Expected Revenue by Close Status"):
                    status_data = []
                    for status in ['Commit', 'Expect', 'Best Case', 'Opportunity']:
                        if status in pipeline_expected['by_status']:
                            s = pipeline_expected['by_status'][status]
                            status_data.append({
                                'Close Status': status,
                                'Deals': s['deal_count'],
                                'Pipeline Value': f"${s['pipeline_value']:,.0f}",
                                'Applied Rate': f"{s['applied_rate']:.1f}%",
                                'Expected Revenue': f"${s['expected_revenue']:,.0f}"
                            })
                    
                    if status_data:
                        st.dataframe(pd.DataFrame(status_data), use_container_width=True, hide_index=True)
            
            # Gap Analysis Section
            st.markdown("---")
            st.markdown("#### 📉 Gap Analysis & Deals Needed")
            
            # Target Input - can use forecast or manual
            target_col1, target_col2 = st.columns([2, 1])
            
            with target_col1:
                # Get YTD target from forecast if available
                default_target = 0
                if 'forecast' in data and not data['forecast'].empty:
                    forecast_df = data['forecast']
                    total_row = forecast_df[(forecast_df['Pipeline'] == 'Total') & (forecast_df['Category'] == 'Total')]
                    if not total_row.empty and 'Annual_Total' in total_row.columns:
                        default_target = total_row['Annual_Total'].values[0]
                
                revenue_target = st.number_input(
                    "Revenue Target ($)",
                    min_value=0,
                    value=int(default_target),
                    step=100000,
                    format="%d",
                    help="Enter your revenue target. Defaults to 2026 Annual Forecast total if available.",
                    key="gap_revenue_target"
                )
            
            with target_col2:
                # Calculate months remaining in year
                current_month = datetime.now().month
                months_remaining = 12 - current_month + 1
                
                months_input = st.number_input(
                    "Months Remaining",
                    min_value=1,
                    max_value=12,
                    value=months_remaining,
                    help="Months remaining to hit target",
                    key="gap_months_remaining"
                )
            
            # Get current actuals from the selected year
            current_actuals = 0
            if not line_items_df.empty and 'Date' in line_items_df.columns:
                year_actuals = line_items_df[line_items_df['Date'].dt.year == selected_year]
                current_actuals = year_actuals['Amount'].sum() if not year_actuals.empty else 0
            
            # Calculate gap analysis
            gap_analysis = calculate_revenue_gap_analysis(
                revenue_target=revenue_target,
                current_actuals=current_actuals,
                expected_pipeline=pipeline_expected['expected_revenue'],
                avg_deal_size=overall_avg,
                close_rate=overall_close_rate
            )
            
            monthly_needs = calculate_monthly_deals_needed(gap_analysis, months_input)
            
            # Display Gap Analysis Results
            st.markdown("<br>", unsafe_allow_html=True)
            
            gap_col1, gap_col2, gap_col3, gap_col4 = st.columns(4)
            
            with gap_col1:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">YTD Actuals ({selected_year})</div>
                        <div class="metric-value" style="color: #10b981;">${gap_analysis['current_actuals']:,.0f}</div>
                        <div class="metric-delta neutral">{gap_analysis['current_attainment']:.1f}% of target</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with gap_col2:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">+ Expected Pipeline</div>
                        <div class="metric-value" style="color: #8b5cf6;">${gap_analysis['expected_pipeline']:,.0f}</div>
                        <div class="metric-delta neutral">Probability-weighted</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with gap_col3:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">= Projected Total</div>
                        <div class="metric-value" style="color: #3b82f6;">${gap_analysis['projected_total']:,.0f}</div>
                        <div class="metric-delta neutral">{gap_analysis['projected_attainment']:.1f}% of target</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with gap_col4:
                gap_color = "#10b981" if gap_analysis['on_track'] else "#ef4444"
                gap_sign = "+" if gap_analysis['revenue_gap'] < 0 else "-"
                gap_label = "Surplus" if gap_analysis['on_track'] else "Gap"
                st.markdown(f"""
                    <div class="metric-card {'success' if gap_analysis['on_track'] else 'danger'}">
                        <div class="metric-label">Revenue {gap_label}</div>
                        <div class="metric-value" style="color: {gap_color};">${abs(gap_analysis['revenue_gap']):,.0f}</div>
                        <div class="metric-delta {'positive' if gap_analysis['on_track'] else 'negative'}">{'On Track! 🎉' if gap_analysis['on_track'] else 'Need to close gap'}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            # Deals/Opportunities Needed
            if not gap_analysis['on_track'] and gap_analysis['revenue_gap'] > 0:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### 🔢 What's Needed to Close the Gap")
                
                need_col1, need_col2, need_col3 = st.columns(3)
                
                with need_col1:
                    st.markdown(f"""
                        <div class="glass-card" style="border-left: 4px solid #ef4444; background: rgba(239, 68, 68, 0.1);">
                            <div style="color: #f87171; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px;">Deals Needed (100% Win)</div>
                            <div style="font-size: 2.5rem; font-weight: 700; color: #fca5a5;">{gap_analysis['deals_needed']:.0f}</div>
                            <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 0.5rem;">
                                {monthly_needs['deals_per_month']:.1f} per month
                            </div>
                            <div style="color: #64748b; font-size: 0.75rem;">
                                Formula: Gap ÷ Avg Deal Size
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with need_col2:
                    st.markdown(f"""
                        <div class="glass-card" style="border-left: 4px solid #f59e0b; background: rgba(245, 158, 11, 0.1);">
                            <div style="color: #fbbf24; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px;">Opportunities Needed</div>
                            <div style="font-size: 2.5rem; font-weight: 700; color: #fcd34d;">{gap_analysis['opportunities_needed']:.0f}</div>
                            <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 0.5rem;">
                                {monthly_needs['opportunities_per_month']:.1f} per month
                            </div>
                            <div style="color: #64748b; font-size: 0.75rem;">
                                Formula: Gap ÷ (Close Rate × Avg Deal Size)
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with need_col3:
                    st.markdown(f"""
                        <div class="glass-card" style="border-left: 4px solid #6366f1; background: rgba(99, 102, 241, 0.1);">
                            <div style="color: #a5b4fc; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px;">Monthly Revenue Needed</div>
                            <div style="font-size: 2.5rem; font-weight: 700; color: #c7d2fe;">${monthly_needs['revenue_per_month']:,.0f}</div>
                            <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 0.5rem;">
                                Over {months_input} months
                            </div>
                            <div style="color: #64748b; font-size: 0.75rem;">
                                To close ${gap_analysis['revenue_gap']:,.0f} gap
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Assumptions callout
                st.markdown(f"""
                    <div style="background: rgba(148, 163, 184, 0.1); border-radius: 8px; padding: 1rem; margin-top: 1rem;">
                        <div style="color: #94a3b8; font-size: 0.85rem;">
                            <strong>📊 Assumptions used:</strong>
                            Avg Deal Size = <strong>${overall_avg:,.0f}</strong> | 
                            Close Rate = <strong>{overall_close_rate:.1f}%</strong> | 
                            Based on historical won deals
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            elif gap_analysis['on_track']:
                st.markdown(f"""
                    <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 1.5rem; margin-top: 1rem; text-align: center;">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎉</div>
                        <div style="color: #34d399; font-size: 1.25rem; font-weight: 600;">On Track to Exceed Target!</div>
                        <div style="color: #94a3b8; margin-top: 0.5rem;">
                            Projected ${gap_analysis['projected_total']:,.0f} vs Target ${revenue_target:,.0f}
                            <br>
                            <span style="color: #10b981; font-weight: 600;">Surplus: ${abs(gap_analysis['revenue_gap']):,.0f}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            # Avg Deal Size by Pipeline breakdown
            if avg_deal_sizes:
                with st.expander("📊 Average Deal Size by Pipeline"):
                    deal_size_data = []
                    for pipeline, metrics in avg_deal_sizes.items():
                        if pipeline != 'Overall' and isinstance(metrics, dict):
                            deal_size_data.append({
                                'Pipeline': pipeline,
                                'Avg Deal Size': f"${metrics['avg_deal_size']:,.0f}",
                                'Median Deal Size': f"${metrics['median_deal_size']:,.0f}",
                                'Won Deals': metrics['total_deals'],
                                'Total Revenue': f"${metrics['total_revenue']:,.0f}"
                            })
                    
                    if deal_size_data:
                        st.dataframe(pd.DataFrame(deal_size_data), use_container_width=True, hide_index=True)
            
            # Raw Data Explorer
            with st.expander("🔍 Explore Raw Deals Data"):
                st.caption("View the underlying deal line item data used for this analysis.")
                
                # Show column info
                st.markdown("**Available Columns:**")
                st.write(list(deals_line_items_df.columns))
                
                # Filters
                filter_col1, filter_col2 = st.columns(2)
                
                with filter_col1:
                    show_won = st.checkbox("Show Won Deals", value=True, key="cr_show_won")
                    show_lost = st.checkbox("Show Lost Deals", value=True, key="cr_show_lost")
                
                with filter_col2:
                    if 'Close Status' in deals_line_items_df.columns:
                        available_statuses = deals_line_items_df['Close Status'].dropna().unique().tolist()
                        selected_statuses = st.multiselect(
                            "Filter by Close Status",
                            options=available_statuses,
                            default=available_statuses,
                            key="cr_status_filter"
                        )
                    else:
                        selected_statuses = None
                
                # Apply filters
                filtered_df = deals_line_items_df.copy()
                
                if not show_won:
                    filtered_df = filtered_df[filtered_df['Is_Won'] != True]
                if not show_lost:
                    filtered_df = filtered_df[filtered_df['Is_Lost'] != True]
                
                if selected_statuses and 'Close Status' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['Close Status'].isin(selected_statuses)]
                
                # Select columns to display
                display_columns = ['Deal Name', 'Company Name', 'Amount', 'Close Status', 'Deal Stage', 
                                  'Is_Won', 'Is_Lost', 'Days_To_Close', 'Product Category', 'SKU']
                available_display_cols = [c for c in display_columns if c in filtered_df.columns]
                
                if available_display_cols:
                    st.dataframe(
                        filtered_df[available_display_cols].head(100),
                        use_container_width=True,
                        hide_index=True
                    )
                    st.caption(f"Showing {min(100, len(filtered_df)):,} of {len(filtered_df):,} records")
                else:
                    st.dataframe(filtered_df.head(100), use_container_width=True, hide_index=True)
    
    # Data Quality Check
    st.markdown("""
        <div class="section-header">
            <span class="section-icon">🔍</span>
            <span class="section-title">Data Quality Check</span>
        </div>
    """, unsafe_allow_html=True)
    
    with st.expander("View Diagnostics", expanded=False):
        # Category Diagnostics
        st.markdown("### 📦 Category Diagnostics")
        
        if not line_items_df.empty:
            cat_diag_col1, cat_diag_col2 = st.columns(2)
            
            with cat_diag_col1:
                st.markdown("**Calyx Columns Found:**")
                calyx_cols = [c for c in line_items_df.columns if 'calyx' in c.lower()]
                if calyx_cols:
                    for col in calyx_cols:
                        unique_vals = line_items_df[col].dropna().unique()[:10].tolist()
                        st.write(f"• `{col}`: {unique_vals}")
                else:
                    st.error("❌ No Calyx columns found! Columns available:")
                    st.write(list(line_items_df.columns))
            
            with cat_diag_col2:
                st.markdown("**Category Distribution:**")
                if 'Product Category' in line_items_df.columns:
                    cat_dist = line_items_df.groupby('Product Category')['Amount'].agg(['count', 'sum']).reset_index()
                    cat_dist.columns = ['Category', 'Count', 'Amount']
                    cat_dist['Amount'] = cat_dist['Amount'].apply(lambda x: f"${x:,.0f}")
                    st.dataframe(cat_dist, hide_index=True)
                else:
                    st.error("❌ No 'Product Category' column found!")
                
                if 'Forecast Category' in line_items_df.columns:
                    st.markdown("**Forecast Category Distribution:**")
                    fc_dist = line_items_df.groupby('Forecast Category')['Amount'].agg(['count', 'sum']).reset_index()
                    fc_dist.columns = ['Forecast Category', 'Count', 'Amount']
                    fc_dist['Amount'] = fc_dist['Amount'].apply(lambda x: f"${x:,.0f}")
                    st.dataframe(fc_dist, hide_index=True)
        
        st.markdown("---")
        st.markdown("### 🔗 Invoice Line Item ↔ Invoices Join Diagnostics")
        
        # Check the join between Invoice Line Item and _NS_Invoices_Data
        invoices_df = data.get('invoices', pd.DataFrame())
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Invoice Line Item**")
            if not line_items_df.empty:
                st.write(f"Total rows: {len(line_items_df):,}")
                st.write(f"Columns: {list(line_items_df.columns)[:10]}...")
                
                # Check Document Number column
                if 'Document Number' in line_items_df.columns:
                    sample_doc_nums = line_items_df['Document Number'].dropna().head(5).tolist()
                    st.write(f"Sample Document Numbers: {sample_doc_nums}")
                else:
                    st.error("❌ No 'Document Number' column found!")
                    # Show all columns to find the right one
                    st.write(f"Available columns: {list(line_items_df.columns)}")
            else:
                st.error("❌ Invoice Line Item is empty!")
        
        with col2:
            st.markdown("**_NS_Invoices_Data**")
            if not invoices_df.empty:
                st.write(f"Total rows: {len(invoices_df):,}")
                st.write(f"Columns: {list(invoices_df.columns)[:10]}...")
                
                # Check Document Number column
                if 'Document Number' in invoices_df.columns:
                    sample_doc_nums = invoices_df['Document Number'].dropna().head(5).tolist()
                    st.write(f"Sample Document Numbers: {sample_doc_nums}")
                else:
                    st.error("❌ No 'Document Number' column found!")
                    st.write(f"Available columns: {list(invoices_df.columns)}")
                
                # Check HubSpot Pipeline column
                pipeline_col = None
                for col in invoices_df.columns:
                    if 'hubspot' in col.lower() and 'pipeline' in col.lower():
                        pipeline_col = col
                        break
                if pipeline_col:
                    st.write(f"✅ Found pipeline column: '{pipeline_col}'")
                    sample_pipelines = invoices_df[pipeline_col].dropna().unique()[:5].tolist()
                    st.write(f"Sample pipeline values: {sample_pipelines}")
                else:
                    st.error("❌ No HubSpot Pipeline column found!")
            else:
                st.error("❌ _NS_Invoices_Data is empty!")
        
        # Test the actual join
        st.markdown("---")
        st.markdown("### 🧪 Join Test Results")
        
        if not line_items_df.empty and not invoices_df.empty:
            if 'Document Number' in line_items_df.columns and 'Document Number' in invoices_df.columns:
                # Get unique doc numbers from each
                line_item_docs = set(line_items_df['Document Number'].dropna().astype(str).str.strip().unique())
                invoice_docs = set(invoices_df['Document Number'].dropna().astype(str).str.strip().unique())
                
                # Find overlap
                matching_docs = line_item_docs.intersection(invoice_docs)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Line Item Doc #s", f"{len(line_item_docs):,}")
                with col2:
                    st.metric("Invoice Doc #s", f"{len(invoice_docs):,}")
                with col3:
                    st.metric("Matching Doc #s", f"{len(matching_docs):,}")
                
                if len(matching_docs) == 0:
                    st.error("❌ NO MATCHING DOCUMENT NUMBERS! This is the problem.")
                    st.write("**Sample Line Item Doc #s:**", list(line_item_docs)[:5])
                    st.write("**Sample Invoice Doc #s:**", list(invoice_docs)[:5])
                elif len(matching_docs) < len(line_item_docs) * 0.5:
                    st.warning(f"⚠️ Only {len(matching_docs)/len(line_item_docs)*100:.1f}% of line items match to invoices")
                else:
                    st.success(f"✅ {len(matching_docs)/len(line_item_docs)*100:.1f}% of line items match to invoices")
                
                # Check Forecast Pipeline assignment
                if 'Forecast Pipeline' in line_items_df.columns:
                    pipeline_assigned = line_items_df['Forecast Pipeline'].notna().sum()
                    st.metric("Line Items with Pipeline Assigned", f"{pipeline_assigned:,} / {len(line_items_df):,}")
        
        st.markdown("---")
        st.markdown("### Invoice Line Item Diagnostics")
        
        if not line_items_df.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Line Items", f"{len(line_items_df):,}")
            
            with col2:
                total_revenue = line_items_df['Amount'].sum() if 'Amount' in line_items_df.columns else 0
                st.metric("Total Revenue (All Time)", f"${total_revenue:,.0f}")
            
            with col3:
                if 'Date' in line_items_df.columns:
                    valid_dates = line_items_df['Date'].dropna()
                    if len(valid_dates) > 0:
                        min_date = valid_dates.min()
                        max_date = valid_dates.max()
                        st.metric("Date Range", f"{min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
                    else:
                        st.metric("Date Range", "No valid dates")
                else:
                    st.metric("Date Range", "No Date column found")
            
            # Show year breakdown
            st.markdown("**Revenue by Year:**")
            if 'Date' in line_items_df.columns:
                line_items_df['Year'] = line_items_df['Date'].dt.year
                year_breakdown = line_items_df.groupby('Year')['Amount'].sum().reset_index()
                year_breakdown.columns = ['Year', 'Revenue']
                year_breakdown = year_breakdown.sort_values('Year', ascending=False)
                year_breakdown['Revenue'] = year_breakdown['Revenue'].apply(lambda x: f"${x:,.0f}")
                st.dataframe(year_breakdown, use_container_width=True, hide_index=True)
                
                # Show count of 2026 records specifically
                records_2026 = line_items_df[line_items_df['Year'] == 2026]
                records_2025 = line_items_df[line_items_df['Year'] == 2025]
                st.info(f"📊 **2026 Records:** {len(records_2026):,} line items | **2025 Records:** {len(records_2025):,} line items")
            else:
                st.warning("⚠️ No 'Date' column found in Invoice Line Items")
        else:
            st.error("❌ Invoice Line Item data is empty!")
        
        st.markdown("---")
        st.markdown("**Pipeline Coverage in Actuals**")
        if not line_items_df.empty and 'Forecast Pipeline' in line_items_df.columns:
            # Filter to selected year for pipeline coverage
            year_filtered = line_items_df[line_items_df['Date'].dt.year == selected_year] if 'Date' in line_items_df.columns else line_items_df
            
            pipeline_coverage = year_filtered.groupby('Forecast Pipeline')['Amount'].sum().reset_index()
            pipeline_coverage.columns = ['Pipeline', 'Revenue']
            pipeline_coverage = pipeline_coverage.sort_values('Revenue', ascending=False)
            pipeline_coverage['Revenue'] = pipeline_coverage['Revenue'].apply(lambda x: f"${x:,.0f}")
            st.dataframe(pipeline_coverage, use_container_width=True, hide_index=True)
            
            unmapped = year_filtered[year_filtered['Forecast Pipeline'].isna()]['Amount'].sum()
            if unmapped > 0:
                st.warning(f"⚠️ ${unmapped:,.0f} in {selected_year} revenue has no pipeline mapping (invoices not linked to HubSpot deals)")
        
        st.markdown("**Category Coverage in Actuals**")
        if not line_items_df.empty and 'Forecast Category' in line_items_df.columns:
            year_filtered = line_items_df[line_items_df['Date'].dt.year == selected_year] if 'Date' in line_items_df.columns else line_items_df
            
            category_coverage = year_filtered.groupby('Forecast Category')['Amount'].sum().reset_index()
            category_coverage.columns = ['Category', 'Revenue']
            category_coverage = category_coverage.sort_values('Revenue', ascending=False)
            category_coverage['Revenue'] = category_coverage['Revenue'].apply(lambda x: f"${x:,.0f}")
            st.dataframe(category_coverage, use_container_width=True, hide_index=True)


# ========== ENTRY POINT ==========
if __name__ == "__main__":
    st.set_page_config(
        page_title="2026 Annual Goal Tracker",
        page_icon="🎯",
        layout="wide"
    )
    render_yearly_planning_2026()
