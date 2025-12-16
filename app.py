"""Gemscap Quantitative Analytics Platform"""

import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from storage import TickStorage
from ingestion import BinanceTickIngestion
from analytics import QuantAnalytics

# ------------------------------------------------------------------
# Page config
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Gemscap Quant Analytics",
    page_icon="📊",
    layout="wide"
)

st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #0ea5e9;
        margin-bottom: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# Session state initialization
# ------------------------------------------------------------------
if "storage" not in st.session_state:
    st.session_state.storage = TickStorage()

if "ingestion" not in st.session_state:
    st.session_state.ingestion = None

if "analytics" not in st.session_state:
    st.session_state.analytics = QuantAnalytics()

if "alerts" not in st.session_state:
    st.session_state.alerts = []

if "run_adf" not in st.session_state:
    st.session_state.run_adf = False

if "auto_started" not in st.session_state:
    st.session_state.auto_started = False

if "adf_results" not in st.session_state:
    st.session_state.adf_results = None

# ------------------------------------------------------------------
# Header
# ------------------------------------------------------------------
st.markdown(
    '<p class="main-header">📊 Gemscap Quantitative Analytics Platform</p>',
    unsafe_allow_html=True,
)
st.markdown("*Real-time Statistical Arbitrage & Pairs Trading Analytics*")

# ------------------------------------------------------------------
# Sidebar: Configuration
# ------------------------------------------------------------------
st.sidebar.header("⚙️ Configuration")
st.sidebar.subheader("Data Ingestion")

default_symbols = ["BTCUSDT", "ETHUSDT"]
symbols_input = st.sidebar.text_input(
    "Trading Symbols",
    value=",".join(default_symbols),
)
symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

# AUTO-START on first load
if not st.session_state.auto_started:
    try:
        if st.session_state.ingestion is None:
            st.session_state.ingestion = BinanceTickIngestion(
                symbols, st.session_state.storage
            )
            st.session_state.ingestion.start()
            st.session_state.auto_started = True
            st.sidebar.success("✅ Auto-started data ingestion!")
    except Exception as e:
        st.sidebar.error(f"Auto-start failed: {str(e)}")

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("▶️ Start", use_container_width=True):
        if (
            st.session_state.ingestion is None
            or not st.session_state.ingestion.is_running()
        ):
            try:
                st.session_state.ingestion = BinanceTickIngestion(
                    symbols, st.session_state.storage
                )
                st.session_state.ingestion.start()
                st.success(f"Started for {len(symbols)} symbols")
            except Exception as e:
                st.error(f"Failed to start ingestion: {str(e)}")

with col2:
    if st.button("⏹️ Stop", use_container_width=True):
        if (
            st.session_state.ingestion
            and st.session_state.ingestion.is_running()
        ):
            st.session_state.ingestion.stop()
            st.success("Stopped")

if st.session_state.ingestion and st.session_state.ingestion.is_running():
    st.sidebar.success("✅ Active")
    stats = st.session_state.ingestion.get_stats()
    st.sidebar.markdown("**Live Counts:**")
    for symbol, stat in stats.items():
        st.sidebar.metric(
            symbol.upper(),
            f"{stat['count']:,}",
            f"${stat['last_price']:,.2f}",
        )
else:
    st.sidebar.info("⏸️ Inactive")

# ------------------------------------------------------------------
# Sidebar: Analytics Config
# ------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("Analytics Config")

available_symbols = st.session_state.storage.get_symbols()
if not available_symbols:
    available_symbols = symbols

symbol_a = st.sidebar.selectbox("Symbol A", options=available_symbols, index=0)

symbol_b = st.sidebar.selectbox(
    "Symbol B",
    options=available_symbols,
    index=1 if len(available_symbols) > 1 else 0,
)

# Fixed timeframes
timeframe_options = {
    "1 Second": "1s",
    "1 Minute": "1min",
    "5 Minutes": "5min",
}

timeframe_label = st.sidebar.selectbox(
    "Timeframe", options=list(timeframe_options.keys()), index=1
)

timeframe = timeframe_options[timeframe_label]

rolling_window = st.sidebar.slider("Rolling Window", 5, 100, 20, 5)
alert_threshold = st.sidebar.slider("Alert Z-Score", 1.0, 4.0, 2.0, 0.1)

# ------------------------------------------------------------------
# Sidebar: Stationarity
# ------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("Stationarity Test")

if st.sidebar.button("🔬 Run ADF Test", use_container_width=True):
    st.session_state.run_adf = True
    st.rerun()

auto_refresh = st.sidebar.checkbox("Auto-refresh (500ms)", value=True)

if st.sidebar.button("🔄 Refresh", use_container_width=True):
    st.rerun()

# ------------------------------------------------------------------
# Tabs
# ------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Live Analytics", "📊 Statistics", "⚠️ Alerts", "💾 Export"]
)

# ==================================================================
# TAB 1: Live Analytics
# ==================================================================
with tab1:
    st.subheader("📈 Live Analytics Dashboard")
    
    tick_count_a = st.session_state.storage.get_tick_count(symbol_a)
    tick_count_b = st.session_state.storage.get_tick_count(symbol_b)

    col_info1, col_info2 = st.columns(2)
    col_info1.metric(f"{symbol_a} Ticks", f"{tick_count_a:,}")
    col_info2.metric(f"{symbol_b} Ticks", f"{tick_count_b:,}")

    if tick_count_a == 0 or tick_count_b == 0:
        st.warning("⏳ Waiting for data... Data ingestion is starting automatically.")
        st.info(f"Current status: {symbol_a}: {tick_count_a} ticks, {symbol_b}: {tick_count_b} ticks")
        
        # Show loading animation
        with st.spinner("Collecting data from Binance..."):
            time.sleep(2)
            st.rerun()
    else:
        try:
            df_a = st.session_state.storage.get_latest_ticks(symbol_a, n=5000)
            df_b = st.session_state.storage.get_latest_ticks(symbol_b, n=5000)

            if not df_a.empty and not df_b.empty:
                # Resample to OHLC
                ohlc_a = st.session_state.analytics.resample_ticks(df_a, timeframe)
                ohlc_b = st.session_state.analytics.resample_ticks(df_b, timeframe)

                if (
                    not ohlc_a.empty
                    and not ohlc_b.empty
                    and len(ohlc_a) > rolling_window
                ):
                    price_a = ohlc_a["close"]
                    price_b = ohlc_b["close"]

                    # Calculate metrics
                    hedge_ratio, alpha, r_squared = (
                        st.session_state.analytics.calculate_ols_hedge_ratio(
                            price_a, price_b
                        )
                    )

                    spread = st.session_state.analytics.calculate_spread(
                        price_a, price_b, hedge_ratio
                    )

                    zscore = st.session_state.analytics.calculate_zscore(
                        spread, window=rolling_window
                    )

                    correlation = (
                        st.session_state.analytics.calculate_rolling_correlation(
                            price_a, price_b, window=rolling_window
                        )
                    )

                    # Display key metrics
                    st.markdown("### 📊 Key Metrics")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Hedge Ratio (β)", f"{hedge_ratio:.4f}")
                    col2.metric("R² (Fit Quality)", f"{r_squared:.4f}")
                    col3.metric(
                        "Current Z-Score",
                        f"{zscore.iloc[-1]:.2f}" if not zscore.empty else "N/A",
                    )
                    col4.metric(
                        "Correlation",
                        f"{correlation.iloc[-1]:.4f}" if not correlation.empty else "N/A",
                    )

                    # Check for alerts
                    if not zscore.empty and abs(zscore.iloc[-1]) > alert_threshold:
                        # Avoid duplicate alerts
                        last_alert = st.session_state.alerts[-1] if st.session_state.alerts else None
                        current_time = datetime.now()
                        
                        should_add_alert = True
                        if last_alert:
                            last_time = datetime.strptime(last_alert['timestamp'], "%Y-%m-%d %H:%M:%S")
                            if (current_time - last_time).seconds < 5:  # Don't add alert within 5 seconds
                                should_add_alert = False
                        
                        if should_add_alert:
                            st.session_state.alerts.append({
                                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                                "symbol_pair": f"{symbol_a}/{symbol_b}",
                                "zscore": zscore.iloc[-1],
                                "spread": spread.iloc[-1]
                            })

                    # Store spread for ADF test
                    st.session_state.current_spread = spread

                    # Create visualizations
                    st.markdown("### 📈 Price Charts")
                    
                    # Price comparison chart
                    fig1 = make_subplots(
                        rows=2, cols=1,
                        subplot_titles=(f'{symbol_a} vs {symbol_b} Prices', 'Spread & Z-Score'),
                        vertical_spacing=0.15,
                        row_heights=[0.5, 0.5]
                    )

                    # Normalize prices for comparison
                    price_a_norm = (price_a - price_a.iloc[0]) / price_a.iloc[0] * 100
                    price_b_norm = (price_b - price_b.iloc[0]) / price_b.iloc[0] * 100

                    fig1.add_trace(
                        go.Scatter(x=price_a_norm.index, y=price_a_norm, name=symbol_a, line=dict(color='#3b82f6')),
                        row=1, col=1
                    )
                    fig1.add_trace(
                        go.Scatter(x=price_b_norm.index, y=price_b_norm, name=symbol_b, line=dict(color='#ef4444')),
                        row=1, col=1
                    )

                    # Spread and Z-score
                    fig1.add_trace(
                        go.Scatter(x=spread.index, y=spread, name='Spread', line=dict(color='#10b981')),
                        row=2, col=1
                    )
                    
                    if not zscore.empty:
                        fig1.add_trace(
                            go.Scatter(x=zscore.index, y=zscore, name='Z-Score', line=dict(color='#f59e0b'), yaxis='y3'),
                            row=2, col=1
                        )
                        
                        # Add threshold lines
                        fig1.add_hline(y=alert_threshold, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
                        fig1.add_hline(y=-alert_threshold, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
                        fig1.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.3, row=2, col=1)

                    fig1.update_xaxes(title_text="Time", row=2, col=1)
                    fig1.update_yaxes(title_text="% Change", row=1, col=1)
                    fig1.update_yaxes(title_text="Spread Value", row=2, col=1)

                    fig1.update_layout(height=700, showlegend=True, hovermode='x unified')
                    st.plotly_chart(fig1, use_container_width=True)

                    # Correlation chart
                    st.markdown("### 🔗 Rolling Correlation")
                    if not correlation.empty:
                        fig2 = go.Figure()
                        fig2.add_trace(
                            go.Scatter(x=correlation.index, y=correlation, 
                                     fill='tozeroy', name='Correlation',
                                     line=dict(color='#8b5cf6'))
                        )
                        fig2.update_layout(
                            height=300,
                            xaxis_title="Time",
                            yaxis_title="Correlation",
                            hovermode='x'
                        )
                        st.plotly_chart(fig2, use_container_width=True)

                    # ADF Test Section - FIXED TO ALWAYS SHOW WHEN TRIGGERED
                    if st.session_state.run_adf or st.session_state.adf_results is not None:
                        st.markdown("---")
                        st.subheader("🔬 Augmented Dickey-Fuller Test (Stationarity)")

                        # Run ADF test if triggered
                        if st.session_state.run_adf:
                            clean_spread = spread.dropna()

                            if clean_spread.shape[0] < 50:
                                st.warning(f"⚠️ ADF test requires at least 50 data points. Current: {clean_spread.shape[0]}")
                                st.info("Wait for more data to accumulate and try again.")
                                st.session_state.run_adf = False
                                st.session_state.adf_results = None
                            else:
                                try:
                                    with st.spinner("Running ADF test..."):
                                        adf_results = st.session_state.analytics.adf_test(clean_spread)
                                        st.session_state.adf_results = adf_results
                                        st.session_state.run_adf = False
                                    
                                    st.success("✅ ADF Test completed successfully!")
                                
                                except Exception as e:
                                    st.error(f"❌ Error running ADF test: {str(e)}")
                                    st.info("Make sure statsmodels is installed: `pip install statsmodels`")
                                    st.session_state.run_adf = False
                                    st.session_state.adf_results = None

                        # Display results if available
                        if st.session_state.adf_results is not None:
                            adf_results = st.session_state.adf_results
                            
                            c1, c2, c3 = st.columns(3)
                            c1.metric("ADF Statistic", f"{adf_results['adf_statistic']:.4f}")
                            c2.metric("P-Value", f"{adf_results['p_value']:.6f}")
                            
                            if adf_results["is_stationary"]:
                                c3.metric("Stationary?", "✅ Yes", delta="Good for trading")
                            else:
                                c3.metric("Stationary?", "❌ No", delta="Poor for trading", delta_color="inverse")

                            st.markdown("**Critical Values (Test Statistic must be less than these)**")
                            cc1, cc2, cc3 = st.columns(3)
                            cc1.metric("1% Level", f"{adf_results['critical_1%']:.4f}")
                            cc2.metric("5% Level", f"{adf_results['critical_5%']:.4f}")
                            cc3.metric("10% Level", f"{adf_results['critical_10%']:.4f}")

                            # Interpretation
                            st.info(f"""
                            **Interpretation:**
                            - **P-Value < 0.05**: Spread is stationary (good for mean-reversion trading) ✅
                            - **P-Value ≥ 0.05**: Spread is non-stationary (not suitable for pairs trading) ❌
                            - **ADF Statistic**: More negative values indicate stronger stationarity
                            - **Result**: {adf_results['interpretation']}
                            - **Observations**: {adf_results['n_observations']} data points used
                            """)
                            
                            # Clear button
                            if st.button("🗑️ Clear ADF Results"):
                                st.session_state.adf_results = None
                                st.rerun()

                else:
                    st.warning(f"⏳ Collecting more data... Need at least {rolling_window} candles. Current: {len(ohlc_a) if not ohlc_a.empty else 0}")
                    progress = min(len(ohlc_a) / rolling_window, 1.0) if not ohlc_a.empty else 0
                    st.progress(progress)
            else:
                st.warning("⏳ Processing tick data...")
        
        except Exception as e:
            st.error(f"❌ Error in analytics: {str(e)}")
            st.info("Check if data ingestion is running properly.")
            import traceback
            st.code(traceback.format_exc())

# ==================================================================
# TAB 2: Statistics
# ==================================================================
with tab2:
    st.subheader("📊 Summary Statistics")

    if tick_count_a > 0 and tick_count_b > 0:
        try:
            df_a = st.session_state.storage.get_latest_ticks(symbol_a, n=5000)
            df_b = st.session_state.storage.get_latest_ticks(symbol_b, n=5000)

            if not df_a.empty and not df_b.empty:
                ohlc_a = st.session_state.analytics.resample_ticks(df_a, timeframe)
                ohlc_b = st.session_state.analytics.resample_ticks(df_b, timeframe)

                if not ohlc_a.empty and not ohlc_b.empty:
                    stats_a = st.session_state.analytics.calculate_summary_stats(
                        ohlc_a["close"]
                    )
                    stats_b = st.session_state.analytics.calculate_summary_stats(
                        ohlc_b["close"]
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"### {symbol_a}")
                        stats_df_a = pd.DataFrame([stats_a]).T
                        stats_df_a.columns = ['Value']
                        st.dataframe(stats_df_a, use_container_width=True)
                        
                    with col2:
                        st.markdown(f"### {symbol_b}")
                        stats_df_b = pd.DataFrame([stats_b]).T
                        stats_df_b.columns = ['Value']
                        st.dataframe(stats_df_b, use_container_width=True)

                    # Additional tick statistics
                    st.markdown("---")
                    st.markdown("### 📍 Tick-Level Statistics")
                    
                    col3, col4 = st.columns(2)
                    with col3:
                        st.markdown(f"**{symbol_a}**")
                        st.metric("Total Ticks", f"{len(df_a):,}")
                        st.metric("Latest Price", f"${df_a['price'].iloc[-1]:,.2f}")
                        st.metric("Price Range", f"${df_a['price'].min():.2f} - ${df_a['price'].max():.2f}")
                        
                    with col4:
                        st.markdown(f"**{symbol_b}**")
                        st.metric("Total Ticks", f"{len(df_b):,}")
                        st.metric("Latest Price", f"${df_b['price'].iloc[-1]:,.2f}")
                        st.metric("Price Range", f"${df_b['price'].min():.2f} - ${df_b['price'].max():.2f}")
                else:
                    st.info("⏳ Resampling data...")
            else:
                st.warning("⏳ Waiting for tick data...")
        except Exception as e:
            st.error(f"❌ Error calculating statistics: {str(e)}")
    else:
        st.warning("⏳ No data available. Data ingestion is starting automatically.")

# ==================================================================
# TAB 3: Alerts
# ==================================================================
with tab3:
    st.subheader("⚠️ Trading Alerts")
    
    st.info(f"**Alert Threshold:** Z-Score ≥ ±{alert_threshold}")

    if st.session_state.alerts:
        st.markdown(f"**Total Alerts:** {len(st.session_state.alerts)}")
        
        for i, alert in enumerate(reversed(st.session_state.alerts[-20:]), 1):
            alert_type = "🔴 SELL Signal" if alert['zscore'] > 0 else "🟢 BUY Signal"
            st.warning(
                f"**Alert #{i}** | {alert_type} | {alert['timestamp']}\n\n"
                f"Pair: **{alert['symbol_pair']}** | "
                f"Z-Score: **{alert['zscore']:.3f}** | "
                f"Spread: **{alert['spread']:.4f}**"
            )

        col_btn1, col_btn2 = st.columns([1, 5])
        with col_btn1:
            if st.button("🗑️ Clear All Alerts", use_container_width=True):
                st.session_state.alerts = []
                st.rerun()
            
    else:
        st.info("✅ No alerts triggered. System is monitoring...")
        st.markdown("""
        **How alerts work:**
        - When Z-Score exceeds your threshold, an alert is generated
        - Positive Z-Score (>threshold): Spread is high → Consider SELLING the spread
        - Negative Z-Score (<-threshold): Spread is low → Consider BUYING the spread
        """)

# ==================================================================
# TAB 4: Export
# ==================================================================
with tab4:
    st.subheader("💾 Export Data")
    
    if tick_count_a > 0 or tick_count_b > 0:
        export_format = st.radio("Select Export Format", ["CSV", "Excel", "JSON"], horizontal=True)
        
        st.markdown("### Select Data to Export")
        export_ticks = st.checkbox("Raw Tick Data", value=True)
        export_ohlc = st.checkbox("OHLC Data", value=True)
        export_analytics = st.checkbox("Analytics Results", value=True)
        export_alerts = st.checkbox("Alerts History", value=False)
        
        if st.button("📥 Generate Export File", type="primary"):
            try:
                export_data = {}
                
                # Export ticks
                if export_ticks:
                    df_a = st.session_state.storage.get_latest_ticks(symbol_a, n=10000)
                    df_b = st.session_state.storage.get_latest_ticks(symbol_b, n=10000)
                    export_data[f'{symbol_a}_ticks'] = df_a
                    export_data[f'{symbol_b}_ticks'] = df_b
                
                # Export OHLC
                if export_ohlc and tick_count_a > 0 and tick_count_b > 0:
                    df_a = st.session_state.storage.get_latest_ticks(symbol_a, n=10000)
                    df_b = st.session_state.storage.get_latest_ticks(symbol_b, n=10000)
                    ohlc_a = st.session_state.analytics.resample_ticks(df_a, timeframe)
                    ohlc_b = st.session_state.analytics.resample_ticks(df_b, timeframe)
                    export_data[f'{symbol_a}_ohlc'] = ohlc_a
                    export_data[f'{symbol_b}_ohlc'] = ohlc_b
                
                # Export analytics
                if export_analytics and tick_count_a > 0 and tick_count_b > 0:
                    df_a = st.session_state.storage.get_latest_ticks(symbol_a, n=10000)
                    df_b = st.session_state.storage.get_latest_ticks(symbol_b, n=10000)
                    ohlc_a = st.session_state.analytics.resample_ticks(df_a, timeframe)
                    ohlc_b = st.session_state.analytics.resample_ticks(df_b, timeframe)
                    
                    if len(ohlc_a) > rolling_window and len(ohlc_b) > rolling_window:
                        price_a = ohlc_a["close"]
                        price_b = ohlc_b["close"]
                        hedge_ratio, alpha, r_squared = st.session_state.analytics.calculate_ols_hedge_ratio(price_a, price_b)
                        spread = st.session_state.analytics.calculate_spread(price_a, price_b, hedge_ratio)
                        zscore = st.session_state.analytics.calculate_zscore(spread, window=rolling_window)
                        
                        analytics_df = pd.DataFrame({
                            'spread': spread,
                            'zscore': zscore
                        })
                        export_data['analytics'] = analytics_df
                
                # Export alerts
                if export_alerts and st.session_state.alerts:
                    alerts_df = pd.DataFrame(st.session_state.alerts)
                    export_data['alerts'] = alerts_df
                
                # Generate download button based on format
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if export_format == "CSV":
                    # Combine all dataframes
                    for name, df in export_data.items():
                        csv = df.to_csv(index=True)
                        st.download_button(
                            label=f"📥 Download {name}.csv",
                            data=csv,
                            file_name=f"{name}_{timestamp}.csv",
                            mime="text/csv"
                        )
                
                elif export_format == "Excel":
                    from io import BytesIO
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        for name, df in export_data.items():
                            df.to_excel(writer, sheet_name=name[:31])  # Excel sheet name limit
                    
                    st.download_button(
                        label="📥 Download Excel File",
                        data=output.getvalue(),
                        file_name=f"gemscap_export_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                elif export_format == "JSON":
                    json_data = {}
                    for name, df in export_data.items():
                        json_data[name] = df.to_json(orient='records', date_format='iso')
                    
                    import json
                    st.download_button(
                        label="📥 Download JSON File",
                        data=json.dumps(json_data, indent=2),
                        file_name=f"gemscap_export_{timestamp}.json",
                        mime="application/json"
                    )
                
                st.success(f"✅ Export files generated successfully!")
                
            except Exception as e:
                st.error(f"❌ Export failed: {str(e)}")
    else:
        st.info("⏳ No data available to export. Data ingestion is starting automatically.")
        st.markdown("""
        **Export Features:**
        - Export raw tick data for both symbols
        - Export OHLC (Open, High, Low, Close) data
        - Export analytics results (spread, z-score, correlation)
        - Export alerts history
        - Multiple formats: CSV, Excel, JSON
        """)

# ------------------------------------------------------------------
# Footer / Auto refresh
# ------------------------------------------------------------------
st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: #64748b;">Gemscap Quantitative Analytics Platform v1.0 | '
    f'Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>',
    unsafe_allow_html=True
)

if auto_refresh:
    time.sleep(0.5)
    st.rerun()
