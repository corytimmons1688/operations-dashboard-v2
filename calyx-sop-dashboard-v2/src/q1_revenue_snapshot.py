"""
Sales Forecasting Dashboard - Q1 2026 Version
Reads from Google Sheets and displays gap-to-goal analysis with interactive visualizations
Includes lead time logic for Q1/Q2 fulfillment determination and detailed order drill-downs
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import time
import base64
import numpy as np





# Configure Plotly for dark mode compatibility
pio.templates.default = "plotly"  # Use default template that adapts to theme

# Helper function for business days calculation
def calculate_business_days_remaining():
    """
    Calculate business days from today through end of Q1 2026 (Mar 31)
    Excludes weekends and major holidays
    """
    from datetime import date, timedelta
    
    today = date.today()
    q1_end = date(2026, 3, 31)
    
    # Define holidays to exclude
    holidays = [
        date(2026, 1, 1),   # New Year's Day
        date(2026, 1, 20),  # MLK Day
        date(2026, 2, 16),  # Presidents Day
    ]
    
    business_days = 0
    current_date = today
    
    while current_date <= q1_end:
        # Check if it's a weekday (Monday=0, Sunday=6)
        if current_date.weekday() < 5 and current_date not in holidays:
            business_days += 1
        current_date += timedelta(days=1)
    
    return business_days

def get_mst_time():
    """
    Get current time in Mountain Standard Time (MST/MDT)
    Returns timezone-aware datetime in America/Denver timezone
    """
    return datetime.now(ZoneInfo("America/Denver"))

# Page configuration - only run when this is the main script
# When imported as a module, the parent app handles page config
try:
    # This will fail if page_config was already set by parent app
    st.set_page_config(
        page_title="Sales Forecasting Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
except:
    pass  # Page config already set by parent app

# Custom CSS for styling - DRAMATIC DARK MODE UI
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ==============================================
       FORCE DARK THEME EVERYWHERE
       ============================================== */
    .stApp {
        background: linear-gradient(135deg, #0a0f1a 0%, #0f172a 50%, #1e1b4b 100%) !important;
        color: #e2e8f0 !important;
    }

    /* ==============================================
       TYPOGRAPHY - CRISP AND MODERN
       ============================================== */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    h1 {
        font-size: 2.5rem !important;
        font-weight: 900 !important;
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        letter-spacing: -1px !important;
        margin-bottom: 1rem !important;
    }
    
    h2, h3, h4 {
        color: #f1f5f9 !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
    }
    
    p, label {
        color: #cbd5e1 !important;
    }

    /* ==============================================
       METRIC CARDS - GLOWING GLASS EFFECT
       ============================================== */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%) !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        border-radius: 20px !important;
        padding: 1.5rem !important;
        box-shadow: 
            0 0 20px rgba(99, 102, 241, 0.15),
            0 8px 32px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
        position: relative !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    [data-testid="stMetric"]::before {
        content: "" !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 3px !important;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899) !important;
        opacity: 0.8 !important;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-8px) scale(1.02) !important;
        border-color: rgba(139, 92, 246, 0.6) !important;
        box-shadow: 
            0 0 40px rgba(139, 92, 246, 0.3),
            0 20px 60px rgba(0, 0, 0, 0.5) !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 1.5px !important;
        color: #94a3b8 !important;
        margin-bottom: 0.5rem !important;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #ffffff 0%, #60a5fa 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        line-height: 1.2 !important;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stMetricDelta"] svg {
        display: inline !important;
    }

    /* ==============================================
       SIDEBAR - SLEEK DARK PANEL
       ============================================== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #020617 0%, #0f172a 100%) !important;
        border-right: 1px solid rgba(99, 102, 241, 0.2) !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdown"] {
        color: #e2e8f0 !important;
    }
    
    /* Sidebar radio buttons as cards */
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label {
        background: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(71, 85, 105, 0.5) !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
        margin: 4px 0 !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label:hover {
        background: rgba(51, 65, 85, 0.8) !important;
        border-color: #6366f1 !important;
        transform: translateX(4px) !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label[data-checked="true"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        border: none !important;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4) !important;
    }

    /* ==============================================
       BUTTONS - GRADIENT WITH GLOW
       ============================================== */
    .stButton > button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.3px !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.5) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* ==============================================
       DATAFRAMES & TABLES - DARK GLASS
       ============================================== */
    [data-testid="stDataFrame"], .stDataFrame {
        background: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(71, 85, 105, 0.3) !important;
        border-radius: 16px !important;
    }
    
    .stDataFrame table {
        background: transparent !important;
    }
    
    .stDataFrame th {
        background: rgba(30, 41, 59, 0.9) !important;
        color: #e2e8f0 !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        font-size: 0.75rem !important;
        letter-spacing: 0.5px !important;
        border-bottom: 2px solid rgba(99, 102, 241, 0.3) !important;
    }
    
    .stDataFrame td {
        background: rgba(15, 23, 42, 0.5) !important;
        color: #cbd5e1 !important;
        border-bottom: 1px solid rgba(51, 65, 85, 0.5) !important;
    }
    
    .stDataFrame tr:hover td {
        background: rgba(51, 65, 85, 0.6) !important;
    }

    /* ==============================================
       EXPANDERS - COLLAPSIBLE CARDS
       ============================================== */
    [data-testid="stExpander"] {
        background: rgba(30, 41, 59, 0.5) !important;
        border: 1px solid rgba(71, 85, 105, 0.4) !important;
        border-radius: 16px !important;
        margin: 12px 0 !important;
    }

    /* ==============================================
       TABS - MODERN PILL STYLE
       ============================================== */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(15, 23, 42, 0.6) !important;
        border-radius: 16px !important;
        padding: 6px !important;
        gap: 6px !important;
        border: 1px solid rgba(51, 65, 85, 0.5) !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: #94a3b8 !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        transition: all 0.3s ease !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #f1f5f9 !important;
        background: rgba(51, 65, 85, 0.5) !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4) !important;
    }

    /* ==============================================
       SELECT BOXES & INPUTS
       ============================================== */
    .stSelectbox > div > div,
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid rgba(71, 85, 105, 0.5) !important;
        border-radius: 12px !important;
        color: #f1f5f9 !important;
    }
    
    .stSelectbox > div > div:hover,
    .stSelectbox > div > div:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
    }
    
    /* Dropdown options */
    [data-baseweb="popover"] {
        background: #1e293b !important;
        border: 1px solid rgba(71, 85, 105, 0.5) !important;
        border-radius: 12px !important;
    }
    
    [data-baseweb="menu"] {
        background: transparent !important;
    }
    
    [role="option"] {
        background: transparent !important;
        color: #e2e8f0 !important;
    }
    
    [role="option"]:hover {
        background: rgba(99, 102, 241, 0.2) !important;
    }

    /* ==============================================
       PROGRESS BREAKDOWN CARD
       ============================================== */
    .progress-breakdown {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%) !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        border-radius: 20px !important;
        padding: 2rem !important;
        margin: 1.5rem 0 !important;
        position: relative !important;
        box-shadow: 
            0 0 30px rgba(99, 102, 241, 0.1),
            0 10px 40px rgba(0, 0, 0, 0.3) !important;
    }
    
    .progress-breakdown::before {
        content: "" !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 5px !important;
        height: 100% !important;
        background: linear-gradient(180deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%) !important;
    }
    
    .progress-breakdown h3 {
        color: #f1f5f9 !important;
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        margin-bottom: 1.5rem !important;
        padding-left: 0.5rem !important;
    }
    
    .progress-item {
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        padding: 1rem 0.5rem !important;
        border-bottom: 1px solid rgba(71, 85, 105, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    
    .progress-item:hover {
        background: rgba(99, 102, 241, 0.05) !important;
    }
    
    .progress-item:last-child {
        border-bottom: none !important;
        border-top: 2px solid rgba(99, 102, 241, 0.3) !important;
        margin-top: 1rem !important;
        padding-top: 1.25rem !important;
    }
    
    .progress-label {
        color: #94a3b8 !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
    }
    
    .progress-value {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        font-family: 'Inter', monospace !important;
    }

    /* ==============================================
       STICKY FOOTER BAR - FLOATING HUD
       ============================================== */
    .sticky-forecast-bar {
        position: fixed !important;
        bottom: 24px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: calc(100% - 380px) !important;
        max-width: 1100px !important;
        z-index: 999999 !important;
        
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.95) 100%) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        
        border: 1px solid rgba(99, 102, 241, 0.4) !important;
        border-radius: 24px !important;
        box-shadow: 
            0 0 40px rgba(99, 102, 241, 0.2),
            0 20px 60px rgba(0, 0, 0, 0.5) !important;
        
        padding: 16px 32px !important;
        display: flex !important;
        justify-content: space-around !important;
        align-items: center !important;
    }
    
    .sticky-forecast-item {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        padding: 0 1rem !important;
    }
    
    .sticky-forecast-label {
        font-size: 0.65rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 1.5px !important;
        color: #64748b !important;
        margin-bottom: 4px !important;
    }
    
    .sticky-forecast-value {
        font-size: 1.25rem !important;
        font-weight: 800 !important;
        color: #f1f5f9 !important;
    }
    
    .sticky-forecast-value.invoiced { 
        color: #4ade80 !important; 
        text-shadow: 0 0 15px rgba(74, 222, 128, 0.5) !important;
    }
    .sticky-forecast-value.pending { 
        color: #fbbf24 !important; 
        text-shadow: 0 0 15px rgba(251, 191, 36, 0.5) !important;
    }
    .sticky-forecast-value.pipeline { 
        color: #60a5fa !important; 
        text-shadow: 0 0 15px rgba(96, 165, 250, 0.5) !important;
    }
    .sticky-forecast-value.total {
        font-size: 1.5rem !important;
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        filter: drop-shadow(0 0 20px rgba(139, 92, 246, 0.5)) !important;
    }
    .sticky-forecast-value.gap-behind { 
        color: #f87171 !important; 
        text-shadow: 0 0 15px rgba(248, 113, 113, 0.5) !important;
    }
    .sticky-forecast-value.gap-ahead { 
        color: #4ade80 !important; 
        text-shadow: 0 0 15px rgba(74, 222, 128, 0.5) !important;
    }
    
    .sticky-forecast-divider {
        width: 1px !important;
        height: 40px !important;
        background: linear-gradient(180deg, transparent, rgba(99, 102, 241, 0.5), transparent) !important;
    }

    /* ==============================================
       LOCKED REVENUE BANNER
       ============================================== */
    .locked-revenue-banner {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(6, 78, 59, 0.2) 100%) !important;
        border: 1px solid rgba(16, 185, 129, 0.4) !important;
        border-radius: 16px !important;
        padding: 1.25rem 1.5rem !important;
        margin-bottom: 1.5rem !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.15) !important;
    }
    
    .banner-value {
        color: #4ade80 !important;
        font-size: 1.75rem !important;
        font-weight: 800 !important;
        text-shadow: 0 0 20px rgba(74, 222, 128, 0.4) !important;
    }
    
    .banner-status {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: #022c22 !important;
        font-size: 0.7rem !important;
        font-weight: 700 !important;
        padding: 6px 12px !important;
        border-radius: 8px !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }

    /* ==============================================
       CHECKBOXES
       ============================================== */
    [data-testid="stCheckbox"] label {
        color: #e2e8f0 !important;
    }
    
    [data-testid="stCheckbox"] > div > div {
        border-color: rgba(99, 102, 241, 0.5) !important;
    }
    
    [data-testid="stCheckbox"] > div > div[data-checked="true"] {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        border: none !important;
    }

    /* ==============================================
       DIVIDERS & MARKDOWN
       ============================================== */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.4), transparent) !important;
        margin: 1.5rem 0 !important;
    }
    
    [data-testid="stMarkdown"] a {
        color: #818cf8 !important;
        text-decoration: none !important;
    }
    
    [data-testid="stMarkdown"] a:hover {
        color: #a5b4fc !important;
        text-decoration: underline !important;
    }
    
    code {
        background: rgba(30, 41, 59, 0.8) !important;
        color: #fbbf24 !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-size: 0.85rem !important;
    }

    /* ==============================================
       SCROLLBAR - CUSTOM DARK
       ============================================== */
    ::-webkit-scrollbar {
        width: 8px !important;
        height: 8px !important;
    }
    
    ::-webkit-scrollbar-track {
        background: #0f172a !important;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #4f46e5, #7c3aed) !important;
        border-radius: 10px !important;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #6366f1, #8b5cf6) !important;
    }

    /* ==============================================
       ALERTS & INFO BOXES
       ============================================== */
    .stAlert {
        background: rgba(30, 41, 59, 0.8) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(71, 85, 105, 0.5) !important;
    }
    
    [data-testid="stInfo"] {
        background: rgba(59, 130, 246, 0.1) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
    }
    
    [data-testid="stSuccess"] {
        background: rgba(16, 185, 129, 0.1) !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
    }
    
    [data-testid="stWarning"] {
        background: rgba(245, 158, 11, 0.1) !important;
        border: 1px solid rgba(245, 158, 11, 0.3) !important;
    }
    
    [data-testid="stError"] {
        background: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
    }

    /* ==============================================
       RESPONSIVE ADJUSTMENTS
       ============================================== */
    @media (max-width: 768px) {
        .sticky-forecast-bar {
            width: 95% !important;
            left: 50% !important;
            bottom: 12px !important;
            padding: 12px 16px !important;
            border-radius: 16px !important;
        }
        
        [data-testid="stMetric"] {
            padding: 1rem !important;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
        }
    }

    /* ==============================================
       BOTTOM PADDING FOR STICKY BAR
       ============================================== */
    .main .block-container {
        padding-bottom: 120px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Google Sheets Configuration
# Reads from st.secrets["SPREADSHEET_ID"] if available, otherwise uses default
DEFAULT_SPREADSHEET_ID = "15JhBZ_7aHHZA1W1qsoC2163borL6RYjk0xTDWPmWPfA"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Cache version for manual refresh control
# No TTL - data only refreshes when user clicks refresh button
CACHE_VERSION = "v64_simplified_deals"

@st.cache_data  # Removed TTL - cache persists until manually cleared
def load_google_sheets_data(sheet_name, range_name, version=CACHE_VERSION, silent=False):
    """
    Load data from Google Sheets with caching and enhanced error handling
    
    Args:
        sheet_name: Name of the sheet tab
        range_name: Range to load (e.g., "A:R")
        version: Cache version string
        silent: If True, don't show error messages (for optional sheets)
    """
    try:
        # Get SPREADSHEET_ID from secrets or use default
        spreadsheet_id = st.secrets.get("SPREADSHEET_ID", DEFAULT_SPREADSHEET_ID)
        
        # Check if secrets exist
        if "service_account" not in st.secrets:
            if not silent:
                st.error("❌ Missing Google Cloud credentials in Streamlit secrets")
            return pd.DataFrame()
        
        # Load credentials from Streamlit secrets
        creds_dict = dict(st.secrets["service_account"])
        
        # Create credentials
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=SCOPES
        )
        
        # Build service
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        
        # Fetch data
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!{range_name}"
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            if not silent:
                st.warning(f"⚠️ No data found in {sheet_name}!{range_name}")
            return pd.DataFrame()
        
        # Handle mismatched column counts - pad shorter rows with empty strings
        if len(values) > 1:
            max_cols = max(len(row) for row in values)
            for row in values:
                while len(row) < max_cols:
                    row.append('')
        
        # Convert to DataFrame
        df = pd.DataFrame(values[1:], columns=values[0])
        
        return df
        
...(truncated 186000 characters)...e Forecast - Path to Quota", "base")
    st.plotly_chart(base_chart, use_container_width=True)

    # Full Forecast Chart with Enhanced Annotations
    st.markdown("### 📊 Full Forecast Breakdown")
    st.caption("Complete view including all orders and pending items")
    
    full_metrics = {
        'orders': team_invoiced,
        'pending_fulfillment': team_pf,
        'pending_fulfillment_no_date': team_pf_no_date,
        'pending_approval': team_pa,
        'pending_approval_no_date': team_pa_no_date,
        'pending_approval_old': team_old_pa,
        'expect_commit': team_hs,
        'best_opp': team_best_opp,
        'total_progress': base_forecast,
        'total_quota': team_quota
    }
    
    full_chart = create_enhanced_waterfall_chart(full_metrics, "📊 Full Forecast - All Sources Included", "full")
    st.plotly_chart(full_chart, use_container_width=True)

    # Other charts remain the same
    col1, col2 = st.columns(2)
   
    with col1:
        st.markdown("#### 🎯 Deal Confidence Levels")
        status_chart = create_status_breakdown_chart(deals_df)
        if status_chart:
            st.plotly_chart(status_chart, use_container_width=True)
        else:
            st.info("📭 Nothing to see here... yet!")
   
    with col2:
        st.markdown("#### 🔮 The Crystal Ball: Where Our Deals Stand")
        pipeline_chart = create_pipeline_breakdown_chart(deals_df)
        if pipeline_chart:
            st.plotly_chart(pipeline_chart, use_container_width=True)
        else:
            st.info("📭 Nothing to see here... yet!")
   
    st.markdown("### 📅 When the Magic Happens (Expected Close Dates)")
    timeline_chart = create_deals_timeline(deals_df)
    if timeline_chart:
        st.plotly_chart(timeline_chart, use_container_width=True)
    else:
        st.info("📭 Nothing to see here... yet!")
   
    if not invoices_df.empty:
        st.markdown("### 💰 Invoice Status (Show Me the Money!)")
        invoice_chart = create_invoice_status_chart(invoices_df)
        if invoice_chart:
            st.plotly_chart(invoice_chart, use_container_width=True)
   
    # Display the two sections
    st.markdown("### 👥 High Confidence Forecast by Rep")
    st.caption("Invoiced + Pending Fulfillment (with date) + Pending Approval (with date) + HubSpot Expect/Commit")
    if section1_data:
        section1_df = pd.DataFrame(section1_data)
        st.dataframe(section1_df, use_container_width=True, hide_index=True)
    else:
        st.warning("📭 No data for High Confidence Forecast")
   
    st.markdown("### 👥 Additional Forecast Items by Rep")
    st.caption("Section 1 (above) + items below = Total Q4. Items below: Pending Fulfillment (without date) + Pending Approval (without date) + Old Pending Approval (>2 weeks)")
    if section2_data:
        section2_df = pd.DataFrame(section2_data)
        st.dataframe(section2_df, use_container_width=True, hide_index=True)
    else:
        st.warning("📭 No additional forecast items")
def display_rep_dashboard(rep_name, deals_df, dashboard_df, invoices_df, sales_orders_df, q4_push_df=None):
    """Display individual rep dashboard with drill-down capability - REDESIGNED"""
    
    st.title(f"👤 {rep_name}'s Q1 2026 Forecast")
    
    # Calculate metrics with details
    metrics = calculate_rep_metrics(rep_name, deals_df, dashboard_df, sales_orders_df)
    
    if not metrics:
        st.error(f"No data found for {rep_name}")
        return
    
    # Calculate the key forecast totals
    high_confidence = metrics['total_progress']  # Invoiced + PF(date) + PA(date) + HS E/C
    
    full_forecast = (high_confidence + 
                    metrics['pending_fulfillment_no_date'] + 
                    metrics['pending_approval_no_date'] + 
                    metrics['pending_approval_old'])
    
    gap_to_quota = metrics['quota'] - high_confidence
    
    potential_attainment_value = high_confidence + metrics['best_opp']
    potential_attainment_pct = (potential_attainment_value / metrics['quota'] * 100) if metrics['quota'] > 0 else 0
    
    # NEW: Top Metrics Row (mirroring Team Scorecard)
    st.markdown("### 📊 Rep Scorecard")
    
    metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
    
    with metric_col1:
        st.metric(
            label="💰 Quota",
            value=f"${metrics['quota']/1000:.0f}K" if metrics['quota'] < 1000000 else f"${metrics['quota']/1000000:.1f}M",
            help="Your Q1 2026 sales quota"
        )
    
    with metric_col2:
        high_conf_pct = (high_confidence / metrics['quota'] * 100) if metrics['quota'] > 0 else 0
        st.metric(
            label="💪 High Confidence Forecast",
            value=f"${high_confidence/1000:.0f}K" if high_confidence < 1000000 else f"${high_confidence/1000000:.1f}M",
            delta=f"{high_conf_pct:.1f}% of quota",
            help="Invoiced & Shipped + PF (with date) + PA (with date) + HS Expect/Commit"
        )
    
    with metric_col3:
        full_forecast_pct = (full_forecast / metrics['quota'] * 100) if metrics['quota'] > 0 else 0
        st.metric(
            label="📊 Full Forecast (All Sources)",
            value=f"${full_forecast/1000:.0f}K" if full_forecast < 1000000 else f"${full_forecast/1000000:.1f}M",
            delta=f"{full_forecast_pct:.1f}% of quota",
            help="Invoiced & Shipped + PF (with date) + PA (with date) + HS Expect/Commit + PF (without date) + PA (without date) + PA (>2 weeks old)"
        )
    
    with metric_col4:
        st.metric(
            label="📉 Gap to Quota",
            value=f"${gap_to_quota/1000:.0f}K" if abs(gap_to_quota) < 1000000 else f"${gap_to_quota/1000000:.1f}M",
            delta=f"${-gap_to_quota/1000:.0f}K" if gap_to_quota < 0 else None,
            delta_color="inverse",
            help="Quota - (Invoiced & Shipped + PF (with date) + PA (with date) + HS Expect/Commit)"
        )
    
    with metric_col5:
        upside = potential_attainment_pct - high_conf_pct
        st.metric(
            label="⭐ Potential Attainment",
            value=f"{potential_attainment_pct:.1f}%",
            delta=f"+{upside:.1f}% upside",
            help="(Invoiced & Shipped + PF (with date) + PA (with date) + HS Expect/Commit + HS Best Case/Opp) ÷ Quota"
        )
    
    st.markdown("---")
    
    # Invoices section for this rep
    display_invoices_drill_down(invoices_df, rep_name)
    
    st.markdown("---")
    
    # Build Your Own Forecast section
    build_your_own_forecast_section(
        metrics,
        metrics['quota'],
        rep_name=rep_name,
        deals_df=deals_df,
        invoices_df=invoices_df,
        sales_orders_df=sales_orders_df,
        q4_push_df=q4_push_df
    )
    
    st.markdown("---")
    
    # HubSpot Deals Audit Section
    display_hubspot_deals_audit(deals_df, rep_name)
    
    st.markdown("---")
    
    # SECTION 1: What's in NetSuite with Dates and HubSpot Expect/Commit
    st.markdown(f"""
    <div class="progress-breakdown">
        <h3>💰 Section 1: What's in NetSuite with Dates and HubSpot Expect/Commit</h3>
        <div class="progress-item">
            <span class="progress-label">✅ Invoiced & Shipped</span>
            <span class="progress-value">${metrics['orders']:,.0f}</span>
        </div>
        <div class="progress-item">
            <span class="progress-label">📦 Pending Fulfillment (with date)</span>
            <span class="progress-value">${metrics['pending_fulfillment']:,.0f}</span>
        </div>
        <div class="progress-item">
            <span class="progress-label">⏳ Pending Approval (with date)</span>
            <span class="progress-value">${metrics['pending_approval']:,.0f}</span>
        </div>
        <div class="progress-item">
            <span class="progress-label">🎯 HubSpot Expect/Commit</span>
            <span class="progress-value">${metrics['expect_commit']:,.0f}</span>
        </div>
        <div class="progress-item">
            <span class="progress-label">💪 THE SAFE BET TOTAL</span>
            <span class="progress-value">${high_confidence:,.0f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Drill-down sections for Section 1
    st.markdown("#### 📊 Section 1 Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        display_drill_down_section(
            "📦 Pending Fulfillment (with date)",
            metrics['pending_fulfillment'],
            metrics.get('pending_fulfillment_details', pd.DataFrame()),
            f"{rep_name}_pf"
        )
        
        display_drill_down_section(
            "⏳ Pending Approval (with date)",
            metrics['pending_approval'],
            metrics.get('pending_approval_details', pd.DataFrame()),
            f"{rep_name}_pa"
        )
    
    with col2:
        display_drill_down_section(
            "🎯 HubSpot Expect/Commit",
            metrics['expect_commit'],
            metrics.get('expect_commit_deals', pd.DataFrame()),
            f"{rep_name}_hs"
        )
        
        display_drill_down_section(
            "🎲 Best Case/Opportunity",
            metrics['best_opp'],
            metrics.get('best_opp_deals', pd.DataFrame()),
            f"{rep_name}_bo"
        )
    
    st.markdown("---")
    
    # SECTION 2: Full Forecast
    st.markdown(f"""
    <div class="progress-breakdown">
        <h3>📊 Section 2: Full Forecast</h3>
        <div class="progress-item">
            <span class="progress-label">✅ Invoiced & Shipped</span>
            <span class="progress-value">${metrics['orders']:,.0f}</span>
        </div>
        <div class="progress-item">
            <span class="progress-label">📦 Pending Fulfillment (with date)</span>
            <span class="progress-value">${metrics['pending_fulfillment']:,.0f}</span>
        </div>
        <div class="progress-item">
            <span class="progress-label">⏳ Pending Approval (with date)</span>
            <span class="progress-value">${metrics['pending_approval']:,.0f}</span>
        </div>
        <div class="progress-item">
            <span class="progress-label">🎯 HubSpot Expect/Commit</span>
            <span class="progress-value">${metrics['expect_commit']:,.0f}</span>
        </div>
        <div class="progress-item">
            <span class="progress-label">📦 Pending Fulfillment (without date)</span>
            <span class="progress-value">${metrics['pending_fulfillment_no_date']:,.0f}</span>
        </div>
        <div class="progress-item">
            <span class="progress-label">⏳ Pending Approval (without date)</span>
            <span class="progress-value">${metrics['pending_approval_no_date']:,.0f}</span>
        </div>
        <div class="progress-item">
            <span class="progress-label">⏱️ Pending Approval (>2 weeks old)</span>
            <span class="progress-value">${metrics['pending_approval_old']:,.0f}</span>
        </div>
        <div class="progress-item">
            <span class="progress-label">📊 FULL FORECAST TOTAL</span>
            <span class="progress-value">${full_forecast:,.0f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Drill-down sections for Section 2 (additional items)
    st.markdown("#### 📊 Section 2 Additional Details")
    
    warning_col1, warning_col2, warning_col3 = st.columns(3)
    
    with warning_col1:
        display_drill_down_section(
            "📦 Pending Fulfillment (without date)",
            metrics['pending_fulfillment_no_date'],
            metrics.get('pending_fulfillment_no_date_details', pd.DataFrame()),
            f"{rep_name}_pf_no_date"
        )
    
    with warning_col2:
        display_drill_down_section(
            "⏳ Pending Approval (without date)",
            metrics['pending_approval_no_date'],
            metrics.get('pending_approval_no_date_details', pd.DataFrame()),
            f"{rep_name}_pa_no_date"
        )
    
    with warning_col3:
        display_drill_down_section(
            "⏱️ Old Pending Approval (>2 weeks)",
            metrics['pending_approval_old'],
            metrics.get('pending_approval_old_details', pd.DataFrame()),
            f"{rep_name}_pa_old"
        )
    
    st.markdown("---")
    
    # Q2 2026 Spillover Details (moved from Section 3)
    st.markdown("#### 🦘 Q2 2026 Spillover Details")
    st.caption("⚠️ These deals close in Q1 2026 but will ship in Q2 2026 due to lead times")
    
    spillover_col1, spillover_col2, spillover_col3 = st.columns(3)
    
    with spillover_col1:
        display_drill_down_section(
            "🎯 Expect/Commit (Q1 Spillover)",
            metrics.get('q1_spillover_expect_commit', 0),
            metrics.get('expect_commit_q1_spillover_deals', pd.DataFrame()),
            f"{rep_name}_ec_q1"
        )
    
    with spillover_col2:
        display_drill_down_section(
            "🎲 Best Case/Opp (Q1 Spillover)",
            metrics.get('q1_spillover_best_opp', 0),
            metrics.get('best_opp_q1_spillover_deals', pd.DataFrame()),
            f"{rep_name}_bo_q1"
        )
    
    with spillover_col3:
        display_drill_down_section(
            "📦 All Q2 2026 Spillover",
            metrics.get('q1_spillover_total', 0),
            metrics.get('all_q1_spillover_deals', pd.DataFrame()),
            f"{rep_name}_all_q1"
        )
    
    st.markdown("---")
    
    # Charts
    st.markdown("### 📊 Visual Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        gap_chart = create_gap_chart(metrics, f"{rep_name} - Q1 2026 Forecast Progress")
        st.plotly_chart(gap_chart, use_container_width=True)
    
    with col2:
        status_chart = create_status_breakdown_chart(deals_df, rep_name)
        if status_chart:
            st.plotly_chart(status_chart, use_container_width=True)
        else:
            st.info("No deal data available for this rep")
    
    # Pipeline breakdown
    st.markdown("### 📊 Pipeline Breakdown by Status")
    pipeline_chart = create_pipeline_breakdown_chart(deals_df, rep_name)
    if pipeline_chart:
        st.plotly_chart(pipeline_chart, use_container_width=True)
    else:
        st.info("📭 Nothing to see here... yet!")
    
    # Timeline
    st.markdown("### 📅 Deal Timeline by Expected Close Date")
    timeline_chart = create_deals_timeline(deals_df, rep_name)
    if timeline_chart:
        st.plotly_chart(timeline_chart, use_container_width=True)
    else:
        st.info("📭 Nothing to see here... yet!")

# Main app
def main():
    
    # Initialize session state for data load timestamp
    if 'data_load_time' not in st.session_state:
        st.session_state.data_load_time = get_mst_time()
    
    # Dashboard tagline
    st.markdown("""
    <div style='text-align: center; padding: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                 color: white; border-radius: 10px; margin-bottom: 20px;'>
        <h3>📊 Sales Forecast Dashboard</h3>
        <p style='font-size: 14px; margin: 0;'>Where numbers meet reality (and sometimes they argue)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        # Sexy header with gradient
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        ">
            <h1 style="
                color: white;
                font-size: 28px;
                margin: 0;
                font-weight: 800;
                text-shadow: 0 2px 10px rgba(0,0,0,0.3);
            ">📊 Calyx Command</h1>
            <p style="
                color: rgba(255,255,255,0.9);
                font-size: 14px;
                margin: 8px 0 0 0;
                font-weight: 500;
            ">Q1 2026 Sales Intelligence</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Custom navigation with icons and descriptions
        st.markdown("### 🧭 Navigation")
        
        # ERP-style navigation with CSS styling
        st.markdown("""
        <style>
        div[data-testid="stRadio"] > div {
            gap: 8px;
        }
        
        div[data-testid="stRadio"] > div > label {
            background: rgba(30, 41, 59, 0.6) !important;
            border: 1px solid rgba(71, 85, 105, 0.5) !important;
            border-left: 4px solid transparent !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
            width: 100% !important;
            margin-bottom: 4px !important;
        }
        
        div[data-testid="stRadio"] > div > label:hover {
            background: rgba(51, 65, 85, 0.8) !important;
            border-color: rgba(100, 116, 139, 0.7) !important;
            transform: translateX(4px);
        }
        
        div[data-testid="stRadio"] > div > label[data-checked="true"] {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
            border: 2px solid #3b82f6 !important;
            border-left: 4px solid #60a5fa !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
        }
        
        div[data-testid="stRadio"] > div > label[data-checked="true"]:hover {
            transform: translateX(0);
        }
        
        div[data-testid="stRadio"] label p {
            font-size: 14px !important;
            font-weight: 600 !important;
            margin: 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create navigation options
        view_mode = st.radio(
            "Select View:",
            ["👥 Team Overview", "👤 Individual Rep"],
            label_visibility="collapsed",
            key="nav_selector"
        )
        
        # Map display names back to internal names
        view_mapping = {
            "👥 Team Overview": "Team Overview",
            "👤 Individual Rep": "Individual Rep"
        }
        
        view_mode = view_mapping.get(view_mode, "Team Overview")
        
        st.markdown("---")
        
        # Sexy metrics cards for quick stats
        biz_days = calculate_business_days_remaining()
        
        # Get data load time from session state
        data_load_time = st.session_state.data_load_time
        current_mst_time = get_mst_time()
        time_since_load = current_mst_time - data_load_time
        minutes_ago = int(time_since_load.total_seconds() / 60)
        
        if minutes_ago < 1:
            time_ago_text = "Just now"
        elif minutes_ago < 60:
            time_ago_text = f"{minutes_ago} min ago"
        else:
            hours_ago = minutes_ago // 60
            time_ago_text = f"{hours_ago} hr ago"
        
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(5, 150, 105, 0.2) 100%);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 15px;
        ">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <span style="font-size: 24px;">⏱️</span>
                <div>
                    <div style="font-size: 11px; opacity: 0.7; text-transform: uppercase; letter-spacing: 1px;">Q1 Days Left</div>
                    <div style="font-size: 24px; font-weight: 700; color: #10b981;">""" + str(biz_days) + """</div>
                </div>
            </div>
            <div style="font-size: 10px; opacity: 0.6;">Business days until Mar 31, 2026</div>
        </div>
        
        <div style="
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(37, 99, 235, 0.2) 100%);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 15px;
        ">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <span style="font-size: 24px;">🔄</span>
                <div style="flex: 1;">
                    <div style="font-size: 11px; opacity: 0.7; text-transform: uppercase; letter-spacing: 1px;">Last Sync</div>
                    <div style="font-size: 14px; font-weight: 600; color: #3b82f6;">""" + data_load_time.strftime('%I:%M %p %Z') + """</div>
                </div>
            </div>
            <div style="font-size: 10px; opacity: 0.6;">""" + time_ago_text + """ • Manual refresh only</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Refresh button with gradient
        if st.button("🔄 Refresh Data Now", use_container_width=True):
            # Store snapshot before clearing cache
            if 'current_snapshot' in st.session_state:
                st.session_state.previous_snapshot = st.session_state.current_snapshot
            
            # Clear cache and update timestamp
            st.cache_data.clear()
            st.session_state.data_load_time = get_mst_time()
            
            # Rerun to load fresh data
            # Note: Your view selection, rep selection, and filters are automatically 
            # preserved via Streamlit's widget keys (nav_selector, rep_selector, etc.)
            st.rerun()
        
        st.markdown("---")
        
        # Sync Status - collapsed by default, for Xander
        with st.expander("🔧 Sync Status (for Xander)"):
            current_spreadsheet_id = st.secrets.get("SPREADSHEET_ID", DEFAULT_SPREADSHEET_ID)
            st.write("**Spreadsheet ID:**")
            st.code(current_spreadsheet_id)
            
            if "service_account" in st.secrets:
                st.success("✅ GCP credentials found")
                try:
                    creds_dict = dict(st.secrets["service_account"])
                    if 'client_email' in creds_dict:
                        st.info(f"Service account: {creds_dict['client_email']}")
                        st.caption("Make sure this email has 'Viewer' access to your Google Sheet")
                except:
                    st.error("Error reading credentials")
            else:
                st.error("❌ GCP credentials missing")
    
    # Load data
    with st.spinner("Loading data from Google Sheets..."):
        deals_df, dashboard_df, invoices_df, sales_orders_df, q4_push_df = load_all_data()
    
    # Store snapshot for change tracking
    store_snapshot(deals_df, dashboard_df, invoices_df, sales_orders_df, q4_push_df)
    
    # Show change detection dialog if there's a previous snapshot
    if 'previous_snapshot' in st.session_state and st.session_state.previous_snapshot:
        with st.expander("🔄 View Changes Since Last Refresh", expanded=False):
            changes = detect_changes(st.session_state.current_snapshot, st.session_state.previous_snapshot)
            show_change_dialog(changes)
    
    # Check if data loaded successfully
    if deals_df.empty and dashboard_df.empty:
        st.error("❌ Unable to load data. Please check your Google Sheets connection.")
        
        with st.expander("📋 Setup Checklist"):
            st.markdown("""
            ### Quick Setup Guide:
            
            1. **Google Cloud Setup:**
               - Create a service account in Google Cloud Console
               - Download the JSON key file
               - Note the service account email (ends with @iam.gserviceaccount.com)
            
            2. **Share Your Google Sheet:**
               - Open your Google Sheet
               - Click 'Share' button
               - Add the service account email
               - Give 'Viewer' permission
            
            3. **Add Credentials to Streamlit:**
               - Go to your Streamlit Cloud dashboard
               - Click on your app
               - Go to Settings → Secrets
               - Paste your service account JSON in the format shown in diagnostics above
            
            4. **Verify Sheet Structure:**
               - Ensure sheet names match: 'All Reps All Pipelines', 'Dashboard Info', '_NS_Invoices_Data', '_NS_SalesOrders_Data'
               - Verify columns are in the expected positions
            """)
        
        return
    elif deals_df.empty:
        st.warning("⚠️ Deals data is empty. Check 'All Reps All Pipelines' sheet.")
    elif dashboard_df.empty:
        st.warning("⚠️ Dashboard info is empty. Check 'Dashboard Info' sheet.")
    
    # Display appropriate dashboard
    if view_mode == "Team Overview":
        display_team_dashboard(deals_df, dashboard_df, invoices_df, sales_orders_df, q4_push_df)
    elif view_mode == "Individual Rep":
        if not dashboard_df.empty:
            # FIX: Added key="rep_selector" to preserve selection across refreshes
            rep_name = st.selectbox(
                "Select Rep:",
                options=dashboard_df['Rep Name'].tolist(),
                key="rep_selector"
            )
            if rep_name:
                display_rep_dashboard(rep_name, deals_df, dashboard_df, invoices_df, sales_orders_df, q4_push_df)
        else:
            st.error("No rep data available")

if __name__ == "__main__":
    main()

# Wrapper function for importing into app.py
def render_q1_revenue_snapshot():
    """Entry point when imported as a module by app.py"""
    main()
