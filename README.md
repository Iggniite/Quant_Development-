# ⚡ Quant Analytics Dashboard

### Real-Time Statistical Arbitrage System

## 📖 Project Overview

This project is a **real-time quantitative trading analytics dashboard** focused on **Statistical Arbitrage (Pairs Trading)**.
It connects to **Binance Futures WebSocket streams**, continuously monitors two correlated crypto assets (e.g., BTC–ETH), and applies statistical models to identify **mean-reversion trading opportunities**.

When the relationship between two assets deviates significantly from its historical norm, the system highlights potential **long/short signals** based on Z-Score thresholds.

---

## 📸 Live Dashboard Preview

![Real-Time Statistical Arbitrage Dashboard](Architecture%20Diagram/dashboard.jpeg)

**What this shows:**

* The **live Streamlit dashboard** displaying hedge ratio, Z-score, correlation, and simulated PnL.
* Interactive charts for **price action**, **spread**, and **standardized Z-score**.
* User-controlled parameters like rolling window size, resampling interval, and alert thresholds for strategy tuning.

---

## 🛠️ System Architecture

![System Architecture Flow](Architecture%20Diagram/flow.jpeg)

**Architecture explanation:**

* Real-time tick data is streamed from **Binance Futures** using WebSockets.
* Data flows through an **ingestion layer**, gets stored in SQLite, and is processed by the analytics engine.
* The frontend dashboard visualizes analytics results and triggers alerts when statistical thresholds are breached.

---

## ✨ Key Features

* 🔴 **Live Market Data** via Binance WebSocket streams
* 📊 **Advanced Analytics**

  * OLS Hedge Ratio
  * Spread computation
  * Z-Score normalization
  * Rolling correlation
  * ADF stationarity test
* 📈 **Interactive Streamlit Dashboard**
* 🧪 **Strategy Backtesting & Simulated PnL**
* 🚨 **Z-Score Based Trading Alerts**
* 📁 **CSV Export for Offline Analysis**

---

## 🚀 Setup & Installation

### Prerequisites

* **Python 3.8+**

### 1️⃣ Install Dependencies

```bash
pip install websockets asyncio pandas numpy statsmodels streamlit plotly
```

---

### 2️⃣ Start Data Ingestion (Backend)

This process continuously listens to Binance and stores live tick data.

```bash
python ingestion.py
```

✔ Keep this terminal running
✔ You should see messages like `Connected to btcusdt`

---

### 3️⃣ Launch the Dashboard (Frontend)

Open a **new terminal window**:

```bash
streamlit run dashboard.py
```

A browser window will open automatically with the live dashboard.

---

## 📊 How to Use the Dashboard

### Pair Selection

* **Symbol Y (Dependent):** Asset being traded (e.g., ETH)
* **Symbol X (Independent):** Reference asset (e.g., BTC)

> Tip: Choose assets with historically strong correlation.

---

### Timeframe & Sampling

* **1 Second:** Fast, noisy, high-frequency analysis
* **1–5 Minutes:** Smoother trends, better statistical stability

---

### Strategy Controls

* **Rolling Window:** Look-back period for mean and standard deviation
* **Z-Score Thresholds:**

  * `Z > +2.0` → Possible Short Opportunity
  * `Z < -2.0` → Possible Long Opportunity

---

## 🧮 Mathematical Methodology

1️⃣ **Hedge Ratio (OLS Regression)**
Uses Ordinary Least Squares to model the relationship between two assets.

2️⃣ **Spread Calculation**
Measures deviation between the assets after applying the hedge ratio.

3️⃣ **Z-Score Normalization**
Standardizes the spread using rolling mean and standard deviation.

4️⃣ **ADF Stationarity Test**
Confirms mean-reversion behavior (p-value < 0.05 indicates stationarity).

---

## 📁 Project Structure

```
.
├── ingestion.py        # WebSocket data ingestion
├── analytics.py        # Statistical calculations & backtesting
├── dashboard.py        # Streamlit frontend
├── market_data.db      # SQLite database (auto-generated)
├── Architecture Diagram/
│   ├── dashboard.jpeg
│   └── flow.jpeg
├── README.md
```

---

## 🤖 AI Usage Disclosure

* **Coding Assistance:** LLMs were used for generating boilerplate code (Streamlit UI, SQLite handling).
* **Logic Verification:** AI assisted in validating OLS regression and Z-Score calculations.

---

## 👤 Author

**Sakib Patel**
📅 *16 December 2025*
