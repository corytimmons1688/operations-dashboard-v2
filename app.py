"""
Calyx Containers S&OP Dashboard
Unified Sales & Operations Planning and Quality Management System

Main Streamlit Application Entry Point

Sections:
- S&OP: Sales Rep View, Operations View, Scenario Planning, PO Forecast, Deliveries
- Quality: NC Dashboard (Status, Aging, Cost, Customer, Pareto Analysis)

Author: Xander @ Calyx Containers
Version: 2.0.0
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import logging

# Local imports - S&OP Modules
from src.sales_rep_view import render_sales_rep_view
from src.operations_view import render_operations_view
from src.scenario_planning import render_scenario_planning
from src.po_forecast import render_po_forecast
from src.deliveries_tracking import render_deliveries_tracking
from src.quality_section import render_quality_section

# Legacy NC Dashboard imports (for fallback)
from src.data_loader import load_nc_data, refresh_data
from src.utils import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Calyx S&OP Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Main header styling */
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A5F;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    /* Navigation tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: #f0f2f6;
        padding: 8px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 12px 24px;
        background-color: transparent;
        border-radius: 8px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E3A5F;
        color: white;
    }
    
    /* Metric cards */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
    }
    
    /* Sidebar styling */
    .sidebar-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    
    /* Section dividers */
    .section-divider {
        border-top: 2px solid #e0e0e0;
        margin: 1rem 0;
    }
    
    /* Tab content padding */
    .tab-content {
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def render_sidebar():
    """Render the main sidebar with navigation and global settings."""
    
    with st.sidebar:
        # Logo placeholder
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="color: #1E3A5F; margin: 0;">🌿 Calyx Containers</h2>
            <p style="color: #666; font-size: 0.9rem; margin: 0;">S&OP Dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Section selector
        st.markdown("### 🧭 Navigation")
        
        section = st.radio(
            "Select Section",
            options=["📈 S&OP Planning", "🔍 Quality Management"],
            key="main_section",
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Refresh button
        if st.button("🔄 Refresh All Data", use_container_width=True):
            st.cache_data.clear()
            st.success("Data cache cleared!")
            st.rerun()
        
        st.markdown("---")
        
        # Info section
        st.markdown("### ℹ️ Dashboard Info")
        st.markdown(f"**Last Refresh:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.markdown(f"**Version:** 2.0.0")
        
        # Quick links
        st.markdown("---")
        st.markdown("### 🔗 Quick Links")
        
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
        
        return section


def render_sop_section():
    """Render the S&OP Planning section with all sub-tabs."""
    
    st.markdown('<h1 class="main-header">📈 Sales & Operations Planning</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Demand Forecasting • Scenario Planning • Supply Chain Visibility</p>', unsafe_allow_html=True)
    
    # S&OP main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👤 Sales Rep View",
        "📦 Operations",
        "🎯 Scenarios",
        "📋 PO Forecast",
        "🚚 Deliveries"
    ])
    
    with tab1:
        try:
            render_sales_rep_view()
        except Exception as e:
            st.error(f"Error loading Sales Rep View: {str(e)}")
            logger.error(f"Sales Rep View error: {e}", exc_info=True)
            with st.expander("🔧 Troubleshooting"):
                st.markdown("""
                This view requires the following data sources:
                - Invoice Line Item (historical demand)
                - _NS_SalesOrders_Data (customer/rep mapping)
                - Raw_Items (SKU details)
                
                Please ensure these sheets exist and are accessible.
                """)
    
    with tab2:
        try:
            render_operations_view()
        except Exception as e:
            st.error(f"Error loading Operations View: {str(e)}")
            logger.error(f"Operations View error: {e}", exc_info=True)
            with st.expander("🔧 Troubleshooting"):
                st.markdown("""
                This view requires:
                - Invoice Line Item (demand history)
                - Deals (pipeline data)
                - Raw_Items (product categories)
                - Raw_Inventory (current stock)
                """)
    
    with tab3:
        try:
            render_scenario_planning()
        except Exception as e:
            st.error(f"Error loading Scenario Planning: {str(e)}")
            logger.error(f"Scenario Planning error: {e}", exc_info=True)
            with st.expander("🔧 Troubleshooting"):
                st.markdown("""
                Scenario planning requires:
                - Invoice Line Item (historical data for base forecast)
                - Deals (optional pipeline data for blending)
                """)
    
    with tab4:
        try:
            render_po_forecast()
        except Exception as e:
            st.error(f"Error loading PO Forecast: {str(e)}")
            logger.error(f"PO Forecast error: {e}", exc_info=True)
            with st.expander("🔧 Troubleshooting"):
                st.markdown("""
                PO Forecast requires:
                - Invoice Line Item (demand history)
                - Raw_Items (lead times, costs)
                - Raw_Vendors (payment terms)
                - Raw_Inventory (current stock)
                """)
    
    with tab5:
        try:
            render_deliveries_tracking()
        except Exception as e:
            st.error(f"Error loading Deliveries Tracking: {str(e)}")
            logger.error(f"Deliveries Tracking error: {e}", exc_info=True)
            with st.expander("🔧 Troubleshooting"):
                st.markdown("""
                Deliveries tracking requires:
                - _NS_SalesOrders_Data (order/shipment data)
                - Sales Order Line Item (line details)
                """)


def render_quality_section_wrapper():
    """Render the Quality Management section."""
    
    st.markdown('<h1 class="main-header">🔍 Quality Management</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Non-Conformance Tracking • Root Cause Analysis • Cost of Quality</p>', unsafe_allow_html=True)
    
    try:
        render_quality_section()
    except Exception as e:
        st.error(f"Error loading Quality Section: {str(e)}")
        logger.error(f"Quality Section error: {e}", exc_info=True)
        
        # Fallback to basic NC data display
        st.markdown("---")
        st.markdown("### 📋 Fallback Data View")
        
        try:
            nc_data = load_nc_data()
            if nc_data is not None and not nc_data.empty:
                st.dataframe(nc_data, use_container_width=True, height=400)
            else:
                st.warning("No NC data available.")
        except Exception as e2:
            st.error(f"Unable to load NC data: {str(e2)}")
        
        with st.expander("🔧 Troubleshooting"):
            st.markdown("""
            The Quality section requires:
            - Non-Conformance Details sheet
            
            Required columns include:
            - NC Number, Status, Priority
            - Customer, Issue Type
            - Date Submitted, Date Closed
            - Cost of Rework, Cost Avoided
            - External Or Internal
            """)


def main():
    """Main application entry point."""
    
    # Render sidebar and get section selection
    section = render_sidebar()
    
    # Render the appropriate section
    if section == "📈 S&OP Planning":
        render_sop_section()
    else:  # Quality Management
        render_quality_section_wrapper()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #888; font-size: 0.8rem;">
            Calyx Containers S&OP Dashboard v2.0 | 
            Built with Streamlit | 
            Data refreshes every 5 minutes
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
