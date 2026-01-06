"""
Q4 2025 Revenue Review Dashboard
================================
A retrospective analysis of Q4 2025 sales performance based on invoice data.

Team View: All reps combined
Individual Rep View: Same metrics filtered to selected rep
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import json

# ============================================================================
# CONFIGURATION
# ============================================================================

CACHE_VERSION = "q4_review_v2"

def get_spreadsheet_id():
    try:
        return st.secrets.get("spreadsheet_id", "15JhBZ_7aHHZA1W1qsoC2163borL6RYjk0xTDWPmWPfA")
    except:
        return "15JhBZ_7aHHZA1W1qsoC2163borL6RYjk0xTDWPmWPfA"

SPREADSHEET_ID = get_spreadsheet_id()

# Q4 2025 date range
Q4_START = datetime(2025, 10, 1)
Q4_END = datetime(2025, 12, 31, 23, 59, 59)

# ============================================================================
# DATA LOADING
# ============================================================================

def get_google_credentials():
    """Get Google API credentials from Streamlit secrets"""
    try:
        creds_dict = st.secrets["service_account"]
        if isinstance(creds_dict, str):
            creds_dict = json.loads(creds_dict)
        else:
            creds_dict = dict(creds_dict)
        
        credentials = Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
        return credentials
    except Exception as e:
        st.error(f"❌ Error loading credentials: {str(e)}")
        return None

@st.cache_data(ttl=300, show_spinner=False)
def load_google_sheets_data(sheet_name, range_name, version=CACHE_VERSION):
    """Load data from Google Sheets with caching"""
    try:
        credentials = get_google_credentials()
        if not credentials:
            return pd.DataFrame()
        
        service = build('sheets', 'v4', credentials=credentials)
        
        full_range = f"'{sheet_name}'!{range_name}"
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=full_range
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            return pd.DataFrame()
        
        headers = values[0]
        data = values[1:] if len(values) > 1 else []
        
        max_cols = len(headers)
        normalized_data = []
        for row in data:
            if len(row) < max_cols:
                row = row + [''] * (max_cols - len(row))
            elif len(row) > max_cols:
                row = row[:max_cols]
            normalized_data.append(row)
        
        df = pd.DataFrame(normalized_data, columns=headers)
        return df
        
    except Exception as e:
        st.error(f"❌ Error loading {sheet_name}: {str(e)}")
        return pd.DataFrame()

def clean_numeric(value):
    """Convert value to numeric, handling currency formatting"""
    if pd.isna(value) or str(value).strip() == '':
        return 0
    cleaned = str(value).replace(',', '').replace('$', '').replace(' ', '').strip()
    try:
        return float(cleaned)
    except:
        return 0

def load_all_data():
    """Load all required data for Q4 review"""
    
    # Load invoice data
    invoices_df = load_google_sheets_data("_NS_Invoices_Data", "A:U", version=CACHE_VERSION)
    
    # Load dashboard info (rep quotas)
    dashboard_df = load_google_sheets_data("Dashboard Info", "A:C", version=CACHE_VERSION)
    
    # Process invoices
    if not invoices_df.empty:
        invoices_df = process_invoices(invoices_df)
    
    # Process dashboard info
    if not dashboard_df.empty:
        dashboard_df = process_dashboard_info(dashboard_df)
    
    return invoices_df, dashboard_df

def process_invoices(df):
    """Process invoice data for Q4 analysis"""
    if df.empty:
        return df
    
    col_mapping = {}
    col_names = df.columns.tolist()
    
    for i, col in enumerate(col_names):
        col_lower = str(col).lower().strip()
        if 'document' in col_lower and 'number' in col_lower:
            col_mapping[col] = 'Invoice Number'
        elif col_lower == 'status':
            col_mapping[col] = 'Status'
        elif col_lower == 'date' and 'due' not in col_lower and 'closed' not in col_lower:
            col_mapping[col] = 'Date'
        elif col_lower == 'customer':
            col_mapping[col] = 'Customer'
        elif 'amount' in col_lower and 'transaction total' in col_lower:
            col_mapping[col] = 'Amount'
        elif 'amount' in col_lower and 'remaining' in col_lower:
            col_mapping[col] = 'Amount Remaining'
        elif col_lower == 'sales rep':
            col_mapping[col] = 'Sales Rep'
        elif 'hubspot' in col_lower and 'pipeline' in col_lower:
            col_mapping[col] = 'Pipeline'
        elif col_lower == 'department':
            col_mapping[col] = 'Department'
        elif col_lower == 'period':
            col_mapping[col] = 'Period'
        elif 'corrected' in col_lower and 'customer' in col_lower:
            col_mapping[col] = 'Corrected Customer'
        elif col_lower == 'rep master':
            col_mapping[col] = 'Rep Master'
    
    df = df.rename(columns=col_mapping)
    
    # Use Rep Master if available
    if 'Rep Master' in df.columns:
        df['Rep Master'] = df['Rep Master'].astype(str).str.strip()
        invalid_values = ['', 'nan', 'None', '#N/A', '#REF!', '#VALUE!', '#ERROR!']
        df = df[~df['Rep Master'].isin(invalid_values)]
        df['Sales Rep'] = df['Rep Master']
    
    # Use Corrected Customer if available
    if 'Corrected Customer' in df.columns and 'Customer' in df.columns:
        df['Corrected Customer'] = df['Corrected Customer'].astype(str).str.strip()
        invalid_values = ['', 'nan', 'None', '#N/A', '#REF!', '#VALUE!', '#ERROR!']
        mask = ~df['Corrected Customer'].isin(invalid_values)
        df.loc[mask, 'Customer'] = df.loc[mask, 'Corrected Customer']
    
    # Clean amount
    if 'Amount' in df.columns:
        df['Amount'] = df['Amount'].apply(clean_numeric)
    else:
        df['Amount'] = 0
    
    # Parse date and filter for Q4 2025
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df[(df['Date'] >= Q4_START) & (df['Date'] <= Q4_END)]
        df['Month'] = df['Date'].dt.strftime('%B %Y')
        df['Month_Num'] = df['Date'].dt.month
    
    # Clean Sales Rep
    if 'Sales Rep' in df.columns:
        df['Sales Rep'] = df['Sales Rep'].astype(str).str.strip()
        invalid_reps = ['', 'nan', 'None', '#N/A', '#REF!']
        df = df[~df['Sales Rep'].isin(invalid_reps)]
    
    return df

def process_dashboard_info(df):
    """Process dashboard info for quota data"""
    if df.empty:
        return df
    
    col_names = df.columns.tolist()
    rename_map = {}
    
    for col in col_names:
        col_lower = str(col).lower().strip()
        if 'rep' in col_lower and 'name' in col_lower:
            rename_map[col] = 'Rep Name'
        elif col_lower == 'quota':
            rename_map[col] = 'Quota'
        elif 'netsuite' in col_lower and 'order' in col_lower:
            rename_map[col] = 'NetSuite Orders'
    
    df = df.rename(columns=rename_map)
    
    if 'Quota' in df.columns:
        df['Quota'] = df['Quota'].apply(clean_numeric)
    
    return df

# ============================================================================
# SHARED DASHBOARD DISPLAY (Used for both Team and Individual Rep)
# ============================================================================

def display_dashboard(invoices_df, dashboard_df, rep_name=None):
    """
    Display Q4 2025 review dashboard.
    If rep_name is None, shows team totals.
    If rep_name is provided, filters to that rep.
    """
    
    # Filter data if individual rep
    if rep_name:
        if 'Sales Rep' in invoices_df.columns:
            invoices_df = invoices_df[invoices_df['Sales Rep'] == rep_name].copy()
        title = f"👤 {rep_name}'s Q4 2025 Review"
        quota = 0
        if not dashboard_df.empty and 'Rep Name' in dashboard_df.columns:
            rep_quota = dashboard_df[dashboard_df['Rep Name'] == rep_name]
            if not rep_quota.empty and 'Quota' in rep_quota.columns:
                quota = rep_quota['Quota'].iloc[0]
    else:
        title = "📊 Q4 2025 Team Revenue Review"
        quota = dashboard_df['Quota'].sum() if not dashboard_df.empty and 'Quota' in dashboard_df.columns else 0
    
    st.title(title)
    st.caption("October - December 2025 | Invoice Data")
    
    if invoices_df.empty:
        st.warning(f"⚠️ No invoice data available for Q4 2025{' for ' + rep_name if rep_name else ''}")
        return
    
    # ==================== TOP METRICS ====================
    total_revenue = invoices_df['Amount'].sum()
    total_invoices = len(invoices_df)
    attainment_pct = (total_revenue / quota * 100) if quota > 0 else 0
    
    st.markdown("### 🏆 Performance Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Q4 Revenue",
            f"${total_revenue:,.0f}"
        )
    
    with col2:
        st.metric(
            "🎯 Quota",
            f"${quota:,.0f}"
        )
    
    with col3:
        gap = total_revenue - quota
        st.metric(
            "📈 Attainment",
            f"{attainment_pct:.1f}%",
            delta=f"${gap:+,.0f}" if quota > 0 else None
        )
    
    with col4:
        st.metric(
            "📄 Invoices",
            f"{total_invoices:,}"
        )
    
    st.markdown("---")
    
    # ==================== LEADERBOARD (Team only) ====================
    if not rep_name and 'Sales Rep' in invoices_df.columns:
        st.markdown("### 🥇 Sales Leaderboard")
        
        rep_revenue = invoices_df.groupby('Sales Rep').agg({
            'Amount': 'sum',
            'Invoice Number': 'count' if 'Invoice Number' in invoices_df.columns else 'size'
        }).reset_index()
        rep_revenue.columns = ['Sales Rep', 'Revenue', 'Invoices']
        
        # Add quota info
        if not dashboard_df.empty and 'Rep Name' in dashboard_df.columns:
            rep_revenue = rep_revenue.merge(
                dashboard_df[['Rep Name', 'Quota']],
                left_on='Sales Rep',
                right_on='Rep Name',
                how='left'
            )
            rep_revenue['Quota'] = rep_revenue['Quota'].fillna(0)
            rep_revenue['Attainment'] = rep_revenue.apply(
                lambda x: (x['Revenue'] / x['Quota'] * 100) if x['Quota'] > 0 else 0, axis=1
            )
        else:
            rep_revenue['Quota'] = 0
            rep_revenue['Attainment'] = 0
        
        rep_revenue = rep_revenue.sort_values('Revenue', ascending=False).reset_index(drop=True)
        
        # Add rank medals
        def get_medal(idx):
            if idx == 0: return "🥇"
            elif idx == 1: return "🥈"
            elif idx == 2: return "🥉"
            else: return f"#{idx + 1}"
        
        rep_revenue['Rank'] = [get_medal(i) for i in range(len(rep_revenue))]
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            display_cols = ['Rank', 'Sales Rep', 'Revenue', 'Quota', 'Attainment', 'Invoices']
            display_df = rep_revenue[[c for c in display_cols if c in rep_revenue.columns]].copy()
            
            st.dataframe(
                display_df.style.format({
                    'Revenue': '${:,.0f}',
                    'Quota': '${:,.0f}',
                    'Attainment': '{:.1f}%'
                }).background_gradient(subset=['Revenue'], cmap='Greens'),
                use_container_width=True,
                hide_index=True,
                height=350
            )
        
        with col2:
            fig = px.bar(
                rep_revenue,
                x='Revenue',
                y='Sales Rep',
                orientation='h',
                color='Attainment',
                color_continuous_scale='RdYlGn',
                range_color=[0, 150]
            )
            fig.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                height=350,
                showlegend=False,
                margin=dict(l=0, r=0, t=10, b=0)
            )
            fig.update_coloraxes(colorbar_title='%')
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
    
    # ==================== MONTHLY BREAKDOWN ====================
    st.markdown("### 📅 Monthly Breakdown")
    
    if 'Month' in invoices_df.columns and 'Month_Num' in invoices_df.columns:
        monthly = invoices_df.groupby(['Month', 'Month_Num']).agg({
            'Amount': 'sum',
            'Invoice Number': 'count' if 'Invoice Number' in invoices_df.columns else 'size'
        }).reset_index()
        monthly.columns = ['Month', 'Month_Num', 'Revenue', 'Invoices']
        monthly = monthly.sort_values('Month_Num')
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = px.bar(
                monthly,
                x='Month',
                y='Revenue',
                color='Revenue',
                color_continuous_scale='Blues',
                text='Revenue'
            )
            fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
            fig.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            for _, row in monthly.iterrows():
                st.metric(
                    row['Month'],
                    f"${row['Revenue']:,.0f}",
                    f"{row['Invoices']} invoices"
                )
    
    st.markdown("---")
    
    # ==================== TOP CUSTOMERS ====================
    st.markdown("### 🏢 Top Customers")
    
    if 'Customer' in invoices_df.columns:
        customer_revenue = invoices_df.groupby('Customer').agg({
            'Amount': 'sum',
            'Invoice Number': 'count' if 'Invoice Number' in invoices_df.columns else 'size'
        }).reset_index()
        customer_revenue.columns = ['Customer', 'Revenue', 'Invoices']
        customer_revenue = customer_revenue.sort_values('Revenue', ascending=False)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            top_15 = customer_revenue.head(15).copy()
            top_15['Rank'] = range(1, len(top_15) + 1)
            
            st.dataframe(
                top_15[['Rank', 'Customer', 'Revenue', 'Invoices']].style.format({
                    'Revenue': '${:,.0f}'
                }),
                use_container_width=True,
                hide_index=True,
                height=400
            )
        
        with col2:
            top_10 = customer_revenue.head(10).copy()
            other_rev = customer_revenue.iloc[10:]['Revenue'].sum() if len(customer_revenue) > 10 else 0
            
            if other_rev > 0:
                pie_data = pd.concat([
                    top_10[['Customer', 'Revenue']],
                    pd.DataFrame({'Customer': ['All Others'], 'Revenue': [other_rev]})
                ], ignore_index=True)
            else:
                pie_data = top_10[['Customer', 'Revenue']]
            
            fig = px.pie(
                pie_data,
                values='Revenue',
                names='Customer',
                hole=0.4
            )
            fig.update_traces(textposition='inside', textinfo='percent')
            fig.update_layout(showlegend=True, height=400, legend=dict(font=dict(size=10)))
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ==================== CATEGORY BREAKDOWN ====================
    st.markdown("### 📦 Revenue by Category")
    
    # Try Pipeline first, then Department
    cat_col = None
    if 'Pipeline' in invoices_df.columns:
        cat_col = 'Pipeline'
    elif 'Department' in invoices_df.columns:
        cat_col = 'Department'
    
    if cat_col:
        cat_revenue = invoices_df.groupby(cat_col).agg({
            'Amount': 'sum',
            'Invoice Number': 'count' if 'Invoice Number' in invoices_df.columns else 'size'
        }).reset_index()
        cat_revenue.columns = ['Category', 'Revenue', 'Invoices']
        cat_revenue = cat_revenue[cat_revenue['Category'].notna()]
        cat_revenue = cat_revenue[cat_revenue['Category'].astype(str).str.strip() != '']
        cat_revenue = cat_revenue.sort_values('Revenue', ascending=False)
        
        if not cat_revenue.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.dataframe(
                    cat_revenue.style.format({'Revenue': '${:,.0f}'}),
                    use_container_width=True,
                    hide_index=True
                )
            
            with col2:
                fig = px.bar(
                    cat_revenue,
                    x='Category',
                    y='Revenue',
                    color='Revenue',
                    color_continuous_scale='Viridis',
                    text='Revenue'
                )
                fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
                fig.update_layout(showlegend=False, height=300)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📭 No category data available")
    else:
        st.info("📭 No category/pipeline data available")

# ============================================================================
# MAIN RENDER FUNCTION
# ============================================================================

def render_q4_revenue_snapshot():
    """Main entry point for Q4 Revenue Snapshot module"""
    
    # Initialize session state
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    
    # Custom CSS
    st.markdown("""
    <style>
        .stMetric {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #3b82f6;
        }
        .stMetric label {
            color: #94a3b8 !important;
        }
        .stMetric [data-testid="stMetricValue"] {
            color: #f1f5f9 !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 20px;
        ">
            <h2 style="color: white; margin: 0;">📊 Q4 2025 Review</h2>
            <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0 0; font-size: 12px;">Calyx Containers</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🧭 Navigation")
        
        view_mode = st.radio(
            "View:",
            ["👥 Team Overview", "👤 Individual Rep"],
            label_visibility="collapsed",
            key="q4_nav"
        )
        
        # Rep selector (only shown for Individual Rep view)
        rep_name = None
        if view_mode == "👤 Individual Rep":
            st.markdown("---")
            st.markdown("### 👤 Select Rep")
    
    # Load data
    with st.spinner("Loading Q4 2025 data..."):
        invoices_df, dashboard_df = load_all_data()
    
    # Get rep list for selector
    if view_mode == "👤 Individual Rep":
        if not dashboard_df.empty and 'Rep Name' in dashboard_df.columns:
            rep_list = dashboard_df['Rep Name'].tolist()
        elif not invoices_df.empty and 'Sales Rep' in invoices_df.columns:
            rep_list = invoices_df['Sales Rep'].unique().tolist()
        else:
            rep_list = []
        
        if rep_list:
            with st.sidebar:
                rep_name = st.selectbox(
                    "Rep:",
                    options=rep_list,
                    key="rep_selector",
                    label_visibility="collapsed"
                )
        else:
            st.error("No rep data available")
            return
    
    # Display data info in sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📈 Data Summary")
        if not invoices_df.empty:
            st.caption(f"📄 {len(invoices_df):,} invoices")
            st.caption(f"💰 ${invoices_df['Amount'].sum():,.0f} total")
        if not dashboard_df.empty and 'Rep Name' in dashboard_df.columns:
            st.caption(f"👥 {len(dashboard_df)} reps")
    
    # Display appropriate dashboard
    if view_mode == "👥 Team Overview":
        display_dashboard(invoices_df, dashboard_df, rep_name=None)
    else:
        display_dashboard(invoices_df, dashboard_df, rep_name=rep_name)

# Entry point
if __name__ == "__main__":
    st.set_page_config(
        page_title="Q4 2025 Review",
        page_icon="📊",
        layout="wide"
    )
    render_q4_revenue_snapshot()
