import numpy as np
import pandas as pd
try:
    from statsmodels.tsa.stattools import adfuller
    import statsmodels.api as sm
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    print("Warning: statsmodels not installed. ADF test will not be available.")
    print("Install it using: pip install statsmodels")


class QuantAnalytics:
    """Quantitative Analytics for Pairs Trading"""
    
    def __init__(self):
        """Initialize analytics engine"""
        if not STATSMODELS_AVAILABLE:
            print("⚠️ Warning: statsmodels is not installed!")
            print("Some features (ADF test, OLS regression) will not work.")
            print("Install with: pip install statsmodels")
    
    def resample_ticks(self, df, timeframe):
        """
        Resample tick data to OHLC format
        
        Args:
            df: DataFrame with columns ['timestamp', 'price', 'quantity']
            timeframe: String like '1s', '1min', '5min'
        
        Returns:
            DataFrame with OHLC data
        """
        try:
            df = df.copy()
            
            # Ensure timestamp is datetime
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            df = df.set_index("timestamp")
            
            # Create OHLC
            ohlc = df["price"].resample(timeframe).ohlc()
            volume = df["quantity"].resample(timeframe).sum()
            
            ohlc["volume"] = volume
            
            # Drop rows with NaN values
            return ohlc.dropna()
        
        except Exception as e:
            print(f"Error in resample_ticks: {str(e)}")
            return pd.DataFrame()
    
    def calculate_ols_hedge_ratio(self, price_a, price_b):
        """
        Calculate hedge ratio using OLS regression
        
        Args:
            price_a: Series of prices for asset A
            price_b: Series of prices for asset B
        
        Returns:
            tuple: (hedge_ratio, intercept, r_squared)
        """
        if not STATSMODELS_AVAILABLE:
            raise ImportError("statsmodels is required for OLS regression. Install with: pip install statsmodels")
        
        try:
            # Align the two price series
            price_a, price_b = price_a.align(price_b, join="inner")
            
            # Remove any NaN values
            valid_idx = ~(price_a.isna() | price_b.isna())
            price_a = price_a[valid_idx]
            price_b = price_b[valid_idx]
            
            if len(price_a) < 2:
                return 1.0, 0.0, 0.0
            
            # Prepare data for OLS
            X = sm.add_constant(price_b.values)
            
            # Fit OLS model
            model = sm.OLS(price_a.values, X).fit()
            
            # Return hedge ratio (beta), intercept (alpha), and R-squared
            return model.params[1], model.params[0], model.rsquared
        
        except Exception as e:
            print(f"Error in calculate_ols_hedge_ratio: {str(e)}")
            return 1.0, 0.0, 0.0
    
    def calculate_spread(self, price_a, price_b, hedge_ratio):
        """
        Calculate the spread between two price series
        
        Args:
            price_a: Series of prices for asset A
            price_b: Series of prices for asset B
            hedge_ratio: The hedge ratio (beta)
        
        Returns:
            Series: The spread (price_a - hedge_ratio * price_b)
        """
        try:
            # Align the two price series
            price_a, price_b = price_a.align(price_b, join="inner")
            
            # Calculate spread
            spread = (price_a - hedge_ratio * price_b).dropna()
            
            return spread
        
        except Exception as e:
            print(f"Error in calculate_spread: {str(e)}")
            return pd.Series()
    
    def calculate_zscore(self, series, window=20):
        """
        Calculate rolling z-score
        
        Args:
            series: Price series
            window: Rolling window size
        
        Returns:
            Series: Z-score values
        """
        try:
            # Calculate rolling mean and std
            rolling_mean = series.rolling(window=window).mean()
            rolling_std = series.rolling(window=window).std()
            
            # Avoid division by zero
            rolling_std = rolling_std.replace(0, np.nan)
            
            # Calculate z-score
            zscore = ((series - rolling_mean) / rolling_std).dropna()
            
            return zscore
        
        except Exception as e:
            print(f"Error in calculate_zscore: {str(e)}")
            return pd.Series()
    
    def calculate_rolling_correlation(self, a, b, window=20):
        """
        Calculate rolling correlation between two series
        
        Args:
            a: First price series
            b: Second price series
            window: Rolling window size
        
        Returns:
            Series: Rolling correlation values
        """
        try:
            correlation = a.rolling(window=window).corr(b).dropna()
            return correlation
        
        except Exception as e:
            print(f"Error in calculate_rolling_correlation: {str(e)}")
            return pd.Series()
    
    def calculate_summary_stats(self, series):
        """
        Calculate summary statistics for a series
        
        Args:
            series: Price series
        
        Returns:
            dict: Summary statistics
        """
        try:
            return {
                "mean": float(series.mean()),
                "std": float(series.std()),
                "min": float(series.min()),
                "max": float(series.max()),
                "skew": float(series.skew()),
                "kurtosis": float(series.kurtosis()),
                "count": int(len(series))
            }
        
        except Exception as e:
            print(f"Error in calculate_summary_stats: {str(e)}")
            return {
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
                "skew": 0.0,
                "kurtosis": 0.0,
                "count": 0
            }
    
    def adf_test(self, series):
        """
        Perform Augmented Dickey-Fuller test for stationarity
        
        Args:
            series: Time series data
        
        Returns:
            dict: ADF test results
        """
        if not STATSMODELS_AVAILABLE:
            raise ImportError(
                "statsmodels is required for ADF test.\n"
                "Install it using: pip install statsmodels"
            )
        
        try:
            # Remove NaN values
            series = series.dropna()
            
            # Check minimum data points
            if len(series) < 50:
                raise ValueError(f"ADF test requires at least 50 data points. Got {len(series)}.")
            
            # Perform ADF test
            result = adfuller(series, autolag="AIC")
            
            # Extract results
            adf_stat = result[0]
            p_value = result[1]
            critical_values = result[4]
            
            return {
                "adf_statistic": float(adf_stat),
                "p_value": float(p_value),
                "critical_1%": float(critical_values["1%"]),
                "critical_5%": float(critical_values["5%"]),
                "critical_10%": float(critical_values["10%"]),
                "is_stationary": p_value < 0.05,
                "n_observations": len(series),
                "interpretation": "Stationary (reject null hypothesis)" if p_value < 0.05 else "Non-stationary (fail to reject null hypothesis)"
            }
        
        except ImportError as e:
            raise ImportError(str(e))
        
        except Exception as e:
            print(f"Error in adf_test: {str(e)}")
            raise
