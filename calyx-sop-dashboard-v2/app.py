"""
Calyx Containers - Operations Dashboard
========================================
S&OP Planning and Quality Management Dashboard
Styled according to Calyx Brand Guidelines

Author: Xander @ Calyx Containers
Version: 3.0
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Calyx Containers | Operations Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CALYX BRAND COLORS (from Brand Guidelines)
# =============================================================================
CALYX_COLORS = {
    'calyx_blue': '#0033A1',      # Primary
    'ocean_blue': '#001F60',       # Dark accent
    'flash_blue': '#004FFF',       # Accessible highlight
    'mist_blue': '#202945',        # Dark background
    'cloud_blue': '#D9F1FD',       # Light accent
    'powder_blue': '#DBE6FF',      # Light background
    'white': '#FFFFFF',
    'black': '#000000',
    'gray_90': '#1A1A1A',
    'gray_60': '#666666',
    'gray_30': '#B3B3B3',
    'gray_10': '#E5E5E5',
    'gray_5': '#F1F2F2',
    # Status colors
    'status_in': '#22C55E',
    'status_ordered': '#3B82F6',
    'status_ordered_not_confirmed': '#8B5CF6',
    'status_out': '#EF4444',
}

# =============================================================================
# CUSTOM CSS - CALYX BRAND STYLING
# =============================================================================
def inject_custom_css():
    """Inject custom CSS for Calyx brand styling."""
    st.markdown(f"""
    <style>
        /* ===== IMPORT FONTS ===== */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
        
        /* ===== ROOT VARIABLES ===== */
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
        
        /* ===== GLOBAL TYPOGRAPHY ===== */
        html, body, [class*="css"] {{
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        }}
        
        /* ===== SIDEBAR STYLING ===== */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, var(--mist-blue) 0%, var(--ocean-blue) 100%);
            border-right: none;
        }}
        
        section[data-testid="stSidebar"] .stMarkdown {{
            color: white;
        }}
        
        section[data-testid="stSidebar"] label {{
            color: rgba(255, 255, 255, 0.8) !important;
        }}
        
        section[data-testid="stSidebar"] .stSelectbox label {{
            color: rgba(255, 255, 255, 0.9) !important;
        }}
        
        /* Sidebar navigation items */
        section[data-testid="stSidebar"] .stRadio > div {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 8px;
        }}
        
        section[data-testid="stSidebar"] .stRadio > div > label {{
            color: white !important;
            padding: 10px 15px;
            border-radius: 6px;
            transition: all 0.2s ease;
        }}
        
        section[data-testid="stSidebar"] .stRadio > div > label:hover {{
            background: rgba(255, 255, 255, 0.1);
        }}
        
        section[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {{
            background: var(--calyx-blue);
        }}
        
        /* ===== MAIN HEADER ===== */
        .main-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1rem 0;
            border-bottom: 2px solid var(--gray-10);
            margin-bottom: 1.5rem;
        }}
        
        .main-header h1 {{
            color: var(--gray-90);
            font-size: 1.75rem;
            font-weight: 600;
            margin: 0;
        }}
        
        .header-actions {{
            display: flex;
            gap: 1rem;
            align-items: center;
        }}
        
        /* ===== TAB STYLING ===== */
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
        
        .stTabs [data-baseweb="tab-highlight"] {{
            display: none;
        }}
        
        .stTabs [data-baseweb="tab-border"] {{
            display: none;
        }}
        
        /* ===== FILTER BAR ===== */
        .filter-bar {{
            background: var(--powder-blue);
            border-radius: 10px;
            padding: 1rem 1.5rem;
            margin: 1rem 0;
            display: flex;
            gap: 1rem;
            align-items: flex-end;
            flex-wrap: wrap;
        }}
        
        .filter-bar .stSelectbox {{
            min-width: 150px;
        }}
        
        /* ===== KPI CARDS ===== */
        .kpi-card {{
            background: white;
            border: 1px solid var(--gray-10);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
            transition: all 0.2s ease;
        }}
        
        .kpi-card:hover {{
            box-shadow: 0 4px 16px rgba(0, 51, 161, 0.1);
            border-color: var(--calyx-blue);
        }}
        
        .kpi-card .kpi-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--calyx-blue);
            line-height: 1;
        }}
        
        .kpi-card .kpi-label {{
            font-size: 0.875rem;
            color: var(--gray-60);
            margin-top: 0.5rem;
            font-weight: 500;
        }}
        
        .kpi-card .kpi-delta {{
            font-size: 0.75rem;
            margin-top: 0.5rem;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }}
        
        .kpi-card .kpi-delta.positive {{
            background: rgba(34, 197, 94, 0.1);
            color: #16a34a;
        }}
        
        .kpi-card .kpi-delta.negative {{
            background: rgba(239, 68, 68, 0.1);
            color: #dc2626;
        }}
        
        /* ===== STATUS BADGES ===== */
        .status-badge {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .status-in {{
            background: rgba(34, 197, 94, 0.15);
            color: #16a34a;
        }}
        
        .status-ordered {{
            background: rgba(59, 130, 246, 0.15);
            color: #2563eb;
        }}
        
        .status-out {{
            background: rgba(239, 68, 68, 0.15);
            color: #dc2626;
        }}
        
        /* ===== DATA TABLE STYLING ===== */
        .stDataFrame {{
            border: 1px solid var(--gray-10);
            border-radius: 10px;
            overflow: hidden;
        }}
        
        .stDataFrame thead tr th {{
            background: var(--calyx-blue) !important;
            color: white !important;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.5px;
            padding: 12px 16px !important;
        }}
        
        .stDataFrame tbody tr:nth-child(even) {{
            background: var(--gray-5);
        }}
        
        .stDataFrame tbody tr:hover {{
            background: var(--powder-blue);
        }}
        
        /* ===== METRIC CONTAINERS ===== */
        [data-testid="stMetric"] {{
            background: white;
            border: 1px solid var(--gray-10);
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
        }}
        
        [data-testid="stMetricLabel"] {{
            color: var(--gray-60) !important;
            font-weight: 500;
        }}
        
        [data-testid="stMetricValue"] {{
            color: var(--calyx-blue) !important;
            font-weight: 700;
        }}
        
        /* ===== BUTTONS ===== */
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
        
        .stButton > button:active {{
            transform: translateY(1px);
        }}
        
        /* Secondary button style */
        .stButton > button[kind="secondary"] {{
            background: transparent;
            color: var(--calyx-blue);
            border: 2px solid var(--calyx-blue);
        }}
        
        .stButton > button[kind="secondary"]:hover {{
            background: var(--powder-blue);
        }}
        
        /* ===== EXPANDER STYLING ===== */
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
        
        /* ===== PLOTLY CHART STYLING ===== */
        .js-plotly-plot .plotly .modebar {{
            background: transparent !important;
        }}
        
        /* ===== SECTION HEADERS ===== */
        .section-header {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin: 1.5rem 0 1rem 0;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid var(--gray-10);
        }}
        
        .section-header h3 {{
            color: var(--gray-90);
            font-size: 1.125rem;
            font-weight: 600;
            margin: 0;
        }}
        
        .section-header .info-badge {{
            background: var(--cloud-blue);
            color: var(--calyx-blue);
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 500;
        }}
        
        /* ===== HIDE STREAMLIT BRANDING ===== */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        
        /* ===== RESPONSIVE ADJUSTMENTS ===== */
        @media (max-width: 768px) {{
            .filter-bar {{
                flex-direction: column;
                align-items: stretch;
            }}
            
            .kpi-card .kpi-value {{
                font-size: 1.75rem;
            }}
        }}
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# SIDEBAR NAVIGATION
# =============================================================================
def render_sidebar():
    """Render the sidebar with Calyx branding and navigation."""
    with st.sidebar:
        # Logo and branding
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0 2rem 0;">
            <div style="
                width: 60px;
                height: 60px;
                margin: 0 auto 1rem auto;
                border: 2px solid rgba(255,255,255,0.3);
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                transform: rotate(45deg);
            ">
                <div style="transform: rotate(-45deg); font-size: 1.5rem;">📦</div>
            </div>
            <h1 style="color: white; font-size: 1.5rem; font-weight: 600; margin: 0;">CALYX</h1>
            <p style="color: rgba(255,255,255,0.6); font-size: 0.75rem; letter-spacing: 3px; margin: 0;">CONTAINERS</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation sections
        st.markdown('<p style="color: rgba(255,255,255,0.5); font-size: 0.7rem; letter-spacing: 1px; margin-bottom: 0.5rem;">MAIN MENU</p>', unsafe_allow_html=True)
        
        section = st.radio(
            "Navigation",
            options=[
                "📊 Dashboard",
                "📈 S&OP Planning",
                "🎯 Quality Management",
                "⚙️ Settings"
            ],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # System status
        st.markdown("""
        <div style="
            background: rgba(34, 197, 94, 0.2);
            border-radius: 8px;
            padding: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        ">
            <div style="
                width: 8px;
                height: 8px;
                background: #22C55E;
                border-radius: 50%;
                animation: pulse 2s infinite;
            "></div>
            <span style="color: white; font-size: 0.8rem;">System Healthy</span>
        </div>
        <style>
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Tenant info
        st.markdown("""
        <div style="
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 0.75rem;
        ">
            <p style="color: rgba(255,255,255,0.5); font-size: 0.65rem; margin: 0;">TENANT</p>
            <p style="color: white; font-size: 0.9rem; font-weight: 500; margin: 0;">Calyx Containers</p>
        </div>
        """, unsafe_allow_html=True)
        
    return section


# =============================================================================
# FILTER COMPONENTS
# =============================================================================
def render_filter_bar(filter_config):
    """Render a filter bar with the specified configuration."""
    st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
    
    cols = st.columns(len(filter_config) + 1)  # +1 for Apply button
    
    filters = {}
    for i, (key, config) in enumerate(filter_config.items()):
        with cols[i]:
            filters[key] = st.selectbox(
                config['label'],
                options=config['options'],
                key=f"filter_{key}"
            )
    
    with cols[-1]:
        st.markdown("<br>", unsafe_allow_html=True)
        apply_clicked = st.button("Apply", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    return filters, apply_clicked


# =============================================================================
# DASHBOARD VIEW
# =============================================================================
def render_dashboard_view():
    """Render the main dashboard overview."""
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>Operations Dashboard</h1>
        <div class="header-actions">
            <span style="color: #666; font-size: 0.875rem;">Last updated: {}</span>
        </div>
    </div>
    """.format(datetime.now().strftime("%B %d, %Y %I:%M %p")), unsafe_allow_html=True)
    
    # Tabs with nested filters
    tab1, tab2, tab3 = st.tabs(["📦 Material Availability", "🎫 Open Tickets", "📋 Purchase Orders"])
    
    with tab1:
        render_material_availability_tab()
    
    with tab2:
        render_open_tickets_tab()
    
    with tab3:
        render_purchase_orders_tab()


def render_material_availability_tab():
    """Render the Material Availability tab with its specific filters."""
    # Tab-specific filters
    filter_config = {
        'facility': {
            'label': 'Facility',
            'options': ['All', 'Calyx Containers', 'Calyx West', 'Calyx East']
        },
        'stock': {
            'label': 'Stock',
            'options': ['All', '172', '177', '247', '300']
        },
        'width': {
            'label': 'Width',
            'options': ['All', '53mm', '65mm', '78mm', '90mm']
        },
        'stock_category': {
            'label': 'Stock Category',
            'options': ['All', 'Drams', 'Tubes', 'Concentrate', 'Custom']
        }
    }
    
    filters, _ = render_filter_bar(filter_config)
    
    # KPI Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-value">94</div>
            <div class="kpi-label">Total Tickets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-value" style="color: #22C55E;">63</div>
            <div class="kpi-label">In Stock</div>
            <div class="kpi-delta positive">↑ 12% vs last week</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-value" style="color: #3B82F6;">25</div>
            <div class="kpi-label">Ordered</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-value" style="color: #EF4444;">6</div>
            <div class="kpi-label">Out of Stock</div>
            <div class="kpi-delta negative">↓ 3 items critical</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts row
    chart_col1, chart_col2 = st.columns([1, 2])
    
    with chart_col1:
        st.markdown("""
        <div class="section-header">
            <h3>Ticket Stock Status</h3>
            <span class="info-badge">Live</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Donut chart
        fig = go.Figure(data=[go.Pie(
            labels=['In', 'Ordered', 'Ordered Not Confirmed', 'Out'],
            values=[63, 19, 6, 6],
            hole=0.6,
            marker_colors=[
                CALYX_COLORS['status_in'],
                CALYX_COLORS['status_ordered'],
                CALYX_COLORS['status_ordered_not_confirmed'],
                CALYX_COLORS['status_out']
            ],
            textinfo='value',
            textfont_size=14,
            textfont_color='white'
        )])
        
        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            margin=dict(t=20, b=60, l=20, r=20),
            height=300,
            annotations=[dict(
                text='<b>94</b><br>Total',
                x=0.5, y=0.5,
                font_size=16,
                showarrow=False
            )]
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with chart_col2:
        st.markdown("""
        <div class="section-header">
            <h3>Stock Inventory Summary</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Sample inventory data
        inventory_df = pd.DataFrame({
            'Stock': ['172', '177', '247'],
            'In': [13, 13, 13],
            'Ordered': [0, 0, 0],
            'Out': [0, 0, 0]
        })
        
        fig = go.Figure()
        
        for col, color in [('In', CALYX_COLORS['status_in']), 
                           ('Ordered', CALYX_COLORS['status_ordered']),
                           ('Out', CALYX_COLORS['status_out'])]:
            fig.add_trace(go.Bar(
                name=col,
                y=inventory_df['Stock'],
                x=inventory_df[col],
                orientation='h',
                marker_color=color
            ))
        
        fig.update_layout(
            barmode='stack',
            height=250,
            margin=dict(t=10, b=30, l=50, r=20),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis_title="Count",
            yaxis_title=""
        )
        
        st.plotly_chart(fig, use_container_width=True)


def render_open_tickets_tab():
    """Render the Open Tickets tab with its specific filters."""
    # Tab-specific filters
    filter_config = {
        'facility': {
            'label': 'Facility',
            'options': ['All', 'Calyx Containers', 'Calyx West', 'Calyx East']
        },
        'ticket_status': {
            'label': 'Ticket Status',
            'options': ['All', 'Ordered', 'Out', 'In', 'Pending']
        },
        'date_range': {
            'label': 'Due Date Range',
            'options': ['All', 'Today', 'This Week', 'This Month', 'Overdue']
        }
    }
    
    filters, _ = render_filter_bar(filter_config)
    
    st.markdown("""
    <div class="section-header">
        <h3>Open Ticket Stock Detail</h3>
        <span class="info-badge">94 tickets</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Sample ticket data
    tickets_df = pd.DataFrame({
        'State': ['🔴', '🔴', '🔴', '🔴', '🔴', '🔴'],
        'Facility': ['Calyx Containers'] * 6,
        'Ticket': ['21995', '21995', '21820', '21820', '21819', '21819'],
        'Status': ['Ordered', 'Ordered', 'Out', 'Out', 'Out', 'Out'],
        'Due Date': ['02-Jan-2026', '02-Jan-2026', '03-Jan-2026', '03-Jan-2026', '03-Jan-2026', '03-Jan-2026'],
        'Task': ['EQUIP', 'PRESS', 'EQUIP', 'PRESS', 'EQUIP', 'PRESS'],
        'Planned': ['266/266', '177/177', '193/193', '247/247', '193/193', '247/247'],
        'Width': ['13/13'] * 6,
        'Stock Status': ['In', 'Ordered', 'In', 'Out', 'In', 'Out'],
        'Qty Required': [2657, 2657, 3869, 3869, 3869, 3869],
        'Remaining': [6260, 8638, 22855, 146, 26724, 146]
    })
    
    # Apply status styling
    def style_status(val):
        if val == 'In':
            return f'<span class="status-badge status-in">{val}</span>'
        elif val == 'Ordered':
            return f'<span class="status-badge status-ordered">{val}</span>'
        elif val == 'Out':
            return f'<span class="status-badge status-out">{val}</span>'
        return val
    
    st.dataframe(
        tickets_df,
        use_container_width=True,
        height=400,
        column_config={
            'State': st.column_config.TextColumn(width="small"),
            'Ticket': st.column_config.TextColumn(width="small"),
            'Qty Required': st.column_config.NumberColumn(format="%d"),
            'Remaining': st.column_config.NumberColumn(format="%d")
        }
    )


def render_purchase_orders_tab():
    """Render the Purchase Orders tab with its specific filters."""
    # Tab-specific filters
    filter_config = {
        'supplier': {
            'label': 'Supplier',
            'options': ['All', 'Primary Supplier', 'Secondary Supplier', 'International']
        },
        'date_range': {
            'label': 'Date Range',
            'options': ['This Week', 'This Month', 'This Quarter', 'All Time']
        },
        'stock_category': {
            'label': 'Category',
            'options': ['All', 'Drams', 'Tubes', 'Concentrate', 'Custom']
        }
    }
    
    filters, _ = render_filter_bar(filter_config)
    
    st.markdown("""
    <div class="section-header">
        <h3>Recommended Purchase Orders</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Sample PO recommendation data
    po_df = pd.DataFrame({
        'Facility': ['Calyx Containers'] * 4,
        'Stock': ['172', '177', '247', '300'],
        'Width': ['53mm', '65mm', '78mm', '90mm'],
        'Category': ['Drams', 'Drams', 'Drams', 'Tubes'],
        'Available Qty': [15000, 8500, 22000, 5200],
        'Min Qty Deficit': [0, 1500, 0, 2800],
        'Min Qty': [10000, 10000, 15000, 8000],
        'Max Qty': [50000, 50000, 75000, 40000],
        'Reorder Qty': [25000, 25000, 30000, 20000],
        'Total Order Qty': [0, 25000, 0, 20000],
        'Est. Arrival': ['-', '15-Jan-2026', '-', '18-Jan-2026']
    })
    
    st.dataframe(
        po_df,
        use_container_width=True,
        height=300,
        column_config={
            'Available Qty': st.column_config.NumberColumn(format="%d"),
            'Min Qty Deficit': st.column_config.NumberColumn(format="%d"),
            'Total Order Qty': st.column_config.NumberColumn(format="%d"),
        }
    )


# =============================================================================
# S&OP PLANNING VIEW
# =============================================================================
def render_sop_view():
    """Render the S&OP Planning section."""
    st.markdown("""
    <div class="main-header">
        <h1>S&OP Planning</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Try to import and render S&OP modules
    try:
        from src.sales_rep_view import render_sales_rep_view
        from src.operations_view import render_operations_view
        from src.scenario_planning import render_scenario_planning
        from src.po_forecast import render_po_forecast
        from src.deliveries_tracking import render_deliveries_tracking
        
        tabs = st.tabs([
            "📊 Sales Rep View",
            "🏭 Operations View", 
            "📈 Scenario Planning",
            "📦 PO Forecast",
            "🚚 Deliveries"
        ])
        
        with tabs[0]:
            render_sales_rep_view()
        with tabs[1]:
            render_operations_view()
        with tabs[2]:
            render_scenario_planning()
        with tabs[3]:
            render_po_forecast()
        with tabs[4]:
            render_deliveries_tracking()
            
    except ImportError as e:
        st.warning(f"S&OP modules not fully configured: {e}")
        st.info("Please ensure all src/ modules are properly installed.")


# =============================================================================
# QUALITY MANAGEMENT VIEW
# =============================================================================
def render_quality_view():
    """Render the Quality Management section."""
    st.markdown("""
    <div class="main-header">
        <h1>Quality Management</h1>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        from src.quality_section import render_quality_section
        render_quality_section()
    except ImportError as e:
        st.warning(f"Quality modules not fully configured: {e}")
        st.info("Please ensure all src/ modules are properly installed.")


# =============================================================================
# SETTINGS VIEW
# =============================================================================
def render_settings_view():
    """Render the Settings page."""
    st.markdown("""
    <div class="main-header">
        <h1>Settings</h1>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="kpi-card">
            <h4 style="margin-top: 0;">Data Connections</h4>
            <p style="color: #666;">Configure your data source connections.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.text_input("Google Sheet ID", value="15JhBZ_7aHHZA1W1qsoC2163borL6RYjk0xTDWPmWPfA")
        st.button("Test Connection")
    
    with col2:
        st.markdown("""
        <div class="kpi-card">
            <h4 style="margin-top: 0;">Cache Settings</h4>
            <p style="color: #666;">Manage data caching and refresh intervals.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.slider("Cache TTL (minutes)", 1, 60, 5)
        if st.button("Clear Cache"):
            st.cache_data.clear()
            st.success("Cache cleared!")


# =============================================================================
# MAIN APPLICATION
# =============================================================================
def main():
    """Main application entry point."""
    # Inject custom CSS
    inject_custom_css()
    
    # Render sidebar and get selection
    section = render_sidebar()
    
    # Route to appropriate view
    if section == "📊 Dashboard":
        render_dashboard_view()
    elif section == "📈 S&OP Planning":
        render_sop_view()
    elif section == "🎯 Quality Management":
        render_quality_view()
    elif section == "⚙️ Settings":
        render_settings_view()
    
    # Footer
    st.markdown("""
    <div style="
        text-align: center;
        padding: 2rem 0 1rem 0;
        color: #999;
        font-size: 0.75rem;
        border-top: 1px solid #eee;
        margin-top: 3rem;
    ">
        Calyx Containers Operations Dashboard v3.0 | 
        Built with Streamlit | 
        Data refreshes every 5 minutes
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
