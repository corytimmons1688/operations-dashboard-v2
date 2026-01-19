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
    """Inject custom CSS for dark, sexy styling."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ==============================================
       FORCE DARK THEME EVERYWHERE (Cleaned up - removed problematic selectors)
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
        letter-spacing: 0.5px !important;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(124, 58, 237, 0.5) !important;
    }

    /* ==============================================
       TABS - FUTURISTIC STYLE
       ============================================== */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(15, 23, 42, 0.8) !important;
        border-radius: 16px !important;
        padding: 8px !important;
        gap: 8px !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        color: #94a3b8 !important;
        transition: all 0.3s ease !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(99, 102, 241, 0.1) !important;
        color: #e2e8f0 !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.4) !important;
    }

    /* ==============================================
       DATA TABLES - DARK GLASS STYLE
       ============================================== */
    .stDataFrame {
        background: rgba(15, 23, 42, 0.8) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        overflow: hidden !important;
    }
    
    [data-testid="stDataFrame"] > div {
        background: transparent !important;
    }
    
    .stDataFrame thead th {
        background: rgba(30, 41, 59, 0.9) !important;
        color: #e2e8f0 !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        font-size: 0.75rem !important;
        padding: 16px !important;
        border-bottom: 2px solid rgba(99, 102, 241, 0.3) !important;
    }
    
    .stDataFrame tbody td {
        background: rgba(15, 23, 42, 0.6) !important;
        color: #cbd5e1 !important;
        padding: 12px 16px !important;
        border-bottom: 1px solid rgba(99, 102, 241, 0.1) !important;
    }
    
    .stDataFrame tbody tr:hover td {
        background: rgba(99, 102, 241, 0.1) !important;
    }

    /* ==============================================
       EXPANDER - SLEEK ACCORDION
       ============================================== */
    .streamlit-expanderHeader {
        background: rgba(30, 41, 59, 0.8) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        color: #e2e8f0 !important;
        font-weight: 600 !important;
    }
    
    .streamlit-expanderContent {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(99, 102, 241, 0.1) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
    }

    /* ==============================================
       SELECT BOXES & INPUTS
       ============================================== */
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    .stTextInput > div > div {
        background: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
    }
    
    .stSelectbox [data-baseweb="select"] > div,
    .stMultiSelect [data-baseweb="select"] > div {
        background: rgba(30, 41, 59, 0.8) !important;
        border-color: rgba(99, 102, 241, 0.3) !important;
    }

    /* ==============================================
       RADIO BUTTONS - NAVIGATION STYLE
       ============================================== */
    .stRadio > div {
        background: transparent !important;
    }
    
    .stRadio > div > label {
        background: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        margin-bottom: 8px !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
    }
    
    .stRadio > div > label:hover {
        background: rgba(99, 102, 241, 0.15) !important;
        border-color: rgba(99, 102, 241, 0.4) !important;
        transform: translateX(4px) !important;
    }
    
    .stRadio > div > label[data-checked="true"] {
        background: linear-gradient(135deg, rgba(79, 70, 229, 0.3) 0%, rgba(124, 58, 237, 0.3) 100%) !important;
        border-color: #7c3aed !important;
        box-shadow: 0 0 20px rgba(124, 58, 237, 0.2) !important;
    }

    /* ==============================================
       PLOTLY CHARTS - DARK THEME
       ============================================== */
    .js-plotly-plot .plotly .bg {
        fill: transparent !important;
    }

    /* ==============================================
       SCROLLBAR - SUBTLE DARK
       ============================================== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(15, 23, 42, 0.5);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(99, 102, 241, 0.4);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(99, 102, 241, 0.6);
    }

    /* ==============================================
       ALERTS & INFO BOXES
       ============================================== */
    .stAlert {
        background: rgba(30, 41, 59, 0.8) !important;
        border-radius: 12px !important;
        border-left: 4px solid #6366f1 !important;
    }
    
    .element-container div[data-testid="stAlert"] {
        background: rgba(30, 41, 59, 0.8) !important;
    }

    /* ==============================================
       DIVIDER
       ============================================== */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent 0%, rgba(99, 102, 241, 0.3) 50%, transparent 100%) !important;
        margin: 2rem 0 !important;
    }

    /* ==============================================
       SIDEBAR RADIO ANIMATION
       ============================================== */
    [data-testid="stSidebar"] .stRadio > div > label {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# SIDEBAR NAVIGATION
# =============================================================================
def render_sidebar():
    """Render the sidebar with navigation."""
    with st.sidebar:
        # Logo and branding
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #1e40af 0%, #7c3aed 50%, #ec4899 100%);
            padding: 25px;
            border-radius: 20px;
            text-align: center;
            margin-bottom: 25px;
            box-shadow: 0 10px 40px rgba(124, 58, 237, 0.4);
            position: relative;
            overflow: hidden;
        ">
            <div style="
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
                animation: shimmer 3s infinite;
            "></div>
            <h1 style="
                color: white;
                font-size: 1.8rem;
                margin: 0;
                font-weight: 900;
                text-shadow: 0 2px 10px rgba(0,0,0,0.3);
                letter-spacing: -1px;
                position: relative;
            ">🚀 CALYX</h1>
            <p style="
                color: rgba(255,255,255,0.9);
                font-size: 0.7rem;
                margin: 8px 0 0 0;
                font-weight: 600;
                letter-spacing: 4px;
                text-transform: uppercase;
                position: relative;
            ">COMMAND CENTER</p>
        </div>
        <style>
        @keyframes shimmer {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Section Header
        st.markdown("""
        <p style="
            color: #64748b;
            font-size: 0.65rem;
            font-weight: 700;
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-bottom: 12px;
            padding-left: 4px;
        ">NAVIGATION</p>
        """, unsafe_allow_html=True)
        
        # Navigation Radio
        section = st.radio(
            "Navigation",
            options=[
                "🎯 Q1 Revenue Snapshot",
                "📈 S&OP Planning", 
                "🛡️ Quality Management",
                "📊 Q4 Revenue Snapshot",
                "📅 2026 Yearly Planning",
                "🎮 Revenue Operations Playground"
            ],
            label_visibility="collapsed",
            key="main_nav"
        )
        
        st.markdown("---")
        
        # Quick Stats Cards
        st.markdown("""
        <p style="
            color: #64748b;
            font-size: 0.65rem;
            font-weight: 700;
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-bottom: 12px;
            padding-left: 4px;
        ">QUICK STATS</p>
        """, unsafe_allow_html=True)
        
        # Current time card
        current_time = get_mst_time()
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(37, 99, 235, 0.2) 100%);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 12px;
        ">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 24px;">🕐</span>
                <div>
                    <div style="font-size: 0.65rem; opacity: 0.7; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8;">Current Time (MST)</div>
                    <div style="font-size: 1.1rem; font-weight: 700; color: #3b82f6;">{current_time.strftime('%I:%M %p')}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # System status card
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(5, 150, 105, 0.2) 100%);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 12px;
        ">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="
                    width: 12px;
                    height: 12px;
                    background: #10b981;
                    border-radius: 50%;
                    box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
                    animation: pulse 2s infinite;
                "></div>
                <div>
                    <div style="font-size: 0.65rem; opacity: 0.7; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8;">System Status</div>
                    <div style="font-size: 0.9rem; font-weight: 700; color: #10b981;">All Systems Operational</div>
                </div>
            </div>
        </div>
        <style>
        @keyframes pulse {
            0%, 100% { opacity: 1; box-shadow: 0 0 10px rgba(16, 185, 129, 0.5); }
            50% { opacity: 0.6; box-shadow: 0 0 20px rgba(16, 185, 129, 0.8); }
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Refresh button
        if st.button("🔄 Refresh All Data", use_container_width=True, key="refresh_btn"):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        
        # Help section
        with st.expander("📚 Help & Navigation"):
            st.markdown("""
            <div style="font-size: 0.85rem; line-height: 1.6;">
            
            **🎯 Q1 Revenue Snapshot**
            Live Q1 2026 forecasting with interactive planning tools
            
            **📈 S&OP Planning**
            Sales & Operations planning with demand forecasting
            
            **🛡️ Quality Management**
            NC tracking, aging analysis, and quality metrics
            
            **📊 Q4 Revenue Snapshot**
            Q4 2025 historical performance data
            
            **📅 2026 Yearly Planning**
            Annual strategic planning and capacity
            
            **🎮 Revenue Operations Playground**
            QBR Generator & ad-hoc analysis tools
            
            </div>
            """, unsafe_allow_html=True)
        
        # Version info
        st.markdown("""
        <div style="
            text-align: center;
            padding: 15px;
            margin-top: 20px;
            border-top: 1px solid rgba(99, 102, 241, 0.2);
        ">
            <p style="font-size: 0.7rem; color: #64748b; margin: 0;">
                Calyx Command Center v4.1
            </p>
            <p style="font-size: 0.65rem; color: #475569; margin: 4px 0 0 0;">
                Built with ❤️ by Xander
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    return section


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
    """Render Q1 Revenue Snapshot & Planning section."""
    # The Q1 module handles its own header and layout - don't add extra headers
    if Q1_MODULE_LOADED:
        try:
            render_q1_revenue_snapshot()
        except Exception as e:
            st.error(f"Error loading Q1 Revenue Snapshot: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.markdown("""
        <div style='text-align: center; padding: 15px; background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); 
                     color: white; border-radius: 16px; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(139, 92, 246, 0.3);'>
            <h2 style='margin: 0; color: white !important;'>🎯 Q1 Revenue Snapshot</h2>
            <p style='font-size: 0.9rem; margin: 8px 0 0 0; opacity: 0.9; color: white !important;'>Q1 2026 Planning & Forecasting</p>
        </div>
        """, unsafe_allow_html=True)
        st.info("📌 **Q1 Revenue Snapshot module not yet loaded.**")
        st.markdown(f"Import Error: `{Q1_IMPORT_ERROR}`")


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
    if section == "🎯 Q1 Revenue Snapshot":
        render_q1_revenue_section()
    elif section == "📈 S&OP Planning":
        render_sop_section()
    elif section == "🛡️ Quality Management":
        render_quality_section_wrapper()
    elif section == "📊 Q4 Revenue Snapshot":
        render_q4_revenue_section()
    elif section == "📅 2026 Yearly Planning":
        render_2026_yearly_planning_section()
    elif section == "🎮 Revenue Operations Playground":
        render_rev_ops_playground_section()


if __name__ == "__main__":
    main()
