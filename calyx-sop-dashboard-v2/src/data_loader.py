"""
Data Loader Module for NC Dashboard
Handles Google Sheets API connection and data retrieval

Author: Xander @ Calyx Containers
"""

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Google Sheets API scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

# Column definitions for the NC sheet
NC_COLUMNS = [
    'Year', 'Week', 'External Or Internal', 'NC Number', 'Priority',
    'Sales Order', 'Related Ticket Numbers', 'Customer', 'Issue Type',
    'Employee Responsible', 'Defect Summary', 'Status', 'Affected Items',
    'On Time Ship Date', 'Total Quantity Affected', 'Cost of Rework',
    'Cost Avoided', 'Date Submitted', 'Equipment', 'First Article Completed',
    'First Article Inspector'
]


def get_google_credentials() -> Optional[Credentials]:
    """
    Retrieve Google credentials from Streamlit secrets.
    
    Supports two secret formats:
    1. [service_account] - flat structure
    2. [gcp_service_account] - nested structure
    
    Returns:
        Credentials object or None if not configured
    """
    try:
        # Check for service_account format (user's format)
        if "service_account" in st.secrets:
            credentials_dict = dict(st.secrets["service_account"])
        # Check for gcp_service_account format (original format)
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
    Create and return a gspread client with proper authentication.
    
    Returns:
        gspread Client object or None if authentication fails
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


@st.cache_data(ttl=300, show_spinner="Loading NC data from Google Sheets...")
def load_nc_data() -> Optional[pd.DataFrame]:
    """
    Load Non-Conformance data from Google Sheets.
    
    Data is cached for 5 minutes (300 seconds) to improve performance.
    
    Supports two secret formats:
    1. SPREADSHEET_ID at root level + [service_account]
    2. [google_sheets] with spreadsheet_id + [gcp_service_account]
    
    Returns:
        DataFrame with NC data or None if loading fails
    """
    try:
        # Get spreadsheet configuration from secrets (support both formats)
        if "SPREADSHEET_ID" in st.secrets:
            # User's format: SPREADSHEET_ID at root level
            spreadsheet_id = st.secrets["SPREADSHEET_ID"]
            sheet_name = st.secrets.get("SHEET_NAME", "Non-Conformance Details")
        elif "google_sheets" in st.secrets:
            # Original format: nested under google_sheets
            spreadsheet_id = st.secrets["google_sheets"]["spreadsheet_id"]
            sheet_name = st.secrets["google_sheets"].get("sheet_name", "Non-Conformance Details")
        else:
            logger.error("Spreadsheet ID not found in secrets")
            st.error("Spreadsheet ID not configured. Add SPREADSHEET_ID to your secrets.")
            return None
        
        # Get gspread client
        client = get_gspread_client()
        if client is None:
            st.error("Failed to authenticate with Google Sheets API")
            return None
        
        # Open spreadsheet and worksheet
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # Get all data
        data = worksheet.get_all_records()
        
        if not data:
            logger.warning("No data found in worksheet")
            return pd.DataFrame(columns=NC_COLUMNS)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Data type conversions
        df = clean_and_transform_data(df)
        
        logger.info(f"Loaded {len(df)} records from Google Sheets")
        return df
        
    except gspread.exceptions.SpreadsheetNotFound:
        logger.error("Spreadsheet not found. Check the spreadsheet ID.")
        st.error("Spreadsheet not found. Please verify the spreadsheet ID in secrets.")
        return None
        
    except gspread.exceptions.WorksheetNotFound:
        logger.error(f"Worksheet '{sheet_name}' not found.")
        st.error(f"Worksheet '{sheet_name}' not found. Please verify the sheet name.")
        return None
        
    except gspread.exceptions.APIError as e:
        logger.error(f"Google Sheets API error: {e}")
        st.error(f"API Error: {str(e)}")
        return None
        
    except Exception as e:
        logger.error(f"Unexpected error loading data: {e}")
        st.error(f"Error loading data: {str(e)}")
        return None


def clean_and_transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and transform the raw data from Google Sheets.
    
    Args:
        df: Raw DataFrame from Google Sheets
        
    Returns:
        Cleaned and transformed DataFrame
    """
    # Make a copy to avoid modifying original
    df = df.copy()
    
    # Convert date columns
    date_columns = ['Date Submitted', 'On Time Ship Date']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Convert numeric columns
    numeric_columns = [
        'Year', 'Week', 'Total Quantity Affected', 
        'Cost of Rework', 'Cost Avoided'
    ]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Fill NaN values for cost columns with 0
    cost_columns = ['Cost of Rework', 'Cost Avoided']
    for col in cost_columns:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    
    # Clean string columns - strip whitespace
    string_columns = [
        'External Or Internal', 'NC Number', 'Priority', 'Sales Order',
        'Customer', 'Issue Type', 'Employee Responsible', 'Status',
        'Defect Summary', 'Affected Items', 'Equipment',
        'First Article Completed', 'First Article Inspector'
    ]
    for col in string_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            # Replace 'nan' string with empty string
            df[col] = df[col].replace('nan', '')
    
    # Add calculated columns
    if 'Date Submitted' in df.columns:
        # Calculate age in days
        df['Age_Days'] = (datetime.now() - df['Date Submitted']).dt.days
        df['Age_Days'] = df['Age_Days'].fillna(0).astype(int)
        
        # Calculate aging bucket
        df['Aging_Bucket'] = df['Age_Days'].apply(categorize_aging)
        
        # Extract month and year for aggregations
        df['Month'] = df['Date Submitted'].dt.to_period('M')
        df['Quarter'] = df['Date Submitted'].dt.to_period('Q')
        df['Year_Submitted'] = df['Date Submitted'].dt.year
        df['Week_Submitted'] = df['Date Submitted'].dt.isocalendar().week
    
    return df


def categorize_aging(days: int) -> str:
    """
    Categorize age in days into aging buckets.
    
    Args:
        days: Number of days since submission
        
    Returns:
        Aging bucket category string
    """
    if pd.isna(days) or days < 0:
        return "Unknown"
    elif days <= 30:
        return "0-30 days"
    elif days <= 60:
        return "31-60 days"
    elif days <= 90:
        return "61-90 days"
    else:
        return "90+ days"


def refresh_data() -> None:
    """
    Clear the data cache to force a refresh from Google Sheets.
    """
    load_nc_data.clear()
    logger.info("Data cache cleared - will refresh on next load")


def get_data_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate summary statistics for the NC data.
    
    Args:
        df: NC DataFrame
        
    Returns:
        Dictionary with summary statistics
    """
    if df is None or df.empty:
        return {}
    
    summary = {
        'total_records': len(df),
        'date_range': {
            'min': df['Date Submitted'].min() if 'Date Submitted' in df.columns else None,
            'max': df['Date Submitted'].max() if 'Date Submitted' in df.columns else None
        },
        'total_cost_of_rework': df['Cost of Rework'].sum() if 'Cost of Rework' in df.columns else 0,
        'total_cost_avoided': df['Cost Avoided'].sum() if 'Cost Avoided' in df.columns else 0,
        'unique_customers': df['Customer'].nunique() if 'Customer' in df.columns else 0,
        'unique_issue_types': df['Issue Type'].nunique() if 'Issue Type' in df.columns else 0,
        'status_breakdown': df['Status'].value_counts().to_dict() if 'Status' in df.columns else {}
    }
    
    return summary


# For testing/demo purposes - load sample data if sheets not configured
def load_sample_data() -> pd.DataFrame:
    """
    Load sample NC data for testing/demo purposes.
    
    Returns:
        DataFrame with sample NC data
    """
    import numpy as np
    
    np.random.seed(42)
    n_records = 100
    
    sample_data = {
        'Year': np.random.choice([2023, 2024, 2025], n_records),
        'Week': np.random.randint(1, 53, n_records),
        'External Or Internal': np.random.choice(['External', 'Internal'], n_records),
        'NC Number': [f'NC-{i:04d}' for i in range(1, n_records + 1)],
        'Priority': np.random.choice(['High', 'Medium', 'Low'], n_records),
        'Sales Order': [f'SO-{np.random.randint(10000, 99999)}' for _ in range(n_records)],
        'Related Ticket Numbers': [f'TKT-{np.random.randint(1000, 9999)}' for _ in range(n_records)],
        'Customer': np.random.choice([
            'Customer A', 'Customer B', 'Customer C', 'Customer D',
            'Customer E', 'Customer F', 'Customer G', 'Customer H'
        ], n_records),
        'Issue Type': np.random.choice([
            'Packaging Defect', 'Print Quality', 'Dimension Error',
            'Material Issue', 'Shipping Damage', 'Labeling Error',
            'Color Mismatch', 'Seal Failure'
        ], n_records),
        'Employee Responsible': np.random.choice([
            'John Smith', 'Jane Doe', 'Bob Wilson', 'Alice Brown'
        ], n_records),
        'Defect Summary': ['Sample defect description'] * n_records,
        'Status': np.random.choice([
            'Open', 'In Progress', 'Pending Review', 'Closed', 'On Hold'
        ], n_records, p=[0.3, 0.25, 0.15, 0.25, 0.05]),
        'Affected Items': np.random.choice(['Item A', 'Item B', 'Item C'], n_records),
        'On Time Ship Date': pd.date_range(end=datetime.now(), periods=n_records, freq='D'),
        'Total Quantity Affected': np.random.randint(10, 5000, n_records),
        'Cost of Rework': np.random.uniform(50, 5000, n_records).round(2),
        'Cost Avoided': np.random.uniform(100, 10000, n_records).round(2),
        'Date Submitted': pd.date_range(end=datetime.now(), periods=n_records, freq='D'),
        'Equipment': np.random.choice(['Printer 1', 'Printer 2', 'Cutter A', 'Sealer B'], n_records),
        'First Article Completed': np.random.choice(['Yes', 'No'], n_records),
        'First Article Inspector': np.random.choice(['Inspector 1', 'Inspector 2', 'Inspector 3'], n_records)
    }
    
    df = pd.DataFrame(sample_data)
    return clean_and_transform_data(df)
