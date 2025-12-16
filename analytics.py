import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
import sqlite3

DB_NAME = "market_data.db"

def load_data(symbol, timeframe='1Min', limit=10000):
    """
    Fetches raw tick data and resamples it to OHLC.
    [Requirement: Sampling for selectable timeframes]
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        # Fetch last N ticks to keep performance fast
        query = f"""
            SELECT timestamp, price 
            FROM trades 
            WHERE symbol = '{symbol}' 
            ORDER BY timestamp DESC 
            LIMIT {limit}
        """
        df = pd.read_sql(query, conn)
        conn.close()
        
        if df.empty:
            return pd.DataFrame()

        # Convert to datetime and sort
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        df.set_index('timestamp', inplace=True)
        
        # Resample to the requested timeframe (1S, 1Min, 5Min)
        # We use the 'last' price for Close
        resampled = df['price'].resample(timeframe).ohlc()
        
        # Drop gaps (periods with no trades)
        resampled.dropna(inplace=True)
        
        return resampled
    except Exception as e:
        print(f"Analytics Error: {e}")
        return pd.DataFrame()

def calculate_ols_hedge_ratio(series_y, series_x):
    """
    Calculates the Hedge Ratio (Beta) using Ordinary Least Squares.
    [Requirement: Hedge ratio via OLS regression]
    """
    # Align timestamps
    df = pd.concat([series_y, series_x], axis=1).dropna()
    if df.empty or len(df) < 5: 
        return 0.0
    
    Y = df.iloc[:, 0]
    X = sm.add_constant(df.iloc[:, 1]) # Add intercept
    
    try:
        model = sm.OLS(Y, X).fit()
        return model.params.iloc[1] # Return the slope (beta)
    except:
        return 0.0

def calculate_spread(series_y, series_x, hedge_ratio):
    """
    Computes the Spread: Y - (Beta * X)
    [Requirement: Spread]
    """
    df = pd.concat([series_y, series_x], axis=1).dropna()
    if df.empty: return pd.Series()
    return df.iloc[:, 0] - (hedge_ratio * df.iloc[:, 1])

def calculate_zscore(spread, window=20):
    """
    Computes Rolling Z-Score.
    [Requirement: Z-score]
    """
    if spread.empty: return pd.Series()
    
    mean = spread.rolling(window=window).mean()
    std = spread.rolling(window=window).std()
    
    z_score = (spread - mean) / std
    return z_score.fillna(0)

def calculate_rolling_correlation(series_y, series_x, window=20):
    """
    Computes Rolling Correlation.
    [Requirement: Rolling correlation]
    """
    df = pd.concat([series_y, series_x], axis=1).dropna()
    if df.empty: return pd.Series()
    
    return df.iloc[:, 0].rolling(window=window).corr(df.iloc[:, 1])

def perform_adf_test(spread):
    """
    Augmented Dickey-Fuller Test for Mean Reversion.
    [Requirement: ADF test]
    """
    clean_spread = spread.dropna()
    if len(clean_spread) < 20: 
        return None # Not enough data
    
    try:
        result = adfuller(clean_spread)
        return {
            'adf_stat': result[0],
            'p_value': result[1],
            'is_stationary': result[1] < 0.05
        }
    except:
        return None

def run_backtest(spread, zscore, entry_threshold=2.0):
    """
    Simulates a strategy: Short Spread if Z > 2, Long Spread if Z < -2.
    [Requirement: Mini mean-reversion backtest]
    """
    df = pd.DataFrame({'spread': spread, 'z': zscore})
    df['position'] = 0 
    
    current_pos = 0 # 0=Flat, 1=Long, -1=Short
    positions = []
    
    for i in range(len(df)):
        z = df.iloc[i]['z']
        
        # Entry Logic
        if current_pos == 0:
            if z > entry_threshold: 
                current_pos = -1 # Sell Spread
            elif z < -entry_threshold: 
                current_pos = 1  # Buy Spread
        
        # Exit Logic (Mean Reversion)
        elif current_pos == -1 and z <= 0: 
            current_pos = 0
        elif current_pos == 1 and z >= 0: 
            current_pos = 0
            
        positions.append(current_pos)
        
    df['position'] = positions
    
    # Calculate PnL: Position * Change in Spread
    df['spread_change'] = df['spread'].diff()
    df['pnl'] = df['position'].shift(1) * df['spread_change']
    df['cumulative_pnl'] = df['pnl'].cumsum()
    
    return df