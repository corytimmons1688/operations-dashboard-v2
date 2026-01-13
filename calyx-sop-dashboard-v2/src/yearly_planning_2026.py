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

# ========== CONFIGURATION ==========
DEFAULT_SPREADSHEET_ID = "15JhBZ_7aHHZA1W1qsoC2163borL6RYjk0xTDWPmWPfA"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
CACHE_VERSION = "v1_qbr_generator"


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
    
    # Load HubSpot Deals (A:X to include Company Name)
    deals_df = load_google_sheets_data("All Reps All Pipelines", "A:X", version=CACHE_VERSION)
    
    # =========================================================================
    # PROCESS SALES ORDERS
    # Columns: A=Internal ID, B=SO Number, C=Status, D=Customer, E=Customer External ID,
    # F=Sales Rep, G=PI||CSM, H=Amount, I=Order Start Date, J=Pending Fulfillment Date,
    # K=Actual Ship Date, L=Customer Promise Last Date to Ship, M=Projected Date,
    # N=Do Not Ship Before, O=Memo, P=Created By, Q=Terms, R=Order Type, S=Quote,
    # T=Shipping State/Province, U=Amount (Shipping), V=Amount (Tax), W=HubSpot Pipeline,
    # X=Sales Management Approved Date, Y=Customer's PO Number, Z=Sales Approved Date,
    # AA=Name, AB=Calyx|External Order, AC=Pending Approval Date, AD=Corrected Customer Name,
    # AE=Rep Master, AF=Updated Status
    # =========================================================================
    if not sales_orders_df.empty:
        col_names = sales_orders_df.columns.tolist()
        
        rename_dict = {}
        if len(col_names) > 0: rename_dict[col_names[0]] = 'Internal ID'
        if len(col_names) > 1: rename_dict[col_names[1]] = 'SO Number'
        if len(col_names) > 2: rename_dict[col_names[2]] = 'Status'
        if len(col_names) > 3: rename_dict[col_names[3]] = 'Customer'
        if len(col_names) > 7: rename_dict[col_names[7]] = 'Amount'
        if len(col_names) > 8: rename_dict[col_names[8]] = 'Order Start Date'
        if len(col_names) > 10: rename_dict[col_names[10]] = 'Actual Ship Date'
        if len(col_names) > 11: rename_dict[col_names[11]] = 'Customer Promise Date'
        if len(col_names) > 12: rename_dict[col_names[12]] = 'Projected Date'
        if len(col_names) > 17: rename_dict[col_names[17]] = 'Order Type'
        if len(col_names) > 29: rename_dict[col_names[29]] = 'Corrected Customer Name'
        if len(col_names) > 30: rename_dict[col_names[30]] = 'Rep Master'
        if len(col_names) > 31: rename_dict[col_names[31]] = 'Updated Status'
        
        sales_orders_df = sales_orders_df.rename(columns=rename_dict)
        
        # Remove duplicate columns
        if sales_orders_df.columns.duplicated().any():
            sales_orders_df = sales_orders_df.loc[:, ~sales_orders_df.columns.duplicated()]
        
        # Clean data
        if 'Amount' in sales_orders_df.columns:
            sales_orders_df['Amount'] = sales_orders_df['Amount'].apply(clean_numeric)
        if 'Order Start Date' in sales_orders_df.columns:
            sales_orders_df['Order Start Date'] = pd.to_datetime(sales_orders_df['Order Start Date'], errors='coerce')
        if 'Actual Ship Date' in sales_orders_df.columns:
            sales_orders_df['Actual Ship Date'] = pd.to_datetime(sales_orders_df['Actual Ship Date'], errors='coerce')
        if 'Customer Promise Date' in sales_orders_df.columns:
            sales_orders_df['Customer Promise Date'] = pd.to_datetime(sales_orders_df['Customer Promise Date'], errors='coerce')
        
        # Clean text fields
        for col in ['Corrected Customer Name', 'Rep Master', 'Updated Status', 'Order Type', 'Status']:
            if col in sales_orders_df.columns:
                sales_orders_df[col] = sales_orders_df[col].astype(str).str.strip()
    
    # =========================================================================
    # PROCESS INVOICES
    # Columns: A=Document Number, B=Status, C=Date, D=Due Date, E=Created From,
    # F=Created By, G=Customer, H=Account, I=Period, J=Department,
    # K=Amount (Transaction Total), L=Amount Remaining, M=CSM, N=Date Closed,
    # O=Sales Rep, P=External ID, Q=Amount (Shipping), R=Amount (Tax),
    # S=HubSpot Pipeline, T=Corrected Customer, U=Rep Master
    # =========================================================================
    if not invoices_df.empty:
        col_names = invoices_df.columns.tolist()
        
        rename_dict = {}
        if len(col_names) > 0: rename_dict[col_names[0]] = 'Document Number'
        if len(col_names) > 1: rename_dict[col_names[1]] = 'Status'
        if len(col_names) > 2: rename_dict[col_names[2]] = 'Date'
        if len(col_names) > 3: rename_dict[col_names[3]] = 'Due Date'
        if len(col_names) > 4: rename_dict[col_names[4]] = 'Created From'
        if len(col_names) > 6: rename_dict[col_names[6]] = 'Customer'
        if len(col_names) > 8: rename_dict[col_names[8]] = 'Period'
        if len(col_names) > 10: rename_dict[col_names[10]] = 'Amount'
        if len(col_names) > 11: rename_dict[col_names[11]] = 'Amount Remaining'
        if len(col_names) > 19: rename_dict[col_names[19]] = 'Corrected Customer'
        if len(col_names) > 20: rename_dict[col_names[20]] = 'Rep Master'
        
        invoices_df = invoices_df.rename(columns=rename_dict)
        
        # Remove duplicate columns
        if invoices_df.columns.duplicated().any():
            invoices_df = invoices_df.loc[:, ~invoices_df.columns.duplicated()]
        
        # Clean data
        if 'Amount' in invoices_df.columns:
            invoices_df['Amount'] = invoices_df['Amount'].apply(clean_numeric)
        if 'Amount Remaining' in invoices_df.columns:
            invoices_df['Amount Remaining'] = invoices_df['Amount Remaining'].apply(clean_numeric)
        if 'Date' in invoices_df.columns:
            invoices_df['Date'] = pd.to_datetime(invoices_df['Date'], errors='coerce')
        if 'Due Date' in invoices_df.columns:
            invoices_df['Due Date'] = pd.to_datetime(invoices_df['Due Date'], errors='coerce')
        
        # Clean text fields
        for col in ['Corrected Customer', 'Rep Master', 'Status']:
            if col in invoices_df.columns:
                invoices_df[col] = invoices_df[col].astype(str).str.strip()
        
        # Clean Created From to extract SO Number
        if 'Created From' in invoices_df.columns:
            invoices_df['SO Number'] = invoices_df['Created From'].astype(str).str.replace('Sales Order #', '', regex=False).str.strip()
    
    # =========================================================================
    # PROCESS HUBSPOT DEALS
    # Columns: A=Record ID, B=Deal Name, C=Deal Stage, D=Close Date,
    # E=Deal Owner First Name, F=Deal Owner Last Name, G=Amount, H=Close Status,
    # I=Pipeline, J=Create Date, K=Deal Type, L=Netsuite SO#, M=Netsuite SO Link,
    # N=New Design SKU, O=SKU, P=Netsuite Sales Order Number,
    # Q=Primary Associated Company, R=Average Leadtime, S=Pending Approval Date,
    # T=Quarter, U=Deal Stage & Close Status, V=Probability, W=Probability Rev,
    # X=Company Name
    # =========================================================================
    if not deals_df.empty:
        col_names = deals_df.columns.tolist()
        
        rename_dict = {}
        if len(col_names) > 0: rename_dict[col_names[0]] = 'Record ID'
        if len(col_names) > 1: rename_dict[col_names[1]] = 'Deal Name'
        if len(col_names) > 2: rename_dict[col_names[2]] = 'Deal Stage'
        if len(col_names) > 3: rename_dict[col_names[3]] = 'Close Date'
        if len(col_names) > 4: rename_dict[col_names[4]] = 'Deal Owner First Name'
        if len(col_names) > 5: rename_dict[col_names[5]] = 'Deal Owner Last Name'
        if len(col_names) > 6: rename_dict[col_names[6]] = 'Amount'
        if len(col_names) > 7: rename_dict[col_names[7]] = 'Close Status'
        if len(col_names) > 8: rename_dict[col_names[8]] = 'Pipeline'
        if len(col_names) > 10: rename_dict[col_names[10]] = 'Deal Type'
        if len(col_names) > 16: rename_dict[col_names[16]] = 'Primary Associated Company'
        if len(col_names) > 18: rename_dict[col_names[18]] = 'Pending Approval Date'
        if len(col_names) > 19: rename_dict[col_names[19]] = 'Quarter'
        if len(col_names) > 21: rename_dict[col_names[21]] = 'Probability'
        if len(col_names) > 22: rename_dict[col_names[22]] = 'Probability Rev'
        if len(col_names) > 23: rename_dict[col_names[23]] = 'Company Name'
        
        deals_df = deals_df.rename(columns=rename_dict)
        
        # Remove duplicate columns
        if deals_df.columns.duplicated().any():
            deals_df = deals_df.loc[:, ~deals_df.columns.duplicated()]
        
        # Create Deal Owner by combining First Name + Last Name
        if 'Deal Owner First Name' in deals_df.columns and 'Deal Owner Last Name' in deals_df.columns:
            deals_df['Deal Owner'] = (
                deals_df['Deal Owner First Name'].fillna('').astype(str).str.strip() + ' ' + 
                deals_df['Deal Owner Last Name'].fillna('').astype(str).str.strip()
            ).str.strip()
        
        # Clean data
        if 'Amount' in deals_df.columns:
            deals_df['Amount'] = deals_df['Amount'].apply(clean_numeric)
        if 'Probability Rev' in deals_df.columns:
            deals_df['Probability Rev'] = deals_df['Probability Rev'].apply(clean_numeric)
        else:
            deals_df['Probability Rev'] = deals_df.get('Amount', 0)
        if 'Close Date' in deals_df.columns:
            deals_df['Close Date'] = pd.to_datetime(deals_df['Close Date'], errors='coerce')
        if 'Pending Approval Date' in deals_df.columns:
            deals_df['Pending Approval Date'] = pd.to_datetime(deals_df['Pending Approval Date'], errors='coerce')
        
        # Clean text fields - strip whitespace AND newlines
        for col in ['Deal Owner', 'Deal Name', 'Close Status', 'Company Name']:
            if col in deals_df.columns:
                deals_df[col] = deals_df[col].astype(str).str.strip().str.replace('\n', '', regex=False).str.replace('\r', '', regex=False)
    
    return sales_orders_df, invoices_df, deals_df


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
    with st.expander("📋 View Order Details"):
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
    
    # Filter to open invoices only
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
    
    # Filter to paid/open invoices (exclude voided, etc.)
    valid_invoices = customer_invoices[
        customer_invoices['Status'].isin(['Paid in Full', 'Open'])
    ].copy()
    
    if valid_invoices.empty:
        st.info("No revenue data available.")
        return
    
    # Get current year
    current_year = datetime.now().year
    
    # Calculate total and by year
    total_revenue = valid_invoices['Amount'].sum()
    total_invoice_count = len(valid_invoices)
    
    # Year breakdown
    valid_invoices['Year'] = valid_invoices['Date'].dt.year
    yearly_revenue = valid_invoices.groupby('Year').agg({
        'Amount': 'sum',
        'Document Number': 'count'
    }).reset_index()
    yearly_revenue.columns = ['Year', 'Revenue', 'Invoice Count']
    yearly_revenue = yearly_revenue.sort_values('Year', ascending=False)
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Lifetime Revenue", f"${total_revenue:,.0f}")
    with col2:
        st.metric("Total Invoices", total_invoice_count)
    with col3:
        avg_invoice = total_revenue / total_invoice_count if total_invoice_count > 0 else 0
        st.metric("Avg Invoice Size", f"${avg_invoice:,.0f}")
    
    # Year-by-year breakdown
    st.markdown("**Revenue by Year:**")
    display_yearly = yearly_revenue.copy()
    display_yearly['Revenue'] = display_yearly['Revenue'].apply(lambda x: f"${x:,.0f}")
    st.dataframe(display_yearly, use_container_width=True, hide_index=True)
    
    # Monthly breakdown for current year and previous year
    recent_invoices = valid_invoices[valid_invoices['Year'] >= current_year - 1].copy()
    if not recent_invoices.empty:
        recent_invoices['Month'] = recent_invoices['Date'].dt.to_period('M')
        monthly_revenue = recent_invoices.groupby('Month')['Amount'].sum().reset_index()
        monthly_revenue['Month'] = monthly_revenue['Month'].astype(str)
        
        if len(monthly_revenue) > 1:
            fig = px.bar(monthly_revenue, x='Month', y='Amount',
                         title=f'Monthly Revenue Trend ({current_year-1}-{current_year})',
                         labels={'Amount': 'Revenue', 'Month': 'Month'})
            fig.update_traces(marker_color='#3b82f6')
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#e2e8f0'
            )
            st.plotly_chart(fig, use_container_width=True)


def render_on_time_section(customer_orders):
    """Section 4: On-Time Shipment Performance"""
    st.markdown("### ⏱️ On-Time Shipment Performance")
    
    if customer_orders.empty:
        st.info("No order data found for this customer.")
        return
    
    # Filter to completed orders (Billed or Closed) with valid dates
    completed_orders = customer_orders[
        (customer_orders['Status'].isin(['Billed', 'Closed'])) &
        (customer_orders['Actual Ship Date'].notna()) &
        (customer_orders['Customer Promise Date'].notna())
    ].copy()
    
    if completed_orders.empty:
        st.info("No completed orders with ship date data available.")
        return
    
    # Calculate on-time status
    completed_orders['Days Variance'] = (completed_orders['Actual Ship Date'] - completed_orders['Customer Promise Date']).dt.days
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
        fig = px.histogram(completed_orders, x='Days Variance', nbins=20,
                           title='Ship Date Variance Distribution',
                           labels={'Days Variance': 'Days (Negative = Early, Positive = Late)'})
        fig.add_vline(x=0, line_dash="dash", line_color="green", annotation_text="On Time")
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#e2e8f0'
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
        # Pie chart
        fig = px.pie(type_mix.reset_index(), values='Total Value', names='Order Type',
                     title='Revenue by Order Type')
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#e2e8f0'
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
    amount_mode = st.radio(
        "Amount Display:",
        ["Raw Forecast", "Probability-Adjusted"],
        horizontal=True,
        key="pipeline_amount_mode"
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


# ========== MAIN RENDER FUNCTION ==========

def render_yearly_planning_2026():
    """Main entry point for QBR Generator"""
    
    st.title("📋 QBR Generator")
    st.caption("Generate Quarterly Business Review reports for customer meetings")
    
    # Load data
    with st.spinner("Loading data..."):
        sales_orders_df, invoices_df, deals_df = load_qbr_data()
    
    # Check if data loaded
    if sales_orders_df.empty and invoices_df.empty:
        st.error("❌ Unable to load data. Please check your Google Sheets connection.")
        return
    
    # Debug info in expander
    with st.expander("🔍 Debug: Data Loading Status"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Sales Orders:** {len(sales_orders_df)} rows")
            if not sales_orders_df.empty:
                st.write(f"Columns: {list(sales_orders_df.columns)}")
                if 'Rep Master' in sales_orders_df.columns:
                    st.write(f"Unique Reps: {sales_orders_df['Rep Master'].nunique()}")
                if 'Corrected Customer Name' in sales_orders_df.columns:
                    st.write(f"Unique Customers: {sales_orders_df['Corrected Customer Name'].nunique()}")
        with col2:
            st.write(f"**Invoices:** {len(invoices_df)} rows")
            if not invoices_df.empty:
                st.write(f"Columns: {list(invoices_df.columns)}")
                if 'Rep Master' in invoices_df.columns:
                    st.write(f"Unique Reps: {invoices_df['Rep Master'].nunique()}")
                if 'Corrected Customer' in invoices_df.columns:
                    st.write(f"Unique Customers: {invoices_df['Corrected Customer'].nunique()}")
        with col3:
            st.write(f"**HubSpot Deals:** {len(deals_df)} rows")
            if not deals_df.empty:
                st.write(f"Columns: {list(deals_df.columns)}")
                if 'Deal Owner' in deals_df.columns:
                    st.write(f"Unique Owners: {deals_df['Deal Owner'].nunique()}")
                    st.write(f"Sample Owners: {deals_df['Deal Owner'].head(5).tolist()}")
                if 'Company Name' in deals_df.columns:
                    st.write(f"Unique Companies: {deals_df['Company Name'].nunique()}")
                    st.write(f"Sample Companies: {deals_df['Company Name'].head(5).tolist()}")
                else:
                    st.error("Company Name column NOT found!")
    
    # Custom CSS for dark dropdown text
    st.markdown("""
        <style>
        /* Dark text for selectbox */
        div[data-baseweb="select"] > div {
            color: #1a1a1a !important;
            background-color: #ffffff !important;
        }
        div[data-baseweb="select"] span {
            color: #1a1a1a !important;
        }
        /* Dropdown options */
        div[data-baseweb="popover"] li {
            color: #1a1a1a !important;
        }
        /* Input labels */
        .stSelectbox label {
            color: #e2e8f0 !important;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # =========================================================================
    # REP AND CUSTOMER SELECTION - ON MAIN DASHBOARD
    # =========================================================================
    st.markdown("---")
    st.markdown("### 🔍 Select Customer for QBR")
    
    # Rep selector
    rep_list = get_rep_list(sales_orders_df, invoices_df)
    if not rep_list:
        st.error("No sales reps found in data.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_rep = st.selectbox(
            "**Sales Rep:**", 
            rep_list, 
            key="qbr_rep_selector"
        )
    
    # Customer selector (filtered by rep)
    customer_list = get_customers_for_rep(selected_rep, sales_orders_df, invoices_df)
    
    with col2:
        if not customer_list:
            st.warning(f"No customers found for {selected_rep}")
            return
        
        selected_customer = st.selectbox(
            "**Customer:**", 
            customer_list, 
            key="qbr_customer_selector"
        )
    
    st.markdown("---")
    
    # Filter data for selected customer
    customer_orders = sales_orders_df[
        (sales_orders_df['Corrected Customer Name'] == selected_customer) &
        (sales_orders_df['Rep Master'] == selected_rep)
    ].copy() if not sales_orders_df.empty and 'Corrected Customer Name' in sales_orders_df.columns else pd.DataFrame()
    
    customer_invoices = invoices_df[
        (invoices_df['Corrected Customer'] == selected_customer) &
        (invoices_df['Rep Master'] == selected_rep)
    ].copy() if not invoices_df.empty and 'Corrected Customer' in invoices_df.columns else pd.DataFrame()
    
    # Direct match for HubSpot deals using Company Name
    customer_deals = get_customer_deals(selected_customer, selected_rep, deals_df)
    
    # Debug: Show filtered counts
    with st.expander("🔍 Debug: Filtered Data for Selected Customer"):
        st.write(f"**Selected Rep:** {selected_rep}")
        st.write(f"**Selected Customer:** `{selected_customer}`")
        st.write(f"**Matching Sales Orders:** {len(customer_orders)}")
        st.write(f"**Matching Invoices:** {len(customer_invoices)}")
        st.write(f"**Matching HubSpot Deals:** {len(customer_deals)}")
        
        if not invoices_df.empty and 'Corrected Customer' in invoices_df.columns:
            # Show sample of what's in the invoice data for this rep
            rep_invoices = invoices_df[invoices_df['Rep Master'] == selected_rep]
            st.write(f"**Total invoices for {selected_rep}:** {len(rep_invoices)}")
            if len(rep_invoices) > 0:
                st.write(f"**Sample customers in invoices:** {rep_invoices['Corrected Customer'].head(10).tolist()}")
        
        if not deals_df.empty and 'Company Name' in deals_df.columns:
            rep_deals = deals_df[deals_df['Deal Owner'] == selected_rep]
            st.write(f"**Total deals for {selected_rep}:** {len(rep_deals)}")
            if len(rep_deals) > 0:
                st.write(f"**Sample Company Names in deals:** {rep_deals['Company Name'].head(10).tolist()}")
                # Show exact match attempt
                st.write(f"**Looking for exact match:** `{selected_customer}`")
                exact_matches = rep_deals[rep_deals['Company Name'] == selected_customer]
                st.write(f"**Exact matches found:** {len(exact_matches)}")
                
                # Try contains match for debugging
                contains_matches = rep_deals[rep_deals['Company Name'].str.contains(selected_customer, case=False, na=False)]
                st.write(f"**Contains matches found:** {len(contains_matches)}")
                if len(contains_matches) > 0:
                    st.write(f"**Contains match Company Names:** {contains_matches['Company Name'].tolist()}")
                
                # Show raw bytes of first Company Name to detect hidden chars
                if len(rep_deals) > 0:
                    first_company = rep_deals['Company Name'].iloc[0]
                    st.write(f"**First Company Name repr:** `{repr(first_company)}`")
    
    # Main content
    st.markdown(f"## QBR: {selected_customer}")
    st.markdown(f"*Sales Rep: {selected_rep} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    
    st.markdown("---")
    
    # Render each section
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


# ========== ENTRY POINT ==========
if __name__ == "__main__":
    st.set_page_config(
        page_title="QBR Generator",
        page_icon="📋",
        layout="wide"
    )
    render_yearly_planning_2026()
