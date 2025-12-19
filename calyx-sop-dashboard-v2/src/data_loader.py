"""
Data Loader Module for NC (Non-Conformance) Dashboard
Handles loading and processing NC data from Google Sheets

Author: Xander @ Calyx Containers
Version: 3.1.0
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List
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
        if 'service_account' in st.secrets:
            creds_dict = dict(st.secrets['service_account'])
        elif 'gcp_service_account' in st.secrets:
            creds_dict = dict(st.secrets['gcp_service_account'])
        else:
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
# NC DATA LOADING
# =============================================================================

@st.cache_data(ttl=300)
def load_nc_data() -> Optional[pd.DataFrame]:
    """
    Load Non-Conformance data from Google Sheets.
    
    Returns:
        DataFrame with NC data or None if loading fails
    """
    try:
        client = get_google_sheets_client()
        if client is None:
            logger.warning("Google Sheets client not available, using sample data")
            return load_sample_data()
        
        spreadsheet_id = get_spreadsheet_id()
        if not spreadsheet_id:
            logger.warning("No spreadsheet ID configured, using sample data")
            return load_sample_data()
        
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # Try different sheet names for NC data
        sheet_names = ['Non-Conformance Details', 'NC Details', 'NC_Details', 'NCs', 'Non-Conformance']
        worksheet = None
        
        for name in sheet_names:
            try:
                worksheet = spreadsheet.worksheet(name)
                break
            except gspread.exceptions.WorksheetNotFound:
                continue
        
        if worksheet is None:
            logger.warning("NC sheet not found, using sample data")
            return load_sample_data()
        
        data = worksheet.get_all_values()
        
        if not data:
            return load_sample_data()
        
        # Handle duplicate column names
        headers = data[0]
        seen = {}
        new_headers = []
        for h in headers:
            if h in seen:
                seen[h] += 1
                new_headers.append(f"{h}_{seen[h]}")
            else:
                seen[h] = 0
                new_headers.append(h)
        
        df = pd.DataFrame(data[1:], columns=new_headers)
        
        # Standardize column names
        df = standardize_nc_columns(df)
        
        # Convert data types
        df = convert_nc_data_types(df)
        
        return df
        
    except Exception as e:
        logger.error(f"Error loading NC data: {e}")
        return load_sample_data()


def standardize_nc_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize NC column names."""
    col_mapping = {}
    
    for col in df.columns:
        col_lower = col.lower().strip()
        
        if 'nc' in col_lower and ('number' in col_lower or 'num' in col_lower or '#' in col_lower):
            col_mapping[col] = 'NC Number'
        elif col_lower in ['status', 'nc status']:
            col_mapping[col] = 'Status'
        elif 'priority' in col_lower:
            col_mapping[col] = 'Priority'
        elif 'customer' in col_lower:
            col_mapping[col] = 'Customer'
        elif 'date' in col_lower and ('created' in col_lower or 'open' in col_lower):
            col_mapping[col] = 'Date Created'
        elif 'date' in col_lower and 'close' in col_lower:
            col_mapping[col] = 'Date Closed'
        elif 'type' in col_lower and ('issue' in col_lower or 'nc' in col_lower):
            col_mapping[col] = 'Issue Type'
        elif 'root' in col_lower and 'cause' in col_lower:
            col_mapping[col] = 'Root Cause'
        elif 'cost' in col_lower or 'amount' in col_lower:
            col_mapping[col] = 'Cost'
        elif 'owner' in col_lower or 'assigned' in col_lower:
            col_mapping[col] = 'Owner'
        elif 'department' in col_lower or 'dept' in col_lower:
            col_mapping[col] = 'Department'
        elif 'product' in col_lower:
            col_mapping[col] = 'Product'
        elif 'description' in col_lower:
            col_mapping[col] = 'Description'
        elif 'external' in col_lower or 'internal' in col_lower:
            col_mapping[col] = 'External/Internal'
    
    df = df.rename(columns=col_mapping)
    
    return df


def convert_nc_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """Convert NC data types."""
    df = df.copy()
    
    # Date columns
    date_cols = ['Date Created', 'Date Closed']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Numeric columns
    if 'Cost' in df.columns:
        df['Cost'] = pd.to_numeric(df['Cost'].replace(r'[\$,]', '', regex=True), errors='coerce').fillna(0)
    
    # Calculate days open
    if 'Date Created' in df.columns:
        today = pd.Timestamp.now()
        if 'Date Closed' in df.columns:
            df['Days Open'] = df.apply(
                lambda row: (row['Date Closed'] - row['Date Created']).days 
                if pd.notna(row['Date Closed']) 
                else (today - row['Date Created']).days 
                if pd.notna(row['Date Created']) 
                else 0,
                axis=1
            )
        else:
            df['Days Open'] = df['Date Created'].apply(
                lambda x: (today - x).days if pd.notna(x) else 0
            )
    
    # Fill missing values
    if 'Status' in df.columns:
        df['Status'] = df['Status'].fillna('Unknown').replace('', 'Unknown')
    if 'Priority' in df.columns:
        df['Priority'] = df['Priority'].fillna('Medium').replace('', 'Medium')
    if 'Issue Type' in df.columns:
        df['Issue Type'] = df['Issue Type'].fillna('Unknown').replace('', 'Unknown')
    
    return df


def load_sample_data() -> pd.DataFrame:
    """Generate sample NC data for testing/demo purposes."""
    np.random.seed(42)
    n_records = 100
    
    statuses = ['Open', 'In Progress', 'Pending Review', 'Closed', 'On Hold']
    priorities = ['High', 'Medium', 'Low']
    issue_types = ['Quality Defect', 'Packaging Error', 'Labeling Issue', 'Shipping Damage', 
                   'Documentation Error', 'Customer Complaint', 'Process Deviation']
    customers = ['Acme Corp', 'Beta Industries', 'Gamma LLC', 'Delta Co', 'Epsilon Inc',
                 'Zeta Manufacturing', 'Eta Products', 'Theta Systems']
    departments = ['Production', 'QA', 'Shipping', 'Receiving', 'Packaging']
    owners = ['John Smith', 'Jane Doe', 'Bob Wilson', 'Alice Brown', 'Charlie Davis']
    products = ['Concentrate Jars', 'Flower Jars', 'Pre-Roll Tubes', 'Custom Packaging', 'Tray Inserts']
    
    # Generate dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    date_range = (end_date - start_date).days
    
    created_dates = [start_date + timedelta(days=np.random.randint(0, date_range)) for _ in range(n_records)]
    
    # Generate data
    data = {
        'NC Number': [f'NC-{2024000 + i}' for i in range(n_records)],
        'Status': np.random.choice(statuses, n_records, p=[0.25, 0.20, 0.15, 0.30, 0.10]),
        'Priority': np.random.choice(priorities, n_records, p=[0.2, 0.5, 0.3]),
        'Issue Type': np.random.choice(issue_types, n_records),
        'Customer': np.random.choice(customers, n_records),
        'Department': np.random.choice(departments, n_records),
        'Owner': np.random.choice(owners, n_records),
        'Product': np.random.choice(products, n_records),
        'Date Created': created_dates,
        'Cost': np.random.exponential(500, n_records).round(2),
        'External/Internal': np.random.choice(['External', 'Internal'], n_records, p=[0.4, 0.6]),
        'Description': [f'Sample NC description for record {i}' for i in range(n_records)]
    }
    
    df = pd.DataFrame(data)
    
    # Add closed dates for closed items
    df['Date Closed'] = df.apply(
        lambda row: row['Date Created'] + timedelta(days=np.random.randint(1, 30))
        if row['Status'] == 'Closed' else pd.NaT,
        axis=1
    )
    
    # Calculate days open
    today = pd.Timestamp.now()
    df['Days Open'] = df.apply(
        lambda row: (row['Date Closed'] - row['Date Created']).days 
        if pd.notna(row['Date Closed']) 
        else (today - row['Date Created']).days,
        axis=1
    )
    
    return df


# =============================================================================
# DATA REFRESH AND SUMMARY
# =============================================================================

def refresh_data() -> Optional[pd.DataFrame]:
    """Force refresh of NC data by clearing cache."""
    st.cache_data.clear()
    return load_nc_data()


def get_data_summary(df: pd.DataFrame = None) -> Dict:
    """
    Get summary statistics for NC data.
    
    Args:
        df: NC DataFrame (loads if not provided)
    
    Returns:
        Dictionary with summary statistics
    """
    if df is None:
        df = load_nc_data()
    
    if df is None or df.empty:
        return {
            'total_records': 0,
            'open_count': 0,
            'closed_count': 0,
            'high_priority': 0,
            'avg_days_open': 0,
            'total_cost': 0
        }
    
    summary = {
        'total_records': len(df),
        'open_count': len(df[df['Status'].isin(['Open', 'In Progress', 'Pending Review', 'On Hold'])]) if 'Status' in df.columns else 0,
        'closed_count': len(df[df['Status'] == 'Closed']) if 'Status' in df.columns else 0,
        'high_priority': len(df[df['Priority'] == 'High']) if 'Priority' in df.columns else 0,
        'avg_days_open': df['Days Open'].mean() if 'Days Open' in df.columns else 0,
        'total_cost': df['Cost'].sum() if 'Cost' in df.columns else 0
    }
    
    return summary


# =============================================================================
# FILTERING FUNCTIONS
# =============================================================================

def filter_nc_data(df: pd.DataFrame, 
                   status: str = None,
                   priority: str = None,
                   customer: str = None,
                   date_from: datetime = None,
                   date_to: datetime = None) -> pd.DataFrame:
    """
    Filter NC data based on criteria.
    
    Args:
        df: NC DataFrame
        status: Filter by status
        priority: Filter by priority
        customer: Filter by customer
        date_from: Start date
        date_to: End date
    
    Returns:
        Filtered DataFrame
    """
    if df is None or df.empty:
        return df
    
    filtered = df.copy()
    
    if status and status != 'All' and 'Status' in filtered.columns:
        filtered = filtered[filtered['Status'] == status]
    
    if priority and priority != 'All' and 'Priority' in filtered.columns:
        filtered = filtered[filtered['Priority'] == priority]
    
    if customer and customer != 'All' and 'Customer' in filtered.columns:
        filtered = filtered[filtered['Customer'] == customer]
    
    if date_from and 'Date Created' in filtered.columns:
        filtered = filtered[filtered['Date Created'] >= pd.Timestamp(date_from)]
    
    if date_to and 'Date Created' in filtered.columns:
        filtered = filtered[filtered['Date Created'] <= pd.Timestamp(date_to)]
    
    return filtered


def get_unique_values(df: pd.DataFrame, column: str) -> List[str]:
    """Get unique values from a column."""
    if df is None or df.empty or column not in df.columns:
        return []
    
    values = df[column].dropna().unique().tolist()
    return sorted([str(v) for v in values if v])


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'load_nc_data',
    'refresh_data',
    'get_data_summary',
    'load_sample_data',
    'filter_nc_data',
    'get_unique_values'
]
