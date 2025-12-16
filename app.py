"""Gemscap Quantitative Analytics Platform"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime
from storage import TickStorage
from ingestion import BinanceTickIngestion
from analytics import QuantAnalytics

st.set_page_config(page_title="Gemscap Quant Analytics", page_icon="📊", layout="wide")

st.markdown("""
<style>
.main-header {font-size: 2.5rem; font-weight: 700; color: #0ea5e9; margin-bottom: 0.5rem;}
</style>
""", unsafe_allow_html=True)

if 'storage' not in st.session_state:
    st.session_state.storage = TickStorage()
if 'ingestion' not in st.session_state:
    st.session_state.ingestion = None
if 'analytics' not in st.session_state:
    st.session_state.analytics = QuantAnalytics()
if 'alerts' not in st.session_state:
    st.session_state.alerts = []
if 'run_adf' not in st.session_state:
    st.session_state.run_adf = False

st.markdown('<p class="main-header">📊 Gemscap Quantitative Analytics Platform</p>', unsafe_allow_html=True)
st.markdown("*Real-time Statistical Arbitrage & Pairs Trading Analytics*")

st.sidebar.header("⚙️ Configuration")
st.sidebar.subheader("Data Ingestion")

default_symbols = ['BTCUSDT', 'ETHUSDT']
symbols_input = st.sidebar.text_input("Trading Symbols", value=",".join(default_symbols))
symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("▶️ Start", use_container_width=True):
        if st.session_state.ingestion is None or not st.session_state.ingestion.is_running():
            st.session_state.ingestion = BinanceTickIngestion(symbols, st.session_state.storage)
            st.session_state.ingestion.start()
            st.success(f"Started for {len(symbols)} symbols")
with col2:
    if st.button("⏹️ Stop", use_container_width=True):
        if st.session_state.ingestion and st.session_state.ingestion.is_running():
            st.session_state.ingestion.stop()
            st.success("Stopped")

if st.session_state.ingestion and st.session_state.ingestion.is_running():
    st.sidebar.success("✅ Active")
    stats = st.session_state.ingestion.get_stats()
    st.sidebar.markdown("**Live Counts:**")
    for symbol, stat in stats.items():
        st.sidebar.metric(symbol.upper(), f"{stat['count']:,}", f"${stat['last_price']:,.2f}")
else:
    st.sidebar.info("⏸️ Inactive")

st.sidebar.markdown("---")
st.sidebar.subheader("Analytics Config")

available_symbols = st.session_state.storage.get_symbols()
if not available_symbols:
    available_symbols = symbols

symbol_a = st.sidebar.selectbox("Symbol A", options=available_symbols, index=0 if available_symbols else 0)
symbol_b = st.sidebar.selectbox("Symbol B", options=available_symbols, index=1 if len(available_symbols) > 1 else 0)

timeframe_options = {"1 Second": "1S", "1 Minute": "1T", "5 Minutes": "5T"}
timeframe_label = st.sidebar.selectbox("Timeframe", options=list(timeframe_options.keys()), index=1)
timeframe = timeframe_options[timeframe_label]

rolling_window = st.sidebar.slider("Rolling Window", 5, 100, 20, 5)
alert_threshold = st.sidebar.slider("Alert Z-Score", 1.0, 4.0, 2.0, 0.1)

st.sidebar.markdown("---")
st.sidebar.subheader("Stationarity Test")
if st.sidebar.button("🔬 Run ADF Test", use_container_width=True):
    st.session_state.run_adf = True

auto_refresh = st.sidebar.checkbox("Auto-refresh (500ms)", value=True)
if st.sidebar.button("🔄 Refresh", use_container_width=True):
    st.rerun()

tab1, tab2, tab3, tab4 = st.tabs(["📈 Live Analytics", "📊 Statistics", "⚠️ Alerts", "💾 Export"])

with tab1:
    tick_count_a = st.session_state.storage.get_tick_count(symbol_a)
    tick_count_b = st.session_state.storage.get_tick_count(symbol_b)
    
    if tick_count_a == 0 or tick_count_b == 0:
        st.warning("⏳ Waiting for data... Start ingestion and wait.")
        st.info(f"{symbol_a}: {tick_count_a} ticks, {symbol_b}: {tick_count_b} ticks")
    else:
        df_a = st.session_state.storage.get_latest_ticks(symbol_a, n=5000)
        df_b = st.session_state.storage.get_latest_ticks(symbol_b, n=5000)
        
        if not df_a.empty and not df_b.empty:
            ohlc_a = st.session_state.analytics.resample_ticks(df_a, timeframe)
            ohlc_b = st.session_state.analytics.resample_ticks(df_b, timeframe)
            
            if not ohlc_a.empty and not ohlc_b.empty and len(ohlc_a) > rolling_window:
                price_a = ohlc_a['close']
                price_b = ohlc_b['close']
                
                hedge_ratio, alpha, r_squared = st.session_state.analytics.calculate_ols_hedge_ratio(price_a, price_b)
                spread = st.session_state.analytics.calculate_spread(price_a, price_b, hedge_ratio)
                zscore = st.session_state.analytics.calculate_zscore(spread, window=rolling_window)
                correlation = st.session_state.analytics.calculate_rolling_correlation(price_a, price_b, window=rolling_window)
                
                if not zscore.empty:
                    latest_zscore = zscore.iloc[-1]
                    if abs(latest_zscore) > alert_threshold:
                        alert_msg = {'timestamp': zscore.index[-1], 'zscore': latest_zscore,
                                   'symbol_pair': f"{symbol_a}/{symbol_b}", 'spread': spread.iloc[-1]}
                        if not any(a['timestamp'] == alert_msg['timestamp'] for a in st.session_state.alerts):
                            st.session_state.alerts.append(alert_msg)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Hedge Ratio (β)", f"{hedge_ratio:.4f}")
                with col2:
                    st.metric("R² (Fit)", f"{r_squared:.4f}")
                with col3:
                    st.metric("Z-Score", f"{zscore.iloc[-1]:.2f}" if not zscore.empty else "N/A")
                with col4:
                    st.metric("Correlation", f"{correlation.iloc[-1]:.4f}" if not correlation.empty else "N/A")
                
                st.subheader("Price Comparison")
                fig_prices = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                                          subplot_titles=(f'{symbol_a} vs {symbol_b}', 'Volume'), row_heights=[0.7, 0.3])
                
                price_a_norm = (price_a / price_a.iloc[0]) * 100
                price_b_norm = (price_b / price_b.iloc[0]) * 100
                
                fig_prices.add_trace(go.Scatter(x=price_a_norm.index, y=price_a_norm, name=symbol_a,
                                              line=dict(color='#0ea5e9', width=2)), row=1, col=1)
                fig_prices.add_trace(go.Scatter(x=price_b_norm.index, y=price_b_norm, name=symbol_b,
                                              line=dict(color='#f59e0b', width=2)), row=1, col=1)
                fig_prices.add_trace(go.Bar(x=ohlc_a.index, y=ohlc_a['volume'], name=f'{symbol_a} Vol',
                                          marker=dict(color='#0ea5e9', opacity=0.5)), row=2, col=1)
                fig_prices.add_trace(go.Bar(x=ohlc_b.index, y=ohlc_b['volume'], name=f'{symbol_b} Vol',
                                          marker=dict(color='#f59e0b', opacity=0.5)), row=2, col=1)
                
                fig_prices.update_layout(height=500, hovermode='x unified', template='plotly_dark')
                fig_prices.update_yaxes(title_text="Normalized Price", row=1, col=1)
                fig_prices.update_yaxes(title_text="Volume", row=2, col=1)
                st.plotly_chart(fig_prices, use_container_width=True)
                
                st.subheader("Spread Analysis")
                fig_spread = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                                          subplot_titles=('Spread', 'Z-Score'), row_heights=[0.5, 0.5])
                
                fig_spread.add_trace(go.Scatter(x=spread.index, y=spread, name='Spread',
                                              line=dict(color='#8b5cf6', width=2)), row=1, col=1)
                fig_spread.add_hline(y=spread.mean(), line_dash="dash", line_color="gray",
                                   annotation_text=f"Mean: {spread.mean():.2f}", row=1, col=1)
                
                if not zscore.empty:
                    fig_spread.add_trace(go.Scatter(x=zscore.index, y=zscore, name='Z-Score',
                                                  line=dict(color='#10b981', width=2)), row=2, col=1)
                    fig_spread.add_hline(y=alert_threshold, line_dash="dash", line_color="red",
                                       annotation_text=f"+{alert_threshold}", row=2, col=1)
                    fig_spread.add_hline(y=-alert_threshold, line_dash="dash", line_color="red",
                                       annotation_text=f"-{alert_threshold}", row=2, col=1)
                    fig_spread.add_hline(y=0, line_dash="dot", line_color="gray", row=2, col=1)
                
                fig_spread.update_layout(height=500, hovermode='x unified', template='plotly_dark')
                fig_spread.update_yaxes(title_text="Spread", row=1, col=1)
                fig_spread.update_yaxes(title_text="Z-Score", row=2, col=1)
                st.plotly_chart(fig_spread, use_container_width=True)
                
                st.subheader("Rolling Correlation")
                fig_corr = go.Figure()
                if not correlation.empty:
                    fig_corr.add_trace(go.Scatter(x=correlation.index, y=correlation, name='Correlation',
                                                 fill='tozeroy', line=dict(color='#ec4899', width=2)))
                    fig_corr.add_hline(y=0.8, line_dash="dash", line_color="green", annotation_text="Strong (0.8)")
                    fig_corr.add_hline(y=0.5, line_dash="dot", line_color="yellow", annotation_text="Moderate (0.5)")
                
                fig_corr.update_layout(height=300, hovermode='x unified', template='plotly_dark',
                                     yaxis_title="Correlation")
                st.plotly_chart(fig_corr, use_container_width=True)
                
                if st.session_state.run_adf:
                    st.subheader("🔬 ADF Test (Stationarity)")
                    adf_results = st.session_state.analytics.adf_test(spread)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("ADF Statistic", f"{adf_results['adf_statistic']:.4f}")
                    with col2:
                        st.metric("P-Value", f"{adf_results['p_value']:.4f}")
                    with col3:
                        st.metric("Stationary?", "✅ Yes" if adf_results['is_stationary'] else "❌ No")
                    
                    st.markdown("**Critical Values:**")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("1%", f"{adf_results['critical_1%']:.4f}")
                    with c2:
                        st.metric("5%", f"{adf_results['critical_5%']:.4f}")
                    with c3:
                        st.metric("10%", f"{adf_results['critical_10%']:.4f}")
                    
                    if adf_results['is_stationary']:
                        st.success("✅ Spread is stationary (mean-reverting)")
                    else:
                        st.warning("⚠️ Spread may not be stationary")
                    
                    st.session_state.run_adf = False
            else:
                st.info(f"📊 Collecting data... Need {rolling_window} points. Current: {len(ohlc_a) if not ohlc_a.empty else 0}")

with tab2:
    st.subheader("📊 Summary Statistics")
    if tick_count_a > 0 and tick_count_b > 0:
        df_a = st.session_state.storage.get_latest_ticks(symbol_a, n=5000)
        df_b = st.session_state.storage.get_latest_ticks(symbol_b, n=5000)
        
        if not df_a.empty and not df_b.empty:
            ohlc_a = st.session_state.analytics.resample_ticks(df_a, timeframe)
            ohlc_b = st.session_state.analytics.resample_ticks(df_b, timeframe)
            
            if not ohlc_a.empty and not ohlc_b.empty:
                stats_a = st.session_state.analytics.calculate_summary_stats(ohlc_a['close'])
                stats_b = st.session_state.analytics.calculate_summary_stats(ohlc_b['close'])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"### {symbol_a}")
                    st.dataframe(pd.DataFrame([stats_a]).T, use_container_width=True)
                with col2:
                    st.markdown(f"### {symbol_b}")
                    st.dataframe(pd.DataFrame([stats_b]).T, use_container_width=True)

with tab3:
    st.subheader("⚠️ Alerts")
    if st.session_state.alerts:
        for alert in reversed(st.session_state.alerts[-20:]):
            st.warning(f"**{alert['timestamp']}** | {alert['symbol_pair']} | Z-Score: {alert['zscore']:.3f} | Spread: {alert['spread']:.4f}")
        if st.button("Clear Alerts"):
            st.session_state.alerts = []
            st.rerun()
    else:
        st.info("No alerts")

with tab4:
    st.subheader("💾 Export")
    if tick_count_a > 0 or tick_count_b > 0:
        export_type = st.radio("Export:", ["Raw Ticks", "OHLC", "Analytics"])
        
        if export_type == "Raw Ticks":
            export_symbol = st.selectbox("Symbol", available_symbols)
            limit = st.number_input("Records", 100, 50000, 1000, 100)
            if st.button("Generate CSV"):
                df = st.session_state.storage.get_latest_ticks(export_symbol, n=limit)
                csv = df.to_csv(index=False)
                st.download_button("📥 Download", csv, f"{export_symbol}_ticks.csv", "text/csv")
        
        elif export_type == "OHLC":
            if st.button("Generate CSV"):
                df_a = st.session_state.storage.get_latest_ticks(symbol_a, n=5000)
                df_b = st.session_state.storage.get_latest_ticks(symbol_b, n=5000)
                ohlc_a = st.session_state.analytics.resample_ticks(df_a, timeframe)
                ohlc_b = st.session_state.analytics.resample_ticks(df_b, timeframe)
                ohlc_a['symbol'] = symbol_a
                ohlc_b['symbol'] = symbol_b
                combined = pd.concat([ohlc_a, ohlc_b])
                st.download_button("📥 Download", combined.to_csv(), f"ohlc_{timeframe}.csv", "text/csv")
        
        elif export_type == "Analytics":
            if st.button("Generate CSV"):
                df_a = st.session_state.storage.get_latest_ticks(symbol_a, n=5000)
                df_b = st.session_state.storage.get_latest_ticks(symbol_b, n=5000)
                ohlc_a = st.session_state.analytics.resample_ticks(df_a, timeframe)
                ohlc_b = st.session_state.analytics.resample_ticks(df_b, timeframe)
                
                if not ohlc_a.empty and not ohlc_b.empty:
                    price_a = ohlc_a['close']
                    price_b = ohlc_b['close']
                    hedge_ratio, alpha, r_squared = st.session_state.analytics.calculate_ols_hedge_ratio(price_a, price_b)
                    spread = st.session_state.analytics.calculate_spread(price_a, price_b, hedge_ratio)
                    zscore = st.session_state.analytics.calculate_zscore(spread, rolling_window)
                    correlation = st.session_state.analytics.calculate_rolling_correlation(price_a, price_b, rolling_window)
                    
                    analytics_df = pd.DataFrame({
                        'timestamp': spread.index, 'spread': spread.values, 'zscore': zscore.values,
                        'correlation': correlation.values, 'hedge_ratio': hedge_ratio, 'r_squared': r_squared
                    })
                    st.download_button("📥 Download", analytics_df.to_csv(index=False), 
                                     f"analytics_{symbol_a}_{symbol_b}.csv", "text/csv")

st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Ticks", f"{sum(st.session_state.storage.get_tick_count(s) for s in available_symbols):,}")
with col2:
    st.metric("Active Symbols", len(available_symbols))
with col3:
    st.metric("Alerts", len(st.session_state.alerts))
with col4:
    st.metric("Timeframe", timeframe_label)

if auto_refresh:
    time.sleep(0.5)
    st.rerun()
