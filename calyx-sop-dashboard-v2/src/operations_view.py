"""
Operations/Supply Chain View Module for S&OP Dashboard
Demand planning, pipeline analysis, and coverage tracking

Author: Xander @ Calyx Containers
Version: 4.2.0 - Added Deals Pipeline by Category
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Default ASP (Average Selling Price) by category for unit conversion
DEFAULT_ASP = {
    'Calyx Cure': 2.50,  # Update with actual ASP
    'Plastic Lids': 0.15,
    'Plastic Bases': 0.20,
    'Glass Bases': 0.75,
    'Shrink Bands': 0.02,
    'Tray Inserts': 0.35,
    'Tray Frames': 1.25,
    'Tubes': 0.45,
}

# =============================================================================
# SETTINGS STORAGE (Session State)
# =============================================================================

def init_settings():
    """Initialize settings in session state if not present."""
    if 'ops_case_quantities' not in st.session_state:
        st.session_state.ops_case_quantities = {
            'Calyx Cure': 1,
            'Plastic Lids': 1000,
            'Plastic Bases': 1000,
            'Glass Bases': 100,
            'Shrink Bands': 5000,
            'Tray Inserts': 100,
            'Tray Frames': 50,
            'Tubes': 500,
        }
    
    if 'ops_item_consolidation' not in st.session_state:
        st.session_state.ops_item_consolidation = {}
    
    if 'ops_asp_overrides' not in st.session_state:
        st.session_state.ops_asp_overrides = DEFAULT_ASP.copy()


def get_asp_for_category(category):
    """Get ASP for a category (from settings or default)."""
    init_settings()
    return st.session_state.ops_asp_overrides.get(category, DEFAULT_ASP.get(category, 1.0))


# =============================================================================
# DATA LOADING FUNCTIONS
# =============================================================================

@st.cache_data(ttl=300)
def load_raw_items(spreadsheet_id, creds_dict):
    """Load Raw_Items tab for SKU to Category mapping."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(spreadsheet_id)
        
        worksheet = spreadsheet.worksheet('Raw_Items')
        data = worksheet.get_all_values()
        
        if len(data) < 2:
            return pd.DataFrame()
        
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
        
    except Exception as e:
        logger.error(f"Error loading Raw_Items: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_deals_data(spreadsheet_id, creds_dict):
    """
    Load Deals tab data.
    Headers are in row 2 (index 1).
    Column D = Close Date
    Column O = SKU
    """
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(spreadsheet_id)
        
        worksheet = spreadsheet.worksheet('Deals')
        data = worksheet.get_all_values()
        
        if len(data) < 3:
            return pd.DataFrame()
        
        # Headers are in row 2 (index 1), data starts row 3 (index 2+)
        headers = data[1]
        df = pd.DataFrame(data[2:], columns=headers)
        
        return df
        
    except Exception as e:
        logger.error(f"Error loading Deals: {e}")
        return pd.DataFrame()


def get_sku_category_map(raw_items_df):
    """
    Create mapping of SKU -> Category from Raw_Items.
    Uses 'SKU' column and 'Calyx Product Type' (or 'Product Type' or 'Category') column.
    """
    if raw_items_df is None or raw_items_df.empty:
        return {}
    
    # Find SKU column
    sku_col = None
    for col in raw_items_df.columns:
        if col.strip().upper() == 'SKU':
            sku_col = col
            break
    
    if sku_col is None:
        logger.warning("Could not find 'SKU' column in Raw_Items")
        return {}
    
    # Find Category column (priority order)
    category_col = None
    priority_names = ['Calyx Product Type', 'Calyx || Product Type', 'Product Type', 'Category', 'Type']
    
    for priority_name in priority_names:
        for col in raw_items_df.columns:
            if priority_name.lower() in col.lower():
                category_col = col
                break
        if category_col:
            break
    
    if category_col is None:
        logger.warning("Could not find category column in Raw_Items")
        return {}
    
    # Build mapping
    mapping = {}
    for _, row in raw_items_df.iterrows():
        sku = str(row.get(sku_col, '')).strip()
        category = str(row.get(category_col, '')).strip()
        if sku and category:
            mapping[sku] = category
    
    logger.info(f"Built SKU->Category map with {len(mapping)} entries")
    return mapping


def get_deals_pipeline_by_category(deals_df, sku_category_map, target_category='Calyx Cure'):
    """
    Process Deals data to get pipeline amounts by period for a specific category.
    
    Args:
        deals_df: DataFrame from Deals tab
        sku_category_map: Dict mapping SKU -> Category
        target_category: Category to filter for (default: 'Calyx Cure')
    
    Returns:
        DataFrame with columns: [period, amount, units]
    
    Logic:
        - Column O (index 14) = SKU
        - Column D (index 3) = Close Date (expected date of demand)
        - Look up SKU in Raw_Items to find category
        - Only include rows where category matches target_category
        - Exclude rows where SKU or Close Date is blank
    """
    if deals_df is None or deals_df.empty:
        return pd.DataFrame(columns=['period', 'amount', 'units'])
    
    # Find relevant columns
    # Try to find by column name first, then fall back to position
    
    # SKU Column (Column O = index 14, but also search by name)
    sku_col = None
    sku_search_names = ['SKU', 'New Design SKU', 'Item', 'Product']
    for name in sku_search_names:
        if name in deals_df.columns:
            sku_col = name
            break
    
    # If not found by name, use column O (index 14)
    if sku_col is None and len(deals_df.columns) > 14:
        sku_col = deals_df.columns[14]
        logger.info(f"Using column index 14 for SKU: '{sku_col}'")
    
    # Close Date Column (Column D = index 3)
    date_col = None
    date_search_names = ['Close Date', 'Expected Close Date', 'close_date']
    for name in date_search_names:
        if name in deals_df.columns:
            date_col = name
            break
    
    if date_col is None and len(deals_df.columns) > 3:
        date_col = deals_df.columns[3]
        logger.info(f"Using column index 3 for Close Date: '{date_col}'")
    
    # Amount Column
    amount_col = None
    amount_search_names = ['Amount', 'Deal Amount', 'Total', 'Value']
    for name in amount_search_names:
        if name in deals_df.columns:
            amount_col = name
            break
    
    if sku_col is None or date_col is None or amount_col is None:
        logger.error(f"Missing required columns. SKU: {sku_col}, Date: {date_col}, Amount: {amount_col}")
        return pd.DataFrame(columns=['period', 'amount', 'units'])
    
    logger.info(f"Using columns - SKU: '{sku_col}', Date: '{date_col}', Amount: '{amount_col}'")
    
    # Process data
    processed_rows = []
    
    for idx, row in deals_df.iterrows():
        sku = str(row.get(sku_col, '')).strip()
        close_date_raw = row.get(date_col, '')
        amount_raw = row.get(amount_col, '')
        
        # Skip if SKU or Close Date is blank
        if not sku or sku.lower() in ['', 'nan', 'none']:
            continue
        if not close_date_raw or str(close_date_raw).strip() == '':
            continue
        
        # Look up category from SKU
        category = sku_category_map.get(sku, '')
        
        # Filter to target category only
        if category.lower() != target_category.lower():
            continue
        
        # Parse close date
        try:
            if isinstance(close_date_raw, str):
                # Handle various date formats
                close_date_str = close_date_raw.strip()
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S']:
                    try:
                        close_date = pd.to_datetime(close_date_str, format=fmt)
                        break
                    except:
                        continue
                else:
                    close_date = pd.to_datetime(close_date_str, errors='coerce')
            else:
                close_date = pd.to_datetime(close_date_raw, errors='coerce')
            
            if pd.isna(close_date):
                continue
                
        except Exception as e:
            logger.debug(f"Could not parse date '{close_date_raw}': {e}")
            continue
        
        # Parse amount
        try:
            if isinstance(amount_raw, str):
                amount = float(amount_raw.replace('$', '').replace(',', '').strip())
            else:
                amount = float(amount_raw)
        except:
            amount = 0.0
        
        if amount <= 0:
            continue
        
        # Get period (start of month)
        period = close_date.to_period('M').to_timestamp()
        
        processed_rows.append({
            'period': period,
            'amount': amount,
            'sku': sku,
            'category': category
        })
    
    if not processed_rows:
        logger.warning(f"No deals found for category '{target_category}'")
        return pd.DataFrame(columns=['period', 'amount', 'units'])
    
    df = pd.DataFrame(processed_rows)
    
    # Aggregate by period
    agg_df = df.groupby('period').agg({
        'amount': 'sum'
    }).reset_index()
    
    # Calculate units based on ASP
    asp = get_asp_for_category(target_category)
    agg_df['units'] = (agg_df['amount'] / asp).round(0).astype(int)
    
    logger.info(f"Processed {len(processed_rows)} deals for '{target_category}', aggregated to {len(agg_df)} periods")
    
    return agg_df.sort_values('period')


# =============================================================================
# CHART BUILDING
# =============================================================================

def add_deals_pipeline_to_chart(fig, deals_pipeline_df, show_units=False):
    """
    Add Deals Pipeline trace to an existing Plotly figure.
    
    Args:
        fig: Existing Plotly figure
        deals_pipeline_df: DataFrame with columns [period, amount, units]
        show_units: If True, show units; if False, show amount (dollars)
    """
    if deals_pipeline_df is None or deals_pipeline_df.empty:
        logger.warning("No deals pipeline data to add to chart")
        return fig
    
    y_col = 'units' if show_units else 'amount'
    y_label = 'Deals Pipeline (Units)' if show_units else 'Deals Pipeline ($)'
    
    fig.add_trace(go.Scatter(
        x=deals_pipeline_df['period'],
        y=deals_pipeline_df[y_col],
        mode='lines+markers',
        name=y_label,
        line=dict(
            color='#FF6B6B',  # Coral red for visibility
            width=2,
            dash='dot'
        ),
        marker=dict(
            size=8,
            symbol='diamond'
        ),
        hovertemplate=(
            f'<b>{y_label}</b><br>'
            'Period: %{x|%b %Y}<br>'
            + ('Units: %{y:,.0f}' if show_units else 'Amount: $%{y:,.0f}')
            + '<extra></extra>'
        )
    ))
    
    return fig


def create_demand_pipeline_chart(
    historical_demand_df,
    forecast_df,
    pipeline_df,
    revenue_plan_df,
    deals_pipeline_df=None,
    show_units=True,
    category_name='All Categories'
):
    """
    Create the main Demand vs Pipeline overlay chart with optional Deals Pipeline line.
    
    Args:
        historical_demand_df: Historical demand data
        forecast_df: Demand forecast data
        pipeline_df: Original pipeline data (if any)
        revenue_plan_df: Top-down revenue plan
        deals_pipeline_df: NEW - Deals pipeline filtered by category
        show_units: Whether to show units or dollars
        category_name: Name of category for title
    """
    fig = go.Figure()
    
    y_suffix = 'Units' if show_units else '$'
    
    # 1. Historical Demand (blue bars)
    if historical_demand_df is not None and not historical_demand_df.empty:
        y_col = 'quantity' if 'quantity' in historical_demand_df.columns else 'amount'
        fig.add_trace(go.Bar(
            x=historical_demand_df['period'],
            y=historical_demand_df[y_col],
            name='Historical Demand',
            marker_color='#4285F4',
            opacity=0.7,
            hovertemplate=(
                '<b>Historical Demand</b><br>'
                'Period: %{x|%b %Y}<br>'
                f'{y_suffix}: %{{y:,.0f}}'
                '<extra></extra>'
            )
        ))
    
    # 2. Demand Forecast (green dashed line with CI band)
    if forecast_df is not None and not forecast_df.empty:
        y_col = 'yhat' if 'yhat' in forecast_df.columns else 'forecast'
        
        # Confidence interval band
        if 'yhat_lower' in forecast_df.columns and 'yhat_upper' in forecast_df.columns:
            fig.add_trace(go.Scatter(
                x=pd.concat([forecast_df['ds'], forecast_df['ds'][::-1]]),
                y=pd.concat([forecast_df['yhat_upper'], forecast_df['yhat_lower'][::-1]]),
                fill='toself',
                fillcolor='rgba(52, 168, 83, 0.15)',
                line=dict(color='rgba(255,255,255,0)'),
                name='Forecast CI (85%)',
                showlegend=True,
                hoverinfo='skip'
            ))
        
        fig.add_trace(go.Scatter(
            x=forecast_df['ds'],
            y=forecast_df[y_col],
            mode='lines+markers',
            name='Demand Forecast',
            line=dict(color='#34A853', width=2, dash='dash'),
            marker=dict(size=6),
            hovertemplate=(
                '<b>Demand Forecast</b><br>'
                'Period: %{x|%b %Y}<br>'
                f'{y_suffix}: %{{y:,.0f}}'
                '<extra></extra>'
            )
        ))
    
    # 3. Revenue Plan / Top-Down (purple line with stars)
    if revenue_plan_df is not None and not revenue_plan_df.empty:
        y_col = 'amount' if 'amount' in revenue_plan_df.columns else 'revenue'
        fig.add_trace(go.Scatter(
            x=revenue_plan_df['period'],
            y=revenue_plan_df[y_col],
            mode='lines+markers',
            name='Revenue Plan (Top-Down)',
            line=dict(color='#9C27B0', width=2),
            marker=dict(size=8, symbol='star'),
            hovertemplate=(
                '<b>Revenue Plan (Top-Down)</b><br>'
                'Period: %{x|%b %Y}<br>'
                f'{y_suffix}: %{{y:,.0f}}'
                '<extra></extra>'
            )
        ))
    
    # 4. Deals Pipeline (NEW - coral red dotted line with diamonds)
    if deals_pipeline_df is not None and not deals_pipeline_df.empty:
        y_col = 'units' if show_units else 'amount'
        y_label = 'Deals Pipeline (Units)' if show_units else 'Deals Pipeline ($)'
        
        fig.add_trace(go.Scatter(
            x=deals_pipeline_df['period'],
            y=deals_pipeline_df[y_col],
            mode='lines+markers',
            name=y_label,
            line=dict(
                color='#FF6B6B',
                width=2,
                dash='dot'
            ),
            marker=dict(
                size=8,
                symbol='diamond'
            ),
            hovertemplate=(
                f'<b>{y_label}</b><br>'
                'Period: %{x|%b %Y}<br>'
                + ('Units: %{y:,.0f}' if show_units else 'Amount: $%{y:,.0f}')
                + '<extra></extra>'
            )
        ))
    
    # Layout
    fig.update_layout(
        title=dict(
            text=f'Demand & Pipeline Overlay - {category_name}',
            font=dict(size=18)
        ),
        xaxis=dict(
            title='Period',
            tickformat='%b %Y',
            dtick='M1'
        ),
        yaxis=dict(
            title=f'Revenue ({y_suffix})',
            tickformat='$,.0f' if not show_units else ',.0f'
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        hovermode='x unified',
        height=500,
        margin=dict(t=80, b=60)
    )
    
    return fig


# =============================================================================
# MAIN RENDER FUNCTION
# =============================================================================

def render_operations_view():
    """Main render function for Operations/Supply Chain View tab."""
    
    st.markdown("## 📦 Operations & Supply Chain View")
    st.markdown("Demand planning, pipeline analysis, and coverage tracking")
    
    # Initialize settings
    init_settings()
    
    # Check for credentials
    if "gcp_service_account" not in st.secrets:
        st.error("❌ Missing Google Cloud credentials in secrets")
        return
    
    creds_dict = dict(st.secrets["gcp_service_account"])
    spreadsheet_id = st.secrets.get("spreadsheet_id", "")
    
    if not spreadsheet_id:
        st.error("❌ Missing spreadsheet_id in secrets")
        return
    
    # Load data
    with st.spinner("Loading data..."):
        raw_items_df = load_raw_items(spreadsheet_id, creds_dict)
        deals_df = load_deals_data(spreadsheet_id, creds_dict)
        sku_category_map = get_sku_category_map(raw_items_df)
    
    # Sidebar filters
    st.sidebar.markdown("### 🔧 Filters")
    
    # Category selection
    available_categories = sorted(set(sku_category_map.values())) if sku_category_map else ['Calyx Cure']
    if 'Calyx Cure' in available_categories:
        default_idx = available_categories.index('Calyx Cure')
    else:
        default_idx = 0
    
    selected_category = st.sidebar.selectbox(
        "Category",
        options=available_categories,
        index=default_idx
    )
    
    # Show units vs dollars toggle
    show_units = st.sidebar.checkbox("Show Units (vs Dollars)", value=False)
    
    # ASP override for selected category
    current_asp = get_asp_for_category(selected_category)
    new_asp = st.sidebar.number_input(
        f"ASP for {selected_category} ($)",
        min_value=0.01,
        max_value=1000.0,
        value=float(current_asp),
        step=0.01,
        help="Average Selling Price used to convert dollars to units"
    )
    
    if new_asp != current_asp:
        st.session_state.ops_asp_overrides[selected_category] = new_asp
        st.rerun()
    
    # Get Deals Pipeline data for selected category
    deals_pipeline_df = get_deals_pipeline_by_category(
        deals_df, 
        sku_category_map, 
        target_category=selected_category
    )
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if not deals_pipeline_df.empty:
            total_pipeline = deals_pipeline_df['amount'].sum()
            st.metric("Deals Pipeline Total", f"${total_pipeline:,.0f}")
        else:
            st.metric("Deals Pipeline Total", "$0")
    
    with col2:
        if not deals_pipeline_df.empty:
            total_units = deals_pipeline_df['units'].sum()
            st.metric("Pipeline Units", f"{total_units:,.0f}")
        else:
            st.metric("Pipeline Units", "0")
    
    with col3:
        deal_count = len(deals_df) if deals_df is not None else 0
        matched_count = len(deals_pipeline_df) if not deals_pipeline_df.empty else 0
        st.metric("Deals Matched", f"{matched_count} periods")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📈 Demand vs Pipeline", "📊 Deals Detail", "⚙️ Settings"])
    
    with tab1:
        # For now, create chart with just the deals pipeline
        # In full implementation, you'd load historical demand and forecast here too
        
        st.markdown(f"### Demand & Pipeline - {selected_category}")
        
        if deals_pipeline_df.empty:
            st.warning(f"No deals found for category '{selected_category}'. Check that:")
            st.markdown("""
            - Column O (SKU) is populated in the Deals tab
            - Column D (Close Date) is populated
            - SKU exists in Raw_Items with matching category
            """)
        else:
            # Create chart with deals pipeline
            fig = create_demand_pipeline_chart(
                historical_demand_df=None,  # Load from your data source
                forecast_df=None,  # Load from your forecast
                pipeline_df=None,  # Original pipeline if any
                revenue_plan_df=None,  # Load from your top-down
                deals_pipeline_df=deals_pipeline_df,
                show_units=show_units,
                category_name=selected_category
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Data table
            with st.expander("📋 View Pipeline Data"):
                display_df = deals_pipeline_df.copy()
                display_df['period'] = display_df['period'].dt.strftime('%b %Y')
                display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:,.0f}")
                display_df['units'] = display_df['units'].apply(lambda x: f"{x:,.0f}")
                display_df.columns = ['Period', 'Amount ($)', 'Units']
                st.dataframe(display_df, use_container_width=True)
    
    with tab2:
        st.markdown("### 📊 Deals Detail")
        
        if deals_df is not None and not deals_df.empty:
            # Show raw deals data with category mapping
            st.markdown(f"**Showing deals for: {selected_category}**")
            
            # Filter deals for display
            display_deals = []
            
            # Find column names
            sku_col = None
            for name in ['SKU', 'New Design SKU', 'Item']:
                if name in deals_df.columns:
                    sku_col = name
                    break
            if sku_col is None and len(deals_df.columns) > 14:
                sku_col = deals_df.columns[14]
            
            date_col = None
            for name in ['Close Date', 'Expected Close Date']:
                if name in deals_df.columns:
                    date_col = name
                    break
            if date_col is None and len(deals_df.columns) > 3:
                date_col = deals_df.columns[3]
            
            amount_col = None
            for name in ['Amount', 'Deal Amount', 'Total']:
                if name in deals_df.columns:
                    amount_col = name
                    break
            
            deal_name_col = None
            for name in ['Deal Name', 'Name', 'Opportunity']:
                if name in deals_df.columns:
                    deal_name_col = name
                    break
            
            if sku_col and date_col:
                for _, row in deals_df.iterrows():
                    sku = str(row.get(sku_col, '')).strip()
                    category = sku_category_map.get(sku, 'Unknown')
                    
                    if category.lower() == selected_category.lower():
                        display_deals.append({
                            'Deal Name': row.get(deal_name_col, '') if deal_name_col else '',
                            'SKU': sku,
                            'Close Date': row.get(date_col, ''),
                            'Amount': row.get(amount_col, '') if amount_col else '',
                            'Category': category
                        })
                
                if display_deals:
                    st.dataframe(pd.DataFrame(display_deals), use_container_width=True)
                else:
                    st.info(f"No deals found matching category '{selected_category}'")
            else:
                st.warning("Could not identify SKU or Close Date columns in Deals tab")
                
            # Debug info
            with st.expander("🔧 Debug Info"):
                st.write(f"**Deals columns found:** {list(deals_df.columns)}")
                st.write(f"**SKU column used:** {sku_col}")
                st.write(f"**Date column used:** {date_col}")
                st.write(f"**Amount column used:** {amount_col}")
                st.write(f"**Total deals loaded:** {len(deals_df)}")
                st.write(f"**SKU->Category mappings:** {len(sku_category_map)}")
                
                # Sample SKUs from mapping
                sample_skus = list(sku_category_map.items())[:10]
                st.write(f"**Sample SKU mappings:** {sample_skus}")
        else:
            st.warning("No deals data loaded")
    
    with tab3:
        st.markdown("### ⚙️ Settings")
        
        # ASP Settings
        st.markdown("#### Average Selling Price (ASP) by Category")
        st.markdown("Used to convert pipeline dollars to units for PO forecasting")
        
        asp_data = []
        for cat, asp in st.session_state.ops_asp_overrides.items():
            asp_data.append({'Category': cat, 'ASP ($)': asp})
        
        asp_df = pd.DataFrame(asp_data)
        edited_asp = st.data_editor(
            asp_df,
            use_container_width=True,
            num_rows="fixed",
            column_config={
                "Category": st.column_config.TextColumn("Category", disabled=True),
                "ASP ($)": st.column_config.NumberColumn("ASP ($)", min_value=0.01, format="$%.2f")
            }
        )
        
        # Update ASP values if changed
        for _, row in edited_asp.iterrows():
            cat = row['Category']
            asp = row['ASP ($)']
            if st.session_state.ops_asp_overrides.get(cat) != asp:
                st.session_state.ops_asp_overrides[cat] = asp


# =============================================================================
# STANDALONE FUNCTION FOR INTEGRATION
# =============================================================================

def get_deals_pipeline_for_chart(spreadsheet_id, creds_dict, category='Calyx Cure'):
    """
    Standalone function to get deals pipeline data for integration with existing charts.
    
    Returns DataFrame with columns: [period, amount, units]
    """
    raw_items_df = load_raw_items(spreadsheet_id, creds_dict)
    deals_df = load_deals_data(spreadsheet_id, creds_dict)
    sku_category_map = get_sku_category_map(raw_items_df)
    
    return get_deals_pipeline_by_category(deals_df, sku_category_map, target_category=category)


if __name__ == "__main__":
    st.set_page_config(page_title="Operations View", layout="wide")
    render_operations_view()
