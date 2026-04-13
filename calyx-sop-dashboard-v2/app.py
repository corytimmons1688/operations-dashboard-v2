"""
Calyx Containers S&OP Dashboard
================================
Unified Sales & Operations Planning and Quality Management System

Sections:
- S&OP: Sales Rep View, Operations View, Scenario Planning, PO Forecast, Deliveries
- Quality: NC Dashboard (Status, Aging, Cost, Customer, Pareto Analysis)
- Revenue Snapshots: Q4, Q1, QBR Generator
- Revenue Operations Playground: QBR Generator & Ad-hoc Analysis

Author: Xander @ Calyx Containers
Version: 4.1.0 - Dark Mode Edition
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import logging

# =============================================================================
# PAGE CONFIGURATION - Must be first Streamlit command
# =============================================================================
st.set_page_config(
    page_title="Calyx Command Center",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# IMPORTS - After page config
# =============================================================================
try:
    from src.sales_rep_view import render_sales_rep_view
    from src.operations_view import render_operations_view
    from src.scenario_planning import render_scenario_planning
    from src.po_forecast import render_po_forecast
    from src.deliveries_tracking import render_deliveries_tracking
    from src.quality_section import render_quality_section
    from src.data_loader import load_nc_data
    from src.utils import setup_logging
    MODULES_LOADED = True
except ImportError as e:
    MODULES_LOADED = False
    IMPORT_ERROR = str(e)

# =============================================================================
# REVENUE MODULE IMPORTS
# =============================================================================
Q4_IMPORT_ERROR = None
try:
    from src.q4_revenue_snapshot import render_q4_revenue_snapshot
    Q4_MODULE_LOADED = True
except ImportError as e:
    Q4_MODULE_LOADED = False
    Q4_IMPORT_ERROR = str(e)

Q1_IMPORT_ERROR = None
try:
    from src.q1_revenue_snapshot import render_q1_revenue_snapshot
    Q1_MODULE_LOADED = True
except ImportError as e:
    Q1_MODULE_LOADED = False
    Q1_IMPORT_ERROR = str(e)

Q2_IMPORT_ERROR = None
try:
    from src.q2_revenue_snapshot import render_q2_revenue_snapshot
    Q2_MODULE_LOADED = True
except ImportError as e:
    Q2_MODULE_LOADED = False
    Q2_IMPORT_ERROR = str(e)

YEARLY_IMPORT_ERROR = None
try:
    from src.yearly_planning_2026 import render_yearly_planning_2026
    YEARLY_MODULE_LOADED = True
except ImportError as e:
    YEARLY_MODULE_LOADED = False
    YEARLY_IMPORT_ERROR = str(e)

# =============================================================================
# REVENUE OPERATIONS PLAYGROUND MODULE IMPORT
# =============================================================================
REV_OPS_IMPORT_ERROR = None
try:
    from src.Rev_Ops_Playground import render_yearly_planning_2026 as render_rev_ops_playground
    REV_OPS_MODULE_LOADED = True
except ImportError as e:
    REV_OPS_MODULE_LOADED = False
    REV_OPS_IMPORT_ERROR = str(e)

# Configure logging
try:
    setup_logging()
except:
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_mst_time():
    """Get current time in Mountain Standard Time"""
    return datetime.now(ZoneInfo("America/Denver"))

# =============================================================================
# CUSTOM CSS - DRAMATIC DARK MODE UI (Matching Q1 Revenue Snapshot)
# =============================================================================
def inject_custom_css():
    """Inject custom CSS — clean light theme matching Streamlit config."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* === BASE === */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* === TYPOGRAPHY === */
    h1 { font-size: 1.75rem !important; font-weight: 800 !important; color: #0f172a !important; letter-spacing: -0.5px !important; }
    h2 { font-size: 1.35rem !important; font-weight: 700 !important; color: #1e293b !important; }
    h3 { font-size: 1.1rem !important; font-weight: 600 !important; color: #1e293b !important; }
    h4 { font-size: 0.95rem !important; font-weight: 600 !important; color: #334155 !important; }

    /* === SIDEBAR — dark navy SaaS style === */
    [data-testid="stSidebar"] {
        background: #0f1b2d !important;
        border-right: 1px solid rgba(255,255,255,0.06) !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        background: transparent !important;
        padding-top: 0 !important;
    }
    [data-testid="stSidebar"] * { color: #cbd5e1 !important; }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: #f1f5f9 !important; }

    /* Sidebar radio items — clean nav */
    [data-testid="stSidebar"] .stRadio > div { gap: 2px !important; }
    [data-testid="stSidebar"] .stRadio > div > label {
        background: transparent !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        margin: 0 !important;
        cursor: pointer !important;
        border-left: 3px solid transparent !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stSidebar"] .stRadio > div > label:hover {
        background: rgba(129,140,248,0.08) !important;
        border-left-color: rgba(129,140,248,0.4) !important;
    }
    [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {
        background: rgba(99,102,241,0.15) !important;
        border-left-color: #818cf8 !important;
    }
    [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] p {
        color: #c7d2fe !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] .stRadio > div > label p {
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        color: #94a3b8 !important;
        margin: 0 !important;
    }
    /* Sidebar buttons (refresh) — dark-friendly */
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,0.04) !important;
        color: #cbd5e1 !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(129,140,248,0.15) !important;
        border-color: rgba(129,140,248,0.3) !important;
    }
    /* Sidebar divider */
    [data-testid="stSidebar"] hr {
        background: rgba(255,255,255,0.06) !important;
    }

    /* === METRIC CARDS === */
    [data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid #e0e4ea !important;
        border-radius: 12px !important;
        padding: 1.25rem !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
    }
    [data-testid="stMetric"]:hover {
        border-color: #c7d2fe !important;
        box-shadow: 0 2px 8px rgba(79,70,229,0.08) !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.7rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        color: #64748b !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        color: #0f172a !important;
    }

    /* === BUTTONS === */
    .stButton > button {
        background: #4f46e5 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        box-shadow: 0 1px 3px rgba(79,70,229,0.2) !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover {
        background: #4338ca !important;
        box-shadow: 0 2px 8px rgba(79,70,229,0.3) !important;
    }

    /* === TABS === */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        border-bottom: 1px solid #e2e8f0 !important;
        border-radius: 0 !important;
        padding: 0 !important;
        gap: 0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 0 !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        color: #94a3b8 !important;
        border-bottom: 2px solid transparent !important;
        background: transparent !important;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #475569 !important; }
    .stTabs [aria-selected="true"] {
        color: #4f46e5 !important;
        font-weight: 600 !important;
        border-bottom-color: #4f46e5 !important;
        background: transparent !important;
    }

    /* === DATA TABLES === */
    .stDataFrame {
        border-radius: 10px !important;
        border: 1px solid #e2e8f0 !important;
        overflow: hidden !important;
    }

    /* === FORM SUBMIT === */
    .stFormSubmitButton > button {
        background: #4f46e5 !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 600 !important;
    }

    /* === SELECT / INPUT === */
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    .stTextInput > div > div {
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
    }

    /* === DIVIDER === */
    hr {
        border: none !important;
        height: 1px !important;
        background: #e2e8f0 !important;
        margin: 1.5rem 0 !important;
    }

    /* === EXPANDER === */
    .streamlit-expanderHeader {
        background: #f0f2f6 !important;
        border-radius: 8px !important;
        border: 1px solid #e2e8f0 !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
    }

    /* === ALERTS === */
    .stAlert {
        border-radius: 8px !important;
    }

    /* === SCROLLBAR === */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# SIDEBAR NAVIGATION
# =============================================================================
def render_sidebar():
    """Render a clean SaaS-grade sidebar — button-based navigation."""

    # Initialize active section (single source of truth)
    if "active_section" not in st.session_state:
        st.session_state.active_section = "📈 Q2 Revenue Snapshot"
    if "q2_view" not in st.session_state:
        st.session_state.q2_view = "Team Overview"

    # Inject nav button styles — scoped to sidebar only
    st.markdown("""
    <style>
    /* Nav buttons — full-width rectangular cards */
    [data-testid="stSidebar"] .nav-btn .stButton > button {
        width: 100% !important;
        text-align: left !important;
        justify-content: flex-start !important;
        background: transparent !important;
        color: #94a3b8 !important;
        border: 1px solid transparent !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        box-shadow: none !important;
        margin: 2px 0 !important;
    }
    [data-testid="stSidebar"] .nav-btn .stButton > button:hover {
        background: rgba(255,255,255,0.04) !important;
        border-color: rgba(255,255,255,0.06) !important;
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] .nav-btn-active .stButton > button {
        background: rgba(99,102,241,0.18) !important;
        border: 1px solid rgba(129,140,248,0.35) !important;
        color: #e0e7ff !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 8px rgba(99,102,241,0.15) !important;
    }
    [data-testid="stSidebar"] .nav-btn-active .stButton > button:hover {
        background: rgba(99,102,241,0.25) !important;
    }
    /* Sub-nav — indented with left border */
    [data-testid="stSidebar"] .nav-sub .stButton > button {
        margin-left: 16px !important;
        width: calc(100% - 16px) !important;
        border-left: 2px solid rgba(129,140,248,0.25) !important;
        border-radius: 0 6px 6px 0 !important;
        padding-left: 14px !important;
        font-size: 0.82rem !important;
    }
    [data-testid="stSidebar"] .nav-sub-active .stButton > button {
        background: rgba(99,102,241,0.18) !important;
        border-left-color: #818cf8 !important;
        color: #e0e7ff !important;
        font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    def nav_button(label, section_key, css_class="nav-btn"):
        """Render a nav button. Returns True if clicked."""
        active = (st.session_state.active_section == section_key)
        wrapper = f"{css_class}-active" if active else css_class
        st.markdown(f'<div class="{wrapper}">', unsafe_allow_html=True)
        clicked = st.button(label, key=f"navbtn_{section_key}", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        if clicked:
            st.session_state.active_section = section_key
            st.rerun()
        return active

    def sub_button(label, view_key):
        """Render a sub-nav button (Q2 views). Returns True if clicked."""
        active = (st.session_state.q2_view == view_key)
        wrapper = "nav-sub-active" if active else "nav-sub"
        st.markdown(f'<div class="{wrapper}">', unsafe_allow_html=True)
        clicked = st.button(label, key=f"subbtn_{view_key}", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        if clicked:
            st.session_state.q2_view = view_key
            st.session_state.active_section = "📈 Q2 Revenue Snapshot"
            st.rerun()

    def section_label(text, color):
        st.markdown(f"""
        <p style="
            color: {color};
            font-size: 0.62rem;
            font-weight: 700;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin: 18px 0 4px 14px;
            padding: 0;
        ">{text}</p>
        """, unsafe_allow_html=True)

    with st.sidebar:
        # Brand header
        st.markdown("""
        <div style="
            padding: 20px 16px 20px 16px;
            margin-bottom: 8px;
            border-bottom: 1px solid rgba(255,255,255,0.06);
        ">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="
                    width: 44px; height: 44px;
                    background: linear-gradient(135deg, #3b82f6, #06b6d4);
                    border-radius: 10px;
                    display: flex; align-items: center; justify-content: center;
                    font-size: 22px;
                    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
                ">📦</div>
                <div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #f1f5f9; letter-spacing: -0.3px; line-height: 1.2;">Calyx Containers</div>
                    <div style="font-size: 0.62rem; font-weight: 600; color: #64748b; letter-spacing: 1.2px; text-transform: uppercase; margin-top: 2px;">calyxcontainers.com</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # REVENUE
        section_label("Revenue", "#3b82f6")
        q2_active = nav_button("📈  Q2 2026 Forecast", "📈 Q2 Revenue Snapshot")

        # Q2 sub-nav — only shown when Q2 is active
        if q2_active:
            sub_button("👥 Team Overview", "Team Overview")
            sub_button("👤 Individual Rep", "Individual Rep")
            sub_button("📊 CRO Scorecard", "CRO Scorecard")

        # PAST QUARTERS
        section_label("Past Quarters", "#06b6d4")
        nav_button("📊  Q1 2026", "🎯 Q1 2026 Review")
        nav_button("📉  Q4 2025", "📉 Q4 Revenue Snapshot")

        # PLANNING
        section_label("Planning", "#a78bfa")
        nav_button("📋  S&OP Planning", "📊 S&OP Planning")
        nav_button("📄  QBR Generator", "📄 QBR Generator")

        # OPERATIONS
        section_label("Operations", "#10b981")
        nav_button("🛡️  Quality Management", "🛡️ Quality Management")
        nav_button("🎮  Rev Ops Playground", "🎮 Revenue Operations Playground")

        # Spacer
        st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)

        # MST time card
        current_time = get_mst_time()
        st.markdown(f"""
        <div style="
            padding: 12px 16px;
            margin: 0 8px;
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.06);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.65rem; color: #64748b; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">MST</span>
                <span style="font-size: 0.8rem; color: #e0e7ff; font-weight: 600;">{current_time.strftime('%I:%M %p')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="height: 8px;"></div>', unsafe_allow_html=True)

        # Refresh
        if st.button("↻  Refresh Data", use_container_width=True, key="refresh_btn"):
            st.cache_data.clear()
            st.rerun()

        # Footer
        st.markdown("""
        <div style="
            text-align: center;
            padding: 16px 0 8px 0;
            margin-top: 12px;
            border-top: 1px solid rgba(255,255,255,0.06);
        ">
            <p style="font-size: 0.6rem; color: #475569; margin: 0;">v4.2 · Built by Xander</p>
        </div>
        """, unsafe_allow_html=True)

    # Sync q2_view with the legacy key used by q2_revenue_snapshot module
    st.session_state["q2_app_view_selector"] = st.session_state.q2_view

    return st.session_state.active_section


# =============================================================================
# S&OP PLANNING SECTION
# =============================================================================
def render_sop_section():
    """Render the S&OP Planning section with all sub-tabs."""
    st.markdown("""
    <div style='text-align: center; padding: 15px; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); 
                 color: white; border-radius: 16px; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(59, 130, 246, 0.3);'>
        <h2 style='margin: 0; color: white !important;'>📈 Sales & Operations Planning</h2>
        <p style='font-size: 0.9rem; margin: 8px 0 0 0; opacity: 0.9; color: white !important;'>Demand Forecasting • Scenario Planning • Supply Chain Visibility</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👤 Sales Rep View",
        "📦 Operations",
        "🎯 Scenarios",
        "📋 PO Forecast",
        "🚚 Deliveries"
    ])
    
    with tab1:
        render_sales_rep_tab()
    with tab2:
        render_operations_tab()
    with tab3:
        render_scenarios_tab()
    with tab4:
        render_po_forecast_tab()
    with tab5:
        render_deliveries_tab()


def render_sales_rep_tab():
    """Render Sales Rep View tab."""
    if MODULES_LOADED:
        try:
            render_sales_rep_view()
        except Exception as e:
            st.error(f"Error loading Sales Rep View: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.warning(f"Module not loaded: {IMPORT_ERROR}")


def render_operations_tab():
    """Render Operations View tab."""
    if MODULES_LOADED:
        try:
            render_operations_view()
        except Exception as e:
            st.error(f"Error loading Operations View: {str(e)}")
    else:
        st.warning(f"Module not loaded: {IMPORT_ERROR}")


def render_scenarios_tab():
    """Render Scenario Planning tab."""
    if MODULES_LOADED:
        try:
            render_scenario_planning()
        except Exception as e:
            st.error(f"Error loading Scenario Planning: {str(e)}")
    else:
        st.warning(f"Module not loaded: {IMPORT_ERROR}")


def render_po_forecast_tab():
    """Render PO Forecast tab."""
    if MODULES_LOADED:
        try:
            render_po_forecast()
        except Exception as e:
            st.error(f"Error loading PO Forecast: {str(e)}")
    else:
        st.warning(f"Module not loaded: {IMPORT_ERROR}")


def render_deliveries_tab():
    """Render Deliveries Tracking tab."""
    if MODULES_LOADED:
        try:
            render_deliveries_tracking()
        except Exception as e:
            st.error(f"Error loading Deliveries: {str(e)}")
    else:
        st.warning(f"Module not loaded: {IMPORT_ERROR}")


# =============================================================================
# QUALITY MANAGEMENT SECTION
# =============================================================================
def render_quality_section_wrapper():
    """Render the Quality Management section."""
    st.markdown("""
    <div style='text-align: center; padding: 15px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                 color: white; border-radius: 16px; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(16, 185, 129, 0.3);'>
        <h2 style='margin: 0; color: white !important;'>🛡️ Quality Management</h2>
        <p style='font-size: 0.9rem; margin: 8px 0 0 0; opacity: 0.9; color: white !important;'>NC Tracking • Aging Analysis • Cost & Customer Impact</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Status Tracker",
        "⏱️ Aging Analysis",
        "💰 Cost Analysis",
        "👥 Customer Impact",
        "📊 Pareto Analysis"
    ])
    
    with tab1:
        render_quality_status_tab()
    with tab2:
        render_quality_aging_tab()
    with tab3:
        render_quality_cost_tab()
    with tab4:
        render_quality_customer_tab()
    with tab5:
        render_quality_pareto_tab()


def render_quality_status_tab():
    """Render Quality Status Tracker tab."""
    if MODULES_LOADED:
        try:
            render_quality_section()
        except Exception as e:
            st.error(f"Error loading Quality Status: {str(e)}")
    else:
        st.warning(f"Module not loaded: {IMPORT_ERROR}")


def render_quality_aging_tab():
    """Render Quality Aging Analysis tab."""
    if MODULES_LOADED:
        try:
            from src.aging_analysis import render_aging_dashboard
            render_aging_dashboard()
        except Exception as e:
            st.error(f"Error loading Aging Analysis: {str(e)}")
    else:
        st.warning(f"Module not loaded: {IMPORT_ERROR}")


def render_quality_cost_tab():
    """Render Quality Cost Analysis tab."""
    if MODULES_LOADED:
        try:
            from src.cost_analysis import render_cost_of_rework, render_cost_avoided
            render_cost_of_rework()
            render_cost_avoided()
        except Exception as e:
            st.error(f"Error loading Cost Analysis: {str(e)}")
    else:
        st.warning(f"Module not loaded: {IMPORT_ERROR}")


def render_quality_customer_tab():
    """Render Quality Customer Impact tab."""
    if MODULES_LOADED:
        try:
            from src.customer_analysis import render_customer_analysis
            render_customer_analysis()
        except Exception as e:
            st.error(f"Error loading Customer Impact: {str(e)}")
    else:
        st.warning(f"Module not loaded: {IMPORT_ERROR}")


def render_quality_pareto_tab():
    """Render Quality Pareto Analysis tab."""
    if MODULES_LOADED:
        try:
            from src.pareto_chart import render_issue_type_pareto
            render_issue_type_pareto()
        except Exception as e:
            st.error(f"Error loading Pareto Analysis: {str(e)}")
    else:
        st.warning(f"Module not loaded: {IMPORT_ERROR}")


# =============================================================================
# REVENUE SNAPSHOT SECTIONS
# =============================================================================
def render_q4_revenue_section():
    """Render Q4 Revenue Snapshot section."""
    if Q4_MODULE_LOADED:
        try:
            render_q4_revenue_snapshot()
        except Exception as e:
            st.error(f"Error loading Q4 Revenue Snapshot: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.markdown("""
        <div style='text-align: center; padding: 15px; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); 
                     color: white; border-radius: 16px; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(245, 158, 11, 0.3);'>
            <h2 style='margin: 0; color: white !important;'>📊 Q4 Revenue Snapshot</h2>
            <p style='font-size: 0.9rem; margin: 8px 0 0 0; opacity: 0.9; color: white !important;'>Q4 2025 Performance Analysis</p>
        </div>
        """, unsafe_allow_html=True)
        st.error(f"❌ Q4 Revenue Snapshot module failed to load: {Q4_IMPORT_ERROR}")


def render_q1_revenue_section():
    """Render Q1 2026 Review (historical snapshot)."""
    if Q1_MODULE_LOADED:
        try:
            render_q1_revenue_snapshot()
        except Exception as e:
            st.error(f"Error loading Q1 2026 Review: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.markdown("""
        <div style='text-align: center; padding: 15px; background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
                     color: white; border-radius: 16px; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(139, 92, 246, 0.3);'>
            <h2 style='margin: 0; color: white !important;'>🎯 Q1 2026 Review</h2>
            <p style='font-size: 0.9rem; margin: 8px 0 0 0; opacity: 0.9; color: white !important;'>Q1 2026 Historical Performance • $3.92M</p>
        </div>
        """, unsafe_allow_html=True)
        st.info("📌 **Q1 2026 Review module not yet loaded.**")
        st.markdown(f"Import Error: `{Q1_IMPORT_ERROR}`")


def render_q2_revenue_section():
    """Render Q2 Revenue Snapshot & Planning section."""
    if Q2_MODULE_LOADED:
        try:
            render_q2_revenue_snapshot()
        except Exception as e:
            st.error(f"Error loading Q2 Revenue Snapshot: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.markdown("""
        <div style='text-align: center; padding: 15px; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                     color: white; border-radius: 16px; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(59, 130, 246, 0.3);'>
            <h2 style='margin: 0; color: white !important;'>📈 Q2 Revenue Snapshot</h2>
            <p style='font-size: 0.9rem; margin: 8px 0 0 0; opacity: 0.9; color: white !important;'>Q2 2026 Planning & Forecasting</p>
        </div>
        """, unsafe_allow_html=True)
        st.info("📌 **Q2 Revenue Snapshot module not yet loaded.**")
        st.markdown(f"Import Error: `{Q2_IMPORT_ERROR}`")


def render_2026_yearly_planning_section():
    """Render QBR Generator section."""
    if YEARLY_MODULE_LOADED:
        try:
            render_yearly_planning_2026()
        except Exception as e:
            st.error(f"Error loading QBR Generator: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.markdown("""
        <div style='text-align: center; padding: 15px; background: linear-gradient(135deg, #ec4899 0%, #db2777 100%); 
                     color: white; border-radius: 16px; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(236, 72, 153, 0.3);'>
            <h2 style='margin: 0; color: white !important;'>📄 QBR Generator</h2>
            <p style='font-size: 0.9rem; margin: 8px 0 0 0; opacity: 0.9; color: white !important;'>Annual Strategic Planning & Capacity</p>
        </div>
        """, unsafe_allow_html=True)
        st.info("📌 **QBR Generator module not yet loaded.**")


# =============================================================================
# REVENUE OPERATIONS PLAYGROUND SECTION
# =============================================================================
def render_rev_ops_playground_section():
    """Render Revenue Operations Playground section."""
    if REV_OPS_MODULE_LOADED:
        try:
            render_rev_ops_playground()
        except Exception as e:
            st.error(f"Error loading Revenue Operations Playground: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.markdown("""
        <div style='text-align: center; padding: 15px; background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%); 
                     color: white; border-radius: 16px; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(6, 182, 212, 0.3);'>
            <h2 style='margin: 0; color: white !important;'>🎮 Revenue Operations Playground</h2>
            <p style='font-size: 0.9rem; margin: 8px 0 0 0; opacity: 0.9; color: white !important;'>QBR Generator • Ad-hoc Analysis • Customer Deep Dives</p>
        </div>
        """, unsafe_allow_html=True)
        st.info("📌 **Revenue Operations Playground module not yet loaded.**")
        if REV_OPS_IMPORT_ERROR:
            st.markdown(f"Import Error: `{REV_OPS_IMPORT_ERROR}`")
        st.markdown("""
        **To enable this section:**
        1. Save `Rev_Ops_Playground.py` to `src/Rev_Ops_Playground.py`
        2. Ensure all dependencies are installed
        3. Refresh the application
        """)


# =============================================================================
# MAIN APPLICATION
# =============================================================================
def main():
    """Main application entry point."""
    inject_custom_css()
    section = render_sidebar()

    # Detect section change — force a clean rerun when switching sections
    # This prevents DOM bleed between different dashboard views
    prev = st.session_state.get("_last_rendered_section")
    if prev != section:
        st.session_state["_last_rendered_section"] = section
        # On section change, clear any persistent DOM elements from prior view
        st.markdown("""
        <script>
        (function() {
            const doc = window.parent.document;
            // Remove any known fixed/sticky elements from other pages
            doc.querySelectorAll('#q2-sticky-forecast-bar').forEach(el => el.remove());
        })();
        </script>
        """, unsafe_allow_html=True)

    # Belt-and-suspenders: always hide the Q2 sticky bar when not on Q2
    if section != "📈 Q2 Revenue Snapshot":
        st.markdown("""
        <style>
        #q2-sticky-forecast-bar { display: none !important; }
        </style>
        """, unsafe_allow_html=True)

    # Route into a single container so content clears cleanly between views
    content_container = st.container()
    with content_container:
        if section == "📈 Q2 Revenue Snapshot":
            render_q2_revenue_section()
        elif section == "🎯 Q1 2026 Review":
            render_q1_revenue_section()
        elif section == "📊 S&OP Planning":
            render_sop_section()
        elif section == "🛡️ Quality Management":
            render_quality_section_wrapper()
        elif section == "📉 Q4 Revenue Snapshot":
            render_q4_revenue_section()
        elif section == "📄 QBR Generator":
            render_2026_yearly_planning_section()
        elif section == "🎮 Revenue Operations Playground":
            render_rev_ops_playground_section()


if __name__ == "__main__":
    main()
