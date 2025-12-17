"""
Unit Tests for NC Dashboard
Tests core functionality of data processing and analysis modules

Author: Xander @ Calyx Containers
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_loader import (
    clean_and_transform_data,
    categorize_aging,
    get_data_summary
)
from src.pareto_chart import calculate_pareto_data
from src.cost_analysis import aggregate_by_period
from src.utils import (
    format_currency,
    format_number,
    format_percentage,
    safe_divide,
    truncate_string,
    validate_dataframe
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_nc_data():
    """Create sample NC data for testing."""
    np.random.seed(42)
    n_records = 50
    
    data = {
        'Year': [2024] * n_records,
        'Week': np.random.randint(1, 53, n_records),
        'External Or Internal': np.random.choice(['External', 'Internal'], n_records),
        'NC Number': [f'NC-{i:04d}' for i in range(1, n_records + 1)],
        'Priority': np.random.choice(['High', 'Medium', 'Low'], n_records),
        'Sales Order': [f'SO-{np.random.randint(10000, 99999)}' for _ in range(n_records)],
        'Customer': np.random.choice(['Customer A', 'Customer B', 'Customer C', 'Customer D'], n_records),
        'Issue Type': np.random.choice(['Defect A', 'Defect B', 'Defect C', 'Defect D'], n_records),
        'Status': np.random.choice(['Open', 'In Progress', 'Closed'], n_records),
        'Cost of Rework': np.random.uniform(100, 5000, n_records).round(2),
        'Cost Avoided': np.random.uniform(500, 10000, n_records).round(2),
        'Date Submitted': pd.date_range(end=datetime.now(), periods=n_records, freq='D'),
        'Total Quantity Affected': np.random.randint(10, 1000, n_records)
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def empty_dataframe():
    """Create an empty DataFrame for testing edge cases."""
    return pd.DataFrame()


# ============================================================================
# Data Loader Tests
# ============================================================================

class TestDataLoader:
    """Tests for data_loader module."""
    
    def test_clean_and_transform_data(self, sample_nc_data):
        """Test data cleaning and transformation."""
        result = clean_and_transform_data(sample_nc_data)
        
        # Check that Age_Days column was added
        assert 'Age_Days' in result.columns
        
        # Check that Aging_Bucket column was added
        assert 'Aging_Bucket' in result.columns
        
        # Check that all Age_Days are non-negative
        assert (result['Age_Days'] >= 0).all()
    
    def test_categorize_aging(self):
        """Test aging bucket categorization."""
        assert categorize_aging(0) == "0-30 days"
        assert categorize_aging(15) == "0-30 days"
        assert categorize_aging(30) == "0-30 days"
        assert categorize_aging(31) == "31-60 days"
        assert categorize_aging(60) == "31-60 days"
        assert categorize_aging(61) == "61-90 days"
        assert categorize_aging(90) == "61-90 days"
        assert categorize_aging(91) == "90+ days"
        assert categorize_aging(365) == "90+ days"
        assert categorize_aging(-1) == "Unknown"
    
    def test_get_data_summary(self, sample_nc_data):
        """Test data summary generation."""
        summary = get_data_summary(sample_nc_data)
        
        assert 'total_records' in summary
        assert summary['total_records'] == 50
        assert 'total_cost_of_rework' in summary
        assert 'unique_customers' in summary
    
    def test_get_data_summary_empty(self, empty_dataframe):
        """Test data summary with empty DataFrame."""
        summary = get_data_summary(empty_dataframe)
        assert summary == {}


# ============================================================================
# Pareto Chart Tests
# ============================================================================

class TestParetoChart:
    """Tests for pareto_chart module."""
    
    def test_calculate_pareto_data(self, sample_nc_data):
        """Test Pareto data calculation."""
        result = calculate_pareto_data(sample_nc_data, min_count=0)
        
        # Check required columns exist
        assert 'Issue Type' in result.columns
        assert 'Count' in result.columns
        assert 'Percentage' in result.columns
        assert 'Cumulative_Pct' in result.columns
        
        # Check cumulative percentage ends at 100
        assert abs(result['Cumulative_Pct'].iloc[-1] - 100) < 0.01
        
        # Check data is sorted descending by count
        assert result['Count'].is_monotonic_decreasing
    
    def test_calculate_pareto_data_with_min_count(self, sample_nc_data):
        """Test Pareto with minimum count threshold."""
        result = calculate_pareto_data(sample_nc_data, min_count=20)
        
        # All counts should be >= 20
        assert (result['Count'] >= 20).all() if len(result) > 0 else True
    
    def test_calculate_pareto_data_empty(self, empty_dataframe):
        """Test Pareto with empty DataFrame."""
        result = calculate_pareto_data(empty_dataframe)
        assert result.empty


# ============================================================================
# Cost Analysis Tests
# ============================================================================

class TestCostAnalysis:
    """Tests for cost_analysis module."""
    
    def test_aggregate_by_period_monthly(self, sample_nc_data):
        """Test monthly aggregation."""
        result = aggregate_by_period(sample_nc_data, 'Cost of Rework', 'Monthly')
        
        assert 'Period' in result.columns
        assert 'Total' in result.columns
        assert 'Count' in result.columns
        assert len(result) > 0
    
    def test_aggregate_by_period_weekly(self, sample_nc_data):
        """Test weekly aggregation."""
        result = aggregate_by_period(sample_nc_data, 'Cost of Rework', 'Weekly')
        
        assert 'Period' in result.columns
        assert len(result) > 0
    
    def test_aggregate_by_period_daily(self, sample_nc_data):
        """Test daily aggregation."""
        result = aggregate_by_period(sample_nc_data, 'Cost of Rework', 'Daily')
        
        assert 'Period' in result.columns
        # Daily should have more rows than weekly or monthly
        assert len(result) >= 1


# ============================================================================
# Utility Function Tests
# ============================================================================

class TestUtils:
    """Tests for utils module."""
    
    def test_format_currency(self):
        """Test currency formatting."""
        assert format_currency(1234.56) == "$1,234.56"
        assert format_currency(0) == "$0.00"
        assert format_currency(1000000) == "$1,000,000.00"
        assert format_currency(None) == "$0.00"
    
    def test_format_number(self):
        """Test number formatting."""
        assert format_number(1234) == "1,234"
        assert format_number(1234.567, decimals=2) == "1,234.57"
        assert format_number(0) == "0"
    
    def test_format_percentage(self):
        """Test percentage formatting."""
        assert format_percentage(0.15) == "15.0%"
        assert format_percentage(0.5, decimals=0) == "50%"
        assert format_percentage(1.0) == "100.0%"
    
    def test_safe_divide(self):
        """Test safe division."""
        assert safe_divide(10, 2) == 5.0
        assert safe_divide(10, 0) == 0.0
        assert safe_divide(10, 0, default=-1) == -1
        assert safe_divide(None, 5) == 0.0
    
    def test_truncate_string(self):
        """Test string truncation."""
        assert truncate_string("Hello", 10) == "Hello"
        assert truncate_string("Hello World", 8) == "Hello..."
        assert truncate_string("Test", 4) == "Test"
    
    def test_validate_dataframe(self, sample_nc_data):
        """Test DataFrame validation."""
        is_valid, missing = validate_dataframe(sample_nc_data, ['NC Number', 'Customer'])
        assert is_valid is True
        assert missing == []
        
        is_valid, missing = validate_dataframe(sample_nc_data, ['NC Number', 'Nonexistent'])
        assert is_valid is False
        assert 'Nonexistent' in missing
    
    def test_validate_dataframe_empty(self, empty_dataframe):
        """Test DataFrame validation with empty DataFrame."""
        is_valid, missing = validate_dataframe(empty_dataframe, ['NC Number'])
        assert is_valid is False


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for combined functionality."""
    
    def test_full_data_pipeline(self, sample_nc_data):
        """Test full data processing pipeline."""
        # Clean and transform
        cleaned = clean_and_transform_data(sample_nc_data)
        
        # Generate summary
        summary = get_data_summary(cleaned)
        
        # Calculate Pareto
        pareto = calculate_pareto_data(cleaned, min_count=0)
        
        # Aggregate costs
        cost_agg = aggregate_by_period(cleaned, 'Cost of Rework', 'Monthly')
        
        # Verify all steps produced valid output
        assert len(cleaned) == len(sample_nc_data)
        assert summary['total_records'] == len(sample_nc_data)
        assert not pareto.empty
        assert not cost_agg.empty


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
