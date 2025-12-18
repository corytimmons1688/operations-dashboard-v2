"""
S&OP Data Loader Module
Handles loading and processing data from Google Sheets for S&OP Dashboard

Features:
- Loads Invoice Lines, Sales Orders, Items, Customers, Deals
- Properly maps 'Calyx || Product Type' column from Raw_Items
- Handles duplicate column names
- Provides data preparation functions

Author: Xander @ Calyx Containers
Version: 3.1.0
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
import logging
import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

# =============================================================================
# GOOGLE SHEETS CONNECTION
# =============================================================================

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

@st.cache_resource
def get_google_sheets_client():
    """Get authenticated Google Sheets client."""
    try:
        # Try different secret formats
        if 'service_account' in st.secrets:
            creds_dict = dict(st.secrets['service_account'])
        elif 'gcp_service_account' in st.secrets:
            creds_dict = dict(st.secrets['gcp_service_account'])
        else:
            # Try top-level secrets
            creds_dict = {
                'type': st.secrets.get('type', 'service_account'),
                'project_id': st.secrets.get('project_id'),
                'private_key_id': st.secrets.get('private_key_id'),
                'private_key': st.secrets.get('private_key'),
                'client_email': st.secrets.get('client_email'),
                'client_id': st.secrets.get('client_id'),
                'auth_uri': st.secrets.get('auth_uri'),
                'token_uri': st.secrets.get('token_uri'),
            }
        
        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        logger.error(f"Failed to authenticate with Google Sheets: {e}")
        return None


def get_spreadsheet_id():
    """Get spreadsheet ID from secrets."""
    return st.secrets.get('SPREADSHEET_ID', st.secrets.get('spreadsheet_id', ''))


# =============================================================================
# SHEET LOADING FUNCTIONS
# =============================================================================

def load_sheet_to_dataframe(sheet_name: str, handle_duplicates: bool = True) -> Optional[pd.DataFrame]:
    """
    Load a Google Sheet into a pandas DataFrame.
    
    Args:
        sheet_name: Name of the sheet to load
        handle_duplicates: Whether to handle duplicate column names
    
    Returns:
        DataFrame or None if loading fails
    """
    try:
        client = get_google_sheets_client()
        if client is None:
            return None
        
        spreadsheet_id = get_spreadsheet_id()
        if not spreadsheet_id:
            logger.error("No spreadsheet ID configured")
            return None
        
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        data = worksheet.get_all_values()
        
        if not data:
            return pd.DataFrame()
        
        # Handle duplicate column names
        headers = data[0]
        if handle_duplicates:
            seen = {}
            new_headers = []
            for h in headers:
                if h in seen:
                    seen[h] += 1
                    new_headers.append(f"{h}_{seen[h]}")
                else:
                    seen[h] = 0
                    new_headers.append(h)
            headers = new_headers
        
        df = pd.DataFrame(data[1:], columns=headers)
        
        # Convert numeric columns
        for col in df.columns:
            # Try to convert to numeric
            try:
                numeric_vals = pd.to_numeric(df[col], errors='coerce')
                if numeric_vals.notna().sum() > len(df) * 0.5:  # More than 50% numeric
                    df[col] = numeric_vals
            except:
                pass
        
        return df
        
    except Exception as e:
        logger.error(f"Error loading sheet '{sheet_name}': {e}")
        return None


# =============================================================================
# DATA LOADING FUNCTIONS
# =============================================================================

@st.cache_data(ttl=300)
def load_invoice_lines() -> Optional[pd.DataFrame]:
    """Load Invoice Line Item data."""
    df = load_sheet_to_dataframe('Invoice Line Item')
    
    if df is None or df.empty:
        return None
    
    # Standardize column names
    col_mapping = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'customer' in col_lower and 'correct' in col_lower:
            col_mapping[col] = 'Customer'
        elif col_lower == 'customer' or 'customer name' in col_lower:
            if 'Customer' not in col_mapping.values():
                col_mapping[col] = 'Customer'
        elif 'item' in col_lower and 'name' not in col_lower:
            col_mapping[col] = 'Item'
        elif 'amount' in col_lower or 'line amount' in col_lower:
            col_mapping[col] = 'Amount'
        elif 'qty' in col_lower or 'quantity' in col_lower:
            col_mapping[col] = 'Quantity'
        elif 'date' in col_lower and ('invoice' in col_lower or 'tran' in col_lower):
            col_mapping[col] = 'Date'
        elif 'rep' in col_lower and 'master' in col_lower:
            col_mapping[col] = 'Rep'
        elif 'calyx' in col_lower and 'product type' in col_lower:
            col_mapping[col] = 'Product Type'
        elif 'product type' in col_lower and 'Product Type' not in col_mapping.values():
            col_mapping[col] = 'Product Type'
    
    df = df.rename(columns=col_mapping)
    
    # Clean Product Type
    if 'Product Type' in df.columns:
        df['Product Type'] = df['Product Type'].fillna('Unknown').replace('', 'Unknown')
    
    return df


@st.cache_data(ttl=300)
def load_sales_orders() -> Optional[pd.DataFrame]:
    """Load Sales Orders Main data."""
    df = load_sheet_to_dataframe('_NS_SalesOrders_Data')
    
    if df is None or df.empty:
        # Try alternate name
        df = load_sheet_to_dataframe('Sales Order Line Item')
    
    if df is None or df.empty:
        return None
    
    # Standardize column names
    col_mapping = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'customer' in col_lower:
            if 'Customer' not in col_mapping.values():
                col_mapping[col] = 'Customer'
        elif 'rep' in col_lower:
            if 'Rep' not in col_mapping.values():
                col_mapping[col] = 'Rep'
        elif 'item' in col_lower:
            if 'Item' not in col_mapping.values():
                col_mapping[col] = 'Item'
        elif 'amount' in col_lower:
            if 'Amount' not in col_mapping.values():
                col_mapping[col] = 'Amount'
        elif 'status' in col_lower:
            if 'Status' not in col_mapping.values():
                col_mapping[col] = 'Status'
    
    df = df.rename(columns=col_mapping)
    
    return df


@st.cache_data(ttl=300)
def load_items() -> Optional[pd.DataFrame]:
    """
    Load Raw_Items data with 'Calyx || Product Type' column.
    """
    df = load_sheet_to_dataframe('Raw_Items')
    
    if df is None or df.empty:
        return None
    
    # Find and standardize the Calyx Product Type column
    product_type_col = None
    for col in df.columns:
        col_lower = col.lower()
        if 'calyx' in col_lower and 'product type' in col_lower:
            product_type_col = col
            break
    
    if product_type_col:
        df['Calyx Product Type'] = df[product_type_col].fillna('Unknown').replace('', 'Unknown')
    
    # Also keep original column mapping
    col_mapping = {}
    for col in df.columns:
        col_lower = col.lower()
        if col_lower in ['item', 'item name', 'name', 'sku']:
            col_mapping[col] = 'Item'
        elif 'description' in col_lower:
            if 'Description' not in col_mapping.values():
                col_mapping[col] = 'Description'
    
    df = df.rename(columns=col_mapping)
    
    return df


@st.cache_data(ttl=300)
def load_customers() -> Optional[pd.DataFrame]:
    """Load Customer List data."""
    df = load_sheet_to_dataframe('_NS_Customer_List')
    
    if df is None or df.empty:
        return None
    
    # Standardize column names
    col_mapping = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'company' in col_lower or 'customer' in col_lower:
            if 'Customer' not in col_mapping.values():
                col_mapping[col] = 'Customer'
        elif 'rep' in col_lower or 'salesperson' in col_lower:
            if 'Rep' not in col_mapping.values():
                col_mapping[col] = 'Rep'
    
    df = df.rename(columns=col_mapping)
    
    return df


@st.cache_data(ttl=300)
def load_deals() -> Optional[pd.DataFrame]:
    """Load HubSpot Deals/Pipeline data."""
    df = load_sheet_to_dataframe('Deals')
    
    if df is None or df.empty:
        # Try alternate names
        for sheet_name in ['All Reps All Pipelines', 'HubSpot Deals', 'Pipeline']:
            df = load_sheet_to_dataframe(sheet_name)
            if df is not None and not df.empty:
                break
    
    if df is None or df.empty:
        return None
    
    # Standardize column names
    col_mapping = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'deal' in col_lower and 'name' in col_lower:
            col_mapping[col] = 'Deal Name'
        elif 'company' in col_lower or 'customer' in col_lower:
            if 'Company' not in col_mapping.values():
                col_mapping[col] = 'Company'
        elif 'amount' in col_lower or 'value' in col_lower:
            if 'Amount' not in col_mapping.values():
                col_mapping[col] = 'Amount'
        elif 'stage' in col_lower:
            if 'Stage' not in col_mapping.values():
                col_mapping[col] = 'Stage'
        elif 'close' in col_lower and 'date' in col_lower:
            col_mapping[col] = 'Close Date'
        elif 'product' in col_lower:
            if 'Product' not in col_mapping.values():
                col_mapping[col] = 'Product'
    
    df = df.rename(columns=col_mapping)
    
    return df


@st.cache_data(ttl=300)
def load_inventory() -> Optional[pd.DataFrame]:
    """Load Raw_Inventory data."""
    df = load_sheet_to_dataframe('Raw_Inventory')
    
    if df is None or df.empty:
        return None
    
    return df


@st.cache_data(ttl=300)
def load_vendors() -> Optional[pd.DataFrame]:
    """Load Raw_Vendors data."""
    df = load_sheet_to_dataframe('Raw_Vendors')
    
    if df is None or df.empty:
        return None
    
    return df


@st.cache_data(ttl=300)
def load_invoices() -> Optional[pd.DataFrame]:
    """Load Invoices Main data."""
    df = load_sheet_to_dataframe('_NS_Invoices_Data')
    
    if df is None or df.empty:
        return None
    
    return df


@st.cache_data(ttl=300)
def load_so_lines() -> Optional[pd.DataFrame]:
    """Load Sales Order Line Items."""
    df = load_sheet_to_dataframe('Sales Order Line Item')
    
    if df is None or df.empty:
        return None
    
    return df


# =============================================================================
# AGGREGATE LOADING
# =============================================================================

@st.cache_data(ttl=300)
def load_all_sop_data() -> Dict[str, pd.DataFrame]:
    """Load all S&OP data at once."""
    return {
        'invoice_lines': load_invoice_lines(),
        'sales_orders': load_sales_orders(),
        'items': load_items(),
        'customers': load_customers(),
        'deals': load_deals(),
        'inventory': load_inventory(),
        'vendors': load_vendors()
    }


# =============================================================================
# DATA PREPARATION FUNCTIONS
# =============================================================================

def get_unique_sales_reps(sales_orders: pd.DataFrame = None, customers: pd.DataFrame = None) -> List[str]:
    """Get list of unique sales reps."""
    reps = set()
    
    if sales_orders is None:
        sales_orders = load_sales_orders()
    if customers is None:
        customers = load_customers()
    
    for df in [sales_orders, customers]:
        if df is not None and not df.empty:
            if 'Rep' in df.columns:
                reps.update(df['Rep'].dropna().unique())
    
    return sorted([str(r).strip() for r in reps if r and str(r).strip()])


def get_customers_for_rep(rep: str = None) -> List[str]:
    """Get customers for a specific rep (or all if rep is None)."""
    sales_orders = load_sales_orders()
    
    if sales_orders is None or sales_orders.empty:
        return []
    
    if rep and rep != "All" and 'Rep' in sales_orders.columns:
        filtered = sales_orders[sales_orders['Rep'] == rep]
    else:
        filtered = sales_orders
    
    if 'Customer' in filtered.columns:
        customers = filtered['Customer'].dropna().unique()
        return sorted([str(c).strip() for c in customers if c and str(c).strip()])
    
    return []


def get_skus_for_customer(customer: str = None) -> List[str]:
    """Get SKUs/Items for a specific customer (or all if customer is None)."""
    invoice_lines = load_invoice_lines()
    
    if invoice_lines is None or invoice_lines.empty:
        return []
    
    if customer and customer != "All" and 'Customer' in invoice_lines.columns:
        filtered = invoice_lines[invoice_lines['Customer'] == customer]
    else:
        filtered = invoice_lines
    
    if 'Item' in filtered.columns:
        items = filtered['Item'].dropna().unique()
        return sorted([str(i).strip() for i in items if i and str(i).strip()])
    
    return []


def get_unique_product_types() -> List[str]:
    """Get unique product types from items."""
    items = load_items()
    
    if items is None or items.empty:
        return []
    
    if 'Calyx Product Type' in items.columns:
        types = items['Calyx Product Type'].dropna().unique()
    elif 'Product Type' in items.columns:
        types = items['Product Type'].dropna().unique()
    else:
        return []
    
    return sorted([str(t).strip() for t in types if t and str(t).strip() and str(t) != 'Unknown'])


def get_unique_skus() -> List[str]:
    """Get unique SKUs/Items."""
    items = load_items()
    
    if items is None or items.empty:
        return []
    
    if 'Item' in items.columns:
        skus = items['Item'].dropna().unique()
        return sorted([str(s).strip() for s in skus if s and str(s).strip()])
    
    return []


def prepare_demand_history(invoice_lines: pd.DataFrame = None, 
                           period: str = 'M') -> pd.DataFrame:
    """Prepare historical demand data aggregated by period."""
    if invoice_lines is None:
        invoice_lines = load_invoice_lines()
    
    if invoice_lines is None or invoice_lines.empty:
        return pd.DataFrame()
    
    df = invoice_lines.copy()
    
    # Convert date
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        df['Period'] = df['Date'].dt.to_period(period)
    else:
        return pd.DataFrame()
    
    # Aggregate
    agg_cols = {}
    if 'Amount' in df.columns:
        agg_cols['Revenue'] = ('Amount', 'sum')
    if 'Quantity' in df.columns:
        agg_cols['Units'] = ('Quantity', 'sum')
    
    if not agg_cols:
        return pd.DataFrame()
    
    grouped = df.groupby('Period').agg(**agg_cols).reset_index()
    grouped['Period'] = grouped['Period'].astype(str)
    
    return grouped


def prepare_revenue_history(invoice_lines: pd.DataFrame = None,
                            group_by: str = None) -> pd.DataFrame:
    """Prepare revenue history, optionally grouped."""
    if invoice_lines is None:
        invoice_lines = load_invoice_lines()
    
    if invoice_lines is None or invoice_lines.empty:
        return pd.DataFrame()
    
    df = invoice_lines.copy()
    
    # Convert date
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        df['Month'] = df['Date'].dt.to_period('M')
    else:
        return pd.DataFrame()
    
    # Group by
    group_cols = ['Month']
    if group_by and group_by in df.columns:
        group_cols.append(group_by)
    
    if 'Amount' in df.columns:
        grouped = df.groupby(group_cols)['Amount'].sum().reset_index()
        grouped.columns = group_cols + ['Revenue']
        grouped['Month'] = grouped['Month'].astype(str)
        return grouped
    
    return pd.DataFrame()


def get_pipeline_by_period(deals: pd.DataFrame = None,
                           period: str = 'M') -> pd.DataFrame:
    """Get pipeline/deals aggregated by expected close period."""
    if deals is None:
        deals = load_deals()
    
    if deals is None or deals.empty:
        return pd.DataFrame()
    
    df = deals.copy()
    
    # Convert close date
    if 'Close Date' in df.columns:
        df['Close Date'] = pd.to_datetime(df['Close Date'], errors='coerce')
        df = df.dropna(subset=['Close Date'])
        df['Period'] = df['Close Date'].dt.to_period(period)
    else:
        return pd.DataFrame()
    
    # Aggregate
    if 'Amount' in df.columns:
        grouped = df.groupby('Period')['Amount'].sum().reset_index()
        grouped.columns = ['Period', 'Pipeline Value']
        grouped['Period'] = grouped['Period'].astype(str)
        return grouped
    
    return pd.DataFrame()

