"""
Utility Functions for NC Dashboard
Common helper functions, logging setup, and export capabilities

Author: Xander @ Calyx Containers
"""

import streamlit as st
import pandas as pd
import logging
from datetime import datetime
from typing import Optional, Any
import io
import sys


def setup_logging(log_level: int = logging.INFO) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (default: INFO)
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)


def export_dataframe(df: pd.DataFrame, filename: Optional[str] = None) -> str:
    """
    Export DataFrame to CSV string.
    
    Args:
        df: DataFrame to export
        filename: Optional filename (not used in return, for reference)
        
    Returns:
        CSV string
    """
    return df.to_csv(index=False)


def export_to_excel(df: pd.DataFrame) -> bytes:
    """
    Export DataFrame to Excel bytes.
    
    Args:
        df: DataFrame to export
        
    Returns:
        Excel file as bytes
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='NC Data')
    return output.getvalue()


def format_currency(value: float) -> str:
    """
    Format a number as currency.
    
    Args:
        value: Numeric value
        
    Returns:
        Formatted currency string
    """
    if pd.isna(value):
        return "$0.00"
    return f"${value:,.2f}"


def format_number(value: float, decimals: int = 0) -> str:
    """
    Format a number with thousands separator.
    
    Args:
        value: Numeric value
        decimals: Number of decimal places
        
    Returns:
        Formatted number string
    """
    if pd.isna(value):
        return "0"
    if decimals == 0:
        return f"{value:,.0f}"
    return f"{value:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format a number as percentage.
    
    Args:
        value: Numeric value (as decimal, e.g., 0.15 for 15%)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    if pd.isna(value):
        return "0%"
    return f"{value * 100:.{decimals}f}%"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero.
    
    Args:
        numerator: Top number
        denominator: Bottom number
        default: Value to return if division fails
        
    Returns:
        Division result or default
    """
    try:
        if denominator == 0 or pd.isna(denominator):
            return default
        return numerator / denominator
    except:
        return default


def get_date_range_string(start_date: datetime, end_date: datetime) -> str:
    """
    Create a formatted date range string.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        Formatted date range string
    """
    return f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"


def create_metric_card_html(
    title: str,
    value: str,
    subtitle: Optional[str] = None,
    color: str = "#3498db",
    icon: Optional[str] = None
) -> str:
    """
    Create HTML for a styled metric card.
    
    Args:
        title: Card title
        value: Main value to display
        subtitle: Optional subtitle
        color: Accent color
        icon: Optional emoji icon
        
    Returns:
        HTML string for the card
    """
    icon_html = f'<span style="font-size: 2rem;">{icon}</span>' if icon else ''
    subtitle_html = f'<p style="margin: 0; color: #888; font-size: 0.8rem;">{subtitle}</p>' if subtitle else ''
    
    return f"""
    <div style="
        background: linear-gradient(135deg, {color}11, {color}22);
        border-radius: 10px;
        padding: 1.5rem;
        border-left: 4px solid {color};
        text-align: center;
    ">
        {icon_html}
        <h2 style="margin: 0.5rem 0; color: #333;">{value}</h2>
        <p style="margin: 0; color: #666; font-weight: 500;">{title}</p>
        {subtitle_html}
    </div>
    """


def validate_dataframe(df: pd.DataFrame, required_columns: list) -> tuple:
    """
    Validate that a DataFrame has required columns.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        
    Returns:
        Tuple of (is_valid, missing_columns)
    """
    if df is None or df.empty:
        return False, required_columns
    
    missing = [col for col in required_columns if col not in df.columns]
    return len(missing) == 0, missing


def clean_string_column(series: pd.Series) -> pd.Series:
    """
    Clean a string column by stripping whitespace and handling nulls.
    
    Args:
        series: Pandas Series to clean
        
    Returns:
        Cleaned Series
    """
    return series.astype(str).str.strip().replace(['nan', 'None', ''], pd.NA)


def calculate_growth_rate(current: float, previous: float) -> Optional[float]:
    """
    Calculate growth rate between two values.
    
    Args:
        current: Current period value
        previous: Previous period value
        
    Returns:
        Growth rate as decimal or None if calculation fails
    """
    if previous == 0 or pd.isna(previous) or pd.isna(current):
        return None
    return (current - previous) / previous


def get_color_scale(value: float, min_val: float = 0, max_val: float = 100) -> str:
    """
    Get a color from a red-yellow-green scale based on value.
    
    Args:
        value: Value to map to color
        min_val: Minimum value (maps to red)
        max_val: Maximum value (maps to green)
        
    Returns:
        Hex color string
    """
    # Normalize value to 0-1 range
    normalized = (value - min_val) / (max_val - min_val) if max_val > min_val else 0.5
    normalized = max(0, min(1, normalized))  # Clamp to [0, 1]
    
    # Interpolate color
    if normalized < 0.5:
        # Red to Yellow
        r = 255
        g = int(255 * normalized * 2)
        b = 0
    else:
        # Yellow to Green
        r = int(255 * (1 - (normalized - 0.5) * 2))
        g = 255
        b = 0
    
    return f"#{r:02x}{g:02x}{b:02x}"


def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.
    
    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


class Timer:
    """Context manager for timing code blocks."""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, *args):
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        logging.info(f"{self.name} completed in {duration:.2f} seconds")
    
    @property
    def elapsed(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
