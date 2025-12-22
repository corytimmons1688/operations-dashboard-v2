"""
Purchase Order Forecast Module for S&OP Dashboard
Plan purchase orders based on demand forecast and inventory requirements

Author: Xander @ Calyx Containers
Version: 3.1.0
Last Updated: 2025-12-22 15:50 MST
Changes: 
- Added extensive type safety and debugging
- Excludes items where Stock Item = No or blank from PO forecasting and cashflow
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
import traceback

logger = logging.getLogger(__name__)

# Version info for tracking deployments
VERSION = "3.1.0"
LAST_UPDATED = "2025-12-22 15:50 MST"


def safe_int(value, default=0):
    """Safely convert a value to integer."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return default
    if pd.isna(value):
        return default
    try:
        # Handle string numbers
        if isinstance(value, str):
            value = value.replace(',', '').replace('$', '').strip()
            if value == '' or value.lower() in ['nan', 'none', 'null']:
                return default
        return int(float(value))
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    """Safely convert a value to float."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return default
    if pd.isna(value):
        return default
    try:
        if isinstance(value, str):
            value = value.replace('$', '').replace(',', '').strip()
            if value == '' or value.lower() in ['nan', 'none', 'null']:
                return default
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_str(value, default=''):
    """Safely convert a value to string."""
    if value is None or pd.isna(value):
        return default
    return str(value).strip()


def get_column_as_series(df, col_name):
    """Safely get a column as a Series."""
    if df is None or col_name not in df.columns:
        return None
    result = df.loc[:, col_name]
    if isinstance(result, pd.DataFrame):
        return result.iloc[:, 0]
    return result


def find_column(df, keywords, exclude=None):
    """Find first column matching any keyword."""
    if df is None:
        return None
    exclude = exclude or []
    for col in df.columns:
        col_lower = str(col).lower()
        if any(kw in col_lower for kw in keywords):
            if not any(ex in col_lower for ex in exclude):
                return col
    return None


def render_po_forecast():
    """Render the Purchase Order Forecast view."""
    
    st.markdown("## 📦 Purchase Order Forecast")
    st.markdown("Plan purchase orders based on demand forecast and inventory requirements")
    
    # Show version info in expander
    with st.expander("ℹ️ Module Info", expanded=False):
        st.write(f"**Version:** {VERSION}")
        st.write(f"**Last Updated:** {LAST_UPDATED}")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 PO Schedule",
        "💰 Cash Flow Impact",
        "📊 SKU Analysis",
        "📤 Export"
    ])
    
    with tab1:
        render_po_schedule_tab()
    
    with tab2:
        render_cash_flow_tab()
    
    with tab3:
        render_sku_analysis_tab()
    
    with tab4:
        render_export_tab()


def render_po_schedule_tab():
    """Render Planned Purchase Order Schedule tab."""
    
    st.markdown("### 📋 Planned Purchase Order Schedule")
    st.markdown("*Note: Only includes items where Stock Item = Yes*")
    
    try:
        # Import with error handling
        try:
            from .sop_data_loader import (
                load_inventory, load_items, load_stock_items, get_topdown_item_forecast
            )
        except ImportError as e:
            st.error(f"Import error: {e}")
            st.code(traceback.format_exc())
            return
        
        # Load data with debugging
        st.write("Loading data...")
        
        try:
            inventory = load_inventory()
            st.write(f"✓ Inventory loaded: {len(inventory) if inventory is not None else 0} rows")
        except Exception as e:
            st.warning(f"Could not load inventory: {e}")
            inventory = None
        
        # Load STOCK ITEMS only (excludes Stock Item = No or blank)
        try:
            items = load_stock_items()
            st.write(f"✓ Stock Items loaded: {len(items) if items is not None else 0} rows (filtered to Stock Item = Yes)")
        except Exception as e:
            st.warning(f"Could not load stock items: {e}")
            items = None
        
        try:
            item_forecast = get_topdown_item_forecast()
            st.write(f"✓ Item forecast loaded: {len(item_forecast) if item_forecast is not None else 0} rows")
        except Exception as e:
            st.error(f"Could not load item forecast: {e}")
            st.code(traceback.format_exc())
            item_forecast = None
        
        if item_forecast is None or item_forecast.empty:
            st.info("No forecast data available. Configure the Revenue Forecast in the Operations view first.")
            return
        
        # Build set of stock item names for filtering
        stock_item_names = set()
        if items is not None and not items.empty:
            item_col = None
            for col in items.columns:
                if col.lower() in ['item', 'sku', 'name', 'item name']:
                    item_col = col
                    break
            if item_col:
                stock_item_names = set(items[item_col].astype(str).str.strip().tolist())
        
        st.write(f"Stock item names for filtering: {len(stock_item_names)} items")
        
        # Filter forecast to only include stock items
        if stock_item_names:
            original_count = len(item_forecast)
            item_forecast = item_forecast[item_forecast['Item'].astype(str).str.strip().isin(stock_item_names)].copy()
            st.write(f"Filtered forecast: {original_count} -> {len(item_forecast)} rows (stock items only)")
        
        if item_forecast.empty:
            st.info("No forecast data for stock items. Check that your items are marked as Stock Item = Yes in Raw_Items.")
            return
        
        # Show forecast columns for debugging
        with st.expander("Debug Info", expanded=False):
            st.write(f"Forecast columns: {list(item_forecast.columns)}")
            st.write(f"Forecast dtypes: {item_forecast.dtypes.to_dict()}")
        
        # Find columns
        inv_item_col = find_column(inventory, ['item', 'sku', 'name']) if inventory is not None else None
        inv_qty_col = find_column(inventory, ['qty', 'quantity', 'on hand', 'available']) if inventory is not None else None
        
        items_item_col = find_column(items, ['item', 'sku', 'name']) if items is not None else None
        lead_time_col = find_column(items, ['lead time', 'leadtime', 'lead_time']) if items is not None else None
        vendor_col = find_column(items, ['vendor', 'supplier']) if items is not None else None
        cost_col = find_column(items, ['cost', 'unit cost', 'price']) if items is not None else None
        
        # Build inventory lookup
        inventory_lookup = {}
        if inventory is not None and inv_item_col and inv_qty_col:
            inv_items = get_column_as_series(inventory, inv_item_col)
            inv_qty = get_column_as_series(inventory, inv_qty_col)
            if inv_items is not None and inv_qty is not None:
                for i, (item, qty) in enumerate(zip(inv_items, inv_qty)):
                    if pd.notna(item):
                        inventory_lookup[safe_str(item)] = safe_int(qty)
        
        # Build items lookup (lead time, vendor, cost)
        items_lookup = {}
        if items is not None and items_item_col:
            for idx, row in items.iterrows():
                try:
                    item_name = row.get(items_item_col) if items_item_col else None
                    if pd.notna(item_name):
                        item_key = safe_str(item_name)
                        items_lookup[item_key] = {
                            'lead_time': safe_int(row.get(lead_time_col, 30) if lead_time_col else 30, 30),
                            'vendor': safe_str(row.get(vendor_col, 'Unknown') if vendor_col else 'Unknown', 'Unknown'),
                            'cost': safe_float(row.get(cost_col, 0) if cost_col else 0, 0)
                        }
                except Exception as e:
                    continue
        
        # Calculate PO requirements
        po_schedule = []
        errors = []
        
        for idx, row in item_forecast.iterrows():
            try:
                # Extract values with safe conversion
                item = safe_str(row.get('Item', ''))
                category = safe_str(row.get('Category', ''))
                period = safe_str(row.get('Period', ''))
                forecast_units = safe_int(row.get('Forecast_Units', 0))
                forecast_revenue = safe_float(row.get('Forecast_Revenue', 0))
                
                if not item or forecast_units <= 0:
                    continue
                
                # Get current inventory (safe)
                current_inventory = safe_int(inventory_lookup.get(item, 0))
                
                # Get item details (safe)
                item_info = items_lookup.get(item, {
                    'lead_time': 30,
                    'vendor': 'Unknown',
                    'cost': 0.0
                })
                
                # Calculate net requirement (all ints now)
                net_requirement = max(0, forecast_units - current_inventory)
                
                # Calculate order date based on lead time
                try:
                    if '-' in period:
                        parts = period.split('-')
                        if len(parts) == 2:
                            year = safe_int(parts[0], datetime.now().year)
                            month = safe_int(parts[1], 1)
                            if month < 1:
                                month = 1
                            if month > 12:
                                month = 12
                            need_date = datetime(year, month, 1)
                        else:
                            need_date = datetime.now() + timedelta(days=30)
                    else:
                        need_date = datetime.now() + timedelta(days=30)
                except Exception:
                    need_date = datetime.now() + timedelta(days=30)
                
                # Calculate order date (need_date - lead_time)
                lead_time_days = safe_int(item_info.get('lead_time', 30), 30)
                order_date = need_date - timedelta(days=lead_time_days)
                
                # Calculate PO value (all floats now)
                unit_cost = safe_float(item_info.get('cost', 0), 0)
                po_value = float(net_requirement) * float(unit_cost)
                
                if net_requirement > 0:
                    po_schedule.append({
                        'Item': item,
                        'Category': category,
                        'Period': period,
                        'Forecast Units': int(forecast_units),
                        'Current Inventory': int(current_inventory),
                        'Net Requirement': int(net_requirement),
                        'Lead Time (Days)': int(lead_time_days),
                        'Order Date': order_date.strftime('%Y-%m-%d'),
                        'Need Date': need_date.strftime('%Y-%m-%d'),
                        'Vendor': safe_str(item_info.get('vendor', 'Unknown'), 'Unknown'),
                        'Unit Cost': float(unit_cost),
                        'PO Value': float(po_value)
                    })
                    
            except Exception as e:
                errors.append(f"Row {idx}: {e}")
                continue
        
        if errors:
            with st.expander(f"⚠️ {len(errors)} rows had errors", expanded=False):
                for err in errors[:20]:
                    st.write(err)
        
        if not po_schedule:
            st.info("No purchase orders needed based on current forecast and inventory levels.")
            return
        
        po_df = pd.DataFrame(po_schedule)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total PO Lines", f"{len(po_df):,}")
        with col2:
            total_units = po_df['Net Requirement'].sum()
            st.metric("Total Units", f"{total_units:,.0f}")
        with col3:
            total_value = po_df['PO Value'].sum()
            st.metric("Total PO Value", f"${total_value:,.0f}")
        with col4:
            unique_items = po_df['Item'].nunique()
            st.metric("Unique Items", f"{unique_items}")
        
        # Format display
        display_df = po_df.copy()
        display_df['Unit Cost'] = display_df['Unit Cost'].apply(lambda x: f"${x:,.2f}" if x > 0 else "-")
        display_df['PO Value'] = display_df['PO Value'].apply(lambda x: f"${x:,.0f}" if x > 0 else "-")
        display_df['Net Requirement'] = display_df['Net Requirement'].apply(lambda x: f"{x:,.0f}")
        display_df['Forecast Units'] = display_df['Forecast Units'].apply(lambda x: f"{x:,.0f}")
        display_df['Current Inventory'] = display_df['Current Inventory'].apply(lambda x: f"{x:,.0f}")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)
        
        # Timeline chart
        st.markdown("### 📅 Order Timeline")
        
        timeline_df = po_df.groupby('Order Date')['PO Value'].sum().reset_index()
        timeline_df = timeline_df.sort_values('Order Date')
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=timeline_df['Order Date'],
            y=timeline_df['PO Value'],
            marker_color='#0033A1',
            hovertemplate='<b>Order Date</b>: %{x}<br><b>PO Value</b>: $%{y:,.0f}<extra></extra>'
        ))
        fig.update_layout(
            title='Purchase Order Value by Order Date',
            xaxis_title='Order Date',
            yaxis_title='PO Value ($)',
            height=400
        )
        fig.update_yaxes(tickformat='$,.0f')
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error generating PO schedule: {str(e)}")
        st.code(traceback.format_exc())


def render_cash_flow_tab():
    """Render Cash Flow Impact tab."""
    
    st.markdown("### 💰 Cash Flow Impact")
    st.markdown("*Note: Only includes items where Stock Item = Yes*")
    
    try:
        from .sop_data_loader import load_stock_items, get_topdown_item_forecast
        
        items = load_stock_items()  # Use stock items only
        item_forecast = get_topdown_item_forecast()
        
        if item_forecast is None or item_forecast.empty:
            st.info("No forecast data available.")
            return
        
        # Build set of stock item names for filtering
        stock_item_names = set()
        if items is not None and not items.empty:
            item_col = None
            for col in items.columns:
                if col.lower() in ['item', 'sku', 'name', 'item name']:
                    item_col = col
                    break
            if item_col:
                stock_item_names = set(items[item_col].astype(str).str.strip().tolist())
        
        # Filter forecast to only include stock items
        if stock_item_names:
            item_forecast = item_forecast[item_forecast['Item'].astype(str).str.strip().isin(stock_item_names)].copy()
        
        if item_forecast.empty:
            st.info("No forecast data for stock items.")
            return
        
        # Find cost column in items
        items_item_col = find_column(items, ['item', 'sku', 'name']) if items is not None else None
        cost_col = find_column(items, ['cost', 'unit cost', 'price']) if items is not None else None
        
        # Build cost lookup
        cost_lookup = {}
        if items is not None and items_item_col and cost_col:
            for _, row in items.iterrows():
                item_name = row.get(items_item_col)
                if pd.notna(item_name):
                    cost_lookup[safe_str(item_name)] = safe_float(row.get(cost_col, 0))
        
        # Calculate cash requirements by period
        cash_by_period = []
        
        for _, row in item_forecast.iterrows():
            item = safe_str(row.get('Item', ''))
            period = safe_str(row.get('Period', ''))
            forecast_units = safe_int(row.get('Forecast_Units', 0))
            
            unit_cost = safe_float(cost_lookup.get(item, 0))
            cash_required = float(forecast_units) * float(unit_cost)
            
            cash_by_period.append({
                'Period': period,
                'Cash Required': cash_required
            })
        
        cash_df = pd.DataFrame(cash_by_period)
        cash_summary = cash_df.groupby('Period')['Cash Required'].sum().reset_index()
        cash_summary = cash_summary.sort_values('Period')
        
        # Cumulative cash flow
        cash_summary['Cumulative'] = cash_summary['Cash Required'].cumsum()
        
        # Chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=cash_summary['Period'],
            y=cash_summary['Cash Required'],
            name='Period Cash Requirement',
            marker_color='#0033A1',
            hovertemplate='<b>Period</b>: %{x}<br><b>Cash Required</b>: $%{y:,.0f}<extra></extra>'
        ))
        
        fig.add_trace(go.Scatter(
            x=cash_summary['Period'],
            y=cash_summary['Cumulative'],
            name='Cumulative',
            mode='lines+markers',
            line=dict(color='#F59E0B', width=3),
            hovertemplate='<b>Period</b>: %{x}<br><b>Cumulative</b>: $%{y:,.0f}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Cash Flow Requirements by Period',
            xaxis_title='Period',
            yaxis_title='Amount ($)',
            height=450,
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        fig.update_yaxes(tickformat='$,.0f')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Cash Required", f"${cash_summary['Cash Required'].sum():,.0f}")
        with col2:
            avg_per_period = cash_summary['Cash Required'].mean()
            st.metric("Average per Period", f"${avg_per_period:,.0f}")
        
        st.dataframe(cash_summary, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"Error calculating cash flow: {str(e)}")
        st.code(traceback.format_exc())


def render_sku_analysis_tab():
    """Render SKU Analysis tab."""
    
    st.markdown("### 📊 SKU Analysis")
    
    try:
        from .sop_data_loader import get_topdown_item_forecast
        
        item_forecast = get_topdown_item_forecast()
        
        if item_forecast is None or item_forecast.empty:
            st.info("No forecast data available.")
            return
        
        # Aggregate by SKU
        sku_summary = item_forecast.groupby(['Item', 'Category']).agg({
            'Forecast_Units': 'sum',
            'Forecast_Revenue': 'sum',
            'Period': 'count'
        }).reset_index()
        sku_summary.columns = ['Item', 'Category', 'Total Units', 'Total Revenue', 'Periods']
        sku_summary = sku_summary.sort_values('Total Revenue', ascending=False)
        
        # Top 20 chart
        top_20 = sku_summary.head(20)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=top_20['Item'],
            y=top_20['Total Revenue'],
            marker_color='#0033A1',
            hovertemplate='<b>%{x}</b><br>Revenue: $%{y:,.0f}<extra></extra>'
        ))
        fig.update_layout(
            title='Top 20 SKUs by Forecasted Revenue',
            xaxis_title='Item',
            yaxis_title='Forecasted Revenue ($)',
            height=450
        )
        fig.update_xaxes(tickangle=45)
        fig.update_yaxes(tickformat='$,.0f')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Format display
        display_df = sku_summary.copy()
        display_df['Total Revenue'] = display_df['Total Revenue'].apply(lambda x: f"${x:,.0f}")
        display_df['Total Units'] = display_df['Total Units'].apply(lambda x: f"{x:,.0f}")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)
        
    except Exception as e:
        st.error(f"Error in SKU analysis: {str(e)}")
        st.code(traceback.format_exc())


def render_export_tab():
    """Render Export tab."""
    
    st.markdown("### 📤 Export Data")
    
    try:
        from .sop_data_loader import get_topdown_item_forecast
        
        item_forecast = get_topdown_item_forecast()
        
        if item_forecast is None or item_forecast.empty:
            st.info("No forecast data available to export.")
            return
        
        st.markdown("Download forecast data for further analysis or import into other systems.")
        
        # Convert to CSV
        csv = item_forecast.to_csv(index=False)
        
        st.download_button(
            label="📥 Download Forecast CSV",
            data=csv,
            file_name=f"po_forecast_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
        st.markdown("---")
        st.markdown("**Data Preview:**")
        st.dataframe(item_forecast.head(50), use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"Error preparing export: {str(e)}")
        st.code(traceback.format_exc())
