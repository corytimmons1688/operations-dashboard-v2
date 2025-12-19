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
            logger.error(f"No Google Sheets client available for sheet '{sheet_name}'")
            return None
        
        spreadsheet_id = get_spreadsheet_id()
        if not spreadsheet_id:
            logger.error("No spreadsheet ID configured")
            return None
        
        logger.info(f"Opening spreadsheet {spreadsheet_id} for sheet '{sheet_name}'")
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        data = worksheet.get_all_values()
        
        if not data:
            logger.info(f"Sheet '{sheet_name}' has no data")
            return pd.DataFrame()
        
        logger.info(f"Sheet '{sheet_name}' has {len(data)} rows")
        
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
        
        logger.info(f"Successfully created DataFrame with {len(df)} rows and {len(df.columns)} columns")
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
            # Handle duplicate columns
            if df.columns.duplicated().any():
                df = df.loc[:, ~df.columns.duplicated()]
            
            # Find rep column
            rep_col = None
            for col in df.columns:
                if 'rep' in col.lower():
                    rep_col = col
                    break
            
            if rep_col:
                series = df.loc[:, rep_col]
                if isinstance(series, pd.DataFrame):
                    series = series.iloc[:, 0]
                reps.update(series.dropna().unique())
    
    return sorted([str(r).strip() for r in reps if r and str(r).strip()])


def get_customers_for_rep(rep: str = None) -> List[str]:
    """Get customers for a specific rep (or all if rep is None)."""
    sales_orders = load_sales_orders()
    
    if sales_orders is None or sales_orders.empty:
        return []
    
    # Handle duplicate columns
    if sales_orders.columns.duplicated().any():
        sales_orders = sales_orders.loc[:, ~sales_orders.columns.duplicated()]
    
    # Find rep and customer columns
    rep_col = None
    cust_col = None
    for col in sales_orders.columns:
        col_lower = col.lower()
        if rep_col is None and 'rep' in col_lower:
            rep_col = col
        if cust_col is None and 'customer' in col_lower:
            cust_col = col
    
    if cust_col is None:
        return []
    
    if rep and rep != "All" and rep_col:
        rep_series = sales_orders.loc[:, rep_col]
        if isinstance(rep_series, pd.DataFrame):
            rep_series = rep_series.iloc[:, 0]
        filtered = sales_orders[rep_series == rep]
    else:
        filtered = sales_orders
    
    cust_series = filtered.loc[:, cust_col]
    if isinstance(cust_series, pd.DataFrame):
        cust_series = cust_series.iloc[:, 0]
    
    customers = cust_series.dropna().unique()
    return sorted([str(c).strip() for c in customers if c and str(c).strip()])


def get_skus_for_customer(customer: str = None) -> List[str]:
    """Get SKUs/Items for a specific customer (or all if customer is None)."""
    invoice_lines = load_invoice_lines()
    
    if invoice_lines is None or invoice_lines.empty:
        return []
    
    # Handle duplicate columns
    if invoice_lines.columns.duplicated().any():
        invoice_lines = invoice_lines.loc[:, ~invoice_lines.columns.duplicated()]
    
    # Find customer and item columns
    cust_col = None
    item_col = None
    for col in invoice_lines.columns:
        col_lower = col.lower()
        if cust_col is None and 'customer' in col_lower:
            cust_col = col
        if item_col is None and col_lower in ['item', 'sku']:
            item_col = col
    
    if item_col is None:
        return []
    
    if customer and customer != "All" and cust_col:
        cust_series = invoice_lines.loc[:, cust_col]
        if isinstance(cust_series, pd.DataFrame):
            cust_series = cust_series.iloc[:, 0]
        filtered = invoice_lines[cust_series == customer]
    else:
        filtered = invoice_lines
    
    item_series = filtered.loc[:, item_col]
    if isinstance(item_series, pd.DataFrame):
        item_series = item_series.iloc[:, 0]
    
    items = item_series.dropna().unique()
    return sorted([str(i).strip() for i in items if i and str(i).strip()])


def get_unique_product_types(items: pd.DataFrame = None) -> List[str]:
    """Get unique product types from items."""
    if items is None:
        items = load_items()
    
    if items is None or items.empty:
        return []
    
    # Handle duplicate columns
    if items.columns.duplicated().any():
        items = items.loc[:, ~items.columns.duplicated()]
    
    if 'Calyx Product Type' in items.columns:
        col = 'Calyx Product Type'
    elif 'Product Type' in items.columns:
        col = 'Product Type'
    else:
        # Find any column with 'product type' in name
        col = None
        for c in items.columns:
            if 'product type' in c.lower():
                col = c
                break
        if col is None:
            return []
    
    # Get as series safely
    series = items.loc[:, col]
    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]
    
    types = series.dropna().unique().tolist()
    return sorted([str(t).strip() for t in types if t and str(t).strip() and str(t) != 'Unknown'])


def get_unique_skus(items: pd.DataFrame = None) -> List[str]:
    """Get unique SKUs/Items."""
    if items is None:
        items = load_items()
    
    if items is None or items.empty:
        return []
    
    # Handle duplicate columns
    if items.columns.duplicated().any():
        items = items.loc[:, ~items.columns.duplicated()]
    
    # Find item column
    item_col = None
    for col in items.columns:
        if col.lower() in ['item', 'sku', 'item name', 'name']:
            item_col = col
            break
    
    if item_col is None:
        return []
    
    # Get as series safely
    series = items.loc[:, item_col]
    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]
    
    skus = series.dropna().unique().tolist()
    return sorted([str(s).strip() for s in skus if s and str(s).strip()])


def prepare_demand_history(invoice_lines: pd.DataFrame = None, 
                           period: str = 'M',
                           freq: str = None) -> pd.DataFrame:
    """Prepare historical demand data aggregated by period."""
    # Handle freq as alias for period
    if freq is not None:
        period = freq
    
    # Map common frequency strings to pandas period strings
    freq_map = {
        'MS': 'M', 'ME': 'M', 'QS': 'Q', 'QE': 'Q', 
        'YS': 'Y', 'YE': 'Y', 'W': 'W', 'D': 'D',
        'M': 'M', 'Q': 'Q', 'Y': 'Y',
    }
    period = freq_map.get(period, 'M')
        
    if invoice_lines is None:
        invoice_lines = load_invoice_lines()
    
    if invoice_lines is None or invoice_lines.empty:
        return pd.DataFrame()
    
    df = invoice_lines.copy()
    
    # Handle duplicate columns
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]
    
    # Find date column
    date_col = None
    for col in df.columns:
        if 'date' in col.lower():
            date_col = col
            break
    
    if date_col is None:
        return pd.DataFrame()
    
    # Get date series safely
    date_series = df.loc[:, date_col]
    if isinstance(date_series, pd.DataFrame):
        date_series = date_series.iloc[:, 0]
    
    df['Date'] = pd.to_datetime(date_series, errors='coerce')
    df = df.dropna(subset=['Date'])
    df['Period'] = df['Date'].dt.to_period(period)
    
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
                            group_by: str = None,
                            freq: str = None,
                            period: str = 'M') -> pd.DataFrame:
    """Prepare revenue history, optionally grouped."""
    # Handle freq as alias for period
    if freq is not None:
        period = freq
    
    # Map common frequency strings to pandas period strings
    freq_map = {
        'MS': 'M', 'ME': 'M', 'QS': 'Q', 'QE': 'Q', 
        'YS': 'Y', 'YE': 'Y', 'W': 'W', 'D': 'D',
        'M': 'M', 'Q': 'Q', 'Y': 'Y',
    }
    period = freq_map.get(period, 'M')
        
    if invoice_lines is None:
        invoice_lines = load_invoice_lines()
    
    if invoice_lines is None or invoice_lines.empty:
        return pd.DataFrame()
    
    df = invoice_lines.copy()
    
    # Handle duplicate columns
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]
    
    # Find date column
    date_col = None
    for col in df.columns:
        if 'date' in col.lower():
            date_col = col
            break
    
    if date_col is None:
        return pd.DataFrame()
    
    # Get date series safely
    date_series = df.loc[:, date_col]
    if isinstance(date_series, pd.DataFrame):
        date_series = date_series.iloc[:, 0]
    
    df['Date'] = pd.to_datetime(date_series, errors='coerce')
    df = df.dropna(subset=['Date'])
    df['Month'] = df['Date'].dt.to_period(period)
    
    # Find amount column
    amt_col = None
    for col in df.columns:
        if 'amount' in col.lower():
            amt_col = col
            break
    
    if amt_col is None:
        return pd.DataFrame()
    
    # Get amount series safely
    amt_series = df.loc[:, amt_col]
    if isinstance(amt_series, pd.DataFrame):
        amt_series = amt_series.iloc[:, 0]
    df['Amount'] = pd.to_numeric(amt_series, errors='coerce')
    
    # Group by
    group_cols = ['Month']
    if group_by and group_by in df.columns:
        group_cols.append(group_by)
    
    grouped = df.groupby(group_cols)['Amount'].sum().reset_index()
    grouped.columns = group_cols + ['Revenue']
    grouped['Month'] = grouped['Month'].astype(str)
    return grouped


# =============================================================================
# TOP-DOWN REVENUE FORECAST FUNCTIONS
# =============================================================================

def get_all_worksheet_names() -> list:
    """Get all worksheet names from the spreadsheet for debugging."""
    try:
        client = get_google_sheets_client()
        if client is None:
            return []
        
        spreadsheet_id = get_spreadsheet_id()
        if not spreadsheet_id:
            return []
        
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheets = spreadsheet.worksheets()
        return [ws.title for ws in worksheets]
    except Exception as e:
        logger.error(f"Error getting worksheet names: {e}")
        return []


@st.cache_data(ttl=60)
def load_revenue_forecast() -> Optional[pd.DataFrame]:
    """
    Load Revenue Forecast data from Google Sheet.
    """
    # Try exact name with capital F first
    sheet_names_to_try = [
        'Revenue Forecast',  # Capital F - user confirmed this is correct
        'Revenue forecast',
        'RevenueForecast',
        'Forecast',
    ]
    
    for sheet_name in sheet_names_to_try:
        try:
            logger.info(f"Trying to load sheet: '{sheet_name}'")
            df = load_sheet_to_dataframe(sheet_name)
            if df is not None and not df.empty:
                logger.info(f"Successfully loaded Revenue Forecast from: '{sheet_name}' with {len(df)} rows")
                if df.columns.duplicated().any():
                    df = df.loc[:, ~df.columns.duplicated()]
                return df
            else:
                logger.info(f"Sheet '{sheet_name}' returned empty or None")
        except Exception as e:
            logger.info(f"Sheet '{sheet_name}' not found or error: {e}")
            continue
    
    # If standard names fail, list all sheets and look for any with "forecast"
    all_sheets = get_all_worksheet_names()
    logger.info(f"Available worksheets: {all_sheets}")
    
    try:
        st.session_state.available_sheets = all_sheets
    except:
        pass
    
    forecast_sheets = [s for s in all_sheets if 'forecast' in s.lower() and s not in sheet_names_to_try]
    
    for sheet_name in forecast_sheets:
        try:
            df = load_sheet_to_dataframe(sheet_name)
            if df is not None and not df.empty:
                logger.info(f"Successfully loaded from: '{sheet_name}'")
                if df.columns.duplicated().any():
                    df = df.loc[:, ~df.columns.duplicated()]
                return df
        except Exception as e:
            continue
    
    logger.warning(f"Could not find Revenue Forecast. Available: {all_sheets}")
    return None


def parse_revenue_forecast(revenue_forecast_df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse the Revenue Forecast sheet to long format (Category, Period, Forecast_Revenue).
    
    Supports two formats:
    1. Wide format: Category + monthly columns (January, February, etc.)
    2. Long format with Month/Year columns: Category, Month, Year, Amount
    """
    if revenue_forecast_df is None or revenue_forecast_df.empty:
        return pd.DataFrame()
    
    df = revenue_forecast_df.copy()
    
    # Handle duplicate columns
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]
    
    # Check if this is the new long format with Month and Year columns
    has_month_col = any('month' in str(col).lower() for col in df.columns)
    has_year_col = any('year' in str(col).lower() for col in df.columns)
    
    if has_month_col and has_year_col:
        return parse_revenue_forecast_long_format(df)
    else:
        return parse_revenue_forecast_wide_format(df)


def parse_revenue_forecast_long_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse Revenue Forecast in long format with Month and Year columns.
    Expected columns: Category, Month, Year, Amount/Revenue
    """
    # Find columns
    cat_col = None
    month_col = None
    year_col = None
    amount_col = None
    
    for col in df.columns:
        col_lower = str(col).lower().strip()
        
        if cat_col is None and ('category' in col_lower or 'product' in col_lower or col_lower == 'type'):
            cat_col = col
        if month_col is None and col_lower == 'month':
            month_col = col
        if year_col is None and col_lower == 'year':
            year_col = col
        if amount_col is None and ('amount' in col_lower or 'revenue' in col_lower or 'forecast' in col_lower):
            amount_col = col
    
    # If no category column found, use first column
    if cat_col is None:
        cat_col = df.columns[0]
    
    # If no amount column found, try to find any numeric column
    if amount_col is None:
        for col in df.columns:
            if col not in [cat_col, month_col, year_col]:
                # Check if column has numeric data
                try:
                    sample = df[col].iloc[0] if len(df) > 0 else None
                    if sample is not None:
                        if isinstance(sample, (int, float)):
                            amount_col = col
                            break
                        elif isinstance(sample, str) and sample.replace('$', '').replace(',', '').replace('.', '').isdigit():
                            amount_col = col
                            break
                except:
                    pass
    
    if month_col is None or year_col is None:
        return pd.DataFrame()
    
    # Month name to number mapping
    month_to_num = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12,
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
        'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9,
        'oct': 10, 'nov': 11, 'dec': 12
    }
    
    result_rows = []
    
    for _, row in df.iterrows():
        category = row[cat_col]
        if pd.isna(category) or str(category).strip() == '':
            continue
        
        # Get month
        month_val = row[month_col]
        if pd.isna(month_val):
            continue
        
        # Convert month to number
        if isinstance(month_val, str):
            month_num = month_to_num.get(month_val.lower().strip())
            if month_num is None:
                # Try to parse as number
                try:
                    month_num = int(month_val)
                except:
                    continue
        else:
            try:
                month_num = int(month_val)
            except:
                continue
        
        # Get year
        year_val = row[year_col]
        if pd.isna(year_val):
            continue
        try:
            year = int(year_val)
        except:
            continue
        
        # Get amount
        if amount_col:
            value = row[amount_col]
            if isinstance(value, str):
                value = value.replace('$', '').replace(',', '').strip()
            try:
                forecast_revenue = float(value)
            except:
                forecast_revenue = 0
        else:
            forecast_revenue = 0
        
        if forecast_revenue > 0:
            period = f"{year}-{month_num:02d}"
            result_rows.append({
                'Category': str(category).strip(),
                'Period': period,
                'Forecast_Revenue': forecast_revenue
            })
    
    return pd.DataFrame(result_rows)


def parse_revenue_forecast_wide_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse Revenue Forecast in wide format (Category + monthly columns).
    Handles columns like "January", "January 2026", "Jan 2026", etc.
    """
    import re
    
    # Find the category column
    cat_col = None
    for col in df.columns:
        col_lower = str(col).lower()
        if 'category' in col_lower or 'product' in col_lower or col_lower == 'type':
            cat_col = col
            break
    
    if cat_col is None:
        cat_col = df.columns[0]
    
    # Month name mapping
    month_names = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12,
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
        'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9,
        'oct': 10, 'nov': 11, 'dec': 12
    }
    
    # Default forecast year
    current_date = datetime.now()
    default_year = current_date.year + 1 if current_date.month >= 6 else current_date.year
    
    result_rows = []
    
    for _, row in df.iterrows():
        category = row[cat_col]
        if pd.isna(category) or str(category).strip() == '':
            continue
        
        for col in df.columns:
            if col == cat_col:
                continue
            
            col_str = str(col).lower().strip()
            
            # Try to find month name within column string
            month_num = None
            for month_name, month_val in month_names.items():
                if month_name in col_str:
                    month_num = month_val
                    break
            
            if month_num is None:
                continue  # Not a month column
            
            # Try to extract year from column (e.g., "January 2026")
            year_match = re.search(r'20\d{2}', str(col))
            year = int(year_match.group()) if year_match else default_year
            
            value = row[col]
            if isinstance(value, str):
                value = value.replace('$', '').replace(',', '').strip()
            
            try:
                forecast_revenue = float(value)
            except:
                forecast_revenue = 0
            
            if forecast_revenue > 0:
                period = f"{year}-{month_num:02d}"
                result_rows.append({
                    'Category': str(category).strip(),
                    'Period': period,
                    'Forecast_Revenue': forecast_revenue
                })
    
    return pd.DataFrame(result_rows)


def calculate_item_unit_mix_rolling12(sales_orders: pd.DataFrame = None) -> pd.DataFrame:
    """
    Calculate historical percentage mix of items by UNITS within each category.
    Uses Sales Order Lines data with Quantity Ordered and Sales Manager Approval Date.
    Joins with Items table to get Product Type (Category).
    Rolling 12 months only.
    
    Returns DataFrame with columns: Category, Item, Total_Units, Mix_Pct
    """
    # Store debug info
    debug_info = {}
    
    if sales_orders is None:
        sales_orders = load_sales_orders()
    
    if sales_orders is None or sales_orders.empty:
        debug_info['sales_orders_status'] = 'Empty or None - falling back to invoices'
        try:
            st.session_state.item_mix_debug = debug_info
        except:
            pass
        return calculate_item_unit_mix_from_invoices()
    
    df = sales_orders.copy()
    debug_info['sales_orders_rows'] = len(df)
    debug_info['sales_orders_columns'] = list(df.columns)[:20]  # First 20 columns
    
    # Handle duplicate columns
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]
    
    # Load Items to get Product Type mapping
    items_df = load_items()
    item_to_category = {}
    
    if items_df is not None and not items_df.empty:
        debug_info['items_rows'] = len(items_df)
        debug_info['items_columns'] = list(items_df.columns)[:20]
        
        # Handle duplicate columns in items
        if items_df.columns.duplicated().any():
            items_df = items_df.loc[:, ~items_df.columns.duplicated()]
        
        # Find item and category columns in Items table
        item_col_items = None
        cat_col_items = None
        
        for col in items_df.columns:
            col_lower = str(col).lower()
            if item_col_items is None and col_lower in ['item', 'sku', 'item name', 'name', 'item/sku']:
                item_col_items = col
            if cat_col_items is None:
                if 'product type' in col_lower or 'calyx' in col_lower:
                    cat_col_items = col
        
        debug_info['items_item_col'] = item_col_items
        debug_info['items_cat_col'] = cat_col_items
        
        if item_col_items and cat_col_items:
            # Create mapping
            for _, row in items_df.iterrows():
                item = row[item_col_items]
                cat = row[cat_col_items]
                if pd.notna(item) and pd.notna(cat):
                    item_to_category[str(item).strip()] = str(cat).strip()
            
            debug_info['item_to_category_count'] = len(item_to_category)
            # Sample of mappings
            sample_items = list(item_to_category.items())[:5]
            debug_info['item_to_category_sample'] = sample_items
    else:
        debug_info['items_status'] = 'Empty or None'
    
    # Find required columns in Sales Orders
    date_col = None
    qty_col = None
    item_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        
        # Date column - prefer "Sales Manager Approval Date"
        if date_col is None:
            if 'sales manager' in col_lower and 'date' in col_lower:
                date_col = col
            elif 'approval' in col_lower and 'date' in col_lower:
                date_col = col
        
        # Quantity column - prefer "Quantity Ordered"
        if qty_col is None:
            if 'quantity ordered' in col_lower:
                qty_col = col
            elif 'qty ordered' in col_lower:
                qty_col = col
        
        # Item column
        if item_col is None:
            if col_lower in ['item', 'sku', 'item name', 'item/sku']:
                item_col = col
    
    # If we didn't find specific columns, try broader search
    if date_col is None:
        for col in df.columns:
            if 'date' in str(col).lower():
                date_col = col
                break
    
    if qty_col is None:
        for col in df.columns:
            col_lower = str(col).lower()
            if 'qty' in col_lower or 'quantity' in col_lower:
                qty_col = col
                break
    
    if item_col is None:
        for col in df.columns:
            if 'item' in str(col).lower():
                item_col = col
                break
    
    debug_info['so_date_col'] = date_col
    debug_info['so_qty_col'] = qty_col
    debug_info['so_item_col'] = item_col
    
    # Store debug info
    try:
        st.session_state.item_mix_debug = debug_info
    except:
        pass
    
    if item_col is None or qty_col is None:
        debug_info['fallback_reason'] = f'Missing columns: item_col={item_col}, qty_col={qty_col}'
        return calculate_item_unit_mix_from_invoices()
    
    # Get series safely
    def safe_get_series(dataframe, column):
        if column not in dataframe.columns:
            return None
        result = dataframe.loc[:, column]
        if isinstance(result, pd.DataFrame):
            return result.iloc[:, 0]
        return result
    
    item_series = safe_get_series(df, item_col)
    qty_series = safe_get_series(df, qty_col)
    date_series = safe_get_series(df, date_col) if date_col else None
    
    if item_series is None or qty_series is None:
        return calculate_item_unit_mix_from_invoices()
    
    temp_df = pd.DataFrame({
        'Item': item_series.astype(str).str.strip(),
        'Quantity': pd.to_numeric(qty_series, errors='coerce').fillna(0)
    })
    
    # Map items to categories using Items table
    temp_df['Category'] = temp_df['Item'].map(item_to_category)
    
    # Count how many mapped vs not
    mapped_count = temp_df['Category'].notna().sum()
    total_count = len(temp_df)
    debug_info['mapped_items'] = mapped_count
    debug_info['total_items'] = total_count
    
    temp_df['Category'] = temp_df['Category'].fillna('Unknown')
    
    # Filter to rolling 12 months
    if date_series is not None:
        temp_df['Date'] = pd.to_datetime(date_series, errors='coerce')
        cutoff_date = datetime.now() - timedelta(days=365)
        before_filter = len(temp_df)
        temp_df = temp_df[temp_df['Date'] >= cutoff_date]
        debug_info['rows_before_date_filter'] = before_filter
        debug_info['rows_after_date_filter'] = len(temp_df)
    
    if temp_df.empty:
        return calculate_item_unit_mix_from_invoices()
    
    # Remove Unknown categories (items without mapping)
    before_unknown_filter = len(temp_df)
    temp_df = temp_df[temp_df['Category'] != 'Unknown']
    debug_info['rows_after_unknown_filter'] = len(temp_df)
    
    if temp_df.empty:
        debug_info['fallback_reason'] = 'All items mapped to Unknown category'
        try:
            st.session_state.item_mix_debug = debug_info
        except:
            pass
        return calculate_item_unit_mix_from_invoices()
    
    # Calculate units by category and item
    by_cat_item = temp_df.groupby(['Category', 'Item'])['Quantity'].sum().reset_index()
    by_cat_item.columns = ['Category', 'Item', 'Total_Units']
    
    # Calculate category totals
    cat_totals = temp_df.groupby('Category')['Quantity'].sum().reset_index()
    cat_totals.columns = ['Category', 'Category_Total_Units']
    
    # Merge and calculate percentage
    by_cat_item = by_cat_item.merge(cat_totals, on='Category')
    by_cat_item['Mix_Pct'] = np.where(
        by_cat_item['Category_Total_Units'] > 0,
        (by_cat_item['Total_Units'] / by_cat_item['Category_Total_Units'] * 100),
        0
    )
    
    debug_info['final_categories'] = by_cat_item['Category'].unique().tolist()
    debug_info['final_rows'] = len(by_cat_item)
    
    try:
        st.session_state.item_mix_debug = debug_info
    except:
        pass
    
    return by_cat_item[['Category', 'Item', 'Total_Units', 'Mix_Pct']]


def calculate_item_unit_mix_from_invoices() -> pd.DataFrame:
    """
    Fallback: Calculate item unit mix from Invoice Lines if Sales Orders don't work.
    """
    debug_info = {'source': 'invoice_lines_fallback'}
    
    invoice_lines = load_invoice_lines()
    
    if invoice_lines is None or invoice_lines.empty:
        debug_info['status'] = 'Invoice lines empty or None'
        try:
            st.session_state.item_mix_debug = debug_info
        except:
            pass
        return pd.DataFrame()
    
    df = invoice_lines.copy()
    debug_info['invoice_rows'] = len(df)
    debug_info['invoice_columns'] = list(df.columns)[:20]
    
    # Handle duplicate columns
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]
    
    # Find columns
    item_col = None
    qty_col = None
    cat_col = None
    date_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        if item_col is None and col_lower in ['item', 'sku']:
            item_col = col
        if qty_col is None and ('qty' in col_lower or 'quantity' in col_lower):
            qty_col = col
        if cat_col is None and ('product type' in col_lower or 'calyx' in col_lower):
            cat_col = col
        if date_col is None and 'date' in col_lower:
            date_col = col
    
    debug_info['inv_item_col'] = item_col
    debug_info['inv_qty_col'] = qty_col
    debug_info['inv_cat_col'] = cat_col
    debug_info['inv_date_col'] = date_col
    
    if item_col is None or cat_col is None:
        debug_info['status'] = f'Missing columns: item={item_col}, category={cat_col}'
        try:
            st.session_state.item_mix_debug = debug_info
        except:
            pass
        return pd.DataFrame()
    
    # Get series safely
    def safe_get_series(dataframe, column):
        if column not in dataframe.columns:
            return None
        result = dataframe.loc[:, column]
        if isinstance(result, pd.DataFrame):
            return result.iloc[:, 0]
        return result
    
    item_series = safe_get_series(df, item_col)
    cat_series = safe_get_series(df, cat_col)
    qty_series = safe_get_series(df, qty_col) if qty_col else None
    date_series = safe_get_series(df, date_col) if date_col else None
    
    if item_series is None or cat_series is None:
        debug_info['status'] = 'Could not extract item or category series'
        try:
            st.session_state.item_mix_debug = debug_info
        except:
            pass
        return pd.DataFrame()
    
    temp_df = pd.DataFrame({
        'Item': item_series,
        'Category': cat_series
    })
    
    if qty_series is not None:
        temp_df['Quantity'] = pd.to_numeric(qty_series, errors='coerce').fillna(1)
    else:
        temp_df['Quantity'] = 1  # Count rows as units if no quantity
    
    # Filter to rolling 12 months
    if date_series is not None:
        temp_df['Date'] = pd.to_datetime(date_series, errors='coerce')
        cutoff_date = datetime.now() - timedelta(days=365)
        before_filter = len(temp_df)
        temp_df = temp_df[temp_df['Date'] >= cutoff_date]
        debug_info['rows_before_date_filter'] = before_filter
        debug_info['rows_after_date_filter'] = len(temp_df)
    
    if temp_df.empty:
        debug_info['status'] = 'Empty after date filter'
        try:
            st.session_state.item_mix_debug = debug_info
        except:
            pass
        return pd.DataFrame()
    
    # Calculate units by category and item
    by_cat_item = temp_df.groupby(['Category', 'Item'])['Quantity'].sum().reset_index()
    by_cat_item.columns = ['Category', 'Item', 'Total_Units']
    
    # Calculate category totals
    cat_totals = temp_df.groupby('Category')['Quantity'].sum().reset_index()
    cat_totals.columns = ['Category', 'Category_Total_Units']
    
    # Merge and calculate percentage
    by_cat_item = by_cat_item.merge(cat_totals, on='Category')
    by_cat_item['Mix_Pct'] = np.where(
        by_cat_item['Category_Total_Units'] > 0,
        (by_cat_item['Total_Units'] / by_cat_item['Category_Total_Units'] * 100),
        0
    )
    
    debug_info['final_categories'] = by_cat_item['Category'].unique().tolist()
    debug_info['final_rows'] = len(by_cat_item)
    debug_info['status'] = 'Success'
    
    try:
        st.session_state.item_mix_debug = debug_info
    except:
        pass
    
    return by_cat_item[['Category', 'Item', 'Total_Units', 'Mix_Pct']]


def calculate_item_asp_rolling12(invoice_lines: pd.DataFrame = None) -> pd.DataFrame:
    """
    Calculate historical Average Selling Price (ASP) by item.
    Uses Invoice Lines data for actual sales prices.
    Rolling 12 months only.
    
    Returns DataFrame with columns: Item, ASP, Total_Units, Total_Revenue
    """
    if invoice_lines is None:
        invoice_lines = load_invoice_lines()
    
    if invoice_lines is None or invoice_lines.empty:
        return pd.DataFrame()
    
    df = invoice_lines.copy()
    
    # Handle duplicate columns
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]
    
    # Find required columns
    item_col = None
    amount_col = None
    qty_col = None
    date_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        
        if item_col is None and col_lower in ['item', 'sku', 'item name']:
            item_col = col
        if amount_col is None and 'amount' in col_lower:
            amount_col = col
        if qty_col is None and ('qty' in col_lower or 'quantity' in col_lower):
            qty_col = col
        if date_col is None and 'date' in col_lower:
            date_col = col
    
    if item_col is None or amount_col is None:
        return pd.DataFrame()
    
    # Get series safely
    def safe_get_series(dataframe, column):
        if column not in dataframe.columns:
            return None
        result = dataframe.loc[:, column]
        if isinstance(result, pd.DataFrame):
            return result.iloc[:, 0]
        return result
    
    item_series = safe_get_series(df, item_col)
    amt_series = safe_get_series(df, amount_col)
    qty_series = safe_get_series(df, qty_col) if qty_col else None
    date_series = safe_get_series(df, date_col) if date_col else None
    
    if item_series is None or amt_series is None:
        return pd.DataFrame()
    
    temp_df = pd.DataFrame({
        'Item': item_series,
        'Amount': pd.to_numeric(amt_series, errors='coerce').fillna(0)
    })
    
    if qty_series is not None:
        temp_df['Quantity'] = pd.to_numeric(qty_series, errors='coerce').fillna(0)
    else:
        temp_df['Quantity'] = 1
    
    # Filter to rolling 12 months
    if date_series is not None:
        temp_df['Date'] = pd.to_datetime(date_series, errors='coerce')
        cutoff_date = datetime.now() - timedelta(days=365)
        temp_df = temp_df[temp_df['Date'] >= cutoff_date]
    
    if temp_df.empty:
        return pd.DataFrame()
    
    # Aggregate by item
    by_item = temp_df.groupby('Item').agg({
        'Amount': 'sum',
        'Quantity': 'sum'
    }).reset_index()
    
    by_item.columns = ['Item', 'Total_Revenue', 'Total_Units']
    
    # Calculate ASP (avoid division by zero)
    by_item['ASP'] = np.where(
        by_item['Total_Units'] > 0,
        by_item['Total_Revenue'] / by_item['Total_Units'],
        0
    )
    
    return by_item


def allocate_topdown_forecast(revenue_forecast: pd.DataFrame = None,
                              item_mix: pd.DataFrame = None,
                              item_asp: pd.DataFrame = None) -> pd.DataFrame:
    """
    Top-down allocation of category-level revenue forecast to item level.
    
    Logic:
    1. Take category revenue forecast
    2. Apply item unit mix % to get item's share of category units
    3. But we need revenue first - so: Category Revenue × Item Mix % = Item Revenue
    4. Item Revenue ÷ Item ASP = Item Units
    
    Returns DataFrame with: Item, Category, Period, Forecast_Revenue, Forecast_Units, Mix_Pct, ASP
    """
    if revenue_forecast is None or revenue_forecast.empty:
        return pd.DataFrame()
    if item_mix is None or item_mix.empty:
        return pd.DataFrame()
    
    result_rows = []
    
    # Get available categories in item_mix for matching
    available_categories = item_mix['Category'].unique().tolist() if 'Category' in item_mix.columns else []
    
    for _, forecast_row in revenue_forecast.iterrows():
        category = str(forecast_row['Category']).strip()
        period = forecast_row['Period']
        cat_forecast_revenue = forecast_row['Forecast_Revenue']
        
        if pd.isna(cat_forecast_revenue) or cat_forecast_revenue <= 0:
            continue
        
        # Try to find matching category in item_mix
        cat_items = item_mix[item_mix['Category'] == category].copy()
        
        # If no exact match, try case-insensitive
        if cat_items.empty:
            category_lower = category.lower()
            for avail_cat in available_categories:
                if str(avail_cat).lower() == category_lower:
                    cat_items = item_mix[item_mix['Category'] == avail_cat].copy()
                    break
        
        # If still no match, try partial match
        if cat_items.empty:
            for avail_cat in available_categories:
                if category_lower in str(avail_cat).lower() or str(avail_cat).lower() in category_lower:
                    cat_items = item_mix[item_mix['Category'] == avail_cat].copy()
                    break
        
        if cat_items.empty:
            # No historical data - keep at category level
            result_rows.append({
                'Item': f'{category} (Unallocated)',
                'Category': category,
                'Period': period,
                'Forecast_Revenue': cat_forecast_revenue,
                'Forecast_Units': 0,
                'Mix_Pct': 100,
                'ASP': 0
            })
            continue
        
        # Normalize mix percentages to sum to 100%
        total_mix = cat_items['Mix_Pct'].sum()
        if total_mix > 0:
            cat_items['Mix_Pct_Normalized'] = cat_items['Mix_Pct'] / total_mix * 100
        else:
            cat_items['Mix_Pct_Normalized'] = 100 / len(cat_items)
        
        # Allocate to each item
        for _, item_row in cat_items.iterrows():
            item_name = item_row['Item']
            mix_pct = item_row['Mix_Pct_Normalized'] / 100  # Convert to decimal
            
            # Item's share of category revenue
            item_forecast_revenue = cat_forecast_revenue * mix_pct
            
            # Get ASP for this item
            asp = 0
            forecast_units = 0
            
            if item_asp is not None and not item_asp.empty:
                item_asp_row = item_asp[item_asp['Item'] == item_name]
                if not item_asp_row.empty:
                    asp = item_asp_row['ASP'].iloc[0]
                    if asp > 0:
                        forecast_units = item_forecast_revenue / asp
            
            result_rows.append({
                'Item': item_name,
                'Category': category,
                'Period': period,
                'Forecast_Revenue': round(item_forecast_revenue, 2),
                'Forecast_Units': round(forecast_units, 0),
                'Mix_Pct': round(item_row['Mix_Pct_Normalized'], 2),
                'ASP': round(asp, 2)
            })
    
    return pd.DataFrame(result_rows)


def get_topdown_item_forecast() -> pd.DataFrame:
    """
    Main function to create top-down item-level forecast.
    
    1. Load Revenue Forecast (category level by month)
    2. Calculate rolling 12-month item unit mix from Sales Orders (joined with Items for category)
    3. Calculate rolling 12-month ASP from Invoice Lines
    4. Allocate category forecast → items
    
    Returns DataFrame with item-level forecasts
    """
    # Load and parse category-level forecast
    revenue_forecast_raw = load_revenue_forecast()
    if revenue_forecast_raw is None or revenue_forecast_raw.empty:
        return pd.DataFrame()
    
    revenue_forecast = parse_revenue_forecast(revenue_forecast_raw)
    if revenue_forecast.empty:
        return pd.DataFrame()
    
    # Calculate item mix from Sales Orders (by units, rolling 12 months)
    # This will try Sales Orders first, then fall back to Invoice Lines
    item_mix = calculate_item_unit_mix_rolling12()
    
    # Calculate ASP from Invoice Lines (rolling 12 months)
    item_asp = calculate_item_asp_rolling12()
    
    # Debug: Log category names from both sources
    forecast_categories = revenue_forecast['Category'].unique().tolist() if 'Category' in revenue_forecast.columns else []
    mix_categories = item_mix['Category'].unique().tolist() if not item_mix.empty and 'Category' in item_mix.columns else []
    
    # Store debug info for display
    try:
        if 'forecast_debug' not in st.session_state:
            st.session_state.forecast_debug = {}
        st.session_state.forecast_debug['forecast_categories'] = forecast_categories
        st.session_state.forecast_debug['mix_categories'] = mix_categories
        st.session_state.forecast_debug['item_mix_rows'] = len(item_mix) if not item_mix.empty else 0
        st.session_state.forecast_debug['item_asp_rows'] = len(item_asp) if not item_asp.empty else 0
        st.session_state.forecast_debug['revenue_forecast_rows'] = len(revenue_forecast)
    except:
        pass  # Ignore session state errors
    
    # Allocate forecast to items
    item_forecast = allocate_topdown_forecast(
        revenue_forecast=revenue_forecast, 
        item_mix=item_mix, 
        item_asp=item_asp
    )
    
    return item_forecast


def get_revenue_forecast_by_period(category: str = None) -> pd.DataFrame:
    """
    Get Revenue Forecast aggregated by period for charting.
    Optionally filter by category.
    
    Falls back to category-level data if item-level allocation fails.
    
    Returns DataFrame with Period and Forecast_Revenue columns.
    """
    # First try to get item-level forecast
    item_forecast = get_topdown_item_forecast()
    
    # If item forecast is empty, fall back to parsed category-level forecast
    if item_forecast.empty:
        # Load and parse the raw forecast
        revenue_forecast_raw = load_revenue_forecast()
        if revenue_forecast_raw is None or revenue_forecast_raw.empty:
            return pd.DataFrame()
        
        parsed_forecast = parse_revenue_forecast(revenue_forecast_raw)
        if parsed_forecast.empty:
            return pd.DataFrame()
        
        # Filter by category if specified
        if category and category != 'All':
            # Try exact match first
            filtered = parsed_forecast[parsed_forecast['Category'] == category]
            
            # If no exact match, try case-insensitive
            if filtered.empty:
                category_lower = category.lower().strip()
                filtered = parsed_forecast[parsed_forecast['Category'].str.lower().str.strip() == category_lower]
            
            # If still no match, try contains
            if filtered.empty:
                filtered = parsed_forecast[parsed_forecast['Category'].str.lower().str.contains(category_lower, na=False)]
            
            parsed_forecast = filtered
        
        if parsed_forecast.empty:
            return pd.DataFrame()
        
        # Aggregate by period
        by_period = parsed_forecast.groupby('Period')['Forecast_Revenue'].sum().reset_index()
        by_period = by_period.sort_values('Period')
        
        return by_period
    
    # If we have item-level forecast, use it
    # Filter by category if specified (with fuzzy matching)
    if category and category != 'All':
        # Try exact match first
        filtered = item_forecast[item_forecast['Category'] == category]
        
        # If no exact match, try case-insensitive
        if filtered.empty:
            category_lower = category.lower().strip()
            filtered = item_forecast[item_forecast['Category'].str.lower().str.strip() == category_lower]
        
        # If still no match, try contains
        if filtered.empty:
            filtered = item_forecast[item_forecast['Category'].str.lower().str.contains(category_lower, na=False)]
        
        item_forecast = filtered
    
    if item_forecast.empty:
        return pd.DataFrame()
    
    # Aggregate by period
    by_period = item_forecast.groupby('Period').agg({
        'Forecast_Revenue': 'sum',
        'Forecast_Units': 'sum'
    }).reset_index()
    
    by_period = by_period.sort_values('Period')
    
    return by_period


def get_pipeline_by_period(deals: pd.DataFrame = None,
                           period: str = 'M',
                           freq: str = None) -> pd.DataFrame:
    """
    Get pipeline/deals aggregated by expected close period.
    
    Args:
        deals: Deals DataFrame (optional, will load if not provided)
        period: Period frequency ('M' for monthly, 'Q' for quarterly, etc.)
        freq: Alias for period (for backwards compatibility)
    """
    # Handle freq as alias for period
    if freq is not None:
        period = freq
    
    # Map common frequency strings to pandas period strings
    freq_map = {
        'MS': 'M',   # Month Start -> Month
        'ME': 'M',   # Month End -> Month
        'QS': 'Q',   # Quarter Start -> Quarter
        'QE': 'Q',   # Quarter End -> Quarter
        'YS': 'Y',   # Year Start -> Year
        'YE': 'Y',   # Year End -> Year
        'W': 'W',
        'D': 'D',
        'M': 'M',
        'Q': 'Q',
        'Y': 'Y',
    }
    period = freq_map.get(period, 'M')  # Default to 'M' if not found
    
    if deals is None:
        deals = load_deals()
    
    if deals is None or deals.empty:
        return pd.DataFrame()
    
    df = deals.copy()
    
    # Handle duplicate columns
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]
    
    # Find close date column
    close_date_col = None
    for col in df.columns:
        col_lower = col.lower()
        if 'close' in col_lower and 'date' in col_lower:
            close_date_col = col
            break
        elif col_lower == 'close date':
            close_date_col = col
            break
    
    if close_date_col is None:
        # Try any date column
        for col in df.columns:
            if 'date' in col.lower():
                close_date_col = col
                break
    
    if close_date_col is None:
        return pd.DataFrame()
    
    # Get date series safely
    date_series = df.loc[:, close_date_col]
    if isinstance(date_series, pd.DataFrame):
        date_series = date_series.iloc[:, 0]
    
    df['Close Date'] = pd.to_datetime(date_series, errors='coerce')
    df = df.dropna(subset=['Close Date'])
    
    if df.empty:
        return pd.DataFrame()
    
    df['Period'] = df['Close Date'].dt.to_period(period)
    
    # Find amount column
    amt_col = None
    for col in df.columns:
        col_lower = col.lower()
        if 'amount' in col_lower or 'value' in col_lower:
            amt_col = col
            break
    
    if amt_col is None:
        return pd.DataFrame()
    
    # Get amount series safely
    amt_series = df.loc[:, amt_col]
    if isinstance(amt_series, pd.DataFrame):
        amt_series = amt_series.iloc[:, 0]
    
    df['Amount'] = pd.to_numeric(amt_series, errors='coerce')
    
    grouped = df.groupby('Period')['Amount'].sum().reset_index()
    grouped.columns = ['Period', 'Pipeline Value']
    grouped['Period'] = grouped['Period'].astype(str)
    
    return grouped


def calculate_lead_times(items: pd.DataFrame = None, 
                         vendors: pd.DataFrame = None) -> pd.DataFrame:
    """
    Calculate lead times for items based on vendor data.
    
    Args:
        items: Items dataframe
        vendors: Vendors dataframe
    
    Returns:
        DataFrame with item lead time information
    """
    if items is None:
        items = load_items()
    if vendors is None:
        vendors = load_vendors()
    
    if items is None or items.empty:
        return pd.DataFrame()
    
    df = items.copy()
    
    # Look for lead time column in items
    lead_time_col = None
    for col in df.columns:
        col_lower = col.lower()
        if 'lead' in col_lower and 'time' in col_lower:
            lead_time_col = col
            break
        elif 'leadtime' in col_lower:
            lead_time_col = col
            break
    
    # If no lead time column, try to get from vendors
    if lead_time_col is None and vendors is not None and not vendors.empty:
        # Find vendor column in items
        vendor_col = None
        for col in df.columns:
            col_lower = col.lower()
            if 'vendor' in col_lower or 'supplier' in col_lower:
                vendor_col = col
                break
        
        if vendor_col:
            # Find lead time in vendors
            vendor_lead_col = None
            for col in vendors.columns:
                col_lower = col.lower()
                if 'lead' in col_lower and 'time' in col_lower:
                    vendor_lead_col = col
                    break
            
            if vendor_lead_col:
                # Find vendor name column
                vendor_name_col = None
                for col in vendors.columns:
                    col_lower = col.lower()
                    if col_lower in ['vendor', 'name', 'vendor name', 'supplier']:
                        vendor_name_col = col
                        break
                
                if vendor_name_col:
                    vendor_lead_times = vendors.set_index(vendor_name_col)[vendor_lead_col].to_dict()
                    df['Lead Time'] = df[vendor_col].map(vendor_lead_times)
    
    # If we found a lead time column, standardize it
    if lead_time_col:
        df['Lead Time'] = pd.to_numeric(df[lead_time_col], errors='coerce').fillna(0)
    elif 'Lead Time' not in df.columns:
        # Default lead time
        df['Lead Time'] = 30  # Default 30 days
    
    # Create summary
    result_cols = ['Item'] if 'Item' in df.columns else [df.columns[0]]
    if 'Calyx Product Type' in df.columns:
        result_cols.append('Calyx Product Type')
    elif 'Product Type' in df.columns:
        result_cols.append('Product Type')
    result_cols.append('Lead Time')
    
    # Add vendor if available
    vendor_col = next((c for c in df.columns if 'vendor' in c.lower()), None)
    if vendor_col:
        result_cols.insert(-1, vendor_col)
    
    return df[[c for c in result_cols if c in df.columns]]
