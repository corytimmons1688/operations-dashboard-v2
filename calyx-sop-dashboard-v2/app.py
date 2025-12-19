"""
Calyx Containers S&OP Dashboard
================================
Unified Sales & Operations Planning and Quality Management System

Sections:
- S&OP: Sales Rep View, Operations View, Scenario Planning, PO Forecast, Deliveries
- Quality: NC Dashboard (Status, Aging, Cost, Customer, Pareto Analysis)

Author: Xander @ Calyx Containers
Version: 3.0.0
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import logging

# =============================================================================
# PAGE CONFIGURATION - Must be first Streamlit command
# =============================================================================
st.set_page_config(
    page_title="Calyx S&OP Dashboard",
    page_icon="📊",
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

# Configure logging
try:
    setup_logging()
except:
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# CALYX BRAND COLORS (from Brand Guidelines)
# =============================================================================
CALYX_COLORS = {
    'calyx_blue': '#0033A1',
    'ocean_blue': '#001F60',
    'flash_blue': '#004FFF',
    'mist_blue': '#202945',
    'cloud_blue': '#D9F1FD',
    'powder_blue': '#DBE6FF',
    'white': '#FFFFFF',
    'black': '#000000',
    'gray_90': '#1A1A1A',
    'gray_60': '#666666',
    'gray_30': '#B3B3B3',
    'gray_10': '#E5E5E5',
    'gray_5': '#F1F2F2',
}

# =============================================================================
# CUSTOM CSS - CALYX BRAND STYLING
# =============================================================================
def inject_custom_css():
    """Inject custom CSS for Calyx brand styling."""
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
        
        :root {{
            --calyx-blue: {CALYX_COLORS['calyx_blue']};
            --ocean-blue: {CALYX_COLORS['ocean_blue']};
            --flash-blue: {CALYX_COLORS['flash_blue']};
            --mist-blue: {CALYX_COLORS['mist_blue']};
            --cloud-blue: {CALYX_COLORS['cloud_blue']};
            --powder-blue: {CALYX_COLORS['powder_blue']};
            --gray-90: {CALYX_COLORS['gray_90']};
            --gray-60: {CALYX_COLORS['gray_60']};
            --gray-30: {CALYX_COLORS['gray_30']};
            --gray-10: {CALYX_COLORS['gray_10']};
            --gray-5: {CALYX_COLORS['gray_5']};
        }}
        
        html, body, [class*="css"] {{
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        }}
        
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, var(--mist-blue) 0%, var(--ocean-blue) 100%);
            border-right: none;
        }}
        
        section[data-testid="stSidebar"] .stMarkdown {{ color: white; }}
        section[data-testid="stSidebar"] label {{ color: rgba(255, 255, 255, 0.8) !important; }}
        section[data-testid="stSidebar"] .stSelectbox label {{ color: rgba(255, 255, 255, 0.9) !important; }}
        
        section[data-testid="stSidebar"] .stRadio > div {{
            background: rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            padding: 12px;
        }}
        
        section[data-testid="stSidebar"] .stRadio > div > label {{
            color: white !important;
            padding: 12px 16px;
            border-radius: 6px;
            transition: all 0.2s ease;
            font-size: 1rem !important;
            font-weight: 500 !important;
        }}
        
        section[data-testid="stSidebar"] .stRadio > div > label:hover {{
            background: rgba(255, 255, 255, 0.15);
        }}
        
        section[data-testid="stSidebar"] .stRadio > div > label > div {{
            color: white !important;
            font-weight: 500 !important;
        }}
        
        section[data-testid="stSidebar"] .stRadio > div > label span {{
            color: white !important;
        }}
        
        .main-header {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--gray-90);
            margin-bottom: 0.25rem;
        }}
        
        .sub-header {{
            font-size: 1rem;
            color: var(--gray-60);
            margin-bottom: 1.5rem;
        }}
        
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0;
            background: var(--gray-5);
            border-radius: 10px;
            padding: 4px;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            background: transparent;
            border-radius: 8px;
            color: var(--gray-60);
            font-weight: 500;
            padding: 12px 24px;
            border: none;
        }}
        
        .stTabs [data-baseweb="tab"]:hover {{
            background: rgba(0, 51, 161, 0.1);
            color: var(--calyx-blue);
        }}
        
        .stTabs [aria-selected="true"] {{
            background: var(--calyx-blue) !important;
            color: white !important;
        }}
        
        .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display: none; }}
        
        .filter-section {{
            background: var(--powder-blue);
            border-radius: 10px;
            padding: 1rem 1.5rem;
            margin: 1rem 0;
        }}
        
        [data-testid="stMetric"] {{
            background: white;
            border: 1px solid var(--gray-10);
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
        }}
        
        [data-testid="stMetricLabel"] {{ color: var(--gray-60) !important; font-weight: 500; }}
        [data-testid="stMetricValue"] {{ color: var(--calyx-blue) !important; font-weight: 700; }}
        
        .stDataFrame {{
            border: 1px solid var(--gray-10);
            border-radius: 10px;
            overflow: hidden;
        }}
        
        .stButton > button {{
            background: var(--calyx-blue);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            padding: 0.5rem 1.5rem;
            transition: all 0.2s ease;
        }}
        
        .stButton > button:hover {{
            background: var(--ocean-blue);
            box-shadow: 0 4px 12px rgba(0, 51, 161, 0.3);
        }}
        
        .streamlit-expanderHeader {{
            background: var(--gray-5);
            border-radius: 8px;
            font-weight: 600;
            color: var(--gray-90);
        }}
        
        .streamlit-expanderHeader:hover {{
            background: var(--powder-blue);
            color: var(--calyx-blue);
        }}
        
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# SIDEBAR NAVIGATION
# =============================================================================
def render_sidebar():
    """Render the sidebar with Calyx branding and navigation."""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem 1rem 2rem 1rem;">
            <img src="https://raw.githubusercontent.com/xxxward/operations-dashboard-v2/main/calyx_logo.png" 
                 alt="Calyx Containers" 
                 style="max-width: 160px; margin-bottom: 0.5rem; filter: brightness(0) invert(1);"
                 onerror="this.style.display='none'; document.getElementById('logo-fallback').style.display='block';">
            <div id="logo-fallback" style="display: none; text-align: center;">
                <h1 style="color: white; font-size: 1.5rem; font-weight: 600; margin: 0;">CALYX</h1>
                <p style="color: rgba(255,255,255,0.7); font-size: 0.75rem; letter-spacing: 3px; margin: 0;">CONTAINERS</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown('<p style="color: rgba(255,255,255,0.7); font-size: 0.75rem; font-weight: 600; letter-spacing: 2px; margin-bottom: 0.75rem;">MAIN MENU</p>', unsafe_allow_html=True)
        
        section = st.radio(
            "Navigation",
            options=["📈 S&OP Planning", "🎯 Quality Management"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown('<p style="color: rgba(255,255,255,0.7); font-size: 0.75rem; font-weight: 600; letter-spacing: 2px; margin-bottom: 0.75rem;">DASHBOARD INFO</p>', unsafe_allow_html=True)
        st.markdown(f'<p style="color: rgba(255,255,255,0.9); font-size: 0.85rem;">Last Refresh: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>', unsafe_allow_html=True)
        st.markdown('<p style="color: rgba(255,255,255,0.9); font-size: 0.85rem;">Version: 3.0.0</p>', unsafe_allow_html=True)
        
        st.markdown("---")
        with st.expander("📚 Help & Documentation"):
            st.markdown("""
            **S&OP Section:**
            - Sales Rep View: Customer forecasts
            - Operations: Demand vs pipeline
            - Scenarios: Plan & compare
            - PO Forecast: Purchase planning
            - Deliveries: Track shipments
            
            **Quality Section:**
            - Status Tracker: Open NCs
            - Aging Analysis: Time in queue
            - Cost Analysis: Rework costs
            - Customer Impact: By customer
            - Pareto: Top issues
            """)
        
        st.markdown("---")
        st.markdown("""
        <div style="background: rgba(34, 197, 94, 0.2); border-radius: 8px; padding: 0.75rem; display: flex; align-items: center; gap: 0.5rem;">
            <div style="width: 8px; height: 8px; background: #22C55E; border-radius: 50%; animation: pulse 2s infinite;"></div>
            <span style="color: white; font-size: 0.8rem;">System Healthy</span>
        </div>
        <style>@keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}</style>
        """, unsafe_allow_html=True)
        
    return section


# =============================================================================
# S&OP PLANNING SECTION
# =============================================================================
def render_sop_section():
    """Render the S&OP Planning section with all sub-tabs."""
    st.markdown('<h1 class="main-header">📈 Sales & Operations Planning</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Demand Forecasting • Scenario Planning • Supply Chain Visibility</p>', unsafe_allow_html=True)
    
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
    """Render Sales Rep View tab - filters are handled within the view itself."""
    if MODULES_LOADED:
        try:
            render_sales_rep_view()
        except Exception as e:
            st.error(f"Error loading Sales Rep View: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            with st.expander("🔧 Troubleshooting"):
                st.markdown("""
                This view requires the following data sources:
                - Invoice Line Item (historical demand)
                - _NS_SalesOrders_Data (customer/rep mapping)
                - Raw_Items (SKU details with 'Calyx || Product Type')
                - Deals (pipeline data)
                
                Please ensure these sheets exist and are accessible.
                """)
    else:
        st.warning(f"Module not loaded: {IMPORT_ERROR}")


def render_operations_tab():
    """Render Operations View tab - filters are handled within the view itself."""
    if MODULES_LOADED:
        try:
            render_operations_view()
        except Exception as e:
            st.error(f"Error loading Operations View: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.warning(f"Module not loaded: {IMPORT_ERROR}")


def render_scenarios_tab():
    """Render Scenario Planning tab with its specific filters."""
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    cols = st.columns([2, 2, 2, 2, 1])
    with cols[0]:
        st.selectbox("Scenario Type", ["Growth", "Conservative", "Custom"], key="scen_type")
    with cols[1]:
        st.selectbox("Base Year", ["2025", "2024"], key="scen_base")
    with cols[2]:
        st.selectbox("Growth Assumption", ["5%", "10%", "15%", "20%", "Custom"], key="scen_growth")
    with cols[3]:
        st.selectbox("Target Year", ["2026", "2027"], key="scen_target")
    with cols[4]:
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("Apply", key="scen_apply", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if MODULES_LOADED:
        try:
            render_scenario_planning()
        except Exception as e:
            st.error(f"Error loading Scenario Planning: {str(e)}")
    else:
        st.warning(f"Module not loaded: {IMPORT_ERROR}")


def render_po_forecast_tab():
    """Render PO Forecast tab with its specific filters."""
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    cols = st.columns([2, 2, 2, 2, 1])
    with cols[0]:
        st.selectbox("Vendor", ["All", "Primary Vendor", "Secondary Vendor"], key="po_vendor")
    with cols[1]:
        st.selectbox("Lead Time", ["Standard", "Expedited", "All"], key="po_lead")
    with cols[2]:
        st.selectbox("PO Status", ["All", "Open", "Pending", "Received"], key="po_status")
    with cols[3]:
        st.selectbox("Date Range", ["Next 30 Days", "Next 60 Days", "Next 90 Days", "All"], key="po_date")
    with cols[4]:
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("Apply", key="po_apply", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if MODULES_LOADED:
        try:
            render_po_forecast()
        except Exception as e:
            st.error(f"Error loading PO Forecast: {str(e)}")
    else:
        st.warning(f"Module not loaded: {IMPORT_ERROR}")


def render_deliveries_tab():
    """Render Deliveries Tracking tab with its specific filters."""
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    cols = st.columns([2, 2, 2, 2, 1])
    with cols[0]:
        st.selectbox("Customer", ["All"], key="del_customer")
    with cols[1]:
        st.selectbox("Delivery Status", ["All", "Pending", "In Transit", "Delivered", "Delayed"], key="del_status")
    with cols[2]:
        st.selectbox("Carrier", ["All", "FedEx", "UPS", "Freight"], key="del_carrier")
    with cols[3]:
        st.selectbox("Date Range", ["This Week", "Next Week", "This Month", "All"], key="del_date")
    with cols[4]:
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("Apply", key="del_apply", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if MODULES_LOADED:
        try:
            render_deliveries_tracking()
        except Exception as e:
            st.error(f"Error loading Deliveries Tracking: {str(e)}")
    else:
        st.warning(f"Module not loaded: {IMPORT_ERROR}")


# =============================================================================
# QUALITY MANAGEMENT SECTION
# =============================================================================
def render_quality_section_wrapper():
    """Render the Quality Management section with NC Dashboard."""
    st.markdown('<h1 class="main-header">🎯 Quality Management</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Non-Conformance Tracking • Root Cause Analysis • Cost of Quality</p>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Status Tracker",
        "⏱️ Aging Analysis",
        "💰 Cost Analysis",
        "👥 Customer Impact",
        "📈 Pareto Analysis"
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
    """Render Quality Status Tracker tab with its specific filters."""
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    cols = st.columns([2, 2, 2, 2, 1])
    with cols[0]:
        st.selectbox("NC Status", ["All", "Open", "In Progress", "Pending Review", "Closed"], key="qs_status")
    with cols[1]:
        st.selectbox("Priority", ["All", "High", "Medium", "Low"], key="qs_priority")
    with cols[2]:
        st.selectbox("NC Type", ["All", "Internal", "External", "Supplier"], key="qs_type")
    with cols[3]:
        st.selectbox("Date Range", ["Last 30 Days", "Last 90 Days", "YTD", "All Time"], key="qs_date")
    with cols[4]:
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("Apply", key="qs_apply", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if MODULES_LOADED:
        try:
            from src.kpi_cards import render_open_nc_status_tracker
            render_open_nc_status_tracker()
        except Exception as e:
            st.error(f"Error loading Status Tracker: {str(e)}")
    else:
        st.warning(f"Module not loaded: {IMPORT_ERROR}")


def render_quality_aging_tab():
    """Render Quality Aging Analysis tab with its specific filters."""
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    cols = st.columns([2, 2, 2, 2, 1])
    with cols[0]:
        st.selectbox("Aging Bucket", ["All", "0-7 Days", "8-14 Days", "15-30 Days", "30+ Days"], key="qa_bucket")
    with cols[1]:
        st.selectbox("Owner", ["All"], key="qa_owner")
    with cols[2]:
        st.selectbox("Department", ["All", "Production", "QA", "Shipping", "Receiving"], key="qa_dept")
    with cols[3]:
        st.selectbox("NC Status", ["Open Only", "All"], key="qa_status")
    with cols[4]:
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("Apply", key="qa_apply", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if MODULES_LOADED:
        try:
            from src.aging_analysis import render_aging_dashboard
            render_aging_dashboard()
        except Exception as e:
            st.error(f"Error loading Aging Analysis: {str(e)}")
    else:
        st.warning(f"Module not loaded: {IMPORT_ERROR}")


def render_quality_cost_tab():
    """Render Quality Cost Analysis tab with its specific filters."""
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    cols = st.columns([2, 2, 2, 2, 1])
    with cols[0]:
        st.selectbox("Cost Type", ["All", "Rework", "Scrap", "Returns", "Labor"], key="qc_type")
    with cols[1]:
        st.selectbox("Product Line", ["All", "Concentrate", "Flower", "Pre-Roll"], key="qc_product")
    with cols[2]:
        st.selectbox("Time Period", ["Monthly", "Quarterly", "YTD", "Yearly"], key="qc_period")
    with cols[3]:
        st.selectbox("Compare To", ["Prior Period", "Budget", "None"], key="qc_compare")
    with cols[4]:
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("Apply", key="qc_apply", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
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
    """Render Quality Customer Impact tab with its specific filters."""
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    cols = st.columns([2, 2, 2, 2, 1])
    with cols[0]:
        st.selectbox("Customer", ["All"], key="qcust_customer")
    with cols[1]:
        st.selectbox("Impact Level", ["All", "High", "Medium", "Low"], key="qcust_impact")
    with cols[2]:
        st.selectbox("NC Category", ["All", "Quality", "Delivery", "Documentation"], key="qcust_cat")
    with cols[3]:
        st.selectbox("Date Range", ["Last 90 Days", "Last 6 Months", "YTD", "All Time"], key="qcust_date")
    with cols[4]:
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("Apply", key="qcust_apply", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if MODULES_LOADED:
        try:
            from src.customer_analysis import render_customer_analysis
            render_customer_analysis()
        except Exception as e:
            st.error(f"Error loading Customer Impact: {str(e)}")
    else:
        st.warning(f"Module not loaded: {IMPORT_ERROR}")


def render_quality_pareto_tab():
    """Render Quality Pareto Analysis tab with its specific filters."""
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    cols = st.columns([2, 2, 2, 2, 1])
    with cols[0]:
        st.selectbox("Analyze By", ["Issue Type", "Root Cause", "Product", "Supplier"], key="qp_by")
    with cols[1]:
        st.selectbox("Metric", ["Count", "Cost", "Days Open"], key="qp_metric")
    with cols[2]:
        st.selectbox("Show Top", ["5", "10", "15", "20"], key="qp_top")
    with cols[3]:
        st.selectbox("Date Range", ["Last 90 Days", "Last 6 Months", "YTD", "All Time"], key="qp_date")
    with cols[4]:
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("Apply", key="qp_apply", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if MODULES_LOADED:
        try:
            from src.pareto_chart import render_issue_type_pareto
            render_issue_type_pareto()
        except Exception as e:
            st.error(f"Error loading Pareto Analysis: {str(e)}")
    else:
        st.warning(f"Module not loaded: {IMPORT_ERROR}")


# =============================================================================
# MAIN APPLICATION
# =============================================================================
def main():
    """Main application entry point."""
    inject_custom_css()
    section = render_sidebar()
    
    if section == "📈 S&OP Planning":
        render_sop_section()
    else:
        render_quality_section_wrapper()
    
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0 1rem 0; color: #999; font-size: 0.75rem; border-top: 1px solid #eee; margin-top: 3rem;">
        Calyx Containers S&OP Dashboard v3.0 | Built with Streamlit | Data refreshes every 5 minutes
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
