# 📊 Gemscap Quantitative Analytics Platform

**Real-time Statistical Arbitrage & Pairs Trading Analytics System**

A production-grade quantitative analytics application for real-time pairs trading, statistical arbitrage analysis, and algorithmic trading research. Built for the Gemscap Global Analyst Quant Developer Internship assignment.

---

## 🎯 Features

### Core Analytics
- ✅ **Real-time WebSocket Data Ingestion** - Live tick data from Binance Futures
- ✅ **OLS Hedge Ratio Estimation** - Statistical regression for pairs trading
- ✅ **Spread Analysis** - Market-neutral spread construction
- ✅ **Z-Score Monitoring** - Rolling z-score with configurable windows
- ✅ **Rolling Correlation** - Dynamic correlation tracking between pairs
- ✅ **ADF Stationarity Test** - Augmented Dickey-Fuller test for mean reversion
- ✅ **Alert System** - Automated alerts when z-score exceeds thresholds
- ✅ **Data Export** - CSV export for raw ticks, OHLC, and analytics

### User Interface
- 📈 **Interactive Plotly Charts** - Zoom, pan, and hover capabilities
- 🎨 **Professional Dashboard** - Multi-tab interface (Live Analytics, Statistics, Alerts, Export)
- ⚡ **Real-time Updates** - 500ms refresh for live monitoring
- 🎛️ **Configurable Parameters** - Symbol selection, timeframes (1s/1m/5m), rolling windows

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Internet connection (for Binance WebSocket)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/adityagorave21/gemscap_quant_app.git
   cd gemscap_quant_app
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   
   **Windows (PowerShell):**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   
   **Windows (CMD):**
   ```cmd
   venv\Scripts\activate.bat
   ```
   
   **Linux/Mac:**
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

**OR use the automated launchers:**
- Windows CMD: `run_app.bat`
- PowerShell: `.\run_app.ps1`

The application will automatically open in your browser at **http://localhost:8501**

---

## 📖 Usage Guide

### Step 1: Start Data Ingestion
1. In the sidebar, verify trading symbols (default: BTCUSDT, ETHUSDT)
2. Click **"▶️ Start"** button
3. Wait 20-30 seconds for initial data collection
4. Monitor live tick counts in the sidebar

### Step 2: Configure Analytics
- **Symbol A / Symbol B**: Select trading pairs for analysis
- **Timeframe**: Choose resampling interval (1s, 1m, or 5m)
- **Rolling Window**: Adjust window size for statistics (default: 20)
- **Alert Threshold**: Set z-score threshold for alerts (default: 2.0)

### Step 3: View Analytics
Navigate through tabs:
- **📈 Live Analytics**: Real-time charts (prices, spread, z-score, correlation)
- **📊 Summary Statistics**: Comprehensive statistical summaries
- **⚠️ Alerts**: Active alerts when z-score exceeds threshold
- **💾 Data Export**: Download raw ticks, OHLC, or analytics results

### Step 4: Advanced Features
- Click **"🔬 Run ADF Test"** to test spread stationarity
- Use **Auto-refresh** for continuous live updates
- Export data in multiple formats for external analysis

---

## 🏗️ Architecture

### Technology Stack
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | Streamlit + Plotly | Interactive dashboard and visualizations |
| **Backend** | Python (pandas, numpy, scipy) | Data processing and analytics |
| **Data Source** | Binance Futures WebSocket | Real-time tick data streaming |
| **Database** | SQLite | Local data persistence with indexing |
| **Analytics** | statsmodels, scipy | Statistical tests and regression |

### Key Design Principles
- **Modular Architecture**: Clear separation between ingestion, storage, analytics, and UI
- **Thread-Safe Operations**: Multi-threaded WebSocket with proper locking
- **Performance Optimized**: Batch database writes, indexed queries
- **Extensible Design**: Easy to add new data sources or analytics

---

## 📊 Expected Results

After 30-60 seconds of data collection (BTC/ETH pair):

| Metric | Expected Value |
|--------|---------------|
| **Hedge Ratio (β)** | ~15-20 (1 BTC ≈ 15-20 ETH) |
| **R² (Fit Quality)** | 0.85-0.95 (strong correlation) |
| **Correlation** | 0.80-0.95 (highly correlated) |
| **ADF Test p-value** | < 0.05 (stationary spread) |
| **Z-Score Range** | Typically between -2 and +2 |

---

## 📁 Project Structure

```
gemscap_quant_app/
├── app.py              # Main Streamlit application
├── analytics.py        # Quantitative analytics engine
├── ingestion.py        # WebSocket data ingestion
├── storage.py          # SQLite database interface
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── .gitignore          # Git ignore rules
├── run_app.bat         # Windows CMD launcher
└── run_app.ps1         # PowerShell launcher
```

---

## 🔧 Dependencies

```
streamlit==1.31.1       # Web application framework
pandas==2.2.0           # Data manipulation
numpy==1.26.3           # Numerical computing
scipy==1.12.0           # Scientific computing
statsmodels==0.14.1     # Statistical models
plotly==5.18.0          # Interactive visualizations
websocket-client==1.7.0 # WebSocket connections
```

---

## 🎓 Analytics Methodology

### OLS Hedge Ratio
**Formula**: `Price_A = α + β × Price_B + ε`

The hedge ratio (β) represents the optimal ratio for constructing a market-neutral spread. Used for pairs trading to determine position sizing.

### Spread Construction
**Formula**: `Spread = Price_A - β × Price_B`

The spread represents the residual after removing the systematic relationship between assets. A stationary spread indicates cointegration and mean-reversion potential.

### Z-Score
**Formula**: `Z = (Spread - μ_rolling) / σ_rolling`

Indicates how many standard deviations the spread is from its rolling mean:
- |Z| > 2: Potential trading signal (spread is stretched)
- |Z| < 0.5: Spread near equilibrium

### ADF Test (Augmented Dickey-Fuller)
Tests for stationarity (mean reversion):
- **p-value < 0.05**: Spread is stationary ✅ (suitable for pairs trading)
- **p-value ≥ 0.05**: Spread may not be mean-reverting ⚠️

---

## 🎬 Demo Video

Watch the 2-minute demonstration: [Video Link]

*Showcasing real-time data ingestion, analytics computation, and interactive visualizations.*

---

## 📝 Assignment Details

**Company**: Gemscap Global Analyst Pvt. Ltd.  
**Position**: Quantitative Developer Intern  
**Institution**: Vishwakarma Institute of Technology (VIT), Pune  
**Batch**: 2026  
**Submission Date**: December 2024

---

## 👤 Author

**Aditya Gorave**  
📧 Email: adityagorave2670@gmail.com  
🎓 VIT Pune - Class of 2026  
💼 GitHub: [@adityagorave21](https://github.com/adityagorave21)

---


## 🙏 Acknowledgments

- **Binance**: For providing free WebSocket API access
- **Streamlit**: For excellent rapid prototyping framework
- **Plotly**: For interactive visualization library
- **Statsmodels**: For statistical testing implementations

---

## 🔍 Troubleshooting

### Common Issues

**"Python not found"**
- Install Python 3.8+ from [python.org](https://python.org/downloads)
- Ensure "Add Python to PATH" is checked during installation

**"Cannot activate venv" (PowerShell)**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**"Module not found" error**
- Ensure virtual environment is activated (you see `(venv)` in terminal)
- Re-run: `pip install -r requirements.txt`

**"Port already in use"**
- Another Streamlit app is running. Close it or use different port:
```bash
streamlit run app.py --server.port 8502
```

**"WebSocket connection failed"**
- Check internet connection
- Verify Binance API is not blocked by firewall
- Wait a few seconds and click "Start" again

---

## 🚀 Future Enhancements

Potential extensions for production deployment:
- Kalman Filter for dynamic hedge ratio estimation
- Multiple exchange support (Binance, FTX, Coinbase)
- Advanced backtesting engine with transaction costs
- Machine learning models for spread prediction
- Portfolio optimization and risk management
- Real-time P&L tracking and reporting

-

**⭐ If this project helped you, please star the repository!**

*Built with passion for quantitative finance and algorithmic trading* 📈
