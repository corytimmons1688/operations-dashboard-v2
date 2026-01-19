"""
2026 Annual Goal Tracker
Progress vs. Plan for Acquisition, Growth, and Retention by Category

Data Sources:
- 2026 Forecast: Planned revenue by Pipeline and Category (monthly/quarterly/annual)
- Invoice Line Item: Actual invoiced revenue (categorized via categorize_product())
- _NS_Invoices_Data: Pipeline lookup for invoices (HubSpot Pipeline column S)
- _NS_SalesOrders_Data: Pending orders not yet invoiced (HubSpot Pipeline column W)
- All Reps All Pipelines: HubSpot deals in pipeline (Pipeline column H)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
import numpy as np
import re

# ========== CONFIGURATION ==========
DEFAULT_SPREADSHEET_ID = "15JhBZ_7aHHZA1W1qsoC2163borL6RYjk0xTDWPmWPfA"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
CACHE_VERSION = "v2_annual_tracker"

# ========== CONSTANTS ==========

# Forecast Categories
FORECAST_CATEGORIES = ['Drams', 'Flexpack', 'Cure', 'Cube', 'Glass', 'Labels', 'Application', 'Shipping', 'Other']

# Forecast Pipelines  
FORECAST_PIPELINES = ['Retention', 'Growth', 'Acquisition', 'Distributors', 'Ecom']

# Category colors
CATEGORY_COLORS = {
    'Drams': '#3b82f6',
    'Flexpack': '#10b981',
    'Cure': '#8b5cf6',
    'Cube': '#f59e0b',
    'Glass': '#06b6d4',
    'Labels': '#ec4899',
    'Application': '#f97316',
    'Shipping': '#64748b',
    'Other': '#94a3b8',
    'Total': '#1e40af'
}

# Pipeline colors
PIPELINE_COLORS = {
    'Retention': '#10b981',
    'Growth': '#3b82f6',
    'Acquisition': '#8b5cf6',
    'Distributors': '#f59e0b',
    'Ecom': '#06b6d4',
    'Total': '#1e40af'
}

# Month mapping
MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 
               'July', 'August', 'September', 'October', 'November', 'December']
MONTH_ABBREV = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# Known Flexpack die tool codes
FLEXPACK_CODES = {
    '10155', '10292', '10293', '10337', '10338', '10359', '10360', '10362',
    '10363', '10385', '10386', '10387', '10388', '10389', '10390', '10391',
    '10392', '10393', '10394', '10396', '10400', '10403', '10404', '10405',
    '10406', '10407', '10427', '10428', '10429', '10459', '10460', '10461',
    '10462', '10463', '10464', '10497', '10552', '10553', '10554', '10556',
    '10557', '10558', '10559', '10560', '10561', '10562', '10563', '10564',
    '10565', '10566', '10567', '10569', '10570', '10571', '10572', '10573',
    '10574', '10575', '10576', '10577', '10578', '10584', '10585', '10586',
    '10597', '10598', '10599', '10600', '10601', '10602', '10603', '10604',
    '10606', '10607', '10609', '10612', '10616', '10617', '10620', '10621',
    '10624', '10625', '10627', '10628', '10629', '10630', '10631', '10633',
    '10635', '10637', '10638', '10639', '10640', '10641', '10642', '10643',
    '10644', '10645', '10646', '10647', '10648', '10649', '10650', '10651',
    '10652', '10653', '10654', '10655', '10656', '10657', '10658', '10659',
    '10663', '10664', '10667', '10668', '10669', '10680', '10681', '10686',
    '10687', '10688', '10691', '10692', '10693', '10694', '10696', '10700'
}


# ========== DATA LOADING ==========

@st.cache_data(ttl=300)
def load_google_sheets_data(sheet_name, range_name, version=CACHE_VERSION, silent=False):
    """Load data from Google Sheets with caching"""
    try:
        spreadsheet_id = st.secrets.get("SPREADSHEET_ID", DEFAULT_SPREADSHEET_ID)
        
        if "service_account" not in st.secrets:
            if not silent:
                st.error("❌ Missing Google Cloud credentials in Streamlit secrets")
            return pd.DataFrame()
        
        creds_dict = dict(st.secrets["service_account"])
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=SCOPES
        )
        
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!{range_name}"
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            if not silent:
                st.warning(f"⚠️ No data found in {sheet_name}!{range_name}")
            return pd.DataFrame()
        
        if len(values) > 1:
            max_cols = max(len(row) for row in values)
            for row in values:
                while len(row) < max_cols:
                    row.append('')
        
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
        
    except Exception as e:
        if not silent:
            st.error(f"❌ Error loading data from {sheet_name}: {str(e)}")
        return pd.DataFrame()


def clean_numeric(value):
    """Clean and convert a value to numeric"""
    if pd.isna(value) or str(value).strip() in ['', '$-', '-']:
        return 0.0
    cleaned = str(value).replace(',', '').replace('$', '').replace(' ', '').strip()
    try:
        return float(cleaned)
    except:
        return 0.0


# ========== PRODUCT CATEGORIZATION ==========

def extract_die_tool(item_name):
    """Extract die tool code from item name"""
    if pd.isna(item_name):
        return None, False
    
    name = str(item_name).upper().strip()
    
    match = re.search(r'-(\d{4,6})$', name)
    if match:
        return match.group(1), False
    
    match = re.search(r'-(\d{1,3}[LBPCH])-', name)
    if match:
        return match.group(1), True
    
    match = re.search(r'\((\d{4,6})\)', name)
    if match:
        return match.group(1), False
    
    match = re.search(r'-([47][CLH])-', name)
    if match:
        return match.group(1), True
    
    return None, False


def categorize_product(item_name, item_description="", calyx_product_type=""):
    """Categorize a product. Returns (category, sub_category, component_type) tuple."""
    if pd.isna(item_name):
        item_name = ""
    if pd.isna(item_description):
        item_description = ""
    if pd.isna(calyx_product_type):
        calyx_product_type = ""
    
    name = str(item_name).upper().strip()
    desc = str(item_description).upper().strip()
    product_type = str(calyx_product_type).upper().strip()
    all_text = f"{name} {desc}"
    
    die_tool, is_alphanumeric = extract_die_tool(item_name)
    
    # SHIPPING/TAXES/FEES
    if re.search(r'\bTAX\b|GST|HST|CANADIAN\s*(BUSINESS|GOODS)', all_text):
        return ('Fees & Adjustments', 'Taxes', None)
    if re.search(r'^SHIPPING|SHIPPING\s*FEE|FREIGHT', all_text):
        return ('Fees & Adjustments', 'Shipping', None)
    if re.search(r'EXPEDITE\s*FEE|RUSH\s*FEE', all_text):
        return ('Fees & Adjustments', 'Expedite Fee', None)
    if re.search(r'CONVENIENCE\s*FEE', all_text):
        return ('Fees & Adjustments', 'Convenience Fee', None)
    if re.search(r'^\$\d+OFF|DISCOUNT|PROMO|%\s*OFF', all_text):
        return ('Fees & Adjustments', 'Discount', None)
    if re.search(r'^ACCOUNTING|OVERPAYMENT|BAD\s*DEBT|REPLACEMENT\s*ORDER', all_text):
        return ('Fees & Adjustments', 'Accounting Adjustment', None)
    if re.search(r'DIE\s*CUT\s*SAMPLE|SAMPLE\s*CHARGE|CREATIVE$|TESTIMONIAL', all_text):
        return ('Fees & Adjustments', 'Sample/Creative', None)
    if re.search(r'TOOLING\s*FEE|TOOL\s*FEE|DIE\s*FEE|PLATE\s*FEE|SETUP\s*FEE', all_text):
        return ('Fees & Adjustments', 'Tooling Fee', None)
    if re.search(r'MODULAR.*SERIAL', all_text):
        return ('Fees & Adjustments', 'Other Fee', None)
    
    # CALYX CURE
    if name.startswith('CC-') or 'CALYX CURE' in all_text:
        return ('Calyx Cure', 'Calyx Cure', 'complete')
    
    # CALYX JAR (8TH Glass)
    if 'GB-8TH' in name or name.startswith('CJ-') or 'CALYX JAR' in all_text:
        return ('Calyx Jar', 'Glass Base', 'base')
    if re.search(r'-JB-', name):
        return ('Calyx Jar', 'Jar Base', 'base')
    if re.search(r'-JL-', name):
        return ('Calyx Jar', 'Jar Lid', 'lid')
    if 'SB-8TH' in name:
        return ('Calyx Jar', 'Shrink Band', 'band')
    
    # CONCENTRATES (4mL/7mL)
    if re.search(r'GB-4ML|4ML.*GLASS|4\s*ML.*BASE', name):
        return ('Concentrates', '4mL Glass Base', 'base')
    if re.search(r'GB-7ML|7ML.*GLASS|7\s*ML.*BASE', name):
        return ('Concentrates', '7mL Glass Base', 'base')
    if re.search(r'-4[CLH]-|-4[CLH]$', name) and not re.search(r'BOX|TUCK|AUTO|DISPLAY', all_text):
        return ('Concentrates', '4mL Lid', 'lid')
    if re.search(r'-7[CLH]-|-7[CLH]$', name) and not re.search(r'BOX|TUCK|AUTO|DISPLAY', all_text):
        return ('Concentrates', '7mL Lid', 'lid')
    if die_tool and is_alphanumeric and re.match(r'^[47][CLH]', die_tool):
        component = 'Lid Label' if 'L' in die_tool else 'Jar Label'
        size = '4mL' if die_tool.startswith('4') else '7mL'
        return ('Concentrates', f'{size} {component}', 'label')
    
    # DRAMS (15D, 25D, 45D, 145D)
    dram_sizes = ['145', '45', '25', '15']
    if die_tool and is_alphanumeric:
        for size in dram_sizes:
            if re.match(rf'^{size}[LBPH]', die_tool):
                size_d = f'{size}D'
                if 'L' in die_tool:
                    return ('Drams', f'{size_d} Lid Label', 'label')
                elif 'B' in die_tool or 'P' in die_tool:
                    return ('Drams', f'{size_d} Base Label', 'label')
                else:
                    return ('Drams', f'{size_d} Label', 'label')
    
    for size in dram_sizes:
        size_d = f'{size}D'
        if re.search(rf'PB-{size}D|{size}D.*BASE|-{size}B-', name):
            return ('Drams', f'{size_d} Base', 'base')
        if size != '15' and re.search(rf'^PL-{size}D|^CL-{size}D', name):
            return ('Drams', f'{size_d} Lid', 'lid')
        if f'{size}D LID' in all_text and not re.search(r'^[A-Z]{3,4}-[A-Z]{2}-', name):
            return ('Drams', f'{size_d} Lid', 'lid')
        if f'{size}D BASE' in all_text and not re.search(r'^[A-Z]{3,4}-[A-Z]{2}-', name):
            return ('Drams', f'{size_d} Base', 'base')
    
    # DML LIDS
    if 'DML' in name or re.search(r'PL-DML|CL-DML', name):
        if name.endswith('-F') or re.search(r'-\d+-F$', name):
            return ('Concentrates', 'Universal Lid (4mL/7mL)', 'lid')
        return ('DML (Universal)', 'Universal Lid', 'lid')
    if re.search(r'-15L-|^15L-', name) and 'DML' not in name:
        if die_tool and is_alphanumeric and die_tool.startswith('15'):
            return ('Drams', '15D Lid Label', 'label')
        return ('DML (Universal)', 'Universal Lid', 'lid')
    
    # DRAM ACCESSORIES
    if name.startswith('TF-') or 'TRAY FRAME' in all_text:
        return ('Dram Accessories', 'Tray Frame', 'accessory')
    if re.search(r'^TI-\d+D|TRAY INSERT', name):
        size_match = re.search(r'TI-(\d+)D', name)
        if size_match:
            return ('Dram Accessories', f'{size_match.group(1)}D Tray Insert', 'accessory')
        return ('Dram Accessories', 'Tray Insert', 'accessory')
    if re.search(r'SB-15D|SB-25D|SB-45D|SB-145D', name):
        size_match = re.search(r'SB-(\d+)D', name)
        if size_match:
            return ('Dram Accessories', f'{size_match.group(1)}D Shrink Band', 'band')
        return ('Dram Accessories', 'Shrink Band', 'band')
    if 'FEP' in name and 'LINER' in all_text:
        return ('Dram Accessories', 'FEP Liner', 'accessory')
    if re.search(r'SG-|STICK.*GRIP', all_text):
        return ('Dram Accessories', 'Stick & Grip', 'accessory')
    
    # TUBES
    if re.search(r'JT-116|116\s*MM|116T|-116-|116P', name) and 'BOX' not in all_text:
        if 'LABEL' in all_text or (die_tool and '116' in die_tool):
            return ('Tubes', '116mm Label', 'label')
        return ('Tubes', '116mm Tube', 'complete')
    if re.search(r'JT-90|90\s*MM|90T|-90-|90M', name) and 'BOX' not in all_text and 'WAVEPACK' not in all_text:
        if 'LABEL' in all_text or (die_tool and '90' in die_tool):
            return ('Tubes', '90mm Label', 'label')
        return ('Tubes', '90mm Tube', 'complete')
    if re.search(r'JT-84|84\s*MM|84T|-84-', name) and 'TUBE' in all_text:
        if 'LABEL' in all_text:
            return ('Tubes', '84mm Label', 'label')
        return ('Tubes', '84mm Tube', 'complete')
    
    # BOXES
    box_keywords = ['CORE AUTO', 'AUTOBOTTOM', 'AUTO BOTTOM', 'CORE TUCK', 
                    'REVERSE TUCK', 'ELEVATED TUCK', 'ELEVATED AUTO']
    if any(kw in all_text for kw in box_keywords) and 'BAG' not in all_text:
        if 'AUTO' in all_text:
            return ('Boxes', 'Core Auto', 'complete')
        if 'TUCK' in all_text:
            return ('Boxes', 'Core Tuck', 'complete')
        return ('Boxes', 'Box', 'complete')
    if re.search(r'-CNCA-|-CNC-', all_text) or 'SHIPPER BOX' in all_text:
        return ('Boxes', 'Shipper Box', 'complete')
    if 'BOX' in all_text and 'SBS' in all_text and 'BAG' not in all_text:
        return ('Boxes', 'Box', 'complete')
    if 'DISPLAY' in all_text and ('TEARAWAY' in all_text or 'ELEVATED' in all_text) and 'BAG' not in all_text:
        return ('Boxes', 'Display Box', 'complete')
    
    # FLEXPACK
    if 'FLEXPACK' in product_type or 'WAVEPACK' in product_type or 'FLEX' in product_type:
        return ('Flexpack', 'Wavepack', 'complete')
    if name.startswith('BAM-') and 'LABEL' not in all_text:
        return ('Flexpack', 'Wavepack', 'complete')
    if re.search(r'WAVEPACK|FLEXPACK', all_text):
        return ('Flexpack', 'Wavepack', 'complete')
    if re.search(r'\bBAGS?\b|\bPOUCH\b', desc):
        return ('Flexpack', 'Bag/Pouch', 'complete')
    if die_tool and not is_alphanumeric and die_tool in FLEXPACK_CODES:
        return ('Flexpack', 'Wavepack', 'complete')
    
    # NON-CORE LABELS
    if 'LABEL' in product_type:
        return ('Non-Core Labels', 'Custom Label', 'label')
    if re.search(r'\bLABEL\b|\bLBL\b|\bBOPP\b', all_text):
        return ('Non-Core Labels', 'Custom Label', 'label')
    if die_tool and not is_alphanumeric:
        return ('Non-Core Labels', 'Custom Label', 'label')
    if re.search(r'^[A-Z]{3,4}-[A-Z]{2}-', name):
        return ('Non-Core Labels', 'Custom Label', 'label')
    
    # APPLICATION FEES
    if re.search(r'APPL\s*FEE|APPLICATION\s*FEE', all_text):
        if re.search(r'15D|25D|45D|145D', all_text):
            return ('Drams', 'Application Fee', 'fee')
        if re.search(r'116|90', all_text) and 'TUBE' in all_text:
            return ('Tubes', 'Application Fee', 'fee')
        return ('Fees & Adjustments', 'Application Fee', 'fee')
    
    return ('Other', 'Uncategorized', None)


def apply_product_categories(df):
    """Apply categorization to a dataframe"""
    if df.empty:
        return df
    
    df = df.copy()
    
    item_col = 'Item' if 'Item' in df.columns else None
    desc_col = 'Item Description' if 'Item Description' in df.columns else None
    product_type_col = 'Calyx || Product Type' if 'Calyx || Product Type' in df.columns else None
    
    if item_col is None and desc_col is None:
        df['Product Category'] = 'Other'
        df['Product Sub-Category'] = 'Uncategorized'
        df['Component Type'] = None
        return df
    
    categories = df.apply(
        lambda row: categorize_product(
            row.get(item_col, '') if item_col else '',
            row.get(desc_col, '') if desc_col else '',
            row.get(product_type_col, '') if product_type_col else ''
        ), axis=1
    )
    
    df['Product Category'] = categories.apply(lambda x: x[0])
    df['Product Sub-Category'] = categories.apply(lambda x: x[1])
    df['Component Type'] = categories.apply(lambda x: x[2])
    
    return df


# ========== MAPPING FUNCTIONS ==========

def map_to_forecast_category(product_category, sub_category=None):
    """Map detailed product category to forecast category"""
    if pd.isna(product_category):
        return 'Other'
    
    cat = str(product_category).strip()
    sub = str(sub_category).strip() if sub_category else ''
    
    if cat == 'Drams':
        return 'Drams'
    if cat == 'Dram Accessories':
        return 'Drams'
    if cat == 'DML (Universal)':
        return 'Drams'
    if cat == 'Flexpack':
        return 'Flexpack'
    if cat == 'Calyx Cure':
        return 'Cure'
    if cat in ['Concentrates', 'Calyx Jar']:
        return 'Glass'
    if cat == 'Non-Core Labels':
        return 'Labels'
    if cat == 'Fees & Adjustments':
        if 'Shipping' in sub:
            return 'Shipping'
        if 'Application' in sub:
            return 'Application'
        return 'Other'
    if cat in ['Boxes', 'Tubes']:
        return 'Other'
    
    return 'Other'


def map_to_forecast_pipeline(pipeline_value):
    """Map HubSpot pipeline values to forecast pipeline categories"""
    if pd.isna(pipeline_value):
        return None
    
    pipeline = str(pipeline_value).upper().strip()
    
    if 'RETENTION' in pipeline:
        return 'Retention'
    if 'GROWTH' in pipeline:
        return 'Growth'
    if 'ACQUISITION' in pipeline or 'NEW' in pipeline:
        return 'Acquisition'
    if 'DISTRIBUT' in pipeline or 'DISTRIBUTION' in pipeline:
        return 'Distributors'
    if 'ECOM' in pipeline or 'E-COM' in pipeline or 'E COM' in pipeline:
        return 'Ecom'
    
    return None


def map_order_type_to_category(order_type):
    """Map Order Type from Sales Orders to Forecast Category"""
    if pd.isna(order_type):
        return 'Other'
    
    ot = str(order_type).upper().strip()
    
    if 'DRAM' in ot or re.search(r'15D|25D|45D|145D', ot):
        return 'Drams'
    if 'FLEX' in ot or 'WAVE' in ot or 'BAG' in ot:
        return 'Flexpack'
    if 'CURE' in ot:
        return 'Cure'
    if 'CUBE' in ot:
        return 'Cube'
    if 'GLASS' in ot or 'CONCENTRATE' in ot or re.search(r'4ML|7ML', ot):
        return 'Glass'
    if 'LABEL' in ot:
        return 'Labels'
    if 'APPL' in ot or 'APPLICATION' in ot:
        return 'Application'
    if 'SHIP' in ot or 'FREIGHT' in ot:
        return 'Shipping'
    
    return 'Other'


def map_deal_type_to_category(deal_type):
    """Map Deal Type from HubSpot to Forecast Category"""
    if pd.isna(deal_type):
        return 'Other'
    
    dt = str(deal_type).upper().strip()
    
    if 'NON-LABELED' in dt or 'NON LABELED' in dt:
        return 'Drams'
    if 'LABELED' in dt and 'LABELS ONLY' not in dt:
        return 'Drams'
    if 'FLEXPACK' in dt:
        return 'Flexpack'
    if 'CURE' in dt or 'CALYX CURE' in dt:
        return 'Cure'
    if 'OUTER BOX' in dt or 'BOX' in dt:
        return 'Other'
    if 'LABELS ONLY' in dt or 'LABEL' in dt:
        return 'Labels'
    
    return 'Other'


# ========== FORECAST DATA LOADING ==========

def parse_forecast_sheet(raw_df):
    """Parse the 2026 Forecast sheet structure"""
    if raw_df.empty:
        return pd.DataFrame()
    
    all_data = []
    
    month_cols = {
        'January': 2, 'February': 3, 'March': 4,
        'April': 6, 'May': 7, 'June': 8,
        'July': 10, 'August': 11, 'September': 12,
        'October': 14, 'November': 15, 'December': 16
    }
    
    quarter_cols = {'Q1': 5, 'Q2': 9, 'Q3': 13, 'Q4': 17}
    yearly_col = 18
    
    current_pipeline = None
    valid_pipelines = ['Retention', 'Growth', 'Acquisition', 'Distributors', 'Ecom', 'Total']
    categories = ['Drams', 'Flexpack', 'Cure', 'Cube', 'Glass', 'Labels', 'Application', 'Shipping', 'Other', 'Total']
    
    for idx, row in raw_df.iterrows():
        if len(row) < 3:
            continue
        
        first_col = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
        second_col = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ''
        
        if first_col in valid_pipelines:
            current_pipeline = first_col
        
        if second_col == 'Category':
            continue
        
        if second_col == '' or second_col == 'nan':
            continue
        
        if current_pipeline and second_col in categories:
            row_data = {
                'Pipeline': current_pipeline,
                'Category': second_col
            }
            
            for month, col_idx in month_cols.items():
                if col_idx < len(row):
                    row_data[month] = clean_numeric(row.iloc[col_idx])
                else:
                    row_data[month] = 0.0
            
            for quarter, col_idx in quarter_cols.items():
                if col_idx < len(row):
                    row_data[quarter] = clean_numeric(row.iloc[col_idx])
                else:
                    row_data[quarter] = 0.0
            
            if yearly_col < len(row):
                row_data['Annual_Total'] = clean_numeric(row.iloc[yearly_col])
            else:
                row_data['Annual_Total'] = 0.0
            
            all_data.append(row_data)
    
    if not all_data:
        return pd.DataFrame()
    
    return pd.DataFrame(all_data)


@st.cache_data(ttl=300)
def load_forecast_data():
    """Load and parse the 2026 Forecast data"""
    raw_df = load_google_sheets_data("2026 Forecast", "A1:S80", version=CACHE_VERSION, silent=True)
    
    if raw_df.empty:
        return pd.DataFrame()
    
    return parse_forecast_sheet(raw_df)


# ========== MAIN DATA LOADING ==========

@st.cache_data(ttl=300)
def load_all_tracker_data():
    """Load all data needed for the Annual Goal Tracker"""
    
    # Load all sheets
    line_items_df = load_google_sheets_data("Invoice Line Item", "A:Z", version=CACHE_VERSION)
    invoices_df = load_google_sheets_data("_NS_Invoices_Data", "A:U", version=CACHE_VERSION)
    sales_orders_df = load_google_sheets_data("_NS_SalesOrders_Data", "A:AG", version=CACHE_VERSION)
    deals_df = load_google_sheets_data("All Reps All Pipelines", "A:Z", version=CACHE_VERSION)
    forecast_df = load_forecast_data()
    
    # Process Invoice Line Items
    if not line_items_df.empty:
        if line_items_df.columns.duplicated().any():
            line_items_df = line_items_df.loc[:, ~line_items_df.columns.duplicated()]
        
        if 'Amount' in line_items_df.columns:
            line_items_df['Amount'] = line_items_df['Amount'].apply(clean_numeric)
        if 'Quantity' in line_items_df.columns:
            line_items_df['Quantity'] = line_items_df['Quantity'].apply(clean_numeric)
        if 'Date' in line_items_df.columns:
            line_items_df['Date'] = pd.to_datetime(line_items_df['Date'], errors='coerce')
        
        line_items_df = apply_product_categories(line_items_df)
        
        line_items_df['Forecast Category'] = line_items_df.apply(
            lambda row: map_to_forecast_category(row.get('Product Category'), row.get('Product Sub-Category')),
            axis=1
        )
    
    # Process Invoices (for pipeline lookup)
    pipeline_lookup = {}
    if not invoices_df.empty:
        if invoices_df.columns.duplicated().any():
            invoices_df = invoices_df.loc[:, ~invoices_df.columns.duplicated()]
        
        if 'Document Number' in invoices_df.columns:
            invoices_df['Document Number'] = invoices_df['Document Number'].astype(str).str.strip()
        
        pipeline_col = None
        for col in invoices_df.columns:
            if 'hubspot' in col.lower() and 'pipeline' in col.lower():
                pipeline_col = col
                break
        
        if pipeline_col is None and 'HubSpot Pipeline' in invoices_df.columns:
            pipeline_col = 'HubSpot Pipeline'
        
        if pipeline_col and 'Document Number' in invoices_df.columns:
            invoices_df['Forecast Pipeline'] = invoices_df[pipeline_col].apply(map_to_forecast_pipeline)
            pipeline_lookup = invoices_df.set_index('Document Number')['Forecast Pipeline'].to_dict()
    
    # Join pipeline to line items
    if not line_items_df.empty and pipeline_lookup:
        if 'Document Number' in line_items_df.columns:
            line_items_df['Document Number'] = line_items_df['Document Number'].astype(str).str.strip()
            line_items_df['Forecast Pipeline'] = line_items_df['Document Number'].map(pipeline_lookup)
    
    # Process Sales Orders
    if not sales_orders_df.empty:
        if sales_orders_df.columns.duplicated().any():
            sales_orders_df = sales_orders_df.loc[:, ~sales_orders_df.columns.duplicated()]
        
        if 'Amount (Transaction Total)' in sales_orders_df.columns and 'Amount' not in sales_orders_df.columns:
            sales_orders_df = sales_orders_df.rename(columns={'Amount (Transaction Total)': 'Amount'})
        
        if 'Amount' in sales_orders_df.columns:
            sales_orders_df['Amount'] = sales_orders_df['Amount'].apply(clean_numeric)
        if 'Order Start Date' in sales_orders_df.columns:
            sales_orders_df['Order Start Date'] = pd.to_datetime(sales_orders_df['Order Start Date'], errors='coerce')
        
        pipeline_col = None
        for col in sales_orders_df.columns:
            if 'hubspot' in col.lower() and 'pipeline' in col.lower():
                pipeline_col = col
                break
        
        if pipeline_col:
            sales_orders_df['Forecast Pipeline'] = sales_orders_df[pipeline_col].apply(map_to_forecast_pipeline)
        
        if 'Order Type' in sales_orders_df.columns:
            sales_orders_df['Forecast Category'] = sales_orders_df['Order Type'].apply(map_order_type_to_category)
    
    # Process HubSpot Deals
    if not deals_df.empty:
        if deals_df.columns.duplicated().any():
            deals_df = deals_df.loc[:, ~deals_df.columns.duplicated()]
        
        if 'Amount' in deals_df.columns:
            deals_df['Amount'] = deals_df['Amount'].apply(clean_numeric)
        if 'Close Date' in deals_df.columns:
            deals_df['Close Date'] = pd.to_datetime(deals_df['Close Date'], errors='coerce')
        
        if 'Pipeline' in deals_df.columns:
            deals_df['Forecast Pipeline'] = deals_df['Pipeline'].apply(map_to_forecast_pipeline)
        
        if 'Deal Type' in deals_df.columns:
            deals_df['Forecast Category'] = deals_df['Deal Type'].apply(map_deal_type_to_category)
    
    return {
        'forecast': forecast_df,
        'line_items': line_items_df,
        'invoices': invoices_df,
        'sales_orders': sales_orders_df,
        'deals': deals_df
    }


# ========== CALCULATIONS ==========

def calculate_ytd_actuals(line_items_df, year=2026):
    """Calculate YTD actuals by Pipeline and Category"""
    if line_items_df.empty:
        return pd.DataFrame()
    
    df = line_items_df.copy()
    if 'Date' in df.columns:
        df = df[df['Date'].dt.year == year]
    
    if df.empty:
        return pd.DataFrame()
    
    grouped = df.groupby(['Forecast Pipeline', 'Forecast Category']).agg({
        'Amount': 'sum'
    }).reset_index()
    
    grouped.columns = ['Pipeline', 'Category', 'Actual']
    
    return grouped


def calculate_monthly_actuals(line_items_df, year=2026):
    """Calculate monthly actuals by Pipeline and Category"""
    if line_items_df.empty:
        return pd.DataFrame()
    
    df = line_items_df.copy()
    if 'Date' in df.columns:
        df = df[df['Date'].dt.year == year]
        df['Month'] = df['Date'].dt.month
        df['Month_Name'] = df['Date'].dt.strftime('%B')
    
    if df.empty:
        return pd.DataFrame()
    
    grouped = df.groupby(['Forecast Pipeline', 'Forecast Category', 'Month', 'Month_Name']).agg({
        'Amount': 'sum'
    }).reset_index()
    
    grouped.columns = ['Pipeline', 'Category', 'Month_Num', 'Month', 'Actual']
    
    return grouped


def get_ytd_plan(forecast_df, through_month):
    """Calculate YTD plan from forecast"""
    if forecast_df.empty:
        return pd.DataFrame()
    
    months_to_sum = MONTH_NAMES[:through_month]
    
    df = forecast_df.copy()
    df['YTD_Plan'] = df[months_to_sum].sum(axis=1)
    
    return df[['Pipeline', 'Category', 'YTD_Plan', 'Annual_Total']]


def calculate_variance(actuals_df, plan_df):
    """Calculate variance between actuals and plan"""
    if actuals_df.empty and plan_df.empty:
        return pd.DataFrame()
    
    merged = plan_df.merge(actuals_df, on=['Pipeline', 'Category'], how='left')
    
    merged['Actual'] = merged['Actual'].fillna(0)
    merged['Variance'] = merged['Actual'] - merged['YTD_Plan']
    merged['Variance_Pct'] = np.where(
        merged['YTD_Plan'] > 0,
        (merged['Actual'] / merged['YTD_Plan'] - 1) * 100,
        0
    )
    merged['Attainment_Pct'] = np.where(
        merged['YTD_Plan'] > 0,
        (merged['Actual'] / merged['YTD_Plan']) * 100,
        0
    )
    
    return merged


# ========== VISUALIZATIONS ==========

def create_gauge_chart(value, max_value, title, color='#3b82f6'):
    """Create a progress gauge"""
    pct = (value / max_value * 100) if max_value > 0 else 0
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=pct,
        number={'suffix': '%', 'font': {'size': 36, 'color': '#f1f5f9'}},
        delta={'reference': 100, 'relative': False, 'position': 'bottom',
               'increasing': {'color': '#10b981'}, 'decreasing': {'color': '#ef4444'}},
        title={'text': title, 'font': {'size': 14, 'color': '#94a3b8'}},
        gauge={
            'axis': {'range': [0, 120], 'tickcolor': '#475569', 'tickfont': {'color': '#64748b'}},
            'bar': {'color': color},
            'bgcolor': '#1e293b',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 80], 'color': '#1e293b'},
                {'range': [80, 100], 'color': '#1e293b'},
                {'range': [100, 120], 'color': '#1e293b'}
            ],
            'threshold': {
                'line': {'color': '#10b981', 'width': 3},
                'thickness': 0.8,
                'value': 100
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': '#f1f5f9'},
        height=200,
        margin=dict(t=80, b=20, l=30, r=30)
    )
    
    return fig


def create_pipeline_bar_chart(data, title="Pipeline Performance"):
    """Create horizontal bar chart for pipeline comparison"""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Plan',
        y=data['Pipeline'],
        x=data['YTD_Plan'],
        orientation='h',
        marker_color='#475569',
        text=[f"${x:,.0f}" for x in data['YTD_Plan']],
        textposition='inside',
        textfont={'color': '#f1f5f9'}
    ))
    
    fig.add_trace(go.Bar(
        name='Actual',
        y=data['Pipeline'],
        x=data['Actual'],
        orientation='h',
        marker_color=[PIPELINE_COLORS.get(p, '#3b82f6') for p in data['Pipeline']],
        text=[f"${x:,.0f}" for x in data['Actual']],
        textposition='inside',
        textfont={'color': '#f1f5f9'}
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color='#f1f5f9')),
        barmode='group',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': '#94a3b8'},
        xaxis=dict(gridcolor='#334155', tickformat='$,.0f'),
        yaxis=dict(gridcolor='#334155'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        height=350,
        margin=dict(t=80, b=40, l=120, r=40)
    )
    
    return fig


def create_category_bar_chart(data, title="Category Performance"):
    """Create bar chart for category comparison"""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Plan',
        x=data['Category'],
        y=data['YTD_Plan'],
        marker_color='#475569',
        text=[f"${x/1000:.0f}K" if x >= 1000 else f"${x:.0f}" for x in data['YTD_Plan']],
        textposition='outside',
        textfont={'color': '#94a3b8'}
    ))
    
    fig.add_trace(go.Bar(
        name='Actual',
        x=data['Category'],
        y=data['Actual'],
        marker_color=[CATEGORY_COLORS.get(c, '#3b82f6') for c in data['Category']],
        text=[f"${x/1000:.0f}K" if x >= 1000 else f"${x:.0f}" for x in data['Actual']],
        textposition='outside',
        textfont={'color': '#f1f5f9'}
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color='#f1f5f9')),
        barmode='group',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': '#94a3b8'},
        xaxis=dict(gridcolor='#334155', tickangle=-45),
        yaxis=dict(gridcolor='#334155', tickformat='$,.0f'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        height=400,
        margin=dict(t=80, b=100, l=80, r=40)
    )
    
    return fig


def create_monthly_trend_chart(monthly_actuals, forecast_df, selected_pipeline='Total', selected_category='Total'):
    """Create monthly trend line chart"""
    
    if selected_pipeline == 'Total' and selected_category == 'Total':
        plan_row = forecast_df[(forecast_df['Pipeline'] == 'Total') & (forecast_df['Category'] == 'Total')]
    elif selected_pipeline == 'Total':
        plan_row = forecast_df[(forecast_df['Pipeline'] == 'Total') & (forecast_df['Category'] == selected_category)]
    elif selected_category == 'Total':
        plan_row = forecast_df[(forecast_df['Pipeline'] == selected_pipeline) & (forecast_df['Category'] == 'Total')]
    else:
        plan_row = forecast_df[(forecast_df['Pipeline'] == selected_pipeline) & (forecast_df['Category'] == selected_category)]
    
    if plan_row.empty:
        return None
    
    plan_values = [plan_row[month].values[0] for month in MONTH_NAMES]
    
    if monthly_actuals.empty:
        actual_values = [0] * 12
    else:
        filtered = monthly_actuals.copy()
        if selected_pipeline != 'Total':
            filtered = filtered[filtered['Pipeline'] == selected_pipeline]
        if selected_category != 'Total':
            filtered = filtered[filtered['Category'] == selected_category]
        
        actual_by_month = filtered.groupby('Month_Num')['Actual'].sum().to_dict()
        actual_values = [actual_by_month.get(i, 0) for i in range(1, 13)]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=MONTH_ABBREV,
        y=plan_values,
        mode='lines+markers',
        name='Plan',
        line=dict(color='#475569', width=2, dash='dash'),
        marker=dict(size=8)
    ))
    
    fig.add_trace(go.Scatter(
        x=MONTH_ABBREV,
        y=actual_values,
        mode='lines+markers',
        name='Actual',
        line=dict(color='#3b82f6', width=3),
        marker=dict(size=10),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.1)'
    ))
    
    fig.update_layout(
        title=dict(text='Monthly Trend: Plan vs Actual', font=dict(size=16, color='#f1f5f9')),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': '#94a3b8'},
        xaxis=dict(gridcolor='#334155'),
        yaxis=dict(gridcolor='#334155', tickformat='$,.0f'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        height=350,
        margin=dict(t=80, b=40, l=80, r=40),
        hovermode='x unified'
    )
    
    return fig


# ========== MAIN DASHBOARD ==========

def render_annual_goal_tracker():
    """Main entry point for the Annual Goal Tracker"""
    
    # Custom CSS
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); }
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 1rem;
        }
        div[data-testid="stMetric"] label { color: #94a3b8 !important; }
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #f1f5f9 !important; }
        h1, h2, h3 { color: #f1f5f9 !important; }
        .progress-card {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 1.5rem;
            margin: 0.5rem 0;
        }
        .progress-card-header { color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem; }
        .progress-card-value { color: #f1f5f9; font-size: 2rem; font-weight: 700; }
        .progress-card-subvalue { color: #64748b; font-size: 0.9rem; }
        .positive { color: #10b981 !important; }
        .negative { color: #ef4444 !important; }
        .neutral { color: #f59e0b !important; }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #06b6d4 100%);
            padding: 2rem; border-radius: 16px; margin-bottom: 2rem;">
            <h1 style="color: white; margin: 0; font-size: 2.5rem;">🎯 2026 Annual Goal Tracker</h1>
            <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0;">Progress vs. Plan by Pipeline & Category</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Load data
    with st.spinner("Loading data..."):
        data = load_all_tracker_data()
    
    forecast_df = data['forecast']
    line_items_df = data['line_items']
    sales_orders_df = data['sales_orders']
    deals_df = data['deals']
    
    if forecast_df.empty:
        st.error("❌ Could not load 2026 Forecast data. Please check the sheet exists.")
        return
    
    # Current period
    now = datetime.now()
    current_month = now.month
    
    # Sidebar
    st.sidebar.markdown("### 📊 Filters")
    
    period_option = st.sidebar.radio("Time Period", ["YTD (through today)", "Full Year", "Custom Month"], index=0)
    
    if period_option == "Custom Month":
        selected_month = st.sidebar.selectbox("Select Month", MONTH_NAMES, index=current_month-1)
        through_month = MONTH_NAMES.index(selected_month) + 1
    elif period_option == "Full Year":
        through_month = 12
    else:
        through_month = current_month
    
    pipeline_options = ['All Pipelines'] + FORECAST_PIPELINES
    selected_pipeline_filter = st.sidebar.selectbox("Pipeline", pipeline_options, index=0)
    
    category_options = ['All Categories'] + FORECAST_CATEGORIES
    selected_category_filter = st.sidebar.selectbox("Category", category_options, index=0)
    
    # Calculations
    ytd_plan = get_ytd_plan(forecast_df, through_month)
    ytd_actuals = calculate_ytd_actuals(line_items_df, year=2026)
    monthly_actuals = calculate_monthly_actuals(line_items_df, year=2026)
    
    if not ytd_actuals.empty:
        comparison = calculate_variance(ytd_actuals, ytd_plan)
    else:
        comparison = ytd_plan.copy()
        comparison['Actual'] = 0
        comparison['Variance'] = -comparison['YTD_Plan']
        comparison['Variance_Pct'] = -100
        comparison['Attainment_Pct'] = 0
    
    # Executive Summary
    st.markdown("### 📈 Executive Summary")
    
    total_row = comparison[(comparison['Pipeline'] == 'Total') & (comparison['Category'] == 'Total')]
    
    if not total_row.empty:
        total_plan = total_row['YTD_Plan'].values[0]
        total_actual = total_row['Actual'].values[0]
        total_annual = total_row['Annual_Total'].values[0]
        total_variance = total_row['Variance'].values[0]
        attainment = total_row['Attainment_Pct'].values[0]
    else:
        total_plan = ytd_plan[ytd_plan['Pipeline'] == 'Total']['YTD_Plan'].sum()
        total_actual = ytd_actuals['Actual'].sum() if not ytd_actuals.empty else 0
        total_annual = ytd_plan[ytd_plan['Pipeline'] == 'Total']['Annual_Total'].sum()
        total_variance = total_actual - total_plan
        attainment = (total_actual / total_plan * 100) if total_plan > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("2026 Annual Goal", f"${total_annual:,.0f}", f"Through {MONTH_NAMES[through_month-1]}")
    with col2:
        st.metric("YTD Plan", f"${total_plan:,.0f}", f"Months 1-{through_month}")
    with col3:
        st.metric("YTD Actual", f"${total_actual:,.0f}", f"{attainment:.1f}% of plan")
    with col4:
        variance_color = "normal" if total_variance >= 0 else "inverse"
        st.metric("Variance", f"${total_variance:,.0f}", f"{'Ahead' if total_variance >= 0 else 'Behind'} of plan", delta_color=variance_color)
    
    # Gauge
    st.markdown("---")
    gauge_col1, gauge_col2, gauge_col3 = st.columns([1, 2, 1])
    
    with gauge_col2:
        gauge = create_gauge_chart(
            total_actual, total_plan,
            f"YTD Attainment ({MONTH_NAMES[through_month-1]})",
            '#3b82f6' if attainment >= 80 else '#f59e0b' if attainment >= 60 else '#ef4444'
        )
        st.plotly_chart(gauge, use_container_width=True)
    
    # Pipeline Breakdown
    st.markdown("---")
    st.markdown("### 🔄 Pipeline Breakdown")
    
    pipeline_data = comparison[
        (comparison['Category'] == 'Total') & 
        (comparison['Pipeline'] != 'Total') &
        (comparison['Pipeline'].isin(FORECAST_PIPELINES))
    ].copy()
    
    if not pipeline_data.empty:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            pipeline_chart = create_pipeline_bar_chart(pipeline_data, "Pipeline: Plan vs Actual")
            st.plotly_chart(pipeline_chart, use_container_width=True)
        
        with col2:
            st.markdown("**Pipeline Summary**")
            for _, row in pipeline_data.iterrows():
                pipeline = row['Pipeline']
                plan = row['YTD_Plan']
                actual = row['Actual']
                att_pct = row['Attainment_Pct']
                
                status_class = 'positive' if att_pct >= 100 else 'neutral' if att_pct >= 80 else 'negative'
                
                st.markdown(f"""
                    <div class="progress-card">
                        <div class="progress-card-header">{pipeline}</div>
                        <div class="progress-card-value">${actual:,.0f}</div>
                        <div class="progress-card-subvalue">Plan: ${plan:,.0f} | <span class="{status_class}">{att_pct:.1f}%</span></div>
                    </div>
                """, unsafe_allow_html=True)
    
    # Category Breakdown
    st.markdown("---")
    st.markdown("### 📦 Category Breakdown")
    
    if selected_pipeline_filter != 'All Pipelines':
        category_data = comparison[
            (comparison['Pipeline'] == selected_pipeline_filter) & 
            (comparison['Category'] != 'Total') &
            (comparison['Category'].isin(FORECAST_CATEGORIES))
        ].copy()
        title_suffix = f" ({selected_pipeline_filter})"
    else:
        category_data = comparison[
            (comparison['Pipeline'] == 'Total') & 
            (comparison['Category'] != 'Total') &
            (comparison['Category'].isin(FORECAST_CATEGORIES))
        ].copy()
        title_suffix = " (All Pipelines)"
    
    if not category_data.empty:
        category_chart = create_category_bar_chart(category_data, f"Category: Plan vs Actual{title_suffix}")
        st.plotly_chart(category_chart, use_container_width=True)
        
        with st.expander("📋 View Category Details"):
            display_df = category_data[['Category', 'YTD_Plan', 'Actual', 'Variance', 'Attainment_Pct', 'Annual_Total']].copy()
            display_df.columns = ['Category', 'YTD Plan', 'YTD Actual', 'Variance', 'Attainment %', 'Annual Goal']
            display_df['YTD Plan'] = display_df['YTD Plan'].apply(lambda x: f"${x:,.0f}")
            display_df['YTD Actual'] = display_df['YTD Actual'].apply(lambda x: f"${x:,.0f}")
            display_df['Variance'] = display_df['Variance'].apply(lambda x: f"${x:,.0f}")
            display_df['Attainment %'] = display_df['Attainment %'].apply(lambda x: f"{x:.1f}%")
            display_df['Annual Goal'] = display_df['Annual Goal'].apply(lambda x: f"${x:,.0f}")
            st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Monthly Trend
    st.markdown("---")
    st.markdown("### 📅 Monthly Trend")
    
    trend_col1, trend_col2 = st.columns([3, 1])
    
    with trend_col2:
        trend_pipeline = st.selectbox("Select Pipeline", ['Total'] + FORECAST_PIPELINES, key='trend_pipeline')
        trend_category = st.selectbox("Select Category", ['Total'] + FORECAST_CATEGORIES, key='trend_category')
    
    with trend_col1:
        trend_chart = create_monthly_trend_chart(monthly_actuals, forecast_df, trend_pipeline, trend_category)
        if trend_chart:
            st.plotly_chart(trend_chart, use_container_width=True)
    
    # Pipeline Health
    st.markdown("---")
    st.markdown("### 💼 Pipeline Health")
    
    health_col1, health_col2 = st.columns(2)
    
    with health_col1:
        st.markdown("**Pending Orders** (Not Yet Invoiced)")
        if not sales_orders_df.empty:
            if 'Status' in sales_orders_df.columns:
                pending_orders = sales_orders_df[
                    sales_orders_df['Status'].str.contains('Pending|Partial', case=False, na=False)
                ]
            else:
                pending_orders = sales_orders_df
            
            pending_total = pending_orders['Amount'].sum() if 'Amount' in pending_orders.columns else 0
            pending_count = len(pending_orders)
            
            st.metric("Pending Value", f"${pending_total:,.0f}", f"{pending_count} orders")
        else:
            st.info("No pending order data available")
    
    with health_col2:
        st.markdown("**Open HubSpot Deals**")
        if not deals_df.empty:
            if 'Close Status' in deals_df.columns:
                open_statuses = ['Opportunity', 'Expect', 'Commit', 'Best Case']
                open_deals = deals_df[deals_df['Close Status'].isin(open_statuses)]
            else:
                open_deals = deals_df
            
            pipeline_total = open_deals['Amount'].sum() if 'Amount' in open_deals.columns else 0
            deal_count = len(open_deals)
            
            st.metric("Pipeline Value", f"${pipeline_total:,.0f}", f"{deal_count} deals")
        else:
            st.info("No HubSpot deal data available")
    
    # Data Quality Check
    with st.expander("🔍 Data Quality Check"):
        st.markdown("**Pipeline Coverage in Actuals**")
        if not line_items_df.empty and 'Forecast Pipeline' in line_items_df.columns:
            pipeline_coverage = line_items_df.groupby('Forecast Pipeline')['Amount'].sum().reset_index()
            pipeline_coverage.columns = ['Pipeline', 'Revenue']
            pipeline_coverage['Revenue'] = pipeline_coverage['Revenue'].apply(lambda x: f"${x:,.0f}")
            st.dataframe(pipeline_coverage, use_container_width=True, hide_index=True)
            
            unmapped = line_items_df[line_items_df['Forecast Pipeline'].isna()]['Amount'].sum()
            if unmapped > 0:
                st.warning(f"⚠️ ${unmapped:,.0f} in revenue has no pipeline mapping")
        
        st.markdown("**Category Coverage in Actuals**")
        if not line_items_df.empty and 'Forecast Category' in line_items_df.columns:
            category_coverage = line_items_df.groupby('Forecast Category')['Amount'].sum().reset_index()
            category_coverage.columns = ['Category', 'Revenue']
            category_coverage['Revenue'] = category_coverage['Revenue'].apply(lambda x: f"${x:,.0f}")
            st.dataframe(category_coverage, use_container_width=True, hide_index=True)


# ========== ENTRY POINT ==========

if __name__ == "__main__":
    st.set_page_config(
        page_title="2026 Annual Goal Tracker",
        page_icon="🎯",
        layout="wide"
    )
    render_annual_goal_tracker()
