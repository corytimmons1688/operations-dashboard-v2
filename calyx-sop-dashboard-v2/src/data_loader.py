"""
S&OP Data Loader Module
Handles all Google Sheets data ingestion for the S&OP Dashboard

Data Sources:
- _NS_Invoices_Data: Invoice header data
- Invoice Line Item: Invoice line details
- Sales Order Line Item: SO line details
- _NS_SalesOrders_Data: Sales order header data
- _NS_Customer_List: Customer master data
- Raw_Items: Item/SKU master data
- Raw_Vendors: Vendor master data
- Raw_Inventory: Current inventory levels
- SO & invoice Data merged: Combined SO/Invoice data
- Deals: HubSpot pipeline data

Author: Xander @ Calyx Containers
"""

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from typing import Optional, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Google Sheets API Scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

# Sheet Configuration
SHEET_CONFIG = {
    'invoices': '_NS_Invoices_Data',
    'invoice_lines': 'Invoice Line Item',
    'so_lines': 'Sales Order Line Item',
    'sales_orders': '_NS_SalesOrders_Data',
    'customers': '_NS_Customer_List',
    'items': 'Raw_Items',
    'vendors': 'Raw_Vendors',
    'inventory': 'Raw_Inventory',
    'so_invoice_merged': 'SO & invoice Data merged',
    'deals': 'Deals',
    'nc_details': 'Non-Conformance Details'
}

# Column type configurations for each sheet
COLUMN_TYPES = {
    'invoices': {
        'date_columns': ['Date', 'Due Date', 'Date Closed'],
        'numeric_columns': ['Amount (Transaction Total)', 'Amount Remaining', 
                          'Amount (Shipping)', 'Amount (Transaction Tax Total)']
    },
    'invoice_lines': {
        'date_columns': ['Date', 'Due Date', 'Date Closed'],
        'numeric_columns': ['Quantity', 'Amount', 'Amount (Transaction Total)', 
                          'Amount Remaining', 'Amount (Shipping)', 'Amount (Transaction Tax Total)']
    },
    'so_lines': {
        'date_columns': ['Pending Fulfillment Date', 'Actual Ship Date', 'Date Created', 
                        'Date Billed', 'Date Closed'],
        'numeric_columns': ['Amount', 'Item Rate', 'Quantity Ordered', 'Quantity Fulfilled',
                          'Transaction Discount']
    },
    'sales_orders': {
        'date_columns': ['Order Start Date', 'Pending Fulfillment Date', 'Actual Ship Date',
                        'Customer Promise Last Date to Ship', 'Projected Date', 
                        'Do Not Ship Before', 'Sales Management Approved Date',
                        'Sales Approved Date', 'Pending Approval Date'],
        'numeric_columns': ['Amount (Transaction Total)', 'Amount (Shipping)', 
                          'Amount (Transaction Tax Total)']
    },
    'customers': {
        'date_columns': [],
        'numeric_columns': []
    },
    'items': {
        'date_columns': [],
        'numeric_columns': ['Purchase Price', 'Purchase Lead Time']
    },
    'vendors': {
        'date_columns': [],
        'numeric_columns': []
    },
    'inventory': {
        'date_columns': [],
        'numeric_columns': ['On Hand', 'Average Cost']
    },
    'deals': {
        'date_columns': ['Close Date', 'Create Date', 'Pending Approval Date'],
        'numeric_columns': ['Amount', 'Average Leadtime']
    }
}


def get_google_credentials() -> Optional[Credentials]:
    """
    Retrieve Google credentials from Streamlit secrets.
    
    Returns:
        Credentials object or None if not configured
    """
    try:
        # Check for service_account format
        if "service_account" in st.secrets:
            credentials_dict = dict(st.secrets["service_account"])
        elif "gcp_service_account" in st.secrets:
            credentials_dict = dict(st.secrets["gcp_service_account"])
        else:
            logger.warning("Service account not found in secrets")
            return None
        
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=SCOPES
        )
        return credentials
        
    except Exception as e:
        logger.error(f"Error getting credentials: {e}")
        return None


def get_gspread_client() -> Optional[gspread.Client]:
    """
    Get authenticated gspread client.
    
    Returns:
        gspread Client or None if authentication fails
    """
    credentials = get_google_credentials()
    if credentials is None:
        return None
    
    try:
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        logger.error(f"Error creating gspread client: {e}")
        return None


def get_spreadsheet_id() -> Optional[str]:
    """Get spreadsheet ID from secrets."""
    if "SPREADSHEET_ID" in st.secrets:
        return st.secrets["SPREADSHEET_ID"]
    elif "google_sheets" in st.secrets:
        return st.secrets["google_sheets"].get("spreadsheet_id")
    return None


def clean_numeric_column(series: pd.Series) -> pd.Series:
    """Clean and convert a series to numeric."""
    if series.dtype == 'object':
        # Remove currency symbols, commas, etc.
        series = series.astype(str).str.replace(r'[\$,]', '', regex=True)
        series = series.str.replace(r'^\s*$', 'nan', regex=True)
    return pd.to_numeric(series, errors='coerce')


def clean_date_column(series: pd.Series) -> pd.Series:
    """Clean and convert a series to datetime."""
    return pd.to_datetime(series, errors='coerce')


def process_dataframe(df: pd.DataFrame, sheet_key: str) -> pd.DataFrame:
    """
    Process a dataframe by converting columns to appropriate types.
    
    Args:
        df: Raw dataframe
        sheet_key: Key to look up column types
        
    Returns:
        Processed dataframe
    """
    if sheet_key not in COLUMN_TYPES:
        return df
    
    config = COLUMN_TYPES[sheet_key]
    
    # Convert date columns
    for col in config.get('date_columns', []):
        if col in df.columns:
            df[col] = clean_date_column(df[col])
    
    # Convert numeric columns
    for col in config.get('numeric_columns', []):
        if col in df.columns:
            df[col] = clean_numeric_column(df[col])
    
    return df


@st.cache_data(ttl=300, show_spinner="Loading data...")
def load_sheet_data(sheet_name: str, sheet_key: str = None) -> Optional[pd.DataFrame]:
    """
    Load data from a specific Google Sheet tab.
    
    Args:
        sheet_name: Name of the sheet tab
        sheet_key: Key for column type processing
        
    Returns:
        DataFrame with sheet data or None if loading fails
    """
    try:
        spreadsheet_id = get_spreadsheet_id()
        if not spreadsheet_id:
            logger.error("Spreadsheet ID not found in secrets")
            return None
        
        client = get_gspread_client()
        if client is None:
            return None
        
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # Get all values first to handle duplicate headers
        all_values = worksheet.get_all_values()
        
        if not all_values or len(all_values) < 2:
            logger.warning(f"No data found in worksheet: {sheet_name}")
            return pd.DataFrame()
        
        # Get headers and deduplicate them
        headers = all_values[0]
        seen = {}
        unique_headers = []
        for h in headers:
            h_str = str(h).strip() if h else 'Unnamed'
            if not h_str:
                h_str = 'Unnamed'
            if h_str in seen:
                seen[h_str] += 1
                unique_headers.append(f"{h_str}_{seen[h_str]}")
            else:
                seen[h_str] = 0
                unique_headers.append(h_str)
        
        # Create DataFrame with unique headers
        df = pd.DataFrame(all_values[1:], columns=unique_headers)
        
        # Remove completely empty/unnamed columns
        cols_to_keep = [c for c in df.columns if not c.startswith('Unnamed')]
        df = df[cols_to_keep]
        
        # Process column types if sheet_key provided
        if sheet_key:
            df = process_dataframe(df, sheet_key)
        
        logger.info(f"Loaded {len(df)} records from {sheet_name}")
        return df
        
    except gspread.exceptions.WorksheetNotFound:
        logger.error(f"Worksheet '{sheet_name}' not found")
        return None
    except Exception as e:
        logger.error(f"Error loading {sheet_name}: {e}")
        return None


# Specific loader functions for each data source
@st.cache_data(ttl=300, show_spinner="Loading invoices...")
def load_invoices() -> Optional[pd.DataFrame]:
    """Load invoice header data."""
    return load_sheet_data(SHEET_CONFIG['invoices'], 'invoices')


@st.cache_data(ttl=300, show_spinner="Loading invoice lines...")
def load_invoice_lines() -> Optional[pd.DataFrame]:
    """Load invoice line item data."""
    return load_sheet_data(SHEET_CONFIG['invoice_lines'], 'invoice_lines')


@st.cache_data(ttl=300, show_spinner="Loading sales order lines...")
def load_so_lines() -> Optional[pd.DataFrame]:
    """Load sales order line item data."""
    return load_sheet_data(SHEET_CONFIG['so_lines'], 'so_lines')


@st.cache_data(ttl=300, show_spinner="Loading sales orders...")
def load_sales_orders() -> Optional[pd.DataFrame]:
    """Load sales order header data."""
    return load_sheet_data(SHEET_CONFIG['sales_orders'], 'sales_orders')


@st.cache_data(ttl=300, show_spinner="Loading customers...")
def load_customers() -> Optional[pd.DataFrame]:
    """Load customer master data."""
    return load_sheet_data(SHEET_CONFIG['customers'], 'customers')


@st.cache_data(ttl=300, show_spinner="Loading items...")
def load_items() -> Optional[pd.DataFrame]:
    """Load item/SKU master data."""
    return load_sheet_data(SHEET_CONFIG['items'], 'items')


@st.cache_data(ttl=300, show_spinner="Loading vendors...")
def load_vendors() -> Optional[pd.DataFrame]:
    """Load vendor master data."""
    return load_sheet_data(SHEET_CONFIG['vendors'], 'vendors')


@st.cache_data(ttl=300, show_spinner="Loading inventory...")
def load_inventory() -> Optional[pd.DataFrame]:
    """Load current inventory data."""
    return load_sheet_data(SHEET_CONFIG['inventory'], 'inventory')


@st.cache_data(ttl=300, show_spinner="Loading pipeline deals...")
def load_deals() -> Optional[pd.DataFrame]:
    """Load HubSpot pipeline/deals data."""
    return load_sheet_data(SHEET_CONFIG['deals'], 'deals')


@st.cache_data(ttl=300, show_spinner="Loading merged SO/Invoice data...")
def load_so_invoice_merged() -> Optional[pd.DataFrame]:
    """Load merged SO and Invoice data."""
    return load_sheet_data(SHEET_CONFIG['so_invoice_merged'])


@st.cache_data(ttl=300, show_spinner="Loading NC data...")
def load_nc_data() -> Optional[pd.DataFrame]:
    """Load Non-Conformance data for Quality tab."""
    return load_sheet_data(SHEET_CONFIG['nc_details'])


@st.cache_data(ttl=600)
def load_all_sop_data() -> Dict[str, Optional[pd.DataFrame]]:
    """
    Load all S&OP data sources at once.
    
    Returns:
        Dictionary with all dataframes
    """
    return {
        'invoices': load_invoices(),
        'invoice_lines': load_invoice_lines(),
        'so_lines': load_so_lines(),
        'sales_orders': load_sales_orders(),
        'customers': load_customers(),
        'items': load_items(),
        'vendors': load_vendors(),
        'inventory': load_inventory(),
        'deals': load_deals(),
        'so_invoice_merged': load_so_invoice_merged()
    }


def get_unique_sales_reps(sales_orders: pd.DataFrame) -> list:
    """Get unique sales rep names from sales orders."""
    if sales_orders is None or 'Rep Master' not in sales_orders.columns:
        return []
    return sorted(sales_orders['Rep Master'].dropna().unique().tolist())


def get_unique_customers(sales_orders: pd.DataFrame) -> list:
    """Get unique customer names from sales orders."""
    if sales_orders is None:
        return []
    
    # Try different customer column names
    for col in ['Customer', 'Corrected Customer Name', 'Customer Companyname']:
        if col in sales_orders.columns:
            return sorted(sales_orders[col].dropna().unique().tolist())
    return []


def get_unique_product_types(items: pd.DataFrame) -> list:
    """Get unique product types from items."""
    if items is None or 'Calyx || Product Type' not in items.columns:
        return []
    return sorted(items['Calyx || Product Type'].dropna().unique().tolist())


def get_unique_skus(items: pd.DataFrame) -> list:
    """Get unique SKUs from items."""
    if items is None or 'SKU' not in items.columns:
        return []
    return sorted(items['SKU'].dropna().unique().tolist())


def get_customers_for_rep(sales_orders: pd.DataFrame, rep: str) -> list:
    """Get customers associated with a specific sales rep."""
    if sales_orders is None or 'Rep Master' not in sales_orders.columns:
        return []
    
    filtered = sales_orders[sales_orders['Rep Master'] == rep]
    
    for col in ['Customer', 'Corrected Customer Name', 'Customer Companyname']:
        if col in filtered.columns:
            return sorted(filtered[col].dropna().unique().tolist())
    return []


def get_skus_for_customer(invoice_lines: pd.DataFrame, customer: str) -> list:
    """Get SKUs historically ordered by a specific customer."""
    if invoice_lines is None:
        return []
    
    # Find the customer column
    customer_col = None
    for col in ['Correct Customer', 'Customer']:
        if col in invoice_lines.columns:
            customer_col = col
            break
    
    if customer_col is None:
        return []
    
    filtered = invoice_lines[invoice_lines[customer_col] == customer]
    
    if 'Item' in filtered.columns:
        return sorted(filtered['Item'].dropna().unique().tolist())
    return []


def prepare_demand_history(invoice_lines: pd.DataFrame, 
                           groupby_cols: list = ['Item'],
                           date_col: str = 'Date',
                           qty_col: str = 'Quantity',
                           freq: str = 'M') -> pd.DataFrame:
    """
    Prepare demand history for forecasting.
    
    Args:
        invoice_lines: Invoice line data
        groupby_cols: Columns to group by (e.g., ['Item'], ['Item', 'Customer'])
        date_col: Name of date column
        qty_col: Name of quantity column
        freq: Frequency for resampling ('D', 'W', 'M', 'Q')
        
    Returns:
        DataFrame with demand history aggregated by time period
    """
    if invoice_lines is None or invoice_lines.empty:
        return pd.DataFrame()
    
    df = invoice_lines.copy()
    
    # Ensure date column is datetime
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    # Drop rows with invalid dates
    df = df.dropna(subset=[date_col])
    
    # Set date as index
    df = df.set_index(date_col)
    
    # Group and resample
    if groupby_cols:
        demand = df.groupby(groupby_cols)[qty_col].resample(freq).sum().reset_index()
    else:
        demand = df[qty_col].resample(freq).sum().reset_index()
    
    demand.columns = groupby_cols + ['Period', 'Demand'] if groupby_cols else ['Period', 'Demand']
    
    return demand


def prepare_revenue_history(invoice_lines: pd.DataFrame,
                           groupby_cols: list = None,
                           date_col: str = 'Date',
                           amount_col: str = 'Amount',
                           freq: str = 'M') -> pd.DataFrame:
    """
    Prepare revenue history for forecasting.
    
    Args:
        invoice_lines: Invoice line data
        groupby_cols: Columns to group by
        date_col: Name of date column
        amount_col: Name of amount column
        freq: Frequency for resampling
        
    Returns:
        DataFrame with revenue history aggregated by time period
    """
    if invoice_lines is None or invoice_lines.empty:
        return pd.DataFrame()
    
    df = invoice_lines.copy()
    
    # Ensure date column is datetime
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    # Drop rows with invalid dates
    df = df.dropna(subset=[date_col])
    
    # Set date as index
    df = df.set_index(date_col)
    
    # Group and resample
    if groupby_cols:
        revenue = df.groupby(groupby_cols)[amount_col].resample(freq).sum().reset_index()
        revenue.columns = groupby_cols + ['Period', 'Revenue']
    else:
        revenue = df[amount_col].resample(freq).sum().reset_index()
        revenue.columns = ['Period', 'Revenue']
    
    return revenue


def get_pipeline_by_period(deals: pd.DataFrame, freq: str = 'M') -> pd.DataFrame:
    """
    Aggregate pipeline deals by close date period.
    
    Args:
        deals: Deals/pipeline data
        freq: Frequency for aggregation
        
    Returns:
        DataFrame with pipeline aggregated by period
    """
    if deals is None or deals.empty:
        return pd.DataFrame()
    
    df = deals.copy()
    
    # Check if required columns exist
    if 'Close Date' not in df.columns:
        logger.warning("'Close Date' column not found in Deals data")
        return pd.DataFrame()
    
    if 'Amount' not in df.columns:
        logger.warning("'Amount' column not found in Deals data")
        return pd.DataFrame()
    
    # Ensure close date is datetime
    df['Close Date'] = pd.to_datetime(df['Close Date'], errors='coerce')
    
    # Filter for open deals (not closed lost)
    if 'Close Status' in df.columns:
        df = df[df['Close Status'] != 'lost']
    
    # Drop rows with invalid dates
    df = df.dropna(subset=['Close Date'])
    
    if df.empty:
        return pd.DataFrame()
    
    # Set date as index and resample
    df = df.set_index('Close Date')
    
    pipeline = df['Amount'].resample(freq).sum().reset_index()
    pipeline.columns = ['Period', 'Pipeline_Amount']
    
    return pipeline


def calculate_lead_times(items: pd.DataFrame, vendors: pd.DataFrame = None) -> pd.DataFrame:
    """
    Calculate lead times for items, incorporating vendor terms if available.
    
    Args:
        items: Item master data
        vendors: Vendor master data
        
    Returns:
        DataFrame with item lead times
    """
    if items is None or items.empty:
        return pd.DataFrame()
    
    df = items[['SKU', 'Name', 'Purchase Lead Time', 'Calyx || Product Type']].copy()
    df = df.rename(columns={'Purchase Lead Time': 'Lead_Time_Days'})
    
    # Fill missing lead times with category average or default
    if df['Lead_Time_Days'].isna().any():
        # Calculate average by product type
        avg_by_type = df.groupby('Calyx || Product Type')['Lead_Time_Days'].transform('mean')
        df['Lead_Time_Days'] = df['Lead_Time_Days'].fillna(avg_by_type)
        
        # Fill remaining with overall average or default of 30 days
        overall_avg = df['Lead_Time_Days'].mean()
        df['Lead_Time_Days'] = df['Lead_Time_Days'].fillna(overall_avg if pd.notna(overall_avg) else 30)
    
    return df

