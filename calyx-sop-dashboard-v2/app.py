"""
Calyx Containers S&OP Dashboard
================================
Unified Sales & Operations Planning and Quality Management System

Sections:
- S&OP: Sales Rep View, Operations View, Scenario Planning, PO Forecast, Deliveries
- Quality: NC Dashboard (Status, Aging, Cost, Customer, Pareto Analysis)
- Revenue Snapshots: Q4, Q1, 2026 Yearly Planning
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
    """Inject custom CSS — bright futuristic theme with high contrast."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* === BASE — bright dark with blue-black tones === */
    .stApp {
        background: #0f1729 !important;
        color: #e8edf5 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* === TYPOGRAPHY — bright and readable === */
    h1 {
        font-size: 1.75rem !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        letter-spacing: -0.5px !important;
    }
    h2 { font-size: 1.35rem !important; font-weight: 700 !important; color: #f0f4ff !important; }
    h3 { font-size: 1.1rem !important; font-weight: 600 !important; color: #e0e7ff !important; }
    h4 { font-size: 0.95rem !important; font-weight: 600 !important; color: #c7d2fe !important; }
    p, span, label, div { color: #c9d1e0 !important; }

    /* === SIDEBAR — slightly lighter panel === */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0c1221 0%, #111a2e 100%) !important;
        border-right: 1px solid rgba(129, 140, 248, 0.15) !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        background: transparent !important;
        padding-top: 0 !important;
    }

    /* Sidebar radio — bright accent on active */
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
        background: rgba(129, 140, 248, 0.08) !important;
        border-left-color: rgba(129, 140, 248, 0.4) !important;
    }
    [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {
        background: rgba(129, 140, 248, 0.15) !important;
        border-left-color: #a5b4fc !important;
    }
    [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] p {
        color: #e0e7ff !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] .stRadio > div > label p {
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        color: #8b95b0 !important;
        margin: 0 !important;
    }

    /* === METRIC CARDS — glass with bright values === */
    [data-testid="stMetric"] {
        background: rgba(17, 25, 50, 0.7) !important;
        border: 1px solid rgba(129, 140, 248, 0.15) !important;
        border-radius: 12px !important;
        padding: 1.25rem !important;
        backdrop-filter: blur(10px) !important;
    }
    [data-testid="stMetric"]:hover {
        border-color: rgba(129, 140, 248, 0.3) !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.7rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        color: #8b95b0 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        background: none !important;
    }
    [data-testid="stMetricDelta"] {
        color: #a5b4fc !important;
    }

    /* === BUTTONS — vivid indigo === */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #818cf8 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.25) !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover {
        box-shadow: 0 4px 16px rgba(99, 102, 241, 0.4) !important;
        filter: brightness(1.1) !important;
    }

    /* === TABS — bright underline === */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        border-bottom: 1px solid rgba(129, 140, 248, 0.12) !important;
        border-radius: 0 !important;
        padding: 0 !important;
        gap: 0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 0 !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        color: #7b85a0 !important;
        border-bottom: 2px solid transparent !important;
        background: transparent !important;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #c7d2fe !important; }
    .stTabs [aria-selected="true"] {
        color: #e0e7ff !important;
        font-weight: 600 !important;
        border-bottom-color: #818cf8 !important;
        background: transparent !important;
    }

    /* === DATA TABLES — readable with bright headers === */
    .stDataFrame {
        border-radius: 10px !important;
        border: 1px solid rgba(129, 140, 248, 0.12) !important;
        overflow: hidden !important;
    }

    /* === CHECKBOXES — ensure bright labels === */
    .stCheckbox label span { color: #d0d7e5 !important; }
    .stCheckbox label p { color: #d0d7e5 !important; }

    /* === TOGGLE === */
    .stToggle label span { color: #c9d1e0 !important; }

    /* === SELECT / INPUT — readable inputs === */
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    .stTextInput > div > div {
        background: rgba(17, 25, 50, 0.6) !important;
        border: 1px solid rgba(129, 140, 248, 0.15) !important;
        border-radius: 8px !important;
        color: #e0e7ff !important;
    }

    /* === DROPDOWN MENU — dark background with readable text === */
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [data-baseweb="select"] ul,
    [role="listbox"] {
        background: #1a2240 !important;
        border: 1px solid rgba(129, 140, 248, 0.2) !important;
    }
    [data-baseweb="menu"] li,
    [role="option"],
    [data-baseweb="select"] ul li {
        background: #1a2240 !important;
        color: #e0e7ff !important;
    }
    [data-baseweb="menu"] li:hover,
    [role="option"]:hover {
        background: rgba(129, 140, 248, 0.15) !important;
        color: #ffffff !important;
    }
    [aria-selected="true"][role="option"] {
        background: rgba(129, 140, 248, 0.25) !important;
        color: #ffffff !important;
    }

    /* === DIVIDER === */
    hr {
        border: none !important;
        height: 1px !important;
        background: rgba(129, 140, 248, 0.1) !important;
        margin: 1.5rem 0 !important;
    }

    /* === EXPANDER — visible text === */
    .streamlit-expanderHeader {
        background: rgba(17, 25, 50, 0.5) !important;
        border-radius: 8px !important;
        border: 1px solid rgba(129, 140, 248, 0.12) !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        color: #c7d2fe !important;
    }
    .streamlit-expanderContent {
        border: 1px solid rgba(129, 140, 248, 0.08) !important;
        border-top: none !important;
    }

    /* === ALERTS === */
    .stAlert {
        background: rgba(17, 25, 50, 0.6) !important;
        border-radius: 8px !important;
        border-left: 3px solid #818cf8 !important;
    }

    /* === FORM SUBMIT BUTTON — bright and clear === */
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #818cf8 100%) !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3) !important;
    }

    /* === SCROLLBAR === */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(129, 140, 248, 0.2); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(129, 140, 248, 0.4); }

    /* === PLOTLY === */
    .js-plotly-plot .plotly .bg { fill: transparent !important; }

    /* === CAPTIONS — visible === */
    .stCaption, [data-testid="stCaptionContainer"] { color: #8b95b0 !important; }

    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# SIDEBAR NAVIGATION
# =============================================================================
def render_sidebar():
    """Render a clean SaaS-grade sidebar."""
    with st.sidebar:
        # Brand header
        st.markdown("""
        <div style="
            padding: 24px 16px 20px 16px;
            margin-bottom: 8px;
        ">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="
                    width: 38px; height: 38px;
                    background: linear-gradient(135deg, #818cf8, #a78bfa);
                    border-radius: 10px;
                    display: flex; align-items: center; justify-content: center;
                    font-size: 18px;
                    box-shadow: 0 4px 16px rgba(129, 140, 248, 0.35);
                ">🚀</div>
                <div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #ffffff; letter-spacing: -0.3px; line-height: 1.2;">Calyx</div>
                    <div style="font-size: 0.65rem; font-weight: 500; color: #8b95b0; letter-spacing: 0.5px;">Command Center</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Nav section label
        st.markdown("""
        <p style="
            color: #7b85a0;
            font-size: 0.6rem;
            font-weight: 600;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin: 0 0 6px 16px;
            padding: 0;
        ">Revenue</p>
        """, unsafe_allow_html=True)

        # Navigation — current quarter
        section = st.radio(
            "Navigation",
            options=["Q2 2026 Forecast"],
            label_visibility="collapsed",
            key="main_nav",
            format_func=lambda x: "📈  Q2 2026 Forecast"
        )

        # Q2 sub-navigation — indented via CSS targeting the specific radio key
        if section == "Q2 2026 Forecast":
            st.markdown("""
            <style>
            /* Indent the Q2 sub-nav radio group */
            [data-testid="stSidebar"] [data-testid="element-container"]:has([data-testid="stRadio"] [key="q2_app_view_selector"]),
            [data-testid="stSidebar"] div:has(> [data-testid="stRadio"] div[data-baseweb="radio"] + div[data-baseweb="radio"] + div[data-baseweb="radio"]) {
                margin-left: 18px !important;
                padding-left: 12px !important;
                border-left: 2px solid rgba(129,140,248,0.2) !important;
                margin-top: -8px !important;
                margin-bottom: 4px !important;
            }
            </style>
            """, unsafe_allow_html=True)
            q2_view = st.radio(
                "Q2 View",
                options=["Team Overview", "Individual Rep", "CRO Scorecard"],
                label_visibility="collapsed",
                key="q2_app_view_selector",
                format_func=lambda x: {
                    "Team Overview": "👥 Team Overview",
                    "Individual Rep": "👤 Individual Rep",
                    "CRO Scorecard": "📊 CRO Scorecard",
                }.get(x, x)
            )

        # Past quarters section
        st.markdown("""
        <p style="
            color: #7b85a0;
            font-size: 0.6rem;
            font-weight: 600;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin: 16px 0 6px 16px;
            padding: 0;
        ">Past Quarters</p>
        """, unsafe_allow_html=True)

        section_hist = st.radio(
            "History",
            options=["Q1 2026 Review", "Q4 2025 Review"],
            label_visibility="collapsed",
            key="main_nav_history",
            format_func=lambda x: {
                "Q1 2026 Review": "📊  Q1 2026",
                "Q4 2025 Review": "📉  Q4 2025",
            }.get(x, x)
        )

        # Planning section
        st.markdown("""
        <p style="
            color: #7b85a0;
            font-size: 0.6rem;
            font-weight: 600;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin: 16px 0 6px 16px;
            padding: 0;
        ">Planning</p>
        """, unsafe_allow_html=True)

        section2 = st.radio(
            "Planning",
            options=[
                "S&OP Planning",
                "2026 Yearly Planning",
            ],
            label_visibility="collapsed",
            key="main_nav_planning",
            format_func=lambda x: {
                "S&OP Planning":       "📋  S&OP Planning",
                "2026 Yearly Planning": "📅  2026 Yearly Plan",
            }.get(x, x)
        )

        # Operations section
        st.markdown("""
        <p style="
            color: #7b85a0;
            font-size: 0.6rem;
            font-weight: 600;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin: 16px 0 6px 16px;
            padding: 0;
        ">Operations</p>
        """, unsafe_allow_html=True)

        section3 = st.radio(
            "Operations",
            options=[
                "Quality Management",
                "Rev Ops Playground",
            ],
            label_visibility="collapsed",
            key="main_nav_ops",
            format_func=lambda x: {
                "Quality Management": "🛡️  Quality Management",
                "Rev Ops Playground": "🎮  Rev Ops Playground",
            }.get(x, x)
        )

        st.markdown("""<div style="height: 16px;"></div>""", unsafe_allow_html=True)

        # Quick info cards — compact
        current_time = get_mst_time()
        st.markdown(f"""
        <div style="
            padding: 12px 16px;
            margin: 0 8px;
            background: rgba(129, 140, 248, 0.06);
            border-radius: 8px;
            border: 1px solid rgba(129, 140, 248, 0.1);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.65rem; color: #8b95b0; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">MST</span>
                <span style="font-size: 0.8rem; color: #c7d2fe; font-weight: 600;">{current_time.strftime('%I:%M %p')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""<div style="height: 8px;"></div>""", unsafe_allow_html=True)

        # Refresh
        if st.button("↻  Refresh Data", use_container_width=True, key="refresh_btn"):
            st.cache_data.clear()
            st.rerun()

        # Version
        st.markdown("""
        <div style="
            text-align: center;
            padding: 16px 0 8px 0;
            margin-top: 12px;
        ">
            <p style="font-size: 0.6rem; color: #6b7394; margin: 0;">v4.2 · Built by Xander</p>
        </div>
        """, unsafe_allow_html=True)

    # Determine which section is active — only one radio group should be "active"
    # Streamlit keeps state for all radio groups independently, so we use a
    # session-state flag to track which group was last clicked.
    # On each run, check which radios changed from their defaults.

    # Map sections to a canonical key
    revenue_map = {
        "Q2 2026 Forecast": "📈 Q2 Revenue Snapshot",
    }
    history_map = {
        "Q1 2026 Review": "🎯 Q1 2026 Review",
        "Q4 2025 Review": "📉 Q4 Revenue Snapshot",
    }
    planning_map = {
        "S&OP Planning": "📊 S&OP Planning",
        "2026 Yearly Planning": "📅 2026 Yearly Planning",
    }
    ops_map = {
        "Quality Management": "🛡️ Quality Management",
        "Rev Ops Playground": "🎮 Revenue Operations Playground",
    }

    # Track last active group
    if "last_nav_group" not in st.session_state:
        st.session_state.last_nav_group = "revenue"

    # Detect which group the user just interacted with
    prev_revenue = st.session_state.get("_prev_main_nav", section)
    prev_history = st.session_state.get("_prev_main_nav_history", section_hist)
    prev_planning = st.session_state.get("_prev_main_nav_planning", section2)
    prev_ops = st.session_state.get("_prev_main_nav_ops", section3)

    if section != prev_revenue:
        st.session_state.last_nav_group = "revenue"
    elif section_hist != prev_history:
        st.session_state.last_nav_group = "history"
    elif section2 != prev_planning:
        st.session_state.last_nav_group = "planning"
    elif section3 != prev_ops:
        st.session_state.last_nav_group = "ops"

    st.session_state["_prev_main_nav"] = section
    st.session_state["_prev_main_nav_history"] = section_hist
    st.session_state["_prev_main_nav_planning"] = section2
    st.session_state["_prev_main_nav_ops"] = section3

    group = st.session_state.last_nav_group
    if group == "revenue":
        return revenue_map.get(section, "📈 Q2 Revenue Snapshot")
    elif group == "history":
        return history_map.get(section_hist, "🎯 Q1 2026 Review")
    elif group == "planning":
        return planning_map.get(section2, "📊 S&OP Planning")
    else:
        return ops_map.get(section3, "🛡️ Quality Management")


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
    """Render 2026 Yearly Planning section."""
    if YEARLY_MODULE_LOADED:
        try:
            render_yearly_planning_2026()
        except Exception as e:
            st.error(f"Error loading 2026 Yearly Planning: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.markdown("""
        <div style='text-align: center; padding: 15px; background: linear-gradient(135deg, #ec4899 0%, #db2777 100%); 
                     color: white; border-radius: 16px; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(236, 72, 153, 0.3);'>
            <h2 style='margin: 0; color: white !important;'>📅 2026 Yearly Planning</h2>
            <p style='font-size: 0.9rem; margin: 8px 0 0 0; opacity: 0.9; color: white !important;'>Annual Strategic Planning & Capacity</p>
        </div>
        """, unsafe_allow_html=True)
        st.info("📌 **2026 Yearly Planning module not yet loaded.**")


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
    
    # Map the navigation options
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
    elif section == "📅 2026 Yearly Planning":
        render_2026_yearly_planning_section()
    elif section == "🎮 Revenue Operations Playground":
        render_rev_ops_playground_section()


if __name__ == "__main__":
    main()
