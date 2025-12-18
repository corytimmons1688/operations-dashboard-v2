"""
Forecasting Models Module for S&OP Dashboard
Implements three user-selectable forecasting approaches:
1. Exponential Smoothing (ETS)
2. ARIMA/SARIMA
3. Machine Learning (Random Forest / Gradient Boosting)

Author: Xander @ Calyx Containers
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime, timedelta
import logging
import warnings

# Forecasting libraries
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.seasonal import seasonal_decompose
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from scipy import stats

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


class ForecastResult:
    """Container for forecast results and metadata."""
    
    def __init__(self, 
                 forecast: pd.Series,
                 model_name: str,
                 confidence_lower: pd.Series = None,
                 confidence_upper: pd.Series = None,
                 metrics: Dict[str, float] = None,
                 feature_importance: pd.DataFrame = None,
                 parameters: Dict[str, Any] = None):
        self.forecast = forecast
        self.model_name = model_name
        self.confidence_lower = confidence_lower
        self.confidence_upper = confidence_upper
        self.metrics = metrics or {}
        self.feature_importance = feature_importance
        self.parameters = parameters or {}
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert forecast to DataFrame with confidence intervals."""
        df = pd.DataFrame({
            'Period': self.forecast.index,
            'Forecast': self.forecast.values
        })
        
        if self.confidence_lower is not None:
            df['Lower_CI'] = self.confidence_lower.values
        if self.confidence_upper is not None:
            df['Upper_CI'] = self.confidence_upper.values
        
        return df


def detect_seasonality(series: pd.Series, freq: str = 'M') -> Tuple[bool, int]:
    """
    Detect if a time series has seasonality and determine the period.
    
    Args:
        series: Time series data
        freq: Frequency of data ('D', 'W', 'M', 'Q')
        
    Returns:
        Tuple of (has_seasonality, seasonal_period)
    """
    if len(series) < 24:  # Need at least 2 years of monthly data
        return False, 1
    
    # Default periods by frequency
    default_periods = {'D': 7, 'W': 52, 'M': 12, 'Q': 4}
    period = default_periods.get(freq, 12)
    
    try:
        # Perform seasonal decomposition
        decomposition = seasonal_decompose(series, model='additive', period=period)
        seasonal = decomposition.seasonal
        
        # Check if seasonal component is significant
        seasonal_var = seasonal.var()
        total_var = series.var()
        
        if total_var > 0:
            seasonal_ratio = seasonal_var / total_var
            has_seasonality = seasonal_ratio > 0.1  # 10% threshold
            return has_seasonality, period
        
    except Exception as e:
        logger.warning(f"Seasonality detection failed: {e}")
    
    return False, 1


def prepare_time_series(df: pd.DataFrame, 
                        date_col: str = 'Period',
                        value_col: str = 'Demand') -> pd.Series:
    """
    Prepare a DataFrame for time series modeling.
    
    Args:
        df: DataFrame with date and value columns
        date_col: Name of date column
        value_col: Name of value column
        
    Returns:
        Series with DatetimeIndex
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(date_col)
    df = df.set_index(date_col)
    
    # Fill any gaps with 0 (no demand)
    series = df[value_col].asfreq('MS', fill_value=0)
    
    return series


# =============================================================================
# EXPONENTIAL SMOOTHING (ETS)
# =============================================================================

def forecast_exponential_smoothing(
    series: pd.Series,
    horizon: int = 12,
    seasonal: bool = None,
    seasonal_periods: int = 12,
    trend: str = 'add',
    damped_trend: bool = True,
    alpha: float = None,
    beta: float = None,
    gamma: float = None,
    confidence_level: float = 0.95
) -> ForecastResult:
    """
    Generate forecast using Exponential Smoothing (Holt-Winters).
    
    Args:
        series: Historical time series
        horizon: Number of periods to forecast
        seasonal: Whether to include seasonality (auto-detect if None)
        seasonal_periods: Number of periods in a season
        trend: Type of trend ('add', 'mul', None)
        damped_trend: Whether to dampen the trend
        alpha: Smoothing parameter for level (auto if None)
        beta: Smoothing parameter for trend (auto if None)
        gamma: Smoothing parameter for seasonality (auto if None)
        confidence_level: Confidence level for intervals
        
    Returns:
        ForecastResult object
    """
    try:
        # Auto-detect seasonality if not specified
        if seasonal is None:
            has_seasonal, detected_period = detect_seasonality(series)
            seasonal = 'add' if has_seasonal else None
            if has_seasonal:
                seasonal_periods = detected_period
        elif seasonal:
            seasonal = 'add'
        else:
            seasonal = None
        
        # Handle short series
        if len(series) < 2 * seasonal_periods and seasonal:
            seasonal = None
            logger.warning("Series too short for seasonality, disabling")
        
        # Build model
        model = ExponentialSmoothing(
            series,
            trend=trend,
            seasonal=seasonal,
            seasonal_periods=seasonal_periods if seasonal else None,
            damped_trend=damped_trend if trend else False,
            initialization_method='estimated'
        )
        
        # Fit with custom parameters or auto
        fit_kwargs = {}
        if alpha is not None:
            fit_kwargs['smoothing_level'] = alpha
        if beta is not None and trend:
            fit_kwargs['smoothing_trend'] = beta
        if gamma is not None and seasonal:
            fit_kwargs['smoothing_seasonal'] = gamma
        
        fitted = model.fit(**fit_kwargs) if fit_kwargs else model.fit()
        
        # Generate forecast
        forecast = fitted.forecast(horizon)
        
        # Calculate confidence intervals using residual standard error
        residuals = fitted.resid
        std_error = np.std(residuals)
        z_score = stats.norm.ppf((1 + confidence_level) / 2)
        
        # Widen intervals for longer horizons
        horizon_multiplier = np.sqrt(np.arange(1, horizon + 1))
        margin = z_score * std_error * horizon_multiplier
        
        lower = forecast - margin
        upper = forecast + margin
        
        # Ensure non-negative forecasts
        forecast = forecast.clip(lower=0)
        lower = lower.clip(lower=0)
        
        # Calculate fit metrics
        fitted_values = fitted.fittedvalues
        mape = np.mean(np.abs((series - fitted_values) / series.replace(0, np.nan))) * 100
        rmse = np.sqrt(np.mean((series - fitted_values) ** 2))
        
        metrics = {
            'MAPE': mape,
            'RMSE': rmse,
            'AIC': fitted.aic if hasattr(fitted, 'aic') else None,
            'BIC': fitted.bic if hasattr(fitted, 'bic') else None
        }
        
        parameters = {
            'alpha': fitted.params.get('smoothing_level', alpha),
            'beta': fitted.params.get('smoothing_trend', beta),
            'gamma': fitted.params.get('smoothing_seasonal', gamma),
            'trend': trend,
            'seasonal': seasonal,
            'seasonal_periods': seasonal_periods,
            'damped_trend': damped_trend
        }
        
        return ForecastResult(
            forecast=forecast,
            model_name='Exponential Smoothing',
            confidence_lower=pd.Series(lower, index=forecast.index),
            confidence_upper=pd.Series(upper, index=forecast.index),
            metrics=metrics,
            parameters=parameters
        )
        
    except Exception as e:
        logger.error(f"Exponential Smoothing failed: {e}")
        raise


# =============================================================================
# ARIMA / SARIMA
# =============================================================================

def auto_arima_params(series: pd.Series, 
                      seasonal: bool = True,
                      seasonal_period: int = 12,
                      max_p: int = 3,
                      max_q: int = 3,
                      max_d: int = 2) -> Dict[str, Tuple]:
    """
    Auto-select ARIMA parameters using AIC minimization.
    
    Args:
        series: Time series data
        seasonal: Whether to fit seasonal model
        seasonal_period: Seasonal period
        max_p, max_q, max_d: Maximum values to search
        
    Returns:
        Dictionary with optimal parameters
    """
    best_aic = np.inf
    best_params = (1, 1, 1)
    best_seasonal_params = (0, 0, 0, seasonal_period) if seasonal else (0, 0, 0, 0)
    
    # Grid search (simplified for performance)
    for p in range(max_p + 1):
        for d in range(max_d + 1):
            for q in range(max_q + 1):
                try:
                    if seasonal and len(series) >= 2 * seasonal_period:
                        model = SARIMAX(
                            series,
                            order=(p, d, q),
                            seasonal_order=(1, 1, 1, seasonal_period),
                            enforce_stationarity=False,
                            enforce_invertibility=False
                        )
                    else:
                        model = SARIMAX(
                            series,
                            order=(p, d, q),
                            enforce_stationarity=False,
                            enforce_invertibility=False
                        )
                    
                    fitted = model.fit(disp=False, maxiter=100)
                    
                    if fitted.aic < best_aic:
                        best_aic = fitted.aic
                        best_params = (p, d, q)
                        if seasonal and len(series) >= 2 * seasonal_period:
                            best_seasonal_params = (1, 1, 1, seasonal_period)
                            
                except Exception:
                    continue
    
    return {
        'order': best_params,
        'seasonal_order': best_seasonal_params
    }


def forecast_arima(
    series: pd.Series,
    horizon: int = 12,
    order: Tuple[int, int, int] = None,
    seasonal_order: Tuple[int, int, int, int] = None,
    auto_params: bool = True,
    confidence_level: float = 0.95
) -> ForecastResult:
    """
    Generate forecast using ARIMA/SARIMA.
    
    Args:
        series: Historical time series
        horizon: Number of periods to forecast
        order: ARIMA order (p, d, q) - auto if None
        seasonal_order: Seasonal order (P, D, Q, s) - auto if None
        auto_params: Whether to auto-select parameters
        confidence_level: Confidence level for intervals
        
    Returns:
        ForecastResult object
    """
    try:
        # Auto-select parameters if needed
        if auto_params or order is None:
            has_seasonal, seasonal_period = detect_seasonality(series)
            params = auto_arima_params(
                series, 
                seasonal=has_seasonal,
                seasonal_period=seasonal_period
            )
            order = params['order']
            seasonal_order = params['seasonal_order']
        
        # Handle no seasonality
        if seasonal_order is None or seasonal_order[3] == 0:
            seasonal_order = (0, 0, 0, 0)
        
        # Build and fit model
        model = SARIMAX(
            series,
            order=order,
            seasonal_order=seasonal_order if seasonal_order[3] > 0 else None,
            enforce_stationarity=False,
            enforce_invertibility=False
        )
        
        fitted = model.fit(disp=False, maxiter=200)
        
        # Generate forecast with confidence intervals
        forecast_obj = fitted.get_forecast(horizon)
        forecast = forecast_obj.predicted_mean
        conf_int = forecast_obj.conf_int(alpha=1 - confidence_level)
        
        # Ensure non-negative
        forecast = forecast.clip(lower=0)
        lower = conf_int.iloc[:, 0].clip(lower=0)
        upper = conf_int.iloc[:, 1].clip(lower=0)
        
        # Calculate metrics
        fitted_values = fitted.fittedvalues
        mape = np.mean(np.abs((series - fitted_values) / series.replace(0, np.nan))) * 100
        rmse = np.sqrt(np.mean((series - fitted_values) ** 2))
        
        metrics = {
            'MAPE': mape,
            'RMSE': rmse,
            'AIC': fitted.aic,
            'BIC': fitted.bic
        }
        
        parameters = {
            'order': order,
            'seasonal_order': seasonal_order
        }
        
        return ForecastResult(
            forecast=forecast,
            model_name='ARIMA/SARIMA',
            confidence_lower=lower,
            confidence_upper=upper,
            metrics=metrics,
            parameters=parameters
        )
        
    except Exception as e:
        logger.error(f"ARIMA failed: {e}")
        raise


# =============================================================================
# MACHINE LEARNING FORECAST
# =============================================================================

def create_ml_features(series: pd.Series, 
                       lags: List[int] = [1, 2, 3, 6, 12],
                       rolling_windows: List[int] = [3, 6, 12]) -> pd.DataFrame:
    """
    Create features for ML forecasting.
    
    Args:
        series: Historical time series
        lags: Lag periods to include
        rolling_windows: Rolling average windows
        
    Returns:
        DataFrame with features
    """
    df = pd.DataFrame({'value': series})
    
    # Lag features
    for lag in lags:
        df[f'lag_{lag}'] = df['value'].shift(lag)
    
    # Rolling statistics
    for window in rolling_windows:
        df[f'rolling_mean_{window}'] = df['value'].shift(1).rolling(window=window).mean()
        df[f'rolling_std_{window}'] = df['value'].shift(1).rolling(window=window).std()
        df[f'rolling_min_{window}'] = df['value'].shift(1).rolling(window=window).min()
        df[f'rolling_max_{window}'] = df['value'].shift(1).rolling(window=window).max()
    
    # Date features (if datetime index)
    if isinstance(series.index, pd.DatetimeIndex):
        df['month'] = series.index.month
        df['quarter'] = series.index.quarter
        df['year'] = series.index.year
        df['month_sin'] = np.sin(2 * np.pi * series.index.month / 12)
        df['month_cos'] = np.cos(2 * np.pi * series.index.month / 12)
    
    # Trend feature
    df['trend'] = np.arange(len(df))
    
    # Year-over-year change
    if len(series) > 12:
        df['yoy_change'] = df['value'].pct_change(12)
    
    return df


def forecast_ml(
    series: pd.Series,
    horizon: int = 12,
    model_type: str = 'random_forest',
    n_estimators: int = 100,
    max_depth: int = 10,
    confidence_level: float = 0.95,
    lags: List[int] = [1, 2, 3, 6, 12],
    rolling_windows: List[int] = [3, 6, 12]
) -> ForecastResult:
    """
    Generate forecast using Machine Learning (Random Forest or Gradient Boosting).
    
    Args:
        series: Historical time series
        horizon: Number of periods to forecast
        model_type: 'random_forest' or 'gradient_boosting'
        n_estimators: Number of trees
        max_depth: Maximum tree depth
        confidence_level: Confidence level for intervals
        lags: Lag periods for features
        rolling_windows: Rolling window sizes
        
    Returns:
        ForecastResult object
    """
    try:
        # Create features
        df = create_ml_features(series, lags=lags, rolling_windows=rolling_windows)
        
        # Drop rows with NaN (from lag/rolling features)
        df = df.dropna()
        
        if len(df) < 20:
            raise ValueError("Insufficient data for ML model (need at least 20 observations after feature creation)")
        
        # Prepare X and y
        feature_cols = [c for c in df.columns if c != 'value']
        X = df[feature_cols]
        y = df['value']
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Initialize model
        if model_type == 'gradient_boosting':
            model = GradientBoostingRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=42,
                learning_rate=0.1
            )
        else:
            model = RandomForestRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=42,
                n_jobs=-1
            )
        
        # Fit model
        model.fit(X_scaled, y)
        
        # Calculate in-sample metrics
        y_pred = model.predict(X_scaled)
        mape = np.mean(np.abs((y.values - y_pred) / y.replace(0, np.nan).values)) * 100
        rmse = np.sqrt(np.mean((y.values - y_pred) ** 2))
        
        # Feature importance
        importance_df = pd.DataFrame({
            'Feature': feature_cols,
            'Importance': model.feature_importances_
        }).sort_values('Importance', ascending=False)
        
        # Generate future forecasts
        last_date = series.index[-1]
        future_dates = pd.date_range(
            start=last_date + pd.DateOffset(months=1),
            periods=horizon,
            freq='MS'
        )
        
        # Iteratively predict future values
        forecast_values = []
        current_series = series.copy()
        
        for i in range(horizon):
            # Create features for next period
            temp_df = create_ml_features(current_series, lags=lags, rolling_windows=rolling_windows)
            last_features = temp_df[feature_cols].iloc[-1:].values
            
            # Handle any remaining NaN
            last_features = np.nan_to_num(last_features, nan=0)
            
            # Scale and predict
            last_features_scaled = scaler.transform(last_features)
            pred = model.predict(last_features_scaled)[0]
            pred = max(0, pred)  # Ensure non-negative
            
            forecast_values.append(pred)
            
            # Add prediction to series for next iteration
            current_series = pd.concat([
                current_series,
                pd.Series([pred], index=[future_dates[i]])
            ])
        
        forecast = pd.Series(forecast_values, index=future_dates)
        
        # Estimate confidence intervals using prediction variance
        # Use cross-validation residuals to estimate uncertainty
        tscv = TimeSeriesSplit(n_splits=min(5, len(y) // 10))
        cv_residuals = []
        
        for train_idx, test_idx in tscv.split(X_scaled):
            if len(train_idx) < 10:
                continue
            model_cv = model.__class__(**model.get_params())
            model_cv.fit(X_scaled[train_idx], y.iloc[train_idx])
            preds = model_cv.predict(X_scaled[test_idx])
            cv_residuals.extend(y.iloc[test_idx].values - preds)
        
        if cv_residuals:
            std_error = np.std(cv_residuals)
        else:
            std_error = np.std(y.values - y_pred)
        
        z_score = stats.norm.ppf((1 + confidence_level) / 2)
        horizon_multiplier = np.sqrt(np.arange(1, horizon + 1))
        margin = z_score * std_error * horizon_multiplier
        
        lower = (forecast - margin).clip(lower=0)
        upper = forecast + margin
        
        metrics = {
            'MAPE': mape,
            'RMSE': rmse,
            'R2': model.score(X_scaled, y)
        }
        
        parameters = {
            'model_type': model_type,
            'n_estimators': n_estimators,
            'max_depth': max_depth,
            'lags': lags,
            'rolling_windows': rolling_windows
        }
        
        return ForecastResult(
            forecast=forecast,
            model_name=f'ML ({model_type.replace("_", " ").title()})',
            confidence_lower=lower,
            confidence_upper=upper,
            metrics=metrics,
            feature_importance=importance_df,
            parameters=parameters
        )
        
    except Exception as e:
        logger.error(f"ML Forecast failed: {e}")
        raise


# =============================================================================
# ENSEMBLE & UTILITY FUNCTIONS
# =============================================================================

def blend_forecasts(forecasts: List[ForecastResult], 
                    weights: List[float] = None) -> ForecastResult:
    """
    Blend multiple forecasts with specified weights.
    
    Args:
        forecasts: List of ForecastResult objects
        weights: Weights for each forecast (equal if None)
        
    Returns:
        Blended ForecastResult
    """
    if not forecasts:
        raise ValueError("No forecasts to blend")
    
    if weights is None:
        weights = [1.0 / len(forecasts)] * len(forecasts)
    else:
        # Normalize weights
        total = sum(weights)
        weights = [w / total for w in weights]
    
    # Blend forecasts
    blended = sum(f.forecast * w for f, w in zip(forecasts, weights))
    
    # Blend confidence intervals if available
    lower = None
    upper = None
    if all(f.confidence_lower is not None for f in forecasts):
        lower = sum(f.confidence_lower * w for f, w in zip(forecasts, weights))
    if all(f.confidence_upper is not None for f in forecasts):
        upper = sum(f.confidence_upper * w for f, w in zip(forecasts, weights))
    
    # Average metrics
    metrics = {}
    for key in ['MAPE', 'RMSE']:
        values = [f.metrics.get(key) for f in forecasts if f.metrics.get(key) is not None]
        if values:
            metrics[key] = np.mean(values)
    
    model_names = [f.model_name for f in forecasts]
    
    return ForecastResult(
        forecast=blended,
        model_name=f"Blended ({', '.join(model_names)})",
        confidence_lower=lower,
        confidence_upper=upper,
        metrics=metrics,
        parameters={'weights': dict(zip(model_names, weights))}
    )


def allocate_topdown_forecast(
    total_forecast: pd.Series,
    historical_proportions: pd.DataFrame,
    allocation_col: str = 'Item'
) -> pd.DataFrame:
    """
    Allocate a top-down forecast to SKU level based on historical proportions.
    
    Args:
        total_forecast: Aggregate forecast
        historical_proportions: DataFrame with historical proportions by allocation_col
        allocation_col: Column to allocate by
        
    Returns:
        DataFrame with allocated forecasts
    """
    # Calculate proportions from historical data
    total_historical = historical_proportions.groupby(allocation_col)['value'].sum()
    proportions = total_historical / total_historical.sum()
    
    # Allocate forecast
    allocated = []
    for item, prop in proportions.items():
        item_forecast = total_forecast * prop
        for date, value in item_forecast.items():
            allocated.append({
                allocation_col: item,
                'Period': date,
                'Allocated_Forecast': value
            })
    
    return pd.DataFrame(allocated)


def calculate_forecast_accuracy(
    actual: pd.Series,
    forecast: pd.Series
) -> Dict[str, float]:
    """
    Calculate various forecast accuracy metrics.
    
    Args:
        actual: Actual values
        forecast: Forecast values
        
    Returns:
        Dictionary of accuracy metrics
    """
    # Align series
    common_idx = actual.index.intersection(forecast.index)
    actual = actual[common_idx]
    forecast = forecast[common_idx]
    
    # Handle zeros in actual
    non_zero_mask = actual != 0
    
    metrics = {}
    
    # MAPE (only where actual != 0)
    if non_zero_mask.any():
        metrics['MAPE'] = np.mean(np.abs((actual[non_zero_mask] - forecast[non_zero_mask]) / actual[non_zero_mask])) * 100
    
    # RMSE
    metrics['RMSE'] = np.sqrt(np.mean((actual - forecast) ** 2))
    
    # MAE
    metrics['MAE'] = np.mean(np.abs(actual - forecast))
    
    # Bias
    metrics['Bias'] = np.mean(forecast - actual)
    
    # Tracking Signal (cumulative bias / MAD)
    cumulative_error = (forecast - actual).cumsum()
    mad = np.mean(np.abs(actual - forecast))
    if mad > 0:
        metrics['Tracking_Signal'] = cumulative_error.iloc[-1] / mad
    
    return metrics


def generate_forecast(
    series: pd.Series,
    model: str = 'exponential_smoothing',
    horizon: int = 12,
    **kwargs
) -> ForecastResult:
    """
    Unified forecast generation function.
    
    Args:
        series: Historical time series
        model: Model type ('exponential_smoothing', 'arima', 'ml_random_forest', 'ml_gradient_boosting')
        horizon: Forecast horizon
        **kwargs: Model-specific parameters
        
    Returns:
        ForecastResult object
    """
    if model == 'exponential_smoothing':
        return forecast_exponential_smoothing(series, horizon=horizon, **kwargs)
    elif model == 'arima':
        return forecast_arima(series, horizon=horizon, **kwargs)
    elif model == 'ml_random_forest':
        return forecast_ml(series, horizon=horizon, model_type='random_forest', **kwargs)
    elif model == 'ml_gradient_boosting':
        return forecast_ml(series, horizon=horizon, model_type='gradient_boosting', **kwargs)
    else:
        raise ValueError(f"Unknown model type: {model}")
