"""
S&OP Data Loader Module
Handles loading and processing data from Google Sheets for S&OP Dashboard

Features:
- Loads Invoice Lines, Sales Orders, Items, Customers, Deals
- Properly maps 'Calyx || Product Type' column from Raw_Items
- Handles duplicate column names
- Handles Coefficient/HubSpot Import title row in Deals sheet
- Fixed Amount column detection for pipeline

Author: Xander @ Calyx Containers
Version: 3.7.0
Last Updated: 2026-01-13 09:50 MST
Changes:
- v3.7.0: Fixed Coefficient header row detection - properly skips Row 1 when HubSpot Import header detected
- v3.6.0: Fixed Amount column detection - checks exact match, variations, and 'Probability Rev'
"""

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import logging
from typing import Optional, Dict, Any
import hashlib
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Version info
VERSION = "3.7.0"
LAST_UPDATED = "2026-01-13 09:50 MST"

# Google Sheets scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

# Cache duration (seconds)
CACHE_TTL = 300  # 5 minutes


def get_google_credentials():
    """Get Google credentials from Streamlit secrets."""
    try:
        creds_dict = st.secrets["gcp_service_account"]
        credentials = Credentials.from_service_account_info(
            dict(creds_dict),
            scopes=SCOPES
        )
        return credentials
    except Exception as e:
        logger.error(f"Failed to get Google credentials: {e}")
        return None


def get_gspread_client():
    """Get authenticated gspread client."""
    credentials = get_google_credentials()
    if credentials is None:
        return None
    try:
        return gspread.authorize(credentials)
    except Exception as e:
        logger.error(f"Failed to authorize gspread: {e}")
        return None


@st.cache_data(ttl=CACHE_TTL)
def get_spreadsheet_id() -> Optional[str]:
    """Get spreadsheet ID from secrets."""
    try:
        return st.secrets.get("spreadsheet_id", st.secrets.get("SPREADSHEET_ID"))
    except Exception:
        return None


@st.cache_data(ttl=CACHE_TTL)
def load_sheet_to_dataframe(sheet_name: str) -> Optional[pd.DataFrame]:
    """Load a specific sheet from Google Sheets into a DataFrame."""
    try:
        client = get_gspread_client()
        if client is None:
            return None
        
        spreadsheet_id = get_spreadsheet_id()
        if spreadsheet_id is None:
            logger.error("Spreadsheet ID not found in secrets")
            return None
        
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # Get all values
        data = worksheet.get_all_values()
        
        if not data or len(data) < 2:
            logger.warning(f"Sheet '{sheet_name}' is empty or has no data rows")
            return None
        
        # First row is headers
        headers = data[0]
        rows = data[1:]
        
        # Handle duplicate column names
        seen = {}
        unique_headers = []
        for h in headers:
            h_str = str(h).strip() if h else ''
            if h_str in seen:
                seen[h_str] += 1
                unique_headers.append(f"{h_str}_{seen[h_str]}")
            else:
                seen[h_str] = 0
                unique_headers.append(h_str)
        
        df = pd.DataFrame(rows, columns=unique_headers)
        
        # Replace empty strings with NaN
        df = df.replace('', pd.NA)
        
        logger.info(f"Loaded sheet '{sheet_name}': {len(df)} rows, {len(df.columns)} columns")
        
        return df
        
    except gspread.exceptions.WorksheetNotFound:
        logger.warning(f"Worksheet '{sheet_name}' not found")
        return None
    except Exception as e:
        logger.error(f"Error loading sheet '{sheet_name}': {e}")
        return None


@st.cache_data(ttl=CACHE_TTL)
def load_invoice_lines() -> Optional[pd.DataFrame]:
    """Load Invoice Lines data."""
    df = load_sheet_to_dataframe('Invoice_Lines')
    
    if df is None or df.empty:
        # Try alternate names
        for sheet_name in ['InvoiceLines', 'Invoice Lines', 'Invoices']:
            df = load_sheet_to_dataframe(sheet_name)
            if df is not None and not df.empty:
                break
    
    if df is None or df.empty:
        return None
    
    # Standardize column names
    col_mapping = {}
    for col in df.columns:
        col_lower = str(col).lower()
        if 'date' in col_lower and 'Date' not in col_mapping.values():
            col_mapping[col] = 'Date'
        elif 'quantity' in col_lower or col_lower == 'qty':
            col_mapping[col] = 'Quantity'
        elif 'amount' in col_lower or 'total' in col_lower:
            if 'Amount' not in col_mapping.values():
                col_mapping[col] = 'Amount'
        elif 'item' in col_lower and 'name' in col_lower:
            col_mapping[col] = 'Item Name/Number'
        elif col_lower == 'item':
            if 'Item Name/Number' not in col_mapping.values():
                col_mapping[col] = 'Item Name/Number'
        elif 'customer' in col_lower:
            if 'Customer' not in col_mapping.values():
                col_mapping[col] = 'Customer'
        elif 'sales' in col_lower and 'rep' in col_lower:
            col_mapping[col] = 'Sales Rep'
    
    df = df.rename(columns=col_mapping)
    
    # Convert numeric columns
    for col in ['Quantity', 'Amount']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Convert date
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    return df


@st.cache_data(ttl=CACHE_TTL)
def load_sales_orders() -> Optional[pd.DataFrame]:
    """Load Sales Orders data."""
    df = load_sheet_to_dataframe('Sales_Orders')
    
    if df is None or df.empty:
        for sheet_name in ['SalesOrders', 'Sales Orders', 'Orders']:
            df = load_sheet_to_dataframe(sheet_name)
            if df is not None and not df.empty:
                break
    
    if df is None or df.empty:
        return None
    
    # Standardize column names
    col_mapping = {}
    for col in df.columns:
        col_lower = str(col).lower()
        if 'date' in col_lower and 'Date' not in col_mapping.values():
            col_mapping[col] = 'Date'
        elif 'customer' in col_lower:
            if 'Customer' not in col_mapping.values():
                col_mapping[col] = 'Customer'
        elif 'amount' in col_lower or 'total' in col_lower:
            if 'Amount' not in col_mapping.values():
                col_mapping[col] = 'Amount'
        elif 'sales' in col_lower and 'rep' in col_lower:
            col_mapping[col] = 'Sales Rep'
        elif 'status' in col_lower:
            if 'Status' not in col_mapping.values():
                col_mapping[col] = 'Status'
    
    df = df.rename(columns=col_mapping)
    
    return df


@st.cache_data(ttl=CACHE_TTL)
def load_items() -> Optional[pd.DataFrame]:
    """Load Items/Products data with Calyx Product Type mapping."""
    df = load_sheet_to_dataframe('Raw_Items')
    
    if df is None or df.empty:
        for sheet_name in ['Items', 'Products', 'SKUs']:
            df = load_sheet_to_dataframe(sheet_name)
            if df is not None and not df.empty:
                break
    
    if df is None or df.empty:
        return None
    
    # Look for Calyx || Product Type column
    product_type_col = None
    for col in df.columns:
        if 'calyx' in str(col).lower() and 'product' in str(col).lower() and 'type' in str(col).lower():
            product_type_col = col
            break
        elif 'product type' in str(col).lower():
            product_type_col = col
    
    if product_type_col and product_type_col != 'Calyx || Product Type':
        df = df.rename(columns={product_type_col: 'Calyx || Product Type'})
    
    # Standardize Item Name column
    for col in df.columns:
        col_lower = str(col).lower()
        if ('item' in col_lower and 'name' in col_lower) or col_lower == 'name' or col_lower == 'item':
            if col != 'Item Name/Number':
                df = df.rename(columns={col: 'Item Name/Number'})
            break
    
    logger.info(f"Items loaded with columns: {list(df.columns)[:10]}")
    
    return df


@st.cache_data(ttl=CACHE_TTL)
def load_customers() -> Optional[pd.DataFrame]:
    """Load Customers data."""
    df = load_sheet_to_dataframe('Customers')
    
    if df is None or df.empty:
        for sheet_name in ['Customer', 'Accounts']:
            df = load_sheet_to_dataframe(sheet_name)
            if df is not None and not df.empty:
                break
    
    return df


@st.cache_data(ttl=CACHE_TTL)
def load_deals() -> Optional[pd.DataFrame]:
    """
    Load HubSpot Deals/Pipeline data.
    
    Handles:
    - Coefficient/HubSpot Import title row (Row 1) - ALWAYS skips to Row 2 for headers
    - Column name standardization including Amount
    
    v3.7.0 - Fixed Coefficient header row handling
    """
    # Load raw data directly to handle header row ourselves
    try:
        client = get_gspread_client()
        if client is None:
            return None
        
        spreadsheet_id = get_spreadsheet_id()
        if spreadsheet_id is None:
            return None
        
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # Try to find the Deals sheet
        worksheet = None
        sheet_loaded = None
        for sheet_name in ['Deals', 'All Reps All Pipelines', 'HubSpot Deals', 'Pipeline']:
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                sheet_loaded = sheet_name
                break
            except gspread.exceptions.WorksheetNotFound:
                continue
        
        if worksheet is None:
            logger.warning("Deals: No deals sheet found")
            return None
        
        # Get all values
        data = worksheet.get_all_values()
        
        if not data or len(data) < 3:
            logger.warning(f"Deals: Sheet '{sheet_loaded}' has insufficient data")
            return None
        
        logger.info(f"Deals: Loaded from sheet '{sheet_loaded}', {len(data)} rows")
        logger.info(f"Deals: Row 1 (raw): {data[0][:5]}...")
        logger.info(f"Deals: Row 2 (raw): {data[1][:8]}...")
        
        # Check if Row 1 is a Coefficient/HubSpot header row
        row1_text = ' '.join(str(x).lower() for x in data[0][:3])
        is_coefficient_header = any(kw in row1_text for kw in ['hubspot', 'import', 'coefficient', 'last updated'])
        
        # Also check if Row 1 has mostly empty cells (merged header row)
        row1_empty_count = sum(1 for x in data[0] if str(x).strip() == '')
        is_merged_header = row1_empty_count > len(data[0]) / 2
        
        # Check if Row 2 looks like actual headers
        row2_text = ' '.join(str(x).lower() for x in data[1][:10])
        row2_has_headers = any(kw in row2_text for kw in ['deal', 'amount', 'stage', 'date', 'name', 'record'])
        
        if (is_coefficient_header or is_merged_header) and row2_has_headers:
            # Skip Row 1, use Row 2 as headers
            headers = [str(x).strip() for x in data[1]]
            rows = data[2:]
            logger.info(f"Deals: Skipped Coefficient header, using Row 2 as headers: {headers[:8]}...")
        else:
            # Normal case - Row 1 is headers
            headers = [str(x).strip() for x in data[0]]
            rows = data[1:]
            logger.info(f"Deals: Using Row 1 as headers: {headers[:8]}...")
        
        # Handle duplicate column names
        seen = {}
        unique_headers = []
        for h in headers:
            if h in seen:
                seen[h] += 1
                unique_headers.append(f"{h}_{seen[h]}")
            else:
                seen[h] = 0
                unique_headers.append(h)
        
        df = pd.DataFrame(rows, columns=unique_headers)
        df = df.replace('', pd.NA)
        
        logger.info(f"Deals: Final columns: {list(df.columns)[:10]}...")
        
    except Exception as e:
        logger.error(f"Deals: Error loading: {e}")
        return None
    
    if df is None or df.empty:
        return None
    
    # Standardize column names - Check for exact matches first!
    col_mapping = {}
    found_amount = False
    
    for col in df.columns:
        col_str = str(col).strip()
        col_lower = col_str.lower()
        
        # Exact match for Amount (highest priority)
        if col_lower == 'amount':
            col_mapping[col] = 'Amount'
            found_amount = True
            logger.info(f"Deals: Found Amount column (exact match) as '{col}'")
        # Deal Name
        elif 'deal' in col_lower and 'name' in col_lower:
            col_mapping[col] = 'Deal Name'
        # Company/Customer
        elif col_lower == 'company' or col_lower == 'customer':
            if 'Company' not in col_mapping.values():
                col_mapping[col] = 'Company'
        # Stage (exact match first)
        elif col_lower == 'stage':
            if 'Stage' not in col_mapping.values():
                col_mapping[col] = 'Stage'
        # Close Date
        elif 'close' in col_lower and 'date' in col_lower:
            if 'Close Date' not in col_mapping.values():
                col_mapping[col] = 'Close Date'
        # SKU
        elif col_lower == 'sku':
            col_mapping[col] = 'SKU'
    
    # Second pass - look for Amount variations if not found yet
    if not found_amount:
        for col in df.columns:
            col_str = str(col).strip()
            col_lower = col_str.lower()
            
            # Check variations: 'deal amount', 'total amount', 'value', 'deal value', 'probability rev'
            if any(x in col_lower for x in ['amount', 'deal value', 'probability rev', 'revenue']):
                if col not in col_mapping:  # Don't override existing mappings
                    col_mapping[col] = 'Amount'
                    found_amount = True
                    logger.info(f"Deals: Found Amount column (variation) as '{col}'")
                    break
    
    df = df.rename(columns=col_mapping)
    
    # If Amount still not found, log a warning with all columns
    if 'Amount' not in df.columns:
        logger.warning(f"Deals: Amount column NOT FOUND! All columns: {list(df.columns)}")
    else:
        # Convert Amount to numeric
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        non_null = df['Amount'].notna().sum()
        total = df['Amount'].sum()
        logger.info(f"Deals: Amount column - {non_null} non-null values, total ${total:,.2f}")
    
    # Convert Close Date to datetime
    if 'Close Date' in df.columns:
        df['Close Date'] = pd.to_datetime(df['Close Date'], errors='coerce')
        logger.info(f"Deals: Close Date - {df['Close Date'].notna().sum()} valid dates")
    
    logger.info(f"Deals loaded: {len(df)} rows, final columns: {list(df.columns)}")
    
    return df


@st.cache_data(ttl=CACHE_TTL)
def load_inventory() -> Optional[pd.DataFrame]:
    """Load Inventory data."""
    df = load_sheet_to_dataframe('Inventory')
    
    if df is None or df.empty:
        for sheet_name in ['Stock', 'Inventory_Levels']:
            df = load_sheet_to_dataframe(sheet_name)
            if df is not None and not df.empty:
                break
    
    return df


@st.cache_data(ttl=CACHE_TTL)
def load_revenue_forecast() -> Optional[pd.DataFrame]:
    """Load Revenue Forecast data from Google Sheets."""
    df = load_sheet_to_dataframe('Revenue Forecast')
    
    if df is None or df.empty:
        for sheet_name in ['RevenueForecast', 'Forecast', 'Revenue_Forecast']:
            df = load_sheet_to_dataframe(sheet_name)
            if df is not None and not df.empty:
                break
    
    if df is not None:
        logger.info(f"Revenue Forecast loaded: {len(df)} rows, columns: {list(df.columns)[:10]}")
    
    return df


def get_product_type_mapping() -> Dict[str, str]:
    """Get mapping of Item Name to Calyx Product Type."""
    items = load_items()
    
    if items is None or items.empty:
        return {}
    
    if 'Item Name/Number' not in items.columns or 'Calyx || Product Type' not in items.columns:
        logger.warning("Items table missing required columns for product type mapping")
        return {}
    
    mapping = items.set_index('Item Name/Number')['Calyx || Product Type'].to_dict()
    
    return mapping


def enrich_with_product_type(df: pd.DataFrame, item_col: str = 'Item Name/Number') -> pd.DataFrame:
    """Add Calyx Product Type column to a dataframe based on item name."""
    if df is None or df.empty:
        return df
    
    if item_col not in df.columns:
        return df
    
    mapping = get_product_type_mapping()
    
    if not mapping:
        return df
    
    df = df.copy()
    df['Calyx || Product Type'] = df[item_col].map(mapping)
    
    return df


def get_all_data() -> Dict[str, Optional[pd.DataFrame]]:
    """Load all data sources and return as dictionary."""
    return {
        'invoice_lines': load_invoice_lines(),
        'sales_orders': load_sales_orders(),
        'items': load_items(),
        'customers': load_customers(),
        'deals': load_deals(),
        'inventory': load_inventory(),
        'revenue_forecast': load_revenue_forecast()
    }


# Aliases for backwards compatibility
load_invoices = load_invoice_lines
load_so_lines = load_sales_orders
load_so = load_sales_orders


def get_data_hash(df: Optional[pd.DataFrame]) -> str:
    """Generate a hash for a dataframe for caching purposes."""
    if df is None or df.empty:
        return "empty"
    
    # Use shape and first/last values as a quick hash
    try:
        hash_str = f"{df.shape}_{df.iloc[0].tolist()}_{df.iloc[-1].tolist()}"
        return hashlib.md5(hash_str.encode()).hexdigest()[:8]
    except Exception:
        return str(hash(str(df.shape)))


@st.cache_data(ttl=CACHE_TTL)
def get_topdown_item_forecast() -> pd.DataFrame:
    """
    Generate top-down item-level forecast by allocating category forecasts to items
    based on historical sales mix.
    """
    invoice_lines = load_invoice_lines()
    items = load_items()
    revenue_forecast = load_revenue_forecast()
    
    if invoice_lines is None or items is None:
        return pd.DataFrame()
    
    # Enrich invoice lines with product type
    df = enrich_with_product_type(invoice_lines)
    
    if 'Calyx || Product Type' not in df.columns:
        logger.warning("Could not map product types for top-down forecast")
        return pd.DataFrame()
    
    # Calculate historical item mix within each category
    if 'Amount' not in df.columns or 'Item Name/Number' not in df.columns:
        return pd.DataFrame()
    
    # Group by category and item to get historical proportions
    category_totals = df.groupby('Calyx || Product Type')['Amount'].sum()
    item_totals = df.groupby(['Calyx || Product Type', 'Item Name/Number'])['Amount'].sum()
    
    # Calculate mix percentage
    item_mix = item_totals / item_totals.groupby(level=0).transform('sum')
    item_mix = item_mix.reset_index()
    item_mix.columns = ['Category', 'Item', 'Mix_Pct']
    
    # Calculate average selling price
    item_qty = df.groupby('Item Name/Number')['Quantity'].sum()
    item_rev = df.groupby('Item Name/Number')['Amount'].sum()
    item_asp = (item_rev / item_qty).reset_index()
    item_asp.columns = ['Item', 'ASP']
    
    # Merge ASP into mix
    item_mix = item_mix.merge(item_asp, on='Item', how='left')
    item_mix['ASP'] = item_mix['ASP'].fillna(item_mix['ASP'].median())
    
    return item_mix


# Utility functions for data validation
def validate_data_loaded() -> Dict[str, bool]:
    """Check which data sources loaded successfully."""
    data = get_all_data()
    return {key: (df is not None and not df.empty) for key, df in data.items()}


def get_data_summary() -> Dict[str, Any]:
    """Get summary statistics for all loaded data."""
    data = get_all_data()
    summary = {}
    
    for key, df in data.items():
        if df is not None and not df.empty:
            summary[key] = {
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': list(df.columns)[:10]
            }
        else:
            summary[key] = {'rows': 0, 'columns': 0, 'column_names': []}
    
    return summary
