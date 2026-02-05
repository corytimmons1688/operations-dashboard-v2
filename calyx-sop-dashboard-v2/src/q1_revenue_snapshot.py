"""
Sales Forecasting Dashboard - Q1 2026 Version
Reads from Google Sheets and displays gap-to-goal analysis with interactive visualizations
Includes lead time logic for Q1/Q2 fulfillment determination and detailed order drill-downs

VERSION 11 CHANGES:
- Added "View All Selected Data" consolidated master table to Build Your Own Forecast section
  - Full-width table combining all checked categories with Source, Category, ID, Name, Amount columns
  - Multiselect filters for Category and Source, plus free-text search across all fields
  - Summary metrics (total amount, prob-adjusted, category count, line items)
  - Category totals breakdown table
- Fixed rep dashboard breakout sections (Section 1, Section 2, Progress Breakdown) not rendering properly
  - Converted CSS class-based HTML (progress-breakdown, progress-item) to inline styles
  - Inline styles render reliably in Streamlit's markdown regardless of CSS load order

VERSION 10 CHANGES:
- Added search filter to Build Your Own Forecast sections (search by Customer/SO# or Deal Name)
- Fixed buggy checkbox behavior in Customize mode - removed conflicting state management
- Checkboxes now respond reliably on first click

VERSION 9 CHANGES:
- Extended All Reps All Pipelines data range from A:U to A:X
- Added support for new column Q: "Primary Associated Company"
- Added support for new column X: "Company Name"
- Updated column handling for separate "Deal Owner First Name" and "Deal Owner Last Name" columns
- Deal Owner is now combined from separate first/last name columns when they exist

VERSION 8 CHANGES:
- Added Probability Toggle for HubSpot deals in Build Your Own Forecast section
- Toggle switches between Raw Amount and Probability-Adjusted amounts
- Loads "Probability Rev" column (Column W) from All Reps All Pipelines sheet
- Displays both amounts in data tables with active mode highlighted
- Export includes both Amount and Prob_Amount columns
- Calculations respect the toggle selection

VERSION 7 CHANGES:
- Sales Order categorization now uses pre-calculated "Updated Status" column (Column AG)
- Removed complex Python logic for categorizing PA/PF statuses
- Updated Status values from sheet: PA No Date, PA with Date, PF with Date (Ext), 
  PF with Date (Int), PF No Date (Int), PF No Date (Ext), PA Old (>2 Weeks)
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

# Custom CSS for styling - DRAMATIC DARK MODE UI (Cleaned up - removed problematic selectors)
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
    
    p, span, label, div {
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
        overflow: hidden !important;
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
    
    [data-testid="stSidebar"] > div:first-child {
        background: transparent !important;
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
        overflow: hidden !important;
    }
    
    [data-testid="stDataFrame"] > div {
        background: transparent !important;
    }
    
    /* Table styling */
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
       EXPANDERS - COLLAPSIBLE CARDS (Simplified to prevent text garbling)
       ============================================== */
    [data-testid="stExpander"] {
        background: rgba(30, 41, 59, 0.5) !important;
        border: 1px solid rgba(71, 85, 105, 0.4) !important;
        border-radius: 16px !important;
        margin: 12px 0 !important;
    }
    
    [data-testid="stExpander"]:hover {
        border-color: rgba(99, 102, 241, 0.5) !important;
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
        overflow: hidden !important;
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
        padding-left: 1rem !important;
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
       CHECKBOXES (Simplified)
       ============================================== */
    [data-testid="stCheckbox"] label {
        color: #e2e8f0 !important;
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
    
    /* Code blocks */
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
CACHE_VERSION = "v66_company_name_columns"

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
        
    except Exception as e:
        error_msg = str(e)
        if not silent:
            st.error(f"❌ Error loading data from {sheet_name}: {error_msg}")
        
        # Provide specific troubleshooting based on error type
        if not silent:
            if "403" in error_msg or "permission" in error_msg.lower():
                st.warning("""
                **Permission Error:**
                - Make sure you've shared the Google Sheet with your service account email
                - The service account email looks like: `your-service-account@project.iam.gserviceaccount.com`
                - Share the sheet with 'Viewer' access
                """)
            elif "404" in error_msg or "not found" in error_msg.lower():
                st.warning("""
                **Sheet Not Found:**
                - Check that the spreadsheet ID is correct
                - Check that the sheet name matches exactly (case-sensitive)
                """)
            elif "401" in error_msg or "authentication" in error_msg.lower():
                st.warning("""
                **Authentication Error:**
                - Your service account credentials may be invalid
                - Try regenerating the service account key in Google Cloud Console
                """)
        
        return pd.DataFrame()

# ========== SPILLOVER COLUMN HELPER FUNCTIONS ==========
# These functions handle both old ('Q1 2026 Spillover') and new ('Q2 2026 Spillover') column names
# to provide backwards compatibility during the spreadsheet transition

def get_spillover_column(df):
    """
    Get the spillover column name - handles both old and new column names.
    Returns the column name if found, None otherwise.
    Checks for 'Q2 2026 Spillover' first, falls back to 'Q1 2026 Spillover'.
    """
    if df is None or df.empty:
        return None
    if 'Q2 2026 Spillover' in df.columns:
        return 'Q2 2026 Spillover'
    elif 'Q1 2026 Spillover' in df.columns:
        return 'Q1 2026 Spillover'
    return None

def get_spillover_value(df, spillover_col):
    """
    Get spillover column values, handling the case where column doesn't exist.
    Returns a Series of the column values or a Series of empty strings if column doesn't exist.
    """
    if spillover_col and spillover_col in df.columns:
        return df[spillover_col]
    return pd.Series([''] * len(df), index=df.index)

def is_q1_deal(df, spillover_col):
    """
    Determine if deals are Q1 2026 deals (primary quarter).
    Q1 deals are NOT marked as Q2 2026 spillover AND NOT marked as Q4 2025 spillover.
    Handles various Quarter column value formats: 'Q2 2026', 'Q2', 'Q4 2025', 'Q4', etc.
    """
    if df is None or df.empty:
        return pd.Series([], dtype=bool)
    if spillover_col is None:
        return pd.Series([True] * len(df), index=df.index)
    
    spillover_vals = get_spillover_value(df, spillover_col).astype(str).str.strip().str.upper()
    
    if spillover_col == 'Q2 2026 Spillover':
        # Exclude Q2 spillover (various formats) and Q4 spillover (various formats)
        # Q2 values: 'Q2 2026', 'Q2', 'Q2 26', etc.
        # Q4 values: 'Q4 2025', 'Q4', 'Q4 25', etc.
        is_q2 = spillover_vals.str.contains('Q2', na=False)
        is_q4 = spillover_vals.str.contains('Q4', na=False)
        return ~is_q2 & ~is_q4
    else:
        # Old column 'Q1 2026 Spillover': for Q1 dashboard, all deals are primary quarter
        return pd.Series([True] * len(df), index=df.index)

def apply_q1_fulfillment_logic(deals_df):
    """
    Apply lead time logic to filter out deals that close late in Q1 2026
    but won't ship until Q2 based on product type
    """
    # Lead time mapping based on your image
    lead_time_map = {
        'Labeled - Labels In Stock': 10,
        'Outer Boxes': 20,
        'Non-Labeled - 1 Week Lead Time': 5,
        'Non-Labeled - 2 Week Lead Time': 10,
        'Labeled - Print & Apply': 20,
        'Non-Labeled - Custom Lead Time': 30,
        'Labeled with FEP - Print & Apply': 35,
        'Labeled - Custom Lead Time': 40,
        'Flexpack': 25,
        'Labels Only - Direct to Customer': 15,
        'Labels Only - For Inventory': 15,
        'Labeled with FEP - Labels In Stock': 25,
        'Labels Only (deprecated)': 15
    }
    
    # Calculate cutoff date for each product type
    q1_end = pd.Timestamp('2026-03-31')
    
    def get_business_days_before(end_date, business_days):
        """Calculate date that is N business days before end_date"""
        current = end_date
        days_counted = 0
        
        while days_counted < business_days:
            current -= timedelta(days=1)
            # Skip weekends (Monday=0, Sunday=6)
            if current.weekday() < 5:
                days_counted += 1
        
        return current
    
    # Add a column to track if deal counts for Q1
    deals_df['Counts_In_Q1'] = True
    deals_df['Q2_Spillover_Amount'] = 0
    
    # Check if we have a Product Type column
    if 'Product Type' in deals_df.columns:
        for product_type, lead_days in lead_time_map.items():
            cutoff_date = get_business_days_before(q1_end, lead_days)
            
            # Mark deals closing after cutoff as Q2
            mask = (
                (deals_df['Product Type'] == product_type) & 
                (deals_df['Close Date'] > cutoff_date) &
                (deals_df['Close Date'].notna())
            )
            deals_df.loc[mask, 'Counts_In_Q1'] = False
            deals_df.loc[mask, 'Q2_Spillover_Amount'] = deals_df.loc[mask, 'Amount']
            
        # Log how many deals were excluded
        excluded_count = (~deals_df['Counts_In_Q1']).sum()
        excluded_value = deals_df[~deals_df['Counts_In_Q1']]['Amount'].sum()
        
        if excluded_count > 0:
            pass  # Debug info removed
            #st.sidebar.info(f"📊 {excluded_count} deals (${excluded_value:,.0f}) deferred to Q2 2026 due to lead times")
    else:
        pass  # Debug info removed
        #st.sidebar.warning("⚠️ No 'Product Type' column found - lead time logic not applied")
    
    return deals_df

def load_all_data():
    """Load all necessary data from Google Sheets"""
    
    #st.sidebar.info("🔄 Loading data from Google Sheets...")
    
    # Load deals data - extend range to include all columns through Company Name (Column X)
    # Columns: A-Record ID, B-Deal Name, C-Deal Stage, D-Close Date, E-Deal Owner First Name, F-Deal Owner Last Name,
    #          G-Amount, H-Close Status, I-Pipeline, J-Create Date, K-Deal Type, L-Netsuite SO#, M-Netsuite SO Link,
    #          N-New Design SKU, O-SKU, P-Netsuite Sales Order Number, Q-Primary Associated Company, R-Average Leadtime,
    #          S-Pending Approval Date, T-Quarter, U-Deal Stage & Close Status, V-Probability, W-Probability Rev, X-Company Name
    deals_df = load_google_sheets_data("All Reps All Pipelines", "A:X", version=CACHE_VERSION)
    
    # DEBUG: Show what we got from HubSpot
    if not deals_df.empty:
        pass  # Debug info removed
        #st.sidebar.success(f"📊 HubSpot raw data: {len(deals_df)} rows, {len(deals_df.columns)} columns")
        pass  # Debug info removed
    else:
        pass  # Debug info removed
        #st.sidebar.error("❌ No HubSpot data loaded!")
        pass
    
    # Load dashboard info (rep quotas)
    dashboard_df = load_google_sheets_data("Dashboard Info", "A:B", version=CACHE_VERSION)
    
    # Load invoice data from NetSuite - EXTEND to include Columns T:U (Corrected Customer Name, Rep Master)
    invoices_df = load_google_sheets_data("_NS_Invoices_Data", "A:Y", version=CACHE_VERSION)
    
    # Load sales orders data from NetSuite - EXTEND to include Columns through AF (Calyx | External Order, Pending Approval Date, Corrected Customer Name, Rep Master)
    sales_orders_df = load_google_sheets_data("_NS_SalesOrders_Data", "A:AG", version=CACHE_VERSION)
    
    # Q4 Push planning status removed for Q1 dashboard
    q4_push_df = pd.DataFrame()  # Empty placeholder for compatibility
    
    # =========================================================================
    # PROCESS DEALS DATA FROM "All Reps All Pipelines" SHEET
    # The query formula in the sheet already filters:
    # - Date range: Q1 2026 (Jan 1 - Mar 31, 2026)
    # - Excluded stages: Cancelled, Checkout Abandoned, Closed Lost, Closed Won, 
    #                    Sales Order Created in NS, NCR, Shipped
    # So we just need to map columns and convert Amount to numeric
    # =========================================================================
    if not deals_df.empty and len(deals_df.columns) >= 6:
        col_names = deals_df.columns.tolist()
        
        st.sidebar.info(f"📋 Raw columns: {col_names}")
        st.sidebar.caption(f"📊 Raw row count: {len(deals_df)}")
        
        # Simple column rename mapping for All Reps All Pipelines sheet
        # Columns: Record ID, Deal Name, Deal Stage, Close Date, Deal Owner First Name, Deal Owner Last Name,
        #          Amount, Close Status, Pipeline, Create Date, Deal Type, Netsuite SO#, Netsuite SO Link,
        #          New Design SKU, SKU, Netsuite Sales Order Number, Primary Associated Company, Average Leadtime,
        #          Pending Approval Date, Quarter, Deal Stage & Close Status, Probability, Probability Rev, Company Name
        rename_dict = {}
        for col in col_names:
            # Handle combined Deal Owner column (old format) or separate columns (new format)
            if 'Deal Owner First Name' in col and 'Deal Owner Last Name' in col:
                rename_dict[col] = 'Deal Owner'
            elif col == 'Close Status':
                rename_dict[col] = 'Status'
            elif col == 'Deal Type':
                rename_dict[col] = 'Product Type'
            elif col == 'Quarter':
                rename_dict[col] = 'Q2 2026 Spillover'
        
        deals_df = deals_df.rename(columns=rename_dict)
        
        # Handle separate First Name / Last Name columns (new format) - combine them into Deal Owner
        if 'Deal Owner First Name' in deals_df.columns and 'Deal Owner Last Name' in deals_df.columns:
            deals_df['Deal Owner'] = (deals_df['Deal Owner First Name'].fillna('').astype(str).str.strip() + ' ' + 
                                      deals_df['Deal Owner Last Name'].fillna('').astype(str).str.strip()).str.strip()
            # Drop the separate columns
            deals_df = deals_df.drop(columns=['Deal Owner First Name', 'Deal Owner Last Name'])
        
        st.sidebar.caption(f"Columns after rename: {deals_df.columns.tolist()}")
        
        # Clean Deal Owner
        if 'Deal Owner' in deals_df.columns:
            deals_df['Deal Owner'] = deals_df['Deal Owner'].astype(str).str.strip()
        
        # Convert Amount to numeric
        def clean_numeric(value):
            if pd.isna(value) or str(value).strip() == '':
                return 0
            cleaned = str(value).replace(',', '').replace('$', '').replace(' ', '').strip()
            try:
                return float(cleaned)
            except:
                return 0
        
        if 'Amount' in deals_df.columns:
            deals_df['Amount'] = deals_df['Amount'].apply(clean_numeric)
        
        # Process Probability Rev column (Column U) - probability-weighted amount
        if 'Probability Rev' in deals_df.columns:
            deals_df['Probability Rev'] = deals_df['Probability Rev'].apply(clean_numeric)
        else:
            # If column doesn't exist, default to same as Amount
            deals_df['Probability Rev'] = deals_df['Amount'] if 'Amount' in deals_df.columns else 0
        
        # Convert Close Date to datetime
        if 'Close Date' in deals_df.columns:
            deals_df['Close Date'] = pd.to_datetime(deals_df['Close Date'], errors='coerce')
        
        # Debug output
        total_deals = len(deals_df)
        total_amount = deals_df['Amount'].sum() if 'Amount' in deals_df.columns else 0
        
        st.sidebar.markdown("### 📊 HubSpot Data (from All Reps All Pipelines)")
        st.sidebar.caption(f"Total deals: {total_deals}")
        st.sidebar.caption(f"Total amount: ${total_amount:,.0f}")
        
        if 'Status' in deals_df.columns:
            unique_status = deals_df['Status'].unique().tolist()
            st.sidebar.caption(f"Status values: {unique_status}")
            
            # Show breakdown by Status
            for status in ['Expect', 'Commit', 'Best Case', 'Opportunity']:
                status_df = deals_df[deals_df['Status'] == status]
                if not status_df.empty:
                    st.sidebar.caption(f"  {status}: {len(status_df)} deals, ${status_df['Amount'].sum():,.0f}")
        
        if 'Q2 2026 Spillover' in deals_df.columns:
            unique_quarter = deals_df['Q2 2026 Spillover'].unique().tolist()
            st.sidebar.caption(f"Quarter values: {unique_quarter}")
    else:
        pass  # Debug info removed
        #st.sidebar.error(f"❌ HubSpot data has insufficient columns: {len(deals_df.columns) if not deals_df.empty else 0}")
    
    if not dashboard_df.empty:
        # Ensure we have the right column names
        if len(dashboard_df.columns) >= 2:
            dashboard_df.columns = ['Rep Name', 'Quota']
            dashboard_df['NetSuite Orders'] = 0  # Placeholder - actual data comes from invoices
            
            # Remove any empty rows and Team Total row (which would double the quota sum)
            dashboard_df = dashboard_df[dashboard_df['Rep Name'].notna() & (dashboard_df['Rep Name'] != '')]
            dashboard_df = dashboard_df[~dashboard_df['Rep Name'].str.contains('Team Total', case=False, na=False)]
            
            # Clean and convert numeric columns
            def clean_numeric(value):
                if pd.isna(value) or str(value).strip() == '':
                    return 0
                cleaned = str(value).replace(',', '').replace('$', '').replace(' ', '').strip()
                try:
                    return float(cleaned)
                except:
                    return 0
            
            dashboard_df['Quota'] = dashboard_df['Quota'].apply(clean_numeric)
    
    # Process invoice data
    if not invoices_df.empty:
        if len(invoices_df.columns) >= 15:
            # Map additional columns for Shopify identification
            rename_dict = {
                invoices_df.columns[0]: 'Invoice Number',
                invoices_df.columns[1]: 'Status',
                invoices_df.columns[2]: 'Date',
                invoices_df.columns[6]: 'Customer',
                invoices_df.columns[10]: 'Amount',
                invoices_df.columns[14]: 'Sales Rep'
            }
            
            # NEW: Map Corrected Customer Name (Column T - index 19) and Rep Master (Column U - index 20)
            if len(invoices_df.columns) > 19:
                rename_dict[invoices_df.columns[19]] = 'Corrected Customer Name'  # Column T
            if len(invoices_df.columns) > 20:
                rename_dict[invoices_df.columns[20]] = 'Rep Master'  # Column U
            
            # NEW: Map Product Type (Column Y - index 24)
            if len(invoices_df.columns) > 24:
                rename_dict[invoices_df.columns[24]] = 'Product Type'  # Column Y
            
            # NEW: Map Shipping (Column Q - index 16) and Tax (Column R - index 17) for shipping toggle
            if len(invoices_df.columns) > 16:
                rename_dict[invoices_df.columns[16]] = 'Amount_Shipping'  # Column Q - Amount (Shipping)
            if len(invoices_df.columns) > 17:
                rename_dict[invoices_df.columns[17]] = 'Amount_Tax'  # Column R - Amount (Transaction Tax Total)
            
            # Try to find HubSpot Pipeline and CSM columns
            for idx, col in enumerate(invoices_df.columns):
                col_str = str(col).lower()
                if 'hubspot' in col_str and 'pipeline' in col_str:
                    rename_dict[col] = 'HubSpot_Pipeline'
                elif col_str == 'csm' or 'csm' in col_str:
                    rename_dict[col] = 'CSM'
            
            invoices_df = invoices_df.rename(columns=rename_dict)
            
            # CRITICAL: Replace Sales Rep with Rep Master and Customer with Corrected Customer Name
            # This fixes the Shopify eCommerce invoices that weren't being applied to reps correctly
            if 'Rep Master' in invoices_df.columns:
                # Rep Master is the ONLY source of truth - completely replace Sales Rep
                invoices_df['Rep Master'] = invoices_df['Rep Master'].astype(str).str.strip()
                
                # Define invalid values that should be filtered out
                invalid_values = ['', 'nan', 'None', '#N/A', '#REF!', '#VALUE!', '#ERROR!']
                
                # FILTER OUT rows where Rep Master is invalid (including #N/A)
                # These rows won't count toward any revenue
                invoices_df = invoices_df[~invoices_df['Rep Master'].isin(invalid_values)]
                
                # Now replace Sales Rep with Rep Master for all remaining rows
                invoices_df['Sales Rep'] = invoices_df['Rep Master']
                # Drop the Rep Master column since we've copied it to Sales Rep
                invoices_df = invoices_df.drop(columns=['Rep Master'])
            else:
                st.sidebar.warning("⚠️ Rep Master column not found in invoices!")
            
            if 'Corrected Customer Name' in invoices_df.columns:
                # Corrected Customer Name takes priority - replace Customer with corrected values
                invoices_df['Corrected Customer Name'] = invoices_df['Corrected Customer Name'].astype(str).str.strip()
                invalid_values = ['', 'nan', 'None', '#N/A', '#REF!', '#VALUE!', '#ERROR!']
                mask = invoices_df['Corrected Customer Name'].isin(invalid_values)
                invoices_df.loc[~mask, 'Customer'] = invoices_df.loc[~mask, 'Corrected Customer Name']
                # Drop the Corrected Customer Name column since we've copied it to Customer
                invoices_df = invoices_df.drop(columns=['Corrected Customer Name'])
            
            def clean_numeric(value):
                if pd.isna(value) or str(value).strip() == '':
                    return 0
                cleaned = str(value).replace(',', '').replace('$', '').replace(' ', '').strip()
                try:
                    return float(cleaned)
                except:
                    return 0
            
            invoices_df['Amount'] = invoices_df['Amount'].apply(clean_numeric)
            invoices_df['Date'] = pd.to_datetime(invoices_df['Date'], errors='coerce')
            
            # NEW: Calculate Net_Amount (Amount without Shipping and Tax) for shipping toggle
            if 'Amount_Shipping' in invoices_df.columns:
                invoices_df['Amount_Shipping'] = invoices_df['Amount_Shipping'].apply(clean_numeric)
            else:
                invoices_df['Amount_Shipping'] = 0
            
            if 'Amount_Tax' in invoices_df.columns:
                invoices_df['Amount_Tax'] = invoices_df['Amount_Tax'].apply(clean_numeric)
            else:
                invoices_df['Amount_Tax'] = 0
            
            # Net_Amount = Transaction Total - Shipping - Tax
            invoices_df['Net_Amount'] = invoices_df['Amount'] - invoices_df['Amount_Shipping'] - invoices_df['Amount_Tax']
            
            # Filter to Q1 2026 only (1/1/2026 - 3/31/2026)
            # This should match exactly what your boss filters in the sheet
            q1_start = pd.Timestamp('2026-01-01')
            q1_end = pd.Timestamp('2026-03-31')
            
            # Apply date filter
            invoices_df = invoices_df[
                (invoices_df['Date'] >= q1_start) & 
                (invoices_df['Date'] <= q1_end)
            ]
            
            # Clean up Sales Rep field
            invoices_df['Sales Rep'] = invoices_df['Sales Rep'].astype(str).str.strip()
            
            # Filter out invalid Sales Reps BEFORE groupby
            # NOTE: We DO NOT filter Amount > 0 because credit memos (negative amounts) should reduce totals
            invoices_df = invoices_df[
                (invoices_df['Sales Rep'].notna()) & 
                (invoices_df['Sales Rep'] != '') &
                (invoices_df['Sales Rep'].str.lower() != 'nan') &
                (invoices_df['Sales Rep'].str.lower() != 'house')
            ]
            
            # CRITICAL: Remove duplicate invoices if they exist (keep first occurrence)
            if 'Invoice Number' in invoices_df.columns:
                before_dedupe = len(invoices_df)
                invoices_df = invoices_df.drop_duplicates(subset=['Invoice Number'], keep='first')
                after_dedupe = len(invoices_df)
                if before_dedupe != after_dedupe:
                    st.sidebar.warning(f"⚠️ Removed {before_dedupe - after_dedupe} duplicate invoices!")
            
            # Calculate invoice totals by rep - store both with and without shipping
            invoice_totals = invoices_df.groupby('Sales Rep')['Amount'].sum().reset_index()
            invoice_totals.columns = ['Rep Name', 'Invoice Total']
            
            # Also calculate Net_Amount totals (without shipping/tax)
            if 'Net_Amount' in invoices_df.columns:
                invoice_totals_net = invoices_df.groupby('Sales Rep')['Net_Amount'].sum().reset_index()
                invoice_totals_net.columns = ['Rep Name', 'Invoice Total Net']
                invoice_totals = invoice_totals.merge(invoice_totals_net, on='Rep Name', how='left')
                invoice_totals['Invoice Total Net'] = invoice_totals['Invoice Total Net'].fillna(0)
            else:
                invoice_totals['Invoice Total Net'] = invoice_totals['Invoice Total']
            
            dashboard_df['Rep Name'] = dashboard_df['Rep Name'].str.strip()
            
            dashboard_df = dashboard_df.merge(invoice_totals, on='Rep Name', how='left')
            dashboard_df['Invoice Total'] = dashboard_df['Invoice Total'].fillna(0)
            dashboard_df['Invoice Total Net'] = dashboard_df['Invoice Total Net'].fillna(0)
            
            # Store both values - NetSuite Orders will be the default (with shipping)
            # NetSuite Orders Net will be without shipping
            dashboard_df['NetSuite Orders'] = dashboard_df['Invoice Total']
            dashboard_df['NetSuite Orders Net'] = dashboard_df['Invoice Total Net']
            dashboard_df = dashboard_df.drop(['Invoice Total', 'Invoice Total Net'], axis=1)
            
            # Add Shopify ECommerce to dashboard if it has invoices but isn't in dashboard yet
            if 'Shopify ECommerce' in invoice_totals['Rep Name'].values:
                if 'Shopify ECommerce' not in dashboard_df['Rep Name'].values:
                    shopify_total = invoice_totals[invoice_totals['Rep Name'] == 'Shopify ECommerce']['Invoice Total'].iloc[0]
                    shopify_total_net = invoice_totals[invoice_totals['Rep Name'] == 'Shopify ECommerce']['Invoice Total Net'].iloc[0] if 'Invoice Total Net' in invoice_totals.columns else shopify_total
                    new_shopify_row = pd.DataFrame([{
                        'Rep Name': 'Shopify ECommerce',
                        'Quota': 0,
                        'NetSuite Orders': shopify_total,
                        'NetSuite Orders Net': shopify_total_net
                    }])
                    dashboard_df = pd.concat([dashboard_df, new_shopify_row], ignore_index=True)
    
    # Process sales orders data with NEW LOGIC
    if not sales_orders_df.empty:
        # Map column positions
        col_names = sales_orders_df.columns.tolist()
        
        rename_dict = {}
        
        # NEW: Map Internal Id column (Column A) - CRITICAL for NetSuite links
        if len(col_names) > 0:
            col_a_lower = str(col_names[0]).lower()
            if 'internal' in col_a_lower and 'id' in col_a_lower:
                rename_dict[col_names[0]] = 'Internal ID'
        
        # Find standard columns - only map FIRST occurrence
        for idx, col in enumerate(col_names):
            col_lower = str(col).lower()
            if 'status' in col_lower and 'Status' not in rename_dict.values():
                rename_dict[col] = 'Status'
            elif ('amount' in col_lower or 'total' in col_lower) and 'Amount' not in rename_dict.values():
                rename_dict[col] = 'Amount'
            elif ('sales rep' in col_lower or 'salesrep' in col_lower) and 'Sales Rep' not in rename_dict.values():
                rename_dict[col] = 'Sales Rep'
            elif 'customer' in col_lower and 'customer promise' not in col_lower and 'Customer' not in rename_dict.values():
                rename_dict[col] = 'Customer'
            elif ('doc' in col_lower or 'document' in col_lower) and 'Document Number' not in rename_dict.values():
                rename_dict[col] = 'Document Number'
        
        # Map specific columns by position (0-indexed) - be more careful
        if len(col_names) > 8 and 'Order Start Date' not in rename_dict.values():
            rename_dict[col_names[8]] = 'Order Start Date'  # Column I
        if len(col_names) > 11 and 'Customer Promise Date' not in rename_dict.values():
            rename_dict[col_names[11]] = 'Customer Promise Date'  # Column L
        if len(col_names) > 12 and 'Projected Date' not in rename_dict.values():
            rename_dict[col_names[12]] = 'Projected Date'  # Column M
        
        # NEW: Map Shipping and Tax columns by keyword search (more robust than position)
        for idx, col in enumerate(col_names):
            col_lower = str(col).lower()
            # Look for Amount (Shipping) column
            if 'amount' in col_lower and 'shipping' in col_lower and 'Amount_Shipping' not in rename_dict.values():
                rename_dict[col] = 'Amount_Shipping'
            # Look for Amount (Transaction Tax Total) column
            elif 'amount' in col_lower and 'tax' in col_lower and 'Amount_Tax' not in rename_dict.values():
                rename_dict[col] = 'Amount_Tax'
        
        # COLUMN POSITIONS - Updated after "Location (no hierarchy)" added at AC
        if len(col_names) > 28:
            rename_dict[col_names[28]] = 'Location No Hierarchy'  # Column AC - Location (no hierarchy)
        if len(col_names) > 29 and 'Pending Approval Date' not in rename_dict.values():
            rename_dict[col_names[29]] = 'Pending Approval Date'  # Column AD
        if len(col_names) > 30:
            rename_dict[col_names[30]] = 'Corrected Customer Name'  # Column AE
        if len(col_names) > 31:
            rename_dict[col_names[31]] = 'Rep Master'  # Column AF
        if len(col_names) > 32:
            rename_dict[col_names[32]] = 'Updated Status'  # Column AG - Pre-calculated SO status category
        
        # Rep Master fallback - search by column name if not found by position
        if 'Rep Master' not in rename_dict.values():
            for idx, col in enumerate(col_names):
                col_str = str(col).lower().strip()
                if 'rep master' in col_str:
                    rename_dict[col_names[idx]] = 'Rep Master'
                    break
        
        # NEW: Map PI || CSM column (Column G based on screenshot)
        for idx, col in enumerate(col_names):
            col_str = str(col).lower()
            if ('pi' in col_str and 'csm' in col_str) or col_str == 'pi || csm':
                rename_dict[col] = 'PI_CSM'
                break
        
        sales_orders_df = sales_orders_df.rename(columns=rename_dict)
        
        # CRITICAL: Replace Sales Rep with Rep Master and Customer with Corrected Customer Name
        # This fixes the Shopify eCommerce orders that weren't being applied to reps correctly
        if 'Rep Master' in sales_orders_df.columns:
            # Rep Master is the ONLY source of truth - completely replace Sales Rep
            sales_orders_df['Rep Master'] = sales_orders_df['Rep Master'].astype(str).str.strip()
            
            # Define invalid values that should be filtered out
            invalid_values = ['', 'nan', 'None', '#N/A', '#REF!', '#VALUE!', '#ERROR!']
            
            # FILTER OUT rows where Rep Master is invalid (including #N/A)
            # These rows won't count toward any revenue
            sales_orders_df = sales_orders_df[~sales_orders_df['Rep Master'].isin(invalid_values)]
            
            # Now replace Sales Rep with Rep Master for all remaining rows
            sales_orders_df['Sales Rep'] = sales_orders_df['Rep Master']
            # Drop the Rep Master column since we've copied it to Sales Rep
            sales_orders_df = sales_orders_df.drop(columns=['Rep Master'])
        
        if 'Corrected Customer Name' in sales_orders_df.columns:
            # Corrected Customer Name takes priority - replace Customer with corrected values
            sales_orders_df['Customer'] = sales_orders_df['Corrected Customer Name']
            # Drop the Corrected Customer Name column since we've copied it to Customer
            sales_orders_df = sales_orders_df.drop(columns=['Corrected Customer Name'])
        
        # CRITICAL: Remove any duplicate columns that may have been created
        if sales_orders_df.columns.duplicated().any():
            pass  # Debug info removed
            #st.sidebar.warning(f"⚠️ Removed duplicate columns in Sales Orders: {sales_orders_df.columns[sales_orders_df.columns.duplicated()].tolist()}")
            sales_orders_df = sales_orders_df.loc[:, ~sales_orders_df.columns.duplicated()]
        
        # Clean numeric values
        def clean_numeric_so(value):
            value_str = str(value).strip()
            if value_str == '' or value_str == 'nan' or value_str == 'None':
                return 0
            cleaned = value_str.replace(',', '').replace('$', '').replace(' ', '')
            try:
                return float(cleaned)
            except:
                return 0
        
        if 'Amount' in sales_orders_df.columns:
            sales_orders_df['Amount'] = sales_orders_df['Amount'].apply(clean_numeric_so)
        
        # NEW: Calculate Net_Amount (Amount without Shipping and Tax) for shipping toggle
        if 'Amount_Shipping' in sales_orders_df.columns:
            sales_orders_df['Amount_Shipping'] = sales_orders_df['Amount_Shipping'].apply(clean_numeric_so)
        else:
            sales_orders_df['Amount_Shipping'] = 0
        
        if 'Amount_Tax' in sales_orders_df.columns:
            sales_orders_df['Amount_Tax'] = sales_orders_df['Amount_Tax'].apply(clean_numeric_so)
        else:
            sales_orders_df['Amount_Tax'] = 0
        
        # Net_Amount = Transaction Total - Shipping - Tax
        if 'Amount' in sales_orders_df.columns:
            sales_orders_df['Net_Amount'] = sales_orders_df['Amount'] - sales_orders_df['Amount_Shipping'] - sales_orders_df['Amount_Tax']
        
        if 'Sales Rep' in sales_orders_df.columns:
            sales_orders_df['Sales Rep'] = sales_orders_df['Sales Rep'].astype(str).str.strip()
        
        if 'Status' in sales_orders_df.columns:
            sales_orders_df['Status'] = sales_orders_df['Status'].astype(str).str.strip()
        
        # Convert date columns - handle 2-digit years correctly (26 = 2026, not 1926)
        date_columns = ['Order Start Date', 'Customer Promise Date', 'Projected Date', 'Pending Approval Date']
        for col in date_columns:
            if col in sales_orders_df.columns:
                # First try standard parsing
                sales_orders_df[col] = pd.to_datetime(sales_orders_df[col], errors='coerce')
                
                # Fix any dates that got parsed as 1900s (2-digit year issue)
                # If year < 2000, add 100 years (e.g., 1926 -> 2026)
                if sales_orders_df[col].notna().any():
                    mask = (sales_orders_df[col].dt.year < 2000) & (sales_orders_df[col].notna())
                    if mask.any():
                        sales_orders_df.loc[mask, col] = sales_orders_df.loc[mask, col] + pd.DateOffset(years=100)
        
        # Filter to include Pending Approval, Pending Fulfillment, AND Pending Billing/Partially Fulfilled
        if 'Status' in sales_orders_df.columns:
            sales_orders_df = sales_orders_df[
                sales_orders_df['Status'].isin(['Pending Approval', 'Pending Fulfillment', 'Pending Billing/Partially Fulfilled'])
            ]
        
        # Calculate age for Old Pending Approval
        if 'Order Start Date' in sales_orders_df.columns:
            today = pd.Timestamp.now()
            
            def business_days_between(start_date, end_date):
                if pd.isna(start_date):
                    return 0
                days = pd.bdate_range(start=start_date, end=end_date).size - 1
                return max(0, days)
            
            sales_orders_df['Age_Business_Days'] = sales_orders_df['Order Start Date'].apply(
                lambda x: business_days_between(x, today)
            )
        else:
            sales_orders_df['Age_Business_Days'] = 0
        
        # Remove rows without amount or sales rep
        if 'Amount' in sales_orders_df.columns and 'Sales Rep' in sales_orders_df.columns:
            sales_orders_df = sales_orders_df[
                (sales_orders_df['Amount'] > 0) & 
                (sales_orders_df['Sales Rep'].notna()) & 
                (sales_orders_df['Sales Rep'] != '') &
                (sales_orders_df['Sales Rep'] != 'nan') &
                (~sales_orders_df['Sales Rep'].str.lower().isin(['house']))
            ]
    else:
        st.warning("Could not find required columns in _NS_SalesOrders_Data")
        sales_orders_df = pd.DataFrame()
    
    return deals_df, dashboard_df, invoices_df, sales_orders_df, q4_push_df

def store_snapshot(deals_df, dashboard_df, invoices_df, sales_orders_df, q4_push_df=None):
    """
    Store a snapshot of current data for change tracking
    """
    snapshot = {
        'timestamp': datetime.now(),
        'deals': deals_df.copy() if not deals_df.empty else pd.DataFrame(),
        'dashboard': dashboard_df.copy() if not dashboard_df.empty else pd.DataFrame(),
        'invoices': invoices_df.copy() if not invoices_df.empty else pd.DataFrame(),
        'sales_orders': sales_orders_df.copy() if not sales_orders_df.empty else pd.DataFrame()
    }
    
    # Store in session state
    if 'previous_snapshot' not in st.session_state:
        st.session_state.previous_snapshot = snapshot
    else:
        # Move current to previous
        st.session_state.previous_snapshot = st.session_state.current_snapshot
    
    st.session_state.current_snapshot = snapshot

def detect_changes(current, previous):
    """
    Detect changes between current and previous snapshots
    Returns a dictionary of changes
    """
    changes = {
        'new_invoices': [],
        'new_sales_orders': [],
        'updated_deals': [],
        'rep_changes': {}
    }
    
    if previous is None:
        return changes
    
    try:
        # Detect new invoices
        if not current['invoices'].empty and not previous['invoices'].empty:
            if 'Document Number' in current['invoices'].columns:
                current_invoices = set(current['invoices']['Document Number'].dropna())
                previous_invoices = set(previous['invoices']['Document Number'].dropna())
                new_invoices = current_invoices - previous_invoices
                changes['new_invoices'] = list(new_invoices)
        
        # Detect new sales orders
        if not current['sales_orders'].empty and not previous['sales_orders'].empty:
            if 'Document Number' in current['sales_orders'].columns:
                current_orders = set(current['sales_orders']['Document Number'].dropna())
                previous_orders = set(previous['sales_orders']['Document Number'].dropna())
                new_orders = current_orders - previous_orders
                changes['new_sales_orders'] = list(new_orders)
        
        # Detect rep-level changes in forecasts
        if not current['dashboard'].empty and not previous['dashboard'].empty:
            if 'Rep Name' in current['dashboard'].columns:
                for rep in current['dashboard']['Rep Name'].unique():
                    current_rep = current['dashboard'][current['dashboard']['Rep Name'] == rep]
                    previous_rep = previous['dashboard'][previous['dashboard']['Rep Name'] == rep]
                    
                    if not previous_rep.empty:
                        rep_change = {}
                        
                        # Check for changes in key metrics
                        if 'Quota' in current_rep.columns:
                            current_val = pd.to_numeric(current_rep['Quota'].iloc[0], errors='coerce')
                            previous_val = pd.to_numeric(previous_rep['Quota'].iloc[0], errors='coerce')
                            if not pd.isna(current_val) and not pd.isna(previous_val):
                                if current_val != previous_val:
                                    rep_change['goal_change'] = current_val - previous_val
                        
                        if 'NetSuite Orders' in current_rep.columns:
                            current_val = pd.to_numeric(current_rep['NetSuite Orders'].iloc[0], errors='coerce')
                            previous_val = pd.to_numeric(previous_rep['NetSuite Orders'].iloc[0], errors='coerce')
                            if not pd.isna(current_val) and not pd.isna(previous_val):
                                if current_val != previous_val:
                                    rep_change['actual_change'] = current_val - previous_val
                        
                        if rep_change:
                            changes['rep_changes'][rep] = rep_change
    
    except Exception as e:
        st.error(f"Error detecting changes: {str(e)}")
    
    return changes

def show_change_dialog(changes):
    """
    Display a dialog showing what changed since last refresh
    """
    if not any([changes['new_invoices'], changes['new_sales_orders'], changes['rep_changes']]):
        st.info("ℹ️ No changes detected since last refresh")
        return
    
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                 padding: 20px; border-radius: 10px; color: white; margin: 15px 0;'>
        <h3 style='color: white; margin: 0 0 10px 0;'>🔄 Changes Detected!</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if changes['new_invoices']:
            st.metric("New Invoices", len(changes['new_invoices']))
            with st.expander("View New Invoices"):
                for inv in changes['new_invoices'][:10]:  # Show first 10
                    st.write(f"• {inv}")
                if len(changes['new_invoices']) > 10:
                    st.caption(f"...and {len(changes['new_invoices']) - 10} more")
    
    with col2:
        if changes['new_sales_orders']:
            st.metric("New Sales Orders", len(changes['new_sales_orders']))
            with st.expander("View New Sales Orders"):
                for so in changes['new_sales_orders'][:10]:
                    st.write(f"• {so}")
                if len(changes['new_sales_orders']) > 10:
                    st.caption(f"...and {len(changes['new_sales_orders']) - 10} more")
    
    with col3:
        if changes['rep_changes']:
            st.metric("Reps with Changes", len(changes['rep_changes']))
            with st.expander("View Rep Changes"):
                for rep, change in changes['rep_changes'].items():
                    st.write(f"**{rep}:**")
                    if 'actual_change' in change:
                        delta = change['actual_change']
                        color = "green" if delta > 0 else "red"
                        st.markdown(f"- Actual: <span style='color:{color}'>${delta:,.0f}</span>", unsafe_allow_html=True)
                    if 'goal_change' in change:
                        st.markdown(f"- Goal: ${change['goal_change']:,.0f}")

def create_dod_audit_section(deals_df, dashboard_df, invoices_df, sales_orders_df):
    """
    Create a day-over-day audit section showing changes
    """
    st.markdown("### 📊 Day-Over-Day Audit Snapshot")
    st.caption("Track changes in key metrics to audit data quality")
    
    # Get previous snapshot if it exists
    if 'previous_snapshot' in st.session_state and st.session_state.previous_snapshot:
        previous = st.session_state.previous_snapshot
        
        # Calculate time difference
        time_diff = datetime.now() - previous['timestamp']
        hours_ago = time_diff.total_seconds() / 3600
        
        st.markdown(f"""
        <div class='audit-section'>
            <p><strong>Previous Snapshot:</strong> {previous['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} 
            ({hours_ago:.1f} hours ago)</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Calculate all current metrics
        current_metrics = calculate_team_metrics(deals_df, dashboard_df)
        previous_metrics = calculate_team_metrics(previous['deals'], previous['dashboard'])
        
        # Helper function to calculate sales order metrics using Updated Status column
        def calculate_so_metrics(so_df):
            metrics = {
                'pending_fulfillment': 0,
                'pending_fulfillment_no_date': 0,
                'pending_approval': 0,
                'pending_approval_no_date': 0,
                'pending_approval_old': 0
            }
            
            if so_df.empty:
                return metrics
            
            so_df = so_df.copy()
            so_df['Amount_Numeric'] = pd.to_numeric(so_df.get('Amount', 0), errors='coerce')
            
            # Use Updated Status column if available
            if 'Updated Status' in so_df.columns:
                so_df['Updated_Status_Clean'] = so_df['Updated Status'].astype(str).str.strip()
                
                # Pending Fulfillment with date (Ext + Int)
                pf_date_ext = so_df[so_df['Updated_Status_Clean'] == 'PF with Date (Ext)']['Amount_Numeric'].sum()
                pf_date_int = so_df[so_df['Updated_Status_Clean'] == 'PF with Date (Int)']['Amount_Numeric'].sum()
                metrics['pending_fulfillment'] = pf_date_ext + pf_date_int
                
                # Pending Fulfillment no date (Ext + Int)
                pf_nodate_ext = so_df[so_df['Updated_Status_Clean'] == 'PF No Date (Ext)']['Amount_Numeric'].sum()
                pf_nodate_int = so_df[so_df['Updated_Status_Clean'] == 'PF No Date (Int)']['Amount_Numeric'].sum()
                metrics['pending_fulfillment_no_date'] = pf_nodate_ext + pf_nodate_int
                
                # Pending Approval with date
                metrics['pending_approval'] = so_df[so_df['Updated_Status_Clean'] == 'PA with Date']['Amount_Numeric'].sum()
                
                # Pending Approval no date
                metrics['pending_approval_no_date'] = so_df[so_df['Updated_Status_Clean'] == 'PA No Date']['Amount_Numeric'].sum()
                
                # Pending Approval old (>2 weeks)
                metrics['pending_approval_old'] = so_df[so_df['Updated_Status_Clean'] == 'PA Old (>2 Weeks)']['Amount_Numeric'].sum()
            
            return metrics
        
        current_so_metrics = calculate_so_metrics(sales_orders_df)
        previous_so_metrics = calculate_so_metrics(previous['sales_orders'])
        
        # Team-level changes - organized by data category
        st.markdown("#### 👥 Team Overview")
        
        # Row 1: Invoiced & Shipped
        st.markdown("**💰 Invoiced & Shipped**")
        inv_col1, inv_col2, inv_col3, inv_col4 = st.columns(4)
        
        with inv_col1:
            current_invoices = len(invoices_df) if not invoices_df.empty else 0
            previous_invoices = len(previous['invoices']) if not previous['invoices'].empty else 0
            delta_invoices = current_invoices - previous_invoices
            st.metric("Total Invoices", current_invoices, delta=delta_invoices)
        
        with inv_col2:
            if not invoices_df.empty and 'Amount' in invoices_df.columns:
                current_inv_total = pd.to_numeric(invoices_df['Amount'], errors='coerce').sum()
            else:
                current_inv_total = 0
            
            if not previous['invoices'].empty and 'Amount' in previous['invoices'].columns:
                previous_inv_total = pd.to_numeric(previous['invoices']['Amount'], errors='coerce').sum()
            else:
                previous_inv_total = 0
            
            delta_inv_amount = current_inv_total - previous_inv_total
            st.metric("Invoice Amount", f"${current_inv_total:,.0f}", delta=f"${delta_inv_amount:,.0f}")
        
        with inv_col3:
            # NetSuite Orders from dashboard
            current_ns_orders = current_metrics.get('orders', 0)
            previous_ns_orders = previous_metrics.get('orders', 0)
            delta_ns = current_ns_orders - previous_ns_orders
            st.metric("NS Orders (Dashboard)", f"${current_ns_orders:,.0f}", delta=f"${delta_ns:,.0f}")
        
        with inv_col4:
            # Average invoice size
            if current_invoices > 0:
                current_avg = current_inv_total / current_invoices
            else:
                current_avg = 0
            
            if previous_invoices > 0:
                previous_avg = previous_inv_total / previous_invoices
            else:
                previous_avg = 0
            
            delta_avg = current_avg - previous_avg
            st.metric("Avg Invoice", f"${current_avg:,.0f}", delta=f"${delta_avg:,.0f}")
        
        # Row 2: Sales Orders
        st.markdown("**📦 Sales Orders**")
        so_col1, so_col2, so_col3, so_col4 = st.columns(4)
        
        with so_col1:
            current_orders = len(sales_orders_df) if not sales_orders_df.empty else 0
            previous_orders = len(previous['sales_orders']) if not previous['sales_orders'].empty else 0
            delta_orders = current_orders - previous_orders
            st.metric("Total Sales Orders", current_orders, delta=delta_orders)
        
        with so_col2:
            delta_pf = current_so_metrics['pending_fulfillment'] - previous_so_metrics['pending_fulfillment']
            st.metric("Pending Fulfillment (with date)", 
                     f"${current_so_metrics['pending_fulfillment']:,.0f}", 
                     delta=f"${delta_pf:,.0f}")
        
        with so_col3:
            delta_pa = current_so_metrics['pending_approval'] - previous_so_metrics['pending_approval']
            st.metric("Pending Approval (with date)", 
                     f"${current_so_metrics['pending_approval']:,.0f}", 
                     delta=f"${delta_pa:,.0f}")
        
        with so_col4:
            delta_pf_nd = current_so_metrics['pending_fulfillment_no_date'] - previous_so_metrics['pending_fulfillment_no_date']
            st.metric("Pending Fulfillment (no date)", 
                     f"${current_so_metrics['pending_fulfillment_no_date']:,.0f}", 
                     delta=f"${delta_pf_nd:,.0f}")
        
        # Row 3: Sales Orders Continued
        so2_col1, so2_col2, so2_col3, so2_col4 = st.columns(4)
        
        with so2_col1:
            delta_pa_nd = current_so_metrics['pending_approval_no_date'] - previous_so_metrics['pending_approval_no_date']
            st.metric("Pending Approval (no date)", 
                     f"${current_so_metrics['pending_approval_no_date']:,.0f}", 
                     delta=f"${delta_pa_nd:,.0f}")
        
        with so2_col2:
            delta_pa_old = current_so_metrics['pending_approval_old'] - previous_so_metrics['pending_approval_old']
            st.metric("Pending Approval (>2 weeks)", 
                     f"${current_so_metrics['pending_approval_old']:,.0f}", 
                     delta=f"${delta_pa_old:,.0f}")
        
        with so2_col3:
            # Total SO Amount
            if not sales_orders_df.empty and 'Amount' in sales_orders_df.columns:
                current_so_total = pd.to_numeric(sales_orders_df['Amount'], errors='coerce').sum()
            else:
                current_so_total = 0
            
            if not previous['sales_orders'].empty and 'Amount' in previous['sales_orders'].columns:
                previous_so_total = pd.to_numeric(previous['sales_orders']['Amount'], errors='coerce').sum()
            else:
                previous_so_total = 0
            
            delta_so_total = current_so_total - previous_so_total
            st.metric("Total SO Amount", f"${current_so_total:,.0f}", delta=f"${delta_so_total:,.0f}")
        
        # Row 4: HubSpot Deals
        st.markdown("**🎯 HubSpot Deals**")
        hs_col1, hs_col2, hs_col3, hs_col4 = st.columns(4)
        
        with hs_col1:
            current_deals = len(deals_df) if not deals_df.empty else 0
            previous_deals = len(previous['deals']) if not previous['deals'].empty else 0
            delta_deals = current_deals - previous_deals
            st.metric("Total Deals", current_deals, delta=delta_deals)
        
        with hs_col2:
            current_commit = current_metrics.get('expect_commit', 0)
            previous_commit = previous_metrics.get('expect_commit', 0)
            delta_commit = current_commit - previous_commit
            st.metric("HubSpot Commit", f"${current_commit:,.0f}", delta=f"${delta_commit:,.0f}")
        
        with hs_col3:
            # Calculate HubSpot Expect separately
            def get_expect_amount(df):
                if df.empty or 'Status' not in df.columns:
                    return 0
                df = df.copy()
                df['Amount_Numeric'] = pd.to_numeric(df.get('Amount', 0), errors='coerce')
                # Use spillover column - handles both old and new column names
                spillover_col = get_spillover_column(df)
                if spillover_col:
                    q1_mask = is_q1_deal(df, spillover_col)
                    q1_deals = df[q1_mask]
                else:
                    q1_deals = df
                return q1_deals[q1_deals['Status'] == 'Expect']['Amount_Numeric'].sum()
            
            current_expect = get_expect_amount(deals_df)
            previous_expect = get_expect_amount(previous['deals'])
            delta_expect = current_expect - previous_expect
            st.metric("HubSpot Expect", f"${current_expect:,.0f}", delta=f"${delta_expect:,.0f}")
        
        with hs_col4:
            # Calculate HubSpot Best Case
            def get_best_case_amount(df):
                if df.empty or 'Status' not in df.columns:
                    return 0
                df = df.copy()
                df['Amount_Numeric'] = pd.to_numeric(df.get('Amount', 0), errors='coerce')
                # Use spillover column - handles both old and new column names
                spillover_col = get_spillover_column(df)
                if spillover_col:
                    q1_mask = is_q1_deal(df, spillover_col)
                    q1_deals = df[q1_mask]
                else:
                    q1_deals = df
                return q1_deals[q1_deals['Status'] == 'Best Case']['Amount_Numeric'].sum()
            
            current_bc = get_best_case_amount(deals_df)
            previous_bc = get_best_case_amount(previous['deals'])
            delta_bc = current_bc - previous_bc
            st.metric("HubSpot Best Case", f"${current_bc:,.0f}", delta=f"${delta_bc:,.0f}")
        
        # Row 5: HubSpot Continued + Q2 Spillover
        hs2_col1, hs2_col2, hs2_col3, hs2_col4 = st.columns(4)
        
        with hs2_col1:
            # Calculate HubSpot Opportunity
            def get_opportunity_amount(df):
                if df.empty or 'Status' not in df.columns:
                    return 0
                df = df.copy()
                df['Amount_Numeric'] = pd.to_numeric(df.get('Amount', 0), errors='coerce')
                # Use spillover column - handles both old and new column names
                spillover_col = get_spillover_column(df)
                if spillover_col:
                    q1_mask = is_q1_deal(df, spillover_col)
                    q1_deals = df[q1_mask]
                else:
                    q1_deals = df
                return q1_deals[q1_deals['Status'] == 'Opportunity']['Amount_Numeric'].sum()
            
            current_opp = get_opportunity_amount(deals_df)
            previous_opp = get_opportunity_amount(previous['deals'])
            delta_opp = current_opp - previous_opp
            st.metric("HubSpot Opportunity", f"${current_opp:,.0f}", delta=f"${delta_opp:,.0f}")
        
        with hs2_col2:
            current_q2 = current_metrics.get('q1_spillover_expect_commit', 0)  # Key mapped to Q2
            previous_q2 = previous_metrics.get('q1_spillover_expect_commit', 0)
            delta_q2 = current_q2 - previous_q2
            st.metric("Q2 Spillover - Expect/Commit", f"${current_q2:,.0f}", delta=f"${delta_q2:,.0f}")
        
        # Rep-level changes
        st.markdown("#### 👤 Rep-Level Changes")
        
        if not dashboard_df.empty and not previous['dashboard'].empty:
            rep_comparison = []
            
            for rep in dashboard_df['Rep Name'].unique():
                current_rep = dashboard_df[dashboard_df['Rep Name'] == rep]
                previous_rep = previous['dashboard'][previous['dashboard']['Rep Name'] == rep]
                
                if not previous_rep.empty:
                    rep_data = {'Rep': rep}
                    
                    # NetSuite Orders change
                    if 'NetSuite Orders' in current_rep.columns:
                        current_val = pd.to_numeric(current_rep['NetSuite Orders'].iloc[0], errors='coerce')
                        previous_val = pd.to_numeric(previous_rep['NetSuite Orders'].iloc[0], errors='coerce')
                        if not pd.isna(current_val) and not pd.isna(previous_val):
                            rep_data['Current Actual'] = current_val
                            rep_data['Previous Actual'] = previous_val
                            rep_data['Δ Actual'] = current_val - previous_val
                    
                    if len(rep_data) > 1:  # If we have any changes
                        rep_comparison.append(rep_data)
            
            if rep_comparison:
                comparison_df = pd.DataFrame(rep_comparison)
                
                # Format for display
                if 'Δ Actual' in comparison_df.columns:
                    comparison_df = comparison_df[comparison_df['Δ Actual'] != 0]
                
                if not comparison_df.empty:
                    st.dataframe(
                        comparison_df.style.format({
                            'Current Actual': '${:,.0f}',
                            'Previous Actual': '${:,.0f}',
                            'Δ Actual': '${:,.0f}'
                        }),
                        use_container_width=True
                    )
                else:
                    st.info("No significant changes in rep metrics")
            else:
                st.info("No rep-level data available for comparison")
        
    else:
        st.info("📸 No previous snapshot available. Changes will be tracked after the next refresh.")

def display_invoices_drill_down(invoices_df, rep_name=None):
    """
    Display invoices with drill-down capability, similar to sales orders
    """
    st.markdown("### 💰 Invoices Detail")
    
    # Determine which amount column to use based on shipping toggle
    include_shipping = st.session_state.get('include_shipping', True)
    amount_col = 'Amount' if include_shipping else 'Net_Amount'
    caption_suffix = "" if include_shipping else " (excluding shipping & tax)"
    st.caption(f"Completed and billed orders from NetSuite{caption_suffix}")
    
    if invoices_df.empty:
        st.info("No invoice data available")
        return
    
    # Filter by rep if specified
    if rep_name and 'Sales Rep' in invoices_df.columns:
        filtered_invoices = invoices_df[invoices_df['Sales Rep'] == rep_name].copy()
    else:
        filtered_invoices = invoices_df.copy()
    
    if filtered_invoices.empty:
        st.info(f"No invoices found{' for ' + rep_name if rep_name else ''}")
        return
    
    # Calculate totals using the appropriate column
    total_invoiced = 0
    if amount_col in filtered_invoices.columns:
        filtered_invoices['Amount_Numeric'] = pd.to_numeric(filtered_invoices[amount_col], errors='coerce')
        total_invoiced = filtered_invoices['Amount_Numeric'].sum()
    elif 'Amount' in filtered_invoices.columns:
        # Fallback to Amount if Net_Amount doesn't exist
        filtered_invoices['Amount_Numeric'] = pd.to_numeric(filtered_invoices['Amount'], errors='coerce')
        total_invoiced = filtered_invoices['Amount_Numeric'].sum()
    
    # Display summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Invoices", len(filtered_invoices))
    
    with col2:
        st.metric("Total Amount", f"${total_invoiced:,.0f}")
    
    with col3:
        if len(filtered_invoices) > 0 and total_invoiced > 0:
            avg_invoice = total_invoiced / len(filtered_invoices)
            st.metric("Avg Invoice", f"${avg_invoice:,.0f}")
    
    # Display invoices table
    with st.expander("📋 View All Invoices", expanded=False):
        display_columns = []
        possible_columns = [
            'Document Number', 'Transaction Date', 'Account Name', 'Customer',
            'Amount', 'Status', 'Sales Rep', 'Sales Order #', 'Terms'
        ]
        
        for col in possible_columns:
            if col in filtered_invoices.columns:
                display_columns.append(col)
        
        if display_columns:
            display_df = filtered_invoices[display_columns].copy()
            
            # Format currency - only if we have both Amount and Amount_Numeric
            if 'Amount' in display_df.columns and 'Amount_Numeric' in filtered_invoices.columns:
                # Use the index to align properly
                display_df['Amount'] = filtered_invoices.loc[display_df.index, 'Amount_Numeric'].apply(
                    lambda x: f"${x:,.0f}" if not pd.isna(x) else ""
                )
            
            # Enhanced dataframe with column config (Gemini enhancement)
            column_config = {}
            
            if 'Amount' in display_df.columns and 'Amount_Numeric' in filtered_invoices.columns:
                max_amount = filtered_invoices['Amount_Numeric'].max()
                if max_amount > 0:
                    column_config['Amount'] = st.column_config.ProgressColumn(
                        "Invoice Value",
                        format="$%.0f",
                        min_value=0,
                        max_value=max_amount,
                        help="Size relative to largest invoice"
                    )
            
            if 'Date' in display_df.columns:
                column_config['Date'] = st.column_config.DateColumn(
                    "Invoice Date",
                    format="MMM DD, YYYY",
                    help="Date invoice was created"
                )
            
            if '🔗 NetSuite' in display_df.columns:
                column_config['🔗 NetSuite'] = st.column_config.LinkColumn(
                    "View",
                    display_text="↗️ Open",
                    help="Open in NetSuite"
                )
            
            st.dataframe(
                display_df, 
                use_container_width=True, 
                hide_index=True,
                column_config=column_config if column_config else None
            )
        else:
            st.dataframe(filtered_invoices, use_container_width=True, hide_index=True)

def build_your_own_forecast_section(metrics, quota, rep_name=None, deals_df=None, invoices_df=None, sales_orders_df=None, q4_push_df=None):
    """
    Refined Interactive Forecast Builder (v6 - Robust Export Edition)
    - Captures 'Customize' selections for export
    - Includes detailed Summary + Line Item export
    - Displays SO#, Links, and Dates safely
    """
    st.markdown("### 🎯 Build Your Own Forecast")
    st.caption("Select components to include. Expand sections to see details.")
    
    # --- LOAD Q4 PLANNING STATUS FROM GOOGLE SHEET ---
    st.markdown("---")
    
    # Initialize session state for planning status
    planning_key = f'planning_status_{rep_name}'
    if planning_key not in st.session_state:
        st.session_state[planning_key] = {}
    
    # Planning status feature removed for Q1 dashboard
    # (The Q4 Push sheet is not used in Q1)
    
    # Clear buttons - Enhanced to include selections
    if st.session_state[planning_key]:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Planning Status", key=f"clear_planning_{rep_name}"):
                # Clear planning status only
                st.session_state[planning_key] = {}
                st.success("✅ Planning status cleared")
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear All Selections", key=f"clear_selections_{rep_name}"):
                # Clear planning status
                st.session_state[planning_key] = {}
                
                # Clear all checkbox states for this rep
                keys_to_clear = [k for k in st.session_state.keys() 
                                 if (k.startswith(f"chk_") or 
                                     k.startswith(f"unselected_") or
                                     k.startswith(f"tgl_")) 
                                 and k.endswith(f"_{rep_name}")]
                for key in keys_to_clear:
                    del st.session_state[key]
                
                st.success("✅ All selections cleared")
                st.rerun()
    
    st.markdown("---")
    
    # Helper function to get planning status for an ID
    def get_planning_status(id_value):
        """Get planning status (IN/OUT/MAYBE) for a given SO# or Deal ID"""
        if not id_value or pd.isna(id_value):
            return None
        id_str = str(id_value).strip()
        item_data = st.session_state[planning_key].get(id_str)
        if item_data:
            # Handle both old format (string) and new format (dict)
            if isinstance(item_data, dict):
                return item_data.get('status')
            else:
                return item_data  # Backward compatibility
        return None
    
    def get_planning_notes(id_value):
        """Get planning notes for a given SO# or Deal ID"""
        if not id_value or pd.isna(id_value):
            return ''
        id_str = str(id_value).strip()
        item_data = st.session_state[planning_key].get(id_str)
        if item_data and isinstance(item_data, dict):
            return item_data.get('notes', '')
        return ''
    
    def update_planning_data(id_value, status=None, notes=None):
        """Update planning status and/or notes for a given ID"""
        if not id_value or pd.isna(id_value):
            return
        id_str = str(id_value).strip()
        
        # Get existing data or create new
        if id_str not in st.session_state[planning_key]:
            st.session_state[planning_key][id_str] = {'status': None, 'notes': ''}
        
        # Ensure it's a dict (convert old string format if needed)
        if isinstance(st.session_state[planning_key][id_str], str):
            st.session_state[planning_key][id_str] = {
                'status': st.session_state[planning_key][id_str],
                'notes': ''
            }
        
        # Update fields
        if status is not None:
            st.session_state[planning_key][id_str]['status'] = status.upper()
        if notes is not None:
            st.session_state[planning_key][id_str]['notes'] = notes
    
    # --- 1. PREPARE DATA LOCALLY ---
    
    # Helper to grab a column by Index (Safe Fallback)
    def get_col_by_index(df, index):
        if df is not None and len(df.columns) > index:
            return df.iloc[:, index]
        return pd.Series()

    # Prepare Sales Order Data
    if sales_orders_df is not None and not sales_orders_df.empty:
        # Filter for Rep
        if rep_name:
            if 'Sales Rep' in sales_orders_df.columns:
                so_data = sales_orders_df[sales_orders_df['Sales Rep'] == rep_name].copy()
            else:
                so_data = sales_orders_df.copy() 
        else:
            so_data = sales_orders_df.copy()
            
        # --- GRAB RAW COLUMNS BY INDEX ---
        so_data['Display_SO_Num'] = get_col_by_index(so_data, 1)        # Col B: SO#
        so_data['Display_PF_Date'] = pd.to_datetime(get_col_by_index(so_data, 9), errors='coerce') # Col J: PF Date
        so_data['Display_Promise_Date'] = pd.to_datetime(get_col_by_index(so_data, 11), errors='coerce') # Col L
        so_data['Display_Projected_Date'] = pd.to_datetime(get_col_by_index(so_data, 12), errors='coerce') # Col M
        so_data['Display_Type'] = get_col_by_index(so_data, 17).fillna('Standard') # Col R: Order Type
        
        # Use renamed column if available, otherwise try by index
        if 'Pending Approval Date' in so_data.columns:
            so_data['Display_PA_Date'] = pd.to_datetime(so_data['Pending Approval Date'], errors='coerce')
        else:
            so_data['Display_PA_Date'] = pd.to_datetime(get_col_by_index(so_data, 29), errors='coerce') # Col AD: PA Date

        # Determine which amount column to use based on shipping toggle
        include_shipping = st.session_state.get('include_shipping', True)
        so_amount_col = 'Amount' if include_shipping else 'Net_Amount'
        
        # Use the appropriate amount column
        if so_amount_col in so_data.columns:
            so_data['Amount_Numeric'] = pd.to_numeric(so_data[so_amount_col], errors='coerce').fillna(0)
        elif 'Amount' in so_data.columns:
            # Fallback to Amount if Net_Amount doesn't exist
            so_data['Amount_Numeric'] = pd.to_numeric(so_data['Amount'], errors='coerce').fillna(0)
        else:
            so_data['Amount_Numeric'] = 0
    else:
        so_data = pd.DataFrame()

    # Prepare HubSpot Data
    if deals_df is not None and not deals_df.empty and 'Deal Owner' in deals_df.columns:
        if rep_name:
            hs_data = deals_df[deals_df['Deal Owner'] == rep_name].copy()
        else:
            hs_data = deals_df.copy()
            
        # Map Deal Type (Column N - Index 13)
        hs_data['Display_Type'] = get_col_by_index(hs_data, 13).fillna('Standard')
        
        # Get Pending Approval Date from Column P (index 15)
        if 'Pending Approval Date' in hs_data.columns:
            hs_data['Display_PA_Date'] = pd.to_datetime(hs_data['Pending Approval Date'], errors='coerce')
        else:
            # Fallback to column index 15 (Column P)
            hs_data['Display_PA_Date'] = pd.to_datetime(get_col_by_index(hs_data, 15), errors='coerce')

        if 'Amount' in hs_data.columns:
            hs_data['Amount_Numeric'] = pd.to_numeric(hs_data['Amount'], errors='coerce').fillna(0)
        
        # Add Probability-adjusted amount column
        if 'Probability Rev' in hs_data.columns:
            hs_data['Prob_Amount_Numeric'] = pd.to_numeric(hs_data['Probability Rev'], errors='coerce').fillna(0)
        else:
            # If no probability column, default to same as Amount
            hs_data['Prob_Amount_Numeric'] = hs_data['Amount_Numeric'] if 'Amount_Numeric' in hs_data.columns else 0
    else:
        hs_data = pd.DataFrame()

    # --- 2. CATEGORY DEFINITIONS ---
    
    invoiced_shipped = metrics.get('orders', 0)
    
    ns_categories = {
        'PF_Date_Ext':   {'label': 'Pending Fulfillment (Date) - External'},
        'PF_Date_Int':   {'label': 'Pending Fulfillment (Date) - Internal'},
        'PF_Q4_Spillover':  {'label': '⏪ PF Spillover (Q4 2025)'},
        'PF_Q2_Spillover':  {'label': '⏩ PF Spillover (Q2 2026)'},
        'PF_NoDate_Ext': {'label': 'PF (No Date) - External'},
        'PF_NoDate_Int': {'label': 'PF (No Date) - Internal'},
        'PA_Date':       {'label': 'Pending Approval (With Date)'},
        'PA_Q4_Spillover':  {'label': '⏪ PA Spillover (Q4 2025)'},
        'PA_Q2_Spillover':  {'label': '⏩ PA Spillover (Q2 2026)'},
        'PA_NoDate':     {'label': 'Pending Approval (No Date)'},
        'PA_Old':        {'label': 'Pending Approval (>2 Wks)'},
    }
    
    hs_categories = {
        'Expect':      {'label': 'HubSpot Expect'},
        'Commit':      {'label': 'HubSpot Commit'},
        'BestCase':    {'label': 'HubSpot Best Case'},
        'Opp':         {'label': 'HubSpot Opp'},
        'Q4_Expect':   {'label': 'Q4 Spillover (Expect)'},
        'Q4_Commit':   {'label': 'Q4 Spillover (Commit)'},
        'Q4_BestCase': {'label': 'Q4 Spillover (Best Case)'},
        'Q4_Opp':      {'label': 'Q4 Spillover (Opp)'},
        'Q2_Expect':   {'label': 'Q2 Spillover (Expect)'},
        'Q2_Commit':   {'label': 'Q2 Spillover (Commit)'},
        'Q2_BestCase': {'label': 'Q2 Spillover (Best Case)'},
        'Q2_Opp':      {'label': 'Q2 Spillover (Opp)'},
    }

    # --- 3. CREATE DISPLAY DATAFRAMES ---
    
    # === USE CENTRALIZED CATEGORIZATION FUNCTION ===
    so_categories = categorize_sales_orders(sales_orders_df, rep_name)
    
    # Determine which amount column to use based on shipping toggle
    include_shipping = st.session_state.get('include_shipping', True)
    ns_amount_col = 'Amount' if include_shipping else 'Net_Amount'
    
    # Helper function to add display columns for UI
    def format_ns_view(df, date_col_name):
        if df.empty: 
            return df
        d = df.copy()
        
        # Create Amount_Numeric based on shipping toggle
        if ns_amount_col in d.columns:
            d['Amount_Numeric'] = pd.to_numeric(d[ns_amount_col], errors='coerce').fillna(0)
        elif 'Amount' in d.columns:
            d['Amount_Numeric'] = pd.to_numeric(d['Amount'], errors='coerce').fillna(0)
        else:
            d['Amount_Numeric'] = 0
        
        # CRITICAL: Ensure Sales Rep column is preserved
        # Sales Rep should already exist from Rep Master (Column AF)
        if 'Sales Rep' not in d.columns and 'Rep Master' in d.columns:
            d['Sales Rep'] = d['Rep Master']
        
        # Add display columns
        if 'Internal ID' in d.columns:
            d['Link'] = d['Internal ID'].apply(lambda x: f"https://7086864.app.netsuite.com/app/accounting/transactions/salesord.nl?id={x}" if pd.notna(x) else "")
        
        # Add SO# column (from Display_SO_Num)
        if 'Display_SO_Num' in d.columns:
            d['SO #'] = d['Display_SO_Num']
        
        # Add Order Type column (from Display_Type)
        if 'Display_Type' in d.columns:
            d['Type'] = d['Display_Type']
        
        # Add Ship Date based on category
        # date_col_name indicates which date field was used to classify this SO
        if date_col_name == 'Promise':
            # For PF with date: use Customer Promise Date OR Projected Date (whichever exists)
            d['Ship Date'] = ''
            
            # Try Customer Promise Date first
            if 'Display_Promise_Date' in d.columns:
                promise_dates = pd.to_datetime(d['Display_Promise_Date'], errors='coerce')
                d.loc[promise_dates.notna(), 'Ship Date'] = promise_dates.dt.strftime('%Y-%m-%d')
            
            # Fill in with Projected Date where Promise Date is missing
            if 'Display_Projected_Date' in d.columns:
                projected_dates = pd.to_datetime(d['Display_Projected_Date'], errors='coerce')
                mask = (d['Ship Date'] == '') & projected_dates.notna()
                if mask.any():
                    d.loc[mask, 'Ship Date'] = projected_dates.loc[mask].dt.strftime('%Y-%m-%d')
                    
        elif date_col_name == 'PA_Date':
            # For PA with date: use Pending Approval Date
            if 'Display_PA_Date' in d.columns:
                pa_dates = pd.to_datetime(d['Display_PA_Date'], errors='coerce')
                d['Ship Date'] = pa_dates.dt.strftime('%Y-%m-%d').fillna('')
            else:
                d['Ship Date'] = ''
        else:
            # For PF/PA no date or other: show blank
            d['Ship Date'] = ''
        
        return d.sort_values('Amount_Numeric', ascending=False) if 'Amount_Numeric' in d.columns else d
    
    # Map centralized categories to display dataframes
    ns_dfs = {
        'PF_Date_Ext': format_ns_view(so_categories['pf_date_ext'], 'Promise'),
        'PF_Date_Int': format_ns_view(so_categories['pf_date_int'], 'Promise'),
        'PF_Q4_Spillover': format_ns_view(so_categories['pf_q4_spillover'], 'Promise'),
        'PF_Q2_Spillover': format_ns_view(so_categories['pf_q2_spillover'], 'Promise'),
        'PF_NoDate_Ext': format_ns_view(so_categories['pf_nodate_ext'], 'PF_Date'),
        'PF_NoDate_Int': format_ns_view(so_categories['pf_nodate_int'], 'PF_Date'),
        'PA_Old': format_ns_view(so_categories['pa_old'], 'PA_Date'),
        'PA_Date': format_ns_view(so_categories['pa_date'], 'PA_Date'),
        'PA_Q4_Spillover': format_ns_view(so_categories['pa_q4_spillover'], 'PA_Date'),
        'PA_Q2_Spillover': format_ns_view(so_categories['pa_q2_spillover'], 'PA_Date'),
        'PA_NoDate': format_ns_view(so_categories['pa_nodate'], 'None')
    }

    hs_dfs = {}
    if not hs_data.empty:
        # Use the spillover column from Google Sheet (handles both old and new column names)
        # Q1 deals: NOT marked as Q2 spillover (primary quarter)
        # Q4 deals: Marked as Q4 2025 (backward spillover - carryover)
        # Q2 deals: Explicitly marked as Q2 2026 (forward spillover)
        spillover_col = get_spillover_column(hs_data)
        
        if spillover_col == 'Q2 2026 Spillover':
            spillover_vals = hs_data[spillover_col]
            q1 = (spillover_vals != 'Q2 2026') & (spillover_vals != 'Q4 2025')
            q4 = spillover_vals == 'Q4 2025'
            q2 = spillover_vals == 'Q2 2026'
        elif spillover_col == 'Q1 2026 Spillover':
            # Old column name - for Q1 dashboard, all deals are primary quarter
            # The old column was marking deals that spill TO Q1, but now we're IN Q1
            q1 = pd.Series([True] * len(hs_data), index=hs_data.index)
            q4 = pd.Series([False] * len(hs_data), index=hs_data.index)
            q2 = pd.Series([False] * len(hs_data), index=hs_data.index)
        else:
            # No spillover column - all deals are primary quarter
            q1 = pd.Series([True] * len(hs_data), index=hs_data.index)
            q4 = pd.Series([False] * len(hs_data), index=hs_data.index)
            q2 = pd.Series([False] * len(hs_data), index=hs_data.index)
        
        def format_hs_view(df):
            if df.empty: return df
            d = df.copy()
            
            # CRITICAL: Ensure Deal Owner column is preserved
            # Deal Owner should already exist from column mapping
            if 'Deal Owner' not in d.columns:
                if 'Deal Owner First Name' in d.columns and 'Deal Owner Last Name' in d.columns:
                    d['Deal Owner'] = d['Deal Owner First Name'].fillna('') + ' ' + d['Deal Owner Last Name'].fillna('')
                    d['Deal Owner'] = d['Deal Owner'].str.strip()
            
            # Add Deal ID column (from Record ID)
            if 'Record ID' in d.columns:
                d['Deal ID'] = d['Record ID']
            
            d['Type'] = d['Display_Type']
            d['Close'] = pd.to_datetime(d['Close Date'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
            
            # Change to Pending Approval Date
            if 'Display_PA_Date' in d.columns:
                pa_dates = pd.to_datetime(d['Display_PA_Date'], errors='coerce')
                d['PA Date'] = pa_dates.dt.strftime('%Y-%m-%d').fillna('')
            else:
                d['PA Date'] = ''
            
            if 'Record ID' in d.columns:
                d['Link'] = d['Record ID'].apply(lambda x: f"https://app.hubspot.com/contacts/6712259/record/0-3/{x}/" if pd.notna(x) else "")
            return d.sort_values(['Type', 'Amount_Numeric'], ascending=[True, False])

        hs_dfs['Expect'] = format_hs_view(hs_data[q1 & (hs_data['Status'] == 'Expect')])
        hs_dfs['Commit'] = format_hs_view(hs_data[q1 & (hs_data['Status'] == 'Commit')])
        hs_dfs['BestCase'] = format_hs_view(hs_data[q1 & (hs_data['Status'] == 'Best Case')])
        hs_dfs['Opp'] = format_hs_view(hs_data[q1 & (hs_data['Status'] == 'Opportunity')])
        hs_dfs['Q4_Expect'] = format_hs_view(hs_data[q4 & (hs_data['Status'] == 'Expect')])
        hs_dfs['Q4_Commit'] = format_hs_view(hs_data[q4 & (hs_data['Status'] == 'Commit')])
        hs_dfs['Q4_BestCase'] = format_hs_view(hs_data[q4 & (hs_data['Status'] == 'Best Case')])
        hs_dfs['Q4_Opp'] = format_hs_view(hs_data[q4 & (hs_data['Status'] == 'Opportunity')])
        hs_dfs['Q2_Expect'] = format_hs_view(hs_data[q2 & (hs_data['Status'] == 'Expect')])
        hs_dfs['Q2_Commit'] = format_hs_view(hs_data[q2 & (hs_data['Status'] == 'Commit')])
        hs_dfs['Q2_BestCase'] = format_hs_view(hs_data[q2 & (hs_data['Status'] == 'Best Case')])
        hs_dfs['Q2_Opp'] = format_hs_view(hs_data[q2 & (hs_data['Status'] == 'Opportunity')])

    # --- 4. RENDER UI & CAPTURE SELECTIONS ---
    
    # We use this dict to store the ACTUAL dataframes to be exported
    export_buckets = {}
    
    # Initialize amount mode in session state if not set (preserves across reruns)
    amount_mode_key = f"amount_mode_{rep_name}"
    if amount_mode_key not in st.session_state:
        st.session_state[amount_mode_key] = "Raw Amount"
    
    # --- SELECT ALL / UNSELECT ALL BUTTONS (Toolbar style) ---
    st.markdown("#### 🛠️ Forecast Builder")
    t_col1, t_col2 = st.columns([1, 1])
    with t_col1:
        if st.button("☑️ Select All Categories", key=f"select_all_{rep_name}", type="secondary", use_container_width=True):
            # Select all NetSuite categories that have data
            for key in ns_categories.keys():
                df = ns_dfs.get(key, pd.DataFrame())
                val = df['Amount_Numeric'].sum() if not df.empty and 'Amount_Numeric' in df.columns else 0
                if val > 0 or key == 'PA_Date':
                    st.session_state[f"chk_{key}_{rep_name}"] = True
            # Select all HubSpot categories that have data
            for key in hs_categories.keys():
                df = hs_dfs.get(key, pd.DataFrame())
                val = df['Amount_Numeric'].sum() if not df.empty else 0
                if val > 0:
                    st.session_state[f"chk_{key}_{rep_name}"] = True
            st.rerun()
    
    with t_col2:
        if st.button("☐ Reset Selection", key=f"unselect_all_{rep_name}", type="secondary", use_container_width=True):
            # Unselect all NetSuite categories
            for key in ns_categories.keys():
                st.session_state[f"chk_{key}_{rep_name}"] = False
            # Unselect all HubSpot categories
            for key in hs_categories.keys():
                st.session_state[f"chk_{key}_{rep_name}"] = False
            st.rerun()
    
    with st.container():
        col_ns, col_hs = st.columns(2)
        
        # === NETSUITE COLUMN ===
        with col_ns:
            st.markdown("#### 📦 NetSuite Orders")
            st.info(f"**Invoiced (Locked):** ${invoiced_shipped:,.0f}")
            
            for key, data in ns_categories.items():
                # Get value for label
                df = ns_dfs.get(key, pd.DataFrame())
                val = df['Amount_Numeric'].sum() if not df.empty and 'Amount_Numeric' in df.columns else 0
                
                # Determine default checkbox value based on planning status
                checkbox_key = f"chk_{key}_{rep_name}"
                
                # Only set default if we have planning status and this key hasn't been set yet
                if st.session_state[planning_key] and checkbox_key not in st.session_state:
                    if not df.empty and 'SO #' in df.columns:
                        # Check planning status for items in this category
                        statuses = [get_planning_status(so_num) for so_num in df['SO #']]
                        in_count = statuses.count('IN')
                        maybe_count = statuses.count('MAYBE')
                        out_count = statuses.count('OUT')
                        
                        # Auto-check if majority are IN or MAYBE
                        if in_count + maybe_count > out_count:
                            st.session_state[checkbox_key] = True
                        else:
                            st.session_state[checkbox_key] = False
                
                # Always show PA_Date even if 0 to debug
                if val > 0 or key == 'PA_Date':
                    is_checked = st.checkbox(
                        f"{data['label']}: ${val:,.0f}", 
                        key=checkbox_key
                    )
                    
                    if is_checked:
                        with st.expander(f"🔎 View Orders ({data['label']})"):
                            if not df.empty:
                                # Search filter for customer name
                                search_key = f"search_ns_{key}_{rep_name}"
                                search_term = st.text_input(
                                    "🔍 Search by Customer or SO#",
                                    key=search_key,
                                    placeholder="Type to filter..."
                                )
                                
                                # Filter dataframe based on search term
                                df_display = df.copy()
                                if search_term:
                                    search_lower = search_term.lower()
                                    mask = pd.Series([False] * len(df_display), index=df_display.index)
                                    if 'Customer' in df_display.columns:
                                        mask |= df_display['Customer'].astype(str).str.lower().str.contains(search_lower, na=False)
                                    if 'SO #' in df_display.columns:
                                        mask |= df_display['SO #'].astype(str).str.lower().str.contains(search_lower, na=False)
                                    df_display = df_display[mask]
                                    
                                    if df_display.empty:
                                        st.info(f"No orders matching '{search_term}'")
                                
                                enable_edit = st.toggle("Customize", key=f"tgl_{key}_{rep_name}")
                                
                                # Display Columns
                                display_cols = []
                                if 'Link' in df.columns: display_cols.append('Link')
                                if 'SO #' in df.columns: display_cols.append('SO #')
                                if 'Type' in df.columns: display_cols.append('Type')
                                if 'Customer' in df.columns: display_cols.append('Customer')
                                if 'Ship Date' in df.columns: display_cols.append('Ship Date')
                                if 'Amount' in df.columns: display_cols.append('Amount')
                                
                                if enable_edit and display_cols and not df_display.empty:
                                    df_edit = df_display.copy()
                                    
                                    # Add Status column based on planning status
                                    if 'SO #' in df_edit.columns:
                                        df_edit['Status'] = df_edit['SO #'].apply(
                                            lambda so: get_planning_status(so) if get_planning_status(so) else '—'
                                        )
                                        df_edit['Notes'] = df_edit['SO #'].apply(
                                            lambda so: get_planning_notes(so)
                                        )
                                    
                                    id_col = 'SO #' if 'SO #' in df_edit.columns else 'Deal ID'
                                    editor_key = f"edit_{key}_{rep_name}"
                                    
                                    # Initialize Select column - data_editor will persist changes via its key
                                    df_edit['Select'] = True
                                    
                                    # Reorder columns
                                    display_with_status = ['Select']
                                    if 'Status' in df_edit.columns:
                                        display_with_status.append('Status')
                                    if 'Notes' in df_edit.columns:
                                        display_with_status.append('Notes')
                                    display_with_status.extend(display_cols)
                                    
                                    # Use on_change to force state persistence
                                    edited = st.data_editor(
                                        df_edit[display_with_status].reset_index(drop=True),
                                        column_config={
                                            "Select": st.column_config.CheckboxColumn("✓", width="small"),
                                            "Status": st.column_config.SelectboxColumn(
                                                "Status",
                                                width="small",
                                                options=['IN', 'MAYBE', 'OUT', '—'],
                                                required=False
                                            ),
                                            "Notes": st.column_config.TextColumn("Notes", width="medium"),
                                            "Link": st.column_config.LinkColumn("🔗", display_text="Open", width="small"),
                                            "SO #": st.column_config.TextColumn("SO #", width="small"),
                                            "Type": st.column_config.TextColumn("Type", width="small"),
                                            "Ship Date": st.column_config.TextColumn("Ship Date", width="small"),
                                            "Amount": st.column_config.NumberColumn("Amount", format="$%d")
                                        },
                                        disabled=[c for c in display_with_status if c not in ['Select', 'Status', 'Notes']],
                                        hide_index=True,
                                        key=editor_key,
                                        num_rows="fixed",
                                        use_container_width=True
                                    )
                                    
                                    # Update planning status and notes from edited data
                                    if 'SO #' in edited.columns:
                                        for idx, row in edited.iterrows():
                                            so_num = str(row['SO #']).strip()
                                            if 'Status' in row:
                                                status = str(row['Status']).strip().upper()
                                                notes = str(row.get('Notes', '')).strip() if 'Notes' in row else ''
                                                if status != '—':
                                                    update_planning_data(so_num, status=status, notes=notes)
                                    
                                    # Get selected rows directly from edited result
                                    selected_rows = edited[edited['Select']].copy()
                                    
                                    # Match back to original df to get all columns
                                    if id_col in selected_rows.columns and id_col in df.columns:
                                        selected_ids = selected_rows[id_col].astype(str).tolist()
                                        export_rows = df[df[id_col].astype(str).isin(selected_ids)].copy()
                                    else:
                                        export_rows = df.copy()
                                    
                                    if 'SO #' in export_rows.columns:
                                        export_rows['Status'] = export_rows['SO #'].apply(get_planning_status)
                                        export_rows['Notes'] = export_rows['SO #'].apply(get_planning_notes)
                                    
                                    export_buckets[key] = export_rows
                                    
                                    current_total = export_rows['Amount_Numeric'].sum() if 'Amount_Numeric' in export_rows.columns else 0
                                    st.caption(f"Selected: ${current_total:,.0f}")
                                else:
                                    # Read-only view
                                    if display_cols and not df_display.empty:
                                        df_readonly = df_display.copy()
                                        
                                        # Add Status column for read-only view too
                                        if 'SO #' in df_readonly.columns:
                                            df_readonly['Status'] = df_readonly['SO #'].apply(
                                                lambda so: get_planning_status(so) if get_planning_status(so) else '—'
                                            )
                                            display_readonly = ['Status'] + display_cols
                                        else:
                                            display_readonly = display_cols
                                        
                                        st.dataframe(
                                            df_readonly[display_readonly],
                                            column_config={
                                                "Status": st.column_config.TextColumn("Status", width="small"),
                                                "Link": st.column_config.LinkColumn("🔗", display_text="Open", width="small"),
                                                "SO #": st.column_config.TextColumn("SO #", width="small"),
                                                "Type": st.column_config.TextColumn("Type", width="small"),
                                                "Ship Date": st.column_config.TextColumn("Ship Date", width="small"),
                                                "Amount": st.column_config.NumberColumn("Amount", format="$%d")
                                            },
                                            hide_index=True,
                                            use_container_width=True
                                        )
                                    # Capture all rows for export
                                    export_buckets[key] = df

        # === HUBSPOT COLUMN ===
        with col_hs:
            st.markdown("#### 🎯 HubSpot Pipeline")
            
            # --- PROBABILITY TOGGLE ---
            # Let user choose between Raw Amount and Probability-Weighted Amount
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
                border: 1px solid rgba(99, 102, 241, 0.3);
                border-radius: 12px;
                padding: 12px 16px;
                margin-bottom: 16px;
            ">
                <div style="font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8; margin-bottom: 8px;">
                    💰 Amount Display Mode
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Radio button - key ensures state persists across reruns
            # Session state initialized earlier in the function
            amount_mode = st.radio(
                "Select amount type:",
                options=["Raw Amount", "Probability-Adjusted"],
                key=amount_mode_key,
                horizontal=True,
                label_visibility="collapsed"
            )
            
            # Determine which amount column to use based on toggle
            use_probability = (amount_mode == "Probability-Adjusted")
            amount_col_display = 'Prob_Amount_Numeric' if use_probability else 'Amount_Numeric'
            
            # Show info about the selected mode
            if use_probability:
                st.caption("📊 Showing probability-weighted amounts from HubSpot")
            else:
                st.caption("📊 Showing raw deal amounts")
            
            st.markdown("---")
            
            for key, data in hs_categories.items():
                df = hs_dfs.get(key, pd.DataFrame())
                # Use the appropriate amount column based on toggle
                if not df.empty:
                    if use_probability and 'Prob_Amount_Numeric' in df.columns:
                        val = df['Prob_Amount_Numeric'].sum()
                    else:
                        val = df['Amount_Numeric'].sum() if 'Amount_Numeric' in df.columns else 0
                else:
                    val = 0
                
                # Determine default checkbox value based on planning status
                checkbox_key = f"chk_{key}_{rep_name}"
                
                # Only set default if we have planning status and this key hasn't been set yet
                if st.session_state[planning_key] and checkbox_key not in st.session_state:
                    if not df.empty and 'Deal ID' in df.columns:
                        # Check planning status for items in this category
                        statuses = [get_planning_status(deal_id) for deal_id in df['Deal ID']]
                        in_count = statuses.count('IN')
                        maybe_count = statuses.count('MAYBE')
                        out_count = statuses.count('OUT')
                        
                        # Auto-check if majority are IN or MAYBE
                        if in_count + maybe_count > out_count:
                            st.session_state[checkbox_key] = True
                        else:
                            st.session_state[checkbox_key] = False
                
                if val > 0:
                    is_checked = st.checkbox(
                        f"{data['label']}: ${val:,.0f}", 
                        key=checkbox_key
                    )
                    if is_checked:
                        with st.expander(f"🔎 View Deals ({data['label']})"):
                            if not df.empty:
                                # Search filter for deal name
                                search_key = f"search_hs_{key}_{rep_name}"
                                search_term = st.text_input(
                                    "🔍 Search by Deal Name",
                                    key=search_key,
                                    placeholder="Type to filter..."
                                )
                                
                                # Filter dataframe based on search term
                                df_display = df.copy()
                                if search_term:
                                    search_lower = search_term.lower()
                                    mask = pd.Series([False] * len(df_display), index=df_display.index)
                                    if 'Deal Name' in df_display.columns:
                                        mask |= df_display['Deal Name'].astype(str).str.lower().str.contains(search_lower, na=False)
                                    if 'Deal ID' in df_display.columns:
                                        mask |= df_display['Deal ID'].astype(str).str.lower().str.contains(search_lower, na=False)
                                    df_display = df_display[mask]
                                    
                                    if df_display.empty:
                                        st.info(f"No deals matching '{search_term}'")
                                
                                enable_edit = st.toggle("Customize", key=f"tgl_{key}_{rep_name}")
                                
                                # Dynamic columns based on probability mode
                                if use_probability:
                                    cols = ['Link', 'Deal ID', 'Deal Name', 'Type', 'Close', 'PA Date', 'Prob_Amount_Numeric', 'Amount_Numeric']
                                    primary_amount_col = 'Prob_Amount_Numeric'
                                else:
                                    cols = ['Link', 'Deal ID', 'Deal Name', 'Type', 'Close', 'PA Date', 'Amount_Numeric', 'Prob_Amount_Numeric']
                                    primary_amount_col = 'Amount_Numeric'
                                
                                cols = [c for c in cols if c in df.columns]
                                
                                if enable_edit and not df_display.empty:
                                    df_edit = df_display.copy()
                                    
                                    # Add Status column based on planning status
                                    if 'Deal ID' in df_edit.columns:
                                        df_edit['Status'] = df_edit['Deal ID'].apply(
                                            lambda deal_id: get_planning_status(deal_id) if get_planning_status(deal_id) else '—'
                                        )
                                        df_edit['Notes'] = df_edit['Deal ID'].apply(
                                            lambda deal_id: get_planning_notes(deal_id)
                                        )
                                    
                                    id_col = 'Deal ID' if 'Deal ID' in df_edit.columns else 'SO #'
                                    editor_key = f"edit_{key}_{rep_name}"
                                    
                                    # Initialize Select column - data_editor will persist changes via its key
                                    df_edit['Select'] = True
                                    
                                    # Reorder columns
                                    display_with_status = ['Select']
                                    if 'Status' in df_edit.columns:
                                        display_with_status.append('Status')
                                    if 'Notes' in df_edit.columns:
                                        display_with_status.append('Notes')
                                    display_with_status.extend(cols)
                                    
                                    edited = st.data_editor(
                                        df_edit[display_with_status].reset_index(drop=True),
                                        column_config={
                                            "Select": st.column_config.CheckboxColumn("✓", width="small"),
                                            "Status": st.column_config.SelectboxColumn(
                                                "Status",
                                                width="small",
                                                options=['IN', 'MAYBE', 'OUT', '—'],
                                                required=False
                                            ),
                                            "Notes": st.column_config.TextColumn("Notes", width="medium"),
                                            "Link": st.column_config.LinkColumn("🔗", display_text="Open", width="small"),
                                            "Deal ID": st.column_config.TextColumn("Deal ID", width="small"),
                                            "Deal Name": st.column_config.TextColumn("Deal Name", width="medium"),
                                            "Type": st.column_config.TextColumn("Type", width="small"),
                                            "Close": st.column_config.TextColumn("Close Date", width="small"),
                                            "PA Date": st.column_config.TextColumn("PA Date", width="small"),
                                            "Amount_Numeric": st.column_config.NumberColumn("Raw $" if use_probability else "Amount ✓", format="$%d"),
                                            "Prob_Amount_Numeric": st.column_config.NumberColumn("Prob $ ✓" if use_probability else "Prob $", format="$%d")
                                        },
                                        disabled=[c for c in display_with_status if c not in ['Select', 'Status', 'Notes']],
                                        hide_index=True,
                                        key=editor_key,
                                        num_rows="fixed",
                                        use_container_width=True
                                    )
                                    
                                    # Update planning status and notes from edited data
                                    if 'Deal ID' in edited.columns:
                                        for idx, row in edited.iterrows():
                                            deal_id = str(row['Deal ID']).strip()
                                            if 'Status' in row:
                                                status = str(row['Status']).strip().upper()
                                                notes = str(row.get('Notes', '')).strip() if 'Notes' in row else ''
                                                if status != '—':
                                                    update_planning_data(deal_id, status=status, notes=notes)
                                    
                                    # Get selected rows directly from edited result
                                    selected_rows = edited[edited['Select']].copy()
                                    
                                    # Match back to original df to get all columns
                                    if id_col in selected_rows.columns and id_col in df.columns:
                                        selected_ids = selected_rows[id_col].astype(str).tolist()
                                        export_rows = df[df[id_col].astype(str).isin(selected_ids)].copy()
                                    else:
                                        export_rows = df.copy()
                                    
                                    if 'Deal ID' in export_rows.columns:
                                        export_rows['Status'] = export_rows['Deal ID'].apply(get_planning_status)
                                        export_rows['Notes'] = export_rows['Deal ID'].apply(get_planning_notes)
                                    
                                    export_buckets[key] = export_rows
                                    
                                    if use_probability and 'Prob_Amount_Numeric' in export_rows.columns:
                                        current_total = export_rows['Prob_Amount_Numeric'].sum()
                                    else:
                                        current_total = export_rows['Amount_Numeric'].sum() if 'Amount_Numeric' in export_rows.columns else 0
                                    st.caption(f"Selected: ${current_total:,.0f}")
                                else:
                                    # Read-only view
                                    if not df_display.empty:
                                        df_readonly = df_display.copy()
                                        
                                        # Add Status column for read-only view too
                                        if 'Deal ID' in df_readonly.columns:
                                            df_readonly['Status'] = df_readonly['Deal ID'].apply(
                                                lambda deal_id: get_planning_status(deal_id) if get_planning_status(deal_id) else '—'
                                            )
                                            display_readonly = ['Status'] + cols
                                        else:
                                            display_readonly = cols
                                        
                                        # Filter display_readonly to only columns that exist
                                        display_readonly = [c for c in display_readonly if c in df_readonly.columns]
                                        
                                        st.dataframe(
                                            df_readonly[display_readonly],
                                            column_config={
                                                "Status": st.column_config.TextColumn("Status", width="small"),
                                                "Link": st.column_config.LinkColumn("🔗", display_text="Open", width="small"),
                                                "Deal ID": st.column_config.TextColumn("Deal ID", width="small"),
                                                "Deal Name": st.column_config.TextColumn("Deal Name", width="medium"),
                                                "Type": st.column_config.TextColumn("Type", width="small"),
                                                "Close": st.column_config.TextColumn("Close Date", width="small"),
                                                "PA Date": st.column_config.TextColumn("PA Date", width="small"),
                                                "Amount_Numeric": st.column_config.NumberColumn("Raw $" if use_probability else "Amount ✓", format="$%d"),
                                                "Prob_Amount_Numeric": st.column_config.NumberColumn("Prob $ ✓" if use_probability else "Prob $", format="$%d")
                                            },
                                            hide_index=True,
                                            use_container_width=True
                                        )
                                    export_buckets[key] = df

    # --- 4b. CONSOLIDATED MASTER TABLE VIEW ---
    st.markdown("---")
    
    # Count how many categories are selected
    selected_cat_count = len(export_buckets)
    
    if selected_cat_count > 0:
        with st.expander(f"📊 View All Selected Data — Full Width ({selected_cat_count} categories, click to expand)", expanded=False):
            # Build unified master dataframe from all export_buckets
            master_rows = []
            for key, df in export_buckets.items():
                if df.empty:
                    continue
                
                is_ns = key in ns_categories
                label = ns_categories.get(key, hs_categories.get(key, {})).get('label', key)
                source = "NetSuite" if is_ns else "HubSpot"
                
                for _, row in df.iterrows():
                    if is_ns:
                        item_id = row.get('SO #', row.get('Display_SO_Num', row.get('Document Number', '')))
                        name = row.get('Customer', '')
                        date_val = row.get('Ship Date', '')
                        amount = pd.to_numeric(row.get('Amount_Numeric', row.get('Amount', 0)), errors='coerce')
                        if pd.isna(amount): amount = 0
                        prob_amount = amount
                        link = row.get('Link', '')
                        rep = row.get('Sales Rep', row.get('Rep Master', ''))
                        order_type = row.get('Type', row.get('Display_Type', ''))
                        status = get_planning_status(item_id) or ''
                    else:
                        item_id = row.get('Deal ID', row.get('Record ID', ''))
                        name = row.get('Deal Name', row.get('Account Name', ''))
                        date_val = row.get('Close', row.get('Close Date', ''))
                        amount = pd.to_numeric(row.get('Amount_Numeric', 0), errors='coerce')
                        if pd.isna(amount): amount = 0
                        prob_amount = pd.to_numeric(row.get('Prob_Amount_Numeric', 0), errors='coerce')
                        if pd.isna(prob_amount): prob_amount = amount
                        link = row.get('Link', '')
                        rep = row.get('Deal Owner', '')
                        order_type = row.get('Type', row.get('Display_Type', ''))
                        status = get_planning_status(item_id) or ''
                    
                    # Clean up NaN values
                    if pd.isna(rep) or rep is None: rep = ''
                    if pd.isna(name) or name is None: name = ''
                    if pd.isna(date_val) or date_val is None: date_val = ''
                    if pd.isna(order_type) or order_type is None: order_type = ''
                    if pd.isna(link) or link is None: link = ''
                    if isinstance(date_val, pd.Timestamp):
                        date_val = date_val.strftime('%Y-%m-%d')
                    
                    master_rows.append({
                        'Source': source,
                        'Category': label,
                        'ID': str(item_id).strip() if item_id else '',
                        'Name': str(name).strip(),
                        'Type': str(order_type).strip(),
                        'Date': str(date_val).strip(),
                        'Amount': amount,
                        'Prob Amount': prob_amount,
                        'Status': status,
                        'Rep': str(rep).strip(),
                        'Link': str(link).strip()
                    })
            
            if master_rows:
                master_df = pd.DataFrame(master_rows)
                
                # --- Filters row ---
                filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 1])
                
                with filter_col1:
                    available_categories = sorted(master_df['Category'].unique().tolist())
                    selected_categories = st.multiselect(
                        "Filter by Category:",
                        options=available_categories,
                        default=available_categories,
                        key=f"master_cat_filter_{rep_name}"
                    )
                
                with filter_col2:
                    master_search = st.text_input(
                        "🔍 Search across all data:",
                        key=f"master_search_{rep_name}",
                        placeholder="Search by name, ID, customer, rep..."
                    )
                
                with filter_col3:
                    source_filter = st.multiselect(
                        "Source:",
                        options=sorted(master_df['Source'].unique().tolist()),
                        default=sorted(master_df['Source'].unique().tolist()),
                        key=f"master_source_filter_{rep_name}"
                    )
                
                # Apply filters
                filtered_master = master_df.copy()
                if selected_categories:
                    filtered_master = filtered_master[filtered_master['Category'].isin(selected_categories)]
                if source_filter:
                    filtered_master = filtered_master[filtered_master['Source'].isin(source_filter)]
                if master_search:
                    search_lower = master_search.lower()
                    text_mask = (
                        filtered_master['Name'].str.lower().str.contains(search_lower, na=False) |
                        filtered_master['ID'].str.lower().str.contains(search_lower, na=False) |
                        filtered_master['Rep'].str.lower().str.contains(search_lower, na=False) |
                        filtered_master['Category'].str.lower().str.contains(search_lower, na=False) |
                        filtered_master['Type'].str.lower().str.contains(search_lower, na=False)
                    )
                    filtered_master = filtered_master[text_mask]
                
                if filtered_master.empty:
                    st.info("No data matches your filters.")
                else:
                    # Summary stats bar
                    total_amt = filtered_master['Amount'].sum()
                    total_prob = filtered_master['Prob Amount'].sum()
                    unique_cats = filtered_master['Category'].nunique()
                    row_count = len(filtered_master)
                    
                    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                    with stat_col1:
                        st.metric("Total Amount", f"${total_amt:,.0f}")
                    with stat_col2:
                        st.metric("Prob-Adjusted", f"${total_prob:,.0f}")
                    with stat_col3:
                        st.metric("Categories", f"{unique_cats}")
                    with stat_col4:
                        st.metric("Line Items", f"{row_count}")
                    
                    # Sort by Amount descending
                    filtered_master = filtered_master.sort_values('Amount', ascending=False)
                    
                    # Display the master table
                    st.dataframe(
                        filtered_master,
                        column_config={
                            "Link": st.column_config.LinkColumn("🔗", display_text="Open", width="small"),
                            "Source": st.column_config.TextColumn("Source", width="small"),
                            "Category": st.column_config.TextColumn("Category", width="medium"),
                            "ID": st.column_config.TextColumn("ID", width="small"),
                            "Name": st.column_config.TextColumn("Name", width="medium"),
                            "Type": st.column_config.TextColumn("Type", width="small"),
                            "Date": st.column_config.TextColumn("Date", width="small"),
                            "Amount": st.column_config.NumberColumn("Amount", format="$%,.0f"),
                            "Prob Amount": st.column_config.NumberColumn("Prob $", format="$%,.0f"),
                            "Status": st.column_config.TextColumn("Status", width="small"),
                            "Rep": st.column_config.TextColumn("Rep", width="small"),
                        },
                        hide_index=True,
                        use_container_width=True,
                        height=600
                    )
                    
                    # Category breakdown summary
                    st.markdown("##### Category Totals")
                    cat_summary = filtered_master.groupby('Category').agg(
                        Items=('Amount', 'count'),
                        Total=('Amount', 'sum'),
                        Prob_Total=('Prob Amount', 'sum')
                    ).sort_values('Total', ascending=False)
                    cat_summary['Total'] = cat_summary['Total'].apply(lambda x: f"${x:,.0f}")
                    cat_summary['Prob_Total'] = cat_summary['Prob_Total'].apply(lambda x: f"${x:,.0f}")
                    st.dataframe(cat_summary, use_container_width=True)
            else:
                st.info("Check some categories above to see data here.")
    else:
        st.caption("☝️ Select categories above, then expand this section to see all data in one view.")

    # --- 5. CALCULATE RESULTS ---
    
    # Get probability mode from session state
    amount_mode_key = f"amount_mode_{rep_name}"
    use_probability_for_calc = st.session_state.get(amount_mode_key, "Raw Amount") == "Probability-Adjusted"
    
    # Calculate totals from export buckets (which reflect custom selections)
    def safe_sum(df, is_hubspot=False):
        if df.empty:
            return 0
        # Handle both Amount and Amount_Numeric columns (NS uses Amount, HS uses Amount_Numeric)
        if is_hubspot and use_probability_for_calc:
            # Use probability-weighted amount for HubSpot if toggle is on
            if 'Prob_Amount_Numeric' in df.columns:
                return df['Prob_Amount_Numeric'].sum()
            elif 'Amount_Numeric' in df.columns:
                return df['Amount_Numeric'].sum()
        else:
            if 'Amount_Numeric' in df.columns:
                return df['Amount_Numeric'].sum()
            elif 'Amount' in df.columns:
                return df['Amount'].sum()
        return 0
    
    selected_pending = sum(safe_sum(df, is_hubspot=False) for k, df in export_buckets.items() if k in ns_categories)
    selected_pipeline = sum(safe_sum(df, is_hubspot=True) for k, df in export_buckets.items() if k in hs_categories)
    
    total_forecast = invoiced_shipped + selected_pending + selected_pipeline
    gap_to_quota = quota - total_forecast
    
    # --- STICKY FORECAST SUMMARY BAR ---
    gap_class = "gap-behind" if gap_to_quota > 0 else "gap-ahead"
    gap_label = "GAP" if gap_to_quota > 0 else "AHEAD"
    gap_display = f"${abs(gap_to_quota):,.0f}"
    gap_color = "#f87171" if gap_to_quota > 0 else "#4ade80"
    gap_shadow = "rgba(248, 113, 113, 0.5)" if gap_to_quota > 0 else "rgba(74, 222, 128, 0.5)"
    
    # Determine pipeline label based on probability mode
    pipeline_label = "+ PIPELINE (Prob)" if use_probability_for_calc else "+ PIPELINE (Raw)"
    pipeline_color = "#a78bfa" if use_probability_for_calc else "#60a5fa"  # Purple for prob, blue for raw
    
    st.markdown(f"""
    <div style="
        position: fixed;
        bottom: 24px;
        left: 50%;
        transform: translateX(-50%);
        width: calc(100% - 380px);
        max-width: 1100px;
        z-index: 999999;
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.98) 0%, rgba(30, 41, 59, 0.98) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(99, 102, 241, 0.4);
        border-radius: 24px;
        box-shadow: 0 0 40px rgba(99, 102, 241, 0.2), 0 20px 60px rgba(0, 0, 0, 0.5);
        padding: 16px 32px;
        display: flex;
        justify-content: space-around;
        align-items: center;
    ">
        <div style="display: flex; flex-direction: column; align-items: center; padding: 0 1rem;">
            <div style="font-size: 0.65rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; color: #64748b; margin-bottom: 4px;">INVOICED</div>
            <div style="font-size: 1.25rem; font-weight: 800; color: #4ade80; text-shadow: 0 0 15px rgba(74, 222, 128, 0.5);">${invoiced_shipped:,.0f}</div>
        </div>
        <div style="width: 1px; height: 40px; background: linear-gradient(180deg, transparent, rgba(99, 102, 241, 0.5), transparent);"></div>
        <div style="display: flex; flex-direction: column; align-items: center; padding: 0 1rem;">
            <div style="font-size: 0.65rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; color: #64748b; margin-bottom: 4px;">+ PENDING</div>
            <div style="font-size: 1.25rem; font-weight: 800; color: #fbbf24; text-shadow: 0 0 15px rgba(251, 191, 36, 0.5);">${selected_pending:,.0f}</div>
        </div>
        <div style="width: 1px; height: 40px; background: linear-gradient(180deg, transparent, rgba(99, 102, 241, 0.5), transparent);"></div>
        <div style="display: flex; flex-direction: column; align-items: center; padding: 0 1rem;">
            <div style="font-size: 0.65rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; color: #64748b; margin-bottom: 4px;">{pipeline_label}</div>
            <div style="font-size: 1.25rem; font-weight: 800; color: {pipeline_color}; text-shadow: 0 0 15px rgba(96, 165, 250, 0.5);">${selected_pipeline:,.0f}</div>
        </div>
        <div style="width: 1px; height: 40px; background: linear-gradient(180deg, transparent, rgba(99, 102, 241, 0.5), transparent);"></div>
        <div style="display: flex; flex-direction: column; align-items: center; padding: 0 1rem;">
            <div style="font-size: 0.65rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; color: #64748b; margin-bottom: 4px;">= FORECAST</div>
            <div style="font-size: 1.5rem; font-weight: 800; background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; filter: drop-shadow(0 0 20px rgba(139, 92, 246, 0.5));">${total_forecast:,.0f}</div>
        </div>
        <div style="width: 1px; height: 40px; background: linear-gradient(180deg, transparent, rgba(99, 102, 241, 0.5), transparent);"></div>
        <div style="display: flex; flex-direction: column; align-items: center; padding: 0 1rem;">
            <div style="font-size: 0.65rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; color: #64748b; margin-bottom: 4px;">{gap_label}</div>
            <div style="font-size: 1.25rem; font-weight: 800; color: {gap_color}; text-shadow: 0 0 15px {gap_shadow};">{gap_display}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🔮 Forecast Scenario Results")
    
    # Add locked revenue banner (using inline styles - CSS classes don't work reliably in Streamlit)
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(6, 78, 59, 0.25) 100%);
        border: 2px solid rgba(16, 185, 129, 0.5);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin: 1rem 0 1.5rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 0 30px rgba(16, 185, 129, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1);
    ">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <span style="font-size: 2rem;">🔒</span>
            <div>
                <div style="font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; color: #94a3b8; margin-bottom: 4px;">Locked Revenue</div>
                <div style="color: #4ade80; font-size: 2rem; font-weight: 800; text-shadow: 0 0 20px rgba(74, 222, 128, 0.4);">${invoiced_shipped:,.0f}</div>
            </div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; color: #94a3b8; margin-bottom: 4px;">Status</div>
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #022c22; font-size: 0.75rem; font-weight: 700; padding: 8px 16px; border-radius: 8px; text-transform: uppercase; letter-spacing: 1px; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);">INVOICED & SECURED</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: st.metric("1. Invoiced", f"${invoiced_shipped:,.0f}")
    with m2: st.metric("2. Selected Pending", f"${selected_pending:,.0f}")
    with m3: st.metric("3. Selected Pipeline", f"${selected_pipeline:,.0f}")
    with m4: st.metric("🏁 Total Forecast", f"${total_forecast:,.0f}", delta="Sum of 1+2+3")
    with m5:
        if gap_to_quota > 0:
            st.metric("Gap to Quota", f"${gap_to_quota:,.0f}", delta="Behind", delta_color="inverse")
        else:
            st.metric("Gap to Quota", f"${abs(gap_to_quota):,.0f}", delta="Ahead!", delta_color="normal")

    c1, c2 = st.columns([2, 1])
    with c1:
        # Use the enhanced sexy gauge with color zones
        fig = create_sexy_gauge(total_forecast, quota, "Progress to Quota")
        st.plotly_chart(fig, use_container_width=True)
        
    with c2:
        # Helper locally if needed
        def calculate_biz_days():
             from datetime import date, timedelta
             today = date.today()
             q4_end = date(2025, 12, 31)
             holidays = [date(2025, 11, 27), date(2025, 11, 28), date(2025, 12, 25), date(2025, 12, 26)]
             days = 0
             current = today
             while current <= q4_end:
                 if current.weekday() < 5 and current not in holidays: days += 1
                 current += timedelta(days=1)
             return days

        biz_days = calculate_biz_days()
        # Calculate based on what still needs to ship (pending orders + pipeline deals)
        items_to_ship = selected_pending + selected_pipeline
        if items_to_ship > 0 and biz_days > 0:
            required = items_to_ship / biz_days
            st.metric("Required Ship Rate", f"${required:,.0f}/day", f"{biz_days} days left")
        elif items_to_ship == 0:
            st.info("✅ No pending items to ship")
        elif gap_to_quota <= 0:
            st.success("🎉 Scenario Hits Quota!")
    
    # Add rep-by-bucket breakdown
    st.markdown("---")
    st.markdown("### 📋 Forecast by Rep & Bucket")
    
    # Create breakdown similar to team dashboard tables
    rep_bucket_summary = []
    for key, df in export_buckets.items():
        if not df.empty:
            label = ns_categories.get(key, hs_categories.get(key, {})).get('label', key)
            
            # Determine which rep column to use
            rep_col = 'Sales Rep' if 'Sales Rep' in df.columns else 'Deal Owner'
            amount_col = 'Amount' if 'Amount' in df.columns else 'Amount_Numeric'
            
            if rep_col in df.columns and amount_col in df.columns:
                by_rep = df.groupby(rep_col)[amount_col].sum()
                for rep, amt in by_rep.items():
                    if pd.notna(rep) and rep and str(rep).strip():
                        rep_bucket_summary.append({
                            'Rep': str(rep).strip(),
                            'Bucket': label,
                            'Amount': amt
                        })
    
    if rep_bucket_summary:
        summary_df = pd.DataFrame(rep_bucket_summary)
        pivot_df = summary_df.pivot_table(
            index='Rep',
            columns='Bucket',
            values='Amount',
            aggfunc='sum',
            fill_value=0
        )
        pivot_df['Total'] = pivot_df.sum(axis=1)
        pivot_df = pivot_df.sort_values('Total', ascending=False)
        
        st.dataframe(
            pivot_df.style.format('${:,.0f}'),
            use_container_width=True
        )
    else:
        st.info("No data to display")

    # --- 6. ROBUST EXPORT FUNCTIONALITY ---
    if total_forecast > 0:
        st.markdown("---")
        
        # Initialize Lists
        export_summary = []
        export_data = []
        
        # A. Build Summary
        export_summary.append({'Category': '=== FORECAST SUMMARY ===', 'Amount': ''})
        export_summary.append({'Category': 'Quota', 'Amount': f"${quota:,.0f}"})
        export_summary.append({'Category': 'Invoiced (Always Included)', 'Amount': f"${invoiced_shipped:,.0f}"})
        export_summary.append({'Category': 'Pending Orders (Selected)', 'Amount': f"${selected_pending:,.0f}"})
        
        # Indicate which pipeline mode is being used
        pipeline_mode_label = "Pipeline Deals (Probability-Adjusted)" if use_probability_for_calc else "Pipeline Deals (Raw Amount)"
        export_summary.append({'Category': pipeline_mode_label, 'Amount': f"${selected_pipeline:,.0f}"})
        
        export_summary.append({'Category': 'Total Forecast', 'Amount': f"${total_forecast:,.0f}"})
        export_summary.append({'Category': 'Gap to Goal', 'Amount': f"${gap_to_quota:,.0f}"})
        export_summary.append({'Category': '', 'Amount': ''})
        export_summary.append({'Category': '=== SELECTED COMPONENTS ===', 'Amount': ''})
        
        # Add Component Totals
        for key, df in export_buckets.items():
            # Handle both Amount and Amount_Numeric columns (NS uses Amount, HS uses Amount_Numeric)
            if 'Amount_Numeric' in df.columns:
                cat_val = df['Amount_Numeric'].sum()
            elif 'Amount' in df.columns:
                cat_val = df['Amount'].sum()
            else:
                cat_val = 0
                
            if cat_val > 0:
                label = ns_categories.get(key, hs_categories.get(key, {})).get('label', key)
                count = len(df)
                export_summary.append({'Category': f"{label} ({count} items)", 'Amount': f"${cat_val:,.0f}"})
        
        export_summary.append({'Category': '', 'Amount': ''})
        export_summary.append({'Category': '=== DETAILED LINE ITEMS ===', 'Amount': ''})
        
        # B. Build Line Items
        
        # 1. Invoices
        if invoices_df is not None and not invoices_df.empty:
            # Filter for rep if needed (using Sales Rep col)
            inv_source = invoices_df
            if rep_name and 'Sales Rep' in invoices_df.columns:
                inv_source = invoices_df[invoices_df['Sales Rep'] == rep_name]
                
            for _, row in inv_source.iterrows():
                export_data.append({
                    'Category': 'Invoice',
                    'ID': row.get('Document Number', row.get('Invoice Number', '')),
                    'Customer': row.get('Account Name', row.get('Customer', '')),
                    'Order/Deal Type': '',
                    'Date': str(row.get('Date', '')),
                    'Amount': pd.to_numeric(row.get('Amount', 0), errors='coerce'),
                    'Prob_Amount': pd.to_numeric(row.get('Amount', 0), errors='coerce'),  # Invoices use same as Amount
                    'Status': '',
                    'Notes': '',
                    'Rep': row.get('Sales Rep', '')
                })
        
        # 2. Pending & Pipeline Items from Buckets
        for key, df in export_buckets.items():
            label = ns_categories.get(key, hs_categories.get(key, {})).get('label', key)
            
            for _, row in df.iterrows():
                # Get planning status for this item
                if key in ns_categories:  # NetSuite
                    item_id_for_status = row.get('SO #', '')
                else:  # HubSpot
                    item_id_for_status = row.get('Deal ID', row.get('Record ID', ''))
                
                planning_status = get_planning_status(item_id_for_status) if item_id_for_status else ''
                if not planning_status:
                    planning_status = ''  # Use empty string instead of em dash
                
                # Get planning notes for this item
                planning_notes = get_planning_notes(item_id_for_status) if item_id_for_status else ''
                if not planning_notes:
                    planning_notes = ''
                
                # Determine fields based on source type (NS vs HS)
                if key in ns_categories: # NetSuite
                    item_type = f"Sales Order - {label}"
                    item_id = row.get('SO #', row.get('Document Number', ''))
                    cust = row.get('Customer', '')
                    date_val = row.get('Ship Date', row.get('Key Date', ''))
                    deal_type = row.get('Type', row.get('Display_Type', ''))
                    # NetSuite uses 'Amount' not 'Amount_Numeric'
                    amount = pd.to_numeric(row.get('Amount', 0), errors='coerce')
                    if pd.isna(amount):
                        amount = 0
                    prob_amount = amount  # NetSuite doesn't have probability, use same as amount
                    # Get Sales Rep - try multiple column names
                    rep = row.get('Sales Rep', row.get('Rep Master', ''))
                    # Ensure it's not NaN
                    if pd.isna(rep) or rep is None or str(rep).lower() in ['nan', 'none', '']:
                        rep = ''
                    else:
                        rep = str(rep).strip()
                else: # HubSpot
                    item_type = f"HubSpot - {label}"
                    item_id = row.get('Deal ID', row.get('Record ID', ''))
                    cust = row.get('Account Name', row.get('Deal Name', '')) # Fallback to Deal Name if Account missing
                    date_val = row.get('Close', row.get('Close Date', ''))
                    deal_type = row.get('Type', row.get('Display_Type', ''))
                    amount = pd.to_numeric(row.get('Amount_Numeric', 0), errors='coerce')
                    if pd.isna(amount):
                        amount = 0
                    prob_amount = pd.to_numeric(row.get('Prob_Amount_Numeric', 0), errors='coerce')
                    if pd.isna(prob_amount):
                        prob_amount = amount  # Default to raw amount if no probability
                    # Get Deal Owner - try multiple possible column names
                    rep = row.get('Deal Owner', '')
                    # If Deal Owner is empty, try to construct from First + Last Name
                    if pd.isna(rep) or rep is None or str(rep).strip() == '':
                        first = row.get('Deal Owner First Name', '')
                        last = row.get('Deal Owner Last Name', '')
                        if first or last:
                            rep = f"{first} {last}".strip()
                    # Ensure it's not NaN
                    if pd.isna(rep) or rep is None or str(rep).lower() in ['nan', 'none', '']:
                        rep = ''
                    else:
                        rep = str(rep).strip()
                
                # Clean up date value - handle timestamps and blank dates
                if pd.isna(date_val) or date_val == '' or date_val == '—':
                    date_val = ''
                elif isinstance(date_val, pd.Timestamp):
                    date_val = date_val.strftime('%Y-%m-%d')
                elif isinstance(date_val, str):
                    # If it's already a formatted date string, keep it
                    # Otherwise try to parse it
                    if date_val and date_val != '—':
                        try:
                            parsed_date = pd.to_datetime(date_val, errors='coerce')
                            if pd.notna(parsed_date):
                                date_val = parsed_date.strftime('%Y-%m-%d')
                            else:
                                date_val = ''
                        except:
                            date_val = ''
                    else:
                        date_val = ''
                else:
                    date_val = ''
                
                # Ensure rep is a string, not NaN
                if pd.isna(rep) or rep is None:
                    rep = ''
                else:
                    rep = str(rep).strip()
                
                export_data.append({
                    'Category': item_type,
                    'ID': item_id,
                    'Customer': cust,
                    'Order/Deal Type': deal_type,
                    'Date': date_val,
                    'Amount': amount,
                    'Prob_Amount': prob_amount,
                    'Status': planning_status,
                    'Notes': planning_notes,
                    'Rep': rep
                })

        # C. Construct CSV
        if export_data:
            summary_df = pd.DataFrame(export_summary)
            data_df = pd.DataFrame(export_data)
            
            # Format Amount columns in Data DF
            if 'Amount' in data_df.columns:
                data_df['Amount'] = data_df['Amount'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00")
            if 'Prob_Amount' in data_df.columns:
                data_df['Prob_Amount'] = data_df['Prob_Amount'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00")
            
            final_csv = summary_df.to_csv(index=False) + "\n" + data_df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download Winning Pipeline",
                data=final_csv,
                file_name=f"winning_pipeline_{rep_name if rep_name else 'team'}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            st.caption(f"Export includes summary + {len(data_df)} line items.")
def display_hubspot_deals_audit(deals_df, rep_name=None):
    """
    Display audit section for HubSpot deals without amounts
    """
    st.markdown("### ⚠️ HubSpot Deals without Amounts (AUDIT!)")
    st.caption("These deals are missing amount data and need attention")
    
    if deals_df is None or deals_df.empty:
        st.info("No HubSpot deals data available")
        return
    
    # Filter by rep if specified
    if rep_name and 'Deal Owner' in deals_df.columns:
        filtered_deals = deals_df[deals_df['Deal Owner'] == rep_name].copy()
    else:
        filtered_deals = deals_df.copy()
    
    if filtered_deals.empty:
        st.info(f"No deals found{' for ' + rep_name if rep_name else ''}")
        return
    
    # Convert Amount to numeric and find deals without amounts
    filtered_deals['Amount_Numeric'] = pd.to_numeric(filtered_deals['Amount'], errors='coerce')
    deals_no_amount = filtered_deals[
        (filtered_deals['Amount_Numeric'].isna()) | 
        (filtered_deals['Amount_Numeric'] == 0)
    ].copy()
    
    if deals_no_amount.empty:
        st.success("✅ All deals have amounts! No issues to audit.")
        return
    
    # Show summary
    st.warning(f"⚠️ Found {len(deals_no_amount)} deals without amounts")
    
    # Break down by status
    if 'Status' in deals_no_amount.columns:
        status_categories = ['Expect', 'Commit', 'Best Case', 'Opportunity']
        
        for status in status_categories:
            status_deals = deals_no_amount[deals_no_amount['Status'] == status].copy()
            
            if not status_deals.empty:
                with st.expander(f"🔍 {status} - {len(status_deals)} deals"):
                    # Create display dataframe
                    display_data = []
                    
                    for _, row in status_deals.iterrows():
                        # Build HubSpot link if we have Record ID
                        deal_link = ""
                        record_id = row.get('Record ID', '')
                        if record_id:
                            deal_link = f"https://app.hubspot.com/contacts/6554605/deal/{record_id}"
                        
                        display_data.append({
                            'Link': deal_link,
                            'Deal Name': row.get('Deal Name', ''),
                            'Amount': '$0.00',
                            'Status': row.get('Status', ''),
                            'Pipeline': row.get('Pipeline', ''),
                            'Close Date': row.get('Close Date', ''),
                            'Product Type': row.get('Product Type', '')
                        })
                    
                    if display_data:
                        display_df = pd.DataFrame(display_data)
                        
                        # Format as clickable links
                        if 'Link' in display_df.columns:
                            display_df['Link'] = display_df['Link'].apply(
                                lambda x: f'<a href="{x}" target="_blank">View Deal</a>' if x else ''
                            )
                        
                        # Display the table with HTML links
                        st.markdown(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)
                    else:
                        st.info("No deals to display")
    else:
        st.warning("Status column not found in deals data")

def calculate_team_metrics(deals_df, dashboard_df):
    """Calculate overall team metrics"""
    
    # Handle empty dashboard_df
    if dashboard_df.empty or 'Quota' not in dashboard_df.columns:
        total_quota = 0
        total_orders = 0
    else:
        total_quota = dashboard_df['Quota'].sum()
        total_orders = dashboard_df['NetSuite Orders'].sum() if 'NetSuite Orders' in dashboard_df.columns else 0
    
    # Get spillover column (handles both old and new column names)
    spillover_col = get_spillover_column(deals_df)
    
    # Filter for Q1 2026 fulfillment only
    if not deals_df.empty and spillover_col:
        q1_mask = is_q1_deal(deals_df, spillover_col)
        deals_q1 = deals_df[q1_mask]
    else:
        # No spillover column or empty - use all deals
        deals_q1 = deals_df
    
    # Calculate Expect/Commit forecast (Q1 only)
    if not deals_q1.empty and 'Status' in deals_q1.columns and 'Amount' in deals_q1.columns:
        expect_commit = deals_q1[deals_q1['Status'].isin(['Expect', 'Commit'])]['Amount'].sum()
        best_opp = deals_q1[deals_q1['Status'].isin(['Best Case', 'Opportunity'])]['Amount'].sum()
    else:
        expect_commit = 0
        best_opp = 0
    
    # Calculate gap
    gap = total_quota - expect_commit - total_orders
    
    # Calculate attainment percentage
    current_forecast = expect_commit + total_orders
    attainment_pct = (current_forecast / total_quota * 100) if total_quota > 0 else 0
    
    # Potential attainment (if all deals close)
    potential_attainment = ((expect_commit + best_opp + total_orders) / total_quota * 100) if total_quota > 0 else 0
    
    return {
        'total_quota': total_quota,
        'total_orders': total_orders,
        'expect_commit': expect_commit,
        'best_opp': best_opp,
        'gap': gap,
        'attainment_pct': attainment_pct,
        'potential_attainment': potential_attainment,
        'current_forecast': current_forecast
    }

# ========== CENTRALIZED SALES ORDER CATEGORIZATION ==========
def categorize_sales_orders(sales_orders_df, rep_name=None):
    """
    SINGLE SOURCE OF TRUTH for categorizing sales orders into forecast buckets.
    
    SIMPLIFIED VERSION: Uses the pre-calculated "Updated Status" column (Column AG)
    from the Google Sheet instead of calculating status categories in Python.
    
    Valid "Updated Status" values:
    - PA No Date
    - PA with Date
    - PF with Date (Ext)
    - PF with Date (Int)
    - PF No Date (Int)
    - PF No Date (Ext)
    - PA Old (>2 Weeks)
    
    Returns a dictionary with categorized DataFrames and their amounts.
    """
    empty_result = {
        'pf_date_ext': pd.DataFrame(), 'pf_date_ext_amount': 0,
        'pf_date_int': pd.DataFrame(), 'pf_date_int_amount': 0,
        'pf_nodate_ext': pd.DataFrame(), 'pf_nodate_ext_amount': 0,
        'pf_nodate_int': pd.DataFrame(), 'pf_nodate_int_amount': 0,
        'pa_date': pd.DataFrame(), 'pa_date_amount': 0,
        'pa_nodate': pd.DataFrame(), 'pa_nodate_amount': 0,
        'pa_old': pd.DataFrame(), 'pa_old_amount': 0,
        'pf_q4_spillover': pd.DataFrame(), 'pf_q4_spillover_amount': 0,
        'pa_q4_spillover': pd.DataFrame(), 'pa_q4_spillover_amount': 0,
        'pf_q2_spillover': pd.DataFrame(), 'pf_q2_spillover_amount': 0,
        'pa_q2_spillover': pd.DataFrame(), 'pa_q2_spillover_amount': 0
    }
    
    if sales_orders_df is None or sales_orders_df.empty:
        return empty_result
    
    # Check if Updated Status column exists
    if 'Updated Status' not in sales_orders_df.columns:
        st.warning("⚠️ 'Updated Status' column not found in Sales Orders data. Using empty results.")
        return empty_result
    
    # Filter by rep if specified
    if rep_name and 'Sales Rep' in sales_orders_df.columns:
        orders = sales_orders_df[sales_orders_df['Sales Rep'] == rep_name].copy()
    else:
        orders = sales_orders_df.copy()
    
    if orders.empty:
        return empty_result
    
    # Remove duplicate columns
    if orders.columns.duplicated().any():
        orders = orders.loc[:, ~orders.columns.duplicated()]
    
    # === ADD DISPLAY COLUMNS FOR UI ===
    orders['Display_SO_Num'] = get_col_by_index(orders, 1)  # Col B: SO#
    orders['Display_Type'] = get_col_by_index(orders, 17).fillna('Standard')  # Col R: Order Type
    orders['Display_Promise_Date'] = pd.to_datetime(get_col_by_index(orders, 11), errors='coerce')  # Col L: Promise Date
    orders['Display_Projected_Date'] = pd.to_datetime(get_col_by_index(orders, 12), errors='coerce')  # Col M: Projected Date
    
    # PA Date handling
    if 'Pending Approval Date' in orders.columns:
        orders['Display_PA_Date'] = pd.to_datetime(orders['Pending Approval Date'], errors='coerce')
    else:
        orders['Display_PA_Date'] = pd.to_datetime(get_col_by_index(orders, 29), errors='coerce')  # Col AD: PA Date
    
    # === CATEGORIZE USING "Updated Status" COLUMN ===
    # Clean and normalize the Updated Status values for matching
    orders['Updated_Status_Clean'] = orders['Updated Status'].astype(str).str.strip()
    
    # Map Updated Status values to categories
    # PF with Date (Ext) -> pf_date_ext
    pf_date_ext = orders[orders['Updated_Status_Clean'] == 'PF with Date (Ext)'].copy()
    
    # PF with Date (Int) -> pf_date_int
    pf_date_int = orders[orders['Updated_Status_Clean'] == 'PF with Date (Int)'].copy()
    
    # PF No Date (Ext) -> pf_nodate_ext
    pf_nodate_ext = orders[orders['Updated_Status_Clean'] == 'PF No Date (Ext)'].copy()
    
    # PF No Date (Int) -> pf_nodate_int
    pf_nodate_int = orders[orders['Updated_Status_Clean'] == 'PF No Date (Int)'].copy()
    
    # PA with Date -> pa_date
    pa_date = orders[orders['Updated_Status_Clean'] == 'PA with Date'].copy()
    
    # PA No Date -> pa_nodate
    pa_nodate = orders[orders['Updated_Status_Clean'] == 'PA No Date'].copy()
    
    # PA Old (>2 Weeks) -> pa_old
    pa_old = orders[orders['Updated_Status_Clean'] == 'PA Old (>2 Weeks)'].copy()
    
    # Spillover categories - check for Q4/Q2 spillover values if they exist
    # These may be added later; for now, return empty DataFrames
    pf_q4_spillover = pd.DataFrame()
    pa_q4_spillover = pd.DataFrame()
    pf_q2_spillover = pd.DataFrame()
    pa_q2_spillover = pd.DataFrame()
    
    # Calculate amounts - respects shipping toggle
    # Determine which amount column to use based on shipping toggle
    include_shipping = st.session_state.get('include_shipping', True)
    amount_col = 'Amount' if include_shipping else 'Net_Amount'
    
    def get_amount(df):
        # Try the preferred column first, fall back to Amount if not available
        if not df.empty:
            if amount_col in df.columns:
                return df[amount_col].sum()
            elif 'Amount' in df.columns:
                return df['Amount'].sum()
        return 0
    
    return {
        'pf_date_ext': pf_date_ext,
        'pf_date_ext_amount': get_amount(pf_date_ext),
        'pf_date_int': pf_date_int,
        'pf_date_int_amount': get_amount(pf_date_int),
        'pf_nodate_ext': pf_nodate_ext,
        'pf_nodate_ext_amount': get_amount(pf_nodate_ext),
        'pf_nodate_int': pf_nodate_int,
        'pf_nodate_int_amount': get_amount(pf_nodate_int),
        'pa_date': pa_date,
        'pa_date_amount': get_amount(pa_date),
        'pa_nodate': pa_nodate,
        'pa_nodate_amount': get_amount(pa_nodate),
        'pa_old': pa_old,
        'pa_old_amount': get_amount(pa_old),
        'pf_q4_spillover': pf_q4_spillover,
        'pf_q4_spillover_amount': get_amount(pf_q4_spillover),
        'pa_q4_spillover': pa_q4_spillover,
        'pa_q4_spillover_amount': get_amount(pa_q4_spillover),
        'pf_q2_spillover': pf_q2_spillover,
        'pf_q2_spillover_amount': get_amount(pf_q2_spillover),
        'pa_q2_spillover': pa_q2_spillover,
        'pa_q2_spillover_amount': get_amount(pa_q2_spillover)
    }

def calculate_rep_metrics(rep_name, deals_df, dashboard_df, sales_orders_df=None):
    """Calculate metrics for a specific rep with detailed order lists for drill-down"""
    
    # Get rep's quota and orders
    rep_info = dashboard_df[dashboard_df['Rep Name'] == rep_name]
    
    if rep_info.empty:
        return None
    
    quota = rep_info['Quota'].iloc[0]
    
    # Determine which orders column to use based on shipping toggle
    include_shipping = st.session_state.get('include_shipping', True)
    if include_shipping:
        orders = rep_info['NetSuite Orders'].iloc[0]
    else:
        # Use Net column if available, otherwise fall back to regular
        if 'NetSuite Orders Net' in rep_info.columns:
            orders = rep_info['NetSuite Orders Net'].iloc[0]
        else:
            orders = rep_info['NetSuite Orders'].iloc[0]
    
    # Filter deals for this rep - ALL Q1 2026 deals (regardless of spillover)
    # Handle empty deals_df gracefully (e.g., when Google Sheets returns 503)
    if deals_df.empty or 'Deal Owner' not in deals_df.columns:
        rep_deals = pd.DataFrame()
    else:
        rep_deals = deals_df[deals_df['Deal Owner'] == rep_name].copy()
    
    # Check for spillover column (handles both old and new column names)
    spillover_col = get_spillover_column(rep_deals)
    
    if spillover_col == 'Q2 2026 Spillover':
        # New column: Separate deals by shipping timeline
        rep_deals['Ships_In_Q1'] = (rep_deals[spillover_col] != 'Q2 2026') & (rep_deals[spillover_col] != 'Q4 2025')
        rep_deals['Ships_In_Q2'] = rep_deals[spillover_col] == 'Q2 2026'
        rep_deals['Ships_In_Q4'] = rep_deals[spillover_col] == 'Q4 2025'
        
        # Deals that ship in Q1 2026 (primary quarter)
        rep_deals_ship_q1 = rep_deals[rep_deals['Ships_In_Q1'] == True].copy()
        
        # Deals that ship in Q2 2026 (forward spillover)
        rep_deals_ship_q2 = rep_deals[rep_deals['Ships_In_Q2'] == True].copy()
        
        # Deals that ship in Q4 2025 (backward spillover - carryover)
        rep_deals_ship_q4 = rep_deals[rep_deals['Ships_In_Q4'] == True].copy()
    else:
        # Old column name or no column - treat all as Q1 (primary quarter)
        rep_deals_ship_q1 = rep_deals.copy()
        rep_deals_ship_q2 = pd.DataFrame()
        rep_deals_ship_q4 = pd.DataFrame()
    
    # Calculate metrics for DEALS SHIPPING IN Q1 (this counts toward quota)
    if not rep_deals_ship_q1.empty and 'Status' in rep_deals_ship_q1.columns:
        expect_commit_q1_deals = rep_deals_ship_q1[rep_deals_ship_q1['Status'].isin(['Expect', 'Commit'])].copy()
        if expect_commit_q1_deals.columns.duplicated().any():
            expect_commit_q1_deals = expect_commit_q1_deals.loc[:, ~expect_commit_q1_deals.columns.duplicated()]
        expect_commit_q1 = expect_commit_q1_deals['Amount'].sum() if not expect_commit_q1_deals.empty else 0
        
        best_opp_q1_deals = rep_deals_ship_q1[rep_deals_ship_q1['Status'].isin(['Best Case', 'Opportunity'])].copy()
        if best_opp_q1_deals.columns.duplicated().any():
            best_opp_q1_deals = best_opp_q1_deals.loc[:, ~best_opp_q1_deals.columns.duplicated()]
        best_opp_q1 = best_opp_q1_deals['Amount'].sum() if not best_opp_q1_deals.empty else 0
    else:
        expect_commit_q1_deals = pd.DataFrame()
        expect_commit_q1 = 0
        best_opp_q1_deals = pd.DataFrame()
        best_opp_q1 = 0
    
    # Calculate metrics for Q2 SPILLOVER DEALS (closing in Q1 but shipping in Q2)
    if not rep_deals_ship_q2.empty and 'Status' in rep_deals_ship_q2.columns:
        expect_commit_q2_deals = rep_deals_ship_q2[rep_deals_ship_q2['Status'].isin(['Expect', 'Commit'])].copy()
        if expect_commit_q2_deals.columns.duplicated().any():
            expect_commit_q2_deals = expect_commit_q2_deals.loc[:, ~expect_commit_q2_deals.columns.duplicated()]
        expect_commit_q2_spillover = expect_commit_q2_deals['Amount'].sum() if not expect_commit_q2_deals.empty else 0
        
        best_opp_q2_deals = rep_deals_ship_q2[rep_deals_ship_q2['Status'].isin(['Best Case', 'Opportunity'])].copy()
        if best_opp_q2_deals.columns.duplicated().any():
            best_opp_q2_deals = best_opp_q2_deals.loc[:, ~best_opp_q2_deals.columns.duplicated()]
        best_opp_q2_spillover = best_opp_q2_deals['Amount'].sum() if not best_opp_q2_deals.empty else 0
    else:
        expect_commit_q2_deals = pd.DataFrame()
        expect_commit_q2_spillover = 0
        best_opp_q2_deals = pd.DataFrame()
        best_opp_q2_spillover = 0
    
    # Calculate metrics for Q4 2025 SPILLOVER DEALS (carryover from Q4)
    if not rep_deals_ship_q4.empty and 'Status' in rep_deals_ship_q4.columns:
        expect_commit_q4_deals = rep_deals_ship_q4[rep_deals_ship_q4['Status'].isin(['Expect', 'Commit'])].copy()
        if expect_commit_q4_deals.columns.duplicated().any():
            expect_commit_q4_deals = expect_commit_q4_deals.loc[:, ~expect_commit_q4_deals.columns.duplicated()]
        expect_commit_q4_spillover = expect_commit_q4_deals['Amount'].sum() if not expect_commit_q4_deals.empty else 0
        
        best_opp_q4_deals = rep_deals_ship_q4[rep_deals_ship_q4['Status'].isin(['Best Case', 'Opportunity'])].copy()
        if best_opp_q4_deals.columns.duplicated().any():
            best_opp_q4_deals = best_opp_q4_deals.loc[:, ~best_opp_q4_deals.columns.duplicated()]
        best_opp_q4_spillover = best_opp_q4_deals['Amount'].sum() if not best_opp_q4_deals.empty else 0
    else:
        expect_commit_q4_deals = pd.DataFrame()
        expect_commit_q4_spillover = 0
        best_opp_q4_deals = pd.DataFrame()
        best_opp_q4_spillover = 0
    
    # Total spillovers
    q2_spillover_total = expect_commit_q2_spillover + best_opp_q2_spillover
    q4_spillover_total = expect_commit_q4_spillover + best_opp_q4_spillover
    
    # === USE CENTRALIZED CATEGORIZATION FUNCTION ===
    so_categories = categorize_sales_orders(sales_orders_df, rep_name)
    
    # Extract amounts
    pending_fulfillment = so_categories['pf_date_ext_amount'] + so_categories['pf_date_int_amount']
    pending_fulfillment_no_date = so_categories['pf_nodate_ext_amount'] + so_categories['pf_nodate_int_amount']
    pending_approval = so_categories['pa_date_amount']
    pending_approval_no_date = so_categories['pa_nodate_amount']
    pending_approval_old = so_categories['pa_old_amount']
    
    # Extract detail dataframes
    pending_approval_details = so_categories['pa_date']
    pending_approval_no_date_details = so_categories['pa_nodate']
    pending_approval_old_details = so_categories['pa_old']
    pending_fulfillment_details = pd.concat([so_categories['pf_date_ext'], so_categories['pf_date_int']])
    pending_fulfillment_no_date_details = pd.concat([so_categories['pf_nodate_ext'], so_categories['pf_nodate_int']])
    
    # Total calculations - ONLY Q1 SHIPPING DEALS COUNT TOWARD QUOTA
    total_pending_fulfillment = pending_fulfillment + pending_fulfillment_no_date
    total_progress = orders + expect_commit_q1 + pending_approval + pending_fulfillment
    gap = quota - total_progress
    attainment_pct = (total_progress / quota * 100) if quota > 0 else 0
    potential_attainment = ((total_progress + best_opp_q1) / quota * 100) if quota > 0 else 0
    
    return {
        'quota': quota,
        'orders': orders,
        'expect_commit': expect_commit_q1,  # Only Q1 shipping deals
        'best_opp': best_opp_q1,  # Only Q1 shipping deals
        'gap': gap,
        'attainment_pct': attainment_pct,
        'potential_attainment': potential_attainment,
        'total_progress': total_progress,
        'pending_approval': pending_approval,
        'pending_approval_no_date': pending_approval_no_date,
        'pending_approval_old': pending_approval_old,
        'pending_fulfillment': pending_fulfillment,
        'pending_fulfillment_no_date': pending_fulfillment_no_date,
        'total_pending_fulfillment': total_pending_fulfillment,
        
        # Q2 2026 Spillover metrics (forward)
        'q2_spillover_expect_commit': expect_commit_q2_spillover,
        'q2_spillover_best_opp': best_opp_q2_spillover,
        'q2_spillover_total': q2_spillover_total,
        
        # Q4 2025 Spillover metrics (backward carryover)
        'q4_spillover_expect_commit': expect_commit_q4_spillover,
        'q4_spillover_best_opp': best_opp_q4_spillover,
        'q4_spillover_total': q4_spillover_total,
        
        # Keep q1_spillover keys for backward compatibility (mapped to q2)
        'q1_spillover_expect_commit': expect_commit_q2_spillover,
        'q1_spillover_best_opp': best_opp_q2_spillover,
        'q1_spillover_total': q2_spillover_total,
        
        # ALL Q1 2026 closing deals (for reference)
        'total_q1_closing_deals': len(rep_deals),
        'total_q1_closing_amount': rep_deals['Amount'].sum() if not rep_deals.empty else 0,
        
        'deals': rep_deals_ship_q1,  # Deals shipping in Q1
        
        # Add detail dataframes for drill-down
        'pending_approval_details': pending_approval_details,
        'pending_approval_no_date_details': pending_approval_no_date_details,
        'pending_approval_old_details': pending_approval_old_details,
        'pending_fulfillment_details': pending_fulfillment_details,
        'pending_fulfillment_no_date_details': pending_fulfillment_no_date_details,
        'expect_commit_deals': expect_commit_q1_deals,
        'best_opp_deals': best_opp_q1_deals,
        
        # Q2 Spillover deal details
        'expect_commit_q2_spillover_deals': expect_commit_q2_deals,
        'best_opp_q2_spillover_deals': best_opp_q2_deals,
        'all_q2_spillover_deals': rep_deals_ship_q2,
        
        # Keep old key names for backward compatibility
        'expect_commit_q1_spillover_deals': expect_commit_q2_deals,
        'best_opp_q1_spillover_deals': best_opp_q2_deals,
        'all_q1_spillover_deals': rep_deals_ship_q2
    }

# ========== ENHANCED CHART FUNCTIONS (GEMINI ENHANCEMENTS) ==========

def create_sexy_gauge(current_val, target_val, title="Progress to Quota"):
    """Enhanced cyber-style gauge"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = current_val,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title.upper(), 'font': {'size': 12, 'color': '#94a3b8'}},
        delta = {
            'reference': target_val, 
            'increasing': {'color': "#10b981"},
            'decreasing': {'color': "#ef4444"},
            'font': {'size': 14}
        },
        number = {'font': {'size': 40, 'color': 'white', 'family': 'Inter'}, 'prefix': "$"},
        gauge = {
            'axis': {'range': [None, max(target_val * 1.1, current_val * 1.1)], 'visible': False},
            'bar': {'color': "#3b82f6", 'thickness': 1},
            'bgcolor': "rgba(255,255,255,0.05)",
            'borderwidth': 0,
            'steps': [
                 {'range': [0, target_val], 'color': "rgba(30, 41, 59, 0.5)"}
            ],
            'threshold': {
                'line': {'color': "#10b981", 'width': 4},
                'thickness': 1,
                'value': target_val
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white', 'family': 'Inter'},
        height=250,
        margin=dict(l=30, r=30, t=40, b=10)
    )
    return fig

def create_pipeline_sankey(deals_df):
    """Sankey diagram showing pipeline flow from Pipeline to Status"""
    if deals_df.empty or 'Pipeline' not in deals_df.columns or 'Status' not in deals_df.columns:
        # Return empty figure if data not available
        return go.Figure()
    
    # Aggregate data: Pipeline -> Status
    df_agg = deals_df.groupby(['Pipeline', 'Status'])['Amount'].sum().reset_index()
    
    if df_agg.empty:
        return go.Figure()
    
    # Create source/target indices
    pipelines = list(df_agg['Pipeline'].unique())
    statuses = list(df_agg['Status'].unique())
    all_labels = pipelines + statuses
    
    source_indices = [pipelines.index(p) for p in df_agg['Pipeline']]
    target_indices = [len(pipelines) + statuses.index(s) for s in df_agg['Status']]
    
    # Create color map for statuses
    status_colors = {
        'Commit': 'rgba(16, 185, 129, 0.6)',
        'Expect': 'rgba(59, 130, 246, 0.6)',
        'Best Case': 'rgba(139, 92, 246, 0.6)',
        'Opp': 'rgba(251, 191, 36, 0.6)'
    }
    
    link_colors = []
    for idx in target_indices:
        status = statuses[idx - len(pipelines)]
        link_colors.append(status_colors.get(status, 'rgba(100, 116, 139, 0.4)'))
    
    fig = go.Figure(data=[go.Sankey(
        node = dict(
            pad = 15,
            thickness = 20,
            line = dict(color = "rgba(255,255,255,0.2)", width = 0.5),
            label = all_labels,
            color = "rgba(59, 130, 246, 0.8)"
        ),
        link = dict(
            source = source_indices,
            target = target_indices,
            value = df_agg['Amount'],
            color = link_colors
        )
    )])
    
    fig.update_layout(
        title_text="Pipeline Flow Analysis",
        font=dict(size=12, color='white'),
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def create_team_sunburst(dashboard_df, deals_df):
    """Enhanced sunburst chart with better colors and formatting"""
    # Prepare data structure for sunburst
    sunburst_data = []
    
    # Define distinct colors for each rep
    rep_colors = {
        'Brad Sherman': '#ef4444',      # Red
        'Jake Lynch': '#3b82f6',        # Blue
        'Dave Borkowski': '#10b981',    # Green
        'Lance Mitton': '#f59e0b',      # Amber
        'Alex Gonzalez': '#8b5cf6',     # Purple
        'Shopify ECommerce': '#ec4899'  # Pink
    }
    
    for _, rep_row in dashboard_df.iterrows():
        rep_name = rep_row['Rep Name']
        
        # Add invoiced with better label
        if 'NetSuite Orders' in rep_row and rep_row['NetSuite Orders'] > 0:
            sunburst_data.append({
                'labels': rep_name,
                'parents': '',
                'values': rep_row['NetSuite Orders'],
                'text': f"${rep_row['NetSuite Orders']:,.0f}",
                'type': 'Invoiced',
                'rep': rep_name
            })
            sunburst_data.append({
                'labels': f"{rep_name} - Invoiced",
                'parents': rep_name,
                'values': rep_row['NetSuite Orders'],
                'text': f"Invoiced: ${rep_row['NetSuite Orders']:,.0f}",
                'type': 'Invoiced',
                'rep': rep_name
            })
        
        # Add pipeline data if available
        rep_deals = deals_df[deals_df['Deal Owner'] == rep_name] if not deals_df.empty else pd.DataFrame()
        if not rep_deals.empty:
            pipeline_total = rep_deals['Amount'].sum()
            if pipeline_total > 0:
                sunburst_data.append({
                    'labels': f"{rep_name} - Pipeline",
                    'parents': rep_name,
                    'values': pipeline_total,
                    'text': f"Pipeline: ${pipeline_total:,.0f}",
                    'type': 'Pipeline',
                    'rep': rep_name
                })
    
    if not sunburst_data:
        return go.Figure()
    
    df_sunburst = pd.DataFrame(sunburst_data)
    
    # Create custom colors based on rep and type
    colors = []
    for _, row in df_sunburst.iterrows():
        rep = row['rep']
        base_color = rep_colors.get(rep, '#64748b')
        
        if row['type'] == 'Invoiced':
            # Darker shade for invoiced
            if base_color.startswith('#'):
                colors.append(base_color + 'dd')  # Add alpha
        else:
            # Lighter shade for pipeline
            if base_color.startswith('#'):
                colors.append(base_color + '88')  # More transparent
    
    fig = go.Figure(go.Sunburst(
        labels=df_sunburst['labels'],
        parents=df_sunburst['parents'],
        values=df_sunburst['values'],
        text=df_sunburst['text'],
        marker=dict(
            colors=colors,
            line=dict(color='rgba(255,255,255,0.3)', width=2)
        ),
        textfont=dict(size=14, color='white', family='Arial Black'),
        hovertemplate='<b>%{label}</b><br>%{text}<br>%{percentParent}<extra></extra>',
        branchvalues="total"
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white', 'size': 12},
        height=500,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    return fig

def create_gap_chart(metrics, title):
    """Create a waterfall/combo chart showing progress to goal"""
    
    fig = go.Figure()
    
    # Create stacked bar
    fig.add_trace(go.Bar(
        name='NetSuite Orders',
        x=['Progress'],
        y=[metrics['total_orders'] if 'total_orders' in metrics else metrics['orders']],
        marker_color='#3b82f6',
        text=[f"${metrics['total_orders'] if 'total_orders' in metrics else metrics['orders']:,.0f}"],
        textposition='auto',
        textfont=dict(size=14)
    ))

    fig.add_trace(go.Bar(
        name='Expect/Commit',
        x=['Progress'],
        y=[metrics['expect_commit']],
        marker_color='#10b981',
        text=[f"${metrics['expect_commit']:,.0f}"],
        textposition='auto',
        textfont=dict(size=14)
    ))
    
    # Add quota line
    fig.add_trace(go.Scatter(
        name='Quota Goal',
        x=['Progress'],
        y=[metrics['total_quota'] if 'total_quota' in metrics else metrics['quota']],
        mode='markers',
        marker=dict(size=12, color='#ef4444', symbol='diamond'),
        text=[f"Goal: ${metrics['total_quota'] if 'total_quota' in metrics else metrics['quota']:,.0f}"],
        textposition='top center'
    ))
    
    # Add potential attainment line
    potential = metrics['expect_commit'] + metrics['best_opp'] + (metrics['total_orders'] if 'total_orders' in metrics else metrics['orders'])
    fig.add_trace(go.Scatter(
        name='Potential (if all deals close)',
        x=['Progress'],
        y=[potential],
        mode='markers',
        marker=dict(size=12, color='#f59e0b', symbol='diamond'),
        text=[f"Potential: ${potential:,.0f}"],
        textposition='bottom center'
    ))
    
    fig.update_layout(
        title=title,
        barmode='stack',
        height=400,
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(color="#94a3b8")
        ),
        yaxis_title="Amount ($)",
        xaxis_title="",
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#f8fafc", family="Inter"),
        xaxis=dict(showgrid=False, tickfont=dict(color='#94a3b8')),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#94a3b8'))
    )
    
    return fig

# Helper function to safely grab a column by index
def get_col_by_index(df, index):
    """Safely grab a column by index with fallback"""
    if df is not None and not df.empty and len(df.columns) > index:
        return df.iloc[:, index]
    return pd.Series(dtype=object)

def create_enhanced_waterfall_chart(metrics, title, mode):
    """
    Creates a high-end waterfall chart
    """
    # Define the steps based on mode
    if mode == "base":
        steps = [
            {'label': 'Invoiced', 'value': metrics['orders'], 'color': '#3b82f6'},
            {'label': 'Pending Full.', 'value': metrics['pending_fulfillment'], 'color': '#f59e0b'},
            {'label': 'Pending Appr.', 'value': metrics['pending_approval'], 'color': '#f97316'},
            {'label': 'Pipeline (Hi-Conf)', 'value': metrics['expect_commit'], 'color': '#10b981'},
        ]
    elif mode == "full":
        steps = [
            {'label': 'Invoiced', 'value': metrics['orders'], 'color': '#3b82f6'},
            {'label': 'Pending Full.', 'value': metrics['pending_fulfillment'], 'color': '#f59e0b'},
            {'label': 'PF (No Date)', 'value': metrics.get('pending_fulfillment_no_date', 0), 'color': '#d97706'},
            {'label': 'Pending Appr.', 'value': metrics['pending_approval'], 'color': '#f97316'},
            {'label': 'PA (No Date)', 'value': metrics.get('pending_approval_no_date', 0), 'color': '#ea580c'},
            {'label': 'PA (Old)', 'value': metrics.get('pending_approval_old', 0), 'color': '#c2410c'},
            {'label': 'Pipeline', 'value': metrics['expect_commit'], 'color': '#10b981'},
        ]
    else:
        return None

    steps = [step for step in steps if step['value'] > 0]
    if not steps: return None

    current_total = sum(step['value'] for step in steps)
    quota = metrics.get('total_quota', metrics.get('quota', 0))
    gap = quota - current_total
    
    fig = go.Figure()
    
    cumulative = 0
    for step in steps:
        fig.add_trace(go.Bar(
            name=step['label'], x=[step['label']], y=[step['value']],
            marker_color=step['color'],
            text=[f"${step['value']/1000:.0f}k"], textposition='auto',
            hovertemplate=f"<b>{step['label']}</b><br>${step['value']:,.0f}<extra></extra>",
            marker=dict(line=dict(width=0))
        ))
        cumulative += step['value']
    
    # Total Bar
    fig.add_trace(go.Bar(
        name='FORECAST', x=['TOTAL'], y=[current_total],
        marker_color='#8b5cf6',
        text=[f"${current_total/1000:.0f}k"], textposition='auto',
        hovertemplate=f"<b>Total Forecast</b><br>${current_total:,.0f}<extra></extra>"
    ))
    
    # Gap Bar (Ghost bar style)
    if gap != 0:
        gap_color = 'rgba(239, 68, 68, 0.3)' if gap > 0 else 'rgba(16, 185, 129, 0.3)'
        gap_label = 'Gap' if gap > 0 else 'Surplus'
        fig.add_trace(go.Bar(
            name=gap_label, x=[gap_label], y=[abs(gap)],
            marker_color=gap_color,
            marker_line=dict(width=1, color='#ef4444' if gap > 0 else '#10b981'),
            text=[f"${abs(gap)/1000:.0f}k"], textposition='auto',
            hovertemplate=f"<b>{gap_label}</b><br>${abs(gap):,.0f}<extra></extra>"
        ))
    
    # Quota Line
    fig.add_shape(type="line",
        x0=-0.5, x1=len(steps)+1.5, y0=quota, y1=quota,
        line=dict(color="white", width=2, dash="dash"),
    )
    fig.add_annotation(x=len(steps)+1, y=quota, text="QUOTA", showarrow=False, yshift=10, font=dict(color="white", size=10))

    fig.update_layout(
        title=dict(text=title.upper(), font=dict(size=14, color="#94a3b8")),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#f8fafc", family="Inter"),
        showlegend=False,
        height=450,
        margin=dict(l=20, r=20, t=50, b=20),
        yaxis=dict(showgrid=False, showticklabels=False, fixedrange=True),
        xaxis=dict(showgrid=False, fixedrange=True),
        barmode='group',
        bargap=0.15
    )
    return fig

def create_status_breakdown_chart(deals_df, rep_name=None):
    """Create a pie chart showing deal distribution by status"""
    
    if deals_df.empty:
        return None
    
    if rep_name and 'Deal Owner' in deals_df.columns:
        deals_df = deals_df[deals_df['Deal Owner'] == rep_name]
    
    # Only show Q1 deals (filter out Q2 and Q4 spillover)
    spillover_col = get_spillover_column(deals_df)
    if spillover_col:
        q1_mask = is_q1_deal(deals_df, spillover_col)
        deals_df = deals_df[q1_mask]
    
    if deals_df.empty:
        return None
    
    status_summary = deals_df.groupby('Status')['Amount'].sum().reset_index()
    
    color_map = {
        'Expect': '#3b82f6',
        'Commit': '#10b981',
        'Best Case': '#f59e0b',
        'Opportunity': '#8b5cf6'
    }
    
    fig = px.pie(
        status_summary,
        values='Amount',
        names='Status',
        title='Deal Amount by Forecast Category (Q1 Only)',
        color='Status',
        color_discrete_map=color_map,
        hole=0.4
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#f8fafc", family="Inter"),
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(color="#94a3b8")
        )
    )
    
    return fig

def create_pipeline_breakdown_chart(deals_df, rep_name=None):
    """Create a stacked bar chart showing pipeline breakdown"""
    
    if deals_df.empty:
        return None
    
    if rep_name and 'Deal Owner' in deals_df.columns:
        deals_df = deals_df[deals_df['Deal Owner'] == rep_name]
    
    # Only show Q1 deals (filter out Q2 and Q4 spillover)
    spillover_col = get_spillover_column(deals_df)
    if spillover_col:
        q1_mask = is_q1_deal(deals_df, spillover_col)
        deals_df = deals_df[q1_mask]
    
    if deals_df.empty:
        return None
    
    # Group by pipeline and status
    pipeline_summary = deals_df.groupby(['Pipeline', 'Status'])['Amount'].sum().reset_index()
    
    color_map = {
        'Expect': '#3b82f6',
        'Commit': '#10b981',
        'Best Case': '#f59e0b',
        'Opportunity': '#8b5cf6'
    }
    
    fig = px.bar(
        pipeline_summary,
        x='Pipeline',
        y='Amount',
        color='Status',
        title='Pipeline Breakdown by Forecast Category (Q1 Only)',
        color_discrete_map=color_map,
        text_auto='.2s',
        barmode='stack'
    )

    fig.update_traces(textfont_size=14, textposition='auto')

    fig.update_layout(
        height=450,
        yaxis_title="Amount ($)",
        xaxis_title="Pipeline",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#f8fafc", family="Inter"),
        xaxis=dict(
            automargin=True,
            tickangle=-45,
            showgrid=False,
            tickfont=dict(color='#94a3b8')
        ),
        yaxis=dict(
            automargin=True,
            showgrid=True,
            gridcolor='rgba(255,255,255,0.05)',
            tickfont=dict(color='#94a3b8')
        ),
        margin=dict(l=50, r=50, t=80, b=100),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#94a3b8")
        )
    )
    
    return fig

def create_deals_timeline(deals_df, rep_name=None):
    """Create a timeline showing when deals are expected to close"""
    
    if deals_df.empty:
        return None
    
    if rep_name and 'Deal Owner' in deals_df.columns:
        deals_df = deals_df[deals_df['Deal Owner'] == rep_name]
    
    # Filter out deals without close dates
    if 'Close Date' not in deals_df.columns:
        return None
    timeline_df = deals_df[deals_df['Close Date'].notna()].copy()
    
    if timeline_df.empty:
        return None
    
    # Sort by close date
    timeline_df = timeline_df.sort_values('Close Date')
    
    # Add Q1/Q4/Q2 indicator to color map
    spillover_col = get_spillover_column(timeline_df)
    
    def get_quarter(row):
        if spillover_col and spillover_col in row.index:
            spillover_val = row.get(spillover_col, '')
            if spillover_col == 'Q2 2026 Spillover':
                if spillover_val == 'Q4 2025':
                    return 'Q4 2025 Spillover'
                elif spillover_val == 'Q2 2026':
                    return 'Q2 2026 Spillover'
        return 'Q1 2026'
    
    timeline_df['Quarter'] = timeline_df.apply(get_quarter, axis=1)
    
    color_map = {
        'Expect': '#3b82f6',
        'Commit': '#10b981',
        'Best Case': '#f59e0b',
        'Opportunity': '#8b5cf6'
    }
    
    fig = px.scatter(
        timeline_df,
        x='Close Date',
        y='Amount',
        color='Status',
        size='Amount',
        hover_data=['Deal Name', 'Amount', 'Pipeline', 'Quarter'],
        title='Deal Close Date Timeline',
        color_discrete_map=color_map
    )
    
    # Fixed: Use datetime object for the vertical line
    from datetime import datetime
    q4_boundary = datetime(2025, 12, 31)
    
    try:
        fig.add_vline(
            x=q4_boundary, 
            line_dash="dash", 
            line_color="#ef4444",
            annotation_text="Q4/Q1 Boundary"
        )
    except:
        pass
    
    fig.update_layout(
        height=400,
        yaxis_title="Deal Amount ($)",
        xaxis_title="Expected Close Date",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#f8fafc", family="Inter"),
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(color="#94a3b8")
        ),
        xaxis=dict(showgrid=False, tickfont=dict(color='#94a3b8')),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#94a3b8'))
    )
    
    return fig

def create_invoice_status_chart(invoices_df, rep_name=None):
    """Create a chart showing invoice breakdown by status"""
    
    if invoices_df.empty:
        return None
    
    if rep_name:
        invoices_df = invoices_df[invoices_df['Sales Rep'] == rep_name]
    
    if invoices_df.empty:
        return None
    
    status_summary = invoices_df.groupby('Status')['Amount'].sum().reset_index()
    
    fig = px.pie(
        status_summary,
        values='Amount',
        names='Status',
        title='Invoice Amount by Status',
        hole=0.4
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#f8fafc", family="Inter"),
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(color="#94a3b8")
        )
    )
    
    return fig

def display_drill_down_section(title, amount, details_df, key_suffix):
    """Display a collapsible section with order details - WITH PROPER SO# AND LINKS"""
    
    item_count = len(details_df)
    with st.expander(f"{title}: ${amount:,.2f} (👀 Click to see {item_count} {'item' if item_count == 1 else 'items'})"):
        if not details_df.empty:
            # DEBUG: Check for duplicate columns
            if details_df.columns.duplicated().any():
                st.warning(f"⚠️ Duplicate columns detected: {details_df.columns[details_df.columns.duplicated()].tolist()}")
                # Remove duplicates
                details_df = details_df.loc[:, ~details_df.columns.duplicated()]
            
            try:
                # Determine data type and prepare display
                is_hubspot = 'Deal Name' in details_df.columns
                is_netsuite = 'Document Number' in details_df.columns or 'Internal ID' in details_df.columns
                
                # Create display dataframe
                display_df = pd.DataFrame()
                column_config = {}
                
                if is_hubspot and 'Record ID' in details_df.columns:
                    # HubSpot deals
                    display_df['🔗 Link'] = details_df['Record ID'].apply(
                        lambda x: f'https://app.hubspot.com/contacts/6712259/record/0-3/{x}/' if pd.notna(x) else ''
                    )
                    column_config['🔗 Link'] = st.column_config.LinkColumn(
                        "🔗 Link",
                        help="Click to view deal in HubSpot",
                        display_text="View Deal"
                    )
                    
                    # Add other HubSpot columns
                    if 'Deal Name' in details_df.columns:
                        display_df['Deal Name'] = details_df['Deal Name']
                    if 'Amount' in details_df.columns:
                        display_df['Amount'] = details_df['Amount'].apply(lambda x: f"${x:,.2f}")
                    if 'Status' in details_df.columns:
                        display_df['Status'] = details_df['Status']
                    if 'Pipeline' in details_df.columns:
                        display_df['Pipeline'] = details_df['Pipeline']
                    if 'Close Date' in details_df.columns:
                        if pd.api.types.is_datetime64_any_dtype(details_df['Close Date']):
                            display_df['Close Date'] = details_df['Close Date'].dt.strftime('%Y-%m-%d')
                        else:
                            display_df['Close Date'] = details_df['Close Date']
                    if 'Product Type' in details_df.columns:
                        display_df['Product Type'] = details_df['Product Type']
                
                elif is_netsuite:
                    # NetSuite sales orders - ALWAYS show Internal ID and create link if available
                    if 'Internal ID' in details_df.columns:
                        display_df['🔗 Link'] = details_df['Internal ID'].apply(
                            lambda x: f'https://7086864.app.netsuite.com/app/accounting/transactions/salesord.nl?id={x}&whence=' if pd.notna(x) else ''
                        )
                        column_config['🔗 Link'] = st.column_config.LinkColumn(
                            "🔗 Link",
                            help="Click to view sales order in NetSuite",
                            display_text="View SO"
                        )
                        # Also show Internal ID as a regular column
                        display_df['Internal ID'] = details_df['Internal ID']
                    
                    # Add SO# (Document Number)
                    if 'Document Number' in details_df.columns:
                        display_df['SO#'] = details_df['Document Number']
                    
                    # Add other NetSuite columns
                    if 'Customer' in details_df.columns:
                        display_df['Customer'] = details_df['Customer']
                    if 'Amount' in details_df.columns:
                        display_df['Amount'] = details_df['Amount'].apply(lambda x: f"${x:,.2f}")
                    if 'Status' in details_df.columns:
                        display_df['Status'] = details_df['Status']
                    if 'Order Start Date' in details_df.columns:
                        if pd.api.types.is_datetime64_any_dtype(details_df['Order Start Date']):
                            display_df['Order Start Date'] = details_df['Order Start Date'].dt.strftime('%Y-%m-%d')
                        else:
                            display_df['Order Start Date'] = details_df['Order Start Date']
                    if 'Pending Approval Date' in details_df.columns:
                        if pd.api.types.is_datetime64_any_dtype(details_df['Pending Approval Date']):
                            display_df['Pending Approval Date'] = details_df['Pending Approval Date'].dt.strftime('%Y-%m-%d')
                        else:
                            display_df['Pending Approval Date'] = details_df['Pending Approval Date']
                    if 'Customer Promise Date' in details_df.columns:
                        if pd.api.types.is_datetime64_any_dtype(details_df['Customer Promise Date']):
                            display_df['Customer Promise Date'] = details_df['Customer Promise Date'].dt.strftime('%Y-%m-%d')
                        else:
                            display_df['Customer Promise Date'] = details_df['Customer Promise Date']
                    if 'Projected Date' in details_df.columns:
                        if pd.api.types.is_datetime64_any_dtype(details_df['Projected Date']):
                            display_df['Projected Date'] = details_df['Projected Date'].dt.strftime('%Y-%m-%d')
                        else:
                            display_df['Projected Date'] = details_df['Projected Date']
                
                # Display the dataframe
                if not display_df.empty:
                    st.dataframe(
                        display_df, 
                        use_container_width=True, 
                        hide_index=True,
                        column_config=column_config if column_config else None
                    )
                    
                    # Summary statistics
                    st.caption(f"Total: ${details_df['Amount'].sum():,.2f} | Count: {len(details_df)} items")
                else:
                    # Fallback - show available columns for debugging
                    st.warning(f"Could not format data. Available columns: {details_df.columns.tolist()}")
                    st.dataframe(details_df, use_container_width=True, hide_index=True)
                    
            except Exception as e:
                st.error(f"Error displaying data: {str(e)}")
                st.write(f"Available columns: {details_df.columns.tolist()}")
                # Show raw data as fallback
                st.dataframe(details_df.head(), use_container_width=True, hide_index=True)
        else:
            st.info("📭 Nothing to see here... yet!")

def display_progress_breakdown(metrics):
    """Display a beautiful progress breakdown card"""
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        position: relative;
        overflow: hidden;
        box-shadow: 0 0 30px rgba(99, 102, 241, 0.1), 0 10px 40px rgba(0, 0, 0, 0.3);
    ">
        <div style="position: absolute; top: 0; left: 0; width: 5px; height: 100%; background: linear-gradient(180deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);"></div>
        <h3 style="color: #f1f5f9 !important; font-size: 1.25rem; font-weight: 700; margin-bottom: 1.5rem; padding-left: 0.5rem;">
            💰 The Safe Bet <span style="font-size: 0.8em; opacity: 0.6; font-weight: 400; margin-left: auto;">High Confidence Revenue</span>
        </h3>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 0.5rem; border-bottom: 1px solid rgba(71, 85, 105, 0.3);">
            <span style="color: #94a3b8; font-size: 0.95rem; font-weight: 500;">✅ Invoiced & Shipped</span>
            <span style="font-size: 1.1rem; font-weight: 700; color: #3b82f6;">${metrics['orders']:,.0f}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 0.5rem; border-bottom: 1px solid rgba(71, 85, 105, 0.3);">
            <span style="color: #94a3b8; font-size: 0.95rem; font-weight: 500;">📦 Pending Fulfillment</span>
            <span style="font-size: 1.1rem; font-weight: 700; color: #f59e0b;">${metrics['pending_fulfillment']:,.0f}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 0.5rem; border-bottom: 1px solid rgba(71, 85, 105, 0.3);">
            <span style="color: #94a3b8; font-size: 0.95rem; font-weight: 500;">⏳ Pending Approval</span>
            <span style="font-size: 1.1rem; font-weight: 700; color: #f97316;">${metrics['pending_approval']:,.0f}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 0.5rem; border-bottom: 1px solid rgba(71, 85, 105, 0.3);">
            <span style="color: #94a3b8; font-size: 0.95rem; font-weight: 500;">🎯 HubSpot Expect/Commit</span>
            <span style="font-size: 1.1rem; font-weight: 700; color: #10b981;">${metrics['expect_commit']:,.0f}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 1.25rem 0.5rem; margin-top: 1rem; border-top: 2px solid rgba(99, 102, 241, 0.3);">
            <span style="color: white; font-size: 0.95rem; font-weight: 600;">TOTAL CONFIRMED</span>
            <span style="font-size: 1.4rem; font-weight: 700; background: linear-gradient(to right, #fff, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">${metrics['total_progress']:,.0f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Add attainment info below
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Current Attainment", f"{metrics['attainment_pct']:.1f}%", 
                 delta=f"${metrics['total_progress']:,.0f} of ${metrics['quota']:,.0f}",
                 help="This is real money! 💵")
    with col2:
        st.metric("If Everything Goes Right", f"{metrics['potential_attainment']:.1f}%",
                 delta=f"+${metrics['best_opp']:,.0f} Best Case/Opp",
                 help="The optimist's view (we believe! 🌟)")

def display_team_dashboard(deals_df, dashboard_df, invoices_df, sales_orders_df, q4_push_df=None):
    """Display the team-level dashboard"""
   
    st.title("🎯 Team Sales Dashboard - Q1 2026")
    
    # Show indicator for shipping mode
    include_shipping = st.session_state.get('include_shipping', True)
    if include_shipping:
        st.caption("💰 Revenue figures include shipping & tax")
    else:
        st.caption("📦 Revenue figures exclude shipping & tax (product revenue only)")
   
    # Calculate basic metrics
    basic_metrics = calculate_team_metrics(deals_df, dashboard_df)
   
    # Aggregate full team metrics from per-rep calculations
    team_quota = basic_metrics['total_quota']
    team_best_opp = basic_metrics['best_opp']
    team_q1_spillover_expect_commit = 0  # Q1 spillover Expect/Commit only
    team_q1_spillover_best_opp = 0  # Q1 spillover Best Case/Opportunity
    
    # Filter out unwanted reps
    excluded_reps = ['House', 'house', 'HOUSE']
   
    team_invoiced = 0
    team_pf = 0
    team_pa = 0
    team_hs = 0
    team_pf_no_date = 0
    team_pa_no_date = 0
    team_old_pa = 0
    
    # Determine which amount column to use based on shipping toggle
    include_shipping = st.session_state.get('include_shipping', True)
    amount_col = 'Amount' if include_shipping else 'Net_Amount'
    
    # FIX: Calculate team_invoiced directly from invoices_df to match Invoice Detail section
    if not invoices_df.empty and amount_col in invoices_df.columns:
        # Filter out House reps if needed
        if 'Sales Rep' in invoices_df.columns:
            filtered_inv = invoices_df[~invoices_df['Sales Rep'].isin(excluded_reps)].copy()
        else:
            filtered_inv = invoices_df.copy()
        
        # Calculate total invoiced amount using the appropriate column
        filtered_inv['Amount_Numeric'] = pd.to_numeric(filtered_inv[amount_col], errors='coerce')
        team_invoiced = filtered_inv['Amount_Numeric'].sum()
    elif not invoices_df.empty and 'Amount' in invoices_df.columns:
        # Fallback to Amount if Net_Amount doesn't exist
        if 'Sales Rep' in invoices_df.columns:
            filtered_inv = invoices_df[~invoices_df['Sales Rep'].isin(excluded_reps)].copy()
        else:
            filtered_inv = invoices_df.copy()
        filtered_inv['Amount_Numeric'] = pd.to_numeric(filtered_inv['Amount'], errors='coerce')
        team_invoiced = filtered_inv['Amount_Numeric'].sum()
    else:
        team_invoiced = 0
   
    section1_data = []
    section2_data = []
    
    for rep_name in dashboard_df['Rep Name']:
        # Skip excluded reps
        if rep_name in excluded_reps:
            continue
            
        rep_metrics = calculate_rep_metrics(rep_name, deals_df, dashboard_df, sales_orders_df)
        if rep_metrics:
            section1_total = (rep_metrics['orders'] + rep_metrics['pending_fulfillment'] +
                              rep_metrics['pending_approval'] + rep_metrics['expect_commit'])
            final_total = (section1_total + rep_metrics['pending_fulfillment_no_date'] +
                           rep_metrics['pending_approval_no_date'] + rep_metrics['pending_approval_old'])
           
            section1_data.append({
                'Rep': rep_name,
                'Invoiced': f"${rep_metrics['orders']:,.0f}",
                'Pending Fulfillment': f"${rep_metrics['pending_fulfillment']:,.0f}",
                'Pending Approval': f"${rep_metrics['pending_approval']:,.0f}",
                'HubSpot Expect/Commit': f"${rep_metrics['expect_commit']:,.0f}",
                'Total': f"${section1_total:,.0f}"
            })
           
            section2_data.append({
                'Rep': rep_name,
                'PF SO\'s No Date': f"${rep_metrics['pending_fulfillment_no_date']:,.0f}",
                'PA SO\'s No Date': f"${rep_metrics['pending_approval_no_date']:,.0f}",
                'Old PA (>2 weeks)': f"${rep_metrics['pending_approval_old']:,.0f}",
                'Total Q4': f"${final_total:,.0f}"
            })
           
            # Aggregate sums (exclude invoiced since we calculate it directly from invoices_df now)
            # team_invoiced += rep_metrics['orders']  # REMOVED - now calculated from raw invoices_df
            team_pf += rep_metrics['pending_fulfillment']
            team_pa += rep_metrics['pending_approval']
            team_hs += rep_metrics['expect_commit']
            team_pf_no_date += rep_metrics['pending_fulfillment_no_date']
            team_pa_no_date += rep_metrics['pending_approval_no_date']
            team_old_pa += rep_metrics['pending_approval_old']
            team_q1_spillover_expect_commit += rep_metrics.get('q1_spillover_expect_commit', 0)
            team_q1_spillover_best_opp += rep_metrics.get('q1_spillover_best_opp', 0)
   
    # Calculate team totals
    base_forecast = team_invoiced + team_pf + team_pa + team_hs
    full_forecast = base_forecast + team_pf_no_date + team_pa_no_date + team_old_pa
    base_gap = team_quota - base_forecast
    full_gap = team_quota - full_forecast
    base_attainment_pct = (base_forecast / team_quota * 100) if team_quota > 0 else 0
    full_attainment_pct = (full_forecast / team_quota * 100) if team_quota > 0 else 0
    potential_attainment = ((base_forecast + team_best_opp) / team_quota * 100) if team_quota > 0 else 0
    
    # NEW: Calculate Best Case only (not Opportunity) for optimistic gap
    if not deals_df.empty:
        spillover_col = get_spillover_column(deals_df)
        if spillover_col:
            q1_mask = is_q1_deal(deals_df, spillover_col)
            deals_q1 = deals_df[q1_mask]
        else:
            deals_q1 = deals_df
    else:
        deals_q1 = pd.DataFrame()
    team_best_case = deals_q1[deals_q1['Status'] == 'Best Case']['Amount'].sum() if not deals_q1.empty and 'Status' in deals_q1.columns else 0
    
    # NEW: Optimistic Gap = Quota - (High Confidence + Best Case + PF no date + PA no date + PA >2 weeks)
    optimistic_forecast = base_forecast + team_best_case + team_pf_no_date + team_pa_no_date + team_old_pa
    optimistic_gap = team_quota - optimistic_forecast
   
    # Add total rows to data
    section1_data.append({
        'Rep': 'TOTAL',
        'Invoiced': f"${team_invoiced:,.0f}",
        'Pending Fulfillment': f"${team_pf:,.0f}",
        'Pending Approval': f"${team_pa:,.0f}",
        'HubSpot Expect/Commit': f"${team_hs:,.0f}",
        'Total': f"${base_forecast:,.0f}"
    })
   
    section2_data.append({
        'Rep': 'TOTAL',
        'PF SO\'s No Date': f"${team_pf_no_date:,.0f}",
        'PA SO\'s No Date': f"${team_pa_no_date:,.0f}",
        'Old PA (>2 weeks)': f"${team_old_pa:,.0f}",
        'Total Q1': f"${full_forecast:,.0f}"
    })
   
    # Display Q2 spillover info if applicable
    team_q2_spillover_total = team_q1_spillover_expect_commit + team_q1_spillover_best_opp
    if team_q2_spillover_total > 0:
        st.info(
            f"ℹ️ **Q2 2026 Spillover**: ${team_q2_spillover_total:,.0f} in deals closing late Q1 2026 "
            f"will ship in Q2 2026 due to product lead times. These are excluded from Q1 revenue recognition."
        )
   
    # Display key metrics with two breakdowns
    st.markdown("### 📊 Team Scorecard")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
   
    with col1:
        st.metric(
            label="🎯 Total Quota",
            value=f"${team_quota/1000:.0f}K" if team_quota < 1000000 else f"${team_quota/1000000:.1f}M",
            delta=None,
            help="Q1 2026 Sales Target"
        )
   
    with col2:
        st.metric(
            label="💪 High Confidence Forecast",
            value=f"${base_forecast/1000:.0f}K" if base_forecast < 1000000 else f"${base_forecast/1000000:.1f}M",
            delta=f"{base_attainment_pct:.1f}% of quota",
            help="Invoiced + PF (with date) + PA (with date) + HS Expect/Commit"
        )
   
    with col3:
        st.metric(
            label="📊 Full Forecast (All Sources)",
            value=f"${full_forecast/1000:.0f}K" if full_forecast < 1000000 else f"${full_forecast/1000000:.1f}M",
            delta=f"{full_attainment_pct:.1f}% of quota",
            help="Invoiced + PF (with date) + PA (with date) + HS Expect/Commit + PF (without date) + PA (without date) + PA (>2 weeks old)"
        )
    
    with col4:
        st.metric(
            label="📉 Gap to Quota",
            value=f"${base_gap/1000:.0f}K" if abs(base_gap) < 1000000 else f"${base_gap/1000000:.1f}M",
            delta=f"${-base_gap/1000:.0f}K" if base_gap < 0 else None,
            delta_color="inverse",
            help="Quota - (Invoiced + PF (with date) + PA (with date) + HS Expect/Commit)"
        )
    
    with col5:
        st.metric(
            label="📈 Optimistic Gap",
            value=f"${optimistic_gap/1000:.0f}K" if abs(optimistic_gap) < 1000000 else f"${optimistic_gap/1000000:.1f}M",
            delta=f"${-optimistic_gap/1000:.0f}K" if optimistic_gap < 0 else None,
            delta_color="inverse",
            help="Quota - (High Confidence + HS Best Case + PF (no date) + PA (no date) + PA >2 weeks)"
        )

    with col6:
        st.metric(
            label="🌟 Potential Attainment",
            value=f"{potential_attainment:.1f}%",
            delta=f"+{potential_attainment - base_attainment_pct:.1f}% upside",
            help="(High Confidence + HS Best Case/Opp) ÷ Quota"
        )
    
    # Add expandable breakdown details
    with st.expander("🔍 View Calculation Breakdowns", expanded=False):
        st.markdown("#### Detailed Component Breakdown")
        
        breakdown_col1, breakdown_col2 = st.columns(2)
        
        with breakdown_col1:
            st.markdown("##### 💪 High Confidence Forecast")
            st.markdown(f"""
            - **Invoiced:** ${team_invoiced:,.0f}
            - **Pending Fulfillment (with date):** ${team_pf:,.0f}
            - **Pending Approval (with date):** ${team_pa:,.0f}
            - **HubSpot Expect/Commit:** ${team_hs:,.0f}
            - **Total:** ${base_forecast:,.0f}
            - **% of Quota:** {base_attainment_pct:.1f}%
            """)
        
        with breakdown_col2:
            st.markdown("##### 📊 Full Forecast (All Sources)")
            st.markdown(f"""
            **High Confidence Components:**
            - Invoiced: ${team_invoiced:,.0f}
            - PF (with date): ${team_pf:,.0f}
            - PA (with date): ${team_pa:,.0f}
            - HS Expect/Commit: ${team_hs:,.0f}
            
            **Additional Sources:**
            - PF (no date): ${team_pf_no_date:,.0f}
            - PA (no date): ${team_pa_no_date:,.0f}
            - PA (>2 weeks): ${team_old_pa:,.0f}
            
            **Total:** ${full_forecast:,.0f}
            - **% of Quota:** {full_attainment_pct:.1f}%
            """)
        
        st.markdown("---")
        
        breakdown_col3, breakdown_col4 = st.columns(2)
        
        with breakdown_col3:
            st.markdown("##### 📈 Optimistic Scenario")
            st.markdown(f"""
            - **High Confidence:** ${base_forecast:,.0f}
            - **Plus: HS Best Case:** ${team_best_case:,.0f}
            - **Plus: PF (no date):** ${team_pf_no_date:,.0f}
            - **Plus: PA (no date):** ${team_pa_no_date:,.0f}
            - **Plus: PA (>2 weeks):** ${team_old_pa:,.0f}
            - **Optimistic Total:** ${optimistic_forecast:,.0f}
            - **Gap to Quota:** ${optimistic_gap:,.0f}
            """)
   
    # Invoices section and audit section
    st.markdown("---")
    
    # Change detection and audit section
    if st.checkbox("📊 Show Day-Over-Day Audit", value=False):
        create_dod_audit_section(deals_df, dashboard_df, invoices_df, sales_orders_df)
    
    st.markdown("---")
    
    # Invoices section
    display_invoices_drill_down(invoices_df)
    
    st.markdown("---")
    
    # Build Your Own Forecast section
    team_metrics_for_forecast = {
        'orders': team_invoiced,
        'pending_fulfillment': team_pf,
        'pending_approval': team_pa,
        'expect_commit': team_hs,
        'pending_fulfillment_no_date': team_pf_no_date,
        'pending_approval_no_date': team_pa_no_date,
        'pending_approval_old': team_old_pa,
        'q1_spillover_expect_commit': team_q1_spillover_expect_commit,
        'q1_spillover_best_opp': team_q1_spillover_best_opp
    }
    build_your_own_forecast_section(
        team_metrics_for_forecast,
        team_quota,
        rep_name=None,
        deals_df=deals_df,
        invoices_df=invoices_df,
        sales_orders_df=sales_orders_df,
        q4_push_df=q4_push_df
    )
    
    st.markdown("---")
    
    # HubSpot Deals Audit Section
    display_hubspot_deals_audit(deals_df)
    
    st.markdown("---")
    
    # Progress bars for both breakdowns
    st.markdown("### 📈 Progress to Quota")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**💪 High Confidence Forecast Progress**")
        st.caption("Confirmed orders and forecast with dates")
        base_progress = min(base_attainment_pct / 100, 1.0)
        st.progress(base_progress)
        st.caption(f"Current: {base_attainment_pct:.1f}% | Potential: {potential_attainment:.1f}%")
   
    with col2:
        st.markdown("**📊 Full Forecast Progress**")
        st.caption("All sources including orders without dates")
        full_progress = min(full_attainment_pct / 100, 1.0)
        st.progress(full_progress)
        st.caption(f"Current: {full_attainment_pct:.1f}%")
   
    # Base Forecast Chart with Enhanced Annotations
    st.markdown("### 💪 High Confidence Forecast Breakdown")
    st.caption("Orders and deals with confirmed dates and high confidence")
    
    # Create metrics dict for base chart
    base_metrics = {
        'orders': team_invoiced,
        'pending_fulfillment': team_pf,
        'pending_approval': team_pa,
        'expect_commit': team_hs,
        'best_opp': team_best_opp,
        'total_progress': base_forecast,
        'total_quota': team_quota
    }
    
    base_chart = create_enhanced_waterfall_chart(base_metrics, "💪 High Confidence Forecast - Path to Quota", "base")
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
    
    # Show indicator for shipping mode
    include_shipping = st.session_state.get('include_shipping', True)
    if include_shipping:
        st.caption("💰 Revenue figures include shipping & tax")
    else:
        st.caption("📦 Revenue figures exclude shipping & tax (product revenue only)")
    
    # DEBUG: Show rep name matching info
    with st.expander("🔧 Debug: Sales Order Rep Matching (for Xander)", expanded=False):
        if not sales_orders_df.empty and 'Sales Rep' in sales_orders_df.columns:
            unique_reps = sales_orders_df['Sales Rep'].unique().tolist()
            st.write(f"**Looking for:** `{rep_name}`")
            st.write(f"**Available Sales Reps in SO data:** {unique_reps}")
            matches = sales_orders_df[sales_orders_df['Sales Rep'] == rep_name]
            st.write(f"**Exact matches found:** {len(matches)} orders")
            if len(matches) == 0:
                # Check for partial matches
                partial = [r for r in unique_reps if rep_name.lower() in str(r).lower() or str(r).lower() in rep_name.lower()]
                st.warning(f"**Possible partial matches:** {partial}")
        else:
            st.error("Sales Orders DataFrame is empty or missing 'Sales Rep' column")
    
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
    <div style="
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        position: relative;
        overflow: hidden;
        box-shadow: 0 0 30px rgba(99, 102, 241, 0.1), 0 10px 40px rgba(0, 0, 0, 0.3);
    ">
        <div style="position: absolute; top: 0; left: 0; width: 5px; height: 100%; background: linear-gradient(180deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);"></div>
        <h3 style="color: #f1f5f9 !important; font-size: 1.25rem; font-weight: 700; margin-bottom: 1.5rem; padding-left: 0.5rem;">
            💰 Section 1: What's in NetSuite with Dates and HubSpot Expect/Commit
        </h3>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 0.5rem; border-bottom: 1px solid rgba(71, 85, 105, 0.3);">
            <span style="color: #94a3b8; font-size: 0.95rem; font-weight: 500;">✅ Invoiced & Shipped</span>
            <span style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0;">${metrics['orders']:,.0f}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 0.5rem; border-bottom: 1px solid rgba(71, 85, 105, 0.3);">
            <span style="color: #94a3b8; font-size: 0.95rem; font-weight: 500;">📦 Pending Fulfillment (with date)</span>
            <span style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0;">${metrics['pending_fulfillment']:,.0f}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 0.5rem; border-bottom: 1px solid rgba(71, 85, 105, 0.3);">
            <span style="color: #94a3b8; font-size: 0.95rem; font-weight: 500;">⏳ Pending Approval (with date)</span>
            <span style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0;">${metrics['pending_approval']:,.0f}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 0.5rem; border-bottom: 1px solid rgba(71, 85, 105, 0.3);">
            <span style="color: #94a3b8; font-size: 0.95rem; font-weight: 500;">🎯 HubSpot Expect/Commit</span>
            <span style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0;">${metrics['expect_commit']:,.0f}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 1.25rem 0.5rem; margin-top: 1rem; border-top: 2px solid rgba(99, 102, 241, 0.3);">
            <span style="color: white; font-size: 0.95rem; font-weight: 600;">💪 THE SAFE BET TOTAL</span>
            <span style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0;">${high_confidence:,.0f}</span>
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
    <div style="
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        position: relative;
        overflow: hidden;
        box-shadow: 0 0 30px rgba(99, 102, 241, 0.1), 0 10px 40px rgba(0, 0, 0, 0.3);
    ">
        <div style="position: absolute; top: 0; left: 0; width: 5px; height: 100%; background: linear-gradient(180deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);"></div>
        <h3 style="color: #f1f5f9 !important; font-size: 1.25rem; font-weight: 700; margin-bottom: 1.5rem; padding-left: 0.5rem;">
            📊 Section 2: Full Forecast
        </h3>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 0.5rem; border-bottom: 1px solid rgba(71, 85, 105, 0.3);">
            <span style="color: #94a3b8; font-size: 0.95rem; font-weight: 500;">✅ Invoiced & Shipped</span>
            <span style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0;">${metrics['orders']:,.0f}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 0.5rem; border-bottom: 1px solid rgba(71, 85, 105, 0.3);">
            <span style="color: #94a3b8; font-size: 0.95rem; font-weight: 500;">📦 Pending Fulfillment (with date)</span>
            <span style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0;">${metrics['pending_fulfillment']:,.0f}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 0.5rem; border-bottom: 1px solid rgba(71, 85, 105, 0.3);">
            <span style="color: #94a3b8; font-size: 0.95rem; font-weight: 500;">⏳ Pending Approval (with date)</span>
            <span style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0;">${metrics['pending_approval']:,.0f}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 0.5rem; border-bottom: 1px solid rgba(71, 85, 105, 0.3);">
            <span style="color: #94a3b8; font-size: 0.95rem; font-weight: 500;">🎯 HubSpot Expect/Commit</span>
            <span style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0;">${metrics['expect_commit']:,.0f}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 0.5rem; border-bottom: 1px solid rgba(71, 85, 105, 0.3);">
            <span style="color: #94a3b8; font-size: 0.95rem; font-weight: 500;">📦 Pending Fulfillment (without date)</span>
            <span style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0;">${metrics['pending_fulfillment_no_date']:,.0f}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 0.5rem; border-bottom: 1px solid rgba(71, 85, 105, 0.3);">
            <span style="color: #94a3b8; font-size: 0.95rem; font-weight: 500;">⏳ Pending Approval (without date)</span>
            <span style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0;">${metrics['pending_approval_no_date']:,.0f}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 0.5rem; border-bottom: 1px solid rgba(71, 85, 105, 0.3);">
            <span style="color: #94a3b8; font-size: 0.95rem; font-weight: 500;">⏱️ Pending Approval (>2 weeks old)</span>
            <span style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0;">${metrics['pending_approval_old']:,.0f}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 1.25rem 0.5rem; margin-top: 1rem; border-top: 2px solid rgba(99, 102, 241, 0.3);">
            <span style="color: white; font-size: 0.95rem; font-weight: 600;">📊 FULL FORECAST TOTAL</span>
            <span style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0;">${full_forecast:,.0f}</span>
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

# ============================================================================
# CRO WEEKLY SCORECARD - Replicates Google Apps Script Email Report
# ============================================================================

# ============================================================================
# CRO WEEKLY SCORECARD - Replicates Google Apps Script Email Report
# ============================================================================

def display_cro_scorecard(deals_df, dashboard_df, invoices_df, sales_orders_df):
    """
    Display CRO Weekly Scorecard - matches the Google Apps Script email report.
    Shows comprehensive forecast metrics for all reps with Face Value and Probability views.
    Includes forecast plug support for Alex, House, and Shopify ECommerce.
    """
    
    # Configuration (matches Google Apps Script)
    REP_ORDER = [
        'Jake Lynch',
        'Dave Borkowski', 
        'Alex Gonzalez',
        'Brad Sherman',
        'Lance Mitton',
        'House',
        'Shopify ECommerce'
    ]
    
    # Get shipping toggle state
    include_shipping = st.session_state.get('include_shipping', True)
    exclude_shipping_tax = not include_shipping
    
    # --- HEADER ---
    report_date = get_mst_time().strftime('%b %d, %Y')
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #60a5fa, #a78bfa, #f472b6);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
    ">
        <div style="font-size: 32px; font-weight: 800; color: #0f172a;">📊 CRO Weekly Scorecard</div>
        <div style="font-size: 16px; color: #1e293b;">{report_date} • Q1 2026</div>
    </div>
    """, unsafe_allow_html=True)
    
    # --- FORECAST PLUGS SECTION ---
    st.markdown("### ⚡ HubSpot Expect Plugs")
    st.caption("Add forecast adjustments for deals not yet in HubSpot. These amounts will be added to HS E/C.")
    
    plug_col1, plug_col2, plug_col3 = st.columns(3)
    
    with plug_col1:
        plug_alex = st.number_input(
            "Alex Gonzalez",
            min_value=0,
            value=int(st.session_state.get('plug_alex', 0)),
            step=10000,
            format="%d",
            key="plug_alex_input",
            help="Plug amount for Alex Gonzalez"
        )
        st.session_state.plug_alex = plug_alex
    
    with plug_col2:
        plug_house = st.number_input(
            "House",
            min_value=0,
            value=int(st.session_state.get('plug_house', 0)),
            step=10000,
            format="%d",
            key="plug_house_input",
            help="Plug amount for House"
        )
        st.session_state.plug_house = plug_house
    
    with plug_col3:
        plug_ecom = st.number_input(
            "Shopify ECommerce",
            min_value=0,
            value=int(st.session_state.get('plug_ecom', 0)),
            step=10000,
            format="%d",
            key="plug_ecom_input",
            help="Plug amount for Shopify ECommerce"
        )
        st.session_state.plug_ecom = plug_ecom
    
    # Store plugs in a dict
    plugs = {
        'Alex Gonzalez': plug_alex,
        'House': plug_house,
        'Shopify ECommerce': plug_ecom
    }
    total_plugs = sum(plugs.values())
    
    if total_plugs > 0:
        plug_parts = []
        if plug_alex > 0:
            plug_parts.append(f"Alex: ${plug_alex:,}")
        if plug_house > 0:
            plug_parts.append(f"House: ${plug_house:,}")
        if plug_ecom > 0:
            plug_parts.append(f"Ecom: ${plug_ecom:,}")
        
        st.success(f"⚡ **Total Plugs: ${total_plugs:,}** ({', '.join(plug_parts)})")
    
    st.markdown("---")
    
    # --- SHIPPING/TAX INDICATOR ---
    if exclude_shipping_tax:
        st.caption("📦 NetSuite amounts shown **excluding** shipping & tax")
    else:
        st.caption("📦 NetSuite amounts shown **including** shipping & tax (gross totals)")
    
    # --- LOAD QUOTAS ---
    quotas = {}
    if not dashboard_df.empty:
        for _, row in dashboard_df.iterrows():
            rep_name = str(row.get('Rep Name', '')).strip()
            if rep_name:
                quota = 0
                for col in dashboard_df.columns:
                    if 'q1' in col.lower() and '2026' in col.lower() and 'quota' in col.lower():
                        quota = pd.to_numeric(row.get(col, 0), errors='coerce') or 0
                        break
                if quota == 0:
                    quota = pd.to_numeric(row.get('Q1 2026 Quota', row.get('Quota', 0)), errors='coerce') or 0
                quotas[rep_name] = quota
    
    # --- CALCULATE INVOICED BY REP ---
    rep_invoiced = {}
    if not invoices_df.empty:
        amount_col = 'Amount' if include_shipping else 'Net_Amount'
        if amount_col not in invoices_df.columns:
            amount_col = 'Amount'
        
        for rep in REP_ORDER:
            if rep.lower() == 'house':
                continue  # Skip House for invoices
            
            rep_inv = invoices_df[invoices_df['Sales Rep'] == rep] if 'Sales Rep' in invoices_df.columns else pd.DataFrame()
            if not rep_inv.empty and amount_col in rep_inv.columns:
                rep_invoiced[rep] = pd.to_numeric(rep_inv[amount_col], errors='coerce').fillna(0).sum()
            else:
                rep_invoiced[rep] = 0
    
    # --- CALCULATE SALES ORDER METRICS BY REP ---
    def get_so_metrics(rep_name):
        metrics = {'pf_with_date': 0, 'pf_no_date': 0, 'pa_with_date': 0, 'pa_no_date': 0, 'pa_old': 0}
        
        if sales_orders_df.empty:
            return metrics
        
        if 'Sales Rep' not in sales_orders_df.columns:
            return metrics
        
        rep_orders = sales_orders_df[sales_orders_df['Sales Rep'] == rep_name].copy()
        if rep_orders.empty:
            return metrics
        
        amount_col = 'Amount' if include_shipping else 'Net_Amount'
        if amount_col not in rep_orders.columns:
            amount_col = 'Amount'
        if amount_col not in rep_orders.columns:
            return metrics
        
        rep_orders['Amount_Calc'] = pd.to_numeric(rep_orders[amount_col], errors='coerce').fillna(0)
        
        # Find Updated Status column
        status_col = None
        for col in ['Updated Status', 'Updated_Status', 'UpdatedStatus']:
            if col in rep_orders.columns:
                status_col = col
                break
        
        if not status_col:
            return metrics
        
        for _, row in rep_orders.iterrows():
            status = str(row.get(status_col, '')).strip()
            amount = row['Amount_Calc']
            
            if 'PF with Date' in status or 'PF w/ Date' in status:
                metrics['pf_with_date'] += amount
            elif 'PF No Date' in status or 'PF no Date' in status:
                metrics['pf_no_date'] += amount
            elif 'PA with Date' in status or 'PA w/ Date' in status:
                metrics['pa_with_date'] += amount
            elif 'PA No Date' in status or 'PA no Date' in status:
                metrics['pa_no_date'] += amount
            elif 'PA Old' in status or '>2 Week' in status:
                metrics['pa_old'] += amount
        
        return metrics
    
    # --- CALCULATE HUBSPOT METRICS BY REP ---
    def get_hs_metrics(rep_name):
        metrics = {
            'expect': 0, 'expect_prob': 0,
            'commit': 0, 'commit_prob': 0,
            'best_case': 0, 'best_case_prob': 0,
            'opportunity': 0, 'opportunity_prob': 0,
            'q2_spillover': 0, 'q2_spillover_prob': 0
        }
        
        if deals_df.empty or 'Deal Owner' not in deals_df.columns:
            return metrics
        
        rep_deals = deals_df[deals_df['Deal Owner'] == rep_name].copy()
        if rep_deals.empty:
            return metrics
        
        # Find spillover column
        spillover_col = None
        for col in rep_deals.columns:
            col_lower = str(col).lower()
            if 'spillover' in col_lower or ('q2' in col_lower and '2026' in col_lower):
                spillover_col = col
                break
        
        for _, row in rep_deals.iterrows():
            status = str(row.get('Status', '')).strip()
            amount = pd.to_numeric(row.get('Amount', 0), errors='coerce') or 0
            prob_amount = pd.to_numeric(row.get('Probability Rev', amount), errors='coerce') or amount
            
            # Check if Q2 spillover
            is_q2 = False
            if spillover_col and spillover_col in row.index:
                spillover_val = str(row.get(spillover_col, '')).upper()
                if 'Q2' in spillover_val:
                    is_q2 = True
                elif 'Q4' in spillover_val:
                    continue
            
            if is_q2:
                metrics['q2_spillover'] += amount
                metrics['q2_spillover_prob'] += prob_amount
            elif status == 'Expect':
                metrics['expect'] += amount
                metrics['expect_prob'] += prob_amount
            elif status == 'Commit':
                metrics['commit'] += amount
                metrics['commit_prob'] += prob_amount
            elif status == 'Best Case':
                metrics['best_case'] += amount
                metrics['best_case_prob'] += prob_amount
            elif status == 'Opportunity':
                metrics['opportunity'] += amount
                metrics['opportunity_prob'] += prob_amount
        
        return metrics
    
    # --- CALCULATE ALL REP METRICS ---
    all_metrics = {}
    for rep in REP_ORDER:
        so_metrics = get_so_metrics(rep)
        hs_metrics = get_hs_metrics(rep)
        
        invoiced = rep_invoiced.get(rep, 0)
        rep_plug = plugs.get(rep, 0)
        
        # Face Value calculations - PLUG ADDS TO HS E/C
        hs_expect_commit = hs_metrics['expect'] + hs_metrics['commit'] + rep_plug
        total_core = invoiced + so_metrics['pf_with_date'] + so_metrics['pa_with_date'] + hs_expect_commit
        all_q1 = total_core + so_metrics['pf_no_date'] + so_metrics['pa_no_date'] + so_metrics['pa_old']
        total_forecast = all_q1 + hs_metrics['best_case'] + hs_metrics['opportunity']
        full_pipeline = total_forecast + hs_metrics['q2_spillover']
        
        # Probability calculations - PLUG ADDS TO HS E/C PROB
        hs_expect_commit_prob = hs_metrics['expect_prob'] + hs_metrics['commit_prob'] + rep_plug
        total_core_prob = invoiced + so_metrics['pf_with_date'] + so_metrics['pa_with_date'] + hs_expect_commit_prob
        all_q1_prob = total_core_prob + so_metrics['pf_no_date'] + so_metrics['pa_no_date'] + so_metrics['pa_old']
        total_forecast_prob = all_q1_prob + hs_metrics['best_case_prob'] + hs_metrics['opportunity_prob']
        full_pipeline_prob = total_forecast_prob + hs_metrics['q2_spillover_prob']
        
        # Realistic total
        realistic_total = invoiced + so_metrics['pf_with_date'] + so_metrics['pf_no_date'] + so_metrics['pa_with_date'] + hs_metrics['expect'] + rep_plug
        
        all_metrics[rep] = {
            'invoiced': invoiced,
            'pf_with_date': so_metrics['pf_with_date'],
            'pf_no_date': so_metrics['pf_no_date'],
            'pa_with_date': so_metrics['pa_with_date'],
            'pa_no_date': so_metrics['pa_no_date'],
            'pa_old': so_metrics['pa_old'],
            'hs_expect_commit': hs_expect_commit,
            'hs_expect_commit_prob': hs_expect_commit_prob,
            'hs_best_case': hs_metrics['best_case'],
            'hs_best_case_prob': hs_metrics['best_case_prob'],
            'hs_opportunity': hs_metrics['opportunity'],
            'hs_opportunity_prob': hs_metrics['opportunity_prob'],
            'hs_q2_spillover': hs_metrics['q2_spillover'],
            'hs_q2_spillover_prob': hs_metrics['q2_spillover_prob'],
            'total_core': total_core,
            'total_core_prob': total_core_prob,
            'all_q1': all_q1,
            'all_q1_prob': all_q1_prob,
            'total_forecast': total_forecast,
            'total_forecast_prob': total_forecast_prob,
            'full_pipeline': full_pipeline,
            'full_pipeline_prob': full_pipeline_prob,
            'realistic_total': realistic_total,
            'quota': quotas.get(rep, 0),
            'plug': rep_plug
        }
    
    # --- CALCULATE TEAM TOTALS ---
    team_totals = {key: sum(m.get(key, 0) for m in all_metrics.values()) for key in [
        'invoiced', 'pf_with_date', 'pf_no_date', 'pa_with_date', 'pa_no_date', 'pa_old',
        'hs_expect_commit', 'hs_expect_commit_prob', 'hs_best_case', 'hs_best_case_prob',
        'hs_opportunity', 'hs_opportunity_prob', 'hs_q2_spillover', 'hs_q2_spillover_prob',
        'total_core', 'total_core_prob', 'all_q1', 'all_q1_prob',
        'total_forecast', 'total_forecast_prob', 'full_pipeline', 'full_pipeline_prob',
        'realistic_total', 'quota', 'plug'
    ]}
    
    team_quota = team_totals['quota']
    realistic_total = team_totals['realistic_total']
    realistic_pct = (realistic_total / team_quota * 100) if team_quota > 0 else 0
    realistic_gap = team_quota - realistic_total
    
    # Determine status
    if realistic_pct >= 100:
        status_emoji, status_text, status_color = '🟢', 'On Track', '#4ade80'
    elif realistic_pct >= 85:
        status_emoji, status_text, status_color = '🟡', 'Close - Push Needed', '#fbbf24'
    elif realistic_pct >= 70:
        status_emoji, status_text, status_color = '🟠', 'Work to Do', '#f97316'
    else:
        status_emoji, status_text, status_color = '🔴', 'Significant Gap', '#f87171'
    
    # --- EXECUTIVE SUMMARY ---
    st.markdown("### 📈 Where We Stand")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"""
        <div style="
            padding: 20px;
            background: rgba({','.join(str(int(status_color[i:i+2], 16)) for i in (1, 3, 5))}, 0.15);
            border-radius: 12px;
            border-left: 4px solid {status_color};
        ">
            <div style="font-size: 12px; color: #64748b; text-transform: uppercase;">Realistic vs Quota</div>
            <div style="font-size: 42px; font-weight: 700; color: {status_color};">{status_emoji} {realistic_pct:.0f}%</div>
            <div style="font-size: 16px; color: #f1f5f9; font-weight: 600;">{status_text}</div>
            <div style="font-size: 14px; color: #94a3b8; margin-top: 5px;">
                {'${:,.0f} gap'.format(realistic_gap) if realistic_gap > 0 else '${:,.0f} over'.format(abs(realistic_gap))}
            </div>
            <div style="font-size: 13px; color: #64748b; margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(100,116,139,0.3);">
                🏁 Quota: <span style="color: #f1f5f9; font-weight: 600;">${team_quota:,.0f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        r1, r2 = st.columns(2)
        with r1:
            st.metric("🟢 Invoiced", f"${team_totals['invoiced']:,.0f}")
            st.metric("🟡 PA w/ Date", f"${team_totals['pa_with_date']:,.0f}")
        with r2:
            st.metric("🟡 PF (all)", f"${team_totals['pf_with_date'] + team_totals['pf_no_date']:,.0f}")
            st.metric("🔵 HS Expect + Plugs", f"${team_totals['hs_expect_commit']:,.0f}")
        
        st.markdown(f"**Realistic Total: ${realistic_total:,.0f}** vs **Quota: ${team_quota:,.0f}**")
    
    # --- SUMMARY CARDS ---
    st.markdown("---")
    
    # Row 1
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Invoiced", f"${team_totals['invoiced']:,.0f}")
    c2.metric("📦 Pend Fulfill", f"${team_totals['pf_with_date'] + team_totals['pf_no_date']:,.0f}")
    c3.metric("📋 Pend Apprv", f"${team_totals['pa_with_date'] + team_totals['pa_no_date']:,.0f}")
    c4.metric("⚠️ PA >2wk", f"${team_totals['pa_old']:,.0f}")
    
    # Row 2
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("🎯 HS E/C", f"${team_totals['hs_expect_commit']:,.0f}")
    c6.metric("📈 Forecast", f"${team_totals['total_forecast']:,.0f}")
    c7.metric("📅 Q2 Spill", f"${team_totals['hs_q2_spillover']:,.0f}")
    c8.metric("🏁 Quota", f"${team_quota:,.0f}")
    
    # --- FACE VALUE TABLE ---
    st.markdown("---")
    st.markdown("### 💵 Face Value Forecast")
    st.caption("Full deal amounts, no probability adjustment")
    
    # Build dataframe
    face_data = []
    for rep in REP_ORDER:
        m = all_metrics.get(rep, {})
        quota = m.get('quota', 0)
        forecast = m.get('total_forecast', 0)
        pct = ((forecast - quota) / quota * 100) if quota > 0 else (100 if forecast > 0 else -100)
        
        # Add indicator for reps with plugs
        rep_display = f"{rep} ⚡" if m.get('plug', 0) > 0 else rep
        
        face_data.append({
            'Rep': rep_display,
            'Inv': m.get('invoiced', 0),
            'PF': m.get('pf_with_date', 0),
            'PA': m.get('pa_with_date', 0),
            'HS E/C': m.get('hs_expect_commit', 0),
            'Total': m.get('total_core', 0),
            'PF ND': m.get('pf_no_date', 0),
            'PA ND': m.get('pa_no_date', 0),
            'PA Old': m.get('pa_old', 0),
            'All Q1': m.get('all_q1', 0),
            'Best': m.get('hs_best_case', 0),
            'Opp': m.get('hs_opportunity', 0),
            'Forecast': forecast,
            'Q2 Spill': m.get('hs_q2_spillover', 0),
            'Full Pipe': m.get('full_pipeline', 0),
            'Quota': quota,
            '%': pct
        })
    
    # Add totals row
    pct_total = ((team_totals['total_forecast'] - team_quota) / team_quota * 100) if team_quota > 0 else 0
    face_data.append({
        'Rep': '**TOTAL**',
        'Inv': team_totals['invoiced'],
        'PF': team_totals['pf_with_date'],
        'PA': team_totals['pa_with_date'],
        'HS E/C': team_totals['hs_expect_commit'],
        'Total': team_totals['total_core'],
        'PF ND': team_totals['pf_no_date'],
        'PA ND': team_totals['pa_no_date'],
        'PA Old': team_totals['pa_old'],
        'All Q1': team_totals['all_q1'],
        'Best': team_totals['hs_best_case'],
        'Opp': team_totals['hs_opportunity'],
        'Forecast': team_totals['total_forecast'],
        'Q2 Spill': team_totals['hs_q2_spillover'],
        'Full Pipe': team_totals['full_pipeline'],
        'Quota': team_quota,
        '%': pct_total
    })
    
    face_df = pd.DataFrame(face_data)
    
    # Style the dataframe
    def style_face_value(df):
        # Create a style dataframe
        styles = pd.DataFrame('', index=df.index, columns=df.columns)
        
        # Highlight Total and All Q1 columns
        styles['Total'] = 'background-color: rgba(59, 130, 246, 0.2)'
        styles['All Q1'] = 'background-color: rgba(59, 130, 246, 0.2)'
        
        # Highlight Forecast column
        styles['Forecast'] = 'background-color: rgba(139, 92, 246, 0.3); color: #a78bfa; font-weight: bold'
        
        # Highlight Q2 and Full Pipe
        styles['Q2 Spill'] = 'color: #f472b6'
        styles['Full Pipe'] = 'background-color: rgba(244, 114, 182, 0.2); color: #f472b6'
        
        # Color % column based on value
        for i, row in df.iterrows():
            if row['%'] >= 0:
                styles.loc[i, '%'] = 'color: #4ade80; font-weight: bold'
            else:
                styles.loc[i, '%'] = 'color: #f87171; font-weight: bold'
        
        # Bold the totals row
        if len(df) > 0:
            styles.iloc[-1] = styles.iloc[-1].apply(lambda x: x + '; font-weight: bold; background-color: rgba(59, 130, 246, 0.3)')
        
        return styles
    
    currency_cols = ['Inv', 'PF', 'PA', 'HS E/C', 'Total', 'PF ND', 'PA ND', 'PA Old', 'All Q1', 'Best', 'Opp', 'Forecast', 'Q2 Spill', 'Full Pipe', 'Quota']
    
    st.dataframe(
        face_df.style.apply(style_face_value, axis=None).format({
            **{col: '${:,.0f}' for col in currency_cols},
            '%': '{:+.0f}%'
        }),
        hide_index=True,
        use_container_width=True,
        height=320
    )
    
    # --- PROBABILITY TABLE ---
    st.markdown("---")
    st.markdown("### 📊 Probability Forecast")
    st.caption("Weighted by close likelihood")
    
    prob_data = []
    for rep in REP_ORDER:
        m = all_metrics.get(rep, {})
        quota = m.get('quota', 0)
        forecast = m.get('total_forecast_prob', 0)
        pct = ((forecast - quota) / quota * 100) if quota > 0 else (100 if forecast > 0 else -100)
        
        rep_display = f"{rep} ⚡" if m.get('plug', 0) > 0 else rep
        
        prob_data.append({
            'Rep': rep_display,
            'Inv': m.get('invoiced', 0),
            'PF': m.get('pf_with_date', 0),
            'PA': m.get('pa_with_date', 0),
            'HS E/C': m.get('hs_expect_commit_prob', 0),
            'Total': m.get('total_core_prob', 0),
            'PF ND': m.get('pf_no_date', 0),
            'PA ND': m.get('pa_no_date', 0),
            'PA Old': m.get('pa_old', 0),
            'All Q1': m.get('all_q1_prob', 0),
            'Best': m.get('hs_best_case_prob', 0),
            'Opp': m.get('hs_opportunity_prob', 0),
            'Forecast': forecast,
            'Q2 Spill': m.get('hs_q2_spillover_prob', 0),
            'Full Pipe': m.get('full_pipeline_prob', 0),
            'Quota': quota,
            '%': pct
        })
    
    pct_total_prob = ((team_totals['total_forecast_prob'] - team_quota) / team_quota * 100) if team_quota > 0 else 0
    prob_data.append({
        'Rep': '**TOTAL**',
        'Inv': team_totals['invoiced'],
        'PF': team_totals['pf_with_date'],
        'PA': team_totals['pa_with_date'],
        'HS E/C': team_totals['hs_expect_commit_prob'],
        'Total': team_totals['total_core_prob'],
        'PF ND': team_totals['pf_no_date'],
        'PA ND': team_totals['pa_no_date'],
        'PA Old': team_totals['pa_old'],
        'All Q1': team_totals['all_q1_prob'],
        'Best': team_totals['hs_best_case_prob'],
        'Opp': team_totals['hs_opportunity_prob'],
        'Forecast': team_totals['total_forecast_prob'],
        'Q2 Spill': team_totals['hs_q2_spillover_prob'],
        'Full Pipe': team_totals['full_pipeline_prob'],
        'Quota': team_quota,
        '%': pct_total_prob
    })
    
    prob_df = pd.DataFrame(prob_data)
    
    st.dataframe(
        prob_df.style.apply(style_face_value, axis=None).format({
            **{col: '${:,.0f}' for col in currency_cols},
            '%': '{:+.0f}%'
        }),
        hide_index=True,
        use_container_width=True,
        height=320
    )
    
    # --- DEAL LISTS ---
    st.markdown("---")
    
    # Find spillover column
    spillover_col = None
    if not deals_df.empty:
        for col in deals_df.columns:
            col_lower = str(col).lower()
            if 'spillover' in col_lower or ('q2' in col_lower and '2026' in col_lower):
                spillover_col = col
                break
    
    # Best Case Deals
    if not deals_df.empty and 'Status' in deals_df.columns:
        best_case_deals = deals_df[deals_df['Status'] == 'Best Case'].copy()
        
        if spillover_col and not best_case_deals.empty:
            best_case_deals = best_case_deals[~best_case_deals[spillover_col].astype(str).str.upper().str.contains('Q2', na=False)]
        
        if not best_case_deals.empty:
            st.markdown("### 🎯 Best Case Deals")
            
            best_case_deals['Amount_Num'] = pd.to_numeric(best_case_deals['Amount'], errors='coerce').fillna(0)
            best_case_deals = best_case_deals.sort_values('Amount_Num', ascending=False)
            
            display_cols = ['Deal Name', 'Deal Owner', 'Amount']
            if 'Probability Rev' in best_case_deals.columns:
                display_cols.append('Probability Rev')
            
            available_cols = [c for c in display_cols if c in best_case_deals.columns]
            
            st.dataframe(
                best_case_deals[available_cols],
                column_config={
                    'Amount': st.column_config.NumberColumn('Amount', format='$%d'),
                    'Probability Rev': st.column_config.NumberColumn('Prob Rev', format='$%d')
                },
                hide_index=True,
                use_container_width=True
            )
            
            st.markdown(f"**Total ({len(best_case_deals)} deals): ${best_case_deals['Amount_Num'].sum():,.0f}**")
    
    # Opportunity Deals
    if not deals_df.empty and 'Status' in deals_df.columns:
        opp_deals = deals_df[deals_df['Status'] == 'Opportunity'].copy()
        
        if spillover_col and not opp_deals.empty:
            opp_deals = opp_deals[~opp_deals[spillover_col].astype(str).str.upper().str.contains('Q2', na=False)]
        
        if not opp_deals.empty:
            st.markdown("---")
            st.markdown("### 🔮 Opportunity Deals")
            
            opp_deals['Amount_Num'] = pd.to_numeric(opp_deals['Amount'], errors='coerce').fillna(0)
            opp_deals = opp_deals.sort_values('Amount_Num', ascending=False)
            
            display_cols = ['Deal Name', 'Deal Owner', 'Amount']
            if 'Probability Rev' in opp_deals.columns:
                display_cols.append('Probability Rev')
            
            available_cols = [c for c in display_cols if c in opp_deals.columns]
            
            st.dataframe(
                opp_deals[available_cols],
                column_config={
                    'Amount': st.column_config.NumberColumn('Amount', format='$%d'),
                    'Probability Rev': st.column_config.NumberColumn('Prob Rev', format='$%d')
                },
                hide_index=True,
                use_container_width=True
            )
            
            st.markdown(f"**Total ({len(opp_deals)} deals): ${opp_deals['Amount_Num'].sum():,.0f}**")
    
    # Q2 Spillover Deals
    if not deals_df.empty and spillover_col:
        q2_deals = deals_df[deals_df[spillover_col].astype(str).str.upper().str.contains('Q2', na=False)].copy()
        
        if not q2_deals.empty:
            st.markdown("---")
            st.markdown("### 📅 Q2 Spillover Pipeline")
            
            q2_deals['Amount_Num'] = pd.to_numeric(q2_deals['Amount'], errors='coerce').fillna(0)
            q2_deals = q2_deals.sort_values('Amount_Num', ascending=False)
            
            q2_display_cols = ['Deal Name', 'Deal Owner', 'Status', 'Amount']
            if 'Probability Rev' in q2_deals.columns:
                q2_display_cols.append('Probability Rev')
            
            available_cols = [c for c in q2_display_cols if c in q2_deals.columns]
            
            st.dataframe(
                q2_deals[available_cols],
                column_config={
                    'Amount': st.column_config.NumberColumn('Amount', format='$%d'),
                    'Probability Rev': st.column_config.NumberColumn('Prob Rev', format='$%d')
                },
                hide_index=True,
                use_container_width=True
            )
            
            st.markdown(f"**Total ({len(q2_deals)} deals): ${q2_deals['Amount_Num'].sum():,.0f}**")
    
    # --- FOOTER ---
    st.markdown("---")
    st.caption(f"Calyx Containers • Revenue Operations • Generated {get_mst_time().strftime('%I:%M %p %Z')}")


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
            ["👥 Team Overview", "👤 Individual Rep", "📊 CRO Scorecard"],
            label_visibility="collapsed",
            key="nav_selector"
        )
        
        # Map display names back to internal names
        view_mapping = {
            "👥 Team Overview": "Team Overview",
            "👤 Individual Rep": "Individual Rep",
            "📊 CRO Scorecard": "CRO Scorecard"
        }
        
        view_mode = view_mapping.get(view_mode, "Team Overview")
        
        st.markdown("---")
        
        # NEW: Include Shipping Toggle
        # This controls whether revenue amounts include shipping & tax or just product revenue
        include_shipping = st.toggle(
            "💰 Include Shipping & Tax",
            value=True,
            key="include_shipping_toggle",
            help="When ON: Shows total transaction amount (includes shipping & tax). When OFF: Shows product revenue only (excludes shipping & tax)."
        )
        
        # Store in session state for use in display functions
        st.session_state.include_shipping = include_shipping
        
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
    
    # DEBUG: Show shipping toggle column detection (for Xander)
    with st.sidebar.expander("🔧 Shipping Toggle Debug", expanded=False):
        include_shipping = st.session_state.get('include_shipping', True)
        st.write(f"**Toggle State:** {'Include Shipping' if include_shipping else 'Exclude Shipping'}")
        
        st.markdown("**Invoices Columns:**")
        if not invoices_df.empty:
            has_shipping = 'Amount_Shipping' in invoices_df.columns
            has_tax = 'Amount_Tax' in invoices_df.columns
            has_net = 'Net_Amount' in invoices_df.columns
            st.write(f"- Amount_Shipping: {'✅' if has_shipping else '❌'}")
            st.write(f"- Amount_Tax: {'✅' if has_tax else '❌'}")
            st.write(f"- Net_Amount: {'✅' if has_net else '❌'}")
            if has_net:
                st.write(f"- Sample Net_Amount: ${invoices_df['Net_Amount'].head(3).tolist()}")
        
        st.markdown("**Sales Orders Columns:**")
        if not sales_orders_df.empty:
            has_shipping = 'Amount_Shipping' in sales_orders_df.columns
            has_tax = 'Amount_Tax' in sales_orders_df.columns
            has_net = 'Net_Amount' in sales_orders_df.columns
            st.write(f"- Amount_Shipping: {'✅' if has_shipping else '❌'}")
            st.write(f"- Amount_Tax: {'✅' if has_tax else '❌'}")
            st.write(f"- Net_Amount: {'✅' if has_net else '❌'}")
            if has_net:
                st.write(f"- Sample Net_Amount: ${sales_orders_df['Net_Amount'].head(3).tolist()}")
            # Show all column names for debugging
            st.write(f"**All SO Columns:** {sales_orders_df.columns.tolist()}")
    
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
    elif view_mode == "CRO Scorecard":
        display_cro_scorecard(deals_df, dashboard_df, invoices_df, sales_orders_df)

if __name__ == "__main__":
    main()

# Wrapper function for importing into app.py
def render_q1_revenue_snapshot(view_mode=None):
    """Entry point when imported as a module by app.py"""
    main()
