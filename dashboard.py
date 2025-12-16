import streamlit as st
import plotly.graph_objects as go
import plotly.express as px  
from plotly.subplots import make_subplots
import pandas as pd
import time


from analytics import (
    load_data, 
    calculate_ols_hedge_ratio, 
    calculate_spread, 
    calculate_zscore, 
    calculate_rolling_correlation, 
    perform_adf_test,
    run_backtest
)

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Quant Analytics Terminal", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚡ Real-Time Statistical Arbitrage Dashboard")
st.markdown("Monitor live cointegration, execute backtests, and analyze correlations.")

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("1. Pair Selection")
# [Requirement: Symbol selection]
symbol_y = st.sidebar.selectbox("Dependent Asset (Y)", ["btcusdt", "ethusdt", "solusdt", "bnbusdt"], index=1)
symbol_x = st.sidebar.selectbox("Independent Asset (X)", ["btcusdt", "ethusdt", "solusdt", "bnbusdt"], index=0)

st.sidebar.header("2. Model Settings")
# [Requirement: Sampling for selectable timeframes]
timeframe_map = {"1 Second": "1S", "1 Minute": "1Min", "5 Minutes": "5Min"}
tf_label = st.sidebar.selectbox("Resample Interval", list(timeframe_map.keys()), index=1)
timeframe = timeframe_map[tf_label]

# [Requirement: Rolling window control]
window_size = st.sidebar.number_input("Rolling Window", min_value=10, max_value=200, value=30)
# [Requirement: Alert threshold]
z_threshold = st.sidebar.slider("Z-Score Threshold", 1.0, 4.0, 2.0, 0.1)

st.sidebar.markdown("---")
# [Requirement: Live Analytics Auto-update]
auto_refresh = st.sidebar.checkbox("Enable Live Refresh", value=True)
refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 1, 10, 2)

# --- DATA LOADING & PROCESSING ---
df_y = load_data(symbol_y, timeframe)
df_x = load_data(symbol_x, timeframe)

if not df_y.empty and not df_x.empty:
    
    # Align data indices
    common_idx = df_y.index.intersection(df_x.index)
    
    if len(common_idx) > window_size:
        series_y = df_y.loc[common_idx]['close']
        series_x = df_x.loc[common_idx]['close']

        # --- RUN ANALYTICS ---
        hedge_ratio = calculate_ols_hedge_ratio(series_y, series_x)
        spread = calculate_spread(series_y, series_x, hedge_ratio)
        zscore = calculate_zscore(spread, window=window_size)
        rolling_corr = calculate_rolling_correlation(series_y, series_x, window=window_size)
        adf_res = perform_adf_test(spread)
        
        # [Requirement: Backtest Strategy Extension]
        backtest_df = run_backtest(spread, zscore, entry_threshold=z_threshold)
        total_pnl = backtest_df['cumulative_pnl'].iloc[-1]
        
        # [Requirement: Cross-correlation Heatmap Extension]
        corr_matrix = pd.DataFrame({
            symbol_y: series_y, 
            symbol_x: series_x
        }).pct_change().corr()

        # --- DISPLAY METRICS ---
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Hedge Ratio (Beta)", f"{hedge_ratio:.4f}")
        c2.metric("Current Z-Score", f"{zscore.iloc[-1]:.2f}")
        c3.metric("Current Correlation", f"{rolling_corr.iloc[-1]:.2f}")
        c4.metric("Strategy PnL (Sim)", f"{total_pnl:.4f}", delta_color="normal")
        
        if adf_res:
            st.caption(f"ADF Test: P-Value {adf_res['p_value']:.4f} | Stationary: {adf_res['is_stationary']}")

        # [Requirement: Alerting]
        if abs(zscore.iloc[-1]) > z_threshold:
            st.error(f"🚨 ALERT: Z-Score Breakout ({zscore.iloc[-1]:.2f}) exceeds threshold!")

        # --- MAIN VISUALIZATION (5 ROWS) ---
        # [Requirement: Interactive visualizations]
        fig = make_subplots(
            rows=5, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.03,
            subplot_titles=(
                "Price Action", 
                "Spread (Residuals)", 
                "Z-Score (Standardized)", 
                "Rolling Correlation", 
                "Backtest Cumulative PnL"
            )
        )
        
        # 1. Price
        fig.add_trace(go.Scatter(x=series_y.index, y=series_y, name=symbol_y), row=1, col=1)
        fig.add_trace(go.Scatter(x=series_x.index, y=series_x, name=symbol_x), row=1, col=1)
        # 2. Spread
        fig.add_trace(go.Scatter(x=spread.index, y=spread, name="Spread", line=dict(color='orange')), row=2, col=1)
        # 3. Z-Score
        fig.add_trace(go.Scatter(x=zscore.index, y=zscore, name="Z-Score", line=dict(color='blue')), row=3, col=1)
        fig.add_hline(y=z_threshold, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=-z_threshold, line_dash="dash", line_color="red", row=3, col=1)
        # 4. Correlation
        fig.add_trace(go.Scatter(x=rolling_corr.index, y=rolling_corr, name="Corr", line=dict(color='purple')), row=4, col=1)
        # 5. PnL
        fig.add_trace(go.Scatter(x=backtest_df.index, y=backtest_df['cumulative_pnl'], name="PnL", fill='tozeroy', line=dict(color='green')), row=5, col=1)
        
        fig.update_layout(height=1100, template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

        # --- HEATMAP & TABLE ---
        col_left, col_right = st.columns([1, 2])
        
        with col_left:
            st.subheader("Correlation Heatmap")
            # [Requirement: Heatmap]
            fig_heat = px.imshow(corr_matrix, text_auto=True, template="plotly_dark", height=300)
            st.plotly_chart(fig_heat, use_container_width=True)

        with col_right:
            st.subheader("Recent Strategy Signals")
            # [Requirement: Table displaying stats]
            display_cols = backtest_df[['spread', 'z', 'position', 'cumulative_pnl']].tail(10)
            st.dataframe(display_cols.style.format("{:.4f}"))

        # --- DATA EXPORT ---
        # [Requirement: Download options]
        st.markdown("### 📥 Export Data")
        csv_data = backtest_df.to_csv().encode('utf-8')
        st.download_button(
            label="Download Full Analytics CSV",
            data=csv_data,
            file_name=f"quant_analysis_{symbol_y}_{symbol_x}.csv",
            mime="text/csv"
        )

    else:
        st.info(f"Insufficient data. Waiting for {window_size} overlapping periods...")

else:
    st.warning("Waiting for Data Stream... Ensure 'ingestion.py' is running.")
    st.write("If you just started ingestion, please wait 30 seconds for the buffer to fill.")

# [Requirement: Live Loop]
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()