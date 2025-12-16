"""Quantitative analytics module."""
import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller
from statsmodels.api import OLS, add_constant

class QuantAnalytics:
    @staticmethod
    def resample_ticks(df, timeframe):
        if df.empty:
            return pd.DataFrame()
        df = df.copy().set_index('timestamp')
        ohlc = df['price'].resample(timeframe).ohlc()
        volume = df['quantity'].resample(timeframe).sum()
        result = ohlc.copy()
        result['volume'] = volume
        return result.dropna()
    
    @staticmethod
    def calculate_ols_hedge_ratio(price_a, price_b):
        if len(price_a) < 2 or len(price_b) < 2:
            return 0.0, 0.0, 0.0
        df = pd.DataFrame({'a': price_a, 'b': price_b}).dropna()
        if len(df) < 2:
            return 0.0, 0.0, 0.0
        X = add_constant(df['b'])
        model = OLS(df['a'], X).fit()
        return model.params[1], model.params[0], model.rsquared
    
    @staticmethod
    def calculate_spread(price_a, price_b, hedge_ratio):
        df = pd.DataFrame({'a': price_a, 'b': price_b}).dropna()
        if df.empty:
            return pd.Series()
        return df['a'] - hedge_ratio * df['b']
    
    @staticmethod
    def calculate_zscore(series, window=20):
        if len(series) < window:
            return pd.Series(index=series.index, dtype=float)
        rolling_mean = series.rolling(window=window).mean()
        rolling_std = series.rolling(window=window).std()
        return (series - rolling_mean) / rolling_std
    
    @staticmethod
    def calculate_rolling_correlation(price_a, price_b, window=20):
        df = pd.DataFrame({'a': price_a, 'b': price_b}).dropna()
        if len(df) < window:
            return pd.Series(index=df.index, dtype=float)
        return df['a'].rolling(window=window).corr(df['b'])
    
    @staticmethod
    def adf_test(series):
        if len(series) < 10:
            return {'adf_statistic': np.nan, 'p_value': np.nan, 'critical_1%': np.nan,
                    'critical_5%': np.nan, 'critical_10%': np.nan, 'is_stationary': False}
        series_clean = series.dropna()
        if len(series_clean) < 10:
            return {'adf_statistic': np.nan, 'p_value': np.nan, 'critical_1%': np.nan,
                    'critical_5%': np.nan, 'critical_10%': np.nan, 'is_stationary': False}
        try:
            result = adfuller(series_clean, autolag='AIC')
            return {'adf_statistic': result[0], 'p_value': result[1],
                    'critical_1%': result[4]['1%'], 'critical_5%': result[4]['5%'],
                    'critical_10%': result[4]['10%'], 'is_stationary': result[1] < 0.05}
        except:
            return {'adf_statistic': np.nan, 'p_value': np.nan, 'critical_1%': np.nan,
                    'critical_5%': np.nan, 'critical_10%': np.nan, 'is_stationary': False}
    
    @staticmethod
    def calculate_summary_stats(prices):
        if prices.empty:
            return {}
        returns = prices.pct_change()
        return {'count': len(prices), 'mean': prices.mean(), 'std': prices.std(),
                'min': prices.min(), 'max': prices.max(),
                'last': prices.iloc[-1] if len(prices) > 0 else np.nan,
                'returns_mean': returns.mean() if len(returns) > 1 else np.nan,
                'returns_std': returns.std() if len(returns) > 1 else np.nan}
